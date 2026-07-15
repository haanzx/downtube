import { describe, it, expect } from "vitest";
import { mount } from "@vue/test-utils";
import BottomTabBar from "../../components/BottomTabBar.vue";

describe("BottomTabBar", () => {
  const factory = (props = {}) =>
    mount(BottomTabBar, {
      props: { modelValue: "search", ...props },
    });

  it("render 4 navigation items", () => {
    const wrapper = factory();
    const buttons = wrapper.findAll("nav button");
    expect(buttons.length).toBe(4);
  });

  it("render labels", () => {
    const wrapper = factory();
    expect(wrapper.text()).toContain("Cari");
    expect(wrapper.text()).toContain("Unduhan");
    expect(wrapper.text()).toContain("Playlist");
    expect(wrapper.text()).toContain("Pengaturan");
  });

  it("emit update:modelValue saat item diklik", async () => {
    const wrapper = factory();
    const buttons = wrapper.findAll("nav button");
    await buttons[2].trigger("click");
    expect(wrapper.emitted("update:modelValue")).toEqual([["playlists"]]);
  });

  it("hidden di desktop (md:hidden)", () => {
    const wrapper = factory();
    expect(wrapper.classes()).toContain("md:hidden");
  });

  it("fixed bottom", () => {
    const wrapper = factory();
    expect(wrapper.classes()).toContain("fixed");
    expect(wrapper.classes()).toContain("bottom-0");
  });

  it("item aktif punya accent color", () => {
    const wrapper = factory({ modelValue: "downloads" });
    const buttons = wrapper.findAll("nav button");
    expect(buttons[1].classes()).toContain("text-am-accent-light");
  });

  it("item tidak aktif punya secondary color", () => {
    const wrapper = factory({ modelValue: "search" });
    const buttons = wrapper.findAll("nav button");
    expect(buttons[1].classes()).toContain("text-black/40");
  });
});
