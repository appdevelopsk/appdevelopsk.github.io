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
homepage, app catalog and five priority app support pages to the checked-out
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
