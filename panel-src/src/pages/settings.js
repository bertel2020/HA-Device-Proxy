import { css, html } from "lit";
import { api, url } from "../api.js";
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
    versions: { state: true }, open: { state: true }, diffs: { state: true }, services: { state: true },
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
    api("api/notify/services").then((list) => { this.services = list; }).catch(() => { this.services = []; });
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
        ${[["net", "sNet"], ["src", "sSource"], ["hist", "sHistory"], ["notify", "sNotify"], ["mqtt", "sMqtt"], ["log", "sLogging"], ["diag", "sDiag"], ["about", "sAbout"]].map(([id, k]) =>
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

        <section id="notify" class="card" aria-labelledby="t-notify">
          <div><h2 id="t-notify">${t("sNotify")}</h2><p class="hint" style="margin-top:4px">${t("sNotifySub")}</p></div>
          <div class="grid2">
            <label class="fld"><span class="lbl">${t("notifyGrace")}</span><input class="inp" inputmode="numeric" .value=${String(d.notify_grace)}
              @input=${(e) => { this.draft = { ...d, notify_grace: Number(e.target.value || 0) }; }}></label>
            <label class="fld"><span class="lbl">${t("noClientMinutes")}</span><input class="inp" inputmode="numeric" .value=${String(d.no_client_minutes)}
              @input=${(e) => { this.draft = { ...d, no_client_minutes: Number(e.target.value || 0) }; }}></label>
            <label class="fld"><span class="lbl">${t("notifyService")}</span><select class="inp" @change=${(e) => { this.draft = { ...d, notify_service: e.target.value }; }}>
              <option value="" ?selected=${!d.notify_service}>${t("notifyNone")}</option>
              ${[...new Set([...(this.services || []), ...(d.notify_service ? [d.notify_service] : [])])].map((sv) => html`<option value=${sv} ?selected=${d.notify_service === sv}>notify.${sv}</option>`)}</select></label>
            <label class="fld"><span class="lbl">${t("notifyLanguage")}</span><select class="inp" @change=${(e) => { this.draft = { ...d, notify_language: e.target.value }; }}>
              <option value="de" ?selected=${d.notify_language === "de"}>Deutsch</option><option value="en" ?selected=${d.notify_language === "en"}>English</option></select></label>
          </div>
          <div class="grid2" style="gap:6px 16px">${[["notify_dismiss", "notifyDismiss"], ["notify_resolved", "notifyResolved"], ["notify_stuck", "notifyStuck"], ["notify_line_errors", "notifyLine"], ["notify_ser2net", "notifySer2net"]].map(([k, l]) =>
            html`<label class="chk"><input type="checkbox" .checked=${!!d[k]} @change=${(e) => { this.draft = { ...this.draft, [k]: e.target.checked }; }}><span>${t(l)}</span></label>`)}</div>
          <p class="hint">${t("notifyPerConnection")}</p>
          <div><button class="btn btn-p" @click=${() => this._saveSettings(Object.fromEntries(["notify_grace", "no_client_minutes", "notify_service", "notify_language", "notify_dismiss", "notify_resolved", "notify_stuck", "notify_line_errors", "notify_ser2net"].map((k) => [k, this.draft[k]])))}>${t("save")}</button></div>
        </section>

        <section id="mqtt" class="card" aria-labelledby="t-mqtt">
          <div class="row"><div><h2 id="t-mqtt">${t("sMqtt")}</h2><p class="hint" style="margin-top:4px">${t("sMqttSub")}</p></div>
            ${s.mqtt.broker ? html`<span class="chip ${s.mqtt.connected ? "ok" : "warn"}">${s.mqtt.connected ? t("mqttConnected") : t("mqttDisconnected")}</span>` : ""}</div>
          ${s.mqtt.broker ? html`<p class="hint">${t("mqttBroker", { b: s.mqtt.broker })}${s.mqtt.error ? ` · ${s.mqtt.error}` : ""}</p>`
            : s.settings.mqtt_enabled ? html`<div class="note warn">${t("mqttNoBroker")}</div>` : ""}
          <label class="chk"><input type="checkbox" .checked=${!!d.mqtt_enabled} @change=${(e) => { this.draft = { ...this.draft, mqtt_enabled: e.target.checked }; }}><span>${t("mqttOn")}</span></label>
          <div class="grid2">
            ${[["mqtt_prefix", "mqttPrefix"], ["mqtt_base", "mqttBase"]].map(([k, l]) => html`<label class="fld"><span class="lbl">${t(l)}</span>
              <input class="inp mono" .value=${d[k]} @input=${(e) => { this.draft = { ...this.draft, [k]: e.target.value }; }}></label>`)}
            <label class="fld"><span class="lbl">${t("mqttInterval")}</span><input class="inp" inputmode="numeric" .value=${String(d.mqtt_interval)}
              @input=${(e) => { this.draft = { ...this.draft, mqtt_interval: Number(e.target.value || 0) }; }}></label>
          </div>
          <p class="hint">${t("mqttNames")}</p>
          <div><button class="btn btn-p" @click=${() => this._saveSettings(Object.fromEntries(["mqtt_enabled", "mqtt_prefix", "mqtt_base", "mqtt_interval"].map((k) => [k, this.draft[k]])))}>${t("save")}</button></div>
        </section>

        <section id="log" class="card" aria-labelledby="t-log">
          <h2 id="t-log">${t("sLogging")}</h2>
          <div class="grid2">
            <label class="fld"><span class="lbl">${t("logLevel")}</span><select class="inp" @change=${(e) => { this.draft = { ...d, log_level: e.target.value }; }}>
              ${["info", "debug"].map((v) => html`<option ?selected=${d.log_level === v}>${v}</option>`)}</select></label>
            ${NUMBERS.map((k) => html`<label class="fld"><span class="lbl">${t(LABELS[k])}</span>
              <input class="inp" inputmode="numeric" .value=${String(d[k])} @input=${(e) => { this.draft = { ...d, [k]: Number(e.target.value || 0) }; }}></label>`)}
            <label class="fld"><span class="lbl">${t("language")}</span><select class="inp" @change=${(e) => this.dispatchEvent(new CustomEvent("dp-lang", { detail: e.target.value, bubbles: true, composed: true }))}>
              <option value="de" ?selected=${lang === "de"}>Deutsch</option><option value="en" ?selected=${lang === "en"}>English</option></select></label>
          </div>
          <div><button class="btn btn-p" @click=${() => this._saveSettings(Object.fromEntries(["log_level", ...NUMBERS].map((k) => [k, d[k]])))}>${t("save")}</button></div>
        </section>

        <section id="diag" class="card" aria-labelledby="t-diag">
          <div class="row"><div><h2 id="t-diag">${t("sDiag")}</h2><p class="hint" style="margin-top:4px">${t("sDiagSub")}</p></div>
            <a class="btn btn-s" href=${url("api/diagnostics")} download>${t("diagDownload")}</a></div>
        </section>

        <section id="about" class="card" aria-labelledby="t-about">
          <h2 id="t-about">${t("sAbout")}</h2>
          <div style="display:grid;grid-template-columns:minmax(120px,180px) minmax(0,1fr);gap:8px 16px">
            <span class="hint" style="font-size:14px">${t("app")}</span><span>${s.version} · ${t("license")}</span>
            <span class="hint" style="font-size:14px">ser2net</span><span>${s.ser2net_version || "?"} (GPL-2.0)</span>
            <span class="hint" style="font-size:14px">${t("source")}</span><a href="https://github.com/bertel2020/HA-Device-Proxy" target="_blank" rel="noopener">github.com/bertel2020/HA-Device-Proxy</a>
          </div>
        </section>
      </div></div>`;
  }
}
