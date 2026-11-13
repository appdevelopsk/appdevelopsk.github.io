"""Offline multilingual release smoke tests, no network calls.

Run: python3 -m unittest discover -s scripts -p 'test_diagnose_growth_routes*.py' -v
"""
import unittest
from urllib.error import URLError
from diagnose_growth_routes import (
    PATHS, PRESS_PAGES, check_press_page, diagnose, origin_from_url,
)

ORIGIN = "https://appdevelopsk.com"

def press_html(route, replace=None):
    lang = PRESS_PAGES[route]
    alternatives = list(PRESS_PAGES.items())
    values = ['<html lang="' + lang + '"><head>',
              '<link rel="canonical" href="' + ORIGIN + route + '">']
    for name, code in alternatives:
        values.append('<link rel="alternate" hreflang="' + code +
                      '" href="' + ORIGIN + name + '">')
    values.append('<link rel="alternate" hreflang="x-default" href="' +
                  ORIGIN + '/press/">')
    values.append('</head><body><script>press_app_click</script>')
    values.extend('<a data-cta="store">Play</a>' for _ in range(5))
    values.append('</body></html>')
    html = ''.join(values)
    return html.replace(*replace).encode() if replace else html.encode()

def good_fetch(url):
    route = url.removeprefix(ORIGIN)
    if route in PRESS_PAGES:
        return 200, url, press_html(route), {'Cache-Control': 'public'}
    if route == "/sitemap.xml":
        locs = ''.join('<loc>' + ORIGIN + route + '</loc>' for route in PRESS_PAGES)
        return 200, url, ('<urlset>' + locs + '</urlset>').encode(), {}
    if route in ("/apps", "/apps.html"):
        body = ('<html id="catalog-language">catalog_language_selected ' +
                ' '.join('option value="' + l + '"' for l in ('en', 'ja', 'es', 'pt-BR', 'id')) +
                '</html>').encode()
        return 200, ORIGIN + "/apps", body, {}
    return 200, url, b"ok", {}

class PressReleaseRouteTests(unittest.TestCase):
    def test_five_press_routes_are_in_scan(self):
        for route in PRESS_PAGES:
            self.assertIn(route, PATHS)

    def test_fully_deployed_press_and_catalog_pass(self):
        out = diagnose(ORIGIN, good_fetch)
        self.assertFalse(out['press_needs_review'])
        self.assertFalse(out['catalog_locale_needs_review'])
        self.assertFalse(out['apps_alias_needs_review'])
        self.assertTrue(all(out['press_routes_ready'].values()))

    def test_404_or_inaccessible_not_reported_as_ready(self):
        def fetch(url):
            if url.endswith('/press/ja/'):
                return 404, url, b"404", {}
            if url.endswith('/press/id/'):
                raise URLError('origin unavailable')
            return good_fetch(url)
        out = diagnose(ORIGIN, fetch)
        self.assertFalse(out['press_routes_ready']['/press/ja/'])
        self.assertFalse(out['press_routes_ready']['/press/id/'])
        self.assertTrue(out['press_needs_review'])
        self.assertEqual(out['pages']['/press/id/']['error'], 'URLError')

    def test_200_fallback_page_not_mistaken_for_press_route(self):
        def fetch(url):
            if url.endswith('/press/es/'):
                status, final, body, headers = good_fetch(ORIGIN + '/apps')
                return status, final, body, headers
            return good_fetch(url)
        out = diagnose(ORIGIN, fetch)
        self.assertTrue(out['press_needs_review'])
        self.assertFalse(out['press_routes_ready']['/press/es/'])
        self.assertFalse(out['pages']['/press/es/']['press_checks']['canonical_matches'])

    def test_wrong_locale_and_missing_hreflang_are_rejected(self):
        html = press_html("/press/ja/", ('<html lang="ja">', '<html lang="en">'))
        checked = check_press_page("/press/ja/", 200, html, ORIGIN)
        self.assertFalse(checked["html_lang_matches"])
        html2 = press_html("/press/id/", ('hreflang="pt-BR"', 'hreflang="pt"'))
        self.assertFalse(check_press_page("/press/id/", 200, html2, ORIGIN)["reciprocal_hreflang"])

    def test_missing_sitemap_locale_is_a_release_blocker(self):
        def fetch(url):
            if url.endswith('/sitemap.xml'):
                return 200, url, b'<loc>https://appdevelopsk.com/press/</loc>', {}
            return good_fetch(url)
        out = diagnose(ORIGIN, fetch)
        self.assertTrue(out['press_needs_review'])
        self.assertTrue(out['press_routes_ready']['/press/'])
        self.assertFalse(out['press_routes_ready']['/press/ja/'])

    def test_sitemap_prefix_and_comment_cannot_fake_publication(self):
        def fetch(url):
            if url.endswith('/sitemap.xml'):
                body = ('<urlset><!-- https://appdevelopsk.com/press/id/ -->'
                        '<loc>https://appdevelopsk.com/press/ja/extra/</loc></urlset>')
                return 200, url, body.encode(), {}
            return good_fetch(url)
        out = diagnose(ORIGIN, fetch)
        self.assertFalse(out['press_routes_ready']['/press/ja/'])
        self.assertFalse(out['press_routes_ready']['/press/id/'])

    def test_invalid_xml_fails_closed_without_crashing(self):
        def fetch(url):
            if url.endswith('/sitemap.xml'):
                return 200, url, b'<invalid sitemap', {}
            return good_fetch(url)
        out = diagnose(ORIGIN, fetch)
        self.assertTrue(out['press_needs_review'])
        self.assertFalse(any(out['press_routes_ready'].values()))

    def test_stale_catalog_locale_is_independently_reported(self):
        def fetch(url):
            if url.endswith('/apps'):
                return 200, url, b'Old English catalog', {}
            return good_fetch(url)
        out = diagnose(ORIGIN, fetch)
        self.assertTrue(out['catalog_locale_needs_review'])
        self.assertFalse(out['press_needs_review'])

    def test_public_report_never_includes_page_text(self):
        out = diagnose(ORIGIN, good_fetch)
        text = repr(out)
        self.assertNotIn('<html', text)
        self.assertNotIn('data-cta="store"', text)

if __name__ == "__main__":
    unittest.main()
