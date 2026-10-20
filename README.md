# Ser2Net

A Home Assistant app (formerly add-on) that shares serial and USB devices over TCP with
several programs, using [ser2net 4](https://github.com/cminyard/ser2net), and manages it from
a web interface in the sidebar.

> Work in progress, not tested on Home Assistant yet. Needs Home Assistant OS or
> Supervised (apps run under the Supervisor).

Deutsch: [README.de.md](README.de.md)

## Installation

[![Add the repository to My Home Assistant](https://my.home-assistant.io/badges/supervisor_add_addon_repository.svg)](https://my.home-assistant.io/redirect/supervisor_add_addon_repository/?repository_url=https%3A%2F%2Fgithub.com%2Fbertel2020%2FHA-Ser2Net)

1. Add this repository with the button, or in Home Assistant under **Settings → Apps → App
   store → ⋮ → Repositories** with `https://github.com/bertel2020/HA-Ser2Net`.
2. Install **Ser2Net**, start it and open **Ser2Net** in the sidebar. Until prebuilt images
   are published, Home Assistant builds the app on install (gensio and ser2net included),
   which takes a few minutes the first time.

Details: [ser2net/DOCS.md](ser2net/DOCS.md).

## What it does

- **Connections in a web interface**: device from a list (stable names, adapters without a
  serial number marked), templates (smart meter SML or D0, Z-Wave stick), all important
  ser2net options, a live `ser2net.yaml` preview. Saving rebuilds only that connection; the
  others keep their clients.
- **Import** of a ser2net 4 `ser2net.yaml` (version 1 and 2) or an old ser2net 3
  `ser2net.conf`, with a preview; **export** as `ser2net.yaml`; or use your own file as it is.
- **Status**: device present, clients with address and bytes, data rate, last data, line
  errors from the driver; clients that stop reading are spotted.
- **Live data and traces** without taking a client place; recording to rotating files
  without disconnecting anyone.
- **Smart meter tools**: SML (with CRC check) and D0 decoded, baud rate detection.
- **Events and history** (30 days, drops and availability), configuration history with
  restore.
- **Notifications** in Home Assistant, optionally to a phone.
- **Entities** over MQTT discovery (with a broker such as Mosquitto): one device per
  connection with its state and a switch.
- Clients limited to private networks by default; ser2net's admin interface reachable from
  inside the app only.
- German and English, light and dark, phone width.

## Development

```bash
python -m pip install -r requirements_test.txt
ruff check .
mypy
python -m pytest
```

`tools/render_images.py` draws `icon.png` and `logo.png`. The web interface is built from
`panel-src/` (`npm ci && node build.mjs` there); `tools/dev_server.py` runs it on a desktop
with example connections.

## License

MIT. ser2net and gensio (both GPL-2.0, see their repositories) are built from their releases into the image.
