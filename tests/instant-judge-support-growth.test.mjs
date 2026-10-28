import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {runInNewContext} from 'node:vm';
const read = p => readFileSync(new URL('../'+p, import.meta.url), 'utf8');
const html = read('support/instant-judge/index.html');
const locales = ['en','ja','zh','zh_TW','ko','es','pt','fr','de','it','ru','ar','th','id','tr','nl','vi'];
function dict(name,next) {
  const found = html.match(new RegExp('const '+name+'=(\\{[\\s\\S]*?\\});\\s*const '+next));
  assert.ok(found,name+' dictionary absent');
  return runInNewContext('('+found[1]+')');
}
test('first paint describes real community vote, creation and delayed reveal',()=>{
  assert.match(html,/<h1>Instant Judge<\/h1>/);
  assert.match(html,/<p id="heroDesc">Vote on everyday dilemmas/);
  assert.match(html,/<span data-feat="0">Vote on questions from the community<\/span>/);
  assert.match(html,/<span data-feat="2">Results appear at their reveal time<\/span>/);
  assert.match(html,/Community voting, posting and result updates require an internet connection/);
  assert.doesNotMatch(html,/Thousands of scenarios to judge|Real-time results|3 seconds and see what the community thinks|Many features work offline|Daily trending judgments/);
});
test('17 locale introduction and feature lists match vote-reveal flow',()=>{
  const intros=dict('APP_T','_oA=applyLang'), features=dict('FEAT_T','__oF=applyLang');
  assert.deepEqual(Object.keys(intros).sort(),[...locales].sort());
  assert.deepEqual(Object.keys(features).sort(),[...locales].sort());
  for(const l of locales) {
    assert.ok(Array.from(intros[l]).length>=10,l+' empty intro');
    assert.deepEqual(Object.keys(features[l]).sort(),['0','1','2','3'],l+' incorrect feature count');
    for(const v of Object.values(features[l])) assert.ok(Array.from(v).length>=6,l+' empty item');
  }
  assert.match(intros.ja,/投票/);
  assert.match(features.en[2],/reveal/);
  assert.match(features.ja[2],/公開時刻/);
  const faqs=[...html.matchAll(/faq4a:"(?:\\.|[^"\\])*"/g)];
  assert.equal(faqs.length,17);
  assert.ok(faqs.every(x=>!x[0].includes('Many features work offline')));
});
test('two distinct Play positions and safe attribution (not a verified installation)',()=>{
  const links=[...html.matchAll(/<a href="(https:\/\/play\.google\.com[^"]+)" class="dl-btn dl-btn-play" data-position="(hero|details)"/g)];
  assert.deepEqual(links.map(x=>x[2]).sort(),['details','hero']);
  for(const x of links) {
    assert.match(x[1],/id=com\.instantjudge\.instant_judge/);
    assert.match(x[1],/referrer=utm_source%3Dappdevelopsk/);
    assert.doesNotMatch(x[1],/user_id|device_id|vote_id|email/);
  }
  assert.match(links.find(x=>x[2]==='hero')[1],/utm_campaign=support_instant_judge_hero/);
  assert.match(html,/placement: a\.getAttribute\('data-position'\)/);
});
test('iOS and Android acquisition links are visible in both hero and details with privacy-safe campaign tags',()=>{
  const apple=[...html.matchAll(/<a href="(https:\/\/apps\.apple\.com\/app\/id6759920352\?ct=([^"]+))" class="dl-btn dl-btn-apple" data-position="(hero|details)"/g)];
  assert.deepEqual(apple.map(x=>x[3]).sort(),['details','hero']);
  assert.equal(apple.find(x=>x[3]==='hero')?.[2], 'support_instant_judge_hero');
  assert.equal(apple.find(x=>x[3]==='details')?.[2], 'support_instant_judge_details');
  for(const link of apple) {
    assert.doesNotMatch(link[1],/user_id|device_id|post_id|invite_token|email/);
  }
  const descriptions=[...html.matchAll(/download_desc:"([^"]+)"/g)].map(x=>x[1]);
  assert.equal(descriptions.length,17);
  for(const desc of descriptions){
    assert.ok(desc.includes('App Store') && desc.includes('Google Play'),desc);
  }
  assert.match(html,/name="description" content="[^"]*iPhone and Android/);
  assert.match(html,/store = \/apps\\.apple\\.com\/\.test\(href\) \? 'app_store' : 'google_play'/);
  assert.match(html,/gtag\('event', 'download_click', \{ store: store,/);
});
test('site publication explicitly includes Instant Judge, and stale live copy fails',()=>{
  const publish=read('scripts/publish_app_discovery.sh');
  const smoke=read('scripts/check_app_discovery_live.sh');
  assert.match(publish,/support\/instant-judge\/index\.html/);
  assert.match(publish,/--dry-run/);
  assert.match(smoke,/fetch '\/support\/instant-judge\/' 'instant-judge.html'/);
  assert.match(smoke,/FAIL Instant Judge reveal copy missing/);
  assert.match(smoke,/FAIL Instant Judge first-screen Play CTA missing/);
});
