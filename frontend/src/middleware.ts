import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

// Owner email from environment (must match backend OWNER_EMAIL)
const OWNER_EMAIL = (process.env.NEXT_PUBLIC_OWNER_EMAIL || 'redr28126@gmail.com').toLowerCase().trim()

// Routes that require owner access - /admin AND /owner are both blocked for everyone except the owner
const OWNER_ONLY_PATHS = ['/admin', '/owner']

export async function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl

  // Only protect page routes (/admin, /owner). API routes (/api/admin/*)
  // are handled by the backend's get_current_owner dependency which
  // validates the JWT token properly. Blocking API calls here caused
  // 401/403 errors even for the owner.
  const isOwnerOnly =
    OWNER_ONLY_PATHS.some((p) => pathname === p || pathname.startsWith(p + '/'))

  if (!isOwnerOnly) {
    return NextResponse.next()
  }

  // Read the user email from a cookie set at login (owner_email)
  const ownerEmailCookie = request.cookies.get('owner_email')?.value?.toLowerCase().trim()
  const accessToken = request.cookies.get('access_token')?.value

  // If not logged in at all, redirect to login
  if (!accessToken) {
    const loginUrl = new URL('/login', request.url)
    loginUrl.searchParams.set('redirect', pathname)
    return NextResponse.redirect(loginUrl)
  }

  // If the cookie email doesn't match the owner, return 403 (forbidden)
  if (!ownerEmailCookie || ownerEmailCookie !== OWNER_EMAIL) {
    const forbiddenUrl = new URL('/dashboard', request.url)
    forbiddenUrl.searchParams.set('error', '403')
    return NextResponse.redirect(forbiddenUrl)
  }

  return NextResponse.next()
}

export const config = {
  matcher: ['/admin/:path*', '/owner/:path*'],
}