# WHATSAPP BUSINESS SETUP — PROFESSIONAL AI

## Step 1: Create WhatsApp Business Account

1. Download **WhatsApp Business** app from Play Store / App Store
2. Register with a dedicated business phone number (use a new SIM or Google Voice)
3. Verify the number via SMS/call
4. Set business name: **Professional AI**
5. Business Category: **Technology / Software**
6. Add business description, hours, address, website URL

## Step 2: Get Meta Business Verification

1. Go to https://business.facebook.com
2. Create a Business Account if you don't have one
3. Add your WhatsApp number under **Business Settings → WhatsApp Accounts**
4. Complete business verification (requires:
   - Business registration documents
   - Website URL
   - Business address
   - Tax ID if applicable)

## Step 3: Set Up WhatsApp Business API (for automation)

For automated messaging at scale, use the WhatsApp Business Platform API:

### API Endpoint:
```
POST https://graph.facebook.com/v18.0/YOUR_PHONE_NUMBER_ID/messages
```

### Headers:
```
Authorization: Bearer YOUR_ACCESS_TOKEN
Content-Type: application/json
```

### Environment Variables:
```
WHATSAPP_PHONE_NUMBER_ID=your_phone_number_id
WHATSAPP_ACCESS_TOKEN=your_access_token
WHATSAPP_BUSINESS_ACCOUNT_ID=your_business_account_id
WHATSAPP_APP_SECRET=your_app_secret
WHATSAPP_VERIFY_TOKEN=your_webhook_verify_token
```

## Step 4: Auto-Reply Bot Message (First Message)

When a new user messages first time, send this:

```
👋 Welcome to Professional AI!

🤖 Thanks for reaching out! Here's what you can do:

📲 Download the App:
https://professionalai.com/download

🎁 Free PRO Trial (7 days, no card):
https://professionalai.com/trial

💬 Need help? Just type your question and our AI will reply instantly.

Examples you can try:
• "Write Python code for a calculator"
• "Scan my website for security issues"
• "Translate this to Urdu"
• "Generate an image of a futuristic city"

— Professional AI Team
```

## Step 5: Quick Reply Templates

### Template 1: Pricing Inquiry
**Trigger:** User types "price", "cost", "pricing", "kitna"

```
💰 Professional AI Plans:

🆓 Free — 10 messages/day
⭐ PRO — $9.99/month or $79/year
   ✅ Unlimited messages
   ✅ Security scanner
   ✅ Image generation
   ✅ Priority support
🏢 Enterprise — Custom pricing

🎁 Start your FREE 7-day PRO trial:
👉 https://professionalai.com/trial

No credit card required.
```

### Template 2: Download Link
**Trigger:** User types "download", "app", "install"

```
📲 Download Professional AI:

🪟 Windows: https://professionalai.com/download/win
🍎 Mac: https://professionalai.com/download/mac
🐧 Linux: https://professionalai.com/download/linux
📱 Android: https://play.google.com/store/apps/...
📱 iOS: https://apps.apple.com/app/...

100% free to start. No credit card needed.
Questions? Just ask!
```

### Template 3: Urdu Language Support
**Trigger:** User types "urdu", "اردو"

```
🇵🇰بلی! Professional AI اردو بولتی ہے۔

آپ roman urdu ya proper urdu میں سوال پوچھ سکتے ہیں۔

مثال:
• "python mein calculator ka code likho"
• "meri website security scan karo"
• "اس تصویر کی绘图 کرو"

Free trial start karo:
👉 https://professionalai.com/trial
```

### Template 4: Help / Capabilities
**Trigger:** User types "help", "what can you do", "madad"

```
🤖 Professional AI can help you with:

💻 Coding & Programming
   • Write code in any language
   • Debug and fix bugs
   • Explain complex concepts

🔒 Security Scanning
   • Scan code for vulnerabilities
   • Fix security issues

🌍 Languages
   • Urdu, Hindi, English, Arabic
   • Translation and conversation

🎨 Image Generation
   • Create images from text
   • Design assets and graphics

📱 App Building
   • Build full apps in minutes
   • Generate UI/UX

💬 Just type what you need!
```

### Template 5: Stop Notifications
**Trigger:** User types "stop", "unsubscribe", "band karo"

```
You've been removed from broadcast messages.

To re-enable notifications, type:
👉 START

We miss you! Come back anytime.
— Professional AI Team
```

## Step 6: Broadcast List Strategy

### Weekly Broadcast Schedule:

| Day | Audience | Message |
|-----|----------|---------|
| Monday | All users | New feature update + tutorial link |
| Wednesday | Free users | "Upgrade to PRO this week for 20% off" |
| Friday | PRO users | Weekend challenge prompt + tips |
| Sunday | All users | Community highlight + promo code |

### Broadcast Example:

```
🌟 WEEKLY UPDATE — Professional AI

🚀 New Feature: AI now generates React + TypeScript apps!

📚 This week's tutorial: "Build a full-stack app in 5 minutes"
👉 https://professionalai.com/blog/fullstack-5-min

🎁 Members-only promo this week:
Code: PRO20 = 20% off PRO plan

Join our Facebook group:
👉 https://facebook.com/groups/professionalaiusers

Questions? Just reply to this message!
— Professional AI Team
```

## Step 7: Webhook Setup (for incoming messages)

### Webhook URL:
```
https://your-api.com/api/webhook/whatsapp
```

### Verify Token:
```
profai_whatsapp_verify_2026
```

### Subscribe to:
- `messages`

### Webhook Handler (Express/Node):

```typescript
// backend/app/routes/whatsapp.ts
import { Router } from 'express';

const router = Router();

router.post('/webhook/whatsapp', async (req, res) => {
  const body = req.body;

  if (body.object === 'whatsapp_business_account') {
    for (const entry of body.entry) {
      const changes = entry.changes[0];
      const message = changes.value.messages?.[0];

      if (message) {
        const phoneNumber = message.from;
        const messageText = message.text?.body?.toLowerCase() || '';

        // Determine response based on keywords
        let replyText = '';

        if (messageText.includes('price') || messageText.includes('cost') || messageText.includes('kitna')) {
          replyText = getPricingReply();
        } else if (messageText.includes('download') || messageText.includes('app')) {
          replyText = getDownloadReply();
        } else if (messageText.includes('urdu') || messageText.includes('اردو')) {
          replyText = getUrduReply();
        } else if (messageText.includes('help')) {
          replyText = getHelpReply();
        } else if (messageText.includes('stop') || messageText.includes('unsubscribe')) {
          replyText = getStopReply();
        } else {
          // Forward to AI backend
          replyText = await getAIReply(messageText);
        }

        await sendWhatsAppMessage(phoneNumber, replyText);
      }
    }
    res.status(200).send('OK');
  } else {
    res.sendStatus(404);
  }
});

async function sendWhatsAppMessage(to: string, text: string) {
  const PHONE_NUMBER_ID = process.env.WHATSAPP_PHONE_NUMBER_ID;
  const ACCESS_TOKEN = process.env.WHATSAPP_ACCESS_TOKEN;

  await fetch(`https://graph.facebook.com/v18.0/${PHONE_NUMBER_ID}/messages`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${ACCESS_TOKEN}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      messaging_product: 'whatsapp',
      to: to,
      type: 'text',
      text: { body: text },
    }),
  });
}

async function getAIReply(userMessage: string): Promise<string> {
  const response = await fetch(`${process.env.API_URL}/api/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message: userMessage, source: 'whatsapp' }),
  });

  const data = await response.json();
  return data.reply || "I couldn't process that. Type 'help' for options.";
}

function getPricingReply() {
  return `💰 Professional AI Plans:\n\n🆓 Free: 10 messages/day\n⭐ PRO: $9.99/mo or $79/yr\n🏢 Enterprise: Custom\n\nFree trial: https://professionalai.com/trial`;
}

function getDownloadReply() {
  return `📲 Download:\nWindows: professionalai.com/download/win\nMac: professionalai.com/download/mac\nLinux: professionalai.com/download/linux`;
}

function getUrduReply() {
  return `🇵🇰 بلی! Professional AI اردو بولتی ہے۔\n\nآپ roman urdu میں سوال پوچھ سکتے ہیں۔\nمثال: "python mein calculator ka code likho"\n\nFree trial: professionalai.com/trial`;
}

function getHelpReply() {
  return `🤖 I can help with:\n• 💻 Coding & debugging\n• 🔒 Security scanning\n• 🌍 Urdu/Hindi/English AI\n• 🎨 Image generation\n• 📱 App building\n\nJust type what you need!`;
}

function getStopReply() {
  return `You've been removed from broadcasts.\nTo re-enable, type: START\n\n— Professional AI Team`;
}

export default router;
```

## Step 8: Phone Number for WhatsApp

**Recommended Setup:**
- Use a dedicated business phone number (not personal)
- Options: Google Voice, VoIP number, or dedicated SIM
- Consider: Pakistan (+92), US (+1), UK (+44) for regional presence

**WhatsApp Business API Limits:**
- Free tier: 1,000 conversations/month
- Paid tier: $0.005-0.07 per conversation (depends on country)
- Template messages: pre-approved for marketing/utility

## Step 9: Compliance & Best Practices

1. **Opt-in required:** Only message users who first message you or explicitly opt-in
2. **24-hour rule:** Free-form replies only within 24 hours of last user message
3. **Template messages:** Use approved templates for outbound marketing after 24 hours
4. **Opt-out:** Always include STOP option
5. **Rate limits:** Don't spam — quality over quantity

---

## WhatsApp vs. Messenger: When to Use Which

| Feature | WhatsApp | Messenger |
|---------|----------|-----------|
| Penetration in Pakistan/India | Higher | Medium |
| International reach | Excellent | Excellent |
| Group chats | 256 people | 50 people |
| File sharing | 16MB | 25MB |
| Business API cost | $0.005-0.07/conversation | Free (mostly) |
| User base | 2B+ | 1B+ |

**Strategy:** Use WhatsApp for Pakistan/India markets, Messenger for US/UK/Middle East.
