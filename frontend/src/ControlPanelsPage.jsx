import { useState } from "react";
import { Loading, LoadError, PageHeader, useJson } from "./ui";

const SUPPLIERS = ["Global", "Royal", "SmartMak", "Li", "Luis", "Wang"];

function InstructionLine({ files, children }) {
  const file = files[0];
  return (
    <p className="meta-line">
      <span>{children}</span>
      {file ? (
        <a href={file.url} target="_blank" rel="noopener noreferrer">{file.name}</a>
      ) : "(None)"}
    </p>
  );
}

function matchesSupplier(panel, supplier) {
  const names = [panel.name, ...(panel.power_boxes || [])].join(" ").toLowerCase();
  if (supplier === "Luis") return names.includes("luis");
  if (supplier === "Wang") return names.includes("wang");
  if (supplier === "Li") return /(^|[^a-z0-9])li([^a-z0-9]|$)/.test(names);
  const wanted = supplier.toLowerCase();
  return (panel.suppliers || []).some((name) => name.toLowerCase() === wanted);
}

export function ControlPanelsPage() {
  const state = useJson("/api/control-panels/");
  const [supplier, setSupplier] = useState("");
  if (state.status === "loading") return <Loading label="Loading control panels" />;
  if (state.status === "error") return <LoadError message={state.error} />;
  const panels = state.data.control_panels.filter((panel) => !supplier || matchesSupplier(panel, supplier));
  return (
    <div className="page">
      <PageHeader
        eyebrow="Hardware"
        title="Control panels"
        lede="Picture, firmware device, both instruction files, and the power boxes that use each panel."
      >
        <p className="count">{panels.length}</p>
      </PageHeader>
      <div className="chip-row filters" role="group" aria-label="Suppliers">
        <button type="button" className={supplier ? "chip" : "chip is-on"} onClick={() => setSupplier("")}>All</button>
        {SUPPLIERS.map((name) => (
          <button
            key={name}
            type="button"
            className={supplier === name ? "chip is-on" : "chip"}
            onClick={() => setSupplier(supplier === name ? "" : name)}
          >
            {name}
          </button>
        ))}
      </div>
      {panels.length ? (
        <div className="panel-grid">
          {panels.map((panel) => {
            const picture = panel.picture[0];
            const boxes = panel.power_boxes || [];
            return (
              <article className="plate" key={panel.name}>
                <div className="plate-visual">
                  {picture ? (
                    <a className="plate-stage" href={picture.url} target="_blank" rel="noopener noreferrer">
                      <img src={picture.url} alt={picture.name} />
                    </a>
                  ) : <div className="photo-empty">No picture on file</div>}
                </div>
                <div className="plate-body">
                  <h2>
                    {picture ? (
                      <a href={picture.url} target="_blank" rel="noopener noreferrer">{panel.name}</a>
                    ) : panel.name}
                  </h2>
                  <p className="meta-line"><span className="with-colon">Firmware device</span> {panel.firmware_device_display}</p>
                  <InstructionLine files={panel.documentation_1}>Firmware instruction</InstructionLine>
                  <InstructionLine files={panel.documentation_2}>CP instruction</InstructionLine>
                  <div>
                    <span className="kicker">Applicable power boxes</span>
                    {boxes.length ? (
                      <div className="chip-row tight">
                        {boxes.map((name) => (
                          <span className="product-chip" key={name}>{name}</span>
                        ))}
                      </div>
                    ) : <p className="plain">—</p>}
                  </div>
                </div>
              </article>
            );
          })}
        </div>
      ) : <p className="empty-block">No control panels found.</p>}
    </div>
  );
}
