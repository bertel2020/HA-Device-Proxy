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
- **EnOcean gateways** (FAM-USB, FAM14, FGW14-USB, USB300, MGW-ETH …) through the app's own
  EnOcean proxy: several programs (Home Assistant, eo_man, PCT14) share one gateway (see
  [EnOcean gateways](#enocean-gateways)).

Everything is set up on the app's page in the sidebar (**Device Proxy**). The app has no options
of its own, so its **Configuration** tab in the Supervisor is empty on purpose: open **Device Proxy**
in the sidebar instead.

## Getting started

1. Install the app and start it; open **Device Proxy** in the sidebar.
2. Either **import** your existing configuration (**Settings → Back up and transfer → Import**:
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

Saving a connection rebuilds only that connection; all others keep their clients. The form
warns when the chosen port is already taken by another program (e.g. a still running
ha-modbusproxy); saving works anyway, the connection starts once the port is free.


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

- **Home Assistant only** – 127.0.0.1, this host only.
- **Home Assistant and apps** – also the other apps (e.g. Z-Wave JS UI), 127.0.0.0/8 and
  172.30.32.0/23, but nothing from the LAN.
- **Home network** (default) – Home Assistant, its apps and the networks listed under
  **Allowed networks**. "My network" (the host's network, read from the Supervisor) is
  predefined; add further networks such as `192.168.80.0/24` or use the private ranges. An
  empty list lets only Home Assistant and the apps in. Installations from before this list
  existed keep the private ranges (10/8, 172.16/12, 192.168/16).
- **Anyone** – no limit. ser2net has no login: whoever reaches the port can read and control
  the device.

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
answers. RTU has no transaction ids, so an answer must fit its request (unit, function,
byte count, the echo of a write), and after a timeout or a broken answer the line gets
half a second for late bytes before the next request – a late answer never reaches the
wrong client.

**Settings**: port for the clients (502 by default; each connection needs its own), number
of clients, answer timeout, further attempts, a pause after connecting (ha-modbusproxy's
`connection_time`, for devices that need a moment) and a pause between requests for slow
devices. Under **Advanced**: disconnect idle clients and replace the oldest client when all
places are taken. Allowed clients and a bind address are in the **Network access** card – the
network setting applies as for serial devices.

**Probe**: optionally the app reads one register (unit, function 3 or 4, address) after a
set time without requests. The state "reachable" is then right without clients, and devices
that close idle connections keep theirs. A probe that gets no answer (after its retries)
marks the device not reachable at once. Probes are counted on their own, not as requests.

**Cache**: when several clients read the same registers (Home Assistant, evcc, a SolarEdge
integration …), a cache time of e.g. 500 ms lets the device answer each read only once in
that time; the same read while one is on its way waits for that answer. Only reads
(functions 1–4) are cached, never exceptions; a write empties the cache. Off by default.

**Connections to the device**: for a network device that allows several connections at
once (up to 4), the requests can run in parallel over that many connections – faster with
many clients. Leave it at 1 for devices that take one connection only (most inverters);
Modbus RTU always has one line.

**Write access**: Modbus has no login – whoever reaches the port could change registers. Per
connection: all clients may write (as with ha-modbusproxy), only listed addresses or
networks, or nobody. A new connection starts with "only these": `127.0.0.1` (Home
Assistant) and `172.30.32.0/23` (other apps); connections imported from ha-modbusproxy
keep "all clients", so nothing changes for their clients. Only known reads pass (functions
1–4, 7, 11, 12, 17, 20, 24, the diagnostics echo and reading the device identification), and
only with the exact length of that request; everything else – writes, vendor functions such
as Huawei's 0x41 – gets exception 0x01 and is counted and logged. Reading stays open to all
allowed clients.

**Unit ids**: under **Advanced** the unit a client asks for can be rewritten
(`client=device`, e.g. `1=3, 2=5`), for clients that always ask unit 1 while the device
answers on another one. Imported from modbus-proxy's `unit_id_remapping`.

**When the device does not answer** the client gets Modbus exception 0x0B ("gateway target
device failed to respond"), when it cannot be reached 0x0A ("gateway path unavailable") – the
answers a Modbus gateway gives; the client stays connected. After three requests in a row
without an answer the device counts as not reachable (event, notification, entity). A
device that is not reachable is tried again every 30 seconds; a device that closed an idle
connection is connected again with the next request.

**Status**: reachable, clients with their requests, requests, answered, exceptions,
timeouts, errors, queue and answer time (average and maximum), the last error; per unit id
(each device on an RS485 bus) requests, exceptions, unanswered requests and answer time.
The live view and the recordings show each request and answer as hex with unit, function,
register and count (e.g. `unit 1 · FC03 read holding registers · @40000 ×4`).

**Tools** on a Modbus connection's details:

- **Read registers**: unit, function (holding or input registers, coils, discrete inputs),
  address (from 0, as in the frame) and count; the values as unsigned, signed and hex. The
  request waits its turn with the clients' and does not use the cache.
- **Write registers**: function 5 or 15 (coils) or 6 or 16 (registers), address and value(s),
  several separated by commas. A dialog asks first; afterwards the value is read back and
  compared. Each write is an event in the log. The tool stays locked when the connection's
  write access is "Nobody".
- **Scan the bus**: which unit ids answer (it reads register 0, an exception counts as an
  answer too). The units found can be taken over into "read registers".

Tool requests are not counted as the clients'. Only "write registers" changes the device.

**Use in Home Assistant**: most devices have an integration of their own (e.g. SolarEdge
Modbus). Add it under **Settings → Devices & services → Add integration**, choose the network
connection (Modbus TCP) and enter the host and port the details page shows (`127.0.0.1` and the
connection's port, each with a copy button). The unit id (called device id in some integrations)
is the one of the device, usually 1. Only if no integration supports your device, use a Modbus
hub in `configuration.yaml`: the details page has the snippet to copy (`type: tcp`, host, port);
add the sensors as the Modbus integration's documentation describes (`address` and
`device_address`, the unit id).

Saving restarts only Modbus connections whose device or proxy settings changed; their
clients connect again. Name, trace and notifications change without a restart.

## EnOcean gateways

An EnOcean connection shares one EnOcean gateway (FAM-USB, FAM14, FGW14-USB, USB300/TCM310,
PioTek MGW-ETH, Symcon LAN …) with several programs: the
[EnOcean Eltako integration](https://github.com/bertel2020/HA-Enocean-Eltako), the old
`eltako` integration, eo_man or PCT14 over the network. It takes over everything the
[EnOcean Proxy app](https://github.com/bertel2020/HA-Enocean-Proxy) did (an import of that app's options is not offered). The app opens the
gateway itself (not through ser2net) and offers it on a TCP port as raw ESP2 or ESP3 frames,
like ser2net would.

- Every telegram from the gateway goes to every program. Frames a program sends are queued
  and go to the gateway one at a time, whole, with a short pause (**Pause between frames
  sent**), so two programs never interleave. Frames are not echoed to the other programs.
- The gateway's answer to a command (base ID, settings …) goes back to the program that
  asked; FAM14 bus traffic (ESP2 ORG ≥ F0) goes to all.
- While the gateway is away, programs stay connected and their frames are dropped; the app
  reconnects by itself (1, 2, 5, 10, 30 s).
- A program that stops reading is disconnected before its data piles up (256 KiB).

**Templates** set protocol, baud rate and kind of connection; everything stays changeable:

| Template | Protocol | Connection |
|---|---|---|
| FAM-USB | ESP2 | USB, 9600 baud |
| FAM14, FGW14-USB | ESP2 | USB, 57600 baud |
| USB300 / TCM310 | ESP3 | USB, 57600 baud |
| PioTek MGW-ETH | ESP3 | TCP, port 5100 (one session only: share it through this app) |
| Symcon LAN | ESP3 | TCP, port 5000 |

**Who may connect**: new gateways follow the network setting, like the other kinds, so a PC
with eo_man or PCT14 in the home network can connect at once. To limit one gateway, enter
addresses or networks under **Allowed clients**, or press "Only Home Assistant and apps"
(`127.0.0.1, 172.30.32.0/23`).

**Replay**: the EnOcean Eltako integration asks for it (`EOPX REPLAY TS`) after every
connect. Radio telegrams that arrive while no such program is connected, e.g. during a Home
Assistant restart, are kept (1000 telegrams, 15 minutes by default) and handed over with their
reception time. **Keep the buffer on disk** keeps them over a restart of this app too
(`/data/replay`).

**Discovery and status**: the app announces its active gateways to the EnOcean Eltako
integration, which offers each one for setup with replay switched on. A read-only status
(port 9199, Home Assistant and the apps only) feeds the integration's gateway cards. Both are
under **Settings → EnOcean**.

**The detail page** shows what is wrong in plain words (gateway away, port taken, air time,
frames dropped or held back, programs refused or disconnected, no program connected), every
frame live with its kind and sender (search, direction, a click on an ID shows only that
sender, copy, take over into "send"), the air time of the last hour against the 1 % limit
(a notification at 80 %), counters and the replay buffer, and the base ID once the gateway
told it. Tools:

- **Gateway test**: reads the base ID ten times; nothing goes over the air.
- **Change base ID**: sets the gateway's base ID (FF-80-00-00 to FF-FF-FF-80, last byte 00 or 80).
  The gateway keeps it in flash and allows only a few changes (10 for TCM 300 modules such as the
  USB300); ESP3 gateways report how many are left, shown next to the base ID. Taught-in actuators
  know the old ID and must be taught in again.
- **Send a frame**: one whole frame as hex, checked while you type (sync, length, ESP2
  checksum, ESP3 CRCs), with a button to add or fix the checksum; the answer is shown.
- **Record frames (PCT14)**: a single recording of every frame in both directions as JSON lines (time, gateway, direction, kind,
  program, hex) into the trace folder, at most 50 MB; listed, downloaded and deleted on the
  **Trace** page. Optionally only one program may send meanwhile, e.g. PCT14 reading a FAM14:
  the frames of the others are held back and the app's own tools wait.

## Status, traces and line errors

- **Status**: device present (and which adapter it is), clients with address, time and bytes,
  data rate and the last data from the device.
- **Live data and traces**: ser2net traces every connection into memory and the app reads
  along. The live view works at any time and takes no client place. **Recording** to files
  (from the device, to the device or both) is switched per connection on the **Trace** page without touching
  ser2net – no client is disconnected. Files: `/addon_configs/<…>_device_proxy/trace/<name>.log`,
  rotated by size (**Settings → Logs and retention**).
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
**Settings → Configuration history** keeps the last 25 configurations with their
differences; each one can be restored.

## Notifications

Problems appear under Home Assistant's bell: one notification per connection and problem,
updated instead of repeated, and removed when the problem is gone (can be switched off).
Optionally a notify service (e.g. the companion app on a phone) gets them too.

- Per connection (in the connection's form): device missing (for Modbus also: not
  reachable), no client connected (after a few minutes), no data from the device for a set
  time (serial devices, only while the device is open). A Modbus port that cannot be opened
  is always reported. An EnOcean gateway: not reachable, and air time at 80 % of the limit.
- For all (**Settings → Notifications**): a client stops reading, line errors rise, ser2net
  keeps restarting, your own `ser2net.yaml` cannot be used.

A problem is reported only after it lasted the grace time (30 s by default) and not in the
first minute after the app started.

## Entities in Home Assistant (MQTT)

With an MQTT broker in Home Assistant (e.g. the Mosquitto add-on) the app creates one device
per connection through MQTT discovery. Usually nothing to set up: the broker comes from the
Supervisor. Another broker (host, port, user, password, TLS) can be set under **Settings →
MQTT entities**, where the entities can also be switched off.

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
time and the switch. An EnOcean gateway has: gateway reachable, clients, telegrams from the
gateway, air time (share of the 1 % limit) and the switch.

Plus a device **Device Proxy** with "ser2net running". Without a broker nothing changes. Prefix
(`homeassistant`), base topic (`device_proxy`) and the update interval are in **Settings → MQTT
entities**; the entity names follow the language of the notifications.

## Coming from ha-modbusproxy

Copy the options of ha-modbusproxy (its **Configuration** tab → ⋮ → **Edit in YAML**) and
paste them under **Settings → Back up and transfer → Import**; each device becomes a Modbus connection
with the same ports, timeout and `connection_time`. A modbus-proxy configuration file
(YAML or TOML, `devices` with `modbus: url`, `listen: bind` and `unit_id_remapping`) works
too. At the start a file
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

**Export as ser2net YAML** writes the serial connections as a ser2net 4 `ser2net.yaml` for any
ser2net; Modbus and EnOcean connections are not part of it, because the app serves them itself.

## Backup and restore

**Settings → Back up and transfer** saves everything the app was set up with – all
connections (serial, Modbus, EnOcean) and the settings – as one JSON file. **Restore from
backup** shows what the file holds and replaces the current configuration after you confirm;
the old state stays in the configuration history. The file contains the MQTT login, so do not
pass it on. The app's data is also part of Home Assistant's own backups.

## Using your own ser2net.yaml

For setups the forms cannot express, **Settings → ser2net.yaml → Own file**
uses your file as it is (`/addon_configs/<…>_device_proxy/ser2net.yaml`, editable in the app with
a check). It must not contain an admin section: the app adds its own. Status, events,
history, notifications and MQTT keep working, with ser2net's connection names; the forms,
"keep open" and the meter tools are not used meanwhile. Modbus and EnOcean connections are
not ser2net's and keep working; their ports must not appear in your file.

Your file is used without limits, so it can do anything ser2net can – including options such
as `connback`, which can start programs. Whoever can write the app's config folder (e.g.
over Samba) can do that as well; the forms and the import only take harmless further options.

## Proxmox

When Home Assistant runs as a VM, pass the USB adapters through to the VM. Identical
adapters without a serial number can only be told apart when they are passed through by
USB port, not by vendor and product ID. If a stick keeps disconnecting, try switching the
USB3 option of the passed-through device.

## Diagnostics

**Settings → Help and info → Download diagnostics** gets a ZIP with versions, configuration,
status, devices and the recent events. IP addresses, host names and the MQTT login are
replaced and clients only counted. Connection names and device paths stay in (a
`/dev/serial/by-id/…` path contains the adapter's serial number): take a quick look before you
attach it to a public issue.

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
| `/addon_configs/<…>_device_proxy/trace/` | recorded traces and EnOcean captures (`.jsonl`) |
| app data (in the backup) | connections, settings, history, configuration versions |
