import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";

class MockEventSource {
  url: string;
  onopen: (() => void) | null = null;
  onmessage: ((e: MessageEvent) => void) | null = null;
  onerror: (() => void) | null = null;
  readyState = 0;
  close = vi.fn();

  constructor(url: string) {
    this.url = url;
  }

  simulateOpen() {
    this.onopen?.();
  }

  simulateMessage(data: string) {
    this.onmessage?.({ data } as MessageEvent);
  }

  simulateError() {
    this.onerror?.();
  }
}

let mockInstances: MockEventSource[] = [];

beforeEach(() => {
  vi.resetModules();
  mockInstances = [];

  vi.stubGlobal(
    "EventSource",
    class extends MockEventSource {
      constructor(url: string) {
        super(url);
        mockInstances.push(this);
      }
    },
  );
});

afterEach(() => {
  vi.restoreAllMocks();
});

describe("useSSE", () => {
  it("connect membuat EventSource", async () => {
    const { useSSE } = await import("../../composables/useSSE");
    const { connect } = useSSE("/api/events");
    connect();
    expect(mockInstances.length).toBe(1);
    expect(mockInstances[0].url).toBe("/api/events");
  });

  it("connected berubah ke true saat onopen", async () => {
    const { useSSE } = await import("../../composables/useSSE");
    const { connected, connect } = useSSE("/api/events");
    connect();
    mockInstances[0].simulateOpen();
    expect(connected.value).toBe(true);
  });

  it("event disimpan ke latest map", async () => {
    const { useSSE } = await import("../../composables/useSSE");
    const { connect, getLatest } = useSSE("/api/events");
    connect();
    mockInstances[0].simulateMessage(
      JSON.stringify({ id: 1, progress: 50, status: "downloading" }),
    );
    const ev = getLatest(1);
    expect(ev).toBeDefined();
    expect(ev?.progress).toBe(50);
    expect(ev?.status).toBe("downloading");
  });

  it("event tanpa id diabaikan", async () => {
    const { useSSE } = await import("../../composables/useSSE");
    const { connect, getLatest } = useSSE("/api/events");
    connect();
    mockInstances[0].simulateMessage(JSON.stringify({ progress: 50 }));
    expect(getLatest(999)).toBeUndefined();
  });

  it("close memutus EventSource", async () => {
    const { useSSE } = await import("../../composables/useSSE");
    const { connected, connect, close } = useSSE("/api/events");
    connect();
    mockInstances[0].simulateOpen();
    expect(connected.value).toBe(true);
    close();
    expect(connected.value).toBe(false);
    expect(mockInstances[0].close).toHaveBeenCalled();
  });

  it("MAX_EVENTS membatasi jumlah event", async () => {
    const { useSSE } = await import("../../composables/useSSE");
    const { connect, latest } = useSSE("/api/events");
    connect();
    for (let i = 0; i < 55; i++) {
      mockInstances[0].simulateMessage(
        JSON.stringify({ id: i, progress: i }),
      );
    }
    expect(latest.value.size).toBe(50);
    expect(latest.value.has(0)).toBe(false);
    expect(latest.value.has(4)).toBe(false);
    expect(latest.value.has(5)).toBe(true);
  });

  it("error set connected ke false", async () => {
    const { useSSE } = await import("../../composables/useSSE");
    const { connected, connect } = useSSE("/api/events");
    connect();
    mockInstances[0].simulateOpen();
    expect(connected.value).toBe(true);
    mockInstances[0].simulateError();
    expect(connected.value).toBe(false);
  });

  it("getLatest return undefined untuk id tidak ada", async () => {
    const { useSSE } = await import("../../composables/useSSE");
    const { getLatest } = useSSE("/api/events");
    expect(getLatest(999)).toBeUndefined();
  });
});
