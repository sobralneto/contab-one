<template>
  <div class="app-layout">
    <!-- Modern sidebar -->
    <aside class="sidebar" :class="{ collapsed: ui.sidebarCollapsed }">
      <!-- Brand -->
      <div class="sidebar-brand">
        <!-- Recolhida, a sidebar tem 68px: a logo horizontal não cabe, então
             mostramos só o símbolo. -->
        <img
          class="brand-logo"
          :class="{ 'brand-logo--marca': ui.sidebarCollapsed }"
          :src="ui.sidebarCollapsed ? logoMarca : logoHorizontal"
          alt="Contab One"
        />
      </div>

      <!-- Navigation -->
      <nav class="sidebar-nav">
        <div class="nav-section-label">Principal</div>

        <router-link
          to="/dashboard"
          class="nav-item"
          active-class="nav-item--active"
        >
          <span class="nav-icon">
            <svg
              width="18"
              height="18"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
              stroke-linecap="round"
              stroke-linejoin="round"
            >
              <rect x="3" y="3" width="7" height="7" />
              <rect x="14" y="3" width="7" height="7" />
              <rect x="14" y="14" width="7" height="7" />
              <rect x="3" y="14" width="7" height="7" />
            </svg>
          </span>
          <span class="nav-label">Dashboard</span>
        </router-link>

        <router-link
          to="/clientes"
          class="nav-item"
          active-class="nav-item--active"
        >
          <span class="nav-icon">
            <svg
              width="18"
              height="18"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
              stroke-linecap="round"
              stroke-linejoin="round"
            >
              <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
              <circle cx="9" cy="7" r="4" />
              <path d="M23 21v-2a4 4 0 0 0-3-3.87" />
              <path d="M16 3.13a4 4 0 0 1 0 7.75" />
            </svg>
          </span>
          <span class="nav-label">Clientes</span>
        </router-link>

        <router-link
          to="/execucoes"
          class="nav-item"
          active-class="nav-item--active"
        >
          <span class="nav-icon">
            <svg
              width="18"
              height="18"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
              stroke-linecap="round"
              stroke-linejoin="round"
            >
              <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
            </svg>
          </span>
          <span class="nav-label">Execu&ccedil;&otilde;es</span>
        </router-link>

        <div class="nav-section-label">Configura&ccedil;&atilde;o</div>

        <router-link
          to="/agentes"
          class="nav-item"
          active-class="nav-item--active"
          v-if="auth.isEscritorioAdmin"
        >
          <span class="nav-icon">
            <svg
              width="18"
              height="18"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
              stroke-linecap="round"
              stroke-linejoin="round"
            >
              <circle cx="12" cy="12" r="3" />
              <path d="M12 1v2" />
              <path d="M12 21v2" />
              <path d="M4.22 4.22l1.42 1.42" />
              <path d="M18.36 18.36l1.42 1.42" />
              <path d="M1 12h2" />
              <path d="M21 12h2" />
              <path d="M4.22 19.78l1.42-1.42" />
              <path d="M18.36 5.64l1.42-1.42" />
            </svg>
          </span>
          <span class="nav-label">Agentes</span>
        </router-link>

        <router-link
          to="/usuarios"
          class="nav-item"
          active-class="nav-item--active"
          v-if="auth.isEscritorioAdmin"
        >
          <span class="nav-icon">
            <svg
              width="18"
              height="18"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
              stroke-linecap="round"
              stroke-linejoin="round"
            >
              <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" />
              <circle cx="9" cy="7" r="4" />
              <line x1="19" y1="8" x2="19" y2="14" />
              <line x1="22" y1="11" x2="16" y2="11" />
            </svg>
          </span>
          <span class="nav-label">Usu&aacute;rios</span>
        </router-link>

        <router-link
          to="/configuracao"
          class="nav-item"
          active-class="nav-item--active"
          v-if="auth.isEscritorioAdmin"
        >
          <span class="nav-icon">
            <svg
              width="18"
              height="18"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
              stroke-linecap="round"
              stroke-linejoin="round"
            >
              <circle cx="12" cy="12" r="3" />
              <path
                d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"
              />
            </svg>
          </span>
          <span class="nav-label">Configura&ccedil;&atilde;o</span>
        </router-link>

        <!-- Admin section -->
        <template v-if="auth.isPlatformAdmin">
          <div class="nav-section-label">Admin</div>

          <router-link
            to="/admin/escritorios"
            class="nav-item"
            active-class="nav-item--active"
          >
            <span class="nav-icon">
              <svg
                width="18"
                height="18"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
                stroke-linecap="round"
                stroke-linejoin="round"
              >
                <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" />
                <polyline points="9 22 9 12 15 12 15 22" />
              </svg>
            </span>
            <span class="nav-label">Escrit&oacute;rios</span>
          </router-link>

          <router-link
            to="/admin/planos"
            class="nav-item"
            active-class="nav-item--active"
          >
            <span class="nav-icon">
              <svg
                width="18"
                height="18"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
                stroke-linecap="round"
                stroke-linejoin="round"
              >
                <polygon
                  points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"
                />
              </svg>
            </span>
            <span class="nav-label">Planos</span>
          </router-link>

          <router-link
            to="/admin/regras"
            class="nav-item"
            active-class="nav-item--active"
          >
            <span class="nav-icon">
              <svg
                width="18"
                height="18"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
                stroke-linecap="round"
                stroke-linejoin="round"
              >
                <line x1="8" y1="6" x2="21" y2="6" />
                <line x1="8" y1="12" x2="21" y2="12" />
                <line x1="8" y1="18" x2="21" y2="18" />
                <line x1="3" y1="6" x2="3.01" y2="6" />
                <line x1="3" y1="12" x2="3.01" y2="12" />
                <line x1="3" y1="18" x2="3.01" y2="18" />
              </svg>
            </span>
            <span class="nav-label">Regras</span>
          </router-link>
        </template>
      </nav>

    </aside>

    <!-- Main area -->
    <div class="main-area">
      <header class="topbar">
        <button
          class="sidebar-toggle"
          @click="ui.toggleSidebar"
          aria-label="Alternar menu"
        >
          <svg
            width="20"
            height="20"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
          >
            <line x1="3" y1="12" x2="21" y2="12" />
            <line x1="3" y1="6" x2="21" y2="6" />
            <line x1="3" y1="18" x2="21" y2="18" />
          </svg>
        </button>
        <h1 class="page-title">{{ ui.pageTitle }}</h1>
        <div class="topbar-right">
          <!-- Montado uma única vez aqui: o componente resolve o conteúdo pela
               rota atual, então nenhuma view precisa saber que ele existe. -->
          <ExplicacaoPagina />

          <span class="topbar-divisor" aria-hidden="true"></span>

          <div class="topbar-user">
            <!-- title no avatar: em tela estreita o nome e o papel somem, e o
                 avatar sozinho precisa continuar identificando quem está logado. -->
            <span
              class="topbar-user-avatar"
              :title="`${auth.usuario?.nome ?? '—'} — ${papelLabel}`"
              >{{ userIniciais }}</span
            >
            <div class="topbar-user-info">
              <span class="topbar-user-name">{{
                auth.usuario?.nome ?? "—"
              }}</span>
              <span class="topbar-user-role">{{ papelLabel }}</span>
            </div>
          </div>

          <div class="topbar-actions">
            <!-- Dark mode toggle -->
            <button
              class="topbar-btn"
              @click="ui.toggleDarkMode"
              :title="ui.darkMode ? 'Modo claro' : 'Modo escuro'"
              :aria-label="ui.darkMode ? 'Modo claro' : 'Modo escuro'"
            >
              <svg
                v-if="!ui.darkMode"
                width="16"
                height="16"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
              >
                <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
              </svg>
              <svg
                v-else
                width="16"
                height="16"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
              >
                <circle cx="12" cy="12" r="5" />
                <line x1="12" y1="1" x2="12" y2="3" />
                <line x1="12" y1="21" x2="12" y2="23" />
                <line x1="4.22" y1="4.22" x2="5.64" y2="5.64" />
                <line x1="18.36" y1="18.36" x2="19.78" y2="19.78" />
                <line x1="1" y1="12" x2="3" y2="12" />
                <line x1="21" y1="12" x2="23" y2="12" />
                <line x1="4.22" y1="19.78" x2="5.64" y2="18.36" />
                <line x1="18.36" y1="5.64" x2="19.78" y2="4.22" />
              </svg>
            </button>
            <button
              class="topbar-btn topbar-logout"
              @click="onLogout"
              title="Sair"
              aria-label="Sair"
            >
              <svg
                width="16"
                height="16"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
                stroke-linecap="round"
                stroke-linejoin="round"
              >
                <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
                <polyline points="16 17 21 12 16 7" />
                <line x1="21" y1="12" x2="9" y2="12" />
              </svg>
            </button>
          </div>
        </div>
      </header>

      <main class="main-content">
        <router-view />
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { useRouter } from "vue-router";
import { useAuthStore } from "@/stores/auth";
import { useUiStore } from "@/stores/ui";
import { logout as apiLogout } from "@/api/endpoints/auth";
import ExplicacaoPagina from "@/components/comum/ExplicacaoPagina.vue";
import logoHorizontal from "@/assets/contab-one-horizontal.png";
import logoMarca from "@/assets/contab-one-favicon.png";

const auth = useAuthStore();
const ui = useUiStore();
const router = useRouter();

const userIniciais = computed(() => {
  const nome = auth.usuario?.nome ?? "";
  const partes = nome.trim().split(/\s+/);
  if (partes.length >= 2) {
    return (partes[0][0] + partes[partes.length - 1][0]).toUpperCase();
  }
  return nome.slice(0, 2).toUpperCase() || "?";
});

const papelLabel = computed(() => {
  switch (auth.papel) {
    case "PlatformAdmin":
      return "Admin da Plataforma";
    case "EscritorioAdmin":
      return "Admin do Escritório";
    case "EscritorioUsuario":
      return "Usuário";
    default:
      return "";
  }
});

async function onLogout() {
  try {
    await apiLogout();
  } catch {
    // Logout is best-effort — clear session regardless
  }
  auth.clearSession();
  router.replace("/login");
}
</script>

<style scoped>
/* Altura fixa (não min-height) + overflow hidden: é o que prende a sidebar e a
   topbar na tela e deixa a rolagem só para .main-content. Com min-height a
   página inteira rolava e a sidebar subia junto. */
.app-layout {
  display: flex;
  height: 100vh;
  overflow: hidden;
}

/* ── Sidebar ── */
.sidebar {
  width: 260px;
  min-width: 260px;
  background: var(--surface-sidebar);
  color: var(--sidebar-text);
  display: flex;
  flex-direction: column;
  transition:
    width 200ms cubic-bezier(0.4, 0, 0.2, 1),
    min-width 200ms cubic-bezier(0.4, 0, 0.2, 1);
  border-right: 1px solid var(--sidebar-border);
}

.sidebar.collapsed {
  width: 68px;
  min-width: 68px;
}

/* Brand — mesma altura e mesma cor da topbar: os dois formam a faixa do topo */
.sidebar-brand {
  height: 60px;
  min-height: 60px;
  padding: 0 1.125rem;
  background: var(--surface-topo);
  border-bottom: 1px solid var(--sidebar-border);
  display: flex;
  align-items: center;
  justify-content: center;
}

.brand-logo {
  display: block;
  width: auto;
  height: auto;
  max-width: 100%;
  max-height: 34px;
}

.brand-logo--marca {
  max-width: 44px;
}

/* No dark mode a sidebar é quase preta e a palavra "CONTAB" da logo é
   verde-escura: uma base clara atrás dela mantém o contraste. */
.dark .brand-logo {
  background: #ffffff;
  border-radius: 8px;
  padding: 5px 10px;
  max-height: 44px;
}

.dark .brand-logo--marca {
  padding: 5px;
  max-width: 48px;
}

/* Navigation */
.sidebar-nav {
  flex: 1;
  padding: 0.75rem 0;
  overflow-y: auto;
}

.nav-section-label {
  padding: 1rem 1.125rem 0.375rem;
  font-size: 10.5px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--sidebar-text-fraco);
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.55rem 1rem;
  margin: 2px 0.625rem;
  border-radius: 8px;
  color: var(--sidebar-text-suave);
  text-decoration: none;
  font-size: 14px;
  font-weight: 400;
  transition: all 150ms ease;
}

.nav-item:hover {
  background: var(--surface-sidebar-hover);
  color: var(--sidebar-text);
}

.nav-item--active {
  background: var(--sidebar-ativo-bg);
  color: var(--sidebar-ativo-text);
  font-weight: 500;
  box-shadow: inset 3px 0 0 var(--sidebar-ativo-marca);
}

.nav-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  flex-shrink: 0;
}

.nav-label {
  white-space: nowrap;
  overflow: hidden;
}

/* Collapsed state */
.collapsed .nav-label,
.collapsed .nav-section-label {
  display: none;
}

.collapsed .nav-item {
  justify-content: center;
  padding: 0.55rem;
}

.collapsed .sidebar-brand {
  padding: 0 0.5rem;
}

/* ── Main area ── */
.main-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  /* min-width/min-height 0: sem isso o item flex adota o tamanho do conteúdo
     como mínimo e .main-content nunca chega a rolar sozinho. */
  min-width: 0;
  min-height: 0;
  background: var(--surface-page);
}

/* ── Topbar — segunda metade da faixa do topo, mesma cor do espaço da logo.
   Era `glass` (fundo translúcido + blur): com o layout fixo nada mais passa
   por baixo dela, então o efeito não tinha o que desfocar. ── */
.topbar {
  height: 60px;
  min-height: 60px;
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 0 1.5rem;
  background: var(--surface-topo);
  border-bottom: 1px solid var(--border);
  z-index: 10;
  position: sticky;
  top: 0;
}

.sidebar-toggle {
  background: none;
  border: none;
  font-size: 20px;
  cursor: pointer;
  color: var(--text-secondary);
  padding: 0.35rem;
  line-height: 1;
  border-radius: 6px;
  display: flex;
  align-items: center;
  transition: all 120ms ease;
}

.sidebar-toggle:hover {
  background: var(--border);
  color: var(--text-primary);
}

.page-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
  letter-spacing: -0.01em;
}

.topbar-right {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: 0.75rem;
  min-width: 0;
}

.topbar-divisor {
  width: 1px;
  height: 24px;
  background: var(--border);
  flex-shrink: 0;
}

/* ── Bloco do usuário (vindo do rodapé da sidebar) ── */
.topbar-user {
  display: flex;
  align-items: center;
  gap: 0.625rem;
  min-width: 0;
}

.topbar-user-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: var(--accent-gradient);
  color: var(--accent-gradient-texto);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 600;
  flex-shrink: 0;
}

.topbar-user-info {
  display: flex;
  flex-direction: column;
  line-height: 1.25;
  min-width: 0;
}

.topbar-user-name {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.topbar-user-role {
  font-size: 11px;
  color: var(--text-muted);
  white-space: nowrap;
}

.topbar-actions {
  display: flex;
  gap: 0.25rem;
  flex-shrink: 0;
}

.topbar-btn {
  background: none;
  border: 1px solid var(--border);
  color: var(--text-secondary);
  border-radius: 6px;
  padding: 0.35rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 120ms ease;
}

.topbar-btn:hover {
  background: var(--border);
  color: var(--text-primary);
  border-color: var(--border-forte);
}

.topbar-logout:hover {
  background: var(--erro-suave);
  border-color: var(--erro);
  color: var(--erro);
}

/* Telas estreitas: o nome e o papel saem, o avatar (com title) fica. */
@media (max-width: 720px) {
  .topbar-user-info {
    display: none;
  }
}

/* ── Main content — o único painel que rola ── */
.main-content {
  flex: 1;
  min-height: 0;
  padding: 1.5rem;
  overflow-y: auto;
}
</style>
