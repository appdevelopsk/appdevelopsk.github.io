import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
const read = path => readFileSync(new URL('../'+path,import.meta.url),'utf8');
const apps = JSON.parse(read('apps_data.json'));
const page = read('apps.html');
const highPriority = {
  'debate-me': 'Practice debating with an AI opponent, get feedback and share your results',
  'roast-me': 'Post a topic, get community feedback and write a kind or blunt roast',
  'instant-judge': 'Vote on community dilemmas, post your own and see results when revealed',
  'future-me': 'Explore playful AI future scenarios, revisit predictions and plan tomorrow',
  'idea-market': 'Explore startup ideas, read public previews and post your own business concept',
};
const encode = value => value.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;').replace(/'/g,'&#x27;');

test('catalog cards reproduce the canonical visible app titles and descriptions', () => {
  const visible = apps.filter(a=>!a.hidden);
  const cards = [...page.matchAll(/<a class="app-card" href="([^"]+)"[\s\S]*?<h3>([^<]+)<\/h3>\s*<p>([^<]*)<\/p>[\s\S]*?<\/a>/g)];
  assert.equal(cards.length,visible.length);
  for (const a of visible) {
    const match=cards.filter(m=>m[1].includes('id='+a.pkg));
    assert.equal(match.length,1,a.app+' missing or duplicate');
    assert.equal(match[0][2],encode(a.title),a.app+' title drift');
    assert.equal(match[0][3],encode(a.desc),a.app+' description drift');
    assert.match(match[0][1],/referrer=utm_source%3Dappdevelopsk/);
  }
});
test('five high-traffic-intent entries describe genuinely implemented core value',()=>{
  for (const [slug,desc] of Object.entries(highPriority)) {
    const a=apps.find(x=>x.app===slug&&!x.hidden);
    assert.ok(a,'published app missing: '+slug);
    assert.equal(a.desc,desc);
    assert.ok(page.includes('<p>'+encode(desc)+'</p>'));
  }
  const titles=Object.fromEntries(apps.map(x=>[x.app,x.title]));
  assert.equal(titles['roast-me'],'RoastMe - Community Roasts');
  assert.doesNotMatch(apps.filter(x=>Object.hasOwn(highPriority,x.app)).map(x=>x.title+' '+x.desc).join('\n'),/win any discussion|write letters to your future self|Post a photo and get roasted and rated|buy & sell startup ideas/i);
});
test('production smoke must verify these five catalog descriptions, not only source',()=>{
  const live=read('scripts/check_app_discovery_live.sh');
  for(const desc of Object.values(highPriority)) assert.ok(live.includes(desc.slice(0,Math.min(35,desc.length))),'live smoke misses '+desc);
  assert.match(live,/FAIL catalog description not deployed/);
});
