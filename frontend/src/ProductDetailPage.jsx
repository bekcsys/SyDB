import { useEffect, useState } from "react";
import { Loading, LoadError, StatusPill, useJson } from "./ui";

function display(value, suffix = "") {
  if (value === null || value === undefined || value === "") return "—";
  const shown = typeof value === "number" ? value.toLocaleString("en-US") : value;
  return `${shown}${suffix}`;
}

function formatDate(iso) {
  const [year, month, day] = iso.split("-");
  return `${Number(month)}/${Number(day)}/${year}`;
}

function FileList({ files }) {
  if (!files.length) return <p className="quiet">None</p>;
  return (
    <ul className="qc-support-file-list">
      {files.map((file) => (
        <li key={file.url}>
          <a href={file.url} target="_blank" rel="noopener noreferrer">
            <span>{file.name}</span>
            <span className="file-kind">{/\.(mp4|m4v|mov|webm)$/i.test(file.name) ? "Video" : "File"}</span>
          </a>
        </li>
      ))}
    </ul>
  );
}

function PictureStage({ pictures, wide }) {
  if (!pictures.length) return <div className="photo-empty">None</div>;
  return (
    <div className="qc-support-photos">
      {pictures.map((file) => (
        <a key={file.url} href={file.url} target="_blank" rel="noopener noreferrer">
          <img
            className={wide ? "qc-support-photo qc-support-photo-wide" : "qc-support-photo"}
            src={file.url}
            alt={file.name}
          />
        </a>
      ))}
    </div>
  );
}

function AccordionSection({ id, title, count, open, onToggle, children }) {
  return (
    <section id={id} className={open ? "fold is-open" : "fold"}>
      <button type="button" className="fold-toggle" aria-expanded={open} onClick={onToggle}>
        <span className="fold-title">{title}</span>
        {count ? <span className="group-count">{count}</span> : null}
        <span className="chevron" aria-hidden="true" />
      </button>
      {open ? <div className="fold-body">{children}</div> : null}
    </section>
  );
}

function IssueTable({ issues }) {
  if (!issues.length) return <p className="empty-block">No issues recorded for this product.</p>;
  return (
    <div className="table-wrap">
      <table className="data-table">
        <thead>
          <tr>
            <th>Date</th>
            <th>Note</th>
            <th>Status</th>
            <th>Documentation</th>
          </tr>
        </thead>
        <tbody>
          {issues.map((issue) => (
            <tr key={issue.id}>
              <td>{formatDate(issue.date)}</td>
              <td className="wrap">{issue.note || "—"}</td>
              <td><StatusPill status={issue.status} label={issue.status_label} /></td>
              <td>
                {issue.documentation_url ? (
                  <a href={issue.documentation_url} target="_blank" rel="noopener noreferrer">View</a>
                ) : "—"}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function ProductDetailPage({ id }) {
  const state = useJson(`/api/products/${id}/`);
  const [open, setOpen] = useState(() => {
    const initial = new Set(["spec"]);
    if (window.location.hash === "#product-issues") initial.add("issues");
    return initial;
  });
  useEffect(() => {
    if (state.status !== "ready" || window.location.hash !== "#product-issues") return;
    document.getElementById("product-issues")?.scrollIntoView({ block: "start" });
  }, [state.status]);

  function toggle(key) {
    setOpen((current) => {
      const next = new Set(current);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
  }

  if (state.status === "loading") return <Loading label="Loading product" />;
  if (state.status === "error") return <LoadError message={state.error} />;
  const product = state.data;
  const panelPictures = product.panels.flatMap((panel) => panel.pictures);
  const boxPictures = product.boxes.flatMap((box) => box.pictures);
  const instructionCount = product.panel_instructions.length + product.firmware_updates.length;
  const issueCount = product.issues.length;

  return (
    <article className="page dossier">
      <a className="back" href="/products/">Products</a>
      <header className="dossier-top">
        <div>
          <p className="eyebrow">Item no. {product.item_no}</p>
          <h1>{product.name}</h1>
          <p className="lede">
            <span className={`mark mark-${product.supplier_label}`}>{product.supplier_label}</span>
            {product.supplier}
            <span className="dot">{product.unit_count} units</span>
          </p>
        </div>
      </header>
      <div className="fold-list">
        <AccordionSection id="product-spec" title="SPEC" open={open.has("spec")} onToggle={() => toggle("spec")}>
          <section className="spec-sheet" aria-label="Specifications">
            <dl>
              <div><dt>Voltage</dt><dd>{display(product.voltage, " V")}</dd></div>
              <div><dt>Plug type</dt><dd>{display(product.plug_type)}</dd></div>
              <div><dt>Wattage</dt><dd>{display(product.wattage, " W")}</dd></div>
              <div><dt>Watt on label</dt><dd>{display(product.watt_on_label, " W")}</dd></div>
              <div><dt>Number of cords</dt><dd>{product.cords}</dd></div>
              <div><dt>Supplier</dt><dd>{product.supplier}</dd></div>
              <div><dt>Power box type</dt><dd>{display(product.power_box)}</dd></div>
              <div><dt>Control panel type</dt><dd>{display(product.control_panel)}</dd></div>
            </dl>
          </section>
          <figure className="fold-photo">
            <PictureStage pictures={boxPictures} />
            <figcaption>
              <h2>Power box picture</h2>
              <p>{display(product.power_box)}</p>
            </figcaption>
          </figure>
        </AccordionSection>
        <AccordionSection
          id="product-instructions"
          title="INSTRUCTIONS"
          count={instructionCount ? String(instructionCount) : ""}
          open={open.has("instructions")}
          onToggle={() => toggle("instructions")}
        >
          <div className="docs-sheet doc-card">
            <div className="docs-group">
              <h2>Control panel instruction</h2>
              <FileList files={product.panel_instructions} />
            </div>
            <div className="docs-group">
              <h2>Firmware instruction</h2>
              <FileList files={product.firmware_updates} />
            </div>
          </div>
        </AccordionSection>
        <AccordionSection
          id="product-panels"
          title="CONTROL PANELS"
          count={String(product.panel_rows.length)}
          open={open.has("panels")}
          onToggle={() => toggle("panels")}
        >
          {product.panel_rows.length ? (
            <div className="table-wrap">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Name</th>
                    <th>Part number</th>
                    <th>Firmware device</th>
                  </tr>
                </thead>
                <tbody>
                  {product.panel_rows.map((panel) => (
                    <tr key={panel.name}>
                      <td>
                        {panel.picture_url ? (
                          <a href={panel.picture_url} target="_blank" rel="noopener noreferrer">{panel.name}</a>
                        ) : panel.name}
                      </td>
                      <td>{panel.part_number}</td>
                      <td>{panel.firmware_device}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : <p className="empty-block">None</p>}
          <figure className="fold-photo">
            <PictureStage pictures={panelPictures} wide />
            <figcaption>
              <h2>Control panel picture</h2>
              <p>{display(product.control_panel)}</p>
            </figcaption>
          </figure>
        </AccordionSection>
        <AccordionSection
          id="product-items"
          title="PRODUCT ITEMS"
          count={`${product.units.length} Units`}
          open={open.has("items")}
          onToggle={() => toggle("items")}
        >
          {product.units.length ? (
            <div className="table-wrap">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>S/N</th>
                    <th>Product</th>
                    <th>Item No.</th>
                    <th>QC Form</th>
                    <th>QC Status</th>
                    <th>Notes</th>
                  </tr>
                </thead>
                <tbody>
                  {product.units.map((unit) => (
                    <tr key={unit.id}>
                      <td><a className="name-link" href={unit.url}>{unit.serial_no}</a></td>
                      <td>{unit.product_name}</td>
                      <td>{unit.item_no}</td>
                      <td>
                        {unit.qc_form_url ? (
                          <a href={unit.qc_form_url} target="_blank" rel="noopener noreferrer">{unit.qc_form_name}</a>
                        ) : "—"}
                      </td>
                      <td><StatusPill status={unit.qc_status} label={unit.qc_status_label} /></td>
                      <td className="wrap">{unit.note || "—"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : <p className="empty-block">No units associated with this product.</p>}
        </AccordionSection>
        <AccordionSection
          id="product-issues"
          title="KNOWN ISSUES"
          count={`${issueCount}`}
          open={open.has("issues")}
          onToggle={() => toggle("issues")}
        >
          <IssueTable issues={product.issues} />
        </AccordionSection>
      </div>
    </article>
  );
}
