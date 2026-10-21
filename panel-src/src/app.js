// The page frame: header with the sections, the router (#/…), and the app state every page reads.
// The state is polled every 2 s; events since the last seen one come with it.
import { LitElement, css, html } from "lit";
import { api } from "./api.js";
import { lang, setLang, t } from "./i18n.js";
import { base, tokens } from "./styles.js";
import { logo } from "./ui.js";

const POLL_MS = 2000;
const EVENTS_KEPT = 1500;

export class DeviceProxyApp extends LitElement {
  static properties = {
    state: { state: true },
    events: { state: true },
    route: { state: true },
    offline: { state: true },
    toast: { state: true },
  };

  static styles = [tokens, base, css`
    :host { display: block; min-height: 100vh; background: var(--bg); }
    header { background: var(--surface); border-bottom: 1px solid var(--line); }
    .bar { max-width: 1200px; margin: 0 auto; padding: 0 24px; display: flex; flex-wrap: wrap; align-items: flex-end; justify-content: space-between; gap: 0 24px; }
    .brand { display: flex; align-items: center; gap: 12px; padding: 14px 0; }
    .brand b { font-size: 18px; display: block; line-height: 1.2; }
    nav { display: flex; flex-wrap: wrap; }
    nav a { display: inline-flex; align-items: center; min-height: 48px; padding: 0 16px; font-weight: 500; color: var(--muted); text-decoration: none; border-bottom: 3px solid transparent; }
    nav a:hover { color: var(--text); }
    nav a[aria-current="page"] { color: var(--accent); border-bottom-color: var(--accent); }
    main { max-width: 1200px; margin: 0 auto; padding: 24px 24px 48px; }
    .offline { max-width: 1200px; margin: 12px auto 0; padding: 0 24px; }
    .toast { position: fixed; left: 50%; bottom: 24px; transform: translateX(-50%); background: var(--text); color: var(--surface);
      padding: 12px 18px; border-radius: 12px; box-shadow: 0 4px 16px rgba(0,0,0,.25); max-width: min(560px, calc(100vw - 32px)); z-index: 10; }
    @media (max-width: 600px) { .bar, main, .offline { padding-left: 16px; padding-right: 16px; } }
  `];

  constructor() {
    super();
    this.state = null;
    this.events = [];
    this.offline = false;
    this.toast = "";
    this._seq = 0;
    this.route = this._parse();
    this._onHash = () => { this.route = this._parse(); window.scrollTo(0, 0); };
  }

  connectedCallback() {
    super.connectedCallback();
    window.addEventListener("hashchange", this._onHash);
    this.addEventListener("dp-refresh", () => this.refresh());
    this.addEventListener("dp-toast", (e) => this.showToast(e.detail));
    this.addEventListener("dp-lang", (e) => { setLang(e.detail); document.documentElement.lang = e.detail; this.requestUpdate(); this._relayLang(); });
    document.documentElement.lang = lang;
    this._loadHistory();
    this.refresh();
    this._timer = setInterval(() => this.refresh(), POLL_MS);
  }

  disconnectedCallback() {
    super.disconnectedCallback();
    window.removeEventListener("hashchange", this._onHash);
    clearInterval(this._timer);
  }

  _relayLang() {
    this.renderRoot.querySelectorAll("main > *").forEach((el) => el.requestUpdate && el.requestUpdate());
  }

  _parse() {
    const parts = (location.hash.replace(/^#\/?/, "") || "connections").split("/");
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
      case "import": return html`<dp-import .state=${s}></dp-import>`;
      case "events": return html`<dp-events .state=${s} .events=${ev}></dp-events>`;
      case "trace": return html`<dp-trace .state=${s} .selected=${id}></dp-trace>`;
      case "settings": return html`<dp-settings .state=${s}></dp-settings>`;
      default: return html`<dp-connections .state=${s}></dp-connections>`;
    }
  }

  render() {
    const s = this.state;
    const page = this.route.page;
    const section = ["connection", "edit", "import"].includes(page) ? "connections" : page;
    const tab = (key, label) => html`<a href="#/${key}" aria-current=${section === key ? "page" : "false"}>${t(label)}</a>`;
    const running = s && s.ser2net_running;
    return html`
      <header><div class="bar">
        <div class="brand">${logo()}<div><b>${t("appTitle")}</b>
          <span class="hint">${s ? `App ${s.version} · ser2net ${s.ser2net_version || "?"}` : ""}</span></div>
          ${s ? html`<span class="chip ${running ? "ok" : "bad"}"><span class="dot"></span>${t(running ? "running" : "notRunning")}</span>` : ""}
        </div>
        <nav aria-label=${t("navMain")}>
          ${tab("connections", "navConnections")}${tab("events", "navEvents")}${tab("trace", "navTrace")}${tab("settings", "navSettings")}
        </nav>
      </div></header>
      ${this.offline ? html`<div class="offline"><div class="note warn" role="status">${t("connectionLost")}</div></div>` : ""}
      <main>${this._page()}</main>
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
