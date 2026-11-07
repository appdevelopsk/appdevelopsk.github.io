"""Offline checks for GSC-driven support-page claims and store conversion."""
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PAW = ROOT / "support" / "dog-breeds-encyclopedia" / "index.html"
FACE = ROOT / "support" / "face-reaction-battle" / "index.html"
PAW_PACKAGE = "com.appdevelopsk.dog_breeds_encyclopedia"


def meta(html, name, attribute="name"):
    matches = re.findall(
        rf'<meta {attribute}="{re.escape(name)}" content="([^"]+)"',
        html,
    )
    return matches[0] if len(matches) == 1 else None


def title(html):
    matches = re.findall(r"<title>([^<]+)</title>", html)
    return matches[0] if len(matches) == 1 else None


class SupportContentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.paw = PAW.read_text(encoding="utf-8")
        cls.face = FACE.read_text(encoding="utf-8")

    def test_paw_count_matches_verified_store_listing(self):
        self.assertIn("100 dog breed profiles", self.paw)
        self.assertNotIn("300+ dog breeds", self.paw)
        self.assertIn("100 Dog Breeds", title(self.paw))

    def test_paw_snippets_match_and_are_specific(self):
        description = meta(self.paw, "description")
        self.assertEqual(description, meta(self.paw, "og:description", "property"))
        self.assertIn("compare breed profiles", description)
        self.assertGreaterEqual(len(description), 90)
        self.assertLessEqual(len(description), 170)

    def test_paw_schema_matches_real_package_and_description(self):
        schemas = re.findall(
            r'<script type="application/ld\+json">\s*([\s\S]*?)</script>', self.paw)
        self.assertEqual(len(schemas), 1)
        data = json.loads(schemas[0])
        self.assertEqual(data["@type"], "SoftwareApplication")
        self.assertEqual(data["operatingSystem"], "Android")
        self.assertEqual(data["description"], meta(self.paw, "description"))
        self.assertEqual(
            data["downloadUrl"],
            f"https://play.google.com/store/apps/details?id={PAW_PACKAGE}",
        )

    def test_paw_two_distinct_measured_play_ctas(self):
        self.assertEqual(self.paw.count('data-position="hero"'), 1)
        self.assertEqual(self.paw.count('data-position="details"'), 1)
        links = re.findall(r'href="(https://play\.google\.com/store/apps/details\?id=([^&"]+)[^"]*)"', self.paw)
        self.assertEqual(len(links), 2)
        self.assertEqual([package for _url, package in links], [PAW_PACKAGE] * 2)
        self.assertIn("app_slug: 'dog-breeds-encyclopedia'", self.paw)
        self.assertIn("placement: a.getAttribute('data-position')", self.paw)

    def test_face_support_does_not_promise_download(self):
        self.assertIn("not currently available for download", self.face.lower())
        self.assertIn("Support & Game Alternatives", title(self.face))
        self.assertIn("not currently available for download", meta(self.face, "description").lower())
        self.assertEqual(meta(self.face, "description"),
                         meta(self.face, "og:description", "property"))
        self.assertEqual(self.face.count('data-alternative="'), 2)
        self.assertNotIn("com.appdevelopsk.face_reaction_battle", self.face)

    def test_canonicals_unchanged(self):
        for slug, html in (("dog-breeds-encyclopedia", self.paw),
                           ("face-reaction-battle", self.face)):
            with self.subTest(slug=slug):
                self.assertIn(
                    f'<link rel="canonical" href="https://appdevelopsk.com/support/{slug}/">',
                    html,
                )
                self.assertEqual(html.count("<title>"), 1)
                self.assertIsNotNone(meta(html, "description"))


if __name__ == "__main__":
    unittest.main()
