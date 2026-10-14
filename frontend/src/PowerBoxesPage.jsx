import { useEffect, useMemo, useRef, useState } from "react";
import { DocIcon, Loading, LoadError, PageHeader, useJson, VideoIcon } from "./ui";

const FAMILY_ORDER = ["Luis", "Li", "Wang", "Royal", "SmartMak", "Other"];

function familyOf(name) {
  const value = name.toLowerCase();
  if (value.includes("luis")) return "Luis";
  if (value.includes("wang")) return "Wang";
  if (/(^|[^a-z0-9])li([^a-z0-9]|$)/.test(value)) return "Li";
  if (value.includes("smmak") || value.includes("smartmak")) return "SmartMak";
  if (value.includes("royal")) return "Royal";
  return "Other";
}

function matches(box, query) {
  if (!query) return true;
  const haystack = [
    box.name,
    box.part_number,
    box.control_panel,
    box.firmware_info,
    ...box.pictures.map((file) => file.name),
    ...box.firmware_files.map((file) => file.name),
    ...box.products.map((product) => product.name),
  ].join(" ").toLowerCase();
  return haystack.includes(query);
}

function PictureStage({ pictures, onOpen }) {
  const hero = pictures[0];
  if (!hero) return <div className="photo-empty">No picture on file</div>;
  return (
    <button type="button" className="plate-stage" onClick={() => onOpen(hero)}>
      <img src={hero.url} alt={hero.name} />
    </button>
  );
}

function PowerBoxCard({ box, onOpen }) {
  return (
    <article className="plate">
      <div className="plate-visual">
        <PictureStage pictures={box.pictures} onOpen={onOpen} />
      </div>
      <div className="plate-body">
        <h2>
          {box.pictures[0] ? (
            <a href={box.pictures[0].url} target="_blank" rel="noopener noreferrer">{box.name}</a>
          ) : box.name}
        </h2>
        <p className="meta-line"><span>P/N:</span> {box.part_number_display}</p>
        <div className="firmware-line">
          <p className="meta-line"><span>Firmware:</span> {box.firmware_display}</p>
          <span className="icon-row">
            {box.firmware_files.map((file) => (
              <a
                className="icon-btn"
                key={file.url}
                href={file.url}
                target="_blank"
                rel="noopener noreferrer"
                aria-label={file.name}
                title={file.name}
              >
                {file.video ? <VideoIcon /> : <DocIcon />}
              </a>
            ))}
          </span>
        </div>
        <div>
          <span className="kicker">Applicable products</span>
          {box.products.length ? (
            <div className="chip-row tight">
              {box.products.map((product) => (
                <a className="product-chip" key={product.url} href={product.url}>{product.name}</a>
              ))}
            </div>
          ) : <p className="plain">—</p>}
        </div>
      </div>
    </article>
  );
}

function Lightbox({ photo, onClose }) {
  const ref = useRef(null);
  useEffect(() => {
    const dialog = ref.current;
    if (!dialog) return undefined;
    dialog.showModal();
    const onCancel = (event) => {
      event.preventDefault();
      onClose();
    };
    dialog.addEventListener("cancel", onCancel);
    return () => {
      dialog.removeEventListener("cancel", onCancel);
      if (dialog.open) dialog.close();
    };
  }, [onClose]);
  return (
    <dialog
      ref={ref}
      className="lightbox"
      onClick={(event) => {
        if (event.target === ref.current) onClose();
      }}
    >
      <div className="lightbox-card">
        <img src={photo.url} alt={photo.name} />
        <div className="lightbox-bar">
          <p>{photo.name}</p>
          <a href={photo.url} target="_blank" rel="noopener noreferrer">Open file</a>
          <button type="button" onClick={onClose}>Close</button>
        </div>
      </div>
    </dialog>
  );
}

export function PowerBoxesPage() {
  const state = useJson("/api/power-boxes/");
  const [query, setQuery] = useState("");
  const [open, setOpen] = useState("");
  const [photo, setPhoto] = useState(null);
  const needle = query.trim().toLowerCase();
  const grouped = useMemo(() => {
    if (state.status !== "ready") return [];
    const buckets = new Map();
    for (const box of state.data.power_boxes) {
      if (!matches(box, needle)) continue;
      const key = familyOf(box.name);
      if (!buckets.has(key)) buckets.set(key, []);
      buckets.get(key).push(box);
    }
    return FAMILY_ORDER.filter((key) => buckets.has(key)).map((key) => ({ key, boxes: buckets.get(key) }));
  }, [state, needle]);

  if (state.status === "loading") return <Loading label="Loading power boxes" />;
  if (state.status === "error") return <LoadError message={state.error} />;

  const shown = grouped.reduce((total, group) => total + group.boxes.length, 0);

  return (
    <div className="page">
      <PageHeader
        eyebrow="Hardware"
        title="Power boxes"
        lede="Open one family at a time. Each plate shows the part number, firmware, and the products that use it."
      >
        <p className="count">{shown}</p>
      </PageHeader>
      <form className="search solo" onSubmit={(event) => event.preventDefault()}>
        <input
          type="search"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="Search name, part, firmware, or product"
          aria-label="Search power boxes"
        />
      </form>
      {shown ? (
        <div className="family-list">
          {grouped.map((group) => {
            const isOpen = open === group.key;
            return (
              <section className={isOpen ? "family is-open" : "family"} key={group.key}>
                <button
                  type="button"
                  className="family-toggle"
                  aria-expanded={isOpen}
                  onClick={() => setOpen(isOpen ? "" : group.key)}
                >
                  <span className="family-name">{group.key}</span>
                  <span className="family-meta">
                    <span className="group-count">{group.boxes.length}</span>
                    <span className="chevron" aria-hidden="true" />
                  </span>
                </button>
                {isOpen ? (
                  <div className="plate-grid">
                    {group.boxes.map((box) => (
                      <PowerBoxCard key={box.name} box={box} onOpen={setPhoto} />
                    ))}
                  </div>
                ) : null}
              </section>
            );
          })}
        </div>
      ) : <p className="empty-block">No power boxes found.</p>}
      {photo ? <Lightbox photo={photo} onClose={() => setPhoto(null)} /> : null}
    </div>
  );
}
