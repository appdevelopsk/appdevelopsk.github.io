"""Offline tests for owner-controlled, no-credentials VPS release ZIP."""
import hashlib
import re
import shutil
import tempfile
import unittest
import zipfile
from pathlib import Path

from scripts import build_site_release_bundle as bundle


class AppsiteReleaseBundleTests(unittest.TestCase):
    def test_exact_publish_manifest_has_five_press_and_seventeen_policies(self):
        files = bundle.release_manifest()
        self.assertEqual(len(files), 46)
        self.assertEqual(len(files), len(set(files)))
        self.assertTrue(bundle.PRESS.issubset(files))
        for guide in ("guides/ai-debate-practice/index.html",
                      "guides/ai-debate-practice/ja/index.html"):
            self.assertIn(guide, files, "published sitemap entry missing from release ZIP")

        self.assertEqual(sum(x.startswith("privacy-policy/") for x in files), 17)
        self.assertNotIn(".env", "\n".join(files))
        self.assertFalse(any(".." in Path(x).parts or "." in Path(x).parts for x in files))

    def test_zip_contains_exact_site_payload_with_matching_checksum_file(self):
        files = bundle.release_manifest()
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "appsite.zip"
            digest = bundle.zip_bytes(bundle.ROOT, files, output)
            self.assertEqual(digest, hashlib.sha256(output.read_bytes()).hexdigest())
            with zipfile.ZipFile(output) as z:
                expected = {"site/" + f for f in files} | {"SHA256SUMS.txt", "DEPLOY_README.txt"}
                self.assertEqual(set(z.namelist()), expected)
                self.assertEqual(z.testzip(), None)
                hashes = {}
                for line in z.read("SHA256SUMS.txt").decode().splitlines():
                    checksum, name = line.split("  ", 1)
                    self.assertNotIn(name, hashes)
                    hashes[name] = checksum
                self.assertEqual(set(hashes), {"site/" + f for f in files})
                for name, checksum in hashes.items():
                    with self.subTest(name=name):
                        self.assertEqual(hashlib.sha256(z.read(name)).hexdigest(), checksum)
                        self.assertEqual(z.read(name), (bundle.ROOT / name.removeprefix("site/")).read_bytes())
                readme = z.read("DEPLOY_README.txt").decode()
                self.assertIn("source-only", readme)
                self.assertIn("mode=dry-run", readme)
                self.assertIn("mode=apply", readme)
                self.assertIn("Do not add --delete", readme)

    def test_publisher_slug_path_traversal_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "scripts").mkdir()
            for filename in (bundle.APP_PUBLISHER, bundle.POLICY_PUBLISHER):
                shutil.copy2(bundle.ROOT / filename, root / filename)
            old = (root / bundle.POLICY_PUBLISHER).read_text()
            self.assertIn("battery-charging-map", old)
            (root / bundle.POLICY_PUBLISHER).write_text(
                old.replace("battery-charging-map", "../outside", 1))
            with self.assertRaises(ValueError):
                bundle.release_manifest(root)

    def test_any_missing_press_route_fails_before_archive(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "scripts").mkdir()
            for filename in (bundle.APP_PUBLISHER, bundle.POLICY_PUBLISHER):
                shutil.copy2(bundle.ROOT / filename, root / filename)
            script = root / bundle.APP_PUBLISHER
            text = script.read_text()
            self.assertIn("press/id/index.html", text)
            script.write_text(text.replace("press/id/index.html",
                                           "press/nonexistent/index.html", 1))
            with self.assertRaises(ValueError):
                bundle.release_manifest(root)

    def test_archive_builder_never_needs_vps_or_credentials(self):
        source = (bundle.ROOT / "scripts/build_site_release_bundle.py").read_text()
        # Deployment instructions (README) legitimately mention SSH and rsync;
        # only the executable packaging code must be free of network commands.
        executable = source.split("def shell_array", 1)[1]
        self.assertNotIn("subprocess", executable)
        self.assertNotIn("urllib.request", executable)
        self.assertNotIn("ssh ", executable)
        self.assertNotIn("rsync -", executable)
        self.assertNotIn("os.system", executable)
        self.assertNotIn("eval(", executable)
        self.assertIn("publishesToVps", executable)


if __name__ == "__main__":
    unittest.main()
