import { useState } from "react";
import { DocIcon, Loading, LoadError, PageHeader, useJson, VideoIcon } from "./ui";

function FileChip({ file, label, icon }) {
  if (!file) {
    return (
      <span className="doc-chip is-empty">
        {icon}
        <span><em>{label}</em>(None)</span>
      </span>
    );
  }
  return (
    <a className="doc-chip" href={file.url} target="_blank" rel="noopener noreferrer">
      {icon}
      <span><em>{label}</em>{file.name}</span>
    </a>
  );
}

export function FirmwarePage() {
  const state = useJson("/api/firmware-instructions/");
  const [query, setQuery] = useState("");
  if (state.status === "loading") return <Loading label="Loading firmware instructions" />;
  if (state.status === "error") return <LoadError message={state.error} />;
  const needle = query.trim().toLowerCase();
  const rows = state.data.firmware_instructions.filter((row) => {
    if (!needle) return true;
    return [row.name, row.target.name, row.document_name, row.video_name].join(" ").toLowerCase().includes(needle);
  });
  return (
    <div className="page">
      <PageHeader
        eyebrow="Instructions"
        title="Firmware instructions"
        lede="Each picture is the device. The video and instruction document sit under it."
      >
        <p className="count">{rows.length}</p>
      </PageHeader>
      <form className="search solo" onSubmit={(event) => event.preventDefault()}>
        <input
          type="search"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="Search firmware"
          aria-label="Search firmware instructions"
        />
      </form>
      {rows.length ? (
        <div className="fw-grid">
          {rows.map((row) => (
            <article className="fw-card" key={`${row.name}-${row.target.name}`}>
              {row.target.url ? (
                <a className="fw-photo" href={row.target.url} target="_blank" rel="noopener noreferrer">
                  <img src={row.target.url} alt={row.target.name} />
                </a>
              ) : <div className="fw-photo" aria-hidden="true" />}
              <div className="fw-copy">
                <h2>{row.name}</h2>
                <p>{row.target.name}</p>
              </div>
              <div className="fw-files">
                <FileChip file={row.video} label="Instruction video" icon={<VideoIcon />} />
                <FileChip file={row.document} label="Instruction document" icon={<DocIcon />} />
              </div>
            </article>
          ))}
        </div>
      ) : <p className="empty-block">None</p>}
    </div>
  );
}
