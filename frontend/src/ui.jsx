import { useEffect, useState } from "react";

export function useJson(url) {
  const [state, setState] = useState({ status: "loading", data: null, error: "" });

  useEffect(() => {
    const controller = new AbortController();
    setState({ status: "loading", data: null, error: "" });
    fetch(url, {
      headers: { Accept: "application/json" },
      signal: controller.signal,
    })
      .then(async (response) => {
        if (!response.ok) {
          throw new Error(
            response.status === 404 ? "This record was not found." : "The page could not be loaded.",
          );
        }
        return response.json();
      })
      .then((data) => setState({ status: "ready", data, error: "" }))
      .catch((error) => {
        if (error.name === "AbortError") return;
        setState({ status: "error", data: null, error: error.message });
      });
    return () => controller.abort();
  }, [url]);

  return state;
}

export function csrfToken() {
  const input = document.querySelector("[name=csrfmiddlewaretoken]");
  return input ? input.value : "";
}

export function PageHeader({ eyebrow, title, lede, children }) {
  return (
    <header className="page-head">
      <div>
        {eyebrow ? <p className="eyebrow">{eyebrow}</p> : null}
        <h1>{title}</h1>
        {lede ? <p className="lede">{lede}</p> : null}
      </div>
      {children ? <div className="page-tools">{children}</div> : null}
    </header>
  );
}

export function Loading({ label }) {
  return (
    <div className="loading" role="status">
      <span />
      <span />
      <span />
      <p>{label}</p>
    </div>
  );
}

export function LoadError({ message }) {
  return (
    <p className="banner banner-error" role="alert">
      {message}
    </p>
  );
}

export function StatusPill({ status, label }) {
  return <span className={`status status-${status}`}>{label}</span>;
}

export function DocIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path d="M6 2.5h8.2L19.5 8v12.2A1.8 1.8 0 0 1 17.7 22H6.3A1.8 1.8 0 0 1 4.5 20.2V4.3A1.8 1.8 0 0 1 6.3 2.5H6z" />
      <path d="M14 2.8V8h5.2" />
    </svg>
  );
}

export function VideoIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path d="M3.5 7.2h11.2A1.3 1.3 0 0 1 16 8.5v7a1.3 1.3 0 0 1-1.3 1.3H3.5A1.3 1.3 0 0 1 2.2 15.5v-7A1.3 1.3 0 0 1 3.5 7.2z" />
      <path d="M16 10.2l5.2-2.6v8.8L16 13.8z" />
    </svg>
  );
}
