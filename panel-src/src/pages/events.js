import { css, html } from "lit";
import { api } from "../api.js";
import { Page } from "../app.js";
import { eventText, lang, t } from "../i18n.js";
import { fmtTime, icon } from "../ui.js";

const LEVELS = ["info", "warning", "error", "debug"];

export class EventsPage extends Page {
  static properties = {
    state: { attribute: false }, events: { attribute: false }, preset: {}, tab: { state: true }, conn: { state: true },
    query: { state: true }, levels: { state: true }, paused: { state: true }, stats: { state: true }, history: { state: true },
  };

  static styles = [...Page.styles, css`
    .tabs { display: inline-flex; background: var(--line); border-radius: 22px; padding: 4px; }
    .tabs button { min-height: 40px; padding: 0 18px; border: none; border-radius: 18px; cursor: pointer; font: inherit; font-weight: 500; background: transparent; color: var(--muted); }
    .tabs button[aria-selected="true"] { background: var(--surface); color: var(--accent-hover); box-shadow: 0 1px 2px rgba(0,0,0,.12); }
    .filters { display: flex; flex-wrap: wrap; align-items: flex-end; gap: 12px; margin-bottom: 20px; }
    .lv { min-height: 40px; padding: 0 14px; border-radius: 20px; cursor: pointer; font: inherit; font-size: 13px; font-weight: 500; border: 1px solid var(--input-line); background: var(--surface); color: var(--muted); }
    .lv[aria-pressed="true"].info { background: var(--accent-soft); color: var(--accent-hover); border-color: var(--accent); }
    .lv[aria-pressed="true"].warning { background: var(--warn-soft); color: var(--warn); border-color: var(--warn); }
    .lv[aria-pressed="true"].error { background: var(--bad-soft); color: var(--bad); border-color: var(--bad); }
    .lv[aria-pressed="true"].debug { background: var(--neutral-soft); color: var(--neutral); border-color: var(--neutral); }
    .log { max-height: max(320px, calc(100vh - 330px)); overflow: auto; }
    .dayrow { padding: 6px 16px; font-size: 12px; font-weight: 500; color: var(--muted); background: var(--surface-2); border-bottom: 1px solid var(--line-2); position: sticky; top: 0; }
    .lv { display: inline-flex; align-items: center; gap: 6px; }
    .name { font-weight: 500; color: inherit; text-decoration: none; }
    a.name:hover { text-decoration: underline; }
    .line { display: grid; grid-template-columns: 130px 78px minmax(0, 1fr); gap: 12px; align-items: baseline; padding: 8px 16px; border-bottom: 1px solid var(--line-2); }
    @media (max-width: 600px) { .line { grid-template-columns: auto auto; } .line > :last-child { grid-column: 1 / -1; } }
    .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 16px; margin-bottom: 20px; }
    .bars { display: flex; align-items: flex-end; gap: 2px; height: 36px; }
    .bars span { flex: 1; min-width: 2px; border-radius: 2px; background: var(--line); }
  `];

  constructor() {
    super();
    this.tab = "live";
    this.conn = "";
    this.query = "";
    this.levels = new Set(["info", "warning", "error"]);
    this.paused = null;
  }

  willUpdate(changed) {
    if (changed.has("preset") && this.preset && this.preset !== this.conn) { this.conn = this.preset; if (this.tab === "history") this._loadHistory(); }
  }

  async _loadHistory() {
    const days = this.state.settings.history_days;
    const since = Date.now() / 1000 - days * 86400;
    try {
      [this.stats, this.history] = await Promise.all([
        api(`api/stats?days=${Math.min(days, 30)}`),
        api(`api/history?since=${since}&limit=2000${this.conn ? `&connection=${this.conn}` : ""}`),
      ]);
    } catch (err) { this.toast(`${t("error")}: ${err.message}`); }
  }

  _dayLabel(ts) {
    const key = new Date(ts * 1000).toDateString();
    const today = new Date().toDateString(), yesterday = new Date(Date.now() - 86400000).toDateString();
    if (key === today) return t("today");
    if (key === yesterday) return t("yesterday");
    return new Date(key).toLocaleDateString(lang, { weekday: "short", day: "2-digit", month: "2-digit" });
  }

  _who(e) {
    const known = e.connection && this.state.connections.some((c) => c.id === e.connection);
    return known ? html`<a class="name" href="#/connection/${e.connection}">[${e.name}]</a>` : html`<b class="name">[${e.name}]</b>`;
  }

  _filtered(list, anyLevel = false) {
    const q = this.query.trim().toLowerCase();
    return list.filter((e) => (anyLevel || this.levels.has(e.level)) && (!this.conn || e.connection === this.conn)
      && (!q || `${e.name} ${eventText(e)}`.toLowerCase().includes(q)));
  }

  /** The rows both tabs share: day rows, time, level, text. */
  _list(lines, total = lines.length) {
    const color = { info: "info", warning: "warn", error: "bad", debug: "" };
    return html`<div class="log" role="log">${lines.map((e, i) => html`${i === 0 || this._dayLabel(lines[i - 1].ts) !== this._dayLabel(e.ts) ? html`<div class="dayrow">${this._dayLabel(e.ts)}</div>` : ""}<div class="line">
        <span class="mono hint">${fmtTime(e.ts, false, true)}</span><span class="chip ${color[e.level]}" style="justify-content:center">${t(`lv_${e.level}`)}</span>
        <span style="overflow-wrap:anywhere">${this._who(e)} ${eventText(e)}${e.count > 1 ? html` <span class="chip">${t("summed", { n: e.count })}</span>` : ""}</span></div>`)}
        ${lines.length ? "" : html`<p class="hint" style="padding:32px 16px;text-align:center;font-size:14px">${t("noEntries")}</p>`}
        ${total > lines.length ? html`<p class="hint" style="padding:12px 16px;font-size:13px">${t("moreEntries", { n: total - lines.length })}</p>` : ""}</div>`;
  }

  _live() {
    const all = this._filtered(this.paused || this.events).sort((a, b) => b.ts - a.ts);
    const lines = all.slice(0, 500);
    return html`<section class="card" style="padding:0;gap:0;overflow:hidden" aria-label=${t("tabLive")}>
      <div class="row" style="padding:12px 16px;border-bottom:1px solid var(--line)">
        <span class="hint" style="font-size:13px;display:flex;align-items:center;gap:8px"><span class="dot" style="color:${this.paused ? "var(--muted)" : "var(--ok)"}"></span>
          ${this.paused ? t("paused") : t("liveState")} · ${t("entries", { n: all.length })}</span>
        <button class="btn btn-g" @click=${() => { this.paused = this.paused ? null : [...this.events]; }}>${this.paused ? t("resume") : t("pause")}</button></div>
      ${this._list(lines, all.length)}
    </section>`;
  }

  _historyView() {
    if (!this.stats || !this.history) {
      const shown = this.state.connections.filter((c) => !this.conn || c.id === this.conn);
      return html`<div class="stats" aria-busy="true">${shown.map((c, i) => html`<section class="card" aria-label=${c.name} style="min-height:150px"><b style="font-weight:500">${c.name}</b>${i ? "" : html`<span class="hint">${t("loading")}</span>`}</section>`)}</div>`;
    }
    const days = this.stats.days;
    const conns = this.state.connections.filter((c) => !this.conn || c.id === this.conn);
    const all = this._filtered(this.history).sort((a, b) => b.ts - a.ts);
    return html`
      <div class="stats">${conns.map((c) => {
        const st = this.stats.connections[c.id] || { drops: 0, availability: 1, per_day: Array(days).fill(0) };
        const max = Math.max(...st.per_day, 1);
        return html`<section class="card" aria-label=${c.name} style="gap:10px">
          <div class="row" style="flex-wrap:nowrap"><b style="font-weight:500;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap" title=${c.name}>${c.name}</b><span class="chip ${st.drops ? "warn" : "ok"}" style="flex:none">${st.drops ? t("unstable", { n: st.drops }) : t("stable")}</span></div>
          <div style="display:flex;gap:20px">
            <div><div class="hint">${t("drops", { d: days })}</div><div style="font-size:22px;font-weight:500">${st.drops}</div></div>
            <div><div class="hint">${t("availability")}</div><div style="font-size:22px;font-weight:500">${(st.availability * 100).toLocaleString(lang, { maximumFractionDigits: 2 })} %</div></div></div>
          <div class="bars" role="img" aria-label="${t("drops", { d: days })}: ${st.drops}">${st.per_day.map((v, i) => html`<span title="${this._dayLabel(Date.now() / 1000 - (days - 1 - i) * 86400)}: ${v ? t("unstable", { n: v }) : t("stable")}" style="height:${v ? 20 + (v / max) * 80 : 8}%;${v ? "background:var(--warn)" : ""}"></span>`)}</div>
          <div class="row hint" style="font-size:12px"><span>${t("daysAgo", { d: days })}</span><span>${t("today")}</span></div>
        </section>`;
      })}</div>
      <section class="card" style="padding:0;gap:0;overflow:hidden" aria-labelledby="t-tl">
        <div class="row" style="padding:12px 16px;border-bottom:1px solid var(--line)">
          <h2 id="t-tl" style="font-size:14px;font-weight:500">${t("timeline")}</h2>
          <span class="hint" style="font-size:13px">${t("retention", { d: this.state.settings.history_days })} · ${t("entries", { n: all.length })}</span></div>
        ${this._list(all.slice(0, 500), all.length)}
      </section>`;
  }

  /** Search and level switches for a list of events (both tabs); the counts follow the other filters. */
  _searchLevels(list) {
    const base = this._filtered(list, true);
    const counts = Object.fromEntries(LEVELS.map((lv) => [lv, base.filter((e) => e.level === lv).length]));
    return html`<label class="fld" style="flex:1 1 220px"><span class="lbl">${t("search")}</span>
        <input class="inp" type="search" .value=${this.query} placeholder=${t("searchPh")} @input=${(e) => { this.query = e.target.value; }}></label>
      <div role="group" aria-label="Level" style="display:flex;flex-wrap:wrap;gap:6px">${LEVELS.map((lv) => html`<button class="lv ${lv}" aria-pressed=${this.levels.has(lv) ? "true" : "false"}
        @click=${() => { const s = new Set(this.levels); s.has(lv) ? s.delete(lv) : s.add(lv); this.levels = s; }}>${this.levels.has(lv) ? icon("check", 14) : ""}${t(`lv_${lv}`)}${counts[lv] ? html` <span style="opacity:.8">${counts[lv]}</span>` : ""}</button>`)}</div>`;
  }

  render() {
    const live = this.tab === "live";
    const tabButton = (key, label) => html`<button role="tab" aria-selected=${this.tab === key ? "true" : "false"}
      @click=${() => { this.tab = key; if (key === "history") this._loadHistory(); }}>${t(label)}</button>`;
    return html`
      <div class="head"><div><h1>${t("eventsTitle")}</h1><p class="sub">${live ? t("eventsSub") : t("eventsSubHistory", { d: this.state.settings.history_days })}</p></div>
        <div class="tabs" role="tablist">${tabButton("live", "tabLive")}${tabButton("history", "tabHistory")}</div></div>
      <div class="filters">
        <label class="fld"><span class="lbl">${t("navConnections")}</span>
          <select class="inp" @change=${(e) => { this.conn = e.target.value; if (this.tab === "history") this._loadHistory(); }}>
            <option value="">${t("allConnections")}</option>
            ${this.state.connections.map((c) => html`<option value=${c.id} ?selected=${this.conn === c.id}>${c.name}</option>`)}</select></label>
        ${this._searchLevels(live ? this.paused || this.events : this.history || [])}
      </div>
      ${live ? this._live() : this._historyView()}`;
  }
}
