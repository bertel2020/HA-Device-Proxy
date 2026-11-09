# Internes Changelog

Technische Notizen für die Entwicklung. Was Nutzer sehen, steht im öffentlichen
[device_proxy/CHANGELOG.md](device_proxy/CHANGELOG.md), das Home Assistant vor einem Update anzeigt.

- Jede Änderung kommt zuerst unter **Unreleased**, in beide Dateien; hier auch das, was Nutzer
  nicht betrifft (CI, Image, Tests, Umbauten).
- Beim Release wird in beiden Dateien aus **Unreleased** `## <Version> - <Datum>`, darüber eine neue
  leere Sektion, und die Version in `device_proxy/config.yaml` passt dazu.
- Das Repository ist öffentlich, also auch diese Datei: keine Zugangsdaten, Adressen oder Namen.

## Unreleased

- MQTT: Modell der Geräte ist `Device Proxy · <Art>` aus `entities.kind_*`, folgt also
  `notify_language`; `Kind.model` entfällt. `identifiers` bleiben, die Entity-IDs ändern sich nicht.
- MQTT: `mqttNote` in `ui.js`, ausgeblendet per `localStorage` (nur ohne Broker, je Browser).
  `#/settings/mqtt` scrollt zur Karte und öffnet ohne gefundenen Broker „Eigener Broker“.
  `mqtt_no_broker` ist Info, weil MQTT ab Werk an ist und viele keinen Broker haben.
- Modbus: `ClientInfo` zählt `cached`, `busy`, `time_avg`, `wait_avg`; `_Job.queued_at` misst die
  Wartezeit inklusive Pause zwischen Anfragen. `busy` zählt auch Timeouts, weil das Gerät dann ebenfalls
  belegt ist. Panel: `_share`, `_sharing` in `detail.js`; „ausgelastet“ heißt Wartezeit über
  (Clients × Antwortzeit), also mehr als eine Runde im Round Robin.
- Ereignisse: `_bursts` nach (Verbindung, Art, Host), `flush_bursts` räumt abgelaufene Einträge weg.
  Eine Sammelzeile bleibt wie geschrieben, `last_ts` kommt aus der Datenbank und im Panel aus den
  Wiederholungen (`app.js`). `stats` schließt offene Ausfälle bei `app_started`/`app_stopped`, weil ein
  Proxy nach dem Neustart bei `reachable is None` kein `*_back` meldet. `Store`, `Database` und
  `KnownClients` sammeln in `problems`, was vor oder unter dem EventLog passiert, `_report_problems`
  leert das. `DEFAULTS` ergänzt `version` für alte `app_started`-Zeilen. `history(contains=)` sucht in
  `params` für den Link von der Client-Karte (`api/history?contains=`). Keine Stufe `debug` mehr im
  Panel, es gab nie ein solches Ereignis. `MqttClient.on_state`, `Process.start_error`, `Captures.on_full`.
- Clients: neue Tabelle `client_sessions` und `sessions.py` (`ClientSessions`), weil die `SUMMED`-Events
  pro Verbindung ohne Adresse hochzählen. Eine Zeile je Host und Verbindung; kurze Besuche (< 120 s,
  Pause <= 60 s) laufen in einer Zeile mit `count` weiter, bleibt der Client, trennt `_settled` die Serie
  ab. Wiederholte Zeilen werden höchstens alle 300 s geschrieben. Offene Zeilen werden beim Start mit
  `unknown = 1` geschlossen, auf `updated` als Ende. Nur Hosts auf der Liste (`_on_the_list`), damit ein
  Scan die Tabelle nicht füllt. Modbus und EnOcean geben die Bytes beim Trennen mit (`_proxy_event`
  nimmt sie aus den Event-Parametern), ser2net nimmt den letzten `showport`. `GET api/clients/history`,
  Panel in `settings.js`, `#/events//<suche>` füllt die Suche der Historie. Aufräumen über `history_days`.
  `tools/dev_server.py` legt Demo-Zeilen für 127.0.0.1 an.
- Mitschnitt: `Recorder` schreibt `<name>-<YYYYmmdd-HHMMSS>.log` (Beginn), nichts wird mehr
  umbenannt. Neue Datei beim Einschalten (`TraceHub._switched_off`) oder bei voller Datei, nach einem
  App-Neustart geht es in der neuesten weiter. Alte `.log`/`.log.N` zählen nach mtime mit und werden
  nicht fortgesetzt. Aufräumen nach Anzahl behebt, dass nach gesenktem `trace_keep` Dateien liegen blieben.
  `recording_stem` ordnet Dateien der Verbindung zu. Panel: Tabelle mit `.iconbtn`, neueste oben.
- Panel: `trace.js` wählt die Verbindung per `<select>` statt über die seitlich scrollende Chip-Reihe.
- Ereignisse: `client_refused_network` (Warnung), `client_refused_exclusive` und
  `client_refused_blocked` (Info) in `modbus.py` und `enocean.py` statt reiner Log-Zeilen, alle in
  `SUMMED`, damit ein Portscan ein Eintrag bleibt. Serielle Verbindungen nicht: dort weist ser2net ab.
- Übersetzungen: `device_proxy/app/device_proxy/locales/<code>.json` je Sprache statt der Tabellen in
  `i18n.js`, `controller.py`, `ha_mqtt.py` und `notify.py`. Das Panel bekommt seine Abschnitte beim
  Build (`__LOCALES__`, Fehlendes auf Englisch), die App liest sie über `i18n.py`. Sprachauswahl,
  Browser-Erkennung und `notify_language` richten sich nach den vorhandenen Dateien. `build.mjs` und
  `tests/test_locales.py` prüfen Schlüssel und Platzhalter; `de` und `en` müssen vollständig sein.
- Fehlermeldungen: Die deutschen Muster stehen als `errors` in `de.json`, kompiliert beim ersten
  Gebrauch. Die Meldung zu `notify_language` lautet jetzt „one of de, en“.

## 1.5.1 - 2026-11-08

- Panel: Die Kachel in `connections.js` zeigt nur noch `clientName`, `clientLabel` mit Stift bleibt
  in `detail.js`; der Button brach in der schmalen Kachel in eine eigene Zeile um.
- READMEs: Voraussetzung Home Assistant OS im Schnellstart; sie war mit dem Teststand-Hinweis
  verschwunden. Supervised wird nicht mehr genannt, Home Assistant unterstützt es seit 2025.12 nicht mehr.
- CI: `publish` läuft auch, wenn ein anderer Job fehlschlägt, damit zu einer Version immer ein Image
  entsteht; der Lauf bleibt dann rot.
- Test `test_a_taken_status_port_is_tried_again` hängt nicht mehr von der Laufzeit des Rechners ab
  (`time.monotonic` zählt ab dem Start, auf einem frischen CI-Runner blieb er unter 30 s).

## 1.5.0 - 2026-11-08

### Neue Felder

Alle haben einen Standardwert, gespeicherte Konfigurationen laden ohne Migration, `SCHEMA` bleibt 1.
Keines startet einen Proxy neu (`restart_key` in `modbus.py` und `enocean.py`).

| Feld | Wo | Inhalt |
| --- | --- | --- |
| `power_switch` | `Connection` | Entität `switch.*` für den Stromzyklus |
| `register_entities`, `entity_seconds` | `Connection` | Zeilen für `modbus_entities.py`, 5 bis 3600 s |
| `write_rules` | `Connection` | Register je Client, ersetzt für ihn `write_registers` |
| `fallback_probe_s`, `fallback_misses`, `fallback_stable_s` | `Connection` | Ersatz-Gateway, 3 bis 300 s, 1 bis 20, 5 bis 3600 s; stabil mindestens so lang wie das Intervall |
| `sender_names` | `Settings` | EnOcean-Sender-ID und Name je Zeile, in der Diagnose `***` |

`TEMPLATES` hat dazu `zigbee` und `MODBUS_PROFILES` (`mb_*`, Werte in `panel-src/src/modbus.js`).

### Neue API und MQTT

- `GET api/ha/switches`, `POST api/connections/<id>/restart` nimmt auch `power`.
- `PUT api/enocean/sender-names` speichert alle Namen als eine Konfig-Version.
- `GET api/tools/<id>/enocean/senders.csv`, mit BOM und gegen Formeln in Tabellen abgesichert.
- `POST api/clients/{name,block,unblock,forget}`; Ereignisse `client_blocked`, `client_unblocked`;
  `state` hat `known_clients`, `blocked_clients`, `new_clients_full`.
- MQTT: Button `power_cycle` nur mit Schalter, Sensoren `reg_<unit>_<funktion>_<adresse>`.
- Ereignisse `power_cycled` und `power_cycle_failed`.

### Umbauten

- Neues Modul `modbus_entities.py`; die Dekodierung entspricht `decode` in `panel-src/src/modbus.js`,
  `DEVICE_CLASSES` muss in beiden gleich sein (Test prüft das).
- `ModbusProxy` und `ListenProxy` haben einen `_entity_loop`. Die Lesezugriffe laufen über `ask`
  und zählen nicht als Client-Anfragen; `ListenProxy` liest aus dem Gehörten.
- `MAIN_PROBE`, `FALLBACK_MISSES` und `FALLBACK_STABLE` in `enocean.py` sind jetzt Felder der
  Verbindung; `FALLBACK_PROBE` (Ersatz prüfen) und `PROBE_TIMEOUT` bleiben fest.
- `_serve` nutzt für Register jetzt `write_refusal`, die Prüfung steht nicht mehr doppelt da.
- `_auto` im Controller hat ein viertes Feld: Stromzyklus schon gemacht.
- `_power_cycle` schaltet auch beim Abbruch (App stoppt) wieder ein. In `_restart_proxy` hält es
  `self._lock` bis zu etwa 35 s, solange blockieren Speichervorgänge.
- Clients: `bf25b3d` (Sperren, bei ser2net aus den erlaubten Netzen herausgeschnitten), `6a4941d`
  (Namen in der Liste, „zuletzt gesehen“ in `known_clients.json`). Danach `08ed776` und `a3938c0`:
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
  MQTT-Discovery der Register, Zigbee-Vorlage an einem Stick, die Sperre mit echtem ser2net (die
  zerlegten `remaddr`-Listen sind nur gegen den Quelltext von gensio geprüft), einstellbare Zeiten
  des Ersatz-Gateways an echten Gateways.
- Die Werte der `mb_*`-Profile sind nicht mit den Herstellerhandbüchern abgeglichen, am unsichersten
  Huawei und Sungrow.
- `tests/HARDWARE.md` hat noch keine Fälle für USB-Reset, Stromzyklus, serielle Bridges, MQTT.
- Screenshots zeigen noch Version 1.2.0.
