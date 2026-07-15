import { ref } from "vue";
import { createDownload, listDownloads, type DownloadItem } from "../api";

export interface DownloadOptions {
  format?: string;
  quality?: string;
  cover_option?: string;
}

export function useDownloads() {
  const items = ref<DownloadItem[]>([]);
  const loading = ref(false);
  const lastMessage = ref<string>("");

  async function refresh() {
    loading.value = true;
    try {
      items.value = await listDownloads();
    } finally {
      loading.value = false;
    }
  }

  async function enqueue(url: string, opts?: DownloadOptions) {
    const result = (await createDownload(url, opts)) as DownloadItem;
    lastMessage.value = result?.title ?? "ok";
    // Optimistic: add item to list without full refresh
    if (result && result.id) {
      items.value.unshift({
        id: result.id,
        url: result.url || url,
        title: result.title,
        artist: result.artist,
        album: result.album,
        status: "pending",
        progress: 0,
        format: result.format || "mp3",
      });
    }
    return result;
  }

  return { items, loading, lastMessage, refresh, enqueue };
}
