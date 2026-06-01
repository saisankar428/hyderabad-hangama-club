import "./globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Hyderabad Hangama Club",
  description: "Event ticketing MVP for Tollywood Jam Night.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
