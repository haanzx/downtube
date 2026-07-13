import { ref } from "vue";

const isDark = ref(document.documentElement.classList.contains("dark"));

export function useTheme() {
  function toggle() {
    isDark.value = !isDark.value;
    apply();
  }

  function setDark(value: boolean) {
    isDark.value = value;
    apply();
  }

  function apply() {
    if (isDark.value) {
      document.documentElement.classList.add("dark");
      localStorage.theme = "dark";
    } else {
      document.documentElement.classList.remove("dark");
      localStorage.theme = "light";
    }
  }

  return { isDark, toggle, setDark };
}
