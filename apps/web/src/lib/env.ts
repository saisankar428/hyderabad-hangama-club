/**
 * Public env vars (baked in at build time on Vercel).
 * Set these in Vercel → Project → Settings → Environment Variables.
 */

const DEFAULT_API_URL = "http://localhost:8000";

export function getApiUrl(): string {
  const url = process.env.NEXT_PUBLIC_API_URL?.trim() || DEFAULT_API_URL;
  return url.replace(/\/$/, "");
}

export function getAdminKey(): string {
  return process.env.NEXT_PUBLIC_ADMIN_KEY?.trim() || "";
}

export function getRazorpayKeyId(): string {
  return process.env.NEXT_PUBLIC_RAZORPAY_KEY_ID?.trim() || "";
}

export function getUpiId(): string {
  return process.env.NEXT_PUBLIC_UPI_ID?.trim() || "";
}

export function isProductionBuild(): boolean {
  return process.env.NODE_ENV === "production";
}

export function isVercelBuild(): boolean {
  return process.env.VERCEL === "1";
}

/** Resolve API-relative paths (e.g. /uploads/screenshots/...) to absolute URLs. */
export function apiAssetUrl(path: string | null | undefined): string | null {
  if (!path) return null;
  if (path.startsWith("http://") || path.startsWith("https://")) return path;
  return `${getApiUrl()}${path.startsWith("/") ? path : `/${path}`}`;
}
