#!/usr/bin/env python3
"""Read-only public metadata parity check for three revised support pages.

Run after deploying the intended main commit:
    python3 scripts/check_support_serp_live.py

Passes only when the publicly served HTML agrees with the checked-out source;
this is not proof of an exact deployed commit, Google reindexing or installs.
"""

import argparse
from html.parser import HTMLParser
import json
from pathlib import Path
import sys
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

BASE = "https://appdevelopsk.com"
SLUGS = ("debate-me", "brain-burst", "taletime")
ROOT = Path(__file__).resolve().parent.parent
FIELDS = ("title", "description", "og_description", "canonical")


class HeadMetadata(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.in_head = False
        self.in_title = False
        self.fields = {key: [] for key in FIELDS}

    def handle_starttag(self, tag, attrs):
        if tag == "head":
            self.in_head = True
            return
        if not self.in_head:
            return
        attributes = dict(attrs)
        if tag == "title":
            self.in_title = True
            self.fields["title"].append("")
        elif tag == "meta":
            if attributes.get("name", "").lower() == "description":
                self.fields["description"].append(attributes.get("content", ""))
            elif attributes.get("property", "").lower() == "og:description":
                self.fields["og_description"].append(attributes.get("content", ""))
        elif tag == "link" and "canonical" in attributes.get("rel", "").lower().split():
            self.fields["canonical"].append(attributes.get("href", ""))

    def handle_data(self, data):
        if self.in_head and self.in_title and self.fields["title"]:
            self.fields["title"][-1] += data

    def handle_endtag(self, tag):
        if tag == "title":
            self.in_title = False
        elif tag == "head":
            self.in_head = False


def read_head(html):
    parser = HeadMetadata()
    parser.feed(html)
    return parser.fields


def compare(source_html, public_html, canonical):
    source = read_head(source_html)
    public = read_head(public_html)
    findings = []
    for key in FIELDS:
        expected = source[key]
        actual = public[key]
        valid = len(expected) == len(actual) == 1 and bool(expected[0]) and expected == actual
        if key == "canonical":
            valid = valid and expected == [canonical]
        findings.append({"check": key, "passed": bool(valid), "expected": expected, "public": actual})
    return findings


def fetch_html(url, timeout):
    request = Request(url, headers={
        "User-Agent": "SKAppsSerpReleaseSmoke/1.0",
        "Cache-Control": "no-cache",
    })
    with urlopen(request, timeout=timeout) as response:
        if response.status != 200:
            raise RuntimeError(f"HTTP {response.status}")
        return response.read(2_500_000).decode("utf-8", "replace")


def run(base_url, timeout, root=ROOT, getter=fetch_html):
    pages = []
    for slug in SLUGS:
        path = f"/support/{slug}/"
        canonical = BASE + path
        local_path = root / "support" / slug / "index.html"
        item = {"path": path, "source": str(local_path.relative_to(root))}
        try:
            source = local_path.read_text(encoding="utf-8")
            public = getter(base_url.rstrip("/") + path, timeout)
            item["checks"] = compare(source, public, canonical)
            item["passed"] = all(c["passed"] for c in item["checks"])
        except (OSError, HTTPError, URLError, TimeoutError, RuntimeError, ValueError) as exc:
            item["passed"] = False
            item["error"] = f"{type(exc).__name__}: {exc}"
        pages.append(item)
    return {"passed": all(item["passed"] for item in pages), "pages": pages,
            "limitations": "Source/public metadata parity only. Verify deployment provider and SHA independently; no browser analytics, indexing or installations checked."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default=BASE)
    parser.add_argument("--timeout", type=float, default=10)
    args = parser.parse_args()
    parsed = urlsplit(args.base_url)
    if parsed.scheme not in ("https", "http") or not parsed.netloc or parsed.username or parsed.password:
        parser.error("--base-url must be a valid HTTP(S) origin without credentials")
    if args.timeout <= 0:
        parser.error("--timeout must be positive")
    report = run(args.base_url, args.timeout)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
