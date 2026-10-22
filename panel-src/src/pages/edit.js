import { css, html } from "lit";
import { api, saveConnection } from "../api.js";
import { Page } from "../app.js";
import { DEFAULTS as ENOCEAN, HA_ONLY, TEMPLATES as EO_TEMPLATES } from "../enocean.js";
import { fieldError, t } from "../i18n.js";
import { confirmDialog, icon, navigate, toggle } from "../ui.js";

const DEFAULTS = {
  name: "", device: "", port: 3333, enabled: true, template: "generic", baud: 9600, data_bits: 8, parity: "n", stop_bits: 1,
  mode: "raw", max_clients: 1, local: true, rtscts: false, xonxoff: false, hangup_when_done: false, nobreak: false, dtr: "", rts: "",
  rs485: "", low_latency: false, timeout: 0, kickolduser: false, chardelay: true, remaddr: "", banner: "", openstr: "", closestr: "",
  connector_retry_time: 0, nodelay: false, bind: "", extra: [], keep_open: false, stuck_disconnect: false, trace: "off",
  notify_missing: true, notify_no_client: false, silence_minutes: 0, kind: "serial",
  link: "tcp", host: "", host_port: 502, request_timeout_ms: 3000, connect_delay_ms: 0, retries: 1, request_gap_ms: 0,
  write_access: "all", write_clients: "", cache_ms: 0, unit_map: "", device_connections: 1, probe_seconds: 0, probe_unit: 1, probe_function: 3, probe_address: 0,
  esp_protocol: "esp2", send_gap_ms: 10, replay_size: 1000, replay_max_age_s: 900, replay_persist: false,
};
// new Modbus connections: only Home Assistant (127.0.0.1) and the other apps may write
const MODBUS = { kind: "modbus", template: "modbus", link: "tcp", max_clients: 10, mode: "raw", keep_open: false, stuck_disconnect: false, silence_minutes: 0,
  write_access: "listed", write_clients: "127.0.0.1, 172.30.32.0/23" };

const LINKS = ["tcp", "rtu", "rtu_tcp"];
// the Z-Wave stick has no login and takes commands: by default only Home Assistant and the other apps
const ZWAVE_CLIENTS = "127.0.0.1, 172.30.32.0/23";
const TEMPLATES = {
  ehz_sml: { baud: 9600, data_bits: 8, parity: "n", stop_bits: 1, max_clients: 5, chardelay: true, nodelay: false },
  ehz_d0: { baud: 9600, data_bits: 7, parity: "e", stop_bits: 1, max_clients: 5, chardelay: true, nodelay: false },
  zwave: { baud: 115200, data_bits: 8, parity: "n", stop_bits: 1, max_clients: 2, chardelay: false, nodelay: true, remaddr: ZWAVE_CLIENTS },
  generic: { baud: 9600, data_bits: 8, parity: "n", stop_bits: 1, max_clients: 1, chardelay: true, nodelay: false },
};
const BAUDS = [300, 1200, 2400, 4800, 9600, 19200, 38400, 57600, 115200, 230400, 460800, 921600];
const MODBUS_ADVANCED = ["kickolduser", "low_latency"];
// Modbus: what is folded into "Feintuning" and counts when it differs from the default
const MODBUS_TUNING = ["retries", "connect_delay_ms", "request_gap_ms", "cache_ms", "device_connections", "probe_seconds", "unit_map", "timeout", "kickolduser", "low_latency"];
const ENOCEAN_ADVANCED = ["kickolduser", "low_latency"];
const ENOCEAN_BAUDS = [9600, 19200, 57600, 115200];
const ADVANCED = ["rtscts", "xonxoff", "hangup_when_done", "nobreak", "low_latency", "kickolduser", "nodelay", "keep_open"];

const extraText = (pairs) => pairs.map(([k, v]) => `${k}: ${v}`).join("\n");
const parseExtra = (text) => text.split("\n").map((l) => l.trim()).filter(Boolean).map((l) => {
  const i = l.indexOf(":");
  return i < 0 ? [l, ""] : [l.slice(0, i).trim(), l.slice(i + 1).trim()];
});
const fieldErrors = (errors) => Object.fromEntries(Object.entries(errors || {}).map(([k, v]) => [k.replace(/^connections\.\d+\./, ""), v]));

export class EditPage extends Page {
  static properties = {
    state: { attribute: false }, connectionId: {},
    draft: { state: true }, errors: { state: true }, yaml: { state: true }, advanced: { state: true },
    otherDevice: { state: true }, replayOpen: { state: true }, saving: { state: true }, extraRaw: { state: true }, touched: { state: true }, warnings: { state: true },

  };

  static styles = [...Page.styles, css`
    form { display: contents; }
    .grid2 { align-items: start; }
    .fld { justify-content: flex-start; }
    .fold { display: flex; align-items: center; justify-content: space-between; gap: 12px; }
    fieldset { border: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 10px; }
    legend { padding: 0; margin-bottom: 8px; font-size: 13px; font-weight: 500; }
    .opts { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 6px 16px; }
    .toggle-head { display: flex; align-items: center; justify-content: space-between; width: 100%; background: none; border: none; padding: 0;
      min-height: 44px; cursor: pointer; font: inherit; color: inherit; text-align: left; }
    .flow { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 6px; }
    .flow li { display: flex; flex-direction: column; gap: 2px; padding: 10px 12px; border-radius: 12px; background: var(--surface-2); }
    .flow li + li::before { content: "↓"; color: var(--muted); margin: -4px 0 2px; }
    .actions { display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: 12px; }
  `];

  willUpdate(changed) {
    if (changed.has("connectionId") || (this.draft === undefined && this.state)) this._load();
  }

  _load() {
    const existing = this.connection(this.connectionId);
    if (existing) {
      const draft = {};
      for (const key of [...Object.keys(DEFAULTS), "id"]) draft[key] = existing[key];
      this.draft = draft;
    } else {
      this.draft = { ...DEFAULTS, ...this._fresh("serial") };
    }
    this.extraRaw = extraText(this.draft.extra);
    this.otherDevice = !!this.draft.device && !this.state.devices.some((d) => d.stable === this.draft.device || d.by_id.includes(this.draft.device) || d.by_path.includes(this.draft.device));
    this.errors = {};
    this.touched = new Set(existing ? Object.keys(DEFAULTS) : []);
    const flags = { modbus: MODBUS_ADVANCED, enocean: ENOCEAN_ADVANCED }[this.draft.kind] || ADVANCED;
    this.advanced = this.draft.kind === "modbus" ? MODBUS_TUNING.concat("trace").some((k) => this.draft[k] !== (DEFAULTS[k] ?? "off"))
      : flags.some((k) => this.draft[k]) || !!(this.draft.unit_map || this.draft.extra.length || this.draft.timeout || this.draft.trace !== "off");
    this.replayOpen = this.draft.replay_size !== DEFAULTS.replay_size || this.draft.replay_max_age_s !== DEFAULTS.replay_max_age_s || this.draft.replay_persist;
    if (!existing && this.draft.kind === "serial") this._suggestName();
    this._preview();
  }

  /** Port and device for a new connection of this kind. */
  _fresh(kind) {
    const ports = this.state.connections.map((c) => c.port);
    const free = this.state.devices.find((d) => !d.used_by);
    if (kind === "modbus") {
      let port = 502;
      while (ports.includes(port)) port++;
      return { ...MODBUS, port, device: "" };
    }
    if (kind === "enocean") {
      let port = 9100;
      while (ports.includes(port)) port++;
      return { ...ENOCEAN, port, device: free ? free.stable : "" };
    }
    const serial = ports.filter((p) => p >= 1024);
    return { kind: "serial", template: "generic", ...TEMPLATES.generic, port: serial.length ? Math.max(...serial) + 1 : 3333, device: free ? free.stable : "" };
  }

  /** A name from the chosen device, as long as the name is empty or still the last suggestion. */
  _suggestName() {
    const d = this.draft;
    const x = this.state.devices.find((v) => v.stable === d.device || v.by_id.includes(d.device) || v.by_path.includes(d.device));
    const what = x ? [x.manufacturer, x.product].filter(Boolean).join(" ") : "";
    if (!what || (d.name && d.name !== this._auto)) return;
    this._auto = what;
    this.draft = { ...d, name: what };
  }

  /** Who may connect when the connection has no limit of its own: the network setting. */
  _follows(d) {
    if (d.bind && !d.bind.startsWith("127.")) return "";
    if (d.remaddr) return t("netOwn", { a: d.remaddr });
    const s = this.state.settings, n = (s.lan_networks || "").split(/[\s,;]+/).filter(Boolean).length;
    const what = s.listen === "lan" ? (n === 1 ? t("netLanOne") : t("netLanN", { n })) : t(`net_${s.listen}`);
    return t("netFollows", { what });
  }

  _kind(kind) {
    if (kind === this.draft.kind) return;
    this.otherDevice = false;
    this._set({ ...DEFAULTS, ...this._fresh(kind), name: this.draft.name, enabled: this.draft.enabled });
    if (!this.draft.id) this.touched = new Set(); // a new connection: no errors before typing
  }

  _set(patch) {
    this.draft = { ...this.draft, ...patch };
    this.touched = new Set([...this.touched, ...Object.keys(patch)]);
    clearTimeout(this._pt);
    this._pt = setTimeout(() => this._preview(), 300);
  }

  async _preview() {
    try {
      const result = await api("api/preview", { method: "POST", body: { connection: this.draft } });
      this.yaml = result.yaml;
      this.errors = fieldErrors(result.errors);
      this.warnings = result.warnings || {};
    } catch { /* keep the last preview */ }
  }

  async _save(e) {
    e.preventDefault();
    this.saving = true;
    this.touched = new Set(Object.keys(DEFAULTS));
    try {
      const result = await saveConnection(this.draft);
      let text = result.rebuilt.length ? t("savedRebuilt", { n: result.rebuilt.join(", ") }) : t("saved");
      if (result.disconnected.length) text += t("savedReconnect", { n: result.disconnected.join(", ") });
      this.toast(text);
      this.refresh();
      navigate(`#/connection/${this.draft.id || result.id}`);
    } catch (err) {
      this.errors = fieldErrors(err.data.errors);
      this.toast(err.data.errors ? t("errorsBelow") : `${t("error")}: ${err.message}`);
    } finally {
      this.saving = false;
    }
  }

  async _delete() {
    if (!(await confirmDialog(this, t("deleteConfirm", { n: this.draft.name }), t("delete")))) return;
    try {
      await api(`api/connections/${this.draft.id}`, { method: "DELETE" });
      this.refresh();
      navigate("#/connections");
    } catch (err) { this.toast(`${t("error")}: ${err.message}`); }
  }

  _shown() { return Object.fromEntries(Object.entries(this.errors).filter(([k]) => this.touched.has(k))); }

  _err(key) {
    const e = this._shown();
    if (e[key]) return html`<span class="err" id="e-${key}">${fieldError(e[key])}</span>`;
    const w = (this.warnings || {})[key];
    return w ? html`<span class="hint" id="e-${key}" style="color:var(--warn)">${t("portWarn", { w: fieldError(w) })}</span>` : "";
  }

  _input(key, label, { type = "text", hint = "", mono = false, number = false } = {}) {
    const value = this.draft[key];
    return html`<label class="fld"><span class="lbl">${label}</span>
      <input class="inp ${mono ? "mono" : ""}" type=${type} .value=${String(value ?? "")} inputmode=${number ? "numeric" : "text"}
        aria-invalid=${this._shown()[key] ? "true" : "false"} aria-describedby="e-${key}"
        @input=${(e) => this._set({ [key]: number ? Number(e.target.value || 0) : e.target.value })}>
      ${this._err(key)}${hint ? html`<span class="hint">${hint}</span>` : ""}</label>`;
  }

  _trace() {
    const d = this.draft;
    return html`<label class="fld"><span class="lbl">${t("traceMode")}</span><select class="inp" @change=${(e) => this._set({ trace: e.target.value })}>
      ${["off", "rx", "tx", "both"].map((v) => html`<option value=${v} ?selected=${d.trace === v}>${t(d.kind === "modbus" ? `trmb_${v}` : `tr_${v}`)}</option>`)}</select></label>`;
  }

  _check(key, plain = false) {
    const option = !plain && key !== "keep_open" && key !== "stuck_disconnect" && !key.startsWith("notify");
    return html`<label class="chk"><input type="checkbox" .checked=${!!this.draft[key]} @change=${(e) => this._set({ [key]: e.target.checked })}>
      <span>${t(`o_${key}`)}${option ? html`<br><span class="hint mono">${key.replace(/_/g, "-")}</span>` : ""}</span></label>`;
  }

  _devicePicker(chosen) {
    const d = this.draft, devices = this.state.devices;
    return html`<label class="fld"><span class="lbl">${t("devicePick")}</span>
        <select class="inp" aria-invalid=${this._shown().device ? "true" : "false"} @change=${(e) => {
          if (e.target.value === "__other") { this.otherDevice = true; return; }
          this.otherDevice = false; this._set({ device: e.target.value });
          if (d.kind === "serial") this._suggestName();
        }}>
          ${d.device ? "" : html`<option value="" selected>–</option>`}
          ${devices.map((x) => html`<option value=${x.stable} ?selected=${!this.otherDevice && chosen === x}>${this._deviceLabel(x)}</option>`)}
          <option value="__other" ?selected=${this.otherDevice}>${t("deviceOther")}</option>
        </select>
        ${this.otherDevice ? html`<input class="inp mono" .value=${d.device} placeholder="/dev/serial/by-id/…" @input=${(e) => this._set({ device: e.target.value })}>` : html`<span class="hint mono" style="overflow-wrap:anywhere">${d.device}</span>`}
        ${this._err("device")}</label>
      ${chosen && chosen.ambiguous ? html`<div class="note warn" role="note">${t("ambiguous")}</div>` : ""}`;
  }

  _serialFormat() {
    const d = this.draft;
    return html`<label class="fld"><span class="lbl">${t("baud")}</span><select class="inp" @change=${(e) => this._set({ baud: Number(e.target.value) })}>
        ${[...new Set([...BAUDS, d.baud])].sort((a, b) => a - b).map((b) => html`<option value=${b} ?selected=${b === d.baud}>${b}</option>`)}</select>${this._err("baud")}</label>
      <label class="fld"><span class="lbl">${t("dataBits")} · ${t("parityF")} · ${t("stopBits")}</span>
        <div style="display:flex;gap:6px">
          <select class="inp" aria-label=${t("dataBits")} @change=${(e) => this._set({ data_bits: Number(e.target.value) })}>${[5, 6, 7, 8].map((v) => html`<option ?selected=${v === d.data_bits}>${v}</option>`)}</select>
          <select class="inp" aria-label=${t("parityF")} @change=${(e) => this._set({ parity: e.target.value })}>${["n", "e", "o", "m", "s"].map((v) => html`<option value=${v} ?selected=${v === d.parity}>${v.toUpperCase()}</option>`)}</select>
          <select class="inp" aria-label=${t("stopBits")} @change=${(e) => this._set({ stop_bits: Number(e.target.value) })}>${[1, 2].map((v) => html`<option ?selected=${v === d.stop_bits}>${v}</option>`)}</select>
        </div></label>`;
  }

  _modbusSections(chosen) {
    const d = this.draft;
    const advancedCount = MODBUS_TUNING.concat("trace").filter((k) => d[k] !== (DEFAULTS[k] ?? "off")).length;
    return html`
      <section class="card" aria-labelledby="t-mdev">
        <h2 id="t-mdev">${t("mbDevice")}</h2>
        <div class="fld"><span class="lbl" id="l-link">${t("mbLink")}</span>
          <div class="seg" role="group" aria-labelledby="l-link">${LINKS.map((l) => html`<button type="button" aria-pressed=${d.link === l ? "true" : "false"}
            @click=${() => this._set(l === "rtu" ? { link: l, device_connections: 1, device: d.device || (this.state.devices.find((x) => !x.used_by) || {}).stable || "" } : { link: l })}>${t(`link_${l}`)}</button>`)}</div>

          <span class="hint">${t(`linksub_${d.link}`)}</span></div>
        ${d.link === "rtu" ? html`${this._devicePicker(chosen)}<div class="grid2">${this._serialFormat()}</div>` : html`<div class="grid2">
          ${this._input("host", t("mbHost"), { mono: true })}${this._input("host_port", t("mbHostPort"), { number: true })}</div>
          <span class="hint">${t("mbHostHint")}</span>`}
      </section>

      <section class="card" aria-labelledby="t-proxy">
        <div><h2 id="t-proxy">${t("ifNetOnly")}</h2><p class="hint" style="margin-top:4px">${t("ifNetSub")}</p></div>
        <div class="grid2">
          ${this._input("port", t("mbPort"), { number: true, hint: t("mbPortHint") })}
          ${this._input("max_clients", t("maxClients"), { number: true, hint: t("mbClientsHint") })}
          ${this._input("request_timeout_ms", t("mbTimeout"), { number: true, hint: t("mbTimeoutHint") })}
        </div>
        ${this._input("remaddr", t("allowed"), { mono: true, hint: t("remaddrHint") })}
        ${this._input("bind", t("bind"), { mono: true, hint: t("bindHint") })}
        <span class="hint">${this._follows(d)}</span>
      </section>

      <section class="card" aria-labelledby="t-write">

        <div><h2 id="t-write">${t("mbWrite")}</h2><p class="hint" style="margin-top:4px">${t("mbWriteSub")}</p></div>
        <div class="seg" role="group" aria-labelledby="t-write">${["all", "listed", "none"].map((v) => html`<button type="button" aria-pressed=${d.write_access === v ? "true" : "false"}
          @click=${() => this._set({ write_access: v })}>${t(`wa_${v}`)}</button>`)}</div>
        <span class="hint">${t(`wasub_${d.write_access}`)}</span>
        ${d.write_access === "listed" ? this._input("write_clients", t("mbWriteClients"), { mono: true, hint: t("mbWriteClientsHint") }) : ""}
      </section>

      <section class="card" aria-labelledby="t-adv">
        <button type="button" class="toggle-head" aria-expanded=${this.advanced ? "true" : "false"} @click=${() => { this.advanced = !this.advanced; }}>
          <span><h2 id="t-adv">${t("tuning")}</h2><span class="hint">${t("tuningSubMb")}</span></span>
          <span class="chip">${advancedCount ? t("tuningSet", { n: advancedCount }) : t("tuningNone")} · ${this.advanced ? t("closeA") : t("open")}</span></button>
        ${this.advanced ? html`
          <div class="grid2">
            ${this._input("retries", t("mbRetries"), { number: true })}
            ${this._input("connect_delay_ms", t("mbConnectDelay"), { number: true, hint: d.link === "rtu" ? "" : t("mbConnectDelayHint") })}
            ${this._input("request_gap_ms", t("mbGap"), { number: true, hint: t("mbGapHint") })}
            ${this._input("cache_ms", t("mbCache"), { number: true, hint: t("mbCacheHint") })}
            ${d.link === "rtu" ? "" : this._input("device_connections", t("mbLinks"), { number: true, hint: t("mbLinksHint") })}
            ${this._input("timeout", t("mbIdle"), { number: true })}
          </div>
          <div class="grp"><h3>${t("mbProbe")}</h3><p class="hint">${t("mbProbeSub")}</p>
            <div class="grid2">
              ${this._input("probe_seconds", t("mbProbeSeconds"), { number: true })}
              ${d.probe_seconds ? html`${this._input("probe_unit", t("mbUnit"), { number: true })}
                <label class="fld"><span class="lbl">${t("mbFunction")}</span><select class="inp" @change=${(e) => this._set({ probe_function: Number(e.target.value) })}>
                  ${[3, 4].map((f) => html`<option value=${f} ?selected=${d.probe_function === f}>${t(`fc_${f}`)}</option>`)}</select></label>
                ${this._input("probe_address", t("mbAddress"), { number: true, hint: t("mbAddressHint") })}` : ""}
            </div></div>
          <div class="opts">${this._check("kickolduser", true)}${d.link === "rtu" && (chosen && chosen.ftdi || d.low_latency) ? this._check("low_latency", true) : ""}</div>
          ${this._input("unit_map", t("mbUnitMap"), { mono: true, hint: t("mbUnitMapHint") })}
          ${this._trace()}` : ""}
      </section>

      <section class="card" aria-labelledby="t-app">
        <h2 id="t-app">${t("alerts")}</h2>
        <div class="opts">${this._check("notify_missing")}${this._check("notify_no_client")}</div>
      </section>`;
  }

  _eoTemplate(k) {
    const d = this.draft, tpl = EO_TEMPLATES[k];
    const patch = { template: k, ...tpl };
    if (tpl.link === "serial" && !d.device) patch.device = (this.state.devices.find((x) => !x.used_by) || {}).stable || "";
    this._set(patch);
  }

  _eoTemplates() {
    const d = this.draft;
    return html`<section class="card" aria-labelledby="t-eotpl">
      <div><h2 id="t-eotpl">${t("eoTemplate")}</h2><p class="hint" style="margin-top:4px">${t("eoTemplateSub")}</p></div>
      <div class="choices">${Object.keys(EO_TEMPLATES).map((k) => html`<button type="button" class="choice" aria-pressed=${d.template === k ? "true" : "false"}
        @click=${() => this._eoTemplate(k)}><b style="font-weight:500">${t(`tpl_${k}`)}</b><span class="hint">${t(`tplsub_${k}`)}</span></button>`)}</div>
    </section>`;
  }

  _enoceanSections(chosen) {
    const d = this.draft;
    const serial = d.link === "serial";
    const advancedCount = ENOCEAN_ADVANCED.filter((k) => d[k]).length + ["timeout"].filter((k) => d[k]).length + (d.trace !== "off" ? 1 : 0);
    return html`
      <section class="card" aria-labelledby="t-eogw">
        <h2 id="t-eogw">${t("eoGateway")}</h2>
        <div class="grid2">
          <div class="fld"><span class="lbl" id="l-eolink">${t("eoLink")}</span>
            <div class="seg" role="group" aria-labelledby="l-eolink">${["serial", "tcp"].map((l) => html`<button type="button" aria-pressed=${d.link === l ? "true" : "false"}
              @click=${() => this._set(l === "serial" ? { link: l, device: d.device || (this.state.devices.find((x) => !x.used_by) || {}).stable || "" } : { link: l })}>${t(`eolink_${l}`)}</button>`)}</div>
            ${this._err("link")}</div>
          <div class="fld"><span class="lbl" id="l-eoproto">${t("eoProtocol")}</span>
            <div class="seg" role="group" aria-labelledby="l-eoproto">${["esp2", "esp3"].map((p) => html`<button type="button" aria-pressed=${d.esp_protocol === p ? "true" : "false"}
              @click=${() => this._set({ esp_protocol: p })}>${p.toUpperCase()}</button>`)}</div>
            <span class="hint">${t(`eoproto_${d.esp_protocol}`)}</span></div>
        </div>
        ${serial ? html`${this._devicePicker(chosen)}
          <label class="fld"><span class="lbl">${t("baud")}</span><select class="inp" @change=${(e) => this._set({ baud: Number(e.target.value) })}>
            ${[...new Set([...ENOCEAN_BAUDS, d.baud])].sort((a, b) => a - b).map((b) => html`<option value=${b} ?selected=${b === d.baud}>${b}</option>`)}</select>
            ${this._err("baud")}</label>` : html`<div class="grid2">
          ${this._input("host", t("mbHost"), { mono: true, hint: t("eoHostHint") })}${this._input("host_port", t("mbHostPort"), { number: true })}</div>`}
      </section>

      <section class="card" aria-labelledby="t-eoproxy">
        <h2 id="t-eoproxy">${t("eoProxy")}</h2>
        <div class="grid2">
          ${this._input("port", t("eoPort"), { number: true, hint: t("eoPortHint") })}
          ${this._input("max_clients", t("maxClients"), { number: true, hint: t("eoClientsHint") })}
          ${this._input("send_gap_ms", t("eoGap"), { number: true, hint: t("eoGapHint") })}
        </div>
        ${this._input("remaddr", t("allowed"), { mono: true, hint: t("eoAllowedHint") })}
        ${d.remaddr !== HA_ONLY ? html`<div><button type="button" class="btn btn-g" @click=${() => this._set({ remaddr: HA_ONLY })}>${t("eoHaOnly")}</button></div>` : ""}
        ${this._input("bind", t("bind"), { mono: true, hint: t("bindHint") })}
      </section>

      <section class="card" aria-labelledby="t-eoreplay">
        <div class="fold"><div><h2 id="t-eoreplay">${t("eoReplay")}</h2><p class="hint" style="margin-top:4px">${t("eoReplaySum", { n: d.replay_size, m: Math.round(d.replay_max_age_s / 60), p: d.replay_persist ? t("eoReplayDisk") : t("eoReplayMem") })}</p></div>
          <button type="button" class="btn btn-g" aria-expanded=${this.replayOpen ? "true" : "false"} @click=${() => { this.replayOpen = !this.replayOpen; }}>${this.replayOpen ? t("closeA") : t("changeBtn")}</button></div>
        ${this.replayOpen ? html`<p class="hint">${t("eoReplaySub")}</p>
        <div class="grid2">
          ${this._input("replay_size", t("eoReplaySize"), { number: true })}
          <label class="fld"><span class="lbl">${t("eoReplayAge")}</span>
            <input class="inp" inputmode="numeric" .value=${String(Math.round(d.replay_max_age_s / 60))} aria-describedby="e-replay_max_age_s"
              @input=${(e) => this._set({ replay_max_age_s: Number(e.target.value || 0) * 60 })}>${this._err("replay_max_age_s")}</label>
        </div>
        <label class="chk"><input type="checkbox" .checked=${!!d.replay_persist} @change=${(e) => this._set({ replay_persist: e.target.checked })}>
          <span>${t("eoPersist")}<br><span class="hint">${t("eoPersistHint")}</span></span></label>` : ""}
      </section>

      <section class="card" aria-labelledby="t-adv">
        <button type="button" class="toggle-head" aria-expanded=${this.advanced ? "true" : "false"} @click=${() => { this.advanced = !this.advanced; }}>
          <span><h2 id="t-adv">${t("eoAccess")}</h2><span class="hint">${t("eoAccessSub")}</span></span>
          <span class="chip">${t("set", { n: advancedCount })} · ${this.advanced ? t("closeA") : t("open")}</span></button>
        ${this.advanced ? html`
          <div class="opts">${this._check("kickolduser", true)}${serial && (chosen && chosen.ftdi || d.low_latency) ? this._check("low_latency", true) : ""}</div>
          ${this._input("timeout", t("mbIdle"), { number: true })}
          ${this._trace()}` : ""}
      </section>

      <section class="card" aria-labelledby="t-app">
        <h2 id="t-app">${t("alerts")}</h2>
        <div class="opts">${this._check("notify_missing")}${this._check("notify_no_client")}</div>
      </section>`;
  }

  _enoceanPreview() {
    const d = this.draft;
    const target = d.link === "serial" ? `${d.device || "–"} · ${d.baud}` : `${d.host || "–"}:${d.host_port}`;
    return html`<section class="card" aria-labelledby="t-prev">
      <div><h2 id="t-prev">${t("mbPreview")}</h2><p class="hint" style="margin-top:4px">${t("eoPreviewSub")}</p></div>
      <ol class="flow">
        <li><b>${t("mbFlowClients", { n: d.max_clients })}</b><span class="hint">${t("eoFlowClients", { p: d.port })}</span></li>
        <li><b>${t("eoFlowQueue")}</b><span class="hint">${t("eoFlowQueueSub", { ms: d.send_gap_ms })}</span></li>
        <li><b>${d.esp_protocol.toUpperCase()} · ${t(`eolink_${d.link}`)}</b><span class="hint mono" style="overflow-wrap:anywhere">${target}</span></li>
      </ol>
      <div class="note ${d.remaddr === HA_ONLY ? "info" : "warn"}">${d.remaddr === HA_ONLY ? t("eoHaOnlyNote") : t("eoLanNote", { a: d.remaddr || t("eoAllNets") })}</div>
      ${Object.keys(this._shown()).length ? html`<div class="note bad">${Object.entries(this._shown()).map(([k, v]) => html`<div><span class="mono">${k}</span>: ${fieldError(v)}</div>`)}</div>` : ""}
    </section>`;
  }

  _modbusPreview() {
    const d = this.draft;
    const target = d.link === "rtu" ? `${d.device || "–"} · ${d.baud} ${d.data_bits}${d.parity.toUpperCase()}${d.stop_bits}` : `${d.host || "–"}:${d.host_port}`;
    return html`<section class="card" aria-labelledby="t-prev">
      <div><h2 id="t-prev">${t("mbPreview")}</h2><p class="hint" style="margin-top:4px">${t("mbPreviewSub")}</p></div>
      <ol class="flow">
        <li><b>${t("mbFlowClients", { n: d.max_clients })}</b><span class="hint">Modbus TCP → ${t("port")} ${d.port}</span></li>
        <li><b>${t("mbFlowQueue")}</b><span class="hint">${t("mbFlowQueueSub", { ms: d.request_timeout_ms, n: d.retries })}</span></li>
        <li><b>${t(`link_${d.link}`)}</b><span class="hint mono" style="overflow-wrap:anywhere">${target}</span></li>
      </ol>
      ${Object.keys(this._shown()).length ? html`<div class="note bad">${Object.entries(this._shown()).map(([k, v]) => html`<div><span class="mono">${k}</span>: ${fieldError(v)}</div>`)}</div>` : ""}
    </section>`;
  }

  _deviceLabel(d) {
    const what = [d.manufacturer, d.product].filter(Boolean).join(" ") || d.driver || d.tty;
    const serial = d.serial ? `${t("serialNo")} ${d.serial}` : t("noSerial");
    const used = d.used_by && d.used_by !== this.draft.name ? ` (${t("usedBy", { n: d.used_by })})` : "";
    return `${what} · ${serial} · ${d.tty}${used}`;
  }

  render() {
    const d = this.draft;
    if (!d) return html`<p class="hint">${t("loading")}</p>`;
    const devices = this.state.devices;
    const chosen = devices.find((x) => x.stable === d.device || x.by_id.includes(d.device) || x.by_path.includes(d.device));
    const advancedCount = ADVANCED.filter((k) => d[k]).length + ["rs485", "banner", "openstr", "closestr"].filter((k) => d[k]).length + (d.extra.length ? 1 : 0) + (d.trace !== "off" ? 1 : 0);
    const isNew = !d.id;
    return html`
      <p class="crumb"><a href="#/connections">${t("connectionsTitle")}</a> › ${isNew ? t("newConnection") : d.name}</p>
      <h1 style="margin:12px 0 20px">${isNew ? t("newConnection") : t("editConnection")}</h1>
      <div class="cols"><form class="main-col" @submit=${this._save} novalidate>
        ${isNew ? html`<section class="card" aria-labelledby="t-kind">
          <div><h2 id="t-kind">${t("kind")}</h2><p class="hint" style="margin-top:4px">${t("kindSub")}</p></div>
          <div class="choices">${["serial", "modbus", "enocean"].map((k) => html`<button type="button" class="choice" aria-pressed=${d.kind === k ? "true" : "false"}
            @click=${() => this._kind(k)}><b style="font-weight:500;display:flex;align-items:center;gap:8px">${icon(k, 18)}${t(`kind_${k}`)}</b><span class="hint">${t(`kindsub_${k}`)}</span></button>`)}</div>
        </section>` : ""}
        ${d.kind !== "serial" ? html`${d.kind === "enocean" ? this._eoTemplates() : ""}<section class="card" aria-labelledby="t-base">
          <h2 id="t-base">${t("basics")}</h2>
          ${this._input("name", t("name"))}
        </section>${d.kind === "modbus" ? this._modbusSections(chosen) : this._enoceanSections(chosen)}` : html`
        <section class="card" aria-labelledby="t-tpl">
          <div><h2 id="t-tpl">${t("template")}</h2><p class="hint" style="margin-top:4px">${t("templateSub")}</p></div>
          <div class="choices">${Object.keys(TEMPLATES).map((k) => html`<button type="button" class="choice" aria-pressed=${d.template === k ? "true" : "false"}
            @click=${() => this._set({ template: k, ...TEMPLATES[k], remaddr: TEMPLATES[k].remaddr ?? (d.remaddr === ZWAVE_CLIENTS ? "" : d.remaddr) })}><b style="font-weight:500">${t(`tpl_${k}`)}</b><span class="hint">${t(`tplsub_${k}`)}</span></button>`)}</div>
        </section>

        <section class="card" aria-labelledby="t-base">
          <div><h2 id="t-base">${t("devicePick")}</h2><p class="hint" style="margin-top:4px">${t("deviceSub")}</p></div>
          ${this._devicePicker(chosen)}
          ${this._input("name", t("name"))}
        </section>

        <section class="card" aria-labelledby="t-if">
          <div><h2 id="t-if">${t("ifSerial")}</h2><p class="hint" style="margin-top:4px">${t("ifSerialSub", { f: `${d.baud} ${d.data_bits}${d.parity.toUpperCase()}${d.stop_bits}` })}</p></div>
          <div class="grid2">${this._serialFormat()}</div>
        </section>

        <section class="card" aria-labelledby="t-net">
          <div><h2 id="t-net">${t("ifNetOnly")}</h2><p class="hint" style="margin-top:4px">${t("ifNetSub")}</p></div>
          <div class="grid2">
            ${this._input("port", t("port"), { number: true, hint: t("portHint") })}
            ${this._input("max_clients", t("maxClients"), { number: true, hint: t("maxClientsHint") })}
          </div>
          <div class="fld"><span class="lbl" id="l-mode">${t("mode")}</span>
            <div class="seg" role="group" aria-labelledby="l-mode">${["raw", "rfc2217", "telnet"].map((m) => html`<button type="button" aria-pressed=${d.mode === m ? "true" : "false"} @click=${() => this._set({ mode: m })}>${m === "rfc2217" ? "RFC2217" : m}</button>`)}</div>
            <span class="hint">${t(`mode_${d.mode}`)}</span></div>
          ${this._input("remaddr", t("allowed"), { mono: true, hint: t("remaddrHint") })}
          ${this._input("bind", t("bind"), { mono: true, hint: t("bindHint") })}
          <span class="hint">${this._follows(d)}</span>
        </section>

        <section class="card" aria-labelledby="t-adv">
          <button type="button" class="toggle-head" aria-expanded=${this.advanced ? "true" : "false"} @click=${() => { this.advanced = !this.advanced; }}>
            <span><h2 id="t-adv">${t("advanced")}</h2><span class="hint">${t("advancedSub")}</span></span>
            <span class="chip">${t("set", { n: advancedCount })} · ${this.advanced ? t("closeA") : t("open")}</span></button>
          ${this.advanced ? html`
            <fieldset><legend>${t("appSide")}</legend>
              <div class="opts">${this._check("keep_open")}</div>
              ${this._trace()}</fieldset>
            <fieldset><legend>${t("serialSide")}</legend>
              <div class="opts">${["local", "rtscts", "xonxoff", "hangup_when_done", "nobreak"].map((k) => this._check(k))}
                ${chosen && chosen.ftdi || d.low_latency ? this._check("low_latency") : ""}</div>
              <div class="grid2">
                ${["dtr", "rts"].map((k) => html`<label class="fld"><span class="lbl">${t(k)}</span><select class="inp" @change=${(e) => this._set({ [k]: e.target.value })}>
                  ${[["", t("lineDefault")], ["on", t("on")], ["off", t("off")]].map(([v, l]) => html`<option value=${v} ?selected=${d[k] === v}>${l}</option>`)}</select></label>`)}
                ${this._input("rs485", t("rs485"), { mono: true, hint: t("rs485Hint") })}
              </div></fieldset>
            <fieldset><legend>${t("connectionSide")}</legend>
              <div class="opts">${this._check("kickolduser")}${this._check("chardelay")}</div>
              <div class="grid2">${this._input("timeout", t("timeout"), { number: true })}${this._input("connector_retry_time", t("retry"), { number: true })}</div>
              <div class="grid2">${this._input("banner", t("banner"))}${this._input("openstr", t("openstr"), { mono: true })}${this._input("closestr", t("closestr"), { mono: true })}</div>
            </fieldset>
            <fieldset><legend>${t("tcpSide")}</legend>
              <div class="opts">${this._check("nodelay")}</div>
            </fieldset>
            <label class="fld"><span class="lbl">${t("extra")}</span>
              <textarea class="inp mono" rows="3" .value=${this.extraRaw} aria-invalid=${this._shown().extra ? "true" : "false"}
                @input=${(e) => { this.extraRaw = e.target.value; this._set({ extra: parseExtra(e.target.value) }); }}></textarea>
              ${this._err("extra")}<span class="hint">${t("extraHint")}</span></label>` : ""}
        </section>

        <section class="card" aria-labelledby="t-app">
          <h2 id="t-app">${t("alerts")}</h2>
          <div class="opts">${this._check("notify_missing")}${this._check("notify_no_client")}${this._check("stuck_disconnect")}</div>
          ${this._input("silence_minutes", t("silence"), { number: true })}
        </section>`}

        <section class="card" aria-labelledby="t-on">
          <div class="fold"><div><h2 id="t-on">${isNew ? t("startNow") : t("enabled")}</h2><p class="hint" style="margin-top:4px">${isNew ? t("startNowSub") : t("enabledSub")}</p></div>
            ${toggle(d.enabled, isNew ? t("startNow") : t("enabled"), (v) => this._set({ enabled: v }))}</div>
        </section>

        <div class="actions">
          ${isNew ? "" : html`<button type="button" class="btn btn-d" @click=${this._delete}>${t("delete")}</button>`}
          <span class="hint" style="display:flex;align-items:center;gap:8px;flex:1 1 240px;justify-content:flex-end">${icon("info", 16)}${isNew ? t("saveHintNew") : t("saveHint")}</span>
          <div style="display:flex;gap:8px;margin-left:auto">
            <a class="btn btn-g" href=${isNew ? "#/connections" : `#/connection/${d.id}`}>${t("cancel")}</a>
            <button type="submit" class="btn btn-p" ?disabled=${this.saving}>${t("save")}</button>
          </div>
        </div>
      </form>

      <aside class="side-col">
        ${d.kind === "modbus" ? this._modbusPreview() : d.kind === "enocean" ? this._enoceanPreview() : html`<section class="card" aria-labelledby="t-prev">
          <div><h2 id="t-prev">${t("preview")}</h2><p class="hint" style="margin-top:4px">${t("previewSub")}</p></div>
          <div class="code">${this.yaml || "…"}</div>
          ${Object.keys(this._shown()).length ? html`<div class="note bad">${Object.entries(this._shown()).map(([k, v]) => html`<div><span class="mono">${k}</span>: ${fieldError(v)}</div>`)}</div>` : ""}
        </section>`}
      </aside></div>`;
  }
}
