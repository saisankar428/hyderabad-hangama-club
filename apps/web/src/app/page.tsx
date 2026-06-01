"use client";

import { useEffect, useMemo, useState } from "react";
import { RegistrationForm } from "@/src/features/registration/RegistrationForm";

interface EventData {
  id: string;
  name: string;
  description: string | null;
  venue: string;
  event_date: string;
  capacity: number;
  ticket_price: number;
}

const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function HomePage() {
  const [event, setEvent] = useState<EventData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchEvent = async () => {
      try {
        const response = await fetch(`${apiUrl}/events`);
        const data = await response.json();
        if (!response.ok) {
          throw new Error(data.detail || "Unable to load event.");
        }
        setEvent(data[0] || null);
      } catch (err) {
        setError("Unable to load event details.");
      } finally {
        setLoading(false);
      }
    };
    fetchEvent();
  }, []);

  const ticketPrice = useMemo(() => {
    if (!event) return "INR 0";
    return `INR ${(event.ticket_price / 100).toFixed(0)}`;
  }, [event]);

  return (
    <main className="page-shell">
      <section className="hero-section">
        <div className="hero-copy">
          <p className="eyebrow">Tollywood Jam Night</p>
          <h1>Roast & Toast Lounge</h1>
          <p className="hero-meta">Sunday June 7 · 5 PM</p>
          <p className="hero-text">
            Join Hyderabad Hangama Club for an evening of Tollywood music, dance, and live entertainment. Secure your ticket fast.
          </p>
          <div className="hero-stats">
            <span>{ticketPrice}</span>
            <span>{event?.capacity ?? "200"} seats available</span>
          </div>
        </div>
        <div className="hero-image">
          <div className="event-banner">Tollywood Jam Night</div>
        </div>
      </section>

      <section className="content-section">
        <div className="content-card">
          <h2>About the event</h2>
          <p>
            Experience the best of Tollywood in a premium lounge ambience. The event includes live performances, curated cocktails, and a perfect evening with friends.
          </p>
        </div>

        <div className="content-card">
          <h2>Register now</h2>
          {loading && <p>Loading registration form…</p>}
          {error && <p className="message-error">{error}</p>}
          {event && <RegistrationForm event={event} />}
        </div>
      </section>
    </main>
  );
}
