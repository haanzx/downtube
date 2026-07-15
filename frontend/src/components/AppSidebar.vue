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
  <aside
    class="hidden w-20 flex-col items-center border-r border-black/5 bg-am-bg-light py-6 md:flex dark:border-white/5 dark:bg-am-bg-dark"
  >
    <!-- Logo -->
    <div
      class="mb-8 flex h-11 w-11 items-center justify-center rounded-2xl bg-am-accent-light text-base font-bold text-white dark:bg-am-accent-dark"
    >
      D
    </div>

    <!-- Navigation -->
    <nav class="flex flex-1 flex-col items-center gap-2" aria-label="Navigasi utama">
      <button
        v-for="item in items"
        :key="item.key"
        :aria-current="modelValue === item.key ? 'page' : undefined"
        @click="emit('update:modelValue', item.key)"
        :class="[
          'group relative flex h-12 w-12 items-center justify-center rounded-2xl transition-all duration-150',
          modelValue === item.key
            ? 'bg-am-accent-light/10 text-am-accent-light dark:bg-am-accent-dark/15 dark:text-am-accent-dark'
            : 'text-black/40 hover:bg-black/5 hover:text-black/90 dark:text-white/40 dark:hover:bg-white/5 dark:hover:text-white/90',
        ]"
      >
        <!-- Active indicator -->
        <span
          v-if="modelValue === item.key"
          class="absolute -left-[13px] top-1/2 h-5 w-[3px] -translate-y-1/2 rounded-full bg-am-accent-light dark:bg-am-accent-dark"
        />
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
        <!-- Tooltip -->
        <span class="pointer-events-none absolute left-full ml-3 whitespace-nowrap rounded-lg bg-am-surface-light px-3 py-1.5 text-xs font-medium text-black/90 opacity-0 shadow-lg transition-opacity group-hover:opacity-100 dark:bg-am-surface-dark dark:text-white/90">
          {{ item.label }}
        </span>
      </button>
    </nav>
  </aside>
</template>
