"""Source preflight and deliberate corruption tests.

Run from repo root:
    python3 -m unittest scripts.test_preflight_app_discovery -v
"""
import importlib.util
import shutil
import tempfile
import unittest
from pathlib import Path

FILE = Path(__file__).with_name("preflight_app_discovery.py")
SPEC = importlib.util.spec_from_file_location("preflight_app_discovery", FILE)
checker = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(checker)
ROOT = Path(__file__).resolve().parents[1]


class PreflightTests(unittest.TestCase):
    def test_current_source_passes(self):
        result = checker.verify(ROOT)
        self.assertTrue(result["ok"], result["errors"])
        self.assertEqual(result["catalog_cards"], 92)
        self.assertEqual(result["press_locales"], {x: "pass" for x in checker.PRESS})

    def fixture_root(self, dest):
        for source in ["apps.html", "sitemap.xml", *checker.PRESS.values(),
                       *["support/" + slug + "/index.html" for slug in checker.PILOTS]]:
            target = dest / source
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / source, target)

    def test_invalid_localized_canonical_is_rejected(self):
        with tempfile.TemporaryDirectory() as work:
            root = Path(work)
            self.fixture_root(root)
            page = root / checker.PRESS["ja"]
            text = page.read_text(encoding="utf-8")
            self.assertIn(checker.page_url(checker.PRESS["ja"]), text)
            page.write_text(text.replace(
                checker.page_url(checker.PRESS["ja"]),
                "https://bad.example/press/ja/", 1), encoding="utf-8")
            result = checker.verify(root)
            self.assertFalse(result["ok"])
            self.assertIn("ja: canonical", result["errors"])

    def test_changed_play_package_or_card_count_is_rejected(self):
        with tempfile.TemporaryDirectory() as work:
            root = Path(work)
            self.fixture_root(root)
            page = root / "apps.html"
            text = page.read_text(encoding="utf-8")
            self.assertIn('class="app-card"', text)
            page.write_text(text.replace('class="app-card"', 'class="other-card"', 1),
                            encoding="utf-8")
            result = checker.verify(root)
            self.assertFalse(result["ok"])
            self.assertTrue(any("92" in s for s in result["errors"]))

    def test_missing_sitemap_entry_is_rejected(self):
        with tempfile.TemporaryDirectory() as work:
            root = Path(work)
            self.fixture_root(root)
            file = root / "sitemap.xml"
            content = file.read_text(encoding="utf-8")
            self.assertIn(checker.page_url(checker.PRESS["id"]), content)
            file.write_text(content.replace(
                checker.page_url(checker.PRESS["id"]),
                "https://bad.example/press/id/"), encoding="utf-8")
            result = checker.verify(root)
            self.assertFalse(result["ok"])
            self.assertIn("sitemap missing id press URL", result["errors"])

    def test_mismatched_app_tracking_identity_is_rejected(self):
        with tempfile.TemporaryDirectory() as work:
            root = Path(work)
            self.fixture_root(root)
            file = root / checker.PRESS["es"]
            content = file.read_text(encoding="utf-8")
            self.assertIn('data-app-package="com.blurapp.blur_app"', content)
            file.write_text(content.replace(
                'data-app-package="com.blurapp.blur_app"',
                'data-app-package="com.example.wrong"'), encoding="utf-8")
            result = checker.verify(root)
            self.assertFalse(result["ok"])
            self.assertIn("es: details catalog package mismatch", result["errors"])
            self.assertIn("es: store catalog package mismatch", result["errors"])

    def test_bad_play_url_is_never_accepted(self):
        self.assertIsNone(checker.play_package("https://evil.example/store/apps/details?id=com.blurapp.blur_app"))
        self.assertIsNone(checker.play_package("https://play.google.com/store/apps/details?id=com.a&id=com.b"))
        self.assertEqual(checker.play_package(
            "https://play.google.com/store/apps/details?id=com.blurapp.blur_app&amp;hl=en"
        ), "com.blurapp.blur_app")  # Extra escaped query params do not corrupt the package ID
        self.assertEqual(checker.play_package(
            "https://play.google.com/store/apps/details?id=com.blurapp.blur_app&hl=en"
        ), "com.blurapp.blur_app")


if __name__ == "__main__":
    unittest.main()
