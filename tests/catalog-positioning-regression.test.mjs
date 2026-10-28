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

test('catalog cards reproduce canonical titles with one or two valid store destinations', () => {
  const visible = apps.filter(a=>!a.hidden);
  assert.equal((page.match(/class="app-card"/g)||[]).length+
               (page.match(/class="app-card app-card-dual"/g)||[]).length,visible.length);
  for (const a of visible) {
    const image='src="icons/apps/'+a.app+'.png"';
    const idx=page.indexOf(image);
    assert.ok(idx>=0,a.app+' missing catalog icon/card');
    assert.equal(page.split(image).length-1,1,a.app+' duplicate catalog card');
    const end=page.indexOf(a.ios_app_id ? '\n      </div>' : '\n      </a>',idx);
    assert.ok(end>idx,a.app+' card boundary missing');
    const card=page.slice(idx,end);
    assert.ok(card.includes('<h3>'+encode(a.title)+'</h3>'),a.app+' title drift');
    assert.ok(card.includes('<p>'+encode(a.desc)+'</p>'),a.app+' description drift');
    assert.ok(card.includes('id='+a.pkg),a.app+' Play package drift');
    assert.match(card,/referrer=utm_source%3Dappdevelopsk/);
    if (a.ios_app_id){
      assert.ok(card.includes('apps.apple.com/app/id'+a.ios_app_id+'?ct=apps_catalog_'+a.app),a.app+' iOS CTA missing');
      assert.ok(card.includes('data-store="app_store"'),a.app+' iOS store label missing');
    }
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

test('privacy-policy recovery is constrained to 17 observed stale public routes',()=>{
  const script=read('scripts/publish_stale_policy_pages.sh');
  for(const slug of ["battery-charging-map","dinnerhomeroulette","drift","ear-train","gratitude-log","heritageatlas","heritagetrace","mood-log","name-maker","nowsnap","posture-reminder","rental-inspector","smile-score","solace","tappitsu-battle","wait-time","water-reminder"]) {
    assert.ok(script.includes('  '+slug+'\n'), 'missing verified stale policy: '+slug);
    assert.match(read('privacy-policy/'+slug+'/index.html'),/<html/i);
  }
  assert.match(script,/--dry-run/);
  assert.match(script,/--check-live/);
  assert.match(script,/--apply/);
  assert.match(script,/rsync -avR --itemize-changes/);
  assert.match(script,/python3 - "\$file" "\$tmp"/);
  assert.doesNotMatch(script,/rsync[^\n]*--delete/);
  assert.doesNotMatch(script,/rsync[^\n]*-e\s+sh/);
});
