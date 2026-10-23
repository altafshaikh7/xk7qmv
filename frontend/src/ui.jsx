export const fmtMW = (v) =>
  v == null ? "-" : `${Math.round(v).toLocaleString("en-GB")} MW`;

export const fmtTime = (iso) =>
  iso ? `${iso.replace("T", " ").slice(0, 16)} UTC` : "-";

export function Card({ label, value, hint }) {
  return (
    <div className="card">
      <div className="card-label">{label}</div>
      <div className="card-value">{value}</div>
      {hint && <div className="card-hint">{hint}</div>}
    </div>
  );
}
