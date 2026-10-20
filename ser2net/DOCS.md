# Ser2Net

The app makes serial and USB devices connected to Home Assistant available on TCP ports,
using [ser2net 4](https://github.com/cminyard/ser2net). Home Assistant integrations and
programs elsewhere in the network connect to these ports instead of opening the device
themselves, for example Z-Wave JS (`tcp://host:port`), ZHA or other pyserial-based
integrations (`socket://host:port`) or a smart meter reader (host and port).

Everything is set up in the app's page in the sidebar (**Ser2Net**): connections, import
and export, events and history, traces and settings.

## Several clients on one device

ser2net can let several clients use one device at the same time. Every client gets all data
from the device; what the clients send goes to the device unchanged and unordered. This
works well for devices that only send (smart meters with SML or D0, GPS). For devices that
answer requests (Z-Wave, Modbus RTU, many heat pumps) it works only as long as one client at
a time sends.

## Proxmox

When Home Assistant runs as a VM, pass USB adapters through to the VM. Two identical adapters
without a serial number (many CH340 ones) can only be told apart when they are passed through
by USB port, not by vendor and product ID. If a stick keeps disconnecting, try switching the
USB3 option of the passed-through device.

## Addresses

- **Home Assistant** (its integrations): `127.0.0.1` and the port.
- **Other apps** (e.g. Z-Wave JS UI): `172.30.32.1` and the port – they run in the Supervisor
  network, where 127.0.0.1 is the app itself.
- **Other computers**: the host's LAN address and the port.

With "only this host" a connection is reachable from Home Assistant only.

## Keeping a device open

ser2net opens a device only while a client is connected. With **keep open** the app stays
connected itself, so missing data, line errors and the test tools work without a client.
It takes one of the connection's client places.

## A client that stops reading

When one client stops reading, ser2net slows down all clients of that connection. The app
reports such a client; optionally it disconnects the connection's clients (ser2net cannot
disconnect a single one), and they connect again.

## Status, traces and line errors

- **Status per connection**: device present (and which adapter it is), clients with address,
  time and bytes, data rate, last data from the device.
- **Traces**: ser2net traces every connection into memory and the app reads along, so the live
  view and the last data work at any time. Recording to files (from the device, to the
  device or both) is switched per connection without touching ser2net: no client is
  disconnected. Files: `/addon_configs/<…>_ser2net/trace/<name>.log`, rotated by size.
- **Line errors** (frame, parity, overrun, break) come from the adapter's driver while the
  device is open; rising numbers usually mean a wrong baud rate or format. Not every driver
  counts them.
- **FTDI latency**: FTDI adapters wait 16 ms before passing data on; "low latency" sets 1 ms
  (better for Z-Wave). If the system does not let the app change it, the app says so.

## Tools for smart meters

- **Check meter data** reads the last 30 seconds of a connection as SML (binary, checks each
  telegram's CRC) or D0 (text) and shows the readings, e.g. the import total.
- **Detect baud rate** listens at each speed and format in turn and shows the best matches,
  to take over with one click. ser2net lets go of the device for this (up to about a
  minute), so the connection's clients are disconnected and connect again afterwards.
  Nothing is sent to the device: it works with meters that push their data.

## Notifications

Problems appear under Home Assistant's bell, one notification per connection and problem,
updated instead of repeated and removed once the problem is gone (can be switched off).
Optionally a notify service (e.g. the companion app on a phone) gets them too.

- Per connection: device missing, no client connected (after a few minutes), no data from
  the device for a set time (only while the device is open).
- For all connections: a client stops reading, line errors rise, ser2net keeps restarting,
  your own ser2net.yaml cannot be used.

A problem is reported only after it lasted the grace time (30 s by default), and not in the
first minute after the app started.

## Entities in Home Assistant (MQTT)

With an MQTT broker in Home Assistant (e.g. the Mosquitto add-on) the app creates one device
per connection through MQTT discovery – no setup needed, the broker comes from the
Supervisor:

| Entity | Content |
|---|---|
| Device connected | the device is plugged in |
| Clients | connected clients |
| Data rate | bytes per second from the device |
| Data from the device | bytes since ser2net started (total) |
| Last data | when the device last sent something |
| Line errors | errors counted by the driver since the start |
| Active (switch) | turns the connection on and off |

Plus one device **Ser2Net** with "ser2net running". Without a broker nothing changes; the
rest of the app works as before. Prefix (`homeassistant`), base topic (`ser2net`) and the
update interval are in the settings; the entity names follow the language of the
notifications.

## Diagnostics

**Settings → Diagnostics** downloads a ZIP with versions, configuration, status, devices and
the recent events. IP addresses are replaced and clients only counted, so it can be attached
to an issue as it is.

## Taking over an existing ser2net.yaml

A ser2net 4 file (version 1 or 2) or an old ser2net 3 `ser2net.conf` can be imported: in
the web interface with a preview, or by putting it into the app's config folder as
`import/ser2net.yaml` or `import/ser2net.conf` (`/addon_configs/<…>_ser2net/import/`); at the
next start the app takes over its connections, skips those whose port, device or name is
already used and renames the file to `….imported-<time>`. The connections can be exported as
a ser2net 4 `ser2net.yaml` again. The app log lists what could not be taken over (e.g. SSL or
other accepters than TCP, unknown serial options) and what became a further option.

Keep the ports of the old file and the clients need no change. Stop the old ser2net first:
both cannot listen on the same port.

Note: ser2net ignores the modem lines only with `local`; the app's forms set it for new
connections, an import keeps what the file says.

## Using your own ser2net.yaml

For setups the forms cannot express, the app can use your own file as it is
(`/addon_configs/<…>_ser2net/ser2net.yaml`). It must not contain an admin section: the app
adds its own. Status, events and history keep working, with ser2net's connection names.

## Configuration

Everything is set in the app's web interface; the app has no options of its own.
