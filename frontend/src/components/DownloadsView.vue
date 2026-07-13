<script setup lang="ts">
import { computed, onMounted, onUnmounted } from "vue";
import { useDownloads } from "../composables/useDownloads";
import { useSSE } from "../composables/useSSE";
import { deleteDownload, retryDownload } from "../api";
import type { DownloadItem } from "../api";

const { items, loading, refresh } = useDownloads();
const { connect, close, getLatest } = useSSE("/api/downloads/events");

function getProgress(item: DownloadItem): number {
  const ev = getLatest(item.id);
  if (ev && typeof ev.progress === "number") {
    return Math.max(ev.progress, item.progress || 0);
  }
  return item.progress || 0;
}

function getPhase(item: DownloadItem): string | undefined {
  const ev = getLatest(item.id);
  return (ev?.phase as string) || item.phase;
}

function getStatus(item: DownloadItem): string {
  const ev = getLatest(item.id);
  return (ev?.status as string) || item.status;
}

onMounted(() => {
  refresh();
  connect();
});

onUnmounted(() => close());

const activeItems = computed(() =>
  items.value.filter((i) => {
    const s = getStatus(i);
    return s === "pending" || s === "downloading";
  }),
);
const doneItems = computed(() => items.value.filter((i) => getStatus(i) === "done"));
const errorItems = computed(() => items.value.filter((i) => getStatus(i) === "error"));

const PHASE_LABELS: Record<string, string> = {
  resolving: "Mengambil info...",
  downloading: "Mengunduh...",
  transcoding: "Transcode...",
  "embedding cover": "Menanam cover...",
  "embedding lyrics": "Menanam lirik...",
  "writing metadata": "Menulis metadata...",
  done: "Selesai",
};

function phaseLabel(phase: string | undefined): string {
  return PHASE_LABELS[phase || ""] || phase || "";
}

async function handleDelete(item: DownloadItem) {
  if (!confirm(`Hapus "${item.title || item.url}" dari daftar dan disk?`)) return;
  await deleteDownload(item.id);
  await refresh();
}

async function handleRetry(item: DownloadItem) {
  await retryDownload(item.id);
  await refresh();
}
</script>

<template>
  <div class="mx-auto max-w-3xl px-6 py-8 space-y-8">
    <header>
      <h1 class="text-2xl font-bold tracking-tight">Unduhan</h1>
      <p class="mt-1 text-sm text-slate-500 dark:text-slate-400">
        {{ doneItems.length }} selesai &middot; {{ activeItems.length }} aktif &middot; {{ errorItems.length }} gagal
      </p>
    </header>

    <p v-if="loading" class="text-center text-sm text-slate-400">Memuat...</p>

    <!-- Active -->
    <section v-if="activeItems.length > 0" class="animate-slide-up">
      <h2 class="mb-3 text-sm font-medium text-amber-600">Sedang diproses</h2>
      <div class="space-y-2">
        <div
          v-for="item in activeItems"
          :key="item.id"
          class="rounded-xl border border-amber-200 bg-white p-4 dark:border-amber-500/30 dark:bg-slate-800"
        >
          <div class="flex items-center gap-4">
            <img
              v-if="item.cover_url"
              :src="item.cover_url"
              class="h-12 w-12 rounded-lg object-cover"
              loading="lazy"
            />
            <div v-else class="flex h-12 w-12 items-center justify-center rounded-lg bg-slate-100 dark:bg-slate-700">
              <svg class="h-5 w-5 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zm12-3c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zM9 10l12-3" />
              </svg>
            </div>
            <div class="min-w-0 flex-1">
              <p class="truncate text-sm font-medium">{{ item.title || item.url }}</p>
              <p v-if="item.artist" class="truncate text-xs text-slate-500 dark:text-slate-400">
                {{ item.artist }}
                <template v-if="item.album"> &middot; {{ item.album }} </template>
              </p>
            </div>
            <div class="shrink-0 text-right">
              <p class="text-xs font-medium text-amber-600">{{ phaseLabel(getPhase(item)) }}</p>
              <p class="text-xs text-slate-400">{{ Math.round(getProgress(item)) }}%</p>
            </div>
          </div>
          <div class="mt-3 h-1.5 w-full overflow-hidden rounded-full bg-slate-100 dark:bg-slate-700">
            <div
              class="h-full rounded-full bg-amber-500 transition-all duration-500 ease-out"
              :style="{ width: getProgress(item) + '%' }"
            />
          </div>
        </div>
      </div>
    </section>

    <!-- Done -->
    <section v-if="doneItems.length > 0">
      <h2 class="mb-3 text-sm font-medium text-emerald-600">Berhasil ({{ doneItems.length }})</h2>
      <div class="divide-y divide-slate-100 rounded-xl border border-slate-200 bg-white dark:divide-slate-700 dark:border-slate-700 dark:bg-slate-800">
        <div v-for="item in doneItems" :key="item.id" class="flex items-center gap-4 px-4 py-3">
          <img
            v-if="item.cover_url"
            :src="item.cover_url"
            class="h-10 w-10 rounded-lg object-cover"
            loading="lazy"
          />
          <div v-else class="flex h-10 w-10 items-center justify-center rounded-lg bg-slate-100 dark:bg-slate-700">
            <svg class="h-4 w-4 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zm12-3c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zM9 10l12-3" />
            </svg>
          </div>
          <div class="min-w-0 flex-1">
            <p class="truncate text-sm font-medium">{{ item.title || "Tanpa judul" }}</p>
            <p v-if="item.artist" class="truncate text-xs text-slate-500 dark:text-slate-400">
              {{ item.artist }}
              <template v-if="item.album"> &middot; {{ item.album }} </template>
            </p>
          </div>
          <span class="shrink-0 text-xs text-slate-400">{{ item.format }}</span>
          <button
            @click="handleDelete(item)"
            class="shrink-0 rounded-lg p-1.5 text-slate-400 transition-colors hover:bg-red-50 hover:text-red-500 dark:hover:bg-red-500/10"
            title="Hapus"
          >
            <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>
          </button>
        </div>
      </div>
    </section>

    <!-- Errors -->
    <section v-if="errorItems.length > 0">
      <h2 class="mb-3 text-sm font-medium text-red-500">Gagal ({{ errorItems.length }})</h2>
      <div class="divide-y divide-slate-100 rounded-xl border border-red-200 bg-white dark:divide-slate-700 dark:border-red-500/30 dark:bg-slate-800">
        <div v-for="item in errorItems" :key="item.id" class="px-4 py-3">
          <div class="flex items-center gap-4">
            <img
              v-if="item.cover_url"
              :src="item.cover_url"
              class="h-10 w-10 rounded-lg object-cover"
              loading="lazy"
            />
            <div v-else class="flex h-10 w-10 items-center justify-center rounded-lg bg-slate-100 dark:bg-slate-700">
              <svg class="h-4 w-4 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zm12-3c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zM9 10l12-3" />
              </svg>
            </div>
            <div class="min-w-0 flex-1">
              <p class="truncate text-sm font-medium">{{ item.title || item.url }}</p>
              <p class="mt-0.5 truncate text-xs text-red-500">{{ item.error || "Error tidak diketahui" }}</p>
            </div>
          </div>
          <div class="mt-2 ml-14 flex gap-2">
            <button
              @click="handleRetry(item)"
              class="rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-medium text-slate-700 transition-colors hover:bg-slate-100 dark:border-slate-600 dark:text-slate-300 dark:hover:bg-slate-700"
            >
              Ulangi
            </button>
            <button
              @click="handleDelete(item)"
              class="rounded-lg border border-red-200 px-3 py-1.5 text-xs font-medium text-red-600 transition-colors hover:bg-red-50 dark:border-red-500/30 dark:hover:bg-red-500/10"
            >
              Hapus
            </button>
          </div>
        </div>
      </div>
    </section>

    <!-- Empty -->
    <div
      v-if="!loading && activeItems.length === 0 && doneItems.length === 0 && errorItems.length === 0"
      class="rounded-xl border border-dashed border-slate-300 py-16 text-center dark:border-slate-700"
    >
      <svg class="mx-auto h-12 w-12 text-slate-300 dark:text-slate-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
        <path stroke-linecap="round" stroke-linejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5M16.5 12L12 16.5m0 0L7.5 12m4.5 4.5V3" />
      </svg>
      <p class="mt-3 text-sm text-slate-400">Belum ada unduhan</p>
    </div>
  </div>
</template>
