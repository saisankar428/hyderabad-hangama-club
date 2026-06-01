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
  if (isVercel && apiUrl.startsWith("http://localhost")) {
    console.error(
      "\n[verify-env] NEXT_PUBLIC_API_URL must not be localhost on Vercel.",
      "\nDeploy the API (Render, Railway, Fly.io, etc.) and set the public HTTPS URL.\n",
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
