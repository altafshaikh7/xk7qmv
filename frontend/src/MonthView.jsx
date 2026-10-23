import {
  ResponsiveContainer, BarChart, Bar, LineChart, Line,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ReferenceLine,
} from "recharts";
import { Card, fmtMW } from "./ui.jsx";

export default function MonthView({ data }) {
  const o = data.overall;
  const daily = data.daily.map((d) => ({ day: d.date.slice(5), mae: d.mae_mw, bias: d.bias_mw }));
  const byHour = data.by_hour.map((h) => ({
    hour: `${String(h.hour_utc).padStart(2, "0")}:00`,
    mae: h.mae_mw,
    bias: h.bias_mw,
  }));

  return (
    <>
      <div className="banner">
        <svg className="banner-icon" viewBox="0 0 20 20" fill="none" aria-hidden="true">
          <circle cx="10" cy="10" r="8" stroke="#4f46e5" strokeWidth="1.5" />
          <path d="M10 9v4M10 6.2v.1" stroke="#4f46e5" strokeWidth="1.8" strokeLinecap="round" />
        </svg>
        Delivery days 2 Jan to 1 Feb 2026 ({data.days_covered} days, {o.n_hours} hours).
        Purchase decisions are made on D-1, so the decisions fall in January 2026.
      </div>

      <h2>Overall accuracy</h2>
      <div className="cards">
        <Card label="Bias" value={fmtMW(o.bias_mw)} hint="Forecast minus actual, average" />
        <Card label="MAE" value={fmtMW(o.mae_mw)} hint={`${o.mae_pct_of_mean_actual?.toFixed(1)}% of mean actual`} />
        <Card label="RMSE" value={fmtMW(o.rmse_mw)} />
        <Card label="Median abs error" value={fmtMW(o.p50_abs_error_mw)} />
        <Card label="P90 abs error" value={fmtMW(o.p90_abs_error_mw)} />
        <Card label="P95 abs error" value={fmtMW(o.p95_abs_error_mw)} />
      </div>

      <h2>Daily MAE and bias</h2>
      <div className="chart">
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={daily} margin={{ top: 8, right: 16, bottom: 8, left: 8 }}>
            <CartesianGrid stroke="#e9eef5" strokeDasharray="3 5" vertical={false} />
            <XAxis dataKey="day" tickLine={false} />
            <YAxis tickLine={false} axisLine={false} />
            <Tooltip formatter={(v) => fmtMW(v)} contentStyle={{ borderRadius: 10, borderColor: "#e2e8f0", boxShadow: "0 8px 24px rgb(15 23 42 / 12%)" }} />
            <Legend verticalAlign="top" height={32} />
            <ReferenceLine y={0} stroke="#94a3b8" strokeDasharray="4 4" />
            <Bar dataKey="mae" name="MAE" fill="#4f46e5" radius={[5, 5, 0, 0]} />
            <Bar dataKey="bias" name="Bias" fill="#e11d48" radius={[5, 5, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      <h2>Error by hour of day (UTC)</h2>
      <div className="chart">
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={byHour} margin={{ top: 8, right: 16, bottom: 8, left: 8 }}>
            <CartesianGrid stroke="#e9eef5" strokeDasharray="3 5" vertical={false} />
            <XAxis dataKey="hour" tickLine={false} />
            <YAxis tickLine={false} axisLine={false} />
            <Tooltip formatter={(v) => fmtMW(v)} contentStyle={{ borderRadius: 10, borderColor: "#e2e8f0", boxShadow: "0 8px 24px rgb(15 23 42 / 12%)" }} />
            <Legend verticalAlign="top" height={32} />
            <Line type="monotone" dataKey="mae" name="MAE" stroke="#4f46e5" dot={false} strokeWidth={2.5} />
            <Line type="monotone" dataKey="bias" name="Bias" stroke="#e11d48" dot={false} strokeWidth={2.5} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </>
  );
}
