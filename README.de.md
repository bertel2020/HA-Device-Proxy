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
2. **Ser2Net** installieren und starten.

Details: [ser2net/DOCS.md](ser2net/DOCS.md).

## Geplant

- Verbindungen in einer Weboberfläche anlegen: Gerät aus einer Liste, Vorlagen (Zähler SML
  oder D0, Z-Wave-Stick), die wichtigen ser2net-Optionen, einzeln ein- und ausschaltbar; eine
  Änderung baut nur diese Verbindung neu auf.
- Import und Export einer ser2net-4-`ser2net.yaml` oder deren direkte Verwendung.
- Status je Verbindung: Gerät vorhanden, Clients mit Adresse und Byte-Zählern,
  Leitungsfehler.
- Ereignis-Log, Historie über 30 Tage und rotierende Mitschnitte der Daten.
- Werkzeuge: Verbindung mitlesend testen, Baudrate eines Zählers erkennen, SML-Telegramme
  prüfen.
- Entitäten über MQTT und Benachrichtigungen in Home Assistant.

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
