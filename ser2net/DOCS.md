# Ser2Net

The app makes serial and USB devices connected to Home Assistant available on TCP ports,
using [ser2net 4](https://github.com/cminyard/ser2net). Home Assistant integrations and
programs elsewhere in the network connect to these ports instead of opening the device
themselves, for example Z-Wave JS (`tcp://host:port`), ZHA or other pyserial-based
integrations (`socket://host:port`) or a smart meter reader (host and port).

> Version 0.1.0 is the foundation: ser2net runs, but connections cannot be set up yet. The
> web interface for connections, import of an existing `ser2net.yaml`, logs, history and
> traces follows in the next versions.

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
