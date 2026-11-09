# Device Proxy

*[Deutsche Fassung](https://github.com/bertel2020/HA-Device-Proxy/blob/main/device_proxy/DOCS.de.md)*

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
   template (smart meter SML or D0, Z-Wave or Zigbee stick, generic), the device from the list and a
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

**A serial bridge in the network**: under **Device → Where the data comes from → Network (TCP)**
a connection takes its data from a serial bridge instead of a device of this host, e.g. an
ESPHome stream server, a Tasmota reading head or a USR-TCP232. Such bridges usually accept one
client only; the app connects to the bridge (only while it has clients itself) and shares it.
Baud rate and format are set on the bridge; the tools that need the device itself (baud rate
detection, line errors, FTDI latency) are not offered.

**An adapter on another port**: the app remembers which adapter each connection had (vendor,
product and serial number). When the device is missing and a free adapter of the same kind is
plugged in (on another USB port, in the VM under another number), the connection's page and
card say so, with a button to take it over; with several such adapters you pick the right
one. An adapter with a serial number is only offered when the serial number matches.

**Advanced** holds ser2net's options, all optional: flow control (RTS/CTS, XON/XOFF), modem
lines (`local`), DTR/RTS on open, RS485, timeout, retry time, allowed clients (`remaddr`),
banner, open and close strings, `nodelay`, a bind address, FTDI latency and further ser2net
options as `name: value` lines. The form shows the resulting `ser2net.yaml` part while you
type.

### Who may connect

**Settings → Network** applies to all connections without their own bind address or
`remaddr`:

- **Home Assistant only** – 127.0.0.1, this host only.
- **Home Assistant and apps** – also the other apps (e.g. Z-Wave JS UI), 127.0.0.0/8,
  172.30.32.0/23 and fd0c:ac1e:2100::/48 (IPv6), but nothing from the LAN.
- **Home network** (default) – Home Assistant, its apps and the networks listed under
  **Allowed networks**. "My network" (the host's network, read from the Supervisor) is
  predefined; add further networks such as `192.168.80.0/24` or use the private ranges. An
  empty list lets only Home Assistant and the apps in. Installations from before this list
  existed keep the private ranges (10/8, 172.16/12, 192.168/16).
- **Anyone** – no limit. ser2net has no login: whoever reaches the port can read and control
  the device.

A **Z-Wave or Zigbee stick** starts with a rule of its own, because it takes commands without a login:
Home Assistant and the apps only (`127.0.0.1, 172.30.32.0/23` under **Advanced → Allowed
clients**). Empty the field to let the network setting decide.

The **Zigbee** template allows one client, because a Zigbee network has one program in charge of
the coordinator. ZHA connects with `socket://host:port`, Zigbee2MQTT with `tcp://host:port`. It
sets 115200 baud, which fits most sticks; a stick that needs hardware flow control gets RTS/CTS
under **Advanced**.

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


**Device profiles** fill in the port and the timing for devices of a vendor (SolarEdge, Huawei
SUN2000, Fronius, SMA, Kostal Plenticore, Sungrow, Victron GX). They are starting values and stay
editable; the unit id is set in the client, and the profile shows the usual one. When **Scan the
bus** recognizes a vendor, it offers its timing; the port stays as it is there.

**Connection to the device**

| Kind | For | Settings |
|---|---|---|
| Modbus TCP | a device in the network | address and port (502) |
| Modbus RTU (serial) | an RS485 adapter on this host | device, baud rate and format |
| RTU over TCP | an RS485-to-Ethernet converter in transparent mode | address and port |
| Listen on RS485 | a bus that has a master already | device, baud rate and format, how long values stay valid |

With Modbus RTU the app opens the adapter itself (not through ser2net) and keeps the pause
of 3.5 characters between frames that RTU needs. Unit 0 is a broadcast: it is sent, nobody
answers. RTU has no transaction ids, so an answer must fit its request (unit, function,
byte count, the echo of a write), and after a timeout or a broken answer the line gets
half a second for late bytes before the next request – a late answer never reaches the
wrong client.

**Listen on RS485** is for a bus where a master asks already, e.g. an inverter polling its
energy meter or a heat pump's controller its modules: a second master would disturb them.
The app only listens, it never sends on the bus. It tells the frames apart by their CRC (the
pauses between frames get lost behind USB adapters), pairs each read (functions 3 and 4) with
its answer and keeps the registers, also those the master writes (6, 16). Modbus TCP clients
read them: a read is answered when every register asked for was heard within "Values valid
for" (60 s by default), else with exception 0B, as from a gateway whose device is away. Only
what the master reads can be read; writing is refused with exception 01. The status card
shows the frames heard and which registers of which units are known.

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
allowed clients. A connection created without this field (over the API, by a script) starts
with "only these" too; one saved before the field existed keeps "all clients". The
connection's page shows who may really write: every client that may connect, the listed ones,
nobody when "only these" lists nobody, the registers it is limited to and, for units of other
connections, their rule as well.

**Registers that may be written** (with write access "All" or "Listed"): addresses and ranges,
e.g. `40100-40120 47000`. A write that changes anything outside, or whose addresses cannot be
told (a vendor's own function), is refused with exception 02, so e.g. evcc may set the
charging registers of an inverter but nothing else. Coils and registers count by their
address alike. The card **Writes** on the connection's page lists the clients' last 200
writes: when, who, unit, function, address, values and whether they were written, refused
by the device, not allowed or outside the allowed registers.

**Registers per client**: one line per client under the registers, an address or network and then
its registers, `*` for any or `none` for no register, e.g. `192.168.1.20 40100-40120` lets evcc set
the charging registers while `127.0.0.1 *` leaves Home Assistant free. The first line that fits
applies instead of **Registers that may be written**. A line does not let anyone write: who may
write at all is still decided by the write access. **Check access** names the line that applies.

**Units of other connections** (under **Advanced**): one port for several devices, as many
energy managers and evcc expect a single Modbus gateway. Each line names a unit asked here,
another Modbus connection of the app and the unit there, e.g. unit 2 → "Meter" (unit 1). A
client asking unit 2 is answered by that connection's device, in turn with its own clients
and with its cache; a write must be allowed by both connections (write access and registers).
Only one step: a connection whose units are routed elsewhere routes none of its own. While
the other connection is off, the client gets exception 0A.

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
After 50 requests the card gives **tips** from these numbers: a longer timeout when answers
come close to it, a shorter one when the device always answers fast (so an outage shows
sooner), a cache when several clients ask, and what a long queue or many exceptions mean.
They are suggestions, not settings: check them against the device's documentation.
The live view and the recordings show each request and answer as hex with unit, function,
register and count (e.g. `unit 1 · FC03 read holding registers · @40000 ×4`).

**Tools** on a Modbus connection's details:

- **Read registers**: unit, function (holding or input registers, coils, discrete inputs),
  address (from 0, as in the frame) and count; the values as unsigned, signed and hex. The
  request waits its turn with the clients' and does not use the cache. **Decode values** reads
  the registers as 16, 32 or 64 bit integers, floats or text, with the register and byte order
  ("swap") and a factor as in Home Assistant's Modbus integration, and gives the matching
  sensor to copy into `configuration.yaml`.
- **Write registers**: function 5 or 15 (coils) or 6 or 16 (registers), address and value(s),
  several separated by commas. A dialog asks first; afterwards the value is read back and
  compared. Each write is an event in the log. The tool stays locked when the connection's
  write access is "Nobody".
- **Scan the bus**: which unit ids answer (it reads register 0, an exception counts as an
  answer too). The units found can be taken over into "read registers". Afterwards each unit
  found is asked who it is: its device identification (function 43) and, for inverters and
  meters, the SunSpec common model at register 40000, 0 or 50000. Vendor, model and version
  are shown, with a fitting integration where one is known.

- **Check access**: a client's IP address, unit, function and register; the answer says
  whether it may connect, read and write and which rule decides – the bind address, the
  connection's allowed clients, the network setting, the write access, the registers, or a
  unit sent on to another connection. Nothing is sent; a client on this host counts as
  127.0.0.1. It checks the saved rules, the same the proxy applies.

Tool requests are not counted as the clients'. Only "write registers" changes the device.

**Registers as entities**: for a device without an integration the app can read registers itself
and offer them as sensors over MQTT, without any YAML. Under **Read registers → Decode values**
find the right type, swap and scale, give the value a name, a unit and a device class and press
**Add as an entity**. The list is under **Advanced → Registers as entities** with one line per
entity (`unit function address type swap scale unit class name`, e.g.
`1 3 40083 int16 none 0.1 W power AC power`, `-` for no unit or class), at most 50, read every
30 seconds by default. Each read goes to the device in turn with the clients and is not counted
as theirs; on a connection that listens on RS485 the values come from what was heard, and nothing
is sent. While the device is not reachable the entities are unknown. A unit that does not fit the
device class is refused by Home Assistant; it then says so in its log.

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

**Templates** set protocol, model, baud rate and kind of connection; everything stays
changeable:

| Template | Protocol | Model | Connection |
|---|---|---|---|
| FAM-USB | ESP2 | `fam_usb` | USB, 9600 baud |
| FAM14, FGW14-USB | ESP2 | `fam14`, `fgw14_usb` | USB, 57600 baud |
| USB300 / TCM310 | ESP3 | `esp3` | USB, 57600 baud |
| PioTek MGW-ETH | ESP3 | `mgw_eth` | TCP, port 5100 (one session only: share it through this app) |
| Symcon LAN | ESP3 | `symcon_lan` | TCP, port 5000 |

**Model**: the gateway's model goes to the EnOcean Eltako integration with the discovery
(Eltako FAM-USB, FGW14-USB or FAM14, PioTek MGW-ETH, Symcon LAN, or another ESP2 or ESP3
gateway). The app cannot tell it by itself, as it only passes bytes on: the template sets it,
and the field **Model** under "Gateway" changes it. It must fit the protocol: ESP2 for
`fam_usb`, `fgw14_usb`, `fam14` and `esp2`, ESP3 for `mgw_eth`, `symcon_lan` and `esp3`; the
field offers only those of the chosen protocol. Left empty, the discovery goes without it.
Gateways saved before version 1.0.0 take the model of their template when it fits.

**Who may connect**: new gateways follow the network setting, like the other kinds, so a PC
with eo_man or PCT14 in the home network can connect at once. To limit one gateway, enter
addresses or networks under **Allowed clients**, or press "Only Home Assistant and apps"
(`127.0.0.1, 172.30.32.0/23`). Home Assistant reaches a discovered gateway by the app's host
name, which is the host's LAN address, so it comes from that address and not from 127.0.0.1;
a connection from the host to its own address counts as 127.0.0.1 all the same (also for the
status port and the Modbus proxy).

**Replay**: the EnOcean Eltako integration asks for it (`EOPX REPLAY TS`) after every
connect. Radio telegrams that arrive while no such program is connected, e.g. during a Home
Assistant restart, are kept (1000 telegrams, 15 minutes by default) and handed over with their
reception time. **Keep the buffer on disk** keeps them over a restart of this app too
(`/data/replay`).

**Discovery and status**: the app announces its active gateways to the EnOcean Eltako
integration with name, port, protocol and model, e.g. `{"name": "PioTek MGW-ETH", "port": 9100,
"protocol": "esp3", "model": "mgw_eth"}`; the integration offers each one for setup with replay
switched on. A read-only status
(port 9199, Home Assistant and the apps only) feeds the integration's gateway cards. Both are
under **Settings → EnOcean**, which also says when the status port could not be opened. If the
integration shows "proxy status not reachable", check it in the terminal app with
`curl http://<host name of this app>:9199/api/status`; from the LAN the connection is reset on
purpose.

**The detail page** shows what is wrong in plain words (gateway away, port taken, air time,
frames dropped (also because of a lock), programs refused or disconnected, no program connected), every
frame live with its kind and sender (search, direction, a click on an ID shows only that
sender, copy, take over into "send"), the air time of the last hour against the 1 % limit
(a notification at 80 %), counters and the replay buffer, and the base ID once the gateway
told it. Tools:

- **Senders** (a card of its own): every sender ID heard since the start with its kind (RPS,
  1BS, 4BS, VLD), how many telegrams, when last, through how many repeaters and, with an ESP3
  gateway, the reception in dBm (above −75 good, below −88 weak); with a fallback also which
  gateway heard it. "New" marks senders first heard more than 5 minutes after the start, so a
  new switch's ID is found by pressing it once; "own" marks the gateway's base ID range.
  With **Edit names** each sender gets a name, for all gateways, saved together in one step;
  **Download as CSV** gives the list as a file. Diagnostics leave the names out.
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
  the frames of the other programs (Home Assistant too) are dropped and not sent later, and
  the app's own tools do not send meanwhile. The fallback check pauses then too, and that
  program's frames go to this gateway only, never through the fallback gateway.

### Fallback gateway

A second gateway can stand in when one fails. Both must report the **same base ID**: the
actuators are taught in to the sender IDs of the first gateway (base ID + 0 … 127), and only a
gateway with that base ID sends from them. The app does not set a base ID for this; it reads
both and compares them. Both gateways speak the same protocol.

1. Set the second gateway up as a normal EnOcean connection and check it there (gateway test,
   base ID, live frames).
2. In the first gateway's form, under **Fallback gateway**, pick it at "When it fails, take over
   with". The app shows whether the base IDs match and asks before it saves, because the second
   gateway changes its role.

While a connection is another gateway's fallback, its port is closed (connected clients are
disconnected), it is not offered to the EnOcean Eltako integration, and its own replay rests.
It stays connected and reads its base ID every minute; its page, live frames, gateway test and
air time stay. Picking "No fallback" again makes it a normal gateway with its own port.

**Switching**: the first gateway reads its base ID every 10 s. When its connection is gone, or
three reads stay unanswered ("gone or silent"; "gone only" waits for the connection to drop),
its programs go on through the fallback: they stay connected to the same port, their frames are
sent by the fallback, its answers and radio telegrams come back to them. Commands unanswered at
that moment are not repeated (the event says how many); the integration decides. The fallback
is only used when it is connected, has answered lately and reports the same base ID; the app
keeps the first gateway's base ID, so this is checked while it is away too. Back to the first
gateway: automatically once it has run steadily for 60 s and nothing waits at the fallback, or
by hand only. If you switched to the fallback yourself, it goes back by hand only. If the
fallback fails, it goes back to the first gateway at once, even if that one is not running yet;
when the fallback returns, it stands in again. The three times (check every 10 s, 3 failed
reads, 60 s steady) are set per gateway in the form under **Fallback gateway → Change**. The card
**Gateways** on the first gateway's page shows both, which one is in use,
and switches by hand.

**Hear both gateways** (optional): the programs get the radio telegrams of both gateways, for
more range. A telegram that the other gateway brought within 200 ms is dropped (compared
without signal strength and repeater count), and so is what the gateway at rest hears from the
own sender IDs: that is the other gateway's own sending. The card shows what came first through
which gateway.

**Fallback becomes the main gateway** (the first gateway broke): on the card **Gateways**. The
connection of the first gateway stays with its name, port, allowed clients, replay, discovery
and history, so the integration notices nothing; only the hardware (template, model, kind
of connection, device or host and port, baud rate) is swapped between the two connections. The
old hardware is then switched off (default), kept as fallback, or its connection deleted. Both
connections restart, and the replay bridges the short gap. The configuration history can
undo it.

## Maintenance: one computer alone

On a connection's page, **Maintenance** lets one computer (its IP address; the hosts of the
clients connected are offered) use the connection alone for 15 minutes to 4 hours, e.g. for
the vendor's service program, PCT14 or a firmware update over RFC2217. All other clients,
Home Assistant too, are disconnected and refused meanwhile; a bar on the page says how long it
lasts and ends it early. When the time is up, and at the latest when the app restarts, every
allowed client may connect again. For ser2net's connections the clients reconnect once at the
start and once at the end.

## Restart and USB reset

When a device hangs, **Restart** on a connection's page restarts it: the device is closed and
opened again (for Modbus and EnOcean the proxy), all clients are disconnected and connect again.
For a USB adapter of this host, **USB reset** also resets the adapter, as if it were unplugged
and plugged in again, only without cutting the power. That often helps when the adapter's chip
hangs (FTDI, CP210x, CH340). A hung firmware in the device itself sometimes still needs a power
cycle, e.g. with a switchable socket on the USB hub. After the reset the adapter may get another
tty number; with the path under `/dev/serial/by-id` the connection finds it again.

Automatically: in a serial connection's form, **Then** sets what happens after the minutes
without data ("Warn when no data for"): only warn, restart the connection, or USB reset and
restart. It only counts while the device is open (a client connected or **Keep the device
open**). If there is still no data after three restarts in a row, only the warning stays until
data comes again. Every restart is in the history.

**Power cycle**: when a restart and a USB reset are not enough, a switch in Home Assistant can
cut the power, e.g. a switchable socket on the USB hub. Enter it under **Power** in the
connection's form (for every kind of connection). A button **Power cycle** then appears next to
**Restart**: the device is closed, the switch goes off for 5 seconds and on again, and the
device is opened again. With automatic restarts set up, one power cycle follows the three
restarts that did not help. Choose a switch that nothing else depends on, and never the one that
feeds Home Assistant itself.

Both are also buttons in Home Assistant (see below).

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

**Meter readings as entities** (in the form under **Advanced**, on by default with the eHZ
templates): with MQTT the connection's device in Home Assistant gets "Meter reading import"
and "Meter reading export" in kWh and "Power" in W, ready for the Energy dashboard. The app
reads them from the data the meter sends anyway (SML only from telegrams with a correct CRC),
so no extra integration and no client place is needed; but ser2net opens the device only
while a client is connected, so with no other client switch on **Keep the device open**.

## Events and history

**Events** shows the live log (filter by connection, level and text) and the history:
drops and availability per connection over 30 days and a timeline. Repeating events, such as
a stick that keeps dropping out, are summed up. With Modbus and EnOcean, refused clients appear
too: all places taken, network not allowed, maintenance or blocked. With serial connections
ser2net decides by itself and does not tell the app. The history is kept 30 days by default.
**Settings → Configuration history** keeps the last 25 configurations with their
differences; each one can be restored. Client names and the notification about new computers
make no version and stay as they are when a version is restored.

**Before saving** the connection form names the running connections that saving sets up again
or stops and how many clients have to connect again ("only this connection" is not always
so: a fallback or the network setting touch others). The same goes for the questions before a
change of the network setting or the home networks, an import, and restoring a version or a
backup. **After saving**: when a connection that worked before stops working (device not
reachable, port taken), the connections page and the connection's page say so, with **Restore
the version before** – the configuration as it was before the change, in one step.

## Clients

**Settings → Clients** shows new, known and blocked computers in one list. The dot in front gives
the state: green connected, grey not connected, yellow new, red blocked. A click on a known
computer opens the field for the name, saved when you leave it; in the details of a connection the
pencil next to a client does the same. The name shows next to the address in the lists of clients and
in the events. This host is called Home Assistant by itself, addresses in the Supervisor network
App; a name of your own goes first.

The ports have no login, so a computer that connects for the first time is reported: an event and,
unless switched off there, a notification in Home Assistant. It stays at the top of the list as
**New** until you mark it as **Known** or give it a name. The list holds at most 50 new computers,
from six on one notification covers them. Home Assistant, its apps and this host always count as
known and are in the list only while connected; after the first start (or the update that brought
this) the app takes the clients of the first ten minutes as known without a word.

**Block** keeps a computer away from every connection until you allow it again with **Release**; it
works from the list or with **Block an IP address**. It is disconnected at once. ser2net cannot drop
a single client, so on serial connections that would let it in, all clients reconnect once when you
block or release it. A block applies to the IP address: a device that gets a new one is no longer
blocked. Home Assistant, its apps and this host cannot be blocked. Ports of an own `ser2net.yaml`
are not covered. With Modbus and EnOcean the line shows how often the computer was refused since
the start; ser2net does not report that.

**Remove** takes a computer that is not connected off the list, with its name; if it connects again
it counts as new. Diagnostics leave out the names and addresses of clients.

## Notifications

Problems appear under Home Assistant's bell: one notification per connection and problem,
updated instead of repeated, and removed when the problem is gone (can be switched off).
Optionally a notify service (e.g. the companion app on a phone) gets them too.

- Per connection (in the connection's form): device missing (for Modbus also: not
  reachable), no client connected (after a few minutes), no data from the device for a set
  time (serial devices, only while the device is open). A Modbus port that cannot be opened
  is always reported. An EnOcean gateway: not reachable, and air time at 80 % of the limit;
  with a fallback: running on the fallback (instead of "not reachable", with the reason), and
  the fallback not ready (switched off, not connected, other base ID, not answering).
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
| Disconnect clients (button) | closes the connections of all clients; they may connect again |
| Restart connection (button) | closes the device and opens it again, the clients connect again |
| USB reset (button) | only with a device of this host: resets the USB adapter and restarts |
| Power cycle (button) | only with a power switch set: cuts the power for 5 seconds and restarts |

A Modbus connection has: its registers as entities (see above), device reachable, clients, requests, unanswered requests, answer
time, the switch and the buttons. An EnOcean gateway has: gateway reachable, clients, telegrams
from the gateway, air time (share of the 1 % limit), the switch and the buttons; with a fallback
also "Fallback gateway active" (a problem while it stands in), "Active gateway" (the name of the
one in use), "Fallback gateway ready" and the buttons "Switch to the fallback gateway" and "Back
to its own gateway" (as on the card **Gateways**). "Gateway reachable" stays the gateway's own
hardware.

The buttons are meant for automations, e.g. restarting a stick that hangs.
**Disconnect clients** is also on a connection's page, next to its clients.

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
pass it on. Client names are in it, the list of known and blocked computers is not. The app's data is also part of Home Assistant's own backups, except the recorded
traces and EnOcean captures (the folder `trace/`), which can be large.

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

## Test cases for issues

**As a test case** in a connection's live data downloads its last few hundred frames as a
file to attach to an issue, so an odd inverter or gateway can be looked at without the
hardware. Client addresses are left out; EnOcean sender IDs and the base ID are replaced by
made-up ones (the checksums computed again). Modbus registers stay as they are, and a smart
meter's telegrams contain the meter's number: look before you share. The development server
plays a test case back as a device: `python tools/dev_server.py 8399 --replay file.json`.

## Diagnostics

**Settings → Help and info → Download diagnostics** gets a ZIP with versions, configuration,
status, devices and the recent events. IP addresses, host names and the MQTT login are
replaced and clients only counted. Connection names and device paths stay in (a
`/dev/serial/by-id/…` path contains the adapter's serial number): take a quick look before you
attach it to a public issue.

## When something does not work

| What you see | What to check |
|---|---|
| Device missing | Is the adapter passed through to the VM? Does it show in the device list? Plugged into another port: the page offers to take it over. |
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
| `/addon_configs/<…>_device_proxy/trace/` | recorded traces and EnOcean captures (`.jsonl`), not in Home Assistant's backups |
| app data (in the backup) | connections, settings, history, configuration versions, known and blocked clients |
