<script setup lang="ts">
import { ref } from "vue";
import { searchMusic, previewUrl, createDownload, type SearchResult, type PreviewResult } from "../api";

const emit = defineEmits<{ (e: "downloaded"): void }>();

const query = ref("");
const searchType = ref("song");
const results = ref<SearchResult[]>([]);
const preview = ref<PreviewResult | null>(null);
const loading = ref(false);
const enqueueing = ref<string | null>(null);
const feedback = ref("");
const hasSearched = ref(false);

function isUrl(text: string): boolean {
  return /^https?:\/\//.test(text.trim());
}

async function doSearch() {
  const q = query.value.trim();
  if (!q) return;
  loading.value = true;
  preview.value = null;
  feedback.value = "";
  hasSearched.value = true;

  if (isUrl(q)) {
    const p = await previewUrl(q);
    preview.value = p;
    results.value = [];
  } else {
    results.value = await searchMusic(q, searchType.value);
    preview.value = null;
  }
  loading.value = false;
}

async function handleEnqueueFromResult(result: SearchResult) {
  enqueueing.value = result.id;
  feedback.value = "";
  try {
    await createDownload(result.url, {
      title: result.title,
      artist: result.artist,
      album: result.album,
      cover_url: result.thumbnail,
    });
    feedback.value = `"${result.title}" ditambahkan ke unduhan.`;
    emit("downloaded");
  } catch (e: unknown) {
    feedback.value = `Gagal: ${e instanceof Error ? e.message : "error tidak diketahui"}`;
  } finally {
    enqueueing.value = null;
  }
}

async function handleEnqueuePreview() {
  if (!preview.value) return;
  enqueueing.value = "preview";
  feedback.value = "";
  try {
    await createDownload(preview.value.url, {
      title: preview.value.title,
      artist: preview.value.artist,
      album: preview.value.album,
      cover_url: preview.value.thumbnail,
    });
    feedback.value = `"${preview.value.title}" ditambahkan ke unduhan.`;
    preview.value = null;
    query.value = "";
    emit("downloaded");
  } catch (e: unknown) {
    feedback.value = `Gagal: ${e instanceof Error ? e.message : "error tidak diketahui"}`;
  } finally {
    enqueueing.value = null;
  }
}

function clear() {
  query.value = "";
  results.value = [];
  preview.value = null;
  feedback.value = "";
  hasSearched.value = false;
}

const categories = [
  { key: "song", label: "Lagu", icon: "music", color: "bg-neutral-400" },
  { key: "album", label: "Album", icon: "disc", color: "bg-neutral-500" },
  { key: "artist", label: "Artis", icon: "mic", color: "bg-neutral-600" },
  { key: "playlist", label: "Playlist", icon: "list", color: "bg-neutral-700" },
];

function selectCategory(key: string) {
  searchType.value = key;
}
</script>

<template>
  <div class="mx-auto max-w-4xl px-6 py-8 space-y-8">
    <!-- Big Search Section -->
    <div class="flex flex-col items-center text-center">
      <h1 class="mb-2 text-4xl font-bold tracking-tight">Cari Musik</h1>
      <p class="mb-8 text-base text-black/40 dark:text-white/40">
        Ketik judul lagu, nama artis, atau tempel tautan
      </p>

      <!-- Big Search Bar -->
      <div class="flex w-full max-w-2xl items-center gap-3">
        <div class="relative flex-1">
          <svg class="absolute left-4 top-1/2 h-5 w-5 -translate-y-1/2 text-black/40 dark:text-white/40" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
          <input
            v-model="query"
            @keydown.enter="doSearch"
            placeholder="Cari lagu, artis, atau tempel tautan..."
            aria-label="Cari lagu atau tempel tautan"
            class="h-12 w-full rounded-full border border-black/5 bg-am-surface-light pl-12 pr-5 text-base transition-all duration-200 placeholder:text-black/40 focus:border-am-accent-light focus:outline-none focus:ring-4 focus:ring-am-accent-light/10 dark:border-white/5 dark:bg-am-surface-dark dark:placeholder:text-white/40 dark:focus:border-am-accent-dark dark:focus:ring-am-accent-dark/10"
          />
        </div>
        <button
          @click="doSearch"
          :disabled="!query.trim() || loading"
          :aria-busy="loading"
          class="h-12 shrink-0 rounded-full bg-am-accent-light px-7 text-base font-semibold text-white transition-all duration-200 hover:opacity-90 active:scale-[0.98] disabled:opacity-40 dark:bg-am-accent-dark"
        >
          {{ loading ? "..." : "Cari" }}
        </button>
      </div>

      <!-- Type Selector -->
      <div class="mt-4 flex gap-2">
        <button
          v-for="cat in categories"
          :key="cat.key"
          @click="selectCategory(cat.key)"
          :class="[
            'flex items-center gap-2 rounded-full px-4 py-2 text-sm font-medium transition-all duration-150',
            searchType === cat.key
              ? 'bg-am-accent-light text-white dark:bg-am-accent-dark'
              : 'bg-am-surface-light text-black/40 hover:bg-black/5 dark:bg-am-surface-dark dark:text-white/40 dark:hover:bg-white/5',
          ]"
        >
          <span :class="['h-2 w-2 rounded-full', cat.color]" />
          {{ cat.label }}
        </button>
      </div>
    </div>

    <!-- Feedback -->
    <p v-if="feedback" role="status" aria-live="polite" class="animate-fade-in text-center text-sm font-medium text-am-accent-light dark:text-am-accent-dark">
      {{ feedback }}
    </p>

    <!-- URL Preview -->
    <div v-if="preview" class="animate-slide-up">
      <div class="mx-auto max-w-2xl overflow-hidden rounded-3xl border border-black/5 bg-am-surface-light shadow-sm shadow-black/5 dark:border-white/5 dark:bg-am-surface-dark dark:shadow-black/5">
        <div class="flex items-start gap-5 p-6">
          <img v-if="preview.thumbnail" :src="preview.thumbnail" :alt="`${preview.title} cover`" class="h-28 w-28 shrink-0 rounded-2xl object-cover shadow-sm" />
          <div v-else class="flex h-28 w-28 shrink-0 items-center justify-center rounded-2xl bg-black/5 dark:bg-white/5">
            <svg class="h-10 w-10 text-black/40 dark:text-white/40" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
              <path stroke-linecap="round" stroke-linejoin="round" d="M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zm12-3c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zM9 10l12-3" />
            </svg>
          </div>
          <div class="min-w-0 flex-1 pt-1">
            <p class="truncate text-xl font-bold">{{ preview.title }}</p>
            <p class="mt-1 truncate text-base text-black/40 dark:text-white/40">
              {{ preview.artist || "Tanpa artis" }}
              <template v-if="preview.album"> &middot; {{ preview.album }} </template>
            </p>
            <p class="mt-1 text-sm text-black/40 dark:text-white/40">
              <template v-if="preview.year">{{ preview.year }} &middot; </template>
              <template v-if="preview.duration">{{ preview.duration }}</template>
            </p>
          </div>
        </div>
        <div class="flex gap-3 border-t border-black/5 px-6 py-4 dark:border-white/5">
          <button
            @click="handleEnqueuePreview"
            :disabled="enqueueing === 'preview'"
            class="rounded-full bg-am-accent-light px-6 py-2.5 text-sm font-semibold text-white transition-all hover:opacity-90 active:scale-[0.98] disabled:opacity-40 dark:bg-am-accent-dark"
          >
            {{ enqueueing === "preview" ? "Menambahkan..." : "Unduh" }}
          </button>
          <button
            @click="clear"
            class="rounded-full border border-black/5 px-6 py-2.5 text-sm font-semibold text-black/40 transition-colors hover:bg-black/5 dark:border-white/5 dark:text-white/40 dark:hover:bg-white/5"
          >
            Batal
          </button>
        </div>
      </div>
    </div>

    <!-- Search Results - Card Grid -->
    <section v-if="results.length > 0" class="animate-slide-up" aria-label="Hasil pencarian">
      <div class="mb-4 flex items-center justify-between">
        <h2 class="text-lg font-semibold">{{ results.length }} hasil</h2>
        <button @click="clear" class="text-sm font-medium text-black/40 transition-colors hover:text-black/90 dark:text-white/40 dark:hover:text-white/90">
          Bersihkan
        </button>
      </div>
      <div class="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
        <div
          v-for="result in results"
          :key="result.id"
          class="group cursor-pointer overflow-hidden rounded-3xl border border-black/5 bg-am-surface-light p-3 transition-all duration-200 hover:shadow-md hover:shadow-black/5 hover:dark:shadow-black/10 dark:border-white/5 dark:bg-am-surface-dark"
        >
          <!-- Cover Art -->
          <div class="relative mb-3 aspect-square overflow-hidden rounded-2xl bg-black/5 dark:bg-white/5">
            <img v-if="result.thumbnail" :src="result.thumbnail" :alt="`${result.title} thumbnail`" class="h-full w-full object-cover transition-transform duration-300 group-hover:scale-105" loading="lazy" />
            <div v-else class="flex h-full w-full items-center justify-center">
              <svg class="h-12 w-12 text-black/15 dark:text-white/15" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
                <path stroke-linecap="round" stroke-linejoin="round" d="M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zm12-3c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zM9 10l12-3" />
              </svg>
            </div>
            <!-- Download Button Overlay -->
            <button
              @click="handleEnqueueFromResult(result)"
              :disabled="enqueueing === result.id"
              class="absolute bottom-2 right-2 flex h-10 w-10 items-center justify-center rounded-full bg-am-accent-light text-white opacity-0 shadow-lg transition-all duration-200 group-hover:opacity-100 hover:scale-105 active:scale-95 disabled:opacity-40 dark:bg-am-accent-dark"
            >
              <svg v-if="enqueueing !== result.id" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
                <path stroke-linecap="round" stroke-linejoin="round" d="M12 4v12m0 0l-4-4m4 4l4-4" />
              </svg>
              <svg v-else class="h-5 w-5 animate-spin" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
            </button>
          </div>
          <!-- Info -->
          <p class="truncate text-[15px] font-semibold">{{ result.title }}</p>
          <p class="mt-0.5 truncate text-sm text-black/40 dark:text-white/40">
            {{ result.artist || "Tanpa artis" }}
          </p>
          <p v-if="result.duration" class="mt-0.5 text-xs text-black/30 dark:text-white/30">
            {{ result.duration }}
          </p>
        </div>
      </div>
    </section>

    <!-- Empty state / Browse Categories -->
    <div
      v-if="!loading && results.length === 0 && !preview && !hasSearched"
      class="animate-fade-in"
    >
      <p class="mb-6 text-center text-sm text-black/40 dark:text-white/40">Atau pilih kategori pencarian</p>
      <div class="mx-auto grid max-w-lg grid-cols-2 gap-4">
        <button
          v-for="cat in categories"
          :key="cat.key"
          @click="selectCategory(cat.key); query ? doSearch() : null"
          :class="[
            'group flex items-center gap-4 overflow-hidden rounded-3xl p-5 transition-all duration-200 hover:shadow-md hover:shadow-black/5 hover:dark:shadow-black/10',
            cat.color,
          ]"
        >
          <span class="text-3xl font-bold text-white/90 transition-transform duration-200 group-hover:scale-110">
            <svg v-if="cat.icon === 'music'" class="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zm12-3c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zM9 10l12-3" /></svg>
            <svg v-else-if="cat.icon === 'disc'" class="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 14.5c-2.49 0-4.5-2.01-4.5-4.5S9.51 7.5 12 7.5s4.5 2.01 4.5 4.5-2.01 4.5-4.5 4.5zm0-5.5c-.55 0-1 .45-1 1s.45 1 1 1 1-.45 1-1-.45-1-1-1z" /></svg>
            <svg v-else-if="cat.icon === 'mic'" class="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3zm-1 1.93c-3.94-.49-7-3.85-7-7.93h2c0 3.31 2.69 6 6 6s6-2.69 6-6h2c0 4.08-3.06 7.44-7 7.93V20h4v2H8v-2h4v-4.07z" /></svg>
            <svg v-else class="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M4 6h16M4 10h16M4 14h10M4 18h6" /></svg>
          </span>
          <span class="text-lg font-bold text-white">{{ cat.label }}</span>
        </button>
      </div>
    </div>

    <!-- Empty search state -->
    <div
      v-if="!loading && results.length === 0 && !preview && hasSearched"
      class="rounded-3xl border border-dashed border-black/5 py-16 text-center dark:border-white/5"
    >
      <svg class="mx-auto h-16 w-16 text-black/10 dark:text-white/10" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1">
        <path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
      </svg>
      <p class="mt-4 text-base font-medium text-black/40 dark:text-white/40">Tidak ada hasil ditemukan</p>
      <p class="mt-1 text-sm text-black/30 dark:text-white/30">Coba kata kunci lain atau periksa URL</p>
    </div>
  </div>
</template>
