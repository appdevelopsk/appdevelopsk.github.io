"""Offline parity check: literal post-deploy smoke assertions vs source main.

Run:
  python3 -m unittest scripts.test_live_smoke_source_parity -v

This never calls the internet or deploys anything. It checks source/contract
coherence, NOT whether the public VPS serves any of these versions. Dynamic
shell loop variables are separately covered by scripts.test_press_kit.
"""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
SMOKE_PATH = ROOT / "scripts/check_app_discovery_live.sh"

# Left hand: tempfile basename used by check_app_discovery_live.sh
# Right hand: exact checked-in source that its fetch(route, basename) loads.
SOURCE_PATHS = {
    "index.html": "index.html",
    "apps.html": "apps.html",
    "quick-games.html": "guides/quick-games/index.html",
    "quick-games-ja.html": "guides/quick-games/ja/index.html",
    "ai-debate-practice.html": "guides/ai-debate-practice/index.html",
    "ai-debate-practice-ja.html": "guides/ai-debate-practice/ja/index.html",
    "sitemap.xml": "sitemap.xml",
    "brain-burst.html": "support/brain-burst/index.html",
    "taletime.html": "support/taletime/index.html",
    "face-battle.html": "support/face-reaction-battle/index.html",
    "dotchi.html": "support/twotaku/index.html",
    "debate-me.html": "support/debate-me/index.html",
    "idea-market.html": "support/idea-market/index.html",
    "blur.html": "support/blur/index.html",
    "instant-judge.html": "support/instant-judge/index.html",
    "roastme.html": "support/roast-me/index.html",
    "futureme.html": "support/future-me/index.html",
}

# Check only literal, single-quoted -Fq source assertions. Double-quoted
# variables (e.g. "$language") are not expanded by this static checker.
LITERAL = re.compile(
    r'(?m)^[ \t]*(?P<forbidden>if[ \t]+)?grep[ \t]+-Fq[ \t]+'
    r"""'(?P<needle>[^']+)'[ \t]+"\$tmp/(?P<temp>[^"]+)\""""
)


def scan(smoke, html_sources):
    """Return a repeatable source-only report; no network or script execution."""
    checked = 0
    excluded_dynamic = 0
    errors = []
    refs = set()
    for match in LITERAL.finditer(smoke):
        target = match.group("temp")
        if "$" in target:
            excluded_dynamic += 1
            continue
        refs.add(target)
        source = html_sources.get(target)
        if source is None:
            errors.append(f"{target}: static smoke file has no checked source mapping")
            continue
        needle = match.group("needle")
        present = needle in source
        expected = not bool(match.group("forbidden"))
        checked += 1
        if present != expected:
            kind = "forbidden old source marker present" if not expected else "current marker missing"
            errors.append(f"{target}: {kind}: {needle[:100]}")
    return {"checked": checked, "excluded_dynamic": excluded_dynamic,
            "files": sorted(refs), "errors": errors}


class SmokeSourceParityTests(unittest.TestCase):
    def test_every_literal_public_assertion_matches_source_main(self):
        smoke = SMOKE_PATH.read_text(encoding="utf-8")
        docs = {temporary: (ROOT / source).read_text(encoding="utf-8")
                for temporary, source in SOURCE_PATHS.items()}
        report = scan(smoke, docs)
        self.assertGreaterEqual(report["checked"], 55, report)
        self.assertGreaterEqual(len(report["files"]), 14, report)
        self.assertEqual(report["errors"], [], report)
        self.assertGreater(report["excluded_dynamic"], 0,
                           "dynamic guide/press checks are verified by separate tests")

    def test_expected_app_pages_are_actually_represented(self):
        smoke = SMOKE_PATH.read_text(encoding="utf-8")
        docs = {temporary: (ROOT / source).read_text(encoding="utf-8")
                for temporary, source in SOURCE_PATHS.items()}
        report = scan(smoke, docs)
        self.assertTrue(set(SOURCE_PATHS).issuperset(report["files"]))
        self.assertIn("debate-me.html", report["files"])
        self.assertIn("brain-burst.html", report["files"])
        self.assertIn("taletime.html", report["files"])
        self.assertIn("futureme.html", report["files"])
        self.assertIn("sitemap.xml", report["files"])
        self.assertIn("ai-debate-practice.html", report["files"])
        self.assertIn("ai-debate-practice-ja.html", report["files"])

    def test_missing_required_marker_is_detected(self):
        fake = """grep -Fq 'current title' "$tmp/debate-me.html" || exit 1"""
        result = scan(fake, {"debate-me.html": "<title>Old title</title>"})
        self.assertEqual(result["checked"], 1)
        self.assertEqual(len(result["errors"]), 1)
        self.assertIn("current marker missing", result["errors"][0])

    def test_forbidden_old_marker_is_detected(self):
        fake = """if grep -Fq 'old cooking copy' "$tmp/debate-me.html"; then exit 1; fi"""
        result = scan(fake, {"debate-me.html": "old cooking copy"})
        self.assertEqual(result["checked"], 1)
        self.assertEqual(len(result["errors"]), 1)
        self.assertIn("forbidden old source marker", result["errors"][0])
        self.assertEqual(scan(fake, {"debate-me.html": "actual debate copy"})["errors"], [])

    def test_unknown_static_source_must_fail_closed(self):
        fake = """grep -Fq 'metadata' "$tmp/unmapped.html" || exit 1"""
        self.assertIn("no checked source mapping",
                      scan(fake, {})["errors"][0])

    def test_variable_dependent_smoke_checks_are_excluded_not_falsified(self):
        fake = """grep -Fq 'press_app_click' "$tmp/press-$code.html" || exit 1"""
        result = scan(fake, {})
        self.assertEqual(result["checked"], 0)
        self.assertEqual(result["excluded_dynamic"], 1)
        self.assertEqual(result["errors"], [])


if __name__ == "__main__":
    unittest.main()
