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


## 日本語ゲーム集客ページの公開確認（2026-11-11）

GitHub の `main` 反映だけでは VPS の `https://appdevelopsk.com/guides/quick-games/ja/` に自動反映されない。macOS の **実際のサイト配信設定がある環境**で以下を順番に実行する。

```bash
git switch main && git pull --ff-only
node --test tests/japanese-quick-games-discovery.test.mjs
python3 scripts/build_catalog.py --check
bash scripts/publish_app_discovery.sh --dry-run
# 差分を確認し、VPSの対象と接続先が正しいことを確認した後に:
bash scripts/publish_app_discovery.sh --apply
bash scripts/check_app_discovery_live.sh
```

`--apply` は明示操作。通常の同期は非破壊 rsync であり、意図しないファイル削除を行わない。検査では日本語ページのHTTP 200、canonical、サイトマップ、英語ページの hreflang、Playリンク計測に加え、ホームページとアプリ一覧からの日本語ガイドへのリンクを確認する。

公開後に `guide_store_click` / `download_click`、広告や動画の流入元、Google Play の実取得数、実際の最初のゲーム操作と成熟したD7を別々に記録する。サイト側のイベントクリックやマージ履歴だけでインストール数やアクティブユーザー増を主張しない。

このチャット実行環境ではVPSへのSSH接続・実サイトHTTP到達ができず、GitHub Actionsも使用していないため、**現時点で本番公開は未確認**。
