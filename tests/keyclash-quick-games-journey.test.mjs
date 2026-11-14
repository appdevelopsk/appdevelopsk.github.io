import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { join } from 'node:path';

const root=process.cwd();
const en=readFileSync(join(root,'guides/quick-games/index.html'),'utf8');
const ja=readFileSync(join(root,'guides/quick-games/ja/index.html'),'utf8');
const support=readFileSync(join(root,'support/key-clash/index.html'),'utf8');

test('unverified Play app is not newly promoted by Quick Games guides', () => {
  assert.equal((en.match(/<article class="app">/g)||[]).length,5);
  assert.equal((ja.match(/<article class="app">/g)||[]).length,4);
  for(const html of [en,ja]){
    const s=JSON.parse(html.match(/<script type="application\/ld\+json">([^<]+)<\/script>/)[1]);
    assert.equal(s.itemListElement.length,(html.match(/<article class="app">/g)||[]).length);
    assert.equal(s.itemListElement.filter(x=>x.url.includes("com.keyclash.key_clash")).length,0);
  }
});

test('KeyClash support has a safe alternative path if Play is unavailable',()=>{
  assert.match(support,/If KeyClash is not listed on Google Play in your region/);
  assert.match(support,/href="\/guides\/quick-games\/"/);
  assert.match(support,/href="\/guides\/quick-games\/ja\/"/);
  assert.equal((support.match(/id="related-games"/g)||[]).length,1);
});

test('only one store-click event remains and support attribution is classified',()=>{
  assert.equal((support.match(/gtag\('event', 'download_click'/g)||[]).length,1);
  assert.ok(support.includes("app_slug: 'key-clash'"));
  assert.ok(support.includes('data-position="details"'));
  assert.ok(support.includes('<link rel="canonical" href="https://appdevelopsk.com/support/key-clash/">'));
});

test('existing bilingual guides retain original canonical and hreflang links',()=>{
  assert.ok(en.includes('<link rel="canonical" href="https://appdevelopsk.com/guides/quick-games/">'));
  assert.ok(ja.includes('<link rel="canonical" href="https://appdevelopsk.com/guides/quick-games/ja/">'));
  assert.ok(en.includes('hreflang="ja" href="https://appdevelopsk.com/guides/quick-games/ja/"'));
  assert.ok(ja.includes('hreflang="en" href="https://appdevelopsk.com/guides/quick-games/"'));
});
