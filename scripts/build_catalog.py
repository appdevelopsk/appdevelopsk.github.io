#!/usr/bin/env python3
"""build_catalog.py — apps_data.json と site_counts.json から公開ページを組み立てる。

アプリ本数の表記が index.html / apps.html で 78+ / 98 / 110+ とバラバラだった
(2026-10-12 外部監査)。本数はここだけで決め、ページへ差し込む。

  apps_data.json   カタログの正本。"hidden" があるアプリはカードに出さない
                   (値は外した理由)。
  site_counts.json 基準日と「制作総数」。
      android_live  公開中の Android アプリ数 = apps_data.json の hidden 無し件数
                    (このスクリプトが毎回数え直して書き戻す)
      built_total   制作総数 = Google Play Console に登録したアプリ数
                    (本番未公開・審査前を含む)。--refresh-total で
                    play_production_refresh の台帳 summary.total から取り直す。
      as_of         上の2つの基準日(YYYY-MM-DD)

書き換える場所(いずれも冪等):
  apps.html   カード一覧(<div class="grid"> の中身)・本数の文言
  index.html  title/meta/og/twitter/About の「N Android Apps」、hero_badge(17言語)、
              通知欄の hint(本数を書いている言語だけ)、統計欄の「制作総数」と
              stat_apps / stats_asof(17言語)

使い方:
  python3 scripts/build_catalog.py                  # 書き換え
  python3 scripts/build_catalog.py --check          # 差分があれば exit 1(書き換えない)
  python3 scripts/build_catalog.py --refresh-total  # 台帳から built_total と as_of を更新
"""
import argparse
import datetime
import html
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
LEDGER = os.path.expanduser(
    "~/Library/Application Support/play_refresh/google_play_production_status.json")

CARD = """      <a class="app-card" href="https://play.google.com/store/apps/details?id={pkg}&amp;utm_source=appdevelopsk&amp;utm_medium=web&amp;utm_campaign=apps_catalog" target="_blank" rel="noopener">
        <img src="icons/apps/{app}.png" alt="{title} icon" loading="lazy" width="64" height="64">
        <div class="app-card-body">
          <h3>{title}</h3>
          <p>{desc}</p>
          <span class="store-badge">Google Play &rarr;</span>
        </div>
      </a>
"""

LANGS = ["en", "ja", "zh", "zh_TW", "ko", "es", "pt", "fr", "de", "it", "ru", "ar",
         "th", "id", "tr", "nl", "vi"]

# {n} = 公開中 Android 数
HERO_BADGE = {
    "en": "{n} Apps on Google Play",
    "ja": "Google Playで{n}アプリ配信中",
    "zh": "Google Play 上 {n} 款应用",
    "zh_TW": "Google Play 上 {n} 款應用",
    "ko": "Google Play에서 앱 {n}개 제공",
    "es": "{n} apps en Google Play",
    "pt": "{n} apps no Google Play",
    "fr": "{n} applis sur Google Play",
    "de": "{n} Apps bei Google Play",
    "it": "{n} app su Google Play",
    "ru": "Приложений в Google Play: {n}",
    "ar": "{n} تطبيقاً على Google Play",
    "th": "{n} แอปบน Google Play",
    "id": "{n} Aplikasi di Google Play",
    "tr": "Google Play'de {n} Uygulama",
    "nl": "{n} apps op Google Play",
    "vi": "{n} ứng dụng trên Google Play",
}

# 統計欄の「制作総数」の見出し
STAT_APPS = {
    "en": "Apps Built", "ja": "制作アプリ数", "zh": "已开发应用", "zh_TW": "已開發應用",
    "ko": "제작한 앱", "es": "Apps creadas", "pt": "Apps criados", "fr": "Applis créées",
    "de": "Entwickelte Apps", "it": "App create", "ru": "Создано приложений",
    "ar": "تطبيقات مطوَّرة", "th": "แอปที่พัฒนา", "id": "Aplikasi Dibuat",
    "tr": "Geliştirilen Uygulama", "nl": "Gemaakte apps", "vi": "Ứng dụng đã làm",
}

# {d} = 基準日
STATS_ASOF = {
    "en": "As of {d}. Apps built includes apps not yet released.",
    "ja": "{d} 時点。制作アプリ数は未公開のアプリを含みます。",
    "zh": "截至 {d}。已开发应用包含尚未发布的应用。",
    "zh_TW": "截至 {d}。已開發應用包含尚未發布的應用。",
    "ko": "{d} 기준. 제작한 앱에는 아직 공개하지 않은 앱이 포함됩니다.",
    "es": "Datos a {d}. Las apps creadas incluyen las aún no publicadas.",
    "pt": "Dados de {d}. Os apps criados incluem os ainda não publicados.",
    "fr": "Chiffres au {d}. Les applis créées incluent celles pas encore publiées.",
    "de": "Stand {d}. Entwickelte Apps schließen noch nicht veröffentlichte ein.",
    "it": "Dati al {d}. Le app create includono quelle non ancora pubblicate.",
    "ru": "Данные на {d}. Включая ещё не опубликованные приложения.",
    "ar": "حتى {d}. يشمل عدد التطبيقات المطوَّرة تطبيقات لم تُنشر بعد.",
    "th": "ข้อมูล ณ {d} จำนวนแอปที่พัฒนารวมแอปที่ยังไม่เผยแพร่",
    "id": "Per {d}. Aplikasi dibuat termasuk yang belum dirilis.",
    "tr": "{d} itibarıyla. Geliştirilen uygulamalara henüz yayınlanmayanlar dahildir.",
    "nl": "Stand {d}. Gemaakte apps omvatten nog niet gepubliceerde apps.",
    "vi": "Tính đến {d}. Số ứng dụng đã làm gồm cả ứng dụng chưa phát hành.",
}

# 通知欄の hint は本数を書いている言語だけ差し込む(他言語は本数を書いていない)
NOTIFY_HINT = {
    "en": "🚀 {n} apps on Google Play — get notified about new releases",
    "es": "🚀 {n} apps en Google Play — te avisamos de novedades",
    "de": "🚀 {n} Apps bei Google Play — wir informieren über Neues",
    "ru": "🚀 Приложений в Google Play: {n} — сообщим о новинках",
    "id": "🚀 {n} aplikasi di Google Play — kabari soal rilis baru",
    "tr": "🚀 Google Play'de {n} uygulama — yeni çıkanları bildiririz",
    "nl": "🚀 {n} apps op Google Play — we melden nieuwe releases",
    "vi": "🚀 {n} ứng dụng trên Google Play — báo bạn app mới",
}


def js_str(s):
    return s.replace("\\", "\\\\").replace('"', '\\"')


def sub1(pattern, repl, text, what, flags=0):
    new, n = re.subn(pattern, repl, text, count=1, flags=flags)
    if n != 1:
        sys.exit(f"build_catalog: {what} が見つからない(ページの構造が変わった?)")
    return new


def load_counts(apps, refresh_total):
    p = os.path.join(REPO, "site_counts.json")
    c = json.load(open(p, encoding="utf-8")) if os.path.exists(p) else {}
    if refresh_total:
        led = json.load(open(LEDGER, encoding="utf-8"))
        c["built_total"] = led["summary"]["total"]
        c["as_of"] = led["updated_at"][:10]
    c["android_live"] = sum(1 for a in apps if not a.get("hidden"))
    for k in ("built_total", "as_of"):
        if k not in c:
            sys.exit(f"build_catalog: site_counts.json に {k} が無い(--refresh-total で作る)")
    datetime.date.fromisoformat(c["as_of"])
    return p, c


def build_apps_html(t, apps, n):
    cards = "".join(CARD.format(pkg=a["pkg"], app=a["app"], title=html.escape(a["title"]),
                                desc=html.escape(a["desc"]))
                    for a in apps if not a.get("hidden"))
    t = sub1(r'(<div class="grid">\n).*?(    </div>\n  </main>)',
             lambda m: m.group(1) + cards + m.group(2), t, "apps.html の grid", re.S)
    t = re.sub(r"Browse all \d+ mobile apps", f"Browse all {n} mobile apps", t)
    t = sub1(r"<p>\d+ free apps on Google Play", f"<p>{n} free apps on Google Play", t,
             "apps.html の見出し文")
    return t


def build_index_html(t, n, built, as_of):
    t = re.sub(r"\b\d+ Android [Aa]pps\b", lambda m: re.sub(r"^\d+", str(n), m.group(0)), t)
    t = re.sub(r"Games, tools, AI-powered apps and more\. \d+ apps crafted",
               f"Games, tools, AI-powered apps and more. {n} apps crafted", t)
    # 初期表示(JS 前)の英語
    t = sub1(r'(data-i18n="hero_badge">)[^<]*(<)',
             lambda m: m.group(1) + HERO_BADGE["en"].format(n=n) + m.group(2), t, "hero-badge")
    t = sub1(r'(<p id="notifyMsg"[^>]*>)[^<]*(<)',
             lambda m: m.group(1) + NOTIFY_HINT["en"].format(n=n) + m.group(2), t, "notifyMsg")
    t = sub1(r'(<div class="stat-number">)[^<]*(</div>\s*<div class="stat-label" data-i18n="stat_apps">)[^<]*(<)',
             lambda m: m.group(1) + str(built) + m.group(2) + STAT_APPS["en"] + m.group(3),
             t, "統計欄 stat_apps")
    asof_html = f'<p class="stats-asof" data-i18n="stats_asof">{STATS_ASOF["en"].format(d=as_of)}</p>'
    if 'data-i18n="stats_asof"' in t:
        t = sub1(r'<p class="stats-asof" data-i18n="stats_asof">[^<]*</p>', asof_html, t, "stats_asof")
    else:
        # 統計欄(<div class="stats">…</div>)の直後に置く
        t = sub1(r'(<!-- Stats -->\n<div class="stats">.*?\n</div>\n)',
                 lambda m: m.group(1) + asof_html + "\n", t, "統計欄の終わり", re.S)

    # I18N 辞書(言語ブロックごと)
    i18n_start = t.index("const I18N = {")
    starts = []
    for lang in LANGS:
        m = re.compile(r"^  " + lang + r": \{$", re.M).search(t, i18n_start)
        if not m:
            sys.exit(f"build_catalog: I18N.{lang} が見つからない")
        starts.append((m.start(), lang))
    starts.sort()
    out, prev = [], 0
    for i, (s, lang) in enumerate(starts):
        e = starts[i + 1][0] if i + 1 < len(starts) else t.index("\n};", s)
        out.append(t[prev:s])
        b = t[s:e]
        b = sub1(r'(hero_badge: ")[^"]*(")',
                 lambda m: m.group(1) + js_str(HERO_BADGE[lang].format(n=n)) + m.group(2),
                 b, f"I18N.{lang}.hero_badge")
        b = sub1(r'(stat_apps: ")[^"]*(")',
                 lambda m: m.group(1) + js_str(STAT_APPS[lang]) + m.group(2), b, f"I18N.{lang}.stat_apps")
        asof = js_str(STATS_ASOF[lang].format(d=as_of))
        if "stats_asof:" in b:
            b = sub1(r'(stats_asof: ")[^"]*(")', lambda m: m.group(1) + asof + m.group(2),
                     b, f"I18N.{lang}.stats_asof")
        else:
            b = sub1(r'(stat_categories: "[^"]*")', lambda m: m.group(1) + f', stats_asof: "{asof}"',
                     b, f"I18N.{lang}.stat_categories")
        out.append(b)
        prev = e
    out.append(t[prev:])
    t = "".join(out)

    # 通知欄の hint
    ns = t.index("const NOTIFY={")
    for lang, tpl in NOTIFY_HINT.items():
        pat = re.compile(r'(^' + lang + r':\{btn:"[^"]*",hint:")[^"]*(")', re.M)
        m = pat.search(t, ns)
        if not m:
            sys.exit(f"build_catalog: NOTIFY.{lang} が見つからない")
        t = t[:m.start()] + m.group(1) + js_str(tpl.format(n=n)) + m.group(2) + t[m.end():]
    return t


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--refresh-total", action="store_true")
    args = ap.parse_args()

    apps = json.load(open(os.path.join(REPO, "apps_data.json"), encoding="utf-8"))
    for a in apps:
        if not a.get("hidden") and not os.path.exists(os.path.join(REPO, "icons/apps", a["app"] + ".png")):
            sys.exit(f"build_catalog: アイコンが無い icons/apps/{a['app']}.png")
    cpath, c = load_counts(apps, args.refresh_total)
    n, built, as_of = c["android_live"], c["built_total"], c["as_of"]

    changed = []
    for f, fn in (("apps.html", lambda t: build_apps_html(t, apps, n)),
                  ("index.html", lambda t: build_index_html(t, n, built, as_of))):
        p = os.path.join(REPO, f)
        old = open(p, encoding="utf-8").read()
        new = fn(old)
        if new != old:
            changed.append(f)
            if not args.check:
                open(p, "w", encoding="utf-8").write(new)
    counts_txt = json.dumps(c, ensure_ascii=False, indent=1) + "\n"
    old_counts = open(cpath, encoding="utf-8").read() if os.path.exists(cpath) else ""
    if counts_txt != old_counts:
        changed.append("site_counts.json")
        if not args.check:
            open(cpath, "w", encoding="utf-8").write(counts_txt)

    print(f"公開中 Android {n} 本 / 制作総数 {built} 本 / 基準日 {as_of}"
          f" / {'差分あり' if changed else '差分なし'}: {', '.join(changed) or '-'}")
    return 1 if (args.check and changed) else 0


if __name__ == "__main__":
    sys.exit(main())
