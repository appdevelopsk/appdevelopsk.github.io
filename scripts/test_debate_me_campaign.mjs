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


test("Debate Me search snippet, Open Graph and SoftwareApplication describe the same actual app", () => {
  const title = html.match(/<title>([^<]+)<\/title>/)?.[1];
  const meta = html.match(/<meta name="description" content="([^"]+)"\s*\/>/)?.[1];
  const og = html.match(/<meta property="og:description" content="([^"]+)"/)?.[1];
  const structured = JSON.parse(html.match(/<script type="application\/ld\+json">\s*([\s\S]*?)\s*<\/script>/)?.[1] || "null");
  assert.equal(title, "Debate Me – AI Debate Practice App for Android | SK APPS");
  assert.ok(title.length <= 65);
  assert.ok(meta && meta.length >= 100 && meta.length <= 160);
  assert.equal(meta, og);
  assert.equal(meta, structured?.description);
  assert.equal(structured?.name, "Debate Me");
  assert.equal(structured?.operatingSystem, "Android");
  assert.equal(structured?.downloadUrl, "https://play.google.com/store/apps/details?id=jp.appdevelopsk.debate_me");
  assert.match(meta, /AI debate practice app/);
  assert.match(meta, /rebuttals/);
  assert.match(meta, /Google Play/);
});

test("the sample exercise is concrete, accessible and preserves help guide links", () => {
  const guide = html.match(/<section class="card" id="debate-practice-guide"[\s\S]*?<\/section>/)?.[0];
  assert.ok(guide);
  assert.match(guide, /Should homework be optional\?/);
  assert.match(guide, /<h2 id="debate-practice-guide-heading">/);
  assert.match(guide, /<ol lang="en"/);
  assert.equal((guide.match(/<li>/g) || []).length, 3);
  for (const part of ["Claim:", "Reason:", "Rebuttal:"]) assert.ok(guide.includes(part));
  assert.match(guide, /href="\/guides\/ai-debate-practice\/"/);
  assert.match(guide, /href="\/guides\/ai-debate-practice\/ja\/"/);
  assert.ok(html.includes('href="https://appdevelopsk.com/support/debate-me/"'));
});
