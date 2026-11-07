import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';

const html=readFileSync(new URL('../support/one-tap-routine/index.html',import.meta.url),'utf8');

test('support page accurately describes the one-tap habit tracker',()=>{
  assert.match(html,/<title>One Tap Routine – Habit Tracker/);
  assert.match(html,/One-tap check-ins/);
  assert.match(html,/Progress &amp; streaks/);
  assert.match(html,/Exported backups may contain private routine names/);
  assert.match(html,/not a phone-locking, device-management or screen-blocking app/);
  assert.doesNotMatch(html,/Lock now|15\/30\/60 min|emergency unlock|Guided Access|Device Owner|Lock Task Mode|focus lock with away detection/i);
});

test('has one canonical and accurate FAQ structured data',()=>{
  assert.equal((html.match(/rel="canonical"/g)||[]).length,1);
  assert.match(html,/https:\/\/appdevelopsk\.com\/support\/one-tap-routine\//);
  assert.match(html,/"@type":"FAQPage"/);
  assert.match(html,/One Tap Routine is a habit tracker, not a phone-locking application/);
  assert.doesNotMatch(html,/FocusLock/i);
  assert.match(html,/https:\/\/appdevelopsk\.com\/privacy-policy\/one-tap-routine\//);
  assert.doesNotMatch(html,/play\.google\.com\/store\/apps\/details\?id=/);
});

test('does not fake a released weekly review or currently available premium purchase',()=>{
  assert.match(html,/weekly review is being tested separately/);
  assert.match(html,/may not yet be available in released versions/);
  assert.match(html,/If you bought a premium upgrade previously/);
  assert.doesNotMatch(html,/permanently removes ads|Subscribe now|Click to download/i);
});
