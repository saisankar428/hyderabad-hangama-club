"use client";

import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";

interface EventData {
  id: string;
  name: string;
  description: string | null;
  venue: string;
  event_date: string;
  capacity: number;
  ticket_price: number;
}

/* ── Zod Schema ──────────────────────────────────────────────── */

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

/* ── Types ───────────────────────────────────────────────────── */

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

/* ── Constants ───────────────────────────────────────────────── */

const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

/* ── Helpers ─────────────────────────────────────────────────── */

function FieldError({ message }: { message?: string }) {
  if (!message) return null;
  return <p className="form-error">{message}</p>;
}

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

/* ── Confirmation Screen ─────────────────────────────────────── */

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
        Show the QR code above at the venue entrance. This ticket is valid for{" "}
        <strong>one-time entry only</strong>. Do not share it.
      </div>
    </div>
  );
}

/* ── Registration Form ───────────────────────────────────────── */

export function RegistrationForm({ event }: { event: EventData }) {
  const [submitError, setSubmitError] = useState("");
  const [confirmation, setConfirmation] = useState<ConfirmationData | null>(null);

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

  const onSubmit = async (data: FormValues) => {
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
        prefill: {
          name: data.fullName,
          email: data.email,
          contact: data.mobile,
        },
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
              ticket_code:  vData.ticket_code,
              qr_code_url:  vData.qr_code_url ?? "",
              attendee_name: vData.attendee_name ?? data.fullName,
              email:        vData.email ?? data.email,
              quantity:     vData.quantity ?? data.tickets,
              event_name:   vData.event_name ?? event.name,
              event_date:   vData.event_date ?? "",
              event_venue:  vData.event_venue ?? event.venue,
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

  if (confirmation) {
    return <ConfirmationScreen data={confirmation} />;
  }

  return (
    <form className="form-card" onSubmit={handleSubmit(onSubmit)} noValidate>

      {/* Full Name */}
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

      {/* Mobile Number */}
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

      {/* WhatsApp Number */}
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

      {/* Email */}
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

      {/* Number of Tickets */}
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

      {/* Total calculation */}
      {ticketCount > 0 && (
        <div className="form-total">
          <span className="form-total-label">
            {ticketCount}&nbsp;{ticketCount === 1 ? "Ticket" : "Tickets"} × ₹{pricePerTicketRupees}
          </span>
          <span className="form-total-amount">₹{totalRupees}</span>
        </div>
      )}

      {/* Special Notes */}
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

      <button
        type="submit"
        className="button"
        disabled={!isValid || isSubmitting}
      >
        {isSubmitting ? "Processing…" : "Proceed to Payment"}
      </button>

      {submitError && <p className="message-error">{submitError}</p>}
    </form>
  );
}
