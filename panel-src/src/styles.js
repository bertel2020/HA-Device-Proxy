import { css } from "lit";

// One look for all pages: the mockup's light theme, and a dark one when the system asks for it.
export const tokens = css`
  :host {
    --bg: #f3f4f6; --surface: #ffffff; --surface-2: #f5f7f9; --line: #e1e5ea; --line-2: #eef0f3;
    --text: #1b1f24; --muted: #5b6270; --accent: #0a6aa8; --accent-hover: #07507f; --accent-soft: #eaf3fa;
    --ok: #1e6b34; --ok-soft: #e6f4ea; --warn: #8a4b00; --warn-soft: #fff1de; --warn-line: #f3d19e;
    --bad: #a1261b; --bad-soft: #fdecea; --bad-line: #f2b8b5; --neutral-soft: #eef1f4; --neutral: #3a414c;
    --code-bg: #14181d; --code-text: #d7dee6; --focus: #7db8e0; --input-line: #c3cbd5; --on-accent: #ffffff;
    color: var(--text); font-family: Roboto, "Noto Sans", system-ui, -apple-system, sans-serif; font-size: 14px;
  }
  @media (prefers-color-scheme: dark) {
    :host {
      --bg: #111418; --surface: #1b1f24; --surface-2: #22272e; --line: #2d333b; --line-2: #262c33;
      --text: #e6e9ed; --muted: #9aa4b1; --accent: #5bb2ea; --accent-hover: #8ccaf2; --accent-soft: #16324a;
      --ok: #7fd49a; --ok-soft: #173a24; --warn: #f2c27a; --warn-soft: #3a2a12; --warn-line: #6b4a1c;
      --bad: #f2a29a; --bad-soft: #3d1c19; --bad-line: #6e2f2a; --neutral-soft: #2a3038; --neutral: #c5ccd5;
      --code-bg: #0b0e11; --input-line: #3a424c; --on-accent: #0b1a26;
    }
  }
`;

export const base = css`
  * { box-sizing: border-box; }
  a { color: var(--accent); }
  a:hover { color: var(--accent-hover); }
  h1 { margin: 0; font-size: 26px; font-weight: 500; }
  h2 { margin: 0; font-size: 16px; font-weight: 500; }
  p { margin: 0; }
  .sub { color: var(--muted); margin-top: 6px; }
  .hint { font-size: 12px; color: var(--muted); }
  .mono { font-family: "Roboto Mono", ui-monospace, SFMono-Regular, Menlo, monospace; }
  .card { background: var(--surface); border: 1px solid var(--line); border-radius: 16px; padding: 20px; display: flex; flex-direction: column; gap: 14px; min-width: 0; }
  .row { display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: 12px; }
  .stack { display: flex; flex-direction: column; gap: 20px; }
  .cols { display: flex; flex-wrap: wrap; gap: 20px; align-items: flex-start; }
  .main-col { flex: 999 1 560px; min-width: 0; display: flex; flex-direction: column; gap: 20px; }
  .side-col { flex: 1 1 300px; min-width: 0; display: flex; flex-direction: column; gap: 20px; }
  .grid2 { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; }
  .btn { display: inline-flex; align-items: center; justify-content: center; gap: 8px; min-height: 40px; padding: 0 18px;
    border-radius: 20px; font-family: inherit; font-size: 14px; font-weight: 500; text-decoration: none; cursor: pointer;
    border: 1px solid transparent; background: none; color: var(--accent); }
  .btn[disabled] { opacity: .55; cursor: default; }
  .btn-p { background: var(--accent); color: var(--on-accent); }
  .btn-p:hover:not([disabled]) { background: var(--accent-hover); color: var(--on-accent); }
  .btn-s { background: var(--surface); border-color: var(--input-line); }
  .btn-s:hover:not([disabled]), .btn-g:hover:not([disabled]) { background: var(--accent-soft); color: var(--accent-hover); }
  .btn-g { padding: 0 12px; }
  .btn-d { color: var(--bad); padding: 0 12px; }
  .btn-d:hover { background: var(--bad-soft); }
  .chip { display: inline-flex; align-items: center; gap: 6px; min-height: 24px; padding: 0 10px; border-radius: 12px;
    background: var(--neutral-soft); color: var(--neutral); font-size: 12px; font-weight: 500; white-space: nowrap; }
  .chip.ok { background: var(--ok-soft); color: var(--ok); } .chip.warn { background: var(--warn-soft); color: var(--warn); }
  .chip.bad { background: var(--bad-soft); color: var(--bad); } .chip.info { background: var(--accent-soft); color: var(--accent-hover); }
  .dot { width: 8px; height: 8px; border-radius: 50%; background: currentColor; flex: none; }
  .note { border-radius: 12px; padding: 12px 14px; }
  .note.warn { background: var(--warn-soft); border: 1px solid var(--warn-line); color: var(--warn); }
  .note.bad { background: var(--bad-soft); border: 1px solid var(--bad-line); color: var(--bad); }
  .note.ok { background: var(--ok-soft); color: var(--ok); }
  .note.info { background: var(--accent-soft); color: var(--accent-hover); }
  .code { background: var(--code-bg); color: var(--code-text); border-radius: 12px; padding: 14px 16px; font-size: 12px;
    line-height: 1.7; white-space: pre; overflow-x: auto; font-family: "Roboto Mono", ui-monospace, Menlo, monospace; }
  .well { background: var(--surface-2); border-radius: 12px; padding: 10px 12px; }
  .fld { display: flex; flex-direction: column; gap: 6px; min-width: 0; }
  .lbl { font-size: 12px; font-weight: 500; color: var(--muted); }
  .err { font-size: 12px; color: var(--bad); }
  .inp { min-height: 42px; padding: 0 12px; border: 1px solid var(--input-line); border-radius: 10px; font: inherit;
    color: var(--text); background: var(--surface); width: 100%; }
  .inp[aria-invalid="true"] { border-color: var(--bad); }
  textarea.inp { padding: 10px 12px; min-height: 84px; resize: vertical; }
  .inp.mono { font-family: "Roboto Mono", ui-monospace, SFMono-Regular, Menlo, monospace; }
  .chk { display: flex; align-items: flex-start; gap: 10px; min-height: 32px; cursor: pointer; }
  .chk input { width: 18px; height: 18px; margin: 2px 0 0; accent-color: var(--accent); flex: none; }
  .seg { display: inline-flex; border: 1px solid var(--input-line); border-radius: 10px; overflow: hidden; align-self: flex-start; }
  .seg button { min-height: 38px; padding: 0 14px; border: none; cursor: pointer; font-family: inherit; font-size: 13px; font-weight: 500;
    background: var(--surface); color: var(--text); }
  .seg button + button { border-left: 1px solid var(--input-line); }
  .seg button[aria-pressed="true"] { background: var(--accent); color: var(--on-accent); }
  .choice { display: flex; flex-direction: column; align-items: flex-start; gap: 2px; min-height: 60px; padding: 12px 14px;
    border-radius: 12px; cursor: pointer; text-align: left; font: inherit; color: var(--text); background: var(--surface); border: 1px solid var(--input-line); }
  .choice[aria-pressed="true"], .choice[aria-checked="true"] { background: var(--accent-soft); border: 2px solid var(--accent); }
  .choices { display: grid; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr)); gap: 10px; }
  table { width: 100%; border-collapse: collapse; }
  th { font-weight: 500; font-size: 12px; color: var(--muted); text-align: left; padding: 8px; border-bottom: 1px solid var(--line); }
  td { padding: 10px 8px; border-bottom: 1px solid var(--line-2); vertical-align: top; }
  .scroll { overflow-x: auto; }
  .switch { flex: none; position: relative; width: 52px; height: 32px; border-radius: 16px; border: none; cursor: pointer; padding: 0; background: #aeb6c1; }
  .switch[aria-checked="true"] { background: var(--accent); }
  .switch span { position: absolute; top: 4px; left: 4px; width: 24px; height: 24px; border-radius: 50%; background: #fff; box-shadow: 0 1px 3px rgba(0,0,0,.25); transition: left .15s; }
  .switch[aria-checked="true"] span { left: 24px; }
  .switch[disabled] { opacity: .5; cursor: default; }
  button:focus-visible, a:focus-visible, input:focus-visible, select:focus-visible, textarea:focus-visible, summary:focus-visible {
    outline: 3px solid var(--focus); outline-offset: 2px; }
  .sr { position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0 0 0 0); white-space: nowrap; }
  .crumb { font-size: 13px; color: var(--muted); }
`;
