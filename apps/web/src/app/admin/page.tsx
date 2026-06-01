"use client";

import { useState } from "react";

const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function AdminPage() {
  const [adminKey, setAdminKey] = useState("");
  const [metrics, setMetrics] = useState<null | {
    total_registrations: number;
    total_revenue: number;
    total_checked_in: number;
  }>(null);
  const [ticketCode, setTicketCode] = useState("");
  const [ticketResult, setTicketResult] = useState<any>(null);
  const [message, setMessage] = useState<string>("");

  const loadMetrics = async () => {
    if (!adminKey) {
      setMessage("Admin key is required.");
      return;
    }

    setMessage("");
    try {
      const response = await fetch(`${apiUrl}/admin/metrics`, {
        headers: { "X-ADMIN-KEY": adminKey },
      });
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || "Unable to load metrics.");
      }
      setMetrics(data);
      setMessage("");
    } catch (err: any) {
      setMessage(err.message || "Error loading metrics.");
      setMetrics(null);
    }
  };

  const searchTicket = async () => {
    if (!adminKey || !ticketCode) {
      setMessage("Admin key and ticket code are required.");
      return;
    }

    setMessage("");
    try {
      const response = await fetch(`${apiUrl}/admin/tickets/search?ticket_code=${encodeURIComponent(ticketCode)}`, {
        headers: { "X-ADMIN-KEY": adminKey },
      });
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || "Ticket not found.");
      }
      setTicketResult(data);
    } catch (err: any) {
      setMessage(err.message || "Error searching ticket.");
      setTicketResult(null);
    }
  };

  return (
    <main className="page-shell">
      <section className="admin-section">
        <h1>Admin Dashboard</h1>
        <p>Protected metrics and ticket lookup.</p>

        <label className="form-label">
          Admin key
          <input
            className="form-field"
            type="password"
            value={adminKey}
            onChange={(event) => setAdminKey(event.target.value)}
            placeholder="Enter admin key"
          />
        </label>
        <button className="button" onClick={loadMetrics} disabled={!adminKey}>
          Load Metrics
        </button>

        {metrics && (
          <div className="metrics-grid">
            <div className="metric-card">
              <span>Total registrations</span>
              <strong>{metrics.total_registrations}</strong>
            </div>
            <div className="metric-card">
              <span>Total revenue</span>
              <strong>INR {(metrics.total_revenue / 100).toFixed(0)}</strong>
            </div>
            <div className="metric-card">
              <span>Checked-in users</span>
              <strong>{metrics.total_checked_in}</strong>
            </div>
          </div>
        )}

        <div className="admin-search-card">
          <h2>Search ticket</h2>
          <label className="form-label">
            Ticket code
            <input
              className="form-field"
              value={ticketCode}
              onChange={(event) => setTicketCode(event.target.value)}
              placeholder="HHC-000001"
            />
          </label>
          <button className="button" onClick={searchTicket} disabled={!adminKey || !ticketCode}>
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

        {message && <p className="message-error">{message}</p>}
      </section>
    </main>
  );
}
