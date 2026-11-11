# International app acquisition — first controlled Japanese/English distribution wave

Prepared 2026-11-11. **Source-only draft. No social accounts connected in Metricool and no posts or videos published.** The native gameplay footage, signed production release and feature wording must be checked before release.

## Why this wave
- The English purpose-based guide already exists at `/guides/quick-games/`; do not produce duplicate English content.
- Added a distinct Japanese search guide at `/guides/quick-games/ja/`, with reciprocal en/ja hreflang, index entry, catalog-verified Android packages and anonymous click events.
- Start with controlled en/ja experiments; there is no reliable country-by-country iOS/Android conversion proof to support an immediate 17-country rollout.
- The Japanese page is **not live merely because GitHub is merged**. The VPS deployment allowlist and read-only live check must both succeed.

## Eight original short-video briefs (not generated, not published)

Use a real screen recording from the *currently installed signed* app. Trim to 8–20 seconds; add native-language subtitles. Do not fabricate vote totals, leaderboards, daily challenges, app reviews, installs, or other user outcomes. Verify that the first-value action shown is available on the published version.

| App | Creative | EN hook | JA hook | Actual on-screen demonstration | CTA |
|---|---|---|---|---|---|
| Blur | blur-visual-01 | Can you guess before the image clears? | ぼかし画像、見える前に当てられる？ | Open a real picture, reveal, enter a guess, show truthful result | See the game guide |
| Blur | blur-reveal-02 | How many clues would you need? | あなたは何回で分かる？ | One authentic reveal sequence without invented scores | Explore Blur |
| Dotchi | dotchi-choice-01 | A or B — which would you pick? | AとB、あなたはどっち？ | Real current production A/B vote and any result only if returned by app | Explore Dotchi |
| Dotchi | dotchi-choice-02 | Your choice might surprise you | みんなと意見は同じ？ | Authentic non-personal question; show no invented aggregate results | Try a two-choice poll |
| Instant Judge | judge-opinion-01 | Your answer in a few seconds? | 数秒で選ぶならどっち？ | Real photo/dilemma voting UI, avoid fake immediate results | Explore Instant Judge |
| Instant Judge | judge-scenario-02 | One quick question, your call | この問い、あなたならどう選ぶ？ | One production question with actual tap, no invented consensus | Find the app |
| BrainBurst | trivia-question-01 | Can you solve this quiz? | このクイズ、分かる？ | Actual built-in published quiz content, no claim of constant fresh items | See quick games |
| BrainBurst | trivia-round-02 | A quick break, a quiz question | 休憩中に一問挑戦 | One valid question and real completion | Explore BrainBurst |

## Privacy-safe link and measurement contract

**Until the Japanese landing is verified live, publish neither its link nor a claim of availability.**

Suggested social bio or post URLs after live smoke:

- English: `https://appdevelopsk.com/guides/quick-games/?utm_source=youtube&utm_medium=organic_social&utm_campaign=world_apps_202611&utm_content=blur-visual-01`
- Japanese: `https://appdevelopsk.com/guides/quick-games/ja/?utm_source=youtube&utm_medium=organic_social&utm_campaign=world_apps_202611&utm_content=blur-visual-01-ja`

For an actual TikTok/Instagram/Reddit placement, use its **true** `utm_source`, and `utm_content` corresponding to its creative ID. Avoid app-store links with hypothetical iOS IDs, personal answers, user identifiers or private prediction text. Do not assume generic UTM parameters survive Play installation; the existing app-guide Play links include a Play referrer, but attributed installs require separate confirmation.

Track for each creative: upload date, platform, country/language, verified view count, outbound guide visits, `guide_store_click` / `download_click`, 28d Play acquisitions, signed app first-success events, and mature D1/D7 by app/country when available. The funnel steps are separate metrics and are not proof of causal attribution by themselves.

## Minimum publication gates
1. Run `node --test tests/japanese-quick-games-discovery.test.mjs` in a full site checkout and validate actual production-video footage.
2. Deploy using `bash scripts/publish_app_discovery.sh --dry-run`, then operator-controlled `--apply`; it is non-destructive and explicitly lists the new file.
3. Confirm `bash scripts/check_app_discovery_live.sh` passes against the actual site. Confirm the sitemap URL is 200 and the English/Japanese pages have reciprocal hreflang.
4. Publish **one** real video in each of the first two languages. No platform login for distribution is currently connected through Metricool; manual connection is needed before scheduling.
5. Review after 7 days; count *real outbound app traffic and first successful actions*, not impressions or bot visits. Run an extended 14–30 day check before claiming D7 or monthly-user improvement.

Existing source PRs for first-play and consent improvements remain independent; do not consider these landing changes a Flutter release.
