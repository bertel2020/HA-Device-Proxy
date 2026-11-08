import { css } from "lit";

// One look for all pages; the colours and --fs (text size) come from <html>, see theme.js.
export const tokens = css`
  :host {
    --header-h: 68px;
    color: var(--text); font-family: Roboto, "Noto Sans", system-ui, -apple-system, sans-serif; font-size: calc(14px * var(--fs, 1));
  }
`;

export const base = css`
  * { box-sizing: border-box; }
  a { color: var(--accent); }
  a:hover { color: var(--accent-hover); }
  h1 { margin: 0; font-size: calc(28px * var(--fs, 1)); font-weight: 500; letter-spacing: -.01em; }
  h2 { margin: 0; font-size: calc(16px * var(--fs, 1)); font-weight: 500; }
  p { margin: 0; }
  .sub { color: var(--muted); margin-top: 6px; }
  .hint { font-size: calc(13px * var(--fs, 1)); color: var(--muted); }
  .mono { font-family: "Roboto Mono", ui-monospace, SFMono-Regular, Menlo, monospace; }
  .card { background: var(--surface); border: 1px solid var(--line); border-radius: 18px; padding: 22px; display: flex; flex-direction: column; gap: 16px; min-width: 0;
    box-shadow: 0 1px 2px var(--shadow-c), 0 6px 18px -10px var(--shadow-c); }
  .card > .row:first-child { min-height: 32px; }
  details.fold > summary { cursor: pointer; font-size: calc(14px * var(--fs, 1)); font-weight: 500; color: var(--accent-hover); display: flex; align-items: center; gap: 8px; min-height: 32px; list-style: none; }
  details.fold > summary::-webkit-details-marker { display: none; }
  details.fold > summary::before { content: "›"; font-size: calc(20px * var(--fs, 1)); line-height: 1; transition: transform .15s; }
  details.fold[open] > summary::before { transform: rotate(90deg); }
  details.fold > summary:hover { text-decoration: underline; }
  .row { display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: 12px; }
  .stack { display: flex; flex-direction: column; gap: 20px; }
  .cols, .main-col { min-width: 0; display: flex; flex-direction: column; gap: 20px; }
  .grid2 { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; }
  .btn { display: inline-flex; align-items: center; justify-content: center; gap: 8px; min-height: 40px; padding: 0 18px;
    border-radius: 20px; font-family: inherit; font-size: calc(14px * var(--fs, 1)); font-weight: 500; text-decoration: none; cursor: pointer;
    border: 1px solid transparent; background: none; color: var(--accent); }
  .btn { transition: background .15s, color .15s, box-shadow .15s; }
  .btn[disabled] { opacity: .55; cursor: default; }
  .btn-p { background: var(--accent); color: var(--on-accent); }
  .btn-p:hover:not([disabled]) { background: var(--accent-hover); color: var(--on-accent); }
  .btn-s { background: var(--surface); border-color: var(--input-line); }
  .btn-s:hover:not([disabled]), .btn-g:hover:not([disabled]) { background: var(--accent-soft); color: var(--accent-hover); }
  .btn-g { padding: 0 12px; }
  .btn-d { color: var(--bad); padding: 0 12px; }
  .btn-d:hover { background: var(--bad-soft); }
  .chip { display: inline-flex; align-items: center; gap: 6px; min-height: 26px; padding: 0 11px; border-radius: 13px;
    background: var(--neutral-soft); color: var(--neutral); font-size: calc(12px * var(--fs, 1)); font-weight: 500; white-space: nowrap; }
  .chip.ok { background: var(--ok-soft); color: var(--ok); } .chip.warn { background: var(--warn-soft); color: var(--warn); }
  .chip.bad { background: var(--bad-soft); color: var(--bad); } .chip.info { background: var(--accent-soft); color: var(--accent-hover); }
  .dot { width: 8px; height: 8px; border-radius: 50%; background: currentColor; flex: none; }
  .note { border-radius: 12px; padding: 12px 14px; }
  .note.warn { background: var(--warn-soft); border: 1px solid var(--warn-line); color: var(--warn); }
  .note.bad { background: var(--bad-soft); border: 1px solid var(--bad-line); color: var(--bad); }
  .note.ok { background: var(--ok-soft); color: var(--ok); }
  .note.info { background: var(--accent-soft); color: var(--accent-hover); }
  .code { background: var(--code-bg); color: var(--code-text); border-radius: 12px; padding: 14px 16px; font-size: calc(12px * var(--fs, 1));
    line-height: 1.7; white-space: pre; overflow-x: auto; font-family: "Roboto Mono", ui-monospace, Menlo, monospace; }
  .well { background: var(--surface-2); border-radius: 12px; padding: 10px 12px; }
  .fld { display: flex; flex-direction: column; justify-content: flex-end; gap: 6px; min-width: 0; }
  .actions { display: flex; justify-content: flex-end; }
  .lbl { font-size: calc(13px * var(--fs, 1)); font-weight: 500; color: var(--muted); }
  .err { font-size: calc(13px * var(--fs, 1)); color: var(--bad); }
  .inp { min-height: 42px; padding: 0 12px; border: 1px solid var(--input-line); border-radius: 10px; font: inherit;
    color: var(--text); background: var(--surface); width: 100%; }
  .inp[aria-invalid="true"] { border-color: var(--bad); }
  .inp:disabled { color: var(--muted); background: var(--surface-2); cursor: not-allowed; }
  textarea.inp { padding: 10px 12px; min-height: 84px; resize: vertical; }
  .inp.mono { font-family: "Roboto Mono", ui-monospace, SFMono-Regular, Menlo, monospace; }
  .chk { display: flex; align-items: flex-start; gap: 10px; min-height: 32px; cursor: pointer; }
  .chk input { width: 18px; height: 18px; margin: 2px 0 0; accent-color: var(--accent); flex: none; }
  /* where the options do not fit they go on a second line; the gap shows the background as the dividing lines, in both directions */
  .seg { display: inline-flex; flex-wrap: wrap; gap: 1px; max-width: 100%; background: var(--input-line); border: 1px solid var(--input-line); border-radius: 10px; overflow: hidden; align-self: flex-start; }
  .seg button { flex: 1 1 auto; min-height: 38px; padding: 0 14px; border: none; cursor: pointer; font-family: inherit; font-size: calc(13px * var(--fs, 1)); font-weight: 500;
    background: var(--surface); color: var(--text); }
  .seg button[aria-pressed="true"] { background: var(--accent); color: var(--on-accent); }
  .choice { display: flex; flex-direction: column; align-items: flex-start; gap: 2px; min-height: 60px; padding: 12px 14px;
    border-radius: 12px; cursor: pointer; text-align: left; font: inherit; color: var(--text); background: var(--surface); border: 1px solid var(--input-line); }
  .choice[aria-pressed="true"], .choice[aria-checked="true"] { background: var(--accent-soft); border-color: var(--accent); box-shadow: 0 0 0 1px var(--accent); }
  .choices { display: grid; grid-template-columns: repeat(auto-fit, minmax(min(100%, 220px), 1fr)); grid-auto-rows: 1fr; gap: 10px; }
  table { width: 100%; border-collapse: collapse; }
  th { font-weight: 500; font-size: calc(13px * var(--fs, 1)); color: var(--muted); text-align: left; padding: 8px; border-bottom: 1px solid var(--line); }
  td { padding: 10px 8px; border-bottom: 1px solid var(--line-2); vertical-align: top; }
  .scroll { overflow-x: auto; position: relative; } /* relative: else an absolute .sr in a wide table escapes and widens the page */
  .meters, .pair { display: grid; grid-template-columns: repeat(auto-fit, minmax(min(100%, 360px), 1fr)); gap: 20px; }
  .addrs { display: grid; grid-template-columns: repeat(auto-fit, minmax(min(100%, 270px), 1fr)); gap: 16px; }
  .meter { --level: var(--accent); }
  .meter.ok { --level: var(--ok); } .meter.warn { --level: var(--warn); border-color: var(--warn-line); } .meter.bad { --level: var(--bad); border-color: var(--bad-line); }
  .meter.info { --level: var(--accent); }
  .big { font-size: calc(34px * var(--fs, 1)); font-weight: 500; line-height: 1.1; letter-spacing: -.01em; }
  .big small { font-size: calc(14px * var(--fs, 1)); font-weight: 400; color: var(--muted); margin-left: 8px; letter-spacing: 0; }
  .meter.warn .big, .meter.bad .big { color: var(--level); }
  .track { position: relative; height: 12px; border-radius: 6px; background: var(--surface-2); overflow: hidden; box-shadow: inset 0 0 0 1px var(--line-2); }
  .track .fill { position: absolute; inset: 0 auto 0 0; border-radius: 6px; background: var(--level); transition: width .4s ease; }
  .track .tick { position: absolute; top: 0; bottom: 0; width: 2px; background: var(--text); opacity: .35; }
  .scale { display: flex; justify-content: space-between; font-size: calc(13px * var(--fs, 1)); color: var(--muted); margin-top: 6px; }
  .stats { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
  .stats .well { display: flex; flex-direction: column; gap: 2px; }
  .stats b { font-size: calc(18px * var(--fs, 1)); font-weight: 500; }
  .meter .chip { align-self: flex-start; min-height: 28px; padding: 0 12px; white-space: normal; }
  .switch { flex: none; position: relative; width: 52px; height: 32px; border-radius: 16px; border: none; cursor: pointer; padding: 0; background: #aeb6c1; }
  .switch[aria-checked="true"] { background: var(--accent); }
  .switch span { position: absolute; top: 4px; left: 4px; width: 24px; height: 24px; border-radius: 50%; background: #fff; box-shadow: 0 1px 3px rgba(0,0,0,.25); transition: left .15s; }
  .switch[aria-checked="true"] span { left: 24px; }
  .switch[disabled] { opacity: .5; cursor: default; }
  button:focus-visible, a:focus-visible, input:focus-visible, select:focus-visible, textarea:focus-visible, summary:focus-visible {
    outline: 3px solid var(--focus); outline-offset: 2px; }
  .sr { position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0 0 0 0); white-space: nowrap; }
  .crumb { font-size: calc(13px * var(--fs, 1)); color: var(--muted); }
`;
