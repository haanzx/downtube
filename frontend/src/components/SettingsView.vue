<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useTheme } from "../composables/useTheme";

const { isDark, toggle } = useTheme();

interface Settings {
  default_format: string;
  default_quality: string;
  default_cover_option: string;
  download_concurrency: string;
  low_power_mode: boolean;
  ffmpeg_threads: string;
  max_search_results: string;
}

const settings = ref<Settings>({
  default_format: "mp3",
  default_quality: "best",
  default_cover_option: "embed",
  download_concurrency: "1",
  low_power_mode: false,
  ffmpeg_threads: "1",
  max_search_results: "10",
});
const feedback = ref("");
const saving = ref(false);

onMounted(async () => {
  const res = await fetch("/api/settings");
  if (res.ok) settings.value = await res.json();
});

async function save() {
  saving.value = true;
  feedback.value = "";
  const res = await fetch("/api/settings", {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ settings: settings.value }),
  });
  if (res.ok) {
    settings.value = await res.json();
    feedback.value = "Tersimpan.";
  } else {
    feedback.value = "Gagal menyimpan.";
  }
  saving.value = false;
}
</script>

<template>
  <div class="mx-auto max-w-3xl px-6 py-8 space-y-6">
    <header>
      <h1 class="text-2xl font-bold tracking-tight">Pengaturan</h1>
      <p class="mt-1 text-sm text-slate-500 dark:text-slate-400">
        Konfigurasi tampilan, format, kualitas, cover, dan performa.
      </p>
    </header>

    <!-- Theme -->
    <div class="rounded-xl border border-slate-200 bg-white p-5 dark:border-slate-700 dark:bg-slate-800">
      <h2 class="mb-3 text-sm font-semibold text-slate-900 dark:text-white">Tampilan</h2>
      <div class="flex items-center justify-between">
        <div>
          <p class="text-sm font-medium">Mode tampilan</p>
          <p class="text-xs text-slate-500 dark:text-slate-400">
            {{ isDark ? "Mode gelap aktif" : "Mode terang aktif" }}
          </p>
        </div>
        <button
          @click="toggle"
          class="relative inline-flex h-7 w-12 items-center rounded-full transition-colors"
          :class="isDark ? 'bg-slate-900 dark:bg-white' : 'bg-slate-300'"
        >
          <span
            class="inline-block h-5 w-5 transform rounded-full bg-white shadow-sm transition-transform dark:bg-slate-900"
            :class="isDark ? 'translate-x-6' : 'translate-x-1'"
          />
        </button>
      </div>
    </div>

    <form @submit.prevent="save" class="space-y-6">
      <!-- Download Settings -->
      <div class="rounded-xl border border-slate-200 bg-white p-5 dark:border-slate-700 dark:bg-slate-800">
        <h2 class="mb-4 text-sm font-semibold text-slate-900 dark:text-white">Unduhan</h2>
        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="mb-1.5 block text-xs font-medium text-slate-600 dark:text-slate-400">Format</label>
            <select v-model="settings.default_format" class="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm focus:border-slate-900 focus:outline-none focus:ring-2 focus:ring-slate-900/10 dark:border-slate-600 dark:bg-slate-700 dark:focus:border-white dark:focus:ring-white/10">
              <option value="mp3">MP3</option>
              <option value="opus">Opus</option>
              <option value="m4a">M4A</option>
              <option value="flac">FLAC</option>
            </select>
          </div>
          <div>
            <label class="mb-1.5 block text-xs font-medium text-slate-600 dark:text-slate-400">Kualitas</label>
            <select v-model="settings.default_quality" class="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm focus:border-slate-900 focus:outline-none focus:ring-2 focus:ring-slate-900/10 dark:border-slate-600 dark:bg-slate-700 dark:focus:border-white dark:focus:ring-white/10">
              <option value="best">Terbaik</option>
              <option value="good">Bagus</option>
              <option value="ok">Cukup</option>
            </select>
          </div>
          <div>
            <label class="mb-1.5 block text-xs font-medium text-slate-600 dark:text-slate-400">Sampul</label>
            <select v-model="settings.default_cover_option" class="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm focus:border-slate-900 focus:outline-none focus:ring-2 focus:ring-slate-900/10 dark:border-slate-600 dark:bg-slate-700 dark:focus:border-white dark:focus:ring-white/10">
              <option value="embed">Tanam</option>
              <option value="file">File</option>
              <option value="both">Keduanya</option>
              <option value="none">Tidak ada</option>
            </select>
          </div>
          <div>
            <label class="mb-1.5 block text-xs font-medium text-slate-600 dark:text-slate-400">Konkurensi</label>
            <input v-model="settings.download_concurrency" type="number" min="1" max="10" class="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm focus:border-slate-900 focus:outline-none focus:ring-2 focus:ring-slate-900/10 dark:border-slate-600 dark:bg-slate-700 dark:focus:border-white dark:focus:ring-white/10" />
          </div>
        </div>
      </div>

      <!-- Performance Settings -->
      <div class="rounded-xl border border-slate-200 bg-white p-5 dark:border-slate-700 dark:bg-slate-800">
        <h2 class="mb-4 text-sm font-semibold text-slate-900 dark:text-white">Performa</h2>
        <div class="space-y-4">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium">Mode Hemat Daya</p>
              <p class="text-xs text-slate-500 dark:text-slate-400">
                {{ settings.low_power_mode ? "Aktif - Mengurangi penggunaan CPU" : "Nonaktif" }}
              </p>
            </div>
            <button
              type="button"
              @click="settings.low_power_mode = !settings.low_power_mode"
              class="relative inline-flex h-7 w-12 items-center rounded-full transition-colors"
              :class="settings.low_power_mode ? 'bg-emerald-500' : 'bg-slate-300'"
            >
              <span
                class="inline-block h-5 w-5 transform rounded-full bg-white shadow-sm transition-transform"
                :class="settings.low_power_mode ? 'translate-x-6' : 'translate-x-1'"
              />
            </button>
          </div>
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="mb-1.5 block text-xs font-medium text-slate-600 dark:text-slate-400">Thread FFmpeg</label>
              <input v-model="settings.ffmpeg_threads" type="number" min="1" max="4" class="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm focus:border-slate-900 focus:outline-none focus:ring-2 focus:ring-slate-900/10 dark:border-slate-600 dark:bg-slate-700 dark:focus:border-white dark:focus:ring-white/10" />
            </div>
            <div>
              <label class="mb-1.5 block text-xs font-medium text-slate-600 dark:text-slate-400">Hasil Pencarian Maks</label>
              <input v-model="settings.max_search_results" type="number" min="5" max="50" class="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm focus:border-slate-900 focus:outline-none focus:ring-2 focus:ring-slate-900/10 dark:border-slate-600 dark:bg-slate-700 dark:focus:border-white dark:focus:ring-white/10" />
            </div>
          </div>
        </div>
      </div>

      <!-- Submit -->
      <div class="flex items-center gap-3">
        <button type="submit" :disabled="saving" class="rounded-xl bg-slate-900 px-6 py-2.5 text-sm font-medium text-white transition-colors hover:bg-slate-800 disabled:opacity-40 dark:bg-white dark:text-slate-900 dark:hover:bg-slate-200">
          {{ saving ? "Menyimpan..." : "Simpan" }}
        </button>
        <p v-if="feedback" class="animate-fade-in text-sm text-slate-500 dark:text-slate-400">{{ feedback }}</p>
      </div>
    </form>
  </div>
</template>
