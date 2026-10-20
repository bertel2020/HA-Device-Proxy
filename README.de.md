# Ser2Net

Eine Home-Assistant-App (früher Add-on), die serielle und USB-Geräte über TCP mit mehreren
Programmen teilt – mit [ser2net 4](https://github.com/cminyard/ser2net) und einer
Weboberfläche in der Seitenleiste.

> In Arbeit, noch nicht auf Home Assistant getestet. Braucht Home Assistant OS oder
> Supervised (Apps laufen unter dem Supervisor).

English: [README.md](README.md)

## Installation

[![Repository zu My Home Assistant hinzufügen](https://my.home-assistant.io/badges/supervisor_add_addon_repository.svg)](https://my.home-assistant.io/redirect/supervisor_add_addon_repository/?repository_url=https%3A%2F%2Fgithub.com%2Fbertel2020%2FHA-Ser2Net)

1. Dieses Repository über den Button hinzufügen, oder in Home Assistant unter
   **Einstellungen → Apps → App-Store → ⋮ → Repositories** mit
   `https://github.com/bertel2020/HA-Ser2Net`.
2. **Ser2Net** installieren, starten und in der Seitenleiste **Ser2Net** öffnen. Solange es
   keine fertigen Images gibt, baut Home Assistant die App bei der Installation selbst (mit
   gensio und ser2net) – das dauert beim ersten Mal einige Minuten.

Details: [ser2net/DOCS.md](ser2net/DOCS.md).

## Was sie kann

- **Verbindungen in einer Weboberfläche**: Gerät aus einer Liste (stabile Namen, Adapter
  ohne Seriennummer markiert), Vorlagen (Zähler SML oder D0, Z-Wave-Stick), alle wichtigen
  ser2net-Optionen, Vorschau der `ser2net.yaml` beim Tippen. Speichern baut nur diese
  Verbindung neu auf; die anderen behalten ihre Clients.
- **Import** einer ser2net-4-`ser2net.yaml` (Version 1 und 2) oder einer alten
  ser2net-3-`ser2net.conf` mit Vorschau; **Export** als `ser2net.yaml`; oder die eigene Datei
  direkt verwenden.
- **Status**: Gerät vorhanden, Clients mit Adresse und Bytes, Datenrate, letzte Daten,
  Leitungsfehler vom Treiber; Clients, die nicht mehr lesen, werden erkannt.
- **Live-Daten und Mitschnitt** ohne Client-Platz; Aufzeichnung in rotierende Dateien, ohne
  jemanden zu trennen.
- **Werkzeuge für Zähler**: SML (mit CRC-Prüfung) und D0 auswerten, Baudrate erkennen.
- **Ereignisse und Historie** (30 Tage, Abbrüche und Verfügbarkeit), Konfig-Historie mit
  Wiederherstellen.
- **Benachrichtigungen** in Home Assistant, optional aufs Handy.
- **Entitäten** über MQTT-Discovery (mit einem Broker wie Mosquitto): ein Gerät je
  Verbindung mit Zustand und Schalter.
- Clients standardmäßig nur aus privaten Netzen; die Admin-Schnittstelle von ser2net ist nur
  innerhalb der App erreichbar.
- Deutsch und Englisch, hell und dunkel, Handy-tauglich.

## Entwicklung

```bash
python -m pip install -r requirements_test.txt
ruff check .
mypy
python -m pytest
```

`tools/render_images.py` zeichnet `icon.png` und `logo.png`. Die Weboberfläche wird aus
`panel-src/` gebaut (dort `npm ci && node build.mjs`); `tools/dev_server.py` startet sie auf
einem Desktop mit Beispielverbindungen.

## Lizenz

MIT. ser2net und gensio (beide GPL-2.0, siehe deren Repositories) werden aus ihren Releases ins Image gebaut.
