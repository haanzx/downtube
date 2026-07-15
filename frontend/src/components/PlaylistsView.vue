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

const playlistColors = ["bg-neutral-200", "bg-neutral-300", "bg-neutral-400", "bg-neutral-500", "bg-neutral-600", "bg-neutral-700"];
function getPlaylistColor(id: number) {
  return playlistColors[id % playlistColors.length];
}
</script>

<template>
  <div class="mx-auto max-w-4xl px-6 py-8 space-y-8">
    <header class="flex items-center justify-between">
      <div>
        <h1 class="text-4xl font-bold tracking-tight">Playlist</h1>
        <p class="mt-2 text-base text-black/40 dark:text-white/40">{{ playlists.length }} playlist</p>
      </div>
      <button
        @click="showForm = !showForm"
        :aria-expanded="showForm"
        class="rounded-full bg-am-accent-light px-6 py-3 text-base font-semibold text-white transition-all duration-200 hover:opacity-90 active:scale-[0.98] dark:bg-am-accent-dark"
      >
        {{ showForm ? "Batal" : "+ Tambah" }}
      </button>
    </header>

    <!-- Create Form -->
    <div v-if="showForm" class="animate-slide-up overflow-hidden rounded-3xl border border-black/5 bg-am-surface-light shadow-sm shadow-black/5 dark:border-white/5 dark:bg-am-surface-dark dark:shadow-black/5">
      <form @submit.prevent="handleCreate" class="p-6 space-y-5">
        <div>
          <label for="playlist-name" class="mb-2 block text-sm font-semibold text-black/40 dark:text-white/40">Nama playlist</label>
          <input id="playlist-name" v-model="newName" placeholder="Playlist favorit saya" class="h-12 w-full rounded-2xl border border-black/5 bg-am-bg-light px-4 text-base transition-all placeholder:text-black/20 focus:border-am-accent-light focus:outline-none focus:ring-4 focus:ring-am-accent-light/10 dark:border-white/5 dark:bg-am-bg-dark dark:placeholder:text-white/20 dark:focus:border-am-accent-dark dark:focus:ring-am-accent-dark/10" />
        </div>
        <div>
          <label for="playlist-url" class="mb-2 block text-sm font-semibold text-black/40 dark:text-white/40">URL Playlist</label>
          <input id="playlist-url" v-model="newUrl" placeholder="https://youtube.com/playlist?list=... atau https://open.spotify.com/playlist/..." class="h-12 w-full rounded-2xl border border-black/5 bg-am-bg-light px-4 text-base transition-all placeholder:text-black/20 focus:border-am-accent-light focus:outline-none focus:ring-4 focus:ring-am-accent-light/10 dark:border-white/5 dark:bg-am-bg-dark dark:placeholder:text-white/20 dark:focus:border-am-accent-dark dark:focus:ring-am-accent-dark/10" />
        </div>
        <div class="flex gap-3 pt-2">
          <button type="submit" class="rounded-full bg-am-accent-light px-6 py-2.5 text-sm font-semibold text-white transition-all hover:opacity-90 active:scale-[0.98] dark:bg-am-accent-dark">Simpan</button>
          <button type="button" @click="showForm = false" class="rounded-full border border-black/5 px-6 py-2.5 text-sm font-semibold text-black/40 transition-colors hover:bg-black/5 dark:border-white/5 dark:text-white/40 dark:hover:bg-white/5">Batal</button>
        </div>
      </form>
    </div>

    <p v-if="loading" role="status" class="py-12 text-center text-base text-black/40 dark:text-white/40">Memuat...</p>

    <!-- Empty -->
    <div v-else-if="playlists.length === 0 && !showForm" class="rounded-3xl border border-dashed border-black/5 py-20 text-center dark:border-white/5">
      <svg class="mx-auto h-16 w-16 text-black/10 dark:text-white/10" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1">
        <path stroke-linecap="round" stroke-linejoin="round" d="M4 6h16M4 10h16M4 14h10M4 18h6" />
      </svg>
      <p class="mt-4 text-lg font-medium text-black/40 dark:text-white/40">Belum ada playlist</p>
      <p class="mt-1 text-sm text-black/30 dark:text-white/30">Tambahkan playlist YouTube atau Spotify</p>
    </div>

    <!-- Grid -->
    <div v-else class="space-y-6">
      <div class="grid grid-cols-2 gap-5 sm:grid-cols-3 lg:grid-cols-4">
        <div v-for="pl in playlists" :key="pl.id" class="group">
          <!-- Card -->
          <div
            class="cursor-pointer overflow-hidden rounded-3xl border border-black/5 bg-am-surface-light transition-all duration-200 hover:shadow-md hover:shadow-black/5 dark:border-white/5 dark:bg-am-surface-dark dark:hover:shadow-black/20"
            @click="selectPlaylist(pl.id)"
          >
            <!-- Cover placeholder -->
            <div :class="['aspect-square w-full', getPlaylistColor(pl.id)]">
              <div class="flex h-full w-full items-center justify-center">
                <svg class="h-16 w-16 text-white/40" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M4 6h16M4 10h16M4 14h10M4 18h6" />
                </svg>
              </div>
            </div>
            <!-- Info -->
            <div class="p-4">
              <p class="truncate text-[15px] font-semibold">{{ pl.name }}</p>
              <p class="mt-0.5 text-sm text-black/40 dark:text-white/40">
                {{ pl.last_sync ? `Synced ${pl.last_sync}` : "Belum sync" }}
              </p>
            </div>
          </div>

          <!-- Actions row below card -->
          <div class="mt-2 flex gap-2 px-1">
            <button
              @click.stop="handleSync(pl.id)"
              :disabled="syncing === pl.id"
              class="flex-1 rounded-full border border-black/5 py-2 text-xs font-semibold text-black/40 transition-colors hover:bg-black/5 disabled:opacity-40 dark:border-white/5 dark:text-white/40 dark:hover:bg-white/5"
            >
              {{ syncing === pl.id ? "Sync..." : "Sinkron" }}
            </button>
            <button
              @click.stop="handleDelete(pl.id)"
              :aria-label="`Hapus playlist ${pl.name}`"
              class="rounded-full border border-black/5 p-2 text-black/40 transition-colors hover:border-am-accent-light/30 hover:bg-am-accent-light/10 hover:text-am-accent-light dark:border-white/5 dark:text-white/40 dark:hover:border-am-accent-dark/30 dark:hover:bg-am-accent-dark/10 dark:hover:text-am-accent-dark"
            >
              <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
            </button>
          </div>
        </div>
      </div>

      <!-- Detail Panel -->
      <div v-if="selected" :id="`playlist-${selected}`" role="region" class="animate-slide-up overflow-hidden rounded-3xl border border-black/5 bg-am-surface-light shadow-sm shadow-black/5 dark:border-white/5 dark:bg-am-surface-dark dark:shadow-black/5">
        <div class="flex items-center justify-between border-b border-black/5 px-6 py-4 dark:border-white/5">
          <div>
            <p class="text-lg font-bold">{{ playlists.find(p => p.id === selected)?.name }}</p>
            <p class="text-sm text-black/40 dark:text-white/40">
              {{ items.length }} lagu ter-sync
            </p>
          </div>
          <button @click="selected = null; items = []" class="rounded-full p-2 text-black/40 transition-colors hover:bg-black/5 dark:text-white/40 dark:hover:bg-white/5">
            <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        <div class="p-6">
          <ul v-if="items.length > 0" class="space-y-1">
            <li v-for="(it, idx) in items" :key="it.id" class="flex items-center gap-4 rounded-2xl px-4 py-3 transition-colors hover:bg-black/5 dark:hover:bg-white/5">
              <span class="w-6 text-right text-sm text-black/20 dark:text-white/20">{{ idx + 1 }}</span>
              <span class="min-w-0 flex-1 truncate text-[15px]">{{ it.title || it.video_id }}</span>
              <span class="text-sm text-black/40 dark:text-white/40">{{ it.artist || "-" }}</span>
            </li>
          </ul>
          <p v-else class="text-center text-sm text-black/40 dark:text-white/40">Belum ada item. Klik "Sinkron".</p>
        </div>
      </div>
    </div>
  </div>
</template>
