// Registers read with the tool, decoded as Home Assistant's modbus integration would: the
// same data types and the same "swap" (byte: the two bytes of each register, word: the order
// of the registers), so a value that looks right here is right in a sensor with these settings.

import { lang } from "./i18n.js";

export const TYPES = ["int16", "uint16", "int32", "uint32", "float32", "int64", "uint64", "float64", "string"];
export const SWAPS = ["none", "word", "byte", "word_byte"];

/** Registers per value; a string takes them all. */
export function width(type, count) {
  if (type === "string") return count;
  return { int16: 1, uint16: 1, int32: 2, uint32: 2, float32: 2, int64: 4, uint64: 4, float64: 4 }[type] || 1;
}

/** Swaps that make sense for a type: one register has no word order. */
export function swapsFor(type) {
  return type === "string" || width(type, 2) === 1 ? ["none", "byte"] : SWAPS;
}

function bytesOf(regs, swap) {
  const words = swap === "word" || swap === "word_byte" ? [...regs].reverse() : regs;
  const out = new Uint8Array(words.length * 2);
  words.forEach((w, i) => {
    const hi = (w >> 8) & 0xff, lo = w & 0xff;
    const swapped = swap === "byte" || swap === "word_byte";
    out[i * 2] = swapped ? lo : hi;
    out[i * 2 + 1] = swapped ? hi : lo;
  });
  return out;
}

/** One value from its registers; scale applies to numbers (as in Home Assistant). */
export function decode(regs, type, swap, scale = 1) {
  const b = bytesOf(regs, swap);
  const v = new DataView(b.buffer);
  const num = (x) => (scale === 1 ? x : x * scale);
  switch (type) {
    case "int16": return num(v.getInt16(0));
    case "uint16": return num(v.getUint16(0));
    case "int32": return num(v.getInt32(0));
    case "uint32": return num(v.getUint32(0));
    case "float32": return num(v.getFloat32(0));
    case "float64": return num(v.getFloat64(0));
    case "int64": return scale === 1 ? v.getBigInt64(0) : Number(v.getBigInt64(0)) * scale;
    case "uint64": return scale === 1 ? v.getBigUint64(0) : Number(v.getBigUint64(0)) * scale;
    case "string": return String.fromCharCode(...b.filter((c) => c !== 0)).trim();
    default: return null;
  }
}

/** The values of a read as rows: address of the first register, its registers, the value. */
export function rows(values, address, type, swap, scale) {
  const n = width(type, values.length), out = [];
  for (let i = 0; i + n <= values.length; i += n) {
    const regs = values.slice(i, i + n);
    out.push({ address: address + i, regs, value: decode(regs, type, swap, scale) });
  }
  return out;
}

/** A number as text: floats rounded to what the eye needs, NaN as such. */
export function fmtValue(v) {
  if (typeof v === "bigint") return v.toLocaleString(lang);
  if (typeof v !== "number") return v;
  if (!Number.isFinite(v)) return String(v);
  if (v !== 0 && (Math.abs(v) < 1e-4 || Math.abs(v) >= 1e15)) return v.toExponential(4);
  return Number.isInteger(v) ? v.toLocaleString(lang) : v.toLocaleString(lang, { maximumFractionDigits: 6 });
}

// the same as DEVICE_CLASSES in modbus_entities.py: Home Assistant refuses an unknown one
export const DEVICE_CLASSES = ["apparent_power", "battery", "current", "energy", "frequency", "gas", "humidity", "power", "power_factor", "pressure", "reactive_power", "temperature", "voltage", "volume", "water"];

/** The line of a register in a connection's register_entities (modbus_entities.py). */
export function entityLine({ unit, fc, address, type, swap, scale, count, uom, deviceClass, name }) {
  const kind = type === "string" ? `string:${count}` : type;
  return `${unit} ${fc} ${address} ${kind} ${swap} ${scale} ${uom.trim() || "-"} ${deviceClass || "-"} ${name.trim().replace(/\s+/g, " ")}`;
}

/** A sensor for Home Assistant's modbus: integration (under the hub's sensors:). */
export function sensorYaml({ unit, fc, address, type, swap, scale, count }) {
  const lines = [
    `- name: "Register ${address}"`,
    `  device_address: ${unit}`,
    `  address: ${address}`,
    `  input_type: ${fc === 4 ? "input" : "holding"}`,
    `  data_type: ${type}`,
  ];
  if (type === "string") lines.push(`  count: ${count}`);
  if (swap !== "none") lines.push(`  swap: ${swap}`);
  if (type !== "string" && scale !== 1) lines.push(`  scale: ${scale}`);
  if (type !== "string" && (type.startsWith("float") || !Number.isInteger(scale))) lines.push("  precision: 2");
  lines.push("  scan_interval: 30");
  return lines.join("\n");
}

// Starting values per vendor (MODBUS_PROFILES in model.py). The timing goes with the device; the
// port only where a new connection is made, a device the scan found has its port already.
const TIMING = { request_timeout_ms: 3000, connect_delay_ms: 0, request_gap_ms: 0, retries: 1 };
export const PROFILES = {
  modbus: { ...TIMING, host_port: 502 },
  mb_solaredge: { ...TIMING, host_port: 1502, request_timeout_ms: 5000 },
  mb_huawei: { ...TIMING, host_port: 502, request_timeout_ms: 10000, connect_delay_ms: 1000, request_gap_ms: 50 },
  mb_fronius: { ...TIMING, host_port: 502 },
  mb_sma: { ...TIMING, host_port: 502 },
  mb_kostal: { ...TIMING, host_port: 1502 },
  mb_sungrow: { ...TIMING, host_port: 502, request_timeout_ms: 10000, connect_delay_ms: 5000, request_gap_ms: 50 },
  mb_victron: { ...TIMING, host_port: 502 },
};

/** A profile's timing, without the port. */
export function profileTiming(key) {
  const { host_port: _port, ...timing } = PROFILES[key];
  return timing;
}

// integrations that fit a device the scan identified, by its vendor; any other SunSpec device
// works with the SunSpec integration
const INTEGRATIONS = [
  [/solaredge/i, "SolarEdge Modbus Multi (HACS)"],
  [/huawei/i, "Huawei Solar (HACS)"],
];
const VENDORS = [
  [/solaredge/i, "mb_solaredge"], [/huawei/i, "mb_huawei"], [/fronius/i, "mb_fronius"], [/\bsma\b/i, "mb_sma"],
  [/kostal/i, "mb_kostal"], [/sungrow/i, "mb_sungrow"], [/victron/i, "mb_victron"],
];

/** Who a unit is, from the scan's identification: vendor, product, revision, a fitting integration. */
export function identity(u) {
  const id = { ...(u.sunspec || {}), ...(u.ident || {}) };
  if (!id.vendor && !id.product) return null;
  const hit = INTEGRATIONS.find(([re]) => re.test(id.vendor || ""));
  const profile = VENDORS.find(([re]) => re.test(id.vendor || ""));
  return { ...id, sunspec: u.sunspec ? u.sunspec.base : null, integration: hit ? hit[1] : u.sunspec ? "SunSpec (HACS)" : null, profile: profile ? profile[1] : null };
}

const MIN_REQUESTS = 50; // what the tips need before they say anything
const roundUp = (ms, step) => Math.ceil(ms / step) * step;

/** Suggestions from what the proxy measured: timeout, cache, load. Each: [key, values]. */
export function timingTips(c, m) {
  const tips = [];
  if (!m || (m.requests || 0) < MIN_REQUESTS) return tips;
  const timeout = c.request_timeout_ms, slow = m.time_max_ms || 0;
  const timeoutShare = m.timeouts / m.requests;
  if (timeoutShare >= 0.02 && slow >= timeout * 0.7) {
    tips.push(["tipTimeoutUp", { p: Math.round(timeoutShare * 100), t: timeout, s: roundUp(Math.max(slow * 2, timeout + 1000), 500) }]);
  } else if (timeoutShare >= 0.02) {
    tips.push(["tipTimeoutsFast", { p: Math.round(timeoutShare * 100), m: Math.round(slow) }]);
  } else if (!m.timeouts && m.answered >= 200 && timeout >= 3000 && timeout >= slow * 5) {
    tips.push(["tipTimeoutDown", { t: timeout, m: Math.round(slow), s: roundUp(Math.max(slow * 3, 1500), 500) }]);
  }
  const clients = (c.clients || []).length;
  if (!c.cache_ms && clients >= 2) tips.push(["tipCache", { n: clients }]);
  if (c.cache_ms && m.cached) tips.push(["tipCacheSaves", { p: Math.round((m.cached / m.requests) * 100) }]);
  if ((m.queue_max || 0) >= 5) tips.push(["tipQueue", { q: m.queue_max, a: Math.round(m.time_avg_ms) }]);
  if (m.exceptions / m.requests >= 0.05) tips.push(["tipExceptions", { p: Math.round((m.exceptions / m.requests) * 100) }]);
  return tips;
}
