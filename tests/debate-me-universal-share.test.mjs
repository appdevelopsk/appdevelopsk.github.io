import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
const read=p=>readFileSync(new URL('../'+p,import.meta.url),'utf8');
const html=read('share/debate-me/index.html');
const js=read('share/debate-me/landing.js');
test('verified Play link is available but unverified iOS download is not promoted',()=>{
  assert.match(html,/play\.google\.com\/store\/apps\/details\?id=jp\.appdevelopsk\.debate_me/);
  assert.doesNotMatch(html,/apps\\.apple\\.com\\/app\\/id6760968208/);
  assert.match(html,/<p id="ios" class="ios-status" role="status"/);
  assert.match(html,/iOS App Store availability is unverified/);
  assert.match(html,/rel="canonical" href="https:\/\/appdevelopsk\.com\/share\/debate-me\/"/);
  assert.doesNotMatch(html,/debate_id|device_id|argument_text/);
  assert.doesNotMatch(js,/window\.location\s*=|location\.replace|innerHTML|fetch\(/);
});
test('query parameters are restricted to non-personal campaign labels',()=>{
  assert.match(js,/new Set\(\['home', 'settings', 'result'\]\)/);
  assert.match(js,/allowedSources\.has\(source\) \? source : 'generic'/);
  assert.match(js,/utm_source=skapps&utm_medium=share&utm_campaign=debate_me_/);
});
test('the visitor-facing landing page supports all 17 app locales',()=>{
  const locales=['en','ja','zh','zh_TW','ko','es','pt','fr','de','it','ru','ar','th','id','tr','nl','vi'];
  for(const loc of locales)assert.match(js,new RegExp('"'+loc+'":'));
  for(const field of ['intro','android','ios','availability','privacy','otherApps'])assert.match(js,new RegExp('"'+field+'":'));
});

test('indexable universal landing is listed once in the sitemap',()=>{
  const sitemap=read('sitemap.xml');
  const entry='https://appdevelopsk.com/share/debate-me/';
  assert.equal(sitemap.split(entry).length-1,1);
  assert.match(html,/meta name="robots" content="index,follow"/);
});

test('every locale describes iOS status honestly, not a confirmed download',()=>{
  const raw=js.match(/const I18N = (\\{[\\s\\S]*?\\});\\n  const browser/);
  assert.ok(raw);
  const copy=JSON.parse(raw[1]);
  for(const [lang,value] of Object.entries(copy)){
    assert.ok(value.ios && value.ios.length>8,lang);
    assert.notEqual(value.ios,'Open in the App Store',lang);
  }
});
