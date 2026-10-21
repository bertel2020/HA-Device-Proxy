# Device Proxy

The app makes serial and USB devices connected to Home Assistant available on TCP ports,
using [ser2net 4](https://github.com/cminyard/ser2net). Home Assistant integrations, other
apps and programs elsewhere in the network connect to these ports instead of opening the
device themselves – for example Z-Wave JS (`tcp://host:port`), ZHA and other pyserial-based
integrations (`socket://host:port`) or a smart meter integration (host and port).

Everything is set up on the app's page in the sidebar (**Device Proxy**). The app has no options
of its own.

## Getting started

1. Install the app and start it; open **Device Proxy** in the sidebar.
2. Either **import** your existing ser2net configuration (**Connections → Import / Export**,
   ser2net 4 `ser2net.yaml` or ser2net 3 `ser2net.conf`), or **add a connection**: pick a
   template (smart meter SML or D0, Z-Wave stick, generic), the device from the list and a
   TCP port.
3. Point the clients at the address the connection shows (**Details → Addresses**):

| Client | Address |
|---|---|
| Home Assistant integrations | `127.0.0.1` and the port |
| Other apps (e.g. Z-Wave JS UI) | `172.30.32.1` and the port – in the Supervisor network 127.0.0.1 is the app itself |
| Other computers | the host's LAN address and the port |

Saving a connection rebuilds only that connection; all others keep their clients.

## Connections

**Templates** fill in the fields; everything stays editable. **Device**: the list shows each
serial adapter with its stable name (`/dev/serial/by-id/…`), vendor, product and serial
number. Identical adapters without a serial number (many CH340) are told apart by their USB
port (`/dev/serial/by-path/…`); the app warns about them.

**Advanced** holds ser2net's options, all optional: flow control (RTS/CTS, XON/XOFF), modem
lines (`local`), DTR/RTS on open, RS485, timeout, retry time, allowed clients (`remaddr`),
banner, open and close strings, `nodelay`, a bind address, FTDI latency and further ser2net
options as `name: value` lines. The form shows the resulting `ser2net.yaml` part while you
type.

### Who may connect

**Settings → Network** applies to all connections without their own bind address or
`remaddr`:

- **This host only** – 127.0.0.1, reachable by Home Assistant only.
- **LAN** (default) – only from private networks (10/8, 172.16/12, 192.168/16, IPv6 local).
- **All networks** – no limit. ser2net has no login: whoever reaches the port can read and
  control the device.

### Several clients on one device

A connection can allow several clients. Every client gets all data from the device; what the
clients send goes to the device unchanged and unordered. This suits devices that only send
(smart meters, GPS). For devices that answer requests (Z-Wave, Modbus RTU, many heat pumps)
it works only while one client at a time sends.

When one client stops reading, ser2net slows down **all** clients of that connection. The
app reports such a client; optionally it disconnects the connection's clients (ser2net
cannot disconnect a single one) so they connect again.

### Keeping a device open

ser2net opens a device only while a client is connected. With **keep the device open** the
app stays connected itself, so "no data" warnings, line errors and the tools work without a
client. It takes one of the connection's client places.

## Status, traces and line errors

- **Status**: device present (and which adapter it is), clients with address, time and bytes,
  data rate and the last data from the device.
- **Live data and traces**: ser2net traces every connection into memory and the app reads
  along. The live view works at any time and takes no client place. **Recording** to files
  (from the device, to the device or both) is switched per connection without touching
  ser2net – no client is disconnected. Files: `/addon_configs/<…>_device_proxy/trace/<name>.log`,
  rotated by size (**Settings → Logging and storage**).
- **Line errors** (frame, parity, overrun, break) come from the adapter's driver while the
  device is open. Rising numbers usually mean a wrong baud rate or format. Not every driver
  counts them.
- **FTDI latency**: FTDI adapters wait 16 ms before passing data on; "low latency" sets 1 ms
  (better for Z-Wave). If the system does not let the app change it, the app says so.

## Tools for smart meters

On a connection's details:

- **Check meter data** reads the last 30 seconds as SML (binary, each telegram's CRC
  checked) or D0 (text) and shows the readings, e.g. the import total.
- **Detect baud rate** listens at each speed and format in turn and offers the best matches
  to take over. ser2net lets go of the device meanwhile (up to about a minute): the
  connection's clients are disconnected and connect again afterwards. Nothing is sent to the
  device, so it works with meters that push their data.

## Events and history

**Events** shows the live log (filter by connection, level and text) and the history:
drops and availability per connection over 30 days and a timeline. Repeating events, such as
a stick that keeps dropping out, are summed up. The history is kept 30 days by default.
**Settings → Configuration history** keeps the last 20 configurations with their
differences; each one can be restored.

## Notifications

Problems appear under Home Assistant's bell: one notification per connection and problem,
updated instead of repeated, and removed when the problem is gone (can be switched off).
Optionally a notify service (e.g. the companion app on a phone) gets them too.

- Per connection (in the connection's form): device missing, no client connected (after a
  few minutes), no data from the device for a set time (only while the device is open).
- For all (**Settings → Notifications**): a client stops reading, line errors rise, ser2net
  keeps restarting, your own `ser2net.yaml` cannot be used.

A problem is reported only after it lasted the grace time (30 s by default) and not in the
first minute after the app started.

## Entities in Home Assistant (MQTT)

With an MQTT broker in Home Assistant (e.g. the Mosquitto add-on) the app creates one device
per connection through MQTT discovery. Nothing to set up: the broker comes from the
Supervisor.

| Entity | Content |
|---|---|
| Device connected | the device is plugged in |
| Clients | connected clients |
| Data rate | bytes per second from the device |
| Data from the device | bytes since ser2net started |
| Last data | when the device last sent something |
| Line errors | errors counted by the driver since the start |
| Active (switch) | turns the connection on and off |

Plus a device **Device Proxy** with "ser2net running". Without a broker nothing changes. Prefix
(`homeassistant`), base topic (`ser2net`) and the update interval are in **Settings → MQTT
entities**; the entity names follow the language of the notifications.

## Taking over an existing configuration

A ser2net 4 `ser2net.yaml` (version 1 or 2, with defines and defaults) or a ser2net 3
`ser2net.conf` can be imported:

- in the web interface: choose or paste the file, check the preview (what is taken over,
  what collides with an existing connection, what cannot be taken over) and choose per
  collision: replace, new port or skip;
- or at the start: put the file into the app's config folder as `import/ser2net.yaml` or
  `import/ser2net.conf` (`/addon_configs/<…>_device_proxy/import/`). Collisions are skipped, the
  app log lists all notes and the file is renamed to `….imported-<time>`.

`/dev/ttyUSB3` and the like are replaced by their stable by-id (else by-path) name. Not
taken over: other accepters than TCP (SSL, SCTP, UDP, mux, certauth), other devices than
serial ports, unknown serial options, rotators, LEDs and admin sections. Unknown ser2net
options become further options.

Keep the old ports and the clients need no change. Stop the old ser2net first – both cannot
listen on the same port.

ser2net ignores the modem lines only with `local`; the forms set it for new connections, an
import keeps what the file says.

**Export** writes the connections as a ser2net 4 `ser2net.yaml` for any ser2net.

## Using your own ser2net.yaml

For setups the forms cannot express, **Settings → Configuration source → Own ser2net.yaml**
uses your file as it is (`/addon_configs/<…>_device_proxy/ser2net.yaml`, editable in the app with
a check). It must not contain an admin section: the app adds its own. Status, events,
history, notifications and MQTT keep working, with ser2net's connection names; the forms,
"keep open" and the meter tools are not used meanwhile.

## Proxmox

When Home Assistant runs as a VM, pass the USB adapters through to the VM. Identical
adapters without a serial number can only be told apart when they are passed through by
USB port, not by vendor and product ID. If a stick keeps disconnecting, try switching the
USB3 option of the passed-through device.

## Diagnostics

**Settings → Diagnostics** downloads a ZIP with versions, configuration, status, devices and
the recent events. IP addresses are replaced and clients only counted, so it can be attached
to an issue as it is.

## When something does not work

| What you see | What to check |
|---|---|
| Device missing | Is the adapter passed through to the VM? Does it show in the device list? |
| Waiting for ser2net | The app log: ser2net reports why it does not start (e.g. a port in use). |
| A client is refused | Network setting or `remaddr`: is the client's address allowed? |
| Data looks like noise | Baud rate or format: use **Detect baud rate** or the template. |
| Line errors rise | Same as noise; also the cable or the USB3 option in Proxmox. |
| All clients slow | A client stopped reading (marked on the connection). |
| "Change pending" | ser2net applies a change when the clients reconnect; the app disconnects them. |

## Files

| Path | Content |
|---|---|
| `/addon_configs/<…>_device_proxy/ser2net.yaml` | your own configuration (optional) |
| `/addon_configs/<…>_device_proxy/import/` | a file to take over at the start |
| `/addon_configs/<…>_device_proxy/trace/` | recorded traces |
| app data (in the backup) | connections, settings, history, configuration versions |
