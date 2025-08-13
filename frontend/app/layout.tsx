import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import { Providers } from './providers'
import { Toaster } from '@/components/ui/toaster'

const inter = Inter({ subsets: ['latin', 'cyrillic'] })

export const metadata: Metadata = {
  title: 'Доходометр - Финансовый сервис',
  description: 'Управляйте финансами с умом. Доходометр — современный инструмент для анализа и планирования личных финансов.',
  keywords: [
    'инвестиции',
    'портфель',
    'акции',
    'облигации',
    'анализ',
    'доходность',
    'диверсификация'
  ],
  authors: [{ name: 'Investment Service Team' }],
  creator: 'Investment Service',
  publisher: 'Investment Service',
  metadataBase: new URL(process.env.NEXT_PUBLIC_APP_URL || 'http://localhost:3000'),
  openGraph: {
    type: 'website',
    locale: 'ru_RU',
    url: process.env.NEXT_PUBLIC_APP_URL || 'http://localhost:3000',
    title: 'Сервис учета инвестиций',
    description: 'Профессиональный сервис для учета и анализа инвестиционных портфелей',
    siteName: 'Investment Service',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Сервис учета инвестиций',
    description: 'Профессиональный сервис для учета и анализа инвестиционных портфелей',
  },
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
    },
  },
  viewport: {
    width: 'device-width',
    initialScale: 1,
    maximumScale: 1,
  },
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="ru" suppressHydrationWarning>
      <head>
        <link rel="icon" href="/favicon.ico" />
      </head>
      <body className={inter.className}>
        <Providers>
          <div className="relative min-h-screen bg-background">
            {children}
          </div>
          <Toaster />
        </Providers>
      </body>
    </html>
  )
}
