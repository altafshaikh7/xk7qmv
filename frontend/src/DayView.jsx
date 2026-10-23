import {
  ResponsiveContainer, LineChart, Line, BarChart, Bar,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ReferenceLine,
} from "recharts";
import { Card, fmtMW, fmtTime } from "./ui.jsx";

export default function DayView({ data, monthly }) {
  const rows = data.hours.map((h) => ({
    hour: h.time.slice(11, 16),
    forecast: h.forecast_mw,
    actual: h.actual_mw,
    error: h.error_mw,
  }));
  const m = data.metrics;
  const o = monthly?.overall;

  return (
    <>
      <div className="banner">
        <svg className="banner-icon" viewBox="0 0 20 20" fill="none" aria-hidden="true">
          <circle cx="10" cy="10" r="8" stroke="#4f46e5" strokeWidth="1.5" />
          <path d="M10 9v4M10 6.2v.1" stroke="#4f46e5" strokeWidth="1.8" strokeLinecap="round" />
        </svg>
        <strong>Decision basis:</strong> for delivery on {data.delivery_day}, the buyer
        decides on D-1 at {data.cutoff_local} UK time ({fmtTime(data.cutoff_utc)}).
        The latest forecast available was published at{" "}
        <strong className="published-time">{fmtTime(data.latest_forecast_published)}</strong>. Forecasts published
        after the cutoff are never used.
      </div>

      <h2>Forecast vs actual wind generation</h2>
      <div className="chart">
        <ResponsiveContainer width="100%" height={320}>
          <LineChart data={rows} margin={{ top: 8, right: 16, bottom: 8, left: 8 }}>
            <CartesianGrid stroke="#e9eef5" strokeDasharray="3 5" vertical={false} />
            <XAxis dataKey="hour" tickLine={false} />
            <YAxis tickFormatter={(v) => `${v / 1000}`} tickLine={false} axisLine={false} label={{ value: "GW", angle: -90, position: "insideLeft", fill: "#64748b" }} />
            <Tooltip formatter={(v) => fmtMW(v)} contentStyle={{ borderRadius: 10, borderColor: "#e2e8f0", boxShadow: "0 8px 24px rgb(15 23 42 / 12%)" }} />
            <Legend verticalAlign="top" height={32} />
            <Line type="monotone" dataKey="forecast" name="Forecast (at decision time)" stroke="#4f46e5" dot={false} strokeWidth={2.5} />
            <Line type="monotone" dataKey="actual" name="Actual" stroke="#10b981" dot={false} strokeWidth={2.5} />
          </LineChart>
        </ResponsiveContainer>
      </div>
      <p className="note">Hours are UTC (equal to UK time in January). Actual = average of the two half-hourly values in each hour.</p>

      <h2>Forecast error (forecast minus actual)</h2>
      <div className="chart">
        <ResponsiveContainer width="100%" height={220}>
          <BarChart data={rows} margin={{ top: 8, right: 16, bottom: 8, left: 8 }}>
            <CartesianGrid stroke="#e9eef5" strokeDasharray="3 5" vertical={false} />
            <XAxis dataKey="hour" tickLine={false} />
            <YAxis tickLine={false} axisLine={false} />
            <Tooltip formatter={(v) => fmtMW(v)} contentStyle={{ borderRadius: 10, borderColor: "#e2e8f0", boxShadow: "0 8px 24px rgb(15 23 42 / 12%)" }} />
            <ReferenceLine y={0} stroke="#94a3b8" strokeDasharray="4 4" />
            <Bar dataKey="error" name="Error (MW)" fill="#e11d48" radius={[5, 5, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
      <p className="note">Positive = forecast too high (wind over-counted, so risk of buying too little thermal).</p>

      <h2>Accuracy for this day</h2>
      <div className="cards">
        <Card label="Bias" value={fmtMW(m.bias_mw)} hint="Average of forecast minus actual" />
        <Card label="MAE" value={fmtMW(m.mae_mw)} hint="Typical miss size" />
        <Card label="RMSE" value={fmtMW(m.rmse_mw)} hint="Penalises large misses" />
        <Card label="P90 abs error" value={fmtMW(m.p90_abs_error_mw)} hint="90% of hours miss by less" />
      </div>

      {o && (
        <div className="banner">
          <svg className="banner-icon" viewBox="0 0 20 20" fill="none" aria-hidden="true">
            <circle cx="10" cy="10" r="8" stroke="#4f46e5" strokeWidth="1.5" />
            <path d="M10 9v4M10 6.2v.1" stroke="#4f46e5" strokeWidth="1.8" strokeLinecap="round" />
          </svg>
          <strong>Using the error in the decision (January 2026 history, same cutoff):</strong>{" "}
          forecast exceeded actual by {fmtMW(o.bias_mw)} on average, and 90% of hours were within{" "}
          {fmtMW(o.p90_abs_error_mw)}. This is measured on the same month it describes, so treat it
          as an indication, not a guarantee.
        </div>
      )}
    </>
  );
}
