"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { RegistrationForm } from "@/features/registration/RegistrationForm";
import { getApiUrl } from "@/lib/env";

interface EventData {
  id: string;
  name: string;
  description: string | null;
  venue: string;
  event_date: string;
  capacity: number;
  ticket_price: number;
}

const apiUrl = getApiUrl();

const FALLBACK_EVENT: EventData = {
  id: "upcoming",
  name: "Tollywood Jam Night",
  description: null,
  venue: "Roast & Toast Lounge",
  event_date: "2026-06-06T11:30:00Z",
  capacity: 100,
  ticket_price: 29900,
};

export default function RegisterPage() {
  const [event, setEvent] = useState<EventData>(FALLBACK_EVENT);
  const [status, setStatus] = useState<"loading" | "success" | "error">("loading");

  const fetchEvent = useCallback(() => {
    setStatus("loading");
    fetch(`${apiUrl}/events`)
      .then((r) => (r.ok ? r.json() : Promise.reject()))
      .then((data) => {
        const first: EventData | undefined = data?.[0];
        if (first) setEvent(first);
        setStatus("success");
      })
      .catch(() => setStatus("error"));
  }, []);

  useEffect(() => { fetchEvent(); }, [fetchEvent]);

  const price = Math.round(event.ticket_price / 100);

  return (
    <div className="register-page">

      {/* Sticky header */}
      <header className="register-header">
        <Link href="/" className="register-back">← Back</Link>
        <p className="register-header-brand">Hyderabad Hangama Club</p>
      </header>

      {/* Event summary */}
      <div className="register-event-strip">
        <h1 className="register-event-title">Tollywood Jam Night</h1>
        <div className="register-event-meta">
          <span>📅 Saturday, June 6, 2026</span>
          <span>🕔 5 PM Onwards</span>
          <span>📍 Roast &amp; Toast Lounge</span>
          <span>🎟 ₹{price} per ticket · {event.capacity} seats only</span>
        </div>
        {status === "loading" && (
          <p className="event-status-line event-status-loading" style={{ marginTop: 10 }}>
            Loading event details…
          </p>
        )}
        {status === "error" && (
          <p className="event-status-line" style={{ marginTop: 10 }}>
            Using saved event info &nbsp;·&nbsp;{" "}
            <button className="event-retry-btn" onClick={fetchEvent}>Retry</button>
          </p>
        )}
      </div>

      {/* Registration form */}
      <div className="register-form-wrap">
        <RegistrationForm event={event} />
      </div>

    </div>
  );
}
