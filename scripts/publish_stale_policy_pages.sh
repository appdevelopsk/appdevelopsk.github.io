#!/usr/bin/env bash
# Recover only the 17 PUBLIC policy pages flagged STALE (HTTP 200) by
# GitHub Actions 40608832623 on 2026-10-28. The app acquisition publisher
# deliberately does NOT cover privacy policies.
#
# --dry-run (default): safe rsync preview, no remote changes.
# --apply: user-owned VPS rsync, never deletes anything.
# --check-live: read-only compare of visible text on canonical HTTPS pages.
set -euo pipefail
cd "$(dirname "$0")/.."
mode="${1:---dry-run}"
case "$mode" in --dry-run|--apply|--check-live) ;; *)
  echo 'Usage: scripts/publish_stale_policy_pages.sh [--dry-run|--apply|--check-live]' >&2
  exit 2 ;;
esac
slugs=(
  battery-charging-map
  dinnerhomeroulette
  drift
  ear-train
  gratitude-log
  heritageatlas
  heritagetrace
  mood-log
  name-maker
  nowsnap
  posture-reminder
  rental-inspector
  smile-score
  solace
  tappitsu-battle
  wait-time
  water-reminder
)
files=()
for slug in "${slugs[@]}"; do
  path="privacy-policy/$slug/index.html"
  [[ -s "$path" ]] || { echo "Missing source file: $path" >&2; exit 2; }
  files+=("$path")
done

if [[ "$mode" == '--check-live' ]]; then
  tmp=$(mktemp)
  trap 'rm -f "$tmp"' EXIT
  ua='Mozilla/5.0 (compatible; SKAppsPolicyRecovery/1.0)'
  failed=0
  for file in "${files[@]}"; do
    url="https://appdevelopsk.com/${file%index.html}"
    code=$(curl -sSL --compressed -A "$ua" --max-time 20 --retry 2 --retry-delay 2 \
      -o "$tmp" -w '%{http_code}' "$url") || code=000
    if [[ "$code" != 200 ]]; then
      echo "FAIL HTTP $code $url" >&2
      failed=$((failed+1))
      continue
    fi
    if ! python3 - "$file" "$tmp" "$url" <<'PY'
import html, re, sys
def visible(path):
    with open(path, encoding="utf-8", errors="replace") as f:
        source = f.read()
    source = re.sub(r"<head[\s\S]*?</head>|<script[\s\S]*?</script>|<style[\s\S]*?</style>", " ", source, flags=re.I)
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", source))).strip()
if visible(sys.argv[1]) != visible(sys.argv[2]):
    print("FAIL STALE", sys.argv[3])
    sys.exit(1)
PY
    then
      failed=$((failed+1))
    else
      echo "PASS $url"
    fi
    sleep 0.35
  done
  echo "Checked ${#files[@]} public policy pages; failures: $failed"
  (( failed == 0 ))
  exit $?
fi

host="${APP_SITE_DEPLOY_HOST:-pickly-vps}"
root="${APP_SITE_DEPLOY_ROOT:-/var/www/html}"
if [[ ! "$host" =~ ^[a-zA-Z0-9_.@-]+$ || ! "$root" =~ ^/var/www/[a-zA-Z0-9_./-]+$ ]]; then
  echo 'Invalid APP_SITE_DEPLOY_HOST or APP_SITE_DEPLOY_ROOT' >&2
  exit 2
fi
flags=(--dry-run)
[[ "$mode" == '--apply' ]] && flags=()
echo "Policy recovery: ${#files[@]} already public paths, target $host:$root; mode $mode"
echo "Source checkout: $(git rev-parse --short HEAD 2>/dev/null || echo unknown)"
# Non-destructive. Never use --delete, and never publish unpublished paths.
rsync -avR --itemize-changes "${flags[@]}" -- "${files[@]}" "$host:$root/"
if [[ "$mode" == '--apply' ]]; then
  echo 'Upload attempted. Confirm live pages with:'
  echo '  bash scripts/publish_stale_policy_pages.sh --check-live'
fi
