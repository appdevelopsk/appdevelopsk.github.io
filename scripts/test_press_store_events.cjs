'use strict';
// Offline browser-style contract for five localized press/creator pages.
// Run: node --test scripts/test_press_store_events.cjs
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const PAGES = {
  en: 'press/index.html',
  es: 'press/es/index.html',
  'pt-BR': 'press/pt-br/index.html',
  ja: 'press/ja/index.html',
  id: 'press/id/index.html',
};

function exercise(locale, cta) {
  const html = fs.readFileSync(path.join(__dirname, '..', PAGES[locale]), 'utf8');
  const scripts = [...html.matchAll(/<script(?:[^>]*)>([\s\S]*?)<\/script>/g)].map(m => m[1]);
  const handlers = scripts.filter(s => s.includes("'press_app_click'"));
  assert.equal(handlers.length, 1, 'one press click handler per locale');
  let onClick = null;
  const document = {
    documentElement: { lang: locale },
    addEventListener(event, callback, capture) {
      assert.equal(event, 'click');
      assert.equal(capture, true);
      onClick = callback;
    },
  };
  const context = { document, Date };
  context.window = context;
  vm.runInNewContext(handlers[0], context);
  assert.equal(typeof onClick, 'function');
  const values = {
    'data-app-slug': 'blur',
    'data-app-package': 'com.blurapp.blur_app',
    'data-cta': cta,
  };
  const anchor = { getAttribute: key => values[key] ?? null };
  onClick({ target: { closest: selector => {
    assert.equal(selector, 'a[data-cta]');
    return anchor;
  } } });
  return context.dataLayer
    .filter(row => row[0] === 'event')
    .map(row => ({ name: row[1], payload: JSON.parse(JSON.stringify(row[2])) }));
}

for (const locale of Object.keys(PAGES)) {
  test(locale + ': store click yields press event plus one unified outbound event', () => {
    const events = exercise(locale, 'store');
    assert.deepEqual(events.map(x => x.name), ['press_app_click', 'download_click']);
    assert.equal(events[0].payload.destination, 'store');
    assert.equal(events[0].payload.locale, locale);
    assert.equal(events[1].payload.store, 'google_play');
    assert.equal(events[1].payload.location, 'press');
    assert.equal(events[1].payload.placement, 'press_kit_card');
    assert.equal(events[1].payload.source, 'press_kit');
    assert.equal(events[1].payload.locale, locale);
    assert.equal(events[1].payload.app_slug, 'blur');
    assert.equal(events[1].payload.app_package, 'com.blurapp.blur_app');
    assert.equal(JSON.stringify(events).includes('link_url'), false);
    assert.equal(JSON.stringify(events).includes('query'), false);
  });

  test(locale + ': app detail click never fires a Play store event', () => {
    const events = exercise(locale, 'details');
    assert.deepEqual(events.map(x => x.name), ['press_app_click']);
    assert.equal(events[0].payload.destination, 'details');
  });
}
