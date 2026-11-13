"""Read-only CI workflow contract for public app site release diagnostics."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "live-acquisition-smoke.yml"
SOURCE_FILES = (
    ROOT / "scripts" / "diagnose_growth_routes.py",
    ROOT / "scripts" / "diagnose_growth_deploy.py",
)


class LiveFailureInventoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.yaml = WORKFLOW.read_text(encoding="utf-8")

    def test_diagnostics_only_after_failed_public_smoke(self):
        source = self.yaml
        smoke = source.index("      - name: Check actual VPS HTTP pages")
        inventory = source.index("      - name: Inventory all stale public routes")
        upload = source.index("      - name: Attach machine-readable public route diagnostics")
        summary = source.index("      - name: Summarize release blockers and recovery")
        self.assertLess(smoke, inventory)
        self.assertLess(inventory, upload)
        self.assertLess(upload, summary)
        self.assertIn("if: failure()", source[inventory:upload])
        self.assertIn("if: failure()", source[upload:summary])

    def test_inventory_runs_only_existing_readonly_public_checkers(self):
        source = self.yaml.split("      - name: Inventory all stale public routes", 1)[1]
        block = source.split("      - name: Attach machine-readable public route diagnostics", 1)[0]
        self.assertIn("python3 scripts/diagnose_growth_routes.py --timeout 7 --output growth-route-diagnosis.json", block)
        self.assertIn("python3 scripts/diagnose_growth_deploy.py --timeout 7 --output growth-deploy-diagnosis.json", block)
        self.assertIn("GITHUB_STEP_SUMMARY", block)
        self.assertIn("press_routes_ready", block)
        self.assertIn("bytes_equal", block)
        for command in ("--apply", "workflow_dispatch", "rsync ", "git push", "indexnow", "curl --request POST"):
            self.assertNotIn(command, block)
        for path in SOURCE_FILES:
            self.assertTrue(path.exists(), str(path))

    def test_failures_are_not_masked_and_structured_logs_retained(self):
        source = self.yaml
        self.assertIn("bash scripts/check_app_discovery_live.sh", source)
        self.assertIn("actions/upload-artifact@v4", source)
        self.assertIn("appsite-live-route-inventory-", source)
        self.assertIn("growth-route-diagnosis.json", source)
        self.assertIn("growth-deploy-diagnosis.json", source)
        self.assertIn("retention-days: 7", source)
        self.assertNotIn("continue-on-error: true", source)

    def test_never_confuse_release_diagnostics_with_genuine_traffic(self):
        source = self.yaml
        self.assertIn("This diagnostic never deploys, requests indexing, posts to SNS or verifies GA4/store installs.", source)
        self.assertIn("Source/live HTML SHA-256 comparison (not exact release-SHA proof)", source)


if __name__ == "__main__":
    unittest.main()
