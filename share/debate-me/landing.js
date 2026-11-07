'use strict';
(() => {
  // Navigation only. No device identifiers, debate content or app-open redirects.
  const I18N = {
  "en": {
    "intro": "Practice a three-round debate with an AI opponent, then get feedback on your arguments.",
    "android": "Get it on Google Play",
    "ios": "Open in the App Store",
    "availability": "Store availability may vary by region.",
    "privacy": "Privacy policy",
    "otherApps": "Explore other SK APPS"
  },
  "ja": {
    "intro": "AIを相手に3ラウンドのディベートを練習し、議論へのフィードバックを確認できます。",
    "android": "Google Playで見る",
    "ios": "App Storeで見る",
    "availability": "ストアでの提供状況は地域によって異なります。",
    "privacy": "プライバシーポリシー",
    "otherApps": "他のSK APPSを見る"
  },
  "zh": {
    "intro": "与AI对手进行三轮辩论练习，并获得论点反馈。",
    "android": "在Google Play查看",
    "ios": "在App Store查看",
    "availability": "商店提供情况可能因地区而异。",
    "privacy": "隐私政策",
    "otherApps": "探索其他SK APPS"
  },
  "zh_TW": {
    "intro": "與AI對手進行三回合辯論練習，並獲得論點回饋。",
    "android": "在Google Play查看",
    "ios": "在App Store查看",
    "availability": "商店提供情況可能因地區而異。",
    "privacy": "隱私權政策",
    "otherApps": "探索其他SK APPS"
  },
  "ko": {
    "intro": "AI 상대와 3라운드 토론을 연습하고 주장에 대한 피드백을 받아보세요.",
    "android": "Google Play에서 보기",
    "ios": "App Store에서 보기",
    "availability": "스토어 제공 여부는 지역에 따라 다릅니다.",
    "privacy": "개인정보 처리방침",
    "otherApps": "다른 SK APPS 보기"
  },
  "es": {
    "intro": "Practica un debate de tres rondas con una IA y recibe comentarios sobre tus argumentos.",
    "android": "Ver en Google Play",
    "ios": "Ver en App Store",
    "availability": "La disponibilidad varía según la región.",
    "privacy": "Política de privacidad",
    "otherApps": "Explorar otras apps"
  },
  "pt": {
    "intro": "Pratique um debate de três rodadas com uma IA e receba comentários sobre seus argumentos.",
    "android": "Ver no Google Play",
    "ios": "Ver na App Store",
    "availability": "A disponibilidade varia conforme a região.",
    "privacy": "Política de privacidade",
    "otherApps": "Explorar outros aplicativos"
  },
  "fr": {
    "intro": "Entraînez-vous à débattre en trois manches avec une IA et recevez des commentaires sur vos arguments.",
    "android": "Voir sur Google Play",
    "ios": "Voir sur l’App Store",
    "availability": "La disponibilité varie selon la région.",
    "privacy": "Politique de confidentialité",
    "otherApps": "Explorer les autres apps"
  },
  "de": {
    "intro": "Übe eine Debatte über drei Runden mit einer KI und erhalte Feedback zu deinen Argumenten.",
    "android": "Bei Google Play ansehen",
    "ios": "Im App Store ansehen",
    "availability": "Die Verfügbarkeit hängt von der Region ab.",
    "privacy": "Datenschutzerklärung",
    "otherApps": "Weitere SK APPS entdecken"
  },
  "it": {
    "intro": "Allenati in un dibattito di tre turni con un'IA e ricevi feedback sulle tue argomentazioni.",
    "android": "Vedi su Google Play",
    "ios": "Vedi su App Store",
    "availability": "La disponibilità varia in base alla regione.",
    "privacy": "Informativa sulla privacy",
    "otherApps": "Scopri altre app"
  },
  "ru": {
    "intro": "Потренируйтесь в трёх раундах дебатов с ИИ и получите отзыв о своих аргументах.",
    "android": "Открыть в Google Play",
    "ios": "Открыть в App Store",
    "availability": "Доступность зависит от региона.",
    "privacy": "Политика конфиденциальности",
    "otherApps": "Другие приложения"
  },
  "ar": {
    "intro": "تدرّب على مناظرة من ثلاث جولات مع الذكاء الاصطناعي واحصل على ملاحظات حول حججك.",
    "android": "عرض في Google Play",
    "ios": "عرض في App Store",
    "availability": "قد يختلف التوفر حسب المنطقة.",
    "privacy": "سياسة الخصوصية",
    "otherApps": "استكشف تطبيقات أخرى"
  },
  "th": {
    "intro": "ฝึกโต้วาที 3 รอบกับ AI และรับคำแนะนำเกี่ยวกับเหตุผลของคุณ",
    "android": "ดูใน Google Play",
    "ios": "ดูใน App Store",
    "availability": "การให้บริการอาจแตกต่างกันตามภูมิภาค",
    "privacy": "นโยบายความเป็นส่วนตัว",
    "otherApps": "สำรวจแอปอื่น"
  },
  "id": {
    "intro": "Latih debat tiga ronde melawan AI dan dapatkan masukan atas argumen Anda.",
    "android": "Lihat di Google Play",
    "ios": "Lihat di App Store",
    "availability": "Ketersediaan dapat berbeda menurut wilayah.",
    "privacy": "Kebijakan privasi",
    "otherApps": "Jelajahi aplikasi lain"
  },
  "tr": {
    "intro": "Yapay zekâ ile üç turluk tartışma yap ve argümanların için geri bildirim al.",
    "android": "Google Play'de görüntüle",
    "ios": "App Store'da görüntüle",
    "availability": "Mağaza erişimi bölgeye göre değişebilir.",
    "privacy": "Gizlilik politikası",
    "otherApps": "Diğer uygulamaları keşfet"
  },
  "nl": {
    "intro": "Oefen een debat van drie rondes met AI en krijg feedback op je argumenten.",
    "android": "Bekijk in Google Play",
    "ios": "Bekijk in de App Store",
    "availability": "Beschikbaarheid verschilt per regio.",
    "privacy": "Privacybeleid",
    "otherApps": "Ontdek andere apps"
  },
  "vi": {
    "intro": "Luyện tranh luận ba vòng với AI và nhận phản hồi về lập luận của bạn.",
    "android": "Xem trên Google Play",
    "ios": "Xem trên App Store",
    "availability": "Tính khả dụng có thể khác theo khu vực.",
    "privacy": "Chính sách quyền riêng tư",
    "otherApps": "Khám phá ứng dụng khác"
  }
};
  const browser = (navigator.language || 'en').replace('-', '_');
  const lang = I18N[browser] ? browser :
    (browser.toLowerCase().startsWith('zh_tw') || browser.toLowerCase().startsWith('zh_hk')) ? 'zh_TW' :
    (I18N[browser.split('_')[0]] ? browser.split('_')[0] : 'en');
  document.documentElement.lang = lang.replace('_', '-');
  if (lang === 'ar') document.documentElement.dir = 'rtl';
  const strings = I18N[lang] || I18N.en;
  document.querySelectorAll('[data-copy]').forEach((element) => {
    const key = element.getAttribute('data-copy');
    if (Object.prototype.hasOwnProperty.call(strings, key)) {
      element.textContent = strings[key];
    }
  });

  const allowedSources = new Set(['home', 'settings', 'result']);
  const source = new URLSearchParams(location.search).get('src');
  const tag = allowedSources.has(source) ? source : 'generic';
  const play = document.getElementById('android');
  const url = new URL(play.href);
  // Play Install Referrer may be useful for measurement if available, but
  // no click here proves an install. No personal or arbitrary URL values.
  url.searchParams.set('referrer',
    'utm_source=skapps&utm_medium=share&utm_campaign=debate_me_' + tag);
  play.href = url.toString();
})();
