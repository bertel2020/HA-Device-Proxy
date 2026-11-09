// Builds the web interface the app serves from the sources in src/.
//
//   node build.mjs            write ../device_proxy/app/device_proxy/web/app.js
//   node build.mjs --check    fail if that file is out of date (CI)
//
// One bundled file (Lit included), so a browser never mixes a new page with a cached old part.
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import * as esbuild from "esbuild";

const here = path.dirname(fileURLToPath(import.meta.url));
const target = path.join(here, "../device_proxy/app/device_proxy/web/app.js");
const HEADER = "// GENERATED FILE - do not edit. Edit panel-src/src/ and run: node panel-src/build.mjs\n";

// One file per language, shared with the app. These sections are the web interface's.
const localeDir = path.join(here, "../device_proxy/app/device_proxy/locales");
const SECTIONS = ["text", "events", "notes", "states", "changes", "settings", "system", "errors"];
const CHECKED = ["text", "notes", "changes", "settings", "system"]; // all of these are worded in English too
const COMPLETE = ["de", "en"]; // the languages that must have every text; others may be partial
const locales = Object.fromEntries(fs.readdirSync(localeDir).filter((f) => f.endsWith(".json")).sort()
  .map((f) => [f.slice(0, -5), JSON.parse(fs.readFileSync(path.join(localeDir, f), "utf8"))]));
const placeholders = (text) => String(text).match(/\{\w+\}/g) || [];
const problems = [];
for (const [code, locale] of Object.entries(locales)) {
  if (!/^[a-z]{2}$/.test(code)) problems.push(`${code}.json: the file name must be a two-letter language code`);
  if (!locale.name) problems.push(`${code}: "name" is missing`);
  for (const section of CHECKED) {
    const english = locales.en[section], own = locale[section] || {};
    for (const key of Object.keys(english)) {
      if (!(key in own)) { if (COMPLETE.includes(code)) problems.push(`${code}.${section}.${key} is missing`); continue; }
      const unknown = placeholders(own[key]).filter((p) => !placeholders(english[key]).includes(p));
      if (unknown.length) problems.push(`${code}.${section}.${key}: ${unknown.join(", ")} is not in the English text`);
    }
    for (const key of Object.keys(own)) if (!(key in english)) problems.push(`${code}.${section}.${key} is not in en.json`);
  }
}
if (problems.length) {
  console.error(problems.join("\n"));
  process.exit(1);
}
// English for what a language leaves out, so the page never shows a key
const bundled = Object.fromEntries(Object.entries(locales).map(([code, locale]) => [code, {
  name: locale.name,
  ...Object.fromEntries(SECTIONS.map((s) => [s, s === "errors" ? locale.errors || {} : { ...locales.en[s], ...locale[s] }])),
}]));

const result = await esbuild.build({
  entryPoints: [path.join(here, "src/main.js")],
  bundle: true,
  format: "esm",
  target: ["es2021"],
  minify: true,
  legalComments: "eof",
  write: false,
  define: { __LOCALES__: JSON.stringify(bundled) },
});
const built = HEADER + result.outputFiles[0].text;

if (process.argv.includes("--check")) {
  const current = fs.existsSync(target) ? fs.readFileSync(target, "utf8") : "";
  if (current !== built) {
    console.error("web/app.js is out of date. Run: node panel-src/build.mjs");
    process.exit(1);
  }
  console.log("web/app.js is up to date.");
} else {
  fs.writeFileSync(target, built);
  console.log(`Wrote ${path.relative(process.cwd(), target)} (${Math.round(built.length / 1024)} kB).`);
}
