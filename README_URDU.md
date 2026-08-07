# Professional AI - مکمل سیٹ اپ گائیڈ

## 🚀 تیزی سے شروع (3 آسان اقدامات)

### اقدام 1: Docker انسٹال کریں
`INSTALL_DOCKER.bat` رن کریں یا Docker Desktop دستی انسٹال کریں:
https://www.docker.com/products/docker-desktop/

**انسٹالیشن کے بعد:**
- اپنے کمپیوٹر کو دوبارہ شروع کریں
- Docker Desktop کھولیں
- انتظار کریں جب تک یہ مکمل لوڈ نہیں ہو جاتی (سسٹم ٹرے میں وہیل آئیکون)

### اقدام 2: Google OAuth کنفیگر کریں (اختیاری لیکن سفارشی)

1. [Google Cloud Console](https://console.cloud.google.com/apis/credentials) پر جائیں
2. نیا پروجیکٹ بنائیں یا موجودہ منتخب کریں
3. "Google+ API" ایکٹیویٹ کریں
4. OAuth 2.0 Client ID بنائیں:
   - Application type: Web application
   - Authorized redirect URIs: `http://localhost:8000/api/auth/callback/google`
   - Authorized JavaScript origins: `http://localhost:8000`
5. Client ID اور Client Secret کاپی کریں
6. `.env` فائل میں تبدیل کریں:
   ```
   GOOGLE_CLIENT_ID=your-actual-client-id.apps.googleusercontent.com
   GOOGLE_CLIENT_SECRET=your-actual-client-secret
   ```

### اقدام 3: ایپلیکیشن شروع کریں

**آپشن A: `START.bat` ڈبل کلک کریں**

**آپشن B: کمانڈ پرومپٹ سے رن کریں:**
```bash
docker-compose up --build
```

## ✅ اپنی AI تک رسائی

شروعات کے بعد (2-3 منٹ)، براؤزر کھولیں:

**مین ایپلیکیشن:** http://localhost:8000
**لاگ ان صفحہ:** http://localhost:8000/login
**ڈیش بورڈ:** http://localhost:8000/dashboard
**AI چیٹ:** http://localhost:8000/chat

## 🔐 مالک ایڈمن رسائی

آپ کا ای میل ایڈمن/مالک کے طور پر کنfigur کیا گیا ہے: **redr28126@gmail.com**

**پہلا لاگ ان:**
1. http://localhost:8000/login پر جائیں
2. "Sign in with Google" کلک کریں (اگر کنfigur ہو)
3. یا ای میل/پاس ورڈ سے رجسٹر کریں
4. مالک اکاؤنٹ خود بخود ایڈمن کے ساتھ بن جائے گا

## 🎯 دستیاب خصوصیات

### مالک/ایڈمن کے طور پر:
- ✅ لامحدود AI چیٹ (تمام موڈز)
- ✅ کوڈ جنریشن (لامحدود)
- ✅ سیکیورٹی انالیسیس
- ✅ بگ فکسنگ
- ✅ تمام ایڈوانسڈ فیچرز
- ✅ ایڈمن پینل رسائی
- ✅ پرائورٹی سپورٹ

### AI موڈز:
1. **چیٹ موڈ** - عمومی گفتگو
2. **کوڈ موڈ** - پروڈکشن-Ready کوڈ بنائیں
3. **سیکیورٹی موڈ** - سائبر سیکیورٹی انالیسیس
4. **بگ فکس موڈ** - ٹوٹا ہوا کوڈ مرمت کریں

## 📱 موبائل اور ڈیسک ٹاپ رسائی

### اسی نیٹ ورک پر:
1. اپنے کمپیوٹر کا IP پتہ تلاش کریں:
   ```bash
   ipconfig
   ```
2. موبائل/ٹیبلیٹ سے رسائی: `http://YOUR_IP:8000`

### ڈیسک ٹاپ ایپ:
ایپ PWA-Ready ہے۔ Chrome/Edge میں:
1. http://localhost:8000 کھولیں
2. ایڈریس بار میں انسٹال آئیکن کلک کریں
3. ڈیسک ٹاپ ایپ کے طور پر انسٹال کریں

## 🛠️ ٹربل شوٹنگ

### Docker شروع نہیں ہو رہا؟
- کمپیوٹر دوبارہ شروع کریں
- BIOS میں ورچولائزیشن ایکٹیویٹ کریں
- Windows چیک کریں: Hyper-V, WSL 2

### پورٹ 8000 پہلے سے استعمال میں ہے؟
```bash
# docker-compose.yml میں پورٹ تبدیل کریں
ports:
  - "8001:8000"  # 8001 استعمال کریں
```

### AI جواب نہیں دے رہا؟
- چیک کریں Ollama چل رہا ہے: `docker ps`
- لاگز دیکھیں: `docker logs pro-ai-backend`
- کلاؤڈ API_keys شامل کریں (Gemini/OpenAI)

### Google Sign-In کام نہیں کر رہا؟
- Google Cloud Console میں OAuth کیڈنشلز چیک کریں
- redirect URI بالکل میچ ہونا چاہیے: `http://localhost:8000/api/auth/callback/google`
- Google+ API ایکٹیویٹ ہونا چاہیے

## 📊 لاگز دیکھیں

```bash
# بیک اینڈ لاگز
docker logs pro-ai-backend

# ڈیٹا بیس لاگز
docker logs pro-ai-postgres

# AI انجین لاگز
docker logs pro-ai-ollama

# تمام لاگز (فالو کریں)
docker-compose logs -f
```

## 🛑 ایپلیکیشن بند کریں

ٹرمینل میں `Ctrl+C` دبائیں، یا:
```bash
docker-compose down
```

## 🎉 آپ تیار ہیں!

آپ کا Professional AI اب چل رہا ہے:
- ✅ مکمل تصدیق (ای میل + Google OAuth)
- ✅ ایڈمن/مالک رسائی redr28126@gmail.com کے لیے
- ✅ ملٹی موڈ AI چیٹ
- ✅ کوڈ جنریشن
- ✅ سیکیورٹی انالیسیس
- ✅ بگ فکسنگ
- ✅ Docker کنٹینرائزیشن
- ✅ ایک کمانڈ سے شروع
- ✅ SEO بہتر بنایا
- ✅ موبائل اور ڈیسک ٹاپ تیار

**اب رسائی کریں:** http://localhost:8000