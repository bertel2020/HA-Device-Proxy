import { css, html } from "lit";
import { api } from "../api.js";
import { Page } from "../app.js";
import { noteText, t } from "../i18n.js";
import { confirmDialog, fmtSerial, icon, modbusTarget } from "../ui.js";

/** The import as a dialog over any page: choose a file, check the preview, done. */
export class ImportDialog extends Page {
  static properties = {
    state: { attribute: false }, text: { state: true }, preview: { state: true }, replaceAll: { state: true },
    take: { state: true }, choice: { state: true }, done: { state: true }, error: { state: true }, busy: { state: true },
  };

  static styles = [...Page.styles, css`
    .back { position: fixed; inset: 0; background: rgba(0,0,0,.4); display: flex; align-items: flex-start; justify-content: center; z-index: 20; padding: 24px 16px; overflow-y: auto; }
    .box { background: var(--surface); border-radius: 16px; padding: 22px; max-width: 760px; width: 100%; display: flex; flex-direction: column; gap: 16px; }
    .box > section.card { border: 0; padding: 0; box-shadow: none; background: none; }
    .steps { list-style: none; margin: 0 0 20px; padding: 0; display: flex; flex-wrap: wrap; gap: 8px; }
    .steps li { display: flex; align-items: center; gap: 8px; min-height: 36px; padding: 0 14px 0 6px; border-radius: 18px; font-weight: 500;
      background: var(--surface); border: 1px solid var(--line); color: var(--muted); }
    .steps li.on { background: var(--accent-soft); border-color: var(--accent); color: var(--accent-hover); }
    .steps li.past { color: var(--accent-hover); }
    .num { display: inline-flex; align-items: center; justify-content: center; width: 24px; height: 24px; border-radius: 50%; font-size: 12px; background: var(--line); color: var(--muted); }
    .on .num, .past .num { background: var(--accent); color: var(--on-accent); }
    .drop { border: 2px dashed var(--input-line); border-radius: 16px; padding: 32px 20px; display: flex; flex-direction: column; align-items: center; gap: 12px; text-align: center; background: var(--surface-2); }
    .drop.over { border-color: var(--accent); background: var(--accent-soft); }
    .formats summary { cursor: pointer; color: var(--accent); font-size: 13px; }
    .formats p { margin: 6px 0 0; }
    .imp { min-width: 680px; }
    .imp td.nm { min-width: 130px; }
    .imp td.dev { font-size: 12px; overflow-wrap: break-word; min-width: 120px; max-width: 200px; }
    .allt { display: none; }
    @media (max-width: 640px) {
      .steps { flex-wrap: nowrap; margin-bottom: 14px; }
      .steps li:not(.on) .stl { display: none; }
      .steps li:not(.on) { padding-right: 6px; }
      .imp { min-width: 0; }
      .imp, .imp thead, .imp tbody, .imp thead tr { display: block; }
      .imp thead th:not(:first-child) { display: none; }
      .imp thead th { display: block; border: 0; padding: 0 0 8px; }
      .allt { display: inline; margin-left: 8px; font-weight: 400; }
      .imp .all { display: flex; align-items: center; }
      .imp tbody tr { display: grid; grid-template-columns: 28px minmax(0, 1fr); gap: 4px 8px; border: 1px solid var(--line); border-radius: 12px; padding: 10px 12px; margin-bottom: 10px; }
      .imp td { display: block; border: 0; padding: 0; }
      .imp td:not(:first-child) { grid-column: 2; }
      .imp td.nm, .imp td.dev { min-width: 0; max-width: none; }
      .imp td[data-l]::before { content: attr(data-l) ": "; color: var(--muted); font-family: system-ui, sans-serif; }
      .imp .chip { white-space: normal; height: auto; min-height: 24px; padding-block: 3px; border-radius: 14px; }
      .imp td[data-l]:empty { display: none; }
    }
    .gone { background: var(--warn-bg, #fdf1dc); color: var(--warn-text, #7a4a00); border-radius: 10px; padding: 10px 12px; font-size: 13px; }
    .sum { display: flex; gap: 10px; flex-wrap: wrap; }
    .sum div { flex: 1; min-width: 100px; background: var(--surface-2); border-radius: 12px; padding: 10px 14px; display: flex; flex-direction: column; font-size: 12px; color: var(--muted); }
    .sum b { font-size: 24px; font-weight: 500; color: var(--text, inherit); }
    td .notes { margin: 6px 0 0; padding-left: 16px; font-size: 12px; color: var(--muted); }
  `];

  constructor() {
    super();
    this.text = "";
    this.replaceAll = false;
    this.take = new Set();
    this.choice = {};
  }

  async _file(file) {
    if (!file) return;
    this.text = await file.text();
    this._preview();
  }

  async _preview() {
    this.error = "";
    try {
      const preview = await api("api/import/preview", { method: "POST", body: { text: this.text } });
      if (!preview.items.length) {
        this.error = [t("importNone"), ...preview.notes.filter((n) => n.code !== "no_connections").map(noteText)].join(" ");
        return;
      }
      this.preview = preview;
      this.take = new Set(this.preview.items.filter((i) => i.connection && !Object.keys(i.conflicts).length).map((i) => i.alias));
      this.choice = Object.fromEntries(this.preview.items.filter((i) => Object.keys(i.conflicts).length).map((i) => [i.alias, "skip"]));
    } catch (err) {
      this.error = err.data.note ? noteText(err.data.note) : err.message;
    }
  }

  async _apply() {
    const take = [...this.preview.items.filter((i) => i.connection && (this.take.has(i.alias) || (this.choice[i.alias] && this.choice[i.alias] !== "skip"))).map((i) => i.alias)];
    const replaced = this.replaceAll ? this.state.connections.length : take.filter((a) => this.choice[a] === "replace").length;
    if (replaced && !(await confirmDialog(this, t("importReplaceConfirm", { n: replaced }), t("importReplace")))) return;
    this.busy = true;
    try {
      const result = await api("api/import", { method: "POST", body: { text: this.text, replace_all: this.replaceAll, take, on_conflict: this.choice } });
      this.done = result;
      this.refresh();
    } catch (err) {
      this.toast(`${t("error")}: ${err.data.note ? noteText(err.data.note) : err.message}`);
    } finally {
      this.busy = false;
    }
  }

  _steps(step) {
    return html`<ol class="steps" aria-label=${t("importTitle")}>${["stepChoose", "stepPreview", "stepDone"].map((k, i) => html`<li class=${i === step ? "on" : i < step ? "past" : ""} aria-current=${i === step ? "step" : "false"}>
      <span class="num">${i < step ? "✓" : i + 1}</span><span class="stl">${t(k)}</span></li>`)}</ol>`;
  }

  _choose() {
    return html`<section class="card" aria-labelledby="t-file"><h2 id="t-file">${t("importChoose")}</h2>
      <div class="drop" @dragover=${(e) => { e.preventDefault(); e.currentTarget.classList.add("over"); }}
        @dragleave=${(e) => e.currentTarget.classList.remove("over")}
        @drop=${(e) => { e.preventDefault(); e.currentTarget.classList.remove("over"); this._file(e.dataTransfer.files[0]); }}>
        ${icon("upload", 40)}<b style="font-size:16px;font-weight:500">${t("importDrop")}</b>
        <label class="btn btn-p">${t("chooseFile")}<input type="file" class="sr" accept=".yaml,.yml,.conf,.json,text/plain" @change=${(e) => this._file(e.target.files[0])}></label>
      </div>
      <details class="formats"><summary>${t("formatsMore")}</summary><p class="hint">${t("importFormats")}</p></details>
      <label class="fld"><span class="lbl">${t("pasteHere")}</span>
        <textarea class="inp mono" rows="6" .value=${this.text} @input=${(e) => { this.text = e.target.value; }}></textarea></label>
      ${this.error ? html`<div class="note bad" role="alert">${this.error}</div>` : ""}
      <div class="row" style="justify-content:flex-end;gap:8px"><button class="btn btn-g" @click=${this._close}>${t("cancel")}</button>
        <button class="btn btn-p" ?disabled=${!this.text.trim()} @click=${this._preview}>${t("readPreview")}</button></div>
    </section>`;
  }

  _result(item) {
    if (!item.connection) return html`<span class="chip bad">${t("resNo")}</span>`;
    if (Object.keys(item.conflicts).length && !this.replaceAll) {
      const c = item.conflicts;
      const same = c.port && c.port === c.device;  // one connection holds both the port and the device
      return html`${Object.entries(c).filter(([k]) => !(same && k === "device")).map(([k, v]) => html`<div><span class="chip bad">${t(same && k === "port" ? "confl_port_device" : `confl_${k}`, { p: item.connection.port, n: v })}</span></div>`)}`;
    }
    return item.notes.length ? html`<span class="chip warn">${t("resNotes")}</span>` : html`<span class="chip ok">${t("resOk")}</span>`;
  }

  _previewView() {
    const p = this.preview;
    const takeable = p.items.filter((i) => i.connection);
    const count = takeable.filter((i) => this.take.has(i.alias) || (this.choice[i.alias] && this.choice[i.alias] !== "skip")).length;
    return html`<section class="card" aria-labelledby="t-prev">
      <div class="row"><div style="display:flex;align-items:center;gap:12px">${icon("file", 28)}
        <div><h2 id="t-prev">${t(`format_${p.version}`)}</h2><span class="hint">${t("found", { n: p.items.length })}</span></div></div>
        <button class="btn btn-g" @click=${() => { this.preview = null; }}>${t("otherFile")}</button></div>
      <div class="choices" role="radiogroup">${[[false, "merge", "mergeSub"], [true, "replaceAll", "replaceAllSub"]].map(([v, k, sub]) => html`
        <button type="button" class="choice" role="radio" aria-checked=${this.replaceAll === v ? "true" : "false"} @click=${() => { this.replaceAll = v; }}>
          <b style="font-weight:500">${t(k)}</b><span class="hint">${t(sub)}</span></button>`)}</div>
      ${this.replaceAll && this.state.connections.length ? html`<div class="gone" role="alert"><b style="font-weight:500">${t("willGo")}</b> ${this.state.connections.map((c) => c.name).join(", ")}</div>` : ""}
      ${p.notes.length ? html`<div class="note warn"><b>${t("fileNotes")}</b>${p.notes.map((n) => html`<div>${noteText(n)}</div>`)}</div>` : ""}
      <div class="scroll"><table class="imp"><thead><tr><th><label class="all"><input type="checkbox" style="width:18px;height:18px;accent-color:var(--accent)" aria-label="${t("takeAll")}" .checked=${count > 0 && count === takeable.filter((i) => !Object.keys(i.conflicts).length || this.replaceAll).length} @change=${(e) => this._all(e.target.checked, takeable)}><span class="allt">${t("takeAll")}</span></label></th><th>${t("name")}</th><th>${t("port")}</th><th>${t("device")}</th><th>${t("result")}</th></tr></thead>
        <tbody>${p.items.map((item) => {
          const c = item.connection;
          const conflict = Object.keys(item.conflicts).length && !this.replaceAll;
          return html`<tr>
            <td>${c && !conflict ? html`<input type="checkbox" style="width:18px;height:18px;accent-color:var(--accent)" aria-label="${item.alias} ${t("take")}"
              .checked=${this.take.has(item.alias)} @change=${(e) => { const s = new Set(this.take); e.target.checked ? s.add(item.alias) : s.delete(item.alias); this.take = s; }}>` : ""}</td>
            <td class="nm"><b style="font-weight:500">${item.alias}</b>${c ? html`<div class="hint">${this._kind(c)} · ${t("importMax", { n: c.max_clients })}${c.enabled ? "" : ` · ${t("importOff")}`}</div>` : ""}</td>
            <td class="mono" data-l=${t("port")}>${c ? c.port : ""}</td>
            <td class="mono dev" data-l=${t("device")}>${c ? (c.kind !== "serial" ? modbusTarget(c) : c.device) : ""}</td>
            <td>${this._result(item)}
              ${item.notes.length ? html`<ul class="notes">${item.notes.map((n) => html`<li>${noteText(n)}</li>`)}</ul>` : ""}
              ${conflict ? html`<label class="fld" style="margin-top:8px"><span class="hint">${t("onConflict")}</span>
                <select class="inp" style="min-height:36px" @change=${(e) => { this.choice = { ...this.choice, [item.alias]: e.target.value }; }}>
                  ${["skip", "replace", "new_port"].filter((v) => v !== "new_port" || !item.conflicts.device).map((v) => html`<option value=${v} ?selected=${this.choice[item.alias] === v}>${t(`c_${v}`)}</option>`)}
                </select></label>` : ""}
            </td></tr>`;
        })}</tbody></table></div>
      <div class="row" style="border-top:1px solid var(--line-2);padding-top:16px">
        <span class="hint" style="font-size:13px">${t("selected", { n: count, m: p.items.length })}</span>
        <div style="display:flex;gap:8px"><button class="btn btn-g" @click=${this._close}>${t("cancel")}</button>
          <button class="btn btn-p" ?disabled=${!count || this.busy} @click=${this._apply}>${t("apply", { n: count })}</button></div>
      </div></section>`;
  }

  _all(on, takeable) {
    this.take = new Set(on ? takeable.filter((i) => !Object.keys(i.conflicts).length || this.replaceAll).map((i) => i.alias) : []);
  }

  _kind(c) {
    if (c.kind === "modbus") return t(`link_${c.link}`);
    if (c.kind === "enocean") return `${c.esp_protocol.toUpperCase()} · ${t(`eolink_${c.link}`)}`;
    return `${fmtSerial(c)} · ${c.mode === "raw" ? t("modeRaw") : c.mode === "rfc2217" ? "RFC 2217" : c.mode}`;
  }

  _done() {
    const n = (kind) => this.done.changes.filter((c) => c.connection && c.change === kind).length;
    const added = n("added"), changed = n("changed"), removed = n("removed");
    const skipped = Math.max(0, this.preview.items.length - added - changed);
    const taken = new Set(this.done.changes.filter((c) => c.connection && c.change !== "removed").map((c) => c.connection));
    const off = this.preview.items.filter((i) => i.connection && !i.connection.enabled && taken.has(i.connection.name)).map((i) => i.connection.name);
    return html`<section class="card"><h2>${t("doneHead")}</h2>
      <div class="sum">${[["added", added], ["changed", changed], ...(removed ? [["removed", removed]] : []), ["skipped", skipped]].map(([k, v]) => html`<div><b>${v}</b>${t(`sum_${k}`)}</div>`)}</div>
      ${off.length ? html`<p class="hint" style="font-size:14px">${t("doneOff", { n: off.join(", ") })}</p>` : ""}
      <p class="hint" style="font-size:14px">${t("doneText")}</p>
      <div style="display:flex;gap:8px;flex-wrap:wrap"><a class="btn btn-p" href="#/connections" @click=${this._close}>${t("toConnections")}</a><a class="btn btn-s" href="#/settings" @click=${this._close}>${t("sHistory")}</a></div></section>`;
  }

  _close() {
    this.dispatchEvent(new CustomEvent("dp-import-close", { bubbles: true, composed: true }));
  }

  firstUpdated() { this.renderRoot.querySelector(".box").focus(); }

  render() {
    const step = this.done ? 2 : this.preview ? 1 : 0;
    return html`<div class="back" @keydown=${(e) => e.key === "Escape" && this._close()}>
      <div class="box" role="dialog" aria-modal="true" aria-labelledby="t-imp" tabindex="-1">
        <div class="row"><h2 id="t-imp" style="margin:0">${t("importTitle")}</h2>
          <button class="btn btn-g" aria-label=${t("close")} @click=${this._close}>${icon("x")}</button></div>
        ${this._steps(step)}
        ${this.done ? this._done()
          : this.preview ? this._previewView() : this._choose()}
      </div></div>`;
  }
}
