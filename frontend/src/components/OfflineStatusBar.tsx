'use client'

import { useState, useEffect } from 'react'
import { Wifi, WifiOff, CloudOff, RefreshCw, Download } from 'lucide-react'
import { useConnectivity } from '@/lib/use-connectivity'
import { offlineSync, SyncStatus } from '@/lib/offline-sync'
import { offlineAI } from '@/lib/offline-ai'

export default function OfflineStatusBar() {
  const { isOnline, status, latency } = useConnectivity()
  const [syncStatus, setSyncStatus] = useState<SyncStatus | null>(null)
  const [modelDownloaded, setModelDownloaded] = useState(false)
  const [showDetails, setShowDetails] = useState(false)

  useEffect(() => {
    offlineSync.init()
    offlineSync.addListener(setSyncStatus)
    offlineSync.getStatus().then(setSyncStatus)
    setModelDownloaded(offlineAI.isModelDownloaded())
  }, [])

  const isOffline = !isOnline || status === 'offline'
  const isLowBandwidth = status === 'low-bandwidth'

  return (
    <div className="fixed bottom-0 left-0 right-0 z-50">
      <div
        className={`flex items-center justify-between px-4 py-1.5 text-xs font-medium ${
          isOffline
            ? 'bg-red-950/90 text-red-200 border-t border-red-800'
            : isLowBandwidth
            ? 'bg-yellow-950/90 text-yellow-200 border-t border-yellow-800'
            : 'bg-emerald-950/90 text-emerald-200 border-t border-emerald-800'
        }`}
      >
        <button
          onClick={() => setShowDetails(!showDetails)}
          className="flex items-center gap-2 hover:opacity-80 transition-opacity"
        >
          {isOffline ? (
            <>
              <WifiOff className="w-3.5 h-3.5" />
              <span>📴 OFFLINE (Local Mode)</span>
            </>
          ) : isLowBandwidth ? (
            <>
              <CloudOff className="w-3.5 h-3.5" />
              <span>🌐 LOW BANDWIDTH (Reduced Mode)</span>
            </>
          ) : (
            <>
              <Wifi className="w-3.5 h-3.5" />
              <span>🌐 ONLINE (Full Power)</span>
            </>
          )}
          {latency !== null && isOnline && (
            <span className="opacity-60">{latency}ms</span>
          )}
        </button>

        <div className="flex items-center gap-3">
          {syncStatus && syncStatus.pending > 0 && (
            <button
              onClick={() => offlineSync.syncPending()}
              className="flex items-center gap-1 hover:opacity-80 transition-opacity"
              title={`${syncStatus.pending} items waiting to sync`}
            >
              <RefreshCw className="w-3 h-3" />
              <span>{syncStatus.pending} pending</span>
            </button>
          )}

          {!modelDownloaded && isOnline && (
            <button
              onClick={() => window.dispatchEvent(new CustomEvent('proai-download-model'))}
              className="flex items-center gap-1 hover:opacity-80 transition-opacity"
              title="Download Offline AI Pack"
            >
              <Download className="w-3 h-3" />
              <span>Download Offline AI Pack</span>
            </button>
          )}

          {modelDownloaded && (
            <span className="opacity-60" title="Offline AI model ready">
              🤖 Local AI Ready
            </span>
          )}
        </div>
      </div>

      {showDetails && (
        <div className="bg-gray-950/95 border-t border-gray-800 px-4 py-3 text-xs text-gray-300">
          <div className="max-w-4xl mx-auto grid grid-cols-2 md:grid-cols-4 gap-3">
            <div>
              <div className="text-gray-500 mb-1">Connection</div>
              <div className="font-medium">
                {isOffline ? 'Offline' : isLowBandwidth ? 'Low Bandwidth' : 'Online'}
              </div>
            </div>
            <div>
              <div className="text-gray-500 mb-1">Local AI</div>
              <div className="font-medium">
                {modelDownloaded ? 'Model Ready' : 'Knowledge Index Only'}
              </div>
            </div>
            <div>
              <div className="text-gray-500 mb-1">Sync Queue</div>
              <div className="font-medium">
                {syncStatus ? `${syncStatus.pending} pending / ${syncStatus.synced} synced` : '...'}
              </div>
            </div>
            <div>
              <div className="text-gray-500 mb-1">Offline Search</div>
              <div className="font-medium">Knowledge Index Active</div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}