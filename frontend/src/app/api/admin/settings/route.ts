import { NextRequest, NextResponse } from 'next/server'
import { getOwnerFromRequest, ownerUnauthorized } from '@/lib/admin-auth'

const BACKEND = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export async function GET(req: NextRequest) {
  const owner = getOwnerFromRequest(req)
  if (!owner) return ownerUnauthorized()

  try {
    const res = await fetch(`${BACKEND}/api/admin/owner/control-state`, {
      headers: { cookie: req.headers.get('cookie') || '' },
    })
    const data = await res.json()
    const toggles = data.feature_toggles || {}
    const limits = data.global_limits || {}

    return NextResponse.json({
      feature_toggles: {
        chat: toggles.chat ?? true,
        code: toggles.code ?? true,
        media: toggles.media ?? true,
        offline: toggles.offline ?? true,
        payments: toggles.payments ?? true,
      },
      trial_days: limits.trial_days ?? 3,
      keys_status: [
        { name: 'Gemini', active: !!process.env.GEMINI_API_KEY },
        { name: 'Groq', active: !!process.env.GROQ_API_KEY },
        { name: 'Fal', active: !!process.env.FAL_API_KEY },
        { name: 'ElevenLabs', active: !!process.env.ELEVENLABS_API_KEY },
      ],
    })
  } catch {
    return NextResponse.json({ error: 'Backend unavailable' }, { status: 502 })
  }
}

export async function POST(req: NextRequest) {
  const owner = getOwnerFromRequest(req)
  if (!owner) return ownerUnauthorized()

  try {
    const body = await req.json()
    const res = await fetch(`${BACKEND}/api/admin/owner/control-state`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        cookie: req.headers.get('cookie') || '',
      },
      body: JSON.stringify({
        feature_toggles: body.feature_toggles || {},
        global_limits: { trial_days: body.trial_days ?? 3 },
        plan_prices: {},
      }),
    })
    const data = await res.json()
    return NextResponse.json(data, { status: res.status })
  } catch {
    return NextResponse.json({ error: 'Backend unavailable' }, { status: 502 })
  }
}