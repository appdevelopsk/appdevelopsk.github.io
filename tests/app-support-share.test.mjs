import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { runInNewContext } from "node:vm";

const root = new URL("../", import.meta.url);
const read = (path) => readFileSync(new URL(path, root), "utf8");
const source = read("scripts/app-share.js");
const sandbox = { module: { exports: {} }, URL };
runInNewContext(source, sandbox);
const { buildShareUrl, TEXT } = sandbox.module.exports;

test("only three real verified app landing paths can be shared", () => {
  for (const slug of ["debate-me", "future-me", "tappitsu-battle"]) {
    const url = new URL(buildShareUrl(slug));
    assert.equal(url.origin, "https://appdevelopsk.com");
    assert.equal(url.pathname, "/support/" + slug + "/");
    assert.deepEqual(Object.fromEntries(url.searchParams), {
      utm_source: "reader_share",
      utm_medium: "referral",
      utm_campaign: "app_support_share",
      utm_content: slug,
    });
    assert.equal(url.hash, "");
    assert.equal(url.username, "");
    assert.equal(url.password, "");
  }
  for (const slug of ["", "admin", "../../private", "debate-me?session=secret", "nattzy"]) {
    assert.equal(buildShareUrl(slug), null);
  }
});

test("all existing app-site interface locales receive localized share labels", () => {
  const locales = ["en","ja","zh","zh_TW","ko","es","pt","fr","de","it","ru","ar","th","id","tr","nl","vi"];
  assert.deepEqual(Object.keys(TEXT).sort(), locales.sort());
  for (const locale of locales) {
    assert.equal(TEXT[locale].length, 3, locale);
    assert.ok(TEXT[locale].every(Boolean), locale);
  }
});

test("each pilot support landing loads precisely the reviewed public asset", () => {
  for (const slug of ["debate-me", "future-me", "tappitsu-battle"]) {
    const html = read("support/" + slug + "/index.html");
    assert.equal((html.match(/<script defer src="\/scripts\/app-share\.js"/g) || []).length, 1);
    assert.ok(html.includes('data-app-share-slug="' + slug + '"'));
    assert.ok(html.includes('class="download-btns"'));
  }
});

test("share UI is reader initiated and never treats a tap as an install", () => {
  assert.match(source, /button\.addEventListener\("click"/);
  assert.match(source, /navigator\.share/);
  assert.match(source, /navigator\.clipboard\.writeText/);
  assert.match(source, /measure\("share_tap", "button"\)/);
  assert.match(source, /measure\("share_copy_success", "clipboard"\)/);
  assert.doesNotMatch(source, /purchase_completed|install_completed|first_open|registered_user/i);
  assert.match(source, /if \(window\.location\.hostname !== "appdevelopsk\.com"/);
});

test("VPS and offline release bundle both contain the shared asset", () => {
  const manifest = read("scripts/publish_app_discovery.sh");
  const bundle = read("scripts/build_site_release_bundle.py");
  assert.match(manifest, /files=\(scripts\/app-share\.js index\.html/);
  assert.match(bundle, /len\(apps\) != 31/);
});


test("live smoke rejects missing share assets or mismatched app landing bindings", () => {
  const smoke = read("scripts/check_app_discovery_live.sh");
  assert.match(smoke, /fetch '\/scripts\/app-share\.js' 'app-share\.js'/);
  assert.match(smoke, /grep -Fq 'app_support_share' "\$tmp\/app-share\.js"/);
  assert.match(smoke, /grep -Fq 'navigator\.share' "\$tmp\/app-share\.js"/);
  assert.match(smoke, /grep -Fq 'navigator\.clipboard\.writeText' "\$tmp\/app-share\.js"/);
  assert.match(smoke, /fetch '\/support\/tappitsu-battle\/' 'tappitsu-battle\.html'/);
  assert.match(smoke, /'debate-me:debate-me' 'futureme:future-me' 'tappitsu-battle:tappitsu-battle'/);
  assert.match(smoke, /data-app-share-slug=/);
  assert.match(smoke, /FAIL opt-in sharing for \$slug not deployed/);
  assert.match(smoke, /browser QA still required/);
  // Source-only and read-only: do not permit the public smoke to publish
  // or misstate a share tap as an install or an inbound human visitor.
  assert.doesNotMatch(smoke, /^\s*(?:rsync|ssh|gh workflow run)\b/m);
  assert.doesNotMatch(smoke, /install_completed/i);
});
