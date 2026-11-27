import { css, unsafeCSS } from "lit";

/** The rules that turn table rows into cards, for the tables that sel picks. */
const CARDS = (sel) => unsafeCSS(`
    ${sel}, ${sel} tbody, ${sel} tr, ${sel} td { display: block; }
    ${sel} { min-width: 0 !important; }
    ${sel} thead { display: none; }
    ${sel} tr { padding: 10px 0; border-bottom: 1px solid var(--line-2); }
    ${sel} tr:last-child { border-bottom: 0; }
    ${sel} td { padding: 2px 0; border: 0; text-align: right !important; white-space: normal !important; overflow-wrap: anywhere; display: flow-root; }
    ${sel} td[data-l]::before { content: attr(data-l); float: left; margin-right: 12px; color: var(--muted); font-size: calc(13px * var(--fs, 1)); font-family: Roboto, "Noto Sans", system-ui, -apple-system, sans-serif; font-weight: 400; text-align: left; }
    ${sel} td:first-child { text-align: left !important; font-weight: 500; padding-bottom: 4px; }
    ${sel} td:first-child[data-l]::before { content: none; }
    ${sel} td:empty { display: none; }
    ${sel} td .chips, ${sel} td .acts { justify-content: flex-end; }
    ${sel} .cardlbl { display: inline; font-family: Roboto, "Noto Sans", system-ui, -apple-system, sans-serif; }
    ${sel} .nocard { display: none; }
    ${sel} td .chips { display: inline-flex; flex-wrap: wrap; }
`);

// One look for all pages; the colours and --fs (text size) come from <html>, see theme.js.
// Text below 12 px (12 px and 11 px at "small" text size) stops at 10.5 px, as in fritzbox-network: max(10.5px, calc(…)).
export const tokens = css`
  :host {
    --header-h: 68px;
    /* the shapes of fritzbox-network: cards share one corner, buttons, fields and switches of a group another; chips stay pills */
    --radius: 16px; --control-radius: 10px;
    --shadow: 0 1px 2px color-mix(in srgb, var(--shadow-c) 45%, transparent), 0 8px 24px -16px var(--shadow-c);
    color: var(--text); font-family: Roboto, "Noto Sans", system-ui, -apple-system, sans-serif; font-size: calc(14px * var(--fs, 1));
    /* the sizes of figures, the same everywhere: a meter's value, a tile or counter, a small tile, a word in a tile's place */
    --num-xl: 32px; --num-l: 24px; --num-m: 20px; --num-text: 18px;
  }
  @media (max-width: 600px) { :host { --num-xl: 26px; --num-l: 20px; --num-m: 18px; --num-text: 16px; } }
`;

export const base = css`
  * { box-sizing: border-box; }
  a { color: var(--accent); }
  a:hover { color: var(--accent-hover); }
  h1 { margin: 0; font-size: calc(24px * var(--fs, 1)); font-weight: 500; letter-spacing: -.01em; }
  h2 { margin: 0; font-size: calc(16px * var(--fs, 1)); font-weight: 500; }
  p { margin: 0; }
  .sub { color: var(--muted); margin-top: 6px; }
  .hint { font-size: calc(13px * var(--fs, 1)); color: var(--muted); }
  .mono { font-family: "Roboto Mono", ui-monospace, SFMono-Regular, Menlo, monospace; }
  .card { background: var(--surface); border: 1px solid var(--line); border-radius: var(--radius); padding: 20px; display: flex; flex-direction: column; gap: 16px; min-width: 0;
    box-shadow: var(--shadow); }
  .card > .row:first-child { min-height: 32px; }
  /* the small label above a value or a group, as in fritzbox-network */
  .label { font-size: max(10.5px, calc(11px * var(--fs, 1))); font-weight: 500; text-transform: uppercase; letter-spacing: .06em; color: var(--muted); }
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
    border-radius: var(--control-radius); font-family: inherit; font-size: calc(14px * var(--fs, 1)); font-weight: 500; text-decoration: none; cursor: pointer;
    border: 1px solid transparent; background: none; color: var(--accent); }
  .btn { transition: background .15s, color .15s, box-shadow .15s; }
  .btn[disabled] { opacity: .55; cursor: default; }
  .btn-p { background: var(--accent); color: var(--on-accent); }
  .btn-p:hover:not([disabled]) { background: var(--accent-hover); color: var(--on-accent); }
  .btn-s { background: var(--surface); border-color: var(--input-line); }
  .btn-s:hover:not([disabled]), .btn-g:hover:not([disabled]) { background: var(--accent-soft); color: var(--accent-hover); }
  .btn-g { padding: 0 12px; }
  .btn-d { color: var(--bad); padding: 0 12px; }
  .btn-s:not(:hover) { color: var(--text); }
  .btn-d:hover { background: var(--bad-soft); }
  .chip { display: inline-flex; align-items: center; gap: 6px; min-height: 26px; padding: 0 11px; border-radius: 13px;
    background: var(--neutral-soft); color: var(--neutral); font-size: max(10.5px, calc(12px * var(--fs, 1))); font-weight: 500; white-space: nowrap; }
  .chip.ok { background: var(--ok-soft); color: var(--ok); } .chip.warn { background: var(--warn-soft); color: var(--warn); }
  .chip.bad { background: var(--bad-soft); color: var(--bad); } .chip.info { background: var(--accent-soft); color: var(--accent-hover); }
  .dot { width: 8px; height: 8px; border-radius: 50%; background: currentColor; flex: none; }
  .note { border-radius: var(--control-radius); padding: 12px 14px; }
  .note.acts { display: flex; align-items: center; gap: 4px 6px; flex-wrap: wrap; }
  .note.acts > span { flex: 1; min-width: min(100%, 200px); overflow-wrap: anywhere; }
  button.chip { border: 0; font-family: inherit; cursor: pointer; }
  button.chip:focus-visible, button.seen:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
  button.seen { all: unset; box-sizing: border-box; display: inline-flex; align-items: center; gap: 4px; min-height: 26px; padding: 0 8px;
    border-radius: 13px; cursor: pointer; color: inherit; font-size: max(10.5px, calc(12px * var(--fs, 1))); font-weight: 500; }
  button.seen:hover { background: color-mix(in srgb, currentColor 12%, transparent); }
  .note.warn { background: var(--warn-soft); border: 1px solid var(--warn-line); color: var(--warn); }
  .note.bad { background: var(--bad-soft); border: 1px solid var(--bad-line); color: var(--bad); }
  .note.ok { background: var(--ok-soft); color: var(--ok); }
  .note.info { background: var(--accent-soft); color: var(--accent-hover); }
  /* a long note folds to one line on a phone: the start of the text and "More"; open, the whole text and its buttons */
  .foldnote .more { display: none; }
  @media (max-width: 600px) {
    .head .sub { display: none; } /* the short text under a page's title: room for the content */
    .foldnote { flex-wrap: nowrap !important; }
    .foldnote.open { flex-wrap: wrap !important; }
    .foldnote:not(.open) .txt { flex: 1 1 0; min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
    .foldnote .more { display: inline-flex; min-height: 32px; flex: none; }
    .foldnote:not(.open) .acts { display: none !important; }
    .foldnote.open .more { display: none; }
  }
  .code { background: var(--code-bg); color: var(--code-text); border-radius: 12px; padding: 14px 16px; font-size: max(10.5px, calc(12px * var(--fs, 1)));
    line-height: 1.7; white-space: pre; overflow-x: auto; font-family: "Roboto Mono", ui-monospace, Menlo, monospace; }
  .well { background: var(--surface-2); border-radius: 12px; padding: 10px 12px; }
  .fld { display: flex; flex-direction: column; justify-content: flex-end; gap: 6px; min-width: 0; }
  .actions { display: flex; justify-content: flex-end; }
  .lbl { font-size: calc(13px * var(--fs, 1)); font-weight: 500; color: var(--muted); }
  .err { font-size: calc(13px * var(--fs, 1)); color: var(--bad); }
  .inp { min-height: 42px; padding: 0 12px; border: 1px solid var(--input-line); border-radius: var(--control-radius); font: inherit;
    color: var(--text); background: var(--surface); width: 100%; }
  .inp[aria-invalid="true"] { border-color: var(--bad); }
  .inp:disabled { color: var(--muted); background: var(--surface-2); cursor: not-allowed; }
  textarea.inp { padding: 10px 12px; min-height: 84px; resize: vertical; }
  .inp.mono { font-family: "Roboto Mono", ui-monospace, SFMono-Regular, Menlo, monospace; }
  .chk { display: flex; align-items: flex-start; gap: 10px; min-height: 32px; cursor: pointer; }
  .chk input { width: 18px; height: 18px; margin: 2px 0 0; accent-color: var(--accent); flex: none; }
  /* where the options do not fit they go on a second line; the gap shows the background as the dividing lines, in both directions */
  .seg { display: inline-flex; flex-wrap: wrap; gap: 1px; max-width: 100%; background: var(--input-line); border: 1px solid var(--input-line); border-radius: var(--control-radius); overflow: hidden; align-self: flex-start; }
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
  /* table.cards: where its .scroll box is narrow (a phone, a tablet for the wide ones) each row
     is a small card, the first cell its title, the others "label (data-l) … value" lines;
     table.cards.wide needs more room as a table and turns into cards sooner */
  .scroll { container-type: inline-size; }
  .cardlbl { display: none; }
  @container (max-width: 540px) {
${CARDS("table.cards")}  }
  @container (max-width: 780px) {
${CARDS("table.cards.wide")}  }
  .meters, .pair { display: grid; grid-template-columns: repeat(auto-fit, minmax(min(100%, 360px), 1fr)); gap: 20px; }
  /* three cards: two side by side and the third below across both, side by side when wide */
  .trio { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 20px; align-items: start; }
  .trio > :nth-child(3) { grid-column: 1 / -1; }
  @media (min-width: 1600px) { .trio { grid-template-columns: repeat(3, minmax(0, 1fr)); } .trio > :nth-child(3) { grid-column: auto; } }
  @media (max-width: 800px) { .trio { grid-template-columns: minmax(0, 1fr); } }
  .addrs { display: grid; grid-template-columns: repeat(auto-fit, minmax(min(100%, 270px), 1fr)); gap: 16px; }
  .meter { --level: var(--accent); }
  .meter.ok { --level: var(--ok); } .meter.warn { --level: var(--warn); border-color: var(--warn-line); } .meter.bad { --level: var(--bad); border-color: var(--bad-line); }
  .meter.info { --level: var(--accent); }
  .big { font-size: calc(var(--num-xl) * var(--fs, 1)); font-weight: 300; line-height: 1.15; letter-spacing: -.02em; font-variant-numeric: tabular-nums; }
  .big small { font-size: calc(14px * var(--fs, 1)); font-weight: 400; color: var(--muted); margin-left: 8px; letter-spacing: 0; }
  .meter.warn .big, .meter.bad .big { color: var(--level); }
  .track { position: relative; height: 12px; border-radius: 6px; background: var(--surface-2); overflow: hidden; box-shadow: inset 0 0 0 1px var(--line-2); }
  .track .fill { position: absolute; inset: 0 auto 0 0; border-radius: 6px; background: var(--level); transition: width .4s ease; }
  .track .tick { position: absolute; top: 0; bottom: 0; width: 2px; background: var(--text); opacity: .35; }
  .scale { display: flex; justify-content: space-between; font-size: calc(13px * var(--fs, 1)); color: var(--muted); margin-top: 6px; }
  .stats { display: grid; grid-template-columns: 1fr 1fr; gap: 14px 20px; }
  /* figures as tiles, as in fritzbox-network: the label small and in capitals above, the value light below; no boxes */
  .counters { display: grid; grid-template-columns: repeat(auto-fit, minmax(110px, 1fr)); gap: 14px 20px; }
  :is(.stats, .counters) .well { display: flex; flex-direction: column; gap: 2px; min-width: 0; background: none; padding: 0; border-radius: 0; }
  :is(.stats, .counters) .well .hint { order: -1; font-size: max(10.5px, calc(11px * var(--fs, 1))); font-weight: 500; text-transform: uppercase; letter-spacing: .06em;
    overflow-wrap: anywhere; hyphens: auto; }
  /* a label on two lines does not push its value below the others: label and value rows are shared across the tiles */
  :is(.stats, .counters) > .well:not(:has(> :nth-child(3))) { display: grid; grid-row: span 2; grid-template-rows: subgrid; row-gap: 2px; align-content: start; }
  :is(.stats, .counters) > .well > .hint { align-self: end; }
  :is(.stats, .counters) b { font-size: calc(var(--num-l) * var(--fs, 1)); font-weight: 300; letter-spacing: -.02em; line-height: 1.25; font-variant-numeric: tabular-nums; }
  .meter .chip { align-self: flex-start; min-height: 28px; padding: 0 12px; white-space: normal; }
  /* a setting as a row: name and explanation left, a narrow field with its unit, then a switch, right;
     in a group with switches every switch has the same column, so fields and switches line up */
  .rows { display: flex; flex-direction: column; container-type: inline-size; }
  .srow { display: grid; grid-template-columns: minmax(0, 1fr) auto; align-items: center; gap: 6px 16px; padding: 10px 0; border-top: 1px solid var(--line-2); }
  :is(.rows, .opts):has(.switch) > .srow { grid-template-columns: minmax(0, 1fr) auto 52px; }
  :is(.rows, .opts) > .srow:first-child { border-top: none; padding-top: 2px; }
  .srow .stext { display: flex; flex-direction: column; gap: 3px; min-width: 0; grid-column: 1; grid-row: 1; }
  .srow .lblrow { display: flex; flex-wrap: wrap; align-items: center; gap: 4px 8px; }
  .srow .lbl { color: var(--text); font-size: calc(14px * var(--fs, 1)); }
  .srow .lblrow .chip { min-height: 20px; padding: 0 8px; font-size: calc(11.5px * var(--fs, 1)); font-weight: 400; }
  .sctl { display: contents; }
  .srow .unit { grid-column: 2; grid-row: 1; justify-self: end; }
  .srow .switch { grid-column: -2; grid-row: 1; }
  .srow.off .stext, .srow.off .unit { opacity: .5; }
  .unit { display: flex; align-items: stretch; border: 1px solid var(--input-line); border-radius: var(--control-radius); overflow: hidden; background: var(--surface); min-height: 42px; }
  .unit:focus-within { outline: 3px solid var(--focus); outline-offset: 2px; }
  .unit input { width: 96px; border: none; border-radius: 0; text-align: right; min-height: 40px; padding: 0 10px; background: transparent; }
  .unit input:focus-visible { outline: none; }
  .unit:has(input[aria-invalid="true"]) { border-color: var(--bad); }
  .unit span { display: flex; align-items: center; padding: 0 10px; border-left: 1px solid var(--input-line); background: var(--surface-2); color: var(--muted); font-size: calc(13px * var(--fs, 1)); min-width: 22px; justify-content: center; }
  .reset { all: unset; cursor: pointer; color: var(--accent); white-space: nowrap; }
  .reset:hover { text-decoration: underline; }
  .reset:focus-visible { outline: 3px solid var(--focus); outline-offset: 2px; border-radius: 4px; }
  .changed { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 6px; }
  /* little room: the switch stays top right next to the text, a field goes below the text */
  @container (max-width: 520px) {
    :is(.rows, .opts) > .srow, :is(.rows, .opts):has(.switch) > .srow { grid-template-columns: minmax(0, 1fr) auto; }
    .srow .switch { grid-column: 2; align-self: start; }
    .srow .unit { grid-column: 1 / -1; grid-row: 2; justify-self: start; }
  }
  .switch { flex: none; position: relative; width: 52px; height: 32px; border-radius: 16px; border: none; cursor: pointer; padding: 0; background: light-dark(#aeb6c1, #4a525d); }
  .switch[aria-checked="true"] { background: var(--accent); }
  .switch span { position: absolute; top: 4px; left: 4px; width: 24px; height: 24px; border-radius: 50%; background: #fff; box-shadow: 0 1px 3px rgba(0,0,0,.25); transition: left .15s; }
  .switch[aria-checked="true"] span { left: 24px; }
  .switch[disabled] { opacity: .5; cursor: default; }
  button:focus-visible, a:focus-visible, input:focus-visible, select:focus-visible, textarea:focus-visible, summary:focus-visible {
    outline: 3px solid var(--focus); outline-offset: 2px; }
  /* a dialog box takes the focus when it opens (tabindex -1); it is not a control, so no ring around the whole box */
  [tabindex="-1"]:focus { outline: none; }
  /* while a page loads: grey bars in the shape of what comes; shown only after 300 ms, so a quick answer does not flash */
  .skel { display: flex; flex-direction: column; gap: 20px; opacity: 0; animation: skel-in .2s ease .3s forwards; }
  @keyframes skel-in { to { opacity: 1; } }
  .sk { display: block; max-width: 100%; background: linear-gradient(90deg, var(--line) 0%, var(--line-2) 50%, var(--line) 100%); background-size: 200% 100%;
    animation: sk-shine 1.4s linear infinite; }
  @keyframes sk-shine { from { background-position: 100% 0; } to { background-position: -100% 0; } }
  .skel .sk-row { display: flex; align-items: center; gap: 10px; }
  .skel .sk-tiles { display: grid; grid-template-columns: repeat(auto-fit, minmax(130px, 1fr)); gap: 16px 24px; }
  .skel .sk-tiles > div, .skel .sk-fld { display: flex; flex-direction: column; gap: 8px; }
  .skel .sk-cards { display: grid; grid-template-columns: repeat(auto-fill, minmax(min(100%, 480px), 1fr)); gap: 16px; }
  .skel .sk-side { display: grid; grid-template-columns: 200px minmax(0, 1fr); gap: 24px; align-items: start; }
  /* as the settings: the sections as a row of chips above the content */
  @media (max-width: 863px) { .skel .sk-side { grid-template-columns: minmax(0, 1fr); } .skel .sk-side > :first-child { flex-direction: row !important; gap: 6px !important; overflow: hidden; }
    .skel .sk-side > :first-child > * { flex: none; width: 96px !important; height: 32px !important; border-radius: 16px !important; } }
  @media (prefers-reduced-motion: reduce) { .sk { animation: none; } .skel { animation-duration: .01s; } }
  .sr { position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0 0 0 0); white-space: nowrap; }
  .crumb { font-size: calc(13px * var(--fs, 1)); color: var(--muted); }
  /* touch: links, chips and the small buttons take taps in a taller area than they show; an invisible extension, so nothing moves */
  @media (max-width: 600px), (pointer: coarse) {
    a:where(:not(.btn, .iconbtn, .act, nav a)), button.chip, button.tap, button.seen { position: relative; }
    a:where(:not(.btn, .iconbtn, .act, nav a))::after, button.chip::after, button.tap::after, button.seen::after { content: ""; position: absolute; inset: -10px 0; }
  }
`;
