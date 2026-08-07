# Professional AI Desktop

Electron desktop app for Professional AI with system tray, global quick-ask shortcut, offline Ollama fallback, and auto-updates.

## Features

- Full Professional AI web interface in a desktop shell
- Global shortcut: `Ctrl+Shift+P` (or `Cmd+Shift+P` on macOS) for "Ask Pro AI"
- System tray quick access + owner admin panel shortcut
- Native notifications via desktop bridge
- Offline local fallback via Ollama (`llama3.1:70b` by default)
- Auto-update via `electron-updater`

## Environment

Copy `.env.example` to `.env` and update values if needed.

## Run (development)

1. Start backend and frontend servers of Professional AI.
2. In this `desktop` folder:

```bash
npm install
npm run dev
```

## Build installers

```bash
npm run dist
```

Artifacts are generated in `desktop/release/`:

- Windows: `.exe` (NSIS)
- macOS: `.dmg`
- Linux: `.AppImage`

## Auto-update setup

- `electron-builder` publish provider is configured as generic URL.
- Host generated release files + update metadata at your update endpoint.
- Desktop app checks for updates on launch and every 30 minutes.

## Sign-in and owner mode

Desktop uses the same secure web auth flows (Google, Microsoft, SSO, GitHub, Apple, phone OTP, 2FA, passkeys).
Owner mode is available through the tray menu "Owner Admin Panel".
