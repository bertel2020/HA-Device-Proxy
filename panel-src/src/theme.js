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
  const dark = homeAssistantDark();
  document.documentElement.style.colorScheme = dark === null ? "light dark" : dark ? "dark" : "light";
}
