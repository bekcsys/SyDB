import { useState } from "react";

import { Loading, LoadError, PageHeader, StatusPill, useJson } from "./ui";

function formatDate(iso) {
  const [year, month, day] = iso.split("-");
  return `${Number(month)}/${Number(day)}/${year}`;
}

function unitHref(id) {
  const base = window.location.pathname.startsWith("/customer-service") ? "/customer-service" : "/units";
  return `${base}/${id}/`;
}

function CollapsibleBlock({ title, children }) {
  const [open, setOpen] = useState(false);
  return (
    <section className={open ? "qc-block is-open" : "qc-block"}>
      <button type="button" className="qc-block-title" aria-expanded={open} onClick={() => setOpen((value) => !value)}>
        <span>{title}</span>
        <span className="chevron" aria-hidden="true" />
      </button>
      {open ? <div className="form-card known-issues">{children}</div> : null}
    </section>
  );
}

export function UnitsPage() {
  const state = useJson("/api/units/");
  if (state.status === "loading") return <Loading label="Loading QC records" />;
  if (state.status === "error") return <LoadError message={state.error} />;
  const data = state.data;
  const issues = data.issues || [];
  return (
    <div className="page">
      <PageHeader
        eyebrow="Inspection"
        title="QC & CS"
        lede="Common product issues, then the serial numbers and inspection records."
      >
        <p className="count">{data.units.length}</p>
      </PageHeader>
      <CollapsibleBlock title="Common product issues and solutions">
        <div className="table-wrap">
          <table className="data-table">
            <thead>
              <tr>
                <th>Impacted products</th>
                <th>Problem description</th>
                <th>Affected products</th>
                <th>Status</th>
                <th>Documentation</th>
                <th>Support</th>
                <th>Date</th>
              </tr>
            </thead>
            <tbody>
              {issues.length ? issues.map((issue) => (
                <tr key={issue.id}>
                  <td className="num">{issue.impacted_products}</td>
                  <td className="wrap">{issue.note || "—"}</td>
                  <td className="wrap">
                    {issue.products.length ? issue.products.map((product, index) => (
                      <span key={product.id}>
                        {index ? ", " : ""}
                        <a href={`/products/${product.id}/#product-issues`}>{product.name}</a>
                      </span>
                    )) : "—"}
                  </td>
                  <td><StatusPill status={issue.status} label={issue.status_label} /></td>
                  <td>
                    {issue.documentation_url ? (
                      <a href={issue.documentation_url} target="_blank" rel="noopener noreferrer">View</a>
                    ) : "—"}
                  </td>
                  <td>
                    {issue.support_doc_url ? (
                      <a href={issue.support_doc_url} target="_blank" rel="noopener noreferrer">View</a>
                    ) : "—"}
                  </td>
                  <td>{formatDate(issue.date)}</td>
                </tr>
              )) : (
                <tr>
                  <td className="empty" colSpan={7}>No issues recorded.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </CollapsibleBlock>
      <CollapsibleBlock title="QC info">
        <div className="table-wrap">
          <table className="data-table">
            <thead>
              <tr>
                <th>Serial No</th>
                <th>Product name</th>
                <th>QC tester</th>
                <th>QC note</th>
                <th>QC form</th>
              </tr>
            </thead>
            <tbody>
              {data.units.length ? data.units.map((unit) => (
                <tr key={unit.id}>
                  <td><a href={unitHref(unit.id)}>{unit.serial_no}</a></td>
                  <td className="wrap">{unit.product_name || "—"}</td>
                  <td>{unit.qc_tester_name || "—"}</td>
                  <td className="wrap note-cell">{unit.note || "—"}</td>
                  <td>
                    {unit.qc_form_url ? (
                      <a href={unit.qc_form_url} target="_blank" rel="noopener noreferrer">{unit.qc_form_name}</a>
                    ) : "—"}
                  </td>
                </tr>
              )) : (
                <tr>
                  <td className="empty" colSpan={5}>No product items found.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </CollapsibleBlock>
    </div>
  );
}
