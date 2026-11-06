"""Offline source checks for editorial-guide category deep links."""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parent.parent
GUIDES = {
    "quick-games": "quick-games",
    "daily-habits": "habits",
    "decision-helpers": "decisions",
    "ai-tools": "ai",
}


class GuideCatalogDeepLinkTests(unittest.TestCase):
    def test_category_links_are_consistent(self):
        for slug, goal in GUIDES.items():
            with self.subTest(guide=slug):
                text = (ROOT / "guides" / slug / "index.html").read_text(encoding="utf-8")
                self.assertEqual(text.count(f'href="/apps?goal={goal}"'), 1)
                self.assertIn('href="/apps"', text)  # unfiltered breadcrumb remains available

    def test_catalog_reads_only_allowlisted_goals(self):
        catalog = (ROOT / "apps.html").read_text(encoding="utf-8")
        self.assertIn("new URLSearchParams(window.location.search).get('goal')", catalog)
        self.assertIn("['quick-games', 'habits', 'decisions', 'ai'].includes(requestedGoal)", catalog)
        self.assertIn("button.dataset.goal === goal", catalog)
        self.assertIn("render();", catalog)
        self.assertNotIn("utm_source=window.location.search", catalog)

    def test_catalog_filter_buttons_cover_guides(self):
        catalog = (ROOT / "apps.html").read_text(encoding="utf-8")
        for goal in GUIDES.values():
            with self.subTest(goal=goal):
                self.assertIn(f'data-goal="{goal}"', catalog)

    def test_catalog_cards_and_details_preserved(self):
        catalog = (ROOT / "apps.html").read_text(encoding="utf-8")
        self.assertEqual(len(re.findall(r'class="app-card"', catalog)), 92)
        self.assertEqual(len(re.findall(r'data-detail-app="', catalog)), 5)


if __name__ == "__main__":
    unittest.main()
