<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useTheme } from "../composables/useTheme";

const { isDark, toggle } = useTheme();

interface Settings {
  default_format: string;
  default_quality: string;
  default_cover_option: string;
  default_lyrics_option: string;
  download_concurrency: string;
  low_power_mode: boolean;
  ffmpeg_threads: string;
  max_search_results: string;
}

const settings = ref<Settings>({
  default_format: "mp3",
  default_quality: "best",
  default_cover_option: "embed",
  default_lyrics_option: "lrc",
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
      <h1 class="text-3xl font-bold tracking-tight">Pengaturan</h1>
      <p class="mt-1 text-sm text-black/40 dark:text-white/40">
        Konfigurasi tampilan, format, kualitas, cover, lirik, dan performa.
      </p>
    </header>

    <!-- Theme -->
    <div class="am-card">
      <h2 class="am-section-title mb-3">Tampilan</h2>
      <div class="flex items-center justify-between">
        <div>
          <p class="text-[15px] font-medium">Mode tampilan</p>
          <p class="text-xs text-black/40 dark:text-white/40">
            {{ isDark ? "Mode gelap aktif" : "Mode terang aktif" }}
          </p>
        </div>
        <button
          type="button"
          role="switch"
          :aria-checked="isDark"
          :aria-label="isDark ? 'Mode gelap aktif' : 'Mode terang aktif'"
          @click="toggle"
          class="am-toggle"
          :class="isDark ? 'bg-am-accent-dark' : 'bg-am-accent-light'"
        >
          <span
            class="am-toggle-knob"
            :class="isDark ? 'translate-x-6' : 'translate-x-1'"
          />
        </button>
      </div>
    </div>

    <form @submit.prevent="save" class="space-y-6">
      <!-- Download Settings -->
      <div class="am-card">
        <h2 class="am-section-title mb-4">Unduhan</h2>
        <div class="grid grid-cols-2 gap-4">
          <div>
            <label for="setting-format" class="am-section-title mb-1.5 block">Format</label>
            <select id="setting-format" v-model="settings.default_format" class="am-select w-full">
              <option value="mp3">MP3</option>
              <option value="opus">Opus</option>
              <option value="m4a">M4A</option>
              <option value="flac">FLAC</option>
            </select>
          </div>
          <div>
            <label for="setting-quality" class="am-section-title mb-1.5 block">Kualitas</label>
            <select id="setting-quality" v-model="settings.default_quality" class="am-select w-full">
              <option value="best">Terbaik</option>
              <option value="good">Bagus</option>
              <option value="ok">Cukup</option>
            </select>
          </div>
          <div>
            <label for="setting-cover" class="am-section-title mb-1.5 block">Sampul</label>
            <select id="setting-cover" v-model="settings.default_cover_option" class="am-select w-full">
              <option value="embed">Tanam</option>
              <option value="file">File</option>
              <option value="both">Keduanya</option>
              <option value="none">Tidak ada</option>
            </select>
          </div>
          <div>
            <label for="setting-concurrency" class="am-section-title mb-1.5 block">Konkurensi</label>
            <input id="setting-concurrency" v-model="settings.download_concurrency" type="number" min="1" max="10" class="am-input" />
          </div>
        </div>
        <div class="mt-4 flex items-center justify-between">
          <div>
            <p class="text-[15px] font-medium">Download synced lyrics (.lrc)</p>
            <p class="text-xs text-black/40 dark:text-white/40">
              {{ settings.default_lyrics_option === "lrc" ? "Aktif - Buat file .lrc" : "Nonaktif" }}
            </p>
          </div>
          <button
            type="button"
            role="switch"
            :aria-checked="settings.default_lyrics_option === 'lrc'"
            :aria-label="settings.default_lyrics_option === 'lrc' ? 'Lirik sinkron aktif' : 'Lirik sinkron nonaktif'"
            @click="settings.default_lyrics_option = settings.default_lyrics_option === 'lrc' ? 'none' : 'lrc'"
            class="am-toggle"
            :class="settings.default_lyrics_option === 'lrc' ? 'bg-am-accent-light dark:bg-am-accent-dark' : 'bg-black/5 dark:bg-white/5'"
          >
            <span
              class="am-toggle-knob"
              :class="settings.default_lyrics_option === 'lrc' ? 'translate-x-6' : 'translate-x-1'"
            />
          </button>
        </div>
      </div>

      <!-- Performance Settings -->
      <div class="am-card">
        <h2 class="am-section-title mb-4">Performa</h2>
        <div class="space-y-4">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-[15px] font-medium">Mode Hemat Daya</p>
              <p class="text-xs text-black/40 dark:text-white/40">
                {{ settings.low_power_mode ? "Aktif - Mengurangi penggunaan CPU" : "Nonaktif" }}
              </p>
            </div>
            <button
              type="button"
              role="switch"
              :aria-checked="settings.low_power_mode"
              :aria-label="settings.low_power_mode ? 'Mode hemat daya aktif' : 'Mode hemat daya nonaktif'"
              @click="settings.low_power_mode = !settings.low_power_mode"
              class="am-toggle"
              :class="settings.low_power_mode ? 'bg-am-accent-light dark:bg-am-accent-dark' : 'bg-black/5 dark:bg-white/5'"
            >
              <span
                class="am-toggle-knob"
                :class="settings.low_power_mode ? 'translate-x-6' : 'translate-x-1'"
              />
            </button>
          </div>
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label for="setting-threads" class="am-section-title mb-1.5 block">Thread FFmpeg</label>
              <input id="setting-threads" v-model="settings.ffmpeg_threads" type="number" min="1" max="4" class="am-input" />
            </div>
            <div>
              <label for="setting-max-results" class="am-section-title mb-1.5 block">Hasil Pencarian Maks</label>
              <input id="setting-max-results" v-model="settings.max_search_results" type="number" min="5" max="50" class="am-input" />
            </div>
          </div>
        </div>
      </div>

      <!-- Submit -->
      <div class="flex items-center gap-3">
        <button type="submit" :disabled="saving" :aria-busy="saving" class="am-btn-primary px-6">
          {{ saving ? "Menyimpan..." : "Simpan" }}
        </button>
        <p v-if="feedback" role="status" aria-live="polite" class="animate-fade-in text-sm text-black/40 dark:text-white/40">{{ feedback }}</p>
      </div>
    </form>
  </div>
</template>
