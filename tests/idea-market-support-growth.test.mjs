import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {runInNewContext} from 'node:vm';
const read = p => readFileSync(new URL('../'+p, import.meta.url), 'utf8');
const html = read('support/idea-market/index.html');
const langs = ['en','ja','zh','zh_TW','ko','es','pt','fr','de','it','ru','ar','th','id','tr','nl','vi'];
function dictionary(name, after) {
  const match = html.match(new RegExp('const '+name+'=(\\{[\\s\\S]*?\\});\\s*const '+after));
  assert.ok(match, name+' missing');
  return runInNewContext('('+match[1]+')');
}
test('first paint describes actual marketplace, not voice diary capabilities',()=>{
  assert.match(html, /<title>Idea Market/);
  assert.match(html, /<div class="hero-emoji">💡<\/div>/);
  assert.match(html, /<div class="hero-cat">Business Ideas<\/div>/);
  assert.match(html, /<p id="heroDesc">Browse startup ideas/);
  for(const text of ['Browse ideas across business categories','Explore public idea previews','Post your own business concept','Manage your listings in a dashboard']) assert.ok(html.includes(text));
  assert.doesNotMatch(html, /Voice-to-text transcription|AI Transcription|Emotion Calendar|voice into a personal diary|AI summaries|Emotion Detection|Record voice memos/i);
});
test('17 localized intros and feature blocks stay aligned with the app',()=>{
  const intro = dictionary('APP_T','_oA=applyLang');
  const feat = dictionary('FEAT_T','__oF=applyLang');
  assert.deepEqual(Object.keys(intro).sort(),[...langs].sort());
  assert.deepEqual(Object.keys(feat).sort(),[...langs].sort());
  for(const l of langs){
    assert.ok(Array.from(intro[l]).length>=10, l+' missing intro');
    assert.deepEqual(Object.keys(feat[l]).sort(),['0','1','2','3'],l+' missing features');
    for(const v of Object.values(feat[l])) assert.ok(Array.from(v).length>=6,l+' empty feature');
  }
  assert.match(intro.en,/Discover business ideas/);
  assert.match(intro.ja,/アイデア/);
});
test('store purchase, support and offline FAQs do not promise an unverified checkout',()=>{
  assert.match(html, /<strong data-i18n="faq1q">What can I view before purchasing\?/);
  assert.match(html, /Private details require verified access/);
  assert.match(html, /Contact support with the idea title and date/);
  assert.match(html, /Browsing, posting and access checks require an internet connection/);
  for(const key of ['faq1q','faq1a','faq3q','faq3a','faq4q','faq4a']){
    const hits=[...html.matchAll(new RegExp(key+':"(?:\\\\.|[^"\\\\])*"','g'))];
    assert.equal(hits.length,17,'localized FAQ count: '+key);
  }
  assert.doesNotMatch(html,/go to Settings, and tap \\"Restore Purchases\\"|voice into a personal diary|Emotion Calendar/i);
});
test('Play link is in first view and old details CTA remains with separate placement',()=>{
  const hits=[...html.matchAll(/<a href="(https:\/\/play\.google\.com[^"]+)" class="dl-btn dl-btn-play" data-position="(hero|details)"/g)];
  assert.deepEqual(hits.map(x=>x[2]).sort(),['details','hero']);
  for(const m of hits){
    assert.ok(m[1].includes('id=jp.appdevelopsk.ideamarket'));
    assert.match(m[1],/referrer=utm_source%3Dappdevelopsk/);
    assert.doesNotMatch(m[1],/user_id|transaction_id|payment_token|email/);
  }
  assert.match(html,/placement: a\.getAttribute\('data-position'\)/);
});
test('read-only smoke and manually applied deployment cover marketplace landing',()=>{
  const pub=read('scripts/publish_app_discovery.sh');
  const live=read('scripts/check_app_discovery_live.sh');
  assert.match(pub,/support\/idea-market\/index\.html/);
  assert.match(pub,/--dry-run/);
  assert.match(live,/fetch '\/support\/idea-market\/' 'idea-market.html'/);
  assert.match(live,/FAIL Idea Market page still describes a voice diary/);
});
