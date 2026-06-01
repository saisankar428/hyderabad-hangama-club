#!/usr/bin/env node
/**
 * Fail Vercel/production builds when required public env vars are missing.
 * Local `npm run dev` is unaffected unless NODE_ENV=production.
 */

const isVercel = process.env.VERCEL === "1";
const isProdBuild =
  process.env.NODE_ENV === "production" || process.env.CI === "true";

if (!isVercel && !isProdBuild) {
  process.exit(0);
}

const required = [
  {
    key: "NEXT_PUBLIC_API_URL",
    hint: "Public HTTPS URL of your FastAPI backend (e.g. https://hhc-api.onrender.com)",
  },
];

const missing = required.filter(({ key }) => !process.env[key]?.trim());

if (missing.length === 0) {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL.trim().replace(/\/$/, "");
  const isLocalApi =
    apiUrl.startsWith("http://localhost") ||
    apiUrl.startsWith("http://127.0.0.1");
  if (isVercel && isLocalApi) {
    console.error(
      "\n[verify-env] NEXT_PUBLIC_API_URL must be a public HTTPS API URL on Vercel.",
      "\nDeploy the API on Render and set NEXT_PUBLIC_API_URL to that URL.\n",
    );
    process.exit(1);
  }
  if (isVercel && !apiUrl.startsWith("https://")) {
    console.error(
      "\n[verify-env] NEXT_PUBLIC_API_URL must use HTTPS on Vercel.\n",
    );
    process.exit(1);
  }
  process.exit(0);
}

console.error("\n[verify-env] Missing required environment variables:\n");
for (const { key, hint } of missing) {
  console.error(`  - ${key}`);
  console.error(`    ${hint}\n`);
}
console.error(
  "Add them in Vercel → Project → Settings → Environment Variables, then redeploy.\n",
);
process.exit(1);
