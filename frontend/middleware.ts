import { NextResponse } from 'next/server'

export function middleware(request: Request) {
  const res = NextResponse.next()
  // Security headers mirrored from backend
  res.headers.set('X-Content-Type-Options', 'nosniff')
  res.headers.set('X-Frame-Options', 'DENY')
  res.headers.set('Referrer-Policy', 'no-referrer')
  res.headers.set('Permissions-Policy', 'geolocation=(), camera=(), microphone=(), payment=()')
  res.headers.set('Content-Security-Policy', "default-src 'self'; object-src 'none'; frame-ancestors 'none'; base-uri 'self'")

  // Cache policy: only for HTML responses
  const accept = request.headers.get('accept') || ''
  if (accept.includes('text/html')) {
    res.headers.set('Cache-Control', 'no-store')
  }
  return res
}

export const config = {
  matcher: [
    '/((?!_next|favicon.ico|robots.txt|api/health).*)',
  ],
}

