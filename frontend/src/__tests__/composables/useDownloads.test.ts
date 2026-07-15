import { describe, it, expect, vi, beforeEach } from "vitest";
import { useDownloads } from "../../composables/useDownloads";
import * as api from "../../api";

vi.mock("../../api", () => ({
  listDownloads: vi.fn(),
  createDownload: vi.fn(),
}));

describe("useDownloads", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("refresh memuat items", async () => {
    const mockItems = [
      { id: 1, url: "https://x.com/1", title: "Song 1", status: "done", progress: 100, format: "mp3" },
    ];
    vi.mocked(api.listDownloads).mockResolvedValue(mockItems);

    const { items, loading, refresh } = useDownloads();
    expect(loading.value).toBe(false);
    expect(items.value).toEqual([]);

    await refresh();
    expect(loading.value).toBe(false);
    expect(items.value).toEqual(mockItems);
  });

  it("refresh set loading ke true selama proses", async () => {
    let resolvePromise: (v: unknown) => void;
    const pending = new Promise((resolve) => {
      resolvePromise = resolve;
    });
    vi.mocked(api.listDownloads).mockReturnValue(pending as Promise<never>);

    const { loading, refresh } = useDownloads();
    const refreshPromise = refresh();
    expect(loading.value).toBe(true);

    resolvePromise!([]);
    await refreshPromise;
    expect(loading.value).toBe(false);
  });

  it("enqueue menambahkan item secara optimistic", async () => {
    const mockResult = {
      id: 2,
      url: "https://youtube.com/watch?v=y",
      title: "Test Song",
      artist: "Test Artist",
      status: "pending",
      progress: 0,
      format: "mp3",
    };
    vi.mocked(api.createDownload).mockResolvedValue(mockResult);

    const { items, enqueue } = useDownloads();
    const result = await enqueue("https://youtube.com/watch?v=y");

    expect(result.id).toBe(2);
    expect(items.value.length).toBe(1);
    expect(items.value[0].title).toBe("Test Song");
    expect(items.value[0].artist).toBe("Test Artist");
    expect(items.value[0].status).toBe("pending");
    expect(items.value[0].progress).toBe(0);
  });

  it("enqueue mengisi lastMessage", async () => {
    vi.mocked(api.createDownload).mockResolvedValue({
      id: 3,
      url: "https://youtube.com/watch?v=z",
      title: "My Song",
      status: "pending",
      progress: 0,
      format: "mp3",
    });

    const { lastMessage, enqueue } = useDownloads();
    await enqueue("https://youtube.com/watch?v=z");
    expect(lastMessage.value).toBe("My Song");
  });

  it("enqueue mengirim opts ke createDownload", async () => {
    vi.mocked(api.createDownload).mockResolvedValue({
      id: 4,
      url: "https://x.com/4",
      status: "pending",
      progress: 0,
      format: "mp3",
    });

    const { enqueue } = useDownloads();
    await enqueue("https://x.com/4", { format: "flac", lyrics_option: "lrc" });

    expect(api.createDownload).toHaveBeenCalledWith("https://x.com/4", {
      format: "flac",
      lyrics_option: "lrc",
    });
  });
});
