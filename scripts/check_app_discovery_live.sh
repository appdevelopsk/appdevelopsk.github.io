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
fetch '/' 'index.html'
grep -Fq 'class="discovery-links"' "$tmp/index.html" || { echo 'FAIL homepage discovery links are stale' >&2; exit 1; }
grep -Fq 'discovery_nav_click' "$tmp/index.html" || { echo 'FAIL homepage discovery tracking is stale' >&2; exit 1; }
fetch '/apps' 'apps.html'
grep -Fq 'id="find-app"' "$tmp/apps.html" || { echo 'FAIL catalog search is stale' >&2; exit 1; }
grep -Fq 'catalog_store_click' "$tmp/apps.html" || { echo 'FAIL store-click attribution is stale' >&2; exit 1; }
grep -Fq 'Dotchi: This or That Polls' "$tmp/apps.html" || { echo 'FAIL Dotchi catalog still presents an anime-only app' >&2; exit 1; }
for slug in quick-games daily-habits decision-helpers ai-tools; do
  fetch "/guides/$slug/" "$slug.html"
  grep -Fq "https://appdevelopsk.com/guides/$slug/" "$tmp/$slug.html" || { echo "FAIL guide $slug content/canonical mismatch" >&2; exit 1; }
  grep -Fq 'guide_store_click' "$tmp/$slug.html" || { echo "FAIL $slug click measurement missing" >&2; exit 1; }
done
fetch '/sitemap.xml' 'sitemap.xml'
for slug in quick-games daily-habits decision-helpers ai-tools; do
  grep -Fq "https://appdevelopsk.com/guides/$slug/" "$tmp/sitemap.xml" || { echo "FAIL sitemap missing $slug" >&2; exit 1; }
done
for slug in brain-burst snaplingo; do
  fetch "/support/$slug/" "$slug.html"
  grep -Fq 'data-position="hero"' "$tmp/$slug.html" || { echo "FAIL $slug first-screen Play CTA not yet live" >&2; exit 1; }
  grep -Fq 'application/ld+json' "$tmp/$slug.html" || { echo "FAIL $slug SEO metadata missing" >&2; exit 1; }
  grep -Fq 'placement:' "$tmp/$slug.html" || { echo "FAIL $slug placement attribution missing" >&2; exit 1; }
done
fetch '/support/face-reaction-battle/' 'face-battle.html'
grep -Fq 'data-alternative="instant-judge"' "$tmp/face-battle.html" || { echo 'FAIL unavailable game alternative CTA missing' >&2; exit 1; }
grep -Fq 'data-alternative="blur"' "$tmp/face-battle.html" || { echo 'FAIL second unavailable game alternative CTA missing' >&2; exit 1; }
fetch '/support/twotaku/' 'dotchi.html'
grep -Fq '<h1>Dotchi: This or That Polls</h1>' "$tmp/dotchi.html" || { echo 'FAIL Dotchi anime-only support content still live' >&2; exit 1; }
grep -Fq 'data-position="hero"' "$tmp/dotchi.html" || { echo 'FAIL Dotchi store call-to-action absent' >&2; exit 1; }
grep -Fq 'const FEAT_T={en:{0:"Choose A or B on a question."' "$tmp/dotchi.html" || { echo 'FAIL Dotchi translated feature claims still stale' >&2; exit 1; }
# Read-only release gate for the recently corrected Debate Me SEO landing.
fetch '/support/debate-me/' 'debate-me.html'
grep -Fq 'AI Debate Practice &amp; Argument Skills' "$tmp/debate-me.html" || grep -Fq 'AI Debate Practice & Argument Skills' "$tmp/debate-me.html" || { echo 'FAIL Debate Me product title is not live' >&2; exit 1; }
grep -Fq 'data-position="hero"' "$tmp/debate-me.html" || { echo 'FAIL Debate Me first-screen Play CTA not live' >&2; exit 1; }
grep -Fq 'data-position="details"' "$tmp/debate-me.html" || { echo 'FAIL Debate Me details Play CTA missing' >&2; exit 1; }
grep -Fq 'support_debate_me_hero' "$tmp/debate-me.html" || { echo 'FAIL Debate Me Play attribution missing' >&2; exit 1; }
if grep -Eq 'Hundreds of meal ideas|Filter by ingredients|Can.t decide what to cook tonight' "$tmp/debate-me.html"; then
  echo 'FAIL Debate Me page still describes cooking instead of AI debates' >&2; exit 1
fi
# Market listing must describe idea discovery, not a voice diary or an unsupported checkout.
fetch '/support/idea-market/' 'idea-market.html'
grep -Fq '<h1>Idea Market</h1>' "$tmp/idea-market.html" || { echo 'FAIL Idea Market support page missing' >&2; exit 1; }
grep -Fq 'Browse startup ideas, explore public previews' "$tmp/idea-market.html" || { echo 'FAIL Idea Market hero copy still stale' >&2; exit 1; }
grep -Fq 'data-position="hero"' "$tmp/idea-market.html" || { echo 'FAIL Idea Market first-screen Play CTA missing' >&2; exit 1; }
grep -Fq 'support_idea_market_hero' "$tmp/idea-market.html" || { echo 'FAIL Idea Market Play campaign missing' >&2; exit 1; }
if grep -Eq 'voice into a personal diary|Voice-to-text transcription|AI Transcription' "$tmp/idea-market.html"; then
  echo 'FAIL Idea Market page still describes a voice diary' >&2; exit 1
fi
fetch '/robots.txt' 'robots.txt'
grep -Fq 'Allow: /icons/apps/' "$tmp/robots.txt" || { echo 'FAIL Google image crawl allow not live' >&2; exit 1; }
echo 'PASS: catalog, guides, priority search landings, store CTAs, icon crawl policy and sitemap current (HTTP 200)'
