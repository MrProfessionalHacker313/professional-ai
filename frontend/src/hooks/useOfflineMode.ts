"use client";

/**
 * Professional AI - Offline Mode Hook
 * Detects connectivity, switches models, manages offline features.
 */

import { useState, useEffect, useCallback, useRef } from "react";

export type ConnectionMode = "online" | "low_bandwidth" | "offline";

export interface OfflineCapabilities {
  mode: ConnectionMode;
  ollamaAvailable: boolean;
  voiceAvailable: boolean;
  translationAvailable: boolean;
  availableModels: string[];
  supportedLanguages: string[];
  compressionEnabled: boolean;
  streamingEnabled: boolean;
}

export interface OfflineStatus {
  mode: ConnectionMode;
  capabilities: OfflineCapabilities;
  connectivity: {
    isOnline: boolean;
    quality: ConnectionMode;
    latencyMs: number;
  };
  sync: {
    totalItems: number;
    pendingItems: number;
    syncedItems: number;
    failedItems: number;
    conflicts: number;
    isSyncing: boolean;
  };
  cache: {
    totalEntries: number;
    activeEntries: number;
    totalSizeMb: number;
  };
  availableModels: string[];
}

interface OfflineEngineState {
  status: OfflineStatus | null;
  loading: boolean;
  error: string | null;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

function getAccessTokenFromCookie(): string | null {
  if (typeof window === 'undefined') return null
  const token = document.cookie
    .split('; ')
    .find((row) => row.startsWith('access_token='))
    ?.split('=')[1]
  return token ? decodeURIComponent(token) : null
}

export function useOfflineMode() {
  const [state, setState] = useState<OfflineEngineState>({
    status: null,
    loading: true,
    error: null,
  });
  const [isOnline, setIsOnline] = useState<boolean>(true);
  const [mode, setMode] = useState<ConnectionMode>("online");
  const intervalRef = useRef<NodeJS.Timeout | null>(null);
  const listenersRef = useRef<Set<(mode: ConnectionMode) => void>>(new Set());

  const fetchStatus = useCallback(async () => {
    try {
      const accessToken = getAccessTokenFromCookie()
      const headers: Record<string, string> = {}
      if (accessToken) {
        headers.Authorization = `Bearer ${accessToken}`
      }
      const response = await fetch(`${API_BASE}/api/offline/status`, {
        headers,
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const data = await response.json();
      setState({ status: data, loading: false, error: null });

      const newMode = (data.mode || "online") as ConnectionMode;
      const wasOnline = isOnline;
      const nowOnline = data.connectivity?.is_online ?? true;

      setIsOnline(nowOnline);
      setMode(newMode);

      if (wasOnline !== nowOnline || mode !== newMode) {
        listenersRef.current.forEach((listener) => listener(newMode));
      }
    } catch (error) {
      // If API fails, assume offline
      setState((prev) => ({
        ...prev,
        loading: false,
        error: error instanceof Error ? error.message : "Unknown error",
      }));
      setIsOnline(false);
      setMode("offline");
    }
  }, [isOnline, mode]);

  // Browser online/offline events
  useEffect(() => {
    const handleOnline = () => {
      fetchStatus();
      listenersRef.current.forEach((listener) => listener("online"));
    };

    const handleOffline = () => {
      setState((prev) => ({
        ...prev,
        status: prev.status
          ? {
              ...prev.status,
              mode: "offline",
              connectivity: { isOnline: false, quality: "offline", latencyMs: 0 },
            }
          : null,
      }));
      setIsOnline(false);
      setMode("offline");
      listenersRef.current.forEach((listener) => listener("offline"));
    };

    window.addEventListener("online", handleOnline);
    window.addEventListener("offline", handleOffline);

    return () => {
      window.removeEventListener("online", handleOnline);
      window.removeEventListener("offline", handleOffline);
    };
  }, [fetchStatus]);

  // Periodic status check
  useEffect(() => {
    fetchStatus();
    intervalRef.current = setInterval(fetchStatus, 30000); // Check every 30s

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [fetchStatus]);

  const addListener = useCallback((listener: (mode: ConnectionMode) => void) => {
    listenersRef.current.add(listener);
    return () => listenersRef.current.delete(listener);
  }, []);

  const generateResponse = useCallback(
    async (
      prompt: string,
      options: {
        mode?: string;
        model?: string;
        stream?: boolean;
      } = {}
    ) => {
      const accessToken = getAccessTokenFromCookie()
      const headers: Record<string, string> = { "Content-Type": "application/json" }
      if (accessToken) {
        headers.Authorization = `Bearer ${accessToken}`
      }
      const response = await fetch(`${API_BASE}/api/offline/chat`, {
        method: "POST",
        headers,
        body: JSON.stringify({
          prompt,
          mode: options.mode || "chat",
          model: options.model,
          stream: options.stream || false,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      return response.json();
    },
    []
  );

  const transcribeVoice = useCallback(async (audioBlob: Blob, language = "en") => {
    const reader = new FileReader();
    const base64 = await new Promise<string>((resolve, reject) => {
      reader.onloadend = () => resolve(reader.result as string);
      reader.onerror = reject;
      reader.readAsDataURL(audioBlob);
    });

    const base64Data = base64.split(",")[1];

    const accessToken = getAccessTokenFromCookie()
    const headers: Record<string, string> = { "Content-Type": "application/json" }
    if (accessToken) {
      headers.Authorization = `Bearer ${accessToken}`
    }
    const response = await fetch(`${API_BASE}/api/offline/voice/transcribe`, {
      method: "POST",
      headers,
      body: JSON.stringify({
        audio_base64: base64Data,
        language,
      }),
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    return response.json();
  }, []);

  const translateText = useCallback(
    async (text: string, sourceLang: string, targetLang: string) => {
      const accessToken = getAccessTokenFromCookie()
      const headers: Record<string, string> = { "Content-Type": "application/json" }
      if (accessToken) {
        headers.Authorization = `Bearer ${accessToken}`
      }
      const response = await fetch(`${API_BASE}/api/offline/translate`, {
        method: "POST",
        headers,
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
    },
    []
  );

  const queueForSync = useCallback(
    async (itemType: string, data: Record<string, unknown>) => {
      const accessToken = getAccessTokenFromCookie()
      const headers: Record<string, string> = { "Content-Type": "application/json" }
      if (accessToken) {
        headers.Authorization = `Bearer ${accessToken}`
      }
      const response = await fetch(`${API_BASE}/api/offline/sync/queue`, {
        method: "POST",
        headers,
        body: JSON.stringify({ item_type: itemType, data }),
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      return response.json();
    },
    []
  );

  const syncNow = useCallback(async () => {
    const accessToken = getAccessTokenFromCookie()
    const headers: Record<string, string> = {}
    if (accessToken) {
      headers.Authorization = `Bearer ${accessToken}`
    }
    const response = await fetch(`${API_BASE}/api/offline/sync/now`, {
      method: "POST",
      headers,
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    return response.json();
  }, []);

  const refresh = useCallback(() => {
    fetchStatus();
  }, [fetchStatus]);

  return {
    status: state.status,
    loading: state.loading,
    error: state.error,
    isOnline,
    mode,
    isOffline: mode === "offline",
    isLowBandwidth: mode === "low_bandwidth",
    capabilities: state.status?.capabilities,
    generateResponse,
    transcribeVoice,
    translateText,
    queueForSync,
    syncNow,
    refresh,
    addListener,
  };
}
