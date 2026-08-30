import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: {
    default: 'GenomeAI — Open-source intelligence for the genome era',
    template: '%s · GenomeAI',
  },
  description:
    'GenomeAI is an open-source genomics research platform combining 18 free biological databases with free-tier Gemini AI to deliver gene, variant, protein, literature, drug, pathway, disease and executive multi-domain analysis.',
  keywords: [
    'genomics',
    'bioinformatics',
    'gene analysis',
    'variant interpretation',
    'protein structure',
    'drug discovery',
    'pathway analysis',
    'genome intelligence',
  ],
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body suppressHydrationWarning>{children}</body>
    </html>
  )
}
