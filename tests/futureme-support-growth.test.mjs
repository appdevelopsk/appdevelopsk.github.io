import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {runInNewContext} from 'node:vm';
const read=p=>readFileSync(new URL('../'+p,import.meta.url),'utf8');
const html=read('support/future-me/index.html');
const langs=['en','ja','zh','zh_TW','ko','es','pt','fr','de','it','ru','ar','th','id','tr','nl','vi'];
function localeDict(name,next){
 const m=html.match(new RegExp('const '+name+'=(\\{[\\s\\S]*?\\});\\s*const '+next));
 assert.ok(m,name+' missing');return runInNewContext('('+m[1]+')');
}
test('FutureMe first paint describes actual forecast reflection and check-ins',()=>{
 assert.match(html,/<h1>FutureMe<\/h1>/);
 assert.match(html,/<p id="heroDesc">Explore AI-generated future scenarios for fun/);
 for(const phrase of ['Explore playful AI-generated future scenarios','Review predictions and note your progress','Read your weekly fortune and reflection prompts','Create a simple action plan for tomorrow']) assert.ok(html.includes(phrase),phrase);
 assert.doesNotMatch(html,/Letters to future self|Time capsule feature|write letters to your future self/i);
});
test('17 locale intro/feature blocks have no hardcoded or misleading subscription prices',()=>{
 const intro=localeDict('APP_T','_oA=applyLang'),f=localeDict('FEAT_T','__oF=applyLang');
 assert.deepEqual(Object.keys(intro).sort(),[...langs].sort());
 assert.deepEqual(Object.keys(f).sort(),[...langs].sort());
 for(const lang of langs){
   assert.ok(Array.from(intro[lang]).length>=10,lang+' missing intro');
   assert.deepEqual(Object.keys(f[lang]).sort(),['0','1','2','3'],lang+' incorrect feature list');
   for(const str of Object.values(f[lang])) assert.ok(Array.from(str).length>=6,lang+' missing text');
 }
 assert.match(intro.ja,/AI/);
 assert.match(f.ja[3],/明日/);
 const source=html.slice(html.indexOf('const APP_T='),html.indexOf('const __oF=applyLang'));
 assert.doesNotMatch(source,/FutureMe Premium|(?:NT\$|¥|₩|€|\$)\s*\d+\s*\/\s*(?:月|年)|月間\([^)]*\d/i);
});
test('hero/details Play CTAs use correct package and anonymous campaign',()=>{
 const hits=[...html.matchAll(/<a href="(https:\/\/play\.google\.com[^"]+)" class="dl-btn dl-btn-play" data-position="(hero|details)"/g)];
 assert.deepEqual(hits.map(x=>x[2]).sort(),['details','hero']);
 for(const x of hits){assert.match(x[1],/id=com\.futureme\.future_me/);assert.match(x[1],/referrer=utm_source%3Dappdevelopsk/);assert.doesNotMatch(x[1],/user_id|device_id|email/)}
 assert.match(hits.find(x=>x[2]==='hero')[1],/utm_campaign=support_future_me_hero/);
 assert.match(html,/placement: a\.getAttribute\('data-position'\)/);
});
test('VPS manual publish includes FutureMe and live smoke fails on stale pages',()=>{
 const release=read('scripts/publish_app_discovery.sh'),live=read('scripts/check_app_discovery_live.sh');
 assert.match(release,/support\/future-me\/index\.html/);
 assert.match(release,/--dry-run/);
 assert.match(live,/fetch '\/support\/future-me\/' 'futureme.html'/);
 assert.match(live,/FAIL FutureMe first-screen Play CTA missing/);
 assert.match(live,/FAIL FutureMe support page contains outdated feature or pricing claims/);
});
