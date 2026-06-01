"use client";

import { FormEvent, useMemo, useState } from "react";

interface EventData {
  id: string;
  name: string;
  description: string | null;
  venue: string;
  event_date: string;
  capacity: number;
  ticket_price: number;
}

interface RegistrationFormProps {
  event: EventData;
}

const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export function RegistrationForm({ event }: RegistrationFormProps) {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [quantity, setQuantity] = useState(1);
  const [status, setStatus] = useState<string>("");
  const [message, setMessage] = useState<string>("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const ticketPrice = useMemo(() => `INR ${(event.ticket_price / 100).toFixed(0)}` , [event.ticket_price]);
  const totalPrice = useMemo(() => `INR ${((event.ticket_price * quantity) / 100).toFixed(0)}` , [event.ticket_price, quantity]);

  const validateForm = () => {
    if (!name.trim() || !email.trim() || !phone.trim()) {
      setMessage("Please fill in all fields.");
      return false;
    }
    if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email)) {
      setMessage("Please enter a valid email address.");
      return false;
    }
    const digits = phone.replace(/\D/g, "");
    if (digits.length < 10) {
      setMessage("Please enter a valid phone number.");
      return false;
    }
    return true;
  };

  const loadScript = async (src: string) => {
    if (document.querySelector(`script[src='${src}']`)) return true;
    return new Promise<boolean>((resolve) => {
      const script = document.createElement("script");
      script.src = src;
      script.onload = () => resolve(true);
      script.onerror = () => resolve(false);
      document.body.appendChild(script);
    });
  };

  const handleSubmit = async (eventSubmit: FormEvent<HTMLFormElement>) => {
    eventSubmit.preventDefault();
    setMessage("");
    setStatus("");

    if (!validateForm()) return;
    setIsSubmitting(true);

    try {
      const response = await fetch(`${apiUrl}/create-order`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          event_id: event.id,
          name,
          email,
          phone,
          quantity,
        }),
      });
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || "Unable to initiate payment.");
      }

      const scriptLoaded = await loadScript("https://checkout.razorpay.com/v1/checkout.js");
      if (!scriptLoaded || !(window as any).Razorpay) {
        throw new Error("Unable to load Razorpay checkout.");
      }

      const options = {
        key: data.payment_order.key_id,
        amount: data.payment_order.amount,
        currency: data.payment_order.currency,
        order_id: data.payment_order.razorpay_order_id,
        name: "Hyderabad Hangama Club",
        description: event.name,
        prefill: {
          name,
          email,
          contact: phone,
        },
        handler: async (response: any) => {
          try {
            const verifyResponse = await fetch(`${apiUrl}/payments/verify`, {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({
                registration_id: data.id,
                razorpay_order_id: response.razorpay_order_id,
                razorpay_payment_id: response.razorpay_payment_id,
                razorpay_signature: response.razorpay_signature,
              }),
            });
            const verifyData = await verifyResponse.json();
            if (!verifyResponse.ok) {
              throw new Error(verifyData.detail || "Payment verification failed.");
            }
            setStatus("success");
            setMessage(`Payment completed. Ticket code: ${verifyData.ticket_code}`);
          } catch (err: any) {
            setStatus("error");
            setMessage(err.message || "Payment verification failed.");
          }
        },
        modal: {
          ondismiss: () => {
            setStatus("error");
            setMessage("Payment window was closed before completion.");
          },
        },
      };

      const rzp = new (window as any).Razorpay(options);
      rzp.open();
    } catch (err: any) {
      setStatus("error");
      setMessage(err.message || "Unable to complete registration.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <form className="form-card" onSubmit={handleSubmit}>
      <label className="form-label">
        Name
        <input className="form-field" value={name} onChange={(e) => setName(e.target.value)} required />
      </label>
      <label className="form-label">
        Email
        <input className="form-field" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
      </label>
      <label className="form-label">
        Mobile number
        <input className="form-field" value={phone} onChange={(e) => setPhone(e.target.value)} required />
      </label>
      <label className="form-label">
        Number of tickets
        <input
          className="form-field"
          type="number"
          min={1}
          max={10}
          value={quantity}
          onChange={(e) => setQuantity(Number(e.target.value))}
          required
        />
      </label>
      <div className="form-row">
        <span>Price per ticket: {ticketPrice}</span>
        <span>Total: {totalPrice}</span>
      </div>
      <button className="button" type="submit" disabled={isSubmitting}>
        {isSubmitting ? "Processing…" : "Register & Pay"}
      </button>
      {message && <p className={status === "success" ? "message-success" : "message-error"}>{message}</p>}
    </form>
  );
}
