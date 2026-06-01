/**
 * Public env vars (baked in at build time on Vercel).
 * Set in Vercel → Project → Settings → Environment Variables.
 */

const DEV_API_FALLBACK = "http://127.0.0.1:8000";

function resolveApiUrl(): string {
  const configured = process.env.NEXT_PUBLIC_API_URL?.trim();
  if (configured) {
    return configured.replace(/\/$/, "");
  }
  if (process.env.NODE_ENV === "development" && process.env.VERCEL !== "1") {
    return DEV_API_FALLBACK;
  }
  return "";
}

export function getApiUrl(): string {
  const url = resolveApiUrl();
  if (!url && (isProductionBuild() || isVercelBuild())) {
    console.error(
      "NEXT_PUBLIC_API_URL is not set. Configure it in Vercel and redeploy.",
    );
  }
  return url;
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

/** Resolve stored asset URLs (Supabase HTTPS or legacy API-relative paths). */
export function apiAssetUrl(path: string | null | undefined): string | null {
  if (!path) return null;
  if (path.startsWith("http://") || path.startsWith("https://")) {
    return path;
  }
  const apiUrl = getApiUrl();
  if (!apiUrl) return null;
  return `${apiUrl}${path.startsWith("/") ? path : `/${path}`}`;
}

export function requireApiUrl(): string {
  const url = getApiUrl();
  if (!url) {
    throw new Error(
      "API URL is not configured. Set NEXT_PUBLIC_API_URL in your environment.",
    );
  }
  return url;
}
