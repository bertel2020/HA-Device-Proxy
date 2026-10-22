# Changelog

## Unreleased

- **Connections**: the card no longer shows the address with a copy button (it is only needed for
  setup, and the detail page has it); instead it says when data last arrived, e.g. "Last data 3 s ago".
  Connections that are not running show nothing there, since their state already says why.
- **Tools card**: on all kinds (serial, Modbus, EnOcean) the card is folded at first, shows in its
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

## 0.3.1

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
