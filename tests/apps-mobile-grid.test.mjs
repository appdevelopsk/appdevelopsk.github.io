import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";

const source = readFileSync(fileURLToPath(new URL("../apps.html", import.meta.url)), "utf8");
test("app catalog grid fits viewports narrower than the original 300px column", () => {
  const css = source.match(/\.grid\s*\{[^}]*\}/)?.[0] ?? "";
  assert.match(css, /grid-template-columns:\s*repeat\(auto-fill,minmax\(min\(100%,300px\),1fr\)\)/);
  assert.doesNotMatch(css, /minmax\(300px,1fr\)/);
});
test("mobile page retains its responsive viewport setting", () => {
  assert.match(source, /<meta name="viewport" content="width=device-width, initial-scale=1\.0">/);
});
