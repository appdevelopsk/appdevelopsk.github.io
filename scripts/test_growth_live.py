"""Offline tests for the read-only growth deployment smoke."""
import json
import unittest

from check_growth_live import FEATURED_SLUGS, GROWTH_RELEASE_ID, PATHS, SLUGS, inspect


def valid_pages():
    pages = {path: "" for path in PATHS}
    pages["/"] = "SK Apps | Mobile Apps, Games & Everyday Tools G-5Z588FVC81 gtag(\'event\', \'app_detail_click\' " + " ".join(
        f'href="support/{slug}/"' for slug in FEATURED_SLUGS)
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
        " ".join(f'<a href="/support/{slug}/" data-detail-app="{slug}">' for slug in SLUGS)
    )
    related = {"debate-me": ("future-me", "tappitsu-battle"),
               "tappitsu-battle": ("debate-me", "future-me"),
               "future-me": ("debate-me", "tappitsu-battle"),
               "twotaku": ("debate-me", "instant-judge"),
               "instant-judge": ("twotaku", "debate-me")}
    for slug in SLUGS:
        other = related[slug]
        canonical = f"https://appdevelopsk.com/support/{slug}/"
        schema = json.dumps({
            "@context": "https://schema.org",
            "@type": "SoftwareApplication",
            "name": slug,
            "operatingSystem": "Android",
            "url": canonical,
        })
        pages[f"/support/{slug}/"] = (
            f'<link rel="canonical" href="{canonical}">' +
            '<script type="application/ld+json">' + schema + '</script>' +
            "related_app_click download_click " +
            'data-position="hero" data-position="details" ' +
            " ".join(f'<a href="/support/{x}/" data-related-app="{x}">' for x in other))
    pages["/robots.txt"] = "User-agent: *\\nAllow: /icons/\\n"
    pages["/sitemap.xml"] = "".join(
        f"<loc>https://appdevelopsk.com{p}</loc>"
        for p in ("/", "/apps") + tuple(f"/support/{s}/" for s in SLUGS))
    for path in ("/", "/apps") + tuple(f"/support/{slug}/" for slug in SLUGS):
        pages[path] = (f'<meta name="sk-growth-release" '
                       f'content="{GROWTH_RELEASE_ID}">' + pages[path])
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

    def test_twotaku_missing_related_link_fails(self):
        data = valid_pages()
        data["/support/twotaku/"] = data["/support/twotaku/"].replace(
            'data-related-app="instant-judge"', "")
        self.assertFalse(inspect(data)["passed"])

    def test_wrong_canonical_fails(self):
        data = valid_pages()
        data["/support/twotaku/"] = data["/support/twotaku/"].replace(
            'rel="canonical" href="https://appdevelopsk.com/support/twotaku/"',
            'rel="canonical" href="https://appdevelopsk.com/support/other/"')
        self.assertFalse(inspect(data)["passed"])

    def test_noindex_fails(self):
        data = valid_pages()
        data["/support/debate-me/"] += '<meta name="robots" content="noindex">'
        self.assertFalse(inspect(data)["passed"])

    def test_invalid_app_jsonld_fails(self):
        data = valid_pages()
        data["/support/instant-judge/"] = data["/support/instant-judge/"].replace(
            '"SoftwareApplication"', '"SomethingOther"', 1)
        self.assertFalse(inspect(data)["passed"])

    def test_missing_instant_judge_page_fails(self):
        data = valid_pages()
        del data["/support/instant-judge/"]
        self.assertFalse(inspect(data)["passed"])

    def test_related_app_wrong_href_fails(self):
        data = valid_pages()
        data["/support/twotaku/"] = data["/support/twotaku/"].replace(
            'href="/support/instant-judge/"', 'href="/support/missing-app/"')
        self.assertFalse(inspect(data)["passed"])

    def test_catalog_detail_wrong_href_fails(self):
        data = valid_pages()
        data["/apps"] = data["/apps"].replace(
            'href="/support/twotaku/"', 'href="/support/missing-app/"', 1)
        self.assertFalse(inspect(data)["passed"])

    def test_disallowed_icons_fail(self):
        data = valid_pages()
        data["/robots.txt"] += "Disallow: /icons/\\n"
        self.assertFalse(inspect(data)["passed"])

    def test_missing_release_fingerprint_fails(self):
        data = valid_pages()
        data["/apps"] = data["/apps"].replace('name="sk-growth-release"',
                                             'name="some-other-tag"')
        self.assertFalse(inspect(data)["passed"])

    def test_stale_release_fingerprint_fails(self):
        data = valid_pages()
        data["/support/twotaku/"] = data["/support/twotaku/"].replace(
            GROWTH_RELEASE_ID, "growth-previous")
        self.assertFalse(inspect(data)["passed"])

    def test_missing_live_page_fails(self):
        data = valid_pages()
        del data["/apps"]
        self.assertFalse(inspect(data)["passed"])

    def test_homepage_click_mislabeled_view_fails(self):
        data = valid_pages()
        data["/"] = data["/"].replace("app_detail_click", "app_view")
        self.assertFalse(inspect(data)["passed"])

    def test_homepage_missing_card_click_event_fails(self):
        data = valid_pages()
        data["/"] = data["/"].replace("app_detail_click", "something_else")
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

    def test_new_catalog_release_with_consistent_schema_passes(self):
        data = valid_pages()
        head, rest = data["/apps"].split("</script>", 1)
        schema = json.loads(head.split(">", 1)[1])
        pkg = "jp.appdevelopsk.testapp92"
        schema["mainEntity"]["numberOfItems"] = 93
        schema["mainEntity"]["itemListElement"].append(
            {"url": f"https://play.google.com/store/apps/details?id={pkg}"}
        )
        card = (f'<a class="app-card" '
                f'href="https://play.google.com/store/apps/details?id={pkg}&amp;utm_source=test">')
        data["/apps"] = ('<script type="application/ld+json">' +
                          json.dumps(schema) + '</script>' + rest + card)
        self.assertTrue(inspect(data)["passed"])

    def test_new_catalog_release_without_schema_update_fails(self):
        data = valid_pages()
        data["/apps"] += ('<a class="app-card" '
                          'href="https://play.google.com/store/apps/details?id=jp.appdevelopsk.testapp92&amp;utm_source=test">')
        self.assertFalse(inspect(data)["passed"])

    def test_fails_when_catalog_count_changes(self):
        data = valid_pages()
        data["/apps"] = data["/apps"].replace('class="app-card" ', "", 1)
        self.assertFalse(inspect(data)["passed"])


if __name__ == "__main__":
    unittest.main()
