<script setup lang="ts">
const props = defineProps<{ modelValue: string }>();
const emit = defineEmits<{
  (e: "update:modelValue", v: string): void;
}>();

const items: { key: string; label: string; icon: string }[] = [
  { key: "search", label: "Cari", icon: "search" },
  { key: "downloads", label: "Unduhan", icon: "download" },
  { key: "playlists", label: "Playlist", icon: "playlist" },
  { key: "settings", label: "Pengaturan", icon: "settings" },
];

void props;
</script>

<template>
  <nav
    class="fixed bottom-0 left-0 right-0 z-40 flex items-stretch border-t border-black/5 bg-am-bg-light safe-area-bottom md:hidden dark:border-white/5 dark:bg-am-bg-dark"
    aria-label="Navigasi bawah"
  >
    <button
      v-for="item in items"
      :key="item.key"
      :aria-current="modelValue === item.key ? 'page' : undefined"
      @click="emit('update:modelValue', item.key)"
      :class="[
        'flex flex-1 flex-col items-center justify-center gap-1 py-2 transition-colors duration-150',
        modelValue === item.key
          ? 'text-am-accent-light dark:text-am-accent-dark'
          : 'text-black/40 dark:text-white/40',
      ]"
    >
      <svg v-if="item.icon === 'search'" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
        <path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
      </svg>
      <svg v-else-if="item.icon === 'download'" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
        <path stroke-linecap="round" stroke-linejoin="round" d="M12 4v12m0 0l-4-4m4 4l4-4M4 20h16" />
      </svg>
      <svg v-else-if="item.icon === 'playlist'" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
        <path stroke-linecap="round" stroke-linejoin="round" d="M4 6h16M4 10h16M4 14h10M4 18h6" />
      </svg>
      <svg v-else-if="item.icon === 'settings'" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
        <path stroke-linecap="round" stroke-linejoin="round" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.066 2.573c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.573 1.066c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.066-2.573c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
        <path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
      </svg>
      <span class="text-[10px] font-medium leading-none">{{ item.label }}</span>
    </button>
  </nav>
</template>

<style scoped>
.safe-area-bottom {
  padding-bottom: env(safe-area-inset-bottom, 0px);
}
</style>
