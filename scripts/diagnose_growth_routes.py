#!/usr/bin/env python3
"""Read-only inspect public catalog aliases and five multilingual press routes.

Does not assert which hosting provider owns the domain. Does not purge caches.
"""
import argparse
import hashlib
import json
import re
import sys
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit, urlunsplit
from urllib.request import Request, urlopen

PRESS_PAGES = {
    "/press/": "en",
    "/press/es/": "es",
    "/press/pt-br/": "pt-BR",
    "/press/ja/": "ja",
    "/press/id/": "id",
}
PATHS = ("/apps", "/apps.html", "/support/twotaku/", "/robots.txt", "/sitemap.xml") + tuple(PRESS_PAGES)
LANG = re.compile(r'<html\b[^>]*\blang="([^"]+)"', re.I)
ALT = re.compile(r'<link\b[^>]*\bhreflang="([^"]+)"\s+href="([^"]+)"', re.I)
HEADERS = ("cache-control", "age", "cf-cache-status", "x-cache", "etag", "last-modified", "server")
CANONICAL = re.compile(r'<link\s+rel="canonical"\s+href="([^"]+)"', re.I)
RELEASE = re.compile(r'<meta\s+name="sk-growth-release"\s+content="([^"]+)"', re.I)


def origin_from_url(url):
    parts = urlsplit(url)
    if parts.scheme not in ("https", "http") or not parts.hostname or parts.username or parts.password or parts.query or parts.fragment or parts.path not in ("", "/"):
        raise ValueError("Base URL must be an HTTP(S) origin with no path, credentials or query")
    return urlunsplit((parts.scheme, parts.netloc, "", "", ""))


def summarize_response(status, final_url, body, headers):
    """Return public diagnostics only, without HTML or user data."""
    text = body.decode("utf-8", "replace")
    canonical = CANONICAL.findall(text)
    releases = RELEASE.findall(text)
    normalized_headers = {k.lower(): str(v) for k, v in headers.items()}
    return {
        "status": status,
        "final_url": final_url,
        "sha256": hashlib.sha256(body).hexdigest(),
        "bytes": len(body),
        "canonical": canonical[0] if len(canonical) == 1 else None,
        "release": releases[0] if len(releases) == 1 else None,
        "headers": {key: normalized_headers[key] for key in HEADERS if key in normalized_headers},
    }


def check_press_page(path, status, body, origin):
    """Safe static content checks for a localized press route; never claim browser functionality."""
    html = body.decode("utf-8", "replace")
    langs = LANG.findall(html)
    urls = CANONICAL.findall(html)
    alternatives = ALT.findall(html)
    expected = {lang: origin + url for url, lang in PRESS_PAGES.items()}
    expected["x-default"] = origin + "/press/"
    return {
        "http_200": status == 200,
        "html_lang_matches": langs == [PRESS_PAGES[path]],
        "canonical_matches": urls == [origin + path],
        "reciprocal_hreflang": len(alternatives) == len(expected) and dict(alternatives) == expected,
        "store_click_event": 'press_app_click' in html,
        "five_store_links": html.count('data-cta="store"') == 5,
    }


def diagnose(origin, fetch):
    rows = {}
    for path in PATHS:
        url = origin + path
        try:
            status, final_url, body, headers = fetch(url)
            rows[path] = summarize_response(status, final_url, body, headers)
            if path in PRESS_PAGES:
                rows[path]["press_checks"] = check_press_page(path, status, body, origin)
            elif path == "/sitemap.xml":
                rows[path]["press_sitemap_entries"] = {
                    language: (origin + target in body.decode("utf-8", "replace"))
                    for target, language in PRESS_PAGES.items()
                }
            elif path == "/apps":
                page = body.decode("utf-8", "replace")
                rows[path]["catalog_locale_source"] = (
                    'id="catalog-language"' in page
                    and 'catalog_language_selected' in page
                    and all('option value="' + lang + '"' in page
                            for lang in ("en", "ja", "es", "pt-BR", "id"))
                )
        except (HTTPError, URLError, TimeoutError, OSError, ValueError) as exc:
            rows[path] = {"error": type(exc).__name__, "status": getattr(exc, "code", None)}
    a, b = rows["/apps"], rows["/apps.html"]
    same_body = bool(a.get("status") == 200 and b.get("status") == 200 and a.get("sha256") == b.get("sha256"))
    same_destination = bool(a.get("status") == 200 and b.get("status") == 200 and
                            a.get("final_url") and a.get("final_url") == b.get("final_url"))
    alias_problem = not (same_body or same_destination)
    sitemap = rows.get("/sitemap.xml", {}).get("press_sitemap_entries", {})
    press_ready = {
        route: (all(rows.get(route, {}).get("press_checks", {}).values())
                and sitemap.get(PRESS_PAGES[route], False))
        for route in PRESS_PAGES
    }
    return {
        "origin": origin,
        "pages": rows,
        "press_routes_ready": press_ready,
        "press_needs_review": not all(press_ready.values()),
        "catalog_locale_needs_review": rows.get("/apps", {}).get("catalog_locale_source") is not True,
        "apps_aliases_equal": same_body,
        "apps_aliases_same_destination": same_destination,
        "apps_alias_needs_review": alias_problem,
        "limitations": "HTTP content checks are static: CDN cache, redirects or host HTML rewriting can affect checks. Inspect provider deployment before changing DNS. No JS, GA4 or installs validated.",
    }


def network_fetch(url, timeout):
    req = Request(url, headers={"User-Agent": "SKAppsReadOnlyReleaseDiagnostic/1.0", "Cache-Control": "no-cache"})
    try:
        with urlopen(req, timeout=timeout) as res:
            return res.status, res.url, res.read(3_000_000), dict(res.headers.items())
    except HTTPError as exc:
        return exc.code, exc.url, exc.read(300_000), dict(exc.headers.items())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="https://appdevelopsk.com")
    parser.add_argument("--timeout", type=float, default=12)
    parser.add_argument("--output")
    args = parser.parse_args()
    if args.timeout <= 0:
        parser.error("--timeout must be positive")
    try:
        origin = origin_from_url(args.base_url)
    except ValueError as exc:
        parser.error(str(exc))
    result = diagnose(origin, lambda url: network_fetch(url, args.timeout))
    payload = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        with open(args.output, "w", encoding="utf-8") as fp:
            fp.write(payload)
    else:
        print(payload, end="")
    return 1 if (result["apps_alias_needs_review"] or result["press_needs_review"] or result["catalog_locale_needs_review"]) else 0


if __name__ == "__main__":
    sys.exit(main())
