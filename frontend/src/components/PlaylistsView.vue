<script setup lang="ts">
import { onMounted, ref } from "vue";
import {
  listPlaylists,
  createPlaylist,
  deletePlaylist,
  syncPlaylist,
  getPlaylistItems,
  type PlaylistInfo,
  type PlaylistItem,
} from "../api";

const playlists = ref<PlaylistInfo[]>([]);
const selected = ref<number | null>(null);
const items = ref<PlaylistItem[]>([]);
const showForm = ref(false);
const newName = ref("");
const newUrl = ref("");
const syncing = ref<number | null>(null);
const loading = ref(false);

async function refresh() {
  loading.value = true;
  playlists.value = await listPlaylists();
  loading.value = false;
}

onMounted(refresh);

async function selectPlaylist(id: number) {
  if (selected.value === id) {
    selected.value = null;
    items.value = [];
    return;
  }
  selected.value = id;
  items.value = await getPlaylistItems(id);
}

async function handleCreate() {
  if (!newName.value.trim() || !newUrl.value.trim()) return;
  await createPlaylist(newName.value.trim(), newUrl.value.trim());
  newName.value = "";
  newUrl.value = "";
  showForm.value = false;
  await refresh();
}

async function handleSync(id: number) {
  syncing.value = id;
  await syncPlaylist(id);
  syncing.value = null;
  if (selected.value === id) items.value = await getPlaylistItems(id);
}

async function handleDelete(id: number) {
  if (!confirm("Hapus playlist ini?")) return;
  await deletePlaylist(id);
  if (selected.value === id) {
    selected.value = null;
    items.value = [];
  }
  await refresh();
}
</script>

<template>
  <div class="mx-auto max-w-3xl px-6 py-8 space-y-6">
    <header class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold tracking-tight">Playlist</h1>
        <p class="mt-1 text-sm text-slate-500 dark:text-slate-400">{{ playlists.length }} playlist</p>
      </div>
      <button
        @click="showForm = !showForm"
        class="rounded-xl bg-slate-900 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-slate-800 dark:bg-white dark:text-slate-900 dark:hover:bg-slate-200"
      >
        {{ showForm ? "Batal" : "+ Tambah" }}
      </button>
    </header>

    <!-- Create Form -->
    <div v-if="showForm" class="animate-slide-up rounded-xl border border-slate-200 bg-white p-5 dark:border-slate-700 dark:bg-slate-800">
      <form @submit.prevent="handleCreate" class="space-y-4">
        <div>
          <label class="mb-1.5 block text-xs font-medium text-slate-600 dark:text-slate-400">Nama playlist</label>
          <input v-model="newName" placeholder="Playlist favorit saya" class="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm placeholder:text-slate-400 focus:border-slate-900 focus:outline-none focus:ring-2 focus:ring-slate-900/10 dark:border-slate-600 dark:bg-slate-700 dark:focus:border-white dark:focus:ring-white/10" />
        </div>
        <div>
          <label class="mb-1.5 block text-xs font-medium text-slate-600 dark:text-slate-400">URL Playlist (YouTube atau Spotify)</label>
          <input v-model="newUrl" placeholder="https://youtube.com/playlist?list=... atau https://open.spotify.com/playlist/..." class="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm placeholder:text-slate-400 focus:border-slate-900 focus:outline-none focus:ring-2 focus:ring-slate-900/10 dark:border-slate-600 dark:bg-slate-700 dark:focus:border-white dark:focus:ring-white/10" />
        </div>
        <div class="flex gap-2">
          <button type="submit" class="rounded-lg bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-800 dark:bg-white dark:text-slate-900 dark:hover:bg-slate-200">Simpan</button>
          <button type="button" @click="showForm = false" class="rounded-lg border border-slate-200 px-4 py-2 text-sm font-medium text-slate-600 hover:bg-slate-50 dark:border-slate-600 dark:text-slate-400 dark:hover:bg-slate-700">Batal</button>
        </div>
      </form>
    </div>

    <p v-if="loading" class="text-center text-sm text-slate-400">Memuat...</p>

    <!-- Empty -->
    <div v-else-if="playlists.length === 0 && !showForm" class="rounded-xl border border-dashed border-slate-300 py-16 text-center dark:border-slate-700">
      <svg class="mx-auto h-12 w-12 text-slate-300 dark:text-slate-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
        <path stroke-linecap="round" stroke-linejoin="round" d="M4 6h16M4 10h16M4 14h10M4 18h6" />
      </svg>
      <p class="mt-3 text-sm text-slate-400">Belum ada playlist. Tambahkan playlist YouTube atau Spotify.</p>
    </div>

    <!-- List -->
    <div v-else class="space-y-3">
      <div v-for="pl in playlists" :key="pl.id" class="rounded-xl border border-slate-200 bg-white dark:border-slate-700 dark:bg-slate-800">
        <div
          class="flex cursor-pointer items-center justify-between px-5 py-4 transition-colors hover:bg-slate-50 dark:hover:bg-slate-700/30"
          @click="selectPlaylist(pl.id)"
        >
          <div class="min-w-0 flex-1">
            <p class="truncate text-sm font-medium">{{ pl.name }}</p>
            <p class="mt-0.5 truncate text-xs text-slate-400">{{ pl.url }}</p>
          </div>
          <div class="flex shrink-0 items-center gap-2">
            <button @click.stop="handleSync(pl.id)" :disabled="syncing === pl.id" class="rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-medium text-slate-700 transition-colors hover:bg-slate-100 disabled:opacity-40 dark:border-slate-600 dark:text-slate-300 dark:hover:bg-slate-700">
              {{ syncing === pl.id ? "Sync..." : "Sinkron" }}
            </button>
            <button @click.stop="handleDelete(pl.id)" class="rounded-lg p-1.5 text-slate-400 transition-colors hover:bg-red-50 hover:text-red-500 dark:hover:bg-red-500/10">
              <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
            </button>
          </div>
        </div>
        <div v-if="selected === pl.id" class="border-t border-slate-100 px-5 py-4 dark:border-slate-700">
          <p class="mb-3 text-xs text-slate-400">
            {{ items.length }} lagu ter-sync
            <template v-if="pl.last_sync"> &middot; {{ pl.last_sync }} </template>
          </p>
          <ul v-if="items.length > 0" class="space-y-0.5">
            <li v-for="it in items" :key="it.id" class="flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors hover:bg-slate-50 dark:hover:bg-slate-700/50">
              <span class="w-8 text-xs text-slate-400">{{ it.video_id.slice(0, 6) }}</span>
              <span class="min-w-0 flex-1 truncate">{{ it.title || it.video_id }}</span>
              <span class="text-xs text-slate-400">{{ it.artist || "-" }}</span>
            </li>
          </ul>
          <p v-else class="text-sm text-slate-400">Belum ada item. Klik "Sinkron".</p>
        </div>
      </div>
    </div>
  </div>
</template>
