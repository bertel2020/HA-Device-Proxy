import { DeviceProxyApp, DeviceProxyConfirm } from "./app.js";
import { EnOceanGateways, EnOceanTools } from "./enocean.js";
import { ConnectionsPage } from "./pages/connections.js";
import { DetailPage } from "./pages/detail.js";
import { EditPage } from "./pages/edit.js";
import { EventsPage } from "./pages/events.js";
import { ImportDialog } from "./pages/import.js";
import { SettingsPage } from "./pages/settings.js";
import { TracePage } from "./pages/trace.js";

const elements = {
  "device-proxy": DeviceProxyApp,
  "dp-confirm": DeviceProxyConfirm,
  "dp-connections": ConnectionsPage,
  "dp-detail": DetailPage,
  "dp-edit": EditPage,
  "dp-enocean-tools": EnOceanTools,
  "dp-eo-gateways": EnOceanGateways,
  "dp-events": EventsPage,
  "dp-import": ImportDialog,
  "dp-settings": SettingsPage,
  "dp-trace": TracePage,
};
for (const [name, element] of Object.entries(elements)) {
  if (!customElements.get(name)) customElements.define(name, element);
}
