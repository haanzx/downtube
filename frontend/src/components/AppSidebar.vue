<script setup lang="ts">
const props = defineProps<{ modelValue: string; open: boolean }>();
const emit = defineEmits<{
  (e: "update:modelValue", v: string): void;
  (e: "close"): void;
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
    :class="[
      'fixed inset-y-0 left-0 z-40 flex w-60 flex-col border-r border-slate-200 bg-white transition-transform duration-200 dark:border-slate-700 dark:bg-slate-800',
      'md:relative md:translate-x-0',
      open ? 'translate-x-0' : '-translate-x-full',
    ]"
  >
    <div class="flex items-center gap-2 px-5 py-5">
      <div
        class="flex h-8 w-8 items-center justify-center rounded-lg bg-slate-900 text-sm font-bold text-white dark:bg-white dark:text-slate-900"
      >
        D
      </div>
      <span class="text-base font-semibold tracking-tight">DownTube</span>
    </div>

    <nav class="flex-1 space-y-0.5 px-3">
      <button
        v-for="item in items"
        :key="item.key"
        @click="emit('update:modelValue', item.key)"
        :class="[
          'flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors',
          modelValue === item.key
            ? 'bg-slate-900 text-white dark:bg-slate-700 dark:text-white'
            : 'text-slate-600 hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-slate-700/50',
        ]"
      >
        <svg v-if="item.icon === 'search'" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
        </svg>
        <svg v-else-if="item.icon === 'download'" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M12 4v12m0 0l-4-4m4 4l4-4M4 20h16" />
        </svg>
        <svg v-else-if="item.icon === 'playlist'" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M4 6h16M4 10h16M4 14h10M4 18h6" />
        </svg>
        <svg v-else-if="item.icon === 'settings'" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.066 2.573c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.573 1.066c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.066-2.573c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
          <path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
        </svg>
        {{ item.label }}
      </button>
    </nav>
  </aside>
</template>
