// Renders the README screenshots (German and English) from the dev server with headless Chrome.
//   node tools/screenshots.mjs [output dir, default screenshots]
// Needs Google Chrome (macOS path below, or CHROME=/path) and Node 22+; starts and stops the dev
// server (tools/dev_server.py, port 8401) and the browser itself. The status line is patched to
// show a running ser2net and the current app version.
import { spawn } from "node:child_process";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";

const OUT = process.argv[2] || "screenshots";
const ROOT = path.resolve(path.dirname(new URL(import.meta.url).pathname), "..");
const VERSION = /^version: "(.+)"/m.exec(fs.readFileSync(path.join(ROOT, "device_proxy/config.yaml"), "utf8"))[1];
const CHROME = process.env.CHROME || "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
const BASE = "http://127.0.0.1:8401/";
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

const server = spawn(path.join(ROOT, ".venv/bin/python"), ["tools/dev_server.py", "8401"], { cwd: ROOT, stdio: "ignore" });
const profile = fs.mkdtempSync(path.join(os.tmpdir(), "dp-chrome-"));
const chrome = spawn(CHROME, ["--headless=new", "--remote-debugging-port=9333", `--user-data-dir=${profile}`, "--window-size=1280,1000", "--hide-scrollbars", "about:blank"], { stdio: "ignore" });
let stopped = false;
const stop = () => {
  if (stopped) return;
  stopped = true;
  server.kill();
  chrome.kill();
  try { fs.rmSync(profile, { recursive: true, force: true, maxRetries: 5 }); } catch { /* the temp folder goes with the system */ }
};
process.on("exit", stop);
for (let i = 0; i < 60; i++) {  // wait for both, then let the simulated devices produce data
  try { await fetch(BASE + "api/state"); await fetch("http://127.0.0.1:9333/json/version"); break; } catch { await sleep(500); }
}
await sleep(12000);

const targets = await (await fetch("http://127.0.0.1:9333/json/list")).json();
const ws = new WebSocket(targets.find((t) => t.type === "page").webSocketDebuggerUrl);
await new Promise((r) => (ws.onopen = r));
let id = 0;
const pending = new Map();
ws.onmessage = (m) => {
  const d = JSON.parse(m.data);
  if (d.id && pending.has(d.id)) { pending.get(d.id)(d); pending.delete(d.id); }
};
const send = (method, params = {}) => new Promise((res) => { const i = ++id; pending.set(i, res); ws.send(JSON.stringify({ id: i, method, params })); });
const evalJs = async (expression) => (await send("Runtime.evaluate", { expression, awaitPromise: true, returnByValue: true })).result?.result?.value;

const FIND = `const f=(r,fn)=>{for(const e of r.querySelectorAll('*')){if(fn(e))return e;if(e.shadowRoot){const x=f(e.shadowRoot,fn);if(x)return x}}};`;
// the status as it would look on a running system
const PATCH = `(() => { const orig = window.fetch.bind(window); window.fetch = async (u, o) => { const r = await orig(u, o);
  if (String(u).includes("api/state")) { const d = await r.clone().json(); d.version = "${VERSION}"; d.ser2net_running = true; d.ser2net_version = "4.6.8";
    return new Response(JSON.stringify(d), { status: 200, headers: { "content-type": "application/json" } }); } return r; }; })();`;

const state = await (await fetch(BASE + "api/state")).json();
const by = (name) => state.connections.find((c) => c.name === name).id;
const IDS = { ehz: by("eHZ Stromzähler"), zwave: by("Z-Wave-Gateway"), modbus: by("SolarEdge Wechselrichter"), eo: by("FAM-USB") };

await send("Page.enable");
await send("Page.addScriptToEvaluateOnNewDocument", { source: PATCH });

async function shot(file, height, prepare) {
  await send("Emulation.setDeviceMetricsOverride", { width: 1280, height, deviceScaleFactor: 2, mobile: false });
  await prepare();
  await sleep(2500);
  const r = await send("Page.captureScreenshot", { format: "png" });
  fs.writeFileSync(`${OUT}/${file}`, Buffer.from(r.result.data, "base64"));
  console.log("wrote", file);
}

const go = async (lang, hash) => {
  await send("Page.navigate", { url: BASE });
  await sleep(800);
  await evalJs(`localStorage.setItem('device_proxy.lang','${lang}'); location.hash='${hash}'; location.reload(); 1`);
  await sleep(2500);
};

for (const lang of ["de", "en"]) {
  fs.mkdirSync(`${OUT}/${lang}`, { recursive: true });
  const dir = (f) => `${lang}/${f}`;
  await shot(dir("overview.png"), 900, () => go(lang, "#/connections"));
  await shot(dir("modbus.png"), 1000, () => go(lang, `#/connection/${IDS.modbus}`));
  await shot(dir("edit.png"), 1000, () => go(lang, `#/edit/${IDS.zwave}`));
  await shot(dir("trace.png"), 1000, () => go(lang, `#/trace/${IDS.ehz}`));
  await shot(dir("enocean.png"), 1000, () => go(lang, `#/connection/${IDS.eo}`));
  await shot(dir("import.png"), 1000, async () => {
    await go(lang, "#/connections");
    const yaml = "%YAML 1.1\\n---\\nconnection: &ehz\\n  accepter: tcp,3335\\n  connector: serialdev,/dev/serial/by-id/usb-CP2102-if00-port0,9600n81\\nconnection: &bwt\\n  accepter: tcp,3999\\n  connector: serialdev,/dev/serial/by-id/usb-FTDI-if00-port0,19200e71\\nconnection: &zwave\\n  accepter: tcp,3333\\n  connector: serialdev,/dev/serial/by-id/usb-Zooz-if00,115200n81\\n";
    await evalJs(`(async()=>{${FIND} const app=f(document,e=>e.tagName==='DEVICE-PROXY'); app.dispatchEvent(new CustomEvent('dp-import-open')); await new Promise(r=>setTimeout(r,500));
      const ta=f(document,e=>e.tagName==='TEXTAREA'); ta.value="${yaml}"; ta.dispatchEvent(new Event('input',{bubbles:true})); await new Promise(r=>setTimeout(r,200));
      const b=f(document,e=>e.tagName==='BUTTON'&&e.classList.contains('btn-p')&&!e.disabled&&e.closest('section')); b.click(); return 1})()`);
  });
}
ws.close();
stop();
process.exit(0);
