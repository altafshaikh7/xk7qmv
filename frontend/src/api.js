// Set VITE_API_BASE at build time when the API is hosted elsewhere.
const BASE = import.meta.env.VITE_API_BASE || "";

export async function api(path, params = {}) {
  const qs = new URLSearchParams(params).toString();
  const res = await fetch(`${BASE}/api/${path}${qs ? `?${qs}` : ""}`);
  if (!res.ok) {
    let msg = `Request failed (${res.status})`;
    try {
      const body = await res.json();
      if (body.detail) msg = typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail);
    } catch {
      /* non-JSON error body */
    }
    throw new Error(msg);
  }
  return res.json();
}
