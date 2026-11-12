'use strict';
// Offline exercise of the actual catalog localization IIFE (no network/DOM library).
// Run: node --test scripts/test_catalog_locale.cjs
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const html = fs.readFileSync(path.join(__dirname, '..', 'apps.html'), 'utf8');
const match = html.match(/<!-- CATALOG_LOCALE_START[^]*?<script>([^]*?)<\/script>\s*<!-- CATALOG_LOCALE_END -->/);
assert.ok(match && match[1], 'catalog locale controller should be embedded exactly once');
const code = match[1];

function boot(url, browserLanguage) {
  const nodes = new Map();
  const createNode = (textContent = '') => ({
    value: '', textContent, listeners: {}, attributes: {},
    addEventListener(name, callback) { this.listeners[name] = callback; },
    dispatchEvent(event) { if (this.listeners[event.type]) this.listeners[event.type](event); },
    setAttribute(name, value) { this.attributes[name] = value; },
  });
  for (const id of ['catalog-language', 'catalog-main-title', 'catalog-intro', 'finder-title',
                   'finder-empty-label', 'finder-reset', 'app-spotlight-title',
                   'catalog-spotlight-description', 'catalog-locale-notice', 'find-app']) {
    nodes.set(id, createNode());
  }
  const filters = Array.from({ length: 5 }, () => createNode());
  const links = ['Debate Me','Tappitsu Battle','FutureMe','Dotchi','Instant Judge']
    .map(name => createNode(name + ' · Original English'));
  const events = [];
  const window = {
    location: { href: url }, history: {
      state: {}, replaceState(state, title, route) {
        window.location.href = new URL(route, window.location.href).href;
      }
    },
    gtag(...args) { events.push(args); },
  };
  const document = {
    documentElement: { lang: 'en' },
    getElementById: id => nodes.get(id),
    querySelectorAll: selector => {
      if (selector === '.finder-filters button') return filters;
      if (selector === '[data-detail-app]') return links;
      throw Error('unexpected selector: ' + selector);
    },
  };
  vm.runInNewContext(code, {
    document, window, navigator: { languages: [browserLanguage] }, URL,
    URLSearchParams, Event: class { constructor(type) { this.type = type; } },
  });
  return { nodes, filters, links, events, window, document };
}

test('five-language finder preserves 92 catalog cards and original analytics', () => {
  assert.equal((html.match(/class="app-card"/g) || []).length, 92);
  for (const name of ['catalog_search_used', 'catalog_filter_used', 'download_click', 'catalog_store_click']) {
    assert.ok(html.includes(name), name + ' must remain present');
  }
});

test('explicit locale overrides browser language without analytics event', () => {
  const ui = boot('https://appdevelopsk.com/apps?goal=ai&lang=es', 'ja-JP');
  assert.equal(ui.document.documentElement.lang, 'es');
  assert.equal(ui.filters[1].textContent, 'Juegos rápidos');
  assert.equal(ui.window.catalogLocaleCount(7), '7 apps mostradas');
  assert.equal(ui.events.length, 0);
  assert.ok(ui.window.location.href.includes('goal=ai'));
  assert.ok(ui.window.catalogSearchAliases.twotaku.includes('encuesta'));
});

test('language change retains goal, tracks selected locale only', () => {
  const ui = boot('https://appdevelopsk.com/apps?goal=habits&lang=es', 'en-US');
  const picker = ui.nodes.get('catalog-language');
  picker.value = 'id';
  picker.listeners.change();
  assert.equal(ui.document.documentElement.lang, 'id');
  assert.equal(ui.window.catalogLocaleCount(2), '2 aplikasi ditampilkan');
  assert.equal(ui.events.length, 1);
  assert.equal(ui.events[0][1], 'catalog_language_selected');
  assert.deepEqual(Object.keys(ui.events[0][2]).sort(), ['locale','placement']);
  assert.equal(ui.events[0][2].locale, 'id');
  const updated = new URL(ui.window.location.href);
  assert.equal(updated.searchParams.get('goal'), 'habits');
  assert.equal(updated.searchParams.get('lang'), 'id');
});

test('invalid query locale falls back safely to browser locale', () => {
  const ui = boot('https://appdevelopsk.com/apps?lang=%3Cscript%3E', 'ja-JP');
  assert.equal(ui.document.documentElement.lang, 'ja');
  assert.equal(ui.nodes.get('catalog-main-title').textContent, 'アプリ一覧');
  assert.equal(ui.events.length, 0);
});
