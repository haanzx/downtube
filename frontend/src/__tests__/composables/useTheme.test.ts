import { describe, it, expect, beforeEach, vi } from "vitest";

const localStorageMock = (() => {
  let store: Record<string, string> = {};
  return {
    getItem: vi.fn((key: string) => store[key] ?? null),
    setItem: vi.fn((key: string, value: string) => {
      store[key] = value;
    }),
    removeItem: vi.fn((key: string) => {
      delete store[key];
    }),
    clear: vi.fn(() => {
      store = {};
    }),
    get length() {
      return Object.keys(store).length;
    },
    key: vi.fn((index: number) => Object.keys(store)[index] ?? null),
  };
})();

vi.stubGlobal("localStorage", localStorageMock);

describe("useTheme", () => {
  beforeEach(() => {
    vi.resetModules();
    document.documentElement.classList.remove("dark");
    localStorageMock.clear();
  });

  it("reads initial state from DOM (dark)", async () => {
    document.documentElement.classList.add("dark");
    const { useTheme } = await import("../../composables/useTheme");
    const { isDark } = useTheme();
    expect(isDark.value).toBe(true);
  });

  it("reads initial state from DOM (light)", async () => {
    const { useTheme } = await import("../../composables/useTheme");
    const { isDark } = useTheme();
    expect(isDark.value).toBe(false);
  });

  it("toggle mengubah isDark dan apply ke DOM", async () => {
    const { useTheme } = await import("../../composables/useTheme");
    const { isDark, toggle } = useTheme();
    expect(isDark.value).toBe(false);
    toggle();
    expect(isDark.value).toBe(true);
    expect(document.documentElement.classList.contains("dark")).toBe(true);
  });

  it("toggle kembali ke light", async () => {
    const { useTheme } = await import("../../composables/useTheme");
    const { isDark, toggle } = useTheme();
    toggle();
    expect(isDark.value).toBe(true);
    toggle();
    expect(isDark.value).toBe(false);
    expect(document.documentElement.classList.contains("dark")).toBe(false);
  });

  it("setDark mengatur value secara langsung", async () => {
    const { useTheme } = await import("../../composables/useTheme");
    const { isDark, setDark } = useTheme();
    setDark(true);
    expect(isDark.value).toBe(true);
    expect(document.documentElement.classList.contains("dark")).toBe(true);
  });

  it("setDark(false) menghapus dark class", async () => {
    const { useTheme } = await import("../../composables/useTheme");
    const { isDark, setDark } = useTheme();
    setDark(true);
    setDark(false);
    expect(isDark.value).toBe(false);
    expect(document.documentElement.classList.contains("dark")).toBe(false);
  });
});
