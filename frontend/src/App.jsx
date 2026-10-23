import { useEffect, useState } from "react";
import { api } from "./api.js";
import DayView from "./DayView.jsx";
import MonthView from "./MonthView.jsx";

export default function App() {
  const [config, setConfig] = useState(null);
  const [view, setView] = useState("day");
  const [date, setDate] = useState("");
  const [cutoff, setCutoff] = useState("");
  const [dayData, setDayData] = useState(null);
  const [monthData, setMonthData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    api("config")
      .then((c) => {
        setConfig(c);
        setDate(c.first_delivery_day);
        setCutoff(c.default_cutoff);
      })
      .catch((e) => setError(`Could not reach the API: ${e.message}`));
  }, []);

  useEffect(() => {
    if (!config || !date || !cutoff) return;
    let cancelled = false;
    setLoading(true);
    setError("");
    const load = async () => {
      try {
        const [d, m] = await Promise.all([
          api("day", { date, cutoff }),
          api("metrics", { cutoff }),
        ]);
        if (!cancelled) {
          setDayData(d);
          setMonthData(m);
        }
      } catch (e) {
        if (!cancelled) {
          setDayData(null);
          setError(e.message);
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    load();
    return () => {
      cancelled = true;
    };
  }, [config, date, cutoff]);

  return (
    <div className="page">
      <header>
        <h1>Wind Forecast Decision Support</h1>
        <p>GB day-ahead purchasing: which wind forecast was available, and how accurate it is.</p>
      </header>

      {config && (
        <div className="controls">
          <label>
            Delivery day
            <input
              type="date"
              value={date}
              min={config.first_delivery_day}
              max={config.last_delivery_day}
              onChange={(e) => e.target.value && setDate(e.target.value)}
            />
          </label>
          <label>
            Decision cutoff (UK time, D-1)
            <input type="time" value={cutoff} onChange={(e) => e.target.value && setCutoff(e.target.value)} />
          </label>
          <div className="tabs">
            <button className={view === "day" ? "active" : ""} onClick={() => setView("day")}>Decision day</button>
            <button className={view === "month" ? "active" : ""} onClick={() => setView("month")}>Month overview</button>
          </div>
        </div>
      )}

      {config && (
        <p className="note">
          Cutoff default {config.default_cutoff} is an assumption (day-ahead gate closure); change it to match your actual deadline.
        </p>
      )}

      {loading && <p className="status">Loading...</p>}
      {error && <p className="status error">{error}</p>}

      {!error && view === "day" && dayData && <DayView data={dayData} monthly={monthData} />}
      {!error && view === "month" && monthData && <MonthView data={monthData} />}
    </div>
  );
}
