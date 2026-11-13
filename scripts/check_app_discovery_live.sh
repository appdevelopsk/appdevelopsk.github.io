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
grep -Fq 'data-guide="quick-games-ja"' "$tmp/index.html" || { echo 'FAIL Japanese guide missing from live homepage navigation' >&2; exit 1; }
# The homepage should lead to currently published Android applications.
grep -Fq 'href="support/twotaku/"' "$tmp/index.html" || { echo 'FAIL homepage missing published Dotchi feature' >&2; exit 1; }
grep -Fq 'data-app-desc="twotaku"' "$tmp/index.html" || { echo 'FAIL homepage Dotchi localized caption missing' >&2; exit 1; }
if grep -Fq 'href="support/face-reaction-battle/"' "$tmp/index.html"; then
  echo 'FAIL homepage still features unavailable Face Reaction Battle' >&2; exit 1
fi
fetch '/apps' 'apps.html'
grep -Fq 'id="find-app"' "$tmp/apps.html" || { echo 'FAIL catalog search is stale' >&2; exit 1; }

# The new UI is browser-side only; these assertions confirm deployed source,
# NOT that user interactions/GA4 events have been executed in a real browser.
grep -Fq 'id="catalog-language"' "$tmp/apps.html" || { echo 'FAIL five-language catalog selector not deployed' >&2; exit 1; }
grep -Fq 'CATALOG_LOCALE_START' "$tmp/apps.html" || { echo 'FAIL catalog locale controller missing' >&2; exit 1; }
grep -Fq 'catalog_language_selected' "$tmp/apps.html" || { echo 'FAIL catalog language analytics contract missing' >&2; exit 1; }
for language in en ja es pt-BR id; do
  grep -Fq "option value=\"$language\"" "$tmp/apps.html" || { echo "FAIL $language catalog option not deployed" >&2; exit 1; }
done
grep -Fq 'catalogSearchAliases' "$tmp/apps.html" || { echo 'FAIL localized pilot discovery aliases missing' >&2; exit 1; }

grep -Fq 'catalog_store_click' "$tmp/apps.html" || { echo 'FAIL store-click attribution is stale' >&2; exit 1; }
grep -Fq '日本語でゲームを探す' "$tmp/apps.html" || { echo 'FAIL Japanese guide missing from live app catalog' >&2; exit 1; }
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
# Dotchi must be reachable from the live quick-games guide AND from the public catalog filter.
grep -Fq 'data-app="twotaku"' "$tmp/quick-games.html" || { echo 'FAIL quick-games guide missing Dotchi CTA' >&2; exit 1; }
grep -Fq 'id=com.dotchi.dotchi_app' "$tmp/quick-games.html" || { echo 'FAIL quick-games Dotchi listing URL missing' >&2; exit 1; }
grep -Fq "'quick-games': ['blur','instant-judge','twotaku'" "$tmp/apps.html" || { echo 'FAIL public catalog quick-games filter excludes Dotchi' >&2; exit 1; }
fetch '/sitemap.xml' 'sitemap.xml'
for slug in quick-games daily-habits decision-helpers ai-tools; do
  grep -Fq "https://appdevelopsk.com/guides/$slug/" "$tmp/sitemap.xml" || { echo "FAIL sitemap missing $slug" >&2; exit 1; }
done
# Verify that the Japanese acquisition guide is really deployed, not merely committed.
fetch '/guides/quick-games/ja/' 'quick-games-ja.html'
grep -Fq '<html lang="ja">' "$tmp/quick-games-ja.html" || { echo 'FAIL Japanese guide language mismatch' >&2; exit 1; }
grep -Fq 'https://appdevelopsk.com/guides/quick-games/ja/' "$tmp/quick-games-ja.html" || { echo 'FAIL Japanese guide canonical missing' >&2; exit 1; }
grep -Fq 'hreflang="ja" href="https://appdevelopsk.com/guides/quick-games/ja/"' "$tmp/quick-games.html" || { echo 'FAIL English guide missing Japanese hreflang' >&2; exit 1; }
grep -Fq 'utm_campaign=quick_games_ja' "$tmp/quick-games-ja.html" || { echo 'FAIL Japanese store attribution missing' >&2; exit 1; }
grep -Fq 'guide_store_click' "$tmp/quick-games-ja.html" || { echo 'FAIL Japanese guide store-click event absent' >&2; exit 1; }
grep -Fq 'https://appdevelopsk.com/guides/quick-games/ja/' "$tmp/sitemap.xml" || { echo 'FAIL Japanese guide omitted from live sitemap' >&2; exit 1; }

for slug in brain-burst snaplingo; do
  fetch "/support/$slug/" "$slug.html"
  grep -Fq 'data-position="hero"' "$tmp/$slug.html" || { echo "FAIL $slug first-screen Play CTA not yet live" >&2; exit 1; }
  grep -Fq 'application/ld+json' "$tmp/$slug.html" || { echo "FAIL $slug SEO metadata missing" >&2; exit 1; }
  grep -Fq 'placement:' "$tmp/$slug.html" || { echo "FAIL $slug placement attribution missing" >&2; exit 1; }
done
# Source merged app SEO and product-truth changes must be on the *public* origin.
grep -Fq '<title>BrainBurst: Daily Trivia & 1v1 Quiz Battles | Android</title>' "$tmp/brain-burst.html" || { echo 'FAIL BrainBurst current SEO title not live' >&2; exit 1; }
if grep -Eq 'How do I restore my purchase\?|How do I cancel a subscription\?|Many features work offline\.' "$tmp/brain-burst.html"; then
  echo 'FAIL BrainBurst advertises unsupported billing or offline features' >&2; exit 1
fi
# The family-story support page is a separate SEO landing; do not confuse source merge with a live rollout.
fetch '/support/taletime/' 'taletime.html'
grep -Fq '<title>TaleTime: AI Story Maker for Parents & Kids | SK APPS</title>' "$tmp/taletime.html" || { echo 'FAIL TaleTime current SEO title not live' >&2; exit 1; }
grep -Fq 'Create stories together in TaleTime' "$tmp/taletime.html" || { echo 'FAIL TaleTime meta description not live' >&2; exit 1; }
# Every localized press page must exist on the VPS, with correct canonical and event wiring.
for entry in 'en:press/:en' 'es:press/es/:es' 'pt-br:press/pt-br/:pt-BR' 'ja:press/ja/:ja' 'id:press/id/:id'; do
  IFS=: read -r code route language <<< "$entry"
  fetch "/$route" "press-$code.html"
  grep -Fq "<html lang=\"$language\">" "$tmp/press-$code.html" || { echo "FAIL press $code language not live" >&2; exit 1; }
  grep -Fq "https://appdevelopsk.com/$route" "$tmp/press-$code.html" || { echo "FAIL press $code canonical not live" >&2; exit 1; }
  grep -Fq 'press_app_click' "$tmp/press-$code.html" || { echo "FAIL press $code app attribution missing" >&2; exit 1; }
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
# The post-GSC 2026-11-11 snippet must be live; rejecting the old SEO
# title prevents a GitHub merge from being mistaken for a published change.
grep -Fq '<title>Debate Me: AI Debate Practice App for Android | SK APPS</title>' "$tmp/debate-me.html" || { echo 'FAIL Debate Me new SEO title not live' >&2; exit 1; }
grep -Fq 'content="Practice debates against an AI opponent in Debate Me for Android' "$tmp/debate-me.html" || { echo 'FAIL Debate Me new search description not live' >&2; exit 1; }
grep -Fq '<meta property="og:title" content="Debate Me: Practice Arguments with AI | Android App">' "$tmp/debate-me.html" || { echo 'FAIL Debate Me OG title not live' >&2; exit 1; }
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
# Blur listing must show a real single-player image-reveal experience.
fetch '/support/blur/' 'blur.html'
grep -Fq '<h1>Blur: Guess the Image</h1>' "$tmp/blur.html" || { echo 'FAIL Blur support landing missing' >&2; exit 1; }
grep -Fq 'data-position="hero"' "$tmp/blur.html" || { echo 'FAIL Blur first-screen Play CTA not live' >&2; exit 1; }
grep -Fq 'support_blur_hero' "$tmp/blur.html" || { echo 'FAIL Blur Play campaign missing' >&2; exit 1; }
if grep -Eq 'Multiplayer mode|Multiple difficulty levels|Timed challenges' "$tmp/blur.html"; then
  echo 'FAIL Blur advertises unverified game modes' >&2; exit 1
fi
# Instant Judge must accurately describe voting and time-gated result reveal.
fetch '/support/instant-judge/' 'instant-judge.html'
grep -Fq 'Vote on everyday dilemmas, create your own post' "$tmp/instant-judge.html" || { echo 'FAIL Instant Judge hero is stale' >&2; exit 1; }
grep -Fq 'data-position="hero"' "$tmp/instant-judge.html" || { echo 'FAIL Instant Judge first-screen Play CTA missing' >&2; exit 1; }
grep -Fq 'support_instant_judge_hero' "$tmp/instant-judge.html" || { echo 'FAIL Instant Judge campaign tagging missing' >&2; exit 1; }
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
# #53 broadened the allow to /icons/ (covers /icons/apps/).
grep -Eq '^Allow: /icons/(apps/)?$' "$tmp/robots.txt" || { echo 'FAIL Google image crawl allow not live' >&2; exit 1; }
echo 'PASS: catalog, guides, priority search landings, store CTAs, icon crawl policy and sitemap current (HTTP 200)'
