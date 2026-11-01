// Registers read with the tool, decoded as Home Assistant's modbus integration would: the
// same data types and the same "swap" (byte: the two bytes of each register, word: the order
// of the registers), so a value that looks right here is right in a sensor with these settings.

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
  if (typeof v === "bigint") return v.toLocaleString();
  if (typeof v !== "number") return v;
  if (!Number.isFinite(v)) return String(v);
  if (v !== 0 && (Math.abs(v) < 1e-4 || Math.abs(v) >= 1e15)) return v.toExponential(4);
  return Number.isInteger(v) ? v.toLocaleString() : v.toLocaleString(undefined, { maximumFractionDigits: 6 });
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
