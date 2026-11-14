import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { join } from 'node:path';

const root=process.cwd();
const en=readFileSync(join(root,'guides/quick-games/index.html'),'utf8');
const ja=readFileSync(join(root,'guides/quick-games/ja/index.html'),'utf8');
const support=readFileSync(join(root,'support/key-clash/index.html'),'utf8');

for(const [locale,html,count] of [['en',en,6],['ja',ja,5]]) {
  test(`${locale}: Quick Games count, schema and real card identifiers stay aligned`,()=>{
    assert.ok(html.includes(`<html lang="${locale}"`));
    const schema=JSON.parse(html.match(/<script type="application\/ld\+json">([^<]+)<\/script>/)[1]);
    assert.equal(schema['@type'],'ItemList');
    assert.equal(schema.itemListElement.length,count);
    assert.deepEqual(schema.itemListElement.map(x=>x.position),Array.from({length:count},(_,i)=>i+1));
    assert.equal((html.match(/<article class="app">/g)||[]).length,count);
    assert.ok(schema.itemListElement.some(x=>x.url==='https://play.google.com/store/apps/details?id=com.keyclash.key_clash'));
    assert.ok(html.includes('data-app="key-clash"'));
    assert.ok(html.includes('href="/support/key-clash/"'));
    assert.ok(html.includes('com.keyclash.key_clash&amp;'));
    assert.ok(html.includes("download_click"));
    assert.ok(html.includes("app_detail_click"));
  });
}

test('KeyClash support offers two ways back to a localized choice guide',()=>{
  assert.match(support,/href="\/guides\/quick-games\/"/);
  assert.match(support,/href="\/guides\/quick-games\/ja\/"/);
  assert.equal((support.match(/id="related-games"/g)||[]).length,1);
  assert.ok(support.includes('https://play.google.com/store/apps/details?id=com.keyclash.key_clash'));
  assert.equal((support.match(/gtag\('event', 'download_click'/g)||[]).length,1);
  assert.ok(support.includes("app_slug: 'key-clash'"));
  assert.ok(support.includes('data-position="details"'));
});

test('existing canonical and language pairing remain correct',()=>{
  assert.ok(en.includes('<link rel="canonical" href="https://appdevelopsk.com/guides/quick-games/">'));
  assert.ok(ja.includes('<link rel="canonical" href="https://appdevelopsk.com/guides/quick-games/ja/">'));
  assert.ok(en.includes('hreflang="ja" href="https://appdevelopsk.com/guides/quick-games/ja/"'));
  assert.ok(ja.includes('hreflang="en" href="https://appdevelopsk.com/guides/quick-games/"'));
  assert.ok(support.includes('<link rel="canonical" href="https://appdevelopsk.com/support/key-clash/">'));
});
