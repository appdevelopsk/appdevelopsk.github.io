import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {Script,runInNewContext} from 'node:vm';
const read = p => readFileSync(new URL('../'+p, import.meta.url),'utf8');
const data = JSON.parse(read('apps_data.json'));
const catalog = read('apps.html');
const sitemap = read('sitemap.xml');
const guides = ['quick-games','daily-habits'];

test('catalog search retains 92 real indexed store cards and passes install referrer',()=>{
  const visible=data.filter(x=>!x.hidden);
  const tags=[...catalog.matchAll(/<a class="app-card" href="([^"]+)"/g)];
  assert.equal(visible.length,92);
  assert.equal(tags.length,visible.length);
  for (const entry of visible) {
    assert.ok(tags.some(t=>t[1].includes('id='+entry.pkg)),entry.app);
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
