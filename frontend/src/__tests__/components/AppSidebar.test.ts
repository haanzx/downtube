import { describe, it, expect } from "vitest";
import { mount } from "@vue/test-utils";
import AppSidebar from "../../components/AppSidebar.vue";

describe("AppSidebar", () => {
  const factory = (props = {}) =>
    mount(AppSidebar, {
      props: { modelValue: "search", ...props },
    });

  it("render 4 navigation items", () => {
    const wrapper = factory();
    const buttons = wrapper.findAll("nav button");
    expect(buttons.length).toBe(4);
  });

  it("render tooltip labels", () => {
    const wrapper = factory();
    expect(wrapper.text()).toContain("Cari");
    expect(wrapper.text()).toContain("Unduhan");
    expect(wrapper.text()).toContain("Playlist");
    expect(wrapper.text()).toContain("Pengaturan");
  });

  it("emit update:modelValue saat item diklik", async () => {
    const wrapper = factory();
    const buttons = wrapper.findAll("nav button");
    await buttons[1].trigger("click");
    expect(wrapper.emitted("update:modelValue")).toEqual([["downloads"]]);
  });

  it("sidebar hidden di mobile (hidden class)", () => {
    const wrapper = factory();
    expect(wrapper.classes()).toContain("hidden");
  });

  it("sidebar flex di desktop (md:flex)", () => {
    const wrapper = factory();
    expect(wrapper.classes()).toContain("md:flex");
  });

  it("item aktif punya class highlight", () => {
    const wrapper = factory({ modelValue: "search" });
    const buttons = wrapper.findAll("nav button");
    expect(buttons[0].classes()).toContain("bg-am-accent-light/10");
    expect(buttons[0].classes()).toContain("text-am-accent-light");
  });

  it("item tidak aktif punya class default", () => {
    const wrapper = factory({ modelValue: "search" });
    const buttons = wrapper.findAll("nav button");
    expect(buttons[1].classes()).not.toContain("bg-am-accent-light/10");
  });
});
