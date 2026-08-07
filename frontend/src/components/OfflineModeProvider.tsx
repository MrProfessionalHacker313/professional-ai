"use client";

/**
 * Professional AI - Offline Mode Provider
 * Wraps the app with offline mode detection and sync capabilities.
 */

import React, { createContext, useContext, useEffect, useState, ReactNode } from "react";
import { useOfflineMode, OfflineStatus } from "@/hooks/useOfflineMode";
import { offlineStorage } from "@/lib/offline-storage";

interface OfflineContextValue {
  status: OfflineStatus | null;
  loading: boolean;
  isOnline: boolean;
  mode: "online" | "low_bandwidth" | "offline";
  isOffline: boolean;
  isLowBandwidth: boolean;
  capabilities: any;
  generateResponse: (
    prompt: string,
    options?: { mode?: string; model?: string; stream?: boolean }
  ) => Promise<any>;
  transcribeVoice: (audioBlob: Blob, language?: string) => Promise<any>;
  translateText: (text: string, sourceLang: string, targetLang: string) => Promise<any>;
  queueForSync: (itemType: string, data: Record<string, unknown>) => Promise<any>;
  syncNow: () => Promise<any>;
  refresh: () => void;
}

const OfflineContext = createContext<OfflineContextValue | null>(null);

export function OfflineModeProvider({ children }: { children: ReactNode }) {
  const offline = useOfflineMode();

  useEffect(() => {
    // Initialize offline storage
    offlineStorage.init();

    // Queue any pending local data for sync when coming online
    if (offline.isOnline && offline.status) {
      const pendingSync = offline.status.sync?.pendingItems || 0;
      if (pendingSync > 0) {
        console.log(`[OfflineMode] Auto-syncing ${pendingSync} pending items`);
      }
    }
  }, [offline.isOnline, offline.status]);

  return (
    <OfflineContext.Provider
      value={{
        status: offline.status,
        loading: offline.loading,
        isOnline: offline.isOnline,
        mode: offline.mode,
        isOffline: offline.isOffline,
        isLowBandwidth: offline.isLowBandwidth,
        capabilities: offline.capabilities,
        generateResponse: offline.generateResponse,
        transcribeVoice: offline.transcribeVoice,
        translateText: offline.translateText,
        queueForSync: offline.queueForSync,
        syncNow: offline.syncNow,
        refresh: offline.refresh,
      }}
    >
      {children}
    </OfflineContext.Provider>
  );
}

export function useOffline(): OfflineContextValue {
  const context = useContext(OfflineContext);
  if (!context) {
    throw new Error("useOffline must be used within an OfflineModeProvider");
  }
  return context;
}
