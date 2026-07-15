import { describe, it, expect, vi, beforeEach } from "vitest";
import { mount } from "@vue/test-utils";
import DownloadsView from "../../components/DownloadsView.vue";

vi.mock("../../api", () => ({
  listDownloads: vi.fn().mockResolvedValue([]),
  deleteDownload: vi.fn().mockResolvedValue(undefined),
  retryDownload: vi.fn().mockResolvedValue(undefined),
}));

vi.mock("../../composables/useSSE", () => ({
  useSSE: () => ({
    latest: { value: new Map() },
    connected: { value: false },
    connect: vi.fn(),
    close: vi.fn(),
    getLatest: vi.fn().mockReturnValue(undefined),
  }),
}));

describe("DownloadsView", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("render header", () => {
    const wrapper = mount(DownloadsView);
    expect(wrapper.text()).toContain("Unduhan");
  });

  it("render empty state", async () => {
    const wrapper = mount(DownloadsView);
    await wrapper.vm.$nextTick();
    await wrapper.vm.$nextTick();
    expect(wrapper.text()).toContain("Belum ada unduhan");
  });

  it("render download stats", async () => {
    const wrapper = mount(DownloadsView);
    await wrapper.vm.$nextTick();
    expect(wrapper.text()).toContain("selesai");
    expect(wrapper.text()).toContain("aktif");
    expect(wrapper.text()).toContain("gagal");
  });

  it("render phase labels", () => {
    const wrapper = mount(DownloadsView);
    const vm = wrapper.vm as unknown as { PHASE_LABELS: Record<string, string> };
    expect(vm.PHASE_LABELS.downloading).toBe("Mengunduh...");
    expect(vm.PHASE_LABELS.resolving).toBe("Mengambil info...");
    expect(vm.PHASE_LABELS.tagging).toBe("Menanam metadata...");
  });
});
