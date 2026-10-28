import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {runInNewContext} from 'node:vm';
const read=p=>readFileSync(new URL('../'+p,import.meta.url),'utf8');
const html=read('support/roast-me/index.html');
const langs=['en','ja','zh','zh_TW','ko','es','pt','fr','de','it','ru','ar','th','id','tr','nl','vi'];
test('RoastMe hero reflects user-made feedback and never promises AI-generated roasts',()=>{
  assert.match(html,/<title>RoastMe – Community Roasts/);
  assert.match(html,/<p id="heroDesc">Post a topic, invite community feedback/);
  assert.match(html,/<span data-feat="0">Browse community posts and discussions<\/span>/);
  assert.match(html,/Community posts, replies and live reactions require an internet connection/);
  assert.doesNotMatch(html,/AI-generated roasts|Get roasted by AI and friends|100% anonymous|Friend roast mode|Many features work offline/);
});
test('all 17 feature locales describe genuine community posts and replies',()=>{
  const match=html.match(/const FEAT_T=(\{[\s\S]*?\});\s*const __oF=applyLang;/);
  assert.ok(match,'localized feature map missing');
  const features=runInNewContext('('+match[1]+')');
  assert.deepEqual(Object.keys(features).sort(),[...langs].sort());
  for(const lang of langs){
    assert.deepEqual(Object.keys(features[lang]).sort(),['0','1','2','3'],lang+' feature coverage');
    for(const v of Object.values(features[lang])) assert.ok(Array.from(v).length>=6,lang+' missing content');
  }
  assert.match(features.ja[1],/優しい/);
  const offline=[...html.matchAll(/faq4a:"(?:\\.|[^"\\])*"/g)];
  assert.equal(offline.length,17);
  assert.ok(offline.every(m=>!m[0].includes('Many features work offline')));
});
test('hero and details Play links carry anonymous placement-specific campaigns',()=>{
  const hits=[...html.matchAll(/<a href="(https:\/\/play\.google\.com[^"]+)" class="dl-btn dl-btn-play" data-position="(hero|details)"/g)];
  assert.deepEqual(hits.map(x=>x[2]).sort(),['details','hero']);
  for(const m of hits) {
    assert.match(m[1],/id=jp\.appdevelopsk\.roast_me_app/);
    assert.match(m[1],/referrer=utm_source%3Dappdevelopsk/);
    assert.doesNotMatch(m[1],/user_id|device_id|email|post_id/);
  }
  assert.match(hits.find(m=>m[2]==='hero')[1],/utm_campaign=support_roast_me_hero/);
  assert.match(html,/placement: a\.getAttribute\('data-position'\)/);
});
test('manual publish gate and public read-only smoke include RoastMe',()=>{
  const pub=read('scripts/publish_app_discovery.sh'), live=read('scripts/check_app_discovery_live.sh');
  assert.match(pub,/support\/roast-me\/index\.html/);
  assert.match(pub,/--dry-run/);
  assert.match(live,/fetch '\/support\/roast-me\/' 'roastme.html'/);
  assert.match(live,/FAIL RoastMe first-screen Play CTA missing/);
  assert.match(live,/FAIL RoastMe promises unverified AI roasts/);
});
