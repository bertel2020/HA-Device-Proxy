import { css, html, svg } from "lit";
import { api, saveConnection, toConnection } from "../api.js";
import { Page } from "../app.js";
import { issues, issuesCard, meterCards, statusCard } from "../enocean.js";
import { eventText, t } from "../i18n.js";
import { confirmDialog, connectionState, copyText, dirLabel, fmtAgo, fmtBytes, fmtRate, fmtSerial, fmtTime, lines16, proxyTarget, toggle } from "../ui.js";

const LIVE_MS = 1000;
// the proxy's words for frames that are no radio telegram
const eoInfo = (info) => info.replace(/^(answer|bus|command)\b/, (w) => t(`eoKind_${w}`));
const SAMPLES = 90; // 3 minutes of state polls

/** Who may connect: the connection's own rule, else the network setting. */
function who(c, s) {
  const bind = c.bind ? `${t("bind")} ${c.bind} · ` : "";
  const local = c.bind && (c.bind.startsWith("127.") || c.bind === "::1");
  return bind + (c.remaddr ? t("whoOwn", { a: c.remaddr }) : local ? t("listen_local") : reach(c, s));
}

function reach(c, s) {
  const { listen, lan_networks: list = "" } = s.settings, net = s.lan_net;
  if (listen !== "lan") return t(`listen_${listen}`);
  const nets = list.split(/[\s,;]+/).filter(Boolean).map((x) => (x === "own" ? net || t("lanOwn") : x));
  return nets.length ? t("listen_lan_n", { nets: nets.join(", ") }) : t("listen_lan_none");
}

export class DetailPage extends Page {
  static properties = {
    state: { attribute: false }, events: { attribute: false }, connectionId: {},
    chunks: { state: true }, paused: { state: true }, ascii: { state: true }, copied: { state: true },
    meter: { state: true }, job: { state: true }, search: { state: true }, dir: { state: true },
    mbForm: { state: true }, mbResult: { state: true }, scan: { state: true }, scanForm: { state: true },
  };

  static styles = [...Page.styles, css`
    .kv { display: grid; grid-template-columns: minmax(110px, 170px) minmax(0, 1fr); gap: 10px 16px; }
    .kv > :nth-child(odd) { color: var(--muted); }
    .counters { display: grid; grid-template-columns: repeat(auto-fit, minmax(90px, 1fr)); gap: 10px; }
    .counters b { display: block; font-size: 20px; font-weight: 500; }
    .live { max-height: 340px; overflow: auto; }
    .live table { font-family: "Roboto Mono", ui-monospace, Menlo, monospace; font-size: 12px; color: var(--code-text); }
    .live td { border: none; padding: 2px 8px; white-space: pre; vertical-align: top; }
    .live .info { white-space: normal; overflow-wrap: anywhere; }
    .dir { display: inline-block; min-width: 78px; white-space: nowrap; text-align: center; border-radius: 6px; padding: 0 6px; }
    .rx { background: #1f3a52; color: #9ccbf0; } .tx { background: #4a3a1c; color: #f4c77d; } .mark { background: #2a3038; color: #c5ccd5; }
    ol { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 12px; }
    li { display: flex; gap: 10px; } li .dot { margin-top: 6px; }
    .grid4 { display: grid; grid-template-columns: repeat(auto-fit, minmax(190px, 1fr)); gap: 10px; }

  `];

  constructor() {
    super();
    this.chunks = [];
    this.paused = false;
    this.ascii = true;
    this.search = "";
    this.dir = "";
    this._samples = [];
    this._after = 0;
    this.mbForm = { unit: 1, function: 3, address: 0, count: 10 };
    this.scanForm = { first: 1, last: 247, timeout_ms: 200 };
  }

  connectedCallback() {
    super.connectedCallback();
    this._timer = setInterval(() => this._poll(), LIVE_MS);
    this._poll();
  }

  disconnectedCallback() {
    super.disconnectedCallback();
    clearInterval(this._timer);
  }

  willUpdate(changed) {
    if (changed.has("connectionId")) { this.chunks = []; this._after = 0; this._n = 0; this._samples = []; this._rqSamples = []; this._rq = null; this.search = ""; this.dir = ""; }
    if (changed.has("state")) {
      const c = this.connection(this.connectionId);
      if (c) this._samples = [...this._samples, c.rate_from_device].slice(-SAMPLES);
      if (c && c.kind === "modbus" && c.modbus && typeof c.modbus.requests === "number") {
        const now = Date.now() / 1000, last = this._rq;
        if (last && now > last.t && c.modbus.requests >= last.n) this._rqSamples = [...(this._rqSamples || []), (c.modbus.requests - last.n) / (now - last.t)].slice(-SAMPLES);
        this._rq = { t: now, n: c.modbus.requests };
      }
    }
  }

  /** The saved choice for this connection's live card: "1" open, "0" closed, null never chosen. */
  _pref() {
    try { return localStorage.getItem(`device_proxy.live.${this.connectionId}`); } catch { return null; }
  }

  _setOpen(open) {
    try { localStorage.setItem(`device_proxy.live.${this.connectionId}`, open ? "1" : "0"); } catch { /* private window */ }
    this.requestUpdate();
  }

  _liveOpen() {
    const pref = this._pref();
    return pref === "1" || (pref === null && this.chunks.length > 0);
  }

  async _poll() {
    if (this.paused || !this.connectionId || document.hidden) return;
    this._n = (this._n || 0) + 1;
    if (!this._liveOpen() && (this._n - 1) % 5) return; // closed: only now and then, for the summary line
    this.requestUpdate();
    try {
      const fresh = await api(`api/live/${this.connectionId}?after=${this._after}`);
      if (fresh.length) {
        this._after = fresh[fresh.length - 1].seq;
        this.chunks = [...this.chunks, ...fresh].slice(-300);
      }
    } catch { /* shown by the frame */ }
  }

  async _enable(c, enabled) {
    if (!enabled && c.clients.length && !(await confirmDialog(this, t("offConfirm", { n: c.name, c: c.clients.length }), t("switchOff")))) return;
    try {
      await api(`api/connections/${c.id}/enabled`, { method: "POST", body: { enabled } });
      this.refresh();
    } catch (err) { this.toast(`${t("error")}: ${err.message}`); }
  }

  async _checkMeter() {
    try { this.meter = await api(`api/tools/${this.connectionId}/meter`); this.meterAt = Date.now() / 1000; } catch (err) { this.toast(`${t("error")}: ${err.message}`); }
  }

  async _detect() {
    if (!(await confirmDialog(this, t("baudConfirm"), t("start")))) return;
    try {
      const { job } = await api(`api/tools/${this.connectionId}/detect`, { method: "POST" });
      this.job = { state: "running", done: 0, total: 0 };
      const poll = setInterval(async () => {
        try {
          this.job = await api(`api/jobs/${job}`);
          if (this.job.state !== "running") clearInterval(poll);
        } catch { clearInterval(poll); }
      }, 1000);
    } catch (err) { this.toast(`${t("error")}: ${err.message}`); }
  }

  async _useCandidate(c, r) {
    try {
      await saveConnection({ ...toConnection(c), baud: r.baud, data_bits: r.data_bits, parity: r.parity, stop_bits: r.stop_bits });
      this.toast(t("saved"));
      this.job = null;
      this.refresh();
    } catch (err) { this.toast(`${t("error")}: ${err.message}`); }
  }

  async _mbRead() {
    try {
      this.mbResult = { ...(await api(`api/tools/${this.connectionId}/modbus/read`, { method: "POST", body: this.mbForm })), form: { ...this.mbForm } };
    } catch (err) { this.toast(`${t("error")}: ${err.message}`); }
  }

  async _mbScan() {
    try {
      const { job } = await api(`api/tools/${this.connectionId}/modbus/scan`, { method: "POST", body: this.scanForm });
      this.scan = { state: "running", done: 0, total: this.scanForm.last - this.scanForm.first + 1, results: [] };
      const poll = setInterval(async () => {
        try {
          this.scan = await api(`api/jobs/${job}`);
          if (this.scan.state !== "running") clearInterval(poll);
        } catch { clearInterval(poll); }
      }, 1000);
    } catch (err) { this.toast(`${t("error")}: ${err.message}`); }
  }

  _num(form, key, label, prop) {
    return html`<label class="fld"><span class="lbl">${label}</span><input class="inp" inputmode="numeric" .value=${String(form[key])}
      @input=${(e) => { this[prop] = { ...this[prop], [key]: Number(e.target.value || 0) }; }}></label>`;
  }

  _modbusTools(c) {
    const f = this.mbForm, r = this.mbResult, sc = this.scan;
    const signed = (v) => (v > 32767 ? v - 65536 : v);
    const hex4 = (v) => `0x${v.toString(16).toUpperCase().padStart(4, "0")}`;
    const exText = (code) => code === null || code === undefined ? t("mbNoAnswer") : t("mbException", { c: code.toString(16).toUpperCase().padStart(2, "0"), n: t(`ex_${code}`) });
    const pref = (() => { try { return localStorage.getItem("device_proxy.mbtools"); } catch { return null; } })();
    return html`<section class="card" aria-labelledby="t-mtools">
      <details ?open=${pref === "1" || !!r || !!sc} @toggle=${(e) => { try { localStorage.setItem("device_proxy.mbtools", e.target.open ? "1" : "0"); } catch { /* private window */ } }}>
      <summary style="cursor:pointer;display:flex;align-items:baseline;gap:8px"><h2 id="t-mtools" style="display:inline">${t("tools")}</h2><span class="hint">· ${t("mbToolsSub")}</span></summary>
      <div style="display:flex;flex-direction:column;gap:12px;margin-top:12px">
      <div><b style="font-weight:500">${t("mbReadTitle")}</b><p class="hint">${t("mbReadSub")}</p></div>
      <div class="grid4">
        ${this._num(f, "unit", t("mbUnit"), "mbForm")}
        <label class="fld"><span class="lbl">${t("mbFunction")}</span><select class="inp" @change=${(e) => { this.mbForm = { ...f, function: Number(e.target.value) }; }}>
          ${[3, 4, 1, 2].map((v) => html`<option value=${v} ?selected=${f.function === v}>${t(`fc_${v}`)}</option>`)}</select></label>
        ${this._num(f, "address", t("mbAddress"), "mbForm")}
        ${this._num(f, "count", t("mbCount"), "mbForm")}
      </div>
      <div style="display:flex;justify-content:flex-end"><button class="btn btn-s" ?disabled=${!c.enabled} @click=${this._mbRead}>${t("mbReadBtn")}</button></div>
      ${r ? r.ok ? html`<div class="scroll"><table style="min-width:360px"><thead><tr><th>${t("mbAddress")}</th>
          ${r.form.function >= 3 ? html`<th style="text-align:right">${t("mbUnsigned")}</th><th style="text-align:right">${t("mbSigned")}</th><th style="text-align:right">Hex</th>` : html`<th style="text-align:right">${t("mbBit")}</th>`}</tr></thead>
          <tbody>${r.values.map((v, i) => html`<tr><td class="mono">${r.form.address + i}</td>
            ${r.form.function >= 3 ? html`<td style="text-align:right">${v}</td><td style="text-align:right">${signed(v)}</td><td class="mono" style="text-align:right">${hex4(v)}</td>` : html`<td style="text-align:right">${v}</td>`}</tr>`)}</tbody></table></div>
          <p class="hint">${t("mbReadTime", { ms: r.time_ms })}</p>`
        : html`<div class="note warn">${exText(r.exception)}</div>` : ""}
      <div class="row" style="border-top:1px solid var(--line-2);padding-top:12px"><div><b style="font-weight:500">${t("mbScanTitle")}</b><p class="hint">${t("mbScanSub")}</p></div></div>
      <div class="grid4">
        ${this._num(this.scanForm, "first", t("mbFirst"), "scanForm")}
        ${this._num(this.scanForm, "last", t("mbLast"), "scanForm")}
        ${this._num(this.scanForm, "timeout_ms", t("mbScanTimeout"), "scanForm")}
      </div>
      <div style="display:flex;justify-content:flex-end"><button class="btn btn-s" ?disabled=${!c.enabled || (sc && sc.state === "running")} @click=${this._mbScan}>${t("start")}</button></div>
      ${sc ? html`${sc.state === "running" ? html`<p class="hint" role="status">${t("detecting", { d: sc.done, t: sc.total })}</p>` : ""}
        ${sc.state === "failed" ? html`<div class="note bad">${t("error")}: ${sc.error}</div>` : ""}
        ${sc.results.length ? html`<div style="display:flex;flex-wrap:wrap;gap:6px">${sc.results.map((u) => html`<button class="chip ${u.exception === null ? "ok" : "info"}" style="cursor:pointer;border:none"
          title=${u.exception === null ? "" : exText(u.exception)} @click=${() => { this.mbForm = { ...this.mbForm, unit: u.unit }; }}>Unit ${u.unit}</button>`)}</div>`
          : sc.state === "done" ? html`<p class="hint">${t("mbScanNone")}</p>` : ""}` : ""}
      </div></details>
    </section>`;
  }

  _tools(c) {
    const m = this.meter, job = this.job;
    const best = job && job.state === "done" ? job.results.filter((r) => r.score >= 0.6) : [];
    const fmt = (r) => `${r.baud} ${r.data_bits}${r.parity.toUpperCase()}${r.stop_bits}`;
    const value = (r) => typeof r.value === "number" && r.unit === "Wh" ? `${(r.value / 1000).toLocaleString(undefined, { maximumFractionDigits: 3 })} kWh` : `${r.value} ${r.unit}`;
    const blocked = !c.enabled ? "toolOff" : c.present === false ? "toolMissing" : "";
    const meterFirst = ["ehz_sml", "ehz_d0"].includes(c.template) || !!(m && m.bytes && m.protocol !== "unknown");
    const meter = (head) => html`<div class="row ${head ? "" : "sep"}"><div><b style="font-weight:500">${t("meterCheck")}</b>${blocked ? "" : html`<p class="hint">${t("meterCheckSub")}</p>`}${blocked ? html`<p class="hint" style="color:var(--bad)">${t(blocked)}</p>` : ""}</div>
        <button class="btn btn-s" ?disabled=${!!blocked} @click=${this._checkMeter}>${t("toolCheck")}</button></div>
      ${m ? m.bytes ? html`<div class="well" style="display:flex;flex-direction:column;gap:8px">
          <div style="display:flex;flex-wrap:wrap;gap:6px;align-items:center"><span class="chip ${m.protocol === "unknown" ? "warn" : "info"}">${t(`proto_${m.protocol}`)}</span>
            ${m.telegrams ? html`<span class="chip">${t("telegrams", { n: m.telegrams })}</span>
              <span class="chip ${m.valid === m.telegrams ? "ok" : "warn"}">${t(m.protocol === "sml" ? "validCrc" : "validD0", { n: m.valid })}</span>` : ""}
            ${this.meterAt ? html`<span class="hint" style="margin-left:auto">${t("checkedAt", { t: fmtTime(this.meterAt, false) })}</span>` : ""}</div>
          ${m.readings.length ? html`<table><tbody>${m.readings.slice(0, 12).map((r) => html`<tr><td class="mono" style="font-size:12px">${r.obis}</td><td>${r.name ? t(`obis_${r.obis}`) : ""}</td><td style="text-align:right">${value(r)}</td></tr>`)}</tbody></table>` : ""}
        </div>` : html`<div class="well hint" style="font-size:13px">${t("noData30")} ${t("noData30Help")} <a href="#/edit/${c.id}">${t("edit")}</a></div>` : ""}`;
    const baud = (head) => html`<div class="row ${head ? "" : "sep"}"><div><b style="font-weight:500">${t("baudDetect")}</b>${blocked ? html`<p class="hint" style="color:var(--bad)">${t(blocked)}</p>` : html`<p class="hint">${t("baudDetectSub")}</p>`}</div>
        <button class="btn btn-s" ?disabled=${!!blocked || (job && job.state === "running")} @click=${this._detect}>${t("toolStart")}</button></div>
      ${job ? job.state === "running" ? html`<p class="hint" role="status">${t("detecting", { d: job.done, t: job.total || "…" })}</p>`
        : job.state === "failed" ? html`<div class="note bad">${t("error")}: ${job.error}</div>`
        : best.length ? html`<div class="note ok"><b>${t("detected", { b: best[0].baud, f: fmt(best[0]).split(" ")[1] })}</b> · ${t(`proto_${best[0].protocol}`)}</div>
          <div class="hint">${t("candidates")}:</div>
          ${best.slice(0, 3).map((r) => html`<div class="row well"><span class="mono">${fmt(r)}</span><span class="hint">${t("score")} ${Math.round(r.score * 100)} %</span>
            <button class="btn btn-g" @click=${() => this._useCandidate(c, r)}>${t("applyThis")}</button></div>`)}`
        : html`<div class="note warn">${t("noDetect")}</div>` : ""}`;
    return html`<section class="card" aria-labelledby="t-tools">
      <h2 id="t-tools">${t("tools")}</h2>
      ${meterFirst ? html`${meter(true)}${baud(false)}` : html`${baud(true)}
        <details class="sep" ?open=${!!m}><summary class="hint" style="cursor:pointer">${t("moreTools")}</summary><div style="margin-top:10px;display:flex;flex-direction:column;gap:12px">${meter(true)}</div></details>`}
    </section>`;
  }

  async _copy(key, text) {
    if (await copyText(text)) { this.copied = key; setTimeout(() => { if (this.copied === key) this.copied = ""; }, 2000); }
  }

  _matches(ch) {
    if (this.dir && ch.direction !== this.dir) return false;
    const q = this.search.trim().toLowerCase().replace(/[\s:-]/g, "");
    if (!q) return true;
    return (ch.info || "").toLowerCase().replace(/[\s:-]/g, "").includes(q) || (ch.hex || "").toLowerCase().replace(/\s/g, "").includes(q);
  }

  _take(hex) {
    const tools = this.renderRoot.querySelector("dp-enocean-tools");
    if (tools) { tools.take(hex); tools.scrollIntoView({ behavior: "smooth", block: "center" }); }
  }

  _live(kind) {
    const modbus = kind === "modbus", enocean = kind === "enocean";
    const all = this.chunks.slice(-300).reverse(); // newest first, like the event log
    const rows = (enocean ? all.filter((ch) => this._matches(ch)) : all).slice(0, 120);
    const sender = (info) => (info.match(/[0-9A-F]{2}(-[0-9A-F]{2}){3}/) || [])[0];
    // a Modbus line ends in the client's address; with one client only it is said once in the subtitle
    const via = (info = "") => (info.match(/ · (\[?[0-9a-f.:]+\]?:\d+)$/i) || [])[1];
    const clients = new Set(modbus ? rows.map((ch) => via(ch.info)).filter(Boolean) : []);
    const only = clients.size === 1 ? [...clients][0] : "";
    const infoOf = (ch) => (only && via(ch.info) === only ? ch.info.slice(0, -(only.length + 3)) : ch.info);
    if (!this._liveOpen()) {
      const last = this.chunks[this.chunks.length - 1];
      const recent = this.chunks.filter((ch) => ch.ts > Date.now() / 1000 - 10).length;
      const rate = recent ? Math.round((recent / 10) * 10) / 10 : 0;
      const line = last ? (last.info || last.hex || last.text || "") : "";
      return html`<section class="card" aria-labelledby="t-live" style="gap:6px">
        <div class="row"><div><h2 id="t-live" style="display:inline">${t("live")}</h2>
          <span class="hint"> · <span class="dot" style="color:${last ? "var(--ok)" : "var(--muted)"}"></span>${last ? `${t("liveLast", { ago: fmtAgo(last.ts) })}${rate ? ` · ${t(modbus ? "liveRateMb" : "liveRate", { n: rate.toLocaleString() })}` : ""}` : t("liveNone")}</span></div>
          <button class="btn btn-g" @click=${() => this._setOpen(true)}>${t("liveShow")}</button></div>
        ${last ? html`<div class="mono hint" style="white-space:nowrap;overflow:hidden;text-overflow:ellipsis">${new Date(last.ts * 1000).toLocaleTimeString(undefined, { hour12: false })} · ${dirLabel(last.direction, kind)} · ${line}</div>`
          : html`<p class="hint" style="margin:0">${t(enocean ? "liveEmptyEo" : modbus ? "liveEmptyMb" : "liveEmpty")} ${t("liveAutoOpen")}</p>`}
      </section>`;
    }
    return html`<section class="card" aria-labelledby="t-live">
      <div class="row"><div><h2 id="t-live">${t("live")}</h2><p class="hint">${t(enocean ? "liveSubEo" : modbus ? "liveSubMb" : "liveSub")}${only ? ` ${t("liveClientOnly", { a: only })}` : ""}</p></div>
        <div style="display:flex;gap:4px">
          ${modbus || enocean ? "" : html`<button class="btn btn-g" aria-pressed=${this.ascii ? "true" : "false"} @click=${() => { this.ascii = !this.ascii; }}>${this.ascii ? t("hexOnly") : t("hexAscii")}</button>`}
          <button class="btn btn-g" @click=${() => { this.paused = !this.paused; }}>${this.paused ? t("resume") : t("pause")}</button>
          <button class="btn btn-g" @click=${() => this._setOpen(false)}>${t("liveHide")}</button>
        </div></div>
      ${enocean ? html`<div class="row" style="justify-content:flex-start;gap:8px">
        <input class="inp" style="flex:1 1 200px" type="search" aria-label=${t("eoSearch")} placeholder=${t("eoSearch")} .value=${this.search} @input=${(e) => { this.search = e.target.value; }}>
        <div class="seg" role="group" aria-label=${t("eoDirection")}>${[["", t("eoBoth")], ["rx", t("dir_rx")], ["tx", t("dir_tx")]].map(([v, l]) => html`<button type="button" aria-pressed=${this.dir === v ? "true" : "false"} @click=${() => { this.dir = v; }}>${l}</button>`)}</div>
        ${this.search || this.dir ? html`<span class="hint">${t("eoShown", { n: rows.length, m: all.length })}</span>` : ""}</div>` : ""}
      ${rows.length ? html`<div class="code live" style="padding:8px 4px"><table><tbody>
        ${rows.map((ch) => html`<tr>
          <td style="color:#8f9ba8">${new Date(ch.ts * 1000).toLocaleTimeString(undefined, { hour12: false })}.${String(Math.floor(ch.ts * 1000) % 1000).padStart(3, "0")}</td>
          <td><span class="dir ${ch.direction === "rx" ? "rx" : ch.direction === "tx" ? "tx" : "mark"}">${dirLabel(ch.direction, modbus ? "modbus" : kind)}</span></td>
          <td>${ch.info ? html`<div class="info" style="color:#9fb3c8">${enocean && sender(ch.info) ? html`<a href="#" style="color:inherit" title=${t("eoOnlySender")}
            @click=${(e) => { e.preventDefault(); this.search = sender(ch.info); }}>${ch.info}</a>` : eoInfo(infoOf(ch))}</div>` : ""}${ch.direction === "open" || ch.direction === "close" ? ch.text : ch.hex ? lines16(ch.hex.split(" "), " ") : ""}${enocean ? html`<div style="display:flex;gap:4px;margin-top:2px"><button class="btn btn-g" style="min-height:24px;padding:0 6px;font-size:12px;color:#9ccbf0" @click=${() => this._copy(`f${ch.seq}`, ch.hex)}>${this.copied === `f${ch.seq}` ? t("copied") : t("copy")}</button>
            <button class="btn btn-g" style="min-height:24px;padding:0 6px;font-size:12px;color:#9ccbf0" @click=${() => this._take(ch.hex)}>${t("eoTake")}</button></div>` : ""}</td>
          ${!ch.info && !enocean && this.ascii && ch.hex ? html`<td style="color:#9fb3c8">${lines16(ch.text.replace(/[^\x20-\x7e]/g, ".").split(""), "")}</td>` : ""}
        </tr>`)}</tbody></table></div>` : html`<div class="well hint" style="font-size:14px">${t(enocean ? (all.length ? "eoNoMatch" : "liveEmptyEo") : modbus ? "liveEmptyMb" : "liveEmpty")}</div>`}
    </section>`;
  }

  _haSnippet(c) {
    const ha = c.addresses.find((a) => a.target === "ha");
    if (!ha || !ha.reachable) return "";
    const yaml = `modbus:\n  - name: ${JSON.stringify(c.name)}\n    type: tcp\n    host: ${ha.host}\n    port: ${c.port}\n    # ${t("haSnippetComment")}`;
    return html`<section class="card" aria-labelledby="t-ha">
      <div><h2 id="t-ha">${t("haSnippet")}</h2><p class="hint" style="margin-top:4px">${t("haUiSteps", { h: ha.host, p: c.port })}</p></div>
      <p class="hint" style="margin:0">${t("haUnitHint")} <a href="https://www.home-assistant.io/integrations/modbus/" target="_blank" rel="noopener">${t("haDocs")}</a></p>
      <details style="border-top:1px solid var(--line-2);padding-top:10px"><summary class="hint" style="cursor:pointer">${t("haYamlSummary")}</summary>
        <div class="row" style="margin:8px 0"><p class="hint" style="margin:0;flex:1">${t("haYamlSub")}</p>
          <button class="btn btn-g" @click=${() => this._copy("ha-yaml", yaml)}>${this.copied === "ha-yaml" ? t("copied") : t("copy")}</button></div>
        <div class="code">${yaml}</div></details>
    </section>`;
  }

  _addresses(c) {
    return html`<section class="card" aria-labelledby="t-addr">
      <h2 id="t-addr">${t("addresses")}</h2>
              ${c.addresses.map((a) => html`<div class="well">
                <div class="row" style="justify-content:flex-start;gap:8px"><span class="dot" style="color:${a.reachable ? "var(--ok)" : "var(--muted)"}"></span>
                  <b style="font-weight:500;${a.reachable ? "" : "color:var(--muted)"}">${t(`target_${a.target}`)}</b></div>
                ${Object.entries(a.urls).map(([k, u]) => html`<div class="row" style="gap:4px;margin-top:4px">
                  <span class="mono" style="font-size:13px;overflow-wrap:anywhere">${u}</span>
                  <button class="btn btn-g" style="min-height:32px" @click=${() => this._copy(`${a.target}${k}`, u)}>${this.copied === `${a.target}${k}` ? t("copied") : t("copy")}</button></div>`)}
                ${a.reachable ? "" : html`<div class="hint" style="margin-top:2px">${a.host ? html`${t(`why_${a.why}`, { a: c.remaddr })}${a.why === "network" ? html` <a href="#/settings">${t("settingsTitle")}</a>` : html` <a href="#/edit/${c.id}">${t("edit")}</a>`}` : t("lanUnknown")}</div>`}
              </div>`)}
    </section>`;
  }

  _modbusCard(m) {
    const reach = m.reachable === true ? ["mbReachable", "ok"] : m.reachable === false ? ["mbUnreachable", "bad"] : ["mbUnknown", ""];
    const rq = this._rqSamples || [];
    const problems = [["mbTimeouts", m.timeouts], ["mbExceptions", m.exceptions], ["mbErrors", m.errors], ["mbBlocked", m.blocked]].filter(([, v]) => v);
    const summary = !m.requests ? t("mbNoRequests") : m.answered === m.requests ? t("mbAllAnswered") : t("mbSomeAnswered", { a: m.answered });
    const rate = rq.length ? rq.slice(-5).reduce((x, y) => x + y, 0) / Math.min(rq.length, 5) : 0;
    return html`<section class="card" aria-labelledby="t-mb">
      <div class="row"><h2 id="t-mb">${t("mbStats")}</h2><span class="chip ${reach[1]}"><span class="dot"></span>${t(reach[0])}</span></div>
      <div><b style="font-size:22px;font-weight:500">${(m.requests ?? 0).toLocaleString()}</b> <span class="hint">${summary}</span></div>
      ${this._sparkline(rq, t("mbRate"))}
      <div class="row hint" style="font-size:12px"><span>${t("sparkOld")}</span><span>${t("mbRateNow", { n: (Math.round(rate * 10) / 10).toLocaleString() })}</span><span>${t("sparkNow")}</span></div>
      <div class="row hint"><span>${t("mbTime")}</span><span>${m.answered ? t("mbTimeVal", { a: m.time_avg_ms, m: m.time_max_ms }) : "–"}</span></div>
      <div class="row hint"><span>${t("mbLastAnswer")}</span><span>${m.last_answer ? fmtAgo(m.last_answer) : t("never")}</span></div>
      ${problems.length || m.cached || m.probes || (m.queue ?? 0) > 1 ? html`<div style="display:flex;flex-wrap:wrap;gap:6px">
        ${problems.map(([k, v]) => html`<span class="chip warn">${v} ${t(k)}</span>`)}
        ${m.cached ? html`<span class="chip">${m.cached} ${t("mbCached")}</span>` : ""}${m.probes ? html`<span class="chip">${m.probes} ${t("mbProbes")}</span>` : ""}
        ${(m.queue ?? 0) > 1 ? html`<span class="chip">${t("mbQueue")} ${m.queue} / ${m.queue_max ?? 0}</span>` : ""}</div>` : ""}
      ${m.listen_error ? html`<div class="note bad">${t("mbListenError", { e: m.listen_error })}</div>` : ""}
      ${m.last_error ? html`<div class="note ${m.reachable === false ? "bad" : "warn"}">${t("mbLastError")}: ${m.last_error}${m.last_error_at ? ` · ${fmtTime(m.last_error_at, true, true)}` : ""}</div>` : ""}
    </section>`;
  }

  _sparkline(samples = this._samples, label = t("dataFromDevice")) {
    const values = samples.length > 1 ? samples : [0, 0];
    const max = Math.max(...values, 1);
    const step = 300 / (values.length - 1);
    const points = values.map((v, i) => `${(i * step).toFixed(1)},${(66 - (v / max) * 56).toFixed(1)}`);
    return html`<svg viewBox="0 0 300 70" width="100%" height="70" role="img" aria-label=${label}>
      ${svg`<path d="M0,70 L${points.join(" L")} L300,70 Z" fill="var(--accent-soft)"></path>
      <path d="M${points.join(" L")}" fill="none" stroke="var(--accent)" stroke-width="2"></path>`}</svg>`;
  }

  render() {
    const s = this.state;
    const c = this.connection(this.connectionId);
    if (!c) return html`<p class="crumb"><a href="#/connections">${t("connectionsTitle")}</a></p><p>${t("error")}</p>`;
    const [stateKey, stateClass] = connectionState(c, s.ser2net_running);
    const recent = this.events.filter((e) => e.connection === c.id).slice(-6).reverse();
    const le = c.line_errors;
    const usb = c.usb;
    const modbus = c.kind === "modbus", m = c.modbus || {};
    const enocean = c.kind === "enocean", eo = c.enocean || {};
    return html`
      <p class="crumb"><a href="#/connections">${t("connectionsTitle")}</a> › ${c.name}</p>
      <div class="head" style="margin-top:12px">
        <div class="row" style="justify-content:flex-start"><h1>${c.name}</h1>
          <span class="chip ${stateClass}"><span class="dot"></span>${t(stateKey)}</span>
          ${c.kept_open ? html`<span class="chip info">${t("keptOpen")}</span>` : ""}
          <span class="hint" style="font-size:13px">${t("clientsLine", { n: c.clients.length, m: c.max_clients })}</span>
          ${c.trace !== "off" ? html`<a class="chip info" href="#/trace/${c.id}" style="text-decoration:none"><span class="dot"></span>${t("recording", { m: t(`${modbus ? "trmb" : "tr"}_${c.trace}`) })}</a>` : ""}
          ${enocean ? html`<span class="chip">${c.esp_protocol.toUpperCase()}</span>${eo.base_id ? html`<span class="chip info mono">Base-ID ${eo.base_id}</span>` : ""}` : ""}</div>
        <div class="row">
          <a class="btn btn-s" href="#/trace/${c.id}">${t("navTrace")}</a>
          <a class="btn btn-s" href="#/edit/${c.id}">${t("edit")}</a>
          ${toggle(c.enabled, t("switchLabel", { name: c.name }), (v) => this._enable(c, v), s.source === "custom" && c.kind === "serial")}
        </div>
      </div>
      <div class="cols">
        <div class="main-col">
          ${enocean ? issuesCard(issues(c, s.capture)) : ""}
          ${enocean ? meterCards(c) : ""}
          ${this._live(c.kind)}
          ${modbus ? "" : enocean ? html`<dp-enocean-tools .connection=${c} .capture=${s.capture}></dp-enocean-tools>` : this.state.source === "custom" ? "" : this._tools(c)}
          ${c.clients.length || (modbus && (m.units || []).length) ? html`<section class="card" aria-labelledby="t-clients">
            <div class="row"><h2 id="t-clients">${t(modbus ? "mbClientsUnits" : "clients")}</h2><span class="hint" style="font-size:13px">${t("clientsOf", { n: c.clients.length, m: c.max_clients })}</span></div>
            ${c.clients.length && modbus ? html`<div class="scroll"><table style="min-width:520px"><thead><tr>
              <th>${t("clientTh")}</th><th>${t("sinceTh")}</th><th style="text-align:right">${t("mbRequests")}</th><th style="text-align:right" title=${t("mbTipFailed")}>${t("mbFailed")}</th><th style="text-align:right" title=${t("mbTipBlocked")}>${t("mbBlocked")}</th></tr></thead>
              <tbody>${c.clients.map((cl) => html`<tr><td class="mono" style="font-size:12px">${cl.address}</td><td>${cl.since ? fmtTime(cl.since) : "–"}</td>
                <td style="text-align:right">${cl.requests}</td><td style="text-align:right;${cl.failed ? "color:var(--warn)" : ""}">${cl.failed}</td><td style="text-align:right">${cl.blocked}</td></tr>`)}</tbody></table></div>`
            : c.clients.length && enocean ? html`<div class="scroll"><table style="min-width:520px"><thead><tr>
              <th>${t("clientTh")}</th><th>${t("sinceTh")}</th><th>${t("eoReplay")}</th><th style="text-align:right">${t("toClient")}</th><th style="text-align:right">${t("fromClient")}</th></tr></thead>
              <tbody>${c.clients.map((cl) => html`<tr><td class="mono" style="font-size:12px">${cl.address}</td><td>${cl.since ? fmtTime(cl.since) : "–"}</td>
                <td>${cl.replay ? html`<span class="chip info">${t("eoReplayChip")}</span>` : "–"}</td>
                <td style="text-align:right">${fmtBytes(cl.bytes_to_client)}</td><td style="text-align:right">${fmtBytes(cl.bytes_from_client)}</td></tr>`)}</tbody></table></div>`
            : c.clients.length ? html`<div class="scroll"><table style="min-width:520px"><thead><tr>
              <th>${t("clientTh")}</th><th>${t("sinceTh")}</th><th style="text-align:right">${t("toClient")}</th><th style="text-align:right">${t("fromClient")}</th><th style="text-align:right">${t("queued")}</th></tr></thead>
              <tbody>${c.clients.map((cl) => html`<tr>
                <td class="mono" style="font-size:12px">${cl.address} ${cl.stuck ? html`<span class="chip bad">${t("stuck", { a: "" })}</span>` : ""}</td>
                <td>${cl.since ? fmtTime(cl.since) : "–"}</td><td style="text-align:right">${fmtBytes(cl.bytes_to_client)}</td>
                <td style="text-align:right">${fmtBytes(cl.bytes_from_client)}</td><td style="text-align:right">${fmtBytes(cl.queued)}</td></tr>`)}</tbody></table></div>`
              : html`<p class="hint" style="font-size:14px">${t("noClients")}</p>`}
          ${modbus && (m.units || []).length ? html`<div style="display:flex;flex-direction:column;gap:8px;border-top:1px solid var(--line-2);padding-top:12px"><div class="row" style="margin-top:6px"><h3 id="t-units" style="font-size:14px;font-weight:500;margin:0">${t("mbUnits")}</h3><span class="hint" style="font-size:13px">${t("mbUnitsSub")}</span></div>
            <div class="scroll"><table style="min-width:520px"><thead><tr><th>${t("mbUnit")}</th><th style="text-align:right">${t("mbRequests")}</th>
              <th style="text-align:right" title=${t("mbTipExceptions")}>${t("mbExceptions")}</th><th style="text-align:right" title=${t("mbTipFailed")}>${t("mbFailed")}</th><th style="text-align:right">${t("mbTimeShort")}</th><th>${t("mbLastAnswer")}</th></tr></thead>
              <tbody>${m.units.map((u) => html`<tr><td class="mono">${u.unit}</td><td style="text-align:right">${u.requests}</td>
                <td style="text-align:right">${u.exceptions}</td><td style="text-align:right;${u.failed ? "color:var(--warn)" : ""}">${u.failed}</td>
                <td style="text-align:right">${u.answered ? `${u.time_avg_ms} ms` : "–"}</td><td>${u.last_answer ? fmtAgo(u.last_answer) : t("never")}</td></tr>`)}</tbody></table></div></div>` : ""}
          </section>` : ""}
          ${modbus ? this._haSnippet(c) : ""}
          <section class="card" aria-labelledby="t-conf">
            <div class="row"><h2 id="t-conf">${t("connectionCard")}</h2><a href="#/edit/${c.id}" style="font-size:13px">${t("edit")}</a></div>
            ${enocean ? html`<div class="kv">
              <span>${t("eoTemplate")}</span><span>${t(`tpl_${c.template}`)}</span>
              <span>${t("eoGateway")}</span><span class="mono" style="font-size:13px;overflow-wrap:anywhere">${c.esp_protocol.toUpperCase()} · ${proxyTarget(c)}${c.link === "serial" ? ` · ${c.baud}` : ""}</span>
              ${c.link === "serial" ? html`<span>${t("resolved")}</span><span class="mono" style="font-size:13px">${c.tty || "–"}</span>` : ""}
              <span>${t("network")}</span><span>Port ${c.port}</span>
              <span>${t("who")}</span><span>${who(c, s)}</span>
              <span>${t("eoGap")}</span><span>${c.send_gap_ms} ms</span>
              <span>${t("eoReplay")}</span><span>${t("eoReplayConf", { n: c.replay_size, m: Math.round(c.replay_max_age_s / 60) })}${c.replay_persist ? ` · ${t("eoPersisted")}` : ""}</span>
            </div>` : modbus ? html`<div class="kv">
              <span>${t("mbKind")}</span><span>${t(`link_${c.link}`)}</span>
              <span>${t("mbAddrOfDevice")}</span><span class="mono" style="font-size:13px;overflow-wrap:anywhere">${proxyTarget(c)}${c.link === "rtu" ? ` · ${fmtSerial(c)}` : ""}</span>
              ${c.link === "rtu" ? html`<span>${t("resolved")}</span><span class="mono" style="font-size:13px">${c.tty || "–"}</span>` : ""}
              ${c.device_connections > 1 ? html`<span>${t("mbLinksShort")}</span><span>${t("mbLinksVal", { o: m.links_open ?? 0, n: c.device_connections })}</span>` : ""}
              <span>${t("mbTimeLimit")}</span><span>${t("mbConf2", { s: Math.round(c.request_timeout_ms / 100) / 10, n: c.retries })}
${c.request_gap_ms ? ` · ${t("mbGapShort", { ms: c.request_gap_ms })}` : ""}</span>
              <span>${t("mbClientPort")}</span><span>${c.port}</span>
              <span>${t("who")}</span><span>${who(c, s)}</span>
              ${c.cache_ms ? html`<span>${t("mbCacheShort")}</span><span>${c.cache_ms} ms</span>` : ""}
              ${c.unit_map ? html`<span>${t("mbUnitMapShort")}</span><span class="mono">${c.unit_map}</span>` : ""}

              ${c.probe_seconds ? html`<span>${t("mbProbe")}</span><span>${t("mbProbeVal", { s: c.probe_seconds, u: c.probe_unit, f: c.probe_function, a: c.probe_address })}</span>` : ""}

              <span>${t("mbWrite")}</span>
<span>${t(`wa_${c.write_access}`)}${c.write_access === "listed" ? html` · <span class="mono">${c.write_clients}</span>` : ""}</span>

            </div>` : html`<div class="kv">
              <span>${t("device")}</span><span class="mono" style="font-size:13px;overflow-wrap:anywhere">${c.device}</span>
              <span>${t("resolved")}</span><span class="mono" style="font-size:13px">${c.tty || "–"}</span>
              ${usb ? html`<span>${t("usb")}</span><span>${[usb.manufacturer, usb.product].filter(Boolean).join(" · ") || `${usb.vendor_id}:${usb.product_id}`}${usb.serial ? ` · ${t("serialNo")} ${usb.serial}` : ""}${usb.driver ? ` · ${usb.driver}` : ""}</span>` : ""}
              <span>${t("interface")}</span><span>${fmtSerial(c)}${c.rtscts ? " · RTS/CTS" : ""}${c.xonxoff ? " · XON/XOFF" : ""}${c.local ? ` · ${t("ifLocal")}` : ""}</span>
              <span>${t("network")}</span><span>${c.mode} · Port ${c.port}</span>
              <span>${t("who")}</span><span>${who(c, s)}</span>
            </div>`}
          </section>
          ${modbus ? this._modbusTools(c) : ""}
        </div>
        <aside class="side-col">
          ${this._addresses(c)}
          ${modbus ? this._modbusCard(m) : enocean ? statusCard(c) : html`<section class="card" aria-labelledby="t-line">
            <div class="row"><h2 id="t-line">${t("line")}</h2>
              ${le && !Object.values(le).some(Boolean) ? html`<span class="chip ok">${t("noLineErrors")}</span>` : ""}</div>
            ${le ? html`<div class="counters">
              ${[["frame", le.frame], ["parity", le.parity], ["overrun", le.overrun], ["brk", le.break], ["bufOverrun", le.buffer_overrun]].map(([k, v]) =>
                html`<div class="well"><span class="hint">${t(k)}</span><b style=${v ? "color:var(--warn)" : ""}>${v}</b></div>`)}</div>`
              : ""}
            <p class="hint" style="margin:0">${le || !c.clients.length || c.line_errors !== null ? t("lineClosed") : t("lineUnsupported")}</p>
          </section>`}
          ${modbus ? "" : html`<section class="card" aria-labelledby="t-rate">
            <div class="row"><h2 id="t-rate">${t("dataFromDevice")}</h2><b style="font-size:18px;font-weight:500">${fmtRate(c.rate_from_device)}</b></div>
            ${this._sparkline()}
            <div class="row hint" style="font-size:12px"><span>${t("sparkOld")}</span><span>${t("sparkPeak", { r: fmtRate(Math.max(...this._samples, 0)) })}</span><span>${t("sparkNow")}</span></div>
            <div class="row hint"><span>${t("lastData")}: ${c.last_data ? fmtAgo(c.last_data) : t("never")}</span><span>${t("sinceStart", { b: fmtBytes(c.bytes_from_device) })}</span></div>
          </section>`}
          <section class="card" aria-labelledby="t-recent">
            <div class="row"><h2 id="t-recent">${t("recent")}</h2><a href="#/events/${c.id}" style="font-size:13px">${t("allEventsOf", { n: c.name })}</a></div>
            <ol>${recent.map((e) => html`<li><span class="dot" style="color:${e.level === "warning" ? "var(--warn)" : e.level === "error" ? "var(--bad)" : "var(--ok)"}"></span>
              <div><div>${eventText(e)}${e.count > 1 ? html` <span class="chip">${t("summed", { n: e.count })}</span>` : ""}</div><div class="hint">${fmtTime(e.ts)}</div></div></li>`)}</ol>
          </section>
        </aside>
      </div>`;
  }
}
