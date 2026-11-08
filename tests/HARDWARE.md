# Testmatrix für echte Hardware

Was sich nur auf Home Assistant OS mit echten Geräten prüfen lässt. Alles andere prüfen
`pytest`, `tests/integration/check_ser2net.py` (ser2net im Image, in der CI) und die
Dauerläufe `tools/soak_test.py` (Modbus) und `tools/soak_enocean.py` (EnOcean mit Ersatz).
Die Spalte **Automatisch** sagt, was davon schon ohne Hardware abgedeckt ist; geprüft wird
hier, was dort nicht nachgestellt werden kann: echte Treiber, USB, der Supervisor, Ingress
und die Geräte selbst.

## Vor dem Durchgang festhalten

| | |
| --- | --- |
| Datum | |
| App-Version (Panel oben links) | |
| ser2net-Version | |
| Home Assistant OS / Core | |
| Hardware (Raspberry Pi, NUC, VM …) | |
| Geräte und Adapter | |

Nach jedem Fall: Panel → Ereignisse und das App-Protokoll (Einstellungen → Apps → Device
Proxy → Protokoll) auf Fehler ansehen. Ein Fall gilt nur als bestanden, wenn dort nichts
Unerwartetes steht.

## Seriell und USB (ser2net)

| # | Fall | Schritte | Erwartet | Automatisch | Ergebnis |
| --- | --- | --- | --- | --- | --- |
| S1 | USB-Stick anlegen | Verbindung hinzufügen, Gerät aus der Liste wählen (Z-Wave- oder Zigbee-Stick) | Vorlage passt, Name ohne USB-Rohtext, Gerät unter `/dev/serial/by-id/…`, Status „Läuft“ | Namen und Vorlagen: pytest | |
| S2 | Client verbindet | Z-Wave JS bzw. die Integration auf `tcp://<host>:<port>` stellen | Client erscheint in der Detailansicht, Daten fließen (Live-Ansicht) | ser2net im Image: CI | |
| S3 | Stromzähler (SML/D0) | Lesekopf anlegen, Vorlage eHZ, „Werkzeuge → Zähler prüfen“ | Protokoll erkannt, gültige Telegramme, Zählerstand stimmt mit dem Display | Zähler-Analyse: pytest | |
| S4 | Baudrate suchen | Werkzeuge → Baudrate erkennen bei einem Zähler mit unbekannter Rate | Richtige Rate unter den Kandidaten oben | Erkennung: pytest | |
| S5 | Gerät abziehen | Stick im laufenden Betrieb abziehen, 1 min warten | Status „Gerät fehlt“, Ereignis, Meldung in HA nach der eingestellten Wartezeit | Zustand: pytest | |
| S6 | Wieder anstecken, gleicher Port | Stick wieder einstecken | Verbindung läuft von selbst wieder, Clients verbinden neu | | |
| S7 | Anderer USB-Port | Stick an einem anderen Port einstecken | Hinweis „Adapter steckt offenbar an einer anderen Stelle“, „Übernehmen“ setzt den Pfad | `test_moved.py` | |
| S8 | Zwei gleiche Adapter | Zwei Adapter ohne Seriennummer | Beide werden unterschieden (by-path), keiner wird verwechselt | | |
| S9 | Wartung | Detailansicht → Wartung, eigenen Rechner eintragen, mit einem Tool verbinden | Nur dieser Rechner kommt hinein, nach Ablauf wieder alle | pytest | |
| S10 | Mitschnitt groß | Mitschnitt „beide Richtungen“, Dateigröße 50 MB, ein paar Stunden laufen lassen, dann herunterladen | Download vollständig, Panel bleibt währenddessen bedienbar | Download in Blöcken: pytest | |

## Modbus

| # | Fall | Schritte | Erwartet | Automatisch | Ergebnis |
| --- | --- | --- | --- | --- | --- |
| M1 | Modbus TCP | Wechselrichter oder Wärmepumpe über TCP anlegen, HA-Modbus-Integration auf den Proxy stellen | Werte in HA stimmen, Antwortzeit plausibel | `soak_test.py tcp` | |
| M2 | Mehrere Clients | Zusätzlich evcc oder ein zweites Tool auf denselben Port | Beide bekommen ihre Antworten, keine Timeouts beim Gerät | `soak_test.py` | |
| M3 | Modbus RTU (RS485-Adapter) | USB-RS485-Adapter, Link „Modbus RTU“, Baudrate des Geräts | Lesen klappt, keine CRC-Fehler in der Live-Ansicht | `soak_test.py rtu` (Pseudo-Terminal, Linux) | |
| M4 | Mithören am Bus | Link „RS485 mithören“ an einem Bus mit eigenem Master | Register erscheinen, Clients lesen sie, Schreiben wird abgelehnt (Ausnahme 01) | `test_listen.py` | |
| M5 | Schreibschutz | Neue Verbindung: Schreiben aus HA klappt, von einem anderen Rechner im LAN nicht | Werkzeuge → „Zugriff prüfen“ sagt dasselbe; Ereignis „Schreiben abgelehnt“ | pytest | |
| M6 | Gerät aus | Gerät vom Strom oder Netz trennen, nach 1 min wieder an | „Nicht erreichbar“, Clients bekommen sofort Ausnahme 0B/0A, danach läuft es von selbst wieder | `soak_test.py` (Ausfälle) | |
| M7 | Hostname statt IP | Gerät per Name eintragen, Namen absichtlich falsch schreiben | „Hostname … nicht gefunden (DNS)“, Proxy läuft weiter | pytest | |
| M8 | Bus-Scan | Werkzeuge → Bus scannen | Gefundene Units, bei SunSpec-Geräten Hersteller und Modell | pytest | |

## EnOcean

| # | Fall | Schritte | Erwartet | Automatisch | Ergebnis |
| --- | --- | --- | --- | --- | --- |
| E1 | Ersatz-Gateway | Zweites Gateway mit gleicher Base-ID als Ersatz eintragen | „Ersatz bereit“, Base-ID „gleich“ | `test_fallback.py` | |
| E2 | Umschalten bei Ausfall | Haupt-Gateway abziehen bzw. vom Netz nehmen | Nach kurzer Zeit „läuft über Ersatz“, Schalter in HA reagieren weiter | `soak_enocean.py` | |
| E3 | Zurückschalten | Haupt-Gateway wieder anschließen | Nach der eingestellten stabilen Laufzeit wieder Haupt-Gateway, keine doppelten Telegramme in HA | `soak_enocean.py` | |
| E4 | Nachliefern | App neu starten, während Sensoren senden | Integration bekommt die Telegramme aus der Zwischenzeit | (bereits auf HA OS getestet) | |
| E5 | Funkbelegung | Viele Befehle in kurzer Zeit (Szene mit vielen Aktoren) | Funkbelegung steigt, Warnung bei 80 % des 1-%-Limits | pytest | |

## App, Supervisor, Ingress

| # | Fall | Schritte | Erwartet | Automatisch | Ergebnis |
| --- | --- | --- | --- | --- | --- |
| A1 | App-Neustart | App neu starten | Alle Verbindungen laufen wieder, Clients verbinden neu, Ereignis-Historie bleibt | | |
| A2 | HA-Neustart / Host-Neustart | Home Assistant bzw. den Host neu starten | Wie A1, USB-Geräte werden wiedergefunden | | |
| A3 | Update der App | Update auf die neue Version einspielen | Konfiguration bleibt, keine Verbindung ändert ihr Verhalten (Modbus-Schreibzugriff alter Verbindungen bleibt „Alle“) | Migration: pytest | |
| A4 | Backup und Wiederherstellung | Backup in den Einstellungen herunterladen, eine Verbindung ändern, Backup zurückspielen | Rückfrage nennt, was neu aufgebaut wird; danach alter Stand | pytest | |
| A5 | HA-Backup | Vollständiges HA-Backup und Wiederherstellung | Konfiguration da; Mitschnitte und EnOcean-Aufzeichnungen sind bewusst nicht im Backup | | |
| A6 | „Stand davor wiederherstellen“ | Bei einer laufenden Verbindung absichtlich einen falschen Port/Host speichern | Hinweis in Übersicht und Detailansicht, ein Klick stellt her, Verbindung läuft wieder | pytest, Dev-Server | |
| A7 | Ingress lange offen | Panel 1 h offen lassen, dann weiterbedienen | Keine Fehlermeldung, Daten aktuell (HTTP-Zeitlimit 60 s schließt nur leere Verbindungen) | pytest | |
| A8 | Ingress und großer Download | Während eines großen Mitschnitt-Downloads Panel in zweitem Tab bedienen | Beide Tabs bleiben bedienbar | pytest | |
| A9 | Netzwerk-Einstellung | Erreichbarkeit von „Heimnetz“ auf „Nur Home Assistant und Apps“ und zurück | Rückfrage nennt alle betroffenen Verbindungen; ein Rechner im LAN kommt danach nicht mehr bzw. wieder hinein | pytest | |
| A10 | Volle Platte | (nur wenn gefahrlos möglich) `/config` fast voll | Speichern sagt „nicht gespeichert“, Verbindungen laufen weiter, Mitschnitt pausiert mit Hinweis | pytest | |
| A11 | Handy | Panel in der HA-App auf dem Handy | Alle Seiten bedienbar, nichts läuft seitlich über | Browser 375 px | |
| A12 | Screenreader | VoiceOver oder TalkBack über Verbindungen, Bearbeiten, Einstellungen | Felder und Auswahlgruppen werden sinnvoll vorgelesen, Pfeiltasten wechseln die Auswahl | | |
