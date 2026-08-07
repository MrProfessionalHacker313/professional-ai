require("dotenv").config();

const path = require("path");
const {
  app,
  BrowserWindow,
  Tray,
  Menu,
  globalShortcut,
  Notification,
  nativeImage,
  ipcMain,
  shell,
} = require("electron");
const log = require("electron-log");
const { autoUpdater } = require("electron-updater");

log.initialize();
autoUpdater.logger = log;
autoUpdater.autoDownload = true;
autoUpdater.autoInstallOnAppQuit = true;

const APP_NAME = "Professional AI";
const WEB_URL = process.env.PRO_AI_WEB_URL || "http://localhost:8000";
const API_URL = process.env.PRO_AI_API_URL || "http://localhost:8000/api";
// OFFLINE-EVERYTHING: No Ollama. Local knowledge index + transformers.js on-device.
const OFFLINE_MODEL = process.env.PRO_AI_OFFLINE_MODEL || "qwen2.5-coder-0.5b";

let mainWindow = null;
let splashWindow = null;
let quickAskWindow = null;
let tray = null;

function buildIcon() {
  const pngPath = path.join(__dirname, "buildResources", "icon.png");
  const svgPath = path.join(__dirname, "buildResources", "icon.svg");

  let icon = nativeImage.createFromPath(pngPath);
  if (icon.isEmpty()) {
    icon = nativeImage.createFromPath(svgPath);
  }
  return icon;
}

function notify(title, body) {
  if (Notification.isSupported()) {
    new Notification({ title, body }).show();
  }
}

function createSplashWindow() {
  splashWindow = new BrowserWindow({
    width: 480,
    height: 300,
    frame: false,
    transparent: false,
    resizable: false,
    alwaysOnTop: true,
    icon: buildIcon(),
    webPreferences: {
      preload: path.join(__dirname, "preload.js"),
      contextIsolation: true,
      sandbox: true,
    },
  });

  splashWindow.loadFile(path.join(__dirname, "offline.html"), {
    query: { mode: "splash" },
  });
}

function createMainWindow() {
  mainWindow = new BrowserWindow({
    width: 1440,
    height: 920,
    minWidth: 1100,
    minHeight: 720,
    show: false,
    title: APP_NAME,
    icon: buildIcon(),
    autoHideMenuBar: true,
    backgroundColor: "#0b1220",
    webPreferences: {
      preload: path.join(__dirname, "preload.js"),
      contextIsolation: true,
      sandbox: true,
      partition: "persist:proai",
    },
  });

  mainWindow.on("ready-to-show", () => {
    if (splashWindow) {
      splashWindow.close();
      splashWindow = null;
    }
    mainWindow.show();
  });

  mainWindow.on("close", (event) => {
    if (!app.isQuiting) {
      event.preventDefault();
      mainWindow.hide();
      notify(APP_NAME, "Running in system tray. Press Ctrl+Shift+P for Quick Ask.");
    }
  });

  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url);
    return { action: "deny" };
  });

  mainWindow.webContents.on("did-fail-load", () => {
    mainWindow.loadFile(path.join(__dirname, "offline.html"), {
      query: {
        mode: "offline",
        web: WEB_URL,
        api: API_URL,
      },
    });
  });

  mainWindow.loadURL(WEB_URL);
}

function createQuickAskWindow() {
  if (quickAskWindow && !quickAskWindow.isDestroyed()) {
    quickAskWindow.show();
    quickAskWindow.focus();
    return;
  }

  quickAskWindow = new BrowserWindow({
    width: 520,
    height: 640,
    title: "Ask Pro AI",
    resizable: true,
    minimizable: false,
    maximizable: false,
    alwaysOnTop: true,
    skipTaskbar: false,
    icon: buildIcon(),
    webPreferences: {
      preload: path.join(__dirname, "preload.js"),
      contextIsolation: true,
      sandbox: true,
    },
  });

  quickAskWindow.on("closed", () => {
    quickAskWindow = null;
  });

  quickAskWindow.loadFile(path.join(__dirname, "quick-ask.html"));
}

function registerGlobalShortcuts() {
  const ok = globalShortcut.register("CommandOrControl+Shift+P", () => {
    createQuickAskWindow();
  });

  if (!ok) {
    log.warn("Global shortcut registration failed: Ctrl/Cmd+Shift+P");
  }
}

function createTray() {
  tray = new Tray(buildIcon());
  tray.setToolTip(APP_NAME);

  const menu = Menu.buildFromTemplate([
    {
      label: "Open Professional AI",
      click: () => {
        if (mainWindow) {
          mainWindow.show();
          mainWindow.focus();
        }
      },
    },
    {
      label: "Ask Pro AI (Ctrl+Shift+P)",
      click: () => createQuickAskWindow(),
    },
    {
      label: "Owner Admin Panel",
      click: () => {
        if (!mainWindow) {
          createMainWindow();
          return;
        }
        mainWindow.show();
        mainWindow.loadURL(`${WEB_URL}/admin`);
      },
    },
    { type: "separator" },
    {
      label: "Quit",
      click: () => {
        app.isQuiting = true;
        app.quit();
      },
    },
  ]);

  tray.setContextMenu(menu);
  tray.on("double-click", () => {
    if (mainWindow) {
      mainWindow.show();
      mainWindow.focus();
    }
  });
}

async function runQuickAsk(promptText) {
  const prompt = String(promptText || "").trim();
  if (!prompt) {
    return "Please enter a prompt.";
  }

  try {
    const response = await fetch(`${API_URL}/api/offline/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        prompt,
        mode: "chat",
        model: OFFLINE_MODEL,
        stream: false,
      }),
    });

    if (response.ok) {
      const data = await response.json();
      if (data && typeof data.response === "string") {
        return data.response;
      }
      if (data && typeof data.content === "string") {
        return data.content;
      }
    }
  } catch (error) {
    log.warn("Offline API quick ask failed", error);
  }

  // OFFLINE-EVERYTHING: No Ollama. The web app handles local AI via transformers.js.
  // If the API is unreachable, return a helpful offline message.
  return "📴 You are offline. Open Professional AI to use the local knowledge index and on-device AI engine.";
}

function wireIpc() {
  ipcMain.handle("desktop:quick-ask", async (_event, prompt) => {
    try {
      const text = await runQuickAsk(prompt);
      return { ok: true, text };
    } catch (error) {
      return { ok: false, text: "📴 Offline mode active. Open Professional AI for local AI answers." };
    }
  });

  ipcMain.handle("desktop:open-main", async () => {
    if (mainWindow) {
      mainWindow.show();
      mainWindow.focus();
      mainWindow.loadURL(`${WEB_URL}/chat`);
    }
    return { ok: true };
  });

  ipcMain.handle("desktop:notify", async (_event, payload) => {
    const title = (payload && payload.title) || APP_NAME;
    const body = (payload && payload.body) || "";
    notify(title, body);
    return { ok: true };
  });
}

function setupAutoUpdates() {
  autoUpdater.on("update-available", () => {
    notify(APP_NAME, "A new desktop update is downloading in the background.");
  });

  autoUpdater.on("update-downloaded", () => {
    notify(APP_NAME, "Update ready. It will install when you restart the app.");
  });

  autoUpdater.on("error", (error) => {
    log.warn("Auto-update error", error);
  });

  autoUpdater.checkForUpdatesAndNotify();
  setInterval(() => {
    autoUpdater.checkForUpdatesAndNotify();
  }, 30 * 60 * 1000);
}

app.whenReady().then(() => {
  createSplashWindow();
  createMainWindow();
  createTray();
  registerGlobalShortcuts();
  wireIpc();
  setupAutoUpdates();

  app.on("activate", () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createMainWindow();
    }
  });
});

app.on("will-quit", () => {
  globalShortcut.unregisterAll();
});

app.on("window-all-closed", () => {
  // Keep app alive in tray on desktop platforms.
});
