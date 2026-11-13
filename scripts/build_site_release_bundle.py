#!/usr/bin/env python3
"""Build a portable, read-only appdevelopsk.com VPS release bundle.

This script packages ONLY the exact files allowed by the existing owner-only
app discovery and privacy-policy publishing scripts. It never touches a VPS,
changes a GitHub branch, sends events, or requires SSH/network access.

Usage:
    python3 scripts/build_site_release_bundle.py --output /tmp/appsite-release.zip
"""
import argparse
import hashlib
import json
import re
import shlex
import sys
import zipfile
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
APP_PUBLISHER = "scripts/publish_app_discovery.sh"
POLICY_PUBLISHER = "scripts/publish_stale_policy_pages.sh"
PRESS = {
    "press/index.html",
    "press/es/index.html",
    "press/pt-br/index.html",
    "press/ja/index.html",
    "press/id/index.html",
}
MAX_FILE_BYTES = 5_000_000
MAX_TOTAL_BYTES = 25_000_000
README = """APP SITE — OWNER-CONTROLLED RELEASE BUNDLE

This ZIP is source-only. Creating or downloading it does NOT publish a site.
The root-level site/ directory preserves paths relative to the VPS web root.
SHA256SUMS.txt verifies the exact bytes included; it is not a deployed SHA.

PREFERRED RELEASE:
  GitHub Actions -> publish to VPS -> main -> mode=dry-run; review.
  The owner may then authorize a separate mode=apply on the self-hosted VPS
  runner. Do NOT use this bundle to bypass a failed source preflight.

ALTERNATIVE WHEN THE SELF-HOSTED RUNNER IS UNAVAILABLE:
  1. Extract this ZIP into a private temporary directory on a trusted computer.
  2. From that extracted directory, run:
       sha256sum -c SHA256SUMS.txt
  3. Owner verifies the SSH host/user, web-root path and exact file list.
  4. Owner uploads only its site/ contents with their relative directories:
       rsync -rlcv --itemize-changes -- site/ USER@VPS:/var/www/html/
     Do not add --delete. Do not blindly copy files to an unverified host.
  5. Run source post-release read-only probes:
       bash scripts/check_app_discovery_live.sh
       bash scripts/publish_stale_policy_pages.sh --check-live
  6. Confirm all five /press/ locale routes return HTTP 200 on
     https://appdevelopsk.com and the expected canonical/hreflang, then
     check the public app catalog and support landing metadata.

This includes 27 app-discovery documents and 17 approved policy documents
from current source. It is NOT a complete VPS backup, nginx configuration,
database migration, browser test, app-store release, or SEO indexing proof.
"""


def shell_array(text, name):
    if name == "files":
        pattern = r"(?m)^files=\(([^)\n]*)\)\s*$"
    elif name == "slugs":
        pattern = r"(?ms)^slugs=\(\s*(.*?)^\)\s*$"
    else:
        raise ValueError("unsupported manifest variable")
    found = re.findall(pattern, text)
    if len(found) != 1:
        raise ValueError("expected exactly one explicit " + name + "=(...) manifest")
    parts = shlex.split(found[0], comments=True)
    if not parts or len(parts) != len(set(parts)):
        raise ValueError(name + " manifest is empty or has duplicate entries")
    return parts


def release_manifest(root=ROOT):
    scripts = root / "scripts"
    apps = shell_array((scripts / "publish_app_discovery.sh").read_text(encoding="utf-8"), "files")
    policies = shell_array((scripts / "publish_stale_policy_pages.sh").read_text(encoding="utf-8"), "slugs")
    if len(apps) != 27 or len(policies) != 17:
        raise ValueError("publisher manifest count changed; review before bundling")
    if not PRESS.issubset(set(apps)):
        raise ValueError("one or more of the five press routes are not in publisher manifest")
    if not {"index.html", "apps.html", "sitemap.xml", "robots.txt",
            "support/brain-burst/index.html", "support/debate-me/index.html"}.issubset(apps):
        raise ValueError("critical app discovery/SEO pages missing from publisher manifest")
    if any(not re.fullmatch(r"[a-z0-9-]+", slug) for slug in policies):
        raise ValueError("unsafe privacy-policy slug")
    files = apps + ["privacy-policy/" + slug + "/index.html" for slug in policies]
    if len(files) != len(set(files)):
        raise ValueError("publisher allowlists overlap")
    total = 0
    for filename in files:
        path = PurePosixPath(filename)
        if (path.is_absolute() or ".." in path.parts or "." in path.parts
                or path.as_posix() != filename or "\\" in filename):
            raise ValueError("unsafe release path: " + filename)
        actual = root / filename
        if (not actual.is_file() or actual.is_symlink()
                or not actual.resolve().is_relative_to(root.resolve())):
            raise ValueError("missing or unsafe source file: " + filename)
        size = actual.stat().st_size
        if size <= 0 or size > MAX_FILE_BYTES:
            raise ValueError("missing, empty or oversized source file: " + filename)
        total += size
    if total > MAX_TOTAL_BYTES:
        raise ValueError("release is too large for the reviewed source-only bundle")
    return files


def zip_bytes(root, files, out):
    out.parent.mkdir(parents=True, exist_ok=True)
    checksum_rows = []
    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED,
                         compresslevel=6) as archive:
        for filename in sorted(files):
            content = (root / filename).read_bytes()
            source = "site/" + filename
            archive.writestr(source, content)
            checksum_rows.append(hashlib.sha256(content).hexdigest() + "  " + source)
        archive.writestr("SHA256SUMS.txt", "\n".join(checksum_rows) + "\n")
        archive.writestr("DEPLOY_README.txt", README)
    return hashlib.sha256(out.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path,
                        help="Local output .zip path; never a production web root")
    args = parser.parse_args()
    if args.output.suffix.lower() != ".zip":
        parser.error("--output must be a .zip filename")
    output = args.output.resolve()
    if output.is_relative_to(ROOT) and output.parent == ROOT:
        parser.error("do not create ZIP at public website root")
    try:
        files = release_manifest(ROOT)
        digest = zip_bytes(ROOT, files, output)
    except (OSError, ValueError, zipfile.BadZipFile) as exc:
        print(type(exc).__name__ + ": " + str(exc), file=sys.stderr)
        return 1
    print(json.dumps({
        "status": "source_bundle_created_not_deployed",
        "output": str(output),
        "sha256": digest,
        "appDiscoveryFiles": 27,
        "policyFiles": 17,
        "totalFiles": len(files),
        "pressRoutes": sorted(PRESS),
        "publishesToVps": False,
        "urlIndexingRequested": False,
    }, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
