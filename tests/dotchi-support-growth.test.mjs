import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {runInNewContext} from 'node:vm';
const read=p=>readFileSync(new URL('../'+p,import.meta.url),'utf8');
const html=read('support/twotaku/index.html');
const languages=['en','ja','zh','zh_TW','ko','es','pt','fr','de','it','ru','ar','th','id','tr','nl','vi'];
function translations(name,next){
 const pattern=new RegExp('const '+name+'=(\\{[\\s\\S]*?\\});\\s*const '+next);
 const match=html.match(pattern);assert.ok(match,name+' dictionary missing');
 return runInNewContext('('+match[1]+')');
}

test('Dotchi search title and above-fold Play CTA reflect real A/B polls',()=>{
 assert.match(html,/<title>Dotchi: A or B Polls/);
 assert.match(html,/<h1>Dotchi: This or That Polls<\/h1>/);
 assert.match(html,/<p id="heroDesc">Pick A or B/);
 assert.doesNotMatch(html,/Anime\/manga database|Watch\/read lists|Naruto|Goku|Anime debates/i);
 const play=[...html.matchAll(/<a href="([^"]+)" class="dl-btn dl-btn-play" data-position="(hero|details)"/g)];
 assert.deepEqual(play.map(x=>x[2]).sort(),['details','hero']);
 for(const link of play){
  assert.match(link[1],/id=com\.dotchi\.dotchi_app/);
  assert.match(link[1],/referrer=utm_source%3Dappdevelopsk/);
 }
 assert.match(html,/placement: a\.getAttribute\('data-position'\)/);
 assert.match(html,/<script type="application\/ld\+json">/);
});

test('all 17 visible languages describe genuine polling features',()=>{
 const titles=translations('APP_T','_oA=applyLang');
 const features=translations('FEAT_T','__oF=applyLang');
 assert.deepEqual(Object.keys(titles).sort(),[...languages].sort());
 assert.deepEqual(Object.keys(features).sort(),[...languages].sort());
 for(const lang of languages){
  assert.ok(titles[lang].length>=15,lang+' missing translated polling intro');
  assert.equal(Object.keys(features[lang]).length,4,lang+' must have 4 verified feature bullets');
  for(const val of Object.values(features[lang])) assert.ok(val.length>=7,lang+' blank feature');
 }
 assert.match(titles.en,/A or B/);
 assert.match(titles.ja,/二択/);
 assert.match(features.en[0],/Choose A or B/);
 assert.match(features.ja[1],/投票結果/);
});

test('Dotchi support publication is part of the non-destructive VPS release gate',()=>{
 const release=read('scripts/publish_app_discovery.sh');
 const live=read('scripts/check_app_discovery_live.sh');
 const sitemap=read('sitemap.xml');
 assert.match(release,/support\/twotaku\/index\.html/);
 assert.match(live,/support\/twotaku/);
 assert.match(live,/FAIL Dotchi anime-only support content still live/);
 assert.match(sitemap,/https:\/\/appdevelopsk\.com\/support\/twotaku\/\/<\/loc><lastmod>2026-10-27/);
});
