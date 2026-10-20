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

## Configuration

| Option | Meaning |
|---|---|
| `log_level` | `info` (default) or `debug`, which also shows the configuration handed to ser2net |
