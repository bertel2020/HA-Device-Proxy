import { css, html } from "lit";
import { api, saveConnection, toConnection, url } from "../api.js";
import { Page } from "../app.js";
import { t } from "../i18n.js";
import { confirmDialog, fmtBytes, fmtTime, icon, navigate } from "../ui.js";

const MODES = ["off", "rx", "tx", "both"];

export class TracePage extends Page {
  static properties = { state: { attribute: false }, selected: {}, chunks: { state: true }, paused: { state: true }, ascii: { state: true } };

  static styles = [...Page.styles, css`
    .conn { display: flex; flex-direction: column; gap: 8px; padding: 10px 12px; border-radius: 12px; border: 1px solid transparent; }
    .conn.on { background: var(--accent-soft); border-color: var(--accent); }
    .pick { display: flex; flex-direction: column; align-items: flex-start; gap: 2px; background: none; border: none; padding: 0; cursor: pointer; font: inherit; color: inherit; text-align: left; min-height: 40px; justify-content: center; width: 100%; }
    .view { max-height: 460px; overflow: auto; padding: 8px 4px; }
    .view table { font-family: "Roboto Mono", ui-monospace, Menlo, monospace; font-size: 12px; color: var(--code-text); }
    .view td { border: none; padding: 2px 8px; white-space: pre; }
    .dir { display: inline-block; min-width: 30px; text-align: center; border-radius: 6px; padding: 0 6px; }
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
      if (fresh.length) { this._after = fresh[fresh.length - 1].seq; this.chunks = [...this.chunks, ...fresh].slice(-400); }
    } catch { /* shown by the frame */ }
  }

  async _mode(c, trace) {
    try {
      await saveConnection({ ...toConnection(c), trace });
      this.refresh();
    } catch (err) { this.toast(`${t("error")}: ${err.message}`); }
  }

  async _delete(name) {
    if (!(await confirmDialog(this, t("deleteFile", { n: name }), t("delete")))) return;
    try { await api(`api/trace/${encodeURIComponent(name)}`, { method: "DELETE" }); this.refresh(); } catch (err) { this.toast(`${t("error")}: ${err.message}`); }
  }

  render() {
    const s = this.state;
    const current = this.connection(this.selected);
    const files = s.trace_files;
    return html`
      <div class="head"><div><h1>${t("traceTitle")}</h1><p class="sub">${t("traceSub")}</p></div></div>
      <div class="cols">
        <section class="card side-col" style="gap:4px;padding:12px" aria-labelledby="t-conns">
          <h2 id="t-conns" style="padding:8px 8px 4px">${t("navConnections")}</h2>
          ${s.connections.map((c) => html`<div class="conn ${c.id === this.selected ? "on" : ""}">
            <button class="pick" aria-current=${c.id === this.selected ? "true" : "false"} @click=${() => navigate(`#/trace/${c.id}`)}>
              <b style="font-weight:500">${c.name}</b><span class="hint">${c.trace === "off" ? t("notRecording") : t("recording", { m: t(`tr_${c.trace}`) })}</span></button>
            <div class="seg" role="group" aria-label="${t("traceMode")} ${c.name}">${MODES.map((m) => html`<button type="button" aria-pressed=${c.trace === m ? "true" : "false"}
              ?disabled=${s.source === "custom" && c.kind !== "modbus"} @click=${() => this._mode(c, m)}>${m === "off" ? t("off") : m === "both" ? t("both") : m.toUpperCase()}</button>`)}</div>
          </div>`)}
          <p class="hint" style="padding:10px 8px 4px">${t("rotation", { mb: s.settings.trace_file_mb, k: s.settings.trace_keep })} · <a href="#/settings">${t("change")}</a></p>
        </section>
        <div class="main-col">
          <section class="card" style="padding:0;gap:0;overflow:hidden" aria-labelledby="t-view">
            <div class="row" style="padding:14px 16px;border-bottom:1px solid var(--line)">
              <h2 id="t-view">${current ? current.name : "–"}</h2>
              <div style="display:flex;gap:4px">
                <button class="btn btn-g" @click=${() => { this.ascii = !this.ascii; }}>${this.ascii ? t("hexOnly") : t("hexAscii")}</button>
                <button class="btn btn-g" @click=${() => { this.paused = !this.paused; }}>${this.paused ? t("resume") : t("pause")}</button></div></div>
            ${this.chunks.length ? html`<div class="code view" style="border-radius:0"><table><tbody>${this.chunks.slice(-200).reverse().map((ch) => html`<tr>
              <td style="color:#8f9ba8">${new Date(ch.ts * 1000).toLocaleTimeString(undefined, { hour12: false })}</td>
              <td><span class="dir ${ch.direction === "rx" ? "rx" : ch.direction === "tx" ? "tx" : "mark"}">${ch.direction.toUpperCase()}</span></td>
              ${ch.info ? html`<td style="color:#9fb3c8">${ch.info}</td>` : ""}<td>${ch.hex || ch.text}</td>${!ch.info && this.ascii && ch.hex ? html`<td style="color:#9fb3c8">${ch.text.replace(/[^\x20-\x7e]/g, ".")}</td>` : ""}</tr>`)}</tbody></table></div>`
              : html`<p class="hint" style="padding:32px 20px;text-align:center;font-size:14px">${t(current && current.kind === "modbus" ? "liveEmptyMb" : "liveEmpty")}</p>`}
          </section>
          <section class="card" aria-labelledby="t-files">
            <div class="row"><h2 id="t-files">${t("files")}</h2><span class="hint mono">/addon_configs/…_device_proxy/trace/</span></div>
            ${files.length ? html`<div class="scroll"><table style="min-width:520px"><thead><tr><th>${t("fileTh")}</th><th>${t("changedTh")}</th><th style="text-align:right">${t("sizeTh")}</th><th><span class="sr">${t("delete")}</span></th></tr></thead>
              <tbody>${files.map((f) => html`<tr><td class="mono" style="font-size:13px">${f.name}</td><td>${fmtTime(f.modified)}</td><td style="text-align:right">${fmtBytes(f.size)}</td>
                <td style="text-align:right;white-space:nowrap;padding:4px 0 4px 8px">
                  <a class="btn btn-g" href=${url(`api/trace/${encodeURIComponent(f.name)}`)} download aria-label="${f.name} ${t("download")}">${icon("download", 16)}</a>
                  <button class="btn btn-d" @click=${() => this._delete(f.name)}>${t("delete")}</button></td></tr>`)}</tbody></table></div>`
              : html`<p class="hint" style="font-size:14px">–</p>`}
          </section>
        </div>
      </div>`;
  }
}
