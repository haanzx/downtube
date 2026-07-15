<script setup lang="ts">
import { ref, computed } from "vue";
import AppSidebar from "./components/AppSidebar.vue";
import BottomTabBar from "./components/BottomTabBar.vue";
import SearchView from "./components/SearchView.vue";
import DownloadsView from "./components/DownloadsView.vue";
import PlaylistsView from "./components/PlaylistsView.vue";
import SettingsView from "./components/SettingsView.vue";

type ViewKey = "search" | "downloads" | "playlists" | "settings";

const current = ref<ViewKey>("search");

const pageTitles: Record<ViewKey, string> = {
  search: "Cari",
  downloads: "Unduhan",
  playlists: "Playlist",
  settings: "Pengaturan",
};

const pageTitle = computed(() => pageTitles[current.value]);

function navigate(key: string) {
  current.value = key as ViewKey;
}
</script>

<template>
  <div class="flex h-screen overflow-hidden bg-am-bg-light dark:bg-am-bg-dark">
    <!-- Desktop sidebar -->
    <AppSidebar
      :model-value="current"
      @update:model-value="navigate"
    />

    <!-- Main -->
    <div class="flex flex-1 flex-col overflow-hidden">
      <!-- Top bar (mobile only) -->
      <header class="flex items-center border-b border-black/5 bg-am-bg-light px-5 py-3 md:hidden">
        <span class="text-lg font-bold tracking-tight">{{ pageTitle }}</span>
      </header>

      <!-- Content — pb-20 on mobile for bottom tab bar -->
      <main class="flex-1 overflow-y-auto pb-20 md:pb-0">
        <div class="animate-fade-in">
          <SearchView v-if="current === 'search'" @downloaded="navigate('downloads')" />
          <DownloadsView v-else-if="current === 'downloads'" />
          <PlaylistsView v-else-if="current === 'playlists'" />
          <SettingsView v-else-if="current === 'settings'" />
        </div>
      </main>
    </div>

    <!-- Mobile bottom tab bar -->
    <BottomTabBar
      :model-value="current"
      @update:model-value="navigate"
    />
  </div>
</template>
