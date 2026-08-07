const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("proAI", {
  quickAsk: (prompt) => ipcRenderer.invoke("desktop:quick-ask", prompt),
  openMain: () => ipcRenderer.invoke("desktop:open-main"),
  notify: (title, body) => ipcRenderer.invoke("desktop:notify", { title, body }),
});
