import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";

const source = readFileSync(fileURLToPath(new URL("../index.html", import.meta.url)), "utf8");

test("homepage category and app grids shrink below former 280/300px minimum", () => {
  assert.match(source, /repeat\(auto-fit, minmax\(min\(100%, 280px\), 1fr\)\)/);
  assert.match(source, /repeat\(auto-fill, minmax\(min\(100%, 300px\), 1fr\)\)/);
  assert.doesNotMatch(source, /minmax\(280px, 1fr\)|minmax\(300px, 1fr\)/);
});
test("homepage app card text wraps without forcing flex overflow", () => {
  assert.match(source, /\.app-card > :not\(\.app-icon\):not\(\.app-icon-placeholder\)\s*\{\s*min-width:\s*0;\s*overflow-wrap:\s*anywhere;/);
});
