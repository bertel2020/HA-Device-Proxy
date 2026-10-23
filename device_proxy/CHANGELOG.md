# Changelog

## Unreleased

- **EnOcean gateway model**: each gateway has a field **Model** (FAM-USB, FGW14-USB, FAM14,
  MGW-ETH, Symcon LAN, other ESP2 or ESP3 gateway) that goes to the EnOcean Eltako integration
  with the discovery (`model` next to name, port and protocol). The template sets it, and
  gateways saved before take it from their template; it must fit the protocol and may stay
  empty, then the discovery goes without it.

## 0.4.0

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
