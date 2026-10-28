#!/usr/bin/env bash
# Publish *only* the app-discovery growth files to the VPS backing appdevelopsk.com.
# Default is a non-destructive dry-run. --apply is an intentional human action.
set -euo pipefail
cd "$(dirname "$0")/.."
mode="${1:---dry-run}"
case "$mode" in
  --dry-run) flags=(--dry-run) ;;
  --apply) flags=() ;;
  *) echo 'Usage: scripts/publish_app_discovery.sh [--dry-run|--apply]' >&2; exit 2 ;;
esac
host="${APP_SITE_DEPLOY_HOST:-pickly-vps}"
root="${APP_SITE_DEPLOY_ROOT:-/var/www/html}"
# Never evaluate an arbitrary SSH target or remote shell path.
if [[ ! "$host" =~ ^[a-zA-Z0-9_.@-]+$ || ! "$root" =~ ^/var/www/[a-zA-Z0-9_./-]+$ ]]; then
  echo 'Invalid APP_SITE_DEPLOY_HOST or APP_SITE_DEPLOY_ROOT' >&2; exit 2
fi
files=(index.html apps.html sitemap.xml robots.txt guides/quick-games/index.html guides/daily-habits/index.html guides/decision-helpers/index.html guides/ai-tools/index.html support/brain-burst/index.html support/snaplingo/index.html support/face-reaction-battle/index.html support/twotaku/index.html support/debate-me/index.html support/idea-market/index.html support/blur/index.html support/instant-judge/index.html support/roast-me/index.html support/future-me/index.html)
for file in "${files[@]}"; do
  [[ -s "$file" ]] || { echo "Missing source file: $file" >&2; exit 2; }
done
echo "Source checkout: $(git rev-parse --short HEAD 2>/dev/null || echo unknown)"
echo "Target: $host:$root; mode: $mode"
# --relative recreates only the listed nested file paths. No --delete.
# On the self-hosted runner (APP_SITE_DEPLOY_HOST=local) copy straight into the web root.
dest="$host:$root/"; [[ "$host" == local ]] && dest="$root/"
# Runner is a non-root user: it cannot chown/utime, so the workflow overrides the flags.
rsync_flags="${APP_SITE_RSYNC_FLAGS:--avR --itemize-changes}"
# shellcheck disable=SC2086
rsync $rsync_flags ${flags[@]+"${flags[@]}"} -- "${files[@]}" "$dest"
if [[ "$mode" == '--apply' ]]; then
  echo 'Files transferred. Check CDN/VPS output (the publish command does not prove it is live):'
  echo '  bash scripts/check_app_discovery_live.sh'
fi
