// EnOcean gateways: the frame check, the issues in plain words, the status card and the tools
// (send one frame, test the gateway, capture with the lock for PCT14).
import { LitElement, css, html } from "lit";
import { api } from "./api.js";
import { lang, t } from "./i18n.js";
import { base, tokens } from "./styles.js";
import { confirmDialog, fmtAgo, fmtTime, icon, toolsCard } from "./ui.js";

export const TEMPLATES = {
  fam_usb: { esp_protocol: "esp2", link: "serial", baud: 9600 },
  fam14: { esp_protocol: "esp2", link: "serial", baud: 57600 },
  fgw14_usb: { esp_protocol: "esp2", link: "serial", baud: 57600 },
  usb300: { esp_protocol: "esp3", link: "serial", baud: 57600 },
  mgw_eth: { esp_protocol: "esp3", link: "tcp", host_port: 5100 },
  symcon_lan: { esp_protocol: "esp3", link: "tcp", host_port: 5000 },
  enocean: {},
};
// new gateways: only Home Assistant (127.0.0.1) and the other apps; the app is in the host network
export const HA_ONLY = "127.0.0.1, 172.30.32.0/23";
export const DEFAULTS = {
  kind: "enocean", template: "fam_usb", ...TEMPLATES.fam_usb, data_bits: 8, parity: "n", stop_bits: 1, mode: "raw",
  max_clients: 4, remaddr: HA_ONLY, keep_open: false, stuck_disconnect: false, silence_minutes: 0,
  send_gap_ms: 10, replay_size: 1000, replay_max_age_s: 900, replay_persist: false,
};

const hx = (n) => n.toString(16).toUpperCase().padStart(2, "0");

export function crc8(bytes) {
  let crc = 0;
  for (const b of bytes) {
    crc ^= b;
    for (let i = 0; i < 8; i++) crc = crc & 0x80 ? ((crc << 1) ^ 0x07) & 0xff : (crc << 1) & 0xff;
  }
  return crc;
}

/** Hex digit pairs (spaces, ":" and "-" allowed) → bytes, or null. */
export function parseHex(text) {
  const clean = text.replace(/[\s:-]/g, "");
  if (clean.length % 2 || /[^0-9a-f]/i.test(clean)) return null;
  return clean.match(/../g)?.map((p) => parseInt(p, 16)) || [];
}

export const toHex = (bytes) => bytes.map(hx).join(" ");

/** What is wrong with a frame, with a fixed one where the checksum is only missing or wrong. */
export function checkFrame(bytes, protocol) {
  if (bytes === null) return { level: "bad", msg: t("eoBadHex") };
  if (!bytes.length) return { level: "empty", msg: t("eoEmpty") };
  if (protocol === "esp2") {
    if (bytes[0] !== 0xa5 || bytes[1] !== 0x5a) return { level: "bad", msg: t("eoSync2") };
    const sum = bytes.slice(2, 13).reduce((a, b) => a + b, 0) & 0xff;
    if (bytes.length === 13) return { level: "bad", msg: t("eoLen2", { n: 13 }), fix: [...bytes, sum], fixLabel: t("eoAdd") };
    if (bytes.length !== 14) return { level: "bad", msg: t("eoLen2", { n: bytes.length }) };
    if (bytes[13] !== sum) return { level: "bad", msg: t("eoSum", { want: hx(sum) }), fix: [...bytes.slice(0, 13), sum], fixLabel: t("eoFix") };
    return { level: "ok", msg: t("eoOk", { p: "ESP2" }) };
  }
  if (bytes[0] !== 0x55) return { level: "bad", msg: t("eoSync3") };
  if (bytes.length < 7) return { level: "bad", msg: t("eoShort3") };
  const hcrc = crc8(bytes.slice(1, 5));
  if (bytes[5] !== hcrc) { const fix = [...bytes]; fix[5] = hcrc; return { level: "bad", msg: t("eoHcrc", { want: hx(hcrc) }), fix, fixLabel: t("eoFix") }; }
  const want = 7 + ((bytes[1] << 8) | bytes[2]) + bytes[3];
  const dcrc = crc8(bytes.slice(6, want - 1));
  if (bytes.length === want - 1) return { level: "bad", msg: t("eoLen3", { want, n: bytes.length }), fix: [...bytes, dcrc], fixLabel: t("eoAdd") };
  if (bytes.length !== want) return { level: "bad", msg: t("eoLen3", { want, n: bytes.length }) };
  if (bytes[want - 1] !== dcrc) return { level: "bad", msg: t("eoDcrc", { want: hx(dcrc) }), fix: [...bytes.slice(0, -1), dcrc], fixLabel: t("eoFix") };
  return { level: "ok", msg: t("eoOk", { p: "ESP3" }) };
}

/** What is wrong with a gateway, worst first: [{level, title, text}]. */
export function issues(c, capture) {
  const e = c.enocean;
  if (!c.enabled || !e) return [];
  const f = e.frames, out = [];
  const add = (level, key, values = {}) => out.push({ level, title: t(`eoI_${key}`, values), text: t(`eoIt_${key}`, values) });
  if (e.listen_error) add("bad", "port", { port: c.port, e: e.listen_error });
  if (c.present === false) add("bad", "missing", { d: c.device });
  else if (!e.connected) e.reachable === false ? add("bad", "down", { e: e.last_error || "?" }) : add("warn", "connecting");
  const duty = e.duty_cycle.of_limit;
  if (duty >= 50) add(duty >= 80 ? "bad" : "warn", "duty", { p: Math.round(duty) });
  if (e.exclusive_peer) add("warn", "locked", { peer: e.exclusive_peer });
  if (e.queue > 10) add("warn", "queue", { n: e.queue });
  if (f.dropped) add("warn", "dropped", { n: f.dropped });
  if (f.slow_clients) add("warn", "slow", { n: f.slow_clients });
  if (f.refused) add("warn", "refused", { n: f.refused });
  if (f.locked) add("info", "held", { n: f.locked });
  if (!c.clients.length && e.listening) { add("info", "noClients", { port: c.port }); out[out.length - 1].jump = "addresses"; }
  if (capture && capture.connection === c.id) add("info", "capture", { f: capture.file });
  return out;
}

const num = (n) => (n ?? 0).toLocaleString(lang);

/** The side card: reachable, protocol, base ID, counters. */
export function statusCard(c) {
  const e = c.enocean || {};
  const f = e.frames || {};
  const reach = e.connected ? ["eoConnected", "ok"] : e.reachable === false ? ["eoDisconnected", "bad"] : ["eoConnecting", "warn"];
  const counters = [["eoFromGw", f.from_gateway], ["eoToGw", f.to_gateway], ["eoReplayed", f.replayed], ["eoDropped", f.dropped], ["eoHeld", f.locked], ["eoRefused", f.refused]];
  return html`<section class="card" aria-labelledby="t-eo">
    <div class="row"><h2 id="t-eo">${t("eoGateway")}</h2><span class="chip ${reach[1]}"><span class="dot"></span>${t(reach[0])}</span></div>
    <div class="kv" style="display:grid;grid-template-columns:auto 1fr;gap:6px 12px">
      <span class="hint">${t("eoProtocol")}</span><span>${(e.protocol || c.esp_protocol || "").toUpperCase()}</span>
      <span class="hint">${t("eoBaseId")}</span><span class="mono">${e.base_id || t("eoBaseUnknown")}</span>
      ${e.connected_since ? html`<span class="hint">${t("eoSince")}</span><span>${fmtAgo(e.connected_since)}</span>` : ""}
    </div>
    <div class="counters">${counters.map(([k, v]) => html`<div class="well"><b style=${["eoDropped", "eoRefused"].includes(k) && v ? "color:var(--warn)" : ""}>${num(v)}</b>
      <span class="hint">${t(k)}</span></div>`)}</div>
    ${e.last_error && !e.connected ? html`<div class="note bad">${e.last_error}${e.last_error_at ? ` · ${fmtTime(e.last_error_at, true, true)}` : ""}</div>` : ""}
  </section>`;
}

/** The two meters at the top of a gateway's page: air time against the 1 % limit, and the replay buffer. */
export function meterCards(c) {
  const e = c.enocean || {};
  const duty = e.duty_cycle || { of_limit: 0, telegrams: 0, ms: 0 }, r = e.replay || {}, f = e.frames || {};
  const air = duty.of_limit;
  const airLevel = air >= 80 ? "bad" : air >= 50 ? "warn" : "ok";
  const airChip = [["ok", "check", "eoAirOk"], ["warn", "info", "eoAirMid"], ["bad", "warn", "eoAirHigh"]][air >= 80 ? 2 : air >= 50 ? 1 : 0];
  const kept = r.kept ?? 0, size = r.size ?? c.replay_size ?? 0;
  const fill = size ? Math.min(100, (kept / size) * 100) : 0;
  const full = size > 0 && kept >= size;
  const live = (c.clients || []).some((cl) => cl.replay);
  const rbChip = !size ? ["", "info", "eoRbOff"] : full ? ["warn", "warn", "eoRbFullWarn"] : live ? ["ok", "check", "eoRbLive"] : ["info", "info", "eoRbCollect"];
  const age = r.oldest_s == null ? t("eoRbNone") : r.oldest_s < 90 ? `${Math.round(r.oldest_s)} s` : `${Math.round(r.oldest_s / 60)} min`;
  const seconds = (duty.ms || 0) / 1000;
  return html`<div class="meters">
    <section class="card meter ${airLevel}" aria-labelledby="t-air">
      <div><h2 id="t-air">${t("eoAirTitle")}</h2><p class="hint">${t("eoAirSub")}</p></div>
      <div class="big">${air.toLocaleString(lang, { maximumFractionDigits: 1 })} %<small>${t("eoAirOf")}</small></div>
      <div><div class="track" role="meter" aria-valuemin="0" aria-valuemax="100" aria-valuenow=${air} aria-label=${t("eoAirTitle")}>
        <div class="fill" style="width:${Math.min(100, air)}%"></div><span class="tick" style="left:80%"></span></div>
        <div class="scale"><span>0</span><span style="margin-left:auto;margin-right:12%">${t("eoAirMark")}</span><span>100 %</span></div></div>
      <div class="stats"><div class="well"><b>${num(duty.telegrams)}</b><span class="hint">${t("eoAirSent")}</span></div>
        <div class="well"><b>${seconds.toLocaleString(lang, { maximumFractionDigits: seconds < 10 ? 2 : 1 })} s</b><span class="hint">${t("eoAirOnAir")}</span></div></div>
      <span class="chip ${airChip[0]}">${icon(airChip[1], 14)}${t(airChip[2])}</span>
    </section>
    <section class="card meter ${full ? "warn" : "info"}" aria-labelledby="t-rb">
      <div><h2 id="t-rb">${t("eoRbTitle")}</h2><p class="hint">${t("eoRbSub")}</p></div>
      <div class="big">${num(kept)}<small>${t("eoRbOf", { s: num(size) })}</small></div>
      <div><div class="track" role="meter" aria-valuemin="0" aria-valuemax=${size} aria-valuenow=${kept} aria-label=${t("eoRbTitle")}>
        <div class="fill" style="width:${fill}%"></div></div>
        <div class="scale"><span>${t("eoRbEmpty")}</span><span>${t("eoRbFull")}</span></div></div>
      <div class="stats"><div class="well"><b>${age}</b><span class="hint">${t("eoRbOldest", { m: Math.round((r.max_age_s || 0) / 60) })}</span></div>
        <div class="well"><b>${num(f.replayed)}</b><span class="hint">${t("eoRbReplayed")}</span></div></div>
      <span class="chip ${rbChip[0]}">${icon(rbChip[1], 14)}${t(rbChip[2])}</span>
      <p class="hint">${c.replay_persist ? t("eoRbDisk") : t("eoRbMem")}</p>
    </section>
  </div>`;
}

export function issuesCard(list) {
  if (!list.length) return html`<div class="note ok" role="status">${t("eoAllWell")}</div>`;
  return html`<div style="display:flex;flex-direction:column;gap:8px">${list.map((i) => html`<div class="note ${i.level}" role="status"><b style="font-weight:500">${i.title}</b><div>${i.text}${i.jump ? html` <a href="#" @click=${(ev) => { ev.preventDefault(); ev.currentTarget.getRootNode().getElementById(i.jump)?.scrollIntoView({ behavior: "smooth", block: "center" }); }}>${t("showAddresses")}</a>` : ""}</div></div>`)}</div>`;
}

/** The tools card of one gateway; its own element, so typing does not wait for the state poll. */
export class EnOceanTools extends LitElement {
  static properties = {
    connection: { attribute: false }, capture: { attribute: false },
    text: { state: true }, answers: { state: true }, test: { state: true }, busy: { state: true }, peer: { state: true },
  };

  static styles = [tokens, base, css`
    :host { display: block; }
    .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 10px; }
    textarea { min-height: 64px; }
  `];

  constructor() {
    super();
    this.text = "";
    this.answers = [];
    this.peer = "";
  }

  /** Take a frame from the live view into "send". */
  take(hex) {
    this.text = hex;
    this.renderRoot.querySelector("textarea")?.focus();
  }

  _toast(text) { this.dispatchEvent(new CustomEvent("dp-toast", { detail: text, bubbles: true, composed: true })); }

  _refresh() { this.dispatchEvent(new CustomEvent("dp-refresh", { bubbles: true, composed: true })); }

  async _send() {
    const c = this.connection;
    const bytes = parseHex(this.text);
    if (checkFrame(bytes, c.esp_protocol).level !== "ok") return;
    if (!(await confirmDialog(this, t("eoSendConfirm", { f: toHex(bytes), n: c.name }), t("eoSend")))) return;
    this.busy = "send";
    try {
      const result = await api(`api/tools/${c.id}/enocean/send`, { method: "POST", body: { hex: toHex(bytes) } });
      this.answers = [{ ts: Date.now() / 1000, ...result }, ...this.answers].slice(0, 5);
    } catch (err) { this._toast(`${t("error")}: ${err.message}`); } finally { this.busy = ""; }
  }

  async _test() {
    this.busy = "test";
    try {
      this.test = await api(`api/tools/${this.connection.id}/enocean/test`, { method: "POST", body: { count: 10 } });
    } catch (err) { this._toast(`${t("error")}: ${err.message}`); } finally { this.busy = ""; }
  }

  async _capture(start) {
    try {
      if (start) await api(`api/tools/${this.connection.id}/enocean/capture`, { method: "POST", body: { exclusive_peer: this.peer || null } });
      else await api("api/capture/stop", { method: "POST", body: {} });
      this._refresh();
    } catch (err) { this._toast(`${t("error")}: ${err.message}`); }
  }

  render() {
    const c = this.connection, e = c.enocean || {};
    const cap = this.capture, mine = cap && cap.connection === c.id;
    const blocked = !c.enabled ? t("eoOff") : !e.connected ? t("eoNotConnected") : e.exclusive_peer ? t("eoReserved", { peer: e.exclusive_peer }) : "";
    const bytes = parseHex(this.text);
    const check = checkFrame(bytes, c.esp_protocol);
    const hosts = [...new Set(c.clients.map((cl) => cl.address.replace(/^\[?(.*?)\]?:\d+$/, "$1")))];
    return toolsCard("device_proxy.tools.enocean", "t-eotools", t("eoToolsSub"), html`
      ${blocked ? html`<div class="note warn">${blocked}</div>` : ""}
      <div class="row"><div><b style="font-weight:500">${t("eoTest")}</b><p class="hint">${t("eoTestSub")}</p></div>
        <button class="btn btn-s" ?disabled=${!!blocked || this.busy === "test"} @click=${this._test}>${this.busy === "test" ? t("eoTesting") : t("eoTestBtn")}</button></div>
      ${this.test ? html`<div class="note ${this.test.lost ? "warn" : "ok"}">${t("eoTestResult", { a: this.test.answered, s: this.test.sent, avg: this.test.avg_ms ?? "–", max: this.test.max_ms ?? "–" })}</div>` : ""}

      <div style="border-top:1px solid var(--line-2);padding-top:12px"><b style="font-weight:500">${t("eoSendTitle")}</b><p class="hint">${t("eoSendSub", { p: c.esp_protocol.toUpperCase() })}</p></div>
      <textarea class="inp mono" spellcheck="false" aria-label=${t("eoSendTitle")} .value=${this.text} placeholder=${c.esp_protocol === "esp2" ? "A5 5A AB 58 00 00 00 00 00 00 00 00 00 03" : "55 00 01 00 05 70 08 38"}
        @input=${(ev) => { this.text = ev.target.value; }}></textarea>
      ${check.level !== "empty" ? html`<div class="row"><span class="hint" style="color:${check.level === "ok" ? "var(--ok)" : "var(--bad)"}">${check.msg}</span>
        ${check.fix ? html`<button class="btn btn-g" @click=${() => { this.text = toHex(check.fix); }}>${check.fixLabel}</button>` : ""}</div>` : ""}
      <div><button class="btn btn-s" ?disabled=${!!blocked || check.level !== "ok" || this.busy === "send"} @click=${this._send}>${t("eoSend")}</button></div>
      ${this.answers.map((a) => html`<div class="well"><div class="hint">${fmtTime(a.ts, false, true)} · ${t("eoSent")}</div><div class="mono" style="font-size:12px;overflow-wrap:anywhere">${a.sent}</div>
        <div class="hint">${a.answer ? t("eoAnswer") : t("eoNoAnswer")}</div>${a.answer ? html`<div class="mono" style="font-size:12px;overflow-wrap:anywhere">${a.answer}</div>` : ""}</div>`)}

      <div style="border-top:1px solid var(--line-2);padding-top:12px"><b style="font-weight:500">${t("eoCapture")}</b><p class="hint">${t("eoCaptureSub")}</p></div>
      ${mine ? html`<div class="note info" role="status">${t("eoCaptureRunning", { f: cap.file, n: cap.frames, since: fmtAgo(cap.started) })}${cap.exclusive_peer ? html`<br>${t("eoCaptureLock", { peer: cap.exclusive_peer })}` : ""}</div>
          <div><button class="btn btn-s" @click=${() => this._capture(false)}>${t("eoCaptureStop")}</button> <a class="btn btn-g" href="#/trace/${c.id}">${t("eoToFiles")}</a></div>`
        : cap ? html`<div class="note warn">${t("eoCaptureOther", { n: cap.name })}</div>`
        : html`<div class="grid"><label class="fld"><span class="lbl">${t("eoLockTo")}</span>
            <select class="inp" @change=${(ev) => { this.peer = ev.target.value; }}>
              <option value="" ?selected=${!this.peer}>${t("eoLockNone")}</option>
              ${hosts.map((h) => html`<option value=${h} ?selected=${this.peer === h}>${h}</option>`)}</select>
            <span class="hint">${t("eoLockHint")}</span></label></div>
          <div><button class="btn btn-s" ?disabled=${!c.enabled} @click=${() => this._capture(true)}>${t("eoCaptureStart")}</button></div>
          <details><summary class="hint" style="cursor:pointer">${t("eoPct14")}</summary><ol class="hint" style="margin:8px 0 0 18px;padding:0">${t("eoPct14Steps").split("|").map((s) => html`<li>${s}</li>`)}</ol></details>`}
    `, !!this.test || this.answers.length > 0 || !!mine);
  }
}
