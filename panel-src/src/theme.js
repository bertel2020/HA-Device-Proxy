// Colour scheme, dark or light, and text size: chosen per browser on the settings page.
// The colours are set on <html>, so every page's shadow tree inherits them; light-dark() picks
// by html's color-scheme, which follows Home Assistant unless light or dark is chosen.
const KEY = "device_proxy.look";
export const SCHEMES = ["ozean", "wald", "graphit"];
export const MODES = ["auto", "light", "dark"];
export const SIZES = { small: 12, normal: 14, large: 16 };

// [light, dark] per token
const PALETTES = {
  ozean: {
    bg: ["#f4f6f9", "#0f1216"], surface: ["#ffffff", "#1b1f24"], "surface-2": ["#f5f7f9", "#22272e"], line: ["#e1e5ea", "#2d333b"], "line-2": ["#eef0f3", "#262c33"],
    "input-line": ["#c3cbd5", "#3a424c"], text: ["#1b1f24", "#e6e9ed"], muted: ["#5b6270", "#9aa4b1"], accent: ["#0a6aa8", "#5bb2ea"], "accent-hover": ["#07507f", "#8ccaf2"],
    "accent-soft": ["#eaf3fa", "#16324a"], "on-accent": ["#ffffff", "#0b1a26"], "neutral-soft": ["#eef1f4", "#2a3038"], neutral: ["#3a414c", "#c5ccd5"],
  },
  wald: {
    bg: ["#f3f7f5", "#0e1513"], surface: ["#ffffff", "#1a2220"], "surface-2": ["#f4f8f6", "#202a27"], line: ["#dce5e1", "#2b3733"], "line-2": ["#eaf0ed", "#24302c"],
    "input-line": ["#bccac4", "#394845"], text: ["#1a201e", "#e4ebe8"], muted: ["#566360", "#98a8a2"], accent: ["#0f7a6b", "#5fd0be"], "accent-hover": ["#0a5a4f", "#8fe0d2"],
    "accent-soft": ["#e4f3f0", "#123430"], "on-accent": ["#ffffff", "#08201c"], "neutral-soft": ["#ecf1ef", "#26312e"], neutral: ["#36423e", "#c3d0cb"],
  },
  graphit: {
    bg: ["#f5f4f2", "#141414"], surface: ["#ffffff", "#1f1f1e"], "surface-2": ["#f6f5f3", "#262625"], line: ["#e4e2de", "#33322f"], "line-2": ["#eeedea", "#2a2a28"],
    "input-line": ["#cbc8c2", "#45433f"], text: ["#1c1b19", "#ebeae7"], muted: ["#5c5853", "#a9a59f"], accent: ["#2f3a48", "#d4dae2"], "accent-hover": ["#1b232d", "#f0f3f6"],
    "accent-soft": ["#eceff3", "#2c3139"], "on-accent": ["#ffffff", "#141820"], "neutral-soft": ["#efeeeb", "#2c2c2a"], neutral: ["#3d3a36", "#cfccc6"],
  },
};

function sheet() {
  const vars = (p) => Object.entries(p).map(([k, [l, d]]) => `--${k}: light-dark(${l}, ${d});`).join(" ");
  return Object.entries(PALETTES).map(([name, p]) => `html[data-scheme="${name}"] { ${vars(p)} }`).join("\n") + `
html { --fs: 1;
  --ok: light-dark(#1e6b34, #7fd49a); --ok-soft: light-dark(#e6f4ea, #173a24); --warn: light-dark(#8a4b00, #f2c27a); --warn-soft: light-dark(#fff1de, #3a2a12);
  --warn-line: light-dark(#f3d19e, #6b4a1c); --bad: light-dark(#a1261b, #f2a29a); --bad-soft: light-dark(#fdecea, #3d1c19); --bad-line: light-dark(#f2b8b5, #6e2f2a);
  --code-bg: light-dark(#14181d, #0b0e11); --code-text: #d7dee6; --focus: #7db8e0; --shadow-c: light-dark(rgba(16, 24, 40, .06), rgba(0, 0, 0, .4)); }
html, body { background: var(--bg); }`;
}

export function look() {
  let saved = {};
  try { saved = JSON.parse(localStorage.getItem(KEY)) || {}; } catch { /* private window or old value */ }
  return {
    scheme: SCHEMES.includes(saved.scheme) ? saved.scheme : "ozean",
    mode: MODES.includes(saved.mode) ? saved.mode : "auto",
    size: saved.size in SIZES ? saved.size : "normal",
  };
}

export function setLook(change) {
  try { localStorage.setItem(KEY, JSON.stringify({ ...look(), ...change })); } catch { /* private window */ }
  applyTheme();
}

// Dark or light as Home Assistant has it: the page runs in an iframe of the same origin, so
// the parent's theme colours can be read. Without them the system's setting stays (color-scheme).
function luminance(color) {
  const probe = document.createElement("span");
  probe.style.color = color;
  document.body.append(probe);
  const rgb = getComputedStyle(probe).color.match(/\d+(\.\d+)?/g);
  probe.remove();
  if (!rgb || rgb.length < 3) return null;
  const [r, g, b] = rgb.slice(0, 3).map(Number);
  return (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255;
}

function homeAssistantDark() {
  try {
    if (!window.parent || window.parent === window) return null;
    const root = window.parent.document.documentElement;
    const color = window.parent.getComputedStyle(root).getPropertyValue("--primary-background-color").trim();
    const l = color ? luminance(color) : null;
    return l === null ? null : l < 0.5;
  } catch { return null; }  // another origin: not readable
}

export function applyTheme() {
  if (!document.getElementById("dp-look")) {
    const style = document.createElement("style");
    style.id = "dp-look";
    style.textContent = sheet();
    document.head.append(style);
  }
  const { scheme, mode, size } = look();
  const root = document.documentElement;
  root.dataset.scheme = scheme;
  root.style.setProperty("--fs", String(SIZES[size] / SIZES.normal));
  const dark = mode === "auto" ? homeAssistantDark() : mode === "dark";
  root.style.colorScheme = dark === null ? "light dark" : dark ? "dark" : "light";
}
