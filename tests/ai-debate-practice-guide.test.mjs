import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { join } from 'node:path';

const ROOT = process.cwd();
const pages = [
  ['en','guides/ai-debate-practice/index.html','https://appdevelopsk.com/guides/ai-debate-practice/'],
  ['ja','guides/ai-debate-practice/ja/index.html','https://appdevelopsk.com/guides/ai-debate-practice/ja/'],
];

for (const [locale,path,canonical] of pages) {
  test(`${locale} guide has unique title, canonical, real Play CTA and no fake AI chat`, () => {
    const html=readFileSync(join(ROOT,path),'utf8');
    assert.match(html,new RegExp(`<html lang="${locale}">`));
    assert.equal((html.match(/<h1\b/g)||[]).length,1);
    assert.equal((html.match(/<title>/g)||[]).length,1);
    assert.ok(html.includes(`<link rel="canonical" href="${canonical}">`));
    assert.ok(html.includes('https://play.google.com/store/apps/details?id=jp.appdevelopsk.debate_me'));
    assert.ok(html.includes('data-app="debate-me"'));
    assert.ok(html.includes("'download_click'"));
    assert.ok(html.includes('data-guide-detail="debate-me"'));
    assert.ok(html.includes('not a live AI chat') || html.includes('リアルタイム対話は行いません'));
    assert.ok(!html.includes('guaranteed results'));
  });
  test(`${locale} has reciprocal hreflang and valid JSON-LD`, () => {
    const html=readFileSync(join(ROOT,path),'utf8');
    for (const [language,,url] of pages) assert.ok(html.includes(`hreflang="${language}" href="${url}"`));
    const m=html.match(/<script type="application\/ld\+json">([^<]+)<\/script>/);
    assert.ok(m);
    const schema=JSON.parse(m[1]);
    assert.equal(schema['@type'],'Article');
    assert.equal(schema.inLanguage,locale);
    assert.equal(schema.mainEntityOfPage,canonical);
  });
}
