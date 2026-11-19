# Internes Changelog

Technische Notizen für die Entwicklung. Was Nutzer sehen, steht im öffentlichen Changelog:
englisch in [device_proxy/CHANGELOG.md](device_proxy/CHANGELOG.md) (Home Assistant zeigt es vor
einem Update, CI nimmt daraus die Release-Notes), deutsch in
[device_proxy/CHANGELOG.de.md](device_proxy/CHANGELOG.de.md).

- Jede Änderung kommt zuerst unter **Unreleased**, in alle drei Dateien; hier auch das, was Nutzer
  nicht betrifft (CI, Image, Tests, Umbauten).
- Öffentlich gruppiert nach `### Neu` / `### Geändert` / `### Behoben` (englisch `New` / `Changed`
  / `Fixed`), bei Bedarf zuerst `### Achtung beim Update` (`Breaking / before updating`); jeder
  Eintrag `- **Bereich:** Text`, eine Zeile, Unterpunkte eingerückt.
- Beim Release wird in allen drei Dateien aus **Unreleased** `## <Version> - <Datum>`, und die
  Version in `device_proxy/config.yaml` passt dazu. Eine neue leere Sektion kommt nur hier darüber;
  in den öffentlichen Dateien entsteht **Unreleased** erst mit dem ersten Eintrag, denn Home
  Assistant zeigt das Changelog vor dem Update und eine leere Überschrift sähe dort verloren aus.
- Das Repository ist öffentlich, also auch diese Datei: keine Zugangsdaten, Adressen oder Namen.

## Unreleased

- Karten-Tabellen über Container-Abfragen statt `@media`: `.scroll` hat `container-type: inline-size`; `table.cards` wird unter 540 px Platz zu Karten, `table.cards.wide` (Modbus-Clients, 1-Wire-Geräte, EnOcean-Sender, Mitschnitt-Dateien) unter 780 px. Die Regeln entstehen einmal in `CARDS(sel)` (`styles.js`, `unsafeCSS`). Geprüft bei 375/640/820/1440 px: nichts scrollt seitlich, am Desktop Tabellen.
- Scroll-Spy der Einstellungen: Schwelle mindestens ein Drittel der Fensterhöhe; `_goto(id)` markiert den angetippten Abschnitt sofort und hält ihn bis `scrollend` (Rückfall nach 2 s).
- Verbindungsliste (`connections.js`): Gateway mit sichtbarem Ersatz (`paired`) zuerst innerhalb der Art, Karte mit `.pair-start` (`grid-column-start: 1`), Ersatz direkt danach; so bleibt das Paar bei jeder Spaltenzahl ≥ 2 in einer Zeile.

## 1.9.2 - 2026-11-19

- Tabellen am Handy (`styles.js`): `table.cards` wird unter 600 px zu Blöcken; `thead` aus, die erste Zelle ist der Titel, die übrigen zeigen ihr `data-l` als Beschriftung links (`::before`, float) und den Wert rechts; leere Zellen entfallen. `.cardlbl` nur in Karten sichtbar (etwa „Unit-ID“ vor der Nummer), `.nocard` nur in Tabellen (unbenanntes 1-Wire-Gerät: Titel ist dann die ID, die ID-Zeile entfällt). Beschriftungen und `.cardlbl` immer in der Textschrift, auch in `.mono`-Zellen. Eingesetzt in den Clients-Tabellen (Seriell, Modbus, EnOcean, 1-Wire), Unit-IDs, 1-Wire-Geräte und -Schreibzugriffe, EnOcean-Sender, Mitschnitt-Dateien.
- Gateway tauschen: `baseIds(c)` in `enocean.js` vergleicht die Base-IDs von Gateway und Ersatz; verschieden: `.note.bad` im Bereich und Absatz im Bestätigungsdialog (`fbPromoteBaseDiffers`), unbekannt: Hinweis (`fbPromoteBaseUnknown`). Kein Sperren, ein nur empfangendes Gateway darf getauscht werden. `dp-confirm` zeigt Zeilenumbrüche (`white-space: pre-line`).
- Ereignis `enocean_fallback_promoted` mit `names`; Texte „Gateway getauscht …“, `fbAction_*` als Satzteile, `fbActionNames`. Ladegerüst der Einstellungen: Titel über dem Layout, unter 864 px eine Chip-Zeile wie die Seite.
- Einstellungen unter 864 px (`settings.js`): `.side` als waagrechte, klebende Chip-Zeile; `--sticky-top` aus der Höhe des App-Headers (`ResizeObserver`), Scroll-Spy-Schwelle und `scroll-margin-top` danach; der aktive Chip wird in der Zeile mittig gescrollt. `h1` aus der `nav` vor das Layout gezogen.
- Zahlengrößen als Variablen in `tokens` (`styles.js`): `--num-xl` 32/26 px (`.big`), `--num-l` 24/20 px (`.stats`/`.counters` b, `.tile b`, Ereignisse `.fig`, Import `.sum b`), `--num-m` 20/18 px (kleine Kacheln der Verbindungskarten), `--num-text` 18/16 px (Wort statt Zahl); der zweite Wert gilt unter 600 px. Die Kachelleiste der Liste hatte 26 px, die Karten 22 px.
- Kopfzeile am Handy in HA (`app.js` `_haSubscribe`): Nachrichten an das App-Panel von HA (`home-assistant/subscribe-properties`, Antwort `home-assistant/properties` mit `narrow`); bei `narrow` neu abonniert mit `kioskMode: true`, dann blendet HA seine Leiste aus, und unser Knopf schickt `home-assistant/toggle-menu`. Kiosk nur schmal, sonst bliebe am Desktop die Seitenleiste zu. Ältere HA ignorieren die Nachrichten. Geprüft mit einer Testseite, die HA nachstellt; Symbol `menu` in `ui.js`, Schlüssel `haMenu`.
- `h1` 24 px statt 28 px; `.head .sub` unter 600 px ausgeblendet (`styles.js`).
- Kopfzeile (`app.js`): Text immer `appRunning`, nur bei seriellen Verbindungen und stehendem ser2net `notRunning`; Schlüssel `running` im obersten Abschnitt entfernt.
- Breite: `--page-max: 1600px` in `app.js` (Kopfleiste, `main`, Offline-Hinweis, Darstellungsmenü); `dp-edit` und `dp-settings` auf 1152 px begrenzt. Neu `.trio` in `styles.js` (zwei Spalten plus eine darunter, ab 1600 px drei, unter 800 px eine); Detailseite: EnOcean mit Ersatz und Seriell nutzen `trio`, Modbus bleibt bei `pair` (die Clients-Tabelle braucht ~700 px). Geprüft bei 375/1024/1440/1600/1920 px ohne Überlauf; am Handy scrollen breite Tabellen und Code wie bisher in ihrer Karte.
- Verbindungsliste: Sortierung nach `KINDS`, eingeschaltet vor ausgeschaltet, Name (`localeCompare`, numerisch); Überschrift `h2.group` je Art, sobald die Liste mehr als eine Art zeigt (Schlüssel `group_*`); nicht mehr „Probleme zuerst“.
- Öffentliches Changelog nach dem Muster der anderen Repos: `device_proxy/CHANGELOG.md` englisch (HA und CI-Release-Notes), `device_proxy/CHANGELOG.de.md` deutsch, je Version `Neu/Geändert/Behoben`, Einträge `- **Bereich:** Text` in einer Zeile; die `### English`-Abschnitte sind in die englische Datei gewandert. READMEs verweisen auf beide.
- Release-Footer (`.github/release-footer.md`) nur noch englisch wie bei Eltako, mit Links auf das deutsche Changelog, DOCS und DOCS.de.
- Spendenblock wie bei Zeitarchiv als Zitat oben in `CHANGELOG.md` und `CHANGELOG.de.md` (HA zeigt `CHANGELOG.md` vor einem Update), mit absolutem Link auf die andere Sprache; der Release-Footer bleibt für GitHub.
- 1-Wire nicht mehr Beta: Chips „Beta“ (Art-Auswahl, owserver-Karte), Hinweis `owBetaNote` und Schlüssel `beta` entfernt, Beta-Absatz in DOCS und README weg.

- EnOcean, Hardware tauschen ohne Neustart: `EnOceanProxy._gateway_loop` hält die Verbindung zum Gateway in einer eigenen Aufgabe (`_gateway_session(link)`); `release_link()` schließt sie und hält an, `use_hardware(c)` setzt neuen Link, `c`/`key`, vergisst Base-ID, Erreichbarkeit und Fehler, schaltet von „fallback“ mit Grund `hardware_swapped` auf „main“ und läuft weiter. `hardware_key()` = `restart_key` ohne `GATEWAY_HARDWARE`; `_reconcile_proxies` nimmt diesen Weg, wenn sich nur die Hardware ändert, und lässt erst alle Links los, bevor einer neu öffnet (zwei Verbindungen zu einem TCP-Gateway). `enocean_promote(..., names=)`, Route `promote_fallback` mit `names`.
  - Panel: „Gateway tauschen“, Adressen im Text, Auswahl „Danach mit dem alten Gateway“, Häkchen „Namen mittauschen“, Bestätigung mit `fbPromoteWhat_*`.
  - i18n.js: der Grund von `enocean_failover`/`enocean_failback` wurde nicht übersetzt (Präfix `enocean_fall` passte nur auf `enocean_fallback_*`).
  - Test: Client bleibt beim Tausch verbunden und bekommt Telegramme der neuen Hardware, Proxy-Objekte bleiben, Namen getauscht. Anlass: Symcon flog beim Tausch hinaus und kam erst nach 4,5 min wieder.

## 1.9.1 - 2026-11-18

- 1-Wire, HTTP-Port: Feld `http_port` (0 aus; nur bei Art onewire, nicht gleich `port`, nicht reserviert, in `AppConfig.validate` mit den Ports aller Verbindungen geprüft; Warnung „belegt“ über `port_problem(c, port)`). Image: owfs mit owhttpd gebaut (`--disable-owhttpd` weg, keine weiteren Abhängigkeiten), Prüfung `owhttpd --version`.
  - `onewire.OwHttpd(OwServer)`: `owhttpd --foreground … -s 127.0.0.1:<innerer Port> -p 127.0.0.1:<freier Port>`, `--readonly`, wenn `write_access` nicht „all“ ist; Neustart wie owserver, Ereignis `onewire_owhttpd_ended`. `OwServer.name` für die Zeilen im App-Log.
  - `OneWireProxy._http_run`: innerer owserver-Port nur auf 127.0.0.1 für owhttpd (`_inner_client`, ein eigener `_Host` „HTTP“, nicht in `clients`), der HTTP-Port für die Programme (`_http_client`: `_allowed`, erste Zeile innerhalb `FIRST_REQUEST`, sonst Port-Check; `_client_for` mit der echten Adresse; Bytes unverändert zu owhttpd und zurück, `_pipe`; ohne owhttpd 503). `_serve` aus `_client` herausgelöst, für beide Wege. Zustand `http` (Port, lauscht, Fehler, owhttpd, Anfragen); `restart_key` startet neu, wenn sich mit HTTP-Port „alle dürfen schreiben“ ändert. Adressen: `urls["http"]`.
  - Panel: Feld im Netz-Abschnitt mit Hinweis „nur lesen“, Zeile „HTTP“ und Fehler an der owserver-Karte, Zeile auf der Detailseite.
  - Tests: `tests/fake_owhttpd.py`; Lesen über HTTP bis zum owserver mit Client und Wert, `--readonly`, Netzregel am HTTP-Port, 503 ohne owhttpd, Konfiguration und `restart_key`. `tests/HARDWARE.md` W14. Anlass: ein Symcon-Modul, das owhttpd auf 2121 nutzt.

- 1-Wire: Erste Anfrage einer Verbindung, die nicht vollständig oder kein owserver-Protokoll ist, wird gemeldet statt still geschlossen: Ereignis `onewire_bad_request` (Warnung, in `SUMMED`) mit `address`, `reason` (geschlossen, Rest kam nicht innerhalb von `FIRST_REQUEST`, `ProtocolError`), `bytes` und den ersten `BAD_SHOWN` (32) Bytes als Hex; Zähler `bad_requests` in `Stats` und im Zustand, die Bytes im Trace. `read_request(reader, seen)` sammelt dafür die gelesenen Bytes (`_exactly` liest stückweise statt `readexactly`, nur für die erste Anfrage). Eine Verbindung ohne ein Byte (Port-Check) bleibt still. Anlass: ein Programm, das den Proxy erreichte, aber nie als Client erschien. Tests: halber Kopf mit Timeout, Schließen mitten im Pfad, HTTP auf den Port.

- DOCS (de/en): Abschnitt 1-Wire neu gegliedert (Quelle, Geräte am Bus, Fehler am Bus, Clients und Schreibzugriff, Umzug, eigener owserver) und auf den Stand von 1.9.0 gebracht; 1-Wire auch in Neu starten und USB-Reset, Ereignisse, Clients, Benachrichtigungen, MQTT-Entitäten und Ereignistypen, Export, Sichern, eigene `ser2net.yaml`, Proxmox, „Wenn etwas nicht geht“ (drei Zeilen) und Dateien. README (de/en): Highlight 1-Wire mit allen Funktionen von 1.9.0 und „Beta“, Sicherheit (Schreibzugriff, Gerätenamen in der Diagnose), Schnellstart mit Port 4304.

## 1.9.0 - 2026-11-18

- 1-Wire, Schritt 2 (USB-Adapter an der App):
  - Image: owfs 3.2p4 aus dem Release-Tarball (SHA-256 geprüft) mit `libusb-dev` gebaut, nur `owserver` (alle anderen Module, Bindings, Zeroconf, i2c, w1, parport, ftdi aus); der Build bricht ab, wenn configure USB weglässt (`OW_USB = 1` im Makefile). Laufzeit `libusb`; `owserver --version` (endet mit Fehlercode) wird über die Ausgabe geprüft. Alpines `owfs` ist ohne libusb gebaut. owfs löst den Kernel-Treiber ds2490 selbst (`libusb_detach_kernel_driver`).
  - `model`: `LINKS["onewire"] = ("owserver", "usb")`, Eigenschaft `onewire_usb` (nicht `remote`, kein Gerät, `upstream` „USB“); `AppConfig.validate` erlaubt nur eine Verbindung auf dem USB-Adapter (Fehler am Feld `link`).
  - `onewire.OwServer`: owserver im Vordergrund (`--foreground --error_print=2 --error_level=1 -u -p 127.0.0.1:<freier Port>`), Ausgabe ins App-Log und die letzten 20 Zeilen in den Zustand, Neustart mit 1/2/5/10/30 s Pause (Ereignis `onewire_owserver_ended`), `restart()` wartet auf den neuen Prozess, `restart_with()` hält den Neustart an, bis der USB-Reset durch ist; beim Stoppen `terminate` unter `shield`.
  - Watchdog `look_after()` nach jeder Geräteliste: 2 Mal ohne Antwort → owserver neu (`onewire_restarted`), nach 2 solchen Neustarts → USB-Reset des ersten Adapters (`onewire_usb_reset`, Fehler `onewire_usb_reset_failed`), höchstens einmal in 600 s. Erste Geräteliste 3 s nach dem Start.
  - `devices`: `usb_devices(vendor, product)` (sysfs, mit Kernel-Treiber der ersten Schnittstelle), `reset_node()` aus `usb_reset` herausgelöst. Controller: `_reset_usb` setzt bei 1-Wire über USB den Adapter zurück (Knopf „USB-Reset“, nach Ende des Proxys); Snapshot `onewire_adapters` für das Formular.
  - Panel: Quelle „owserver im Netz“/„USB-Adapter an diesem Rechner“, gefundene Adapter mit Kernel-Treiber (außer `usbfs`), Hinweis ohne Adapter; owserver-Karte mit eigenem owserver, Neustarts, Resets, Startfehler und letzten Meldungen; USB-Reset-Knopf, wenn ein Adapter da ist; `proxyTarget` „USB“.
  - Tests: `tests/fake_owserver.py` (owserver-Ersatz, Modi „hang“ und „fail“), eigener owserver mit Argumenten und Geräteliste, Neustart nach Ende, Watchdog bis zum USB-Reset und zurück, nur ein USB-Bus, `usb_devices` aus einem sysfs-Baum, Reset-Knopf im Controller. `tests/HARDWARE.md` W6–W10.
  - DOCS (de/en): Quelle USB, Schritt 3 des Umzugs, eigener owserver und Watchdog.
  - Cache des eigenen owserver: Feld `owserver_cache_s` (Standard 15, 0 bis 3600), als `--timeout_volatile` an owserver; eine Änderung startet den Proxy und damit owserver neu (`restart_key`). Formular unter „Erweitert“ nur bei Quelle USB, Detailseite zeigt den Wert. Panel: ein bekanntes Gerät, das gerade nicht in der Liste ist (noch nicht „fehlt“), zeigt „zuletzt gesehen“ statt „kein Programm liest es“.
  - Nachträge: `restart_connection(usb=True)` akzeptiert eine 1-Wire-Verbindung über USB (prüft, ob ein Adapter da ist) statt „a USB reset needs a device of this host“; vorher schlug der Knopf auf der Detailseite fehl. MQTT-Knopf `usb_reset` auch für `onewire_usb`. Statistik wird gelesen, sobald der owserver erreichbar ist (alle 5 s bis dahin), nicht erst nach 60 s. Kachel „Fehlende Geräte“ statt „Fehlen“ (neben „Fehler“). README (de/en): Kurztext und Highlight um Quelle USB und Diagnose; neues Bild `screenshots/<lang>/onewire.png`, `tools/screenshots.mjs` wartet dafür, bis der Dev-Server den fehlenden Sensor zeigt. Test im Controller: Knopf mit Proxy-Neustart, MQTT-Knopf, ohne Adapter.
- 1-Wire, Diagnose (`onewire_bus.py`, `Bus` je Verbindung im Proxy):
  - Bekannte Geräte in `/data/onewire_devices.json` (je Verbindungs-ID erstes und letztes Sehen; gespeichert bei Änderung der Menge, sonst alle 600 s). Fehlt nach `MISSING_AFTER` (2) Listen in Folge (`onewire_device_missing`, `…_back`); neu, wenn erst `NEW_AFTER` (300 s) nach der ersten Liste gesehen und die Liste nicht leer war (`onewire_device_new`); `forget()` über `POST api/tools/<id>/onewire/forget`.
  - Werte aus den Antworten auf read/get, die durch den Proxy gehen (kein eigenes Lesen): letzter Wert je Eigenschaft, Fehler je Gerät; bei Temperatur (Familien 10/22/28/3B/42, `temperature`, `temperature9..12`, `fasttemp`) 85 °C (`onewire_value_85`, höchstens einmal pro Stunde je Gerät) und „bewegt sich nicht“ (2 h und 20 Abfragen ohne Änderung, nur Anzeige).
  - Zähler aus `/statistics/errors/` (CRC8/16 errors und tries, BUS_*) alle 60 s über `ask()`; Anteil CRC-Fehler, Summe Busfehler, Zeitpunkt des letzten Anstiegs. Fehlt die Statistik (ENOENT), bleibt sie weg.
  - Namen: `Settings.onewire_names` („ID Name“ je Zeile, `parse_names`), privat in Historie und Diagnose, `PUT api/onewire/names`. Der Controller hängt an 1-Wire-Ereignisse mit `device` ein `label` (Name und ID); Benachrichtigung `onewire_missing` mit Namen, wenn `notify_missing`. MQTT-Entität `onewire_missing`; `onewire_devices` zählt jetzt die vorhandenen.
  - Zustand: `devices` sind die Zeilen von `Bus.rows()` (fehlende zuerst, mit Werten, Fehlern, `bad`, `frozen`), dazu `present`, `missing`, `statistics`.
  - Panel: `dp-ow-devices` (Namen bearbeiten, Wert, Zustands-Chips, Vergessen mit Rückfrage), Kachel „Fehlen“ und Zeile „Busfehler“ an der owserver-Karte. Dev-Server: simulierter owserver mit Statistik, gelegentlich 85 °C, ein gestern gesehener Sensor fehlt, zwei Namen.
  - Eigener owserver: die erste Geräteliste und die Statistik warten, bis er Verbindungen annimmt (`_owserver_ready`, bis 10 s), statt fest 3 s; sonst kam beim Start ein „nicht erreichbar“.
  - Tests: `tests/test_onewire_bus.py`, Werte und Zähler im Proxy, Benachrichtigung und Ereignis mit Namen im Controller; `tests/HARDWARE.md` W11–W13.
  - iButtons: `onewire_bus.TRANSIENT_FAMILIES` (01, 02, 04, 06, 08, 0A, 0C) zählen nie als fehlend (kein Ereignis, keine Benachrichtigung, nicht in `missing()`), Zeile mit `transient`; Panel-Chip „iButton aufgelegt“ bzw. „zuletzt aufgelegt“, „Vergessen“ auch für ein abgenommenes. `FAMILIES` um die iButton-Typen ergänzt, 01 heißt „DS1990A / DS2401“. Test in `test_onewire_bus.py`.
  - Versorgung: Nach jeder erfolgreichen Geräteliste fragt der Proxy für Temperatursensoren ohne bekannte Versorgung einmal je Lauf `/<id>/power` (`Bus.needs_power()`/`powered()`, 1 extern, 0 parasitär; ohne Antwort in diesem Lauf nicht wieder). Zeile `power`; Panel-Chip „parasitär versorgt“, der 85-°C-Hinweis nennt dann die Ursache. Dev-Server: zweiter Sensor parasitär. Tests in `test_onewire_bus.py` und `test_onewire.py`.
  - Adapter-Infos: `read_info()` nach einer Geräteliste, höchstens alle 600 s: `/bus.0/interface/settings/{name,address,version}` (owfs 2.x: `/system/adapter/*.0`) und `/system/configuration/version`; nur was der owserver hat, Zustand `info`. Panel-Zeile „Adapter“ an der owserver-Karte. Dev-Server und Test (`test_values_and_counters_reach_the_state`).
  - Genauer Chip: nach einer Geräteliste einmal je Gerät und Lauf `/<id>/type` (`Bus.needs_type()`/`typed()`), gespeichert in `/data/onewire_devices.json` (`type`), damit auch fehlende Geräte ihn behalten und er nicht neu gefragt wird. Zustand `chip`, `type` ist der genaue oder der übliche aus `FAMILIES`; Panel-Spalte „Chip“ mit „(üblich)“, solange der genaue fehlt. Dev-Server antwortet auf `type`. Tests.
  - Alle Werte: Panel zeigt in der Zeile die Temperatur oder sonst den zuletzt gelesenen Wert, „+N Werte“ klappt eine Unterzeile mit allen gelesenen Eigenschaften auf (`open`-Menge im Element). `onewire_bus.VALUES_MAX` (32) Eigenschaften je Gerät, die am längsten nicht gelesene fällt heraus. Dev-Server liest auch PIO.A/PIO.B/sensed.A des DS2413. Test in `test_onewire_bus.py`.
  - DS2438: „bewegt sich nicht“ auch für die Temperatur der Familie 26 (`FROZEN_FAMILIES`); 85 °C bleibt bei den DS18x20 (`TEMPERATURE_FAMILIES`), der DS2438 hat keinen solchen Startwert. Test.
  - Ausreißer: je Temperatur-Eigenschaft (Familien wie „bewegt sich nicht“) ein `Track` mit letztem gutem Wert; ein Sprung über `SPIKE` (10 °C) wartet auf den nächsten anderen Wert (dieselbe Antwort aus dem Cache zählt nicht); zurück auf `SETTLE` (2 °C) an den alten Wert → Ausreißer (`spikes`, `spike_at`, `spike_value`, Ereignis `onewire_value_spike` höchstens einmal pro Stunde je Gerät), sonst echte Änderung. 85 °C beim DS18x20 zählt nicht als Ausreißer und verschiebt den alten Wert nicht. Panel-Chip mit Wert und Zeit, MQTT-Ereignistyp. Dev-Server: erster Sensor alle drei Minuten einmal 127,94 °C. Test.
  - Bus jetzt absuchen: `probe(uncached=True)` liest DIRALL `/uncached/` (Zeitlimit `SCAN_TIMEOUT` 30 s) und zählt wie eine normale Geräteliste; `scan()` über `POST api/tools/<id>/onewire/scan` (Controller `onewire_scan`), Antwort Geräte und Dauer. `probe()` gibt jetzt zurück, ob es geklappt hat. Panel-Knopf in der Geräte-Karte mit Ergebnis. Test.
  - Schreib-Protokoll: `OneWireProxy.writes` (deque, `WRITES_KEPT` 100) mit Zeit, Client, Pfad, Wert (`written()`, Text oder Hex) und Ergebnis (`…` bis zur Antwort, dann `ok` oder der errno-Name, `EACCES` bei Schreibschutz); `Waiting` trägt den Eintrag bis zur Antwort. Zustand `writes` (neueste zuerst), Panel-Karte „Schreibzugriffe“ mit Namen der Geräte. Test in `test_writes_only_from_allowed_clients`.
  - Diagnose-Paket: `diagnostics.unnamed()` ersetzt bei Ereignissen mit `device` und `label` das Label (Name und ID) durch die ID, in `params` und `message`; vorher kamen die Gerätenamen über die 1-Wire-Ereignisse ins ZIP. Test `test_diagnostics_of_a_onewire_bus_keep_the_bus_and_hide_who` (Geräte, Schreibzugriffe und owserver-Log drin, Namen, Client-Adressen und Host des owserver nicht).
- Review des Branches (`/code-review high main...onewire-usb`), 8 Befunde, je ein Commit:
  - USB-Reset von Hand (Knopf, MQTT) bei 1-Wire über USB geht über `OneWireProxy.usb_reset()` statt den Proxy neu zu starten: Clients, Werte, Zähler, Schreib-Protokoll und Watchdog-Zahlen bleiben, Ereignis `onewire_usb_reset` mit der Quelle als Grund. Nur zusammen mit dem Stromschalter läuft es weiter über den Neustart.
  - `onewire_bus.prune()`: der Controller lässt bei jedem Abgleich der Proxys die Geräte gelöschter 1-Wire-Verbindungen aus `/data/onewire_devices.json` weg (abgeschaltete bleiben); vorher blieben sie für immer. Ohne jede 1-Wire-Verbindung wird nichts weggelassen, damit eine nicht lesbare Konfiguration die Geräte nicht mitnimmt.
  - `Bus.typed()` speichert nicht mehr selbst; der Proxy speichert die Geräte-Datei einmal nach allen Chip-Abfragen (vorher einmal je Gerät).
  - Die eigenen Abfragen der App (`ask()`: Statistik, Chip-Typ, Versorgung, Adapter-Infos) teilen eine gehaltene Verbindung mit `PERSISTENCE` (Lock), statt je Anfrage eine neue zu öffnen (vorher etwa 12 Verbindungen pro Minute nur für die Statistik); gewährt der owserver keine Persistenz oder ist die Verbindung weg (Neustart), geht es einmal auf einer neuen weiter. Der Dauertest zählt diese eine Verbindung nicht als übrig geblieben. Test `test_the_apps_own_requests_share_one_connection`.
  - „neu“ gilt einen Tag ab dem ersten Sehen (`NEW_FOR`), nicht bis zum nächsten Neustart der App.
  - Nur eingeschaltete 1-Wire-Verbindungen über USB schließen sich aus; eine abgeschaltete zweite darf als Ersatz bleiben.
  - „Bus jetzt absuchen“ zählt nicht für „fehlt“ (`Bus.listed(count=False)`): was da ist, ist gesehen oder wieder da, was fehlt, zählt nur in den regelmäßigen Listen; vorher konnten zwei Klicks beim Verkabeln ein Gerät als fehlend melden und benachrichtigen.
  - Der eigene owserver bekommt bei jedem Start einen frischen freien Port (`free_port()` in `_run_once`) statt einmal beim Bau des Proxys; war der Port inzwischen vergeben, startete owserver vorher immer wieder vergeblich.
- Tests und Werkzeuge:
  - `tools/soak_onewire.py`: Dauertest des 1-Wire-Proxys gegen einen nachgebauten owserver, der jeden Lesezugriff mit Pfad und Zähler beantwortet (eine Antwort beim falschen Client fällt auf). 8 Clients mit einer Verbindung je Anfrage, 2 mit dauerhafter Verbindung, einer, der schreibt, 2, die mitten in der Anfrage abbrechen; alle 40 s ist der owserver 6 s weg, abwechselnd nicht erreichbar und hängend, gelegentlich Pings. Am Ende: keine falsch zugestellte Antwort, keine offene Verbindung an Proxy und owserver, Hosts nach `IDLE_AFTER` weg, Schreib-Protokoll und Werte in ihren Grenzen, nichts fehlt, Tasks nicht gewachsen; Grenzen 2 % Fehlschläge außerhalb der Ausfälle, 20 MB Speicher. 2-Minuten-Lauf: 6237 Lesezugriffe, 0 falsch, 0 % Fehlschläge außerhalb der Ausfälle, +0,8 MB. README (de/en) nennt es unter Development.
  - CI: Job „Tests“ führt `tools/soak_onewire.py --ci` aus (45 s, Ausfälle alle 16 s für 4 s, also „weg“ und „hängt“). Der erste kurze Lauf fand einen Fehler im Proxy: eine Verbindung, die keine oder nur eine halbe erste Anfrage schickt, blieb für immer offen (kein Zeitlimit vor der ersten Anfrage, wenn `timeout` 0 ist). Jetzt `FIRST_REQUEST` (30 s, oder das kürzere `timeout`); Test `test_a_connection_that_sends_no_request_is_closed`. Im Dauertest bricht der abbrechende Client seine Verbindung jetzt auch ab, wenn der Lauf endet (`finally`).
  - Test `test_a_persistent_connection_with_pings_and_a_directory` war unter Last unzuverlässig (unter voller CPU-Last 60 von 60 Mal rot): er zählte alle Verbindungen zum nachgebauten owserver, auch die eigenen Abfragen der App (Chip-Typ, Versorgung, Adapter), die da noch liefen. Jetzt merkt sich der Test, über welche Verbindung jede Anfrage kam, und prüft, dass DIR und READ dieselbe nutzten. Gefunden mit 60 Läufen der 1-Wire-Tests bei belegten Kernen (`yes > /dev/null` je Kern); danach 60 von 60 grün, dazu 5 komplette Läufe unter Last. Parallele Testläufe kollidieren an den festen Ports von `test_kinds.py` (15021, 14304); das ist der Versuchsaufbau, kein Fehler.

## 1.8.0 - 2026-11-18

- GitHub-Vorschaubild (Social Preview) `screenshots/social-preview.png`, 1280×640: Icon, Name, Kernsatz, acht Funktionen (ser2net 4, Modbus-Proxy, EnOcean-Proxy, Gateway-Ersatz, zweites oder Test-HA, Replay, Schreibschutz je Client, Live-Daten) und der englische Modbus-Screenshot. Quelle `tools/social-preview.html`, gerendert mit headless Chrome (Befehl oben in der Datei); hochgeladen wird es von Hand unter Settings → General → Social preview. README (de/en) nennt es unter Development.
- GitHub Discussions eingeschaltet; `.github/ISSUE_TEMPLATE/config.yml` hat als ersten Kontakt-Link „Question / Frage“ auf die Kategorie Q&A.
- README (de/en), Modbus-Proxy: statt „verbreitete Wechselrichter“ die Hersteller der Geräteprofile aus `model.py` (SolarEdge, Huawei SUN2000, Fronius, SMA, Kostal Plenticore, Sungrow, Victron GX), damit Suchen nach dem Hersteller das Projekt finden.
- 1-Wire, Schritt 1 (owserver im Netz als Quelle):
  - Neue Verbindungsart `onewire` (`model.KINDS`, `LINKS["onewire"] = ("owserver",)`, Vorlage `onewire`, `host_port` ohne Angabe 4304). Schreibrechte über die vorhandenen Felder `write_access`/`write_clients`; deren Prüfung ist `_validate_writers()`, auch von Modbus benutzt. Neu als Konstante `OWSERVER_PORT`.
  - `onewire.py`: `OneWireProxy` in `kinds.PROXIED`. Je Client-Verbindung eine eigene Verbindung zum owserver, Bytes unverändert; unterwegs werden die 24-Byte-Köpfe gelesen (`read_request`/`read_answer`, Tokens anderer owserver berücksichtigt, Pings mit Payload −1 durchgereicht, DIR als mehrere Nachrichten mit leerem Abschluss). Schreiben (Typ 3) ohne `may_write` beantwortet der Proxy selbst mit −EACCES ohne Persistenz und schließt; Ereignis `onewire_write_blocked`. Client = Host (pyownet verbindet je Anfrage neu): `client_connected` bei der ersten Anfrage, `client_disconnected` nach `IDLE_AFTER` (300 s) ohne Anfrage und ohne offene Verbindung; eine Verbindung ohne Anfrage (Port-Check) legt keinen Client an. `max_clients` zählt Hosts, je Host höchstens 32 offene Verbindungen.
  - Erreichbarkeit: alle 30 s DIRALL "/" (aus dem Cache des owserver), daraus die Geräteliste (`parse_devices`, Familien-Tabelle `FAMILIES`); Ereignisse `onewire_down`/`onewire_back` (in `GONE`/`BACK`, `SUMMED`), Meldung `onewire_loaded`. Mitschnitt: Pfad und Client, Antworten auf read/get mit Wert, Fehler mit errno-Namen.
  - MQTT: `reachable`, `onewire_devices`, `requests`; `EVENT_TYPES["onewire"]`. Adressen: `{"owserver": "host:port"}`. Testfall: `link` und `info` ohne Client wie bei Modbus.
  - Panel: `panel-src/src/onewire.js` (Vorgaben, Karten owserver, Geräte am Bus, Clients-Tabelle); Formular `_onewireSections()`/`_onewirePreview()` (ohne Stromschalter-Karte), Detailseite, Übersicht (Chip „n Geräte“, Filter), Mitschnitt- und Live-Beschriftungen wie Modbus (`dirmb_*`, `trmb_*`), Icon `onewire`. Texte `ow*`, `liveEmptyOw`, `liveSubOw`, `kind(sub|Name)_onewire`, `filter_onewire`; Aufzählungen der Proxy-Arten um 1-Wire ergänzt.
  - `tools/dev_server.py`: simulierter owserver mit vier Geräten, Verbindung „1-Wire-Bus“ auf 14304 und ein Client, der alle 5 s zwei Temperaturen liest.
  - Tests: `tests/test_onewire.py` (Protokoll, Durchreichen, Persistenz mit Pings und DIR, Schreibrechte, Abweisen und Ablauf von Clients, nicht erreichbarer owserver, Konfiguration, Neustart-Schlüssel, Entitäten), `test_kinds.py` (Controller, Snapshot, Adressen, Probleme, MQTT).
  - `tests/HARDWARE.md`: Abschnitt 1-Wire (W1–W5) für den Test gegen einen echten owserver.
  - Als Beta gekennzeichnet: Chip „Beta“ an der Verbindungsart im Formular und an der Karte owserver, Hinweis `owBetaNote` oben im Formular, Satz in DOCS (de/en).
  - Noch nicht: owserver im Image (libusb) und USB-Adapter direkt an der App; das kommt mit Schritt 2.
- CI, Job `publish`: auch andere Branches veröffentlichen ein Image, aber nur eine Testversion (Version mit „-“, etwa `1.8.0-dev1`), nur wenn alle Jobs grün sind und nie als `latest`; eine Version ohne „-“ auf einem Branch wird übersprungen. Die Tags kommen aus dem Schritt `version`. Eine Testinstanz installiert so `<Repository-URL>#<Branch>`; wer `main` nutzt, bleibt auf dessen Version. So entstand `1.8.0-dev1` vom Branch `onewire` (das Image ist auf ghcr, ohne Release).
- DOCS (de/en): Abschnitt „1-Wire buses“/„1-Wire-Busse“ und Punkt in der Einleitung; README (de/en): Kurztext, Einleitung und Highlight; `config.yaml` `description`.

## 1.7.0 - 2026-11-15

- Neuer Panel-Look:
  - `styles.js`: `--radius` (16 px, Karten), `--control-radius` (10 px, Buttons, Felder, `.seg`, `.note`), `--shadow`, Klasse `.label` (Großbuchstaben). Kacheln global: `.counters` und `.stats` ohne `.well`-Box, `.hint` per `order: -1` als Label darüber, Wert 24 px/300 mit `tabular-nums`; `.big` ebenso dünn. Schrift-Untergrenze: alle `calc(11px|12px * var(--fs, 1))` in `panel-src/src` als `max(10.5px, calc(…))`. `.foldnote` (unter 600 px einzeilig mit Knopf „Mehr“). `[tabindex="-1"]:focus` ohne Outline.
  - `app.js`: Navigation als Tabs mit Unterstrich und 16-px-Icons, `.count` als Badge auch auf dem Desktop, unter 960 px eigene Zeile; am Handy untere Leiste mit Pill. Header: `.status`-Zeile statt der Chips (ser2net, Probleme, App), Tooltip mit App- und ser2net-Version, Mitschnitt-Chip bleibt; `.brand` mit `flex: 1 1 0`, `nav` mit `flex: none`. Paletten-Button `#lookbtn` mit Menü (`menuitemradio`, Escape, Scrim), außerhalb des Headers gerendert, weil dessen `backdrop-filter` fixe Boxen einschließt; am Handy als Sheet von unten; öffnet auch auf `dp-look-open`.
  - `connections.js`: `.band` als Karte mit `.tile`s. Verbindungskarte mit `.figs` (Clients `n / max`, Rate + `sparkline` 120×22, `fmtAgo` der letzten Daten mit `ok`/`warn`), Client-Liste auf `CLIENTS_SHOWN` (3) mit Link `moreClients`; `_last` und der Client-Balken entfallen. `mqttNote` (`ui.js`) als `.foldnote`, Zustand `page._mqttOpen`.
  - `detail.js`: eigene `.counters`-Regel entfällt; Rate- und Modbus-Karte nutzen `.big`. Seriell ohne `last_data` und ohne `line_errors`: `quietCard` statt `pair(rateCard, stateCard)`.
  - `events.js`: Kartenraster `.stats` heißt `.statcards` (sonst griffe die globale `.stats b` auf die Namen), Zahlen als `.label` + `.fig`; `.tabs` und `.lv` mit `--control-radius`.
  - `edit.js`: `.grid2 > .fld` als Subgrid über drei Zeilen (Label, Feld, `.fx` mit Fehler und Hinweis), nur bei höchstens drei Kindern; `_input` legt Fehler und Hinweis in `.fx`; `mbHostHint` als Hinweis von `host`.
  - `settings.js`: statt drei `.seg` für Schema, Modus und Größe eine Zusammenfassung mit Knopf (`dp-look-open`); `.act:hover` auf `--surface-2` (war das nicht definierte `--surface-1`). `import.js`: `.gone` auf `--warn-soft`/`--warn`/`--warn-line` (war `--warn-bg`/`--warn-text` mit festen Fallbacks).
  - Lade-Zustand: `sk()` und `skeleton(page, title)` in `ui.js` (Vorlagen für `connections`, `connection`, `edit`, `events`, `settings`, `trace`), Stile `.skel`/`.sk` in `styles.js` (erst nach 300 ms per `animation-delay` sichtbar, Schimmer aus bei `prefers-reduced-motion`, `aria-busy` und `.sr`-Text). `app.js` zeigt ohne ersten Status Kopfzeile, Reiter und das Skelett der Route, in der Statuszeile einen Balken; `edit.js` ohne Entwurf `skeleton("edit")`.
  - `.stats`/`.counters` > `.well` mit zwei Kindern als Subgrid über zwei Zeilen (Label, Wert), damit ein umbrechendes Label den Wert nicht verschiebt.
  - README-Screenshots (`screenshots/de`, `screenshots/en`) im neuen Look neu erzeugt; `tools/screenshots.mjs` blendet den MQTT-Hinweis aus (Dev-Server ohne Broker) und sagt im Kopf, dass kein anderer Dev-Server laufen darf (sonst „Port belegt“ auf den Bildern).
  - `edit.js` Fehler: die drei Sammel-Hinweise (`note bad` mit Schlüsseln) sind `_errorList()`, Label des Felds aus dem DOM (`#e-<key>` → `.fld .lbl`/`legend`, sonst der Schlüssel), jeder Eintrag ein Knopf `_toField(key)` (öffnet `advanced`, scrollt, fokussiert). `_save` springt nach einer Fehlerantwort zum ersten `.err` in Seitenreihenfolge. `updated()` klappt `advanced` auf, wenn ein gezeigter Fehler kein Feld auf der Seite hat, einmal je Fehlermenge (`_openedFor`). Text neu: `errorsTitle`.
  - Texte neu: `lookTitle`, `lookHint`, `tileState`, `tileClients`, `tileData`, `tileLast`, `moreClients`, `noteMore`; entfernt: `lastDataAgo`, `noDataYet`.

## 1.6.2 - 2026-11-14

- CI: Job `release` nach `publish` (nur main, alle Jobs grün): legt `v<version>` als GitHub-Release an, falls es noch fehlt. Notes = Abschnitt `## <version> - …` aus `device_proxy/CHANGELOG.md` plus `.github/release-footer.md` (Stern, Issue mit Diagnose-Paket, Spenden, Anleitung; deutsch und englisch). Der Tag sitzt auf dem Commit, der die Version in `config.yaml` gesetzt hat. Fehlt der Abschnitt, wird der Job rot.
- Zweites Review mit Fable (Kern, Web/Speicher, Panel), alle Befunde behoben:
  - Modbus: `_connect` setzt bei TCP `_down_on_connect` nach `_up()` zurück; sonst nullte jeder Neuaufbau nach einem Timeout `_failures`, und `DOWN_AFTER` wurde nie erreicht (auch `FAIL_FAST` griff nach erfolgreichem Verbinden weiter).
  - Modbus: `_shutdown` setzt `_stopped`, leert den `Scheduler` (`drain()`) und beantwortet alle Futures mit `EXC_PATH`; `_work` beantwortet den laufenden Job beim Abbruch; `_queued` antwortet nach dem Stopp sofort. `kickolduser` bricht auch den Task des verdrängten Clients ab.
  - `importer.read_file()`: UTF-8, sonst Latin-1; benutzt für Import-Ordner, `_runtime` und `GET api/custom`. `parse()` macht aus `RecursionError` einen `ReadError` (`unreadable`), `modbus_import._load` fängt ihn auch. `import_folder` fängt `ValueError` statt nur `ReadError`.
  - `_remaddr` entfernt `ipv4,`/`ipv6,`/`tcp,`/`udp,`/`sctp,` vorne, wie `_accepter`.
  - `db._open`: nur bei `DAMAGED` `_recreate`, sonst `_in_memory` (`:memory:`, Ereignis `history_unavailable`); `_recreate` fällt bei `OSError`/`sqlite3.Error` ebenfalls auf `_in_memory` zurück. `Database.generation` zählt neue Dateien; `ClientSessions._write` fügt eine Zeile aus einer älteren Generation neu ein, statt per alter ID zu updaten.
  - `WebServer.stop`: offene Verbindungen (`_writers`) per `transport.abort()`, `wait_closed()` mit 2 s.
  - Web: `api/preview` prüft `connection` auf Objekt, `api/versions/<id>` nur bis 15 Ziffern (sonst 404), `api/mqtt/test` Port 1–65535. `_backup_config` verlangt `config`; `_custom_only_if_there` setzt `source` auf `forms`, wenn die eigene Datei fehlt (Backup und Versionen).
  - EnOcean: neue Netz-Clients halten Frames in `held`, bis die ersten Bytes da sind oder `HOLD_SECONDS` (1 s) um ist; `_start_replay` schickt danach nur die gehaltenen, die nicht im Replay waren. `active` merkt Daten in beide Richtungen für `timeout`. Die Warteschleife bei `CLIENT_QUEUE_MAX` endet, wenn der Writer schließt.
  - `listen._sniff`: 1 s Pause nach „the adapter was closed“.
  - MQTT: Client-ID aus dem Basis-Topic (`device-proxy` beim Standard), `_stale_config` löscht nur Configs mit `availability` `<base>/status`. DOCS: zwei Installationen brauchen je ein eigenes Basis-Topic.
  - Panel: `_jobPoll` toleriert vier Fehler in Folge (404 sofort) und setzt dann `state: "failed"`; `rows()` mit Breite 0 gibt nichts zurück; `decodeURIComponent` im Hash mit `try`; `unit_routes` auf der Detailseite an `[,;\s]+` getrennt; `has()` in `i18n.js`, `ex_7`/`ex_other`; `fbReason_none` wird nicht gezeigt.
  - Locales: elf deutsche Fehlermuster (Sperren, Wartung, `silence_restart`, Namen, `source`), `history_unavailable`.
  - Tests für alle Punkte; zwei MQTT-Tests schicken jetzt Configs mit `availability`.
- MQTT: Scheitert `press()`, meldet `_message` das Ereignis `button_failed` (Knopfname in der Sprache der Benachrichtigungen, `error`); das Panel übersetzt `error` mit `fieldError`.
- Jobs tragen `tool` (`detect`, `scan`); `Controller.running_jobs()` und `GET api/tools/<id>/jobs` liefern die laufenden als tool → job id. Die Detailseite holt sie in `_resumeJobs()` (bei Wechsel der Verbindung und beim erneuten Einhängen) und pollt weiter; `disconnectedCallback` setzt laufende Stände zurück.

## 1.6.1 - 2026-11-13

- Panel: `fmtSince(ts)` (Dauer über `fmtDuration`) für alle „seit {t}“-Texte statt `fmtAgo`, das „vor …“ liefert; englische Texte von „since“ auf „for“.
- Review mit Fable (Backend und Panel), alle Befunde behoben:
  - Modbus: `write_shape_ok()` prüft Länge, Bytezahl und Anzahl von FC5/6/15/16/22/23, sonst `EXC_VALUE` (Log `blocked`, Zugriffstest `ac_malformed`). Herstellerfunktionen bleiben offen.
  - Modbus: RTU-Leitung nach `_down_on_connect` wieder offen → `reachable = None`, `_back_due` hält `modbus_back` fällig. Die Entity-Runde liest bei `reachable False` eine Entität je Runde als Probe.
  - Diagnose: `masked()` maskiert Namen, Notify-Dienst und MQTT-Zugang auch in alten Ereignissen. `store.changes` speichert `client_names` und `sender_names` nicht mehr (`PRIVATE_SETTINGS`).
  - EnOcean: `Captures._write` fängt `OSError`, stoppt und meldet `capture_failed`. `stop()` gibt auch frei, wenn `close()` scheitert. Keepalive für Clients.
  - `block_client` gibt `serial_unaffected` zurück (API und Toast `blockSerialNote`), Ereignis `client_blocked_not_custom`.
  - `migrate`: `lan_networks` aus allen `PRIVATE_NETWORKS` außer den App-Netzen. Keine zweite Migration, weil sie bearbeitete Listen nicht erkennen kann.
  - `apply()`: Debounce wird übernommen; nach dem Speichern läuft der Abgleich in `try/finally`; `OSError` aus `write_config` wird zu `SaveError`; `AdminClient.command` macht aus `OSError` einen `AdminError`.
  - `ha_mqtt._stale_config` prüft zuerst das Präfix, dann `configs()`.
  - Dateinamen der Mitschnitte (`_file_names`) nummeriert über alle Verbindungen in der Reihenfolge der Konfiguration, auch für Aufzeichnungen.
  - Panel: `.selected` statt `?selected` (37 Stellen); `_syncSaved` nach dem Speichern; `discard()` beim Löschen; Import über `_taken`/`_mode`; Sequenzzähler in `_loadHistory`; `wholeNumber()` für Zahlenfelder; `fmtAgo` mit `Math.floor`; `lang` bei allen `toLocale*`; `tn()` mit `_1`-Schlüsseln für die Einzahl; Pfad der Aufzeichnungen ohne Kopier-Knopf.
- CI: Der Integrationstest sucht die Aufzeichnung als `a-*.log`, seit Dateien das Startdatum tragen.

## 1.6.0 - 2026-11-09

- MQTT: `default_entity_id` je Entität (ab HA 2025.10, ersetzt `object_id`), greift nur beim ersten Anlegen. Bestehende IDs über
  `ha_registry.py`, ein kleiner WebSocket-Client auf `/core/websocket` (`config/entity_registry/list` und `/update`, `search/related`).
  Bewusst per Knopf, nicht beim Update, weil Verweise auf alte IDs brechen.
- MQTT: Plattform `event` je Verbindung und am Hub, Liste in `EVENT_TYPES`/`APP_EVENT_TYPES`, gesendet per
  EventLog-Listener auf dem Controller (die Bridge wird neu gebaut). Nur `count == 1`, nicht retained.
- MQTT: `sw_version` aus `APP_VERSION` an jedem Gerät, die ser2net-Version steht weiter im Panel.
- MQTT: `configuration_url` je Gerät als `homeassistant://hassio/ingress/<slug>`, Slug von
  `/addons/self/info`, auf dem Controller gemerkt (die Bridge wird bei Änderungen neu gebaut).
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
