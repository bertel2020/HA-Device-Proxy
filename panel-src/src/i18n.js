// The texts live in device_proxy/app/device_proxy/locales/<language>.json, one file per language;
// the build (build.mjs) puts them here as __LOCALES__, with English for whatever a language leaves
// out. Events and import notes come from the app as a code plus values; they are worded here, so
// the history reads in the viewer's language.
const LOCALES = __LOCALES__;
const CODES = Object.keys(LOCALES);

/** [code, name] of every language, for the language pickers. */
export const LANGUAGES = CODES.map((code) => [code, LOCALES[code].name]);

const stored = (() => {
  try { return localStorage.getItem("device_proxy.lang"); } catch { return null; }
})();
const browser = (globalThis.navigator?.language || "en").slice(0, 2).toLowerCase();
export let lang = CODES.includes(stored) ? stored : CODES.includes(browser) ? browser : "en";
const texts = () => LOCALES[lang];

export function setLang(value) {
  lang = value;
  try { localStorage.setItem("device_proxy.lang", value); } catch { /* private window */ }
}

// The app words field errors and API answers in English; "errors" of a language holds a pattern
// for each. Compiled once, on first use.
const compiled = new Map();
const errorPatterns = () => {
  if (!compiled.has(lang)) compiled.set(lang, Object.entries(texts().errors).map(([pattern, text]) => [new RegExp(pattern), text]));
  return compiled.get(lang);
};

export function fieldError(message) {
  for (const [pattern, text] of errorPatterns()) if (pattern.test(message)) return message.replace(pattern, text);
  return message;
}

const fill = (text, params = {}) =>
  text.replace(/\{(\w+)\}/g, (m, key) => {
    const value = params[key];
    if (value === undefined) return m;
    if (value === null) return "–";
    return Array.isArray(value) ? value.join(", ") : typeof value === "object" ? JSON.stringify(value) : String(value);
  });

export const retriesText = (n) => t(n === 0 ? "retries_0" : n === 1 ? "retries_1" : "retries_n", { n });
export const t = (key, params) => fill(texts().text[key] ?? key, params);
/** A text with a count in it: the key's "_1" text when the count is 1 ("1 Eintrag", not "1 Einträge"). */
export const tn = (key, count, params) => t(count === 1 && `${key}_1` in texts().text ? `${key}_1` : key, params);

const settingValue = (key, value) => {
  if (typeof value === "boolean") return t(value ? "histOn" : "histOff");
  if (key === "listen") return t(`net_${value}`);
  if (key === "lan_networks") return value.trim().replace(/\bown\b/, t("lanOwn")) || "–";
  if (key === "source") return value === "custom" ? t("own") : t("forms");
  return value === "" ? "–" : String(value);
};

/** One change of a configuration version in the viewer's language. */
function changeText(c) {
  const words = texts().changes;
  if (c.connection || !c.fields) return c.fields ? `${c.connection}: ${c.fields.join(", ")}` : `${c.connection || words.settings} ${words[c.change] || c.change}`;
  const names = texts().settings;
  const shown = c.fields.slice(0, 3).map((k) => {
    const name = names[k] || k;
    return c.values && k in c.values ? `${name}: ${settingValue(k, c.values[k])}` : `${name} ${words.changed}`;
  });
  return shown.join(", ") + (c.fields.length > 3 ? ` +${c.fields.length - 3}` : "");
}

/** The changes of a configuration version in the viewer's language. */
export function changesText(changes) {
  return (changes || []).map(changeText).join("; ");
}

/** Technical error texts of the system in plain words. */
export function plain(text) {
  const words = texts().system;
  return String(text)
    .replace(/\[Errno (?:61|111)\] Connect call failed \('([^']+)', (\d+)\)/g, (_, host, port) => fill(words.refused, { host, port }))
    .replace(/\[Errno (?:113|65)\][^)]*/g, () => words.no_route)
    .replace(/host name (\S+) not found \([^)]*\)/g, (_, host) => fill(words.host_not_found, { host }))
    .replace(/(\S+) not reached within ([\d.]+) s/g, (_, target, seconds) => fill(words.not_reached, { target, seconds }))
    .replace(/\btimed out\b/g, () => words.timed_out);
}

export function eventText(event) {
  return plain(rawEventText(event));
}

// the names given to client addresses (Settings → Clients): "192.168.1.20 evcc" per line
let clientNames = new Map();
let ownClient = "";

export function setClientNames(text = "", own = "") {
  ownClient = own || "";
  clientNames = new Map(text.split("\n").map((l) => l.split("#")[0].trim()).filter(Boolean)
    .map((l) => { const i = l.indexOf(" "); return [l.slice(0, i), l.slice(i + 1).trim()]; }).filter(([h, n]) => h && n));
}

/** The host of a client "192.168.1.20:50114" or "[fe80::1]:50114". */
export function clientHost(address = "") {
  return address.startsWith("[") ? address.slice(1).split("]")[0] : (address.match(/:/g) || []).length === 1 ? address.split(":")[0] : address;
}

/** The name Home Assistant and the apps have without being named, else "". */
export function autoClientName(address = "") {
  const host = clientHost(address);
  if (host === ownClient || host === "::1" || host.startsWith("127.")) return "Home Assistant";
  return /^172\.30\.3[23]\./.test(host) || host.startsWith("fd0c:ac1e:2100:") ? "App" : "";
}

/** The name given to a client, "" when it has none of its own. */
export const ownClientName = (address = "") => clientNames.get(clientHost(address)) || "";

/** The name of a client "192.168.1.20:50114" or "[fe80::1]:50114", "" when it has none. */
export function clientName(address = "") {
  return ownClientName(address) || autoClientName(address);
}

function rawEventText(event) {
  const p = event.params || {};
  return [p.address, p.host, p.only, p.peer].reduce((text, who) => named(text, who), templatedText(event));
}

function templatedText(event) {
  const template = texts().events[event.kind];
  if (!template) return event.message;
  const params = { ...event.params };
  if (params.state) params.state = texts().states[params.state] || params.state;
  if (event.kind === "config_changed" && params.changes) params.summary = changesText(params.changes);
  if (params.error === "no answer") params.error = texts().system.no_answer;
  if (event.kind.startsWith("enocean_fall") && params.reason) params.reason = t(`fbReason_${params.reason}`);
  if (event.kind === "enocean_fallback_promoted") params.action = t(`fbAction_${params.action}`);
  if (event.kind === "clients_disconnected" || event.kind === "connection_restarted") params.by = t(`by_${params.by}`);
  if (event.kind === "connection_restarted" && params.usb) params.by = `${params.by}, ${t("byUsb")}`;
  if (event.kind === "auto_restart_failed") params.error = fieldError(params.error);
  if (event.kind === "exclusive_off") params.reason = t(`exReason_${params.reason}`);
  if (Array.isArray(params.errors)) params.errors = params.errors.map((n) => (n?.code ? noteText(n) : String(n))).join("; ");
  if (params.error?.code) params.error = noteText(params.error);
  return fill(template, params);
}

function named(text, address) {
  if (typeof address !== "string") return text; // a tool's write has a register number here
  const name = clientName(address);
  return name && address ? text.replace(address, `${address} (${name})`) : text;
}

export function noteText(note) {
  const template = texts().notes[note.code];
  if (!template) return note.code;
  const params = { ...note };
  if (params.errors && typeof params.errors === "object") {
    params.errors = Object.entries(params.errors).map(([k, v]) => (k ? `${k}: ${v}` : v)).join("; ");
  }
  return fill(template, params);
}
