import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';

const read = p => readFileSync(new URL('../'+p,import.meta.url),'utf8');
const apps = [
  {slug:'blur', id:'6759920723', camp:'blur', packageId:'com.blurapp.blur_app'},
  {slug:'twotaku', id:'6760481027', camp:'twotaku', packageId:'com.dotchi.dotchi_app'},
  {slug:'debate-me', id:'6760968208', camp:'debate_me', packageId:'jp.appdevelopsk.debate_me'},
];

test('three high-priority landings expose iOS and Android stores at both visible positions',()=>{
  for(const app of apps){
    const html=read('support/'+app.slug+'/index.html');
    const apple=[...html.matchAll(/<a href="(https:\/\/apps\.apple\.com\/app\/id\d+\?ct=[^"]+)" class="dl-btn dl-btn-apple" data-position="(hero|details)"/g)];
    const play=[...html.matchAll(/<a href="(https:\/\/play\.google\.com[^"]+)" class="dl-btn dl-btn-play" data-position="(hero|details)"/g)];
    assert.deepEqual(apple.map(m=>m[2]).sort(),['details','hero'],app.slug+' missing App Store placements');
    assert.deepEqual(play.map(m=>m[2]).sort(),['details','hero'],app.slug+' missing Play placements');
    for(const m of apple){
      assert.equal(m[1], 'https://apps.apple.com/app/id'+app.id+'?ct=support_'+app.camp+'_'+m[2]);
      assert.doesNotMatch(m[1], /user_id|device_id|invite_token|email|post_id|vote_id/);
    }
    for(const m of play){
      assert.ok(m[1].includes('id='+app.packageId),app.slug+' Play package mismatch');
      assert.match(m[1],/referrer=utm_source%3Dappdevelopsk/);
    }
    assert.doesNotMatch(html,/apps\.apple\.com\/app\/id6796349449/);
  }
});

test('all 17 language download descriptions inform iPhone visitors as well as Android',()=>{
  for(const app of apps){
    const html=read('support/'+app.slug+'/index.html');
    const translations=[...html.matchAll(/download_desc:"([^"]*)"/g)].map(m=>m[1]);
    assert.equal(translations.length,17,app.slug+' locale count');
    for(const d of translations){
      assert.ok(d.includes('App Store')&&d.includes('Google Play'),app.slug+': '+d);
      assert.ok(d.length>=25);
    }
    assert.match(html,/data-i18n="download_desc">Available on iPhone and Android/);
  }
});

test('all three pages log store and placement separately without counting link clicks as installs',()=>{
  for(const app of apps){
    const html=read('support/'+app.slug+'/index.html');
    assert.match(html,/var store = \/apps\\.apple\\.com\/\.test\(href\) \? 'app_store' : 'google_play'/);
    assert.match(html,/gtag\('event', 'download_click', \{ store: store,/);
    assert.match(html,/placement: a\.getAttribute\('data-position'\)/);
    assert.doesNotMatch(html,/gtag\('event', 'install_success'/);
  }
});

test('live read-only smoke refuses a production page missing iOS buttons',()=>{
  const smoke=read('scripts/check_app_discovery_live.sh');
  for(const app of apps){
    assert.ok(smoke.includes('apps.apple.com/app/id'+app.id+'?ct=support_'+app.camp+'_hero'));
    assert.ok(smoke.includes('apps.apple.com/app/id'+app.id+'?ct=support_'+app.camp+'_details'));
  }
});
