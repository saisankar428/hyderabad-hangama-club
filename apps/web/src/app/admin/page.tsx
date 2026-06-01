"use client";

import { useState, useEffect, useCallback, useRef } from "react";

const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const POLL_MS = 30_000;

interface PendingPayment {
  id: string;
  registration_id: string;
  order_ref: string | null;
  amount: number;
  currency: string;
  utr_reference: string | null;
  payment_screenshot_url: string | null;
  attendee_name: string;
  email: string;
  phone: string;
  quantity: number;
  created_at: string;
}

interface Metrics {
  total_registrations: number;
  total_revenue: number;
  total_checked_in: number;
}

interface Toast {
  id: number;
  message: string;
  type: "success" | "error";
}

function screenshotSrc(path: string | null): string | null {
  if (!path) return null;
  return path.startsWith("http") ? path : `${apiUrl}${path}`;
}

function ToastStack({ toasts }: { toasts: Toast[] }) {
  if (!toasts.length) return null;
  return (
    <div className="toast-container">
      {toasts.map((t) => (
        <div key={t.id} className={`toast toast-${t.type}`}>{t.message}</div>
      ))}
    </div>
  );
}

export default function AdminPage() {
  const [adminKey, setAdminKey] = useState(() =>
    typeof window !== "undefined" ? localStorage.getItem("hhc_admin_key") || "" : ""
  );
  const [authed, setAuthed] = useState(false);
  const [authLoading, setAuthLoading] = useState(false);
  const [metrics, setMetrics] = useState<Metrics | null>(null);
  const [pending, setPending] = useState<PendingPayment[]>([]);
  const [processingId, setProcessingId] = useState<string | null>(null);
  const [expandedImg, setExpandedImg] = useState<string | null>(null);
  const [toasts, setToasts] = useState<Toast[]>([]);
  const [ticketCode, setTicketCode] = useState("");
  const [ticketResult, setTicketResult] = useState<any>(null);
  const [lastPolled, setLastPolled] = useState<Date | null>(null);
  const [refreshing, setRefreshing] = useState(false);
  const toastRef = useRef(0);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const toast = useCallback((message: string, type: "success" | "error") => {
    const id = ++toastRef.current;
    setToasts((p) => [...p, { id, message, type }]);
    setTimeout(() => setToasts((p) => p.filter((t) => t.id !== id)), 4500);
  }, []);

  const fetchMetrics = useCallback(async (key: string) => {
    const res = await fetch(`${apiUrl}/admin/metrics`, { headers: { "X-ADMIN-KEY": key } });
    if (!res.ok) throw new Error("metrics");
    return res.json() as Promise<Metrics>;
  }, []);

  const fetchPending = useCallback(async (key: string) => {
    const res = await fetch(`${apiUrl}/admin/payments/pending`, { headers: { "X-ADMIN-KEY": key } });
    if (!res.ok) return;
    const data: PendingPayment[] = await res.json();
    setPending(data);
    setLastPolled(new Date());
  }, []);

  const handleLogin = async () => {
    if (!adminKey) return;
    setAuthLoading(true);
    try {
      const m = await fetchMetrics(adminKey);
      setMetrics(m);
      setAuthed(true);
      localStorage.setItem("hhc_admin_key", adminKey);
      await fetchPending(adminKey);
    } catch {
      toast("Invalid admin key", "error");
    } finally {
      setAuthLoading(false);
    }
  };

  // Start 30-second polling loop once authenticated
  useEffect(() => {
    if (!authed) return;
    pollRef.current = setInterval(async () => {
      try {
        await fetchPending(adminKey);
        const m = await fetchMetrics(adminKey);
        setMetrics(m);
      } catch {
        // silent — don't disrupt the UI on transient poll failure
      }
    }, POLL_MS);
    return () => { if (pollRef.current) clearInterval(pollRef.current); };
  }, [authed, adminKey, fetchPending, fetchMetrics]);

  const handleApprove = async (paymentId: string) => {
    if (processingId) return;
    setProcessingId(paymentId);
    try {
      const res = await fetch(`${apiUrl}/admin/payments/${paymentId}/confirm`, {
        method: "POST",
        headers: { "X-ADMIN-KEY": adminKey },
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Failed");
      toast(`Ticket issued: ${data.ticket_code}`, "success");
      setPending((p) => p.filter((x) => x.id !== paymentId));
      fetchMetrics(adminKey).then(setMetrics).catch(() => {});
    } catch (e: any) {
      toast(e.message || "Approval failed", "error");
    } finally {
      setProcessingId(null);
    }
  };

  const handleReject = async (paymentId: string) => {
    if (processingId) return;
    setProcessingId(paymentId);
    try {
      const res = await fetch(`${apiUrl}/admin/payments/${paymentId}/reject`, {
        method: "POST",
        headers: { "X-ADMIN-KEY": adminKey },
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Failed");
      toast("Payment rejected", "success");
      setPending((p) => p.filter((x) => x.id !== paymentId));
    } catch (e: any) {
      toast(e.message || "Rejection failed", "error");
    } finally {
      setProcessingId(null);
    }
  };

  const searchTicket = async () => {
    if (!ticketCode) return;
    try {
      const res = await fetch(
        `${apiUrl}/admin/tickets/search?ticket_code=${encodeURIComponent(ticketCode)}`,
        { headers: { "X-ADMIN-KEY": adminKey } },
      );
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Not found");
      setTicketResult(data);
    } catch (e: any) {
      toast(e.message, "error");
      setTicketResult(null);
    }
  };

  const handleRefreshNow = async () => {
    if (refreshing) return;
    setRefreshing(true);
    try {
      await fetchPending(adminKey);
      const m = await fetchMetrics(adminKey);
      setMetrics(m);
    } catch {
      toast("Refresh failed", "error");
    } finally {
      setRefreshing(false);
    }
  };

  const handleLogout = () => {
    if (pollRef.current) clearInterval(pollRef.current);
    setAuthed(false);
    setMetrics(null);
    setPending([]);
    setTicketResult(null);
  };

  // ── Login screen ──────────────────────────────────────────────────
  if (!authed) {
    return (
      <main className="page-shell">
        <section className="admin-section admin-login-card">
          <h1 className="admin-login-title">Admin Dashboard</h1>
          <p className="admin-login-sub">Hyderabad Hangama Club — secure access</p>
          <label className="form-label">
            Admin key
            <input
              className="form-field"
              type="password"
              value={adminKey}
              onChange={(e) => setAdminKey(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleLogin()}
              placeholder="Enter admin key"
              autoComplete="current-password"
            />
          </label>
          <button className="button" onClick={handleLogin} disabled={!adminKey || authLoading}>
            {authLoading ? "Verifying…" : "Access Dashboard"}
          </button>
        </section>
        <ToastStack toasts={toasts} />
      </main>
    );
  }

  // ── Main dashboard ────────────────────────────────────────────────
  return (
    <main className="page-shell">
      {/* Screenshot lightbox */}
      {expandedImg && (
        <div className="screenshot-lightbox" onClick={() => setExpandedImg(null)}>
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src={expandedImg} alt="Payment screenshot" onClick={(e) => e.stopPropagation()} />
          <button className="lightbox-close" onClick={() => setExpandedImg(null)}>✕</button>
        </div>
      )}

      <ToastStack toasts={toasts} />

      <section className="admin-section">
        {/* Header row */}
        <div className="admin-topbar">
          <h1 className="admin-topbar-title">Admin Dashboard</h1>
          <button className="admin-logout-btn" onClick={handleLogout}>Sign out</button>
        </div>

        {/* Metrics */}
        {metrics && (
          <div className="metrics-grid">
            <div className="metric-card">
              <span>Registrations</span>
              <strong>{metrics.total_registrations}</strong>
            </div>
            <div className="metric-card">
              <span>Revenue</span>
              <strong>₹{(metrics.total_revenue / 100).toFixed(0)}</strong>
            </div>
            <div className="metric-card">
              <span>Checked in</span>
              <strong>{metrics.total_checked_in}</strong>
            </div>
          </div>
        )}

        {/* Pending Payments */}
        <div className="admin-pending-section">
          <div className="admin-section-header">
            <h2 className="admin-section-title">Pending Payments</h2>
            {pending.length > 0 && (
              <span className="pending-badge">{pending.length}</span>
            )}
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 16, flexWrap: "wrap" }}>
            {lastPolled && (
              <p className="admin-poll-note" style={{ margin: 0 }}>
                Auto-refreshes every 30s · last updated {lastPolled.toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit", second: "2-digit" })}
              </p>
            )}
            <button
              style={{
                background: "rgba(255,255,255,0.06)",
                border: "1px solid rgba(255,255,255,0.12)",
                borderRadius: 8,
                padding: "5px 14px",
                fontSize: "0.76rem",
                fontWeight: 700,
                color: "rgba(255,255,255,0.6)",
                cursor: refreshing ? "not-allowed" : "pointer",
                letterSpacing: "0.04em",
                whiteSpace: "nowrap",
              }}
              onClick={handleRefreshNow}
              disabled={refreshing}
            >
              {refreshing ? "Refreshing…" : "↻ Refresh Now"}
            </button>
          </div>

          {pending.length === 0 ? (
            <div className="admin-empty-state">No pending payments</div>
          ) : (
            <div className="pending-cards">
              {pending.map((p) => {
                const imgSrc = screenshotSrc(p.payment_screenshot_url);
                const busy = processingId === p.id;
                return (
                  <div key={p.id} className="pending-card">
                    <div className="pending-card-head">
                      <span className="pending-card-name">{p.attendee_name}</span>
                      <span className="pending-card-amount">₹{(p.amount / 100).toFixed(0)}</span>
                    </div>

                    <div className="pending-card-row">
                      <span className="pcr-label">Mobile</span>
                      <a href={`tel:${p.phone}`} className="pcr-value pcr-phone">{p.phone}</a>
                    </div>

                    <div className="pending-card-row">
                      <span className="pcr-label">Tickets</span>
                      <span className="pcr-value">{p.quantity}</span>
                    </div>

                    <div className="pending-card-row pending-card-row--utr">
                      <span className="pcr-label">Transaction ID</span>
                      {p.utr_reference ? (
                        <span className="pcr-value pcr-utr">{p.utr_reference}</span>
                      ) : (
                        <em className="pcr-value pcr-missing">not submitted</em>
                      )}
                    </div>

                    <div className="pending-card-row">
                      <span className="pcr-label">Submitted</span>
                      <span className="pcr-value pcr-date">
                        {new Date(p.created_at).toLocaleString("en-IN", { dateStyle: "short", timeStyle: "short" })}
                      </span>
                    </div>

                    {imgSrc && (
                      <div className="pending-card-screenshot" onClick={() => setExpandedImg(imgSrc)}>
                        {/* eslint-disable-next-line @next/next/no-img-element */}
                        <img src={imgSrc} alt="Payment screenshot" />
                        <div className="screenshot-tap-hint">Tap to expand</div>
                      </div>
                    )}

                    <div className="pending-card-actions">
                      <button
                        className="btn-approve"
                        onClick={() => handleApprove(p.id)}
                        disabled={!!processingId}
                      >
                        {busy ? "Issuing ticket…" : "✓ Approve"}
                      </button>
                      <button
                        className="btn-reject"
                        onClick={() => {
                          if (!window.confirm(`Reject payment from ${p.attendee_name}?`)) return;
                          handleReject(p.id);
                        }}
                        disabled={!!processingId}
                      >
                        ✕ Reject
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Ticket Search */}
        <div className="admin-search-card">
          <h2>Search Ticket</h2>
          <label className="form-label">
            Ticket code
            <input
              className="form-field"
              value={ticketCode}
              onChange={(e) => setTicketCode(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && searchTicket()}
              placeholder="HHC-000001"
            />
          </label>
          <button className="button" onClick={searchTicket} disabled={!ticketCode}>
            Search Ticket
          </button>

          {ticketResult && (
            <div className="ticket-result">
              <p><strong>Ticket code:</strong> {ticketResult.ticket_code}</p>
              <p><strong>Status:</strong> {ticketResult.status}</p>
              <p><strong>Attendee:</strong> {ticketResult.attendee_name}</p>
              <p><strong>Email:</strong> {ticketResult.email}</p>
              <p><strong>Phone:</strong> {ticketResult.phone}</p>
              <p><strong>Payment status:</strong> {ticketResult.payment_status}</p>
            </div>
          )}
        </div>
      </section>
    </main>
  );
}
