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
2. Install **Ser2Net** and start it.

Details: [ser2net/DOCS.md](ser2net/DOCS.md).

## Planned

- Connections set up in a web interface: device from a list, templates (smart meter SML or
  D0, Z-Wave stick), the important ser2net options, switched on and off one by one; a change
  rebuilds only that connection.
- Import and export of a ser2net 4 `ser2net.yaml`, or using one as it is.
- Status per connection: device present, clients with address and byte counts, line errors.
- Event log, a 30-day history and traces of the data, rotated.
- Tools: test a connection by reading along, detect the baud rate of a smart meter, check
  SML telegrams.
- Entities over MQTT and notifications in Home Assistant.

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
