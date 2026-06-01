"use client";

import { useEffect, useRef, useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";

/* ── Event shape (passed from parent page) ────────────────────── */

interface EventData {
  id: string;
  name: string;
  description: string | null;
  venue: string;
  event_date: string;
  capacity: number;
  ticket_price: number;
}

/* ── Zod schema ───────────────────────────────────────────────── */

const mobileCheck = (val: string) => {
  const stripped = val.replace(/[\s\-()]/g, "");
  return /^(\+?91)?[6-9]\d{9}$/.test(stripped);
};

const schema = z.object({
  fullName: z.string().min(1, "Full name is required"),
  mobile: z
    .string()
    .min(1, "Mobile number is required")
    .refine(mobileCheck, "Enter a valid 10-digit mobile number"),
  whatsapp: z
    .string()
    .min(1, "WhatsApp number is required")
    .refine(mobileCheck, "Enter a valid 10-digit WhatsApp number"),
  email: z
    .string()
    .min(1, "Email address is required")
    .email("Enter a valid email address"),
  tickets: z.coerce
    .number()
    .int("Must be a whole number")
    .min(1, "At least 1 ticket required")
    .max(10, "Maximum 10 tickets per booking"),
  notes: z.string().optional(),
});

type FormValues = z.infer<typeof schema>;

/* ── Internal state types ─────────────────────────────────────── */

interface ConfirmationData {
  ticket_code: string;
  qr_code_url: string;
  attendee_name: string;
  email: string;
  quantity: number;
  event_name: string;
  event_date: string;
  event_venue: string;
}

interface UpiOrderData {
  registration_id: string;
  order_ref: string;
  amount: number;
  upi_id: string;
  upi_link: string;
  upi_qr_base64: string;
  attendee_email: string;
  event_name: string;
  event_venue: string;
  quantity: number;
}

interface PendingData {
  order_ref: string;
  message: string;
  email: string;
}

/* ── Constants ────────────────────────────────────────────────── */

const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

/** sessionStorage key for persisting the active UPI order across app-switches */
const SESSION_KEY = "hhc_upi_order";

/* ── Helper: field error ──────────────────────────────────────── */

function FieldError({ message }: { message?: string }) {
  if (!message) return null;
  return <p className="form-error">{message}</p>;
}

/* ── Helper: load external script ────────────────────────────── */

const loadScript = (src: string) => {
  if (document.querySelector(`script[src='${src}']`)) return Promise.resolve(true);
  return new Promise<boolean>((resolve) => {
    const s = document.createElement("script");
    s.src = src;
    s.onload = () => resolve(true);
    s.onerror = () => resolve(false);
    document.body.appendChild(s);
  });
};

/* ── Confirmation Screen (ticket issued immediately) ─────────── */

function ConfirmationScreen({ data }: { data: ConfirmationData }) {
  return (
    <div className="confirm-wrap">
      <div className="confirm-icon">✓</div>
      <h3 className="confirm-title">Booking Confirmed!</h3>
      <p className="confirm-sub">
        Your ticket is on its way to <strong>{data.email}</strong> and your WhatsApp.
      </p>

      <div className="confirm-ticket-box">
        <p className="confirm-label">TICKET CODE</p>
        <p className="confirm-code">{data.ticket_code}</p>
      </div>

      {data.qr_code_url && (
        <div className="confirm-qr-wrap">
          <p className="confirm-label">SCAN AT ENTRY</p>
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src={data.qr_code_url}
            alt={`QR code for ticket ${data.ticket_code}`}
            className="confirm-qr"
          />
        </div>
      )}

      <table className="confirm-table">
        <tbody>
          <tr>
            <td className="confirm-table-key">Event</td>
            <td className="confirm-table-val">{data.event_name}</td>
          </tr>
          <tr>
            <td className="confirm-table-key">Date</td>
            <td className="confirm-table-val">{data.event_date}</td>
          </tr>
          <tr>
            <td className="confirm-table-key">Venue</td>
            <td className="confirm-table-val">{data.event_venue}</td>
          </tr>
          <tr>
            <td className="confirm-table-key">Name</td>
            <td className="confirm-table-val">{data.attendee_name}</td>
          </tr>
          <tr>
            <td className="confirm-table-key">Tickets</td>
            <td className="confirm-table-val">{data.quantity}</td>
          </tr>
        </tbody>
      </table>

      <div className="confirm-notice">
        Show the QR code at the venue entrance. This ticket is valid for{" "}
        <strong>one-time entry only</strong>. Do not share it.
      </div>
    </div>
  );
}

/* ── Pending Verification Screen (UPI payment submitted) ─────── */

function PendingScreen({ data, onBack }: { data: PendingData; onBack: () => void }) {
  return (
    <div className="confirm-wrap">
      <div
        className="confirm-icon"
        style={{ background: "linear-gradient(135deg,#d97706,#b45309)" }}
      >
        ⏳
      </div>
      <h3 className="confirm-title">Payment Submitted!</h3>
      <p className="confirm-sub">{data.message}</p>

      <div className="confirm-ticket-box">
        <p className="confirm-label">ORDER REFERENCE</p>
        <p className="confirm-code" style={{ fontSize: "1rem", letterSpacing: "0.06em" }}>
          {data.order_ref}
        </p>
      </div>

      <div className="confirm-notice">
        Your ticket will be sent to <strong>{data.email}</strong> once our team verifies
        your UPI payment. Keep your order reference for follow-up if needed.
      </div>

      {/* Re-submission escape hatch — backend allows overwriting UTR while still pending_verification */}
      <button type="button" className="upi-back-link" onClick={onBack}>
        Entered wrong details? Update payment proof →
      </button>
    </div>
  );
}

/* ── UPI Payment Screen ───────────────────────────────────────── */

function UpiPaymentScreen({
  upiData,
  onSubmit,
  returnFocus = false,
}: {
  upiData: UpiOrderData;
  onSubmit: (utr: string, screenshot: File) => Promise<void>;
  /** True when the page was reloaded mid-payment (sessionStorage restore). */
  returnFocus?: boolean;
}) {
  const [utr, setUtr] = useState("");
  const [screenshot, setScreenshot] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [retryCount, setRetryCount] = useState(0);
  // SSR-safe mobile detection — starts false (server), updated after mount
  const [isMobile, setIsMobile] = useState(false);
  // True after user returns from a UPI app — triggers the post-payment banner + auto-focus
  const [justReturned, setJustReturned] = useState(returnFocus);
  // Client-side fallback QR (used only when server doesn't provide upi_qr_base64)
  const [fallbackQr, setFallbackQr] = useState<string | null>(null);

  const fileInputRef  = useRef<HTMLInputElement>(null);
  const utrInputRef   = useRef<HTMLInputElement>(null);
  // Set to true when user taps a payment app button — gates the visibilitychange handler
  const paymentTappedRef = useRef(false);

  const amountRupees = Math.round(upiData.amount / 100);

  // Detect Android / iOS after mount (navigator is browser-only)
  useEffect(() => {
    setIsMobile(/Android|iPhone|iPad|iPod/i.test(navigator.userAgent));
  }, []);

  // visibilitychange — fires when user returns to the browser from GPay / PhonePe / etc.
  // Only acts if the user actually tapped one of our payment app buttons.
  useEffect(() => {
    const onVisible = () => {
      if (document.visibilityState === "visible" && paymentTappedRef.current) {
        paymentTappedRef.current = false;
        setJustReturned(true);
        // Brief delay so the DOM re-paints before we scroll and focus
        setTimeout(() => {
          utrInputRef.current?.scrollIntoView({ behavior: "smooth", block: "center" });
          utrInputRef.current?.focus();
        }, 300);
      }
    };
    document.addEventListener("visibilitychange", onVisible);
    return () => document.removeEventListener("visibilitychange", onVisible);
  }, []);

  // If the page was reloaded mid-payment (returnFocus), auto-scroll + focus UTR on mount
  useEffect(() => {
    if (returnFocus) {
      setTimeout(() => {
        utrInputRef.current?.scrollIntoView({ behavior: "smooth", block: "center" });
        utrInputRef.current?.focus();
      }, 500);
    }
  }, [returnFocus]);

  // Client-side QR fallback: generate from NEXT_PUBLIC_UPI_ID when server QR is absent.
  // The server-generated QR (upi_qr_base64) is always preferred because it embeds the
  // order reference (tr=...) enabling payment reconciliation.
  useEffect(() => {
    if (upiData.upi_qr_base64) return; // server QR present — nothing to do

    const upiId = process.env.NEXT_PUBLIC_UPI_ID;
    if (!upiId) return;

    const fallbackLink = [
      `upi://pay?pa=${encodeURIComponent(upiId)}`,
      `pn=${encodeURIComponent("Hyderabad Hangama Club")}`,
      `am=${(upiData.amount / 100).toFixed(2)}`,
      `cu=INR`,
    ].join("&");

    import("qrcode")
      .then((QRCode) =>
        QRCode.toDataURL(fallbackLink, { width: 200, margin: 2, color: { dark: "#000", light: "#fff" } })
      )
      .then(setFallbackQr)
      .catch(() => { /* qrcode unavailable — UPI ID copy remains as fallback */ });
  }, [upiData.upi_qr_base64, upiData.amount]);

  // Derive app-specific deep links from the existing upi_link.
  // The server returns:  upi://pay?pa=...&pn=...&am=...&tn=...&tr=...&cu=INR
  // GPay, PhonePe and Paytm all accept the same query params under their own scheme.
  const _upiParams  = upiData.upi_link.replace("upi://pay?", "");
  const gpayLink    = `gpay://upi/pay?${_upiParams}`;
  const phonepeLink = `phonepe://pay?${_upiParams}`;
  const paytmLink   = `paytmmp://pay?${_upiParams}`;

  // Final QR source: server base64 > client-side fallback > null (show UPI ID only)
  const qrSrc = upiData.upi_qr_base64
    ? `data:image/png;base64,${upiData.upi_qr_base64}`
    : fallbackQr ?? null;

  // Called on every payment app button tap — arms the visibilitychange handler
  const handleAppButtonClick = () => { paymentTappedRef.current = true; };

  // Revoke object URL on unmount to avoid memory leak
  useEffect(() => {
    return () => {
      if (previewUrl) URL.revokeObjectURL(previewUrl);
    };
  }, [previewUrl]);

  const copyUpiId = async () => {
    try {
      await navigator.clipboard.writeText(upiData.upi_id);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // clipboard unavailable — user can copy manually
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    // Client-side validation before upload
    if (!["image/jpeg", "image/png", "image/webp", "image/gif"].includes(file.type)) {
      setError("Only JPEG, PNG, WEBP or GIF images are allowed.");
      return;
    }
    if (file.size > 5 * 1024 * 1024) {
      setError("Screenshot must be under 5 MB.");
      return;
    }
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    setScreenshot(file);
    setPreviewUrl(URL.createObjectURL(file));
    setError("");
  };

  const clearScreenshot = () => {
    setScreenshot(null);
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    setPreviewUrl(null);
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!utr.trim()) {
      setError("Please enter your Transaction ID.");
      return;
    }
    if (!screenshot) {
      setError("Please upload your payment screenshot.");
      return;
    }
    setError("");
    setSubmitting(true);
    try {
      await onSubmit(utr.trim(), screenshot);
    } catch (err: any) {
      setRetryCount((n) => n + 1);
      setError(err.message || "Failed to submit. Please try again.");
    } finally {
      setSubmitting(false);
    }
  };

  const canSubmit = utr.trim().length >= 6 && screenshot !== null && !submitting;

  return (
    <div className="upi-screen">

      {/* Payment summary */}
      <div className="upi-summary-bar">
        <p className="upi-summary-event">{upiData.event_name}</p>
        {upiData.event_venue && (
          <p className="upi-summary-venue">📍 {upiData.event_venue}</p>
        )}
        <p className="upi-summary-amount">₹{amountRupees}</p>
        <p className="upi-summary-meta">
          {upiData.quantity} {upiData.quantity === 1 ? "Ticket" : "Tickets"} · {upiData.upi_id}
        </p>
      </div>

      {/* ─── Step 1: Pay ─── */}
      <div className="upi-step-header">
        <span className="upi-step-num">1</span>
        <span className="upi-step-title">
          {isMobile ? "Open UPI App & Pay" : "Scan & Pay"}
        </span>
      </div>

      {/*
        Mobile: show branded app shortcut buttons above the QR.
        Desktop: app URI schemes don't work in desktop browsers — show QR only.
      */}
      {isMobile && (
        <div className="upi-app-buttons">
          <a href={gpayLink} className="upi-app-btn upi-app-btn--gpay" onClick={handleAppButtonClick}>
            <span className="upi-app-btn-icon">G</span>
            <span>GPay</span>
          </a>
          <a href={phonepeLink} className="upi-app-btn upi-app-btn--phonepe" onClick={handleAppButtonClick}>
            <span className="upi-app-btn-icon">Pe</span>
            <span>PhonePe</span>
          </a>
          <a href={paytmLink} className="upi-app-btn upi-app-btn--paytm" onClick={handleAppButtonClick}>
            <span className="upi-app-btn-icon">P</span>
            <span>Paytm</span>
          </a>
          <a href={upiData.upi_link} className="upi-app-btn upi-app-btn--any" onClick={handleAppButtonClick}>
            <span className="upi-app-btn-icon">↗</span>
            <span>Other</span>
          </a>
        </div>
      )}

      <div className="upi-qr-block">
        {/* On mobile the QR is secondary (user pays via app buttons above) */}
        {isMobile && <p className="upi-qr-or-label">or scan QR with another phone</p>}

        {qrSrc ? (
          /* eslint-disable-next-line @next/next/no-img-element */
          <img
            src={qrSrc}
            alt="UPI payment QR code"
            className="upi-qr-img"
            style={isMobile ? { width: 160, height: 160 } : undefined}
          />
        ) : (
          /* No QR available — show UPI ID prominently so user can type it manually */
          <div className="upi-qr-placeholder">
            <p className="upi-qr-placeholder-label">UPI ID</p>
            <p className="upi-qr-placeholder-id">{upiData.upi_id}</p>
            <p className="upi-qr-placeholder-hint">Open your UPI app and pay to the ID above</p>
          </div>
        )}

        <div className="upi-id-row">
          <span className="upi-id-value">{upiData.upi_id}</span>
          <button type="button" className="upi-copy-btn" onClick={copyUpiId}>
            {copied ? "Copied!" : "Copy"}
          </button>
        </div>
      </div>

      {/* Generic deep link — useful on desktop if user has a UPI browser extension;
          hidden on mobile because the branded buttons above cover every major app */}
      {!isMobile && (
        <a href={upiData.upi_link} className="upi-app-link">
          Open UPI App →
        </a>
      )}

      <ol className="upi-instructions">
        <li>
          <span className="upi-instr-num">1</span>
          Scan the QR code or copy the UPI ID above
        </li>
        <li>
          <span className="upi-instr-num">2</span>
          Enter the exact amount <strong style={{ color: "var(--gold)" }}>₹{amountRupees}</strong>
        </li>
        <li>
          <span className="upi-instr-num">3</span>
          Complete the payment in your UPI app
        </li>
        <li>
          <span className="upi-instr-num">4</span>
          Note down your <strong>Transaction ID</strong> (shown after payment)
        </li>
        <li>
          <span className="upi-instr-num">5</span>
          Take a screenshot of the payment confirmation
        </li>
      </ol>

      {/* Divider */}
      <div className="upi-divider">
        <span className="upi-divider-text">After paying, confirm below</span>
      </div>

      {/* ─── Step 2: Confirm ─── */}
      <form onSubmit={handleSubmit} noValidate>
        <div className="upi-step-header">
          <span className="upi-step-num">2</span>
          <span className="upi-step-title">Confirm Your Payment</span>
        </div>

        {/* Post-payment return banner — shown when user comes back from a UPI app */}
        {justReturned && (
          <div className="upi-return-banner" role="status">
            <span className="upi-return-icon">✓</span>
            <span>Payment done? Enter your Transaction ID below.</span>
          </div>
        )}

        {/* Transaction ID */}
        <div className="form-group">
          <label className="form-label" htmlFor="utr">
            Transaction ID <span className="form-required">*</span>
          </label>
          <input
            ref={utrInputRef}
            id="utr"
            className={`form-field${error && !utr.trim() ? " form-field--error" : ""}`}
            placeholder="e.g. 412345678901"
            value={utr}
            onChange={(e) => setUtr(e.target.value)}
            autoComplete="off"
            inputMode="text"
          />
          <p style={{
            margin: "0",
            fontSize: "0.72rem",
            color: "rgba(255,255,255,0.28)",
            lineHeight: 1.4,
          }}>
            Found in your UPI app under payment history
          </p>
        </div>

        {/* Screenshot upload */}
        <div className="form-group">
          <label className="form-label">
            Payment Screenshot <span className="form-required">*</span>
          </label>

          {!screenshot ? (
            <div className="screenshot-zone">
              <input
                ref={fileInputRef}
                type="file"
                accept="image/jpeg,image/png,image/webp,image/gif"
                onChange={handleFileChange}
                tabIndex={0}
              />
              <span className="screenshot-zone-icon">📎</span>
              <p className="screenshot-zone-text">Tap to upload payment screenshot</p>
              <p className="screenshot-zone-hint">JPEG · PNG · WEBP &nbsp;·&nbsp; Max 5 MB</p>
            </div>
          ) : (
            <div className="screenshot-preview">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src={previewUrl!}
                alt="Payment screenshot preview"
                className="screenshot-preview-img"
              />
              <div className="screenshot-preview-footer">
                <span className="screenshot-preview-name">{screenshot.name}</span>
                <button
                  type="button"
                  className="screenshot-remove-btn"
                  onClick={clearScreenshot}
                >
                  Remove
                </button>
              </div>
            </div>
          )}
        </div>

        {error && (
          <div style={{
            background: "rgba(248,113,113,0.08)",
            border: "1px solid rgba(248,113,113,0.28)",
            borderRadius: 10,
            padding: "12px 14px",
            marginBottom: 10,
          }}>
            <p className="message-error" style={{ margin: 0 }}>{error}</p>
            {retryCount > 0 && (
              <p style={{ margin: "6px 0 0", fontSize: "0.74rem", color: "rgba(255,255,255,0.38)" }}>
                You can retry — your booking slot is held.
              </p>
            )}
          </div>
        )}

        <button type="submit" className="button" disabled={!canSubmit}>
          {submitting
            ? <span style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: 8 }}>
                <span style={{
                  width: 16, height: 16, border: "2px solid rgba(0,0,0,0.3)",
                  borderTop: "2px solid #000", borderRadius: "50%",
                  display: "inline-block", animation: "spin 0.7s linear infinite"
                }} />
                Submitting…
              </span>
            : retryCount > 0 ? "Retry Submission" : "Submit Payment"}
        </button>

        <p className="upi-secure-note">
          🔒 Your booking is reserved. Ticket will be sent once payment is verified.
        </p>
      </form>
    </div>
  );
}

/* ── Registration Form ────────────────────────────────────────── */

export function RegistrationForm({ event }: { event: EventData }) {
  const [submitError, setSubmitError] = useState("");
  const [confirmation, setConfirmation] = useState<ConfirmationData | null>(null);
  const [upiOrder, setUpiOrder] = useState<UpiOrderData | null>(null);
  const [pending, setPending] = useState<PendingData | null>(null);
  // True when the page was reloaded mid-payment (e.g. browser killed while user was in GPay)
  const [restoredFromSession, setRestoredFromSession] = useState(false);
  // Prevent re-submission once order creation succeeds
  const orderCreated = useRef(false);

  // ── Session storage: restore UPI order if the page reloaded mid-payment ──────
  // Mobile browsers can kill the page while the user is inside GPay / PhonePe.
  // We persist the order data so the payment screen re-appears on reload.
  useEffect(() => {
    try {
      const saved = sessionStorage.getItem(SESSION_KEY);
      if (saved) {
        const order = JSON.parse(saved) as UpiOrderData;
        setUpiOrder(order);
        setRestoredFromSession(true);
        orderCreated.current = true; // guard against re-registration
      }
    } catch {
      sessionStorage.removeItem(SESSION_KEY);
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // Persist upiOrder whenever it changes
  useEffect(() => {
    if (upiOrder) {
      try { sessionStorage.setItem(SESSION_KEY, JSON.stringify(upiOrder)); } catch { /* quota */ }
    }
  }, [upiOrder]);

  // Clear persisted order once payment is confirmed (terminal state)
  useEffect(() => {
    if (confirmation) sessionStorage.removeItem(SESSION_KEY);
  }, [confirmation]);

  const pricePerTicketPaise = event.ticket_price;
  const pricePerTicketRupees = Math.round(pricePerTicketPaise / 100);

  const {
    register,
    handleSubmit,
    watch,
    formState: { errors, isValid, isSubmitting },
  } = useForm<FormValues>({
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    resolver: zodResolver(schema) as any,
    mode: "onChange",
    defaultValues: { tickets: 1, notes: "" },
  });

  const ticketCount = Number(watch("tickets")) || 0;
  const totalRupees = pricePerTicketRupees * ticketCount;

  /* ── Form submit → create order ── */
  const onSubmit = async (data: FormValues) => {
    // Guard: prevent duplicate order creation if already submitted
    if (orderCreated.current) return;
    setSubmitError("");
    try {
      const res = await fetch(`${apiUrl}/create-order`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          event_id: event.id,
          name: data.fullName,
          email: data.email,
          phone: data.mobile,
          whatsapp: data.whatsapp,
          notes: data.notes ?? "",
          quantity: data.tickets,
        }),
      });
      const orderData = await res.json();
      if (!res.ok) throw new Error(orderData.detail || "Unable to initiate payment.");

      // UPI mode — server returned a UPI QR order
      if (orderData.payment_order?.upi_qr_base64) {
        orderCreated.current = true;
        setUpiOrder({
          registration_id: orderData.id,
          order_ref: orderData.payment_order.order_ref,
          amount: orderData.payment_order.amount,
          upi_id: orderData.payment_order.upi_id,
          upi_link: orderData.payment_order.upi_link,
          upi_qr_base64: orderData.payment_order.upi_qr_base64,
          attendee_email: data.email,
          event_name: event.name,
          event_venue: event.venue,
          quantity: data.tickets,
        });
        return;
      }

      // Razorpay mode (preserved for when account is restored)
      const ok = await loadScript("https://checkout.razorpay.com/v1/checkout.js");
      if (!ok || !(window as any).Razorpay)
        throw new Error("Unable to load payment gateway. Please try again.");

      const rzp = new (window as any).Razorpay({
        key: orderData.payment_order.key_id,
        amount: orderData.payment_order.amount,
        currency: orderData.payment_order.currency,
        order_id: orderData.payment_order.razorpay_order_id,
        name: "Hyderabad Hangama Club",
        description: event.name,
        prefill: { name: data.fullName, email: data.email, contact: data.mobile },
        handler: async (response: any) => {
          try {
            const vRes = await fetch(`${apiUrl}/payments/verify`, {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({
                registration_id: orderData.id,
                razorpay_order_id: response.razorpay_order_id,
                razorpay_payment_id: response.razorpay_payment_id,
                razorpay_signature: response.razorpay_signature,
              }),
            });
            const vData = await vRes.json();
            if (!vRes.ok) throw new Error(vData.detail || "Payment verification failed.");
            setConfirmation({
              ticket_code: vData.ticket_code,
              qr_code_url: vData.qr_code_url ?? "",
              attendee_name: vData.attendee_name ?? data.fullName,
              email: vData.email ?? data.email,
              quantity: vData.quantity ?? data.tickets,
              event_name: vData.event_name ?? event.name,
              event_date: vData.event_date ?? "",
              event_venue: vData.event_venue ?? event.venue,
            });
          } catch (err: any) {
            setSubmitError(err.message || "Payment verification failed.");
          }
        },
        modal: {
          ondismiss: () =>
            setSubmitError("Payment window closed before completion. Please try again."),
        },
      });
      rzp.open();
    } catch (err: any) {
      setSubmitError(err.message || "Unable to complete registration.");
    }
  };

  /* ── UPI confirmation submit (FormData multipart) ── */
  const submitUpi = async (utr: string, screenshot: File) => {
    if (!upiOrder) return;

    const formData = new FormData();
    formData.append("registration_id", upiOrder.registration_id);
    formData.append("order_ref", upiOrder.order_ref);
    formData.append("utr_reference", utr);
    formData.append("screenshot", screenshot);

    const res = await fetch(`${apiUrl}/payments/submit-utr`, {
      method: "POST",
      body: formData,
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Failed to submit payment details.");

    setPending({
      order_ref: upiOrder.order_ref,
      message: data.message,
      email: upiOrder.attendee_email,
    });
    // Keep upiOrder alive so the user can return via PendingScreen's "Update payment proof" button.
    // The backend allows re-submission while status = pending_verification (overwrites previous UTR).
  };

  /* ── Render state machine ── */
  if (confirmation) return <ConfirmationScreen data={confirmation} />;
  if (pending) return <PendingScreen data={pending} onBack={() => setPending(null)} />;
  if (upiOrder) return <UpiPaymentScreen upiData={upiOrder} onSubmit={submitUpi} returnFocus={restoredFromSession} />;

  /* ── Registration form ── */
  return (
    <form className="form-card" onSubmit={handleSubmit(onSubmit)} noValidate>

      <div className="form-group">
        <label className="form-label" htmlFor="fullName">
          Full Name <span className="form-required">*</span>
        </label>
        <input
          id="fullName"
          className={`form-field${errors.fullName ? " form-field--error" : ""}`}
          placeholder="Enter your full name"
          autoComplete="name"
          {...register("fullName")}
        />
        <FieldError message={errors.fullName?.message} />
      </div>

      <div className="form-group">
        <label className="form-label" htmlFor="mobile">
          Mobile Number <span className="form-required">*</span>
        </label>
        <input
          id="mobile"
          className={`form-field${errors.mobile ? " form-field--error" : ""}`}
          placeholder="9876543210"
          inputMode="tel"
          autoComplete="tel"
          {...register("mobile")}
        />
        <FieldError message={errors.mobile?.message} />
      </div>

      <div className="form-group">
        <label className="form-label" htmlFor="whatsapp">
          WhatsApp Number <span className="form-required">*</span>
        </label>
        <input
          id="whatsapp"
          className={`form-field${errors.whatsapp ? " form-field--error" : ""}`}
          placeholder="9876543210"
          inputMode="tel"
          {...register("whatsapp")}
        />
        <FieldError message={errors.whatsapp?.message} />
      </div>

      <div className="form-group">
        <label className="form-label" htmlFor="email">
          Email Address <span className="form-required">*</span>
        </label>
        <input
          id="email"
          type="email"
          className={`form-field${errors.email ? " form-field--error" : ""}`}
          placeholder="you@example.com"
          autoComplete="email"
          {...register("email")}
        />
        <FieldError message={errors.email?.message} />
      </div>

      <div className="form-group">
        <label className="form-label" htmlFor="tickets">
          Number of Tickets <span className="form-required">*</span>
        </label>
        <input
          id="tickets"
          type="number"
          min={1}
          max={10}
          inputMode="numeric"
          pattern="[0-9]*"
          className={`form-field${errors.tickets ? " form-field--error" : ""}`}
          {...register("tickets")}
        />
        <FieldError message={errors.tickets?.message} />
      </div>

      {ticketCount > 0 && (
        <div className="form-total">
          <span className="form-total-label">
            {ticketCount}&nbsp;{ticketCount === 1 ? "Ticket" : "Tickets"} × ₹{pricePerTicketRupees}
          </span>
          <span className="form-total-amount">₹{totalRupees}</span>
        </div>
      )}

      <div className="form-group">
        <label className="form-label" htmlFor="notes">
          Special Notes
        </label>
        <textarea
          id="notes"
          className="form-field form-textarea"
          placeholder="Any special requests or dietary requirements…"
          rows={3}
          {...register("notes")}
        />
      </div>

      <button type="submit" className="button" disabled={!isValid || isSubmitting}>
        {isSubmitting ? "Processing…" : "Proceed to Payment"}
      </button>

      {submitError && <p className="message-error">{submitError}</p>}
    </form>
  );
}
