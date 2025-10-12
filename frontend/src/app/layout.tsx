import type { Metadata } from "next"
import { Space_Grotesk, Inter } from "next/font/google"
import "./globals.css"
import { Navigation } from "@/components/Navigation"
import { ErrorBoundary } from "@/components/ErrorBoundary"

const spaceGrotesk = Space_Grotesk({
  subsets: ["latin"],
  variable: "--font-heading",
  weight: ["400", "500", "600", "700"],
})

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-body",
})

export const metadata: Metadata = {
  title: "Numen AI - Personalized Manifestation & Transformation",
  description: "AI-powered manifestation and hypnotherapy for your transformation journey",
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className={`${spaceGrotesk.variable} ${inter.variable}`}>
      <head>
        <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no" />
      </head>
      <body className={inter.className}>
        <ErrorBoundary>
          <Navigation />
          {children}
        </ErrorBoundary>
      </body>
    </html>
  )
}