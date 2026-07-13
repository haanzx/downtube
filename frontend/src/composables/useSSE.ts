import { onUnmounted, ref } from "vue";

export interface SseEvent {
  id?: number;
  progress?: number;
  status?: string;
  phase?: string;
  phase_label?: string;
  output_path?: string;
  [key: string]: unknown;
}

export function useSSE(url: string) {
  const latest = ref<Map<number, SseEvent>>(new Map());
  const connected = ref(false);
  let es: EventSource | null = null;
  const MAX_EVENTS = 50;
  let eventCount = 0;

  function connect() {
    es = new EventSource(url);
    es.onopen = () => (connected.value = true);
    es.onmessage = (e) => {
      try {
        const ev: SseEvent = JSON.parse(e.data);
        if (ev.id != null) {
          latest.value.set(ev.id, ev);
          eventCount++;
          if (eventCount > MAX_EVENTS) {
            const firstKey = latest.value.keys().next().value;
            if (firstKey !== undefined) latest.value.delete(firstKey);
            eventCount--;
          }
        }
      } catch {
        // ignore parse errors
      }
    };
    es.onerror = () => (connected.value = false);
  }

  function close() {
    es?.close();
    connected.value = false;
  }

  function getLatest(id: number): SseEvent | undefined {
    return latest.value.get(id);
  }

  onUnmounted(close);

  return { latest, connected, connect, close, getLatest };
}
