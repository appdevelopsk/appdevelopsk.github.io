#!/usr/bin/env python3
"""Read-only compare of fifteen deployed growth HTML pages against this checkout.

Exit 0 requires HTTP 200 and byte-identical HTML on all configured pages. Hosts
that rewrite HTML can cause false mismatches; inspect alongside growth smoke.
"""
import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen

SLUGS = ("debate-me", "brain-burst", "tappitsu-battle", "future-me", "twotaku", "instant-judge")
PAGE_FILES = {"/": "index.html", "/apps": "apps.html",
              "/guides/ai-debate-practice/": "guides/ai-debate-practice/index.html",
              "/guides/ai-debate-practice/ja/": "guides/ai-debate-practice/ja/index.html"}
PAGE_FILES.update({f"/support/{s}/": f"support/{s}/index.html" for s in SLUGS})
PAGE_FILES.update({"/press/": "press/index.html", "/press/es/": "press/es/index.html", "/press/pt-br/": "press/pt-br/index.html", "/press/ja/": "press/ja/index.html", "/press/id/": "press/id/index.html"})
STAMP = re.compile(rb'<meta\s+name="sk-growth-release"\s+content="([^"]+)"')


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def stamp(data):
    values = [m.decode("utf-8", "replace") for m in STAMP.findall(data)]
    return values[0] if len(values) == 1 else None


def compare(local, remote, error=None, status=None):
    """Pure comparison; report hashes, never page body or user data."""
    return {
        "local_sha256": sha256(local),
        "live_sha256": sha256(remote) if remote is not None else None,
        "local_release": stamp(local),
        "live_release": stamp(remote) if remote is not None else None,
        "http_status": status,
        "bytes_equal": (status == 200 and remote == local) if remote is not None else False,
        "error": error,
    }


def inspect(root, fetch):
    """fetch(path) -> (bytes, HTTP status); failures stay explicit."""
    results = {}
    for path, filename in PAGE_FILES.items():
        try:
            local = (Path(root) / filename).read_bytes()
        except OSError as exc:
            results[path] = {"error": f"local file unavailable: {type(exc).__name__}", "bytes_equal": False}
            continue
        try:
            live, status = fetch(path)
            if status != 200:
                results[path] = compare(local, live, f"HTTP {status}", status)
            else:
                results[path] = compare(local, live, status=status)
        except (HTTPError, URLError, TimeoutError, OSError, ValueError) as exc:
            results[path] = compare(local, None, type(exc).__name__)
    identical = sum(v["bytes_equal"] for v in results.values())
    return {
        "all_identical": identical == len(PAGE_FILES),
        "identical_pages": identical,
        "checked_pages": len(PAGE_FILES),
        "pages": results,
        "interpretation": (
            "Byte mismatch may be host transformation, stale cache or different deploy. "
            "Release markers are milestone labels, not per-commit hashes. "
            "Passing this test does not verify JavaScript, GA4 or installs."
        ),
    }


def fetcher(base_url, timeout):
    parsed = urlparse(base_url)
    if (parsed.scheme not in ("http", "https") or not parsed.netloc or parsed.username or parsed.password or parsed.path not in ("", "/") or parsed.query or parsed.fragment):
        raise ValueError("--base-url must be an http(s) site origin without userinfo")
    base = parsed.scheme + "://" + parsed.netloc + "/"

    def fetch(path):
        request = Request(urljoin(base, path.lstrip("/")), headers={"User-Agent": "SKAppsDeployCompare/1.0"})
        with urlopen(request, timeout=timeout) as response:
            return response.read(3_000_000), response.status
    return fetch


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="https://appdevelopsk.com")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parent.parent)
    parser.add_argument("--timeout", type=float, default=10)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.timeout <= 0:
        parser.error("--timeout must be positive")
    try:
        result = inspect(args.root, fetcher(args.base_url, args.timeout))
    except ValueError as exc:
        parser.error(str(exc))
    payload = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.write_text(payload, encoding="utf-8")
    else:
        print(payload, end="")
    return 0 if result["all_identical"] else 1


if __name__ == "__main__":
    sys.exit(main())
