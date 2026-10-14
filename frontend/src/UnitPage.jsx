import { useEffect, useState } from "react";
import { csrfToken, Loading, LoadError, StatusPill, useJson } from "./ui";

async function postForm(url, fields) {
  const body = new FormData();
  body.append("csrfmiddlewaretoken", csrfToken());
  Object.entries(fields).forEach(([key, value]) => {
    if (value !== undefined && value !== null) body.append(key, value);
  });
  const response = await fetch(url, {
    method: "POST",
    headers: { "X-CSRFToken": csrfToken(), Accept: "application/json" },
    body,
  });
  const payload = await response.json();
  if (!response.ok) throw new Error((payload.errors || ["The change could not be saved."]).join(" "));
  return payload;
}

export function UnitPage({ id, editable }) {
  const state = useJson(`/api/units/${id}/`);
  const [form, setForm] = useState(null);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (state.status !== "ready") return;
    const unit = state.data;
    setForm({
      product: unit.product_id ? String(unit.product_id) : "",
      qc_tester_name: unit.qc_tester_name,
      qc_status: unit.qc_status,
      note: unit.note,
      qc_form_name: unit.qc_form_name,
      qc_form_url: unit.qc_form_url,
    });
  }, [state]);

  if (state.status === "error") return <LoadError message={state.error} />;
  if (state.status !== "ready" || !form) return <Loading label="Loading serial" />;
  const unit = state.data;
  const status = unit.statuses.find((item) => item.value === form.qc_status);

  async function onSave(event) {
    event.preventDefault();
    setBusy(true);
    setError("");
    setMessage("");
    try {
      const payload = await postForm(`/api/units/${id}/`, {
        product: form.product,
        qc_tester_name: form.qc_tester_name,
        qc_status: form.qc_status,
        note: form.note,
      });
      setForm((current) => ({
        ...current,
        qc_tester_name: payload.unit.qc_tester_name,
        qc_status: payload.unit.qc_status,
        note: payload.unit.note,
        product: payload.unit.product_id ? String(payload.unit.product_id) : "",
      }));
      setMessage("Saved.");
    } catch (saveError) {
      setError(saveError.message);
    } finally {
      setBusy(false);
    }
  }

  async function onUpload(event) {
    const file = event.target.files?.[0];
    event.target.value = "";
    if (!file) return;
    setBusy(true);
    setError("");
    setMessage("");
    try {
      const payload = await postForm(`/api/units/${id}/form/`, { qc_form: file });
      setForm((current) => ({
        ...current,
        qc_form_name: payload.qc_form_name,
        qc_form_url: payload.qc_form_url,
      }));
      setMessage("QC form uploaded.");
    } catch (uploadError) {
      setError(uploadError.message);
    } finally {
      setBusy(false);
    }
  }

  async function onDeleteForm() {
    setBusy(true);
    setError("");
    setMessage("");
    try {
      const payload = await postForm(`/api/units/${id}/form/`, { action: "delete_form" });
      setForm((current) => ({
        ...current,
        qc_form_name: payload.qc_form_name,
        qc_form_url: payload.qc_form_url,
      }));
      setMessage("QC form removed.");
    } catch (deleteError) {
      setError(deleteError.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <article className="page">
      <a className="back" href="/">Back to QC &amp; CS</a>
      <header className="dossier-top">
        <div>
          <p className="eyebrow">Serial</p>
          <h1>{unit.serial_no}</h1>
          <p className="lede">{unit.product_name || "No product assigned"}</p>
        </div>
        <StatusPill status={form.qc_status} label={status ? status.label : form.qc_status} />
      </header>
      {editable ? null : <p className="view-note">View only. Customer Service cannot change QC records.</p>}
      {message ? <p className="banner banner-ok">{message}</p> : null}
      {error ? <p className="banner banner-error" role="alert">{error}</p> : null}
      <div className="editor-grid">
        <section className="form-card">
          <h2>QC record</h2>
          {editable ? (
            <form onSubmit={onSave}>
              <label className="field">
                <span>Product</span>
                <select
                  value={form.product}
                  aria-label="Product"
                  onChange={(event) => setForm({ ...form, product: event.target.value })}
                >
                  <option value="">—</option>
                  {unit.products.map((product) => (
                    <option key={product.id} value={product.id}>{product.name} · {product.item_no}</option>
                  ))}
                </select>
              </label>
              <label className="field">
                <span>QC tester name</span>
                <input
                  value={form.qc_tester_name}
                  aria-label="QC tester name"
                  onChange={(event) => setForm({ ...form, qc_tester_name: event.target.value })}
                />
              </label>
              <label className="field">
                <span>QC status</span>
                <select
                  value={form.qc_status}
                  aria-label="QC status"
                  onChange={(event) => setForm({ ...form, qc_status: event.target.value })}
                >
                  {unit.statuses.map((item) => (
                    <option key={item.value} value={item.value}>{item.label}</option>
                  ))}
                </select>
              </label>
              <label className="field">
                <span>Note</span>
                <textarea
                  rows={4}
                  value={form.note}
                  aria-label="Note"
                  placeholder="QC note"
                  onChange={(event) => setForm({ ...form, note: event.target.value })}
                />
              </label>
              <button className="button" type="submit" disabled={busy}>Save</button>
            </form>
          ) : (
            <dl className="readout">
              <div><dt>Product</dt><dd>{unit.product_name || "—"}</dd></div>
              <div><dt>QC tester name</dt><dd>{unit.qc_tester_name || "—"}</dd></div>
              <div><dt>QC status</dt><dd>{status ? status.label : form.qc_status}</dd></div>
              <div><dt>Note</dt><dd>{unit.note || "—"}</dd></div>
            </dl>
          )}
        </section>
        <section className="form-card">
          <h2>QC form</h2>
          {form.qc_form_url ? (
            <p><a href={form.qc_form_url} target="_blank" rel="noopener noreferrer">{form.qc_form_name}</a></p>
          ) : <p className="quiet">—</p>}
          {editable ? (
            <div className="form-actions">
              <label className="button file-button">
                Upload PDF
                <input type="file" accept="application/pdf,.pdf" aria-label="QC form" onChange={onUpload} disabled={busy} />
              </label>
              {form.qc_form_url ? (
                <button className="button button-quiet" type="button" onClick={onDeleteForm} disabled={busy}>Remove form</button>
              ) : null}
            </div>
          ) : null}
        </section>
      </div>
    </article>
  );
}
