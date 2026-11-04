import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

const pages = [
  ['30sec-challenge', 'com.thirtysecchallenge.thirtySecChallenge'],
  ['debate-me', 'jp.appdevelopsk.debate_me'],
];

for (const [slug, pkg] of pages) {
  test(`${slug} support page has verifiable application metadata`, () => {
    const html = readFileSync(new URL(`../support/${slug}/index.html`, import.meta.url), 'utf8');
    const schemas = [...html.matchAll(/<script type="application\/ld\+json">([\s\S]*?)<\/script>/g)].map(m => JSON.parse(m[1]));
    const app = schemas.find(s => s['@type'] === 'SoftwareApplication');
    const desc = html.match(/<meta name="description" content="([^"]+)"/)?.[1];
    assert.ok(app);
    assert.equal(app.operatingSystem, 'Android');
    assert.equal(app.url, `https://appdevelopsk.com/support/${slug}/`);
    assert.equal(app.downloadUrl, `https://play.google.com/store/apps/details?id=${pkg}`);
    assert.equal(app.description, desc);
    assert.match(html, new RegExp(`rel="canonical" href="https://appdevelopsk\\.com/support/${slug}/"`));
    assert.ok(html.includes(`id=${pkg}`), 'must match visible store link');
    assert.equal('offers' in app, false, 'do not invent prices');
    assert.equal('aggregateRating' in app, false, 'do not invent ratings');
  });
}
