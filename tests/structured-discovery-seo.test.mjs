import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

const read = path => readFileSync(new URL('../' + path, import.meta.url), 'utf8');
const jsonLd = html => [...html.matchAll(/<script\s+type="application\/ld\+json">([\s\S]*?)<\/script>/g)]
  .map(match => JSON.parse(match[1]));

test('homepage declares a single canonical WebSite and real publisher', () => {
  const home = read('index.html');
  assert.match(home, /<link rel="canonical" href="https:\/\/appdevelopsk\.com\/"/);
  const schemas = jsonLd(home);
  const graph = schemas.find(x => x['@graph']?.some(n => n['@type'] === 'WebSite'));
  assert.ok(graph, 'missing WebSite graph');
  const site = graph['@graph'].find(x => x['@type'] === 'WebSite');
  const org = graph['@graph'].find(x => x['@type'] === 'Organization');
  assert.equal(site.url, 'https://appdevelopsk.com/');
  assert.equal(site.publisher['@id'], org['@id']);
  assert.equal(org.url, site.url);
  assert.ok(!JSON.stringify(graph).includes('SearchAction'), 'do not advertise a non-existent site-search URL');
});

test('catalog schema includes only published store listings in visible order', () => {
  const apps = JSON.parse(read('apps_data.json')).filter(x => !x.hidden);
  const schemas = jsonLd(read('apps.html'));
  const page = schemas.find(x => x['@type'] === 'CollectionPage');
  assert.ok(page, 'missing CollectionPage schema');
  const list = page.mainEntity;
  assert.equal(list['@type'], 'ItemList');
  assert.equal(list.numberOfItems, apps.length);
  assert.equal(list.itemListElement.length, apps.length);
  const seen = new Set();
  for (let i = 0; i < apps.length; i++) {
    const element = list.itemListElement[i];
    const app = apps[i];
    assert.equal(element.position, i + 1);
    assert.equal(element.name, app.title);
    assert.equal(element.url, 'https://play.google.com/store/apps/details?id=' + encodeURIComponent(app.pkg));
    assert.ok(!seen.has(element.url), 'duplicate store target');
    seen.add(element.url);
  }
  assert.equal(page.url, 'https://appdevelopsk.com/apps');
  assert.doesNotMatch(JSON.stringify(page), /aggregateRating|ratingValue|reviewCount/i);
});
