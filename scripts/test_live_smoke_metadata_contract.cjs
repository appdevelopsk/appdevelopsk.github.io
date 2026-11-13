'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const root = path.join(__dirname, '..');

test('production smoke checks actual Debate Me SEO and OG metadata', () => {
  const html = fs.readFileSync(path.join(root, 'support/debate-me/index.html'), 'utf8');
  const smoke = fs.readFileSync(path.join(__dirname, 'check_app_discovery_live.sh'), 'utf8');
  const pageTitle = html.match(/<title>([^<]+)<\/title>/);
  const ogTitle = html.match(/<meta property="og:title" content="([^"]+)">/);
  assert.ok(pageTitle);
  assert.ok(ogTitle);
  assert.ok(smoke.includes('<title>' + pageTitle[1] + '</title>'));
  assert.ok(smoke.includes('<meta property="og:title" content="' + ogTitle[1] + '">'));
  assert.notEqual(pageTitle[1], ogTitle[1], 'separate SEO and sharing titles must not be conflated');
});

test('deploy smoke retains source truth and five-locale gate', () => {
  const smoke = fs.readFileSync(path.join(__dirname, 'check_app_discovery_live.sh'), 'utf8');
  assert.ok(smoke.includes("fetch '/support/debate-me/' 'debate-me.html'"));
  assert.ok(smoke.includes("fetch '/apps' 'apps.html'"));
  assert.ok(smoke.includes("for language in en ja es pt-BR id"));
  assert.ok(smoke.includes('catalog_language_selected'));
  assert.ok(!smoke.includes('rsync '));
});
