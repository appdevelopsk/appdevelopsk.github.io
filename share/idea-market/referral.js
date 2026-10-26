'use strict';
// This static landing does NOT request idea details and does not track tokens.
// Only harmless alphanumeric IDs are used to build an app-specific URI.
(() => {
  const id = new URLSearchParams(location.search).get('id') ?? '';
  const validId = /^[a-zA-Z0-9_-]{1,96}$/.test(id);
  const open = document.getElementById('open-app');
  const error = document.getElementById('error');
  if (validId) {
    open.href = 'ideamarket://open/ideas/' + encodeURIComponent(id);
    open.hidden = false;
  } else {
    error.hidden = false;
  }
  if (navigator.language?.toLowerCase().startsWith('ja')) {
    document.getElementById('title').textContent = 'アイデアが共有されました';
    document.getElementById('intro').textContent = 'Idea Marketアプリで共有されたアイデアを開けます。購入前の非公開情報はこのページに表示しません。';
    open.textContent = 'アプリでアイデアを開く';
    error.textContent = '共有リンクを確認できません。もう一度共有してもらってください。';
  }
})();
