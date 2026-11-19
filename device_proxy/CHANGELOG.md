# Changelog

> ### 🔌 One device, many clients – and one person behind it
>
> Device Proxy is a hobby project and stays free. This is how you can help:
>
> - ⭐ **Star it on GitHub**: it makes the project easier to find.
> - 🐞 **Report a bug or an idea**: as an [issue](https://github.com/bertel2020/HA-Device-Proxy/issues/new/choose), ideally with the diagnostics (Settings → Help and info).
> - ☕ **Keep the proxy running**: [Buy Me a Coffee](https://buymeacoffee.com/bertel2020) · [Ko-fi](https://ko-fi.com/bertel2020) · [PayPal](https://paypal.me/RobertoMartins)
>
> 🇩🇪 [Änderungen auf Deutsch](https://github.com/bertel2020/HA-Device-Proxy/blob/main/device_proxy/CHANGELOG.de.md)

## Unreleased

## 1.9.2 - 2026-11-19

### Changed

- **Interface on a phone:** more room for the content, nothing scrolls sideways any more.
  - Home Assistant's bar with the menu and the app's name is left out; the menu icon sits at the left of the app's own header instead, as in EnOcean Eltako. On a desktop nothing changes.
  - Tables (clients, unit IDs, 1-Wire devices and writes, heard EnOcean senders, recording files) are small cards one below the other: the client, device or file on top, below it each value with its label. On a desktop they stay tables.
  - The settings show their sections as one row of chips above the content instead of a long list (on a tablet too). The row stays under the header while scrolling, marks the current section and jumps there when tapped.
  - The short text under the page titles (Connections, Events, Recording) is left out.
  - Large figures are a little smaller.
- **Interface:**
  - Wide screens: the pages use up to 1600 px instead of 1200 px. The connection list shows three columns there; on a connection's page the three top cards stand side by side from 1600 px (such as Gateways, Gateway and Clients). The form and the settings stay narrower so they stay readable.
  - Large figures have the same three sizes everywhere (meter values, tiles and counters, small tiles). The tiles above the connection list are now as large as the counters on the other pages.
  - Page titles are a little smaller (24 instead of 28 px); in the settings the title stands above both columns.
  - Header: the line under the name now says "Running · App …" instead of "ser2net running". It is red with the reason only when ser2net is stopped and serial connections need it; problems of single connections are still counted at the "Connections" tab. The versions are in the tooltip.
- **Connections, order:** the list is sorted by kind (serial, Modbus, EnOcean, 1-Wire), with a heading per kind, and by name within; switched-off connections are at the end of their group, a fallback gateway stays right after its gateway. Connections with a problem no longer jump to the top; the filter "Problems" is there for that.
- **1-Wire:** is no longer beta. The "Beta" notes and labels in the interface and the docs are gone.
- **EnOcean, Swap the gateway** (formerly "Fallback becomes the main gateway")**:** the programs now stay connected during the swap. Before, the connection restarted and dropped all clients; programs in the network such as Symcon only came back after minutes.
  - If the fallback was active at the time, it goes on through the swapped gateway right away.
  - New: **Swap the names too**, when the names of the connections describe the gateway (off by default). Its hint says that the entity IDs in Home Assistant keep the old names.
  - When the two gateways have different base IDs, the section and the confirmation warn about it: commands from Home Assistant no longer reach the actuators afterwards until the base ID is matched or the actuators are taught again.
  - The event says in words what was swapped and what happened to the old gateway, also whether the names were swapped.
  - Clearer texts: which gateway (address) goes where and what happens to the old one.
  - Also when you change the host, port or device of an EnOcean gateway, the programs now stay connected.

### Fixed

- **EnOcean, events:** when switching to the fallback and back, the reason is given in words again instead of as an identifier (such as "by hand" instead of "by_hand").

## 1.9.1 - 2026-11-18

### New

- **1-Wire, HTTP port (beta):** Programs that read the bus over HTTP from owhttpd (port 2121, such as 1-Wire modules for IP-Symcon) can now use the app directly. Set the **HTTP port (owhttpd)** in the connection; the app starts owhttpd itself.
  - The HTTP port has the same allowed clients, maximum number and blocks as the owserver port; the program appears with its address among the clients, its values under "Devices on the bus".
  - Writing over HTTP only with "Write access: All clients", otherwise owhttpd runs read-only.

### Changed

- **1-Wire, programs that do not get through:** If a program sends something to the port of a 1-Wire connection that is not a complete owserver request (another protocol, or it closes in the middle of the request), this now shows in the events, with host, reason and the first bytes. Before, the app closed such connections without a word, and the program showed up nowhere. A plain port check stays silent.

## 1.9.0 - 2026-11-18

### New

- **1-Wire, USB adapter on Home Assistant (beta):** A 1-Wire connection can now also use the USB adapter (DS9490R, DS1490F) plugged into Home Assistant or passed through to its VM: source **USB adapter of this host**.
  - The app runs its own owserver for it. The programs keep connecting to the connection's port, so moving from an owserver in the network changes nothing for them.
  - The form says whether it finds the adapter.
  - When the bus stops answering, the app starts owserver again and then gives the adapter a USB reset. "USB reset" works by hand too, on the connection's page and as a button in Home Assistant; clients and diagnostics stay.
  - The page shows whether owserver runs, its restarts and its last messages.
  - Under "Advanced" you set how long the own owserver keeps read values in its cache (15 s by default); that saves bus time when several programs read the same sensors.
- **1-Wire, devices on the bus:**
  - Names of your own for the devices; events and notifications use them.
  - The exact chip as the owserver names it.
  - The last value your programs read; for devices with several values (such as DS2408, DS2438) all of them can be shown.
  - The app remembers the devices, also over restarts: one missing from the device list twice in a row shows as "missing since", and a notification with its name comes. One taken off on purpose can be forgotten, a new one is marked for a day.
  - "Search the bus now" searches the bus at once instead of the cached list, handy while wiring.
  - iButtons on the reader of a DS1490F come and go without counting as missing; the list says when one was on the reader last.
  - Over MQTT there is the number of missing devices.
- **1-Wire, faults on the bus:**
  - 85 °C: a conversion that did not finish.
  - Sensors on parasite power, the usual cause of the 85 °C.
  - A temperature that does not move for a long time, also on a DS2438.
  - Outliers: a single value far off that is back at the next read.
  - The owserver card shows the adapter's name and version, the owserver's version and its CRC and bus errors.
- **1-Wire, writes:** The page of a 1-Wire connection lists the last 100 writes (switching an output of a DS2408, say) with time, client, device, value and result, also the refused ones. So you find who switched a relay.

### Changed

- **1-Wire, more:**
  - A connection that sends no request within 30 seconds (a program that hangs, a port scan) is closed. Before, it stayed open for good.
  - The names you give the 1-Wire devices are not in the diagnostics, also not in the events; the IDs stay, so the fault can be followed.

## 1.8.0 - 2026-11-18

### New

- **1-Wire buses (new, beta):** A new kind of connection shares an owserver (OWFS), for example the one on another computer that has the USB adapter. Home Assistant's 1-Wire integration, owhttpd and other systems connect to the app's port (4304 by default) instead of the owserver; every request passes unchanged. The connection's page shows whether the owserver answers, the devices on the bus with their family and usual chip, requests, errors and answer time, the clients per computer with their last request, and in the live data every read with its value. When the owserver stops answering, a notification comes. Writes (switching outputs) can be limited to some computers or locked. Over MQTT there are "Device reachable", the number of 1-Wire devices and the requests as entities. The USB adapter directly on Home Assistant comes in a later version.

## 1.7.0 - 2026-11-15

### Changed

- **Interface, new look:** The sections are tabs with an icon, and the number of problems shows as a counter on the "Connections" tab. At the top next to the name there is now just one line with the state and the app version; the version of ser2net is in the tooltip. Colour scheme, light or dark, and font size are changed with the palette icon at the top right of every page; the settings page now only shows the current choice with a button leading there. Buttons and fields share corners that are less round, numbers are shown as tiles with a small label above. With font size "Small", text is not smaller than 10.5 px. On the phone the bottom bar highlights the chosen section. On opening, the header and tabs are there at once, and while the data loads, grey placeholders show the shape of the page instead of "Loading …"; this also holds for the edit form.
- **Interface, connections:** The overview shows its numbers as tiles. Each connection card shows clients, data rate with a curve and last data as tiles, below them at most three clients; you find the rest via "+N more" on the detail page. On the phone the note about the missing MQTT broker is folded into one line with "More".
- **Interface, detail page and events:** Data rate, Modbus requests, line errors, gateway counters, radio load and replay buffer are shown as tiles, as are drop-outs and availability under "History and stability". If a serial device has no data flowing yet, the detail page shows one slim card instead of two half-empty ones. If a label wraps onto two lines, the numbers of a row still stand at the same height.
- **Interface, form and dialogs:** Fields side by side stand at the same height, even if a label wraps onto two lines. The note "IP address or hostname" is under the address instead of under the port. The list of errors under the form names the fields by their name instead of the internal key, and a click on one jumps to the field. When saving with errors, the form jumps to the first faulty field; if it is under "Advanced", the section opens. The import dialog no longer has a coloured frame on opening. A note in the import and the buttons under "Back up and transfer" have the right colours in dark mode.

## 1.6.2 - 2026-11-14

### Changed

- **Texts:** More error messages are in German, and invalid input gives a message instead of "internal error".

### Fixed

- **Modbus TCP, reachable:** A device that takes connections but does not answer (e.g. the dongle awake, the inverter asleep) counts as not reachable after three requests without an answer. Before, it stayed "reachable" once the app had started before the device, and no notification came.
- **Modbus, restarting a connection:** Waiting requests get an answer at once. Before, a client of another connection (through `unit_routes`) and a running bus scan could hang for good; the scan could not be started again.
- **Import and own ser2net.yaml:** A file not saved as UTF-8 (such as an old `ser2net.conf` with an umlaut) no longer makes the app crash at every start. The own `ser2net.yaml` can be opened in the interface again, too.
- **Import, access:** `remaddr` such as `ipv4,192.168.1.10,0` is taken over. Before, the entry was dropped and the connection was open to the whole home network instead of the one host.
- **History:** A locked database or a full disk no longer counts as damaged. The file stays as it is, the app keeps running and keeps the history in memory until the next start. Before, events, client history and all versions for "Undo" were moved aside, and with a full disk the app did not start at all.
- **Stop and update:** An open panel no longer holds up the stop of the app.
- **Backup:** A backup without a configuration is refused instead of deleting all connections. A backup or version made with an own `ser2net.yaml` uses the forms when the file is missing (e.g. after a new install).
- **EnOcean:** A telegram just before the replay request arrives only once. As in ser2net, the timeout also counts telegrams to the client, so an integration that only listens is no longer disconnected. After a restart no old client handler keeps running in the background.
- **Modbus RTU, listen only:** An adapter that hangs up at once is opened again once a second instead of thousands of times.
- **MQTT:** Two installations on the same broker with their own base topics no longer throw each other out or delete each other's entities.
- **Interface:** A tool run (baud rate, scan) no longer stays on "running" after a short connection error. The read tool no longer hangs with type "string" and an empty answer. A cut address no longer leaves the page empty. `unit_routes` with commas is shown right on the detail page. Exception 07 and unknown codes have a text, no "fbReason_none" right after the start.
- **Home Assistant, buttons:** When a button does nothing, such as "Back to its own gateway" while the gateway is not connected yet, the reason now shows in the events. Before, it was only in the app's log.
- **Tools:** A running baud rate detection or bus scan shows again when you leave the page and come back, or open it in another browser. Before, starting it again only said "already running".

## 1.6.1 - 2026-11-13

### Changed

- **Blocking clients:** With an own `ser2net.yaml`, a block only applies to Modbus and EnOcean. The interface and the event now say so.
- **Network:** Anyone coming from a version before 0.3 now also has the private IPv6 networks in the home network. Anyone who has already updated adds `fc00::/7` and `fe80::/10` themselves if needed.
- **Interface, texts:** Numbers and times follow the app's language. "1 day ago" and "1 entry" instead of "1 days ago" and "1 entrys", "1 hour ago" instead of "60 minutes ago".
- **Interface, time details:** Instead of "since 30 minutes ago" it now says "since 30 min", for clients, for the replacement gateway and for running EnOcean recordings.

### Fixed

- **Modbus, write protection:** A write command must now be exactly as long as its count says. Before, a client that may only write certain registers could append a second command or send more data than allowed.
- **Modbus RTU:** When the USB adapter is back, the app finds the device without a restart. Before, "reachable" and the register entities stayed away until a client asked for something.
- **Diagnostics:** The diagnostics ZIP no longer contains client and sender names, not even through earlier settings changes in the history.
- **EnOcean, recording:** If a recording can no longer write (for example with a full disk), it ends and frees the gateway again. An event says why.
- **EnOcean, clients:** A client that disappears without logging off is now detected and no longer blocks a slot.
- **Events:** Changed values for summing up equal events take effect at once, not only after a restart.
- **Recordings:** If two connections have almost the same name, their files keep their names, even when one is switched off.
- **Interface:** After saving an MQTT password it no longer says "Not saved". Selection fields always show the value that applies. After deleting a connection there is no confirmation prompt any more. In the import, a deselected row is no longer taken over. The events history shows the right state when the filter is changed quickly.
- **Interface, texts:** Number fields accept only digits instead of showing "NaN". The path of the recordings is shown as text; the copy button only copied a placeholder.

## 1.6.0 - 2026-11-09

### New

- **Home Assistant, events:** Every connection now has an entity "Events". Device gone, new client, write refused and more can start automations with it.
- **Home Assistant, device page:** Every device of the app now has a link straight into the Device Proxy interface.
- **MQTT, note:** If the app finds no broker, as with EMQX, or loses it, the Connections page now says so and leads straight to the setting. Without a broker the note can be hidden.
- **Modbus, clients side by side:** The table of clients now shows each client's share of the device's time, answer time and waiting time. A sentence below says whether they slow each other down.
- **Clients, history:** Tap a computer to see when it was connected to which connection: a timeline over 7 days or 24 hours, the recent connections with duration and data, plus reconnect bursts and refused attempts. The history starts with this update. On serial connections the amount of data is as exact as the last status read; refused attempts exist for Modbus and EnOcean. Removing a computer removes its history too.
- **Events, new:** MQTT connected or lost, no broker found, ser2net does not start, an internal error of a connection, a failed automatic restart, a full recording, the app stopping, and an unusable configuration, history or list of blocked clients. The start names the version, a restart the USB reset.

### Changed

- **Home Assistant, entity IDs:** New entities begin with `device_proxy_`. Existing ones are changed under Settings → MQTT, the preview shows where they are used. Home Assistant does not adapt references to the old IDs.
- **Home Assistant, version:** All devices of the app now name the app's version. The device Device Proxy used to show the version of ser2net there.
- **Home Assistant, devices:** The list of devices now shows "Device Proxy · Serial", "· Modbus" or "· EnOcean", so the devices can be placed at a glance. Devices and entities stay the same.
- **Events, summed rows:** Repeats are now summed up per client, so no computer disappears behind another. The row says how often and when last.
- **Events, levels:** A warning now means something needs attention. Blocking and maintenance are info, an automatic restart is a warning. The empty Debug filter is gone.
- **Languages:** Each language is now a file of its own, with the web interface, notifications and entity names. A new language needs just one file; whatever it leaves out appears in English. The texts themselves have not changed.
- **Events:** With Modbus and EnOcean, refused clients now also appear when their network is not allowed, maintenance is on or they are blocked. Repeats are summed up.
- **Trace:** The connection is now chosen from a list as under Events, so every connection stays within reach however many there are. Running recordings are marked in it.
- **Trace, files:** Every file carries the start date of its recording in its name and keeps it, for example `ehz_sml-20261109-104012.log`. Switching recording on begins a new file. Lowering the number of files kept now also removes the surplus ones. Existing files keep their names until they rotate out.
- **Trace, table:** Compact rows, newest first, download and delete as icons of the same size, and the running file is marked.

### Fixed

- **Availability:** If a Modbus or EnOcean device was away and the app restarted meanwhile, the time after that kept counting as an outage. Fixed, for what is shown of the past too.

## 1.5.1 - 2026-11-08

### Changed

- **Overview:** The clients on a connection's card no longer have a pencil, so the line stays in one piece. Renaming is still available in the connection's details and under Clients.
- **README:** The quick start names the requirement again: Home Assistant OS.

## 1.5.0 - 2026-11-08

Modbus registers directly as entities in Home Assistant, write rights per client, device profiles, a power cycle for devices that hang, blocking and naming clients, EnOcean senders with names.

### New

- **Modbus, registers as entities:** The app reads registers itself and offers them as sensors over MQTT, without YAML. Added under Read registers → Decode values or as lines in the form, at most 50, every 30 seconds by default. When listening on an RS485 bus, the values come from what was heard and nothing is sent.
- **Modbus, registers per client:** One line per client sets which registers it may write, instead of the general registers. "Check access" names the line that applies.
- **Modbus, device profiles:** Starting values for SolarEdge, Huawei SUN2000, Fronius, SMA, Kostal Plenticore, Sungrow and Victron GX; when the bus scan recognizes the vendor, it offers its timing.
- **Power cycle:** A switch in Home Assistant can cut the power of a hanging device for 5 seconds: by hand, as a button in Home Assistant and once when three automatic restarts did not help.
- **Blocking clients:** A computer can be kept out of every connection and released again. With Modbus and EnOcean its line shows how often it was refused.
- **Naming clients:** New, known and blocked computers are in one list with their state and "last seen"; a click opens the name. In the lists of clients of a connection the pencil does the same. This host is called Home Assistant by itself, addresses in the Supervisor network App. Computers that are not connected can be removed from the list. Many new computers at once get one notification together.
- **EnOcean senders:** names of your own for all gateways, saved together and left out of the diagnostics, and the list as a CSV file.
- **EnOcean fallback gateway:** the check interval, the failed reads before switching and the steady time before going back can be set per gateway.
- **Zigbee stick:** a template of its own (115200 baud, one client, Home Assistant and apps only).

## 1.4.1 - 2026-11-08

The panel works well on phones, plus many fixes for EnOcean, Modbus and MQTT.

### Changed

- **Phones:** the sections as a bar at the bottom, no page is wider than the screen, the save bar of the form is one row, links and small buttons are easier to hit.

### Fixed

- **Trace:** the bytes of decoded frames no longer collapse to one character per line; the file of a running capture can no longer be deleted.
- **EnOcean:** one command expecting an answer at a time, a late answer goes to nobody; ESP2 checks the checksum of every frame; a capture with a lock no longer switches to the fallback gateway by mistake.
- **Modbus:** a device that cannot be reached turns clients away at once, clients that vanished free their place, every write empties the cache, invalid reads when listening on a bus get an error answer.
- **MQTT and notifications:** an error from a button no longer ends MQTT, old entities go away reliably, notifications that are resolved are dismissed after a restart too.
- **App:** an invalid configuration no longer starts empty, what is valid is kept; when a background part fails, the app starts again; the import shows conflicts within a file in the preview.

## 1.4.0 - 2026-11-05

A hanging connection can be restarted, also with a USB reset of its adapter: by hand, from Home Assistant or automatically.

### New

- **Restart:** a new card on a connection's page. The device (for Modbus and EnOcean the proxy) is closed and opened again, the clients connect again, also with "Keep the device open".
- **USB reset:** for USB adapters of this host; resets the adapter like unplugging and plugging it in again, without cutting the power, and waits until it is back.
- **Automatically:** after the minutes without data, restart or USB reset and restart (serial connections), at most three times in a row until data comes again.
- **Home Assistant:** buttons "Restart connection" and "USB reset" per connection.
- **History:** Every restart is in the history, a failed USB reset as a warning.

## 1.3.0 - 2026-11-02

The panel can be adjusted: three colour schemes, light or dark, and three text sizes.

### New

- **Colour scheme:** Ocean (as before), Forest or Graphite, each light and dark.
- **Light or dark:** as Home Assistant (as before), always light or always dark.
- **Text size:** Small (12 px), Normal (14 px) or Large (16 px); all texts scale with it, spacing stays the same.
- **Setting:** Set under Settings → Help and info; applies to this browser only, and at once.

### Changed

- **Ocean colour scheme:** The muted text is a little lighter.

## 1.2.2 - 2026-11-02

The EnOcean Eltako integration reaches the status port again, over IPv6 too.

### Changed

- **Refusal at the status port:** The 403 answer gives the reason; the log adds the Host header.

### Fixed

- **EnOcean, status port:** Home Assistant was refused with 403. It runs in the host network and may come from another address of the host than the one it connects to. Every address of the host now counts as this host (status port, EnOcean and Modbus proxy, Modbus write lock).
- **Apps over IPv6:** The Supervisor's IPv6 network (fd0c:ac1e:2100::/48) counts as the apps, like 172.30.32.0/23 (status port, "Home Assistant and apps", ser2net).

## 1.2.1 - 2026-11-02

The status port for the EnOcean Eltako integration says why it does not answer a request instead of resetting the connection.

### Changed

- **Log:** Every refusal and failure at the status port is in the app's log, with the client's address and port, the address it arrived at, and the reason (not allowed, timeout, request cut off or too long, status failure with traceback).

### Fixed

- **EnOcean, status port:** A refused request got "Connection reset by peer", because the app closed the connection before reading the request. It now reads the request and answers 403; if the status itself fails, 500.

## 1.2.0 - 2026-11-02

See before saving what a change does, and get back in one step when it broke something; check who may write to a Modbus device; safer defaults where a connection is made without the form; a more robust web interface.

### New

- **What saving does:** the connection form, and the questions before a change of the network setting or the home networks, an import or restoring a version or backup, name the running connections that are set up again or stop and how many clients have to connect again.
- **Restore the version before:** when a connection that worked stops working after a change, the connections page and its own page say so and offer the configuration before the change.
- **Modbus, check access (Tools):** whether a client at an address may connect, read and write a register, and which rule decides – by the same checks the proxy makes, without sending.
- **Modbus, who may really write:** on the connection's page: every client that may connect, the listed ones, nobody when none is listed, the allowed registers, and the rule of a connection that units are sent on to.

### Changed

- **Modbus:** New Modbus connections made without the form (API, scripts) let only Home Assistant and the apps write, as the form always did. Connections saved before write access existed keep "all".
- **Z-Wave:** A Z-Wave stick made without the form also lets only Home Assistant and the apps connect.
- **Host names:** a name that cannot be looked up, or a device not reached in time, is said in words ("host name … not found (DNS)", "… not reached within … s") instead of the system's text or "no answer".
- **EnOcean:** the settings say when the status port for the EnOcean Eltako integration could not be opened, why, and that the app tries again.
- **Trace files:** Trace files are downloaded in blocks instead of read whole into memory; the interface stays usable during a large download.
- **Status requests:** one at a time with a time limit; requests no longer pile up while the app is busy, and an older answer never overwrites a newer one.
- **Operation:** Choice groups (network, MQTT broker, ser2net source, import mode) work with arrow keys.
- **Screenshots:** New screenshots in the READMEs.

### Fixed

- **Settings:** leaving the page with changes not saved yet asks first, as the connection form does (before, they were gone).
- **Full disk:** a configuration that cannot be saved changes nothing and the page says why (before, "internal error"). When only the configuration history cannot keep it, the saved change counts all the same.
- **Import:** a ser2net.yaml with a control character is refused with a message instead of an error.
- **Web interface:** a connection that does not send its request or body in time is closed.

### Tests and tools

- **Tests:** Random and broken input for all parsers and the running proxies, broken uploads and backups.
- **Soak tests:** `tools/soak_test.py` with limits for answer times, memory and recovery, device outages and slow readers; `tools/soak_enocean.py` for a gateway and its fallback.
- **Hardware tests:** `tests/HARDWARE.md`: the checks that need real devices on Home Assistant OS.

## 1.1.0 - 2026-11-01

Many new tools: Modbus values decoded and devices identified, names for clients and a word on new ones, maintenance with one computer alone, meter readings for the Energy dashboard, an RS485 bus listened to without sending, several Modbus devices behind one port. The app now comes as a prebuilt image.

### New

- **Modbus, decode values:** under "Read registers": 16, 32 and 64 bit integers, floats or text, with the register and byte order ("swap") and a factor as Home Assistant's Modbus integration reads them, and the matching sensor to copy into `configuration.yaml`.
- **Modbus, bus scan:** asks each unit found who it is (device identification, SunSpec) and shows vendor, model, version and a fitting integration.
- **Modbus, timing tips:** on the status card: a longer or shorter timeout, a cache, what a long queue or many exceptions mean.
- **Modbus, registers that may be written:** addresses and ranges; a write outside is refused with exception 02. The card **Writes** lists the clients' last writes and their result.
- **Modbus, listen on RS485:** a new kind of connection for a bus that has a master already (e.g. an inverter and its meter). The app only listens, never sends, and answers reads from what it heard.
- **Modbus, units of other connections:** one port for several devices; a unit asked here is answered by another Modbus connection's device.
- **EnOcean, senders:** every sender ID heard with kind, count, last seen, repeaters, reception (ESP3) and which gateway heard it; new senders marked, IDs to copy.
- **Serial devices, meter readings as entities:** import and export in kWh and power in W over MQTT, for the Energy dashboard, read from what the meter sends anyway (on with the eHZ templates).
- **Serial devices, serial bridge in the network:** A serial bridge in the network (ESPHome stream server, Tasmota reading head, USR-TCP232) as the source of a connection, shared like a device of this host.
- **Serial devices, device moved:** when a device is missing and its adapter is plugged in elsewhere, the page offers to take it over.
- **All connections, clients:** names for client addresses (**Settings → Clients**), shown in the lists and events. A computer that connects for the first time is reported until it is marked as known or named.
- **All connections, disconnect clients:** a button on the connection's page and an MQTT button in Home Assistant; an EnOcean gateway with a fallback also gets buttons to switch.
- **All connections, maintenance:** one computer may use a connection alone for a while, e.g. for a service tool or a firmware update; the others are kept out until the time is up.
- **All connections, as a test case:** a connection's last frames as a file for an issue, EnOcean IDs replaced.

### Changed

- **Prebuilt image:** Home Assistant downloads the app instead of building gensio and ser2net on the device. Recorded traces and EnOcean captures are left out of Home Assistant's backups.

## 1.0.1 - 2026-10-23

Home Assistant is let in at an EnOcean gateway limited to Home Assistant and the apps again.

### Fixed

- **EnOcean, "Only Home Assistant and apps":** Home Assistant was refused at a discovered gateway and at the status port, so the EnOcean Eltako integration could not read the base ID and asked for it. It connects to the app's host name, which is the host's LAN address, and so comes from there, not from 127.0.0.1. A connection from the host to its own address now counts as 127.0.0.1 (EnOcean and Modbus proxy, status port, Modbus write lock).

## 1.0.0 - 2026-10-23

EnOcean gateways tell the EnOcean Eltako integration their model.

### New

- **EnOcean gateway model:** each gateway has a field **Model** (FAM-USB, FGW14-USB, FAM14, MGW-ETH, Symcon LAN, other ESP2 or ESP3 gateway) that goes to the EnOcean Eltako integration with the discovery (`model` next to name, port and protocol). The template sets it, and gateways saved before take it from their template; it must fit the protocol and may stay empty, then the discovery goes without it.

## 0.4.0 - 2026-10-22

EnOcean gateways get a fallback: a second gateway with the same base ID stands in when one fails. Also new: setting the base ID with the tools.

### New

- **EnOcean fallback gateway:** a second gateway with the same base ID stands in when one fails. It is set up as a normal connection and then picked in the first gateway's form; while it is the fallback it has no port of its own and is not offered to the integration. The first gateway reads its base ID every 10 s; when it is gone or stays silent, its programs go on through the fallback without reconnecting, and come back after 60 s of steady running or by hand. Optionally both gateways are heard, duplicates and the own sending dropped. The card "Gateways" shows both and switches by hand; "Fallback becomes the main gateway" swaps the hardware when a gateway broke. Notifications, MQTT entities (fallback active, active gateway, fallback ready) and the status for the integration tell which gateway is in use.
- **EnOcean base ID:** the tools set a new base ID, and ESP3 gateways show how many changes are left (the gateway allows only a few).
- **Modbus tools:** new "Write registers" (functions 5, 6, 15, 16) next to "Read registers". It asks for confirmation first, reads the value back afterwards and says whether it matches, and writes an event to the log. It stays locked on connections whose write access is "Nobody". The Read button moved into the row of fields.

### Changed

- **Saving a connection:** the form no longer asks whether to discard the changes just saved.
- **Documentation:** the MQTT base topic is `device_proxy` (it still said `ser2net`); the four network levels with their current names, including "Home Assistant and apps"; the Modbus write lock as it works now; menu paths as the interface names them; EnOcean in the introduction; the own MQTT broker; what an own ser2net.yaml may do. The README describes today's default for allowed clients and where the address of a connection is shown.
- **Connections:** the card no longer shows the address with a copy button (it is only needed for setup, and the detail page has it); instead it says when data last arrived, e.g. "Last data 3 s ago". Connections that are not running show nothing there, since their state already says why.
- **Allowed clients:** new EnOcean gateways leave the field empty, so they follow the network setting like the other kinds (before, they were limited to Home Assistant and apps and eo_man or PCT14 in the home network could not connect without a change). The button "Only Home Assistant and apps" stays for an own limit. The Z-Wave stick keeps its preset and says why: it takes commands and has no login. Existing connections keep what they have; a gateway with a limit shows a button "Follow the global setting" that empties the field, and the note says so.
- **Choice tiles** (gateway template, connection kind, settings): all tiles of a group are the same size in an even grid (seven templates sit four and three instead of six and one), and the chosen one is marked without its content moving.
- **Recent events:** always the full width, one line per event (time, level dot, text) in aligned columns instead of the time under the text. On serial and EnOcean the connection card is full width as well, as on Modbus.
- **Use in Home Assistant** (Modbus): folded at first like the tools and addresses.
- **Addresses:** the card is just called "Addresses", is folded at first like the tools (they are only needed for setup) and opens by itself when "Show addresses" in a hint jumps to it.
- **Foldable parts:** "More tools", "How it works with PCT14", the Home Assistant YAML and "Which formats work?" in the import get the same "›" marker as the ones in the settings; it turns when opened.
- **Tools card:** shows it can be folded: "Show" or "Collapse" with a chevron on the right, and the header is highlighted when the pointer is over it. On all kinds (serial, Modbus, EnOcean) the card is folded at first, shows in its title what it holds, remembers per kind whether it was opened, and opens by itself when a result is there.
- **Modbus tools:** read, write and scan share one grid, so the fields line up in four columns and the buttons sit in one column on the right (the scan's Start button no longer has a row of its own).
- **Detail page (EnOcean):** the six counters of the gateway card sit in an even grid of three by two, like the tiles of the other cards (value on top, label below); card headers line up across a pair; the clients table fits its card instead of being cut off.
- **EnOcean tools:** the "Capture" tool is called "Record frames (PCT14)" (German: "Telegramme aufzeichnen") and says how it differs from the permanent trace, so the two are not mixed up.
- **Settings, log:** the log section says it is the technical log for troubleshooting, where to find it in Home Assistant and how it differs from the Events tab.
- **Settings, MQTT "Advanced":** the three fields under MQTT "Advanced" line up at the top; the hint of the first no longer pushes the others down.
- **Live data** (detail page and recording): time and direction take only the room they need; on Modbus and EnOcean the description and the bytes share a line and wrap only when the card is narrow, instead of breaking every 16 bytes.
- **Detail page:** no side column any more; cards sit in pairs of two equal columns, in the order state, measurements, live data, tools, then addresses and settings last (the "no program connected" hint links to the addresses). Same order for serial, Modbus and EnOcean.
- **Edit page:** the preview of a Modbus or EnOcean connection moves below the form, above the save bar; its flow reads left to right.
- **Import:** the import of the EnOcean Proxy app's options is gone (that app was never in use): no "Fetch from the EnOcean Proxy app", no `import/enocean_proxy.yaml`.

### Fixed

- **Unsaved changes:** leaving the connection form by the header, the breadcrumb, a chip or the browser's back button now asks first, like Cancel did (before, the changes were gone).
- **After an app restart:** an open page shows new events and live data again (they stood still until the new counters passed the old ones).
- **Saving while the app is not reachable:** shows "no connection to the app" instead of nothing.
- **Settings after a restore:** the form shows the restored values (Save could put the old ones back), and the configuration history fills again after restoring a backup.
- **Connection details:** results of the scan or the baud rate detection no longer carry over to the next connection, and live data no longer shows twice on a slow connection.
- **Dialogs:** Tab stays inside, and the focus goes back to where it was. The level filter of the events has a German label; no id is used twice on the settings page.
- **Texts:** the network level "Home Assistant and apps" showed as `listen_apps`, Modbus exception 8 as `ex_8`; the English import preview said "höchstens 5 Clients". Errors of the Modbus write tool, of a restore and of the MQTT test are translated to German. The events "own ser2net.yaml cannot be used" and "import failed" show the reason in both languages (English showed a Python list). 39 texts nothing used any more are gone.
- **Modbus write lock:** a read only passes when its request has exactly the length of that read. On RTU and RTU over TCP the proxy passes the bytes on as they are, so a write frame hidden behind a read reached the device although writing was locked.
- **Modbus RTU:** the echo of diagnostics (function 8) is read to its end instead of being cut after 8 bytes. With "kick old user" a new client no longer gets in beside one that is still being pushed out.
- **EnOcean ESP3:** garbage whose first bytes look like a long frame no longer holds back every telegram until that many bytes have arrived (hours); the data CRC is checked, lengths are capped, and an unfinished frame is given up after 0.5 s.
- **Health check:** it no longer connects to the EnOcean ports as a client (with one client allowed and "kick old user" it pushed out the integration every minute, and it put two events a minute in the history). The app writes the gateways' state for it instead; when the app stops writing it, the check fails and the Supervisor restarts the app.
- **Recordings:** one that cannot be written (full disk, folder not writable) no longer freezes the live view and "last data" of every connection, nor reports "no data" for them.
- **Network gateways** (EnOcean, Modbus TCP, RTU over TCP): TCP keepalive notices a gateway that loses power without closing the connection, after about 90 s, and connects again.
- **EnOcean status port:** when it was taken (e.g. by the old EnOcean Proxy app), it is tried again every 30 s instead of only at the next change.
- **History:** a full disk or an I/O error no longer moves the history aside as damaged; the event is logged but not kept.
- **Further ser2net options:** only harmless ones are taken (buffer sizes, chardelay, sendon/closeon, signature, mDNS, …). `connback` can start a program through its gensio string and is refused, as are logins, LEDs and values that read a file (`*{…}`, `*(…)`), also in banner, openstr and closestr. An import or backup leaves them out with a note; a saved configuration drops them when loading.
- **Import and own ser2net.yaml:** reading runs beside the proxies instead of stopping them, and a text without colons no longer takes minutes to check. Uploads are limited to 1 MB.
- **Web interface API:** bodies of the wrong shape (a list instead of an object, a backup with a broken `config`) give 400 instead of 500; a Modbus import with `timeout: nan` uses the default.
- **Recordings, trace folder:** a download or delete no longer follows a symlink out of the trace folder.
- **Diagnostics:** the user name and password of an own MQTT broker were still in `status.json` of the ZIP (only `config.json` hid them). Both are replaced now.
- **MQTT password:** no longer sent to the browser (status every 2 s, configuration history). The form shows dots for a set password; sent back unchanged, the saved one stays, also for "Test".
- **Settings:** a settings change and saving the own ser2net.yaml at the same time no longer undo each other; the own file is written in turn with other changes and synced to disk.
- **Modbus and EnOcean proxies:** one that ends by an unexpected error starts again after 30 s (before, its port stayed closed until the next change or a restart of the app). Causes that ended it are caught now: a USB adapter pulled while it is opened, a host name like `a..b` (refused when saving as well), a full disk while capturing (only the capture ends).
- **EnOcean:** stopping or restarting a gateway no longer hangs when a client has stopped reading (a sleeping PC); saving hung with it. A client that sends faster than the gateway is no longer buffered without limit.
- **Tools:** an unexpected error ends a run as failed instead of leaving it "running" and locking the tools of that connection until a restart (e.g. baud rate detection on a device that is no tty).

## 0.3.1 - 2026-10-22

A pass over every page of the interface.

### Changed

- **Connections:** each card shows its clients as a small fill bar and the data rate as a curve of the last minute; a problem card shows its state once (stripe and chip) with a calm sentence below; the copy button is an icon, the recording chip sits in the chip row.
- **Detail page:** the addresses to copy have their own card at the top of the side column; live data uses the same direction words and sixteen-byte lines as the trace page, can be collapsed to one living line and wraps long lines; a connection bound to 127.x says it is reachable from this host only; the header carries a short recording chip that links to the trace; side cards with short tool buttons, a labelled data chart and "Recent events" for this connection.
- **Modbus details:** one status card (requests per second, problems only as chips) instead of six counters; clients and units in one card with tooltips on the column headers ("error replies" instead of "exceptions"); the Connection card moves to the side column; the read and scan forms fit one row; "Use in Home Assistant" leads with the device's integration in the interface and keeps the YAML as the fallback; "1 retry" instead of "1 retries"; the live view names the client once when only one asks.
- **Edit pages:** serial connections get a Basics card with the name like the other kinds; a sticky Delete / Cancel / Save bar, a "Not saved" chip, a confirmation on Cancel and a warning when the tab is closed with changes; templates folded for an existing connection and a confirmation before one overwrites fields; arrows on folded cards; the preview stays in view and says who may connect; Modbus answer timeout and retries sit with the device, the advanced options are grouped (pacing, clients, probe, recording) and the EnOcean send pause sits with the gateway. A bind address of 127.x now says only this host may connect, and a warning appears when allowed clients name networks that address can never serve.
- **Import:** content without any connection stays at the first step with an error; the first step names each thing once and folds the list of formats away; one conflict chip per holder and one note per device; paths no longer break inside short names; on a phone the steps stay in one row and each entry is a card; the footer with "Take over" stays at the bottom of a long list.
- **Events and trace:** Live and History share one filter bar and one row format; connections as a chip bar on the trace page; hex and ASCII in sixteen-byte lines at every width; direction badges use the words of the recording switch.
- **Settings:** every card's Save button is active only after a change and says "Not saved"; the side navigation marks the section in view; the card for an own ser2net.yaml offers "From the forms" and "Own file", the editor on demand and an automatic check while typing, with saving locked on errors.
- **Readability:** hints, field labels and table headers are 13 px, the grey text has more contrast in light and dark.

## 0.3.0 - 2026-10-22

### New

- **Home network:** who counts as "LAN" is now a list under **Settings → Network → Allowed networks**. The host's own network is predefined, further networks can be added; Home Assistant and the apps are always allowed. Existing installations keep the private ranges.
- **Backup and restore:** **Settings → Back up and transfer** saves all connections (serial, Modbus, EnOcean) and the settings as one file and restores them after a preview and a confirmation. Import and the ser2net export moved there; the export says it holds the serial connections only.
- **Confirmations:** before switching off a connection with clients, before an import replaces connections and before deleting.

### Changed

- **Connections overview:** one status band instead of four tiles, problems first with their own filter and a next step, compact cards that open the details as a whole.
- **Connection pages:** device before name, serial interface and network access as separate cards, alerts block, "Active" as its own switch, delete set apart; the detail page shows one connection card with the real networks and reachability per target.
- **Events:** log sorted by time with day rows, level buttons with counts, plain-language connection errors, names link to the connection, labelled history bars.
- **Trace:** one recording switch for the chosen connection in plain words, live view with line count, clear and millisecond times, recorded files name their connection, copyable path.
- **Import:** collisions in plain words, select all, the connections "Replace all" removes are named, and the finished step counts added, replaced and skipped connections.
- **Narrow screens:** header chips wrap, the navigation fits one row, the trace page picks the connection from a list. Messages of the API and the tools are shown in German as well.

## 0.2.1 - 2026-10-22

### New

- **EnOcean:** the base ID is read from the gateway once after each connection (nothing goes over the air), so it shows in the list and on the detail page without anyone asking.

### Changed

- **Looks:** a sticky header with pill tabs, softer cards with a light shadow, connection cards with a coloured status edge and a kind icon; light and dark.
- **EnOcean detail page:** air time and replay buffer are two big cards at the top with a large number, a bar (80 % mark for the air time), the oldest buffered telegram and a status in plain words (below the limit, nearly at the limit, collecting, program connected, full, off).
- **Settings:** the menu on the left stays in view while scrolling (when it sits beside the content).
- **Addresses:** an address that cannot be reached now says why (bound to this host, allowed clients, network setting) and shows the address.
- **Docs:** the app's **Configuration** tab in the Supervisor is empty on purpose; DOCS and both READMEs now point to the sidebar entry **Device Proxy**, where everything is set up.

## 0.2.0 - 2026-10-21

### New

- **EnOcean gateways** (taken over from the EnOcean Proxy app, which this replaces)
  - A third kind of connection: one FAM-USB, FAM14, FGW14-USB, USB300/TCM310, MGW-ETH or Symcon LAN gateway for several programs, over USB or TCP, ESP2 or ESP3, with templates.
  - Whole frames in turn with a pause, the gateway's answers to the program that asked, no echo to the others, slow programs disconnected, reconnecting by itself.
  - Replay for the EnOcean Eltako integration (`EOPX REPLAY`, with reception times), optionally kept on disk over a restart of the app.
  - Discovery by the integration and a read-only status for its gateway cards (port 9199, Home Assistant and the apps only); settings under **Settings → EnOcean**.
  - Detail page: issues in plain words, live frames with sender and kind (search, direction, filter by sender, copy, take over into send), air time against the 1 % limit, counters, replay buffer, base ID; tools: gateway test, sending a checked frame (checksum added or fixed), captures as JSON lines with a lock for PCT14.
  - New gateways take Home Assistant and the apps only (the app runs in the host network).
  - Notification at 80 % air time; MQTT entities: reachable, telegrams, air time.
  - Moving: the EnOcean Proxy app's options are fetched from Home Assistant, pasted or put into `import/enocean_proxy.yaml`.
- **For all connections:** filter chips by kind above the list; a running capture shows in the header.

### Fixed

- **Modbus TCP:** a Modbus TCP connection saved without a device field could not be loaded.

## 0.1.0 - 2026-10-21

First version.

### New

- **Connections:**
  - Set up in a web interface in the sidebar: device list with stable names, templates, all important ser2net options, live `ser2net.yaml` preview.
  - Saving rebuilds only the changed connection; the others keep their clients.
  - Clients from private networks only by default; keep a device open; clients that stop reading are reported.
- **Modbus proxy:**
  - A Modbus device for several Modbus TCP clients: Modbus TCP, Modbus RTU on an RS485 adapter, RTU over TCP; requests in turn, each answer to the client that asked.
  - Timeout, retries, pause after connecting and between requests; gateway exceptions when the device does not answer.
  - Status with requests, unanswered requests and answer time, also per unit id; decoded requests and answers in the trace.
  - Write access per connection, a cache for reads, clients taking turns, up to 4 connections to a network device, unit ids rewritten, an optional probe read.
  - Tools: read registers, scan the bus for unit ids.
- **Import and export:**
  - ser2net 4 `ser2net.yaml` (version 1 and 2), ser2net 3 `ser2net.conf` and the options of ha-modbusproxy (or a modbus-proxy file), with a preview; export as `ser2net.yaml`; or use your own file as it is.
- **Status and diagnosis:**
  - Device, clients, data rate, last data, line errors from the driver, FTDI latency.
  - Live data and traces without taking a client place; recording without disconnecting.
  - Smart meter tools: SML (with CRC check) and D0, baud rate detection.
  - Events and 30-day history, configuration history with restore, diagnostics ZIP.
- **Home Assistant:**
  - Notifications (optionally to a notify service).
  - Entities over MQTT discovery, one device per connection with a switch (for Modbus: reachable, requests, unanswered requests, answer time).
- **Under the hood:**
  - ser2net 4.6.8 and gensio 3.0.4 built from their releases; admin interface on a socket inside the app; restarts, health check and backups handled.
  - German and English, light and dark, phone width.
