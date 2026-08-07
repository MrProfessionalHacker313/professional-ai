import { NextResponse } from 'next/server'
import { CONTENT_CALENDAR_90_DAYS } from '@/lib/seo/contentCalendar'

export async function GET() {
  return NextResponse.json({
    days: CONTENT_CALENDAR_90_DAYS.length,
    calendar: CONTENT_CALENDAR_90_DAYS,
  })
}
