import { ControlPanelsPage } from "./ControlPanelsPage";
import { FirmwarePage } from "./FirmwarePage";
import { PowerBoxesPage } from "./PowerBoxesPage";
import { ProductDetailPage } from "./ProductDetailPage";
import { ProductsPage } from "./ProductsPage";
import { UnitPage } from "./UnitPage";
import { UnitsPage } from "./UnitsPage";

export function App() {
  const path = window.location.pathname;
  if (path === "/" || path === "/units" || path === "/units/" || path === "/customer-service" || path === "/customer-service/") {
    return <UnitsPage />;
  }
  const unit = path.match(/^\/units\/(\d+)\/?$/);
  if (unit) return <UnitPage id={unit[1]} editable />;
  const service = path.match(/^\/customer-service\/(\d+)\/?$/);
  if (service) return <UnitPage id={service[1]} editable={false} />;
  if (path === "/products" || path === "/products/") return <ProductsPage />;
  const product = path.match(/^\/products\/(\d+)\/?$/);
  if (product) return <ProductDetailPage id={product[1]} />;
  if (path.startsWith("/power-boxes")) return <PowerBoxesPage />;
  if (path.startsWith("/control-panels")) return <ControlPanelsPage />;
  if (path.startsWith("/firmware-instructions")) return <FirmwarePage />;
  return <ProductsPage />;
}
