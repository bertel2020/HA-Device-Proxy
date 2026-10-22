import { css, html } from "lit";
import { api, saveConnection, toConnection, url } from "../api.js";
import { Page } from "../app.js";
import { t } from "../i18n.js";
import { confirmDialog, copyText, fmtBytes, fmtTime, icon, navigate } from "../ui.js";

const MODES = ["off", "rx", "tx", "both"];
const KEEP = 400;
const PATH = "/addon_configs/…_device_proxy/trace/";

/** Items joined sixteen to a line, so hex and ASCII break at the same bytes. */
const lines16 = (items, sep) => Array.from({ length: Math.ceil(items.length / 16) }, (_, i) => items.slice(i * 16, i * 16 + 16).join(sep)).join("\n");

export class TracePage extends Page {
  static properties = { state: { attribute: false }, selected: {}, chunks: { state: true }, paused: { state: true }, ascii: { state: true }, copied: { state: true } };

  static styles = [...Page.styles, css`
    .chips { display: flex; gap: 6px; overflow-x: auto; padding: 2px 2px 6px; margin-bottom: 14px; scrollbar-width: thin; }
    .chips button { display: inline-flex; align-items: center; gap: 6px; flex: none; white-space: nowrap; min-height: 36px; padding: 0 14px; border-radius: 18px; cursor: pointer; font: inherit; font-size: 14px; font-weight: 500;
      border: 1px solid var(--input-line); background: var(--surface); color: var(--muted); }
    .chips button[aria-pressed="true"] { background: var(--accent-soft); color: var(--accent-hover); border-color: var(--accent); }
    .chips .dot { width: 8px; height: 8px; color: var(--accent); }
    .modes { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; padding: 12px 16px; border-bottom: 1px solid var(--line); }
    .view { max-height: 460px; overflow: auto; padding: 8px 4px; }
    .view table { width: auto; font-family: "Roboto Mono", ui-monospace, Menlo, monospace; font-size: 12px; color: var(--code-text); }
    .view td { border: none; padding: 2px 8px; white-space: pre; vertical-align: top; }
    .view td.hex, .view td.asc { white-space: pre; }
    .dir { display: inline-block; min-width: 78px; white-space: nowrap; text-align: center; border-radius: 6px; padding: 0 6px; }
    .rx { background: #1f3a52; color: #9ccbf0; } .tx { background: #4a3a1c; color: #f4c77d; } .mark { background: #2a3038; color: #c5ccd5; }
  `];

  constructor() {
    super();
    this.chunks = [];
    this.paused = false;
    this.ascii = true;
    this._after = 0;
  }

  connectedCallback() {
    super.connectedCallback();
    this._timer = setInterval(() => this._poll(), 1000);
  }

  disconnectedCallback() {
    super.disconnectedCallback();
    clearInterval(this._timer);
  }

  willUpdate(changed) {
    if (changed.has("selected")) { this.chunks = []; this._after = 0; }
    if (!this.selected && this.state?.connections.length) this.selected = this.state.connections[0].id;
  }

  async _poll() {
    if (this.paused || !this.selected || document.hidden) return;
    try {
      const fresh = await api(`api/live/${this.selected}?after=${this._after}`);
      if (fresh.length) { this._after = fresh[fresh.length - 1].seq; this.chunks = [...this.chunks, ...fresh].slice(-KEEP); }
    } catch { /* shown by the frame */ }
  }

  async _mode(c, trace) {
    if (c.trace === trace) return;
    try {
      await saveConnection({ ...toConnection(c), trace });
      this.toast(trace === "off" ? t("recStopped", { n: c.name }) : t("recStarted", { n: c.name, m: this._label(c, trace) }));
      this.refresh();
    } catch (err) { this.toast(`${t("error")}: ${err.message}`); }
  }

  _label(c, mode) { return t(c.kind === "modbus" ? `trmb_${mode}` : `tr_${mode}`); }

  async _copyPath() {
    if (await copyText(PATH)) { this.copied = true; setTimeout(() => { this.copied = false; }, 1500); }
  }

  async _delete(name) {
    if (!(await confirmDialog(this, t("deleteFile", { n: name }), t("delete")))) return;
    try { await api(`api/trace/${encodeURIComponent(name)}`, { method: "DELETE" }); this.refresh(); } catch (err) { this.toast(`${t("error")}: ${err.message}`); }
  }

  render() {
    const s = this.state;
    const current = this.connection(this.selected);
    const files = s.trace_files;
    const rows = this.chunks.slice(-200);
    const file = current && current.trace !== "off" ? files.filter((f) => f.connection === current.id).sort((a, b) => b.modified - a.modified)[0] : null;
    const locked = s.source === "custom" && current?.kind === "serial";
    const name = (id) => s.connections.find((c) => c.id === id)?.name;
    return html`
      <div class="head"><div><h1>${t("traceTitle")}</h1><p class="sub">${t("traceSub")}</p></div></div>
      <div class="chips" role="group" aria-label=${t("navConnections")}>${s.connections.map((c) => html`<button type="button" aria-pressed=${c.id === this.selected ? "true" : "false"}
        title=${c.trace === "off" ? c.name : `${c.name} · ${t("recording", { m: this._label(c, c.trace) })}`} @click=${() => navigate(`#/trace/${c.id}`)}>${c.trace === "off" ? "" : html`<span class="dot" role="img" aria-label=${t("recording", { m: this._label(c, c.trace) })}></span>`}${c.name}</button>`)}</div>
      <div class="cols">
        <div class="main-col">
          <section class="card" style="padding:0;gap:0;overflow:hidden" aria-labelledby="t-view">
            <div class="row" style="padding:14px 16px;border-bottom:1px solid var(--line)">
              <div><h2 id="t-view">${t("liveView")}${current ? html` · ${current.name}` : ""}</h2>
                <p class="hint" style="margin:2px 0 0">${t("liveCap", { n: KEEP })}${this.chunks.length ? ` · ${t("linesShown", { n: rows.length })}` : ""}${this.paused ? ` · ${t("paused")}` : ""}</p></div>
              <div style="display:flex;gap:4px;flex-wrap:wrap">
                <div class="seg" role="group" aria-label=${t("liveView")}>${[[false, "hexOnly"], [true, "hexAscii"]].map(([v, k]) => html`<button type="button" aria-pressed=${this.ascii === v ? "true" : "false"} @click=${() => { this.ascii = v; }}>${t(k)}</button>`)}</div>
                <button class="btn btn-g" @click=${() => { this.paused = !this.paused; }}>${this.paused ? t("resume") : t("pause")}</button>
                <button class="btn btn-g" ?disabled=${!this.chunks.length} @click=${() => { this.chunks = []; }}>${t("clearView")}</button></div></div>
            ${current ? html`<div class="modes"><span style="font-weight:500">${t("recMode")}</span>
              <div class="seg" role="group" aria-label="${t("traceMode")} ${current.name}">${MODES.map((m) => html`<button type="button" aria-pressed=${current.trace === m ? "true" : "false"}
                ?disabled=${locked} @click=${() => this._mode(current, m)}>${m === "off" ? t("off") : this._label(current, m)}</button>`)}</div>
              <span class="hint">${t("recNote")}</span>
              ${file ? html`<span class="hint" style="flex-basis:100%">${t("recFile")}: <span class="mono">${file.name}</span> · ${fmtBytes(file.size)}
                <a href=${url(`api/trace/${encodeURIComponent(file.name)}`)} download aria-label="${file.name} ${t("download")}">${t("download")}</a></span>` : ""}</div>` : ""}
            ${rows.length ? html`<div class="code view" style="border-radius:0"><table><tbody>${rows.slice().reverse().map((ch) => html`<tr>
              <td style="color:#8f9ba8">${this._time(ch.ts)}</td>
              <td><span class="dir ${ch.direction === "rx" ? "rx" : ch.direction === "tx" ? "tx" : "mark"}">${ch.direction === "rx" || ch.direction === "tx" ? t(`${current && current.kind === "modbus" ? "dirmb" : "dir"}_${ch.direction}`) : ch.direction.toUpperCase()}</span></td>
              ${ch.info ? html`<td style="color:#9fb3c8">${ch.info}</td>` : ""}<td class="hex">${ch.hex ? lines16(ch.hex.split(" "), " ") : ch.text}</td>${!ch.info && this.ascii && ch.hex ? html`<td class="asc" style="color:#9fb3c8">${lines16(ch.text.replace(/[^\x20-\x7e]/g, ".").split(""), "")}</td>` : ""}</tr>`)}</tbody></table></div>`
              : html`<p class="hint" style="padding:32px 20px;text-align:center;font-size:14px">${t(current && current.kind === "modbus" ? "liveEmptyMb" : current && current.kind === "enocean" ? "liveEmptyEo" : "liveEmpty")}</p>`}
          </section>
          <section class="card" aria-labelledby="t-files">
            <div class="row"><h2 id="t-files">${t("recFiles")}</h2>
              <button class="btn btn-g mono" style="font-size:12px" @click=${this._copyPath} aria-label="${t("copyPath")}">${icon("copy", 14)} ${this.copied ? t("copied") : PATH}</button></div>
            <p class="hint" style="margin:0">${t("rotation", { mb: s.settings.trace_file_mb, k: s.settings.trace_keep })} · <a href="#/settings">${t("change")}</a></p>
            ${files.length ? html`<div class="scroll"><table style="min-width:560px"><thead><tr><th>${t("fileTh")}</th><th>${t("connTh")}</th><th>${t("changedTh")}</th><th style="text-align:right">${t("sizeTh")}</th><th><span class="sr">${t("delete")}</span></th></tr></thead>
              <tbody>${files.map((f) => html`<tr><td class="mono" style="font-size:13px">${f.name}</td>
                <td>${f.connection && name(f.connection) ? html`<a href="#/trace/${f.connection}">${name(f.connection)}</a>` : html`<span class="hint">${t("noConnection")}</span>`}</td>
                <td>${fmtTime(f.modified)}</td><td style="text-align:right">${fmtBytes(f.size)}</td>
                <td style="text-align:right;white-space:nowrap;padding:4px 0 4px 8px">
                  <a class="btn btn-g" href=${url(`api/trace/${encodeURIComponent(f.name)}`)} download aria-label="${f.name} ${t("download")}">${icon("download", 16)}</a>
                  <button class="btn btn-d" @click=${() => this._delete(f.name)}>${t("delete")}</button></td></tr>`)}</tbody></table></div>`
              : html`<p class="hint" style="font-size:14px">${t("noFiles")}</p>`}
          </section>
        </div>
      </div>`;
  }

  _time(ts) {
    const d = new Date(ts * 1000);
    return `${d.toLocaleTimeString(undefined, { hour12: false })}.${String(d.getMilliseconds()).padStart(3, "0")}`;
  }
}
