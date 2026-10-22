# Changelog

## 0.3.0

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
- **Events**: Live and History share one filter bar and one row format; log sorted by time with day rows, level buttons with counts, plain-language
  connection errors, names link to the connection, labelled history bars.
- **Live data** on the detail page can be collapsed to one living line (last data, rate, last
  block); the choice is remembered per connection, a card never opened yet opens when data
  arrives, and a collapsed card polls only every five seconds.
- **Trace**: one recording switch for the chosen connection in plain words, live view with line
  count, clear and millisecond times, recorded files name their connection, copyable path.
- **Import**: collisions in plain words, select all, the connections "Replace all" removes are
  named, and the finished step counts added, replaced and skipped connections.
- **Own ser2net.yaml**: a card of its own with the two choices "From the forms" and "Own file", the
  editor only when you want it, an automatic check while typing, saving locked on errors and a
  button to refill the file from the forms.
- Confirmations before switching off a connection with clients, before an import replaces
  connections and before deleting.
- Narrow screens: header chips wrap, the navigation fits one row, the trace page picks the
  connection from a list. Messages of the API and the tools are shown in German as well.

## 0.2.1

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

## 0.2.0

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

## 0.1.0

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
