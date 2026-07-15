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
    return s === "pending" || s === "resolving" || s === "downloading" || s === "transcoding" || s === "tagging";
  }),
);
const doneItems = computed(() => items.value.filter((i) => getStatus(i) === "done"));
const errorItems = computed(() => items.value.filter((i) => getStatus(i) === "failed"));

const PHASE_LABELS: Record<string, string> = {
  resolving: "Mengambil info...",
  downloading: "Mengunduh...",
  transcoding: "Transcode...",
  "fetching_lyrics": "Mengambil lirik...",
  "fetching_cover": "Mengambil cover...",
  "writing metadata": "Menulis metadata...",
  "embedding cover": "Menanam cover...",
  "embedding lyrics": "Menanam lirik...",
  tagging: "Menanam metadata...",
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
  <div class="mx-auto max-w-4xl px-6 py-8 space-y-10">
    <header>
      <h1 class="text-4xl font-bold tracking-tight">Unduhan</h1>
      <p class="mt-2 text-base text-black/40 dark:text-white/40">
        {{ doneItems.length }} selesai &middot; {{ activeItems.length }} aktif &middot; {{ errorItems.length }} gagal
      </p>
    </header>

    <p v-if="loading" role="status" class="py-12 text-center text-base text-black/40 dark:text-white/40">Memuat...</p>

    <!-- Active Downloads - Big Cards -->
    <section v-if="activeItems.length > 0" class="animate-slide-up">
      <h2 class="mb-4 text-lg font-semibold text-am-accent-light dark:text-am-accent-dark">Sedang diproses</h2>
      <div class="space-y-4">
        <div
          v-for="item in activeItems"
          :key="item.id"
          class="overflow-hidden rounded-3xl border border-am-accent-light/20 bg-am-surface-light shadow-sm dark:bg-am-surface-dark dark:border-am-accent-dark/20"
        >
          <div class="flex items-center gap-5 p-5">
            <div class="relative shrink-0">
              <img
                v-if="item.cover_url"
                :src="item.cover_url"
                :alt="`${item.title || 'Lagu'} cover`"
                class="h-20 w-20 rounded-2xl object-cover shadow-sm"
                loading="lazy"
              />
              <div v-else class="flex h-20 w-20 items-center justify-center rounded-2xl bg-black/5 dark:bg-white/5">
                <svg class="h-8 w-8 text-black/15 dark:text-white/15" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zm12-3c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zM9 10l12-3" />
                </svg>
              </div>
              <!-- Pulsing indicator -->
              <span class="absolute -right-1 -top-1 flex h-3 w-3">
                <span class="absolute inline-flex h-full w-full animate-ping rounded-full bg-am-accent-light/15 opacity-75 dark:bg-am-accent-dark/15" />
                <span class="relative inline-flex h-3 w-3 rounded-full bg-am-accent-light/15 dark:bg-am-accent-dark/15" />
              </span>
            </div>
            <div class="min-w-0 flex-1">
              <p class="truncate text-lg font-semibold">{{ item.title || item.url }}</p>
              <p v-if="item.artist" class="mt-0.5 truncate text-sm text-black/40 dark:text-white/40">
                {{ item.artist }}
                <template v-if="item.album"> &middot; {{ item.album }} </template>
              </p>
              <div class="mt-2 flex items-center gap-3">
                <span class="text-sm font-medium text-am-accent-light dark:text-am-accent-dark">{{ phaseLabel(getPhase(item)) }}</span>
                <span class="text-sm text-black/40 dark:text-white/40">{{ Math.round(getProgress(item)) }}%</span>
              </div>
            </div>
          </div>
          <div
            role="progressbar"
            :aria-valuenow="Math.round(getProgress(item))"
            aria-valuemin="0"
            aria-valuemax="100"
            :aria-label="`Progress: ${Math.round(getProgress(item))}%`"
            class="h-2 w-full bg-black/5 dark:bg-white/5"
          >
            <div
              class="h-full bg-am-accent-light transition-all duration-500 ease-out dark:bg-am-accent-dark"
              :style="{ width: getProgress(item) + '%' }"
            />
          </div>
        </div>
      </div>
    </section>

    <!-- Done - Grid Cards -->
    <section v-if="doneItems.length > 0">
      <h2 class="mb-4 text-lg font-semibold text-am-accent-light dark:text-am-accent-dark">Berhasil ({{ doneItems.length }})</h2>
      <div class="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
        <div v-for="item in doneItems" :key="item.id" class="group relative overflow-hidden rounded-3xl border border-black/5 bg-am-surface-light p-3 transition-all duration-200 hover:shadow-md hover:shadow-black/5 dark:border-white/5 dark:bg-am-surface-dark dark:hover:shadow-black/10">
          <div class="relative mb-3 aspect-square overflow-hidden rounded-2xl bg-black/5 dark:bg-white/5">
            <img
              v-if="item.cover_url"
              :src="item.cover_url"
              :alt="`${item.title || 'Lagu'} cover`"
              class="h-full w-full object-cover transition-transform duration-300 group-hover:scale-105"
              loading="lazy"
            />
            <div v-else class="flex h-full w-full items-center justify-center">
              <svg class="h-12 w-12 text-black/15 dark:text-white/15" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
                <path stroke-linecap="round" stroke-linejoin="round" d="M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zm12-3c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zM9 10l12-3" />
              </svg>
            </div>
            <!-- Delete button overlay -->
            <button
              @click="handleDelete(item)"
              :aria-label="`Hapus ${item.title || item.url}`"
              class="absolute bottom-2 right-2 flex h-9 w-9 items-center justify-center rounded-full bg-am-accent-light/80 text-white opacity-0 shadow-sm transition-all duration-200 group-hover:opacity-100 hover:scale-105 dark:bg-am-accent-dark/80"
            >
              <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
            </button>
            <!-- Format badge -->
            <span class="absolute left-2 top-2 rounded-full bg-black/50 px-2 py-0.5 text-xs font-medium text-white backdrop-blur-sm">{{ item.format }}</span>
          </div>
          <p class="truncate text-[15px] font-semibold">{{ item.title || "Tanpa judul" }}</p>
          <p v-if="item.artist" class="mt-0.5 truncate text-sm text-black/40 dark:text-white/40">
            {{ item.artist }}
          </p>
        </div>
      </div>
    </section>

    <!-- Errors -->
    <section v-if="errorItems.length > 0">
      <h2 class="mb-4 text-lg font-semibold text-am-accent-light dark:text-am-accent-dark">Gagal ({{ errorItems.length }})</h2>
      <div class="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
        <div v-for="item in errorItems" :key="item.id" class="group relative overflow-hidden rounded-3xl border border-am-accent-light/20 bg-am-surface-light p-3 transition-all dark:border-am-accent-dark/20 dark:bg-am-surface-dark">
          <div class="relative mb-3 aspect-square overflow-hidden rounded-2xl bg-black/5 dark:bg-white/5">
            <img
              v-if="item.cover_url"
              :src="item.cover_url"
              :alt="`${item.title || 'Lagu'} cover`"
              class="h-full w-full object-cover opacity-60"
              loading="lazy"
            />
            <div v-else class="flex h-full w-full items-center justify-center">
              <svg class="h-12 w-12 text-black/15 dark:text-white/15" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
                <path stroke-linecap="round" stroke-linejoin="round" d="M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zm12-3c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zM9 10l12-3" />
              </svg>
            </div>
            <!-- Error overlay -->
            <div class="absolute inset-0 flex items-center justify-center bg-am-accent-light/10 dark:bg-am-accent-dark/10">
              <svg class="h-10 w-10 text-am-accent-light dark:text-am-accent-dark" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
              </svg>
            </div>
          </div>
          <p class="truncate text-[15px] font-semibold">{{ item.title || item.url }}</p>
          <p class="mt-0.5 truncate text-xs text-am-accent-light dark:text-am-accent-dark">{{ item.error || "Error tidak diketahui" }}</p>
          <div class="mt-2 flex gap-2">
            <button
              @click="handleRetry(item)"
              aria-label="Ulangi unduhan"
              class="rounded-full border border-black/5 px-3 py-1.5 text-xs font-semibold text-black/40 transition-colors hover:bg-black/5 dark:border-white/5 dark:text-white/40 dark:hover:bg-white/5"
            >
              Ulangi
            </button>
            <button
              @click="handleDelete(item)"
              :aria-label="`Hapus ${item.title || item.url}`"
              class="rounded-full border border-am-accent-light/30 px-3 py-1.5 text-xs font-semibold text-am-accent-light transition-colors hover:bg-am-accent-light/10 dark:border-am-accent-dark/30 dark:text-am-accent-dark dark:hover:bg-am-accent-dark/10"
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
      class="rounded-3xl border border-dashed border-black/5 py-20 text-center dark:border-white/5"
    >
      <svg class="mx-auto h-16 w-16 text-black/10 dark:text-white/10" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1">
        <path stroke-linecap="round" stroke-linejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5M16.5 12L12 16.5m0 0L7.5 12m4.5 4.5V3" />
      </svg>
      <p class="mt-4 text-lg font-medium text-black/40 dark:text-white/40">Belum ada unduhan</p>
      <p class="mt-1 text-sm text-black/30 dark:text-white/30">Cari lagu dan mulai mengunduh</p>
    </div>
  </div>
</template>
