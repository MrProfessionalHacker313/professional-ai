/**
 * Professional AI - Offline API Client
 * Handles API calls with automatic offline mode support.
 */

import api from './api'

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface OfflineChatMessage {
  role: "user" | "assistant" | "system";
  content: string;
  timestamp: number;
}

export interface OfflineApiOptions {
  method?: "GET" | "POST" | "PUT" | "DELETE";
  body?: any;
  headers?: Record<string, string>;
  useOfflineCache?: boolean;
}

async function getAuthHeaders(): Promise<Record<string, string>> {
  const token = localStorage.getItem("access_token");
  return token ? { Authorization: `Bearer ${token}` } : {};
}

export async function offlineChat(
  messages: OfflineChatMessage[],
  options: OfflineApiOptions = {}
): Promise<any> {
  const { method = "POST", body, headers = {} } = options;

  const lastMessage = messages[messages.length - 1];
  const requestBody = {
    prompt: lastMessage?.content || "",
    mode: body?.mode || "chat",
    model: body?.model,
    stream: false,
  };

  try {
    const response = await fetch(`${API_BASE}/api/offline/chat`, {
      method,
      headers: {
        "Content-Type": "application/json",
        ...headers,
        ...(await getAuthHeaders()),
      },
      body: JSON.stringify(requestBody),
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error("Offline chat failed:", error);
    throw error;
  }
}

export async function offlineTranscribe(
  audioBlob: Blob,
  language = "en"
): Promise<{ text: string; confidence: number; offline: boolean }> {
  const reader = new FileReader();
  const base64 = await new Promise<string>((resolve, reject) => {
    reader.onloadend = () => resolve(reader.result as string);
    reader.onerror = reject;
    reader.readAsDataURL(audioBlob);
  });

  const base64Data = base64.split(",")[1];

  const response = await api.post(`${API_BASE}/api/offline/voice/transcribe`, {
    audio_base64: base64Data,
    language,
  });

  return response.data
}

export async function offlineTranslate(
  text: string,
  sourceLang: string,
  targetLang: string
): Promise<{ translated_text: string; offline: boolean }> {
  const response = await fetch(`${API_BASE}/api/offline/translate`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(await getAuthHeaders()),
    },
    body: JSON.stringify({
      text,
      source_lang: sourceLang,
      target_lang: targetLang,
    }),
  });

  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`);
  }

  return response.json();
}

export async function queueOfflineSync(
  itemType: string,
  data: Record<string, unknown>
): Promise<{ item_id: string; status: string }> {
  const response = await fetch(`${API_BASE}/api/offline/sync/queue`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(await getAuthHeaders()),
    },
    body: JSON.stringify({ item_type: itemType, data }),
  });

  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`);
  }

  return response.json();
}

export async function triggerSyncNow(): Promise<any> {
  const response = await fetch(`${API_BASE}/api/offline/sync/now`, {
    method: "POST",
    headers: {
      ...(await getAuthHeaders()),
    },
  });

  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`);
  }

  return response.json();
}

export async function getOfflineStatus(): Promise<any> {
  const response = await fetch(`${API_BASE}/api/offline/status`, {
    headers: {
      ...(await getAuthHeaders()),
    },
  });

  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`);
  }

  return response.json();
}

export async function downloadVoiceModel(languageCode: string): Promise<any> {
  const response = await fetch(
    `${API_BASE}/api/offline/voice/models/download/${languageCode}`,
    {
      method: "POST",
      headers: {
        ...(await getAuthHeaders()),
      },
    }
  );

  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`);
  }

  return response.json();
}
