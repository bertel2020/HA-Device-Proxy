import { css, html } from "lit";
import { api, url } from "../api.js";
import { Page } from "../app.js";
import { noteText, t } from "../i18n.js";
import { fmtSerial, icon } from "../ui.js";

export class ImportPage extends Page {
  static properties = {
    state: { attribute: false }, text: { state: true }, preview: { state: true }, replaceAll: { state: true },
    take: { state: true }, choice: { state: true }, done: { state: true }, error: { state: true }, disabled: { state: true }, busy: { state: true },
  };

  static styles = [...Page.styles, css`
    .steps { list-style: none; margin: 0 0 20px; padding: 0; display: flex; flex-wrap: wrap; gap: 8px; }
    .steps li { display: flex; align-items: center; gap: 8px; min-height: 36px; padding: 0 14px 0 6px; border-radius: 18px; font-weight: 500;
      background: var(--surface); border: 1px solid var(--line); color: var(--muted); }
    .steps li.on { background: var(--accent-soft); border-color: var(--accent); color: var(--accent-hover); }
    .steps li.past { color: var(--accent-hover); }
    .num { display: inline-flex; align-items: center; justify-content: center; width: 24px; height: 24px; border-radius: 50%; font-size: 12px; background: var(--line); color: var(--muted); }
    .on .num, .past .num { background: var(--accent); color: var(--on-accent); }
    .drop { border: 2px dashed var(--input-line); border-radius: 16px; padding: 32px 20px; display: flex; flex-direction: column; align-items: center; gap: 12px; text-align: center; background: var(--surface-2); }
    .drop.over { border-color: var(--accent); background: var(--accent-soft); }
    td .notes { margin: 6px 0 0; padding-left: 16px; font-size: 12px; color: var(--muted); }
  `];

  constructor() {
    super();
    this.text = "";
    this.replaceAll = false;
    this.take = new Set();
    this.choice = {};
    this.disabled = true;
  }

  async _file(file) {
    if (!file) return;
    this.text = await file.text();
    this._preview();
  }

  async _preview() {
    this.error = "";
    try {
      this.preview = await api("api/import/preview", { method: "POST", body: { text: this.text } });
      this.take = new Set(this.preview.items.filter((i) => i.connection && !Object.keys(i.conflicts).length).map((i) => i.alias));
      this.choice = Object.fromEntries(this.preview.items.filter((i) => Object.keys(i.conflicts).length).map((i) => [i.alias, "skip"]));
    } catch (err) {
      this.error = err.data.note ? noteText(err.data.note) : err.message;
    }
  }

  async _apply() {
    this.busy = true;
    const take = [...this.preview.items.filter((i) => i.connection && (this.take.has(i.alias) || (this.choice[i.alias] && this.choice[i.alias] !== "skip"))).map((i) => i.alias)];
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
      <span class="num">${i < step ? "✓" : i + 1}</span>${t(k)}</li>`)}</ol>`;
  }

  _choose() {
    return html`<section class="card" aria-labelledby="t-file"><h2 id="t-file">${t("importChoose")}</h2>
      <div class="drop" @dragover=${(e) => { e.preventDefault(); e.currentTarget.classList.add("over"); }}
        @dragleave=${(e) => e.currentTarget.classList.remove("over")}
        @drop=${(e) => { e.preventDefault(); e.currentTarget.classList.remove("over"); this._file(e.dataTransfer.files[0]); }}>
        ${icon("upload", 40)}<b style="font-size:16px;font-weight:500">${t("importDrop")}</b><span class="hint">${t("importFormats")}</span>
        <label class="btn btn-p">${t("chooseFile")}<input type="file" class="sr" accept=".yaml,.yml,.conf,text/plain" @change=${(e) => this._file(e.target.files[0])}></label>
      </div>
      <label class="fld"><span class="lbl">${t("pasteHere")}</span>
        <textarea class="inp mono" rows="6" .value=${this.text} @input=${(e) => { this.text = e.target.value; }}></textarea></label>
      ${this.error ? html`<div class="note bad" role="alert">${this.error}</div>` : ""}
      <div><button class="btn btn-s" ?disabled=${!this.text.trim()} @click=${this._preview}>${t("readPreview")}</button></div>
    </section>`;
  }

  _result(item) {
    if (!item.connection) return html`<span class="chip bad">${t("resNo")}</span>`;
    if (Object.keys(item.conflicts).length && !this.replaceAll) return html`<span class="chip bad">${t("resConflict")}: ${Object.entries(item.conflicts).map(([k, v]) => `${k} ↔ ${v}`).join(", ")}</span>`;
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
      ${p.notes.length ? html`<div class="note warn"><b>${t("fileNotes")}</b>${p.notes.map((n) => html`<div>${noteText(n)}</div>`)}</div>` : ""}
      <div class="scroll"><table style="min-width:680px"><thead><tr><th><span class="sr">${t("take")}</span></th><th>${t("name")}</th><th>${t("port")}</th><th>${t("device")}</th><th>${t("result")}</th></tr></thead>
        <tbody>${p.items.map((item) => {
          const c = item.connection;
          const conflict = Object.keys(item.conflicts).length && !this.replaceAll;
          return html`<tr>
            <td>${c && !conflict ? html`<input type="checkbox" style="width:18px;height:18px;accent-color:var(--accent)" aria-label="${item.alias} ${t("take")}"
              .checked=${this.take.has(item.alias)} @change=${(e) => { const s = new Set(this.take); e.target.checked ? s.add(item.alias) : s.delete(item.alias); this.take = s; }}>` : ""}</td>
            <td><b style="font-weight:500">${item.alias}</b>${c ? html`<div class="hint">${fmtSerial(c)} · ${c.mode} · max. ${c.max_clients}${c.enabled ? "" : " · off"}</div>` : ""}</td>
            <td class="mono">${c ? c.port : ""}</td>
            <td class="mono" style="font-size:12px;overflow-wrap:anywhere;max-width:260px">${c ? c.device : ""}</td>
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
        <div style="display:flex;gap:8px"><a class="btn btn-g" href="#/connections">${t("cancel")}</a>
          <button class="btn btn-p" ?disabled=${!count || this.busy} @click=${this._apply}>${t("apply", { n: count })}</button></div>
      </div></section>`;
  }

  render() {
    const step = this.done ? 2 : this.preview ? 1 : 0;
    return html`
      <p class="crumb"><a href="#/connections">${t("connectionsTitle")}</a> › ${t("importTitle")}</p>
      <h1 style="margin:12px 0 20px">${t("importTitle")}</h1>
      <div class="cols"><div class="main-col">
        ${this._steps(step)}
        ${this.done ? html`<section class="card" style="align-items:flex-start"><span class="chip ok">${t("stepDone")}</span>
          <h2>${t("doneTitle", { n: this.done.changes.filter((c) => c.change === "added").length })}</h2><p class="hint" style="font-size:14px">${t("doneText")}</p>
          <div style="display:flex;gap:8px"><a class="btn btn-p" href="#/connections">${t("toConnections")}</a><a class="btn btn-s" href="#/settings">${t("sHistory")}</a></div></section>`
          : this.preview ? this._previewView() : this._choose()}
      </div>
      <aside class="side-col">
        <section class="card" aria-labelledby="t-exp"><h2 id="t-exp">${t("exportTitle")}</h2><p class="hint" style="font-size:14px">${t("exportText")}</p>
          <label class="chk"><input type="checkbox" .checked=${this.disabled} @change=${(e) => { this.disabled = e.target.checked; }}><span>${t("exportDisabled")}</span></label>
          <a class="btn btn-s" style="align-self:flex-start" href=${url(`api/export?disabled=${this.disabled ? 1 : 0}`)} download>${icon("download")}${t("download")}</a></section>
        <section class="card" aria-labelledby="t-own"><h2 id="t-own">${t("ownTitle")}</h2><p class="hint" style="font-size:14px">${t("ownText")}</p>
          <a href="#/settings">${t("toSource")}</a></section>
      </aside></div>`;
  }
}
