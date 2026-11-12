"use strict";
const { test } = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");

const html = fs.readFileSync(path.resolve(__dirname, "../support/brain-burst/index.html"), "utf8");

test("BrainBurst FAQ excludes unverified purchase, subscription, and offline instructions", () => {
  for (const key of ["faq1q", "faq1a", "faq3q", "faq3a", "faq4q", "faq4a"]) {
    assert.doesNotMatch(html, new RegExp("data-i18n=\\\"" + key + "\\\""));
    assert.doesNotMatch(html, new RegExp("(?:^|,)" + key + ":\\\"", "m"));
  }
  for (const unsupported of [
    "How do I restore my purchase?",
    "How do I cancel a subscription?",
    "Many features work offline.",
    "購入を復元するには？",
    "サブスクリプションをキャンセルするには？",
  ]) assert.ok(!html.includes(unsupported), "unsupported claim: " + unsupported);
});

test("BrainBurst support keeps useful translated FAQ, real Android links and attribution", () => {
  for (const key of ["faq2q", "faq2a", "faq5q", "faq5a", "faq6q", "faq6a"]) {
    assert.match(html, new RegExp("data-i18n=\\\"" + key + "\\\""));
    assert.equal((html.match(new RegExp("," + key + ":\\\"", "g")) || []).length, 17);
  }
  assert.equal((html.match(/https:\/\/play\.google\.com\/store\/apps\/details\?id=com\.brainburst\.brain_burst/g) || []).length, 3);
  assert.match(html, /gtag\('event', 'download_click'/);
  assert.match(html, /<link rel="canonical" href="https:\/\/appdevelopsk\.com\/support\/brain-burst\/"/);
  assert.match(html, /<meta name="description" content="Challenge yourself with daily AI-generated trivia/);
});
