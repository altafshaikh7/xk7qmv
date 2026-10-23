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
        <strong>Decision basis:</strong> for delivery on {data.delivery_day}, the buyer
        decides on D-1 at {data.cutoff_local} UK time ({fmtTime(data.cutoff_utc)}).
        The latest forecast available was published at{" "}
        <strong>{fmtTime(data.latest_forecast_published)}</strong>. Forecasts published
        after the cutoff are never used.
      </div>

      <h2>Forecast vs actual wind generation</h2>
      <div className="chart">
        <ResponsiveContainer width="100%" height={320}>
          <LineChart data={rows} margin={{ top: 8, right: 16, bottom: 8, left: 8 }}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="hour" />
            <YAxis tickFormatter={(v) => `${v / 1000}`} label={{ value: "GW", angle: -90, position: "insideLeft" }} />
            <Tooltip formatter={(v) => fmtMW(v)} />
            <Legend />
            <Line type="monotone" dataKey="forecast" name="Forecast (at decision time)" stroke="#2563eb" dot={false} strokeWidth={2} />
            <Line type="monotone" dataKey="actual" name="Actual" stroke="#16a34a" dot={false} strokeWidth={2} />
          </LineChart>
        </ResponsiveContainer>
      </div>
      <p className="note">Hours are UTC (equal to UK time in January). Actual = average of the two half-hourly values in each hour.</p>

      <h2>Forecast error (forecast minus actual)</h2>
      <div className="chart">
        <ResponsiveContainer width="100%" height={220}>
          <BarChart data={rows} margin={{ top: 8, right: 16, bottom: 8, left: 8 }}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="hour" />
            <YAxis />
            <Tooltip formatter={(v) => fmtMW(v)} />
            <ReferenceLine y={0} stroke="#444" />
            <Bar dataKey="error" name="Error (MW)" fill="#dc2626" />
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
          <strong>Using the error in the decision (January 2026 history, same cutoff):</strong>{" "}
          forecast exceeded actual by {fmtMW(o.bias_mw)} on average, and 90% of hours were within{" "}
          {fmtMW(o.p90_abs_error_mw)}. This is measured on the same month it describes, so treat it
          as an indication, not a guarantee.
        </div>
      )}
    </>
  );
}
