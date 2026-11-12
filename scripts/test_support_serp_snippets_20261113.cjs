"use strict";

const { test } = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const nodePath = require("node:path");

// Source-level regression checks for the low-CTR app support pages.
// These do not prove that the production host serves this commit.
const cases = [
  {
    slug: "debate-me",
    title: "Debate Me: AI Debate Practice App for Android | SK APPS",
    description: "Practice debates against an AI opponent in Debate Me for Android. Pick a topic, build your argument and review feedback. Explore the app on Google Play.",
    hasPlayLink: true,
  },
  {
    slug: "brain-burst",
    title: "BrainBurst: Daily Trivia & 1v1 Quiz Battles | Android",
    description: "Challenge yourself with daily AI-generated trivia in BrainBurst, then try 1v1 quiz battles. Explore the Android app on Google Play.",
    hasPlayLink: true,
  },
  {
    slug: "taletime",
    title: "TaleTime: AI Story Maker for Parents & Kids | SK APPS",
    description: "Create stories together in TaleTime: choose a theme and hero, take turns with your child, and save your AI-assisted story to reread. Learn how it works.",
    hasPlayLink: false,
  },
];

function tagContent(html, pattern) {
  const matches = [...html.matchAll(pattern)];
  assert.equal(matches.length, 1, "expected exactly one matching metadata tag");
  return matches[0][1];
}

for (const spec of cases) {
  test(`support/${spec.slug} keeps truthful unique search metadata and analytics`, () => {
    const file = nodePath.resolve(__dirname, "..", "support", spec.slug, "index.html");
    const html = fs.readFileSync(file, "utf8");
    assert.equal(tagContent(html, /<title>([^<]*)<\/title>/g), spec.title);
    assert.equal(tagContent(html, /<meta name="description" content="([^"]*)"/g), spec.description);
    assert.equal(tagContent(html, /<meta property="og:description" content="([^"]*)"/g), spec.description);
    assert.equal(tagContent(html, /<link rel="canonical" href="([^"]*)"/g), `https://appdevelopsk.com/support/${spec.slug}/`);
    assert.equal((html.match(/googletagmanager.com\/gtag\/js/g) || []).length, 1);
    assert.match(html, /gtag\('event', 'download_click'/);
    if (spec.hasPlayLink) {
      assert.match(html, /https:\/\/play\.google\.com\/store\/apps\/details/);
    } else {
      assert.doesNotMatch(html, /https:\/\/play\.google\.com\/store\/apps\/details/);
    }
  });
}
