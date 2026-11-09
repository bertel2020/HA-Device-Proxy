# Changelog

## Unreleased

- **Clients, Verlauf**: Tippst du auf einen Rechner, siehst du jetzt, wann er an welcher Verbindung
  hing: eine Zeitleiste über 7 Tage oder 24 Stunden, die letzten Verbindungen mit Dauer und
  Datenmenge, dazu Abbruch-Serien und abgewiesene Versuche. Der Verlauf beginnt mit diesem Update.
  Bei seriellen Verbindungen ist die Datenmenge so genau wie der letzte Statusabruf, abgewiesene
  Versuche gibt es bei Modbus und EnOcean. Wird ein Rechner entfernt, verschwindet auch sein Verlauf.
- **Sprachen**: Jede Sprache ist jetzt eine eigene Datei, mit Weboberfläche, Meldungen und
  Entitätsnamen. Eine neue Sprache braucht nur noch eine Datei; was darin fehlt, erscheint auf
  Englisch. Die Texte selbst sind unverändert.
- **Ereignisse**: Abgewiesene Clients erscheinen bei Modbus und EnOcean jetzt auch, wenn ihr Netz
  nicht erlaubt ist, gerade Wartung läuft oder sie blockiert sind. Wiederholungen werden
  zusammengefasst.
- **Mitschnitt**: Die Verbindung wählst du jetzt in einer Liste wie unter Ereignisse, so bleibt
  auch bei vielen Verbindungen jede erreichbar. Laufende Aufzeichnungen sind darin markiert.
- **Mitschnitt, Dateien**: Jede Datei trägt das Startdatum ihrer Aufzeichnung im Namen und behält
  ihn, zum Beispiel `pumpe-20261109-104012.log`. Das Einschalten beginnt eine neue Datei. Wird die
  Zahl der behaltenen Dateien gesenkt, verschwinden die überzähligen jetzt auch. Vorhandene Dateien
  bleiben unter ihrem Namen, bis sie herausrotieren.
- **Mitschnitt, Tabelle**: Kompakte Zeilen, neueste oben, Herunterladen und Löschen als gleich große
  Symbole, die laufende Datei ist markiert.

### English

- **Clients, history**: Tap a computer to see when it was connected to which connection: a timeline
  over 7 days or 24 hours, the recent connections with duration and data, plus reconnect bursts and
  refused attempts. The history starts with this update. On serial connections the amount of data is
  as exact as the last status read; refused attempts exist for Modbus and EnOcean. Removing a
  computer removes its history too.
- **Languages**: Each language is now a file of its own, with the web interface, notifications and
  entity names. A new language needs just one file; whatever it leaves out appears in English. The
  texts themselves have not changed.
- **Events**: With Modbus and EnOcean, refused clients now also appear when their network is not
  allowed, maintenance is on or they are blocked. Repeats are summed up.
- **Trace**: The connection is now chosen from a list as under Events, so every connection stays
  within reach however many there are. Running recordings are marked in it.
- **Trace, files**: Every file carries the start date of its recording in its name and keeps it,
  for example `pump-20261109-104012.log`. Switching recording on begins a new file. Lowering the
  number of files kept now also removes the surplus ones. Existing files keep their names until
  they rotate out.
- **Trace, table**: Compact rows, newest first, download and delete as icons of the same size, and
  the running file is marked.

## 1.5.1 - 2026-11-08

- **Übersicht**: In der Kachel einer Verbindung steht bei den Clients kein Stift mehr, die Zeile
  bricht nicht mehr um. Umbenennen geht weiter in den Details der Verbindung und unter Clients.
- **README**: Die Voraussetzung steht wieder im Schnellstart: Home Assistant OS.

### English

- **Overview**: The clients on a connection's card no longer have a pencil, so the line stays in one
  piece. Renaming is still available in the connection's details and under Clients.
- **README**: The quick start names the requirement again: Home Assistant OS.

## 1.5.0 - 2026-11-08

Modbus-Register direkt als Entitäten in Home Assistant, Schreibrechte je Client, Geräteprofile,
ein Stromzyklus für hängende Geräte, Clients sperren und benennen, EnOcean-Sender mit Namen.

- **Modbus, Register als Entitäten**: Die App liest Register selbst und bietet sie über MQTT als
  Sensoren an, ohne YAML. Anlegen unter Register lesen → Werte dekodieren oder als Zeilen im
  Formular, höchstens 50, standardmäßig alle 30 Sekunden. Beim Mithören am RS485-Bus kommen die
  Werte aus dem Gehörten, es wird nichts gesendet.
- **Modbus, Register je Client**: Eine Zeile je Client legt fest, welche Register er schreiben
  darf, statt der allgemeinen Register. „Zugriff prüfen“ nennt die Zeile, die gilt.
- **Modbus, Geräteprofile**: Startwerte für SolarEdge, Huawei SUN2000, Fronius, SMA, Kostal
  Plenticore, Sungrow und Victron GX; erkennt der Bus-Scan den Hersteller, bietet er dessen Zeiten
  an.
- **Stromzyklus**: Ein Schalter in Home Assistant kann ein hängendes Gerät 5 Sekunden vom Strom
  trennen: von Hand, als Button in Home Assistant und einmal, wenn drei automatische Neustarts
  nicht geholfen haben.
- **Clients sperren**: Ein Rechner lässt sich von allen Verbindungen aussperren und wieder
  freigeben. Bei Modbus und EnOcean steht in seiner Zeile, wie oft er abgewiesen wurde.
- **Clients benennen**: Neue, bekannte und blockierte Rechner stehen in einer Liste mit Status und
  „zuletzt gesehen“; ein Klick öffnet den Namen. In den Client-Listen einer Verbindung geht das mit dem Stift. Dieser Rechner heißt von
  selbst Home Assistant, Adressen im Supervisor-Netz App. Nicht verbundene Rechner lassen sich aus
  der Liste entfernen. Viele neue Rechner auf einmal ergeben eine gemeinsame Benachrichtigung.
- **EnOcean-Sender**: eigene Namen für alle Gateways, gemeinsam gespeichert und nicht in der
  Diagnose, dazu die Liste als CSV-Datei.
- **EnOcean-Ersatz-Gateway**: Prüfintervall, Fehlversuche bis zum Umschalten und die stabile
  Laufzeit vor der Rückkehr lassen sich je Gateway einstellen.
- **Zigbee-Stick**: eine eigene Vorlage (115200 Baud, ein Client, nur Home Assistant und Apps).

### English

Modbus registers directly as entities in Home Assistant, write rights per client, device profiles,
a power cycle for devices that hang, blocking and naming clients, EnOcean senders with names.

- **Modbus, registers as entities**: The app reads registers itself and offers them as sensors
  over MQTT, without YAML. Added under Read registers → Decode values or as lines in the form, at
  most 50, every 30 seconds by default. When listening on an RS485 bus, the values come from what
  was heard and nothing is sent.
- **Modbus, registers per client**: One line per client sets which registers it may write, instead
  of the general registers. "Check access" names the line that applies.
- **Modbus, device profiles**: Starting values for SolarEdge, Huawei SUN2000, Fronius, SMA, Kostal
  Plenticore, Sungrow and Victron GX; when the bus scan recognizes the vendor, it offers its timing.
- **Power cycle**: A switch in Home Assistant can cut the power of a hanging device for 5 seconds:
  by hand, as a button in Home Assistant and once when three automatic restarts did not help.
- **Blocking clients**: A computer can be kept out of every connection and released again. With
  Modbus and EnOcean its line shows how often it was refused.
- **Naming clients**: New, known and blocked computers are in one list with their state and "last
  seen"; a click opens the name. In the lists of clients of a connection the pencil does the same. This host is called Home Assistant by
  itself, addresses in the Supervisor network App. Computers that are not connected can be removed
  from the list. Many new computers at once get one notification together.
- **EnOcean senders**: names of your own for all gateways, saved together and left out of the
  diagnostics, and the list as a CSV file.
- **EnOcean fallback gateway**: the check interval, the failed reads before switching and the
  steady time before going back can be set per gateway.
- **Zigbee stick**: a template of its own (115200 baud, one client, Home Assistant and apps only).

## 1.4.1 - 2026-11-08

Das Panel ist auf dem Handy gut bedienbar, dazu viele Korrekturen bei EnOcean, Modbus und MQTT.

- **Handy**: die Bereiche als Leiste unten, keine Seite ist mehr breiter als der Bildschirm, die
  Speichern-Leiste des Formulars ist einzeilig, Links und kleine Knöpfe sind leichter zu treffen.
- **Mitschnitt**: die Bytes dekodierter Telegramme schrumpfen nicht mehr auf ein Zeichen pro
  Zeile; die Datei einer laufenden Aufzeichnung lässt sich nicht mehr löschen.
- **EnOcean**: immer nur ein Befehl mit erwarteter Antwort, eine verspätete Antwort geht an
  niemanden; ESP2 prüft die Prüfsumme jedes Telegramms; bei einer Aufzeichnung mit Sperre kein
  falscher Wechsel auf das Ersatz-Gateway.
- **Modbus**: ein nicht erreichbares Gerät weist Clients sofort ab, verschwundene Clients geben
  ihren Platz frei, jedes Schreiben leert den Cache, ungültige Lesewünsche beim Mithören am Bus
  bekommen eine Fehlerantwort.
- **MQTT und Benachrichtigungen**: ein Fehler eines Buttons beendet MQTT nicht mehr, alte
  Entitäten verschwinden zuverlässig, erledigte Meldungen werden auch nach einem Neustart entfernt.
- **App**: eine ungültige Konfiguration startet nicht mehr leer, was gültig ist, bleibt erhalten;
  fällt ein Hintergrundteil aus, startet die App neu; der Import zeigt Konflikte innerhalb einer
  Datei in der Vorschau.

### English

The panel works well on phones, plus many fixes for EnOcean, Modbus and MQTT.

- **Phones**: the sections as a bar at the bottom, no page is wider than the screen, the save bar
  of the form is one row, links and small buttons are easier to hit.
- **Trace**: the bytes of decoded frames no longer collapse to one character per line; the file
  of a running capture can no longer be deleted.
- **EnOcean**: one command expecting an answer at a time, a late answer goes to nobody; ESP2
  checks the checksum of every frame; a capture with a lock no longer switches to the fallback
  gateway by mistake.
- **Modbus**: a device that cannot be reached turns clients away at once, clients that vanished
  free their place, every write empties the cache, invalid reads when listening on a bus get an
  error answer.
- **MQTT and notifications**: an error from a button no longer ends MQTT, old entities go away
  reliably, notifications that are resolved are dismissed after a restart too.
- **App**: an invalid configuration no longer starts empty, what is valid is kept; when a
  background part fails, the app starts again; the import shows conflicts within a file in the
  preview.

## 1.4.0 - 2026-11-05

Eine hängende Verbindung lässt sich neu starten, auch mit einem USB-Reset des Adapters, von Hand,
aus Home Assistant oder automatisch.

- **Neu starten**: neue Karte auf der Seite einer Verbindung. Das Gerät (bei Modbus und EnOcean
  der Proxy) wird geschlossen und neu geöffnet, die Clients verbinden sich wieder, auch mit
  „Gerät offen halten“.
- **USB-Reset**: für USB-Adapter dieses Rechners; setzt den Adapter zurück wie Ab- und
  Anstecken, ohne den Strom zu unterbrechen, und wartet, bis er wieder da ist.
- **Automatisch**: nach den Minuten ohne Daten wahlweise neu starten oder USB-Reset und neu
  starten (serielle Verbindungen), höchstens dreimal in Folge, bis wieder Daten kommen.
- **Home Assistant**: Buttons „Verbindung neu starten“ und „USB-Reset“ je Verbindung.
- Jeder Neustart steht in der Historie, ein fehlgeschlagener USB-Reset als Warnung.

### English

A hanging connection can be restarted, also with a USB reset of its adapter: by hand, from
Home Assistant or automatically.

- **Restart**: a new card on a connection's page. The device (for Modbus and EnOcean the proxy)
  is closed and opened again, the clients connect again, also with "Keep the device open".
- **USB reset**: for USB adapters of this host; resets the adapter like unplugging and plugging
  it in again, without cutting the power, and waits until it is back.
- **Automatically**: after the minutes without data, restart or USB reset and restart (serial
  connections), at most three times in a row until data comes again.
- **Home Assistant**: buttons "Restart connection" and "USB reset" per connection.
- Every restart is in the history, a failed USB reset as a warning.

## 1.3.0 - 2026-11-02

Das Panel lässt sich anpassen: drei Farbschemata, hell oder dunkel, und drei Schriftgrößen.

- **Farbschema**: Ozean (wie bisher), Wald oder Graphit, jeweils hell und dunkel.
- **Hell oder dunkel**: wie Home Assistant (wie bisher), immer hell oder immer dunkel.
- **Schriftgröße**: Klein (12 px), Normal (14 px) oder Groß (16 px); alle Texte wachsen mit,
  Abstände bleiben gleich.
- Einzustellen unter Einstellungen → Hilfe und Info; gilt nur für diesen Browser und sofort.
- Der gedämpfte Text im Schema Ozean ist etwas heller.

### English

The panel can be adjusted: three colour schemes, light or dark, and three text sizes.

- **Colour scheme**: Ocean (as before), Forest or Graphite, each light and dark.
- **Light or dark**: as Home Assistant (as before), always light or always dark.
- **Text size**: Small (12 px), Normal (14 px) or Large (16 px); all texts scale with it,
  spacing stays the same.
- Set under Settings → Help and info; applies to this browser only, and at once.
- The muted text in the Ocean scheme is a little lighter.

## 1.2.2 - 2026-11-02

Die EnOcean-Eltako-Integration kommt wieder an den Statusport, auch über IPv6.

- **EnOcean, Statusport**: Home Assistant wurde mit 403 abgewiesen. Es läuft im Host-Netzwerk und
  kann von einer anderen Adresse des Rechners kommen als der, an die es sich verbindet. Jede Adresse
  des Rechners zählt jetzt als dieser Rechner (Statusport, EnOcean- und Modbus-Proxy,
  Modbus-Schreibsperre).
- **Apps über IPv6**: Das IPv6-Netz des Supervisors (fd0c:ac1e:2100::/48) zählt wie 172.30.32.0/23
  zu den Apps (Statusport, „Home Assistant und Apps“, ser2net).
- **Abweisung am Statusport**: Die Antwort 403 nennt den Grund; das Log nennt dazu den Host-Header.

### English

The EnOcean Eltako integration reaches the status port again, over IPv6 too.

- **EnOcean, status port**: Home Assistant was refused with 403. It runs in the host network and
  may come from another address of the host than the one it connects to. Every address of the
  host now counts as this host (status port, EnOcean and Modbus proxy, Modbus write lock).
- **Apps over IPv6**: The Supervisor's IPv6 network (fd0c:ac1e:2100::/48) counts as the apps,
  like 172.30.32.0/23 (status port, "Home Assistant and apps", ser2net).
- **Refusal at the status port**: The 403 answer gives the reason; the log adds the Host header.

## 1.2.1 - 2026-11-02

Der Statusport für die EnOcean-Eltako-Integration sagt, warum er eine Anfrage nicht beantwortet,
statt die Verbindung zurückzusetzen.

- **EnOcean, Statusport**: Eine abgewiesene Anfrage bekam einen Verbindungsabbruch („Connection
  reset by peer“), weil die App die Verbindung schloss, bevor sie die Anfrage gelesen hatte. Jetzt
  liest sie die Anfrage und antwortet mit 403; schlägt der Status selbst fehl, mit 500.
- **Log**: Jede Abweisung und jeder Fehler am Statusport steht im Log der App, mit Adresse und Port
  des Clients, der Adresse, an der er ankam, und dem Grund (nicht erlaubt, Zeitlimit, Anfrage
  abgebrochen oder zu lang, Fehler beim Status mit Traceback).

### English

The status port for the EnOcean Eltako integration says why it does not answer a request instead
of resetting the connection.

- **EnOcean, status port**: A refused request got "Connection reset by peer", because the app
  closed the connection before reading the request. It now reads the request and answers 403; if
  the status itself fails, 500.
- **Log**: Every refusal and failure at the status port is in the app's log, with the client's
  address and port, the address it arrived at, and the reason (not allowed, timeout, request cut
  off or too long, status failure with traceback).

## 1.2.0 - 2026-11-02

Vor dem Speichern sehen, was eine Änderung bewirkt, und mit einem Schritt zurück, wenn sie etwas
kaputt gemacht hat; prüfen, wer auf ein Modbus-Gerät schreiben darf; sichere Vorgaben, wo eine
Verbindung ohne das Formular entsteht; eine robustere Weboberfläche.

### Neu

- **Was Speichern bewirkt**: Das Formular einer Verbindung und die Rückfragen vor einer Änderung der
  Netzwerk-Einstellung oder des Heimnetzes, einem Import und dem Wiederherstellen einer Version oder
  Sicherung nennen die laufenden Verbindungen, die neu aufgebaut oder beendet werden, und wie viele
  Clients sich neu verbinden müssen.
- **Stand davor wiederherstellen**: Arbeitet nach einer Änderung eine Verbindung nicht mehr, die
  vorher lief, sagen das die Übersicht und die Seite der Verbindung und bieten die Konfiguration von
  vor der Änderung an.
- **Modbus, Zugriff prüfen** (Werkzeuge): ob ein Client an einer Adresse sich verbinden, lesen und
  ein Register schreiben darf und welche Regel entscheidet – mit denselben Prüfungen wie der Proxy,
  ohne etwas zu senden.
- **Modbus, wer wirklich schreiben darf** auf der Seite der Verbindung: jeder Client, der sich
  verbinden darf, die eingetragenen, niemand, wenn keiner eingetragen ist, die erlaubten Register
  und die Regel einer Verbindung, an die Units weitergehen.

### Geändert

- **Neue Modbus-Verbindungen ohne das Formular** (API, Skripte) lassen nur Home Assistant und die
  Apps schreiben, wie das Formular schon immer. Verbindungen, die gespeichert wurden, bevor es den
  Schreibzugriff gab, behalten „Alle“.
- **Ein Z-Wave-Stick ohne das Formular** lässt ebenfalls nur Home Assistant und die Apps verbinden.
- **Hostnamen**: Ein Name, der sich nicht auflösen lässt, oder ein Gerät, das nicht rechtzeitig
  erreicht wird, steht in Worten da („Hostname … nicht gefunden (DNS)“, „… in … s nicht erreicht“)
  statt im Text des Systems oder als „keine Antwort“.
- **EnOcean**: Die Einstellungen sagen, wenn der Statusport für die EnOcean-Eltako-Integration nicht
  geöffnet werden konnte, warum, und dass die App es erneut versucht.
- **Mitschnitte** werden in Blöcken heruntergeladen statt ganz in den Speicher gelesen; die
  Oberfläche bleibt während eines großen Downloads bedienbar.
- **Statusabfrage**: immer nur eine zur Zeit, mit Zeitlimit; Anfragen stauen sich nicht mehr,
  während die App beschäftigt ist, und eine ältere Antwort überschreibt nie eine neuere.
- **Auswahlgruppen** (Netzwerk, MQTT-Broker, ser2net-Quelle, Import-Art) lassen sich mit den
  Pfeiltasten bedienen.
- **Neue Screenshots** in den READMEs.

### Behoben

- **Einstellungen**: Wer die Seite mit noch nicht gespeicherten Änderungen verlässt, wird vorher
  gefragt, wie im Formular einer Verbindung (vorher waren sie weg).
- **Volle Platte**: Eine Konfiguration, die nicht gespeichert werden kann, ändert nichts, und die
  Seite sagt warum (vorher „interner Fehler“). Kann nur die Konfig-Historie sie nicht behalten, gilt
  die gespeicherte Änderung trotzdem.
- **Import**: Eine ser2net.yaml mit einem Steuerzeichen wird mit einer Meldung abgelehnt statt mit
  einem Fehler.
- **Weboberfläche**: Eine Verbindung, die ihre Anfrage oder deren Inhalt nicht rechtzeitig schickt,
  wird geschlossen.

### Tests und Werkzeuge

- Zufällige und kaputte Eingaben für alle Parser und die laufenden Proxys, kaputte Uploads und
  Sicherungen.
- `tools/soak_test.py` mit Grenzwerten für Antwortzeiten, Speicher und Wiederanlauf, mit
  Geräteausfällen und langsamen Lesern; `tools/soak_enocean.py` für ein Gateway und sein
  Ersatz-Gateway.
- `tests/HARDWARE.md`: die Prüfungen, die echte Geräte unter Home Assistant OS brauchen.

### English

See before saving what a change does, and get back in one step when it broke something; check who
may write to a Modbus device; safer defaults where a connection is made without the form; a more
robust web interface.

#### New

- **What saving does**: the connection form, and the questions before a change of the network
  setting or the home networks, an import or restoring a version or backup, name the running
  connections that are set up again or stop and how many clients have to connect again.
- **Restore the version before**: when a connection that worked stops working after a change, the
  connections page and its own page say so and offer the configuration before the change.
- **Modbus, check access** (Tools): whether a client at an address may connect, read and write a
  register, and which rule decides – by the same checks the proxy makes, without sending.
- **Modbus, who may really write** on the connection's page: every client that may connect, the
  listed ones, nobody when none is listed, the allowed registers, and the rule of a connection that
  units are sent on to.

#### Changed

- **New Modbus connections made without the form** (API, scripts) let only Home Assistant and the
  apps write, as the form always did. Connections saved before write access existed keep "all".
- **A Z-Wave stick made without the form** also lets only Home Assistant and the apps connect.
- **Host names**: a name that cannot be looked up, or a device not reached in time, is said in words
  ("host name … not found (DNS)", "… not reached within … s") instead of the system's text or "no
  answer".
- **EnOcean**: the settings say when the status port for the EnOcean Eltako integration could not be
  opened, why, and that the app tries again.
- **Trace files** are downloaded in blocks instead of read whole into memory; the interface stays
  usable during a large download.
- **Status requests**: one at a time with a time limit; requests no longer pile up while the app is
  busy, and an older answer never overwrites a newer one.
- **Choice groups** (network, MQTT broker, ser2net source, import mode) work with arrow keys.
- **New screenshots** in the READMEs.

#### Fixed

- **Settings**: leaving the page with changes not saved yet asks first, as the connection form does
  (before, they were gone).
- **Full disk**: a configuration that cannot be saved changes nothing and the page says why (before,
  "internal error"). When only the configuration history cannot keep it, the saved change counts all
  the same.
- **Import**: a ser2net.yaml with a control character is refused with a message instead of an error.
- **Web interface**: a connection that does not send its request or body in time is closed.

#### Tests and tools

- Random and broken input for all parsers and the running proxies, broken uploads and backups.
- `tools/soak_test.py` with limits for answer times, memory and recovery, device outages and slow
  readers; `tools/soak_enocean.py` for a gateway and its fallback.
- `tests/HARDWARE.md`: the checks that need real devices on Home Assistant OS.

## 1.1.0 - 2026-11-01

Viele neue Werkzeuge: Modbus-Werte dekodiert und Geräte erkannt, Namen für Clients und ein Hinweis
auf neue, Wartung mit einem Rechner allein, Zählerstände für das Energie-Dashboard, ein RS485-Bus,
der mitgehört wird, ohne zu senden, mehrere Modbus-Geräte hinter einem Port. Die App kommt jetzt als
fertiges Image.

- **Fertiges Image**: Home Assistant lädt die App herunter, statt gensio und ser2net auf dem Gerät
  zu bauen. Aufgezeichnete Mitschnitte und EnOcean-Aufzeichnungen bleiben aus den Sicherungen von
  Home Assistant heraus.

**Modbus**

- **Werte dekodieren** unter „Register lesen“: 16-, 32- und 64-Bit-Ganzzahlen, Gleitkommazahlen oder
  Text, mit Register- und Byte-Reihenfolge („swap“) und einem Faktor, wie die Modbus-Integration von
  Home Assistant sie liest, und der passende Sensor zum Kopieren in die `configuration.yaml`.
- **Bus scannen** fragt jede gefundene Unit, wer sie ist (Geräte-Identifikation, SunSpec), und zeigt
  Hersteller, Modell, Version und eine passende Integration.
- **Hinweise zum Timing** auf der Statuskarte: ein längeres oder kürzeres Timeout, ein
  Zwischenspeicher, was eine lange Warteschlange oder viele Fehlerantworten bedeuten.
- **Erlaubte Register beim Schreiben**: Adressen und Bereiche; ein Schreibzugriff außerhalb wird mit
  Fehler 02 abgewiesen. Die Karte **Schreibzugriffe** listet die letzten Schreibzugriffe der Clients
  und ihr Ergebnis.
- **RS485 mithören**: eine neue Art Verbindung für einen Bus, der schon einen Master hat (z. B. ein
  Wechselrichter und sein Zähler). Die App hört nur mit, sendet nie und beantwortet Lesezugriffe aus
  dem Gehörten.
- **Units anderer Verbindungen**: ein Port für mehrere Geräte; eine hier gefragte Unit beantwortet
  das Gerät einer anderen Modbus-Verbindung.

**EnOcean**

- **Sender**: jede gehörte Sender-ID mit Art, Anzahl, zuletzt gehört, Repeatern, Empfang (ESP3) und
  welches Gateway sie gehört hat; neue Sender markiert, IDs zum Kopieren.

**Serielle Geräte**

- **Zählerstände als Entitäten**: Bezug und Einspeisung in kWh und Leistung in W über MQTT, für das
  Energie-Dashboard, gelesen aus dem, was der Zähler ohnehin sendet (an mit den eHZ-Vorlagen).
- **Eine serielle Brücke im Netz** (ESPHome Stream Server, Tasmota-Lesekopf, USR-TCP232) als Quelle
  einer Verbindung, geteilt wie ein Gerät dieses Rechners.
- **Gerät umgesteckt**: Fehlt ein Gerät und steckt sein Adapter an anderer Stelle, bietet die Seite
  an, ihn zu übernehmen.

**Alle Verbindungen**

- **Clients**: Namen für Client-Adressen (**Einstellungen → Clients**), angezeigt in den Listen und
  Ereignissen. Ein Rechner, der sich zum ersten Mal verbindet, wird gemeldet, bis er als bekannt
  markiert oder benannt ist.
- **Clients trennen**: ein Knopf auf der Seite der Verbindung und ein MQTT-Knopf in Home Assistant;
  ein EnOcean-Gateway mit Ersatz bekommt auch Knöpfe zum Umschalten.
- **Wartung**: Ein Rechner darf eine Verbindung eine Weile allein nutzen, z. B. für ein Service-Tool
  oder ein Firmware-Update; die anderen bleiben draußen, bis die Zeit um ist.
- **Als Testfall**: die letzten Frames einer Verbindung als Datei für ein Issue, EnOcean-IDs
  ersetzt.

### English

Many new tools: Modbus values decoded and devices identified, names for clients and a word on
new ones, maintenance with one computer alone, meter readings for the Energy dashboard, an RS485
bus listened to without sending, several Modbus devices behind one port. The app now comes as a
prebuilt image.

- **Prebuilt image**: Home Assistant downloads the app instead of building gensio and ser2net on
  the device. Recorded traces and EnOcean captures are left out of Home Assistant's backups.

**Modbus**

- **Decode values** under "Read registers": 16, 32 and 64 bit integers, floats or text, with
  the register and byte order ("swap") and a factor as Home Assistant's Modbus integration reads
  them, and the matching sensor to copy into `configuration.yaml`.
- **Bus scan** asks each unit found who it is (device identification, SunSpec) and shows
  vendor, model, version and a fitting integration.
- **Timing tips** on the status card: a longer or shorter timeout, a cache, what a long queue or
  many exceptions mean.
- **Registers that may be written**: addresses and ranges; a write outside is refused with
  exception 02. The card **Writes** lists the clients' last writes and their result.
- **Listen on RS485**: a new kind of connection for a bus that has a master already (e.g. an
  inverter and its meter). The app only listens, never sends, and answers reads from what it
  heard.
- **Units of other connections**: one port for several devices; a unit asked here is answered
  by another Modbus connection's device.

**EnOcean**

- **Senders**: every sender ID heard with kind, count, last seen, repeaters, reception (ESP3)
  and which gateway heard it; new senders marked, IDs to copy.

**Serial devices**

- **Meter readings as entities**: import and export in kWh and power in W over MQTT, for the
  Energy dashboard, read from what the meter sends anyway (on with the eHZ templates).
- **A serial bridge in the network** (ESPHome stream server, Tasmota reading head, USR-TCP232)
  as the source of a connection, shared like a device of this host.
- **Device moved**: when a device is missing and its adapter is plugged in elsewhere, the page
  offers to take it over.

**All connections**

- **Clients**: names for client addresses (**Settings → Clients**), shown in the lists and
  events. A computer that connects for the first time is reported until it is marked as known
  or named.
- **Disconnect clients**: a button on the connection's page and an MQTT button in Home
  Assistant; an EnOcean gateway with a fallback also gets buttons to switch.
- **Maintenance**: one computer may use a connection alone for a while, e.g. for a service tool
  or a firmware update; the others are kept out until the time is up.
- **As a test case**: a connection's last frames as a file for an issue, EnOcean IDs replaced.

## 1.0.1 - 2026-10-23

Home Assistant kommt an einem EnOcean-Gateway, das auf Home Assistant und die Apps beschränkt ist,
wieder hinein.

- **EnOcean, „Nur Home Assistant und Apps“**: Home Assistant wurde an einem erkannten Gateway und am
  Statusport abgewiesen, sodass die EnOcean-Eltako-Integration die Base-ID nicht lesen konnte und
  danach fragte. Sie verbindet sich mit dem Hostnamen der App, also der LAN-Adresse des Rechners,
  und kommt damit von dort, nicht von 127.0.0.1. Eine Verbindung vom Rechner zu seiner eigenen
  Adresse zählt jetzt als 127.0.0.1 (EnOcean- und Modbus-Proxy, Statusport, Modbus-Schreibsperre).

### English

Home Assistant is let in at an EnOcean gateway limited to Home Assistant and the apps again.

- **EnOcean, "Only Home Assistant and apps"**: Home Assistant was refused at a discovered
  gateway and at the status port, so the EnOcean Eltako integration could not read the base ID
  and asked for it. It connects to the app's host name, which is the host's LAN address, and so
  comes from there, not from 127.0.0.1. A connection from the host to its own address now counts
  as 127.0.0.1 (EnOcean and Modbus proxy, status port, Modbus write lock).

## 1.0.0 - 2026-10-23

EnOcean-Gateways nennen der EnOcean-Eltako-Integration ihr Modell.

- **Modell des EnOcean-Gateways**: Jedes Gateway hat ein Feld **Modell** (FAM-USB, FGW14-USB, FAM14,
  MGW-ETH, Symcon LAN, anderes ESP2- oder ESP3-Gateway), das mit der Erkennung an die
  EnOcean-Eltako-Integration geht (`model` neben Name, Port und Protokoll). Die Vorlage setzt es,
  und vorher gespeicherte Gateways nehmen es aus ihrer Vorlage; es muss zum Protokoll passen und
  darf leer bleiben, dann geht die Erkennung ohne.

### English

EnOcean gateways tell the EnOcean Eltako integration their model.

- **EnOcean gateway model**: each gateway has a field **Model** (FAM-USB, FGW14-USB, FAM14,
  MGW-ETH, Symcon LAN, other ESP2 or ESP3 gateway) that goes to the EnOcean Eltako integration
  with the discovery (`model` next to name, port and protocol). The template sets it, and
  gateways saved before take it from their template; it must fit the protocol and may stay
  empty, then the discovery goes without it.

## 0.4.0 - 2026-10-22

EnOcean-Gateways bekommen ein Ersatz-Gateway: ein zweites Gateway mit derselben Base-ID springt ein,
wenn eines ausfällt. Ebenfalls neu: die Base-ID mit den Werkzeugen setzen.

- **EnOcean-Ersatz-Gateway**: Ein zweites Gateway mit derselben Base-ID springt ein, wenn eines
  ausfällt. Es wird als normale Verbindung angelegt und dann im Formular des ersten Gateways
  gewählt; solange es Ersatz ist, hat es keinen eigenen Port und wird der Integration nicht
  angeboten. Das erste Gateway liest alle 10 s seine Base-ID; ist es weg oder bleibt stumm, laufen
  seine Programme ohne neue Verbindung über den Ersatz weiter und kommen nach 60 s stabilem Lauf
  oder von Hand zurück. Wahlweise werden beide Gateways gehört, Duplikate und das eigene Senden
  verworfen. Die Karte „Gateways“ zeigt beide und schaltet von Hand um; „Ersatz wird Haupt-Gateway“
  tauscht die Hardware, wenn ein Gateway kaputt ist. Benachrichtigungen, MQTT-Entitäten (Ersatz
  aktiv, aktives Gateway, Ersatz bereit) und der Status für die Integration sagen, welches Gateway
  in Gebrauch ist.
- **Verbindung speichern**: Das Formular fragt nicht mehr, ob die gerade gespeicherten Änderungen
  verworfen werden sollen.

- **EnOcean-Base-ID**: Die Werkzeuge setzen eine neue Base-ID, und ESP3-Gateways zeigen, wie viele
  Änderungen noch übrig sind (das Gateway erlaubt nur wenige).

- **Dokumentation**: Das MQTT-Basis-Topic ist `device_proxy` (dort stand noch `ser2net`); die vier
  Netzwerk-Stufen mit ihren heutigen Namen, auch „Home Assistant und Apps“; die
  Modbus-Schreibsperre, wie sie jetzt arbeitet; Menüpfade, wie die Oberfläche sie nennt; EnOcean in
  der Einleitung; der eigene MQTT-Broker; was eine eigene ser2net.yaml darf. Die README beschreibt
  die heutige Vorgabe für erlaubte Clients und wo die Adresse einer Verbindung steht.

- **Nicht gespeicherte Änderungen**: Wer das Formular einer Verbindung über den Kopf, die
  Brotkrumen, einen Chip oder den Zurück-Knopf des Browsers verlässt, wird jetzt vorher gefragt, wie
  bei Abbrechen (vorher waren die Änderungen weg).
- **Nach einem Neustart der App**: Eine offene Seite zeigt wieder neue Ereignisse und Live-Daten
  (sie standen still, bis die neuen Zähler die alten überholten).
- **Speichern, während die App nicht erreichbar ist**: zeigt „keine Verbindung zur App“ statt
  nichts.
- **Einstellungen nach einer Wiederherstellung**: Das Formular zeigt die wiederhergestellten Werte
  (Speichern konnte die alten zurückschreiben), und die Konfig-Historie füllt sich nach dem
  Wiederherstellen einer Sicherung wieder.
- **Details einer Verbindung**: Ergebnisse des Scans oder der Baudraten-Erkennung bleiben nicht mehr
  bei der nächsten Verbindung stehen, und Live-Daten erscheinen auf einer langsamen Verbindung nicht
  mehr doppelt.
- **Dialoge**: Tab bleibt im Dialog, und der Fokus geht dorthin zurück, wo er war. Der Stufen-Filter
  der Ereignisse hat eine deutsche Beschriftung; keine ID kommt auf der Einstellungsseite doppelt
  vor.

- **Texte**: Die Netzwerk-Stufe „Home Assistant und Apps“ erschien als `listen_apps`, Modbus-Fehler
  8 als `ex_8`; die englische Import-Vorschau sagte „höchstens 5 Clients“. Fehler des
  Modbus-Schreibwerkzeugs, einer Wiederherstellung und des MQTT-Tests sind ins Deutsche übersetzt.
  Die Ereignisse „eigene ser2net.yaml nicht verwendbar“ und „Import fehlgeschlagen“ zeigen den Grund
  in beiden Sprachen (Englisch zeigte eine Python-Liste). 39 Texte, die nichts mehr nutzte, sind
  weg.

- **Modbus-Schreibsperre**: Ein Lesezugriff geht nur durch, wenn seine Anfrage genau die Länge
  dieses Lesezugriffs hat. Bei RTU und RTU über TCP gibt der Proxy die Bytes unverändert weiter,
  sodass ein hinter einem Lesezugriff versteckter Schreib-Frame das Gerät erreichte, obwohl
  Schreiben gesperrt war.
- **Modbus RTU**: Das Echo der Diagnose (Funktion 8) wird bis zu seinem Ende gelesen statt nach 8
  Bytes abgeschnitten. Mit „alten Client verdrängen“ kommt ein neuer Client nicht mehr neben einen,
  der gerade verdrängt wird.

- **EnOcean ESP3**: Müll, dessen erste Bytes wie ein langer Frame aussehen, hält nicht mehr jedes
  Telegramm zurück, bis so viele Bytes angekommen sind (Stunden); die Daten-CRC wird geprüft, Längen
  sind begrenzt, und ein unfertiger Frame wird nach 0,5 s aufgegeben.
- **Gesundheitsprüfung**: Sie verbindet sich nicht mehr als Client mit den EnOcean-Ports (bei einem
  erlaubten Client und „alten Client verdrängen“ drängte sie jede Minute die Integration hinaus und
  schrieb zwei Ereignisse pro Minute in die Historie). Die App schreibt dafür den Zustand der
  Gateways; hört die App damit auf, schlägt die Prüfung fehl, und der Supervisor startet die App
  neu.
- **Aufzeichnungen**: Eine, die sich nicht schreiben lässt (volle Platte, Ordner nicht
  beschreibbar), friert nicht mehr die Live-Ansicht und „letzte Daten“ jeder Verbindung ein und
  meldet für sie nicht mehr „keine Daten“.
- **Gateways im Netz** (EnOcean, Modbus TCP, RTU über TCP): TCP-Keepalive bemerkt nach etwa 90 s ein
  Gateway, das den Strom verliert, ohne die Verbindung zu schließen, und verbindet neu.
- **EnOcean-Statusport**: War er belegt (z. B. von der alten EnOcean-Proxy-App), wird er alle 30 s
  erneut versucht statt erst bei der nächsten Änderung.
- **Historie**: Eine volle Platte oder ein E/A-Fehler schiebt die Historie nicht mehr als beschädigt
  beiseite; das Ereignis wird protokolliert, aber nicht behalten.

- **Weitere ser2net-Optionen**: Nur harmlose werden übernommen (Puffergrößen, chardelay,
  sendon/closeon, signature, mDNS, …). `connback` kann über seinen gensio-String ein Programm
  starten und wird abgewiesen, ebenso Anmeldungen, LEDs und Werte, die eine Datei lesen (`*{…}`,
  `*(…)`), auch in banner, openstr und closestr. Ein Import oder eine Sicherung lässt sie mit einem
  Hinweis weg; eine gespeicherte Konfiguration verwirft sie beim Laden.
- **Import und eigene ser2net.yaml**: Das Lesen läuft neben den Proxys, statt sie anzuhalten, und
  ein Text ohne Doppelpunkte braucht zum Prüfen nicht mehr Minuten. Uploads sind auf 1 MB begrenzt.
- **API der Weboberfläche**: Inhalte in falscher Form (eine Liste statt eines Objekts, eine
  Sicherung mit kaputtem `config`) ergeben 400 statt 500; ein Modbus-Import mit `timeout: nan` nimmt
  die Vorgabe.
- **Aufzeichnungen**: Herunterladen oder Löschen folgt keinem symbolischen Link mehr aus dem
  Mitschnitt-Ordner hinaus.

- **Diagnose**: Benutzername und Passwort eines eigenen MQTT-Brokers standen noch in der
  `status.json` des ZIP (nur die `config.json` verbarg sie). Beide werden jetzt ersetzt.
- **MQTT-Passwort**: wird nicht mehr an den Browser geschickt (Status alle 2 s, Konfig-Historie).
  Das Formular zeigt Punkte für ein gesetztes Passwort; unverändert zurückgeschickt bleibt das
  gespeicherte, auch für „Testen“.
- **Einstellungen**: Eine Änderung der Einstellungen und das Speichern der eigenen ser2net.yaml zur
  selben Zeit machen sich nicht mehr gegenseitig rückgängig; die eigene Datei wird der Reihe nach
  mit anderen Änderungen geschrieben und auf die Platte gebracht.

- **Modbus- und EnOcean-Proxys**: Einer, der durch einen unerwarteten Fehler endet, startet nach 30
  s neu (vorher blieb sein Port bis zur nächsten Änderung oder einem Neustart der App zu). Ursachen,
  die ihn beendeten, werden jetzt abgefangen: ein USB-Adapter, der beim Öffnen gezogen wird, ein
  Hostname wie `a..b` (wird auch beim Speichern abgewiesen), eine volle Platte beim Aufzeichnen (nur
  die Aufzeichnung endet).
- **EnOcean**: Anhalten oder Neustarten eines Gateways hängt nicht mehr, wenn ein Client nicht mehr
  liest (ein schlafender PC); das Speichern hing damit. Ein Client, der schneller sendet als das
  Gateway, wird nicht mehr ohne Grenze gepuffert.
- **Werkzeuge**: Ein unerwarteter Fehler beendet einen Lauf als fehlgeschlagen, statt ihn „laufend“
  zu lassen und die Werkzeuge dieser Verbindung bis zu einem Neustart zu sperren (z. B.
  Baudraten-Erkennung an einem Gerät, das kein tty ist).

- **Verbindungen**: Die Karte zeigt die Adresse nicht mehr mit Kopierknopf (sie wird nur zum
  Einrichten gebraucht, und die Detailseite hat sie); stattdessen steht dort, wann zuletzt Daten
  kamen, z. B. „Letzte Daten vor 3 s“. Verbindungen, die nicht laufen, zeigen dort nichts, denn ihr
  Zustand sagt schon warum.
- **Erlaubte Clients**: Neue EnOcean-Gateways lassen das Feld leer und folgen damit der
  Netzwerk-Einstellung wie die anderen Arten (vorher waren sie auf Home Assistant und Apps
  beschränkt, und eo_man oder PCT14 im Heimnetz kamen ohne Änderung nicht hinein). Der Knopf „Nur
  Home Assistant und Apps“ bleibt für eine eigene Grenze. Der Z-Wave-Stick behält seine Vorgabe und
  sagt warum: Er nimmt Befehle an und hat keine Anmeldung. Bestehende Verbindungen behalten, was sie
  haben; ein Gateway mit Grenze zeigt einen Knopf „Der globalen Einstellung folgen“, der das Feld
  leert, und der Hinweis sagt das.
- **Auswahlkacheln** (Gateway-Vorlage, Art der Verbindung, Einstellungen): Alle Kacheln einer Gruppe
  sind gleich groß in einem gleichmäßigen Raster (sieben Vorlagen stehen vier und drei statt sechs
  und eins), und die gewählte ist markiert, ohne dass ihr Inhalt springt.
- **Letzte Ereignisse**: immer volle Breite, eine Zeile je Ereignis (Zeit, Stufen-Punkt, Text) in
  ausgerichteten Spalten statt der Zeit unter dem Text. Bei seriell und EnOcean ist auch die
  Verbindungskarte voll breit, wie bei Modbus.
- **In Home Assistant verwenden** (Modbus): zuerst eingeklappt wie die Werkzeuge und Adressen.
- **Adressen**: Die Karte heißt nur „Adressen“, ist zuerst eingeklappt wie die Werkzeuge (sie werden
  nur zum Einrichten gebraucht) und öffnet sich von selbst, wenn „Adressen zeigen“ in einem Hinweis
  zu ihr springt.
- **Aufklappbare Teile**: „Weitere Werkzeuge“, „So geht es mit PCT14“, das YAML für Home Assistant
  und „Welche Formate gehen?“ im Import bekommen dasselbe „›“ wie die in den Einstellungen; es dreht
  sich beim Öffnen.
- **Werkzeugkarte**: zeigt, dass sie sich einklappen lässt: „Anzeigen“ oder „Einklappen“ mit Pfeil
  rechts, und der Kopf wird hervorgehoben, wenn der Zeiger darüber ist. Bei allen Arten (seriell,
  Modbus, EnOcean) ist die Karte zuerst eingeklappt, zeigt im Titel, was sie enthält, merkt sich je
  Art, ob sie offen war, und öffnet sich von selbst, wenn ein Ergebnis da ist.
- **Modbus-Werkzeuge**: Lesen, Schreiben und Scannen teilen sich ein Raster, sodass die Felder in
  vier Spalten stehen und die Knöpfe rechts in einer Spalte (der Start-Knopf des Scans hat keine
  eigene Zeile mehr).
- **Modbus-Werkzeuge**: neu „Register schreiben“ (Funktionen 5, 6, 15, 16) neben „Register lesen“.
  Es fragt vorher nach, liest den Wert danach zurück, sagt, ob er passt, und schreibt ein Ereignis
  ins Protokoll. Bei Verbindungen mit Schreibzugriff „Niemand“ bleibt es gesperrt. Der Lesen-Knopf
  ist in die Zeile der Felder gewandert.
- **Detailseite (EnOcean)**: Die sechs Zähler der Gateway-Karte stehen in einem gleichmäßigen Raster
  von drei mal zwei, wie die Kacheln der anderen Karten (Wert oben, Beschriftung darunter);
  Kartenköpfe stehen in einem Paar auf einer Linie; die Client-Tabelle passt in ihre Karte, statt
  abgeschnitten zu werden.
- **EnOcean-Werkzeuge**: Das Werkzeug „Aufzeichnung“ heißt „Telegramme aufzeichnen“ (englisch
  „Record frames (PCT14)“) und sagt, wie es sich vom ständigen Mitschnitt unterscheidet, damit die
  beiden nicht verwechselt werden.
- **Einstellungen**: Der Abschnitt zum Protokoll sagt, dass es das technische Protokoll zur
  Fehlersuche ist, wo es in Home Assistant steht und wie es sich vom Reiter Ereignisse
  unterscheidet.
- **Einstellungen**: Die drei Felder unter MQTT „Erweitert“ stehen oben auf einer Linie; der Hinweis
  des ersten schiebt die anderen nicht mehr nach unten.
- **Live-Daten** (Detailseite und Mitschnitt): Zeit und Richtung nehmen nur den Platz, den sie
  brauchen; bei Modbus und EnOcean teilen sich Beschreibung und Bytes eine Zeile und brechen nur um,
  wenn die Karte schmal ist, statt alle 16 Bytes.
- **Detailseite**: keine Seitenspalte mehr; Karten stehen in Paaren zweier gleicher Spalten, in der
  Reihenfolge Zustand, Messwerte, Live-Daten, Werkzeuge, zuletzt Adressen und Einstellungen (der
  Hinweis „kein Programm verbunden“ verweist auf die Adressen). Dieselbe Reihenfolge für seriell,
  Modbus und EnOcean.
- **Bearbeiten-Seite**: Die Vorschau einer Modbus- oder EnOcean-Verbindung steht unter dem Formular,
  über der Speicherleiste; ihr Ablauf liest sich von links nach rechts.
- **Import**: Der Import der Optionen der EnOcean-Proxy-App ist weg (diese App war nie in Gebrauch):
  kein „Aus der EnOcean-Proxy-App holen“, keine `import/enocean_proxy.yaml`.

### English

EnOcean gateways get a fallback: a second gateway with the same base ID stands in when one
fails. Also new: setting the base ID with the tools.

- **EnOcean fallback gateway**: a second gateway with the same base ID stands in when one fails.
  It is set up as a normal connection and then picked in the first gateway's form; while it is
  the fallback it has no port of its own and is not offered to the integration. The first
  gateway reads its base ID every 10 s; when it is gone or stays silent, its programs go on
  through the fallback without reconnecting, and come back after 60 s of steady running or by
  hand. Optionally both gateways are heard, duplicates and the own sending dropped. The card
  "Gateways" shows both and switches by hand; "Fallback becomes the main gateway" swaps the
  hardware when a gateway broke. Notifications, MQTT entities (fallback active, active gateway,
  fallback ready) and the status for the integration tell which gateway is in use.
- **Saving a connection**: the form no longer asks whether to discard the changes just saved.

- **EnOcean base ID**: the tools set a new base ID, and ESP3 gateways show how many changes are
  left (the gateway allows only a few).

- **Documentation**: the MQTT base topic is `device_proxy` (it still said `ser2net`); the four
  network levels with their current names, including "Home Assistant and apps"; the Modbus write
  lock as it works now; menu paths as the interface names them; EnOcean in the introduction; the
  own MQTT broker; what an own ser2net.yaml may do. The README describes today's default for
  allowed clients and where the address of a connection is shown.

- **Unsaved changes**: leaving the connection form by the header, the breadcrumb, a chip or the
  browser's back button now asks first, like Cancel did (before, the changes were gone).
- **After an app restart**: an open page shows new events and live data again (they stood still until
  the new counters passed the old ones).
- **Saving while the app is not reachable**: shows "no connection to the app" instead of nothing.
- **Settings after a restore**: the form shows the restored values (Save could put the old ones back),
  and the configuration history fills again after restoring a backup.
- **Connection details**: results of the scan or the baud rate detection no longer carry over to the
  next connection, and live data no longer shows twice on a slow connection.
- **Dialogs**: Tab stays inside, and the focus goes back to where it was. The level filter of the
  events has a German label; no id is used twice on the settings page.

- **Texts**: the network level "Home Assistant and apps" showed as `listen_apps`, Modbus exception 8 as
  `ex_8`; the English import preview said "höchstens 5 Clients". Errors of the Modbus write tool,
  of a restore and of the MQTT test are translated to German. The events "own ser2net.yaml cannot
  be used" and "import failed" show the reason in both languages (English showed a Python list).
  39 texts nothing used any more are gone.

- **Modbus write lock**: a read only passes when its request has exactly the length of that read. On
  RTU and RTU over TCP the proxy passes the bytes on as they are, so a write frame hidden behind a
  read reached the device although writing was locked.
- **Modbus RTU**: the echo of diagnostics (function 8) is read to its end instead of being cut after
  8 bytes. With "kick old user" a new client no longer gets in beside one that is still being
  pushed out.

- **EnOcean ESP3**: garbage whose first bytes look like a long frame no longer holds back every
  telegram until that many bytes have arrived (hours); the data CRC is checked, lengths are capped,
  and an unfinished frame is given up after 0.5 s.
- **Health check**: it no longer connects to the EnOcean ports as a client (with one client allowed
  and "kick old user" it pushed out the integration every minute, and it put two events a minute in
  the history). The app writes the gateways' state for it instead; when the app stops writing it,
  the check fails and the Supervisor restarts the app.
- **Recordings**: one that cannot be written (full disk, folder not writable) no longer freezes the
  live view and "last data" of every connection, nor reports "no data" for them.
- **Network gateways** (EnOcean, Modbus TCP, RTU over TCP): TCP keepalive notices a gateway that
  loses power without closing the connection, after about 90 s, and connects again.
- **EnOcean status port**: when it was taken (e.g. by the old EnOcean Proxy app), it is tried again
  every 30 s instead of only at the next change.
- **History**: a full disk or an I/O error no longer moves the history aside as damaged; the event is
  logged but not kept.

- **Further ser2net options**: only harmless ones are taken (buffer sizes, chardelay, sendon/closeon,
  signature, mDNS, …). `connback` can start a program through its gensio string and is refused, as
  are logins, LEDs and values that read a file (`*{…}`, `*(…)`), also in banner, openstr and closestr.
  An import or backup leaves them out with a note; a saved configuration drops them when loading.
- **Import and own ser2net.yaml**: reading runs beside the proxies instead of stopping them, and a
  text without colons no longer takes minutes to check. Uploads are limited to 1 MB.
- **Web interface API**: bodies of the wrong shape (a list instead of an object, a backup with a
  broken `config`) give 400 instead of 500; a Modbus import with `timeout: nan` uses the default.
- **Recordings**: a download or delete no longer follows a symlink out of the trace folder.

- **Diagnostics**: the user name and password of an own MQTT broker were still in `status.json` of
  the ZIP (only `config.json` hid them). Both are replaced now.
- **MQTT password**: no longer sent to the browser (status every 2 s, configuration history). The form
  shows dots for a set password; sent back unchanged, the saved one stays, also for "Test".
- **Settings**: a settings change and saving the own ser2net.yaml at the same time no longer undo
  each other; the own file is written in turn with other changes and synced to disk.

- **Modbus and EnOcean proxies**: one that ends by an unexpected error starts again after 30 s
  (before, its port stayed closed until the next change or a restart of the app). Causes that ended
  it are caught now: a USB adapter pulled while it is opened, a host name like `a..b` (refused when
  saving as well), a full disk while capturing (only the capture ends).
- **EnOcean**: stopping or restarting a gateway no longer hangs when a client has stopped reading
  (a sleeping PC); saving hung with it. A client that sends faster than the gateway is no longer
  buffered without limit.
- **Tools**: an unexpected error ends a run as failed instead of leaving it "running" and locking the
  tools of that connection until a restart (e.g. baud rate detection on a device that is no tty).

- **Connections**: the card no longer shows the address with a copy button (it is only needed for
  setup, and the detail page has it); instead it says when data last arrived, e.g. "Last data 3 s ago".
  Connections that are not running show nothing there, since their state already says why.
- **Allowed clients**: new EnOcean gateways leave the field empty, so they follow the network setting
  like the other kinds (before, they were limited to Home Assistant and apps and eo_man or PCT14 in
  the home network could not connect without a change). The button "Only Home Assistant and apps"
  stays for an own limit. The Z-Wave stick keeps its preset and says why: it takes commands and has
  no login. Existing connections keep what they have; a gateway with a limit shows a button
  "Follow the global setting" that empties the field, and the note says so.
- **Choice tiles** (gateway template, connection kind, settings): all tiles of a group are the same
  size in an even grid (seven templates sit four and three instead of six and one), and the chosen
  one is marked without its content moving.
- **Recent events**: always the full width, one line per event (time, level dot, text) in aligned
  columns instead of the time under the text. On serial and EnOcean the connection card is full
  width as well, as on Modbus.
- **Use in Home Assistant** (Modbus): folded at first like the tools and addresses.
- **Addresses**: the card is just called "Addresses", is folded at first like the tools (they are only
  needed for setup) and opens by itself when "Show addresses" in a hint jumps to it.
- **Foldable parts**: "More tools", "How it works with PCT14", the Home Assistant YAML and "Which formats
  work?" in the import get the same "›" marker as the ones in the settings; it turns when opened.
- **Tools card**: shows it can be folded: "Show" or "Collapse" with a chevron on the right, and the
  header is highlighted when the pointer is over it. On all kinds (serial, Modbus, EnOcean) the card is folded at first, shows in its
  title what it holds, remembers per kind whether it was opened, and opens by itself when a result
  is there.
- **Modbus tools**: read, write and scan share one grid, so the fields line up in four columns and the
  buttons sit in one column on the right (the scan's Start button no longer has a row of its own).
- **Modbus tools**: new "Write registers" (functions 5, 6, 15, 16) next to "Read registers". It asks
  for confirmation first, reads the value back afterwards and says whether it matches, and writes an
  event to the log. It stays locked on connections whose write access is "Nobody". The Read button
  moved into the row of fields.
- **Detail page (EnOcean)**: the six counters of the gateway card sit in an even grid of three by two,
  like the tiles of the other cards (value on top, label below); card headers line up across a
  pair; the clients table fits its card instead of being cut off.
- **EnOcean tools**: the "Capture" tool is called "Record frames (PCT14)" (German: "Telegramme
  aufzeichnen") and says how it differs from the permanent trace, so the two are not mixed up.
- **Settings**: the log section says it is the technical log for troubleshooting, where to find it in
  Home Assistant and how it differs from the Events tab.
- **Settings**: the three fields under MQTT "Advanced" line up at the top; the hint of the first no
  longer pushes the others down.
- **Live data** (detail page and recording): time and direction take only the room they need; on
  Modbus and EnOcean the description and the bytes share a line and wrap only when the card is
  narrow, instead of breaking every 16 bytes.
- **Detail page**: no side column any more; cards sit in pairs of two equal columns, in the order
  state, measurements, live data, tools, then addresses and settings last (the "no program
  connected" hint links to the addresses). Same order for serial, Modbus and EnOcean.
- **Edit page**: the preview of a Modbus or EnOcean connection moves below the form, above the
  save bar; its flow reads left to right.
- **Import**: the import of the EnOcean Proxy app's options is gone (that app was never in use):
  no "Fetch from the EnOcean Proxy app", no `import/enocean_proxy.yaml`.

## 0.3.1 - 2026-10-22

Ein Durchgang über jede Seite der Oberfläche.

- **Verbindungen**: Jede Karte zeigt ihre Clients als kleinen Füllbalken und die Datenrate als Kurve
  der letzten Minute; eine Karte mit Problem zeigt ihren Zustand einmal (Streifen und Chip) mit
  einem ruhigen Satz darunter; der Kopierknopf ist ein Symbol, der Aufzeichnungs-Chip steht in der
  Chip-Zeile.
- **Detailseite**: Die Adressen zum Kopieren haben eine eigene Karte oben in der Seitenspalte;
  Live-Daten nutzen dieselben Richtungswörter und Zeilen zu sechzehn Bytes wie die Mitschnitt-Seite,
  lassen sich auf eine lebende Zeile einklappen und brechen lange Zeilen um; eine an 127.x gebundene
  Verbindung sagt, dass sie nur von diesem Rechner erreichbar ist; der Kopf trägt einen kurzen
  Aufzeichnungs-Chip, der zum Mitschnitt führt; Seitenkarten mit kurzen Werkzeugknöpfen, einem
  beschrifteten Datendiagramm und „Letzte Ereignisse“ dieser Verbindung.
- **Modbus-Details**: eine Statuskarte (Anfragen pro Sekunde, Probleme nur als Chips) statt sechs
  Zählern; Clients und Units in einer Karte mit Tooltips an den Spaltenköpfen („Fehlerantworten“
  statt „Exceptions“); die Verbindungskarte wandert in die Seitenspalte; die Formulare zum Lesen und
  Scannen passen in eine Zeile; „In Home Assistant verwenden“ beginnt mit der Integration des Geräts
  in der Oberfläche und behält das YAML als Rückfall; „1 Wiederholung“ statt „1 Wiederholungen“; die
  Live-Ansicht nennt den Client einmal, wenn nur einer fragt.
- **Bearbeiten-Seiten**: Serielle Verbindungen bekommen eine Karte Grundlagen mit dem Namen wie die
  anderen Arten; eine mitlaufende Leiste Löschen / Abbrechen / Speichern, ein Chip „Nicht
  gespeichert“, eine Rückfrage bei Abbrechen und eine Warnung, wenn der Tab mit Änderungen
  geschlossen wird; Vorlagen bei einer bestehenden Verbindung eingeklappt und eine Rückfrage, bevor
  eine Felder überschreibt; Pfeile an eingeklappten Karten; die Vorschau bleibt im Blick und sagt,
  wer sich verbinden darf; Antwort-Timeout und Wiederholungen bei Modbus stehen beim Gerät, die
  erweiterten Optionen sind gruppiert (Takt, Clients, Probe, Aufzeichnung), und die Sendepause von
  EnOcean steht beim Gateway. Eine Bind-Adresse 127.x sagt jetzt, dass nur dieser Rechner sich
  verbinden darf, und eine Warnung erscheint, wenn erlaubte Clients Netze nennen, die diese Adresse
  nie bedienen kann.
- **Import**: Inhalt ohne jede Verbindung bleibt mit einem Fehler im ersten Schritt; der erste
  Schritt nennt jedes Ding einmal und klappt die Liste der Formate weg; ein Konflikt-Chip je Inhaber
  und ein Hinweis je Gerät; Pfade brechen nicht mehr in kurzen Namen um; auf dem Handy bleiben die
  Schritte in einer Zeile, und jeder Eintrag ist eine Karte; die Fußzeile mit „Übernehmen“ bleibt am
  Ende einer langen Liste stehen.
- **Ereignisse und Mitschnitt**: Live und Historie teilen eine Filterleiste und ein Zeilenformat;
  Verbindungen als Chip-Leiste auf der Mitschnitt-Seite; Hex und ASCII in Zeilen zu sechzehn Bytes
  bei jeder Breite; Richtungs-Abzeichen nutzen die Wörter des Aufzeichnungsschalters.
- **Einstellungen**: Der Speichern-Knopf jeder Karte ist erst nach einer Änderung aktiv und sagt
  „Nicht gespeichert“; die Navigation an der Seite markiert den sichtbaren Abschnitt; die Karte für
  eine eigene ser2net.yaml bietet „Aus den Formularen“ und „Eigene Datei“, den Editor auf Wunsch und
  eine Prüfung beim Tippen, mit gesperrtem Speichern bei Fehlern.
- **Lesbarkeit**: Hinweise, Feldbeschriftungen und Tabellenköpfe sind 13 px, der graue Text hat in
  hell und dunkel mehr Kontrast.

### English

A pass over every page of the interface.

- **Connections**: each card shows its clients as a small fill bar and the data rate as a curve of
  the last minute; a problem card shows its state once (stripe and chip) with a calm sentence
  below; the copy button is an icon, the recording chip sits in the chip row.
- **Detail page**: the addresses to copy have their own card at the top of the side column; live data
  uses the same direction words and sixteen-byte lines as the trace page, can be collapsed to one
  living line and wraps long lines; a connection bound to 127.x says it is reachable from this
  host only; the header carries a short recording chip that links to the trace; side cards with
  short tool buttons, a labelled data chart and "Recent events" for this connection.
- **Modbus details**: one status card (requests per second, problems only as chips) instead of six
  counters; clients and units in one card with tooltips on the column headers ("error replies"
  instead of "exceptions"); the Connection card moves to the side column; the read and scan forms
  fit one row; "Use in Home Assistant" leads with the device's integration in the interface and
  keeps the YAML as the fallback; "1 retry" instead of "1 retries"; the live view names the client
  once when only one asks.
- **Edit pages**: serial connections get a Basics card with the name like the other kinds; a
  sticky Delete / Cancel / Save bar, a "Not saved" chip, a confirmation on Cancel and a warning
  when the tab is closed with changes; templates folded for an existing connection and a
  confirmation before one overwrites fields; arrows on folded cards; the preview stays in view and
  says who may connect; Modbus answer timeout and retries sit with the device, the advanced options
  are grouped (pacing, clients, probe, recording) and the EnOcean send pause sits with the
  gateway. A bind address of 127.x now says only this host may connect, and a warning appears
  when allowed clients name networks that address can never serve.
- **Import**: content without any connection stays at the first step with an error; the first step
  names each thing once and folds the list of formats away; one conflict chip per holder and one
  note per device; paths no longer break inside short names; on a phone the steps stay in one row
  and each entry is a card; the footer with "Take over" stays at the bottom of a long list.
- **Events and trace**: Live and History share one filter bar and one row format; connections as a
  chip bar on the trace page; hex and ASCII in sixteen-byte lines at every width; direction
  badges use the words of the recording switch.
- **Settings**: every card's Save button is active only after a change and says "Not saved"; the
  side navigation marks the section in view; the card for an own ser2net.yaml offers "From the
  forms" and "Own file", the editor on demand and an automatic check while typing, with saving
  locked on errors.
- **Readability**: hints, field labels and table headers are 13 px, the grey text has more
  contrast in light and dark.

## 0.3.0 - 2026-10-22

- **Heimnetz**: Wer als „LAN“ zählt, ist jetzt eine Liste unter **Einstellungen → Netzwerk →
  Erlaubte Netze**. Das eigene Netz des Rechners ist vorgegeben, weitere Netze lassen sich
  hinzufügen; Home Assistant und die Apps sind immer erlaubt. Bestehende Installationen behalten die
  privaten Bereiche.
- **Sichern und Wiederherstellen**: **Einstellungen → Sichern und Übertragen** speichert alle
  Verbindungen (seriell, Modbus, EnOcean) und die Einstellungen als eine Datei und stellt sie nach
  einer Vorschau und einer Bestätigung wieder her. Import und ser2net-Export sind dorthin umgezogen;
  der Export sagt, dass er nur die seriellen Verbindungen enthält.
- **Übersicht der Verbindungen**: ein Statusband statt vier Kacheln, Probleme zuerst mit eigenem
  Filter und einem nächsten Schritt, kompakte Karten, die als Ganzes die Details öffnen.
- **Seiten einer Verbindung**: Gerät vor Name, serielle Schnittstelle und Netzzugang als eigene
  Karten, Block für Meldungen, „Aktiv“ als eigener Schalter, Löschen abgesetzt; die Detailseite
  zeigt eine Verbindungskarte mit den echten Netzen und der Erreichbarkeit je Ziel.
- **Ereignisse**: Protokoll nach Zeit sortiert mit Tageszeilen, Stufen-Knöpfe mit Anzahl,
  Verbindungsfehler in einfachen Worten, Namen verweisen auf die Verbindung, beschriftete Balken der
  Historie.
- **Mitschnitt**: ein Aufzeichnungsschalter für die gewählte Verbindung in einfachen Worten,
  Live-Ansicht mit Zeilenzahl, Leeren und Zeiten in Millisekunden, aufgezeichnete Dateien nennen
  ihre Verbindung, Pfad zum Kopieren.
- **Import**: Konflikte in einfachen Worten, alle auswählen, die Verbindungen, die „Alle ersetzen“
  entfernt, werden genannt, und der letzte Schritt zählt hinzugefügte, ersetzte und übersprungene
  Verbindungen.
- Rückfragen vor dem Ausschalten einer Verbindung mit Clients, bevor ein Import Verbindungen
  ersetzt, und vor dem Löschen.
- Schmale Bildschirme: Chips im Kopf brechen um, die Navigation passt in eine Zeile, die
  Mitschnitt-Seite wählt die Verbindung aus einer Liste. Meldungen der API und der Werkzeuge
  erscheinen auch auf Deutsch.

### English

- **Home network**: who counts as "LAN" is now a list under **Settings → Network → Allowed
  networks**. The host's own network is predefined, further networks can be added; Home
  Assistant and the apps are always allowed. Existing installations keep the private ranges.
- **Backup and restore**: **Settings → Back up and transfer** saves all connections (serial,
  Modbus, EnOcean) and the settings as one file and restores them after a preview and a
  confirmation. Import and the ser2net export moved there; the export says it holds the serial
  connections only.
- **Connections overview**: one status band instead of four tiles, problems first with their own
  filter and a next step, compact cards that open the details as a whole.
- **Connection pages**: device before name, serial interface and network access as separate
  cards, alerts block, "Active" as its own switch, delete set apart; the detail page shows one
  connection card with the real networks and reachability per target.
- **Events**: log sorted by time with day rows, level buttons with counts, plain-language
  connection errors, names link to the connection, labelled history bars.
- **Trace**: one recording switch for the chosen connection in plain words, live view with line
  count, clear and millisecond times, recorded files name their connection, copyable path.
- **Import**: collisions in plain words, select all, the connections "Replace all" removes are
  named, and the finished step counts added, replaced and skipped connections.
- Confirmations before switching off a connection with clients, before an import replaces
  connections and before deleting.
- Narrow screens: header chips wrap, the navigation fits one row, the trace page picks the
  connection from a list. Messages of the API and the tools are shown in German as well.

## 0.2.1 - 2026-10-22

- **Aussehen**: ein mitlaufender Kopf mit Reitern als Pillen, weichere Karten mit leichtem Schatten,
  Verbindungskarten mit farbigem Statusrand und einem Symbol für die Art; hell und dunkel.
- **EnOcean-Detailseite**: Funkbelegung und Nachlieferungspuffer sind zwei große Karten oben mit
  großer Zahl, einem Balken (Marke bei 80 % für die Funkbelegung), dem ältesten gepufferten
  Telegramm und einem Status in einfachen Worten (unter der Grenze, fast an der Grenze, sammelt,
  Programm verbunden, voll, aus).
- **EnOcean**: Die Base-ID wird nach jedem Verbinden einmal vom Gateway gelesen (nichts geht über
  die Luft), sodass sie in der Liste und auf der Detailseite steht, ohne dass jemand fragt.
- Einstellungen: Das Menü links bleibt beim Scrollen im Blick (wenn es neben dem Inhalt steht).
- Adressen: Eine Adresse, die nicht erreichbar ist, sagt jetzt warum (an diesen Rechner gebunden,
  erlaubte Clients, Netzwerk-Einstellung) und zeigt die Adresse.
- Doku: Der Reiter **Konfiguration** der App im Supervisor ist absichtlich leer; DOCS und beide
  READMEs verweisen jetzt auf den Eintrag **Device Proxy** in der Seitenleiste, wo alles
  eingerichtet wird.

### English

- **Looks**: a sticky header with pill tabs, softer cards with a light shadow, connection cards
  with a coloured status edge and a kind icon; light and dark.
- **EnOcean detail page**: air time and replay buffer are two big cards at the top with a large
  number, a bar (80 % mark for the air time), the oldest buffered telegram and a status in plain
  words (below the limit, nearly at the limit, collecting, program connected, full, off).
- **EnOcean**: the base ID is read from the gateway once after each connection (nothing
  goes over the air), so it shows in the list and on the detail page without anyone asking.
- Settings: the menu on the left stays in view while scrolling (when it sits beside the content).
- Addresses: an address that cannot be reached now says why (bound to this host, allowed clients,
  network setting) and shows the address.
- Docs: the app's **Configuration** tab in the Supervisor is empty on purpose; DOCS and both
  READMEs now point to the sidebar entry **Device Proxy**, where everything is set up.

## 0.2.0 - 2026-10-21

- **EnOcean-Gateways** (übernommen aus der EnOcean-Proxy-App, die diese ersetzt)
  - Eine dritte Art Verbindung: ein FAM-USB-, FAM14-, FGW14-USB-, USB300/TCM310-, MGW-ETH- oder
    Symcon-LAN-Gateway für mehrere Programme, über USB oder TCP, ESP2 oder ESP3, mit Vorlagen.
  - Ganze Frames der Reihe nach mit Pause, die Antworten des Gateways an das Programm, das gefragt
    hat, kein Echo an die anderen, langsame Programme getrennt, verbindet sich von selbst neu.
  - Nachliefern für die EnOcean-Eltako-Integration (`EOPX REPLAY`, mit Empfangszeiten), wahlweise
    über einen Neustart der App auf der Platte behalten.
  - Erkennung durch die Integration und ein nur lesbarer Status für ihre Gateway-Karten (Port 9199,
    nur Home Assistant und die Apps); Einstellungen unter **Einstellungen → EnOcean**.
  - Detailseite: Probleme in einfachen Worten, Live-Frames mit Sender und Art (Suche, Richtung,
    Filter nach Sender, Kopieren, ins Senden übernehmen), Funkbelegung gegen die 1-%-Grenze, Zähler,
    Nachlieferungspuffer, Base-ID; Werkzeuge: Gateway-Test, einen geprüften Frame senden (Prüfsumme
    ergänzt oder korrigiert), Aufzeichnungen als JSON-Zeilen mit einer Sperre für PCT14.
  - Neue Gateways nehmen nur Home Assistant und die Apps an (die App läuft im Netz des Rechners).
  - Benachrichtigung bei 80 % Funkbelegung; MQTT-Entitäten: erreichbar, Telegramme, Funkbelegung.
  - Umzug: Die Optionen der EnOcean-Proxy-App werden aus Home Assistant geholt, eingefügt oder in
    `import/enocean_proxy.yaml` gelegt.
- **Für alle Verbindungen**: Filter-Chips nach Art über der Liste; eine laufende Aufzeichnung
  erscheint im Kopf.
- Behoben: Eine Modbus-TCP-Verbindung, die ohne Gerätefeld gespeichert war, ließ sich nicht laden.

### English

- **EnOcean gateways** (taken over from the EnOcean Proxy app, which this replaces)
  - A third kind of connection: one FAM-USB, FAM14, FGW14-USB, USB300/TCM310, MGW-ETH or
    Symcon LAN gateway for several programs, over USB or TCP, ESP2 or ESP3, with templates.
  - Whole frames in turn with a pause, the gateway's answers to the program that asked, no
    echo to the others, slow programs disconnected, reconnecting by itself.
  - Replay for the EnOcean Eltako integration (`EOPX REPLAY`, with reception times),
    optionally kept on disk over a restart of the app.
  - Discovery by the integration and a read-only status for its gateway cards (port 9199,
    Home Assistant and the apps only); settings under **Settings → EnOcean**.
  - Detail page: issues in plain words, live frames with sender and kind (search,
    direction, filter by sender, copy, take over into send), air time against the 1 % limit,
    counters, replay buffer, base ID; tools: gateway test, sending a checked frame (checksum
    added or fixed), captures as JSON lines with a lock for PCT14.
  - New gateways take Home Assistant and the apps only (the app runs in the host network).
  - Notification at 80 % air time; MQTT entities: reachable, telegrams, air time.
  - Moving: the EnOcean Proxy app's options are fetched from Home Assistant, pasted or put
    into `import/enocean_proxy.yaml`.
- **For all connections**: filter chips by kind above the list; a running capture shows in
  the header.
- Fixed: a Modbus TCP connection saved without a device field could not be loaded.

## 0.1.0 - 2026-10-21

Erste Version.

- **Verbindungen**
  - Eingerichtet in einer Weboberfläche in der Seitenleiste: Geräteliste mit stabilen Namen,
    Vorlagen, alle wichtigen ser2net-Optionen, Live-Vorschau der `ser2net.yaml`.
  - Speichern baut nur die geänderte Verbindung neu auf; die anderen behalten ihre Clients.
  - Clients standardmäßig nur aus privaten Netzen; ein Gerät offen halten; Clients, die nicht mehr
    lesen, werden gemeldet.
- **Modbus-Proxy**
  - Ein Modbus-Gerät für mehrere Modbus-TCP-Clients: Modbus TCP, Modbus RTU an einem RS485-Adapter,
    RTU über TCP; Anfragen der Reihe nach, jede Antwort an den Client, der gefragt hat.
  - Timeout, Wiederholungen, Pause nach dem Verbinden und zwischen Anfragen;
    Gateway-Fehlerantworten, wenn das Gerät nicht antwortet.
  - Status mit Anfragen, unbeantworteten Anfragen und Antwortzeit, auch je Unit-ID; dekodierte
    Anfragen und Antworten im Mitschnitt.
  - Schreibzugriff je Verbindung, ein Zwischenspeicher für Lesezugriffe, Clients der Reihe nach, bis
    zu 4 Verbindungen zu einem Gerät im Netz, Unit-IDs umgeschrieben, ein wahlweiser
    Probe-Lesezugriff.
  - Werkzeuge: Register lesen, den Bus nach Unit-IDs scannen.
- **Import und Export**
  - ser2net 4 `ser2net.yaml` (Version 1 und 2), ser2net 3 `ser2net.conf` und die Optionen von
    ha-modbusproxy (oder eine modbus-proxy-Datei), mit Vorschau; Export als `ser2net.yaml`; oder die
    eigene Datei unverändert verwenden.
- **Status und Diagnose**
  - Gerät, Clients, Datenrate, letzte Daten, Leitungsfehler vom Treiber, FTDI-Latenz.
  - Live-Daten und Mitschnitte, ohne einen Client-Platz zu belegen; Aufzeichnen ohne Trennen.
  - Werkzeuge für Stromzähler: SML (mit CRC-Prüfung) und D0, Baudraten-Erkennung.
  - Ereignisse und 30-Tage-Historie, Konfig-Historie mit Wiederherstellen, Diagnose-ZIP.
- **Home Assistant**
  - Benachrichtigungen (wahlweise an einen Notify-Dienst).
  - Entitäten über MQTT-Discovery, ein Gerät je Verbindung mit Schalter (bei Modbus: erreichbar,
    Anfragen, unbeantwortete Anfragen, Antwortzeit).
- **Unter der Haube**
  - ser2net 4.6.8 und gensio 3.0.4 aus ihren Releases gebaut; Admin-Schnittstelle über einen Socket
    in der App; Neustarts, Gesundheitsprüfung und Sicherungen abgedeckt.
  - Deutsch und Englisch, hell und dunkel, Handy-Breite.

### English

First version.

- **Connections**
  - Set up in a web interface in the sidebar: device list with stable names, templates,
    all important ser2net options, live `ser2net.yaml` preview.
  - Saving rebuilds only the changed connection; the others keep their clients.
  - Clients from private networks only by default; keep a device open; clients that stop
    reading are reported.
- **Modbus proxy**
  - A Modbus device for several Modbus TCP clients: Modbus TCP, Modbus RTU on an RS485
    adapter, RTU over TCP; requests in turn, each answer to the client that asked.
  - Timeout, retries, pause after connecting and between requests; gateway exceptions when
    the device does not answer.
  - Status with requests, unanswered requests and answer time, also per unit id; decoded
    requests and answers in the trace.
  - Write access per connection, a cache for reads, clients taking turns, up to 4
    connections to a network device, unit ids rewritten, an optional probe read.
  - Tools: read registers, scan the bus for unit ids.

- **Import and export**
  - ser2net 4 `ser2net.yaml` (version 1 and 2), ser2net 3 `ser2net.conf` and the options of
    ha-modbusproxy (or a modbus-proxy file), with a preview; export as `ser2net.yaml`; or use
    your own file as it is.
- **Status and diagnosis**
  - Device, clients, data rate, last data, line errors from the driver, FTDI latency.
  - Live data and traces without taking a client place; recording without disconnecting.
  - Smart meter tools: SML (with CRC check) and D0, baud rate detection.
  - Events and 30-day history, configuration history with restore, diagnostics ZIP.
- **Home Assistant**
  - Notifications (optionally to a notify service).
  - Entities over MQTT discovery, one device per connection with a switch (for Modbus:
    reachable, requests, unanswered requests, answer time).
- **Under the hood**
  - ser2net 4.6.8 and gensio 3.0.4 built from their releases; admin interface on a socket
    inside the app; restarts, health check and backups handled.
  - German and English, light and dark, phone width.
