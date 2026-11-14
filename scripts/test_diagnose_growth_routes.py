import unittest
from urllib.error import URLError
from scripts.diagnose_growth_routes import diagnose, origin_from_url, summarize_response

ORIGIN = "https://appdevelopsk.com"
BODY = b'<html><head><link rel="canonical" href="https://appdevelopsk.com/apps"><meta name="sk-growth-release" content="growth-20261106-wave2"></head></html>'


def fetched(url):
    path = url.removeprefix(ORIGIN)
    if path in ("/apps", "/apps.html"):
        return 200, ORIGIN + "/apps", BODY, {"Cache-Control": "max-age=30", "Age": "5"}
    return 200, url, b"ok", {}


class RouteDiagnosisTests(unittest.TestCase):
    def test_alias_redirect_equivalent(self):
        report = diagnose(ORIGIN, fetched)
        self.assertFalse(report["apps_alias_needs_review"])
        self.assertTrue(report["apps_aliases_equal"])
        self.assertTrue(report["apps_aliases_same_destination"])

    def test_alias_different_body_detected(self):
        def f(url):
            if url.endswith(".html"):
                return 200, url, b"old catalog", {"Age": "1200"}
            return fetched(url)
        report = diagnose(ORIGIN, f)
        self.assertTrue(report["apps_alias_needs_review"])
        self.assertNotEqual(report["pages"]["/apps"]["sha256"], report["pages"]["/apps.html"]["sha256"])

    def test_alias_error_detected(self):
        def f(url):
            if url.endswith(".html"):
                raise URLError("unavailable")
            return fetched(url)
        report = diagnose(ORIGIN, f)
        self.assertTrue(report["apps_alias_needs_review"])
        self.assertEqual(report["pages"]["/apps.html"]["error"], "URLError")

    def test_failed_status_not_equivalent(self):
        def f(url):
            if url.endswith(".html"):
                return 404, url, BODY, {}
            return fetched(url)
        report = diagnose(ORIGIN, f)
        self.assertTrue(report["apps_alias_needs_review"])

    def test_both_404_same_url_still_review(self):
        def f(url):
            return 404, ORIGIN + "/apps", b"missing", {}
        report = diagnose(ORIGIN, f)
        self.assertTrue(report["apps_alias_needs_review"])
        self.assertFalse(report["apps_aliases_same_destination"])

    def test_headers_public_and_lowercase(self):
        row = summarize_response(200, ORIGIN + "/apps", BODY, {"Cache-Control": "max-age=30", "Set-Cookie": "sensitive", "CF-Cache-Status": "HIT"})
        self.assertEqual(row["headers"], {"cache-control": "max-age=30", "cf-cache-status": "HIT"})
        self.assertEqual(row["canonical"], ORIGIN + "/apps")
        self.assertEqual(row["release"], "growth-20261106-wave2")
        self.assertNotIn("sensitive", repr(row))

    def test_invalid_origin(self):
        for url in ("file:///tmp", ORIGIN + "/apps", "https://u:p@host.com", ORIGIN + "/?x=1"):
            with self.subTest(url=url), self.assertRaises(ValueError):
                origin_from_url(url)

    def test_missing_release_marker(self):
        row = summarize_response(200, ORIGIN + "/apps", b"plain html", {})
        self.assertIsNone(row["release"])

    def test_alias_identical_body_not_false_alarm_if_url_differs(self):
        def f(url):
            if url.endswith(".html"):
                return 200, url, BODY, {}
            return fetched(url)
        report = diagnose(ORIGIN, f)
        self.assertFalse(report["apps_alias_needs_review"])
        self.assertFalse(report["apps_aliases_same_destination"])


if __name__ == "__main__":
    unittest.main()
