# Internes Changelog

Technische Notizen für die Entwicklung. Was Nutzer sehen, steht im öffentlichen
[device_proxy/CHANGELOG.md](device_proxy/CHANGELOG.md), das Home Assistant vor einem Update anzeigt.

- Jede Änderung kommt zuerst unter **Unreleased**, in beide Dateien; hier auch das, was Nutzer
  nicht betrifft (CI, Image, Tests, Umbauten).
- Beim Release wird in beiden Dateien aus **Unreleased** `## <Version> - <Datum>`, darüber eine neue
  leere Sektion, und die Version in `device_proxy/config.yaml` passt dazu.
- Das Repository ist öffentlich, also auch diese Datei: keine Zugangsdaten, Adressen oder Namen.

## Unreleased

### Neue Felder

Alle haben einen Standardwert, gespeicherte Konfigurationen laden ohne Migration, `SCHEMA` bleibt 1.
Keines startet einen Proxy neu (`restart_key` in `modbus.py` und `enocean.py`).

| Feld | Wo | Inhalt |
| --- | --- | --- |
| `power_switch` | `Connection` | Entität `switch.*` für den Stromzyklus |
| `register_entities`, `entity_seconds` | `Connection` | Zeilen für `modbus_entities.py`, 5 bis 3600 s |
| `write_rules` | `Connection` | Register je Client, ersetzt für ihn `write_registers` |
| `sender_names` | `Settings` | EnOcean-Sender-ID und Name je Zeile, in der Diagnose `***` |

`TEMPLATES` hat dazu `zigbee` und `MODBUS_PROFILES` (`mb_*`, Werte in `panel-src/src/modbus.js`).

### Neue API und MQTT

- `GET api/ha/switches`, `POST api/connections/<id>/restart` nimmt auch `power`.
- `PUT api/enocean/sender-names` speichert alle Namen als eine Konfig-Version.
- `GET api/tools/<id>/enocean/senders.csv`, mit BOM und gegen Formeln in Tabellen abgesichert.
- MQTT: Button `power_cycle` nur mit Schalter, Sensoren `reg_<unit>_<funktion>_<adresse>`.
- Ereignisse `power_cycled` und `power_cycle_failed`.

### Umbauten

- Neues Modul `modbus_entities.py`; die Dekodierung entspricht `decode` in `panel-src/src/modbus.js`,
  `DEVICE_CLASSES` muss in beiden gleich sein (Test prüft das).
- `ModbusProxy` und `ListenProxy` haben einen `_entity_loop`. Die Lesezugriffe laufen über `ask`
  und zählen nicht als Client-Anfragen; `ListenProxy` liest aus dem Gehörten.
- `_serve` nutzt für Register jetzt `write_refusal`, die Prüfung steht nicht mehr doppelt da.
- `_auto` im Controller hat ein viertes Feld: Stromzyklus schon gemacht.
- `_power_cycle` schaltet auch beim Abbruch (App stoppt) wieder ein. In `_restart_proxy` hält es
  `self._lock` bis zu etwa 35 s, solange blockieren Speichervorgänge.
- Clients: `bf25b3d` (Sperren, bei ser2net aus den erlaubten Netzen herausgeschnitten), `6a4941d`
  (Namen in der Liste, „zuletzt gesehen“ in `known_clients.json`). Danach:
  - `store.QUIET_SETTINGS` (`client_names`, `notify_new_clients`): keine Konfig-Version, kein
    `last_change`; `restore` einer Version behält diese Werte.
  - Sperren in eigener Datei `blocked_clients.json`, beide Dateien mit `fsync`; eine defekte
    Sperrdatei wird als `.invalid-<ts>` beiseitegelegt.
  - `new` höchstens `MAX_NEW` (50), ab `NOTIFY_EACH_CLIENT` (5) eine Sammelmeldung `new_clients`.
  - Proxies fragen `refuse(host, name)` statt `blocked`; Versuche zählt `KnownClients.refused` im
    Speicher, Protokollzeile höchstens alle `LOG_SECONDS`. ser2net meldet Abweisungen nicht.
  - `POST api/clients/forget` entfernt Eintrag und Namen.
  - Karte Clients: eine Liste (`_clientList`, `_clientRow` in `settings.js`), `client_names` ist
    kein Textfeld mehr.

### Repository und CI

- Image: Downloads von gensio und ser2net bis zu 10 Versuche im Abstand von 30 s (`123116a`).
- `.github/ISSUE_TEMPLATE/` und `SECURITY.md`; private Sicherheitsmeldungen im Repo eingeschaltet.
- Hinweis zum Teststand aus den READMEs und `tests/HARDWARE.md` entfernt. Damit steht auch nicht
  mehr im README, dass Home Assistant OS oder Supervised nötig ist.

### Offen

- Nicht mit echtem Home Assistant oder echter Hardware getestet: Stromzyklus über die Core-API,
  MQTT-Discovery der Register, Zigbee-Vorlage an einem Stick.
- Die Werte der `mb_*`-Profile sind nicht mit den Herstellerhandbüchern abgeglichen, am unsichersten
  Huawei und Sungrow.
- `tests/HARDWARE.md` hat noch keine Fälle für USB-Reset, Stromzyklus, serielle Bridges, MQTT.
- Screenshots zeigen noch Version 1.2.0.
