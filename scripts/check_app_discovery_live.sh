#!/usr/bin/env bash
# Read-only production smoke. Run after the VPS rsync; no deploy or credentials.
set -euo pipefail
base="${APP_SITE_PUBLIC_BASE:-https://appdevelopsk.com}"
[[ "$base" == 'https://appdevelopsk.com' ]] || { echo 'Expected canonical https://appdevelopsk.com' >&2; exit 2; }
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
ua='Mozilla/5.0 (compatible; SKAppsGrowthCheck/1.0)'
fetch() {
  local route="$1" filename="$2"
  local code
  code=$(curl -sSL --compressed -A "$ua" --max-time 20 --retry 2 --retry-delay 2 \
    -o "$tmp/$filename" -w '%{http_code}' "$base$route")
  [[ "$code" == 200 ]] || { echo "FAIL HTTP $code $base$route" >&2; exit 1; }
}
fetch '/apps' 'apps.html'
grep -Fq 'id="find-app"' "$tmp/apps.html" || { echo 'FAIL catalog search is stale' >&2; exit 1; }
grep -Fq 'catalog_store_click' "$tmp/apps.html" || { echo 'FAIL store-click attribution is stale' >&2; exit 1; }
for slug in quick-games daily-habits; do
  fetch "/guides/$slug/" "$slug.html"
  grep -Fq "https://appdevelopsk.com/guides/$slug/" "$tmp/$slug.html" || { echo "FAIL guide $slug content/canonical mismatch" >&2; exit 1; }
  grep -Fq 'guide_store_click' "$tmp/$slug.html" || { echo "FAIL $slug click measurement missing" >&2; exit 1; }
done
fetch '/sitemap.xml' 'sitemap.xml'
for slug in quick-games daily-habits; do
  grep -Fq "https://appdevelopsk.com/guides/$slug/" "$tmp/sitemap.xml" || { echo "FAIL sitemap missing $slug" >&2; exit 1; }
done
echo 'PASS: VPS catalog, two guides, click-tracking markers and sitemap all current (HTTP 200)'
