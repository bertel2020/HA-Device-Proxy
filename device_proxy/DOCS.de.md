# Device Proxy

*[English version](DOCS.md)*

Die App teilt Geräte mit mehreren Programmen gleichzeitig:

- **Serielle und USB-Geräte**, die an Home Assistant hängen, über TCP-Ports mit
  [ser2net 4](https://github.com/cminyard/ser2net). Integrationen von Home Assistant, andere Apps
  und Programme im Netz verbinden sich mit diesen Ports, statt das Gerät selbst zu öffnen –
  etwa Z-Wave JS (`tcp://host:port`), ZHA und andere Integrationen auf Basis von pyserial
  (`socket://host:port`) oder eine Zähler-Integration (Host und Port).
- **Modbus-Geräte** über den eigenen Modbus-Proxy der App: ein Gerät, das nur eine Verbindung
  annimmt (viele Wechselrichter, Wärmepumpen, Batterien, Energiezähler), oder ein RS485-Bus mit
  Modbus RTU bekommt einen Modbus-TCP-Port, den mehrere Clients gleichzeitig nutzen – wie die
  App ha-modbusproxy, dazu Modbus RTU (siehe [Modbus-Geräte](#modbus-geräte)).
- **EnOcean-Gateways** (FAM-USB, FAM14, FGW14-USB, USB300, MGW-ETH …) über den eigenen
  EnOcean-Proxy der App: mehrere Programme (Home Assistant, eo_man, PCT14) teilen sich ein
  Gateway (siehe [EnOcean-Gateways](#enocean-gateways)).

Eingerichtet wird alles auf der Seite der App in der Seitenleiste (**Device Proxy**). Die App hat
keine eigenen Optionen; ihr Reiter **Konfiguration** im Supervisor bleibt deshalb mit Absicht leer.
Stattdessen **Device Proxy** in der Seitenleiste öffnen.

Diese Anleitung ist eine Übersetzung der [englischen Fassung](DOCS.md). Home Assistant zeigt im
Reiter „Dokumentation“ der App die englische Fassung an.

## Erste Schritte

1. Die App installieren und starten; **Device Proxy** in der Seitenleiste öffnen.
2. Entweder die vorhandene Konfiguration **importieren** (**Einstellungen → Sichern und
   Übertragen → Importieren**: ser2net-4-`ser2net.yaml`, ser2net-3-`ser2net.conf` oder die
   Optionen von ha-modbusproxy), oder **eine Verbindung hinzufügen**: serielles Gerät oder
   Modbus-Gerät wählen; bei einem seriellen Gerät eine Vorlage (Zähler SML oder D0, Z-Wave- oder Zigbee-Stick,
   allgemein), das Gerät aus der Liste und einen TCP-Port; bei einem Modbus-Gerät seine Adresse
   (oder den RS485-Adapter) und den Port für die Clients.
3. Die Clients auf die Adresse einstellen, die die Verbindung zeigt (**Details → Adressen**):

| Client | Adresse |
|---|---|
| Integrationen von Home Assistant | `127.0.0.1` und der Port |
| Andere Apps (z. B. Z-Wave JS UI) | `172.30.32.1` und der Port – im Supervisor-Netz ist 127.0.0.1 die App selbst |
| Andere Rechner | die LAN-Adresse des Hosts und der Port |

Speichern baut nur diese Verbindung neu auf; alle anderen behalten ihre Clients. Das Formular
warnt, wenn der gewählte Port schon von einem anderen Programm belegt ist (z. B. einem noch
laufenden ha-modbusproxy); speichern geht trotzdem, die Verbindung startet, sobald der Port frei
ist.


## Verbindungen

**Vorlagen** füllen die Felder aus; alles bleibt änderbar. **Gerät**: die Liste zeigt jeden
seriellen Adapter mit seinem stabilen Namen (`/dev/serial/by-id/…`), Hersteller, Produkt und
Seriennummer. Gleiche Adapter ohne Seriennummer (viele CH340) werden über ihren USB-Port
unterschieden (`/dev/serial/by-path/…`); die App warnt bei ihnen.

**Eine serielle Brücke im Netz**: unter **Gerät → Woher die Daten kommen → Netzwerk (TCP)** holt
eine Verbindung ihre Daten von einer seriellen Brücke statt von einem Gerät dieses Hosts, z. B.
einem ESPHome-Stream-Server, einem Tasmota-Lesekopf oder einem USR-TCP232. Solche Brücken nehmen
meist nur einen Client an; die App verbindet sich mit der Brücke (nur solange sie selbst Clients
hat) und teilt sie. Baudrate und Format werden an der Brücke eingestellt; die Werkzeuge, die das
Gerät selbst brauchen (Baudrate erkennen, Leitungsfehler, FTDI-Latenz), gibt es dann nicht.

**Ein Adapter an einem anderen Port**: die App merkt sich, welchen Adapter jede Verbindung hatte
(Hersteller, Produkt und Seriennummer). Fehlt das Gerät und steckt ein freier Adapter derselben
Art (an einem anderen USB-Port, in der VM unter einer anderen Nummer), sagen das die Seite und
die Karte der Verbindung, mit einem Button zum Übernehmen; bei mehreren solchen Adaptern wählst
du den richtigen. Ein Adapter mit Seriennummer wird nur angeboten, wenn die Seriennummer passt.

**Erweitert** enthält die Optionen von ser2net, alle optional: Flusskontrolle (RTS/CTS,
XON/XOFF), Modemleitungen (`local`), DTR/RTS beim Öffnen, RS485, Timeout, Wiederholzeit,
erlaubte Clients (`remaddr`), Banner, Texte beim Öffnen und Schließen, `nodelay`, eine
Bind-Adresse, FTDI-Latenz und weitere ser2net-Optionen als Zeilen `name: wert`. Das Formular
zeigt beim Tippen den entstehenden Teil der `ser2net.yaml`.

### Wer sich verbinden darf

**Einstellungen → Netzwerk** gilt für alle Verbindungen ohne eigene Bind-Adresse oder
`remaddr`:

- **Nur Home Assistant** – 127.0.0.1, nur dieser Host.
- **Home Assistant und Apps** – auch die anderen Apps (z. B. Z-Wave JS UI), 127.0.0.0/8,
  172.30.32.0/23 und fd0c:ac1e:2100::/48 (IPv6), aber nichts aus dem LAN.
- **Heimnetz** (Standard) – Home Assistant, seine Apps und die Netze unter **Erlaubte Netze**.
  „Mein Netz“ (das Netz des Hosts, vom Supervisor gelesen) ist vorgegeben; weitere Netze wie
  `192.168.80.0/24` lassen sich hinzufügen, oder die privaten Bereiche. Eine leere Liste lässt
  nur Home Assistant und die Apps herein. Installationen von vor dieser Liste behalten die
  privaten Bereiche (10/8, 172.16/12, 192.168/16).
- **Jeder** – keine Grenze. ser2net hat keine Anmeldung: wer den Port erreicht, kann das Gerät
  lesen und steuern.

Ein **Z-Wave- oder Zigbee-Stick** beginnt mit einer eigenen Vorgabe, weil er ohne Anmeldung Befehle annimmt:
nur Home Assistant und die Apps (`127.0.0.1, 172.30.32.0/23` unter **Erweitert → Erlaubte
Clients**). Ist das Feld leer, entscheidet die Netzwerk-Einstellung.

Die Vorlage **Zigbee** erlaubt einen Client, denn ein Zigbee-Netz hat genau ein Programm, das den
Koordinator führt. ZHA verbindet sich mit `socket://host:port`, Zigbee2MQTT mit `tcp://host:port`.
Sie stellt 115200 Baud ein, das passt für die meisten Sticks; ein Stick, der Hardware-Flusskontrolle
braucht, bekommt RTS/CTS unter **Erweitert**.

### Mehrere Clients an einem Gerät

Eine Verbindung kann mehrere Clients zulassen. Jeder Client bekommt alle Daten des Geräts; was
die Clients senden, geht unverändert und ungeordnet ans Gerät. Das passt zu Geräten, die nur
senden (Zähler, GPS). Bei Geräten, die auf Anfragen antworten (Z-Wave, viele Wärmepumpen), geht
es nur, solange jeweils ein Client sendet; für Modbus RTU stattdessen eine Modbus-Verbindung
nehmen, die die Anfragen ordnet.

Hört ein Client auf zu lesen, bremst ser2net **alle** Clients dieser Verbindung. Die App meldet
einen solchen Client; auf Wunsch trennt sie die Clients der Verbindung (ser2net kann keinen
einzelnen trennen), damit sie sich neu verbinden.

### Gerät offen halten

ser2net öffnet ein Gerät nur, solange ein Client verbunden ist. Mit **Gerät offen halten** bleibt
die App selbst verbunden, sodass Warnungen „keine Daten“, Leitungsfehler und die Werkzeuge auch
ohne Client funktionieren. Das belegt einen der Client-Plätze der Verbindung.

## Modbus-Geräte

Eine Modbus-Verbindung lauscht auf einem eigenen TCP-Port und spricht Modbus TCP mit ihren
Clients (die Modbus-Integration von Home Assistant, SolarEdge Modbus, evcc, ioBroker …). Alle
ihre Anfragen gehen nacheinander über eine einzige Verbindung ans Gerät; jede Antwort geht
zurück an den Client, der gefragt hat. Die App nummeriert die Anfragen zum Gerät selbst, sodass
eine verspätete Antwort auf eine abgelaufene Anfrage nie beim nächsten Client landet. Wartende
Clients kommen abwechselnd dran: ein Client, der ohne Pause fragt, kann die anderen nicht
aufhalten.


**Geräteprofile** tragen Port und Zeiten für Geräte eines Herstellers ein (SolarEdge, Huawei
SUN2000, Fronius, SMA, Kostal Plenticore, Sungrow, Victron GX). Es sind Startwerte, die änderbar
bleiben; die Unit-ID stellt der Client ein, das Profil nennt die übliche. Erkennt **Bus scannen**
einen Hersteller, bietet es dessen Zeiten an; der Port bleibt dabei, wie er ist.

**Verbindung zum Gerät**

| Art | Für | Einstellungen |
|---|---|---|
| Modbus TCP | ein Gerät im Netz | Adresse und Port (502) |
| Modbus RTU (seriell) | ein RS485-Adapter an diesem Host | Gerät, Baudrate und Format |
| RTU über TCP | ein RS485-Ethernet-Wandler im transparenten Modus | Adresse und Port |
| Am RS485 mithören | ein Bus, der schon einen Master hat | Gerät, Baudrate und Format, wie lange Werte gültig bleiben |

Bei Modbus RTU öffnet die App den Adapter selbst (nicht über ser2net) und hält die Pause von 3,5
Zeichen zwischen den Frames ein, die RTU verlangt. Unit 0 ist ein Broadcast: er wird gesendet,
niemand antwortet. RTU hat keine Transaktions-IDs, also muss eine Antwort zu ihrer Anfrage
passen (Unit, Funktion, Byte-Anzahl, das Echo eines Schreibzugriffs), und nach einem Timeout
oder einer kaputten Antwort bekommt die Leitung eine halbe Sekunde für späte Bytes, bevor die
nächste Anfrage kommt – eine verspätete Antwort landet nie beim falschen Client.

**Am RS485 mithören** ist für einen Bus, auf dem schon ein Master fragt, z. B. ein
Wechselrichter, der seinen Energiezähler abfragt, oder die Steuerung einer Wärmepumpe ihre
Module: ein zweiter Master würde sie stören. Die App hört nur zu, sie sendet nie auf dem Bus. Sie
trennt die Frames an ihrer CRC (die Pausen zwischen Frames gehen hinter USB-Adaptern verloren),
ordnet jedem Lesezugriff (Funktionen 3 und 4) seine Antwort zu und merkt sich die Register, auch
die, die der Master schreibt (6, 16). Modbus-TCP-Clients lesen sie: ein Lesezugriff wird
beantwortet, wenn jedes gefragte Register innerhalb von „Werte gültig für“ (Standard 60 s) zu
hören war, sonst mit Fehler 0B, wie von einem Gateway, dessen Gerät weg ist. Lesen lässt sich nur,
was der Master liest; Schreiben wird mit Fehler 01 abgewiesen. Die Status-Karte zeigt die
gehörten Frames und welche Register welcher Units bekannt sind.

**Einstellungen**: Port für die Clients (Standard 502; jede Verbindung braucht ihren eigenen),
Anzahl der Clients, Antwort-Timeout, weitere Versuche, eine Pause nach dem Verbinden
(`connection_time` von ha-modbusproxy, für Geräte, die einen Moment brauchen) und eine Pause
zwischen Anfragen für langsame Geräte. Unter **Erweitert**: untätige Clients trennen und den
ältesten Client ersetzen, wenn alle Plätze belegt sind. Erlaubte Clients und eine Bind-Adresse
stehen in der Karte **Zugriff im Netz** – die Netzwerk-Einstellung gilt wie bei seriellen Geräten.

**Prüfabfrage**: auf Wunsch liest die App nach einer eingestellten Zeit ohne Anfragen ein
Register (Unit, Funktion 3 oder 4, Adresse). Der Zustand „erreichbar“ stimmt dann auch ohne
Clients, und Geräte, die untätige Verbindungen schließen, behalten ihre. Eine Prüfabfrage ohne
Antwort (nach ihren Wiederholungen) markiert das Gerät sofort als nicht erreichbar.
Prüfabfragen werden getrennt gezählt, nicht als Anfragen.

**Zwischenspeicher**: lesen mehrere Clients dieselben Register (Home Assistant, evcc, eine
SolarEdge-Integration …), lässt eine Speicherzeit von z. B. 500 ms das Gerät jeden Lesezugriff
in dieser Zeit nur einmal beantworten; derselbe Lesezugriff, während einer unterwegs ist, wartet
auf dessen Antwort. Zwischengespeichert werden nur Lesezugriffe (Funktionen 1–4), nie
Fehlerantworten; ein Schreibzugriff leert den Speicher. Standardmäßig aus.

**Verbindungen zum Gerät**: bei einem Netzwerkgerät, das mehrere Verbindungen gleichzeitig
zulässt (bis zu 4), können die Anfragen parallel über so viele Verbindungen laufen – schneller
bei vielen Clients. Bei Geräten, die nur eine Verbindung annehmen (die meisten Wechselrichter),
auf 1 lassen; Modbus RTU hat immer eine Leitung.

**Schreibzugriff**: Modbus hat keine Anmeldung – wer den Port erreicht, könnte Register ändern.
Je Verbindung: **Alle Clients** dürfen schreiben (wie bei ha-modbusproxy), **Nur diese**
Adressen oder Netze, oder **Niemand**. Eine neue Verbindung beginnt mit „Nur diese“: `127.0.0.1`
(Home Assistant) und `172.30.32.0/23` (andere Apps); aus ha-modbusproxy importierte Verbindungen
behalten „Alle Clients“, sodass sich für ihre Clients nichts ändert. Durch kommen nur bekannte
Lesezugriffe (Funktionen 1–4, 7, 11, 12, 17, 20, 24, das Diagnose-Echo und das Lesen der
Geräte-Identifikation), und nur mit genau der Länge dieser Anfrage; alles andere –
Schreibzugriffe, Herstellerfunktionen wie Huaweis 0x41 – bekommt Fehler 0x01 und wird gezählt
und protokolliert. Lesen bleibt allen erlaubten Clients offen. Eine Verbindung, die ohne dieses
Feld angelegt wird (über die API, per Skript), beginnt ebenfalls mit „Nur diese“; eine, die
gespeichert wurde, bevor es das Feld gab, behält „Alle Clients“. Die Seite der Verbindung zeigt,
wer wirklich schreiben darf: jeder Client, der sich verbinden darf, die eingetragenen, niemand,
wenn bei „Nur diese“ keiner eingetragen ist, die erlaubten Register und bei Units anderer
Verbindungen auch deren Regel.

**Erlaubte Register beim Schreiben** (bei Schreibzugriff „Alle Clients“ oder „Nur diese“):
Adressen und Bereiche, z. B. `40100-40120 47000`. Ein Schreibzugriff, der etwas außerhalb ändert
oder dessen Adressen sich nicht bestimmen lassen (eine eigene Funktion eines Herstellers), wird
mit Fehler 02 abgewiesen; so darf z. B. evcc die Laderegister eines Wechselrichters setzen, aber
sonst nichts. Coils und Register zählen gleichermaßen nach ihrer Adresse. Die Karte
**Schreibzugriffe** auf der Seite der Verbindung listet die letzten 200 Schreibzugriffe der
Clients: wann, wer, Unit, Funktion, Adresse, Werte und ob sie geschrieben, vom Gerät abgelehnt,
nicht erlaubt oder außerhalb der erlaubten Register waren.

**Register je Client**: eine Zeile je Client unter den Registern, eine Adresse oder ein Netz und
dann seine Register, `*` für alle oder `none` für keine; z. B. lässt `192.168.1.20 40100-40120` evcc
die Laderegister setzen, während `127.0.0.1 *` Home Assistant freie Hand lässt. Die erste passende
Zeile gilt statt der allgemeinen Register. Eine Zeile erlaubt niemandem das Schreiben: Wer überhaupt
schreiben darf, regelt weiter der Schreibzugriff. **Zugriff prüfen** nennt die Zeile, die gilt.

**Units anderer Verbindungen** (unter **Erweitert**): ein Port für mehrere Geräte, denn viele
Energiemanager und evcc erwarten ein einziges Modbus-Gateway. Jede Zeile nennt eine hier
gefragte Unit, eine andere Modbus-Verbindung der App und die Unit dort, z. B. Unit 2 → „Zähler“
(Unit 1). Ein Client, der Unit 2 fragt, bekommt die Antwort vom Gerät dieser Verbindung, der
Reihe nach mit deren Clients und mit deren Zwischenspeicher; ein Schreibzugriff muss beiden
Verbindungen erlaubt sein (Schreibzugriff und Register). Nur eine Stufe: eine Verbindung, deren
Units woanders hingeleitet werden, leitet selbst keine weiter. Solange die andere Verbindung aus
ist, bekommt der Client Fehler 0A.

**Unit-IDs**: unter **Erweitert** lässt sich die Unit, die ein Client fragt, umschreiben
(`client=gerät`, z. B. `1=3, 2=5`), für Clients, die immer Unit 1 fragen, während das Gerät auf
einer anderen antwortet. Wird aus `unit_id_remapping` von modbus-proxy übernommen.

**Wenn das Gerät nicht antwortet**, bekommt der Client den Modbus-Fehler 0x0B („gateway target
device failed to respond“), wenn es nicht erreichbar ist 0x0A („gateway path unavailable“) – die
Antworten, die ein Modbus-Gateway gibt; der Client bleibt verbunden. Nach drei Anfragen in Folge
ohne Antwort gilt das Gerät als nicht erreichbar (Ereignis, Benachrichtigung, Entität). Ein nicht
erreichbares Gerät wird alle 30 Sekunden erneut versucht; ein Gerät, das eine untätige Verbindung
geschlossen hat, wird mit der nächsten Anfrage wieder verbunden.

**Status**: erreichbar, Clients mit ihren Anfragen, Anfragen, beantwortet, Fehlerantworten,
Timeouts, Fehler, Warteschlange und Antwortzeit (Mittel und Maximum), der letzte Fehler; je
Unit-ID (jedes Gerät an einem RS485-Bus) Anfragen, Fehlerantworten, unbeantwortete Anfragen und
Antwortzeit. Nach 50 Anfragen gibt die Karte **Tipps** aus diesen Zahlen: ein längerer Timeout,
wenn Antworten nahe daran kommen, ein kürzerer, wenn das Gerät immer schnell antwortet (damit ein
Ausfall früher auffällt), ein Zwischenspeicher, wenn mehrere Clients fragen, und was eine lange
Warteschlange oder viele Fehlerantworten bedeuten. Es sind Vorschläge, keine Einstellungen:
prüfe sie gegen die Dokumentation des Geräts. Die Live-Ansicht und die Mitschnitte zeigen jede
Anfrage und Antwort als Hex mit Unit, Funktion, Register und Anzahl (z. B.
`unit 1 · FC03 read holding registers · @40000 ×4`).

**Werkzeuge** in den Details einer Modbus-Verbindung:

- **Register lesen**: Unit, Funktion (Holding- oder Input-Register, Coils, Discrete Inputs),
  Adresse (ab 0, wie im Frame) und Anzahl; die Werte vorzeichenlos, vorzeichenbehaftet und als
  Hex. Die Anfrage wartet mit denen der Clients, bis sie dran ist, und nutzt den
  Zwischenspeicher nicht. **Werte deuten** liest die Register als 16-, 32- oder 64-Bit-Ganzzahlen,
  Gleitkommazahlen oder Text, mit Register- und Byte-Reihenfolge („swap“) und einem Faktor wie in
  der Modbus-Integration von Home Assistant, und liefert den passenden Sensor zum Kopieren in die
  `configuration.yaml`.
- **Register schreiben**: Funktion 5 oder 15 (Coils) oder 6 oder 16 (Register), Adresse und
  Wert(e), mehrere durch Kommas getrennt. Ein Dialog fragt vorher nach; danach wird der Wert
  zurückgelesen und verglichen. Jeder Schreibzugriff ist ein Ereignis im Protokoll. Das Werkzeug
  bleibt gesperrt, wenn der Schreibzugriff der Verbindung „Niemand“ ist.
- **Bus scannen**: welche Unit-IDs antworten (es liest Register 0, eine Fehlerantwort zählt auch
  als Antwort). Die gefundenen Units lassen sich in „Register lesen“ übernehmen. Danach wird jede
  gefundene Unit gefragt, wer sie ist: ihre Geräte-Identifikation (Funktion 43) und, bei
  Wechselrichtern und Zählern, das SunSpec-Common-Model an Register 40000, 0 oder 50000.
  Hersteller, Modell und Version werden angezeigt, dazu eine passende Integration, wo eine
  bekannt ist.

- **Zugriff prüfen**: IP-Adresse eines Clients, Unit, Funktion und Register; die Antwort sagt,
  ob er sich verbinden, lesen und schreiben darf und welche Regel entscheidet – die
  Bind-Adresse, die erlaubten Clients der Verbindung, die Netzwerk-Einstellung, der
  Schreibzugriff, die erlaubten Register oder eine Unit, die an eine andere Verbindung geht. Es
  wird nichts gesendet; ein Client auf diesem Rechner zählt als 127.0.0.1. Geprüft werden die
  gespeicherten Regeln, dieselben, die der Proxy anwendet.

Anfragen der Werkzeuge zählen nicht als die der Clients. Nur „Register schreiben“ ändert das
Gerät.

**Register als Entitäten**: Für ein Gerät ohne Integration kann die App Register selbst lesen
und als Sensoren über MQTT anbieten, ganz ohne YAML. Unter **Register lesen → Werte dekodieren**
den richtigen Typ, Swap und Faktor finden, dem Wert Name, Einheit und Geräteklasse geben und
**Als Entität anlegen** drücken. Die Liste steht unter **Erweitert → Register als Entitäten**, eine
Zeile je Entität (`Unit Funktion Adresse Typ Swap Faktor Einheit Klasse Name`, z. B.
`1 3 40083 int16 none 0.1 W power AC-Leistung`, `-` für keine Einheit oder Klasse), höchstens 50,
standardmäßig alle 30 Sekunden gelesen. Jedes Lesen geht der Reihe nach mit den Clients ans Gerät
und zählt nicht als deren Anfrage; bei einer Verbindung, die am RS485-Bus mithört, kommen die Werte
aus dem Gehörten, und es wird nichts gesendet. Solange das Gerät nicht erreichbar ist, sind die
Entitäten unbekannt. Eine Einheit, die nicht zur Geräteklasse passt, lehnt Home Assistant ab und
meldet das in seinem Log.

**Verwendung in Home Assistant**: die meisten Geräte haben eine eigene Integration (z. B.
SolarEdge Modbus). Sie unter **Einstellungen → Geräte & Dienste → Integration hinzufügen**
hinzufügen, die Netzwerkverbindung (Modbus TCP) wählen und Host und Port eintragen, die die
Detailseite zeigt (`127.0.0.1` und der Port der Verbindung, jeweils mit Kopier-Button). Die
Unit-ID (in manchen Integrationen Geräte-ID genannt) ist die des Geräts, meist 1. Nur wenn keine
Integration das Gerät unterstützt, einen Modbus-Hub in der `configuration.yaml` anlegen: die
Detailseite hat den Ausschnitt zum Kopieren (`type: tcp`, Host, Port); die Sensoren so ergänzen,
wie die Dokumentation der Modbus-Integration es beschreibt (`address` und `device_address`, die
Unit-ID).

Speichern startet nur Modbus-Verbindungen neu, deren Gerät oder Proxy-Einstellungen sich
geändert haben; ihre Clients verbinden sich neu. Name, Mitschnitt und Benachrichtigungen ändern
sich ohne Neustart.

## EnOcean-Gateways

Eine EnOcean-Verbindung teilt ein EnOcean-Gateway (FAM-USB, FAM14, FGW14-USB, USB300/TCM310,
PioTek MGW-ETH, Symcon LAN …) mit mehreren Programmen: der
[Integration EnOcean Eltako](https://github.com/bertel2020/HA-Enocean-Eltako), der alten
Integration `eltako`, eo_man oder PCT14 über das Netz. Sie übernimmt alles, was die
[App EnOcean Proxy](https://github.com/bertel2020/HA-Enocean-Proxy) getan hat (ein Import der
Optionen dieser App wird nicht angeboten). Die App öffnet das Gateway selbst (nicht über ser2net)
und bietet es auf einem TCP-Port als rohe ESP2- oder ESP3-Frames an, wie ser2net es täte.

- Jedes Telegramm vom Gateway geht an jedes Programm. Telegramme, die ein Programm sendet, werden
  eingereiht und gehen einzeln und ganz ans Gateway, mit einer kurzen Pause (**Pause zwischen
  Sendungen**), sodass sich zwei Programme nie vermischen. Telegramme werden nicht an die anderen
  Programme gespiegelt.
- Die Antwort des Gateways auf einen Befehl (Base-ID, Einstellungen …) geht an das Programm, das
  gefragt hat; FAM14-Busverkehr (ESP2 ORG ≥ F0) geht an alle.
- Solange das Gateway weg ist, bleiben die Programme verbunden und ihre Telegramme werden
  verworfen; die App verbindet sich selbst neu (1, 2, 5, 10, 30 s).
- Ein Programm, das nicht mehr liest, wird getrennt, bevor sich seine Daten stauen (256 KiB).

**Vorlagen** setzen Protokoll, Modell, Baudrate und Art der Verbindung; alles bleibt änderbar:

| Vorlage | Protokoll | Modell | Verbindung |
|---|---|---|---|
| FAM-USB | ESP2 | `fam_usb` | USB, 9600 Baud |
| FAM14, FGW14-USB | ESP2 | `fam14`, `fgw14_usb` | USB, 57600 Baud |
| USB300 / TCM310 | ESP3 | `esp3` | USB, 57600 Baud |
| PioTek MGW-ETH | ESP3 | `mgw_eth` | TCP, Port 5100 (nur eine Sitzung: über diese App teilen) |
| Symcon LAN | ESP3 | `symcon_lan` | TCP, Port 5000 |

**Modell**: das Modell des Gateways geht mit der Erkennung an die Integration EnOcean Eltako
(Eltako FAM-USB, FGW14-USB oder FAM14, PioTek MGW-ETH, Symcon LAN oder ein anderes ESP2- oder
ESP3-Gateway). Die App kann es nicht selbst erkennen, da sie nur Bytes weiterreicht: die Vorlage
setzt es, und das Feld **Modell** unter „Gateway“ ändert es. Es muss zum Protokoll passen: ESP2
für `fam_usb`, `fgw14_usb`, `fam14` und `esp2`, ESP3 für `mgw_eth`, `symcon_lan` und `esp3`; das
Feld bietet nur die des gewählten Protokolls an. Leer geht die Erkennung ohne Modell. Gateways,
die vor Version 1.0.0 gespeichert wurden, bekommen das Modell ihrer Vorlage, wenn es passt.

**Wer sich verbinden darf**: neue Gateways folgen der Netzwerk-Einstellung wie die anderen Arten,
sodass sich ein PC mit eo_man oder PCT14 im Heimnetz sofort verbinden kann. Um ein Gateway
einzuschränken, Adressen oder Netze unter **Erlaubte Clients** eintragen oder „Nur Home
Assistant und Apps“ drücken (`127.0.0.1, 172.30.32.0/23`). Home Assistant erreicht ein erkanntes
Gateway über den Hostnamen der App, also die LAN-Adresse des Hosts; es kommt deshalb von dieser
Adresse und nicht von 127.0.0.1. Eine Verbindung vom Host an seine eigene Adresse zählt trotzdem
als 127.0.0.1 (auch für den Status-Port und den Modbus-Proxy).

**Nachlieferung (Replay)**: die Integration EnOcean Eltako fragt nach jedem Verbinden danach
(`EOPX REPLAY TS`). Funktelegramme, die ankommen, während kein solches Programm verbunden ist,
z. B. während eines Neustarts von Home Assistant, werden aufbewahrt (standardmäßig 1000
Telegramme, 15 Minuten) und mit ihrer Empfangszeit übergeben. **Puffer auf Platte sichern**
bewahrt sie auch über einen Neustart dieser App hinweg auf (`/data/replay`).

**Erkennung und Status**: die App meldet ihre aktiven Gateways der Integration EnOcean Eltako mit
Name, Port, Protokoll und Modell, z. B. `{"name": "PioTek MGW-ETH", "port": 9100,
"protocol": "esp3", "model": "mgw_eth"}`; die Integration bietet jedes zur Einrichtung an, mit
eingeschalteter Nachlieferung. Ein Status zum Lesen (Port 9199, nur Home Assistant und die Apps)
versorgt die Gateway-Karten der Integration. Beides steht unter **Einstellungen → EnOcean**; dort
steht auch, wenn der Status-Port nicht geöffnet werden konnte. Zeigt die Integration „Proxy-Status
nicht erreichbar“, lässt er sich in der Terminal-App prüfen:
`curl http://<Hostname dieser App>:9199/api/status`. Aus dem LAN wird die Verbindung absichtlich
zurückgesetzt.

**Die Detailseite** zeigt in Klartext, was nicht stimmt (Gateway weg, Port belegt, Funkzeit,
Telegramme verworfen (auch wegen einer Sperre), Programme abgewiesen oder getrennt, kein Programm
verbunden), jedes Telegramm live mit Art und Absender (Suche, Richtung, ein Klick auf eine ID
zeigt nur diesen Absender, kopieren, in „Senden“ übernehmen), die Funkbelegung der letzten Stunde
gegenüber dem 1-%-Limit (eine Benachrichtigung bei 80 %), Zähler und den Nachlieferungspuffer,
und die Base-ID, sobald das Gateway sie genannt hat. Werkzeuge:

- **Sender** (eine eigene Karte): jede seit dem Start gehörte Sender-ID mit ihrer Art (RPS, 1BS,
  4BS, VLD), wie viele Telegramme, wann zuletzt, über wie viele Repeater und, bei einem
  ESP3-Gateway, der Empfang in dBm (über −75 gut, unter −88 schwach); mit Ersatz-Gateway auch,
  welches Gateway sie gehört hat. „Neu“ markiert Sender, die erst mehr als 5 Minuten nach dem
  Start zu hören waren, sodass sich die ID eines neuen Tasters durch einmaliges Drücken findet;
  „eigen“ markiert den Base-ID-Bereich des Gateways.
  Mit **Namen bearbeiten** bekommt jeder Sender einen Namen, für alle Gateways, gemeinsam in
  einem Schritt gespeichert; **Als CSV herunterladen** gibt die Liste als Datei. Die Diagnose lässt
  die Namen weg.
- **Gateway-Test**: liest die Base-ID zehnmal; nichts geht über Funk.
- **Base-ID ändern**: setzt die Base-ID des Gateways (FF-80-00-00 bis FF-FF-FF-80, letztes Byte
  00 oder 80). Das Gateway speichert sie im Flash und erlaubt nur wenige Änderungen (10 bei
  TCM-300-Modulen wie dem USB300); ESP3-Gateways melden, wie viele übrig sind, angezeigt neben
  der Base-ID. Eingelernte Aktoren kennen die alte ID und müssen neu eingelernt werden.
- **Telegramm senden**: ein ganzes Telegramm als Hex, beim Tippen geprüft (Sync, Länge,
  ESP2-Prüfsumme, ESP3-CRCs), mit einem Button, der die Prüfsumme ergänzt oder korrigiert; die
  Antwort wird angezeigt.
- **Telegramme aufzeichnen (PCT14)**: eine einzelne Aufzeichnung jedes Telegramms in beide
  Richtungen als JSON-Zeilen (Zeit, Gateway, Richtung, Art, Programm, Hex) in den
  Mitschnitt-Ordner, höchstens 50 MB; aufgelistet, heruntergeladen und gelöscht auf der Seite
  **Mitschnitt**. Auf Wunsch darf währenddessen nur ein Programm senden, z. B. PCT14 beim Auslesen
  eines FAM14: die Telegramme der anderen Programme (auch Home Assistant) werden verworfen und
  danach nicht nachgesendet, die eigenen Werkzeuge der App senden währenddessen nicht.
  Auch die Prüfung für das Ersatz-Gateway ruht dann, und die Telegramme dieses Programms gehen
  nur an dieses Gateway, nie über das Ersatz-Gateway.

### Ersatz-Gateway

Ein zweites Gateway kann einspringen, wenn eines ausfällt. Beide müssen **dieselbe Base-ID**
melden: die Aktoren sind auf die Sender-IDs des ersten Gateways eingelernt (Base-ID + 0 … 127),
und nur ein Gateway mit dieser Base-ID sendet von ihnen. Die App setzt dafür keine Base-ID; sie
liest beide und vergleicht sie. Beide Gateways sprechen dasselbe Protokoll.

1. Das zweite Gateway als normale EnOcean-Verbindung einrichten und dort prüfen (Gateway-Test,
   Base-ID, Live-Telegramme).
2. Im Formular des ersten Gateways unter **Ersatz-Gateway** bei „Bei Ausfall übernimmt“ auswählen.
   Die App zeigt, ob die Base-IDs übereinstimmen, und fragt vor dem Speichern nach, weil das
   zweite Gateway seine Rolle wechselt.

Solange eine Verbindung Ersatz eines anderen Gateways ist, ist ihr Port geschlossen (verbundene
Clients werden getrennt), sie wird der Integration EnOcean Eltako nicht angeboten und ihre eigene
Nachlieferung ruht. Sie bleibt verbunden und liest jede Minute ihre Base-ID; ihre Seite,
Live-Telegramme, Gateway-Test und Funkzeit bleiben. Wird wieder „Kein Ersatz“ gewählt, ist sie
ein normales Gateway mit eigenem Port.

**Umschalten**: das erste Gateway liest alle 10 s seine Base-ID. Ist seine Verbindung weg oder
bleiben drei Lesezugriffe in Folge unbeantwortet („weg oder stumm“; „nur weg“ wartet, bis die
Verbindung abbricht), laufen seine Programme über das Ersatz-Gateway weiter: sie bleiben mit
demselben Port verbunden, ihre Telegramme sendet das Ersatz-Gateway, dessen Antworten und Funktelegramme kommen
zu ihnen zurück. Befehle, die in diesem Moment unbeantwortet sind, werden nicht wiederholt (das
Ereignis sagt, wie viele); das entscheidet die Integration. Das Ersatz-Gateway wird nur genutzt,
wenn es verbunden ist, zuletzt geantwortet hat und dieselbe Base-ID meldet; die App merkt sich
die Base-ID des ersten Gateways, sodass das auch geprüft wird, während es weg ist. Zurück zum
ersten Gateway: automatisch, sobald es 60 s stabil gelaufen ist und beim Ersatz nichts wartet,
oder nur von Hand. Hast du selbst auf den Ersatz geschaltet, geht es nur von Hand zurück. Fällt der
Ersatz aus, geht es sofort zurück zum ersten Gateway, auch wenn es noch nicht läuft; kommt der
Ersatz wieder, springt er erneut ein. Die drei Zeiten (prüfen alle 10 s, 3 Fehlversuche, 60 s
stabil) stellst du je Gateway im Formular unter **Ersatz-Gateway → Ändern** ein. Die Karte
**Gateways** auf der Seite des ersten Gateways zeigt beide, welches
in Benutzung ist, und schaltet von Hand um.

**Beide Gateways hören** (optional): die Programme bekommen die Funktelegramme beider Gateways,
für mehr Reichweite. Ein Telegramm, das das andere Gateway innerhalb von 200 ms gebracht hat,
wird verworfen (verglichen ohne Signalstärke und Repeater-Zahl), ebenso, was das ruhende Gateway
von den eigenen Sender-IDs hört: das ist das eigene Senden des anderen Gateways. Die Karte zeigt,
was zuerst über welches Gateway kam.

**Ersatz wird Haupt-Gateway** (das erste Gateway ist kaputt): auf der Karte **Gateways**. Die
Verbindung des ersten Gateways bleibt mit Name, Port, erlaubten Clients, Nachlieferung, Erkennung
und Historie erhalten, sodass die Integration nichts merkt; nur die Hardware (Vorlage, Modell,
Art der Verbindung, Gerät oder Host und Port, Baudrate) wird zwischen den beiden Verbindungen
getauscht. Die alte Hardware wird danach ausgeschaltet (Standard), als Ersatz behalten oder ihre
Verbindung gelöscht. Beide Verbindungen starten neu, und die Nachlieferung überbrückt die kurze
Lücke. Die Konfig-Historie kann das rückgängig machen.

## Wartung: ein Rechner allein

Auf der Seite einer Verbindung lässt **Wartung** einen Rechner (seine IP-Adresse; die Hosts der
verbundenen Clients werden angeboten) die Verbindung 15 Minuten bis 4 Stunden allein nutzen,
z. B. für das Service-Programm des Herstellers, PCT14 oder ein Firmware-Update über RFC2217. Alle
anderen Clients, auch Home Assistant, werden währenddessen getrennt und abgewiesen; ein Balken
auf der Seite sagt, wie lange es noch dauert, und beendet es vorzeitig. Ist die Zeit um, und
spätestens bei einem Neustart der App, darf sich jeder erlaubte Client wieder verbinden. Bei den
Verbindungen von ser2net verbinden sich die Clients einmal am Anfang und einmal am Ende neu.

## Neu starten und USB-Reset

Hängt ein Gerät, startet **Neu starten** auf der Seite einer Verbindung sie neu: Das Gerät wird
geschlossen und wieder geöffnet (bei Modbus und EnOcean der Proxy), alle Clients werden getrennt
und verbinden sich wieder. Bei einem USB-Adapter dieses Rechners setzt **USB-Reset** den Adapter
zusätzlich zurück, als würde er ab- und wieder angesteckt, nur ohne den Strom zu unterbrechen.
Das hilft oft, wenn der Chip des Adapters hängt (FTDI, CP210x, CH340). Eine aufgehängte Firmware
im Gerät selbst braucht manchmal trotzdem einen Neustart ohne Strom, z. B. über eine schaltbare
Steckdose am USB-Hub. Nach dem Reset kann der Adapter eine andere tty-Nummer bekommen; mit dem
Pfad unter `/dev/serial/by-id` findet die Verbindung ihn wieder.

Automatisch: Im Formular einer seriellen Verbindung legt **Dann** fest, was nach den Minuten
ohne Daten („Warnen, wenn keine Daten seit“) geschieht: nur warnen, die Verbindung neu starten
oder USB-Reset und neu starten. Gezählt wird nur, solange das Gerät offen ist (ein Client
verbunden oder **Gerät offen halten**). Kommen auch nach drei Neustarts in Folge keine Daten,
bleibt es bei der Warnung, bis wieder Daten kommen. Jeder Neustart steht in der Historie.

**Stromzyklus**: Reichen Neustart und USB-Reset nicht, kann ein Schalter in Home Assistant den
Strom trennen, z. B. eine schaltbare Steckdose am USB-Hub. Er wird unter **Stromversorgung** im
Formular der Verbindung eingetragen (bei jeder Art von Verbindung). Neben **Neu starten**
erscheint dann der Knopf **Stromzyklus**: Das Gerät wird geschlossen, der Schalter geht für
5 Sekunden aus und wieder an, und das Gerät wird wieder geöffnet. Sind automatische Neustarts
eingestellt, folgt nach den drei erfolglosen Neustarts einmal der Stromzyklus. Wähle einen
Schalter, an dem nichts anderes hängt, und niemals den, der Home Assistant selbst versorgt.

Beides gibt es auch als Buttons in Home Assistant (siehe unten).

## Status, Mitschnitt und Leitungsfehler

- **Status**: Gerät vorhanden (und welcher Adapter es ist), Clients mit Adresse, Zeit und Bytes,
  Datenrate und die letzten Daten vom Gerät.
- **Live-Daten und Mitschnitt**: ser2net schneidet jede Verbindung im Speicher mit und die App
  liest mit. Die Live-Ansicht geht jederzeit und belegt keinen Client-Platz. Die **Aufzeichnung**
  in Dateien (vom Gerät, zum Gerät oder beides) wird je Verbindung auf der Seite **Mitschnitt**
  geschaltet, ohne ser2net anzufassen – kein Client wird getrennt. Dateien:
  `/addon_configs/<…>_device_proxy/trace/<name>-<Startdatum>.log`, je Einschalten und bei Erreichen
  der Größe eine neue Datei, die ältesten über dem Limit werden gelöscht (**Einstellungen →
  Protokolle und Aufbewahrung**).
- **Leitungsfehler** (Frame, Parität, Überlauf, Break) kommen vom Treiber des Adapters, solange
  das Gerät offen ist. Steigende Zahlen bedeuten meist eine falsche Baudrate oder ein falsches
  Format. Nicht jeder Treiber zählt sie.
- **FTDI-Latenz**: FTDI-Adapter warten 16 ms, bevor sie Daten weitergeben; „niedrige Latenz“
  setzt 1 ms (besser für Z-Wave). Lässt das System die App das nicht ändern, sagt die App das.

## Werkzeuge für Zähler

In den Details einer Verbindung:

- **Zählerdaten prüfen** liest die letzten 30 Sekunden als SML (binär, die CRC jedes Telegramms
  geprüft) oder D0 (Text) und zeigt die Werte, z. B. den Bezug gesamt.
- **Baudrate erkennen** hört nacheinander jede Geschwindigkeit und jedes Format ab und bietet die
  besten Treffer zum Übernehmen an. ser2net gibt das Gerät währenddessen frei (bis etwa eine
  Minute): die Clients der Verbindung werden getrennt und verbinden sich danach neu. Ans Gerät
  wird nichts gesendet, es geht also mit Zählern, die ihre Daten von selbst schicken.

**Zählerstände als Entitäten** (im Formular unter **Erweitert**, bei den eHZ-Vorlagen
standardmäßig an): mit MQTT bekommt das Gerät der Verbindung in Home Assistant „Zählerstand
Bezug“ und „Zählerstand Einspeisung“ in kWh und „Leistung“ in W, fertig für das
Energie-Dashboard. Die App liest sie aus den Daten, die der Zähler ohnehin sendet (SML nur aus
Telegrammen mit korrekter CRC), es braucht also keine zusätzliche Integration und keinen
Client-Platz; ser2net öffnet das Gerät aber nur, solange ein Client verbunden ist, also ohne
anderen Client **Gerät offen halten** einschalten.

## Ereignisse und Historie

**Ereignisse** zeigt das Live-Protokoll (Filter nach Verbindung, Stufe und Text) und die
Historie: Abbrüche und Verfügbarkeit je Verbindung über 30 Tage und eine Zeitleiste. Sich
wiederholende Ereignisse, etwa ein Stick, der immer wieder wegfällt, werden je Client zusammengefasst;
die Zeile nennt, wie oft und wann zuletzt. Bei
Modbus und EnOcean erscheinen auch abgewiesene Clients: Plätze belegt, Netz nicht erlaubt, Wartung
oder blockiert. Bei seriellen Verbindungen entscheidet ser2net selbst und meldet das der App nicht.
Auch der Start und das Ende der App, MQTT und Probleme mit Konfiguration, Historie oder Blockliste
stehen hier. Warnung heißt, dass etwas Aufmerksamkeit braucht; eigene Handlungen sind Info. Die
Historie wird standardmäßig 30 Tage aufbewahrt. **Einstellungen → Konfig-Historie** hält die
letzten 25 Konfigurationen mit ihren Unterschieden; jede lässt sich wiederherstellen. Namen von
Clients und die Benachrichtigung über neue Rechner legen keinen Stand an und bleiben beim
Wiederherstellen eines Stands, wie sie sind.

**Vor dem Speichern** nennt das Formular einer Verbindung die laufenden Verbindungen, die beim
Speichern neu aufgebaut oder beendet werden, und wie viele Clients sich neu verbinden müssen
(„nur diese Verbindung“ stimmt nicht immer: ein Ersatz-Gateway oder die Netzwerk-Einstellung
betreffen andere). Ebenso die Rückfragen vor einer Änderung der Netzwerk-Einstellung oder des
Heimnetzes, einem Import und dem Wiederherstellen einer Version oder Sicherung. **Nach dem
Speichern**: arbeitet eine Verbindung nicht mehr, die vorher lief (Gerät nicht erreichbar, Port
belegt), sagen das die Übersicht und die Seite der Verbindung, mit **Stand davor
wiederherstellen** – die Konfiguration von vor der Änderung, in einem Schritt.

## Clients

**Einstellungen → Clients** zeigt neue, bekannte und blockierte Rechner in einer Liste. Der Punkt
vorne sagt den Zustand: grün verbunden, grau nicht verbunden, gelb neu, rot blockiert. Ein Klick
auf einen bekannten Rechner öffnet das Feld für den Namen, das beim Verlassen speichert; in den
Details einer Verbindung geht das über den Stift beim Client. Der Name steht neben der Adresse in den
Client-Listen und in den Ereignissen. Dieser Host heißt von selbst Home Assistant, Adressen aus dem
Supervisor-Netz App; ein eigener Name geht vor.

Darunter steht der Verlauf des Rechners: eine Zeitleiste je Verbindung über 7 Tage oder 24 Stunden
und die letzten Verbindungen mit Dauer und Datenmenge. Kurze Besuche kurz hintereinander, etwa von
einem pollenden Client oder bei Abbrüchen, sind zu einer Zeile zusammengefasst und gelb markiert.
Abgewiesene Versuche (rot) gibt es bei Modbus und EnOcean; bei seriellen Verbindungen ist die
Datenmenge so genau wie der letzte Statusabruf. Der Verlauf bleibt so lange wie die Historie und
verschwindet, wenn der Rechner entfernt wird.

Die Ports haben keine Anmeldung, also wird ein Rechner gemeldet, der sich zum ersten Mal verbindet:
ein Ereignis und, sofern dort nicht ausgeschaltet, eine Benachrichtigung in Home Assistant. Er steht
als **Neu** oben in der Liste, bis du ihn als **Bekannt** markierst oder ihm einen Namen gibst. Als
neu stehen höchstens 50 Rechner in der Liste, ab sechs kommt eine gemeinsame Benachrichtigung. Home
Assistant, seine Apps und dieser Host gelten immer als bekannt und stehen nur in der Liste, solange
sie verbunden sind; nach dem ersten Start (oder dem Update, das diese Funktion brachte) übernimmt
die App die Clients der ersten zehn Minuten stillschweigend als bekannt.

**Blockieren** hält einen Rechner von allen Verbindungen fern, bis du ihn mit **Freigeben** wieder
zulässt; das geht aus der Liste oder mit **IP-Adresse blockieren**. Er wird sofort getrennt. ser2net
kann keinen einzelnen Client trennen, an seriellen Verbindungen, die ihn zulassen würden, verbinden
sich deshalb beim Blockieren und Freigeben alle Clients einmal neu. Die Sperre gilt für die
IP-Adresse: bekommt das Gerät eine neue, ist es nicht mehr gesperrt. Home Assistant, seine Apps und
dieser Host lassen sich nicht blockieren. Für Ports aus einer eigenen `ser2net.yaml` gilt die Sperre
nicht. Bei Modbus und EnOcean zeigt die Zeile, wie oft der Rechner seit dem Start abgewiesen wurde;
ser2net meldet das nicht.

**Entfernen** nimmt einen nicht verbundenen Rechner samt Namen aus der Liste; verbindet er sich
wieder, gilt er als neu. Die Diagnose lässt Namen und Adressen der Clients weg.

## Benachrichtigungen

Probleme erscheinen unter der Glocke von Home Assistant: eine Benachrichtigung je Verbindung und
Problem, aktualisiert statt wiederholt, und entfernt, wenn das Problem weg ist (abschaltbar).
Optional bekommt sie auch ein Notify-Dienst (z. B. die Companion-App auf einem Handy).

- Je Verbindung (im Formular der Verbindung): Gerät fehlt (bei Modbus auch: nicht erreichbar),
  kein Client verbunden (nach einigen Minuten), keine Daten vom Gerät für eine eingestellte Zeit
  (serielle Geräte, nur solange das Gerät offen ist). Ein Modbus-Port, der sich nicht öffnen
  lässt, wird immer gemeldet. Ein EnOcean-Gateway: nicht erreichbar, und Funkzeit bei 80 % des
  Limits; mit Ersatz-Gateway: läuft über den Ersatz (statt „nicht erreichbar“, mit Grund), und
  der Ersatz ist nicht bereit (ausgeschaltet, nicht verbunden, andere Base-ID, antwortet nicht).
- Für alle (**Einstellungen → Benachrichtigungen**): ein Client hört auf zu lesen, Leitungsfehler
  steigen, ser2net startet immer wieder neu, die eigene `ser2net.yaml` ist nicht verwendbar.

Ein Problem wird erst gemeldet, wenn es die Schonfrist (Standard 30 s) angedauert hat, und nicht
in der ersten Minute nach dem Start der App.

## Entitäten in Home Assistant (MQTT)

Mit einem MQTT-Broker in Home Assistant (z. B. der App Mosquitto) legt die App über
MQTT-Discovery je Verbindung ein Gerät an. Meist ist nichts einzurichten: der Broker kommt vom
Supervisor. Ein anderer Broker (Host, Port, Benutzer, Passwort, TLS) lässt sich unter
**Einstellungen → MQTT-Entitäten** einstellen, wo sich die Entitäten auch abschalten lassen.

| Entität | Inhalt |
|---|---|
| Gerät verbunden | das Gerät ist angeschlossen |
| Clients | verbundene Clients |
| Datenrate | Bytes pro Sekunde vom Gerät |
| Daten vom Gerät | Bytes seit dem Start von ser2net |
| Letzte Daten | wann das Gerät zuletzt etwas gesendet hat |
| Leitungsfehler | seit dem Start vom Treiber gezählte Fehler |
| Aktiv (Schalter) | schaltet die Verbindung ein und aus |
| Clients trennen (Button) | schließt die Verbindungen aller Clients; sie dürfen sich neu verbinden |
| Verbindung neu starten (Button) | schließt das Gerät und öffnet es neu, die Clients verbinden sich wieder |
| USB-Reset (Button) | nur mit einem Gerät dieses Rechners: setzt den USB-Adapter zurück und startet neu |
| Stromzyklus (Button) | nur mit eingetragenem Schalter: trennt 5 Sekunden den Strom und startet neu |

Eine Modbus-Verbindung hat: ihre Register als Entitäten (siehe oben), Gerät erreichbar, Clients, Anfragen, unbeantwortete Anfragen,
Antwortzeit, den Schalter und die Buttons. Ein EnOcean-Gateway hat: Gateway erreichbar, Clients,
Telegramme vom Gateway, Funkzeit (Anteil am 1-%-Limit), den Schalter und die Buttons; mit
Ersatz-Gateway außerdem „Ersatz-Gateway aktiv“ (ein Problem, solange es einspringt), „Aktives
Gateway“ (der Name des genutzten), „Ersatz-Gateway bereit“ und die Buttons „Auf Ersatz-Gateway
umschalten“ und „Zurück zum eigenen Gateway“ (wie auf der Karte **Gateways**). „Gateway
erreichbar“ bleibt die eigene Hardware des Gateways.

Die Buttons sind für Automationen gedacht, z. B. um einen hängenden Stick neu zu starten. **Clients trennen** gibt es auch auf der Seite einer Verbindung, neben ihren Clients.

Dazu ein Gerät **Device Proxy** mit „ser2net läuft“. Ohne Broker ändert sich nichts. Präfix
(`homeassistant`), Basis-Topic (`device_proxy`) und das Aktualisierungsintervall stehen unter
**Einstellungen → MQTT-Entitäten**; die Namen der Entitäten folgen der Sprache der
Benachrichtigungen.

## Umstieg von ha-modbusproxy

Die Optionen von ha-modbusproxy kopieren (dessen Reiter **Konfiguration** → ⋮ → **Als YAML
bearbeiten**) und unter **Einstellungen → Sichern und Übertragen → Importieren** einfügen; jedes
Gerät wird eine Modbus-Verbindung mit denselben Ports, Timeout und `connection_time`. Eine
Konfigurationsdatei von modbus-proxy (YAML oder TOML, `devices` mit `modbus: url`,
`listen: bind` und `unit_id_remapping`) geht auch. Beim Start wird eine Datei
`import/modbus-proxy.yaml` im Konfigurationsordner der App wie eine ser2net-Datei übernommen.

**Zuerst ha-modbusproxy stoppen**: beide Apps lauschen im Netz des Hosts, also kann nur eine den
Port 502 haben. Die Clients (z. B. die Modbus-Integration) brauchen keine Änderung, wenn die Ports
bleiben.

## Eine vorhandene Konfiguration übernehmen

Eine ser2net-4-`ser2net.yaml` (Version 1 oder 2, mit Defines und Defaults) oder eine
ser2net-3-`ser2net.conf` lässt sich importieren:

- in der Weboberfläche: die Datei wählen oder einfügen, die Vorschau prüfen (was übernommen wird,
  was mit einer vorhandenen Verbindung kollidiert, was sich nicht übernehmen lässt) und je
  Kollision wählen: ersetzen, neuer Port oder überspringen;
- oder beim Start: die Datei als `import/ser2net.yaml` oder `import/ser2net.conf` in den
  Konfigurationsordner der App legen (`/addon_configs/<…>_device_proxy/import/`). Kollisionen
  werden übersprungen, das Protokoll der App listet alle Hinweise und die Datei wird in
  `….imported-<zeit>` umbenannt.

`/dev/ttyUSB3` und Ähnliches werden durch ihren stabilen by-id-Namen ersetzt (sonst by-path).
Nicht übernommen werden: andere Accepter als TCP (SSL, SCTP, UDP, mux, certauth), andere Geräte
als serielle Ports, unbekannte serielle Optionen, Rotatoren, LEDs und Admin-Abschnitte.
Unbekannte ser2net-Optionen werden zu weiteren Optionen.

Mit den alten Ports brauchen die Clients keine Änderung. Den alten ser2net zuerst stoppen – beide
können nicht auf demselben Port lauschen.

ser2net ignoriert die Modemleitungen nur mit `local`; die Formulare setzen es für neue
Verbindungen, ein Import übernimmt, was in der Datei steht.

**Als ser2net-YAML exportieren** schreibt die seriellen Verbindungen als ser2net-4-`ser2net.yaml`
für jeden ser2net; Modbus- und EnOcean-Verbindungen gehören nicht dazu, weil die App sie selbst
bedient.

## Sichern und Wiederherstellen

**Einstellungen → Sichern und Übertragen** speichert alles, womit die App eingerichtet wurde –
alle Verbindungen (seriell, Modbus, EnOcean) und die Einstellungen – als eine JSON-Datei. **Aus
Sicherung wiederherstellen** zeigt, was die Datei enthält, und ersetzt nach einer Bestätigung die
aktuelle Konfiguration; der alte Stand bleibt in der Konfig-Historie. Die Datei enthält die
MQTT-Anmeldung, also nicht weitergeben. Die Namen der Clients sind dabei, die Liste der bekannten
und blockierten Rechner nicht. Die Daten der App sind auch Teil der eigenen Sicherungen
von Home Assistant, außer den aufgezeichneten Mitschnitten und EnOcean-Aufzeichnungen (der Ordner
`trace/`), die groß werden können.

## Eigene ser2net.yaml verwenden

Für Aufbauten, die die Formulare nicht abbilden, verwendet **Einstellungen → ser2net.yaml →
Eigene Datei** deine Datei so, wie sie ist (`/addon_configs/<…>_device_proxy/ser2net.yaml`, in
der App mit Prüfung bearbeitbar). Sie darf keinen Admin-Abschnitt enthalten: die App fügt ihren
eigenen hinzu. Status, Ereignisse, Historie, Benachrichtigungen und MQTT funktionieren weiter,
mit den Verbindungsnamen von ser2net; die Formulare, „Gerät offen halten“ und die Zählerwerkzeuge
werden währenddessen nicht genutzt. Modbus- und EnOcean-Verbindungen gehören nicht zu ser2net und
laufen weiter; ihre Ports dürfen nicht in deiner Datei vorkommen.

Deine Datei wird ohne Einschränkung verwendet, sie kann also alles, was ser2net kann – auch
Optionen wie `connback`, die Programme starten können. Wer den Konfigurationsordner der App
beschreiben kann (z. B. über Samba), kann das ebenso; die Formulare und der Import übernehmen nur
harmlose weitere Optionen.

## Proxmox

Läuft Home Assistant als VM, die USB-Adapter an die VM durchreichen. Gleiche Adapter ohne
Seriennummer lassen sich nur unterscheiden, wenn sie nach USB-Port durchgereicht werden, nicht
nach Hersteller- und Produkt-ID. Trennt sich ein Stick immer wieder, die USB3-Option des
durchgereichten Geräts umschalten.

## Testfälle für Fehlermeldungen

**Als Testfall** in den Live-Daten einer Verbindung lädt ihre letzten paar hundert Frames als
Datei herunter, die sich an ein Issue hängen lässt; so lässt sich ein eigenwilliger
Wechselrichter oder ein Gateway ohne die Hardware ansehen. Client-Adressen werden weggelassen;
EnOcean-Sender-IDs und die Base-ID werden durch erfundene ersetzt (die Prüfsummen neu berechnet).
Modbus-Register bleiben, wie sie sind, und die Telegramme eines Zählers enthalten die
Zählernummer: vor dem Teilen hineinschauen. Der Entwicklungsserver spielt einen Testfall als
Gerät ab: `python tools/dev_server.py 8399 --replay datei.json`.

## Diagnose

**Einstellungen → Hilfe und Info → Diagnose-Paket herunterladen** liefert ein ZIP mit Versionen,
Konfiguration, Status, Geräten und den letzten Ereignissen. IP-Adressen, Hostnamen und die
MQTT-Anmeldung werden ersetzt und Clients nur gezählt. Verbindungsnamen und Gerätepfade bleiben
drin (ein Pfad `/dev/serial/by-id/…` enthält die Seriennummer des Adapters): kurz hineinschauen,
bevor du es an ein öffentliches Issue hängst.

## Wenn etwas nicht geht

| Was du siehst | Was zu prüfen ist |
|---|---|
| Gerät fehlt | Ist der Adapter an die VM durchgereicht? Erscheint er in der Geräteliste? An einem anderen Port eingesteckt: die Seite bietet an, ihn zu übernehmen. |
| Wartet auf ser2net | Das Protokoll der App: ser2net meldet, warum es nicht startet (z. B. ein belegter Port). |
| Ein Client wird abgewiesen | Netzwerk-Einstellung oder `remaddr`: ist die Adresse des Clients erlaubt? |
| Daten sehen nach Rauschen aus | Baudrate oder Format: **Baudrate erkennen** oder die Vorlage nutzen. |
| Leitungsfehler steigen | Wie bei Rauschen; außerdem das Kabel oder die USB3-Option in Proxmox. |
| Alle Clients langsam | Ein Client hat aufgehört zu lesen (an der Verbindung markiert). |
| „Änderung wartet“ | ser2net übernimmt eine Änderung, wenn sich die Clients neu verbinden; die App trennt sie. |
| Modbus „Port belegt“ | Eine andere App (z. B. ha-modbusproxy) lauscht noch auf dem Port: stoppen. |
| Modbus „nicht erreichbar“ | Adresse und Port des Geräts; lässt das Gerät nur eine Verbindung zu, die ein anderes Programm noch hält? |
| Modbus antwortet 0x0B | Das Gerät antwortet nicht rechtzeitig: Timeout erhöhen, Unit-ID prüfen; bei RTU Baudrate, Format und Verdrahtung (A/B). |

## Dateien

| Pfad | Inhalt |
|---|---|
| `/addon_configs/<…>_device_proxy/ser2net.yaml` | deine eigene Konfiguration (optional) |
| `/addon_configs/<…>_device_proxy/import/` | eine Datei zum Übernehmen beim Start (`ser2net.yaml`, `ser2net.conf`, `modbus-proxy.yaml`) |
| `/addon_configs/<…>_device_proxy/trace/` | aufgezeichnete Mitschnitte und EnOcean-Aufzeichnungen (`.jsonl`), nicht in den Sicherungen von Home Assistant |
| App-Daten (in der Sicherung) | Verbindungen, Einstellungen, Historie, Konfigurationsstände, bekannte und blockierte Clients |
