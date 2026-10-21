import { css, html, svg } from "lit";
import { api, saveConnection, toConnection } from "../api.js";
import { Page } from "../app.js";
import { eventText, t } from "../i18n.js";
import { confirmDialog, connectionState, copyText, fmtAgo, fmtBytes, fmtRate, fmtSerial, fmtTime, modbusTarget, toggle } from "../ui.js";

const LIVE_MS = 1000;
const SAMPLES = 90; // 3 minutes of state polls

export class DetailPage extends Page {
  static properties = {
    state: { attribute: false }, events: { attribute: false }, connectionId: {},
    chunks: { state: true }, paused: { state: true }, ascii: { state: true }, copied: { state: true },
    meter: { state: true }, job: { state: true },
  };

  static styles = [...Page.styles, css`
    .kv { display: grid; grid-template-columns: minmax(110px, 170px) minmax(0, 1fr); gap: 10px 16px; }
    .kv > :nth-child(odd) { color: var(--muted); }
    .counters { display: grid; grid-template-columns: repeat(auto-fit, minmax(90px, 1fr)); gap: 10px; }
    .counters b { display: block; font-size: 20px; font-weight: 500; }
    .live { max-height: 340px; overflow: auto; }
    .live table { font-family: "Roboto Mono", ui-monospace, Menlo, monospace; font-size: 12px; color: var(--code-text); }
    .live td { border: none; padding: 2px 8px; white-space: pre; }
    .dir { display: inline-block; min-width: 30px; text-align: center; border-radius: 6px; padding: 0 6px; }
    .rx { background: #1f3a52; color: #9ccbf0; } .tx { background: #4a3a1c; color: #f4c77d; } .mark { background: #2a3038; color: #c5ccd5; }
    ol { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 12px; }
    li { display: flex; gap: 10px; } li .dot { margin-top: 6px; }
  `];

  constructor() {
    super();
    this.chunks = [];
    this.paused = false;
    this.ascii = true;
    this._samples = [];
    this._after = 0;
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
    if (changed.has("connectionId")) { this.chunks = []; this._after = 0; this._samples = []; }
    if (changed.has("state")) {
      const c = this.connection(this.connectionId);
      if (c) this._samples = [...this._samples, c.rate_from_device].slice(-SAMPLES);
    }
  }

  async _poll() {
    if (this.paused || !this.connectionId) return;
    try {
      const fresh = await api(`api/live/${this.connectionId}?after=${this._after}`);
      if (fresh.length) {
        this._after = fresh[fresh.length - 1].seq;
        this.chunks = [...this.chunks, ...fresh].slice(-300);
      }
    } catch { /* shown by the frame */ }
  }

  async _enable(c, enabled) {
    try {
      await api(`api/connections/${c.id}/enabled`, { method: "POST", body: { enabled } });
      this.refresh();
    } catch (err) { this.toast(`${t("error")}: ${err.message}`); }
  }

  async _checkMeter() {
    try { this.meter = await api(`api/tools/${this.connectionId}/meter`); } catch (err) { this.toast(`${t("error")}: ${err.message}`); }
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

  _tools(c) {
    const m = this.meter, job = this.job;
    const best = job && job.state === "done" ? job.results.filter((r) => r.score >= 0.6) : [];
    const fmt = (r) => `${r.baud} ${r.data_bits}${r.parity.toUpperCase()}${r.stop_bits}`;
    const value = (r) => typeof r.value === "number" && r.unit === "Wh" ? `${(r.value / 1000).toLocaleString(undefined, { maximumFractionDigits: 3 })} kWh` : `${r.value} ${r.unit}`;
    return html`<section class="card" aria-labelledby="t-tools">
      <h2 id="t-tools">${t("tools")}</h2>
      <div class="row"><div><b style="font-weight:500">${t("meterCheck")}</b><p class="hint">${t("meterCheckSub")}</p></div>
        <button class="btn btn-s" @click=${this._checkMeter}>${t("meterCheck")}</button></div>
      ${m ? m.bytes ? html`<div class="well" style="display:flex;flex-direction:column;gap:8px">
          <div style="display:flex;flex-wrap:wrap;gap:6px"><span class="chip ${m.protocol === "unknown" ? "warn" : "info"}">${t(`proto_${m.protocol}`)}</span>
            ${m.telegrams ? html`<span class="chip">${t("telegrams", { n: m.telegrams })}</span>
              <span class="chip ${m.valid === m.telegrams ? "ok" : "warn"}">${t(m.protocol === "sml" ? "validCrc" : "validD0", { n: m.valid })}</span>` : ""}</div>
          ${m.readings.length ? html`<table><tbody>${m.readings.slice(0, 12).map((r) => html`<tr><td class="mono" style="font-size:12px">${r.obis}</td><td>${r.name ? t(`obis_${r.obis}`) : ""}</td><td style="text-align:right">${value(r)}</td></tr>`)}</tbody></table>` : ""}
        </div>` : html`<p class="hint">${t("noData30")}</p>` : ""}
      <div class="row" style="border-top:1px solid var(--line-2);padding-top:12px"><div><b style="font-weight:500">${t("baudDetect")}</b><p class="hint">${t("baudDetectSub")}</p></div>
        <button class="btn btn-s" ?disabled=${job && job.state === "running"} @click=${this._detect}>${t("baudDetect")}</button></div>
      ${job ? job.state === "running" ? html`<p class="hint" role="status">${t("detecting", { d: job.done, t: job.total || "…" })}</p>`
        : job.state === "failed" ? html`<div class="note bad">${t("error")}: ${job.error}</div>`
        : best.length ? html`<div class="note ok"><b>${t("detected", { b: best[0].baud, f: fmt(best[0]).split(" ")[1] })}</b> · ${t(`proto_${best[0].protocol}`)}</div>
          <div class="hint">${t("candidates")}:</div>
          ${best.slice(0, 3).map((r) => html`<div class="row well"><span class="mono">${fmt(r)}</span><span class="hint">${t("score")} ${Math.round(r.score * 100)} %</span>
            <button class="btn btn-g" @click=${() => this._useCandidate(c, r)}>${t("applyThis")}</button></div>`)}`
        : html`<div class="note warn">${t("noDetect")}</div>` : ""}
    </section>`;
  }

  async _copy(key, text) {
    if (await copyText(text)) { this.copied = key; setTimeout(() => { if (this.copied === key) this.copied = ""; }, 2000); }
  }

  _live(modbus) {
    const rows = this.chunks.slice(-120).reverse(); // newest first, like the event log
    return html`<section class="card" aria-labelledby="t-live">
      <div class="row"><div><h2 id="t-live">${t("live")}</h2><p class="hint">${t(modbus ? "liveSubMb" : "liveSub")}</p></div>
        <div style="display:flex;gap:4px">
          ${modbus ? "" : html`<button class="btn btn-g" aria-pressed=${this.ascii ? "true" : "false"} @click=${() => { this.ascii = !this.ascii; }}>${this.ascii ? t("hexOnly") : t("hexAscii")}</button>`}
          <button class="btn btn-g" @click=${() => { this.paused = !this.paused; }}>${this.paused ? t("resume") : t("pause")}</button>
        </div></div>
      ${rows.length ? html`<div class="code live" style="padding:8px 4px"><table><tbody>
        ${rows.map((ch) => html`<tr>
          <td style="color:#8f9ba8">${new Date(ch.ts * 1000).toLocaleTimeString(undefined, { hour12: false })}.${String(Math.floor(ch.ts * 1000) % 1000).padStart(3, "0")}</td>
          <td><span class="dir ${ch.direction === "rx" ? "rx" : ch.direction === "tx" ? "tx" : "mark"}">${ch.direction.toUpperCase()}</span></td>
          ${ch.info ? html`<td style="color:#9fb3c8">${ch.info}</td>` : ""}
          <td>${ch.direction === "open" || ch.direction === "close" ? ch.text : ch.hex}</td>
          ${!ch.info && this.ascii && ch.hex ? html`<td style="color:#9fb3c8">${ch.text.replace(/[^\x20-\x7e]/g, ".")}</td>` : ""}
        </tr>`)}</tbody></table></div>` : html`<div class="well hint" style="font-size:14px">${t(modbus ? "liveEmptyMb" : "liveEmpty")}</div>`}
    </section>`;
  }

  _modbusCard(m) {
    const reach = m.reachable === true ? ["mbReachable", "ok"] : m.reachable === false ? ["mbUnreachable", "bad"] : ["mbUnknown", ""];
    const counters = [["mbRequests", m.requests], ["mbAnswered", m.answered], ["mbExceptions", m.exceptions], ["mbTimeouts", m.timeouts], ["mbErrors", m.errors], ["mbQueue", `${m.queue ?? 0} / ${m.queue_max ?? 0}`]];
    if (m.blocked) counters.push(["mbBlocked", m.blocked]);
    return html`<section class="card" aria-labelledby="t-mb">
      <div class="row"><h2 id="t-mb">${t("mbStats")}</h2><span class="chip ${reach[1]}"><span class="dot"></span>${t(reach[0])}</span></div>
      <div class="counters">${counters.map(([k, v]) => html`<div class="well"><span class="hint">${t(k)}</span>
        <b style=${(k === "mbTimeouts" || k === "mbErrors") && v ? "color:var(--warn)" : ""}>${v ?? 0}</b></div>`)}</div>
      <div class="row hint"><span>${t("mbTime")}</span><span>${m.answered ? t("mbTimeVal", { a: m.time_avg_ms, m: m.time_max_ms }) : "–"}</span></div>
      <div class="row hint"><span>${t("mbLastAnswer")}</span><span>${m.last_answer ? fmtAgo(m.last_answer) : t("never")}</span></div>
      ${m.listen_error ? html`<div class="note bad">${t("mbListenError", { e: m.listen_error })}</div>` : ""}
      ${m.last_error ? html`<div class="note ${m.reachable === false ? "bad" : "warn"}">${t("mbLastError")}: ${m.last_error}${m.last_error_at ? ` · ${fmtTime(m.last_error_at, true, true)}` : ""}</div>` : ""}
    </section>`;
  }

  _sparkline() {
    const values = this._samples.length > 1 ? this._samples : [0, 0];
    const max = Math.max(...values, 1);
    const step = 300 / (values.length - 1);
    const points = values.map((v, i) => `${(i * step).toFixed(1)},${(66 - (v / max) * 56).toFixed(1)}`);
    return html`<svg viewBox="0 0 300 70" width="100%" height="70" role="img" aria-label=${t("dataFromDevice")}>
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
    return html`
      <p class="crumb"><a href="#/connections">${t("connectionsTitle")}</a> › ${c.name}</p>
      <div class="head" style="margin-top:12px">
        <div class="row" style="justify-content:flex-start"><h1>${c.name}</h1>
          <span class="chip ${stateClass}"><span class="dot"></span>${t(stateKey)}</span>
          ${c.kept_open ? html`<span class="chip info">${t("keptOpen")}</span>` : ""}</div>
        <div class="row">
          <a class="btn btn-s" href="#/trace/${c.id}">${t("navTrace")}</a>
          <a class="btn btn-s" href="#/edit/${c.id}">${t("edit")}</a>
          ${toggle(c.enabled, t("switchLabel", { name: c.name }), (v) => this._enable(c, v), s.source === "custom" && !modbus)}
        </div>
      </div>
      <div class="cols">
        <div class="main-col">
          ${this._live(modbus)}
          ${this.state.source === "custom" || modbus ? "" : this._tools(c)}
          <section class="card" aria-labelledby="t-clients">
            <div class="row"><h2 id="t-clients">${t("clients")}</h2><span class="hint" style="font-size:13px">${t("clientsOf", { n: c.clients.length, m: c.max_clients })}</span></div>
            ${c.clients.length && modbus ? html`<div class="scroll"><table style="min-width:520px"><thead><tr>
              <th>${t("clientTh")}</th><th>${t("sinceTh")}</th><th style="text-align:right">${t("mbRequests")}</th><th style="text-align:right">${t("mbFailed")}</th><th style="text-align:right">${t("mbBlocked")}</th></tr></thead>
              <tbody>${c.clients.map((cl) => html`<tr><td class="mono" style="font-size:12px">${cl.address}</td><td>${cl.since ? fmtTime(cl.since) : "–"}</td>
                <td style="text-align:right">${cl.requests}</td><td style="text-align:right;${cl.failed ? "color:var(--warn)" : ""}">${cl.failed}</td><td style="text-align:right">${cl.blocked}</td></tr>`)}</tbody></table></div>`
            : c.clients.length ? html`<div class="scroll"><table style="min-width:520px"><thead><tr>
              <th>${t("clientTh")}</th><th>${t("sinceTh")}</th><th style="text-align:right">${t("toClient")}</th><th style="text-align:right">${t("fromClient")}</th><th style="text-align:right">${t("queued")}</th></tr></thead>
              <tbody>${c.clients.map((cl) => html`<tr>
                <td class="mono" style="font-size:12px">${cl.address} ${cl.stuck ? html`<span class="chip bad">${t("stuck", { a: "" })}</span>` : ""}</td>
                <td>${cl.since ? fmtTime(cl.since) : "–"}</td><td style="text-align:right">${fmtBytes(cl.bytes_to_client)}</td>
                <td style="text-align:right">${fmtBytes(cl.bytes_from_client)}</td><td style="text-align:right">${fmtBytes(cl.queued)}</td></tr>`)}</tbody></table></div>`
              : html`<p class="hint" style="font-size:14px">${t("noClients")}</p>`}
          </section>
          <section class="card" aria-labelledby="t-addr">
            <h2 id="t-addr">${t("addresses")}</h2>
            ${c.addresses.map((a) => html`<div class="well row">
              <div style="min-width:0"><div class="hint">${t(`target_${a.target}`)}</div>
                ${a.reachable ? Object.entries(a.urls).map(([k, u]) => html`<div class="row" style="justify-content:flex-start;gap:4px">
                  <span class="mono" style="font-size:13px;overflow-wrap:anywhere">${u}</span>
                  <button class="btn btn-g" style="min-height:32px" @click=${() => this._copy(`${a.target}${k}`, u)}>${this.copied === `${a.target}${k}` ? t("copied") : t("copy")}</button></div>`)
                  : html`<div class="hint">${a.host ? t("notReachable") : t("lanUnknown")}</div>`}
              </div></div>`)}
          </section>
          <section class="card" aria-labelledby="t-conf">
            <div class="row"><h2 id="t-conf">${t("configuration")}</h2><a href="#/edit/${c.id}" style="font-size:13px">${t("edit")}</a></div>
            ${modbus ? html`<div class="kv">
              <span>${t("mbLink")}</span><span>${t(`link_${c.link}`)}</span>
              <span>${t("device")}</span><span class="mono" style="font-size:13px;overflow-wrap:anywhere">${modbusTarget(c)}${c.link === "rtu" ? ` · ${fmtSerial(c)}` : ""}</span>
              ${c.link === "rtu" ? html`<span>${t("resolved")}</span><span class="mono" style="font-size:13px">${c.tty || "–"}</span>` : ""}
              <span>${t("mbProxy")}</span><span>${t("mbConf", { ms: c.request_timeout_ms, n: c.retries })}${c.request_gap_ms ? ` · ${t("mbGapShort", { ms: c.request_gap_ms })}` : ""}</span>
              <span>${t("network")}</span><span>Modbus TCP · Port ${c.port} · ${c.bind || t(`listen_${s.settings.listen}`)}</span>
              <span>${t("mbWrite")}</span><span>${t(`wa_${c.write_access}`)}${c.write_access === "listed" ? html` · <span class="mono">${c.write_clients}</span>` : ""}</span>

            </div>` : html`<div class="kv">
              <span>${t("device")}</span><span class="mono" style="font-size:13px;overflow-wrap:anywhere">${c.device}</span>
              <span>${t("resolved")}</span><span class="mono" style="font-size:13px">${c.tty || "–"}</span>
              ${usb ? html`<span>${t("usb")}</span><span>${[usb.manufacturer, usb.product].filter(Boolean).join(" · ") || `${usb.vendor_id}:${usb.product_id}`}${usb.serial ? ` · ${t("serialNo")} ${usb.serial}` : ""}${usb.driver ? ` · ${usb.driver}` : ""}</span>` : ""}
              <span>${t("interface")}</span><span>${fmtSerial(c)}${c.rtscts ? " · RTS/CTS" : ""}${c.xonxoff ? " · XON/XOFF" : ""}${c.local ? " · local" : ""}</span>
              <span>${t("network")}</span><span>${c.mode} · Port ${c.port} · ${c.bind || t(`listen_${s.settings.listen}`)}</span>
            </div>`}
          </section>
        </div>
        <aside class="side-col">
          ${modbus ? this._modbusCard(m) : html`<section class="card" aria-labelledby="t-line">
            <div class="row"><h2 id="t-line">${t("line")}</h2>
              ${le && !Object.values(le).some(Boolean) ? html`<span class="chip ok">${t("noLineErrors")}</span>` : ""}</div>
            ${le ? html`<div class="counters">
              ${[["frame", le.frame], ["parity", le.parity], ["overrun", le.overrun], ["brk", le.break], ["bufOverrun", le.buffer_overrun]].map(([k, v]) =>
                html`<div class="well"><span class="hint">${t(k)}</span><b style=${v ? "color:var(--warn)" : ""}>${v}</b></div>`)}</div>`
              : html`<p class="hint">${c.line_errors === null && c.clients.length ? t("lineUnsupported") : t("lineClosed")}</p>`}
          </section>`}
          <section class="card" aria-labelledby="t-rate">
            <div class="row"><h2 id="t-rate">${t("dataFromDevice")}</h2><b style="font-size:18px;font-weight:500">${fmtRate(c.rate_from_device)}</b></div>
            ${this._sparkline()}
            <div class="row hint"><span>${t("lastData")}: ${c.last_data ? fmtAgo(c.last_data) : t("never")}</span><span>${fmtBytes(c.bytes_from_device)}</span></div>
          </section>
          <section class="card" aria-labelledby="t-recent">
            <div class="row"><h2 id="t-recent">${t("recent")}</h2><a href="#/events" style="font-size:13px">${t("allEvents")}</a></div>
            <ol>${recent.map((e) => html`<li><span class="dot" style="color:${e.level === "warning" ? "var(--warn)" : e.level === "error" ? "var(--bad)" : "var(--ok)"}"></span>
              <div><div>${eventText(e)}${e.count > 1 ? html` <span class="chip">${t("summed", { n: e.count })}</span>` : ""}</div><div class="hint">${fmtTime(e.ts)}</div></div></li>`)}</ol>
          </section>
        </aside>
      </div>`;
  }
}
