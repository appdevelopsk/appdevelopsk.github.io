"""Offline fixtures for read-only support page deployment verification."""
import tempfile
import unittest
from pathlib import Path

from check_support_serp_live import BASE, SLUGS, compare, run


def head(title="Current snippet", desc="Accurate summary", canonical="https://appdevelopsk.com/support/debate-me/", duplicate=False):
    meta = f'<meta name="description" content="{desc}"><meta property="og:description" content="{desc}">'
    if duplicate:
        meta += f'<meta name="description" content="{desc}">'
    return f'<html><head><title>{title}</title>{meta}<link rel="canonical" href="{canonical}"></head><body><title>Ignore body title</title></body></html>'


class SupportSerpLiveTests(unittest.TestCase):
    def test_matching_unique_head_metadata_passes(self):
        expected = head()
        checks = compare(expected, expected, BASE + "/support/debate-me/")
        self.assertTrue(all(x["passed"] for x in checks))

    def test_old_public_title_fails(self):
        checks = compare(head(), head(title="Stale title"), BASE + "/support/debate-me/")
        self.assertIn("title", [x["check"] for x in checks if not x["passed"]])

    def test_old_public_description_fails(self):
        checks = compare(head(), head(desc="Stale description"), BASE + "/support/debate-me/")
        self.assertIn("description", [x["check"] for x in checks if not x["passed"]])

    def test_duplicate_public_description_fails(self):
        checks = compare(head(), head(duplicate=True), BASE + "/support/debate-me/")
        self.assertIn("description", [x["check"] for x in checks if not x["passed"]])

    def test_wrong_canonical_fails_even_when_matching_source(self):
        wrong = head(canonical="https://example.com/support/debate-me/")
        checks = compare(wrong, wrong, BASE + "/support/debate-me/")
        self.assertIn("canonical", [x["check"] for x in checks if not x["passed"]])

    def test_run_fail_closed_on_missing_live_page(self):
        with tempfile.TemporaryDirectory() as t:
            root = Path(t)
            for slug in SLUGS:
                page = root / "support" / slug / "index.html"
                page.parent.mkdir(parents=True)
                page.write_text(head(canonical=BASE + f"/support/{slug}/"), encoding="utf-8")
            def getter(url, timeout):
                if "taletime" in url:
                    raise TimeoutError("synthetic network outage")
                slug = url.split("/")[-2]
                return head(canonical=BASE + f"/support/{slug}/")
            report = run(BASE, 1, root=root, getter=getter)
            self.assertFalse(report["passed"])
            self.assertEqual(sum(bool(p["passed"]) for p in report["pages"]), 2)


if __name__ == "__main__":
    unittest.main()
