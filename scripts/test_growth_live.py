"""Offline tests for the read-only growth deployment smoke."""
import json
import unittest

from check_growth_live import PATHS, SLUGS, inspect


def valid_pages():
    pages = {path: "" for path in PATHS}
    pages["/"] = "SK Apps | Mobile Apps, Games & Everyday Tools G-5Z588FVC81 " + " ".join(
        f'href="support/{slug}/"' for slug in SLUGS)
    packages = [f"jp.appdevelopsk.testapp{i}" for i in range(92)]
    cards = " ".join(
        f'<a class="app-card" href="https://play.google.com/store/apps/details?id={pkg}&amp;utm_source=test">'
        for pkg in packages
    )
    listing = {
        "mainEntity": {
            "numberOfItems": len(packages),
            "itemListElement": [
                {"url": f"https://play.google.com/store/apps/details?id={pkg}"}
                for pkg in packages
            ],
        }
    }
    pages["/apps"] = (
        '<script type="application/ld+json">' + json.dumps(listing) + '</script>' +
        cards + " catalog_store_click download_click catalog_app_detail_click " +
        " ".join(f'data-detail-app="{slug}"' for slug in SLUGS)
    )
    for slug in SLUGS:
        other = [x for x in SLUGS if x != slug]
        pages[f"/support/{slug}/"] = (
            "related_app_click download_click " +
            'data-position="hero" data-position="details" ' +
            " ".join(f'data-related-app="{x}"' for x in other))
    pages["/robots.txt"] = "User-agent: *\\nAllow: /icons/\\n"
    pages["/sitemap.xml"] = "".join(
        f"<loc>https://appdevelopsk.com{p}</loc>"
        for p in ("/", "/apps") + tuple(f"/support/{s}/" for s in SLUGS))
    return pages


class GrowthSmokeTests(unittest.TestCase):
    def test_valid_source_fixture_passes(self):
        report = inspect(valid_pages())
        self.assertTrue(report["passed"])
        self.assertEqual(report["passedChecks"], report["totalChecks"])

    def test_missing_related_link_fails(self):
        data = valid_pages()
        data["/support/future-me/"] = data["/support/future-me/"].replace(
            'data-related-app="debate-me"', "")
        self.assertFalse(inspect(data)["passed"])

    def test_disallowed_icons_fail(self):
        data = valid_pages()
        data["/robots.txt"] += "Disallow: /icons/\\n"
        self.assertFalse(inspect(data)["passed"])

    def test_missing_live_page_fails(self):
        data = valid_pages()
        del data["/apps"]
        self.assertFalse(inspect(data)["passed"])

    def test_stale_homepage_metadata_fails(self):
        data = valid_pages()
        data["/"] += "92 Apps on Google Play"
        self.assertFalse(inspect(data)["passed"])

    def test_duplicate_store_package_fails(self):
        data = valid_pages()
        data["/apps"] = data["/apps"].replace(
            "id=jp.appdevelopsk.testapp1&amp;", "id=jp.appdevelopsk.testapp0&amp;", 1)
        self.assertFalse(inspect(data)["passed"])

    def test_store_schema_package_mismatch_fails(self):
        data = valid_pages()
        data["/apps"] = data["/apps"].replace(
            "id=jp.appdevelopsk.testapp1", "id=jp.appdevelopsk.unlisted", 1)
        self.assertFalse(inspect(data)["passed"])

    def test_stale_catalog_claim_fails(self):
        data = valid_pages()
        data["/apps"] += "92 free apps on Google Play"
        self.assertFalse(inspect(data)["passed"])

    def test_fails_when_catalog_count_changes(self):
        data = valid_pages()
        data["/apps"] = data["/apps"].replace('class="app-card" ', "", 1)
        self.assertFalse(inspect(data)["passed"])


if __name__ == "__main__":
    unittest.main()
