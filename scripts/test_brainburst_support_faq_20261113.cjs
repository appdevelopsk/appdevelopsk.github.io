"use strict";
const { test } = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");

const html = fs.readFileSync(path.resolve(__dirname, "../support/brain-burst/index.html"), "utf8");

test("BrainBurst FAQ excludes unverified purchase, subscription, and offline instructions", () => {
  for (const key of ["faq1q", "faq1a", "faq3q", "faq3a", "faq4q", "faq4a"]) {
    assert.equal(html.includes('data-i18n="' + key + '"'), false);
    assert.equal(html.includes("," + key + ':"'), false);
  }
  for (const unsupported of [
    "How do I restore my purchase?",
    "How do I cancel a subscription?",
    "Many features work offline.",
    "購入を復元するには？",
    "サブスクリプションをキャンセルするには？",
  ]) assert.equal(html.includes(unsupported), false, "unsupported claim: " + unsupported);
});

test("BrainBurst support keeps translated FAQ, Play links and attribution", () => {
  for (const key of ["faq2q", "faq2a", "faq5q", "faq5a", "faq6q", "faq6a"]) {
    assert.equal(html.includes('data-i18n="' + key + '"'), true);
    assert.equal(html.split("," + key + ':"').length - 1, 17);
  }
  assert.equal(
    html.split("https://play.google.com/store/apps/details?id=com.brainburst.brain_burst").length - 1, 3
  );
  assert.equal(html.includes("gtag('event', 'download_click'"), true);
  assert.equal(html.includes('<link rel="canonical" href="https://appdevelopsk.com/support/brain-burst/">'), true);
  assert.equal(
    html.includes('<meta name="description" content="Challenge yourself with daily AI-generated trivia'),
    true
  );
});
