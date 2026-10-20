# Changelog

## 0.1.0

- First version.
- Web interface in the sidebar (ingress), German and English, light and dark: connections
  with status and switch, details with live data, a form with templates, device list,
  advanced options and a live ser2net.yaml preview, import with preview, export, events
  (live and history with drops and availability), traces, settings with your own
  ser2net.yaml and the configuration history with differences and restore.
- ser2net 4.6.8 with gensio 3.0.4, built from their release tarballs (Alpine's gensio is too
  old to limit clients to networks).
- Connections are kept in the app's own configuration (versioned, checked field by field);
  ser2net.yaml is written from it. Each connection has a stable name inside ser2net, so a
  rename changes nothing for its clients.
- Saving rebuilds only the changed connections; their clients are disconnected so the change
  takes effect, all other connections keep theirs.
- New connections accept clients from private networks only, unless set otherwise.
- Events in the app log and in a history (SQLite, 30 days): start, devices found, missing
  and back, clients connected and disconnected (reported by ser2net itself), configuration
  changes, ser2net restarts. Repeating events are summed up.
- The last 20 configurations are kept for undo.
- Import of a ser2net 4 ser2net.yaml (version 1 and 2, with defines and defaults) or an
  old ser2net 3 ser2net.conf: with a
  preview of what is taken over, what collides and what cannot be; or from the config
  folder at start. Export of the connections as a ser2net.yaml.
- Your own ser2net.yaml can be used as it is instead of the forms.
- Status per connection: device and adapter (USB vendor, product, serial number, driver),
  clients with address, time and bytes, data rate, last data, line errors from the driver.
- Traces: always read along from ser2net in memory; recording to rotating files is switched
  per connection without disconnecting clients.
- Serial devices listed with their stable names; adapters without a serial number that
  cannot be told apart are marked.
- FTDI latency 1 ms per connection.
- Tools for smart meters: SML (with CRC check) and D0 decoded from the trace; baud rate and
  format detected by listening.
- Notifications in Home Assistant (and optionally a notify service) for missing devices,
  missing clients, silent devices, stuck clients, rising line errors, ser2net restarts.
- Diagnostics ZIP without IP addresses.
- Keep open: the app stays connected to a connection itself, so the device is open even
  without clients.
- A client that stops reading (and so slows down all others) is reported; optionally the
  connection's clients are disconnected.
- Addresses for Home Assistant, other apps (172.30.32.1) and the LAN.
- The log level is a setting of the app, applied without a restart.
- ser2net's admin interface listens on a socket inside the container only.
- ser2net is started again when it ends; health check on its admin socket; the history is
  written out completely before a backup.
