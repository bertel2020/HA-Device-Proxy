import { css, html } from "lit";
import { api, url } from "../api.js";
import { Page } from "../app.js";
import { changesText, fieldError, lang, noteText, t } from "../i18n.js";
import { confirmDialog, copyText, fmtTime, icon, logo } from "../ui.js";

const NUMBERS = ["history_days", "trace_file_mb", "trace_keep", "debounce_count", "debounce_minutes"];

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
    versions: { state: true }, open: { state: true }, histAll: { state: true }, runtime: { state: true }, copied: { state: true }, diffs: { state: true }, services: { state: true },
  };

  static styles = [...Page.styles, css`
    .layout { display: flex; flex-wrap: wrap; gap: 24px; align-items: flex-start; }
    .side { flex: 1 1 200px; display: flex; flex-direction: column; gap: 2px; }
    /* beside the content (not wrapped above it) the menu stays in view while scrolling */
    @media (min-width: 864px) {
      .side { position: sticky; top: calc(var(--header-h) + 16px); max-height: calc(100vh - var(--header-h) - 32px); overflow-y: auto; }
    }
    .side a { display: flex; align-items: center; min-height: 40px; padding: 0 12px; border-radius: 10px; text-decoration: none; color: var(--neutral); }
    .side a:hover { background: var(--line); color: var(--text); }
    .content { flex: 999 1 640px; min-width: 0; display: flex; flex-direction: column; gap: 20px; }
    .card { scroll-margin-top: calc(var(--header-h) + 16px); }
    ol { list-style: none; margin: 0; padding: 0; }
    li { border-top: 1px solid var(--line-2); padding: 12px 0; display: flex; flex-direction: column; gap: 10px; }
    ol.hist li { padding: 0; gap: 0; }
    .acts { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 10px; }
    .act { all: unset; box-sizing: border-box; display: flex; flex-direction: column; gap: 4px; padding: 12px 14px; border: 1px solid var(--input-line); border-radius: 12px; cursor: pointer; }
    .act:hover { background: var(--surface-1); }
    .act:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
    .act b { display: flex; align-items: center; gap: 8px; font-weight: 500; font-size: 14px; }
    .act span { font-size: 12px; color: var(--muted); }
    .act.on { background: var(--accent-soft); border-color: var(--accent); }
    .act.on b { color: var(--accent-hover); }
    pre.runtime { margin: 0; max-height: 420px; overflow: auto; font-size: 12px; line-height: 1.6; white-space: pre; }
    details.expert > summary { cursor: pointer; font-size: 14px; color: var(--muted); display: flex; align-items: center; gap: 8px; min-height: 32px; }
    .expert-body { display: flex; flex-direction: column; gap: 12px; margin-top: 12px; }
    .grp { display: flex; flex-direction: column; gap: 10px; border-top: 1px solid var(--line-2); padding-top: 16px; }
    .grp h3 { margin: 0; font-size: 14px; font-weight: 500; }
    .pills { display: flex; flex-wrap: wrap; gap: 6px; align-items: center; }
    .sentence { display: flex; align-items: center; flex-wrap: wrap; gap: 8px; font-size: 14px; }
    .sentence .num { width: 72px; text-align: center; padding: 0 8px; }
    .grp .grid2 { align-items: start; }
    .grp .fld { justify-content: flex-start; }
    .fld .hint { color: var(--muted); }
    .inp:disabled { opacity: .5; cursor: not-allowed; }
    .day { font-size: 12px; font-weight: 500; color: var(--muted); margin: 14px 0 4px; }
    .day:first-child { margin-top: 0; }
    .hrow { all: unset; box-sizing: border-box; width: 100%; display: flex; align-items: center; gap: 10px; min-height: 40px; cursor: pointer; border-radius: 8px; }
    .hrow:hover { background: var(--line-2); }
    .hrow:focus-visible { outline: 2px solid var(--accent); outline-offset: -2px; }
    .hrow .chev { flex: none; width: 7px; height: 7px; margin: 0 4px 0 8px; border-right: 2px solid var(--muted); border-bottom: 2px solid var(--muted); transform: rotate(-45deg); transition: transform .15s; }
    .hrow[aria-expanded="true"] .chev { transform: rotate(45deg); }
    .hrow .tm { flex: none; width: 44px; font-size: 13px; color: var(--muted); font-variant-numeric: tabular-nums; }
    .hrow .tx { flex: 1; min-width: 0; font-weight: 500; overflow-wrap: anywhere; }
    .hbody { display: flex; flex-direction: column; gap: 10px; padding: 4px 0 12px 69px; align-items: flex-start; }
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

  async _toggleRuntime() {
    if (this.runtime) { this.runtime = null; return; }
    try { this.runtime = await api("api/runtime"); } catch (err) { this.toast(`${t("error")}: ${err.message}`); }
  }

  async _copyRuntime() {
    if (await copyText(this.runtime?.text || "")) { this.copied = true; setTimeout(() => { this.copied = false; }, 2000); }
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
      this.toast(err.data.errors ? Object.values(err.data.errors).map(fieldError).join("; ") : `${t("error")}: ${err.message}`);
    }
  }

  async _changeListen(v) {
    if (v === this.state.settings.listen) return;
    if (!(await confirmDialog(this, t("listenConfirm"), t("confirm")))) return;
    this._saveSettings({ listen: v });
  }

  async _useOwn() {
    if (this.state.settings.source === "custom") return;
    if (!(await confirmDialog(this, t("ownConfirm"), t("confirm")))) return;
    this._saveSettings({ source: "custom" });
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

  async _toggleDiff(group) {
    const v = group.ids[0];
    if (this.open === v.id) { this.open = -1; return; }
    this.open = v.id;
    if (this.diffs[v.id] !== undefined) return;
    const before = this.versions[this.versions.indexOf(group.ids[group.ids.length - 1]) + 1];
    try {
      const after = await api(`api/versions/${v.id}`);
      const prior = before ? await api(`api/versions/${before.id}`) : { connections: [] };
      this.diffs = { ...this.diffs, [v.id]: lineDiff(JSON.stringify(prior, null, 1), JSON.stringify(after, null, 1)) };
    } catch { this.diffs = { ...this.diffs, [v.id]: "–" }; }
  }

  /** The versions newest first, equal neighbours as one row, under day headings. */
  _history() {
    const groups = [];
    for (const v of this.versions || []) {
      const text = this._changeLine(v), last = groups[groups.length - 1];
      if (last && last.text === text && last.source === v.source) last.ids.push(v);
      else groups.push({ text, source: v.source, ids: [v] });
    }
    return groups;
  }

  _day(ts) {
    const d = new Date(ts * 1000), today = new Date();
    if (d.toDateString() === today.toDateString()) return t("today");
    if (d.toDateString() === new Date(today.getTime() - 86400000).toDateString()) return t("yesterday");
    return d.toLocaleDateString(lang, { weekday: "short", day: "2-digit", month: "2-digit" });
  }

  _historyRows() {
    const groups = this._history();
    const shown = this.histAll ? groups : groups.slice(0, 5);
    let day = "";
    const rows = shown.map((g) => {
      const v = g.ids[0], label = this._day(v.ts), open = this.open === v.id, first = v === this.versions[0];
      const heading = label !== day ? html`<div class="day">${label}</div>` : "";
      day = label;
      return html`${heading}<li>
        <button class="hrow" aria-expanded=${open ? "true" : "false"} @click=${() => this._toggleDiff(g)}>
          <span class="chev"></span><span class="tm">${fmtTime(v.ts, false)}</span><span class="tx">${g.text}</span>
          ${g.ids.length > 1 ? html`<span class="chip">${g.ids.length}×</span>` : ""}
          ${v.source !== "ui" ? html`<span class="chip">${t(`src_${v.source}`)}</span>` : ""}
          ${first ? html`<span class="chip info">${t("current")}</span>` : ""}</button>
        ${open ? html`<div class="hbody">
          <div class="code" style="background:var(--surface-2);color:var(--text);align-self:stretch">${this.diffs[v.id] ?? t("loading")}</div>
          ${first ? "" : html`<button class="btn btn-s" @click=${() => this._restore(v)}>${t("restore")}</button>`}</div>` : ""}
      </li>`;
    });
    const rest = groups.length - 5;
    return html`<ol class="hist">${rows}</ol>${rest > 0 ? html`<div><button class="btn btn-g" @click=${() => { this.histAll = !this.histAll; }}>${this.histAll ? t("histLess") : t("histMore", { n: rest })}</button></div>` : ""}`;
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
    const conns = s.connections || [];
    const noClient = conns.some((c) => c.notify_no_client);
    const gateways = conns.filter((c) => c.kind === "enocean" && c.enabled).length;
    const check = this.customCheck;
    return html`<div class="layout">
      <nav class="side" aria-label=${t("settingsTitle")}>
        <h1 style="margin:0 0 12px 12px">${t("settingsTitle")}</h1>
        ${[["net", "sNet"], ["src", "sSource"], ["hist", "sHistory"], ["notify", "sNotify"], ["mqtt", "sMqtt"], ["enocean", "sEnocean"], ["log", "sLogging"], ["about", "sAbout"]].map(([id, k]) =>
          html`<a href="#/settings" @click=${(e) => { e.preventDefault(); this.renderRoot.getElementById(id).scrollIntoView({ behavior: "smooth" }); }}>${t(k)}</a>`)}
      </nav>
      <div class="content">
        <section id="net" class="card" aria-labelledby="t-net">
          <div><h2 id="t-net">${t("sNet")}</h2><p class="hint" style="margin-top:4px">${t("sNetSub")}</p></div>
          <div class="choices" role="radiogroup" aria-labelledby="t-net">${["local", "apps", "lan", "all"].map((v) => html`<button type="button" class="choice" role="radio"
            aria-checked=${s.settings.listen === v ? "true" : "false"} @click=${() => this._changeListen(v)}>
            <b style="font-weight:500">${t(`net_${v}`)}</b><span class="hint">${v === "lan" && s.lan_net ? t("netsub_lan_net", { net: s.lan_net }) : t(`netsub_${v}`)}</span></button>`)}</div>
          ${s.settings.listen === "all" ? html`<div class="note bad" role="alert">${t("netWarn")}</div>` : ""}
        </section>

        <section id="src" class="card" aria-labelledby="t-src">
          <div><h2 id="t-src">${t("sSource")}</h2><p class="hint" style="margin-top:4px">${t("sSourceSub")}</p></div>
          <div class="acts">
            <a class="act" href="#/import"><b>${icon("upload")}${t("srcImport")}</b><span>${t("srcImportSub")}</span></a>
            <a class="act" href=${url("api/export")} download><b>${icon("download")}${t("srcExport")}</b><span>${t("srcExportSub")}</span></a>
            <button class="act ${this.runtime ? "on" : ""}" aria-expanded=${this.runtime ? "true" : "false"} @click=${this._toggleRuntime}><b>${icon("file")}${t("srcRuntime")}</b><span>${t("srcRuntimeSub")}</span></button>
          </div>
          ${this.runtime ? html`
            <div class="row"><div style="flex:1;min-width:220px"><b style="font-weight:500">${t("runtimeTitle")}</b><p class="hint" style="margin-top:4px">${t("runtimeHint")}</p></div>
              <div style="display:flex;gap:8px"><button class="btn btn-s" @click=${this._copyRuntime}>${icon("copy")}${this.copied ? t("copied") : t("copy")}</button></div></div>
            <pre class="code runtime">${this.runtime.text || "–"}</pre>
            <div class="hint">${this.runtime.ts ? `${fmtTime(this.runtime.ts)} · ` : ""}${t("runtimeConns", { n: this.runtime.connections })} · ${t("runtimeFoot")}</div>` : ""}
          <details class="expert" ?open=${own}>
            <summary>${t("expert")} ${own ? "" : html`<span class="chip warn">${t("expertTag")}</span>`}</summary>
            <div class="expert-body">
              <div class="row"><div class="hint" style="flex:1">${t("expertSub")}</div>
                <div class="seg" role="group" aria-label=${t("sSource")}>
                  <button aria-pressed=${!own ? "true" : "false"} @click=${() => this._saveSettings({ source: "forms" })}>${t("forms")}</button>
                  <button aria-pressed=${own ? "true" : "false"} ?disabled=${!this.custom?.exists} @click=${() => this._useOwn()}>${t("own")}</button></div></div>
          ${own ? html`<div class="note warn" role="note">${t("ownWarn")}</div>` : ""}
          <div class="hint">${t("ownHint")}</div>
          <textarea class="inp mono editor" aria-label="ser2net.yaml" .value=${this.customText || ""} @input=${(e) => { this.customText = e.target.value; this.customCheck = null; }}></textarea>
          <div class="row">
            ${check ? check.errors.length ? html`<div class="note bad" style="flex:1">${check.errors.map((n) => html`<div>${noteText(n)}</div>`)}</div>`
              : html`<span class="chip ok">${t("checkOk", { n: check.connections.length })}</span>` : html`<span class="hint">${t("notChecked")}</span>`}
            <div style="display:flex;gap:8px;flex-wrap:wrap"><button class="btn btn-s" @click=${this._check}>${t("check")}</button>
              <button class="btn btn-s" @click=${() => this._saveCustom(false)}>${t("saveFile")}</button>
              <button class="btn btn-p" @click=${() => this._saveCustom(true)}>${t("saveUse")}</button></div>
          </div>
          ${check && check.notes.length ? html`<div class="hint">${check.notes.map((n) => html`<div>${noteText(n)}</div>`)}</div>` : ""}
            </div>
          </details>
        </section>

        <section id="hist" class="card" aria-labelledby="t-hist">
          <div class="row"><h2 id="t-hist">${t("sHistory")}</h2><span class="hint">${t("sHistorySub")}</span></div>
          ${this._historyRows()}
        </section>

        <section id="notify" class="card" aria-labelledby="t-notify">
          <div><h2 id="t-notify">${t("sNotify")}</h2><p class="hint" style="margin-top:4px">${t("sNotifySub")}</p></div>
          <div class="grp">
            <h3>${t("nWhat")}</h3>
            <div class="grid2" style="gap:6px 24px">${[["notify_stuck", "notifyStuck"], ["notify_line_errors", "notifyLine"], ["notify_ser2net", "notifySer2net"]].map(([k, l]) =>
              html`<label class="chk"><input type="checkbox" .checked=${!!d[k]} @change=${(e) => { this.draft = { ...this.draft, [k]: e.target.checked }; }}><span>${t(l)}</span></label>`)}</div>
            <div class="pills">${[["notify_missing", "nMissing"], ["notify_no_client", "nNoClient"], ["silence_minutes", "nNoData"]].map(([k, l]) => {
              const n = conns.filter((c) => c[k]).length;
              return html`<span class="chip ${n ? "ok" : ""}">${t(l)} · ${t("nOf", { n, m: conns.length })}</span>`;
            })}<a href="#/connections" style="font-size:13px">${t("nPerConnection")}</a></div>
          </div>
          <div class="grp">
            <h3>${t("nWhen")}</h3>
            <div class="grid2">
              <label class="fld"><span class="lbl">${t("notifyGrace")}</span><input class="inp" inputmode="numeric" .value=${String(d.notify_grace)}
                @input=${(e) => { this.draft = { ...d, notify_grace: Number(e.target.value || 0) }; }}><span class="hint">${t("notifyGraceHint")}</span></label>
              <label class="fld"><span class="lbl">${t("noClientMinutes")}</span><input class="inp" inputmode="numeric" ?disabled=${!noClient} .value=${String(d.no_client_minutes)}
                @input=${(e) => { this.draft = { ...d, no_client_minutes: Number(e.target.value || 0) }; }}><span class="hint">${noClient ? t("noClientHint") : t("noClientOff")}</span></label>
            </div>
          </div>
          <div class="grp">
            <h3>${t("nWhere")}</h3>
            <div class="note" style="display:flex;gap:8px;align-items:center">${icon("info")}${t("nBell")}</div>
            <label class="chk"><input type="checkbox" .checked=${!!d.notify_dismiss} @change=${(e) => { this.draft = { ...this.draft, notify_dismiss: e.target.checked }; }}><span>${t("notifyDismiss")}</span></label>
            <div class="grid2">
              <label class="fld"><span class="lbl">${t("notifyService")}</span><select class="inp" @change=${(e) => { this.draft = { ...d, notify_service: e.target.value }; }}>
                <option value="" ?selected=${!d.notify_service}>${t("notifyNone")}</option>
                ${[...new Set([...(this.services || []), ...(d.notify_service ? [d.notify_service] : [])])].map((sv) => html`<option value=${sv} ?selected=${d.notify_service === sv}>notify.${sv}</option>`)}</select></label>
              <label class="fld"><span class="lbl">${t("notifyLanguage")}</span><select class="inp" @change=${(e) => { this.draft = { ...d, notify_language: e.target.value }; }}>
                <option value="de" ?selected=${d.notify_language === "de"}>Deutsch</option><option value="en" ?selected=${d.notify_language === "en"}>English</option></select><span class="hint">${t("notifyLanguageHint")}</span></label>
            </div>
            <label class="chk" style=${d.notify_service ? "" : "opacity:.5"}><input type="checkbox" ?disabled=${!d.notify_service} .checked=${!!d.notify_resolved} @change=${(e) => { this.draft = { ...this.draft, notify_resolved: e.target.checked }; }}><span>${t("notifyResolved")}${d.notify_service ? "" : html` <span class="hint">· ${t("notifyResolvedNeeds")}</span>`}</span></label>
          </div>
          <div class="actions"><button class="btn btn-p" @click=${() => this._saveSettings(Object.fromEntries(["notify_grace", "no_client_minutes", "notify_service", "notify_language", "notify_dismiss", "notify_resolved", "notify_stuck", "notify_line_errors", "notify_ser2net"].map((k) => [k, this.draft[k]])))}>${t("save")}</button></div>
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
          <div><b style="font-weight:500">${t("mqttOwnBroker")}</b><p class="hint" style="margin-top:4px">${t("mqttOwnBrokerSub")}</p></div>
          <div class="grid2">
            <label class="fld"><span class="lbl">${t("mqttHost")}</span><input class="inp mono" placeholder=${t("mqttHostAuto")} .value=${d.mqtt_host} @input=${(e) => { this.draft = { ...this.draft, mqtt_host: e.target.value.trim() }; }}></label>
            <label class="fld"><span class="lbl">${t("mqttPort")}</span><input class="inp" inputmode="numeric" .value=${String(d.mqtt_port)} @input=${(e) => { this.draft = { ...this.draft, mqtt_port: Number(e.target.value || 0) }; }}></label>
            <label class="fld"><span class="lbl">${t("mqttUser")}</span><input class="inp" autocomplete="off" .value=${d.mqtt_user} @input=${(e) => { this.draft = { ...this.draft, mqtt_user: e.target.value }; }}></label>
            <label class="fld"><span class="lbl">${t("mqttPassword")}</span><input class="inp" type="password" autocomplete="new-password" .value=${d.mqtt_password} @input=${(e) => { this.draft = { ...this.draft, mqtt_password: e.target.value }; }}></label>
          </div>
          <label class="chk"><input type="checkbox" .checked=${!!d.mqtt_tls} @change=${(e) => { this.draft = { ...this.draft, mqtt_tls: e.target.checked }; }}><span>${t("mqttTls")}</span></label>
          <p class="hint">${t("mqttNames")}</p>
          <div class="actions"><button class="btn btn-p" @click=${() => this._saveSettings(Object.fromEntries(["mqtt_enabled", "mqtt_prefix", "mqtt_base", "mqtt_interval", "mqtt_host", "mqtt_port", "mqtt_user", "mqtt_password", "mqtt_tls"].map((k) => [k, this.draft[k]])))}>${t("save")}</button></div>
        </section>

        <section id="enocean" class="card" aria-labelledby="t-enocean">
          <div class="row"><div><h2 id="t-enocean">${t("sEnocean")}</h2><p class="hint" style="margin-top:4px">${t("sEnoceanSub")}</p></div>
            ${gateways ? html`<span class="chip ok">${t("eoStatusOn", { n: gateways })}</span>` : html`<span class="chip">${t("eoStatusOff")}</span>`}</div>
          ${gateways ? "" : html`<div class="note" style="display:flex;gap:8px;align-items:center">${icon("info")}<span>${t("eoNoGateway")} <a href="#/edit/new">${t("addConnection")}</a></span></div>`}
          <label class="chk"><input type="checkbox" .checked=${!!d.enocean_discovery} @change=${(e) => { this.draft = { ...this.draft, enocean_discovery: e.target.checked }; }}>
            <span>${t("eoDiscovery")}<br><span class="hint">${t("eoDiscoveryHint")}</span></span></label>
          <details class="expert" ?open=${d.enocean_status_port !== 9199}>
            <summary>${t("eoAdvanced")}${d.enocean_status_port !== 9199 ? html` <span class="hint">· ${t("eoPortCustom")}</span>` : ""}</summary>
            <div class="expert-body">
              <label class="fld"><span class="lbl">${t("eoStatusPort")}</span><input class="inp" inputmode="numeric" style="max-width:200px" .value=${String(d.enocean_status_port)}
                @input=${(e) => { this.draft = { ...this.draft, enocean_status_port: Number(e.target.value || 0) }; }}>
                <span class="hint">${t("eoStatusPortHint")}</span></label>
            </div>
          </details>
          <div class="actions"><button class="btn btn-p" @click=${() => this._saveSettings({ enocean_discovery: d.enocean_discovery, enocean_status_port: d.enocean_status_port })}>${t("save")}</button></div>
        </section>

        <section id="log" class="card" aria-labelledby="t-log">
          <div><h2 id="t-log">${t("sLogging")}</h2><p class="hint" style="margin-top:4px">${t("logSub")}</p></div>
          <div class="grp" style="border-top:none;padding-top:0">
            <h3>${t("logAddon")}</h3>
            <label class="fld" style="max-width:280px"><span class="lbl">${t("logLevel")}</span><select class="inp" @change=${(e) => { this.draft = { ...d, log_level: e.target.value }; }}>
              ${[["info", "logNormal"], ["debug", "logDebug"]].map(([v, k]) => html`<option value=${v} ?selected=${d.log_level === v}>${t(k)}</option>`)}</select></label>
            <p class="hint">${t("logHint")}</p>
          </div>
          <div class="grp">
            <h3>${t("evTitle")}</h3>
            <label class="fld" style="max-width:280px"><span class="lbl">${t("historyDays")}</span><input class="inp" inputmode="numeric" .value=${String(d.history_days)} @input=${(e) => { this.draft = { ...d, history_days: Number(e.target.value || 0) }; }}></label>
            <p class="hint">${t("historyDaysHint")}</p>
            <div class="sentence">${t("debA")}<input class="inp num" inputmode="numeric" aria-label=${t("debA")} .value=${String(d.debounce_count)} @input=${(e) => { this.draft = { ...d, debounce_count: Number(e.target.value || 0) }; }}>${t("debB")}<input class="inp num" inputmode="numeric" aria-label=${t("debB")} .value=${String(d.debounce_minutes)} @input=${(e) => { this.draft = { ...d, debounce_minutes: Number(e.target.value || 0) }; }}>${t("debC")}</div>
            <p class="hint">${t("debHint")}</p>
          </div>
          <div class="grp">
            <h3>${t("trTitle")}</h3>
            <p class="hint">${t("trHint")}</p>
            <div class="grid2">
              <label class="fld"><span class="lbl">${t("traceMb")}</span><input class="inp" inputmode="numeric" .value=${String(d.trace_file_mb)} @input=${(e) => { this.draft = { ...d, trace_file_mb: Number(e.target.value || 0) }; }}></label>
              <label class="fld"><span class="lbl">${t("traceKeep")}</span><input class="inp" inputmode="numeric" .value=${String(d.trace_keep)} @input=${(e) => { this.draft = { ...d, trace_keep: Number(e.target.value || 0) }; }}></label>
            </div>
            <div class="note" style="display:flex;gap:8px;align-items:center">${icon("info")}${t("traceCalc", { mb: d.trace_file_mb * (1 + d.trace_keep), size: d.trace_file_mb, files: 1 + d.trace_keep })}</div>
          </div>
          <div class="actions"><button class="btn btn-p" @click=${() => this._saveSettings(Object.fromEntries(["log_level", ...NUMBERS].map((k) => [k, d[k]])))}>${t("save")}</button></div>
        </section>

        <section id="about" class="card" aria-labelledby="t-about">
          <h2 id="t-about">${t("sAbout")}</h2>
          <div class="grp" style="border-top:none;padding-top:0">
            <h3>${t("helpTitle")}</h3>
            <p class="hint" style="font-size:14px">${t("helpText")}</p>
            <div style="display:flex;gap:8px;flex-wrap:wrap">
              <a class="btn btn-s" href=${url("api/diagnostics")} download>${icon("download")}${t("diagDownload")}</a>
              <a class="btn btn-g" href="https://github.com/bertel2020/HA-Device-Proxy/issues/new" target="_blank" rel="noopener">${t("reportIssue")}</a>
            </div>
            <ul class="hint" style="margin:0;padding-left:18px">${["diagVersions", "diagConfig", "diagStatus", "diagEvents", "diagYaml"].map((k) => html`<li style="border:0;padding:0;display:list-item">${t(k)}</li>`)}</ul>
            <p class="hint">${t("diagPrivacy")}</p>
          </div>
          <div class="grp">
          <div style="display:flex;align-items:center;gap:16px">${logo(64)}
              <div style="min-width:0"><h2 id="t-about" style="margin:0;font-size:22px">${t("appTitle")}</h2>
                <div style="display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin-top:6px"><span class="chip info">${s.version}</span><span class="hint" style="font-size:14px">${t("license")}</span></div></div></div>
            <div style="display:grid;grid-template-columns:minmax(80px,140px) minmax(0,1fr);gap:10px 16px;border-top:1px solid var(--line);padding-top:16px">
              <span class="hint" style="font-size:14px">${t("language")}</span>
              <span><select class="inp" style="max-width:200px" aria-label=${t("language")} @change=${(e) => this.dispatchEvent(new CustomEvent("dp-lang", { detail: e.target.value, bubbles: true, composed: true }))}>
                <option value="de" ?selected=${lang === "de"}>Deutsch</option><option value="en" ?selected=${lang === "en"}>English</option></select>
                <span class="hint" style="display:block;margin-top:4px">${t("langHint")}</span></span>
              <span class="hint" style="font-size:14px">ser2net</span><span>${s.ser2net_version || "?"} · GPL-2.0</span>
              <span class="hint" style="font-size:14px">${t("source")}</span><a href="https://github.com/bertel2020/HA-Device-Proxy" target="_blank" rel="noopener">github.com/bertel2020/HA-Device-Proxy</a>
            </div>
          </div>
        </section>
      </div></div>`;
  }
}
