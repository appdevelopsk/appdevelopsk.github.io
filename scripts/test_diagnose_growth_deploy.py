"""Offline deployment diagnosis tests: no network calls."""
import tempfile
import unittest
from pathlib import Path
from diagnose_growth_deploy import PAGE_FILES, compare, fetcher, inspect, stamp


class DeploymentDiagnosisTests(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.dir.cleanup)
        self.root = Path(self.dir.name)
        self.contents = {}
        for page, file in PAGE_FILES.items():
            data = (f'<html><head><meta name="sk-growth-release" content="r1"></head><body>{page}</body></html>').encode()
            self.contents[page] = data
            dest = self.root / file
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(data)

    def test_same_pages_pass(self):
        result = inspect(self.root, lambda p: (self.contents[p], 200))
        self.assertTrue(result['all_identical'])
        self.assertEqual(result['identical_pages'], 7)

    def test_one_stale_page_fails(self):
        result = inspect(self.root, lambda p: (b'old' if p == '/apps' else self.contents[p], 200))
        self.assertFalse(result['all_identical'])
        self.assertEqual(result['identical_pages'], 6)
        self.assertEqual(result['pages']['/apps']['live_sha256'], compare(b'old', b'old')['live_sha256'])

    def test_fetch_failure_is_not_success(self):
        def fetch(p):
            if p == '/support/twotaku/':
                raise TimeoutError('timeout')
            return self.contents[p], 200
        result = inspect(self.root, fetch)
        self.assertFalse(result['all_identical'])
        self.assertEqual(result['pages']['/support/twotaku/']['error'], 'TimeoutError')

    def test_non_200_is_not_success_even_if_bytes_match(self):
        result = inspect(self.root, lambda p: (self.contents[p], 404 if p == '/apps' else 200))
        self.assertFalse(result['all_identical'])
        self.assertEqual(result['pages']['/apps']['http_status'], 404)

    def test_missing_local_file_is_reported(self):
        (self.root / 'apps.html').unlink()
        result = inspect(self.root, lambda p: (self.contents[p], 200))
        self.assertFalse(result['all_identical'])
        self.assertIn('local file unavailable', result['pages']['/apps']['error'])

    def test_markers_are_not_commits(self):
        self.assertEqual(stamp(self.contents['/']), 'r1')
        self.assertIsNone(stamp(b'<html>no marker</html>'))
        self.assertIsNone(stamp(b'<meta name="sk-growth-release" content="a"><meta name="sk-growth-release" content="b">'))

    def test_base_url_rejects_invalid_origin(self):
        for url in ('file:///tmp/test', 'https://user:pass@example.com', 'not-a-url'):
            with self.subTest(url=url), self.assertRaises(ValueError):
                fetcher(url, 5)


if __name__ == '__main__':
    unittest.main()
