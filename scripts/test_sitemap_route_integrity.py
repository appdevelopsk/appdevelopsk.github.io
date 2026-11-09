"""Offline sitemap integrity checks for published static routes.

Run: python3 -m unittest scripts/test_sitemap_route_integrity.py -v
No network or store API requests are performed.
"""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit, unquote
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent.parent
ORIGIN = "https://appdevelopsk.com"
NS = "{http://www.sitemaps.org/schemas/sitemap/0.9}"


class CanonicalParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.values = []

    def handle_starttag(self, tag, attrs):
        if tag != "link":
            return
        values = dict(attrs)
        if (values.get("rel") or "").lower() == "canonical":
            self.values.append(values.get("href", ""))


def listed_urls():
    root = ET.parse(ROOT / "sitemap.xml").getroot()
    if root.tag != NS + "urlset":
        raise ValueError("Not a sitemap urlset")
    return [el.findtext(NS + "loc") for el in root.findall(NS + "url")]


def resolve_source(url):
    if not isinstance(url, str):
        raise ValueError(f"Missing loc: {url!r}")
    parsed = urlsplit(url)
    if f"{parsed.scheme}://{parsed.netloc}" != ORIGIN or parsed.query or parsed.fragment:
        raise ValueError(f"Unexpected sitemap URL: {url}")
    path = unquote(parsed.path)
    if ".." in Path(path).parts or "\\" in path:
        raise ValueError(f"Unsafe sitemap path: {url}")
    if path == "/":
        return ROOT / "index.html"
    relative = path.lstrip("/")
    if path.endswith("/"):
        return ROOT / relative / "index.html"
    return ROOT / (relative + ".html")


class SitemapRouteIntegrityTests(unittest.TestCase):
    def test_every_sitemap_route_has_a_real_source(self):
        urls = listed_urls()
        self.assertEqual(len(urls), len(set(urls)), "duplicate sitemap <loc>")
        for url in urls:
            with self.subTest(url=url):
                self.assertTrue(resolve_source(url).is_file(), f"missing HTML for {url}")

    def test_all_sitemap_pages_have_exact_self_canonical(self):
        for url in listed_urls():
            with self.subTest(url=url):
                parser = CanonicalParser()
                parser.feed(resolve_source(url).read_text(encoding="utf-8"))
                self.assertEqual(parser.values, [url],
                                 f"canonical mismatch for {url}")


if __name__ == "__main__":
    unittest.main()
