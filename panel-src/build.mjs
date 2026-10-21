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

const result = await esbuild.build({
  entryPoints: [path.join(here, "src/main.js")],
  bundle: true,
  format: "esm",
  target: ["es2021"],
  minify: true,
  legalComments: "eof",
  write: false,
});
const built = HEADER + result.outputFiles[0].text;

// Both languages need the same texts (a missing one would show its key).
const { LANGUAGES } = await import("./src/i18n.js");
for (const [name, table] of Object.entries(LANGUAGES)) {
  const de = new Set(Object.keys(table.de)), en = new Set(Object.keys(table.en));
  const missing = [...[...de].filter((k) => !en.has(k)).map((k) => `en.${k}`), ...[...en].filter((k) => !de.has(k)).map((k) => `de.${k}`)];
  if (missing.length) {
    console.error(`${name}: missing ${missing.join(", ")}`);
    process.exit(1);
  }
}

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
