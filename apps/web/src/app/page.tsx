"use client";

import { useEffect, useMemo, useState } from "react";
import { RegistrationForm } from "@/features/registration/RegistrationForm";

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

  useEffect(() => {
    fetch(`${apiUrl}/events`)
      .then((r) => (r.ok ? r.json() : null))
      .then((data) => setEvent(data?.[0] ?? null))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const price = useMemo(
    () => (event ? `₹${(event.ticket_price / 100).toFixed(0)}` : "₹500"),
    [event]
  );
  const capacity = event?.capacity ?? 200;

  return (
    <div style={{ background: "#000", minHeight: "100vh" }}>

      {/* ── HERO ───────────────────────────────────────────── */}
      <section className="hhc-hero">

        {/* Concert spotlights */}
        <div className="hhc-light hhc-light-gold"   aria-hidden="true" />
        <div className="hhc-light hhc-light-purple" aria-hidden="true" />
        <div className="hhc-light hhc-light-orange" aria-hidden="true" />

        <div className="hhc-hero-inner">

          {/* 1 — Brand */}
          <p className="hhc-brand">Hyderabad Hangama Club</p>

          {/* 2 — Tagline */}
          <p className="hhc-tagline">
            Mana Paata&nbsp;&nbsp;•&nbsp;&nbsp;Mana Vibe&nbsp;&nbsp;•&nbsp;&nbsp;Mana Hangama
          </p>

          {/* Gold rule */}
          <div className="hhc-divider" />

          {/* 3 — Event name */}
          <h1 className="hhc-event-title">
            Tollywood<br />Jam Night
          </h1>

          {/* 4–6 — Venue · Date · Time */}
          <div className="hhc-meta">
            <span className="hhc-meta-item">
              <span className="hhc-meta-icon">📍</span>
              Roast &amp; Toast Lounge
            </span>
            <span className="hhc-meta-sep" aria-hidden="true">·</span>
            <span className="hhc-meta-item">
              <span className="hhc-meta-icon">📅</span>
              Sunday, June 7
            </span>
            <span className="hhc-meta-sep" aria-hidden="true">·</span>
            <span className="hhc-meta-item">
              <span className="hhc-meta-icon">🕔</span>
              5 PM Onwards
            </span>
          </div>

          {/* Badges */}
          <div className="hhc-badges">
            <span className="hhc-badge hhc-badge-price">{price} per ticket</span>
            <span className="hhc-badge hhc-badge-seats">{capacity} seats</span>
          </div>

          {/* CTA */}
          <a href="#register" className="hhc-cta">
            Book My Ticket
          </a>
        </div>
      </section>

      {/* ── ABOUT + REGISTER ───────────────────────────────── */}
      <section id="register" className="hhc-content">

        <div className="hhc-card">
          <h2>About the event</h2>
          <p>
            Hyderabad Hangama Club brings you Tollywood Jam Night — an evening of live
            Tollywood music, energy-filled performances, curated cocktails, and pure
            hangama with your people. Join us at the iconic Roast &amp; Toast Lounge
            for a night you&apos;ll talk about for weeks.
          </p>
          <p style={{ marginTop: "16px" }}>
            Limited seats. First come, first served. Secure yours now.
          </p>
        </div>

        <div className="hhc-card">
          <h2>Register now</h2>

          {loading && (
            <p style={{ color: "rgba(255,255,255,0.4)", fontSize: "0.9rem" }}>
              Loading…
            </p>
          )}

          {!loading && !event && (
            <p style={{ color: "rgba(255,255,255,0.45)", fontSize: "0.9rem", lineHeight: 1.7 }}>
              Registration details loading shortly.
              <br />
              Check back in a moment or refresh the page.
            </p>
          )}

          {event && <RegistrationForm event={event} />}
        </div>
      </section>
    </div>
  );
}
