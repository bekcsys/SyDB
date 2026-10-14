import { Loading, LoadError, PageHeader, StatusPill, useJson } from "./ui";

function listHref({ q, sort, dir, pick }) {
  const params = new URLSearchParams();
  if (q) params.set("q", q);
  params.set("sort", sort);
  params.set("dir", dir);
  if (pick) params.set("pick", pick);
  const query = params.toString();
  const path = window.location.pathname.endsWith("/") ? window.location.pathname : `${window.location.pathname}/`;
  return query ? `${path}?${query}` : path;
}

function SortLink({ field, label, state }) {
  const next = state.sort === field && state.dir === "asc" ? "desc" : "asc";
  const href = listHref({ q: state.q, sort: field, dir: next, pick: state.pick });
  const active = state.sort === field ? ` active ${state.dir}` : "";
  return <a className={`sort-link${active}`} href={href}>{label}</a>;
}

export function UnitsPage() {
  const state = useJson(`/api/units/${window.location.search}`);
  if (state.status === "loading") return <Loading label="Loading QC records" />;
  if (state.status === "error") return <LoadError message={state.error} />;
  const data = state.data;
  return (
    <div className="page">
      <PageHeader
        eyebrow="Inspection"
        title="QC & CS"
        lede="Serial numbers, who tested them, and the current inspection status."
      >
        <p className="count">{data.units.length}</p>
      </PageHeader>
      <div className="toolbar">
        <form className="search" method="get" action={window.location.pathname}>
          <input type="hidden" name="sort" value={data.sort} />
          <input type="hidden" name="dir" value={data.dir} />
          {data.pick ? <input type="hidden" name="pick" value={data.pick} /> : null}
          <input
            type="search"
            name="q"
            defaultValue={data.q}
            placeholder="Serial, product, tester, status, or note"
            aria-label="Search product items"
          />
          <button type="submit">Search</button>
          {data.q ? <a className="text-button" href={listHref({ q: "", sort: data.sort, dir: data.dir, pick: data.pick })}>Clear</a> : null}
        </form>
        <div className="chip-row" role="group" aria-label="QC tracker filters">
          {data.filters.map((item) => (
            <a
              key={item.key}
              className={data.pick === item.key ? "chip is-on" : "chip"}
              href={listHref({ q: data.q, sort: data.sort, dir: data.dir, pick: data.pick === item.key ? "" : item.key })}
            >
              {item.label}
            </a>
          ))}
        </div>
      </div>
      <div className="table-wrap">
        <table className="data-table">
          <thead>
            <tr>
              <th><SortLink field="serial" label="Serial no" state={data} /></th>
              <th>Product</th>
              <th><SortLink field="qc_person" label="QC tester name" state={data} /></th>
              <th><SortLink field="qc_status" label="QC status" state={data} /></th>
              <th><SortLink field="note" label="Note" state={data} /></th>
              <th>QC form</th>
              <th />
            </tr>
          </thead>
          <tbody>
            {data.units.length ? data.units.map((unit) => (
              <tr key={unit.id}>
                <td><a href={`/units/${unit.id}/`}>{unit.serial_no}</a></td>
                <td className="wrap">{unit.product_name || "—"}</td>
                <td>{unit.qc_tester_name || "—"}</td>
                <td><StatusPill status={unit.qc_status} label={unit.qc_status_label} /></td>
                <td className="wrap note-cell">{unit.note || "—"}</td>
                <td>
                  {unit.qc_form_url ? (
                    <a href={unit.qc_form_url} target="_blank" rel="noopener noreferrer">{unit.qc_form_name}</a>
                  ) : "—"}
                </td>
                <td>
                  <a className="text-button" href={`/units/${unit.id}/`}>Edit</a>
                </td>
              </tr>
            )) : (
              <tr>
                <td className="empty" colSpan={7}>No product items found.</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
