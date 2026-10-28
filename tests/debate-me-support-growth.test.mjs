import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {runInNewContext} from 'node:vm';
const read = p => readFileSync(new URL('../'+p, import.meta.url), 'utf8');
const html = read('support/debate-me/index.html');
const languages = ['en','ja','zh','zh_TW','ko','es','pt','fr','de','it','ru','ar','th','id','tr','nl','vi'];
function dictionary(name, after) {
  const match = html.match(new RegExp('const '+name+'=(\\{[\\s\\S]*?\\});\\s*const '+after));
  assert.ok(match, name+' dictionary missing');
  return runInNewContext('('+match[1]+')');
}
test('first paint shows real AI debate and never a food spinner', () => {
  assert.match(html, /<title>Debate Me: AI Debate Practice & Argument Skills/);
  assert.match(html, /<h1>Debate Me<\/h1>/);
  assert.match(html, /<div class="hero-emoji">🗣️<\/div>/);
  assert.match(html, /<div class="hero-cat">Education<\/div>/);
  assert.match(html, /<p id="heroDesc">Choose a topic, defend your position against AI/);
  assert.match(html, /<span data-feat="0">Choose from six categories/);
  assert.match(html, /<span data-feat="1">Defend a position against an AI/);
  assert.match(html, /AI debate responses and scoring require an internet connection/);
  assert.doesNotMatch(html, /Can't decide what to cook tonight|meal ideas|Filter by ingredients|Cooking time estimates|Cooking time \(15min|home-cooked meals|Save favorites/i);
});
test('all 17 languages describe debate and a correct internet requirement', () => {
  const intros = dictionary('APP_T','_oA=applyLang');
  const features = dictionary('FEAT_T','__oF=applyLang');
  assert.deepEqual(Object.keys(intros).sort(), [...languages].sort());
  assert.deepEqual(Object.keys(features).sort(), [...languages].sort());
  for (const lang of languages) {
    assert.ok(Array.from(intros[lang]).length >= 10, 'missing translated debate intro: '+lang);
    assert.deepEqual(Object.keys(features[lang]).sort(), ['0','1','2','3'], lang+' feature count');
    for (const value of Object.values(features[lang])) assert.ok(Array.from(value).length >= 6, lang+' incomplete feature');
  }
  assert.match(intros.en, /AI partner/);
  assert.match(intros.ja, /ディベート/);
  assert.match(features.en[2], /reasoning/);
  assert.match(features.ja[1], /AIと議論/);
  // The actual T object may have unrelated quoted HTML text. Scan the 17 FAQ entries
  // instead of treating T as a JSON object.
  const faq = [...html.matchAll(/faq4a:"(?:\\.|[^"\\])*"/g)];
  assert.equal(faq.length, 17);
  assert.ok(faq.every(x => !/many features work offline|多くの機能はオフライン|支持离线使用/i.test(x[0])));
});
test('Play CTA is above the fold, tracked separately from the details CTA', () => {
  const links = [...html.matchAll(/<a href="(https:\/\/play\.google\.com[^"]+)" class="dl-btn dl-btn-play" data-position="(hero|details)"/g)];
  assert.deepEqual(links.map(m => m[2]).sort(), ['details','hero']);
  for (const m of links) {
    assert.ok(m[1].includes('id=jp.appdevelopsk.debate_me'));
    assert.match(m[1], /referrer=utm_source%3Dappdevelopsk/);
    assert.doesNotMatch(m[1], /user_id|debate_id|device_id|invite_token/);
  }
  assert.match(links.find(m=>m[2]==='hero')[1],/utm_campaign=support_debate_me_hero/);
  assert.match(html, /placement: a\.getAttribute\('data-position'\)/);
});
test('manual VPS publishing includes the landing and its read-only live validation', () => {
  const pub = read('scripts/publish_app_discovery.sh');
  const live = read('scripts/check_app_discovery_live.sh');
  assert.match(pub,/support\/debate-me\/index\.html/);
  assert.match(pub,/--dry-run/);
  assert.doesNotMatch(pub,/rsync .*--delete/);
  assert.match(live,/fetch '\/support\/debate-me\/' 'debate-me.html'/);
  assert.match(live,/FAIL Debate Me page still describes cooking/);
  assert.match(live,/FAIL Debate Me first-screen Play CTA not live/);
});
