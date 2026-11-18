// 1-Wire: an owserver shared through the app (onewire.py): the form's starting values and
// the cards of the detail page (state, devices on the bus, clients).
import { LitElement, css, html } from "lit";
import { api } from "./api.js";
import { fieldError, lang, t } from "./i18n.js";
import { base, tokens } from "./styles.js";
import { confirmDialog, fmtAgo, fmtTime, proxyTarget } from "./ui.js";

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
  const counters = [["owDevices", o.present ?? (o.devices || []).length], ["owMissing", (o.missing || []).length], ["owRequests", total], ["owErrors", o.errors], ["owBlocked", o.blocked], ["owRefused", o.refused]];
  return html`<section class="card" aria-labelledby="t-ow">
    <div class="row"><h2 id="t-ow">owserver <span class="chip info">${t("beta")}</span></h2><span class="chip ${reach[1]}"><span class="dot"></span>${t(reach[0])}</span></div>
    <div class="kv" style="display:grid;grid-template-columns:auto 1fr;gap:6px 12px">
      <span class="hint">${t("owSource")}</span><span class="mono" style="overflow-wrap:anywhere">${c.link === "usb" ? usbSource(o) : proxyTarget(c)}</span>
      ${o.owserver ? html`<span class="hint">${t("owOwn")}</span><span>${o.owserver.running ? t("owOwnRunning", { t: fmtAgo(o.owserver.started_at) }) : t("owOwnStopped")}${o.owserver.restarts ? ` · ${t("owOwnRestarts", { n: num(o.owserver.restarts) })}` : ""}${o.watchdog?.resets ? ` · ${t("owOwnResets", { n: num(o.watchdog.resets) })}` : ""}</span>` : ""}
      ${o.info && (o.info.name || o.info.owserver) ? html`<span class="hint">${t("owAdapter")}</span><span>${adapterText(o.info)}</span>` : ""}
      <span class="hint">${t("owAnswer")}</span><span>${o.answer_ms?.avg != null ? t("owAnswerVal", { a: num(o.answer_ms.avg), l: num(o.answer_ms.last) }) : "–"}</span>
      <span class="hint">${t("owListRead")}</span><span>${o.devices_at ? `${fmtAgo(o.devices_at)}${o.probe_ms != null ? ` · ${num(o.probe_ms)} ms` : ""}` : t("never")}</span>
      <span class="hint">${t("owKinds")}</span><span>${t("owKindsVal", { r: num(r.read), w: num(r.write), d: num(r.dir), o: num(r.other) })}</span>
      ${o.statistics ? html`<span class="hint">${t("owBusErrors")}</span><span>${t("owBusErrorsVal", { c: num(o.statistics.crc_errors), t: num(o.statistics.crc_tries), p: o.statistics.crc_share.toLocaleString(lang), b: num(o.statistics.bus_errors) })}${rising(o.statistics) ? html` <span class="chip warn">${t("owRising", { t: fmtAgo(o.statistics.rising_at) })}</span>` : ""}</span>` : ""}
    </div>
    <div class="counters">${counters.map(([k, v]) => html`<div class="well"><b style=${["owErrors", "owBlocked", "owRefused", "owMissing"].includes(k) && v ? "color:var(--warn)" : ""}>${num(v)}</b>
      <span class="hint">${t(k)}</span></div>`)}</div>
    ${o.listen_error ? html`<div class="note bad">${t("mbListenError", { e: o.listen_error })}</div>` : ""}
    ${o.owserver && !(o.adapters || []).length ? html`<div class="note bad">${t("owAdapterGone")}</div>` : ""}
    ${o.owserver?.start_error ? html`<div class="note bad">${t("owOwnStartError", { e: o.owserver.start_error })}</div>` : ""}
    ${o.owserver?.log?.length ? html`<details><summary class="hint" style="cursor:pointer">${t("owOwnLog")}</summary>
      <div class="code" style="white-space:pre-wrap;margin-top:6px">${o.owserver.log.join("\n")}</div></details>` : ""}
    ${o.last_error ? html`<div class="note ${o.reachable === false ? "bad" : "warn"}">${t("mbLastError")}: ${o.last_error}${o.last_error_at ? ` · ${fmtTime(o.last_error_at, true, true)}` : ""}</div>` : ""}
  </section>`;
}

/** "DS9490 · version 3 · owserver 3.2p4" from what the owserver says about itself. */
const adapterText = (info) => [info.name, info.version ? t("owAdapterVersion", { v: info.version }) : "", info.owserver ? `owserver ${info.owserver}` : ""].filter(Boolean).join(" · ");

const usbSource = (o) => {
  const a = (o.adapters || [])[0];
  return a ? `${a.product || "DS2490"} · USB ${a.place}` : "USB · –";
};

const RISING = 3600; // s: counters that went up within this time get a chip
const rising = (st) => st.rising_at && Date.now() / 1000 - st.rising_at < RISING;
const TEMPERATURE = /^(temperature(9|10|11|12)?|fasttemp)$/;

/** "28.A1B2C3D4E5F6 Living room" per line (the setting onewire_names) → {ID: name}. */
export function names(text) {
  const out = {};
  for (const line of (text || "").split("\n")) {
    const [id, ...rest] = line.trim().split(/\s+/);
    if (id && rest.length) out[id.toUpperCase()] = rest.join(" ");
  }
  return out;
}

/** The value to show: a temperature first, else the first property read. */
function shown(d) {
  const entries = Object.entries(d.values || {});
  const [prop, v] = entries.find(([p]) => TEMPERATURE.test(p)) || entries[0] || [];
  if (!v) return html`<span class="hint">${t("owNoValue")}</span>`;
  const number = Number(v.value);
  const text = TEMPERATURE.test(prop) && !Number.isNaN(number) ? `${number.toLocaleString(lang, { maximumFractionDigits: 2 })} °C` : `${prop} = ${v.value}`;
  return html`${text} <span class="hint">· ${fmtAgo(v.at)}</span>`;
}

/** The devices on the bus: also the known ones that are missing now, with names of your own. */
export class OneWireDevices extends LitElement {
  static properties = { connection: { attribute: false }, settings: { attribute: false }, edit: { state: true }, error: { state: true } };

  static styles = [tokens, base, css`
    :host { display: block; }
    td, th { font-size: calc(13px * var(--fs, 1)); vertical-align: top; }
    .id { font-family: "Roboto Mono", ui-monospace, Menlo, monospace; white-space: nowrap; }
    .chips { display: flex; flex-wrap: wrap; gap: 4px; }
  `];

  _refresh() { this.dispatchEvent(new CustomEvent("dp-refresh", { bubbles: true, composed: true })); }

  async _save() {
    try {
      await api("api/onewire/names", { method: "PUT", body: { names: this.edit } });
      this.edit = undefined;
      this.error = "";
      this._refresh();
    } catch (err) { this.error = fieldError((err.data.errors || {}).onewire_names || err.message); }
  }

  async _forget(d, label) {
    if (!(await confirmDialog(this, t("owForgetAsk", { d: label }), t("owForget")))) return;
    try {
      await api(`api/tools/${this.connection.id}/onewire/forget`, { method: "POST", body: { device: d.id } });
      this._refresh();
    } catch (err) { this.error = err.message; }
  }

  _chips(d) {
    const out = [];
    if (d.transient) out.push(html`<span class="chip ${d.present ? "ok" : ""}" title=${t("owIButtonHint")}>${d.present ? t("owIButtonOn") : t("owIButtonOff", { t: fmtAgo(d.last) })}</span>`);
    else if (d.missing_since) out.push(html`<span class="chip bad">${t("owMissingSince", { t: fmtAgo(d.missing_since) })}</span>`);
    if (d.new && !d.missing_since) out.push(html`<span class="chip info">${t("owNew")}</span>`);
    if (d.bad) out.push(html`<span class="chip warn" title=${t(d.power === "parasite" ? "owBadParasite" : "owBadHint")}>${t("owBad", { n: num(d.bad), t: fmtAgo(d.bad_at) })}</span>`);
    if (d.power === "parasite") out.push(html`<span class="chip ${d.bad ? "warn" : ""}" title=${t("owParasiteHint")}>${t("owParasite")}</span>`);
    if (d.frozen) out.push(html`<span class="chip warn" title=${t("owFrozenHint")}>${t("owFrozen")}</span>`);
    if (d.errors) out.push(html`<span class="chip warn" title=${d.last_error || ""}>${t("owDeviceErrors", { n: num(d.errors) })}</span>`);
    return out;
  }

  render() {
    const o = this.connection.onewire || {};
    const devices = o.devices || [];
    const named = names(this.settings?.onewire_names);
    return html`<section class="card" aria-labelledby="t-owdev">
      <div class="row"><h2 id="t-owdev">${t("owDevicesTitle")}</h2><span class="hint" style="font-size: calc(13px * var(--fs, 1))">${t("owDevicesSub")}</span></div>
      ${devices.length ? html`<div style="display:flex;flex-wrap:wrap;gap:8px">
        ${this.edit ? html`<button class="btn btn-s" @click=${() => this._save()}>${t("eoSendersSave")}</button>
          <button class="btn btn-g" @click=${() => { this.edit = undefined; this.error = ""; }}>${t("cancel")}</button>`
        : html`<button class="btn btn-g" @click=${() => { this.edit = {}; }}>${t("owNamesEdit")}</button>`}</div>
        ${this.error ? html`<div class="note bad" role="alert">${this.error}</div>` : ""}
        <div class="scroll"><table><thead><tr><th>${t("owName")}</th><th>${t("owId")}</th><th>${t("owChip")}</th><th>${t("owValue")}</th><th>${t("owState")}</th><th></th></tr></thead>
        <tbody>${devices.map((d) => {
          const label = named[d.id] ? `${named[d.id]} (${d.id})` : d.id;
          return html`<tr>
            <td>${this.edit ? html`<input class="inp" style="min-width:140px" maxlength="64" aria-label="${t("owName")} ${d.id}" .value=${this.edit[d.id] ?? named[d.id] ?? ""}
              @input=${(e) => { this.edit = { ...this.edit, [d.id]: e.target.value }; }}>` : named[d.id] || html`<span class="hint">–</span>`}</td>
            <td><span class="id">${d.id}</span></td>
            <td>${d.type || d.family}${d.family === "81" ? html`<br><span class="hint">${t("owAdapterChip")}</span>` : ""}</td>
            <td>${d.missing_since || (d.transient && !d.present) ? html`<span class="hint">${t("owLastSeen", { t: fmtAgo(d.last) })}</span>` : shown(d)}</td>
            <td><div class="chips">${this._chips(d)}</div></td>
            <td>${d.missing_since || (d.transient && !d.present) ? html`<button class="btn btn-g" style="min-height:28px" @click=${() => this._forget(d, label)}>${t("owForget")}</button>` : ""}</td></tr>`;
        })}</tbody></table></div>
        <p class="hint" style="margin:0">${t("owValuesHint")}</p>`
        : html`<p class="hint" style="font-size: calc(14px * var(--fs, 1))">${o.reachable === false ? t("owNoList") : o.devices_at ? t("owNoDevices") : t("owNotRead")}</p>`}
    </section>`;
  }
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
