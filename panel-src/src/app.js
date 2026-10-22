// The page frame: header with the sections, the router (#/…), and the app state every page reads.
// The state is polled every 2 s while the page is visible; events since the last seen one come with it.
import { LitElement, css, html } from "lit";
import { api } from "./api.js";
import { lang, setLang, t } from "./i18n.js";
import { base, tokens } from "./styles.js";
import { applyTheme } from "./theme.js";
import { connectionState, logo } from "./ui.js";

const POLL_MS = 2000;
const EVENTS_KEPT = 1500;

export class DeviceProxyApp extends LitElement {
  static properties = {
    state: { state: true },
    events: { state: true },
    route: { state: true },
    offline: { state: true },
    toast: { state: true },
    importOpen: { state: true },
  };

  static styles = [tokens, base, css`
    :host { display: block; min-height: 100vh; background: var(--bg); }
    header { position: sticky; top: 0; z-index: 5; background: color-mix(in srgb, var(--surface) 88%, transparent); backdrop-filter: blur(12px);
      -webkit-backdrop-filter: blur(12px); border-bottom: 1px solid var(--line); }
    .bar { max-width: 1200px; margin: 0 auto; padding: 0 24px; display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: 0 24px; }
    .brand { display: flex; flex-wrap: wrap; align-items: center; gap: 6px 12px; padding: 12px 0; min-width: 0; }
    .brand .name { display: flex; flex-direction: column; }
    .brand b { font-size: 18px; display: block; line-height: 1.2; white-space: nowrap; }
    nav { display: flex; gap: 4px; padding: 8px 0; max-width: 100%; overflow-x: auto; scrollbar-width: none; }
    nav a { display: inline-flex; align-items: center; min-height: 40px; padding: 0 16px; font-weight: 500; color: var(--muted); text-decoration: none; border-radius: 20px; transition: background .15s, color .15s; }
    nav a:hover { color: var(--text); background: var(--neutral-soft); }
    nav a[aria-current="page"] { color: var(--accent-hover); background: var(--accent-soft); }
    main { max-width: 1200px; margin: 0 auto; padding: 28px 24px 56px; }
    .offline { max-width: 1200px; margin: 12px auto 0; padding: 0 24px; }
    .toast { position: fixed; left: 50%; bottom: 24px; transform: translateX(-50%); background: var(--text); color: var(--surface);
      padding: 12px 18px; border-radius: 12px; box-shadow: 0 4px 16px rgba(0,0,0,.25); max-width: min(560px, calc(100vw - 32px)); z-index: 10; }
    @media (max-width: 600px) { .bar, main, .offline { padding-left: 16px; padding-right: 16px; } nav { flex: 1 1 100%; gap: 0; } nav a { padding: 0 5px; font-size: 13px; white-space: nowrap; } }
  `];

  constructor() {
    super();
    this.state = null;
    this.events = [];
    this.offline = false;
    this.toast = "";
    this._seq = 0;
    this.importOpen = false;
    this.route = this._parse();
    this._onHash = () => { this.route = this._parse(); window.scrollTo(0, 0); };
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
    this._timer = setInterval(() => { if (!document.hidden) { applyTheme(); this.refresh(); } }, POLL_MS);
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
    return { page: parts[0], id: parts[1] || "" };
  }

  async _loadHistory() {
    try {
      const history = await api("api/history?limit=300");
      const known = new Set(this.events.map((e) => e.id));
      this.events = [...history.reverse().filter((e) => !known.has(e.id)), ...this.events];
    } catch { /* the live events still come */ }
  }

  async refresh() {
    try {
      const [state, events] = await Promise.all([api("api/state"), api(`api/events?after=${this._seq}`)]);
      this.state = state;
      if (events.length) {
        this._seq = events[events.length - 1].seq;
        const byId = new Map(this.events.map((e, i) => [e.id ?? `s${e.seq}`, i]));
        const list = [...this.events];
        for (const e of events) {
          const key = e.id ?? `s${e.seq}`;
          if (byId.has(key)) list[byId.get(key)] = e; else { byId.set(key, list.length); list.push(e); }
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
      case "events": return html`<dp-events .state=${s} .events=${ev}></dp-events>`;
      case "trace": return html`<dp-trace .state=${s} .selected=${id}></dp-trace>`;
      case "settings": return html`<dp-settings .state=${s}></dp-settings>`;
      default: return html`<dp-connections .state=${s}></dp-connections>`;
    }
  }

  render() {
    const s = this.state;
    const page = this.route.page;
    const section = ["connection", "edit"].includes(page) ? "connections" : page;
    const tab = (key, label) => html`<a href="#/${key}" aria-current=${section === key ? "page" : "false"}>${t(label)}</a>`;
    const running = s && s.ser2net_running;
    // ser2net only matters with serial connections (or the own ser2net.yaml)
    const serial = s && (s.source === "custom" || s.connections.some((c) => c.kind === "serial"));
    const problems = s ? s.connections.filter((c) => connectionState(c, running)[1] === "bad").length : 0;
    return html`
      <header><div class="bar">
        <div class="brand">${logo()}<div class="name"><b>${t("appTitle")}</b>
          <span class="hint">${s ? `App ${s.version}${serial ? ` · ser2net ${s.ser2net_version || "?"}` : ""}` : ""}</span></div>
          ${s && serial ? html`<span class="chip ${running ? "ok" : "bad"}"><span class="dot"></span>${t(running ? "running" : "notRunning")}</span>` : ""}
          ${s && s.capture ? html`<a class="chip info" href="#/connection/${s.capture.connection}" style="text-decoration:none"><span class="dot"></span>${t("captureChip", { n: s.capture.name })}</a>` : ""}
          ${s && problems ? (page === "connections" ? "" : html`<a class="chip warn" href="#/connections" style="text-decoration:none"><span class="dot"></span>${t("problems", { n: problems })}</a>`)
            : s && !serial ? html`<span class="chip ok"><span class="dot"></span>${t("appRunning")}</span>` : ""}
        </div>

        <nav aria-label=${t("navMain")}>
          ${tab("connections", "navConnections")}${tab("events", "navEvents")}${tab("trace", "navTrace")}${tab("settings", "navSettings")}
        </nav>
      </div></header>
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
  static properties = { message: {}, confirmLabel: {} };

  static styles = [tokens, base, css`
    .back { position: fixed; inset: 0; background: rgba(0,0,0,.4); display: flex; align-items: center; justify-content: center; z-index: 20; padding: 16px; }
    .box { background: var(--surface); border-radius: 16px; padding: 24px; max-width: 440px; width: 100%; display: flex; flex-direction: column; gap: 20px; }
    .actions { display: flex; justify-content: flex-end; gap: 8px; }
  `];

  firstUpdated() { this.renderRoot.querySelector(".btn-g").focus(); }

  _done(value) { this.dispatchEvent(new CustomEvent("done", { detail: value })); }

  render() {
    return html`<div class="back" @keydown=${(e) => e.key === "Escape" && this._done(false)}>
      <div class="box" role="alertdialog" aria-modal="true" aria-label=${t("confirm")}>
        <p>${this.message}</p>
        <div class="actions"><button class="btn btn-g" @click=${() => this._done(false)}>${t("cancel")}</button>
          <button class="btn btn-p" @click=${() => this._done(true)}>${this.confirmLabel}</button></div>
      </div></div>`;
  }
}
