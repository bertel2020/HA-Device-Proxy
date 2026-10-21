# Device Proxy

The app shares devices with several programs at once:

- **Serial and USB devices** connected to Home Assistant on TCP ports, using
  [ser2net 4](https://github.com/cminyard/ser2net). Home Assistant integrations, other apps
  and programs elsewhere in the network connect to these ports instead of opening the device
  themselves – for example Z-Wave JS (`tcp://host:port`), ZHA and other pyserial-based
  integrations (`socket://host:port`) or a smart meter integration (host and port).
- **Modbus devices** through the app's own Modbus proxy: a device that accepts only one
  connection (many inverters, heat pumps, batteries, energy meters) or an RS485 bus with
  Modbus RTU gets a Modbus TCP port that several clients use at the same time – like the
  ha-modbusproxy app, plus Modbus RTU (see [Modbus devices](#modbus-devices)).

Everything is set up on the app's page in the sidebar (**Device Proxy**). The app has no options
of its own.

## Getting started

1. Install the app and start it; open **Device Proxy** in the sidebar.
2. Either **import** your existing configuration (**Connections → Import / Export**:
   ser2net 4 `ser2net.yaml`, ser2net 3 `ser2net.conf` or the options of ha-modbusproxy), or
   **add a connection**: choose serial device or Modbus device; for a serial device pick a
   template (smart meter SML or D0, Z-Wave stick, generic), the device from the list and a
   TCP port; for a Modbus device its address (or RS485 adapter) and the port for the
   clients.
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
(smart meters, GPS). For devices that answer requests (Z-Wave, many heat pumps) it works
only while one client at a time sends; for Modbus RTU use a Modbus connection instead, which
puts the requests in order.

When one client stops reading, ser2net slows down **all** clients of that connection. The
app reports such a client; optionally it disconnects the connection's clients (ser2net
cannot disconnect a single one) so they connect again.

### Keeping a device open

ser2net opens a device only while a client is connected. With **keep the device open** the
app stays connected itself, so "no data" warnings, line errors and the tools work without a
client. It takes one of the connection's client places.

## Modbus devices

A Modbus connection listens on a TCP port of its own and speaks Modbus TCP to its clients
(Home Assistant's Modbus integration, SolarEdge Modbus, evcc, ioBroker …). All their requests
go to the device one after another over a single connection; each answer goes back to the
client that asked. The app numbers the requests towards the device itself, so a late answer
to a request that timed out never reaches the next client. Waiting clients take turns: a
client that asks without a pause cannot hold up the others.


**Connection to the device**

| Kind | For | Settings |
|---|---|---|
| Modbus TCP | a device in the network | address and port (502) |
| Modbus RTU (serial) | an RS485 adapter on this host | device, baud rate and format |
| RTU over TCP | an RS485-to-Ethernet converter in transparent mode | address and port |

With Modbus RTU the app opens the adapter itself (not through ser2net) and keeps the pause
of 3.5 characters between frames that RTU needs. Unit 0 is a broadcast: it is sent, nobody
answers.

**Settings**: port for the clients (502 by default; each connection needs its own), number
of clients, answer timeout, further attempts, a pause after connecting (ha-modbusproxy's
`connection_time`, for devices that need a moment) and a pause between requests for slow
devices. Under **Advanced**: disconnect idle clients, replace the oldest client when all
places are taken, allowed clients and a bind address – the network setting applies as for
serial devices.

**Cache**: when several clients read the same registers (Home Assistant, evcc, a SolarEdge
integration …), a cache time of e.g. 500 ms lets the device answer each read only once in
that time; the same read while one is on its way waits for that answer. Only reads
(functions 1–4) are cached, never exceptions; a write empties the cache. Off by default.

**Write access**:
 Modbus has no login – whoever reaches the port could change registers. Per
connection: all clients may write (as with ha-modbusproxy), only listed addresses or
networks (e.g. `127.0.0.1` for Home Assistant, `172.30.32.0/23` for other apps), or nobody.
Refused writes (functions 5, 6, 15, 16, 21, 22, 23 and diagnostics other than the echo) get
exception 0x01 and are counted and logged; reading stays open to all allowed clients.

**When the device does not answer**
 the client gets Modbus exception 0x0B ("gateway target
device failed to respond"), when it cannot be reached 0x0A ("gateway path unavailable") – the
answers a Modbus gateway gives; the client stays connected. After three requests in a row
without an answer the device counts as not reachable (event, notification, entity). A
device that is not reachable is tried again every 30 seconds; a device that closed an idle
connection is connected again with the next request.

**Status**: reachable, clients with their requests, requests, answered, exceptions,
timeouts, errors, queue and answer time (average and maximum), the last error. The live
view and the recordings show each request and answer as hex with unit, function, register
and count (e.g. `unit 1 · FC03 read holding registers · @40000 ×4`).

Saving restarts only Modbus connections whose device or proxy settings changed; their
clients connect again. Name, trace and notifications change without a restart.

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

- Per connection (in the connection's form): device missing (for Modbus also: not
  reachable), no client connected (after a few minutes), no data from the device for a set
  time (serial devices, only while the device is open). A Modbus port that cannot be opened
  is always reported.
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

A Modbus connection has: device reachable, clients, requests, unanswered requests, answer
time and the switch.

Plus a device **Device Proxy** with "ser2net running". Without a broker nothing changes. Prefix
(`homeassistant`), base topic (`ser2net`) and the update interval are in **Settings → MQTT
entities**; the entity names follow the language of the notifications.

## Coming from ha-modbusproxy

Copy the options of ha-modbusproxy (its **Configuration** tab → ⋮ → **Edit in YAML**) and
paste them under **Connections → Import / Export**; each device becomes a Modbus connection
with the same ports, timeout and `connection_time`. A modbus-proxy configuration file
(`devices` with `modbus: url` and `listen: bind`) works too. At the start a file
`import/modbus-proxy.yaml` in the app's config folder is taken over like a ser2net file.

**Stop ha-modbusproxy first**: both apps listen on the host's network, so only one can have
port 502. The clients (e.g. the Modbus integration) need no change when the ports stay.

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
"keep open" and the meter tools are not used meanwhile. Modbus connections are not
ser2net's and keep working; their ports must not appear in your file.

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
| Modbus "port in use" | Another app (e.g. ha-modbusproxy) still listens on the port: stop it. |
| Modbus "not reachable" | Address and port of the device; does the device allow only one connection that another program still holds? |
| Modbus answers 0x0B | The device does not answer in time: raise the timeout, check the unit id; for RTU baud rate, format and wiring (A/B). |

## Files

| Path | Content |
|---|---|
| `/addon_configs/<…>_device_proxy/ser2net.yaml` | your own configuration (optional) |
| `/addon_configs/<…>_device_proxy/import/` | a file to take over at the start (`ser2net.yaml`, `ser2net.conf`, `modbus-proxy.yaml`) |
| `/addon_configs/<…>_device_proxy/trace/` | recorded traces |
| app data (in the backup) | connections, settings, history, configuration versions |
