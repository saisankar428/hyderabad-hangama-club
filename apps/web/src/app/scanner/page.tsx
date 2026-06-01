"use client";

import { useCallback, useEffect, useRef, useState } from "react";

const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

type ScanStatus = "idle" | "scanning" | "valid" | "used" | "invalid";

interface ScanResult {
  valid: boolean;
  ticket_code: string;
  attendee_name: string;
  event_id: string;
  message: string;
  already_scanned?: boolean;
}

/** Extract the plain ticket code from a raw QR payload.
 *  QR format: HHC:TICKET:HHC-000001:<uuid>
 *  Direct entry: HHC-000001
 */
function extractTicketCode(raw: string): string {
  const s = raw.trim();
  if (s.startsWith("HHC:TICKET:")) {
    const parts = s.split(":");
    if (parts.length >= 4) return parts[2]; // "HHC-000001"
  }
  return s;
}

export default function ScannerPage() {
  const [scanStatus, setScanStatus] = useState<ScanStatus>("idle");
  const [scanResult, setScanResult] = useState<ScanResult | null>(null);
  const [manualCode, setManualCode] = useState("");
  const [validating, setValidating] = useState(false);
  const [cameraError, setCameraError] = useState<string | null>(null);

  // Refs to QR scanner instance so we can stop/restart
  const html5QrRef = useRef<any>(null);
  const scannerStarted = useRef(false);

  const startScanner = useCallback(async () => {
    if (scannerStarted.current) return;
    try {
      const module = await import("html5-qrcode");
      const Html5Qrcode = module.Html5Qrcode;
      const qr = new Html5Qrcode("scanner-container");
      html5QrRef.current = qr;
      scannerStarted.current = true;
      setScanStatus("scanning");

      await qr.start(
        { facingMode: { exact: "environment" } },
        { fps: 10, qrbox: 250 },
        async (decodedText: string) => {
          const code = extractTicketCode(decodedText);
          setManualCode(code);
          try {
            await qr.stop();
          } catch {
            // ignore stop errors
          }
          scannerStarted.current = false;
          await runValidation(code);
        },
        (_errorMessage: string) => {
          // per-frame scan errors are normal — suppress
        }
      );
    } catch {
      setCameraError("Camera unavailable. Enter the ticket code manually below.");
      setScanStatus("idle");
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    startScanner();
    return () => {
      if (html5QrRef.current && scannerStarted.current) {
        html5QrRef.current.stop().catch(() => {});
        scannerStarted.current = false;
      }
    };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const runValidation = async (code: string) => {
    if (!code.trim()) return;
    setValidating(true);
    setScanResult(null);
    try {
      const res = await fetch(`${apiUrl}/scanner/scan`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ticket_code: code.trim() }),
      });
      const data: ScanResult = await res.json();

      if (!res.ok) {
        setScanStatus("invalid");
        setScanResult({
          valid: false,
          ticket_code: code,
          attendee_name: "",
          event_id: "",
          message: (data as any).detail || "Ticket not found.",
        });
        return;
      }

      if (data.valid) {
        setScanStatus("valid");
      } else if (data.already_scanned) {
        setScanStatus("used");
      } else {
        setScanStatus("invalid");
      }
      setScanResult(data);
    } catch {
      setScanStatus("invalid");
      setScanResult({
        valid: false,
        ticket_code: code,
        attendee_name: "",
        event_id: "",
        message: "Network error — please try again.",
      });
    } finally {
      setValidating(false);
    }
  };

  const handleManualValidate = () => {
    const code = extractTicketCode(manualCode);
    runValidation(code);
  };

  const handleRescan = () => {
    setScanStatus("idle");
    setScanResult(null);
    setManualCode("");
    setCameraError(null);
    // Small delay so the DOM element is ready
    setTimeout(() => startScanner(), 100);
  };

  const scanned = scanStatus === "valid" || scanStatus === "used" || scanStatus === "invalid";

  return (
    <main className="page-shell">
      <section className="scanner-section">
        <h1 style={{ margin: "0 0 4px", fontSize: "1.3rem", fontWeight: 900 }}>
          Ticket Scanner
        </h1>
        <p style={{ margin: "0 0 20px", fontSize: "0.84rem", color: "rgba(255,255,255,0.45)" }}>
          Scan QR code or enter ticket code manually
        </p>

        {/* Camera view — hidden after result */}
        {!scanned && (
          <div id="scanner-container" className="scanner-box" />
        )}

        {cameraError && (
          <p className="message-error" style={{ marginBottom: 12 }}>{cameraError}</p>
        )}

        {/* Manual entry */}
        {!scanned && (
          <>
            <div className="form-group" style={{ marginTop: 14 }}>
              <label className="form-label" htmlFor="ticketCode">Ticket code</label>
              <input
                id="ticketCode"
                className="form-field"
                value={manualCode}
                onChange={(e) => setManualCode(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleManualValidate()}
                placeholder="HHC-000001"
                autoComplete="off"
                autoCapitalize="characters"
              />
            </div>
            <button
              className="button"
              onClick={handleManualValidate}
              disabled={!manualCode.trim() || validating}
            >
              {validating ? "Validating…" : "Validate Ticket"}
            </button>
          </>
        )}

        {/* Scan result */}
        {scanned && scanResult && (
          <div className={`status-box ${scanStatus}`} style={{ marginTop: 0 }}>
            <strong style={{ fontSize: "1.1rem", letterSpacing: "0.08em" }}>
              {scanStatus === "valid"
                ? "✓ ENTRY GRANTED"
                : scanStatus === "used"
                ? "⚠ ALREADY SCANNED"
                : "✗ INVALID TICKET"}
            </strong>

            {scanResult.attendee_name && (
              <p style={{ margin: "8px 0 4px", fontSize: "1.05rem", fontWeight: 700 }}>
                {scanResult.attendee_name}
              </p>
            )}
            <p style={{ margin: "4px 0 0", fontSize: "0.84rem", opacity: 0.8 }}>
              {scanResult.message}
            </p>
            {scanResult.ticket_code && (
              <p style={{
                margin: "8px 0 0",
                fontFamily: "monospace",
                fontSize: "0.8rem",
                opacity: 0.55,
              }}>
                {scanResult.ticket_code}
              </p>
            )}
          </div>
        )}

        {/* Re-scan button */}
        {scanned && (
          <button
            className="button"
            onClick={handleRescan}
            style={{ marginTop: 16 }}
          >
            Scan Next Ticket
          </button>
        )}
      </section>
    </main>
  );
}
