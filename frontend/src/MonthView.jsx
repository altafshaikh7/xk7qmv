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
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="day" />
            <YAxis />
            <Tooltip formatter={(v) => fmtMW(v)} />
            <Legend />
            <ReferenceLine y={0} stroke="#444" />
            <Bar dataKey="mae" name="MAE" fill="#2563eb" />
            <Bar dataKey="bias" name="Bias" fill="#dc2626" />
          </BarChart>
        </ResponsiveContainer>
      </div>

      <h2>Error by hour of day (UTC)</h2>
      <div className="chart">
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={byHour} margin={{ top: 8, right: 16, bottom: 8, left: 8 }}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="hour" />
            <YAxis />
            <Tooltip formatter={(v) => fmtMW(v)} />
            <Legend />
            <Line type="monotone" dataKey="mae" name="MAE" stroke="#2563eb" dot={false} strokeWidth={2} />
            <Line type="monotone" dataKey="bias" name="Bias" stroke="#dc2626" dot={false} strokeWidth={2} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </>
  );
}
