// 1-Wire: an owserver shared through the app (onewire.py): the form's starting values and
// the cards of the detail page (state, devices on the bus, clients).
import { html } from "lit";
import { lang, t } from "./i18n.js";
import { fmtAgo, fmtTime, proxyTarget } from "./ui.js";

export const OWSERVER_PORT = 4304;
// a new connection: the owserver of another computer, writes from every client as owserver itself does
export const DEFAULTS = {
  kind: "onewire", template: "onewire", link: "owserver", device: "", host: "", host_port: OWSERVER_PORT, max_clients: 10, mode: "raw",
  keep_open: false, stuck_disconnect: false, silence_minutes: 0, silence_restart: "", power_switch: "",
  write_access: "all", write_clients: "",
};

const num = (n) => (n ?? 0).toLocaleString(lang);

/** The side card: is the owserver there, and what goes through. */
export function oneWireCard(c) {
  const o = c.onewire || {};
  const r = o.requests || {};
  const reach = o.reachable === true ? ["owReachable", "ok"] : o.reachable === false ? ["owUnreachable", "bad"] : ["owUnknown", ""];
  const total = Object.values(r).reduce((a, b) => a + b, 0);
  const counters = [["owDevices", (o.devices || []).length], ["owRequests", total], ["owErrors", o.errors], ["owBlocked", o.blocked], ["owRefused", o.refused]];
  return html`<section class="card" aria-labelledby="t-ow">
    <div class="row"><h2 id="t-ow">owserver <span class="chip info">${t("beta")}</span></h2><span class="chip ${reach[1]}"><span class="dot"></span>${t(reach[0])}</span></div>
    <div class="kv" style="display:grid;grid-template-columns:auto 1fr;gap:6px 12px">
      <span class="hint">${t("owSource")}</span><span class="mono" style="overflow-wrap:anywhere">${c.link === "usb" ? usbSource(o) : proxyTarget(c)}</span>
      ${o.owserver ? html`<span class="hint">${t("owOwn")}</span><span>${o.owserver.running ? t("owOwnRunning", { t: fmtAgo(o.owserver.started_at) }) : t("owOwnStopped")}${o.owserver.restarts ? ` · ${t("owOwnRestarts", { n: num(o.owserver.restarts) })}` : ""}${o.watchdog?.resets ? ` · ${t("owOwnResets", { n: num(o.watchdog.resets) })}` : ""}</span>` : ""}
      <span class="hint">${t("owAnswer")}</span><span>${o.answer_ms?.avg != null ? t("owAnswerVal", { a: num(o.answer_ms.avg), l: num(o.answer_ms.last) }) : "–"}</span>
      <span class="hint">${t("owListRead")}</span><span>${o.devices_at ? `${fmtAgo(o.devices_at)}${o.probe_ms != null ? ` · ${num(o.probe_ms)} ms` : ""}` : t("never")}</span>
      <span class="hint">${t("owKinds")}</span><span>${t("owKindsVal", { r: num(r.read), w: num(r.write), d: num(r.dir), o: num(r.other) })}</span>
    </div>
    <div class="counters">${counters.map(([k, v]) => html`<div class="well"><b style=${["owErrors", "owBlocked", "owRefused"].includes(k) && v ? "color:var(--warn)" : ""}>${num(v)}</b>
      <span class="hint">${t(k)}</span></div>`)}</div>
    ${o.listen_error ? html`<div class="note bad">${t("mbListenError", { e: o.listen_error })}</div>` : ""}
    ${o.owserver && !(o.adapters || []).length ? html`<div class="note bad">${t("owAdapterGone")}</div>` : ""}
    ${o.owserver?.start_error ? html`<div class="note bad">${t("owOwnStartError", { e: o.owserver.start_error })}</div>` : ""}
    ${o.owserver?.log?.length ? html`<details><summary class="hint" style="cursor:pointer">${t("owOwnLog")}</summary>
      <div class="code" style="white-space:pre-wrap;margin-top:6px">${o.owserver.log.join("\n")}</div></details>` : ""}
    ${o.last_error ? html`<div class="note ${o.reachable === false ? "bad" : "warn"}">${t("mbLastError")}: ${o.last_error}${o.last_error_at ? ` · ${fmtTime(o.last_error_at, true, true)}` : ""}</div>` : ""}
  </section>`;
}

const usbSource = (o) => {
  const a = (o.adapters || [])[0];
  return a ? `${a.product || "DS2490"} · USB ${a.place}` : "USB · –";
};

/** The devices the owserver lists, with the usual chip of their family. */
export function devicesCard(c) {
  const o = c.onewire || {};
  const devices = o.devices || [];
  return html`<section class="card" aria-labelledby="t-owdev">
    <div class="row"><h2 id="t-owdev">${t("owDevicesTitle")}</h2><span class="hint" style="font-size: calc(13px * var(--fs, 1))">${t("owDevicesSub")}</span></div>
    ${devices.length ? html`<div class="scroll"><table><thead><tr><th>${t("owId")}</th><th>${t("owFamily")}</th><th>${t("owChip")}</th></tr></thead>
      <tbody>${devices.map((d) => html`<tr><td class="mono">${d.id}</td><td class="mono">${d.family}</td><td>${d.type || "–"}${d.family === "81" ? html` <span class="hint">· ${t("owAdapterChip")}</span>` : ""}</td></tr>`)}</tbody></table></div>`
      : html`<p class="hint" style="font-size: calc(14px * var(--fs, 1))">${o.reachable === false ? t("owNoList") : o.devices_at ? t("owNoDevices") : t("owNotRead")}</p>`}
  </section>`;
}

/** The clients: one row per computer (owserver clients connect again for each request). */
export function clientsTable(c, label) {
  return html`<div class="scroll"><table><thead><tr>
    <th>${t("clientTh")}</th><th>${t("sinceTh")}</th><th style="text-align:right">${t("mbRequests")}</th><th style="text-align:right">${t("owErrors")}</th>
    <th style="text-align:right">${t("owBlocked")}</th><th>${t("owLast")}</th></tr></thead>
    <tbody>${c.clients.map((cl) => html`<tr><td class="mono" style="font-size: max(10.5px, calc(12px * var(--fs, 1)))">${cl.address}${label(cl.address)}</td>
      <td>${cl.since ? fmtTime(cl.since) : "–"}</td><td style="text-align:right">${num(cl.requests)}</td>
      <td style="text-align:right;${cl.errors ? "color:var(--warn)" : ""}">${num(cl.errors)}</td><td style="text-align:right">${num(cl.blocked)}</td>
      <td><span class="mono" style="font-size: max(10.5px, calc(12px * var(--fs, 1)));overflow-wrap:anywhere">${cl.last_path || "–"}</span>${cl.last_request ? html` <span class="hint">· ${fmtAgo(cl.last_request)}</span>` : ""}</td></tr>`)}</tbody></table></div>
    <p class="hint" style="margin:0">${t("owClientsHint")}</p>`;
}
