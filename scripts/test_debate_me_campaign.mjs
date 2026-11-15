import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

const html = readFileSync(new URL("../support/debate-me/index.html", import.meta.url), "utf8");

test("Debate Me Play store CTAs share one campaign but keep independent placements", () => {
  const tags = [...html.matchAll(/<a\b[^>]*href="([^"]*play\.google\.com\/store\/apps\/details[^"]*)"[^>]*>/g)];
  assert.equal(tags.length, 2, "expected hero and details CTAs");
  const positions = [];
  for (const [tag, href] of tags.map(m => [m[0], m[1]])) {
    const url = new URL(href.replaceAll("&amp;", "&"));
    assert.equal(url.protocol, "https:");
    assert.equal(url.hostname, "play.google.com");
    assert.equal(url.searchParams.get("id"), "jp.appdevelopsk.debate_me");
    assert.equal(url.searchParams.get("utm_source"), "appdevelopsk");
    assert.equal(url.searchParams.get("utm_medium"), "web");
    assert.equal(url.searchParams.get("utm_campaign"), "support_debate-me");
    const referrer = new URLSearchParams(url.searchParams.get("referrer") || "");
    assert.equal(referrer.get("utm_campaign"), "support_debate-me");
    assert.equal(referrer.get("utm_source"), "appdevelopsk");
    assert.equal(referrer.get("utm_medium"), "web");
    const placement = tag.match(/data-position="([^"]+)"/);
    assert.ok(placement);
    positions.push(placement[1]);
  }
  assert.deepEqual(positions.sort(), ["details", "hero"]);
});

test("existing GA4 per-position event data remains intact", () => {
  assert.match(html, /gtag\('event', 'download_click'/);
  assert.match(html, /a\.getAttribute\('data-position'\)/);
  assert.doesNotMatch(html, /support_debate_me_hero/);
});
