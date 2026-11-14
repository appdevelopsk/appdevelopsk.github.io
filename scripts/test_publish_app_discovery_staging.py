"""Offline deployment-layout tests for the exact manual appsite rsync manifest.

These tests DO NOT contact or publish to appdevelopsk.com or a VPS.
Requires the rsync binary shipped with GitHub's ubuntu-latest runner.

Run: python3 -m unittest scripts.test_publish_app_discovery_staging -v
"""
import re
import shlex
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
PUBLISH = ROOT / "scripts" / "publish_app_discovery.sh"
PRESS = {
    "press/index.html",
    "press/es/index.html",
    "press/pt-br/index.html",
    "press/ja/index.html",
    "press/id/index.html",
}


def manifest():
    script = PUBLISH.read_text(encoding="utf-8")
    match = re.search(r"(?m)^files=\(([^)]*)\)$", script)
    if match is None:
        raise AssertionError("Publisher's explicit files=(...) manifest was not found")
    paths = shlex.split(match.group(1))
    if not paths or len(paths) != len(set(paths)):
        raise AssertionError("Publisher has no paths, or duplicates")
    for filename in paths:
        value = PurePosixPath(filename)
        if value.is_absolute() or ".." in value.parts or str(value) != filename:
            raise AssertionError("Unsafe source path: " + filename)
        if not (ROOT / filename).is_file():
            raise AssertionError("Missing checked-in release file: " + filename)
    return paths


def rsync_to(directory, paths, dry_run=False):
    if shutil.which("rsync") is None:
        raise AssertionError("rsync is required to prove the VPS staging layout")
    cmd = ["rsync", "-rlcvR", "--itemize-changes"]
    if dry_run:
        cmd += ["--dry-run"]
    cmd += ["--", *paths, str(directory) + "/"]
    return subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True, check=True)


class AppPublishStagingTests(unittest.TestCase):
    def test_real_relative_rsync_layout_matches_exact_allowlist(self):
        paths = manifest()
        self.assertTrue(PRESS.issubset(set(paths)), "Every press locale must deploy")
        self.assertIn("apps.html", paths)
        self.assertIn("support/brain-burst/index.html", paths)
        self.assertIn("guides/ai-debate-practice/index.html", paths)
        self.assertIn("guides/ai-debate-practice/ja/index.html", paths)
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "www"
            dest.mkdir()
            rsync_to(dest, paths)
            actual = {
                p.relative_to(dest).as_posix()
                for p in dest.rglob("*") if p.is_file()
            }
            self.assertEqual(actual, set(paths))
            for filename in paths:
                with self.subTest(filename=filename):
                    self.assertEqual((dest / filename).read_bytes(),
                                     (ROOT / filename).read_bytes())
            self.assertFalse(any(p.is_symlink() for p in dest.rglob("*")))

    def test_dry_run_never_copies_any_published_page(self):
        paths = manifest()
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "www"
            dest.mkdir()
            preview = rsync_to(dest, paths, dry_run=True)
            self.assertEqual(list(dest.iterdir()), [])
            self.assertIn("press/", preview.stdout)

    def test_production_script_is_opt_in_and_non_destructive(self):
        script = PUBLISH.read_text(encoding="utf-8")
        self.assertIn('mode="${1:---dry-run}"', script)
        self.assertIn("python3 scripts/preflight_app_discovery.py", script)
        lines = [s.strip() for s in script.splitlines()
                 if s.lstrip().startswith("rsync $rsync_flags")]
        self.assertEqual(len(lines), 1)
        self.assertNotIn("--delete", lines[0])
        self.assertNotIn("--remove-source-files", lines[0])
        self.assertIn('"${files[@]}"', lines[0])
        self.assertIn("APP_SITE_DEPLOY_ROOT", script)
        self.assertIn('dest="$root/"', script)
        self.assertFalse(any(x.startswith("privacy-policy/") for x in manifest()))


if __name__ == "__main__":
    unittest.main()
