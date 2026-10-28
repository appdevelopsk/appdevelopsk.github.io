import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {runInNewContext} from 'node:vm';
const read = p => readFileSync(new URL('../'+p, import.meta.url), 'utf8');
const html = read('support/blur/index.html');
const langs = ['en','ja','zh','zh_TW','ko','es','pt','fr','de','it','ru','ar','th','id','tr','nl','vi'];

test('first-rendered Blur benefits are verified single-player reveal mechanics',()=>{
  for(const phrase of [
    'Daily blurred-image guessing challenge',
    'Reveal more of the picture step by step',
    'Guess before the full image appears',
    'Keep playing in infinite mode',
  ]) assert.ok(html.includes(phrase),phrase);
  assert.doesNotMatch(html,/Multiplayer mode|Timed challenges|Multiple difficulty levels/);
});
test('all 17 locale feature blocks communicate the same four real game actions',()=>{
  const match=html.match(/const FEAT_T=(\{[\s\S]*?\});\s*const __oF=applyLang;/);
  assert.ok(match,'missing localized feature block');
  const dict=runInNewContext('('+match[1]+')');
  assert.deepEqual(Object.keys(dict).sort(),[...langs].sort());
  for(const locale of langs){
    assert.deepEqual(Object.keys(dict[locale]).sort(),['0','1','2','3'],locale+' must show four verified actions');
    for(const item of Object.values(dict[locale])) assert.ok(Array.from(item).length>=6,locale+' blank feature');
  }
  assert.match(dict.en[0],/daily/);
  assert.match(dict.ja[3],/無限モード/);
});
test('first screen and detail Play links use the legitimate package with different placement',()=>{
  const links=[...html.matchAll(/<a href="(https:\/\/play\.google\.com[^"]+)" class="dl-btn dl-btn-play" data-position="(hero|details)"/g)];
  assert.deepEqual(links.map(l=>l[2]).sort(),['details','hero']);
  for(const link of links){
    assert.ok(link[1].includes('id=com.blurapp.blur_app'));
    assert.match(link[1],/referrer=utm_source%3Dappdevelopsk/);
    assert.doesNotMatch(link[1],/user_id|device_id|email|quiz_answer/);
  }
  assert.match(html,/placement: a\.getAttribute\('data-position'\)/);
});
test('manual site deployment and read-only smoke include Blur landing',()=>{
  assert.match(read('scripts/publish_app_discovery.sh'),/support\/blur\/index\.html/);
  const live=read('scripts/check_app_discovery_live.sh');
  assert.match(live,/fetch '\/support\/blur\/' 'blur.html'/);
  assert.match(live,/FAIL Blur first-screen Play CTA not live/);
  assert.match(live,/FAIL Blur advertises unverified game modes/);
});
