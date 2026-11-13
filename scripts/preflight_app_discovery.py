#!/usr/bin/env python3
"""Offline, read-only preflight for the SK Apps website acquisition release.

Run: python3 scripts/preflight_app_discovery.py
No remote network, credentials, publishing, DNS, analytics, or store changes.
This verifies *source files* only; successful preflight is not live deployment.
"""
import argparse
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import parse_qs, urlsplit
from xml.etree import ElementTree

ORIGIN = "https://appdevelopsk.com"
PRESS = {
    "en": "press/index.html",
    "es": "press/es/index.html",
    "pt-BR": "press/pt-br/index.html",
    "ja": "press/ja/index.html",
    "id": "press/id/index.html",
}
PILOTS = {"blur", "twotaku", "instant-judge", "debate-me", "future-me"}


def page_url(filename):
    return ORIGIN + "/" + filename.removesuffix("index.html")


def play_package(href):
    parts = urlsplit(href)
    ids = parse_qs(parts.query).get("id", [])
    if (parts.scheme != "https" or parts.hostname != "play.google.com"
            or parts.username or parts.password
            or parts.path != "/store/apps/details" or len(ids) != 1
            or not re.fullmatch(r"[A-Za-z0-9_.]+", ids[0])):
        return None
    return ids[0]


class Markup(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.tags = []
        self.cards = []
        self.current_card = None

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        self.tags.append((tag, a))
        if tag == "a" and "app-card" in a.get("class", "").split():
            if self.current_card is not None:
                raise ValueError("Nested catalog cards")
            self.current_card = {"package": play_package(a.get("href", "")), "slug": None}
        elif tag == "img" and self.current_card is not None:
            match = re.fullmatch(r"icons/apps/([a-z0-9-]+)\.png", a.get("src", ""))
            if match:
                self.current_card["slug"] = match.group(1)

    def handle_endtag(self, tag):
        if tag == "a" and self.current_card is not None:
            self.cards.append(self.current_card)
            self.current_card = None


def load_html(root, filename):
    return (root / filename).read_text(encoding="utf-8")


def parse_html(text):
    parser = Markup()
    parser.feed(text)
    return parser


def verify(root):
    errors = []
    result = {"source_only": True, "catalog_cards": 0, "press_locales": {}, "ok": False}
    try:
        catalog = load_html(root, "apps.html")
        doc = parse_html(catalog)
    except (OSError, UnicodeError, ValueError) as exc:
        return {**result, "errors": ["apps.html unavailable or malformed: " + type(exc).__name__]}

    cards = doc.cards
    result["catalog_cards"] = len(cards)
    if len(cards) != 92:
        errors.append("Catalog must contain exactly 92 verified Play cards")
    if any(not c["package"] or not c["slug"] for c in cards):
        errors.append("Catalog card has invalid Google Play URL or icon slug")
    slugs = [c["slug"] for c in cards]
    packages = [c["package"] for c in cards]
    if len(set(slugs)) != len(cards) or len(set(packages)) != len(cards):
        errors.append("Catalog has duplicate slug or Play package")
    if not re.search(r'"numberOfItems"\s*:\s*92\b', catalog):
        errors.append("Catalog JSON-LD item count differs from 92 cards")
    if not PILOTS.issubset(set(slugs)):
        errors.append("A pilot app is absent from catalog")
    if not all(x in catalog for x in ('id="catalog-language"', "catalog_language_selected", "download_click")):
        errors.append("Catalog five-language UI or GA4 outbound tracking missing")
    for lang in PRESS:
        if 'option value="' + lang + '"' not in catalog:
            errors.append("Catalog language selector missing " + lang)

    mapped = {c["slug"]: c["package"] for c in cards}
    expected_hreflang = {lang: page_url(filename) for lang, filename in PRESS.items()}
    expected_hreflang["x-default"] = expected_hreflang["en"]
    for lang, filename in PRESS.items():
        checks = []
        try:
            html = load_html(root, filename)
            p = parse_html(html)
            nodes = p.tags
            links = [a for tag, a in nodes if tag == "link"]
            actual_langs = [a.get("lang") for tag, a in nodes if tag == "html"]
            canonicals = [a.get("href") for a in links if a.get("rel") == "canonical"]
            alternates = [a for a in links if a.get("rel") == "alternate"]
            actual_hreflang = {a.get("hreflang"): a.get("href") for a in alternates}
            anchors = [a for tag, a in nodes if tag == "a" and a.get("data-cta")]
            details = [a for a in anchors if a.get("data-cta") == "details"]
            stores = [a for a in anchors if a.get("data-cta") == "store"]
            if actual_langs != [lang]:
                checks.append("html lang")
            if canonicals != [page_url(filename)]:
                checks.append("canonical")
            if len(alternates) != len(expected_hreflang) or actual_hreflang != expected_hreflang:
                checks.append("reciprocal hreflang")
            if len(details) != 5 or len(stores) != 5 or len(anchors) != 10:
                checks.append("five detail and store CTAs")
            if sum(tag == "article" for tag, _ in nodes) != 5 or sum(tag == "h1" for tag, _ in nodes) != 1:
                checks.append("five app cards and one H1")
            if "press_app_click" not in html or "'download_click'" not in html:
                checks.append("GA4 press/store event contract")
            for cta, group in (("details", details), ("store", stores)):
                if {a.get("data-app-slug") for a in group} != PILOTS:
                    checks.append(cta + " app slug coverage")
                for a in group:
                    slug = a.get("data-app-slug")
                    pkg = a.get("data-app-package")
                    if not slug or pkg != mapped.get(slug):
                        checks.append(cta + " catalog package mismatch")
                    if cta == "details":
                        if a.get("href") != "/support/" + str(slug) + "/":
                            checks.append("detail support destination mismatch")
                        elif not (root / "support" / slug / "index.html").is_file():
                            checks.append("missing support page")
                    elif play_package(a.get("href", "")) != pkg:
                        checks.append("store destination mismatch")
            result["press_locales"][lang] = "pass" if not checks else "fail"
            errors.extend(lang + ": " + problem for problem in sorted(set(checks)))
        except (OSError, UnicodeError, ValueError) as exc:
            result["press_locales"][lang] = "fail"
            errors.append(lang + ": source unavailable or malformed (" + type(exc).__name__ + ")")

    try:
        root_xml = ElementTree.parse(root / "sitemap.xml").getroot()
        locations = {(node.text or "").strip() for node in root_xml.iter()
                     if node.tag.rsplit("}", 1)[-1] == "loc"}
        for lang, url in expected_hreflang.items():
            if lang != "x-default" and url not in locations:
                errors.append("sitemap missing " + lang + " press URL")
    except (OSError, ElementTree.ParseError) as exc:
        errors.append("sitemap.xml unavailable or invalid: " + type(exc).__name__)

    result["errors"] = sorted(set(errors))
    result["ok"] = not errors
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    report = verify(args.root)
    print(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
