// Small helpers shared by the pages: formats, icons, the switch, copying, confirming.
import { html, nothing, svg } from "lit";
import { lang, t } from "./i18n.js";

export const logo = (size = 36) => html`<svg width=${size} height=${size} viewBox="0 0 128 128" aria-hidden="true" style="flex:none">
  <rect width="128" height="128" rx="28" fill="#0A6AA8"></rect>
  <g fill="none" stroke="#FFFFFF" stroke-width="10" stroke-linecap="round" stroke-linejoin="round">
    <path d="M16 46H70L64 82H22Z"></path><path d="M67 64H84M84 64L104 40M84 64H108M84 64L104 88"></path></g>
  <g fill="#FFFFFF"><circle cx="104" cy="40" r="11"></circle><circle cx="108" cy="64" r="11"></circle><circle cx="104" cy="88" r="11"></circle></g></svg>`;

const ICONS = {
  plus: "M12 5v14M5 12h14",
  chevron: "M6 9l6 6 6-6",
  check: "M5 12l5 5L20 7",
  upload: "M12 15V3M7 8l5-5 5 5M5 21h14",
  x: "M6 6l12 12M18 6L6 18",
  pencil: "M4 20h4L19 9l-4-4L4 16v4zM13.5 6.5l4 4",
  download: "M12 3v12M7 10l5 5 5-5M5 21h14",
  copy: "M9 9h12v12H9zM5 15V5a2 2 0 0 1 2-2h10",
  warn: "M12 9v4M12 17h.01M10.3 3.9 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z",
  info: "M12 16v-4M12 8h.01M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20z",
  file: "M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8zM14 3v5h5",
  serial: "M3 8h14l-2 8H5zM7 12h.01M10 12h.01M13 12h.01M17 12h4",
  modbus: "M4 4h16v6H4zM4 14h16v6H4zM8 7h.01M8 17h.01M12 10v4",
  enocean: "M12 13v8M9 21h6M8.5 9.5a5 5 0 0 1 7 0M5.6 6.6a9 9 0 0 1 12.8 0M12 13h.01",
};

export const icon = (name, size = 18) => html`<svg width=${size} height=${size} viewBox="0 0 24 24" fill="none" stroke="currentColor"
  stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${svg`<path d=${ICONS[name]}></path>`}</svg>`;

export function fmtBytes(n) {
  if (n === null || n === undefined) return "–";
  const units = ["B", "kB", "MB", "GB"];
  let value = n, unit = 0;
  while (value >= 1000 && unit < units.length - 1) { value /= 1000; unit++; }
  return `${value.toLocaleString(lang, { maximumFractionDigits: unit ? 1 : 0 })} ${units[unit]}`;
}

const RATE_KEPT = 30; // about a minute of state polls
const rates = new Map();

/** Remember the data rate of every connection from each state poll, so a card has a curve when the page opens. */
export function recordRates(connections) {
  const ids = new Set(connections.map((c) => c.id));
  for (const id of rates.keys()) if (!ids.has(id)) rates.delete(id);
  for (const c of connections) rates.set(c.id, [...(rates.get(c.id) || []), c.rate_from_device || 0].slice(-RATE_KEPT));
}

export const rateHistory = (id) => rates.get(id) || [];

/** A small area curve of the values, scaled to their peak. */
export function sparkline(values, { w = 84, h = 26, label = "" } = {}) {
  const v = values.length > 1 ? values : [0, 0];
  const max = Math.max(...v, 1), step = w / (v.length - 1);
  const points = v.map((x, i) => `${(i * step).toFixed(1)},${(h - 2 - (x / max) * (h - 5)).toFixed(1)}`).join(" L");
  return html`<svg viewBox="0 0 ${w} ${h}" width=${w} height=${h} role="img" aria-label=${label} style="flex:none">
    ${svg`<path d="M0,${h} L${points} L${w},${h} Z" fill="var(--accent-soft)"></path>
    <path d="M${points}" fill="none" stroke="var(--accent)" stroke-width="1.5" stroke-linejoin="round"></path>`}</svg>`;
}

export const fmtRate = (bytesPerSecond) => `${fmtBytes(Math.round(bytesPerSecond || 0))}/s`;

export function fmtTime(ts, withDate = true, seconds = false) {
  if (!ts) return t("never");
  const d = new Date(ts * 1000);
  const today = new Date();
  const time = d.toLocaleTimeString(lang, { hour: "2-digit", minute: "2-digit", ...(seconds ? { second: "2-digit" } : {}) });
  if (!withDate || d.toDateString() === today.toDateString()) return time;
  const yesterday = new Date(today.getTime() - 86400000);
  if (d.toDateString() === yesterday.toDateString()) return `${t("yesterday")} ${time}`;
  return `${d.toLocaleDateString(lang, { day: "2-digit", month: "2-digit" })} ${time}`;
}

export function fmtAgo(ts) {
  if (!ts) return t("never");
  const seconds = Math.max(0, Date.now() / 1000 - ts);
  const rtf = new Intl.RelativeTimeFormat(lang, { numeric: "auto" });
  if (seconds < 60) return rtf.format(-Math.round(seconds), "second");
  if (seconds < 3600) return rtf.format(-Math.round(seconds / 60), "minute");
  if (seconds < 86400) return rtf.format(-Math.round(seconds / 3600), "hour");
  return rtf.format(-Math.round(seconds / 86400), "day");
}

/** Where a proxy's device is: the serial device or host:port. */
/** Items joined sixteen to a line, so hex and ASCII break at the same bytes. */
export const lines16 = (items, sep) => Array.from({ length: Math.ceil(items.length / 16) }, (_, i) => items.slice(i * 16, i * 16 + 16).join(sep)).join("\n");

/** The badge word of a live line: the direction as seen from the device, or the Modbus request/answer. */
export const dirLabel = (direction, kind) => (direction === "rx" || direction === "tx" ? t(`${kind === "modbus" ? "dirmb" : "dir"}_${direction}`) : direction.toUpperCase());

export const usesDevice = (c) => c.kind === "serial" || c.link === "rtu" || c.link === "serial";
export const proxyTarget = (c) => usesDevice(c) ? c.device : `${c.host.includes(":") ? `[${c.host}]` : c.host}:${c.host_port}`;
export const modbusTarget = proxyTarget;

export const fmtSerial = (c) => `${c.baud} ${c.data_bits}${c.parity.toUpperCase()}${c.stop_bits}`;

export const toggle = (checked, label, onChange, disabled = false) => html`<button type="button" class="switch" role="switch"
  aria-checked=${checked ? "true" : "false"} aria-label=${label} ?disabled=${disabled} @click=${() => onChange(!checked)}><span></span></button>`;

export async function copyText(text) {
  try {
    await navigator.clipboard.writeText(text);
    return true;
  } catch {
    const area = document.createElement("textarea");
    area.value = text;
    area.style.position = "fixed";
    area.style.opacity = "0";
    document.body.appendChild(area);
    area.select();
    const done = document.execCommand("copy");
    area.remove();
    return done;
  }
}

/** The state of a connection as one word plus a chip class. */
export function connectionState(c, ser2netRunning) {
  if (!c.enabled) return ["stDisabled", ""];
  if (c.present === false) return ["stMissing", "bad"];
  if (c.kind !== "serial") {
    const m = c[c.kind] || {};
    if (m.listen_error) return ["stPortBusy", "bad"];
    if (m.serves) return !m.connected ? ["stConnecting", "warn"] : ["stFbStandby", "info"];
    if (m.fallback?.active === "fallback") return ["stOnFallback", "warn"];
    if (!m.listening) return ["stStarting", "warn"];
    if (m.reachable === false) return ["stUnreachable", "bad"];
    if (m.exclusive_peer) return ["stReserved", "info"];
    if (c.kind === "enocean" && !m.connected) return ["stConnecting", "warn"];
    return ["stRunning", "ok"];
  }
  if (!ser2netRunning) return ["stWaiting", "warn"];
  if (c.pending === "reconfigured") return ["stPending", "info"];
  return ["stRunning", "ok"];
}

/** A card folded by default that remembers in the browser whether it was opened; `sectionId` is the anchor to jump to. */
export function foldCard(key, id, title, sub, body, force = false, sectionId = "") {
  let pref = null;
  try { pref = localStorage.getItem(key); } catch { /* private window */ }
  return html`<section class="card" id=${sectionId || nothing} aria-labelledby=${id}>
    <style>
      .tc > summary { cursor: pointer; display: flex; align-items: center; gap: 8px; list-style: none; border-radius: 10px; margin: -6px -8px; padding: 6px 8px; }
      .tc > summary::-webkit-details-marker { display: none; }
      .tc > summary:hover { background: var(--surface-2); }
      .tc .chev { margin-left: auto; flex: none; display: inline-flex; align-items: center; gap: 4px; color: var(--accent-hover); font-size: 13px; font-weight: 500; }
      .tc .chev svg { transition: transform .15s; }
      .tc[open] .chev svg { transform: rotate(180deg); }
      .tc .chev .on { display: none; } .tc[open] .chev .on { display: inline; } .tc[open] .chev .off { display: none; }
    </style>
    <details class="tc" ?open=${pref === "1" || force} @toggle=${(e) => { try { localStorage.setItem(key, e.target.open ? "1" : "0"); } catch { /* private window */ } }}>
      <summary><h2 id=${id} style="display:inline">${title}</h2><span class="hint">· ${sub}</span>
        <span class="chev"><span class="off">${t("toolsShow")}</span><span class="on">${t("toolsHide")}</span>${icon("chevron", 18)}</span></summary>
      <div style="display:flex;flex-direction:column;gap:12px;margin-top:16px">${body}</div>
    </details>
  </section>`;
}

/** The Tools card. */
export const toolsCard = (key, id, sub, body, force = false) => foldCard(key, id, t("tools"), sub, body, force);

export const navigate = (hash) => { location.hash = hash; };

/** The focused element, also inside shadow roots. */
export function focused() {
  let el = document.activeElement;
  while (el?.shadowRoot?.activeElement) el = el.shadowRoot.activeElement;
  return el;
}

/** Keeps Tab inside a dialog's box. */
export function trapTab(e, box) {
  if (e.key !== "Tab" || !box) return;
  const items = [...box.querySelectorAll('button, a[href], input, select, textarea, [tabindex]:not([tabindex="-1"])')].filter((el) => !el.disabled);
  if (!items.length) return;
  const first = items[0], last = items[items.length - 1], now = focused();
  if (e.shiftKey && (now === first || !box.contains(now))) { e.preventDefault(); last.focus(); }
  else if (!e.shiftKey && (now === last || !box.contains(now))) { e.preventDefault(); first.focus(); }
}

/** A confirm dialog in the page (window.confirm is blocked in some frames). */
export function confirmDialog(host, message, confirmLabel) {
  return new Promise((resolve) => {
    const dialog = document.createElement("dp-confirm");
    dialog.message = message;
    dialog.confirmLabel = confirmLabel || t("confirm");
    dialog.addEventListener("done", (e) => { dialog.remove(); resolve(e.detail); });
    (host.shadowRoot || document.body).appendChild(dialog);
  });
}
