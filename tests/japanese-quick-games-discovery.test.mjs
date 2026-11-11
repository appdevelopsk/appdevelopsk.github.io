import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
const read = p => readFileSync(new URL('../'+p, import.meta.url),'utf8');
const ja = read('guides/quick-games/ja/index.html');
const en = read('guides/quick-games/index.html');
const sitemap = read('sitemap.xml');
const apps = JSON.parse(read('apps_data.json'));
const base='https://appdevelopsk.com/guides/quick-games/';
const jaUrl=base+'ja/';

test('Japanese page has unique canonical, accurate locale and reciprocal hreflang',()=>{
 assert.match(ja,/<html lang="ja">/);
 assert.match(ja,new RegExp('<link rel="canonical" href="'+jaUrl.replaceAll('.','\\.')+'">'));
 for (const page of [ja,en]) {
  assert.ok(page.includes('hreflang="ja" href="'+jaUrl+'"'));
  assert.ok(page.includes('hreflang="en" href="'+base+'"'));
  assert.ok(page.includes('hreflang="x-default" href="'+base+'"'));
 }
 assert.match(ja,/<h1>すきま時間に遊べるAndroidゲームを選ぶ<\/h1>/);
 assert.doesNotMatch(ja,/aggregateRating|reviewCount|ratingValue/);
});

test('Japanese guide only promotes four real catalog apps with the correct Android package',()=>{
 const links=[...ja.matchAll(/<a class="store" data-app="([^"]+)" href="([^"]+)"/g)];
 assert.equal(links.length,4);
 const slugs=['blur','twotaku','instant-judge','brain-burst'];
 assert.deepEqual(links.map(x=>x[1]),slugs);
 for (const [,slug,url] of links) {
  const item=apps.find(a=>a.app===slug&&!a.hidden);
  assert.ok(item,'missing visible catalog app '+slug);
  assert.ok(url.includes('id='+item.pkg),slug+' package mismatch');
  assert.ok(url.includes('referrer=utm_source%3Dappdevelopsk'),slug+' referrer absent');
  assert.ok(url.includes('utm_campaign=quick_games_ja'));
  assert.ok(!/itunes\.apple\.com|apps\.apple\.com/.test(url));
 }
});

test('Japanese guide is discoverable and uses existing anonymous event names',()=>{
 assert.equal((sitemap.match(/<loc>https:\/\/appdevelopsk\.com\/guides\/quick-games\/ja\/<\/loc>/g)||[]).length,1);
 assert.match(ja,/guide_store_click/);
 assert.match(ja,/download_click/);
 assert.match(ja,/app_detail_click/);
 assert.match(ja,/placement:'guide_card'/);
 assert.doesNotMatch(ja,/document\.querySelector\(['"]input|search_text|email_address|user_id/);
});

test('JSON-LD names map directly to the four app listings without invented ratings',()=>{
 const raw=ja.match(/<script type="application\/ld\+json">([^<]+)<\/script>/)?.[1];
 assert.ok(raw);
 const data=JSON.parse(raw);
 assert.equal(data['@type'],'ItemList');
 assert.equal(data.inLanguage,'ja');
 assert.equal(data.itemListElement.length,4);
 assert.deepEqual(data.itemListElement.map(x=>x.position),[1,2,3,4]);
 assert.ok(data.itemListElement.every(x=>apps.some(a=>!a.hidden&&x.url.endsWith('id='+a.pkg))));
});

test('non-destructive deployment includes the new guide and smoke checks actual live output',()=>{
 const publish=read('scripts/publish_app_discovery.sh');
 const live=read('scripts/check_app_discovery_live.sh');
 assert.match(publish,/guides\/quick-games\/ja\/index\.html/);
 assert.match(publish,/--dry-run/);
 assert.match(publish,/--apply/);
 assert.doesNotMatch(publish,/rsync[^\n]*--delete/);
 assert.match(live,/fetch '\/guides\/quick-games\/ja\/' 'quick-games-ja\.html'/);
 assert.match(live,/FAIL Japanese guide omitted from live sitemap/);
 assert.match(live,/FAIL Japanese store attribution missing/);
});

test('Japanese guide is discoverable from both homepage and the catalog',()=>{
 const homepage=read('index.html'),catalog=read('apps.html');
 assert.match(homepage,/<a class="discovery-link" data-guide="quick-games-ja" href="\/guides\/quick-games\/ja\/" lang="ja" hreflang="ja">/);
 assert.match(catalog,/<a href="\/guides\/quick-games\/ja\/" lang="ja" hreflang="ja">/);
 assert.equal((homepage.match(/data-guide="quick-games-ja"/g)||[]).length,1);
 assert.equal((catalog.match(/href="\/guides\/quick-games\/ja\/"/g)||[]).length,1);
 const smoke=read('scripts/check_app_discovery_live.sh');
 assert.ok(smoke.includes('data-guide="quick-games-ja"'));
 assert.ok(smoke.includes('日本語でゲームを探す'));
});
