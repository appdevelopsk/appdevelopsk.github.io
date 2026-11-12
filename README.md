# appdevelopsk.github.io
<!-- cache-bust: 2026-04-06 07:45:05 UTC -->
## Production deployment verification (no GitHub Actions)

The production domain is `https://appdevelopsk.com`, but this repository does not
contain a deploy-provider configuration or `CNAME`. **Do not assume merging
`main` publishes this domain.** Check the hosting provider's project settings
for the actual source repository, production branch, deployed commit and
production domain before making changes to DNS or hosting.

From a clean checkout of the intended production commit:

```bash
python3 -m unittest discover -s scripts -p 'test_*.py' -v
node --test scripts/test_catalog_search_events.cjs
node --test scripts/test_guide_store_events.cjs
python3 scripts/diagnose_growth_deploy.py --root . --output growth-deploy-diagnosis.json
python3 scripts/diagnose_growth_routes.py --output growth-route-diagnosis.json
python3 scripts/check_growth_live.py > growth-live-smoke.json
```

The route diagnosis additionally compares /apps and /apps.html, recording final URLs, public cache headers, canonical tags and hashes to uncover split cache/rewrite behavior. Inspect both results before editing redirects; the command makes no hosting or DNS changes.

The deploy diagnosis checks HTTP 200 and compares the raw HTML bytes of the
homepage, app catalog, five priority app support pages, and five press locales to the checked-out
commit. It records hashes, release markers and fetch errors, **not page bodies
or user data**. A byte mismatch is not necessarily failed deployment if the
host minifies/injects content; consult the semantic growth smoke and inspect
the hosting deployment logs. A matching milestone meta tag does not establish
the exact deployed commit. Do not equate site-to-Play clicks with installs.

After publication, manually verify catalog search, zero-result reset, app
referrals and real GA4 DebugView events, then reconcile actual first-time
installers in Google Play Console. Keep tracking in
[the release verification issue](https://github.com/appdevelopsk/appdevelopsk.github.io/issues/51)
until those checks have evidence.

## App support search snippet deployment gate (2026-11-13)

The Debate Me, BrainBurst, and TaleTime titles and descriptions were updated on
`main`, but merging source is **not** proof that the public host received it.
Run this read-only check after an authorized deployment and compare the local
source against the public HTML (titles, descriptions, Open Graph descriptions,
canonical URLs, and duplicate tags):

```bash
node --test scripts/test_support_serp_snippets_20261113.cjs
python3 -m unittest discover -s scripts -p 'test_support_serp_live.py' -v
python3 scripts/check_support_serp_live.py > support-serp-live.json
```

A nonzero exit means the live host is stale, unavailable, or inconsistent with
source. Inspect `support-serp-live.json` and the hosting provider's deployed
branch/SHA before changing DNS or announcing the release. The tool does not
request indexing, change the site, or prove search clicks or app installs.

## Global press/creator landing pages — 2026-11-13

Source contains five intended localized press routes: `/press/` (English), `/press/es/` (Spanish), `/press/pt-br/` (Brazilian Portuguese), `/press/ja/` (Japanese), and `/press/id/` (Indonesian). This is *source coverage*, not proof of production delivery or indexing. No automated outreach or social publication follows from a merge.

Before promoting these URLs to partners:

```bash
python3 -m unittest scripts.test_press_kit -v
python3 -m unittest scripts.test_diagnose_growth_deploy -v
python3 scripts/diagnose_growth_deploy.py --root . --output growth-deploy-diagnosis.json
```

The deployment comparison includes all five press pages (12 pages in total). Confirm the hosting provider's actual production source/ref/commit, inspect public HTTP 200, redirects, canonical/hreflang and all five Play links, and verify `press_app_click` in GA4 DebugView. A source merge or static test is **not** a live deployment check. Record results in issue #51. Only promote the published URL after these checks pass; otherwise use verified live app support/store pages.


## Five-language catalog discovery UI (2026-11-13)

The /apps page has browser-language-aware interface labels in English, Japanese,
Spanish, Brazilian Portuguese and Indonesian, plus an explicit language selector.
Category labels, five featured-app descriptions, finder status, empty state, and
selected search synonyms are localized. App card names and descriptions remain
English. No SEO hreflang pages are claimed and canonical stays /apps.
The allowlisted ?lang=es etc. query is UI preference, not an indexed translation.
The ?goal=... filter is preserved during manual language changes.

Search text is never sent to analytics; existing coarse search events remain.
The only new event is catalog_language_selected, carrying the selected locale
and placement without search text or sensitive identifiers.

Run checks:
  node --test scripts/test_catalog_search_events.cjs
  node --test scripts/test_catalog_locale.cjs
  python3 scripts/check_growth_live.py > growth-live-smoke.json

Before claiming a live release, verify the hosting provider deployed SHA and open
/apps?goal=quick-games&lang=es and /apps?lang=ja in a real browser. Confirm 92
cards, filters, language switching, console errors, real store destinations,
and exactly one catalog_language_selected per manual choice in GA4 DebugView.
Record source-vs-live evidence in GitHub issue #51. A merge is not deployment.
