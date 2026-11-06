#!/usr/bin/env python3
"""Read-only inspect public /apps URL aliases and core growth endpoints.

Does not assert which hosting provider owns the domain. Does not purge caches.
"""
import argparse
import hashlib
import json
import re
import sys
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit, urlunsplit
from urllib.request import Request, urlopen

PATHS = ("/apps", "/apps.html", "/support/twotaku/", "/robots.txt", "/sitemap.xml")
HEADERS = ("cache-control", "age", "cf-cache-status", "x-cache", "etag", "last-modified", "server")
CANONICAL = re.compile(r'<link\s+rel="canonical"\s+href="([^"]+)"', re.I)
RELEASE = re.compile(r'<meta\s+name="sk-growth-release"\s+content="([^"]+)"', re.I)


def origin_from_url(url):
    parts = urlsplit(url)
    if parts.scheme not in ("https", "http") or not parts.hostname or parts.username or parts.password or parts.query or parts.fragment or parts.path not in ("", "/"):
        raise ValueError("Base URL must be an HTTP(S) origin with no path, credentials or query")
    return urlunsplit((parts.scheme, parts.netloc, "", "", ""))


def summarize_response(status, final_url, body, headers):
    """Return public diagnostics only, without HTML or user data."""
    text = body.decode("utf-8", "replace")
    canonical = CANONICAL.findall(text)
    releases = RELEASE.findall(text)
    normalized_headers = {k.lower(): str(v) for k, v in headers.items()}
    return {
        "status": status,
        "final_url": final_url,
        "sha256": hashlib.sha256(body).hexdigest(),
        "bytes": len(body),
        "canonical": canonical[0] if len(canonical) == 1 else None,
        "release": releases[0] if len(releases) == 1 else None,
        "headers": {key: normalized_headers[key] for key in HEADERS if key in normalized_headers},
    }


def diagnose(origin, fetch):
    rows = {}
    for path in PATHS:
        url = origin + path
        try:
            status, final_url, body, headers = fetch(url)
            rows[path] = summarize_response(status, final_url, body, headers)
        except (HTTPError, URLError, TimeoutError, OSError, ValueError) as exc:
            rows[path] = {"error": type(exc).__name__, "status": getattr(exc, "code", None)}
    a, b = rows["/apps"], rows["/apps.html"]
    same_body = bool(a.get("status") == 200 and b.get("status") == 200 and a.get("sha256") == b.get("sha256"))
    same_destination = bool(a.get("status") == 200 and b.get("status") == 200 and
                            a.get("final_url") and a.get("final_url") == b.get("final_url"))
    alias_problem = not (same_body or same_destination)
    return {
        "origin": origin,
        "pages": rows,
        "apps_aliases_equal": same_body,
        "apps_aliases_same_destination": same_destination,
        "apps_alias_needs_review": alias_problem,
        "limitations": "HTTP responses may vary by cache, compression or locale; inspect provider deployments before changing routing or DNS. No JS or GA4 validation.",
    }


def network_fetch(url, timeout):
    req = Request(url, headers={"User-Agent": "SKAppsReadOnlyReleaseDiagnostic/1.0", "Cache-Control": "no-cache"})
    try:
        with urlopen(req, timeout=timeout) as res:
            return res.status, res.url, res.read(3_000_000), dict(res.headers.items())
    except HTTPError as exc:
        return exc.code, exc.url, exc.read(300_000), dict(exc.headers.items())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="https://appdevelopsk.com")
    parser.add_argument("--timeout", type=float, default=12)
    parser.add_argument("--output")
    args = parser.parse_args()
    if args.timeout <= 0:
        parser.error("--timeout must be positive")
    try:
        origin = origin_from_url(args.base_url)
    except ValueError as exc:
        parser.error(str(exc))
    result = diagnose(origin, lambda url: network_fetch(url, args.timeout))
    payload = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        with open(args.output, "w", encoding="utf-8") as fp:
            fp.write(payload)
    else:
        print(payload, end="")
    return 1 if result["apps_alias_needs_review"] else 0


if __name__ == "__main__":
    sys.exit(main())
