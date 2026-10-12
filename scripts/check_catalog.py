#!/usr/bin/env python3
"""check_catalog.py — apps_data.json(カタログ)と各アプリの実体を突き合わせる。

背景(2026-10-12 外部監査): apps.html の "Face Symmetry - Mirror Check" は
jp.appdevelopsk.facesymmetry へリンクしていたが、そのパッケージは 7/30 に
HangTrue(水平器)へ作り替え済みで、カタログだけが旧名のまま残っていた。
TrueMe(com.trueme.true_me → Daylapse)も同じ。カタログ側に照合の仕組みが
無かったため、ここで「タイトル → ストア名 → パッケージ ID → 公開状態」を照らす。

情報源(すべてローカル。Google Play の公開ページは取得しない):
  1. カタログ          apps_data.json(このリポジトリ)
  2. リポジトリの掲載文  <APPS_ROOT>/<app>/flutter_app/android/fastlane/metadata/android/en-US/
                        title.txt / short_description.txt と build.gradle(.kts) の applicationId
  3. 公開状態          ~/Library/Application Support/play_refresh/google_play_production_status.json
                        (launchd com.appdevelopsk.play_production_refresh が毎日更新)
  4. (任意 --play-api) Google Play Developer API の掲載文 en-US を読み取りだけで取得
                        (edit を作って listings を GET し、commit せずに DELETE する。
                         play_production_refresh と同じ鍵・同じ手順)

判定:
  ERROR  カタログ名とストア名が別製品(語の重なりなし)/ パッケージが Play に無い・
         本番未公開 / applicationId がカタログの pkg と違う
  WARN   名前の表記ゆれ(語は重なる)/ リポジトリに掲載文が無い / 本数表記がデータと違う
  INFO   本番公開中なのにカタログに無いアプリ / hidden(カード非表示)なのに台帳は released
  (apps_data.json の "hidden" はカードに出さないアプリ。公開状態の ERROR は出さない)
  build_catalog.py --check の差分(本数・カードの再生成漏れ)も ERROR

使い方:
  python3 scripts/check_catalog.py                # ローカル情報だけ
  python3 scripts/check_catalog.py --play-api     # Play API の掲載文も読む(読み取りのみ)
  python3 scripts/check_catalog.py --json out.json
終了コード: ERROR があれば 1、それ以外 0。
"""
import argparse
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
APPS_ROOT = os.environ.get("APPS_ROOT", os.path.expanduser("~/app-infra"))
PLAY_DIR = os.path.expanduser("~/Library/Application Support/play_refresh")
STATUS_JSON = os.path.join(PLAY_DIR, "google_play_production_status.json")
KEY_CANDIDATES = [
    os.path.join(PLAY_DIR, "google-play-key.json"),
    os.path.expanduser("~/.config/gcloud/google-play-key.json"),
]

STOP = set("""the a an and or of to for your you with in on it its is are be get see app apps free
new best this that from by at as all any every each what when how my me & - — : |""".split())


def words(s):
    return {w for w in re.findall(r"[a-z0-9]+", (s or "").lower()) if w not in STOP and len(w) > 1}


def read(p):
    try:
        with open(p, encoding="utf-8") as f:
            return f.read().strip()
    except OSError:
        return None


def app_id_of(app_dir):
    for g in ("android/app/build.gradle.kts", "android/app/build.gradle"):
        t = read(os.path.join(app_dir, g))
        if t:
            m = re.search(r'applicationId\s*=?\s*"([^"]+)"', t)
            if m:
                return m.group(1)
    return None


def index_local_apps():
    """APPS_ROOT 配下の flutter_app を applicationId で引けるようにする。"""
    by_pkg = {}
    if not os.path.isdir(APPS_ROOT):
        return by_pkg
    for name in sorted(os.listdir(APPS_ROOT)):
        fa = os.path.join(APPS_ROOT, name, "flutter_app")
        if not os.path.isdir(fa):
            continue
        pkg = app_id_of(fa)
        if not pkg:
            continue
        md = os.path.join(fa, "android/fastlane/metadata/android/en-US")
        by_pkg.setdefault(pkg, {
            "dir": name,
            "title": read(os.path.join(md, "title.txt")),
            "short": read(os.path.join(md, "short_description.txt")),
        })
    return by_pkg


def load_status():
    try:
        d = json.load(open(STATUS_JSON, encoding="utf-8"))
    except (OSError, ValueError):
        return None, {}
    return d.get("updated_at"), {a["pkg"]: a for a in d.get("apps", [])}


def play_api_listings(pkgs):
    """Play Developer API で en-US 掲載文を読む(edit は commit せず破棄)。"""
    from google.oauth2 import service_account
    import google.auth.transport.requests
    import urllib.request
    import urllib.error

    key = next((k for k in KEY_CANDIDATES if os.path.exists(k)), None)
    if not key:
        print("WARN: Play API の鍵が無いので --play-api を飛ばす", file=sys.stderr)
        return {}
    cred = service_account.Credentials.from_service_account_file(
        key, scopes=["https://www.googleapis.com/auth/androidpublisher"])
    cred.refresh(google.auth.transport.requests.Request())

    def api(url, method="GET"):
        req = urllib.request.Request(url, method=method)
        req.add_header("Authorization", f"Bearer {cred.token}")
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                body = r.read().decode() or "{}"
                return r.status, json.loads(body)
        except urllib.error.HTTPError as e:
            return e.code, {}

    out = {}
    base0 = "https://androidpublisher.googleapis.com/androidpublisher/v3/applications"
    for pkg in pkgs:
        s, e = api(f"{base0}/{pkg}/edits", "POST")
        if s != 200:
            out[pkg] = {"error": f"edit_create_{s}"}
            continue
        base = f"{base0}/{pkg}/edits/{e['id']}"
        s, lst = api(f"{base}/listings/en-US")
        out[pkg] = ({"title": lst.get("title"), "short": lst.get("shortDescription")}
                    if s == 200 else {"error": f"listing_{s}"})
        api(base, "DELETE")
    return out


def count_claims():
    """公開ページに書かれた「◯本」の表記を拾う(SITE_COUNT の差し込み漏れ検出用)。"""
    hits = []
    for f in ("index.html", "apps.html", "about.html"):
        t = read(os.path.join(REPO, f)) or ""
        for m in re.finditer(r"(\d{2,3})\+?\s*(?:Android\s+)?(?:apps|Apps|mobile apps|free apps|アプリ|款|個|приложени|applis|app|Aplikasi|ứng dụng|แอป|uygulama|تطبيق)", t):
            hits.append((f, m.group(0)))
        for m in re.finditer(r'class="stat-number"[^>]*>([^<]+)<', t):
            hits.append((f, "stat " + m.group(1)))
    return hits


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--play-api", action="store_true")
    ap.add_argument("--json")
    args = ap.parse_args()

    catalog = json.load(open(os.path.join(REPO, "apps_data.json"), encoding="utf-8"))
    counts = read(os.path.join(REPO, "site_counts.json"))
    counts = json.loads(counts) if counts else None
    local = index_local_apps()
    status_at, status = load_status()
    live = play_api_listings([a["pkg"] for a in catalog]) if args.play_api else {}

    rows, n_err, n_warn = [], 0, 0
    for a in catalog:
        pkg, title = a["pkg"], a["title"]
        st = status.get(pkg)
        loc = local.get(pkg)
        lv = live.get(pkg) or {}
        store_title = lv.get("title") or (loc or {}).get("title")
        src = "play-api" if lv.get("title") else ("repo" if loc and loc.get("title") else None)
        issues = []
        hidden = a.get("hidden")
        if hidden:
            if st and st.get("access") == "released":
                issues.append(("INFO", f"hidden だが台帳は released(Play の公開ページで要確認): {hidden}"))
        elif st is None:
            issues.append(("ERROR", "Play の状態台帳に無い"))
        elif st.get("access") != "released":
            issues.append(("ERROR", f"本番未公開 access={st.get('access')}"))
        if loc is None:
            issues.append(("WARN", f"{APPS_ROOT} に applicationId={pkg} の flutter_app が無い"))
        if store_title:
            cw, sw = words(title), words(store_title)
            if title.strip().lower() == store_title.strip().lower():
                pass
            elif cw & sw:
                issues.append(("WARN", f"表記ゆれ: ストア[{src}]={store_title!r}"))
            else:
                issues.append(("ERROR", f"別製品: ストア[{src}]={store_title!r}"))
        else:
            issues.append(("WARN", "ストア名を取得できない(掲載文がリポジトリに無い)"))
        if lv.get("error"):
            issues.append(("WARN", f"Play API {lv['error']}"))
        n_err += sum(1 for s, _ in issues if s == "ERROR")
        n_warn += sum(1 for s, _ in issues if s == "WARN")
        rows.append({"app": a["app"], "pkg": pkg, "catalog_title": title,
                     "store_title": store_title, "store_title_source": src,
                     "access": (st or {}).get("access"), "issues": issues})

    in_cat = {a["pkg"] for a in catalog}
    released = sorted(p for p, s in status.items() if s.get("access") == "released")
    missing = [p for p in released if p not in in_cat]

    if counts:
        n_live = sum(1 for a in catalog if not a.get("hidden"))
        if counts.get("android_live") != n_live:
            print(f"ERROR site_counts.json android_live={counts.get('android_live')} だが"
                  f" apps_data.json の表示対象は {n_live} 本")
            n_err += 1
        if status and counts.get("built_total") != len(status):
            print(f"WARN  site_counts.json built_total={counts.get('built_total')} だが台帳は {len(status)} 本"
                  f"(build_catalog.py --refresh-total で更新)")
            n_warn += 1
    import subprocess
    r = subprocess.run([sys.executable, os.path.join(HERE, "build_catalog.py"), "--check"],
                       capture_output=True, text=True)
    if r.returncode != 0:
        print("ERROR build_catalog.py --check: " + (r.stdout + r.stderr).strip())
        n_err += 1

    print(f"カタログ {len(catalog)} 本 / Play 台帳 {len(status)} 本(本番公開 {len(released)})"
          f" 台帳更新 {status_at} / Play API {'使用' if args.play_api else '未使用'}")
    for r in rows:
        for sev, msg in r["issues"]:
            if sev in ("ERROR", "WARN", "INFO"):
                print(f"{sev:5} {r['app']:28} {r['pkg']:45} {r['catalog_title']!r}: {msg}")
    for p in missing:
        loc = local.get(p) or {}
        print(f"INFO  本番公開中だがカタログに無い: {p} {loc.get('title')!r}")
    print("本数表記:", sorted(set(h[1] for h in count_claims())))
    print(f"ERROR {n_err} / WARN {n_warn}")

    if args.json:
        json.dump({"status_updated_at": status_at, "rows": rows, "released_not_in_catalog": missing},
                  open(args.json, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return 1 if n_err else 0


if __name__ == "__main__":
    sys.exit(main())
