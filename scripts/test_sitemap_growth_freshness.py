"""Validate catalog and recently revised support/guide sitemap dates.

Run with: python3 -m unittest discover -s scripts -p 'test_sitemap_growth_freshness.py' -v
"""
from datetime import date
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent.parent
NS = "{http://www.sitemaps.org/schemas/sitemap/0.9}"
BASE = "https://appdevelopsk.com"
CHANGED_2026_11_07 = (
    "/", "/apps",
    "/support/taletime/", "/support/debate-me/",
    "/support/dog-breeds-encyclopedia/", "/support/face-reaction-battle/",
    "/guides/quick-games/", "/guides/daily-habits/",
    "/guides/decision-helpers/", "/guides/ai-tools/",
)


def entries():
    root = ET.parse(ROOT / "sitemap.xml").getroot()
    if root.tag != NS + "urlset":
        raise ValueError("unexpected sitemap XML root")
    records = []
    for item in root.findall(NS + "url"):
        url = item.findtext(NS + "loc")
        lastmod = item.findtext(NS + "lastmod")
        records.append((url, lastmod))
    return records


class GrowthSitemapFreshnessTests(unittest.TestCase):
    def test_sitemap_canonical_urls_are_unique(self):
        records = entries()
        urls = [url for url, _ in records]
        self.assertEqual(len(urls), len(set(urls)))
        self.assertGreaterEqual(len(urls), 319)
        self.assertTrue(all(url.startswith(BASE + "/") for url in urls))
        self.assertNotIn(BASE + "/apps.html", urls)

    def test_changed_pages_have_accurate_nov_7_date(self):
        pages = dict(entries())
        for path in CHANGED_2026_11_07:
            with self.subTest(path=path):
                self.assertEqual(pages.get(BASE + path), "2026-11-07")

    def test_sitemap_dates_are_valid_and_not_future(self):
        for url, stamp in entries():
            with self.subTest(url=url):
                parsed = date.fromisoformat(stamp)
                self.assertLessEqual(parsed, date.today())

    def test_filtered_catalog_urls_are_not_indexed_separately(self):
        urls = [url for url, _ in entries()]
        self.assertFalse(any("?goal=" in url for url in urls))


if __name__ == "__main__":
    unittest.main()
