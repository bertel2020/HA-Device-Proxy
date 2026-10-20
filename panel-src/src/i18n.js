// Texts in German and English. Events and import notes come from the app as a code plus values;
// they are worded here, so the history reads in the viewer's language.
const TEXT = {
  de: {
    appTitle: "Ser2Net", running: "ser2net läuft", notRunning: "ser2net läuft nicht",
    navConnections: "Verbindungen", navEvents: "Ereignisse", navTrace: "Mitschnitt", navSettings: "Einstellungen",
    navMain: "Bereiche", breadcrumb: "Pfad",
    connectionsTitle: "Verbindungen", connectionsSub: "Serielle Geräte, die über das Netzwerk bereitgestellt werden.",
    importExport: "Import / Export", addConnection: "Verbindung hinzufügen",
    tileActive: "Aktiv", tileOf: "von {n}", tileClients: "Clients verbunden", tileErrors: "Leitungsfehler", tileReach: "Erreichbar aus",
    listen_local: "nur dieser Rechner", listen_lan: "LAN · nur private Netze", listen_all: "alle Netze",
    stRunning: "Läuft", stDisabled: "Deaktiviert", stMissing: "Gerät fehlt", stWaiting: "Wartet auf ser2net", stPending: "Änderung wartet",
    clients: "Clients", clientsOf: "{n} von {m}", noClients: "Keine Clients verbunden.", disabledText: "Verbindung ist deaktiviert – Port geschlossen.",
    missingText: "Gerät nicht angeschlossen.", since: "seit {t}", copy: "Kopieren", copied: "Kopiert", edit: "Bearbeiten", details: "Details",
    switchLabel: "{name} aktiv", emptyTitle: "Noch keine Verbindungen", emptyText: "Lege eine Verbindung an oder übernimm deine bestehende ser2net-Konfiguration.",
    emptyImport: "ser2net.yaml / ser2net.conf importieren",
    customActive: "Eigene ser2net.yaml ist aktiv", customActiveText: "Die Formulare sind gespeichert, werden aber nicht verwendet. Ports von ser2net:",
    toSettings: "Zu den Einstellungen",
    stuck: "Client {a} liest nicht", lineErrors: "{n} Leitungsfehler", latencyRO: "FTDI-Latenz nicht änderbar", keptOpen: "Gerät offen gehalten",
    // detail
    live: "Live-Daten", liveSub: "Gelesen aus dem Mitschnitt von ser2net – belegt keinen Client-Platz.", pause: "Pausieren", resume: "Fortsetzen",
    hexOnly: "Nur Hex", hexAscii: "Hex + ASCII", liveEmpty: "Noch keine Daten. ser2net öffnet das Gerät erst, wenn ein Client verbunden ist – oder mit „Gerät offen halten“.",
    clientTh: "Client", sinceTh: "Verbunden seit", toClient: "an Client", fromClient: "vom Client", queued: "Warteschlange",
    addresses: "Adressen zum Kopieren", target_ha: "Home Assistant (Integrationen)", target_apps: "Andere Apps (z. B. Z-Wave JS UI)", target_lan: "Andere Rechner im LAN",
    notReachable: "nicht erreichbar mit dieser Einstellung", lanUnknown: "LAN-Adresse unbekannt",
    configuration: "Konfiguration", line: "Leitung", noLineErrors: "keine Fehler", lineUnsupported: "Der Treiber zählt keine Fehler.", lineClosed: "Zählt nur, solange das Gerät offen ist.",
    frame: "Frame", parity: "Parität", overrun: "Overrun", brk: "Break", bufOverrun: "Puffer",
    dataFromDevice: "Daten vom Gerät", lastData: "Letzte Daten", never: "noch nie", recent: "Verlauf", allEvents: "Alle Ereignisse",
    device: "Gerät", resolved: "Aufgelöst", usb: "USB", serialNo: "Seriennr.", interface: "Schnittstelle", network: "Netzwerk",
    // edit
    newConnection: "Neue Verbindung", editConnection: "Verbindung bearbeiten", template: "Vorlage", templateSub: "Füllt die Felder passend vor. Alles bleibt änderbar.",
    tpl_ehz_sml: "eHZ SML", tpl_ehz_d0: "eHZ D0", tpl_zwave: "Z-Wave-Stick", tpl_generic: "Allgemein",
    tplsub_ehz_sml: "9600 8N1 · bis 5 Clients", tplsub_ehz_d0: "9600 7E1 · bis 5 Clients", tplsub_zwave: "115200 8N1 · nodelay", tplsub_generic: "9600 8N1 · 1 Client",
    basics: "Grunddaten", name: "Name", enabled: "Aktiv", enabledText: "Nach dem Speichern bereitstellen", devicePick: "Gerät",
    deviceOther: "Anderer Pfad …", devicePath: "Pfad", usedBy: "belegt: {n}", noSerial: "ohne Seriennr.", ambiguous: "Mehrere gleiche Adapter ohne Seriennummer: Auswahl über den USB-Port (by-path). In Proxmox diese Geräte nach Port durchreichen.",
    ifNet: "Schnittstelle und Netzwerk", baud: "Baudrate", format: "Format", dataBits: "Datenbits", parityF: "Parität", stopBits: "Stoppbits",
    port: "TCP-Port", maxClients: "Max. Clients", maxClientsHint: "Mehr als 1 nur, wenn das Gerät das verträgt.", mode: "Modus",
    mode_raw: "Bytes unverändert durchreichen – passt für die meisten Integrationen.", mode_rfc2217: "Clients stellen Baudrate und Leitungen selbst ein (rfc2217://…).", mode_telnet: "Für Terminal-Zugriff per telnet.",
    advanced: "Erweitert", advancedSub: "ser2net-Optionen · alles optional", open: "aufklappen", closeA: "zuklappen", set: "{n} gesetzt",
    serialSide: "Serielle Seite", connectionSide: "Verbindung", tcpSide: "TCP", appSide: "App",
    o_local: "Modem-Steuerleitungen (CD) ignorieren", o_rtscts: "Hardware-Flusskontrolle", o_xonxoff: "Software-Flusskontrolle",
    o_hangup_when_done: "DTR fallen lassen, wenn der letzte Client geht", o_nobreak: "Break-Signal unterdrücken", o_low_latency: "FTDI-Latenz 1 ms statt 16 ms",
    o_kickolduser: "Bei vollem Limit einen alten Client trennen", o_chardelay: "Bytes sammeln und gebündelt senden", o_nodelay: "Nagle aus – weniger Latenz",
    o_keep_open: "Gerät offen halten (die App verbindet sich selbst, belegt einen Platz)", o_stuck_disconnect: "Clients trennen, wenn einer nicht mehr liest",
    o_notify_missing: "Benachrichtigen, wenn das Gerät fehlt", o_notify_no_client: "Benachrichtigen, wenn kein Client verbunden ist",
    dtr: "DTR beim Öffnen", rts: "RTS beim Öffnen", lineDefault: "unverändert", on: "an", off: "aus", rs485: "RS485", rs485Hint: "z. B. 0:0:rts_on_send – leer = aus",
    timeout: "Timeout (s, 0 = nie)", retry: "Neuer Versuch nach (s, 0 = Standard)", remaddr: "Erlaubte Clients (remaddr)", remaddrHint: "Leer: nach der globalen Einstellung. Adressen oder Netze, mit Leerzeichen getrennt.",
    banner: "Banner", openstr: "openstr", closestr: "closestr", bind: "Bind-Adresse", bindHint: "Leer: nach der globalen Einstellung.",
    extra: "Weitere Optionen", extraHint: "Eine pro Zeile: name: wert", traceMode: "Mitschnitt aufzeichnen", silence: "Warnen, wenn keine Daten seit (min, 0 = nie)",
    tr_off: "aus", tr_rx: "vom Gerät", tr_tx: "zum Gerät", tr_both: "beide Richtungen",
    preview: "Vorschau ser2net.yaml", previewSub: "So wird die Verbindung an ser2net übergeben.", save: "Speichern", cancel: "Abbrechen", delete: "Löschen",
    saveHint: "Nur diese Verbindung wird neu aufgebaut. Andere bleiben verbunden.", saved: "Gespeichert.", savedRebuilt: "Gespeichert. Neu aufgebaut: {n}.", savedReconnect: " Clients neu verbunden: {n}.",
    deleteConfirm: "Verbindung „{n}“ löschen? Ihre Clients werden getrennt.", errorsBelow: "Bitte die markierten Felder prüfen.",
    // import
    importTitle: "Import / Export", stepChoose: "Datei wählen", stepPreview: "Vorschau prüfen", stepDone: "Übernommen",
    importChoose: "ser2net.yaml oder ser2net.conf auswählen", importDrop: "Datei auswählen oder Inhalt einfügen", importFormats: "ser2net 4 (YAML, Version 1 und 2) oder ser2net 3 (ser2net.conf)",
    chooseFile: "Datei auswählen", pasteHere: "… oder den Inhalt hier einfügen", readPreview: "Vorschau", otherFile: "Andere Datei",
    format_0: "ser2net 3 (ser2net.conf)", format_1: "ser2net 4 · YAML Version 1", format_2: "ser2net 4 · YAML Version 2",
    found: "{n} Verbindungen gefunden", merge: "Ergänzen", mergeSub: "Vorhandene bleiben; bei Kollisionen wählst du pro Verbindung", replaceAll: "Alles ersetzen", replaceAllSub: "Vorhandene Verbindungen werden entfernt",
    result: "Ergebnis", resOk: "wird übernommen", resNotes: "mit Hinweisen", resNo: "nicht übertragbar", resConflict: "Kollision",
    onConflict: "Bei Kollision", c_replace: "vorhandene ersetzen", c_new_port: "neuer Port", c_skip: "überspringen", take: "Übernehmen",
    selected: "{n} von {m} ausgewählt", apply: "{n} übernehmen", doneTitle: "{n} Verbindungen übernommen", doneText: "Der vorherige Stand liegt in der Konfig-Historie.",
    toConnections: "Zu den Verbindungen", exportTitle: "Export", exportText: "Die Verbindungen als ser2net-4-ser2net.yaml – zum Sichern oder für einen anderen Rechner.",
    exportDisabled: "Deaktivierte Verbindungen mitnehmen", download: "ser2net.yaml herunterladen", ownTitle: "Datei lieber direkt verwenden?", ownText: "Für Sonderfälle, die die Formulare nicht abbilden.",
    toSource: "Konfigurationsquelle umstellen", fileNotes: "Hinweise zur Datei",
    // events
    eventsTitle: "Ereignisse", eventsSub: "Live-Log der App und Historie.", tabLive: "Live-Log", tabHistory: "Historie", allConnections: "Alle Verbindungen",
    search: "Suche", searchPh: "z. B. getrennt, 192.168.1.20", lv_info: "Info", lv_warning: "Warnung", lv_error: "Fehler", lv_debug: "Debug",
    entries: "{n} Einträge", both: "Beide", paused: "Pausiert", liveState: "Live", noEntries: "Keine Einträge für diesen Filter.",
    drops: "Abbrüche ({d} T.)", availability: "Verfügbar", stable: "stabil", unstable: "{n}× getrennt", timeline: "Zeitleiste", retention: "Aufbewahrung {d} Tage",
    today: "Heute", yesterday: "Gestern", summed: "{n}× zusammengefasst",
    // trace
    traceTitle: "Mitschnitt", traceSub: "Bytes zwischen Gerät und Clients. Aufzeichnen trennt keine Clients; Dateien rotieren automatisch.",
    recording: "zeichnet auf · {m}", notRecording: "keine Aufzeichnung", files: "Dateien", fileTh: "Datei", sizeTh: "Größe", changedTh: "Geändert",
    rotation: "Rotation: {mb} MB je Datei · {k} ältere behalten", change: "ändern", deleteFile: "„{n}“ löschen?",
    // settings
    settingsTitle: "Einstellungen", sNet: "Netzwerk", sNetSub: "Gilt für alle Verbindungen ohne eigene Bind-Adresse oder remaddr.",
    net_local: "Nur dieser Rechner", netsub_local: "127.0.0.1 · nur Home Assistant", net_lan: "LAN", netsub_lan: "nur aus privaten Netzen (empfohlen)", net_all: "Alle Netze", netsub_all: "ohne Einschränkung",
    netWarn: "ser2net hat keine Anmeldung. Wer den Port erreicht, kann das Gerät lesen und steuern.",
    sSource: "Konfigurationsquelle", sSourceSub: "Formulare oder eine eigene ser2net.yaml für Sonderfälle.", forms: "Formulare", own: "Eigene ser2net.yaml",
    ownWarn: "Solange die eigene Datei aktiv ist, werden die Formulare nicht verwendet. Ohne admin-Abschnitt: die App fügt ihren eigenen an.",
    check: "Prüfen", saveFile: "Speichern", saveUse: "Speichern und verwenden", checkOk: "Gültig · {n} Verbindungen", notChecked: "Noch nicht geprüft",
    sHistory: "Konfig-Historie", sHistorySub: "die letzten 20 Stände", current: "aktuell", diff: "Unterschiede", hide: "Ausblenden", restore: "Wiederherstellen",
    restoreConfirm: "Diesen Stand wiederherstellen? Geänderte Verbindungen werden neu aufgebaut.", src_ui: "Oberfläche", src_import: "Import", src_custom: "eigene Datei", src_restore: "Wiederherstellung", src_test: "Test",
    sLogging: "Logging und Speicher", logLevel: "Log-Level", historyDays: "Historie aufbewahren (Tage)", traceMb: "Mitschnitt: Größe je Datei (MB)", traceKeep: "Mitschnitt: ältere Dateien",
    debounceCount: "Wiederholungen zusammenfassen ab", debounceMinutes: "innerhalb von (min)", sAbout: "Über", app: "App", license: "Lizenz MIT", source: "Quelle",
    // tools
    tools: "Werkzeuge", meterCheck: "Zählerdaten prüfen", meterCheckSub: "Wertet die Daten der letzten 30 s als SML oder D0 aus.",
    proto_sml: "SML", proto_d0: "D0 (Text)", proto_unknown: "kein Zählerprotokoll erkannt", telegrams: "{n} Telegramme", validCrc: "{n} gültig (CRC)", validD0: "{n} vollständig",
    noData30: "In den letzten 30 s kamen keine Daten.", baudDetect: "Baudrate erkennen", baudDetectSub: "Hört jede Baudrate und jedes Format kurz ab; sendet nichts.",
    baudConfirm: "Für die Erkennung gibt ser2net das Gerät bis zu etwa einer Minute frei – die Clients dieser Verbindung werden getrennt und verbinden sich danach neu. Starten?",
    start: "Starten", detecting: "Prüfe {d} von {t} …", detected: "Erkannt: {b} {f}", noDetect: "Nichts Eindeutiges erkannt.", applyThis: "Übernehmen",
    candidates: "Beste Treffer", score: "Treffer",
    "obis_1-0:1.8.0": "Bezug gesamt", "obis_1-0:2.8.0": "Einspeisung gesamt", "obis_1-0:16.7.0": "Leistung",
    "obis_1-0:1.8.1": "Bezug Tarif 1", "obis_1-0:1.8.2": "Bezug Tarif 2",
    // settings: notifications and diagnostics
    sNotify: "Benachrichtigungen", sNotifySub: "Als Meldung im Glocken-Symbol von Home Assistant; optional zusätzlich aufs Handy.",
    notifyGrace: "Melden, wenn ein Problem länger dauert als (s)", notifyDismiss: "Meldung entfernen, wenn das Problem behoben ist",
    notifyService: "Zusätzlich senden an (notify-Dienst)", notifyNone: "nicht senden", notifyResolved: "Auch melden, wenn es wieder in Ordnung ist",
    notifyStuck: "Ein Client liest nicht mehr", notifyLine: "Leitungsfehler steigen", notifySer2net: "ser2net startet immer wieder neu",
    notifyLanguage: "Sprache der Meldungen", noClientMinutes: "„Kein Client“ melden nach (min)", notifyPerConnection: "Gerät fehlt, kein Client und keine Daten stellst du pro Verbindung ein.",
    sDiag: "Diagnose", sDiagSub: "ZIP mit Versionen, Konfiguration, Status, Geräten und Ereignissen – ohne IP-Adressen, Clients nur gezählt.", diagDownload: "Diagnose-Paket herunterladen",
    // generic
    error: "Fehler", loading: "Lädt …", confirm: "Bestätigen", yes: "Ja", no: "Nein", close: "Schließen", language: "Sprache",
    connectionLost: "Keine Verbindung zur App – zeige den letzten Stand.",
  },
  en: {
    appTitle: "Ser2Net", running: "ser2net running", notRunning: "ser2net not running",
    navConnections: "Connections", navEvents: "Events", navTrace: "Trace", navSettings: "Settings",
    navMain: "Sections", breadcrumb: "Path",
    connectionsTitle: "Connections", connectionsSub: "Serial devices shared over the network.",
    importExport: "Import / export", addConnection: "Add connection",
    tileActive: "Active", tileOf: "of {n}", tileClients: "Clients connected", tileErrors: "Line errors", tileReach: "Reachable from",
    listen_local: "this host only", listen_lan: "LAN · private networks only", listen_all: "all networks",
    stRunning: "Running", stDisabled: "Disabled", stMissing: "Device missing", stWaiting: "Waiting for ser2net", stPending: "Change pending",
    clients: "Clients", clientsOf: "{n} of {m}", noClients: "No clients connected.", disabledText: "Connection disabled – port closed.",
    missingText: "Device not plugged in.", since: "since {t}", copy: "Copy", copied: "Copied", edit: "Edit", details: "Details",
    switchLabel: "{name} active", emptyTitle: "No connections yet", emptyText: "Add a connection or take over your existing ser2net configuration.",
    emptyImport: "Import ser2net.yaml / ser2net.conf",
    customActive: "Your own ser2net.yaml is in use", customActiveText: "The forms are kept but not used. ser2net's ports:",
    toSettings: "To the settings",
    stuck: "Client {a} does not read", lineErrors: "{n} line errors", latencyRO: "FTDI latency cannot be changed", keptOpen: "Device kept open",
    live: "Live data", liveSub: "Read from ser2net's trace – takes no client place.", pause: "Pause", resume: "Resume",
    hexOnly: "Hex only", hexAscii: "Hex + ASCII", liveEmpty: "No data yet. ser2net opens the device only while a client is connected – or with “keep device open”.",
    clientTh: "Client", sinceTh: "Connected since", toClient: "to client", fromClient: "from client", queued: "Queue",
    addresses: "Addresses to copy", target_ha: "Home Assistant (integrations)", target_apps: "Other apps (e.g. Z-Wave JS UI)", target_lan: "Other computers in the LAN",
    notReachable: "not reachable with this setting", lanUnknown: "LAN address unknown",
    configuration: "Configuration", line: "Line", noLineErrors: "no errors", lineUnsupported: "The driver does not count errors.", lineClosed: "Counted only while the device is open.",
    frame: "Frame", parity: "Parity", overrun: "Overrun", brk: "Break", bufOverrun: "Buffer",
    dataFromDevice: "Data from the device", lastData: "Last data", never: "never", recent: "Recent", allEvents: "All events",
    device: "Device", resolved: "Resolved", usb: "USB", serialNo: "Serial no.", interface: "Interface", network: "Network",
    newConnection: "New connection", editConnection: "Edit connection", template: "Template", templateSub: "Fills in the fields; everything stays editable.",
    tpl_ehz_sml: "eHZ SML", tpl_ehz_d0: "eHZ D0", tpl_zwave: "Z-Wave stick", tpl_generic: "Generic",
    tplsub_ehz_sml: "9600 8N1 · up to 5 clients", tplsub_ehz_d0: "9600 7E1 · up to 5 clients", tplsub_zwave: "115200 8N1 · nodelay", tplsub_generic: "9600 8N1 · 1 client",
    basics: "Basics", name: "Name", enabled: "Active", enabledText: "Share after saving", devicePick: "Device",
    deviceOther: "Other path …", devicePath: "Path", usedBy: "used: {n}", noSerial: "no serial no.", ambiguous: "Several identical adapters without a serial number: chosen by USB port (by-path). In Proxmox pass these through by port.",
    ifNet: "Interface and network", baud: "Baud rate", format: "Format", dataBits: "Data bits", parityF: "Parity", stopBits: "Stop bits",
    port: "TCP port", maxClients: "Max. clients", maxClientsHint: "More than 1 only if the device copes with it.", mode: "Mode",
    mode_raw: "Bytes passed on unchanged – fits most integrations.", mode_rfc2217: "Clients set baud rate and lines themselves (rfc2217://…).", mode_telnet: "For terminal access with telnet.",
    advanced: "Advanced", advancedSub: "ser2net options · all optional", open: "open", closeA: "close", set: "{n} set",
    serialSide: "Serial side", connectionSide: "Connection", tcpSide: "TCP", appSide: "App",
    o_local: "Ignore the modem lines (CD)", o_rtscts: "Hardware flow control", o_xonxoff: "Software flow control",
    o_hangup_when_done: "Drop DTR when the last client leaves", o_nobreak: "Suppress the break signal", o_low_latency: "FTDI latency 1 ms instead of 16 ms",
    o_kickolduser: "Disconnect an old client when full", o_chardelay: "Collect bytes and send them together", o_nodelay: "Nagle off – less latency",
    o_keep_open: "Keep the device open (the app connects itself, takes a place)", o_stuck_disconnect: "Disconnect the clients when one stops reading",
    o_notify_missing: "Notify when the device is missing", o_notify_no_client: "Notify when no client is connected",
    dtr: "DTR on open", rts: "RTS on open", lineDefault: "unchanged", on: "on", off: "off", rs485: "RS485", rs485Hint: "e.g. 0:0:rts_on_send – empty = off",
    timeout: "Timeout (s, 0 = never)", retry: "Retry after (s, 0 = default)", remaddr: "Allowed clients (remaddr)", remaddrHint: "Empty: as the global setting. Addresses or networks, separated by spaces.",
    banner: "Banner", openstr: "openstr", closestr: "closestr", bind: "Bind address", bindHint: "Empty: as the global setting.",
    extra: "Further options", extraHint: "One per line: name: value", traceMode: "Record trace", silence: "Warn when no data for (min, 0 = never)",
    tr_off: "off", tr_rx: "from the device", tr_tx: "to the device", tr_both: "both directions",
    preview: "Preview ser2net.yaml", previewSub: "This is what ser2net gets.", save: "Save", cancel: "Cancel", delete: "Delete",
    saveHint: "Only this connection is rebuilt. The others stay connected.", saved: "Saved.", savedRebuilt: "Saved. Rebuilt: {n}.", savedReconnect: " Clients reconnected: {n}.",
    deleteConfirm: "Delete connection “{n}”? Its clients are disconnected.", errorsBelow: "Please check the marked fields.",
    importTitle: "Import / export", stepChoose: "Choose file", stepPreview: "Check preview", stepDone: "Done",
    importChoose: "Choose ser2net.yaml or ser2net.conf", importDrop: "Choose a file or paste its content", importFormats: "ser2net 4 (YAML, version 1 and 2) or ser2net 3 (ser2net.conf)",
    chooseFile: "Choose file", pasteHere: "… or paste the content here", readPreview: "Preview", otherFile: "Other file",
    format_0: "ser2net 3 (ser2net.conf)", format_1: "ser2net 4 · YAML version 1", format_2: "ser2net 4 · YAML version 2",
    found: "{n} connections found", merge: "Add", mergeSub: "Existing ones stay; on a collision you choose per connection", replaceAll: "Replace all", replaceAllSub: "Existing connections are removed",
    result: "Result", resOk: "taken over", resNotes: "with notes", resNo: "cannot be taken over", resConflict: "collision",
    onConflict: "On collision", c_replace: "replace existing", c_new_port: "new port", c_skip: "skip", take: "Take over",
    selected: "{n} of {m} selected", apply: "Take over {n}", doneTitle: "{n} connections taken over", doneText: "The previous state is in the configuration history.",
    toConnections: "To the connections", exportTitle: "Export", exportText: "The connections as a ser2net 4 ser2net.yaml – as a backup or for another computer.",
    exportDisabled: "Include disabled connections", download: "Download ser2net.yaml", ownTitle: "Rather use the file as it is?", ownText: "For setups the forms cannot express.",
    toSource: "Change the configuration source", fileNotes: "Notes on the file",
    eventsTitle: "Events", eventsSub: "The app's live log and history.", tabLive: "Live log", tabHistory: "History", allConnections: "All connections",
    search: "Search", searchPh: "e.g. disconnected, 192.168.1.20", lv_info: "Info", lv_warning: "Warning", lv_error: "Error", lv_debug: "Debug",
    entries: "{n} entries", both: "Both", paused: "Paused", liveState: "Live", noEntries: "No entries for this filter.",
    drops: "Drops ({d} d)", availability: "Available", stable: "stable", unstable: "{n}× disconnected", timeline: "Timeline", retention: "Kept {d} days",
    today: "Today", yesterday: "Yesterday", summed: "{n}× summed up",
    traceTitle: "Trace", traceSub: "Bytes between device and clients. Recording disconnects no client; files rotate on their own.",
    recording: "recording · {m}", notRecording: "not recording", files: "Files", fileTh: "File", sizeTh: "Size", changedTh: "Changed",
    rotation: "Rotation: {mb} MB per file · {k} older kept", change: "change", deleteFile: "Delete “{n}”?",
    settingsTitle: "Settings", sNet: "Network", sNetSub: "Applies to all connections without their own bind address or remaddr.",
    net_local: "This host only", netsub_local: "127.0.0.1 · Home Assistant only", net_lan: "LAN", netsub_lan: "private networks only (recommended)", net_all: "All networks", netsub_all: "no limit",
    netWarn: "ser2net has no login. Whoever reaches the port can read and control the device.",
    sSource: "Configuration source", sSourceSub: "Forms, or your own ser2net.yaml for special cases.", forms: "Forms", own: "Own ser2net.yaml",
    ownWarn: "While your own file is in use, the forms are not used. No admin section: the app adds its own.",
    check: "Check", saveFile: "Save", saveUse: "Save and use", checkOk: "Valid · {n} connections", notChecked: "Not checked yet",
    sHistory: "Configuration history", sHistorySub: "the last 20 versions", current: "current", diff: "Differences", hide: "Hide", restore: "Restore",
    restoreConfirm: "Restore this version? Changed connections are rebuilt.", src_ui: "web interface", src_import: "import", src_custom: "own file", src_restore: "restore", src_test: "test",
    sLogging: "Logging and storage", logLevel: "Log level", historyDays: "Keep history (days)", traceMb: "Trace: size per file (MB)", traceKeep: "Trace: older files",
    debounceCount: "Sum up repeats from", debounceMinutes: "within (min)", sAbout: "About", app: "App", license: "License MIT", source: "Source",
    tools: "Tools", meterCheck: "Check meter data", meterCheckSub: "Reads the data of the last 30 s as SML or D0.",
    proto_sml: "SML", proto_d0: "D0 (text)", proto_unknown: "no meter protocol found", telegrams: "{n} telegrams", validCrc: "{n} valid (CRC)", validD0: "{n} complete",
    noData30: "No data in the last 30 s.", baudDetect: "Detect baud rate", baudDetectSub: "Listens briefly at each baud rate and format; sends nothing.",
    baudConfirm: "For the detection ser2net lets go of the device for up to about a minute – this connection's clients are disconnected and connect again afterwards. Start?",
    start: "Start", detecting: "Checking {d} of {t} …", detected: "Found: {b} {f}", noDetect: "Nothing clear found.", applyThis: "Use this",
    candidates: "Best matches", score: "Match",
    "obis_1-0:1.8.0": "Import total", "obis_1-0:2.8.0": "Export total", "obis_1-0:16.7.0": "Power",
    "obis_1-0:1.8.1": "Import tariff 1", "obis_1-0:1.8.2": "Import tariff 2",
    sNotify: "Notifications", sNotifySub: "As a notification under Home Assistant's bell; optionally also to a phone.",
    notifyGrace: "Report when a problem lasts longer than (s)", notifyDismiss: "Remove the notification when the problem is gone",
    notifyService: "Also send to (notify service)", notifyNone: "do not send", notifyResolved: "Also report when it is OK again",
    notifyStuck: "A client stops reading", notifyLine: "Line errors rise", notifySer2net: "ser2net keeps restarting",
    notifyLanguage: "Language of the notifications", noClientMinutes: "Report “no client” after (min)", notifyPerConnection: "Device missing, no client and no data are set per connection.",
    sDiag: "Diagnostics", sDiagSub: "ZIP with versions, configuration, status, devices and events – without IP addresses, clients only counted.", diagDownload: "Download diagnostics",
    error: "Error", loading: "Loading …", confirm: "Confirm", yes: "Yes", no: "No", close: "Close", language: "Language",
    connectionLost: "No connection to the app – showing the last state.",
  },
};

const EVENTS = {
  de: {
    app_started: "Gestartet mit {connections} Verbindungen, {active} aktiv",
    connection_loaded: "{state}: {device} · {format} · {mode} · Port {port} · bis {max_clients} Clients",
    config_changed: "Konfiguration gespeichert: {summary}",
    clients_reconnect: "{count} Client(s) getrennt, damit die Änderung greift",
    client_connected: "Client verbunden: {address}", client_disconnected: "Client getrennt: {address}",
    client_stuck: "Client {address} liest nicht ({queued} Bytes warten) – alle Clients dieser Verbindung werden gebremst",
    stuck_disconnected: "Clients getrennt, weil {address} nicht las",
    device: "Gerät gefunden: {device} → {target}", device_back: "Gerät wieder da: {device} → {target}", device_missing: "Gerät fehlt: {device}",
    keep_open_failed: "Gerät konnte nicht offen gehalten werden: {error}",
    ser2net_restart: "ser2net beendet (Code {code}), Neustart in {delay} s",
    line_errors: "Leitungsfehler seit Start: {frame} Frame, {parity} Parität, {overrun} Overrun, {buffer_overrun} Puffer, {break} Break",
    latency_read_only: "FTDI-Latenz ließ sich nicht auf 1 ms setzen: /sys ist für die App schreibgeschützt",
    custom_saved: "Eigene ser2net.yaml gespeichert ({connections} Verbindungen)",
    custom_invalid: "Eigene ser2net.yaml nicht verwendbar – nichts wird bereitgestellt",
    imported: "Import: {taken} übernommen, {skipped} übersprungen, {notes} Hinweise",
    import_failed: "Import fehlgeschlagen",
  },
  en: {},
};

const NOTES = {
  de: {
    device_missing: "Gerät {device} ist gerade nicht angeschlossen.", device_unstable: "{device} kann sich nach einem Neustart ändern – besser einen by-id- oder by-path-Namen wählen.",
    device_renamed: "{device} durch den stabilen Namen {stable} ersetzt.", option_extra: "Option {option} übernommen als „weitere Option“.",
    option_dropped: "Option {option} nicht übernommen.", serial_option_dropped: "Serielle Option {option} nicht übernommen.", legacy_option_dropped: "Option {option} nicht übernommen.",
    accepter_option_dropped: "Accepter-Option {option} nicht übernommen.", remaddr_port_dropped: "remaddr {address}: der Client-Port fällt weg.", remaddr_dropped: "remaddr {address} nicht lesbar, weggelassen.",
    trace_files_moved: "Trace-Dateien werden durch den Mitschnitt der App ersetzt.", external_file: "Option {option} liest eine externe Datei – bitte prüfen.",
    accepter_unsupported: "Accepter {accepter} wird nicht unterstützt (nur TCP, telnet, RFC2217).", connector_unsupported: "Connector {connector} wird nicht unterstützt (nur serielle Geräte).",
    invalid: "Ungültig: {errors}", admin_ignored: "Admin-Abschnitt ignoriert – die App hat ihren eigenen.", include_ignored: "include {path} ignoriert.",
    section_ignored: "Abschnitt {section} ignoriert.", define_unresolved: "Nicht aufgelöste Defines: {names}.", no_connections: "Keine Verbindungen in der Datei.",
    default_ignored: "DEFAULT {name} ignoriert.", line_unreadable: "Zeile nicht lesbar: {line}",
    yaml: "YAML-Fehler in Zeile {line}: {message}", admin_present: "Die Datei hat einen admin-Abschnitt – bitte entfernen, die App fügt ihren eigenen an.",
    port_twice: "Port {port} doppelt: {names}.", port_reserved: "Port {port} ist für die App reserviert.", legacy_format: "Das alte Format (ser2net.conf) kann ser2net 4 nicht lesen – bitte importieren.",
    unreadable: "Datei nicht lesbar: {error}",
  },
  en: {
    device_missing: "Device {device} is not plugged in right now.", device_unstable: "{device} may change after a restart – better choose a by-id or by-path name.",
    device_renamed: "{device} replaced by its stable name {stable}.", option_extra: "Option {option} kept as a further option.",
    option_dropped: "Option {option} not taken over.", serial_option_dropped: "Serial option {option} not taken over.", legacy_option_dropped: "Option {option} not taken over.",
    accepter_option_dropped: "Accepter option {option} not taken over.", remaddr_port_dropped: "remaddr {address}: the client port is dropped.", remaddr_dropped: "remaddr {address} unreadable, left out.",
    trace_files_moved: "Trace files are replaced by the app's trace.", external_file: "Option {option} reads an external file – please check.",
    accepter_unsupported: "Accepter {accepter} is not supported (TCP, telnet, RFC2217 only).", connector_unsupported: "Connector {connector} is not supported (serial devices only).",
    invalid: "Invalid: {errors}", admin_ignored: "Admin section ignored – the app has its own.", include_ignored: "include {path} ignored.",
    section_ignored: "Section {section} ignored.", define_unresolved: "Unresolved defines: {names}.", no_connections: "No connections in the file.",
    default_ignored: "DEFAULT {name} ignored.", line_unreadable: "Line unreadable: {line}",
    yaml: "YAML error in line {line}: {message}", admin_present: "The file has an admin section – please remove it, the app adds its own.",
    port_twice: "Port {port} twice: {names}.", port_reserved: "Port {port} is reserved for the app.", legacy_format: "ser2net 4 cannot read the old format (ser2net.conf) – please import it.",
    unreadable: "File unreadable: {error}",
  },
};

// The app checks fields in English; these are its messages in German.
const FIELD_ERRORS_DE = [
  [/^between (\d+) and (\d+)$/, "zwischen $1 und $2"], [/^(\d+) to (\d+) seconds$/, "$1 bis $2 Sekunden"],
  [/^(\d+) to (\d+) minutes$/, "$1 bis $2 Minuten"], [/^(\d+) to (\d+) days$/, "$1 bis $2 Tage"],
  [/^(\d+) to (\d+) characters$/, "$1 bis $2 Zeichen"], [/^(\d+) to (\d+) files$/, "$1 bis $2 Dateien"],
  [/^(\d+) to (\d+) MB$/, "$1 bis $2 MB"], [/^(\d+) to (\d+)$/, "$1 bis $2"], [/^(\d+) or (\d+)$/, "$1 oder $2"],
  [/^a path under \/dev without commas or spaces$/, "ein Pfad unter /dev ohne Kommas und Leerzeichen"],
  [/^an IP address of this host$/, "eine IP-Adresse dieses Rechners"], [/^also used by (.+)$/, "schon verwendet von $1"],
  [/^another connection has this name$/, "eine andere Verbindung heißt schon so"], [/^used by the app's web interface$/, "von der Weboberfläche der App belegt"],
  [/^at least 2 when the device is kept open \(the app uses one\)$/, "mindestens 2, wenn das Gerät offen gehalten wird (die App belegt einen Platz)"],
  [/^'(.+)' is not an option name$/, "„$1“ ist kein Optionsname"], [/^(.+) has its own field$/, "$1 hat ein eigenes Feld"],
  [/^'(.+)' is not an address or network$/, "„$1“ ist keine Adresse und kein Netz"], [/^no address or network given$/, "keine Adresse und kein Netz angegeben"],
  [/^is missing$/, "fehlt"], [/^has the wrong type$/, "hat den falschen Typ"], [/^one of (.+)$/, "eins von: $1"],
  [/^off or <delay before>:<delay after>\[:<conf>\]$/, "off oder <vorher>:<nachher>[:<conf>]"],
];

export function fieldError(message) {
  if (lang !== "de") return message;
  for (const [pattern, text] of FIELD_ERRORS_DE) if (pattern.test(message)) return message.replace(pattern, text);
  return message;
}

const stored = (() => { try { return localStorage.getItem("ser2net.lang"); } catch { return null; } })();
export let lang = stored || ((navigator.language || "en").toLowerCase().startsWith("de") ? "de" : "en");

export function setLang(value) {
  lang = value;
  try { localStorage.setItem("ser2net.lang", value); } catch { /* private window */ }
}

const fill = (text, params = {}) =>
  text.replace(/\{(\w+)\}/g, (m, key) => {
    const value = params[key];
    if (value === undefined) return m;
    if (value === null) return "–";
    return Array.isArray(value) ? value.join(", ") : typeof value === "object" ? JSON.stringify(value) : String(value);
  });

export const t = (key, params) => fill(TEXT[lang][key] ?? TEXT.en[key] ?? key, params);

const STATE_WORDS = { de: { active: "aktiv", disabled: "deaktiviert" }, en: {} };
const CHANGE_WORDS = {
  de: { added: "hinzugefügt", removed: "entfernt", enabled: "aktiviert", disabled: "deaktiviert", settings: "Einstellungen" },
  en: { added: "added", removed: "removed", enabled: "enabled", disabled: "disabled", settings: "settings" },
};

/** The changes of a configuration version in the viewer's language. */
export function changesText(changes) {
  const words = CHANGE_WORDS[lang];
  return (changes || []).map((c) => {
    const who = c.connection || words.settings;
    return c.fields ? `${who}: ${c.fields.join(", ")}` : `${who} ${words[c.change] || c.change}`;
  }).join("; ");
}

export function eventText(event) {
  const template = EVENTS[lang][event.kind];
  if (!template) return event.message;
  const params = { ...event.params };
  if (params.state) params.state = STATE_WORDS[lang][params.state] || params.state;
  if (event.kind === "config_changed" && params.changes) params.summary = changesText(params.changes);
  return fill(template, params);
}

export function noteText(note) {
  const template = NOTES[lang][note.code] || NOTES.en[note.code];
  if (!template) return note.code;
  const params = { ...note };
  if (params.errors && typeof params.errors === "object") {
    params.errors = Object.entries(params.errors).map(([k, v]) => (k ? `${k}: ${v}` : v)).join("; ");
  }
  return fill(template, params);
}
