import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
const html=readFileSync(new URL('../share/idea-market/index.html',import.meta.url),'utf8');
const js=readFileSync(new URL('../share/idea-market/referral.js',import.meta.url),'utf8');
test('share page gives real Play acquisition fallback and an explicit app open',()=>{
 assert.match(html,/play\.google\.com\/store\/apps\/details\?id=jp\.appdevelopsk\.ideamarket/);
 assert.match(html,/id="open-app"/);
 assert.match(html,/script src="referral\.js"/);
 assert.match(html,/noindex,nofollow/);
});
test('identifiers cannot inject scripts or arbitrary external redirects',()=>{
 assert.match(js,/\[a-zA-Z0-9_-\]\{1,96\}/);
 assert.match(js,/encodeURIComponent\(id\)/);
 assert.match(js,/ideamarket:\/\/open\/ideas\//);
 assert.doesNotMatch(js,/innerHTML|window\.location\s*=|fetch\(/);
});
