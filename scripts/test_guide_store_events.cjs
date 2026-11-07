'use strict';
// Run from repository checkout: node --test scripts/test_guide_store_events.cjs
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const GUIDES = {
  'quick-games': 'a.store',
  'daily-habits': 'a.store',
  'decision-helpers': 'a.play',
  'ai-tools': 'a.play',
};

function exercise(guide, withGtag = true) {
  const html = fs.readFileSync(
    path.join(__dirname, '..', 'guides', guide, 'index.html'), 'utf8'
  );
  const scripts = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)]
    .map(m => m[1]);
  const handlerSource = scripts.filter(s => s.includes("'guide_store_click'"));
  assert.equal(handlerSource.length, 1, 'only one store analytics handler');
  const callbacks = {};
  const events = [];
  const anchor = {
    dataset: { app: 'known-app' },
    addEventListener(name, fn) { callbacks[name] = fn; },
  };
  const document = {
    querySelectorAll(selector) {
      assert.equal(selector, GUIDES[guide]);
      return [anchor];
    },
  };
  const window = {};
  if (withGtag) window.gtag = (...args) => events.push(args);
  vm.runInNewContext(handlerSource[0], { document, window });
  assert.equal(typeof callbacks.click, 'function');
  callbacks.click();
  return events;
}

for (const guide of Object.keys(GUIDES)) {
  test(guide + ': store click keeps legacy and unified event', () => {
    const events = exercise(guide);
    assert.equal(events.length, 2, 'exactly two distinct event names per click');
    assert.equal(events[0][0], 'event');
    assert.equal(events[0][1], 'guide_store_click');
    assert.equal(events[0][2].app, 'known-app');
    assert.equal(events[0][2].guide, guide);
    assert.equal(events[1][0], 'event');
    assert.equal(events[1][1], 'download_click');
    assert.equal(events[1][2].app_slug, 'known-app');
    assert.equal(events[1][2].guide, guide);
    assert.equal(events[1][2].store, 'google_play');
    assert.equal(events[1][2].location, 'guide');
    assert.equal(events[1][2].placement, 'guide_card');
    assert.equal(Object.hasOwn(events[1][2], 'link_url'), false);
  });

  test(guide + ': no GA4 is a safe no-op', () => {
    const events = exercise(guide, false);
    assert.equal(events.length, 0);
  });
}
