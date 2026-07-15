import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import {
  listDownloads,
  createDownload,
  searchMusic,
  getHealth,
  previewUrl,
  deleteDownload,
  retryDownload,
} from "../../api";

beforeEach(() => {
  vi.restoreAllMocks();
});

afterEach(() => {
  vi.restoreAllMocks();
});

describe("API layer", () => {
  describe("getHealth", () => {
    it("return status dari server", async () => {
      vi.spyOn(globalThis, "fetch").mockResolvedValue(
        new Response(JSON.stringify({ status: "ok" }), { status: 200 }),
      );
      const result = await getHealth();
      expect(result.status).toBe("ok");
    });
  });

  describe("listDownloads", () => {
    it("return array pada success", async () => {
      const mockData = [{ id: 1, title: "Song", status: "done" }];
      vi.spyOn(globalThis, "fetch").mockResolvedValue(
        new Response(JSON.stringify(mockData), { status: 200 }),
      );
      const result = await listDownloads();
      expect(Array.isArray(result)).toBe(true);
      expect(result).toHaveLength(1);
    });

    it("return empty array pada error", async () => {
      vi.spyOn(globalThis, "fetch").mockResolvedValue(
        new Response("Error", { status: 500 }),
      );
      const result = await listDownloads();
      expect(result).toEqual([]);
    });
  });

  describe("createDownload", () => {
    it("return DownloadItem pada success", async () => {
      const mockItem = { id: 1, url: "https://x.com/1", status: "pending", progress: 0, format: "mp3" };
      vi.spyOn(globalThis, "fetch").mockResolvedValue(
        new Response(JSON.stringify(mockItem), { status: 200 }),
      );
      const result = await createDownload("https://x.com/1");
      expect(result.id).toBe(1);
      expect(result.status).toBe("pending");
    });

    it("throw Error pada HTTP error", async () => {
      vi.spyOn(globalThis, "fetch").mockResolvedValue(
        new Response(JSON.stringify({ detail: "Invalid URL" }), { status: 400 }),
      );
      await expect(createDownload("bad-url")).rejects.toThrow("Invalid URL");
    });

    it("throw Error pada network error dengan default message", async () => {
      vi.spyOn(globalThis, "fetch").mockResolvedValue(
        new Response("Error", { status: 500 }),
      );
      await expect(createDownload("url")).rejects.toThrow();
    });

    it("mengirim body dengan opts", async () => {
      vi.spyOn(globalThis, "fetch").mockResolvedValue(
        new Response(JSON.stringify({ id: 1, status: "pending", progress: 0, format: "flac" }), { status: 200 }),
      );
      await createDownload("https://x.com/1", { format: "flac", title: "Test" });

      const call = vi.mocked(globalThis.fetch).mock.calls[0];
      const body = JSON.parse(call[1]?.body as string);
      expect(body.url).toBe("https://x.com/1");
      expect(body.format).toBe("flac");
      expect(body.title).toBe("Test");
    });
  });

  describe("searchMusic", () => {
    it("return array pada success", async () => {
      const mockResults = [{ id: "1", title: "Song", type: "song", url: "https://x.com/1" }];
      vi.spyOn(globalThis, "fetch").mockResolvedValue(
        new Response(JSON.stringify(mockResults), { status: 200 }),
      );
      const result = await searchMusic("test song", "song");
      expect(Array.isArray(result)).toBe(true);
    });

    it("return empty array pada error", async () => {
      vi.spyOn(globalThis, "fetch").mockResolvedValue(
        new Response("Error", { status: 500 }),
      );
      const result = await searchMusic("test");
      expect(result).toEqual([]);
    });

    it("mengirim query params", async () => {
      vi.spyOn(globalThis, "fetch").mockResolvedValue(
        new Response(JSON.stringify([]), { status: 200 }),
      );
      await searchMusic("lagu artist", "album", 10);

      const call = vi.mocked(globalThis.fetch).mock.calls[0];
      const calledUrl = call[0] as string;
      expect(calledUrl).toContain("q=lagu+artist");
      expect(calledUrl).toContain("type=album");
      expect(calledUrl).toContain("limit=10");
    });
  });

  describe("previewUrl", () => {
    it("return PreviewResult pada success", async () => {
      const mockPreview = { id: "1", title: "Preview Song", type: "song", url: "https://x.com/1" };
      vi.spyOn(globalThis, "fetch").mockResolvedValue(
        new Response(JSON.stringify(mockPreview), { status: 200 }),
      );
      const result = await previewUrl("https://youtube.com/watch?v=1");
      expect(result?.title).toBe("Preview Song");
    });

    it("return null pada error", async () => {
      vi.spyOn(globalThis, "fetch").mockResolvedValue(
        new Response("Error", { status: 404 }),
      );
      const result = await previewUrl("https://invalid.url");
      expect(result).toBeNull();
    });
  });

  describe("deleteDownload", () => {
    it("mengirim DELETE request", async () => {
      vi.spyOn(globalThis, "fetch").mockResolvedValue(
        new Response(null, { status: 204 }),
      );
      await deleteDownload(42);

      const call = vi.mocked(globalThis.fetch).mock.calls[0];
      expect(call[0]).toContain("/api/downloads/42");
      expect(call[1]?.method).toBe("DELETE");
    });
  });

  describe("retryDownload", () => {
    it("mengirim POST request", async () => {
      vi.spyOn(globalThis, "fetch").mockResolvedValue(
        new Response(null, { status: 200 }),
      );
      await retryDownload(42);

      const call = vi.mocked(globalThis.fetch).mock.calls[0];
      expect(call[0]).toContain("/api/downloads/42/retry");
      expect(call[1]?.method).toBe("POST");
    });
  });
});
