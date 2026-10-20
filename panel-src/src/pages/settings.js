import { css, html } from "lit";
import { api } from "../api.js";
import { Page } from "../app.js";
import { changesText, lang, noteText, t } from "../i18n.js";
import { confirmDialog, fmtTime } from "../ui.js";

const NUMBERS = ["history_days", "trace_file_mb", "trace_keep", "debounce_count", "debounce_minutes"];
const LABELS = { history_days: "historyDays", trace_file_mb: "traceMb", trace_keep: "traceKeep", debounce_count: "debounceCount", debounce_minutes: "debounceMinutes" };

/** A short line diff of two JSON texts, enough to see what a version changed. */
function lineDiff(before, after) {
  const a = before.split("\n"), b = after.split("\n");
  const setA = new Set(a), setB = new Set(b);
  const out = [];
  for (const line of b) out.push(setA.has(line) ? `  ${line}` : `+ ${line}`);
  for (const line of a) if (!setB.has(line)) out.push(`- ${line}`);
  return out.filter((l) => !l.startsWith("  ")).join("\n") || "  (–)";
}

export class SettingsPage extends Page {
  static properties = {
    state: { attribute: false }, draft: { state: true }, custom: { state: true }, customText: { state: true }, customCheck: { state: true },
    versions: { state: true }, open: { state: true }, diffs: { state: true },
  };

  static styles = [...Page.styles, css`
    .layout { display: flex; flex-wrap: wrap; gap: 24px; align-items: flex-start; }
    .side { flex: 1 1 200px; display: flex; flex-direction: column; gap: 2px; }
    .side a { display: flex; align-items: center; min-height: 40px; padding: 0 12px; border-radius: 10px; text-decoration: none; color: var(--neutral); }
    .side a:hover { background: var(--line); color: var(--text); }
    .content { flex: 999 1 640px; min-width: 0; display: flex; flex-direction: column; gap: 20px; }
    .card { scroll-margin-top: 16px; }
    ol { list-style: none; margin: 0; padding: 0; }
    li { border-top: 1px solid var(--line-2); padding: 12px 0; display: flex; flex-direction: column; gap: 10px; }
    textarea.editor { min-height: 260px; font-size: 12px; line-height: 1.6; background: var(--code-bg); color: var(--code-text); border-color: var(--code-bg); }
  `];

  connectedCallback() {
    super.connectedCallback();
    this.open = -1;
    this.diffs = {};
    this._loadVersions();
    this._loadCustom();
  }

  willUpdate() {
    if (!this.draft && this.state) this.draft = { ...this.state.settings };
  }

  async _loadVersions() {
    try { this.versions = await api("api/versions"); } catch { this.versions = []; }
  }

  async _loadCustom() {
    try {
      this.custom = await api("api/custom");
      this.customText = this.custom.text;
      this.customCheck = this.custom.exists ? this.custom.check : null;
    } catch { /* stays empty */ }
  }

  async _saveSettings(patch) {
    try {
      await api("api/settings", { method: "PUT", body: { settings: patch } });
      this.toast(t("saved"));
      this.refresh();
      this._loadVersions();
    } catch (err) {
      this.toast(err.data.errors ? Object.values(err.data.errors).join("; ") : `${t("error")}: ${err.message}`);
    }
  }

  async _check() {
    try { this.customCheck = await api("api/custom/check", { method: "POST", body: { text: this.customText } }); } catch (err) { this.toast(err.message); }
  }

  async _saveCustom(use) {
    try {
      await api("api/custom", { method: "PUT", body: { text: this.customText, use } });
      this.toast(t("saved"));
      this.refresh();
      this._loadCustom();
      this._loadVersions();
    } catch (err) {
      if (err.data.check) this.customCheck = err.data.check; else this.toast(`${t("error")}: ${err.message}`);
    }
  }

  async _toggleDiff(index) {
    if (this.open === index) { this.open = -1; return; }
    this.open = index;
    const v = this.versions[index], before = this.versions[index + 1];
    if (this.diffs[v.id] !== undefined) return;
    try {
      const after = await api(`api/versions/${v.id}`);
      const prior = before ? await api(`api/versions/${before.id}`) : { connections: [] };
      this.diffs = { ...this.diffs, [v.id]: lineDiff(JSON.stringify(prior, null, 1), JSON.stringify(after, null, 1)) };
    } catch { this.diffs = { ...this.diffs, [v.id]: "–" }; }
  }

  async _restore(v) {
    if (!(await confirmDialog(this, t("restoreConfirm"), t("restore")))) return;
    try {
      await api(`api/versions/${v.id}/restore`, { method: "POST" });
      this.toast(t("saved"));
      this.refresh();
      this._loadVersions();
    } catch (err) { this.toast(`${t("error")}: ${err.message}`); }
  }

  _changeLine(v) {
    return changesText(v.changes) || v.summary;
  }

  render() {
    const s = this.state, d = this.draft;
    if (!d) return "";
    const own = s.source === "custom";
    const check = this.customCheck;
    return html`<div class="layout">
      <nav class="side" aria-label=${t("settingsTitle")}>
        <h1 style="margin:0 0 12px 12px">${t("settingsTitle")}</h1>
        ${[["net", "sNet"], ["src", "sSource"], ["hist", "sHistory"], ["log", "sLogging"], ["about", "sAbout"]].map(([id, k]) =>
          html`<a href="#/settings" @click=${(e) => { e.preventDefault(); this.renderRoot.getElementById(id).scrollIntoView({ behavior: "smooth" }); }}>${t(k)}</a>`)}
      </nav>
      <div class="content">
        <section id="net" class="card" aria-labelledby="t-net">
          <div><h2 id="t-net">${t("sNet")}</h2><p class="hint" style="margin-top:4px">${t("sNetSub")}</p></div>
          <div class="choices" role="radiogroup" aria-labelledby="t-net">${["local", "lan", "all"].map((v) => html`<button type="button" class="choice" role="radio"
            aria-checked=${s.settings.listen === v ? "true" : "false"} @click=${() => this._saveSettings({ listen: v })}>
            <b style="font-weight:500">${t(`net_${v}`)}</b><span class="hint">${t(`netsub_${v}`)}</span></button>`)}</div>
          ${s.settings.listen === "all" ? html`<div class="note bad" role="alert">${t("netWarn")}</div>` : ""}
        </section>

        <section id="src" class="card" aria-labelledby="t-src">
          <div class="row"><div><h2 id="t-src">${t("sSource")}</h2><p class="hint" style="margin-top:4px">${t("sSourceSub")}</p></div>
            <div class="seg" role="group" aria-labelledby="t-src">
              <button aria-pressed=${!own ? "true" : "false"} @click=${() => this._saveSettings({ source: "forms" })}>${t("forms")}</button>
              <button aria-pressed=${own ? "true" : "false"} ?disabled=${!this.custom?.exists} @click=${() => this._saveSettings({ source: "custom" })}>${t("own")}</button></div></div>
          <div class="note warn" role="note">${t("ownWarn")}</div>
          <textarea class="inp mono editor" aria-label="ser2net.yaml" .value=${this.customText || ""} @input=${(e) => { this.customText = e.target.value; this.customCheck = null; }}></textarea>
          <div class="row">
            ${check ? check.errors.length ? html`<div class="note bad" style="flex:1">${check.errors.map((n) => html`<div>${noteText(n)}</div>`)}</div>`
              : html`<span class="chip ok">${t("checkOk", { n: check.connections.length })}</span>` : html`<span class="hint">${t("notChecked")}</span>`}
            <div style="display:flex;gap:8px;flex-wrap:wrap"><button class="btn btn-s" @click=${this._check}>${t("check")}</button>
              <button class="btn btn-s" @click=${() => this._saveCustom(false)}>${t("saveFile")}</button>
              <button class="btn btn-p" @click=${() => this._saveCustom(true)}>${t("saveUse")}</button></div>
          </div>
          ${check && check.notes.length ? html`<div class="hint">${check.notes.map((n) => html`<div>${noteText(n)}</div>`)}</div>` : ""}
        </section>

        <section id="hist" class="card" aria-labelledby="t-hist">
          <div class="row"><h2 id="t-hist">${t("sHistory")}</h2><span class="hint">${t("sHistorySub")}</span></div>
          <ol>${(this.versions || []).map((v, i) => html`<li>
            <div class="row"><div style="min-width:0"><div style="display:flex;flex-wrap:wrap;gap:8px;align-items:center"><span style="font-weight:500">${this._changeLine(v)}</span>
              ${i === 0 ? html`<span class="chip info">${t("current")}</span>` : ""}</div>
              <div class="hint">${fmtTime(v.ts)} · ${t(`src_${v.source}`)}</div></div>
              <div style="display:flex;gap:4px"><button class="btn btn-g" aria-expanded=${this.open === i ? "true" : "false"} @click=${() => this._toggleDiff(i)}>${this.open === i ? t("hide") : t("diff")}</button>
                ${i ? html`<button class="btn btn-s" @click=${() => this._restore(v)}>${t("restore")}</button>` : ""}</div></div>
            ${this.open === i ? html`<div class="code" style="background:var(--surface-2);color:var(--text)">${this.diffs[v.id] ?? t("loading")}</div>` : ""}
          </li>`)}</ol>
        </section>

        <section id="log" class="card" aria-labelledby="t-log">
          <h2 id="t-log">${t("sLogging")}</h2>
          <div class="grid2">
            <label class="fld"><span class="lbl">${t("logLevel")}</span><select class="inp" @change=${(e) => { this.draft = { ...d, log_level: e.target.value }; }}>
              ${["info", "debug"].map((v) => html`<option ?selected=${d.log_level === v}>${v}</option>`)}</select></label>
            ${NUMBERS.map((k) => html`<label class="fld"><span class="lbl">${t(LABELS[k])}</span>
              <input class="inp" inputmode="numeric" .value=${String(d[k])} @input=${(e) => { this.draft = { ...d, [k]: Number(e.target.value || 0) }; }}></label>`)}
            <label class="fld"><span class="lbl">${t("language")}</span><select class="inp" @change=${(e) => this.dispatchEvent(new CustomEvent("s2n-lang", { detail: e.target.value, bubbles: true, composed: true }))}>
              <option value="de" ?selected=${lang === "de"}>Deutsch</option><option value="en" ?selected=${lang === "en"}>English</option></select></label>
          </div>
          <div><button class="btn btn-p" @click=${() => this._saveSettings(Object.fromEntries(["log_level", ...NUMBERS].map((k) => [k, d[k]])))}>${t("save")}</button></div>
        </section>

        <section id="about" class="card" aria-labelledby="t-about">
          <h2 id="t-about">${t("sAbout")}</h2>
          <div style="display:grid;grid-template-columns:minmax(120px,180px) minmax(0,1fr);gap:8px 16px">
            <span class="hint" style="font-size:14px">${t("app")}</span><span>${s.version} · ${t("license")}</span>
            <span class="hint" style="font-size:14px">ser2net</span><span>${s.ser2net_version || "?"} (GPL-2.0)</span>
            <span class="hint" style="font-size:14px">${t("source")}</span><a href="https://github.com/bertel2020/HA-Ser2Net" target="_blank" rel="noopener">github.com/bertel2020/HA-Ser2Net</a>
          </div>
        </section>
      </div></div>`;
  }
}
