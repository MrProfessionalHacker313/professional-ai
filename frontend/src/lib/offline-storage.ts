/**
 * Professional AI - Offline Storage Utility
 * IndexedDB-based local storage for offline mode.
 */

const DB_NAME = "professional-ai-offline";
const DB_VERSION = 1;

type StoreName = "chat_history" | "generated_code" | "translations" | "voice_recordings" | "sync_queue" | "cache";

class OfflineStorage {
  private db: IDBDatabase | null = null;

  async init(): Promise<IDBDatabase> {
    if (this.db) return this.db;

    return new Promise((resolve, reject) => {
      const request = indexedDB.open(DB_NAME, DB_VERSION);

      request.onerror = () => reject(request.error);
      request.onsuccess = () => {
        this.db = request.result;
        resolve(request.result);
      };

      request.onupgradeneeded = (event) => {
        const db = (event.target as IDBOpenDBRequest).result;

        const stores: StoreName[] = [
          "chat_history",
          "generated_code",
          "translations",
          "voice_recordings",
          "sync_queue",
          "cache",
        ];

        stores.forEach((storeName) => {
          if (!db.objectStoreNames.contains(storeName)) {
            const store = db.createObjectStore(storeName, { keyPath: "id" });
            store.createIndex("timestamp", "timestamp", { unique: false });
            store.createIndex("user_id", "user_id", { unique: false });
          }
        });
      };
    });
  }

  async get<T>(storeName: StoreName, id: string): Promise<T | null> {
    try {
      const db = await this.init();
      return new Promise((resolve, reject) => {
        const transaction = db.transaction(storeName, "readonly");
        const store = transaction.objectStore(storeName);
        const request = store.get(id);

        request.onerror = () => reject(request.error);
        request.onsuccess = () => resolve(request.result?.value ?? null);
      });
    } catch {
      return null;
    }
  }

  async getAll<T>(storeName: StoreName, user_id?: string): Promise<T[]> {
    try {
      const db = await this.init();
      return new Promise((resolve, reject) => {
        const transaction = db.transaction(storeName, "readonly");
        const store = transaction.objectStore(storeName);
        const request = store.getAll();

        request.onerror = () => reject(request.error);
        request.onsuccess = () => {
          let results = request.result.map((r) => r.value);
          if (user_id) {
            results = results.filter((item: any) => item.user_id === user_id);
          }
          resolve(results);
        };
      });
    } catch {
      return [];
    }
  }

  async set<T>(storeName: StoreName, id: string, value: T, user_id?: string): Promise<void> {
    try {
      const db = await this.init();
      return new Promise((resolve, reject) => {
        const transaction = db.transaction(storeName, "readwrite");
        const store = transaction.objectStore(storeName);
        const request = store.put({
          id,
          value,
          user_id,
          timestamp: Date.now(),
        });

        request.onerror = () => reject(request.error);
        request.onsuccess = () => resolve();
      });
    } catch (error) {
      console.error(`Failed to set ${storeName}:`, error);
    }
  }

  async delete(storeName: StoreName, id: string): Promise<void> {
    try {
      const db = await this.init();
      return new Promise((resolve, reject) => {
        const transaction = db.transaction(storeName, "readwrite");
        const store = transaction.objectStore(storeName);
        const request = store.delete(id);

        request.onerror = () => reject(request.error);
        request.onsuccess = () => resolve();
      });
    } catch (error) {
      console.error(`Failed to delete ${storeName}:`, error);
    }
  }

  async clear(storeName: StoreName): Promise<void> {
    try {
      const db = await this.init();
      return new Promise((resolve, reject) => {
        const transaction = db.transaction(storeName, "readwrite");
        const store = transaction.objectStore(storeName);
        const request = store.clear();

        request.onerror = () => reject(request.error);
        request.onsuccess = () => resolve();
      });
    } catch (error) {
      console.error(`Failed to clear ${storeName}:`, error);
    }
  }

  async count(storeName: StoreName): Promise<number> {
    try {
      const db = await this.init();
      return new Promise((resolve, reject) => {
        const transaction = db.transaction(storeName, "readonly");
        const store = transaction.objectStore(storeName);
        const request = store.count();

        request.onerror = () => reject(request.error);
        request.onsuccess = () => resolve(request.result);
      });
    } catch {
      return 0;
    }
  }
}

export const offlineStorage = new OfflineStorage();
