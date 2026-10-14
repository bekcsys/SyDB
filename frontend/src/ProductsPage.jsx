import { Loading, LoadError, PageHeader, useJson } from "./ui";

function catalogHref({ q, sort, dir, supplier, box, family }) {
  const params = new URLSearchParams();
  if (q) params.set("q", q);
  params.set("sort", sort);
  params.set("dir", dir);
  if (supplier) params.set("supplier", supplier);
  else if (box) params.set("box", box);
  else if (family) params.set("family", family);
  const query = params.toString();
  return query ? `/products/?${query}` : "/products/";
}

function SortLink({ field, label, state }) {
  const next = state.sort === field && state.dir === "asc" ? "desc" : "asc";
  const href = catalogHref({ ...state, sort: field, dir: next });
  const active = state.sort === field ? ` active ${state.dir}` : "";
  return (
    <a className={`sort-link${active}`} href={href}>
      {label}
    </a>
  );
}

function FilterLink({ active, href, children }) {
  return (
    <a className={active ? "chip is-on" : "chip"} href={href}>
      {children}
    </a>
  );
}

function EquipmentLink({ item }) {
  if (!item) return "—";
  if (!item.picture_url) return item.name;
  return (
    <a href={item.picture_url} target="_blank" rel="noopener noreferrer">
      {item.name}
    </a>
  );
}

export function ProductsPage() {
  const state = useJson(`/api/products/${window.location.search}`);
  if (state.status === "loading") return <Loading label="Loading products" />;
  if (state.status === "error") return <LoadError message={state.error} />;
  const data = state.data;
  const filters = { q: data.q, sort: data.sort, dir: data.dir, supplier: "", box: "", family: "" };
  return (
    <div className="page">
      <PageHeader
        eyebrow="Catalog"
        title="Products"
        lede="Models in the catalog, the power box each one uses, and its control panel."
      >
        <p className="count">{data.products.length}</p>
      </PageHeader>
      <div className="toolbar">
        <form className="search" method="get" action="/products/">
          <input type="hidden" name="sort" value={data.sort} />
          <input type="hidden" name="dir" value={data.dir} />
          {data.supplier ? <input type="hidden" name="supplier" value={data.supplier} /> : null}
          {data.box ? <input type="hidden" name="box" value={data.box} /> : null}
          {data.family ? <input type="hidden" name="family" value={data.family} /> : null}
          <input
            type="search"
            name="q"
            defaultValue={data.q}
            placeholder="Product ID, item number, name, or supplier"
            aria-label="Search products"
          />
          <button type="submit">Search</button>
          {data.q ? <a className="text-button" href={catalogHref({ ...filters, supplier: data.supplier, box: data.box, family: data.family, q: "" })}>Clear</a> : null}
        </form>
        <div className="chip-row" role="group" aria-label="Product filters">
          <FilterLink active={!data.supplier && !data.box && !data.family} href={catalogHref(filters)}>
            All
          </FilterLink>
          {data.filters.suppliers.map((item) => (
            <FilterLink
              key={item.key}
              active={data.supplier === item.key}
              href={catalogHref({ ...filters, supplier: data.supplier === item.key ? "" : item.key })}
            >
              {item.label}
            </FilterLink>
          ))}
          {data.filters.boxes.map((item) => (
            <FilterLink
              key={item.key}
              active={data.box === item.key}
              href={catalogHref({ ...filters, box: data.box === item.key ? "" : item.key })}
            >
              {item.label}
            </FilterLink>
          ))}
          {data.filters.families.map((item) => (
            <FilterLink
              key={item.key}
              active={data.family === item.key}
              href={catalogHref({ ...filters, family: data.family === item.key ? "" : item.key })}
            >
              {item.label}
            </FilterLink>
          ))}
        </div>
      </div>
      <div className="table-wrap">
        <table className="data-table">
          <thead>
            <tr>
              <th><SortLink field="id" label="Product ID" state={data} /></th>
              <th><SortLink field="supplier" label="Sup" state={data} /></th>
              <th><SortLink field="known_issues" label="Known Issues" state={data} /></th>
              <th><SortLink field="item_no" label="Item No" state={data} /></th>
              <th><SortLink field="product" label="Product name" state={data} /></th>
              <th><SortLink field="power_box" label="Power box" state={data} /></th>
              <th>Control Panel</th>
            </tr>
          </thead>
          <tbody>
            {data.products.length ? data.products.map((product) => (
              <tr key={product.id}>
                <td className="num">{product.id}</td>
                <td><span className={`mark mark-${product.supplier_label}`}>{product.supplier_label}</span></td>
                <td>
                  <a
                    className={product.known_issues ? "issue-badge" : "issue-badge is-zero"}
                    href={`/products/${product.id}/#product-issues`}
                  >
                    {product.known_issues}
                  </a>
                </td>
                <td>{product.item_no}</td>
                <td className="wrap">
                  <a className="name-link" href={`/products/${product.id}/`}>{product.name}</a>
                </td>
                <td><EquipmentLink item={product.power_box} /></td>
                <td><EquipmentLink item={product.control_panel} /></td>
              </tr>
            )) : (
              <tr>
                <td className="empty" colSpan={7}>No products found.</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
