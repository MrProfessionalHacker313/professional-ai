# Meta Pixel + Conversions API Integration Guide

## Installation

1. Replace `YOUR_PIXEL_ID_HERE` in `marketing/meta-pixel-code.html` with your actual Pixel ID
2. Copy the `<head>` snippet into your website's `<head>` section
3. Add the `meta-pixel-code.html` snippet to all pages (Next.js: add to `_app.tsx` or layout)

## Next.js / React Implementation

Add to `frontend/src/app/layout.tsx`:

```typescript
import Script from 'next/script';

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <head>
        <Script id="meta-pixel" strategy="afterInteractive">
          {`
            !function(f,b,e,v,n,t,s)
            {if(f.fbq)return;n=f.fbq=function(){n.callMethod?
            n.callMethod.apply(n,arguments):n.queue.push(arguments)};
            if(!f._fbq)f._fbq=n;n.push=n;n.loaded=!0;n.version='2.0';
            n.queue=[];t=b.createElement(e);t.async=!0;
            t.src=v;s=b.getElementsByTagName(e)[0];
            s.parentNode.insertBefore(t,s)}(window, document,'script',
            'https://connect.facebook.net/en_US/fbevents.js');
            fbq('init', 'YOUR_PIXEL_ID_HERE');
            fbq('track', 'PageView');
          `}
        </Script>
        <noscript>
          <img height="1" width="1" style={{display: 'none'}}
               src={`https://www.facebook.com/tr?id=YOUR_PIXEL_ID_HERE&ev=PageView&noscript=1`} />
        </noscript>
      </head>
      <body>{children}</body>
    </html>
  );
}
```

## Tracking Events from Frontend

```typescript
// lib/meta-pixel.ts
export const trackEvent = (eventName: string, params?: Record<string, any>) => {
  if (typeof window !== 'undefined' && (window as any).fbq) {
    (window as any).fbq('track', eventName, params);
  }
};

// Usage:
import { trackEvent } from '@/lib/meta-pixel';

trackEvent('Signup', { content_name: 'Professional AI Free Account' });
trackEvent('StartTrial', { value: 29.99, currency: 'USD' });
trackEvent('Purchase', { value: 29.99, currency: 'USD', content_ids: ['pro_monthly'] });
```

## Server-side Conversions API

Create API route at `frontend/src/app/api/meta-pixel/route.ts`:

```typescript
import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  const body = await request.json();
  const { event_name, user_data, custom_data } = body;

  const PIXEL_ID = process.env.META_PIXEL_ID;
  const ACCESS_TOKEN = process.env.META_CAPI_ACCESS_TOKEN;

  await fetch(
    `https://graph.facebook.com/v18.0/${PIXEL_ID}/events?access_token=${ACCESS_TOKEN}`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        data: [{
          event_name,
          event_time: Math.floor(Date.now() / 1000),
          user_data: {
            email: hash(user_data?.email),
            phone: hash(user_data?.phone),
            client_ip_address: request.headers.get('x-forwarded-for'),
            client_user_agent: request.headers.get('user-agent'),
          },
          custom_data,
        }],
      }),
    }
  );

  return NextResponse.json({ success: true });
}

function hash(value: string | undefined): string | undefined {
  if (!value) return undefined;
  const crypto = require('crypto');
  return crypto.createHash('sha256').update(value.toLowerCase().trim()).digest('hex');
}
```

## Environment Variables

Add to your `.env.local`:
```
META_PIXEL_ID=your_pixel_id_here
META_CAPI_ACCESS_TOKEN=your_access_token_here
```

## Verification

1. Install Meta Pixel Helper Chrome extension
2. Visit your website and confirm Pixel fires
3. Go to Facebook Events Manager → Test Events
4. Verify all events appear in real-time
5. Check Conversions API events show as "Server-side"
