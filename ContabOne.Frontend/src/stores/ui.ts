import { defineStore } from "pinia";
import { ref, watch } from "vue";

export const useUiStore = defineStore("ui", () => {
  const sidebarCollapsed = ref(false);
  const pageTitle = ref("");

  // Dark mode — persisted in localStorage
  const storedDark = localStorage.getItem("nfse-dark-mode");
  const darkMode = ref(storedDark === "true");

  // Sync to <html> class and localStorage
  watch(
    darkMode,
    (val) => {
      document.documentElement.classList.toggle("dark", val);
      localStorage.setItem("nfse-dark-mode", String(val));
    },
    { immediate: true },
  );

  function toggleSidebar() {
    sidebarCollapsed.value = !sidebarCollapsed.value;
  }

  function toggleDarkMode() {
    darkMode.value = !darkMode.value;
  }

  function setPageTitle(title: string) {
    pageTitle.value = title;
    document.title = title ? `${title} — Contab One` : "Contab One";
  }

  return {
    sidebarCollapsed,
    pageTitle,
    darkMode,
    toggleSidebar,
    toggleDarkMode,
    setPageTitle,
  };
});
