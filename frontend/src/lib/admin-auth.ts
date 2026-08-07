import { NextRequest, NextResponse } from 'next/server'
import crypto from 'crypto'

const OWNER_EMAIL = (process.env.OWNER_EMAIL || 'redr28126@gmail.com').toLowerCase().trim()
const JWT_SECRET = process.env.JWT_SECRET || ''

function base64UrlDecode(input: string): string {
  const base64 = input.replace(/-/g, '+').replace(/_/g, '/')
  const padded = base64.padEnd(base64.length + ((4 - (base64.length % 4)) % 4), '=')
  return Buffer.from(padded, 'base64').toString('utf8')
}

export function verifyOwnerJwt(token: string): { email: string } | null {
  try {
    const parts = token.split('.')
    if (parts.length !== 3) return null

    const header = JSON.parse(base64UrlDecode(parts[0]))
    const payload = JSON.parse(base64UrlDecode(parts[1]))

    const data = `${parts[0]}.${parts[1]}`
    const signature = crypto
      .createHmac('sha256', JWT_SECRET)
      .update(data)
      .digest('base64')
      .replace(/\+/g, '-')
      .replace(/\//g, '_')
      .replace(/=+$/, '')

    if (signature !== parts[2]) return null

    const email = (payload.email || '').toLowerCase().trim()
    if (email !== OWNER_EMAIL) return null

    return { email }
  } catch {
    return null
  }
}

export function getOwnerFromRequest(req: NextRequest): { email: string } | null {
  const token = req.cookies.get('access_token')?.value
  if (!token) return null
  return verifyOwnerJwt(token)
}

export function ownerUnauthorized(): NextResponse {
  return NextResponse.json({ error: 'Forbidden: owner access required' }, { status: 403 })
}