# MESSENGER BOT SETUP GUIDE — PROFESSIONAL AI

## Step 1: Create Facebook App

1. Go to https://developers.facebook.com/apps/
2. Click **Create App**
3. Select **Business** as app type
4. App Name: `Professional AI Assistant`
5. App Contact Email: `support@professionalai.com`
6. Click **Create App**

## Step 2: Add Messenger Product

1. In App Dashboard, find **Messenger** under Products
2. Click **Set Up**
3. Select your Facebook Page (Professional AI)
4. Generate **Page Access Token** — copy and save securely
5. Subscribe to webhook events:
   - `messages`
   - `messaging_postbacks`
   - `messaging_optins`
   - `messaging_referrals`

## Step 3: Set Up Webhook

### Webhook URL:
```
https://your-api-domain.com/api/webhook/messenger
```

### Verify Token:
Generate a random string, e.g., `profai_webhook_verify_2026`

### Subscribe to Fields:
- `messages`
- `messaging_postbacks`

## Step 4: Backend Implementation

Create webhook endpoint:

```typescript
// backend/app/routes/messenger.ts
import { Router } from 'express';
import crypto from 'crypto';

const router = Router();

const VERIFY_TOKEN = process.env.MESSENGER_VERIFY_TOKEN!;
const PAGE_ACCESS_TOKEN = process.env.MESSENGER_PAGE_ACCESS_TOKEN!;

// Webhook verification (GET)
router.get('/webhook/messenger', (req, res) => {
  const mode = req.query['hub.mode'];
  const token = req.query['hub.verify_token'];
  const challenge = req.query['hub.challenge'];

  if (mode === 'subscribe' && token === VERIFY_TOKEN) {
    res.status(200).send(challenge);
  } else {
    res.sendStatus(403);
  }
});

// Webhook handler (POST)
router.post('/webhook/messenger', async (req, res) => {
  const body = req.body;

  if (body.object === 'page') {
    for (const entry of body.entry) {
      const webhookEvent = entry.messaging[0];
      const senderPsid = webhookEvent.sender.id;

      if (webhookEvent.message) {
        await handleMessage(senderPsid, webhookEvent.message);
      } else if (webhookEvent.postback) {
        await handlePostback(senderPsid, webhookEvent.postback);
      }
    }
    res.status(200).send('EVENT_RECEIVED');
  } else {
    res.sendStatus(404);
  }
});

async function handleMessage(senderPsid: string, receivedMessage: any) {
  const response = await getAIResponse(receivedMessage.text);
  await callSendAPI(senderPsid, response);
}

async function handlePostback(senderPsid: string, receivedPostback: any) {
  let response;

  switch (receivedPostback.payload) {
    case 'GET_STARTED':
      response = {
        text: `👋 Hey! Welcome to Professional AI!\n\nI'm your AI assistant. Ask me anything:\n• 💻 Code & programming\n• 🔒 Security scanning\n• 🇵🇰 Urdu/Hindi AI\n• 🎨 Image generation\n• 📱 Build apps in 1 min\n\nOr tap a button below to get started:`
      };
      break;
    case 'DOWNLOAD_APP':
      response = { text: '📲 Download Professional AI:\n\nWindows: https://professionalai.com/download/win\nMac: https://professionalai.com/download/mac\nLinux: https://professionalai.com/download/linux' };
      break;
    case 'VIEW_PRICING':
      response = { text: '💰 Professional AI Plans:\n\n🆓 Free: 10 messages/day\n⭐ PRO: $9.99/mo — Unlimited\n🏢 Enterprise: Custom pricing\n\nStart free trial: https://professionalai.com/trial' };
      break;
    default:
      response = { text: "I didn't understand that. Type 'help' to see what I can do!" };
  }

  await callSendAPI(senderPsid, response);
}

async function getAIResponse(userMessage: string): Promise<any> {
  // Forward to your Professional AI backend API
  const apiResponse = await fetch(`${process.env.API_URL}/api/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message: userMessage, source: 'messenger' }),
  });

  const data = await apiResponse.json();
  return { text: data.reply };
}

async function callSendAPI(senderPsid: string, response: any) {
  const requestBody = {
    recipient: { id: senderPsid },
    message: response,
  };

  await fetch(`https://graph.facebook.com/v18.0/me/messages?access_token=${PAGE_ACCESS_TOKEN}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(requestBody),
  });
}

export default router;
```

## Step 5: Quick Replies (Persistent Menu)

Set up the Messenger persistent menu:

```typescript
// Set this once via Facebook Graph API
const persistentMenu = {
  persistent_menu: [
    {
      locale: 'default',
      call_to_actions: [
        {
          type: 'postback',
          title: '🚀 Get Started',
          payload: 'GET_STARTED'
        },
        {
          type: 'postback',
          title: '📲 Download App',
          payload: 'DOWNLOAD_APP'
        },
        {
          type: 'web_url',
          title: '💰 View Pricing',
          url: 'https://professionalai.com/pricing'
        }
      ]
    }
  ]
};

// POST to: https://graph.facebook.com/v18.0/me/messenger_profile?access_token=PAGE_ACCESS_TOKEN
```

## Step 6: Greeting Text

Set welcome message for new conversations:

```typescript
const greetingResponse = {
  greeting: [
    {
      locale: 'default',
      text: 'Hey! 👋 I\'m the Professional AI assistant. Ask me anything — code, security, Urdu, images, or app building.'
    }
  ]
};

// POST to: https://graph.facebook.com/v18.0/me/messenger_profile?access_token=PAGE_ACCESS_TOKEN
```

## Step 7: Domain Verification

1. In Facebook App Settings → Settings → Basic
2. Add your domain: `professionalai.com`
3. Upload HTML verification file to your website root
4. Enable domain in Messenger settings

## Step 8: Testing

1. Use Facebook's **Test Users** feature in App Dashboard
2. Or message your page from a personal Facebook account
3. Verify webhook receives events in your server logs
4. Test all quick replies and buttons

## Step 9: Go Live

1. In App Dashboard, toggle **Make app public?** to YES
2. Submit for review if required by Meta
3. Monitor conversations in Facebook Page Inbox
4. Set up automated responses for off-hours

---

## Environment Variables Required

```
MESSENGER_VERIFY_TOKEN=profai_webhook_verify_2026
MESSENGER_PAGE_ACCESS_TOKEN=EAAG...your_long_token_here
MESSENGER_APP_SECRET=your_app_secret_here
API_URL=https://your-backend-api.com
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Webhook not receiving events | Check HTTPS is valid, verify token matches, check firewall |
| Messages not sending | Verify Page Access Token has `pages_messaging` permission |
| "Postback not received" | Ensure payload is under 1000 characters |
| Rate limiting | Facebook allows 20 messages/second per page — add queue |
