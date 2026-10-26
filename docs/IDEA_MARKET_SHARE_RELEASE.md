# Idea Market share landing — VPS release

**Source status:** merged into this repository's `main` via PR #1.
**Production status:** separate. `appdevelopsk.com` is served by VPS nginx (`/var/www/html`), **not** automatically from this GitHub repository.

## Files and target

- Source: `share/idea-market/index.html` and `share/idea-market/referral.js`.
- Target on VPS: `/var/www/html/share/idea-market/`.
- Public route after deployment: `https://appdevelopsk.com/share/idea-market/?id=qa123`.
- Never include an idea title, price, purchaser data or protected description on the static page. The query is only the opaque idea ID.

## Controlled deploy (run on the machine with the configured SSH alias)

```sh
git checkout main && git pull --ff-only
rsync -av --dry-run share/idea-market/ pickly-vps:/var/www/html/share/idea-market/
rsync -av share/idea-market/ pickly-vps:/var/www/html/share/idea-market/
curl -fsS -L 'https://appdevelopsk.com/share/idea-market/?id=qa123' | grep 'A friend shared an idea'
curl -fsS -L 'https://appdevelopsk.com/share/idea-market/referral.js' | grep 'ideamarket://open/ideas/'
```

**Do not use `rsync --delete`.** Existing nginx routes and website assets must remain intact.

## Release sequence

1. Confirm both live URLs return HTTP 200 and contain current expected strings; action `Idea Market Live Share Landing Check` must pass.
2. Only then merge `appdevelopsk/idea-market-flutter` PR #4, build a signed Android binary, and release after real device QA.
3. On a real device, share a PUBLISHED idea. Tap the HTTPS link from SMS/email/browser, then the `Open this idea in the app` CTA, and verify the exact idea ID opens from cold start and warm start.
4. Test absent app: Google Play CTA opens `jp.appdevelopsk.ideamarket`; after installing, revisit the same link. Test an invalid/expired ID, signed-out visitor, members-only and paid idea to ensure protected details never leak.
5. Track public shared-link opens and actual idea-detail visits separately; never treat page views as installs or purchases.

Without live VPS confirmation and signed-store release, keep the Flutter PR pending and report source-only implementation.
