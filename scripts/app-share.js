/* Small opt-in support-page sharing surface. No accounts, cookies, third-party SDK
 * or automatic social posting. A share_tap is only an intent, not a verified
 * referral session or an app install. */
(function () {
  "use strict";
  var TITLES = {
    "debate-me": "Debate Me",
    "future-me": "FutureMe",
    "tappitsu-battle": "Tappitsu Battle"
  };
  var TEXT = {
    en: ["Share this app", "Link copied", "Copy this link:"],
    ja: ["このアプリを共有", "リンクをコピーしました", "リンクをコピーしてください:"],
    zh: ["分享此应用", "链接已复制", "请复制此链接:"],
    zh_TW: ["分享此應用程式", "連結已複製", "請複製此連結:"],
    ko: ["앱 공유하기", "링크 복사됨", "링크를 복사하세요:"],
    es: ["Compartir aplicación", "Enlace copiado", "Copia este enlace:"],
    pt: ["Compartilhar aplicativo", "Link copiado", "Copie este link:"],
    fr: ["Partager l'application", "Lien copié", "Copiez ce lien :"],
    de: ["App teilen", "Link kopiert", "Link kopieren:"],
    it: ["Condividi app", "Link copiato", "Copia il link:"],
    ru: ["Поделиться приложением", "Ссылка скопирована", "Скопируйте ссылку:"],
    ar: ["مشاركة التطبيق", "تم نسخ الرابط", "انسخ هذا الرابط:"],
    th: ["แชร์แอป", "คัดลอกลิงก์แล้ว", "คัดลอกลิงก์นี้:"],
    id: ["Bagikan aplikasi", "Tautan disalin", "Salin tautan ini:"],
    tr: ["Uygulamayı paylaş", "Bağlantı kopyalandı", "Bu bağlantıyı kopyalayın:"],
    nl: ["App delen", "Link gekopieerd", "Kopieer deze link:"],
    vi: ["Chia sẻ ứng dụng", "Đã sao chép liên kết", "Sao chép liên kết:"]
  };

  function buildShareUrl(slug) {
    if (!Object.prototype.hasOwnProperty.call(TITLES, slug)) return null;
    // Never copy query strings, fragments or credentials from the browser URL.
    var url = new URL("/support/" + slug + "/", "https://appdevelopsk.com");
    url.searchParams.set("utm_source", "reader_share");
    url.searchParams.set("utm_medium", "referral");
    url.searchParams.set("utm_campaign", "app_support_share");
    url.searchParams.set("utm_content", slug);
    return url.toString();
  }

  // Allow Node regression tests to validate the *same* URL builder offline.
  if (typeof module === "object" && module.exports) {
    module.exports = { buildShareUrl: buildShareUrl, TEXT: TEXT };
    return;
  }
  if (typeof document === "undefined") return;

  var script = document.querySelector("script[data-app-share-slug]");
  var slug = script && script.getAttribute("data-app-share-slug");
  if (!slug || !Object.prototype.hasOwnProperty.call(TITLES, slug)) return;
  if (window.location.pathname.replace(/\/$/, "") !== "/support/" + slug) return;
  var group = document.querySelector(".hero .download-btns");
  if (!group) return;
  var button = document.createElement("button");
  button.type = "button";
  button.className = "dl-btn dl-btn-apple";
  button.style.cursor = "pointer";
  button.setAttribute("data-app-share", slug);
  var status = document.createElement("p");
  status.setAttribute("role", "status");
  status.setAttribute("aria-live", "polite");
  status.style.cssText = "margin:8px auto 0;font-size:0.82rem;max-width:600px;";
  var manual = null;

  function lang() {
    try {
      var saved = window.localStorage.getItem("sk_lang");
      if (Object.prototype.hasOwnProperty.call(TEXT, saved)) return saved;
    } catch (_) { /* Browsers may block storage. */ }
    var raw = document.documentElement.lang || (navigator.language || "en");
    if (Object.prototype.hasOwnProperty.call(TEXT, raw)) return raw;
    return raw.split(/[-_]/)[0] in TEXT ? raw.split(/[-_]/)[0] : "en";
  }
  function labels() { return TEXT[lang()] || TEXT.en; }
  function updateLanguage() {
    button.textContent = labels()[0];
    button.setAttribute("aria-label", labels()[0] + " — " + TITLES[slug]);
  }

  function measure(name, method) {
    if (window.location.hostname !== "appdevelopsk.com" &&
        window.location.hostname !== "www.appdevelopsk.com") return;
    if (typeof window.gtag !== "function") return;
    window.gtag("event", name, {
      app_slug: slug, placement: "support_hero", share_method: method
    });
  }

  button.addEventListener("click", async function () {
    var link = buildShareUrl(slug);
    if (!link) return;
    status.textContent = "";
    if (manual) { manual.remove(); manual = null; }
    measure("share_tap", "button"); // A tap is not a confirmed share.
    if (typeof navigator.share === "function") {
      try {
        await navigator.share({ title: TITLES[slug], url: link });
        return;
      } catch (error) {
        if (error && error.name === "AbortError") return;
      }
    }
    try {
      if (!navigator.clipboard || !navigator.clipboard.writeText) throw new Error("clipboard unavailable");
      await navigator.clipboard.writeText(link);
      status.textContent = labels()[1];
      measure("share_copy_success", "clipboard");
    } catch (_) {
      // Restricted browsers: let the reader copy a visible, selectable link.
      manual = document.createElement("input");
      manual.type = "text";
      manual.readOnly = true;
      manual.value = link;
      manual.setAttribute("aria-label", labels()[2]);
      manual.style.cssText = "display:block;width:min(95%,570px);margin:8px auto 0;padding:8px;border-radius:6px;";
      status.textContent = labels()[2];
      status.appendChild(manual);
      manual.addEventListener("focus", function () { manual.select(); });
    }
  });

  group.appendChild(button);
  group.parentNode.appendChild(status);
  updateLanguage();
  var langNode = document.getElementById("langLabel");
  if (langNode && typeof MutationObserver === "function") {
    new MutationObserver(updateLanguage).observe(langNode, {
      childList: true, characterData: true, subtree: true
    });
  }
})();
