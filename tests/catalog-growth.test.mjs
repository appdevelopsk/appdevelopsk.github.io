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
    assert.equal(apps.length,slug==='quick-games'?5:4);
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
  assert.ok(groups['quick-games'].includes('twotaku'));
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
  const card = catalog.match(/<a class="app-card" href="[^"]+id=com\.dotchi\.dotchi_app[\s\S]+?<\/a>/)?.[0];
  assert.ok(card, 'missing indexed Dotchi catalog card');
  assert.match(card, /Dotchi: This or That Polls/);
  assert.match(card, /Vote, see results and compare opinions with friends/);
  assert.doesNotMatch(card, /anime|manga/i);
  assert.match(card, /referrer=utm_source%3Dappdevelopsk/);
});


test('Dotchi receives a truthful, measurable quick-games guide placement', () => {
  const page=read('guides/quick-games/index.html');
  const source=data.find(x=>x.app==='twotaku'&&!x.hidden);
  assert.ok(source,'Dotchi must be publicly available in the catalog');
  assert.equal(source.pkg,'com.dotchi.dotchi_app');
  assert.match(source.desc,/Pick A or B on everyday questions/);
  const actual=[...page.matchAll(/<a class="store" data-app="twotaku" href="([^"]+)"/g)];
  assert.equal(actual.length,1,'One and only one Dotchi CTA in the guide');
  const url=actual[0][1];
  assert.match(url,/id=com\.dotchi\.dotchi_app/);
  assert.match(url,/utm_campaign=quick_games/);
  assert.match(url,/referrer=utm_source%3Dappdevelopsk%26utm_medium%3Dguide%26utm_campaign%3Dquick_games/);
  assert.doesNotMatch(url,/user_?id|device_?id|email|answer/i);
  assert.match(page,/For A-or-B polls with friends/);
  assert.match(page,/Pick A or B on everyday questions/);
  assert.match(page,/guide_store_click/);
  const schemaText=page.match(/<script type="application\/ld\+json">([^<]+)<\/script>/)?.[1];
  assert.ok(schemaText,'missing JSON-LD');
  const schema=JSON.parse(schemaText);
  assert.equal(schema['@type'],'ItemList');
  assert.equal(schema.itemListElement.length,5);
  assert.deepEqual(schema.itemListElement.map(item=>item.position),[1,2,3,4,5]);
  assert.equal(schema.itemListElement[2].url,'https://play.google.com/store/apps/details?id=com.dotchi.dotchi_app');
});



test('home features public Dotchi instead of an unavailable app, with 17 language captions', () => {
  const home=read('index.html');
  const featured=home.match(/<!-- Featured Apps -->([\s\S]*?)<\/section>/)?.[1];
  assert.ok(featured,'missing featured section');
  assert.match(featured,/href="support\/twotaku\/"/);
  assert.match(featured,/src="icons\/twotaku\.png"/);
  assert.match(featured,/data-app-desc="twotaku"/);
  assert.doesNotMatch(featured,/href="support\/face-reaction-battle\/"/,
    'unavailable Face Reaction Battle must not be featured as downloadable');
  assert.ok(data.some(app=>app.app==='twotaku'&&!app.hidden),'Dotchi is not in the published catalog');
  const match=home.match(/const APP_DESC=(\{[\s\S]*?\});\s*const origApplyLang=/);
  assert.ok(match,'missing localized featured app captions');
  const translations=runInNewContext('('+match[1]+')');
  for(const lang of ['en','ja','zh','zh_TW','ko','es','pt','fr','de','it','ru','ar','th','id','tr','nl','vi']){
    assert.equal(typeof translations[lang].twotaku,'string',lang+' must localize Dotchi caption');
    assert.ok(translations[lang].twotaku.length>=12,lang+' missing meaningful caption');
  }
  assert.match(home,/gtag\('event', 'app_view'/,'homepage app-card clicks remain measurable');
});
