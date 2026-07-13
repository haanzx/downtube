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

function isUrl(text: string): boolean {
  return /^https?:\/\//.test(text.trim());
}

async function doSearch() {
  const q = query.value.trim();
  if (!q) return;
  loading.value = true;
  preview.value = null;
  feedback.value = "";

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
}
</script>

<template>
  <div class="mx-auto max-w-3xl px-6 py-8 space-y-6">
    <header>
      <h1 class="text-2xl font-bold tracking-tight">Cari</h1>
      <p class="mt-1 text-sm text-slate-500 dark:text-slate-400">
        Cari lagu, artis, atau tempel tautan YouTube / YT Music / Spotify
      </p>
    </header>

    <!-- Search bar -->
    <div class="flex gap-3">
      <div class="relative flex-1">
        <svg class="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
        </svg>
        <input
          v-model="query"
          @keydown.enter="doSearch"
          placeholder="Cari lagu, artis, atau tempel tautan..."
          class="w-full rounded-xl border border-slate-200 bg-white py-2.5 pl-10 pr-4 text-sm transition-colors placeholder:text-slate-400 focus:border-slate-900 focus:outline-none focus:ring-2 focus:ring-slate-900/10 dark:border-slate-700 dark:bg-slate-800 dark:focus:border-white dark:focus:ring-white/10"
        />
      </div>
      <select
        v-model="searchType"
        class="rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm transition-colors focus:border-slate-900 focus:outline-none focus:ring-2 focus:ring-slate-900/10 dark:border-slate-700 dark:bg-slate-800 dark:focus:border-white dark:focus:ring-white/10"
      >
        <option value="song">Lagu</option>
        <option value="album">Album</option>
        <option value="artist">Artis</option>
        <option value="playlist">Playlist</option>
      </select>
      <button
        @click="doSearch"
        :disabled="!query.trim() || loading"
        class="rounded-xl bg-slate-900 px-5 py-2.5 text-sm font-medium text-white transition-colors hover:bg-slate-800 disabled:opacity-40 dark:bg-white dark:text-slate-900 dark:hover:bg-slate-200"
      >
        {{ loading ? "..." : "Cari" }}
      </button>
    </div>

    <p v-if="feedback" class="animate-fade-in text-sm text-emerald-600 dark:text-emerald-400">
      {{ feedback }}
    </p>

    <!-- URL Preview -->
    <div v-if="preview" class="animate-slide-up rounded-xl border border-slate-200 bg-white p-5 dark:border-slate-700 dark:bg-slate-800">
      <div class="flex items-start gap-4">
        <img v-if="preview.thumbnail" :src="preview.thumbnail" class="h-20 w-20 rounded-xl object-cover" />
        <div v-else class="flex h-20 w-20 items-center justify-center rounded-xl bg-slate-100 dark:bg-slate-700">
          <svg class="h-8 w-8 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zm12-3c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zM9 10l12-3" />
          </svg>
        </div>
        <div class="min-w-0 flex-1">
          <p class="truncate text-base font-semibold">{{ preview.title }}</p>
          <p class="mt-0.5 truncate text-sm text-slate-500 dark:text-slate-400">
            {{ preview.artist || "Tanpa artis" }}
            <template v-if="preview.album"> &middot; {{ preview.album }} </template>
          </p>
          <p class="mt-0.5 text-xs text-slate-400">
            <template v-if="preview.year">{{ preview.year }} &middot; </template>
            <template v-if="preview.duration">{{ preview.duration }}</template>
          </p>
        </div>
      </div>
      <div class="mt-4 flex gap-2">
        <button
          @click="handleEnqueuePreview"
          :disabled="enqueueing === 'preview'"
          class="rounded-xl bg-slate-900 px-5 py-2 text-sm font-medium text-white transition-colors hover:bg-slate-800 disabled:opacity-40 dark:bg-white dark:text-slate-900 dark:hover:bg-slate-200"
        >
          {{ enqueueing === "preview" ? "Menambahkan..." : "Unduh" }}
        </button>
        <button
          @click="clear"
          class="rounded-xl border border-slate-200 px-4 py-2 text-sm font-medium text-slate-600 transition-colors hover:bg-slate-50 dark:border-slate-600 dark:text-slate-400 dark:hover:bg-slate-700"
        >
          Batal
        </button>
      </div>
    </div>

    <!-- Search Results -->
    <section v-if="results.length > 0" class="animate-slide-up">
      <div class="mb-3 flex items-center justify-between">
        <h2 class="text-sm font-medium text-slate-500 dark:text-slate-400">
          {{ results.length }} hasil
        </h2>
        <button @click="clear" class="text-xs text-slate-400 transition-colors hover:text-slate-600 dark:hover:text-slate-300">
          Bersihkan
        </button>
      </div>
      <div class="divide-y divide-slate-100 rounded-xl border border-slate-200 bg-white dark:divide-slate-700 dark:border-slate-700 dark:bg-slate-800">
        <div
          v-for="result in results"
          :key="result.id"
          class="flex items-center gap-4 px-4 py-3 transition-colors hover:bg-slate-50 dark:hover:bg-slate-700/50"
        >
          <img v-if="result.thumbnail" :src="result.thumbnail" class="h-10 w-10 rounded-lg object-cover" loading="lazy" />
          <div v-else class="flex h-10 w-10 items-center justify-center rounded-lg bg-slate-100 dark:bg-slate-700">
            <svg class="h-4 w-4 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zm12-3c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zM9 10l12-3" />
            </svg>
          </div>
          <div class="min-w-0 flex-1">
            <p class="truncate text-sm font-medium">{{ result.title }}</p>
            <p class="truncate text-xs text-slate-500 dark:text-slate-400">
              {{ result.artist || "Tanpa artis" }}
              <template v-if="result.album"> &middot; {{ result.album }} </template>
              <template v-if="result.duration"> &middot; {{ result.duration }} </template>
            </p>
          </div>
          <button
            @click="handleEnqueueFromResult(result)"
            :disabled="enqueueing === result.id"
            class="shrink-0 rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-medium text-slate-700 transition-colors hover:bg-slate-100 disabled:opacity-40 dark:border-slate-600 dark:text-slate-300 dark:hover:bg-slate-700"
          >
            {{ enqueueing === result.id ? "..." : "Unduh" }}
          </button>
        </div>
      </div>
    </section>

    <!-- Empty state -->
    <div
      v-if="!loading && results.length === 0 && !preview"
      class="rounded-xl border border-dashed border-slate-300 py-16 text-center dark:border-slate-700"
    >
      <svg class="mx-auto h-12 w-12 text-slate-300 dark:text-slate-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
        <path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
      </svg>
      <p class="mt-3 text-sm text-slate-400">Ketik judul lagu, nama artis, atau tempel tautan</p>
    </div>
  </div>
</template>
