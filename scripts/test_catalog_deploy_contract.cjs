'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const root = path.join(__dirname, '..');
const catalog = fs.readFileSync(path.join(root, 'apps.html'), 'utf8');
const releaseSmoke = fs.readFileSync(path.join(__dirname, 'check_app_discovery_live.sh'), 'utf8');

test('the live gate checks all five source locale choices', () => {
  for (const lang of ['en', 'ja', 'es', 'pt-BR', 'id']) {
    assert.ok(catalog.includes('option value="' + lang + '"'), lang + ' missing from source');
  }
  assert.ok(releaseSmoke.includes('for language in en ja es pt-BR id'));
  assert.ok(releaseSmoke.includes('catalog_language_selected'));
  assert.ok(releaseSmoke.includes('id="catalog-language"'));
  assert.ok(releaseSmoke.includes('CATALOG_LOCALE_START'));
});

test('catalog remains complete and existing analytics are preserved', () => {
  assert.equal((catalog.match(/class="app-card"/g) || []).length, 92);
  assert.match(catalog, /"numberOfItems": 92/);
  for (const event of ['download_click', 'catalog_store_click', 'catalog_search_used']) {
    assert.ok(catalog.includes(event), event);
  }
  assert.ok(catalog.includes('catalog_language_selected'));
});

test('the live gate is read-only and preserves fail-fast behavior', () => {
  assert.ok(releaseSmoke.includes("fetch '/apps' 'apps.html'"));
  assert.ok(releaseSmoke.includes('exit 1'));
  assert.ok(!releaseSmoke.includes('rsync '), 'live smoke must not deploy');
  assert.ok(!releaseSmoke.includes('ssh '), 'live smoke must not mutate remote host');
});
