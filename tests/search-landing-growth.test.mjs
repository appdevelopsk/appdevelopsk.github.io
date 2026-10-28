import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
const read = path => readFileSync(new URL('../'+path,import.meta.url),'utf8');
const catalog = JSON.parse(read('apps_data.json'));
const published = slug => catalog.find(a=>a.app===slug&&!a.hidden);

test('BrainBurst and SnapLingo metadata reflects the existing public Play catalog',()=>{
 for(const slug of ['brain-burst','snaplingo']){
   const app=published(slug);
   assert.ok(app,'not a public listed app: '+slug);
   const html=read('support/'+slug+'/index.html');
   assert.match(html,new RegExp('<meta name="description" content="[^\"]+"'));
   assert.match(html,new RegExp('https://appdevelopsk\\.com/support/'+slug+'/'));
   assert.match(html,/<meta property="og:title"/);
   assert.match(html,/<meta name="twitter:card"/);
   const embedded=html.match(/<script type="application\/ld\+json">([^<]+)<\/script>/)?.[1];
   assert.ok(embedded,'missing structured app data');
   const schema=JSON.parse(embedded);
   assert.equal(schema['@type'],'SoftwareApplication');
   assert.equal(schema.operatingSystem,'Android');
   assert.ok(schema.url.endsWith('id='+app.pkg));
   assert.ok(!Object.hasOwn(schema,'aggregateRating'));
   const store=[...html.matchAll(/<a href="([^"]+play\.google\.com[^"]+)"[^>]*data-position="(hero|details)"/g)];
   assert.deepEqual(store.map(m=>m[2]).sort(),['details','hero']);
   assert.ok(store.every(m=>m[1].includes('id='+app.pkg)&&m[1].includes('referrer=')));
   assert.match(html,/placement: a\.getAttribute\('data-position'\)/);
 }
});

test('BrainBurst default text describes published daily trivia, not an unrelated memory game',()=>{
 const html=read('support/brain-burst/index.html');
 assert.match(html,/<p id="heroDesc">A daily trivia quiz/);
 assert.match(html,/Daily AI-generated quiz questions/);
 assert.doesNotMatch(html,/<span data-feat="0">Multiple brain training categories<\/span>/);
 assert.match(html,/href="\/guides\/quick-games\/"/);
});

test('unavailable Face Reaction Battle stays unavailable and offers distinct published games',()=>{
 const html=read('support/face-reaction-battle/index.html');
 assert.match(html,/Not currently available for download/);
 assert.match(html,/different games by SK Apps, not replacements/);
 for(const slug of ['instant-judge','blur']) {
  const app=published(slug);assert.ok(app);
  assert.ok(html.includes('data-alternative="'+slug+'"'));
  assert.ok(html.includes('id='+app.pkg));
  assert.ok(html.includes('utm_campaign%3Dsupport_face_reaction_alternatives'));
 }
 assert.match(html,/placement: a\.hasAttribute\('data-alternative'\)/);
});

test('public catalog icons are crawlable and explicit VPS release is non-destructive',()=>{
 const robots=read('robots.txt');
 assert.match(robots,/Allow: \/icons\/apps\//);
 const pub=read('scripts/publish_app_discovery.sh');
 assert.match(pub,/--dry-run/);
 assert.match(pub,/support\/brain-burst\/index\.html/);
 assert.match(pub,/support\/snaplingo\/index\.html/);
 assert.match(pub,/support\/face-reaction-battle\/index\.html/);
 assert.match(pub,/robots\.txt/);
 assert.match(pub,/rsync -avR --itemize-changes/);
 const live=read('scripts/check_app_discovery_live.sh');
 assert.match(live,/data-position="hero"/);
 assert.match(live,/Allow: \/icons\/apps\//);
});

test('daily live acquisition check is read-only, scheduled and fails visibly on stale VPS',()=>{
 const workflow=read('.github/workflows/live-acquisition-smoke.yml');
 assert.match(workflow,/cron: '40 0 \* \* \*'/);
 assert.match(workflow,/workflow_dispatch:/);
 assert.match(workflow,/push:\s*\n\s*branches: \[main\]/);
 assert.match(workflow,/support\/\*\*/);
 assert.match(workflow,/apps_data\.json/);
 assert.match(workflow,/contents: read/);
 assert.match(workflow,/bash scripts\/check_app_discovery_live\.sh/);
 assert.doesNotMatch(workflow,/publish_app_discovery\.sh --apply\s*\n\s*(?:git|rsync|bash)/);
 assert.match(workflow,/if: failure\(\)/);
});

test('production smoke refuses the stale anime-only Dotchi catalog card',()=>{
 const live=read('scripts/check_app_discovery_live.sh');
 assert.match(live,/Dotchi: This or That Polls/);
 assert.match(live,/FAIL Dotchi catalog still presents an anime-only app/);
 assert.match(live,/fetch '\/apps' 'apps\.html'/);
});
