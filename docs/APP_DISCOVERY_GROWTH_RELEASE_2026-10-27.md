# App acquisition release and experiment plan (2026-10-27)

## Source of truth / deployment reality

- App catalog: **92** non-hidden Android listings in `apps_data.json` as of site count 2026-10-12. Do not call all 117 created apps Play-published. Hidden entries must never be promoted automatically.
- Production `appdevelopsk.com` is served by nginx on the VPS (`/var/www/html`). GitHub repository `appdevelopsk/appdevelopsk.github.io` **main is not itself the live site**. GitHub Pages publishes from a separate `pages-blank` branch and is not a replacement for the VPS.
- The source PR #4 introduced in `/apps` a searchable, accessible catalog and two new canonical SEO guides. **No successful HTTPS production deployment was established by merging it.**

## Deployment with the existing local `pickly-vps` SSH alias

From a **fresh main** checkout of this site repository, after checking working tree status:

```bash
git pull --ff-only
bash scripts/publish_app_discovery.sh --dry-run
# Review the four changed destination paths. Never pass --delete.
bash scripts/publish_app_discovery.sh --apply
bash scripts/check_app_discovery_live.sh
```

Only these files transfer: `apps.html`, `sitemap.xml`, `guides/quick-games/index.html`, `guides/daily-habits/index.html`. Every other VPS file, including privacy, support, policy, payment and ads assets, stays untouched. To override environment use `APP_SITE_DEPLOY_HOST` and `APP_SITE_DEPLOY_ROOT` with a known-safe absolute path. The script refuses unknown flags/invalid targets.

**Publish gate:** a dry-run is not publication. Only mark live once `check_app_discovery_live.sh` reports HTTP 200 and matches `id="find-app"`, both guide canonical URLs, guide click event and sitemap entries. After manual publication consider Google Search Console URL inspection and sitemap submission if the `appdevelopsk.com` property is available.

## Growth experiment — acquisition, not vanity pageviews

| Funnel stage | Event / source | Decision |
|---|---|---|
| Website entry | GA4 landing page, organic / referral / direct, `appdevelopsk.com/apps` and `/guides/*` | New landing sessions and engaged sessions by source |
| Discovery | `catalog_search_used`, `catalog_filter_used` | What proportion of visitors use discovery controls? These events must not include raw search terms |
| Store intent | `catalog_store_click`, `guide_store_click` with app slug | Store clicks by guide and category vs catalog views |
| Play install | Google Play Console listing visitors, acquisitions and Install Referrer campaign (`apps_catalog`, `quick_games`, `daily_habits`) | Conversion separately for each campaign, geography and released package |
| First app value | App GA4 events (first post, first game result, first photo, etc.) | Do newly acquired users finish core action? |
| Repeat value | Mature D1/D7 cohort with sufficient n, crash-free | Keep acquisition spend/effort only if app delivers retention |

Do not sum the 117 apps' 7-day active-user counts as unique people. Do not interpret clicks as downloads, installs as activated users, or app-source merges as store releases. If a campaign has fewer than ~100 store visitors or D7 cohort n<30, call it directional/inconclusive. Monitor the first 7 days to catch broken links; compare at least 28-day periods for conversion trends while accounting for rollout date and channel mix.

## Safe search-indexing / content integrity

- All guides recommend only 4 existing **non-hidden** catalog apps each; their descriptions are sourced from the public catalog. Guides have no made-up star ratings, screenshots, money claims or app feature promises.
- All cards remain server-rendered so crawlers and no-JavaScript users still see published links. Filters run only when JS works.
- URLs use Play Install Referrer with guide-specific campaigns. Keep referrer and GA4 attribution separate; the actual install remains subject to Google Play behavior.
- If an app is delisted or renamed, edit `apps_data.json`, `scripts/build_catalog.py` and the affected guide together, then run Node tests and `python3 scripts/build_catalog.py --check`.

## Release checklist

- [x] Source changes merged to main (PR #4)
- [x] Static website tests and build-catalog consistency passed on PR #4
- [ ] VPS rsync dry-run reviewed by deploy operator
- [ ] VPS content uploaded, actual HTTPS endpoint verified
- [ ] Sitemap submitted/indexing checked in Search Console
- [ ] GA4 DebugView events observed without search query payload
- [ ] Google Play listing traffic / acquisition comparison recorded after meaningful sample
