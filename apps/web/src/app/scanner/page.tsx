"use client";

import { useEffect, useRef, useState } from "react";

const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function ScannerPage() {
  const [status, setStatus] = useState("");
  const [message, setMessage] = useState("");
  const [ticketCode, setTicketCode] = useState("");
  const [error, setError] = useState<string | null>(null);
  const scannerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const loadScanner = async () => {
      if (!scannerRef.current) return;

      try {
        const module = await import("html5-qrcode");
        const Html5Qrcode = module.Html5Qrcode;
        const html5QrCode = new Html5Qrcode("scanner-container");

        await html5QrCode.start(
          { facingMode: { exact: "environment" } },
          {
            fps: 10,
            qrbox: 250,
          },
          async (decodedText: string) => {
            setTicketCode(decodedText);
            await html5QrCode.stop();
            validateTicket(decodedText);
          },
          (errorMessage: string) => {
            console.debug("QR scan error", errorMessage);
          }
        );
      } catch (err) {
        setError("Camera scanner unavailable. Please enter the ticket code manually.");
      }
    };

    loadScanner();
  }, []);

  const validateTicket = async (code: string) => {
    if (!code) {
      setMessage("Please provide a ticket code.");
      return;
    }

    try {
      const response = await fetch(`${apiUrl}/scanner/scan`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ticket_code: code }),
      });
      const result = await response.json();
      if (!response.ok) {
        setStatus("INVALID");
        setMessage(result.detail || "Ticket validation failed.");
        return;
      }

      setStatus(result.valid ? "VALID" : result.already_scanned ? "USED" : "INVALID");
      setMessage(result.message || "Scan completed.");
    } catch (err) {
      setStatus("INVALID");
      setMessage("Unable to validate ticket.");
    }
  };

  return (
    <main className="page-shell">
      <section className="scanner-section">
        <h1>Ticket Scanner</h1>
        <p>Scan a ticket QR code or enter the ticket code manually.</p>

        <div ref={scannerRef} id="scanner-container" className="scanner-box" />
        <label className="form-label">
          Ticket code
          <input
            className="form-field"
            value={ticketCode}
            onChange={(event) => setTicketCode(event.target.value)}
            placeholder="HHC-000001"
          />
        </label>
        <button className="button" onClick={() => validateTicket(ticketCode)}>
          Validate Ticket
        </button>

        {status && (
          <div className={`status-box ${status.toLowerCase()}`}>
            <strong>{status}</strong>
            <p>{message}</p>
          </div>
        )}

        {error && <p className="message-error">{error}</p>}
      </section>
    </main>
  );
}
