"""Static regression tests for multilingual press/creator landing pages.

Run: python3 -m unittest scripts.test_press_kit -v
Offline only. This does not verify production hosting or actual Play availability.
"""
from html.parser import HTMLParser
from pathlib import Path
from xml.etree import ElementTree
import unittest

ROOT = Path(__file__).resolve().parents[1]
PAGES = {
    "en": ("press/index.html", "https://appdevelopsk.com/press/"),
    "es": ("press/es/index.html", "https://appdevelopsk.com/press/es/"),
    "pt-BR": ("press/pt-br/index.html", "https://appdevelopsk.com/press/pt-br/"),
    "ja": ("press/ja/index.html", "https://appdevelopsk.com/press/ja/"),
    "id": ("press/id/index.html", "https://appdevelopsk.com/press/id/"),
}
PACKAGES = {
    "blur": "com.blurapp.blur_app",
    "twotaku": "com.dotchi.dotchi_app",
    "instant-judge": "com.instantjudge.instant_judge",
    "debate-me": "jp.appdevelopsk.debate_me",
    "future-me": "com.futureme.future_me",
}

class Tags(HTMLParser):
    def __init__(self):
        super().__init__()
        self.attrs = []
    def handle_starttag(self, tag, attrs):
        self.attrs.append((tag, dict(attrs)))

class PressKitTests(unittest.TestCase):
    def test_all_locales_and_store_destinations(self):
        for locale, (source, canonical) in PAGES.items():
            with self.subTest(locale=locale):
                html = (ROOT / source).read_text(encoding="utf-8")
                doc = Tags()
                doc.feed(html)
                self.assertIn(("html", {"lang": locale}), [item for item in doc.attrs if item[0]=="html"])
                self.assertEqual(sum(tag=="h1" for tag, _ in doc.attrs), 1)
                self.assertEqual(sum(tag=="article" for tag, _ in doc.attrs), 5)
                links = [attrs for tag, attrs in doc.attrs if tag=="link"]
                self.assertEqual([x["href"] for x in links if x.get("rel")=="canonical"], [canonical])
                actual = {x["hreflang"]:x["href"] for x in links if x.get("rel")=="alternate"}
                self.assertEqual(actual, {**{k:v[1] for k,v in PAGES.items()}, "x-default":PAGES["en"][1]})
                anchors = [x.get("href","") for tag, x in doc.attrs if tag=="a"]
                for slug, package in PACKAGES.items():
                    self.assertTrue((ROOT / "support" / slug / "index.html").is_file(), slug)
                    self.assertTrue(any(f"/support/{slug}/" in h for h in anchors), slug)
                    self.assertIn(f"https://play.google.com/store/apps/details?id={package}", anchors)
                    tracked = [a for tag,a in doc.attrs if tag=="a" and a.get("data-app-slug")==slug]
                    self.assertEqual(len(tracked), 2, slug)
                    self.assertEqual({a.get("data-cta") for a in tracked}, {"details", "store"})
                    self.assertEqual({a.get("data-app-package") for a in tracked}, {package})
                self.assertIn("/apps", anchors)
                self.assertNotIn("utm_source=presskit", html, "Internal UTMs would reset acquisition attribution")
                self.assertIn("press_app_click", html)
                self.assertEqual(sum(x.get("data-cta")=="store" for tag,x in doc.attrs if tag=="a"), 5)
                self.assertEqual(sum(tag=="a" and attrs.get("lang") in PAGES for tag,attrs in doc.attrs), len(PAGES))

    def test_press_pages_in_manual_vps_publish_manifest(self):
        script = (ROOT / "scripts" / "publish_app_discovery.sh").read_text(encoding="utf-8")
        self.assertIn("mode=\"\u0024{1:---dry-run}\"", script)
        self.assertNotIn(" --delete", script)
        manifest = script.split("files=(", 1)[1].split(")", 1)[0].split()
        self.assertEqual(len(manifest), len(set(manifest)))
        for source, _ in PAGES.values():
            with self.subTest(source=source):
                self.assertIn(source, manifest)

    def test_live_smoke_checks_all_press_locales_and_latest_support(self):
        smoke = (ROOT / "scripts" / "check_app_discovery_live.sh").read_text(encoding="utf-8")
        for code in ("en", "es", "pt-br", "ja", "id"):
            self.assertIn("press-" + code + ".html", smoke)
        self.assertIn("BrainBurst: Daily Trivia & 1v1 Quiz Battles | Android", smoke)
        self.assertIn("Debate Me: AI Debate Practice App for Android | SK APPS", smoke)
        self.assertNotIn("Debate Me – Free AI Debate App for Android | SK APPS", smoke)

    def test_homepage_and_sitemap_discoverable(self):
        homepage = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn('href="/press/"', homepage)
        root = ElementTree.parse(ROOT / "sitemap.xml").getroot()
        locs = {node.text for node in root.findall("{http://www.sitemaps.org/schemas/sitemap/0.9}url/{http://www.sitemaps.org/schemas/sitemap/0.9}loc")}
        for _, url in PAGES.values():
            self.assertIn(url, locs)

if __name__ == "__main__":
    unittest.main()
