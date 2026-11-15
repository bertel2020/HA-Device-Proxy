// The page frame: header with the sections, the router (#/…), and the app state every page reads.
// The state is polled every 2 s while the page is visible; events since the last seen one come with it.
import { LitElement, css, html } from "lit";
import { api } from "./api.js";
import { lang, setClientNames, setLang, t } from "./i18n.js";
import { base, tokens } from "./styles.js";
import { applyTheme, look, MODES, SCHEMES, setLook, SIZES } from "./theme.js";
import { confirmDialog, connectionState, focused, icon, logo, recordRates, trapTab } from "./ui.js";

const POLL_MS = 2000;
const POLL_TIMEOUT_MS = 10000;
const EVENTS_KEPT = 1500;

export class DeviceProxyApp extends LitElement {
  static properties = {
    state: { state: true },
    events: { state: true },
    route: { state: true },
    offline: { state: true },
    toast: { state: true },
    importOpen: { state: true },
    lookOpen: { state: true },
  };

  static styles = [tokens, base, css`
    :host { display: block; min-height: 100vh; background: var(--bg); }
    header { position: sticky; top: 0; z-index: 5; background: color-mix(in srgb, var(--surface) 88%, transparent); backdrop-filter: blur(12px);
      -webkit-backdrop-filter: blur(12px); border-bottom: 1px solid var(--line); }
    .bar { max-width: 1200px; margin: 0 auto; padding: 0 24px; display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: 0 24px; }
    .brand { display: flex; flex-wrap: wrap; align-items: center; gap: 6px 12px; padding: 10px 0; min-height: 60px; min-width: 0; flex: 1 1 0; }
    /* the title gives way first: its chips wrap under the name, so the tabs and the button stay on the row */
    .brand .name { flex: none; }
    /* one line under the name: what runs, and the version; ser2net's version in the tooltip. The problems count stands at the tab. */
    .status { display: flex; align-items: center; gap: 6px; font-size: calc(13px * var(--fs, 1)); white-space: nowrap; }
    .status.ok { color: var(--ok); } .status.bad { color: var(--bad); }
    .status .ver { color: var(--muted); }
    .brand .name { display: flex; flex-direction: column; }
    .brand b { font-size: calc(18px * var(--fs, 1)); display: block; line-height: 1.2; white-space: nowrap; }
    /* the sections as tabs with a line under the chosen one, as in fritzbox-network */
    nav { flex: none; display: flex; gap: 4px; align-self: stretch; max-width: 100%; overflow-x: auto; scrollbar-width: none; }
    nav a { display: inline-flex; align-items: center; gap: 8px; min-height: 56px; padding: 0 14px; font-weight: 500; color: var(--muted); text-decoration: none; white-space: nowrap;
      border-bottom: 2px solid transparent; margin-bottom: -1px; transition: color .15s, border-color .15s; }
    nav a:hover { color: var(--text); }
    nav a[aria-current="page"] { color: var(--accent-hover); border-bottom-color: var(--accent); }
    nav a svg { opacity: .85; }
    nav .count { display: inline-grid; place-items: center; min-width: 20px; height: 20px; padding: 0 6px; border-radius: 10px; background: var(--warn-soft); color: var(--warn);
      font-size: max(10.5px, calc(11px * var(--fs, 1))); font-weight: 600; line-height: 1; }
    .end { display: flex; align-items: center; gap: 4px; }
    .iconbtn { display: inline-grid; place-items: center; width: 40px; height: 40px; border-radius: 50%; border: none; background: none; color: var(--muted); cursor: pointer; padding: 0; }
    .iconbtn:hover, .iconbtn[aria-expanded="true"] { background: var(--accent-soft); color: var(--accent-hover); }
    /* outside the header, whose blur would hold fixed boxes inside itself; the scrim takes the click that closes the menu */
    .scrim { position: fixed; inset: 0; z-index: 7; }
    .lookmenu { position: fixed; top: 64px; right: max(16px, calc((100vw - 1200px) / 2 + 24px)); z-index: 8; width: 300px; max-width: calc(100vw - 32px); max-height: calc(100vh - 92px); overflow: auto; padding: 8px;
      background: var(--surface); border: 1px solid var(--line); border-radius: 14px; box-shadow: 0 10px 30px var(--shadow-c); }
    .lookmenu .label { display: block; padding: 8px 10px 4px; }
    .lookmenu [role="group"] + .label { margin-top: 4px; border-top: 1px solid var(--line-2); padding-top: 12px; }
    .lookmenu button { display: flex; width: 100%; align-items: center; gap: 10px; min-height: 40px; padding: 0 10px; border: none; border-radius: 8px; background: none;
      font: inherit; color: var(--text); text-align: left; cursor: pointer; }
    .lookmenu button:hover { background: var(--surface-2); }
    .lookmenu button[aria-checked="true"] { background: var(--accent-soft); color: var(--accent-hover); font-weight: 500; }
    .swatch { width: 14px; height: 14px; border-radius: 50%; border: 1px solid var(--muted); flex: none; }
    .swatch.ozean { background: #0a6aa8; } .swatch.wald { background: #0f7a6b; } .swatch.graphit { background: #2f3a48; }
    main { max-width: 1200px; margin: 0 auto; padding: 24px 24px 56px; }
    .offline { max-width: 1200px; margin: 12px auto 0; padding: 0 24px; }
    .toast { position: fixed; left: 50%; bottom: 24px; transform: translateX(-50%); background: var(--text); color: var(--surface);
      padding: 12px 18px; border-radius: 12px; box-shadow: 0 4px 16px rgba(0,0,0,.25); max-width: min(560px, calc(100vw - 32px)); z-index: 10; }
    /* the sections and the button need about 900 px beside the title; below that the tabs get a row of their own */
    @media (max-width: 960px) { nav { order: 3; flex: 1 1 100%; } nav a { min-height: 44px; } }
    @media (max-width: 600px) {
      :host { --nav-b: calc(60px + env(safe-area-inset-bottom, 0px)); }
      /* a backdrop-filter would hold the fixed bar inside the header */
      header { backdrop-filter: none; -webkit-backdrop-filter: none; background: var(--surface); }
      .bar, main, .offline { padding-left: 16px; padding-right: 16px; }
      /* the button stays beside the title; the chips wrap under the name instead */
      .bar { flex-wrap: nowrap; gap: 0 8px; }
      main { padding-bottom: calc(var(--nav-b) + 32px); }
      nav { position: fixed; left: 0; right: 0; bottom: 0; z-index: 6; gap: 2px; padding: 4px 4px max(4px, env(safe-area-inset-bottom, 0px)); overflow: visible;
        order: 0; background: var(--surface); border-top: 1px solid var(--line); }
      nav a { position: relative; flex: 1 1 0; min-width: 0; flex-direction: column; justify-content: center; gap: 2px; min-height: 52px; height: 52px; padding: 4px 2px;
        border-radius: 14px; border-bottom: none; margin-bottom: 0; font-size: max(10.5px, calc(11px * var(--fs, 1))); }
      nav a span.nl { max-width: 100%; overflow: hidden; text-overflow: ellipsis; }
      nav a[aria-current="page"] { background: var(--accent-soft); }
      nav a svg { width: 22px; height: 22px; opacity: 1; }
      nav .count { position: absolute; top: 4px; left: calc(50% + 6px); min-width: 16px; height: 16px; padding: 0 4px; font-size: 10px; box-shadow: 0 0 0 2px var(--surface); }
      .lookmenu { position: fixed; top: auto; left: 0; right: 0; bottom: 0; width: auto; max-width: none; max-height: 85vh; border-radius: 16px 16px 0 0; padding: 8px 12px 20px; }
      .scrim { background: rgb(0 0 0 / 35%); }
      .lookmenu button { min-height: 48px; }
      .toast { bottom: calc(var(--nav-b) + 16px); }
    }
  `];

  constructor() {
    super();
    this.state = null;
    this.events = [];
    this.offline = false;
    this.toast = "";
    this._seq = 0;
    this.importOpen = false;
    this.lookOpen = false;
    this.route = this._parse();
    this._hash = location.hash;
    this._onHash = () => this._leave();
  }

  _lookMenu() {
    const now = look();
    const group = (label, key, values) => html`<span class="label" aria-hidden="true">${t(label)}</span>
      <div role="group" aria-label=${t(label)}>${values.map((v) => html`<button role="menuitemradio" aria-checked=${now[key] === v ? "true" : "false"}
        @click=${() => { setLook({ [key]: v }); this.requestUpdate(); this._relayLang(); }}>${key === "scheme" ? html`<i class="swatch ${v}"></i>` : ""}${t(`${key}_${v}`)}</button>`)}</div>`;
    return html`<div class="scrim" @click=${() => { this.lookOpen = false; }}></div>
      <div class="lookmenu" id="lookmenu" role="menu" aria-label=${t("lookTitle")}
        @keydown=${(e) => { if (e.key === "Escape") { this.lookOpen = false; this.renderRoot.querySelector("#lookbtn")?.focus(); } }}>
        ${group("lookScheme", "scheme", SCHEMES)}${group("lookMode", "mode", MODES)}${group("lookSize", "size", Object.keys(SIZES))}
      </div>`;
  }

  updated(changed) {
    if (changed.has("lookOpen") && this.lookOpen) this.renderRoot.querySelector('.lookmenu [aria-checked="true"]')?.focus();
  }

  /** Going to another page: a form with unsaved changes asks first. */
  async _leave() {
    if (this._asking) return;
    const page = this.renderRoot?.querySelector("main > *");
    if (location.hash !== this._hash && page?._dirty?.()) {
      const target = location.hash;
      history.replaceState(null, "", this._hash || "#/");  // stay on the form while asking
      this._asking = true;
      const leave = await confirmDialog(page, t(page.discardText || "discardConfirm"), t("discard"));
      this._asking = false;
      if (!leave) return;
      page.discard?.();
      history.replaceState(null, "", target);
    }
    this._hash = location.hash;
    this.route = this._parse();
    window.scrollTo(0, 0);
  }

  connectedCallback() {
    super.connectedCallback();
    window.addEventListener("hashchange", this._onHash);
    this.addEventListener("dp-refresh", () => this.refresh());
    this.addEventListener("dp-toast", (e) => this.showToast(e.detail));
    this.addEventListener("dp-import-open", () => { this.importOpen = true; });
    this.addEventListener("dp-import-close", () => { this.importOpen = false; });
    this.addEventListener("dp-lang", (e) => { setLang(e.detail); document.documentElement.lang = e.detail; this.requestUpdate(); this._relayLang(); });
    document.documentElement.lang = lang;
    this._loadHistory();
    this.refresh();
    this._onVisible = () => { if (!document.hidden) { applyTheme(); this.refresh(); } };
    document.addEventListener("visibilitychange", this._onVisible);
    applyTheme();
    // a tick while the last request still runs is left out
    this._timer = setInterval(() => { if (!document.hidden && !this._polling) { applyTheme(); this.refresh(); } }, POLL_MS);
  }

  disconnectedCallback() {
    super.disconnectedCallback();
    window.removeEventListener("hashchange", this._onHash);
    document.removeEventListener("visibilitychange", this._onVisible);
    clearInterval(this._timer);
  }

  _relayLang() {
    this.renderRoot.querySelectorAll("main > *").forEach((el) => el.requestUpdate && el.requestUpdate());
  }

  _parse() {
    const parts = (location.hash.replace(/^#\/?/, "") || "connections").split("/");
    if (parts[0] === "import") {  // the old page address: the dialog over the connections
      this.importOpen = true;
      history.replaceState(null, "", "#/connections");
      return { page: "connections", id: "" };
    }
    let search = parts[2] || "";
    try { search = decodeURIComponent(search); } catch { /* a cut or typed address: as it is */ }
    return { page: parts[0], id: parts[1] || "", search };
  }

  async _loadHistory() {
    try {
      const history = await api("api/history?limit=300");
      const known = new Set(this.events.map((e) => e.id));
      this.events = [...history.reverse().filter((e) => !known.has(e.id)), ...this.events];
    } catch { /* the live events still come */ }
  }

  /** One status request at a time, so an older answer never overwrites a newer one; a refresh
   *  asked for meanwhile (after a save) follows it. */
  async refresh() {
    if (this._polling) { this._again = true; return; }
    this._polling = true;
    try { await this._poll(); } finally { this._polling = false; }
    if (this._again) { this._again = false; this.refresh(); }
  }

  async _poll() {
    try {
      const opts = { timeout: POLL_TIMEOUT_MS };
      const [state, events] = await Promise.all([api("api/state", opts), api(`api/events?after=${this._seq}`, opts)]);
      recordRates(state.connections);
      if (this._boot && state.boot !== this._boot) {  // the app restarted: its numbers start over
        this._seq = 0;
        this.events = [];
        this._loadHistory();
      }
      this._boot = state.boot;
      setClientNames(state.settings.client_names, state.lan_ip);
      this.state = state;
      if (events.length) {
        this._seq = events[events.length - 1].seq;
        const byId = new Map(this.events.map((e, i) => [e.id ?? `s${e.seq}`, i]));
        const list = [...this.events];
        for (const e of events) {
          const key = e.id ?? `s${e.seq}`;
          // a repeat only counts on: the row stays as it was written, as in the history
          if (byId.has(key)) { const old = list[byId.get(key)]; list[byId.get(key)] = { ...old, count: Math.max(old.count, e.count), last_ts: Math.max(old.last_ts, e.ts), seq: e.seq }; }
          else { byId.set(key, list.length); list.push(e); }
        }
        this.events = list.slice(-EVENTS_KEPT);
      }
      this.offline = false;
    } catch {
      this.offline = true;
    }
  }

  showToast(text) {
    this.toast = text;
    clearTimeout(this._toastTimer);
    this._toastTimer = setTimeout(() => { this.toast = ""; }, 4500);
  }

  _page() {
    const { page, id } = this.route;
    const s = this.state, ev = this.events;
    if (!s) return html`<p class="hint">${t("loading")}</p>`;
    switch (page) {
      case "connection": return html`<dp-detail .state=${s} .events=${ev} .connectionId=${id}></dp-detail>`;
      case "edit": return html`<dp-edit .state=${s} .connectionId=${id}></dp-edit>`;
      case "events": return html`<dp-events .state=${s} .events=${ev} .preset=${id} .search=${this.route.search}></dp-events>`;
      case "trace": return html`<dp-trace .state=${s} .selected=${id}></dp-trace>`;
      case "settings": return html`<dp-settings .state=${s} .section=${id}></dp-settings>`;
      default: return html`<dp-connections .state=${s}></dp-connections>`;
    }
  }

  render() {
    const s = this.state;
    const page = this.route.page;
    const section = ["connection", "edit"].includes(page) ? "connections" : page;
    const tab = (key, label, symbol, count = 0) => html`<a href="#/${key}" aria-current=${section === key ? "page" : "false"}>${icon(symbol, 16)}<span
      class="nl">${t(label)}</span>${count ? html`<span class="count" aria-label=${t("problems", { n: count })}>${count}</span>` : ""}</a>`;
    const running = s && s.ser2net_running;
    // ser2net only matters with serial connections (or the own ser2net.yaml)
    const serial = s && (s.source === "custom" || s.connections.some((c) => c.kind === "serial"));
    const problems = s ? s.connections.filter((c) => connectionState(c, running)[1] === "bad").length : 0;
    return html`
      <header><div class="bar">
        <div class="brand">${logo()}<div class="name"><b>${t("appTitle")}</b>
          ${s ? html`<span class="status ${serial && !running ? "bad" : "ok"}" title=${`App ${s.version}${serial ? ` · ser2net ${s.ser2net_version || "?"}` : ""}`}><span
            class="dot"></span>${t(serial ? (running ? "running" : "notRunning") : "appRunning")}<span class="ver">· App ${s.version}</span></span>` : ""}</div>
          ${s && s.capture ? html`<a class="chip info" href="#/connection/${s.capture.connection}" style="text-decoration:none"><span class="dot"></span>${t("captureChip", { n: s.capture.name })}</a>` : ""}
        </div>

        <nav aria-label=${t("navMain")}>
          ${tab("connections", "navConnections", "plug", problems)}${tab("events", "navEvents", "list")}${tab("trace", "navTrace", "pulse")}${tab("settings", "navSettings", "sliders")}
        </nav>
        <div class="end">
          <button class="iconbtn" id="lookbtn" aria-haspopup="menu" aria-expanded=${this.lookOpen ? "true" : "false"} aria-controls="lookmenu"
            title=${t("lookTitle")} aria-label=${t("lookTitle")} @click=${() => { this.lookOpen = !this.lookOpen; }}>${icon("palette", 22)}</button>
        </div>
      </div></header>
      ${this.lookOpen ? this._lookMenu() : ""}
      ${this.offline ? html`<div class="offline"><div class="note warn" role="status">${t("connectionLost")}</div></div>` : ""}
      <main>${this._page()}</main>
      ${this.importOpen && s ? html`<dp-import .state=${s}></dp-import>` : ""}
      ${this.toast ? html`<div class="toast" role="status">${this.toast}</div>` : ""}`;
  }
}

/** Base for the pages: shared styles and helpers to talk to the frame. */
export class Page extends LitElement {
  static styles = [tokens, base, css`:host { display: block; } .head { display: flex; flex-wrap: wrap; align-items: flex-end; justify-content: space-between; gap: 16px; margin-bottom: 20px; }`];

  refresh() { this.dispatchEvent(new CustomEvent("dp-refresh", { bubbles: true, composed: true })); }

  toast(text) { this.dispatchEvent(new CustomEvent("dp-toast", { detail: text, bubbles: true, composed: true })); }

  connection(id) { return this.state?.connections.find((c) => c.id === id); }
}

export class DeviceProxyConfirm extends LitElement {
  static properties = { message: {}, confirmLabel: {}, text: {}, hintText: {} };

  static styles = [tokens, base, css`
    .back { position: fixed; inset: 0; background: rgba(0,0,0,.4); display: flex; align-items: center; justify-content: center; z-index: 20; padding: 16px; }
    .box { background: var(--surface); border-radius: 16px; padding: 24px; max-width: 440px; width: 100%; display: flex; flex-direction: column; gap: 20px; }
    .actions { display: flex; justify-content: flex-end; gap: 8px; }
  `];

  firstUpdated() {
    this._before = focused();  // gets the focus back when the dialog closes
    (this.renderRoot.querySelector("input") || this.renderRoot.querySelector(".btn-g")).focus();
  }

  _done(value) {
    this._before?.focus?.();
    this.dispatchEvent(new CustomEvent("done", { detail: value }));
  }

  render() {
    return html`<div class="back" @keydown=${(e) => { if (e.key === "Escape") this._done(false); else trapTab(e, this.renderRoot.querySelector(".box")); }}>
      <div class="box" role="alertdialog" aria-modal="true" aria-label=${t("confirm")}>
        <p>${this.message}</p>
        ${this.text === undefined ? "" : html`<input class="inp" maxlength="40" aria-label=${this.message} .value=${this.text} placeholder=${this.hintText || ""}
          @keydown=${(e) => { if (e.key === "Enter") this._done(e.target.value); }}>`}
        <div class="actions"><button class="btn btn-g" @click=${() => this._done(false)}>${t("cancel")}</button>
          <button class="btn btn-p" @click=${() => this._done(this.text === undefined ? true : this.renderRoot.querySelector("input").value)}>${this.confirmLabel}</button></div>
      </div></div>`;
  }
}
