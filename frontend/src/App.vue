<script setup lang="ts">
import { ref } from "vue";
import AppSidebar from "./components/AppSidebar.vue";
import SearchView from "./components/SearchView.vue";
import DownloadsView from "./components/DownloadsView.vue";
import PlaylistsView from "./components/PlaylistsView.vue";
import SettingsView from "./components/SettingsView.vue";

type ViewKey = "search" | "downloads" | "playlists" | "settings";

const current = ref<ViewKey>("search");
const sidebarOpen = ref(false);

function navigate(key: string) {
  current.value = key as ViewKey;
  sidebarOpen.value = false;
}
</script>

<template>
  <div class="flex h-screen overflow-hidden bg-slate-50 dark:bg-slate-900">
    <!-- Sidebar -->
    <AppSidebar
      :model-value="current"
      :open="sidebarOpen"
      @update:model-value="navigate"
      @close="sidebarOpen = false"
    />

    <!-- Main -->
    <div class="flex flex-1 flex-col overflow-hidden">
      <!-- Top bar (mobile) -->
      <header class="flex items-center border-b border-slate-200 bg-white px-4 py-3 dark:border-slate-700 dark:bg-slate-800 md:hidden">
        <button
          @click="sidebarOpen = true"
          class="rounded-lg p-1.5 text-slate-600 hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-slate-700"
        >
          <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M4 6h16M4 12h16M4 18h16" />
          </svg>
        </button>
        <span class="ml-3 text-sm font-semibold">DownTube</span>
      </header>

      <!-- Content -->
      <main class="flex-1 overflow-y-auto">
        <div class="animate-fade-in">
          <SearchView v-if="current === 'search'" @downloaded="navigate('downloads')" />
          <DownloadsView v-else-if="current === 'downloads'" />
          <PlaylistsView v-else-if="current === 'playlists'" />
          <SettingsView v-else-if="current === 'settings'" />
        </div>
      </main>
    </div>

    <!-- Sidebar overlay (mobile) -->
    <Transition name="fade">
      <div
        v-if="sidebarOpen"
        class="fixed inset-0 z-30 bg-black/40 md:hidden"
        @click="sidebarOpen = false"
      />
    </Transition>
  </div>
</template>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
