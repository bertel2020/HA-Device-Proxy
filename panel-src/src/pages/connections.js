import { css, html } from "lit";
import { api } from "../api.js";
import { Page } from "../app.js";
import { t } from "../i18n.js";
import { connectionState, copyText, fmtAgo, fmtRate, fmtSerial, icon, primaryAddress, proxyTarget, toggle } from "../ui.js";

const KINDS = ["serial", "modbus", "enocean"];
const FILTER_KEY = "device_proxy.filter";

export class ConnectionsPage extends Page {
  static properties = { state: { attribute: false }, copied: { state: true }, busy: { state: true }, filter: { state: true } };

  static styles = [...Page.styles, css`
    .tiles { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 12px; margin-bottom: 20px; }
    .tile { background: var(--surface); border: 1px solid var(--line); border-radius: 16px; padding: 16px 20px; }
    .tile b { display: block; font-size: 28px; font-weight: 500; margin-top: 4px; }
    .tile small { font-size: 15px; color: var(--muted); font-weight: 400; }
    .cards { display: grid; grid-template-columns: repeat(auto-fill, minmax(min(100%, 480px), 1fr)); gap: 16px; }
    .conn.off { background: var(--surface-2); }
    .conn.missing { border-color: var(--bad-line); }
    .top { display: flex; align-items: flex-start; justify-content: space-between; gap: 16px; }
    .title { display: flex; flex-wrap: wrap; align-items: center; gap: 10px; }
    .title h2 { font-size: 18px; }
    .dev { font-size: 12px; color: var(--muted); overflow-wrap: anywhere; margin-top: 6px; }
    .chips { display: flex; flex-wrap: wrap; gap: 6px; }
    .clients { border-top: 1px solid var(--line-2); padding-top: 12px; display: flex; flex-direction: column; gap: 8px; }
    .client { display: flex; flex-wrap: wrap; justify-content: space-between; gap: 4px 12px; }
    .foot { display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: 8px; margin-top: auto; }
    .addr { display: flex; align-items: center; gap: 4px; background: var(--surface-2); border-radius: 10px; padding: 2px 2px 2px 12px; min-width: 0; max-width: 100%; }
    .addr .mono { font-size: 13px; overflow-wrap: anywhere; }
    .empty { text-align: center; padding: 48px 20px; align-items: center; }
    .filters { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 16px; }
    .filters button { min-height: 32px; padding: 0 12px; border-radius: 16px; border: 1px solid var(--input-line); background: var(--surface);
      color: var(--text); font: inherit; font-size: 13px; cursor: pointer; display: inline-flex; align-items: center; gap: 6px; }
    .filters button[aria-pressed="true"] { background: var(--accent-soft); border-color: var(--accent); color: var(--accent-hover); }
  `];

  constructor() {
    super();
    try { this.filter = localStorage.getItem(FILTER_KEY) || "all"; } catch { this.filter = "all"; }
  }

  _filter(kind) {
    this.filter = kind;
    try { localStorage.setItem(FILTER_KEY, kind); } catch { /* private window */ }
  }

  async _enable(c, enabled) {
    this.busy = c.id;
    try {
      await api(`api/connections/${c.id}/enabled`, { method: "POST", body: { enabled } });
      this.refresh();
    } catch (err) {
      this.toast(`${t("error")}: ${err.message}`);
    } finally {
      this.busy = "";
    }
  }

  async _copy(c) {
    if (await copyText(primaryAddress(c))) {
      this.copied = c.id;
      setTimeout(() => { if (this.copied === c.id) this.copied = ""; }, 2000);
    }
  }

  _card(c, running, own) {
    if (c.kind !== "serial") own = false; // the app's own proxies work with an own ser2net.yaml too
    const [stateKey, stateClass] = connectionState(c, running);
    const off = !c.enabled, missing = c.enabled && c.present === false;
    const errors = c.line_errors ? Object.values(c.line_errors).reduce((a, b) => a + b, 0) : 0;
    const modbus = c.kind === "modbus", m = c.modbus || {};
    const enocean = c.kind === "enocean", eo = c.enocean;
    const proxied = c.kind !== "serial";
    const chips = modbus ? [t(`link_${c.link}`), `Port ${c.port}`]
      : enocean ? [`${c.esp_protocol.toUpperCase()} · ${c.link === "serial" ? c.baud : "TCP"}`, `Port ${c.port}`]
      : [fmtSerial(c), c.mode, `Port ${c.port}`];
    if (modbus && c.link === "rtu") chips.splice(1, 0, fmtSerial(c));
    if (modbus && m.answered) chips.push(t("mbAvg", { ms: m.time_avg_ms }));
    if (enocean && eo) chips.push(t("eoDutyChip", { p: eo.duty_cycle.of_limit.toLocaleString() }));
    if (enocean && eo && eo.base_id) chips.push(`ID ${eo.base_id}`);
    if (c.nodelay && !proxied) chips.push("nodelay");
    if (c.latency === "set" || c.latency === "already") chips.push("FTDI 1 ms");
    if (c.trace !== "off") chips.push(t("recording", { m: t(`tr_${c.trace}`) }));
    const stuck = c.clients.filter((cl) => cl.stuck);
    return html`<section class="card conn ${off ? "off" : ""} ${missing ? "missing" : ""}" aria-label=${c.name}>
      <div class="top">
        <div style="min-width:0">
          <div class="title"><span class="hint" style="display:flex" title=${t(`kind_${c.kind}`)}>${icon(c.kind, 20)}</span><h2>${c.name}</h2><span class="chip ${stateClass}"><span class="dot"></span>${t(stateKey)}</span></div>
          <div class="dev mono">${proxied ? proxyTarget(c) : c.device}${c.tty && c.tty !== c.device ? html` → ${c.tty}` : ""}</div>
        </div>
        ${toggle(c.enabled, t("switchLabel", { name: c.name }), (v) => this._enable(c, v), own || this.busy === c.id)}
      </div>
      <div class="chips">
        ${chips.map((x) => html`<span class="chip">${x}</span>`)}
        ${c.kept_open ? html`<span class="chip info">${t("keptOpen")}</span>` : ""}
        ${enocean && c.clients.some((cl) => cl.replay) ? html`<span class="chip info">${t("eoReplayChip")}</span>` : ""}
        ${enocean && eo && eo.duty_cycle.of_limit >= 80 ? html`<span class="chip bad">${t("eoDutyHigh")}</span>` : ""}
        ${errors ? html`<span class="chip warn">${t("lineErrors", { n: errors })}</span>` : ""}
        ${c.latency === "read_only" ? html`<span class="chip warn">${t("latencyRO")}</span>` : ""}
        ${modbus && m.failed ? html`<span class="chip warn">${t("mbFailedN", { n: m.failed })}</span>` : ""}
        ${stuck.map((cl) => html`<span class="chip bad">${t("stuck", { a: cl.address })}</span>`)}
      </div>
      <div class="clients">
        <div class="row hint" style="font-weight:500"><span>${t("clients")}</span>
          <span>${t("clientsOf", { n: c.clients.length, m: c.max_clients })}${c.enabled && (c.present || proxied) ? html` · ${fmtRate(c.rate_from_device)}` : ""}</span></div>
        ${c.clients.map((cl) => html`<div class="client"><span><span class="mono" style="font-size:13px">${cl.address}</span></span>
          <span class="hint">${cl.since ? t("since", { t: fmtAgo(cl.since) }) : ""}</span></div>`)}
        ${c.clients.length ? "" : html`<div class="hint" style="font-size:14px">${off ? t("disabledText") : missing ? t("missingText") : proxied && (c[c.kind] || {}).reachable === false ? t(enocean ? "eoDownText" : "mbDownText", { e: (c[c.kind] || {}).last_error || "?" }) : t("noClients")}</div>`}
      </div>
      <div class="foot">
        <div class="addr"><span class="mono">${primaryAddress(c)}</span>
          <button class="btn btn-g" style="min-height:36px" @click=${() => this._copy(c)} aria-label=${t("copy")}>${icon("copy", 16)}${this.copied === c.id ? t("copied") : t("copy")}</button></div>
        <div style="display:flex;gap:4px"><a class="btn btn-g" href="#/edit/${c.id}">${t("edit")}</a><a class="btn btn-s" href="#/connection/${c.id}">${t("details")}</a></div>
      </div>
    </section>`;
  }

  render() {
    const s = this.state;
    const own = s.source === "custom";
    const all = s.connections;
    const counts = Object.fromEntries(KINDS.map((k) => [k, all.filter((c) => c.kind === k).length]));
    const filter = this.filter !== "all" && counts[this.filter] ? this.filter : "all";
    const list = filter === "all" ? all : all.filter((c) => c.kind === filter);
    const active = all.filter((c) => c.enabled).length;
    const clients = all.reduce((n, c) => n + c.clients.length, 0);
    const errors = all.reduce((n, c) => n + (c.line_errors ? Object.values(c.line_errors).reduce((a, b) => a + b, 0) : 0), 0);
    return html`
      <div class="head">
        <div><h1>${t("connectionsTitle")}</h1><p class="sub">${t("connectionsSub")}</p></div>
        <div style="display:flex;flex-wrap:wrap;gap:8px">
          <a class="btn btn-s" href="#/import">${icon("upload")}${t("importExport")}</a>
          <a class="btn btn-p" href="#/edit/new">${icon("plus")}${t("addConnection")}</a>
        </div>
      </div>
      ${own ? html`<div class="note info" style="margin-bottom:20px">
        <b>${t("customActive")}</b> · ${t("customActiveText")}
        ${s.custom_ports.map((p) => html` <span class="chip">${p.alias} · ${p.clients.length}</span>`)}
        · <a href="#/settings">${t("toSettings")}</a></div>` : ""}
      <div class="tiles">
        <div class="tile"><span class="lbl">${t("tileActive")}</span><b>${active} <small>${t("tileOf", { n: all.length })}</small></b></div>
        <div class="tile"><span class="lbl">${t("tileClients")}</span><b>${clients}</b></div>
        <div class="tile"><span class="lbl">${t("tileErrors")}</span><b style=${errors ? "color:var(--warn)" : ""}>${errors}</b></div>
        <div class="tile"><span class="lbl">${t("tileReach")}</span><b style="font-size:16px;margin-top:10px">${t(`listen_${s.settings.listen}`)}</b></div>
      </div>
      ${KINDS.filter((k) => counts[k]).length > 1 ? html`<div class="filters" role="group" aria-label=${t("filterLabel")}>
        <button aria-pressed=${filter === "all" ? "true" : "false"} @click=${() => this._filter("all")}>${t("filterAll", { n: all.length })}</button>
        ${KINDS.filter((k) => counts[k]).map((k) => html`<button aria-pressed=${filter === k ? "true" : "false"} @click=${() => this._filter(k)}>${icon(k, 16)}${t(`filter_${k}`, { n: counts[k] })}</button>`)}
      </div>` : ""}
      ${list.length ? html`<div class="cards">${list.map((c) => this._card(c, s.ser2net_running, own))}</div>` : html`
        <section class="card empty"><h2>${t("emptyTitle")}</h2><p class="hint" style="font-size:14px">${t("emptyText")}</p>
          <div style="display:flex;flex-wrap:wrap;gap:8px;justify-content:center">
            <a class="btn btn-s" href="#/import">${icon("upload")}${t("emptyImport")}</a>
            <a class="btn btn-p" href="#/edit/new">${icon("plus")}${t("addConnection")}</a></div></section>`}`;
  }
}
