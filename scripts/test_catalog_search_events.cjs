'use strict';
// Run from repository root: node --test scripts/test_catalog_search_events.cjs
// Execute the actual catalog's input/reporting handlers in an isolated VM.
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const html = fs.readFileSync(path.join(__dirname, '..', 'apps.html'), 'utf8');
const start = html.indexOf('    const reportSearch = () => {');
const after = html.indexOf("    input.addEventListener('keydown', event => {", start);
const end = html.indexOf('    });', after) + '    });'.length;
assert.ok(start >= 0 && after > start && end > after, 'search handlers are present');
const handlers = html.slice(start, end);

function setup() {
  const events = [];
  const listeners = {};
  const input = {
    value: '',
    addEventListener(type, callback) { listeners[type] = callback; },
  };
  const context = {
    input,
    clean: v => v.normalize('NFKC').toLocaleLowerCase().trim(),
    render: () => 4,
    fire: (name, payload) => events.push({ name, ...payload }),
  };
  vm.runInNewContext("let lastReportedSearch = '';\n" + handlers + "\nglobalThis.commitSearch = reportSearch;", context);
  assert.equal(typeof listeners.input, 'function');
  assert.equal(typeof listeners.blur, 'function');
  assert.equal(typeof listeners.keydown, 'function');
  return { input, events, listeners, commit: context.commitSearch };
}

test('typing does not send an unfinished search', () => {
  const h = setup();
  h.input.value = 'do';
  h.listeners.input();
  assert.equal(h.events.length, 0);
});

test('Enter emits exactly one committed search', () => {
  const h = setup();
  h.input.value = 'dotchi';
  h.listeners.input();
  h.listeners.keydown({ key: 'Enter' });
  h.listeners.blur();
  assert.equal(h.events.length, 1);
  assert.equal(h.events[0].name, 'catalog_search_used');
  assert.equal(h.events[0].results, 4);
  assert.equal(h.events[0].search_length_band, 'long');
});

test('browser search clear allows the same query to count again', () => {
  const h = setup();
  h.input.value = 'dotchi';
  h.listeners.input();
  h.listeners.blur();
  h.input.value = '';
  h.listeners.input();
  h.input.value = 'dotchi';
  h.listeners.input();
  h.listeners.blur();
  assert.equal(h.events.length, 2);
});

test('clearing a search does not emit a blank query', () => {
  const h = setup();
  h.input.value = '   ';
  h.listeners.input();
  h.listeners.blur();
  assert.equal(h.events.length, 0);
});

test('repeated blur without a cleared search is deduplicated', () => {
  const h = setup();
  h.input.value = 'sleep';
  h.listeners.input();
  h.listeners.blur();
  h.listeners.blur();
  assert.equal(h.events.length, 1);
});

test('committed searches never send raw query text', () => {
  const h = setup();
  h.input.value = 'sensitive private query';
  h.listeners.input();
  h.listeners.blur();
  assert.equal(h.events.length, 1);
  assert.equal(JSON.stringify(h.events).includes('sensitive'), false);
});
