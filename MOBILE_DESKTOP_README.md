# Professional AI — Mobile + Desktop Apps

Complete guide for building, installing, and distributing the Professional AI mobile and desktop apps.

---

## Table of Contents
1. [Overview](#overview)
2. [Mobile App (Flutter)](#mobile-app-flutter)
3. [Desktop App (Electron)](#desktop-app-electron)
4. [Download Page](#download-page)
5. [Install Guide Page](#install-guide-page)
6. [Store Listings](#store-listings)
7. [Building for Production](#building-for-production)
8. [Distribution](#distribution)
9. [Troubleshooting](#troubleshooting)

---

## Overview

Professional AI is available on **all platforms**:

| Platform | Technology | Files | Install Method |
|----------|-----------|-------|----------------|
| **Android** | Flutter | `app-release.apk` | APK download or Google Play |
| **iOS** | Flutter | `.ipa` / TestFlight | App Store or TestFlight |
| **Windows** | Electron | `ProfessionalAI-Setup.exe` | Double-click installer |
| **macOS** | Electron | `ProfessionalAI.dmg` | Drag to Applications |
| **Linux** | Electron | `ProfessionalAI.AppImage` | chmod +x and run |
| **Web** | Next.js | Browser | https://professionalai.com |

**All platforms share the same account, same features, and sync in real-time.**

---

## Mobile App (Flutter)

### Project Structure

```
mobile/
├── lib/
│   ├── main.dart                    # App entry point, splash screen
│   ├── screens/
│   │   ├── login_screen.dart        # Google, Apple, GitHub, Phone sign-in
│   │   ├── two_factor_screen.dart   # 2FA TOTP verification
│   │   ├── passkey_screen.dart      # Passkey / biometric setup
│   │   ├── dashboard_screen.dart    # Main dashboard with feature grid
│   │   ├── chat_screen.dart         # AI chat interface
│   │   ├── code_screen.dart         # Code generation
│   │   ├── media_screen.dart        # Image/video/animation generation
│   │   ├── vault_screen.dart        # Secure encrypted vault
│   │   ├── pricing_screen.dart      # Subscription plans
│   │   └── admin_screen.dart        # Owner admin panel
│   └── services/
│       ├── auth_service.dart        # Authentication logic
│       ├── api_service.dart         # Backend API calls
│       └── offline_service.dart     # Offline mode support
├── android/
│   ├── app/
│   │   ├── build.gradle.kts         # Android build config
│   │   └── src/main/AndroidManifest.xml
│   └── build.gradle.kts
├── ios/
│   └── Runner/
│       └── Info.plist               # iOS config
├── pubspec.yaml                     # Flutter dependencies
└── assets/
    └── images/
        └── eagle_logo.png           # App logo
```

### Flutter Dependencies

```yaml
dependencies:
  flutter_web_auth_2: ^4.1.0      # OAuth flow
  google_sign_in: ^6.2.1           # Google Sign-In
  sign_in_with_apple: ^6.1.0       # Apple Sign-In
  twitter_login: ^4.4.2            # Twitter Sign-In
  http: ^1.2.0                     # API calls
  shared_preferences: ^2.2.2       # Local storage
  flutter_secure_storage: ^9.0.0   # Secure token storage
  provider: ^6.1.1                 # State management
  connectivity_plus: ^5.0.2        # Network detection
  hive: ^2.2.3                     # Offline storage
  url_launcher: ^6.2.3             # Open URLs
```

### Building the Mobile App

#### Prerequisites
- Flutter SDK 3.13.0+
- Android Studio (for Android builds)
- Xcode 15+ (for iOS builds, macOS only)
- CocoaPods (`sudo gem install cocoapods`)

#### Build APK (Android)

```bash
cd C:\Users\GrafiX\Desktop\professional-ai\mobile

# 1. Install dependencies
flutter pub get

# 2. Build release APK
flutter build apk --release

# Output: mobile\build\app\outputs\flutter-apk\app-release.apk
```

#### Build App Bundle (Google Play)

```bash
flutter build appbundle --release

# Output: mobile\build\app\outputs\bundle\release\app-release.aab
```

#### Build iOS (App Store / TestFlight)

```bash
cd C:\Users\GrafiX\Desktop\professional-ai\mobile

# 1. Install pods
cd ios && pod install && cd ..

# 2. Build iOS
flutter build ios --release

# 3. Open Xcode for archive
open ios/Runner.xcworkspace

# 4. In Xcode: Product > Archive > Distribute to App Store / TestFlight
```

---

## Desktop App (Electron)

### Project Structure

```
desktop/
├── main.js                  # Electron main process
├── preload.js               # Preload script (IPC bridge)
├── quick-ask.html           # Quick-ask popup (Ctrl+Shift+P)
├── offline.html             # Offline fallback page
├── package.json             # Electron config + electron-builder
├── .env.example             # Environment variables
├── buildResources/
│   ├── icon.png             # App icon (256x256)
│   └── icon.svg             # Vector icon
├── build.bat                # Windows build script
├── build-mac.sh             # macOS build script
└── build-linux.sh           # Linux build script
```

### Electron Features

- **System Tray**: Minimize to tray, quick access menu
- **Global Shortcut**: Ctrl+Shift+P (Windows/Linux) or Cmd+Shift+P (Mac) opens Quick Ask
- **Auto-Updates**: Checks for updates every 30 minutes via electron-updater
- **Offline Fallback**: Shows offline page when backend unreachable
- **Quick Ask**: Floating popup for quick AI questions without opening full app
- **Owner Admin**: Direct access to admin panel from tray menu

### Building the Desktop App

#### Prerequisites
- Node.js 18+
- npm or yarn
- Windows/Mac/Linux matching target platform

#### Build Windows (.exe)

```bash
cd C:\Users\GrafiX\Desktop\professional-ai\desktop

# 1. Install dependencies
npm install

# 2. Build installer
npm run dist -- --win

# Output: desktop\release\Professional AI Setup.exe
# Or run build.bat for automated build
```

#### Build macOS (.dmg)

```bash
cd desktop
npm install
npm run dist -- --mac

# Output: desktop/release/Professional AI.dmg
# Or run: bash build-mac.sh
```

#### Build Linux (.AppImage)

```bash
cd desktop
npm install
npm run dist -- --linux

# Output: desktop/release/Professional AI.AppImage
# Or run: bash build-linux.sh
```

#### Development Mode

```bash
cd desktop
npm install
npm start

# Opens Electron app pointing to http://localhost:8000
```

### Electron Environment Variables

```env
# .env file in desktop/
PRO_AI_WEB_URL=http://localhost:8000
PRO_AI_API_URL=http://localhost:8000/api
PRO_AI_OFFLINE_MODEL=qwen2.5-coder-0.5b
```

---

## Download Page

Location: `frontend/src/app/download/page.tsx`

The download page (`/download`) provides:
- 6 download buttons: Android APK, iOS App Store, Windows .exe, Mac .dmg, Linux .AppImage, Web
- SEO optimized with schema.org structured data
- Links to local files and store URLs
- PWA install option

### Download URLs (Production)

Replace these with actual hosted URLs:

| Platform | Local Path | Production URL |
|----------|-----------|----------------|
| Android APK | `/downloads/android/app-release.apk` | `https://downloads.professionalai.com/android/app-release.apk` |
| iOS App Store | N/A | `https://apps.apple.com/app/professional-ai/id000000000` |
| Windows | `/downloads/desktop/Professional-AI-Setup.exe` | `https://downloads.professionalai.com/desktop/Professional-AI-Setup.exe` |
| macOS | `/downloads/desktop/Professional-AI.dmg` | `https://downloads.professionalai.com/desktop/Professional-AI.dmg` |
| Linux | `/downloads/desktop/Professional-AI.AppImage` | `https://downloads.professionalai.com/desktop/Professional-AI.AppImage` |

### Serving Downloads from Backend

Add this to `backend/app/main.py` to serve local downloads:

```python
from fastapi.static import StaticFiles
app.mount("/downloads", StaticFiles(directory="downloads"), name="downloads")
```

Place built files in `C:\Users\GrafiX\Desktop\professional-ai\downloads\`:
```
downloads/
├── android/
│   └── app-release.apk
├── desktop/
│   ├── Professional-AI-Setup.exe
│   ├── Professional-AI.dmg
│   └── Professional-AI.AppImage
```

---

## Install Guide Page

Location: `frontend/src/app/install-guide/page.tsx`

The install guide (`/install-guide`) provides step-by-step instructions for:
- Android: Download APK, enable unknown sources, install
- iOS: App Store / TestFlight download
- Windows: Run .exe installer
- macOS: Open .dmg, drag to Applications
- Linux: chmod +x, run AppImage
- Web: Open browser, add to home screen

---

## Store Listings

### Google Play Store
Location: `mobile/store-listings/google-play.txt`

- App title, short description, full description
- Subscription plans (Free, Pro $9.99, Enterprise $99.99)
- Keywords: AI, chat, code, programming, developer, security, vault, media
- Permissions explanation
- Privacy policy link

### Apple App Store
Location: `mobile/store-listings/app-store.txt`

- App name, subtitle, description
- Subscription plans with pricing
- Screenshot requirements (8 screens for 6.7" and 5.5")
- App Preview video recommendation (30 seconds)
- Keywords for ASO
- Privacy policy and support links

---

## Building for Production

### Complete Build Pipeline

```bash
# 1. Build frontend
cd C:\Users\GrafiX\Desktop\professional-ai
docker compose up --build -d

# 2. Build mobile apps
cd mobile
flutter pub get
flutter build apk --release
flutter build appbundle --release
flutter build ios --release

# 3. Build desktop apps
cd ../desktop
npm install
npm run dist -- --win --mac --linux

# 4. Collect all artifacts
# - mobile/build/app/outputs/flutter-apk/app-release.apk
# - mobile/build/app/outputs/bundle/release/app-release.aab
# - desktop/release/Professional AI Setup.exe
# - desktop/release/Professional AI.dmg
# - desktop/release/Professional AI.AppImage
```

### Code Signing

#### Android
```bash
# Generate keystore (once)
keytool -genkey -v -keystore professional-ai.keystore -keyalg RSA -keysize 2048 -validity 10000

# Sign APK
jarsigner -verbose -sigalg SHA1withRSA -digestalg SHA1 -keystore professional-ai.keystore app-release.apk professional-ai

# Verify
jarsigner -verify -verbose -certs app-release.apk
```

#### iOS
- Requires Apple Developer Account ($99/year)
- In Xcode: Signing & Capabilities > Team
- Archive and upload to App Store Connect

#### Windows
```bash
# In desktop/package.json, configure signing:
"win": {
  "signingHashAlgorithms": ["sha256"],
  "certificateFile": "cert.pfx",
  "certificatePassword": "password"
}
```

#### macOS
```bash
# Notarization (Apple Developer Account required)
# In desktop/package.json:
"mac": {
  "identity": "Developer ID Application: Your Name (TEAM_ID)",
  "hardenedRuntime": true,
  "gatekeeperAssess": false
}
```

---

## Distribution

### Hosting Downloads

1. **Upload to CDN** (Cloudflare, AWS CloudFront, etc.)
2. **Update download page URLs** to point to CDN
3. **Enable HTTPS** on download domain
4. **Add checksums** (SHA256) for verification

### Google Play Store
1. Create developer account ($25 one-time fee)
2. Upload `app-release.aab`
3. Fill store listing from `mobile/store-listings/google-play.txt`
4. Upload screenshots (8 required, 4 optional)
5. Set pricing and distribution
6. Submit for review (1-3 days)

### Apple App Store
1. Create Apple Developer account ($99/year)
2. Upload IPA via Xcode or Transporter
3. Fill App Store Connect listing from `mobile/store-listings/app-store.txt`
4. Upload screenshots (required for each device size)
5. Submit for review (1-3 days)

### Desktop Distribution
1. **Direct download**: Host .exe/.dmg/.AppImage on website
2. **Auto-updates**: Configure electron-updater with update server
3. **Microsoft Store**: Package as MSIX for Windows Store
4. **Mac App Store**: Requires special entitlements and review

---

## Troubleshooting

### Flutter Build Issues

**"Flutter SDK not found"**
```bash
flutter doctor
# Follow instructions to install Flutter
```

**Gradle build fails**
```bash
cd mobile/android
./gradlew clean
cd ..
flutter clean
flutter pub get
```

**iOS build fails**
```bash
cd ios
pod deintegrate
pod install
cd ..
flutter clean
```

### Electron Build Issues

**"electron-builder not found"**
```bash
cd desktop
npm install
```

**NSIS installer fails on Windows**
```bash
# Install NSIS
choco install nsis
```

**Code signing fails**
```bash
# For development, disable signing in package.json:
"win": { "signingHashAlgorithms": [] }
"mac": { "identity": null }
```

---

## Account Sync

All platforms use the same backend API (`http://localhost:8000/api` or production URL). Users sign in once and access:
- Chat history
- Code projects
- Vault items
- Media library
- Settings and preferences

**Offline mode**: Mobile and desktop apps queue operations locally and sync when online.

---

## Support

- Documentation: https://professionalai.com/docs
- Support: support@professionalai.com
- GitHub: https://github.com/professionalai/professionalai

---

## License

Professional AI is proprietary software. All rights reserved.
