"""Offline tests for the read-only growth deployment smoke."""
import unittest

from check_growth_live import PATHS, SLUGS, inspect


def valid_pages():
    pages = {path: "" for path in PATHS}
    pages["/"] = "SK Apps | Mobile Apps, Games & Everyday Tools G-5Z588FVC81 " + " ".join(
        f'href="support/{slug}/"' for slug in SLUGS)
    pages["/apps"] = ('class="app-card" ' * 92 +
                      "catalog_store_click download_click catalog_app_detail_click " +
                      " ".join(f'data-detail-app="{slug}"' for slug in SLUGS))
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
