# 本番反映(appdevelopsk.com)

main へのマージでは本番に反映されない。次のどちらかで反映する。

1. **基本: ken の Mac から**
   `bash scripts/publish_app_discovery.sh --dry-run` → 確認 → `--apply`、
   `bash scripts/publish_stale_policy_pages.sh --dry-run|--apply`、
   検証は `scripts/check_app_discovery_live.sh` と `publish_stale_policy_pages.sh --check-live`。
2. **ChatGPT/Codex など Mac 以外から: Actions の `publish to VPS`**
   `gh workflow run publish-vps.yml -f mode=dry-run` → 結果を確認 → ken の許可を得て `-f mode=apply`。
   main の HEAD だけが対象。`--delete` はしない。apply 後に本番検証まで走る。

禁止: 許可なしの `mode=apply`、App Store(apps.apple.com)リンクの追加(iOS は 404・ADP 終了)。
