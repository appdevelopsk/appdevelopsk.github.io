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
# Source metadata is not proof that the public catalog was updated.
# Check the actual live HTML for each corrected high-priority app description.
grep -Fq 'Practice debating with an AI opponent, get feedback and share your results' "$tmp/apps.html" || { echo 'FAIL catalog description not deployed: Practice debating with a' >&2; exit 1; }
grep -Fq 'Post a topic, get community feedback and write a kind or blunt roast' "$tmp/apps.html" || { echo 'FAIL catalog description not deployed: Post a topic, get commun' >&2; exit 1; }
grep -Fq 'Vote on community dilemmas, post your own and see results when revealed' "$tmp/apps.html" || { echo 'FAIL catalog description not deployed: Vote on community dilemm' >&2; exit 1; }
grep -Fq 'Explore playful AI future scenarios, revisit predictions and plan tomorrow' "$tmp/apps.html" || { echo 'FAIL catalog description not deployed: Explore playful AI futur' >&2; exit 1; }
grep -Fq 'Explore startup ideas, read public previews and post your own business concept' "$tmp/apps.html" || { echo 'FAIL catalog description not deployed: Explore startup ideas, r' >&2; exit 1; }
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
grep -Fq 'apps.apple.com/app/id6760481027?ct=support_twotaku_hero' "$tmp/dotchi.html" || { echo 'FAIL twotaku hero App Store CTA missing' >&2; exit 1; }
grep -Fq 'apps.apple.com/app/id6760481027?ct=support_twotaku_details' "$tmp/dotchi.html" || { echo 'FAIL twotaku details App Store CTA missing' >&2; exit 1; }
grep -Fq 'const FEAT_T={en:{0:"Choose A or B on a question."' "$tmp/dotchi.html" || { echo 'FAIL Dotchi translated feature claims still stale' >&2; exit 1; }
# Read-only release gate for the recently corrected Debate Me SEO landing.
fetch '/support/debate-me/' 'debate-me.html'
grep -Fq 'AI Debate Practice &amp; Argument Skills' "$tmp/debate-me.html" || grep -Fq 'AI Debate Practice & Argument Skills' "$tmp/debate-me.html" || { echo 'FAIL Debate Me product title is not live' >&2; exit 1; }
grep -Fq 'data-position="hero"' "$tmp/debate-me.html" || { echo 'FAIL Debate Me first-screen Play CTA not live' >&2; exit 1; }
grep -Fq 'apps.apple.com/app/id6760968208?ct=support_debate_me_hero' "$tmp/debate-me.html" || { echo 'FAIL debate_me hero App Store CTA missing' >&2; exit 1; }
grep -Fq 'apps.apple.com/app/id6760968208?ct=support_debate_me_details' "$tmp/debate-me.html" || { echo 'FAIL debate_me details App Store CTA missing' >&2; exit 1; }
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
# Blur listing must show a real single-player image-reveal experience.
fetch '/support/blur/' 'blur.html'
grep -Fq '<h1>Blur: Guess the Image</h1>' "$tmp/blur.html" || { echo 'FAIL Blur support landing missing' >&2; exit 1; }
grep -Fq 'data-position="hero"' "$tmp/blur.html" || { echo 'FAIL Blur first-screen Play CTA not live' >&2; exit 1; }
grep -Fq 'apps.apple.com/app/id6759920723?ct=support_blur_hero' "$tmp/blur.html" || { echo 'FAIL blur hero App Store CTA missing' >&2; exit 1; }
grep -Fq 'apps.apple.com/app/id6759920723?ct=support_blur_details' "$tmp/blur.html" || { echo 'FAIL blur details App Store CTA missing' >&2; exit 1; }
grep -Fq 'support_blur_hero' "$tmp/blur.html" || { echo 'FAIL Blur Play campaign missing' >&2; exit 1; }
if grep -Eq 'Multiplayer mode|Multiple difficulty levels|Timed challenges' "$tmp/blur.html"; then
  echo 'FAIL Blur advertises unverified game modes' >&2; exit 1
fi
# Instant Judge must accurately describe voting and time-gated result reveal.
fetch '/support/instant-judge/' 'instant-judge.html'
grep -Fq 'Vote on everyday dilemmas, create your own post' "$tmp/instant-judge.html" || { echo 'FAIL Instant Judge hero is stale' >&2; exit 1; }
grep -Fq 'data-position="hero"' "$tmp/instant-judge.html" || { echo 'FAIL Instant Judge first-screen Play CTA missing' >&2; exit 1; }
grep -Fq 'support_instant_judge_hero' "$tmp/instant-judge.html" || { echo 'FAIL Instant Judge campaign tagging missing' >&2; exit 1; }
grep -Fq 'apps.apple.com/app/id6759920352?ct=support_instant_judge_hero' "$tmp/instant-judge.html" || { echo 'FAIL Instant Judge hero App Store CTA missing' >&2; exit 1; }
grep -Fq 'apps.apple.com/app/id6759920352?ct=support_instant_judge_details' "$tmp/instant-judge.html" || { echo 'FAIL Instant Judge details App Store CTA missing' >&2; exit 1; }
grep -Fq 'Results appear at their reveal time' "$tmp/instant-judge.html" || { echo 'FAIL Instant Judge reveal copy missing' >&2; exit 1; }
if grep -Eiq 'Thousands of scenarios|Real-time results|Many features work offline' "$tmp/instant-judge.html"; then
  echo 'FAIL Instant Judge advertises unsupported immediate results or scale' >&2; exit 1
fi
# RoastMe offers community-written roasts, not a guaranteed AI roast service.
fetch '/support/roast-me/' 'roastme.html'
grep -Fq 'Post a topic, invite community feedback' "$tmp/roastme.html" || { echo 'FAIL RoastMe public hero copy is stale' >&2; exit 1; }
grep -Fq 'data-position="hero"' "$tmp/roastme.html" || { echo 'FAIL RoastMe first-screen Play CTA missing' >&2; exit 1; }
grep -Fq 'support_roast_me_hero' "$tmp/roastme.html" || { echo 'FAIL RoastMe campaign tagging missing' >&2; exit 1; }
if grep -Eiq 'AI-generated roasts|Get roasted by AI and friends|100% anonymous' "$tmp/roastme.html"; then
  echo 'FAIL RoastMe promises unverified AI roasts or absolute anonymity' >&2; exit 1
fi
# FutureMe landing must not promise unrelated letter/time-capsule features or fixed premium prices.
fetch '/support/future-me/' 'futureme.html'
grep -Fq 'Explore AI-generated future scenarios for fun' "$tmp/futureme.html" || { echo 'FAIL FutureMe first-view copy stale' >&2; exit 1; }
grep -Fq 'data-position="hero"' "$tmp/futureme.html" || { echo 'FAIL FutureMe first-screen Play CTA missing' >&2; exit 1; }
grep -Fq 'support_future_me_hero' "$tmp/futureme.html" || { echo 'FAIL FutureMe Play campaign missing' >&2; exit 1; }
if grep -Eiq 'Letters to future self|Time capsule feature|FutureMe Premium.*[0-9]+/(month|year)|FutureMe Premium 提供月度|NT\\$150/月' "$tmp/futureme.html"; then
  echo 'FAIL FutureMe support page contains outdated feature or pricing claims' >&2; exit 1
fi
fetch '/robots.txt' 'robots.txt'
grep -Fq 'Allow: /icons/apps/' "$tmp/robots.txt" || { echo 'FAIL Google image crawl allow not live' >&2; exit 1; }
echo 'PASS: catalog, guides, priority search landings, store CTAs, icon crawl policy and sitemap current (HTTP 200)'
