// What a USB adapter is, as far as its USB strings tell, and which adapter fits a new connection.
// Only sticks that name themselves are recognized; meter read heads are plain USB-serial chips.

const KINDS = {
  zwave: { text: /z-?wave|\bzwa-?\d|\buzb\d*\b|z-?stick/i, ids: ["0658:0200"] }, // Aeotec / Sigma Designs
  enocean: { text: /enocean|\busb ?300\b|\btcm ?3\d0|\bfam-?usb|\bfgw14|\bfam14|eltako/i, ids: [] },
  zigbee: { text: /zigbee|skyconnect|conbee|raspbee|\bzbt-?\d|slzb|cc2652|cc2531|efr32|ezsp/i, ids: ["1cf1:0030"] }, // ConBee II
};

/** "zwave", "enocean", "zigbee", or "" when the adapter does not say what it is. */
export function usbKind(x) {
  const text = `${x.manufacturer || ""} ${x.product || ""}`, id = `${x.vendor_id}:${x.product_id}`;
  return Object.keys(KINDS).find((k) => KINDS[k].text.test(text) || KINDS[k].ids.includes(id)) || "";
}

/** A free adapter for a connection that wants this kind ("" for a plain serial device such as a
 * meter read head): one recognized as that kind, else one not recognized as anything, else any. */
export function pickDevice(devices, want) {
  const free = devices.filter((x) => !x.used_by);
  const found = (want && free.find((x) => usbKind(x) === want)) || free.find((x) => !usbKind(x)) || free[0];
  return found ? found.stable : "";
}
