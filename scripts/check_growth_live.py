#!/usr/bin/env python3
"""Read-only deployment smoke: python3 scripts/check_growth_live.py [--base-url URL]."""
import argparse
import json
import re
import sys
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin
from urllib.request import Request, urlopen

SLUGS = ("debate-me", "tappitsu-battle", "future-me", "twotaku", "instant-judge")
FEATURED_SLUGS = ("debate-me", "tappitsu-battle", "future-me", "twotaku")
PATHS = ("/", "/apps", "/robots.txt", "/sitemap.xml") + tuple(
    f"/support/{slug}/" for slug in SLUGS
)


def inspect(pages):
    """Check public HTML without invoking JS or claiming installs."""
    findings = []

    def check(path, key, valid):
        findings.append({"path": path, "check": key, "passed": bool(valid)})

    for path in PATHS:
        check(path, "retrieved", path in pages)
    home = pages.get("/", "")
    check("/", "current_meta", "SK Apps | Mobile Apps, Games & Everyday Tools" in home)
    check("/", "no_stale_store_count", "92 Apps on Google Play" not in home)
    check("/", "analytics", "G-5Z588FVC81" in home)
    for slug in FEATURED_SLUGS:
        check("/", f"featured_{slug}", f'href="support/{slug}/"' in home)

    catalog = pages.get("/apps", "")
    check("/apps", "catalog_cards_92", len(re.findall(r'class="app-card"', catalog)) == 92)

    # Ensure listed Android packages match the actual schema and are not duplicated.
    package_ids = re.findall(
        r'<a class="app-card" href="https://play\.google\.com/store/apps/details\?id=([^&"]+)',
        catalog,
    )
    schema_match = re.search(
        r'<script type="application/ld\+json">\s*([\s\S]*?)</script>', catalog
    )
    try:
        listing = json.loads(schema_match.group(1))["mainEntity"]
        declared_count = listing["numberOfItems"]
        schema_items = listing["itemListElement"]
        schema_ids = [
            re.search(r"[?&]id=([^&]+)", item["url"]).group(1)
            for item in schema_items
        ]
    except (AttributeError, IndexError, KeyError, TypeError, ValueError):
        declared_count, schema_items, schema_ids = None, [], []
    check("/apps", "unique_play_packages",
          len(package_ids) == 92 and len(set(package_ids)) == 92)
    check("/apps", "catalog_schema_matches_links",
          declared_count == len(package_ids) == len(schema_items) and
          package_ids == schema_ids)
    check("/apps", "no_stale_live_store_claim", "92 free apps on Google Play" not in catalog)
    check("/apps", "store_click_tracking", "catalog_store_click" in catalog and "download_click" in catalog)
    check("/apps", "detail_click_tracking", "catalog_app_detail_click" in catalog)
    details = re.findall(
        r'<a\\b[^>]*\\bhref="([^"]+)"[^>]*\\bdata-detail-app="([^"]+)"', catalog
    )
    for slug in SLUGS:
        check("/apps", f"detail_{slug}",
              sum(link == f"/support/{slug}/" and key == slug for link, key in details) == 1)
    check("/apps", "five_distinct_detail_links", len(details) == len(SLUGS))

    for slug in SLUGS:
        path = f"/support/{slug}/"
        html = pages.get(path, "")
        links = re.findall(
            r'<a\\b[^>]*\\bhref="([^"]+)"[^>]*\\bdata-related-app="([^"]+)"', html
        )
        check(path, "two_other_apps",
              len(links) == 2 and
              len({key for _, key in links}) == 2 and
              all(key in SLUGS and key != slug and
                  href == f"/support/{key}/" for href, key in links))
        check(path, "analytics", "related_app_click" in html and "download_click" in html)
        check(path, "play_cta", 'data-position="hero"' in html and 'data-position="details"' in html)

    robots = pages.get("/robots.txt", "")
    check("/robots.txt", "public_icons_crawlable",
          "Allow: /icons/" in robots and "Disallow: /icons/" not in robots)
    sitemap = pages.get("/sitemap.xml", "")
    for path in ("/", "/apps") + tuple(f"/support/{s}/" for s in SLUGS):
        loc = "https://appdevelopsk.com" + path
        check("/sitemap.xml", f"listed_{path}", f"<loc>{loc}</loc>" in sitemap)

    return {"passed": all(item["passed"] for item in findings),
            "passedChecks": sum(item["passed"] for item in findings),
            "totalChecks": len(findings), "checks": findings,
            "limitations": "Read-only HTTP/source smoke; no JS execution, GA4 DebugView, store installs or device verification."}


def fetch_pages(base_url, timeout):
    pages = {}
    for path in PATHS:
        url = urljoin(base_url.rstrip("/") + "/", path.lstrip("/"))
        try:
            request = Request(url, headers={"User-Agent": "SKAppsGrowthSmoke/1.0"})
            with urlopen(request, timeout=timeout) as response:
                if response.status != 200:
                    raise RuntimeError(f"HTTP {response.status}")
                pages[path] = response.read(2_500_000).decode("utf-8", "replace")
        except (HTTPError, URLError, TimeoutError, RuntimeError) as exc:
            print(f"WARN: {path}: {exc}", file=sys.stderr)
    return pages


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="https://appdevelopsk.com")
    parser.add_argument("--timeout", type=float, default=10)
    args = parser.parse_args()
    if not args.base_url.startswith(("https://", "http://")):
        parser.error("--base-url must begin with http:// or https://")
    if args.timeout <= 0:
        parser.error("--timeout must be positive")
    report = inspect(fetch_pages(args.base_url, args.timeout))
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
