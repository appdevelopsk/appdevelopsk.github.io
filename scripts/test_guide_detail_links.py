"""Check every editorial guide's store and support-detail navigation.

Run from checkout: python3 -m unittest discover -s scripts -p 'test_guide_detail_links.py' -v
"""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parent.parent
GUIDES = {
    "quick-games": {"blur", "instant-judge", "twotaku", "nodo", "brain-burst"},
    "daily-habits": {"true-me", "future-me", "water-reminder", "gratitude-log"},
    "decision-helpers": {"food-roulette", "movie-roulette", "what-to-do", "chore-roulette"},
    "ai-tools": {"debate-me", "voice-memo", "pantry-ai", "name-maker"},
}
ARTICLE = re.compile(r'<article class="app">([\s\S]*?)</article>')
STORE = re.compile(r'<a class="(?:store|play)" data-app="([^"]+)"')
DETAIL = re.compile(
    r'<a class="app-detail" href="/support/([^/"]+)/" data-guide-detail="([^"]+)"'
)


class GuideDetailLinksTests(unittest.TestCase):
    @staticmethod
    def read(guide):
        return (ROOT / "guides" / guide / "index.html").read_text(encoding="utf-8")

    def test_each_guide_card_has_matching_support_page(self):
        for guide, expected in GUIDES.items():
            with self.subTest(guide=guide):
                html = self.read(guide)
                articles = ARTICLE.findall(html)
                self.assertGreaterEqual(len(articles), len(expected))
                seen = set()
                for article in articles:
                    stores = STORE.findall(article)
                    details = DETAIL.findall(article)
                    self.assertEqual(len(stores), 1, "every card needs one store CTA")
                    self.assertEqual(len(details), 1, "every card needs one detail CTA")
                    app = stores[0]
                    title_match = re.search(r"<h3>([^<]+)</h3>", article)
                    self.assertIsNotNone(title_match)
                    self.assertIn(
                        f'aria-label="Features and FAQs for {title_match.group(1)}"',
                        article,
                    )
                    detail_path, detail_slug = details[0]
                    self.assertEqual((detail_path, detail_slug), (app, app))
                    self.assertNotIn(app, seen, "duplicate app card")
                    self.assertTrue(
                        (ROOT / "support" / detail_slug / "index.html").is_file(),
                        f"missing support page for {detail_slug}",
                    )
                    seen.add(app)
                self.assertTrue(expected.issubset(seen))

    def test_guide_click_events_do_not_replace_store_events(self):
        for guide in GUIDES:
            with self.subTest(guide=guide):
                html = self.read(guide)
                self.assertIn("'guide_store_click'", html)
                self.assertIn("'app_detail_click'", html)
                self.assertIn("placement: 'guide_card'", html)
                self.assertIn(f"guide: '{guide}'", html)
                self.assertEqual(html.count("document.querySelectorAll('a[data-guide-detail]')"), 1)
                self.assertIn("typeof window.gtag === 'function'", html)
                self.assertNotIn("query: input.value", html)

    def test_detail_links_remain_first_party_and_store_links_remain_external(self):
        for guide in GUIDES:
            with self.subTest(guide=guide):
                html = self.read(guide)
                self.assertEqual(
                    len(DETAIL.findall(html)),
                    len(STORE.findall(html)),
                )
                self.assertNotIn('class="app-detail" href="https://', html)
                for article in ARTICLE.findall(html):
                    self.assertIn("play.google.com/store/apps/details?id=", article)


if __name__ == "__main__":
    unittest.main()
