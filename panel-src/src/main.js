import { Ser2NetApp, Ser2NetConfirm } from "./app.js";
import { ConnectionsPage } from "./pages/connections.js";
import { DetailPage } from "./pages/detail.js";
import { EditPage } from "./pages/edit.js";
import { EventsPage } from "./pages/events.js";
import { ImportPage } from "./pages/import.js";
import { SettingsPage } from "./pages/settings.js";
import { TracePage } from "./pages/trace.js";

const elements = {
  "ser2net-app": Ser2NetApp,
  "s2n-confirm": Ser2NetConfirm,
  "s2n-connections": ConnectionsPage,
  "s2n-detail": DetailPage,
  "s2n-edit": EditPage,
  "s2n-events": EventsPage,
  "s2n-import": ImportPage,
  "s2n-settings": SettingsPage,
  "s2n-trace": TracePage,
};
for (const [name, element] of Object.entries(elements)) {
  if (!customElements.get(name)) customElements.define(name, element);
}
