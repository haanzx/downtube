import { describe, it, expect, vi, beforeEach } from "vitest";
import { mount } from "@vue/test-utils";
import SearchView from "../../components/SearchView.vue";

vi.mock("../../api", () => ({
  searchMusic: vi.fn().mockResolvedValue([]),
  previewUrl: vi.fn().mockResolvedValue(null),
  createDownload: vi.fn().mockResolvedValue({
    id: 1,
    url: "x",
    title: "Test",
    status: "pending",
    progress: 0,
    format: "mp3",
  }),
}));

describe("SearchView", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("render search input", () => {
    const wrapper = mount(SearchView);
    const input = wrapper.find("input");
    expect(input.exists()).toBe(true);
  });

  it("render search type buttons", () => {
    const wrapper = mount(SearchView);
    const buttons = wrapper.findAll("button");
    const catButtons = buttons.filter((b) => ["Lagu", "Album", "Artis", "Playlist"].includes(b.text().trim()));
    expect(catButtons.length).toBeGreaterThanOrEqual(4);
  });

  it("render search button", () => {
    const wrapper = mount(SearchView);
    const buttons = wrapper.findAll("button");
    const searchBtn = buttons.find((b) => b.text().includes("Cari"));
    expect(searchBtn).toBeDefined();
  });

  it("render header", () => {
    const wrapper = mount(SearchView);
    expect(wrapper.text()).toContain("Cari");
  });

  it("render empty state awal", () => {
    const wrapper = mount(SearchView);
    expect(wrapper.text()).toContain("Ketik judul lagu");
  });

  it("search input menerima input", async () => {
    const wrapper = mount(SearchView);
    const input = wrapper.find("input");
    await input.setValue("test lagu");
    expect((input.element as HTMLInputElement).value).toBe("test lagu");
  });
});
