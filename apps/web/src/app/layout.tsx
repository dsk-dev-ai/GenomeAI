import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'GenomeAI',
  description: 'Open-source intelligence for the genome era',
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
