"""Verify source preflight is mandatory before any VPS rsync.

Run: python3 -m unittest scripts.test_publish_preflight_gate -v
"""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class PublishGateTests(unittest.TestCase):
    def test_offline_preflight_runs_before_transfer(self):
        script = (ROOT / "scripts/publish_app_discovery.sh").read_text(encoding="utf-8")
        check = "python3 scripts/preflight_app_discovery.py"
        self.assertEqual(script.count(check), 1)
        self.assertLess(script.index(check), script.index("rsync $rsync_flags"))
        self.assertIn('--dry-run) flags=(--dry-run)', script)
        self.assertIn('--apply) flags=()', script)

    def test_publish_does_not_deploy_on_source_preflight_error(self):
        script = (ROOT / "scripts/publish_app_discovery.sh").read_text(encoding="utf-8")
        self.assertIn("set -euo pipefail", script)
        self.assertIn("Missing source file:", script)
        self.assertIn("python3 required for safe publish preflight", script)
        self.assertNotIn("|| true", script)
        self.assertNotIn("rsync --delete", script)

    def test_preflight_is_explicitly_source_only(self):
        source = (ROOT / "scripts/preflight_app_discovery.py").read_text(encoding="utf-8")
        self.assertIn('"source_only": True', source)
        for forbidden in ("urlopen(", "subprocess.run(", "os.system(", "socket.connect("):
            self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
