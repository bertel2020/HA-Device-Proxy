# Changelog (Deutsch)

> ### 🔌 Ein Gerät, viele Clients – und eine Person dahinter
>
> Device Proxy ist ein Hobbyprojekt und bleibt kostenlos. So kannst du helfen:
>
> - ⭐ **Stern auf GitHub**: So finden andere das Projekt leichter.
> - 🐞 **Fehler oder Idee melden**: als [Issue](https://github.com/bertel2020/HA-Device-Proxy/issues/new/choose), am besten mit dem Diagnose-Paket (Einstellungen → Hilfe und Info).
> - ☕ **Den Proxy am Laufen halten**: [Buy Me a Coffee](https://buymeacoffee.com/bertel2020) · [Ko-fi](https://ko-fi.com/bertel2020) · [PayPal](https://paypal.me/RobertoMartins)
>
> 🇬🇧 [English version](https://github.com/bertel2020/HA-Device-Proxy/blob/main/device_proxy/CHANGELOG.md)

## Unreleased

### Geändert

- **Oberfläche, Seitentitel:** etwas kleiner (24 statt 28 px); am Handy entfällt der kurze Text darunter (Verbindungen, Ereignisse, Mitschnitt), damit mehr Inhalt zu sehen ist.
- **Oberfläche, Kopfzeile:** Unter dem Namen steht jetzt „Läuft · App …“ statt „ser2net läuft“. Rot und mit Grund nur, wenn ser2net steht und serielle Verbindungen es brauchen; Probleme einzelner Verbindungen zählt weiter der Reiter „Verbindungen“. Die Versionen stehen im Tooltip.
- **Oberfläche, breite Bildschirme:** Die Seiten nutzen bis zu 1600 px statt 1200 px. Die Verbindungsliste zeigt dort drei Spalten; auf der Seite einer Verbindung stehen ab 1600 px die drei oberen Karten nebeneinander (etwa Gateways, Gateway und Clients). Formular und Einstellungen bleiben schmaler, damit sie lesbar bleiben.
- **Verbindungen, Sortierung:** Die Liste ist nach Art sortiert (Seriell, Modbus, EnOcean, 1-Wire), mit einer Überschrift je Art, darin nach Name; ausgeschaltete Verbindungen stehen am Ende ihrer Gruppe, ein Ersatz-Gateway weiter direkt hinter seinem Gateway. Verbindungen mit Problem springen nicht mehr nach oben; dafür gibt es den Filter „Probleme“.
- **1-Wire:** ist nicht mehr Beta. Die Hinweise und Markierungen „Beta“ in der Oberfläche und der Doku sind weg.
- **EnOcean, Gateway tauschen** (früher „Ersatz wird Haupt-Gateway“)**:** Die Programme bleiben beim Tausch jetzt verbunden. Vorher startete die Verbindung neu und warf alle Clients hinaus; Programme im Netz wie Symcon kamen erst nach Minuten wieder.
  - War gerade der Ersatz aktiv, geht es danach gleich über das getauschte Gateway weiter.
  - Neu: **Namen mittauschen**, wenn die Namen der Verbindungen das Gateway beschreiben (standardmäßig aus).
  - Klarere Texte: welches Gateway (Adresse) wohin kommt und was mit dem alten passiert.
  - Auch wenn du Host, Port oder Gerät eines EnOcean-Gateways änderst, bleiben die Programme jetzt verbunden.

### Behoben

- **EnOcean, Ereignisse:** Beim Umschalten auf den Ersatz und zurück steht der Grund jetzt in Worten da statt als Kennung (etwa „von Hand“ statt „by_hand“).

## 1.9.1 - 2026-11-18

### Neu

- **1-Wire, HTTP-Port (Beta):** Programme, die den Bus über HTTP vom owhttpd lesen (Port 2121, etwa 1-Wire-Module für IP-Symcon), können jetzt direkt die App nutzen. In der Verbindung den **HTTP-Port (owhttpd)** setzen; die App startet owhttpd selbst.
  - Am HTTP-Port gelten dieselben erlaubten Clients, Höchstzahl und Sperren wie am owserver-Port; das Programm erscheint mit seiner Adresse unter den Clients, seine Werte unter „Geräte am Bus“.
  - Schreiben über HTTP nur mit „Schreibzugriff: Alle Clients“, sonst läuft owhttpd nur lesend.

### Geändert

- **1-Wire, Programme, die nicht ankommen:** Schickt ein Programm an den Port einer 1-Wire-Verbindung etwas, das keine vollständige owserver-Anfrage ist (ein anderes Protokoll, oder es schließt mitten in der Anfrage), steht das jetzt in den Ereignissen, mit Rechner, Grund und den ersten Bytes. Vorher schloss die App solche Verbindungen ohne ein Wort, und das Programm tauchte nirgends auf. Ein reiner Port-Check bleibt still.

## 1.9.0 - 2026-11-18

### Neu

- **1-Wire, USB-Adapter an Home Assistant (Beta):** Eine 1-Wire-Verbindung kann jetzt auch den USB-Adapter (DS9490R, DS1490F) nutzen, der an Home Assistant steckt oder in dessen VM durchgereicht ist: Quelle **USB-Adapter an diesem Rechner**.
  - Die App startet dafür ihren eigenen owserver. Die Programme verbinden sich weiter mit dem Port der Verbindung, ein Umzug vom owserver im Netz ändert für sie nichts.
  - Das Formular sagt, ob es den Adapter findet.
  - Bleibt der Bus stehen, startet die App owserver neu und setzt den Adapter danach per USB-Reset zurück. „USB-Reset“ geht auch von Hand, auf der Seite der Verbindung und als Knopf in Home Assistant; Clients und Diagnose bleiben dabei erhalten.
  - Die Seite zeigt, ob owserver läuft, seine Neustarts und seine letzten Meldungen.
  - Unter „Erweitert“ lässt sich einstellen, wie lange der eigene owserver gelesene Werte zwischenspeichert (Standard 15 s); das spart Buszeit, wenn mehrere Programme dieselben Sensoren lesen.
- **1-Wire, Geräte am Bus:**
  - Eigene Namen für die Geräte; Ereignisse und Benachrichtigungen nennen sie.
  - Der genaue Chip, wie der owserver ihn nennt.
  - Der letzte Wert, den deine Programme gelesen haben; bei Geräten mit mehreren Werten (etwa DS2408, DS2438) lassen sich alle aufklappen.
  - Die App merkt sich die Geräte, auch über Neustarts: Fehlt eines zweimal hintereinander in der Geräteliste, steht es auf „fehlt seit“, und es kommt eine Benachrichtigung mit dem Namen. Ein absichtlich entferntes lässt sich vergessen, ein neues ist einen Tag lang markiert.
  - „Bus jetzt absuchen“ sucht sofort auf dem Bus statt in der zwischengespeicherten Liste, praktisch beim Verkabeln.
  - iButtons in der Lesemulde eines DS1490F kommen und gehen, ohne als fehlend zu gelten; die Liste sagt, wann einer zuletzt aufgelegt war.
  - Über MQTT gibt es die Zahl der fehlenden Geräte.
- **1-Wire, Fehler am Bus erkennen:**
  - 85 °C: eine Wandlung, die nicht fertig wurde.
  - Parasitär versorgte Sensoren, die übliche Ursache der 85 °C.
  - Eine Temperatur, die sich lange nicht bewegt, auch beim DS2438.
  - Ausreißer: ein einzelner Wert weit daneben, der beim nächsten Lesen wieder zurück ist.
  - Die owserver-Karte zeigt Name und Version des Adapters, die Version des owserver und seine CRC- und Busfehler.
- **1-Wire, Schreibzugriffe:** Die Seite einer 1-Wire-Verbindung listet die letzten 100 Schreibzugriffe (etwa einen Ausgang eines DS2408 schalten) mit Zeit, Client, Gerät, Wert und Ergebnis, auch die abgewiesenen. So findest du, wer ein Relais geschaltet hat.

### Geändert

- **1-Wire, Weiteres:**
  - Eine Verbindung, die innerhalb von 30 Sekunden keine Anfrage schickt (etwa ein hängendes Programm oder ein Port-Scan), schließt die App. Vorher blieb sie für immer offen.
  - Die Namen, die du den 1-Wire-Geräten gibst, stehen nicht im Diagnose-Paket, auch nicht in den Ereignissen; die IDs bleiben, damit der Fehler nachvollziehbar ist.

## 1.8.0 - 2026-11-18

### Neu

- **1-Wire-Busse (neu, Beta):** Eine neue Verbindungsart teilt einen owserver (OWFS), etwa den auf einem anderen Rechner, an dem der USB-Adapter hängt. Die 1-Wire-Integration von Home Assistant, owhttpd und andere Systeme verbinden sich mit dem Port der App (vorgegeben 4304) statt mit dem owserver; jede Anfrage geht unverändert durch. Die Seite der Verbindung zeigt, ob der owserver antwortet, die Geräte am Bus mit Familie und üblichem Chip, Anfragen, Fehler und Antwortzeit, die Clients je Rechner mit ihrer letzten Anfrage, und in den Live-Daten jeden Lesezugriff mit seinem Wert. Antwortet der owserver nicht, kommt eine Benachrichtigung. Schreiben (Ausgänge schalten) lässt sich auf bestimmte Rechner beschränken oder ganz sperren. Über MQTT gibt es „Gerät erreichbar“, die Zahl der 1-Wire-Geräte und die Anfragen als Entitäten. Den USB-Adapter direkt an Home Assistant bringt eine spätere Version.

## 1.7.0 - 2026-11-15

### Geändert

- **Oberfläche, neuer Look:** Die Bereiche sind Reiter mit Symbol, die Zahl der Probleme steht als Zähler am Reiter „Verbindungen“. Oben neben dem Namen steht nur noch eine Zeile mit dem Zustand und der App-Version, die Version von ser2net steht im Tooltip. Farbschema, hell oder dunkel und Schriftgröße stellst du über das Paletten-Symbol oben rechts von jeder Seite aus um; die Einstellungsseite zeigt nur noch die aktuelle Wahl mit einem Knopf dorthin. Buttons und Felder haben gemeinsame, weniger runde Ecken, Zahlen stehen als Kacheln mit einem kleinen Label darüber. Bei Schriftgröße „Klein“ wird Text nicht kleiner als 10,5 px. Am Handy hebt die untere Leiste den gewählten Bereich hervor. Beim Öffnen stehen Kopfzeile und Reiter sofort da, und solange die Daten laden, zeigen graue Platzhalter die Form der Seite statt „Lädt …“; das gilt auch für das Bearbeiten-Formular.
- **Oberfläche, Verbindungen:** Die Übersicht zeigt ihre Zahlen als Kacheln. Jede Verbindungskarte zeigt Clients, Datenrate mit Kurve und letzte Daten als Kacheln, darunter höchstens drei Clients; die übrigen findest du über „+N weitere“ auf der Detailseite. Am Handy ist der Hinweis zum fehlenden MQTT-Broker auf eine Zeile mit „Mehr“ eingeklappt.
- **Oberfläche, Detailseite und Ereignisse:** Datenrate, Modbus-Anfragen, Leitungsfehler, Gateway-Zähler, Funkbelegung und Nachlieferungspuffer stehen als Kacheln, ebenso Abbrüche und Verfügbarkeit unter „Verlauf und Stabilität“. Fließen bei einem seriellen Gerät noch keine Daten, zeigt die Detailseite eine schmale Karte statt zwei halbleerer. Bricht ein Label auf zwei Zeilen um, stehen die Zahlen einer Reihe trotzdem auf einer Höhe.
- **Oberfläche, Formular und Dialoge:** Nebeneinanderliegende Felder stehen auf einer Höhe, auch wenn ein Label auf zwei Zeilen umbricht. Der Hinweis „IP-Adresse oder Hostname“ steht unter der Adresse statt unter dem Port. Die Liste der Fehler unter dem Formular nennt die Felder mit ihrem Namen statt mit dem internen Schlüssel, ein Klick darauf springt zum Feld. Beim Speichern mit Fehlern springt das Formular zum ersten fehlerhaften Feld; liegt es unter „Erweitert“, klappt der Bereich auf. Der Import-Dialog hat beim Öffnen keinen farbigen Rahmen mehr. Ein Hinweis im Import und die Schaltflächen unter „Sichern und Übertragen“ haben im dunklen Modus die richtigen Farben.

## 1.6.2 - 2026-11-14

### Geändert

- **Texte:** Weitere Fehlermeldungen sind auf Deutsch, und ungültige Eingaben ergeben eine Meldung statt „internal error“.

### Behoben

- **Modbus TCP, erreichbar:** Nimmt ein Gerät Verbindungen an, antwortet aber nicht (etwa Dongle wach, Wechselrichter schläft), gilt es nach drei Anfragen ohne Antwort als nicht erreichbar. Vorher blieb es „erreichbar“, wenn die App einmal vor dem Gerät gestartet war, und es kam keine Benachrichtigung.
- **Modbus, Neustart einer Verbindung:** Wartende Anfragen bekommen sofort eine Antwort. Vorher konnten ein Client einer anderen Verbindung (über `unit_routes`) und ein laufender Bus-Scan für immer hängen bleiben; der Scan ließ sich dann nicht mehr starten.
- **Import und eigene ser2net.yaml:** Eine Datei, die nicht als UTF-8 gespeichert ist (etwa eine alte `ser2net.conf` mit Umlaut), lässt die App nicht mehr bei jedem Start abstürzen. Die eigene `ser2net.yaml` lässt sich dann auch wieder in der Oberfläche öffnen.
- **Import, Zugriff:** `remaddr` wie `ipv4,192.168.1.10,0` wird übernommen. Vorher fiel der Eintrag weg und die Verbindung war für das ganze Heimnetz offen statt für den einen Host.
- **Historie:** Eine gesperrte Datenbank oder ein voller Speicher gilt nicht mehr als beschädigt. Die Datei bleibt, wie sie ist, die App läuft weiter und hält die Historie bis zum nächsten Start im Speicher. Vorher wurden Ereignisse, Client-Verlauf und alle Versionen für „Rückgängig“ beiseitegeschoben, bei vollem Speicher startete die App gar nicht.
- **Stoppen und Update:** Ein offenes Panel hält das Stoppen der App nicht mehr auf.
- **Backup:** Ein Backup ohne Konfiguration wird abgelehnt, statt alle Verbindungen zu löschen. Ein Backup oder eine Version mit eigener `ser2net.yaml` nutzt die Formulare, wenn die Datei fehlt (etwa nach einer Neuinstallation).
- **EnOcean:** Ein Telegramm kurz vor der Replay-Anfrage kommt nur noch einmal an. Der Timeout zählt wie bei ser2net auch Telegramme zum Client, eine Integration, die nur zuhört, wird nicht mehr getrennt. Nach einem Neustart läuft kein alter Client-Handler im Hintergrund weiter.
- **Modbus RTU, nur mithören:** Ein Adapter, der sofort wieder auflegt, wird nur noch einmal pro Sekunde neu geöffnet statt tausendfach.
- **MQTT:** Zwei Installationen am selben Broker mit eigenem Basis-Topic werfen sich nicht mehr gegenseitig hinaus und löschen nicht mehr die Entitäten der anderen.
- **Oberfläche:** Ein Werkzeuglauf (Baudrate, Scan) bleibt nach einem kurzen Verbindungsfehler nicht mehr auf „läuft“ stehen. Das Lesewerkzeug hängt nicht mehr bei Typ „string“ und leerer Antwort. Eine abgeschnittene Adresse lässt die Seite nicht mehr leer. `unit_routes` mit Kommas wird auf der Detailseite richtig gezeigt. Exception 07 und unbekannte Codes haben einen Text, kein „fbReason_none“ direkt nach dem Start.
- **Home Assistant, Knöpfe:** Bewirkt ein Knopf nichts, etwa „Zurück zum eigenen Gateway“, solange das Gateway noch nicht verbunden ist, steht der Grund jetzt in den Ereignissen. Vorher stand er nur im Log der App.
- **Werkzeuge:** Eine laufende Baudraten-Erkennung oder ein Bus-Scan wird wieder angezeigt, wenn du die Seite verlässt und zurückkommst oder sie in einem anderen Browser öffnest. Vorher hieß es beim neuen Start nur „already running“.

## 1.6.1 - 2026-11-13

### Geändert

- **Clients sperren:** Mit eigener `ser2net.yaml` gilt eine Sperre nur für Modbus und EnOcean. Oberfläche und Ereignis sagen das jetzt.
- **Netzwerk:** Wer von einer Version vor 0.3 kommt, hat jetzt auch die privaten IPv6-Netze im Heimnetz. Wer schon aktualisiert hat, ergänzt `fc00::/7` und `fe80::/10` bei Bedarf selbst.
- **Oberfläche, Texte:** Zahlen und Uhrzeiten folgen der Sprache der App. „vor 1 Tag“ und „1 Eintrag“ statt „vor 1 Tagen“ und „1 Einträge“, „vor 1 Stunde“ statt „vor 60 Minuten“.
- **Oberfläche, Zeitangaben:** Statt „seit vor 30 Minuten“ steht jetzt „seit 30 Min“, bei Clients, beim Ersatz-Gateway und bei laufenden EnOcean-Aufzeichnungen.

### Behoben

- **Modbus, Schreibschutz:** Ein Schreibbefehl muss jetzt genau so lang sein, wie seine Anzahl sagt. Vorher konnte ein Client, der nur bestimmte Register schreiben darf, einen zweiten Befehl anhängen oder mehr Daten mitschicken, als erlaubt war.
- **Modbus RTU:** Ist der USB-Adapter wieder da, findet die App das Gerät ohne Neustart. Vorher blieben „erreichbar“ und die Register-Entitäten aus, bis ein Client etwas fragte.
- **Diagnose:** Das Diagnose-ZIP enthält keine Client- und Sendernamen mehr, auch nicht über frühere Einstellungsänderungen im Verlauf.
- **EnOcean, Aufzeichnung:** Kann eine Aufzeichnung nicht mehr schreiben (etwa bei vollem Speicher), endet sie und gibt das Gateway wieder frei. Ein Ereignis sagt, warum.
- **EnOcean, Clients:** Ein Client, der ohne Abmeldung verschwindet, wird jetzt erkannt und blockiert keinen Platz mehr.
- **Ereignisse:** Geänderte Werte für das Zusammenfassen gleicher Ereignisse wirken sofort, nicht erst nach einem Neustart.
- **Aufzeichnungen:** Haben zwei Verbindungen fast den gleichen Namen, behalten ihre Dateien den Namen, auch wenn eine abgeschaltet wird.
- **Oberfläche:** Nach dem Speichern eines MQTT-Passworts steht nicht mehr „Nicht gespeichert“. Auswahlfelder zeigen immer den Wert, der gilt. Nach dem Löschen einer Verbindung kommt keine Rückfrage mehr. Beim Import wird eine abgewählte Zeile nicht mehr übernommen. Der Ereignis-Verlauf zeigt bei schnellem Filterwechsel den richtigen Stand.
- **Oberfläche, Texte:** Zahlenfelder nehmen nur Ziffern an statt „NaN“ zu zeigen. Der Pfad der Aufzeichnungen steht als Text da, der Kopier-Knopf kopierte nur einen Platzhalter.

## 1.6.0 - 2026-11-09

### Neu

- **Home Assistant, Ereignisse:** Jede Verbindung hat jetzt eine Entität „Ereignisse“. Gerät weg, neuer Client, Schreiben abgewiesen und mehr können damit Automationen auslösen.
- **Home Assistant, Geräteseite:** Jedes Gerät der App hat jetzt einen Link direkt in die Device-Proxy-Oberfläche.
- **MQTT, Hinweis:** Findet die App keinen Broker, etwa bei EMQX, oder verliert sie ihn, sagt die Seite Verbindungen das jetzt und führt direkt zur Einstellung. Ohne Broker lässt sich der Hinweis ausblenden.
- **Modbus, Clients nebeneinander:** Die Client-Tabelle zeigt jetzt Anteil an der Gerätezeit, Antwortzeit und Wartezeit je Client. Ein Satz darunter sagt, ob sich die Clients ausbremsen.
- **Clients, Verlauf:** Tippst du auf einen Rechner, siehst du jetzt, wann er an welcher Verbindung hing: eine Zeitleiste über 7 Tage oder 24 Stunden, die letzten Verbindungen mit Dauer und Datenmenge, dazu Abbruch-Serien und abgewiesene Versuche. Der Verlauf beginnt mit diesem Update. Bei seriellen Verbindungen ist die Datenmenge so genau wie der letzte Statusabruf, abgewiesene Versuche gibt es bei Modbus und EnOcean. Wird ein Rechner entfernt, verschwindet auch sein Verlauf.
- **Ereignisse, neu:** MQTT verbunden oder verloren, kein Broker gefunden, ser2net startet nicht, interner Fehler einer Verbindung, fehlgeschlagener automatischer Neustart, volle Aufzeichnung, App beendet sowie unbrauchbare Konfiguration, Historie oder Blockliste. Der Start nennt die Version, ein Neustart den USB-Reset.

### Geändert

- **Home Assistant, Entity-IDs:** Neue Entitäten beginnen mit `device_proxy_`. Bestehende stellst du unter Einstellungen → MQTT um, die Vorschau zeigt, wo sie benutzt werden. Verweise auf alte IDs passt Home Assistant nicht an.
- **Home Assistant, Version:** Alle Geräte der App nennen jetzt die Version der App. Beim Gerät Device Proxy stand dort bisher die Version von ser2net.
- **Home Assistant, Geräte:** Die Geräteliste zeigt jetzt „Device Proxy · Seriell“, „· Modbus“ oder „· EnOcean“, so sind die Geräte auf den ersten Blick zuzuordnen. Geräte und Entitäten bleiben dieselben.
- **Ereignisse, Sammelzeilen:** Wiederholungen werden jetzt je Client zusammengefasst, kein Rechner verschwindet mehr hinter einem anderen. Die Zeile nennt, wie oft und wann zuletzt.
- **Ereignisse, Stufen:** Warnung heißt jetzt, dass etwas Aufmerksamkeit braucht. Blockieren und Wartung sind Info, ein automatischer Neustart ist eine Warnung. Der leere Filter Debug ist weg.
- **Sprachen:** Jede Sprache ist jetzt eine eigene Datei, mit Weboberfläche, Meldungen und Entitätsnamen. Eine neue Sprache braucht nur noch eine Datei; was darin fehlt, erscheint auf Englisch. Die Texte selbst sind unverändert.
- **Ereignisse:** Abgewiesene Clients erscheinen bei Modbus und EnOcean jetzt auch, wenn ihr Netz nicht erlaubt ist, gerade Wartung läuft oder sie blockiert sind. Wiederholungen werden zusammengefasst.
- **Mitschnitt:** Die Verbindung wählst du jetzt in einer Liste wie unter Ereignisse, so bleibt auch bei vielen Verbindungen jede erreichbar. Laufende Aufzeichnungen sind darin markiert.
- **Mitschnitt, Dateien:** Jede Datei trägt das Startdatum ihrer Aufzeichnung im Namen und behält ihn, zum Beispiel `ehz_sml-20261109-104012.log`. Das Einschalten beginnt eine neue Datei. Wird die Zahl der behaltenen Dateien gesenkt, verschwinden die überzähligen jetzt auch. Vorhandene Dateien bleiben unter ihrem Namen, bis sie herausrotieren.
- **Mitschnitt, Tabelle:** Kompakte Zeilen, neueste oben, Herunterladen und Löschen als gleich große Symbole, die laufende Datei ist markiert.

### Behoben

- **Verfügbarkeit:** Fiel ein Modbus- oder EnOcean-Gerät aus und die App startete währenddessen neu, zählte die Zeit danach weiter als Ausfall. Das ist behoben, auch rückwirkend für die Anzeige.

## 1.5.1 - 2026-11-08

### Geändert

- **Übersicht:** In der Kachel einer Verbindung steht bei den Clients kein Stift mehr, die Zeile bricht nicht mehr um. Umbenennen geht weiter in den Details der Verbindung und unter Clients.
- **README:** Die Voraussetzung steht wieder im Schnellstart: Home Assistant OS.

## 1.5.0 - 2026-11-08

Modbus-Register direkt als Entitäten in Home Assistant, Schreibrechte je Client, Geräteprofile, ein Stromzyklus für hängende Geräte, Clients sperren und benennen, EnOcean-Sender mit Namen.

### Neu

- **Modbus, Register als Entitäten:** Die App liest Register selbst und bietet sie über MQTT als Sensoren an, ohne YAML. Anlegen unter Register lesen → Werte dekodieren oder als Zeilen im Formular, höchstens 50, standardmäßig alle 30 Sekunden. Beim Mithören am RS485-Bus kommen die Werte aus dem Gehörten, es wird nichts gesendet.
- **Modbus, Register je Client:** Eine Zeile je Client legt fest, welche Register er schreiben darf, statt der allgemeinen Register. „Zugriff prüfen“ nennt die Zeile, die gilt.
- **Modbus, Geräteprofile:** Startwerte für SolarEdge, Huawei SUN2000, Fronius, SMA, Kostal Plenticore, Sungrow und Victron GX; erkennt der Bus-Scan den Hersteller, bietet er dessen Zeiten an.
- **Stromzyklus:** Ein Schalter in Home Assistant kann ein hängendes Gerät 5 Sekunden vom Strom trennen: von Hand, als Button in Home Assistant und einmal, wenn drei automatische Neustarts nicht geholfen haben.
- **Clients sperren:** Ein Rechner lässt sich von allen Verbindungen aussperren und wieder freigeben. Bei Modbus und EnOcean steht in seiner Zeile, wie oft er abgewiesen wurde.
- **Clients benennen:** Neue, bekannte und blockierte Rechner stehen in einer Liste mit Status und „zuletzt gesehen“; ein Klick öffnet den Namen. In den Client-Listen einer Verbindung geht das mit dem Stift. Dieser Rechner heißt von selbst Home Assistant, Adressen im Supervisor-Netz App. Nicht verbundene Rechner lassen sich aus der Liste entfernen. Viele neue Rechner auf einmal ergeben eine gemeinsame Benachrichtigung.
- **EnOcean-Sender:** eigene Namen für alle Gateways, gemeinsam gespeichert und nicht in der Diagnose, dazu die Liste als CSV-Datei.
- **EnOcean-Ersatz-Gateway:** Prüfintervall, Fehlversuche bis zum Umschalten und die stabile Laufzeit vor der Rückkehr lassen sich je Gateway einstellen.
- **Zigbee-Stick:** eine eigene Vorlage (115200 Baud, ein Client, nur Home Assistant und Apps).

## 1.4.1 - 2026-11-08

Das Panel ist auf dem Handy gut bedienbar, dazu viele Korrekturen bei EnOcean, Modbus und MQTT.

### Geändert

- **Handy:** die Bereiche als Leiste unten, keine Seite ist mehr breiter als der Bildschirm, die Speichern-Leiste des Formulars ist einzeilig, Links und kleine Knöpfe sind leichter zu treffen.

### Behoben

- **Mitschnitt:** die Bytes dekodierter Telegramme schrumpfen nicht mehr auf ein Zeichen pro Zeile; die Datei einer laufenden Aufzeichnung lässt sich nicht mehr löschen.
- **EnOcean:** immer nur ein Befehl mit erwarteter Antwort, eine verspätete Antwort geht an niemanden; ESP2 prüft die Prüfsumme jedes Telegramms; bei einer Aufzeichnung mit Sperre kein falscher Wechsel auf das Ersatz-Gateway.
- **Modbus:** ein nicht erreichbares Gerät weist Clients sofort ab, verschwundene Clients geben ihren Platz frei, jedes Schreiben leert den Cache, ungültige Lesewünsche beim Mithören am Bus bekommen eine Fehlerantwort.
- **MQTT und Benachrichtigungen:** ein Fehler eines Buttons beendet MQTT nicht mehr, alte Entitäten verschwinden zuverlässig, erledigte Meldungen werden auch nach einem Neustart entfernt.
- **App:** eine ungültige Konfiguration startet nicht mehr leer, was gültig ist, bleibt erhalten; fällt ein Hintergrundteil aus, startet die App neu; der Import zeigt Konflikte innerhalb einer Datei in der Vorschau.

## 1.4.0 - 2026-11-05

Eine hängende Verbindung lässt sich neu starten, auch mit einem USB-Reset des Adapters, von Hand, aus Home Assistant oder automatisch.

### Neu

- **Neu starten:** neue Karte auf der Seite einer Verbindung. Das Gerät (bei Modbus und EnOcean der Proxy) wird geschlossen und neu geöffnet, die Clients verbinden sich wieder, auch mit „Gerät offen halten“.
- **USB-Reset:** für USB-Adapter dieses Rechners; setzt den Adapter zurück wie Ab- und Anstecken, ohne den Strom zu unterbrechen, und wartet, bis er wieder da ist.
- **Automatisch:** nach den Minuten ohne Daten wahlweise neu starten oder USB-Reset und neu starten (serielle Verbindungen), höchstens dreimal in Folge, bis wieder Daten kommen.
- **Home Assistant:** Buttons „Verbindung neu starten“ und „USB-Reset“ je Verbindung.
- **Historie:** Jeder Neustart steht in der Historie, ein fehlgeschlagener USB-Reset als Warnung.

## 1.3.0 - 2026-11-02

Das Panel lässt sich anpassen: drei Farbschemata, hell oder dunkel, und drei Schriftgrößen.

### Neu

- **Farbschema:** Ozean (wie bisher), Wald oder Graphit, jeweils hell und dunkel.
- **Hell oder dunkel:** wie Home Assistant (wie bisher), immer hell oder immer dunkel.
- **Schriftgröße:** Klein (12 px), Normal (14 px) oder Groß (16 px); alle Texte wachsen mit, Abstände bleiben gleich.
- **Einstellung:** Einzustellen unter Einstellungen → Hilfe und Info; gilt nur für diesen Browser und sofort.

### Geändert

- **Farbschema Ozean:** Der gedämpfte Text ist etwas heller.

## 1.2.2 - 2026-11-02

Die EnOcean-Eltako-Integration kommt wieder an den Statusport, auch über IPv6.

### Geändert

- **Abweisung am Statusport:** Die Antwort 403 nennt den Grund; das Log nennt dazu den Host-Header.

### Behoben

- **EnOcean, Statusport:** Home Assistant wurde mit 403 abgewiesen. Es läuft im Host-Netzwerk und kann von einer anderen Adresse des Rechners kommen als der, an die es sich verbindet. Jede Adresse des Rechners zählt jetzt als dieser Rechner (Statusport, EnOcean- und Modbus-Proxy, Modbus-Schreibsperre).
- **Apps über IPv6:** Das IPv6-Netz des Supervisors (fd0c:ac1e:2100::/48) zählt wie 172.30.32.0/23 zu den Apps (Statusport, „Home Assistant und Apps“, ser2net).

## 1.2.1 - 2026-11-02

Der Statusport für die EnOcean-Eltako-Integration sagt, warum er eine Anfrage nicht beantwortet, statt die Verbindung zurückzusetzen.

### Geändert

- **Log:** Jede Abweisung und jeder Fehler am Statusport steht im Log der App, mit Adresse und Port des Clients, der Adresse, an der er ankam, und dem Grund (nicht erlaubt, Zeitlimit, Anfrage abgebrochen oder zu lang, Fehler beim Status mit Traceback).

### Behoben

- **EnOcean, Statusport:** Eine abgewiesene Anfrage bekam einen Verbindungsabbruch („Connection reset by peer“), weil die App die Verbindung schloss, bevor sie die Anfrage gelesen hatte. Jetzt liest sie die Anfrage und antwortet mit 403; schlägt der Status selbst fehl, mit 500.

## 1.2.0 - 2026-11-02

Vor dem Speichern sehen, was eine Änderung bewirkt, und mit einem Schritt zurück, wenn sie etwas kaputt gemacht hat; prüfen, wer auf ein Modbus-Gerät schreiben darf; sichere Vorgaben, wo eine Verbindung ohne das Formular entsteht; eine robustere Weboberfläche.

### Neu

- **Was Speichern bewirkt:** Das Formular einer Verbindung und die Rückfragen vor einer Änderung der Netzwerk-Einstellung oder des Heimnetzes, einem Import und dem Wiederherstellen einer Version oder Sicherung nennen die laufenden Verbindungen, die neu aufgebaut oder beendet werden, und wie viele Clients sich neu verbinden müssen.
- **Stand davor wiederherstellen:** Arbeitet nach einer Änderung eine Verbindung nicht mehr, die vorher lief, sagen das die Übersicht und die Seite der Verbindung und bieten die Konfiguration von vor der Änderung an.
- **Modbus, Zugriff prüfen (Werkzeuge):** ob ein Client an einer Adresse sich verbinden, lesen und ein Register schreiben darf und welche Regel entscheidet – mit denselben Prüfungen wie der Proxy, ohne etwas zu senden.
- **Modbus, wer wirklich schreiben darf:** auf der Seite der Verbindung: jeder Client, der sich verbinden darf, die eingetragenen, niemand, wenn keiner eingetragen ist, die erlaubten Register und die Regel einer Verbindung, an die Units weitergehen.

### Geändert

- **Modbus:** Neue Modbus-Verbindungen ohne das Formular (API, Skripte) lassen nur Home Assistant und die Apps schreiben, wie das Formular schon immer. Verbindungen, die gespeichert wurden, bevor es den Schreibzugriff gab, behalten „Alle“.
- **Z-Wave:** Ein Z-Wave-Stick ohne das Formular lässt ebenfalls nur Home Assistant und die Apps verbinden.
- **Hostnamen:** Ein Name, der sich nicht auflösen lässt, oder ein Gerät, das nicht rechtzeitig erreicht wird, steht in Worten da („Hostname … nicht gefunden (DNS)“, „… in … s nicht erreicht“) statt im Text des Systems oder als „keine Antwort“.
- **EnOcean:** Die Einstellungen sagen, wenn der Statusport für die EnOcean-Eltako-Integration nicht geöffnet werden konnte, warum, und dass die App es erneut versucht.
- **Mitschnitte:** Mitschnitte werden in Blöcken heruntergeladen statt ganz in den Speicher gelesen; die Oberfläche bleibt während eines großen Downloads bedienbar.
- **Statusabfrage:** immer nur eine zur Zeit, mit Zeitlimit; Anfragen stauen sich nicht mehr, während die App beschäftigt ist, und eine ältere Antwort überschreibt nie eine neuere.
- **Bedienung:** Auswahlgruppen (Netzwerk, MQTT-Broker, ser2net-Quelle, Import-Art) lassen sich mit den Pfeiltasten bedienen.
- **Screenshots:** Neue Screenshots in den READMEs.

### Behoben

- **Einstellungen:** Wer die Seite mit noch nicht gespeicherten Änderungen verlässt, wird vorher gefragt, wie im Formular einer Verbindung (vorher waren sie weg).
- **Volle Platte:** Eine Konfiguration, die nicht gespeichert werden kann, ändert nichts, und die Seite sagt warum (vorher „interner Fehler“). Kann nur die Konfig-Historie sie nicht behalten, gilt die gespeicherte Änderung trotzdem.
- **Import:** Eine ser2net.yaml mit einem Steuerzeichen wird mit einer Meldung abgelehnt statt mit einem Fehler.
- **Weboberfläche:** Eine Verbindung, die ihre Anfrage oder deren Inhalt nicht rechtzeitig schickt, wird geschlossen.

### Tests und Werkzeuge

- **Tests:** Zufällige und kaputte Eingaben für alle Parser und die laufenden Proxys, kaputte Uploads und Sicherungen.
- **Soak-Tests:** `tools/soak_test.py` mit Grenzwerten für Antwortzeiten, Speicher und Wiederanlauf, mit Geräteausfällen und langsamen Lesern; `tools/soak_enocean.py` für ein Gateway und sein Ersatz-Gateway.
- **Hardware-Tests:** `tests/HARDWARE.md`: die Prüfungen, die echte Geräte unter Home Assistant OS brauchen.

## 1.1.0 - 2026-11-01

Viele neue Werkzeuge: Modbus-Werte dekodiert und Geräte erkannt, Namen für Clients und ein Hinweis auf neue, Wartung mit einem Rechner allein, Zählerstände für das Energie-Dashboard, ein RS485-Bus, der mitgehört wird, ohne zu senden, mehrere Modbus-Geräte hinter einem Port. Die App kommt jetzt als fertiges Image.

### Neu

- **Modbus, Werte dekodieren:** unter „Register lesen“: 16-, 32- und 64-Bit-Ganzzahlen, Gleitkommazahlen oder Text, mit Register- und Byte-Reihenfolge („swap“) und einem Faktor, wie die Modbus-Integration von Home Assistant sie liest, und der passende Sensor zum Kopieren in die `configuration.yaml`.
- **Modbus, Bus scannen:** fragt jede gefundene Unit, wer sie ist (Geräte-Identifikation, SunSpec), und zeigt Hersteller, Modell, Version und eine passende Integration.
- **Modbus, Hinweise zum Timing:** auf der Statuskarte: ein längeres oder kürzeres Timeout, ein Zwischenspeicher, was eine lange Warteschlange oder viele Fehlerantworten bedeuten.
- **Modbus, erlaubte Register beim Schreiben:** Adressen und Bereiche; ein Schreibzugriff außerhalb wird mit Fehler 02 abgewiesen. Die Karte **Schreibzugriffe** listet die letzten Schreibzugriffe der Clients und ihr Ergebnis.
- **Modbus, RS485 mithören:** eine neue Art Verbindung für einen Bus, der schon einen Master hat (z. B. ein Wechselrichter und sein Zähler). Die App hört nur mit, sendet nie und beantwortet Lesezugriffe aus dem Gehörten.
- **Modbus, Units anderer Verbindungen:** ein Port für mehrere Geräte; eine hier gefragte Unit beantwortet das Gerät einer anderen Modbus-Verbindung.
- **EnOcean, Sender:** jede gehörte Sender-ID mit Art, Anzahl, zuletzt gehört, Repeatern, Empfang (ESP3) und welches Gateway sie gehört hat; neue Sender markiert, IDs zum Kopieren.
- **Serielle Geräte, Zählerstände als Entitäten:** Bezug und Einspeisung in kWh und Leistung in W über MQTT, für das Energie-Dashboard, gelesen aus dem, was der Zähler ohnehin sendet (an mit den eHZ-Vorlagen).
- **Serielle Geräte, serielle Brücke im Netz:** Eine serielle Brücke im Netz (ESPHome Stream Server, Tasmota-Lesekopf, USR-TCP232) als Quelle einer Verbindung, geteilt wie ein Gerät dieses Rechners.
- **Serielle Geräte, Gerät umgesteckt:** Fehlt ein Gerät und steckt sein Adapter an anderer Stelle, bietet die Seite an, ihn zu übernehmen.
- **Alle Verbindungen, Clients:** Namen für Client-Adressen (**Einstellungen → Clients**), angezeigt in den Listen und Ereignissen. Ein Rechner, der sich zum ersten Mal verbindet, wird gemeldet, bis er als bekannt markiert oder benannt ist.
- **Alle Verbindungen, Clients trennen:** ein Knopf auf der Seite der Verbindung und ein MQTT-Knopf in Home Assistant; ein EnOcean-Gateway mit Ersatz bekommt auch Knöpfe zum Umschalten.
- **Alle Verbindungen, Wartung:** Ein Rechner darf eine Verbindung eine Weile allein nutzen, z. B. für ein Service-Tool oder ein Firmware-Update; die anderen bleiben draußen, bis die Zeit um ist.
- **Alle Verbindungen, als Testfall:** die letzten Frames einer Verbindung als Datei für ein Issue, EnOcean-IDs ersetzt.

### Geändert

- **Fertiges Image:** Home Assistant lädt die App herunter, statt gensio und ser2net auf dem Gerät zu bauen. Aufgezeichnete Mitschnitte und EnOcean-Aufzeichnungen bleiben aus den Sicherungen von Home Assistant heraus.

## 1.0.1 - 2026-10-23

Home Assistant kommt an einem EnOcean-Gateway, das auf Home Assistant und die Apps beschränkt ist, wieder hinein.

### Behoben

- **EnOcean, „Nur Home Assistant und Apps“:** Home Assistant wurde an einem erkannten Gateway und am Statusport abgewiesen, sodass die EnOcean-Eltako-Integration die Base-ID nicht lesen konnte und danach fragte. Sie verbindet sich mit dem Hostnamen der App, also der LAN-Adresse des Rechners, und kommt damit von dort, nicht von 127.0.0.1. Eine Verbindung vom Rechner zu seiner eigenen Adresse zählt jetzt als 127.0.0.1 (EnOcean- und Modbus-Proxy, Statusport, Modbus-Schreibsperre).

## 1.0.0 - 2026-10-23

EnOcean-Gateways nennen der EnOcean-Eltako-Integration ihr Modell.

### Neu

- **Modell des EnOcean-Gateways:** Jedes Gateway hat ein Feld **Modell** (FAM-USB, FGW14-USB, FAM14, MGW-ETH, Symcon LAN, anderes ESP2- oder ESP3-Gateway), das mit der Erkennung an die EnOcean-Eltako-Integration geht (`model` neben Name, Port und Protokoll). Die Vorlage setzt es, und vorher gespeicherte Gateways nehmen es aus ihrer Vorlage; es muss zum Protokoll passen und darf leer bleiben, dann geht die Erkennung ohne.

## 0.4.0 - 2026-10-22

EnOcean-Gateways bekommen ein Ersatz-Gateway: ein zweites Gateway mit derselben Base-ID springt ein, wenn eines ausfällt. Ebenfalls neu: die Base-ID mit den Werkzeugen setzen.

### Neu

- **EnOcean-Ersatz-Gateway:** Ein zweites Gateway mit derselben Base-ID springt ein, wenn eines ausfällt. Es wird als normale Verbindung angelegt und dann im Formular des ersten Gateways gewählt; solange es Ersatz ist, hat es keinen eigenen Port und wird der Integration nicht angeboten. Das erste Gateway liest alle 10 s seine Base-ID; ist es weg oder bleibt stumm, laufen seine Programme ohne neue Verbindung über den Ersatz weiter und kommen nach 60 s stabilem Lauf oder von Hand zurück. Wahlweise werden beide Gateways gehört, Duplikate und das eigene Senden verworfen. Die Karte „Gateways“ zeigt beide und schaltet von Hand um; „Ersatz wird Haupt-Gateway“ tauscht die Hardware, wenn ein Gateway kaputt ist. Benachrichtigungen, MQTT-Entitäten (Ersatz aktiv, aktives Gateway, Ersatz bereit) und der Status für die Integration sagen, welches Gateway in Gebrauch ist.
- **EnOcean-Base-ID:** Die Werkzeuge setzen eine neue Base-ID, und ESP3-Gateways zeigen, wie viele Änderungen noch übrig sind (das Gateway erlaubt nur wenige).
- **Modbus-Werkzeuge:** neu „Register schreiben“ (Funktionen 5, 6, 15, 16) neben „Register lesen“. Es fragt vorher nach, liest den Wert danach zurück, sagt, ob er passt, und schreibt ein Ereignis ins Protokoll. Bei Verbindungen mit Schreibzugriff „Niemand“ bleibt es gesperrt. Der Lesen-Knopf ist in die Zeile der Felder gewandert.

### Geändert

- **Verbindung speichern:** Das Formular fragt nicht mehr, ob die gerade gespeicherten Änderungen verworfen werden sollen.
- **Dokumentation:** Das MQTT-Basis-Topic ist `device_proxy` (dort stand noch `ser2net`); die vier Netzwerk-Stufen mit ihren heutigen Namen, auch „Home Assistant und Apps“; die Modbus-Schreibsperre, wie sie jetzt arbeitet; Menüpfade, wie die Oberfläche sie nennt; EnOcean in der Einleitung; der eigene MQTT-Broker; was eine eigene ser2net.yaml darf. Die README beschreibt die heutige Vorgabe für erlaubte Clients und wo die Adresse einer Verbindung steht.
- **Verbindungen:** Die Karte zeigt die Adresse nicht mehr mit Kopierknopf (sie wird nur zum Einrichten gebraucht, und die Detailseite hat sie); stattdessen steht dort, wann zuletzt Daten kamen, z. B. „Letzte Daten vor 3 s“. Verbindungen, die nicht laufen, zeigen dort nichts, denn ihr Zustand sagt schon warum.
- **Erlaubte Clients:** Neue EnOcean-Gateways lassen das Feld leer und folgen damit der Netzwerk-Einstellung wie die anderen Arten (vorher waren sie auf Home Assistant und Apps beschränkt, und eo_man oder PCT14 im Heimnetz kamen ohne Änderung nicht hinein). Der Knopf „Nur Home Assistant und Apps“ bleibt für eine eigene Grenze. Der Z-Wave-Stick behält seine Vorgabe und sagt warum: Er nimmt Befehle an und hat keine Anmeldung. Bestehende Verbindungen behalten, was sie haben; ein Gateway mit Grenze zeigt einen Knopf „Der globalen Einstellung folgen“, der das Feld leert, und der Hinweis sagt das.
- **Auswahlkacheln** (Gateway-Vorlage, Art der Verbindung, Einstellungen): Alle Kacheln einer Gruppe sind gleich groß in einem gleichmäßigen Raster (sieben Vorlagen stehen vier und drei statt sechs und eins), und die gewählte ist markiert, ohne dass ihr Inhalt springt.
- **Letzte Ereignisse:** immer volle Breite, eine Zeile je Ereignis (Zeit, Stufen-Punkt, Text) in ausgerichteten Spalten statt der Zeit unter dem Text. Bei seriell und EnOcean ist auch die Verbindungskarte voll breit, wie bei Modbus.
- **In Home Assistant verwenden** (Modbus): zuerst eingeklappt wie die Werkzeuge und Adressen.
- **Adressen:** Die Karte heißt nur „Adressen“, ist zuerst eingeklappt wie die Werkzeuge (sie werden nur zum Einrichten gebraucht) und öffnet sich von selbst, wenn „Adressen zeigen“ in einem Hinweis zu ihr springt.
- **Aufklappbare Teile:** „Weitere Werkzeuge“, „So geht es mit PCT14“, das YAML für Home Assistant und „Welche Formate gehen?“ im Import bekommen dasselbe „›“ wie die in den Einstellungen; es dreht sich beim Öffnen.
- **Werkzeugkarte:** zeigt, dass sie sich einklappen lässt: „Anzeigen“ oder „Einklappen“ mit Pfeil rechts, und der Kopf wird hervorgehoben, wenn der Zeiger darüber ist. Bei allen Arten (seriell, Modbus, EnOcean) ist die Karte zuerst eingeklappt, zeigt im Titel, was sie enthält, merkt sich je Art, ob sie offen war, und öffnet sich von selbst, wenn ein Ergebnis da ist.
- **Modbus-Werkzeuge:** Lesen, Schreiben und Scannen teilen sich ein Raster, sodass die Felder in vier Spalten stehen und die Knöpfe rechts in einer Spalte (der Start-Knopf des Scans hat keine eigene Zeile mehr).
- **Detailseite (EnOcean):** Die sechs Zähler der Gateway-Karte stehen in einem gleichmäßigen Raster von drei mal zwei, wie die Kacheln der anderen Karten (Wert oben, Beschriftung darunter); Kartenköpfe stehen in einem Paar auf einer Linie; die Client-Tabelle passt in ihre Karte, statt abgeschnitten zu werden.
- **EnOcean-Werkzeuge:** Das Werkzeug „Aufzeichnung“ heißt „Telegramme aufzeichnen“ (englisch „Record frames (PCT14)“) und sagt, wie es sich vom ständigen Mitschnitt unterscheidet, damit die beiden nicht verwechselt werden.
- **Einstellungen, Protokoll:** Der Abschnitt zum Protokoll sagt, dass es das technische Protokoll zur Fehlersuche ist, wo es in Home Assistant steht und wie es sich vom Reiter Ereignisse unterscheidet.
- **Einstellungen, MQTT „Erweitert“:** Die drei Felder unter MQTT „Erweitert“ stehen oben auf einer Linie; der Hinweis des ersten schiebt die anderen nicht mehr nach unten.
- **Live-Daten** (Detailseite und Mitschnitt): Zeit und Richtung nehmen nur den Platz, den sie brauchen; bei Modbus und EnOcean teilen sich Beschreibung und Bytes eine Zeile und brechen nur um, wenn die Karte schmal ist, statt alle 16 Bytes.
- **Detailseite:** keine Seitenspalte mehr; Karten stehen in Paaren zweier gleicher Spalten, in der Reihenfolge Zustand, Messwerte, Live-Daten, Werkzeuge, zuletzt Adressen und Einstellungen (der Hinweis „kein Programm verbunden“ verweist auf die Adressen). Dieselbe Reihenfolge für seriell, Modbus und EnOcean.
- **Bearbeiten-Seite:** Die Vorschau einer Modbus- oder EnOcean-Verbindung steht unter dem Formular, über der Speicherleiste; ihr Ablauf liest sich von links nach rechts.
- **Import:** Der Import der Optionen der EnOcean-Proxy-App ist weg (diese App war nie in Gebrauch): kein „Aus der EnOcean-Proxy-App holen“, keine `import/enocean_proxy.yaml`.

### Behoben

- **Nicht gespeicherte Änderungen:** Wer das Formular einer Verbindung über den Kopf, die Brotkrumen, einen Chip oder den Zurück-Knopf des Browsers verlässt, wird jetzt vorher gefragt, wie bei Abbrechen (vorher waren die Änderungen weg).
- **Nach einem Neustart der App:** Eine offene Seite zeigt wieder neue Ereignisse und Live-Daten (sie standen still, bis die neuen Zähler die alten überholten).
- **Speichern, während die App nicht erreichbar ist:** zeigt „keine Verbindung zur App“ statt nichts.
- **Einstellungen nach einer Wiederherstellung:** Das Formular zeigt die wiederhergestellten Werte (Speichern konnte die alten zurückschreiben), und die Konfig-Historie füllt sich nach dem Wiederherstellen einer Sicherung wieder.
- **Details einer Verbindung:** Ergebnisse des Scans oder der Baudraten-Erkennung bleiben nicht mehr bei der nächsten Verbindung stehen, und Live-Daten erscheinen auf einer langsamen Verbindung nicht mehr doppelt.
- **Dialoge:** Tab bleibt im Dialog, und der Fokus geht dorthin zurück, wo er war. Der Stufen-Filter der Ereignisse hat eine deutsche Beschriftung; keine ID kommt auf der Einstellungsseite doppelt vor.
- **Texte:** Die Netzwerk-Stufe „Home Assistant und Apps“ erschien als `listen_apps`, Modbus-Fehler 8 als `ex_8`; die englische Import-Vorschau sagte „höchstens 5 Clients“. Fehler des Modbus-Schreibwerkzeugs, einer Wiederherstellung und des MQTT-Tests sind ins Deutsche übersetzt. Die Ereignisse „eigene ser2net.yaml nicht verwendbar“ und „Import fehlgeschlagen“ zeigen den Grund in beiden Sprachen (Englisch zeigte eine Python-Liste). 39 Texte, die nichts mehr nutzte, sind weg.
- **Modbus-Schreibsperre:** Ein Lesezugriff geht nur durch, wenn seine Anfrage genau die Länge dieses Lesezugriffs hat. Bei RTU und RTU über TCP gibt der Proxy die Bytes unverändert weiter, sodass ein hinter einem Lesezugriff versteckter Schreib-Frame das Gerät erreichte, obwohl Schreiben gesperrt war.
- **Modbus RTU:** Das Echo der Diagnose (Funktion 8) wird bis zu seinem Ende gelesen statt nach 8 Bytes abgeschnitten. Mit „alten Client verdrängen“ kommt ein neuer Client nicht mehr neben einen, der gerade verdrängt wird.
- **EnOcean ESP3:** Müll, dessen erste Bytes wie ein langer Frame aussehen, hält nicht mehr jedes Telegramm zurück, bis so viele Bytes angekommen sind (Stunden); die Daten-CRC wird geprüft, Längen sind begrenzt, und ein unfertiger Frame wird nach 0,5 s aufgegeben.
- **Gesundheitsprüfung:** Sie verbindet sich nicht mehr als Client mit den EnOcean-Ports (bei einem erlaubten Client und „alten Client verdrängen“ drängte sie jede Minute die Integration hinaus und schrieb zwei Ereignisse pro Minute in die Historie). Die App schreibt dafür den Zustand der Gateways; hört die App damit auf, schlägt die Prüfung fehl, und der Supervisor startet die App neu.
- **Aufzeichnungen:** Eine, die sich nicht schreiben lässt (volle Platte, Ordner nicht beschreibbar), friert nicht mehr die Live-Ansicht und „letzte Daten“ jeder Verbindung ein und meldet für sie nicht mehr „keine Daten“.
- **Gateways im Netz** (EnOcean, Modbus TCP, RTU über TCP): TCP-Keepalive bemerkt nach etwa 90 s ein Gateway, das den Strom verliert, ohne die Verbindung zu schließen, und verbindet neu.
- **EnOcean-Statusport:** War er belegt (z. B. von der alten EnOcean-Proxy-App), wird er alle 30 s erneut versucht statt erst bei der nächsten Änderung.
- **Historie:** Eine volle Platte oder ein E/A-Fehler schiebt die Historie nicht mehr als beschädigt beiseite; das Ereignis wird protokolliert, aber nicht behalten.
- **Weitere ser2net-Optionen:** Nur harmlose werden übernommen (Puffergrößen, chardelay, sendon/closeon, signature, mDNS, …). `connback` kann über seinen gensio-String ein Programm starten und wird abgewiesen, ebenso Anmeldungen, LEDs und Werte, die eine Datei lesen (`*{…}`, `*(…)`), auch in banner, openstr und closestr. Ein Import oder eine Sicherung lässt sie mit einem Hinweis weg; eine gespeicherte Konfiguration verwirft sie beim Laden.
- **Import und eigene ser2net.yaml:** Das Lesen läuft neben den Proxys, statt sie anzuhalten, und ein Text ohne Doppelpunkte braucht zum Prüfen nicht mehr Minuten. Uploads sind auf 1 MB begrenzt.
- **API der Weboberfläche:** Inhalte in falscher Form (eine Liste statt eines Objekts, eine Sicherung mit kaputtem `config`) ergeben 400 statt 500; ein Modbus-Import mit `timeout: nan` nimmt die Vorgabe.
- **Aufzeichnungen, Mitschnitt-Ordner:** Herunterladen oder Löschen folgt keinem symbolischen Link mehr aus dem Mitschnitt-Ordner hinaus.
- **Diagnose:** Benutzername und Passwort eines eigenen MQTT-Brokers standen noch in der `status.json` des ZIP (nur die `config.json` verbarg sie). Beide werden jetzt ersetzt.
- **MQTT-Passwort:** wird nicht mehr an den Browser geschickt (Status alle 2 s, Konfig-Historie). Das Formular zeigt Punkte für ein gesetztes Passwort; unverändert zurückgeschickt bleibt das gespeicherte, auch für „Testen“.
- **Einstellungen:** Eine Änderung der Einstellungen und das Speichern der eigenen ser2net.yaml zur selben Zeit machen sich nicht mehr gegenseitig rückgängig; die eigene Datei wird der Reihe nach mit anderen Änderungen geschrieben und auf die Platte gebracht.
- **Modbus- und EnOcean-Proxys:** Einer, der durch einen unerwarteten Fehler endet, startet nach 30 s neu (vorher blieb sein Port bis zur nächsten Änderung oder einem Neustart der App zu). Ursachen, die ihn beendeten, werden jetzt abgefangen: ein USB-Adapter, der beim Öffnen gezogen wird, ein Hostname wie `a..b` (wird auch beim Speichern abgewiesen), eine volle Platte beim Aufzeichnen (nur die Aufzeichnung endet).
- **EnOcean:** Anhalten oder Neustarten eines Gateways hängt nicht mehr, wenn ein Client nicht mehr liest (ein schlafender PC); das Speichern hing damit. Ein Client, der schneller sendet als das Gateway, wird nicht mehr ohne Grenze gepuffert.
- **Werkzeuge:** Ein unerwarteter Fehler beendet einen Lauf als fehlgeschlagen, statt ihn „laufend“ zu lassen und die Werkzeuge dieser Verbindung bis zu einem Neustart zu sperren (z. B. Baudraten-Erkennung an einem Gerät, das kein tty ist).

## 0.3.1 - 2026-10-22

Ein Durchgang über jede Seite der Oberfläche.

### Geändert

- **Verbindungen:** Jede Karte zeigt ihre Clients als kleinen Füllbalken und die Datenrate als Kurve der letzten Minute; eine Karte mit Problem zeigt ihren Zustand einmal (Streifen und Chip) mit einem ruhigen Satz darunter; der Kopierknopf ist ein Symbol, der Aufzeichnungs-Chip steht in der Chip-Zeile.
- **Detailseite:** Die Adressen zum Kopieren haben eine eigene Karte oben in der Seitenspalte; Live-Daten nutzen dieselben Richtungswörter und Zeilen zu sechzehn Bytes wie die Mitschnitt-Seite, lassen sich auf eine lebende Zeile einklappen und brechen lange Zeilen um; eine an 127.x gebundene Verbindung sagt, dass sie nur von diesem Rechner erreichbar ist; der Kopf trägt einen kurzen Aufzeichnungs-Chip, der zum Mitschnitt führt; Seitenkarten mit kurzen Werkzeugknöpfen, einem beschrifteten Datendiagramm und „Letzte Ereignisse“ dieser Verbindung.
- **Modbus-Details:** eine Statuskarte (Anfragen pro Sekunde, Probleme nur als Chips) statt sechs Zählern; Clients und Units in einer Karte mit Tooltips an den Spaltenköpfen („Fehlerantworten“ statt „Exceptions“); die Verbindungskarte wandert in die Seitenspalte; die Formulare zum Lesen und Scannen passen in eine Zeile; „In Home Assistant verwenden“ beginnt mit der Integration des Geräts in der Oberfläche und behält das YAML als Rückfall; „1 Wiederholung“ statt „1 Wiederholungen“; die Live-Ansicht nennt den Client einmal, wenn nur einer fragt.
- **Bearbeiten-Seiten:** Serielle Verbindungen bekommen eine Karte Grundlagen mit dem Namen wie die anderen Arten; eine mitlaufende Leiste Löschen / Abbrechen / Speichern, ein Chip „Nicht gespeichert“, eine Rückfrage bei Abbrechen und eine Warnung, wenn der Tab mit Änderungen geschlossen wird; Vorlagen bei einer bestehenden Verbindung eingeklappt und eine Rückfrage, bevor eine Felder überschreibt; Pfeile an eingeklappten Karten; die Vorschau bleibt im Blick und sagt, wer sich verbinden darf; Antwort-Timeout und Wiederholungen bei Modbus stehen beim Gerät, die erweiterten Optionen sind gruppiert (Takt, Clients, Probe, Aufzeichnung), und die Sendepause von EnOcean steht beim Gateway. Eine Bind-Adresse 127.x sagt jetzt, dass nur dieser Rechner sich verbinden darf, und eine Warnung erscheint, wenn erlaubte Clients Netze nennen, die diese Adresse nie bedienen kann.
- **Import:** Inhalt ohne jede Verbindung bleibt mit einem Fehler im ersten Schritt; der erste Schritt nennt jedes Ding einmal und klappt die Liste der Formate weg; ein Konflikt-Chip je Inhaber und ein Hinweis je Gerät; Pfade brechen nicht mehr in kurzen Namen um; auf dem Handy bleiben die Schritte in einer Zeile, und jeder Eintrag ist eine Karte; die Fußzeile mit „Übernehmen“ bleibt am Ende einer langen Liste stehen.
- **Ereignisse und Mitschnitt:** Live und Historie teilen eine Filterleiste und ein Zeilenformat; Verbindungen als Chip-Leiste auf der Mitschnitt-Seite; Hex und ASCII in Zeilen zu sechzehn Bytes bei jeder Breite; Richtungs-Abzeichen nutzen die Wörter des Aufzeichnungsschalters.
- **Einstellungen:** Der Speichern-Knopf jeder Karte ist erst nach einer Änderung aktiv und sagt „Nicht gespeichert“; die Navigation an der Seite markiert den sichtbaren Abschnitt; die Karte für eine eigene ser2net.yaml bietet „Aus den Formularen“ und „Eigene Datei“, den Editor auf Wunsch und eine Prüfung beim Tippen, mit gesperrtem Speichern bei Fehlern.
- **Lesbarkeit:** Hinweise, Feldbeschriftungen und Tabellenköpfe sind 13 px, der graue Text hat in hell und dunkel mehr Kontrast.

## 0.3.0 - 2026-10-22

### Neu

- **Heimnetz:** Wer als „LAN“ zählt, ist jetzt eine Liste unter **Einstellungen → Netzwerk → Erlaubte Netze**. Das eigene Netz des Rechners ist vorgegeben, weitere Netze lassen sich hinzufügen; Home Assistant und die Apps sind immer erlaubt. Bestehende Installationen behalten die privaten Bereiche.
- **Sichern und Wiederherstellen:** **Einstellungen → Sichern und Übertragen** speichert alle Verbindungen (seriell, Modbus, EnOcean) und die Einstellungen als eine Datei und stellt sie nach einer Vorschau und einer Bestätigung wieder her. Import und ser2net-Export sind dorthin umgezogen; der Export sagt, dass er nur die seriellen Verbindungen enthält.
- **Rückfragen:** vor dem Ausschalten einer Verbindung mit Clients, bevor ein Import Verbindungen ersetzt, und vor dem Löschen.

### Geändert

- **Übersicht der Verbindungen:** ein Statusband statt vier Kacheln, Probleme zuerst mit eigenem Filter und einem nächsten Schritt, kompakte Karten, die als Ganzes die Details öffnen.
- **Seiten einer Verbindung:** Gerät vor Name, serielle Schnittstelle und Netzzugang als eigene Karten, Block für Meldungen, „Aktiv“ als eigener Schalter, Löschen abgesetzt; die Detailseite zeigt eine Verbindungskarte mit den echten Netzen und der Erreichbarkeit je Ziel.
- **Ereignisse:** Protokoll nach Zeit sortiert mit Tageszeilen, Stufen-Knöpfe mit Anzahl, Verbindungsfehler in einfachen Worten, Namen verweisen auf die Verbindung, beschriftete Balken der Historie.
- **Mitschnitt:** ein Aufzeichnungsschalter für die gewählte Verbindung in einfachen Worten, Live-Ansicht mit Zeilenzahl, Leeren und Zeiten in Millisekunden, aufgezeichnete Dateien nennen ihre Verbindung, Pfad zum Kopieren.
- **Import:** Konflikte in einfachen Worten, alle auswählen, die Verbindungen, die „Alle ersetzen“ entfernt, werden genannt, und der letzte Schritt zählt hinzugefügte, ersetzte und übersprungene Verbindungen.
- **Schmale Bildschirme:** Chips im Kopf brechen um, die Navigation passt in eine Zeile, die Mitschnitt-Seite wählt die Verbindung aus einer Liste. Meldungen der API und der Werkzeuge erscheinen auch auf Deutsch.

## 0.2.1 - 2026-10-22

### Neu

- **EnOcean:** Die Base-ID wird nach jedem Verbinden einmal vom Gateway gelesen (nichts geht über die Luft), sodass sie in der Liste und auf der Detailseite steht, ohne dass jemand fragt.

### Geändert

- **Aussehen:** ein mitlaufender Kopf mit Reitern als Pillen, weichere Karten mit leichtem Schatten, Verbindungskarten mit farbigem Statusrand und einem Symbol für die Art; hell und dunkel.
- **EnOcean-Detailseite:** Funkbelegung und Nachlieferungspuffer sind zwei große Karten oben mit großer Zahl, einem Balken (Marke bei 80 % für die Funkbelegung), dem ältesten gepufferten Telegramm und einem Status in einfachen Worten (unter der Grenze, fast an der Grenze, sammelt, Programm verbunden, voll, aus).
- **Einstellungen:** Das Menü links bleibt beim Scrollen im Blick (wenn es neben dem Inhalt steht).
- **Adressen:** Eine Adresse, die nicht erreichbar ist, sagt jetzt warum (an diesen Rechner gebunden, erlaubte Clients, Netzwerk-Einstellung) und zeigt die Adresse.
- **Doku:** Der Reiter **Konfiguration** der App im Supervisor ist absichtlich leer; DOCS und beide READMEs verweisen jetzt auf den Eintrag **Device Proxy** in der Seitenleiste, wo alles eingerichtet wird.

## 0.2.0 - 2026-10-21

### Neu

- **EnOcean-Gateways** (übernommen aus der EnOcean-Proxy-App, die diese ersetzt)
  - Eine dritte Art Verbindung: ein FAM-USB-, FAM14-, FGW14-USB-, USB300/TCM310-, MGW-ETH- oder Symcon-LAN-Gateway für mehrere Programme, über USB oder TCP, ESP2 oder ESP3, mit Vorlagen.
  - Ganze Frames der Reihe nach mit Pause, die Antworten des Gateways an das Programm, das gefragt hat, kein Echo an die anderen, langsame Programme getrennt, verbindet sich von selbst neu.
  - Nachliefern für die EnOcean-Eltako-Integration (`EOPX REPLAY`, mit Empfangszeiten), wahlweise über einen Neustart der App auf der Platte behalten.
  - Erkennung durch die Integration und ein nur lesbarer Status für ihre Gateway-Karten (Port 9199, nur Home Assistant und die Apps); Einstellungen unter **Einstellungen → EnOcean**.
  - Detailseite: Probleme in einfachen Worten, Live-Frames mit Sender und Art (Suche, Richtung, Filter nach Sender, Kopieren, ins Senden übernehmen), Funkbelegung gegen die 1-%-Grenze, Zähler, Nachlieferungspuffer, Base-ID; Werkzeuge: Gateway-Test, einen geprüften Frame senden (Prüfsumme ergänzt oder korrigiert), Aufzeichnungen als JSON-Zeilen mit einer Sperre für PCT14.
  - Neue Gateways nehmen nur Home Assistant und die Apps an (die App läuft im Netz des Rechners).
  - Benachrichtigung bei 80 % Funkbelegung; MQTT-Entitäten: erreichbar, Telegramme, Funkbelegung.
  - Umzug: Die Optionen der EnOcean-Proxy-App werden aus Home Assistant geholt, eingefügt oder in `import/enocean_proxy.yaml` gelegt.
- **Für alle Verbindungen:** Filter-Chips nach Art über der Liste; eine laufende Aufzeichnung erscheint im Kopf.

### Behoben

- **Modbus TCP:** Eine Modbus-TCP-Verbindung, die ohne Gerätefeld gespeichert war, ließ sich nicht laden.

## 0.1.0 - 2026-10-21

Erste Version.

### Neu

- **Verbindungen:**
  - Eingerichtet in einer Weboberfläche in der Seitenleiste: Geräteliste mit stabilen Namen, Vorlagen, alle wichtigen ser2net-Optionen, Live-Vorschau der `ser2net.yaml`.
  - Speichern baut nur die geänderte Verbindung neu auf; die anderen behalten ihre Clients.
  - Clients standardmäßig nur aus privaten Netzen; ein Gerät offen halten; Clients, die nicht mehr lesen, werden gemeldet.
- **Modbus-Proxy:**
  - Ein Modbus-Gerät für mehrere Modbus-TCP-Clients: Modbus TCP, Modbus RTU an einem RS485-Adapter, RTU über TCP; Anfragen der Reihe nach, jede Antwort an den Client, der gefragt hat.
  - Timeout, Wiederholungen, Pause nach dem Verbinden und zwischen Anfragen; Gateway-Fehlerantworten, wenn das Gerät nicht antwortet.
  - Status mit Anfragen, unbeantworteten Anfragen und Antwortzeit, auch je Unit-ID; dekodierte Anfragen und Antworten im Mitschnitt.
  - Schreibzugriff je Verbindung, ein Zwischenspeicher für Lesezugriffe, Clients der Reihe nach, bis zu 4 Verbindungen zu einem Gerät im Netz, Unit-IDs umgeschrieben, ein wahlweiser Probe-Lesezugriff.
  - Werkzeuge: Register lesen, den Bus nach Unit-IDs scannen.
- **Import und Export:**
  - ser2net 4 `ser2net.yaml` (Version 1 und 2), ser2net 3 `ser2net.conf` und die Optionen von ha-modbusproxy (oder eine modbus-proxy-Datei), mit Vorschau; Export als `ser2net.yaml`; oder die eigene Datei unverändert verwenden.
- **Status und Diagnose:**
  - Gerät, Clients, Datenrate, letzte Daten, Leitungsfehler vom Treiber, FTDI-Latenz.
  - Live-Daten und Mitschnitte, ohne einen Client-Platz zu belegen; Aufzeichnen ohne Trennen.
  - Werkzeuge für Stromzähler: SML (mit CRC-Prüfung) und D0, Baudraten-Erkennung.
  - Ereignisse und 30-Tage-Historie, Konfig-Historie mit Wiederherstellen, Diagnose-ZIP.
- **Home Assistant:**
  - Benachrichtigungen (wahlweise an einen Notify-Dienst).
  - Entitäten über MQTT-Discovery, ein Gerät je Verbindung mit Schalter (bei Modbus: erreichbar, Anfragen, unbeantwortete Anfragen, Antwortzeit).
- **Unter der Haube:**
  - ser2net 4.6.8 und gensio 3.0.4 aus ihren Releases gebaut; Admin-Schnittstelle über einen Socket in der App; Neustarts, Gesundheitsprüfung und Sicherungen abgedeckt.
  - Deutsch und Englisch, hell und dunkel, Handy-Breite.
