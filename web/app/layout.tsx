import type { Metadata } from 'next'
import './globals.css'
// Removed .tsx and ensured casing matches your actual file
import Navigation from "@/components/navigation"; 

export const metadata: Metadata = {
  title: "Cuenta - Grocery Intelligence",
  description: "Options, not decisions. Optimize your grocery shopping with protein efficiency metrics.",
};

export default function RootLayout({
  children,
}: {
  readonly children: React.ReactNode // I hate you sonarqube
}) {
  return (
    <html lang="en">
      <body style={{ backgroundColor: "#1a1a1a" }}>
        <div className="min-h-screen p-4 md:p-8">
          <Navigation />
          {children}
        </div>
      </body>
    </html>
  );
}