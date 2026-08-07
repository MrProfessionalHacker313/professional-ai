import { NextApiRequest, NextApiResponse } from 'next';

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const { body } = req;
  const { event_name, event_time, user_data, custom_data } = body;

  try {
    const PIXEL_ID = process.env.META_PIXEL_ID;
    const ACCESS_TOKEN = process.env.META_CAPI_ACCESS_TOKEN;
    const API_VERSION = 'v18.0';

    const response = await fetch(
      `https://graph.facebook.com/${API_VERSION}/${PIXEL_ID}/events`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          data: [
            {
              event_name,
              event_time: event_time || Math.floor(Date.now() / 1000),
              user_data: {
                email: user_data?.email ? hashEmail(user_data.email) : undefined,
                phone: user_data?.phone ? hashPhone(user_data.phone) : undefined,
                client_ip_address: req.headers['x-forwarded-for'] || req.socket.remoteAddress,
                client_user_agent: req.headers['user-agent'],
              },
              custom_data: custom_data || {},
            },
          ],
        }),
      }
    );

    const result = await response.json();
    res.status(200).json(result);
  } catch (error) {
    console.error('Conversions API error:', error);
    res.status(500).json({ error: 'Failed to send event' });
  }
}

function hashEmail(email: string): string {
  const crypto = require('crypto');
  return crypto.createHash('sha256').update(email.toLowerCase().trim()).digest('hex');
}

function hashPhone(phone: string): string {
  const crypto = require('crypto');
  const cleaned = phone.replace(/[^0-9]/g, '');
  return crypto.createHash('sha256').update(cleaned).digest('hex');
}
