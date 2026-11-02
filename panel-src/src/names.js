// The suggested name of a new connection: short and saying what is connected, not the USB
// strings verbatim ("EnOcean GmbH EnOcean Programmer V3.2" becomes "EnOcean Programmer").

// USB-serial chips name themselves, not the device behind them
const BRIDGE = /\b(cp210\d|ft2?23\d\w*|ft23\d\w*|ch34\d|ch910\d|pl230\d|uart|usb[\s-]*(2\.0[\s-]*)?(to[\s-]*)?ser(ial)?|serial[\s-]*(converter|controller|port)|usb[\s-]*rs[\s-]*(232|485))\b/i;
const CHIP_MAKERS = /^(ftdi|silicon labs|silicon laboratories|qinheng|wch|prolific|future technology devices)/i;
const LEGAL = /[\s,]+(gmbh(\s*&\s*co\.?\s*kg)?|ag|kg|inc\.?|ltd\.?|llc|co\.?,?\s*ltd\.?|corp(oration|\.)?|b\.?v\.?|s\.?a\.?|s\.?r\.?l\.?|electronics|technolog(y|ies))$/i;
const VERSION = /[\s_-]+(v|ver\.?\s*|rev\.?\s*)\d+(\.\d+)*[a-z]?\b|[\s_-]+\d+(\.\d+)+$/gi; // "V3.2", "Rev 2", a trailing "1.0"
const MAX = 32;

const cut = (s) => (s.length <= MAX ? s : s.slice(0, MAX + 1).replace(/\s+\S*$/, "")); // whole words
const tidy = (s) => (s || "").replace(/_/g, " ").replace(/\s+/g, " ").trim();
const company = (s) => {
  let m = tidy(s), prev;
  do { prev = m; m = m.replace(LEGAL, ""); } while (m !== prev);
  return m;
};

/** What the device's USB strings say about it, or "" when they only name a USB-serial chip. */
export function deviceName(manufacturer, product) {
  const maker = company(manufacturer);
  const what = tidy((product || "").replace(VERSION, ""));
  if (!what || BRIDGE.test(what)) return "";
  if (!maker || CHIP_MAKERS.test(maker) || what.toLowerCase().includes(maker.split(" ")[0].toLowerCase())) return cut(what);
  const both = `${maker} ${what}`;
  return both.length <= MAX ? both : cut(what);
}

/** base, or "base 2", "base 3" … when another connection has that name already. */
export function uniqueName(base, taken) {
  const used = new Set(taken.map((n) => n.trim().toLowerCase()));
  let name = base, n = 2;
  while (used.has(name.toLowerCase())) name = `${base} ${n++}`;
  return name;
}
