"use client";

import { Fragment, useCallback, useEffect, useMemo, useState } from "react";
import { RegistrationForm } from "@/features/registration/RegistrationForm";

/* ── Types ───────────────────────────────────────────────────── */

interface EventData {
  id: string;
  name: string;
  description: string | null;
  venue: string;
  event_date: string;
  capacity: number;
  ticket_price: number;
}

/* ── SVG: Vintage Microphone ─────────────────────────────────── */

function MicSVG({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 100 200" fill="none" xmlns="http://www.w3.org/2000/svg">
      {/* Capsule body */}
      <rect x="21" y="8" width="58" height="96" rx="29" stroke="currentColor" strokeWidth="3.5" />
      {/* Horizontal mesh lines */}
      <line x1="21" y1="36" x2="79" y2="36" stroke="currentColor" strokeWidth="1.8" />
      <line x1="19" y1="52" x2="81" y2="52" stroke="currentColor" strokeWidth="1.8" />
      <line x1="19" y1="68" x2="81" y2="68" stroke="currentColor" strokeWidth="1.8" />
      <line x1="21" y1="84" x2="79" y2="84" stroke="currentColor" strokeWidth="1.8" />
      {/* Vertical centre line */}
      <line x1="50" y1="8" x2="50" y2="104" stroke="currentColor" strokeWidth="1.4" strokeDasharray="4 3" />
      {/* Stand */}
      <line x1="50" y1="104" x2="50" y2="148" stroke="currentColor" strokeWidth="5" strokeLinecap="round" />
      {/* Arm */}
      <path d="M24 148 Q50 170 76 148" stroke="currentColor" strokeWidth="4" fill="none" strokeLinecap="round" />
      {/* Base */}
      <line x1="14" y1="174" x2="86" y2="174" stroke="currentColor" strokeWidth="5" strokeLinecap="round" />
    </svg>
  );
}

/* ── SVG: Acoustic Guitar ────────────────────────────────────── */

function GuitarSVG({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 72 200" fill="none" xmlns="http://www.w3.org/2000/svg">
      {/* Headstock */}
      <rect x="28" y="4" width="16" height="30" rx="5" stroke="currentColor" strokeWidth="2.5" />
      {/* Tuning pegs */}
      <circle cx="26" cy="13" r="3.5" stroke="currentColor" strokeWidth="2" />
      <circle cx="46" cy="13" r="3.5" stroke="currentColor" strokeWidth="2" />
      <circle cx="26" cy="25" r="3.5" stroke="currentColor" strokeWidth="2" />
      <circle cx="46" cy="25" r="3.5" stroke="currentColor" strokeWidth="2" />
      {/* Nut */}
      <line x1="28" y1="34" x2="44" y2="34" stroke="currentColor" strokeWidth="2.5" />
      {/* Neck */}
      <rect x="32" y="34" width="8" height="72" stroke="currentColor" strokeWidth="2" />
      {/* Fret lines */}
      <line x1="32" y1="50" x2="40" y2="50" stroke="currentColor" strokeWidth="1.5" />
      <line x1="32" y1="65" x2="40" y2="65" stroke="currentColor" strokeWidth="1.5" />
      <line x1="32" y1="80" x2="40" y2="80" stroke="currentColor" strokeWidth="1.5" />
      <line x1="32" y1="95" x2="40" y2="95" stroke="currentColor" strokeWidth="1.5" />
      {/* Upper bout */}
      <ellipse cx="36" cy="128" rx="22" ry="22" stroke="currentColor" strokeWidth="2.5" />
      {/* Waist (mask + lines) */}
      <rect x="28" y="144" width="16" height="12" fill="#060611" />
      <line x1="28" y1="144" x2="28" y2="156" stroke="currentColor" strokeWidth="2.5" />
      <line x1="44" y1="144" x2="44" y2="156" stroke="currentColor" strokeWidth="2.5" />
      {/* Lower bout */}
      <ellipse cx="36" cy="168" rx="28" ry="24" stroke="currentColor" strokeWidth="2.5" />
      {/* Sound hole */}
      <circle cx="36" cy="165" r="10" stroke="currentColor" strokeWidth="2" />
      {/* Bridge */}
      <rect x="26" y="179" width="20" height="5" rx="2.5" stroke="currentColor" strokeWidth="1.8" />
    </svg>
  );
}

/* ── Countdown hook ──────────────────────────────────────────── */

interface TimeLeft { days: number; hours: number; minutes: number; seconds: number; }

function useCountdown(target: Date): TimeLeft {
  const [t, setT] = useState<TimeLeft>({ days: 0, hours: 0, minutes: 0, seconds: 0 });
  useEffect(() => {
    const tick = () => {
      const diff = target.getTime() - Date.now();
      if (diff <= 0) { setT({ days: 0, hours: 0, minutes: 0, seconds: 0 }); return; }
      setT({
        days:    Math.floor(diff / 86_400_000),
        hours:   Math.floor((diff % 86_400_000) / 3_600_000),
        minutes: Math.floor((diff % 3_600_000) / 60_000),
        seconds: Math.floor((diff % 60_000) / 1_000),
      });
    };
    tick();
    const id = setInterval(tick, 1000);
    return () => clearInterval(id);
  }, [target]);
  return t;
}

/* ── Static data ─────────────────────────────────────────────── */

// 7 Jun 2026 17:00 IST = 11:30 UTC
const EVENT_DATE = new Date("2026-06-07T11:30:00Z");

const FEATURES = [
  { icon: "🎤", label: "Sing\nAlong" },
  { icon: "🎸", label: "Live\nBand" },
  { icon: "🎵", label: "Tollywood\nHits" },
  { icon: "👥", label: "Music\nLovers" },
  { icon: "✨", label: "Good\nVibes" },
];

const WHAT_TO_EXPECT = [
  "Telugu Retro Classics",
  "Melody Hits",
  "DSP & Thaman Specials",
  "Devi Sri Prasad Mass Beats",
  "Ilaiyaraaja & Keeravani Magic",
  "Audience Sing-Along Sessions",
  "Live Band Experience",
  "Networking & Fun",
];

// Floating notes — deterministic positions (no random, SSR-safe)
const FLOAT_NOTES = [
  { sym: "♪", left: "5%",  bottom: "18%", size: "1.3rem", delay: "0s",    dur: "5.5s" },
  { sym: "♫", left: "14%", bottom: "30%", size: "1.0rem", delay: "1.2s",  dur: "6.0s" },
  { sym: "♩", left: "23%", bottom: "12%", size: "1.5rem", delay: "0.5s",  dur: "5.0s" },
  { sym: "♬", left: "35%", bottom: "22%", size: "0.9rem", delay: "2.0s",  dur: "6.5s" },
  { sym: "♪", left: "48%", bottom: "8%",  size: "1.2rem", delay: "0.8s",  dur: "5.2s" },
  { sym: "🎵", left: "58%", bottom: "28%", size: "1.0rem", delay: "1.8s",  dur: "6.2s" },
  { sym: "♫", left: "68%", bottom: "15%", size: "1.4rem", delay: "0.3s",  dur: "4.8s" },
  { sym: "♩", left: "78%", bottom: "24%", size: "0.85rem",delay: "2.5s",  dur: "5.8s" },
  { sym: "♬", left: "88%", bottom: "10%", size: "1.1rem", delay: "1.0s",  dur: "5.4s" },
  { sym: "♪", left: "93%", bottom: "32%", size: "0.8rem", delay: "3.0s",  dur: "6.8s" },
];

const CD_ITEMS = ["Days", "Hrs", "Mins", "Secs"] as const;

const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const FALLBACK_EVENT: EventData = {
  id: "upcoming",
  name: "Tollywood Jam Night",
  description: null,
  venue: "Roast & Toast Lounge",
  event_date: "2026-06-07T11:30:00Z",
  capacity: 200,
  ticket_price: 29900,
};

/* ── Page ────────────────────────────────────────────────────── */

export default function HomePage() {
  const [event, setEvent] = useState<EventData>(FALLBACK_EVENT);
  const [eventStatus, setEventStatus] = useState<"loading" | "success" | "error">("loading");
  const countdown = useCountdown(EVENT_DATE);

  const fetchEvent = useCallback(() => {
    setEventStatus("loading");
    fetch(`${apiUrl}/events`)
      .then((r) => (r.ok ? r.json() : Promise.reject()))
      .then((data) => {
        const first: EventData | undefined = data?.[0];
        if (first) setEvent(first);
        setEventStatus("success");
      })
      .catch(() => setEventStatus("error"));
  }, []);

  useEffect(() => { fetchEvent(); }, [fetchEvent]);

  const price    = useMemo(() => `₹${(event.ticket_price / 100).toFixed(0)}`, [event]);
  const capacity = event.capacity;
  const pad      = (n: number) => String(n).padStart(2, "0");

  const cdValues: Record<typeof CD_ITEMS[number], string> = {
    Days: pad(countdown.days),
    Hrs:  pad(countdown.hours),
    Mins: pad(countdown.minutes),
    Secs: pad(countdown.seconds),
  };

  return (
    <div style={{ background: "var(--bg)", minHeight: "100vh" }}>

      {/* ══════════════════════════ HERO ══════════════════════════ */}
      <section className="concert-hero">

        {/* Spotlight blobs */}
        <div className="cl cl-gold"   aria-hidden="true" />
        <div className="cl cl-purple" aria-hidden="true" />
        <div className="cl cl-orange" aria-hidden="true" />
        <div className="cl cl-blue"   aria-hidden="true" />

        {/* Floating musical notes */}
        {FLOAT_NOTES.map((n, i) => (
          <span
            key={i}
            className="float-note"
            aria-hidden="true"
            style={{
              left:              n.left,
              bottom:            n.bottom,
              fontSize:          n.size,
              animationDelay:    n.delay,
              animationDuration: n.dur,
            }}
          >
            {n.sym}
          </span>
        ))}

        {/* Corner badge */}
        <div className="grand-badge">★ &nbsp; Grand Launch Event &nbsp; ★</div>

        <div className="concert-hero-inner">

          {/* Eyebrow */}
          <p className="hero-eyebrow">
            It&apos;s not just an event &mdash; it&apos;s the start of a musical movement.
          </p>

          {/* Brand row: Mic ── Name ── Guitar */}
          <div className="brand-row">
            <MicSVG className="hero-mic-svg" />
            <div>
              <p className="concert-brand">Hyderabad Hangama Club</p>
              <p className="concert-brand-sub">Where Hyderabad Sings Together</p>
            </div>
            <GuitarSVG className="hero-guitar-svg" />
          </div>

          {/* Animated shimmer divider */}
          <div className="concert-divider" />

          {/* Event name */}
          <h1 className="concert-event-name">
            <span className="en-line1">Tollywood</span>
            <span className="en-line2">Jam Night</span>
          </h1>

          {/* Purple tagline pill */}
          <div className="mana-pill">
            Mana Paata &nbsp;•&nbsp; Mana Vibe &nbsp;•&nbsp; Mana Hangama
          </div>

          {/* Feature chips */}
          <div className="features-strip">
            {FEATURES.map((f) => (
              <div key={f.label} className="feature-chip">
                <span className="feature-icon">{f.icon}</span>
                <span className="feature-label" style={{ whiteSpace: "pre-line" }}>{f.label}</span>
              </div>
            ))}
          </div>

          {/* Countdown */}
          <div className="countdown-wrap">
            <p className="countdown-label">Event starts in</p>
            <div className="countdown-grid">
              {CD_ITEMS.map((unit, i) => (
                <Fragment key={unit}>
                  <div className="cd-box">
                    <span className="cd-val">{cdValues[unit]}</span>
                    <span className="cd-unit">{unit}</span>
                  </div>
                  {i < 3 && <span className="cd-sep" aria-hidden="true">:</span>}
                </Fragment>
              ))}
            </div>
          </div>

          {/* Event meta */}
          <div className="event-meta-bar">
            <div className="meta-chip"><span>📅</span><span>Sunday, June 7, 2026</span></div>
            <span className="meta-divider" aria-hidden="true">|</span>
            <div className="meta-chip"><span>🕔</span><span>5 PM Onwards</span></div>
            <span className="meta-divider" aria-hidden="true">|</span>
            <div className="meta-chip"><span>📍</span><span>Roast &amp; Toast Lounge</span></div>
          </div>

          {/* Badges */}
          <div className="ticket-badges">
            <span className="tbadge tbadge-price">{price} per ticket</span>
            <span className="tbadge tbadge-seats">{capacity} seats only</span>
            <span className="tbadge tbadge-early">🎟 Early Bird Available</span>
          </div>

          {/* CTA */}
          <a href="#register" className="book-cta">
            <span>🎤</span>
            <span>Book My Spot</span>
            <span className="cta-arrow">→</span>
          </a>

          <p className="social-handle">
            Follow us for updates: <strong>@hyderabadhangamaclub</strong>
          </p>

        </div>
      </section>

      {/* ══════════════════════ WHAT TO EXPECT ══════════════════ */}
      <section className="expect-section">
        <div className="expect-inner">
          <h2 className="expect-title">What to Expect?</h2>
          <div className="expect-grid">
            {WHAT_TO_EXPECT.map((item) => (
              <div key={item} className="expect-item">
                <span className="expect-note">♪</span>
                <span>{item}</span>
              </div>
            ))}
          </div>
          <p className="expect-cta">
            Be a part of Hyderabad&apos;s biggest Telugu Musical Community!
          </p>
          <p className="expect-social">
            Follow us: <strong>@hyderabadhangamaclub</strong>
          </p>
        </div>
      </section>

      {/* ══════════════════════ ABOUT + REGISTER ════════════════ */}
      <section id="register" className="hhc-content">

        <div className="hhc-card">
          <h2>About the event</h2>
          <p>
            Hyderabad Hangama Club brings you Tollywood Jam Night — an evening of live
            Tollywood music, energy-filled performances, curated cocktails, and pure
            hangama with your people. Join us at the iconic Roast &amp; Toast Lounge
            for a night you&apos;ll talk about for weeks.
          </p>
          <p style={{ marginTop: 16 }}>
            Limited seats. First come, first served. Secure yours now before they&apos;re gone.
          </p>
        </div>

        <div className="hhc-card">
          <h2>Register now</h2>
          {eventStatus === "loading" && (
            <p className="event-status-line event-status-loading">Loading event details…</p>
          )}
          {eventStatus === "error" && (
            <p className="event-status-line">
              Using saved event info &nbsp;·&nbsp;{" "}
              <button className="event-retry-btn" onClick={fetchEvent}>Retry</button>
            </p>
          )}
          <RegistrationForm event={event} />
        </div>

      </section>

    </div>
  );
}
