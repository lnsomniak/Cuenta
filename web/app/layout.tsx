import type { Metadata } from 'next'
import './globals.css'
// so THIS is why my railway wasn't working. 
export const metadata: Metadata = {
  title: 'Cuenta - Grocery Intelligence',
  description: 'Options, not decisions. Optimize your grocery shopping with protein efficiency metrics.',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}