import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {Script,runInNewContext} from 'node:vm';
const read = p => readFileSync(new URL('../'+p, import.meta.url),'utf8');
const data = JSON.parse(read('apps_data.json'));
const catalog = read('apps.html');
const sitemap = read('sitemap.xml');
const guides = ['quick-games','daily-habits','decision-helpers','ai-tools'];

test('catalog search retains 92 real indexed store cards and passes install referrer',()=>{
  const visible=data.filter(x=>!x.hidden);
  const tags=[...catalog.matchAll(/<a class="app-card" href="([^"]+)"/g)];
  assert.equal(visible.length,JSON.parse(read('site_counts.json')).android_live);
  const dual=[...catalog.matchAll(/<div class="app-card app-card-dual">/g)];
  assert.equal(tags.length+dual.length,visible.length);
  for (const entry of visible) {
    if (entry.ios_app_id) {
      assert.ok(catalog.includes('id='+entry.pkg),entry.app+' Play destination missing');
      assert.ok(catalog.includes('apps.apple.com/app/id'+entry.ios_app_id+'?ct=apps_catalog_'+entry.app),entry.app+' App Store destination missing');
    } else {
      assert.ok(tags.some(t=>t[1].includes('id='+entry.pkg)),entry.app);
    }
  }
  assert.ok(tags.every(t=>t[1].includes('referrer=utm_source%3Dappdevelopsk')));
  assert.match(catalog,/id="find-app"/);
  assert.match(catalog,/id="finder-count"[^>]*role="status"/);
});

test('filters work client-side without tracking raw search text',()=>{
  const scripts=[...catalog.matchAll(/<script[^>]*>([\s\S]*?)<\/script>/g)].map(m=>m[1]);
  const source=scripts.find(s=>s.includes('catalog_store_click'));
  assert.ok(source); new Script(source);
  function el(extra={}) {return {events:{},hidden:false,...extra,addEventListener(name,fn){this.events[name]=fn;},setAttribute(key,value){this[key]=value;}}}
  const input=el({value:''}),count=el({textContent:''}),empty=el();
  const buttons=['all','quick-games','habits','decisions','ai'].map(goal=>el({dataset:{goal}}));
  const cards=[
    el({textContent:'Blur: Guess the Image Guess the photo',querySelector:()=>({getAttribute:()=> 'icons/apps/blur.png'})}),
    el({textContent:'FutureMe - AI Prediction write future letters',querySelector:()=>({getAttribute:()=> 'icons/apps/future-me.png'})}),
    el({textContent:'Food Roulette pick a restaurant',querySelector:()=>({getAttribute:()=> 'icons/apps/food-roulette.png'})}),
  ];
  const events=[];
  runInNewContext(source,{document:{getElementById(id){return {'find-app':input,'finder-count':count,'finder-empty':empty}[id];},querySelectorAll(q){return q==='.grid .app-card'?cards:buttons;}},window:{gtag(...args){events.push(args);}}});
  assert.equal(count.textContent,'3 apps shown');
  buttons[1].events.click();
  assert.equal(count.textContent,'1 apps shown');
  assert.equal(cards[0].hidden,false);
  assert.equal(cards[1].hidden,true);
  buttons[0].events.click();
  input.value='personal-email@example.com';input.events.input();
  assert.equal(count.textContent,'0 apps shown');
  assert.equal(empty.hidden,false);
  assert.ok(!JSON.stringify(events).includes('personal-email'));
  input.value='image';input.events.input();
  assert.equal(cards[0].hidden,false);
  cards[0].events.click();
  assert.ok(events.some(e=>e[1]==='catalog_store_click'&&e[2].app==='blur'));
});

test('dual-store cards log distinct app-store and Play clicks, not a whole-card click',()=>{
  const source=[...catalog.matchAll(/<script[^>]*>([\s\S]*?)<\/script>/g)].map(m=>m[1]).find(x=>x.includes('catalog_store_click'));
  assert.ok(source);
  function el(extra={}){return {events:{},hidden:false,...extra,addEventListener(name,fn){this.events[name]=fn;},setAttribute(key,val){this[key]=val;}}}
  const apple=el({dataset:{store:'app_store'}}), play=el({dataset:{store:'google_play'}});
  const dual=el({
    textContent:'Debate Me - AI Debate Practice',
    querySelector:()=>({getAttribute:()=> 'icons/apps/debate-me.png'}),
    querySelectorAll:()=>[play,apple],
  });
  const input=el({value:''}),count=el({textContent:''}),empty=el();
  const buttons=['all','quick-games','habits','decisions','ai'].map(goal=>el({dataset:{goal}}));
  const events=[];
  runInNewContext(source,{document:{getElementById(id){return {'find-app':input,'finder-count':count,'finder-empty':empty}[id];},querySelectorAll(q){return q==='.grid .app-card'?[dual]:buttons;}},window:{gtag(...args){events.push(args);}}});
  assert.equal(dual.events.click,undefined,'card body must not masquerade as a store click');
  apple.events.click();
  play.events.click();
  const tracked=events.filter(e=>e[1]==='catalog_store_click');
  assert.deepEqual(tracked.map(e=>e[2].store),['app_store','google_play']);
  assert.ok(tracked.every(e=>e[2].app==='debate-me'&&e[2].source==='apps_catalog'));
});

test('guide landing pages link only to listed published applications and are discoverable',()=>{
  for(const slug of guides){
    const page=read('guides/'+slug+'/index.html');
    assert.match(sitemap,new RegExp('https://appdevelopsk\\.com/guides/'+slug+'/'));
    assert.match(catalog,new RegExp('href="/guides/'+slug+'/"'));
    assert.match(page,/<link rel="canonical"/);
    assert.match(page,/<script type="application\/ld\+json">/);
    assert.match(page,/gtag\('event','guide_store_click'/);
    const apps=[...page.matchAll(/data-app="([a-z0-9-]+)"/g)].map(m=>m[1]);
    assert.equal(apps.length,4);
    for(const a of apps){
      const record=data.find(x=>x.app===a);
      assert.ok(record&&!record.hidden,slug+' invalid app '+a);
      assert.match(page,new RegExp('id='+record.pkg.replaceAll('.','\\.')));
    }
    assert.doesNotMatch(page,/aggregateRating|ratingValue|100% free|guaranteed/i);
  }
});

test('homepage sends visitors to catalog and both indexable guides without a search gate',()=>{
  const home=read('index.html');
  assert.match(home,/class="discovery-links"/);
  assert.match(home,/href="\/apps"/);
  for (const slug of guides) assert.match(home,new RegExp('href="/guides/'+slug+'/"'));
  assert.match(home,/discovery_nav_click/);
});

test('purpose filters refer only to visible current catalog slugs, not renamed app titles',()=>{
  const match=catalog.match(/const groups = (\{[\s\S]*?\});\s*const clean/);
  assert.ok(match,'missing purpose filter definitions');
  const groups=runInNewContext('('+match[1]+')');
  const visible=new Set(data.filter(a=>!a.hidden).map(a=>a.app));
  for(const [goal,slugs] of Object.entries(groups)){
    assert.ok(slugs.length>=4,'too few choices for '+goal);
    assert.equal(new Set(slugs).size,slugs.length,'duplicate catalog slug in '+goal);
    for(const slug of slugs){
      assert.ok(visible.has(slug),'invalid or delisted catalog slug '+slug+' in '+goal);
    }
  }
  assert.ok(groups.decisions.includes('chore-roulette'));
  assert.ok(groups['quick-games'].includes('daily-duel'));
});

test('public Dotchi catalog aligns with its real two-choice voting product', () => {
  const app = data.find(x => x.app === 'twotaku');
  assert.ok(app && !app.hidden);
  assert.equal(app.pkg, 'com.dotchi.dotchi_app');
  assert.match(app.title, /Dotchi: This or That Polls/);
  assert.match(app.desc, /Pick A or B on everyday questions/);
  assert.doesNotMatch(app.title + app.desc, /anime|manga|Naruto|Goku/i);
  const img = catalog.indexOf('src="icons/apps/twotaku.png"');
  const card = img >= 0 ? catalog.slice(catalog.lastIndexOf('      <div class="app-card app-card-dual">',img),img+800) : '';

  assert.ok(card, 'missing indexed Dotchi catalog card');
  assert.match(card, /Dotchi: This or That Polls/);
  assert.match(card, /Vote, see results and compare opinions with friends/);
  assert.doesNotMatch(card, /anime|manga/i);
  assert.match(card, /referrer=utm_source%3Dappdevelopsk/);
});
