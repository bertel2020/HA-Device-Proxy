// Talks to the app's JSON API. All URLs are relative, so the page works under the ingress path.
const base = new URL(".", location.href.split("#")[0]);

export const url = (path) => new URL(path, base).href;

export class ApiError extends Error {
  constructor(status, data) {
    super((data && data.error) || `HTTP ${status}`);
    this.status = status;
    this.data = data || {};
  }
}

export async function api(path, { method = "GET", body } = {}) {
  const response = await fetch(url(path), {
    method,
    credentials: "same-origin",
    headers: body === undefined ? {} : { "Content-Type": "application/json" },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  const type = response.headers.get("content-type") || "";
  const data = type.includes("json") ? await response.json() : await response.text();
  if (!response.ok) throw new ApiError(response.status, typeof data === "object" ? data : { error: data });
  return data;
}

// What the status adds to a connection; dropped before the connection is saved again.
const STATUS_KEYS = ["alias", "present", "tty", "usb", "running", "pending", "clients", "kept_open", "bytes_from_device",
  "bytes_to_device", "rate_from_device", "rate_to_device", "last_data", "line_errors", "latency", "addresses"];

export const toConnection = (status) => Object.fromEntries(Object.entries(status).filter(([k]) => !STATUS_KEYS.includes(k)));

export const saveConnection = (connection) =>
  connection.id
    ? api(`api/connections/${connection.id}`, { method: "PUT", body: { connection } })
    : api("api/connections", { method: "POST", body: { connection } });
