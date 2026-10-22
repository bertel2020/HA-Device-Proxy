// EnOcean gateways: the frame check, the issues in plain words, the status card and the tools
// (send one frame, test the gateway, capture with the lock for PCT14).
import { LitElement, css, html } from "lit";
import { api } from "./api.js";
import { lang, t } from "./i18n.js";
import { base, tokens } from "./styles.js";
import { confirmDialog, fmtAgo, fmtTime, icon, proxyTarget, toolsCard } from "./ui.js";

export const TEMPLATES = {
  fam_usb: { esp_protocol: "esp2", link: "serial", baud: 9600 },
  fam14: { esp_protocol: "esp2", link: "serial", baud: 57600 },
  fgw14_usb: { esp_protocol: "esp2", link: "serial", baud: 57600 },
  usb300: { esp_protocol: "esp3", link: "serial", baud: 57600 },
  mgw_eth: { esp_protocol: "esp3", link: "tcp", host_port: 5100 },
  symcon_lan: { esp_protocol: "esp3", link: "tcp", host_port: 5000 },
  enocean: {},
};
// the restriction the button "Only Home Assistant and apps" sets; new gateways follow the network setting
export const HA_ONLY = "127.0.0.1, 172.30.32.0/23";
export const DEFAULTS = {
  kind: "enocean", template: "fam_usb", ...TEMPLATES.fam_usb, data_bits: 8, parity: "n", stop_bits: 1, mode: "raw",
  max_clients: 4, remaddr: "", keep_open: false, stuck_disconnect: false, silence_minutes: 0,
  send_gap_ms: 10, replay_size: 1000, replay_max_age_s: 900, replay_persist: false,
  fallback: "", fallback_trigger: "probe", fallback_return: "auto", fallback_listen: false,
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

/** A base ID to set: { ok, msg }, or null while nothing is typed. Range FF-80-00-00 to FF-FF-FF-80 in steps of 0x80. */
export function checkBaseId(text, current) {
  const bytes = parseHex(text.trim());
  if (bytes !== null && !bytes.length) return null;
  if (bytes === null || bytes.length !== 4) return { ok: false, msg: t("eoBaseBadFormat") };
  const value = ((bytes[0] << 24) | (bytes[1] << 16) | (bytes[2] << 8) | bytes[3]) >>> 0;
  if (value < 0xff800000 || value > 0xffffff80 || value & 0x7f) return { ok: false, msg: t("eoBaseRange") };
  if (current && toHex(bytes).replaceAll(" ", "-") === current) return { ok: false, msg: t("eoBaseSame") };
  return { ok: true, msg: t("eoBaseRange") };
}

/** The EnOcean gateway a connection is the fallback of, from the app state. */
export const mainOf = (c, connections) => connections.find((x) => x.kind === "enocean" && x.fallback === c.id && x.id !== c.id);

/** What is wrong with a gateway, worst first: [{level, title, text}]. */
export function issues(c, capture, main = null) {
  const e = c.enocean;
  if (!c.enabled || !e) return [];
  const f = e.frames, out = [];
  const add = (level, key, values = {}) => out.push({ level, title: t(`eoI_${key}`, values), text: t(`eoIt_${key}`, values) });
  if (e.listen_error) add("bad", "port", { port: c.port, e: e.listen_error });
  const fb = e.fallback;
  if (fb && fb.active === "fallback") add("warn", fb.reason === "by_hand" ? "fallbackHand" : "fallback", { b: fb.name || "?", r: t(`fbReason_${fb.reason}`), t: fmtAgo(fb.active_since) });
  else if (fb && !fb.ready) add("warn", "fbUnready", { b: fb.name || "?", r: t(`fbReason_${fb.not_ready}`) });
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
  if (e.serves) out.push({ level: "info", title: t("eoI_serves", { a: e.serves }), text: t(main?.enocean?.fallback?.active === "fallback" ? "eoIt_servesActive" : "eoIt_serves", { a: e.serves }), link: main ? [`#/connection/${main.id}`, t("fbToMain", { a: main.name })] : null });
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
      ${e.base_id_writes_left != null ? html`<span class="hint">${t("eoBaseLeft")}</span><span style=${e.base_id_writes_left ? "" : "color:var(--warn)"}>${e.base_id_writes_left}</span>` : ""}
      ${e.connected_since ? html`<span class="hint">${t("eoSince")}</span><span>${fmtAgo(e.connected_since)}</span>` : ""}
    </div>
    <div class="counters">${counters.map(([k, v]) => html`<div class="well"><b style=${["eoDropped", "eoRefused"].includes(k) && v ? "color:var(--warn)" : ""}>${num(v)}</b>
      <span class="hint">${t(k)}</span></div>`)}</div>
    ${e.last_error && !e.connected ? html`<div class="note bad">${e.last_error}${e.last_error_at ? ` · ${fmtTime(e.last_error_at, true, true)}` : ""}</div>` : ""}
    ${!c.fallback && !e.serves ? html`<a href="#/edit/${c.id}/fallback" style="font-size:13px">${t("fbAdd")}</a>` : ""}
  </section>`;
}

/** One gateway in the card "Gateways": role, state, base ID, answer time. */
function gatewayBox(role, name, href, connected, stateText, stateClass, baseId, same, probeMs, current, frames = {}) {
  return html`<div class="well" style="display:flex;flex-direction:column;gap:6px;${current ? "outline:2px solid var(--accent);outline-offset:-2px" : ""}">
    <div class="row"><b style="font-weight:500">${role} · ${href ? html`<a href=${href}>${name}</a>` : name}</b>
      <span class="chip ${stateClass}"><span class="dot"></span>${stateText}</span></div>
    <div class="kv" style="display:grid;grid-template-columns:auto 1fr;gap:4px 12px">
      <span class="hint">${t("eoBaseId")}</span><span><span class="mono">${baseId || t("eoBaseUnknown")}</span>${same === true ? html` <span style="color:var(--ok)">✓ ${t("fbSame")}</span>` : same === false ? html` <span style="color:var(--bad)">${t("fbDiffers")}</span>` : ""}</span>
      <span class="hint">${t("fbAnswer")}</span><span>${connected ? (probeMs != null ? `${probeMs.toLocaleString(lang)} ms` : "–") : t("fbDown")}</span>
      <span class="hint">${t("fbFrames")}</span><span>${t("fbFramesN", { r: num(frames.from_gateway), s: num(frames.to_gateway) })}</span>
    </div></div>`;
}

/** The card of a gateway with a fallback: both gateways, which one is in use, switching and the hardware swap. */
export class EnOceanGateways extends LitElement {
  static properties = { connection: { attribute: false }, connections: { attribute: false }, busy: { state: true }, old: { state: true } };

  static styles = [tokens, base, css`:host { display: block; } .stack { display: flex; flex-direction: column; gap: 10px; }`];

  constructor() { super(); this.old = "off"; }

  _toast(text) { this.dispatchEvent(new CustomEvent("dp-toast", { detail: text, bubbles: true, composed: true })); }

  _refresh() { this.dispatchEvent(new CustomEvent("dp-refresh", { bubbles: true, composed: true })); }

  async _switch(to) {
    const c = this.connection, fb = c.enocean.fallback;
    if (to === "fallback" && !(await confirmDialog(this, t("fbSwitchConfirm", { a: c.name, b: fb.name }), t("fbToFallback")))) return;
    this.busy = true;
    try {
      await api(`api/tools/${c.id}/enocean/switch`, { method: "POST", body: { to } });
      this._toast(t("fbSwitched"));
      this._refresh();
    } catch (err) { this._toast(`${t("error")}: ${err.message}`); } finally { this.busy = false; }
  }

  async _promote() {
    const c = this.connection, other = this.connections.find((x) => x.id === c.fallback);
    if (!other) return;
    const what = t(`fbold_${this.old}`, { b: other.name });
    if (!(await confirmDialog(this, t("fbPromoteConfirm", { a: c.name, new: proxyTarget(other), old: proxyTarget(c), what }), t("fbPromote")))) return;
    this.busy = true;
    try {
      await api(`api/connections/${c.id}/promote_fallback`, { method: "POST", body: { old: this.old } });
      this._toast(t("fbPromoted"));
      this._refresh();
    } catch (err) { this._toast(`${t("error")}: ${err.message}`); } finally { this.busy = false; }
  }

  render() {
    const c = this.connection, e = c.enocean || {}, fb = e.fallback || {};
    const other = this.connections.find((x) => x.id === c.fallback);
    const onFallback = fb.active === "fallback";
    const mine = e.base_id;
    const same = fb.base_id && mine ? fb.base_id === mine : null;
    const mainState = onFallback ? [e.connected ? t("fbStandby") : t("fbDown"), e.connected ? "info" : "bad"] : [t("fbActive"), "ok"];
    const fbState = !other?.enabled ? [t("fbNotReady"), "bad"] : onFallback ? [t("fbActive"), "warn"] : fb.ready ? [fb.listen ? t("fbStandbyListen") : t("fbStandby"), "ok"] : [t("fbNotReady"), "bad"];
    const h = fb.heard || {};
    return html`<section class="card" aria-labelledby="t-gws"><div class="stack">
      <div class="row"><h2 id="t-gws">${t("fbCardTitle")}</h2><span class="hint">${c.fallback_return === "manual" ? t("fbReturnManual") : t("fbReturnAuto")}</span></div>
      ${gatewayBox(t("fbMain"), c.name, "", e.connected, ...mainState, mine, null, e.probe_ms, !onFallback, e.frames)}
      ${gatewayBox(t("fbFallback"), fb.name || other?.name || "?", other ? `#/connection/${other.id}` : "", fb.connected, ...fbState, fb.base_id, same, fb.probe_ms, onFallback, fb.frames)}
      ${!fb.ready && fb.not_ready ? html`<div class="note warn">${t(`fbReason_${fb.not_ready}`)}</div>` : ""}
      ${onFallback ? html`<p class="hint" style="margin:0">${t("fbSince", { t: fmtAgo(fb.active_since) })} · ${t(`fbReason_${fb.reason}`)}${fb.manual ? ` · ${t("fbManualNote")}` : ""}</p>` : ""}
      <div class="row" style="justify-content:flex-start;gap:8px">
        ${onFallback ? html`<button class="btn btn-s" ?disabled=${this.busy || !e.connected} @click=${() => this._switch("main")}>${t("fbBack", { a: c.name })}</button>`
          : html`<button class="btn btn-s" ?disabled=${this.busy || !fb.ready} @click=${() => this._switch("fallback")}>${t("fbToFallback")}</button>`}
      </div>
      ${fb.listen ? html`<div style="border-top:1px solid var(--line-2);padding-top:10px"><b style="font-weight:500">${t("fbHeard")}</b></div>
        <div class="counters">${[["fbHeardMain", h.main], ["fbHeardFallback", h.fallback], ["fbHeardDup", h.duplicates], ["fbHeardOwn", h.own]].map(([k, v]) =>
          html`<div class="well"><b>${num(v)}</b><span class="hint">${t(k, { a: c.name, b: fb.name || "?" })}</span></div>`)}</div>` : ""}
      ${other ? html`<details class="fold" style="border-top:1px solid var(--line-2);padding-top:10px"><summary>${t("fbPromote")}</summary>
        <div class="stack" style="margin-top:8px"><p class="hint" style="margin:0">${t("fbPromoteSub", { a: c.name, b: other.name })}</p>
          <label class="fld"><span class="lbl">${t("fbOld")}</span><select class="inp" @change=${(ev) => { this.old = ev.target.value; }}>
            ${["off", "keep", "delete"].map((v) => html`<option value=${v} ?selected=${this.old === v}>${t(`fbold_${v}`, { b: other.name })}</option>`)}</select></label>
          <div><button class="btn btn-s" ?disabled=${this.busy} @click=${this._promote}>${t("fbPromote")}</button></div></div></details>` : ""}
    </div></section>`;
  }
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
  return html`<div style="display:flex;flex-direction:column;gap:8px">${list.map((i) => html`<div class="note ${i.level}" role="status"><b style="font-weight:500">${i.title}</b><div>${i.text}${i.link ? html` <a href=${i.link[0]}>${i.link[1]}</a>` : ""}${i.jump ? html` <a href="#" @click=${(ev) => { ev.preventDefault(); const target = ev.currentTarget.getRootNode().getElementById(i.jump); const fold = target?.querySelector("details"); if (fold) fold.open = true; target?.scrollIntoView({ behavior: "smooth", block: "center" }); }}>${t("showAddresses")}</a>` : ""}</div></div>`)}</div>`;
}

/** The tools card of one gateway; its own element, so typing does not wait for the state poll. */
export class EnOceanTools extends LitElement {
  static properties = {
    connection: { attribute: false }, capture: { attribute: false },
    text: { state: true }, answers: { state: true }, test: { state: true }, busy: { state: true }, peer: { state: true },
    baseId: { state: true }, baseResult: { state: true },
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
    this.baseId = "";
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

  async _setBaseId() {
    const c = this.connection, e = c.enocean || {};
    const left = e.base_id_writes_left;
    const wanted = this.baseId.trim().toUpperCase();
    const text = t("eoBaseConfirm", { id: wanted, n: c.name }) + (left != null ? ` ${t("eoBaseConfirmLeft", { n: Math.max(0, left - 1) })}` : ` ${t("eoBaseConfirmUnknown")}`);
    if (!(await confirmDialog(this, text, t("eoBaseSet")))) return;
    this.busy = "base";
    try {
      this.baseResult = await api(`api/tools/${c.id}/enocean/base_id`, { method: "POST", body: { base_id: wanted } });
      if (this.baseResult.result === "ok") this.baseId = "";
      this._refresh();
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
    const baseCheck = checkBaseId(this.baseId, e.base_id);
    const hosts = [...new Set(c.clients.map((cl) => cl.address.replace(/^\[?(.*?)\]?:\d+$/, "$1")))];
    return toolsCard("device_proxy.tools.enocean", "t-eotools", t("eoToolsSub"), html`
      ${blocked ? html`<div class="note warn">${blocked}</div>` : ""}
      <div class="row"><div><b style="font-weight:500">${t("eoTest")}</b><p class="hint">${t("eoTestSub")}</p></div>
        <button class="btn btn-s" ?disabled=${!!blocked || this.busy === "test"} @click=${this._test}>${this.busy === "test" ? t("eoTesting") : t("eoTestBtn")}</button></div>
      ${this.test ? html`<div class="note ${this.test.lost ? "warn" : "ok"}">${t("eoTestResult", { a: this.test.answered, s: this.test.sent, avg: this.test.avg_ms ?? "–", max: this.test.max_ms ?? "–" })}</div>` : ""}

      <div style="border-top:1px solid var(--line-2);padding-top:12px"><b style="font-weight:500">${t("eoBaseTitle")}</b><p class="hint">${t("eoBaseSub")}</p></div>
      <div class="kv" style="display:grid;grid-template-columns:auto 1fr;gap:6px 12px">
        <span class="hint">${t("eoBaseNow")}</span><span class="mono">${e.base_id || t("eoBaseUnknown")}</span>
        <span class="hint">${t("eoBaseLeft")}</span><span style=${e.base_id_writes_left === 0 ? "color:var(--warn)" : ""}>${e.base_id_writes_left ?? t(c.esp_protocol === "esp2" ? "eoBaseLeftEsp2" : "eoBaseLeftUnknown")}</span>
      </div>
      <div class="grid"><label class="fld"><span class="lbl">${t("eoBaseNew")}</span>
        <input class="inp mono" spellcheck="false" placeholder="FF-B7-44-80" .value=${this.baseId} @input=${(ev) => { this.baseId = ev.target.value; }}>
        <span class="hint" style=${baseCheck && !baseCheck.ok ? "color:var(--bad)" : ""}>${baseCheck ? baseCheck.msg : t("eoBaseRange")}</span></label></div>
      <div><button class="btn btn-s" ?disabled=${!!blocked || !baseCheck?.ok || e.base_id_writes_left === 0 || this.busy === "base"} @click=${this._setBaseId}>${this.busy === "base" ? t("eoBaseSetting") : t("eoBaseSet")}</button></div>
      ${this.baseResult ? html`<div class="note ${this.baseResult.result === "ok" ? "ok" : "bad"}" role="status">${t(`eoBaseR_${this.baseResult.result}`)}${this.baseResult.writes_left != null ? ` · ${t("eoBaseLeftN", { n: this.baseResult.writes_left })}` : ""}</div>` : ""}

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
          <details class="fold"><summary>${t("eoPct14")}</summary><ol class="hint" style="margin:8px 0 0 18px;padding:0">${t("eoPct14Steps").split("|").map((s) => html`<li>${s}</li>`)}</ol></details>`}
    `, !!this.test || this.answers.length > 0 || !!mine);
  }
}
