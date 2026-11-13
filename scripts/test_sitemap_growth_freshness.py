"""Validate catalog and recently revised support/guide sitemap dates.

Run with: python3 -m unittest discover -s scripts -p 'test_sitemap_growth_freshness.py' -v
"""
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent.parent
NS = "{http://www.sitemaps.org/schemas/sitemap/0.9}"
BASE = "https://appdevelopsk.com"
# Sitemap lastmod dates are authored in Japan Standard Time (UTC+09:00).
# GitHub-hosted runners use UTC, so date.today() wrongly rejects JST updates
# during 00:00–08:59 in Japan.
JST = timezone(timedelta(hours=9))


def publication_today(now=None):
    current = now if now is not None else datetime.now(timezone.utc)
    return current.astimezone(JST).date()

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
                stamp = pages.get(BASE + path)
                self.assertIsNotNone(stamp)
                self.assertGreaterEqual(date.fromisoformat(stamp), date(2026, 11, 7))

    def test_nov_13_serp_refinements_have_actual_lastmod(self):
        pages = dict(entries())
        for slug in ("debate-me", "brain-burst", "taletime"):
            with self.subTest(slug=slug):
                self.assertEqual(
                    pages.get(BASE + "/support/" + slug + "/"),
                    "2026-11-13",
                )

    def test_future_valid_page_updates_are_not_rejected(self):
        self.assertGreaterEqual(date.fromisoformat("2026-11-08"), date(2026, 11, 7))
        self.assertLess(date.fromisoformat("2026-11-06"), date(2026, 11, 7))

    def test_sitemap_dates_are_valid_and_not_future(self):
        for url, stamp in entries():
            with self.subTest(url=url):
                parsed = date.fromisoformat(stamp)
                self.assertLessEqual(parsed, publication_today())

    def test_jst_publication_date_is_not_utc_runner_date(self):
        # At 15:30 UTC on Nov 12 it is already Nov 13 in Japan.
        before_jst_midnight = datetime(2026, 11, 12, 14, 59, tzinfo=timezone.utc)
        after_jst_midnight = datetime(2026, 11, 12, 15, 30, tzinfo=timezone.utc)
        self.assertEqual(publication_today(before_jst_midnight), date(2026, 11, 12))
        self.assertEqual(publication_today(after_jst_midnight), date(2026, 11, 13))

    def test_filtered_catalog_urls_are_not_indexed_separately(self):
        urls = [url for url, _ in entries()]
        self.assertFalse(any("?goal=" in url for url in urls))


if __name__ == "__main__":
    unittest.main()
