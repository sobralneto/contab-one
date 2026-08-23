<template>
  <div class="login-view">
    <div class="login-header">
      <h2 class="login-title">Bem-vindo de volta</h2>
      <p class="login-subtitle">Entre com sua conta para continuar</p>
    </div>

    <form class="login-form" @submit.prevent="onSubmit">
      <div class="form-field">
        <label for="email">E-mail</label>
        <div class="input-wrapper">
          <svg
            class="input-icon"
            width="16"
            height="16"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
          >
            <path
              d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"
            />
            <polyline points="22,6 12,13 2,6" />
          </svg>
          <input
            id="email"
            v-model="email"
            type="email"
            placeholder="seu@email.com"
            autocomplete="email"
            :disabled="loading"
          />
        </div>
      </div>
      <div class="form-field">
        <label for="password">Senha</label>
        <div class="input-wrapper">
          <svg
            class="input-icon"
            width="16"
            height="16"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
          >
            <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
            <path d="M7 11V7a5 5 0 0 1 10 0v4" />
          </svg>
          <input
            id="password"
            v-model="password"
            :type="showPassword ? 'text' : 'password'"
            placeholder="Sua senha"
            autocomplete="current-password"
            :disabled="loading"
          />
          <button
            type="button"
            class="toggle-pw"
            @click="showPassword = !showPassword"
            tabindex="-1"
          >
            <svg
              v-if="!showPassword"
              width="16"
              height="16"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
            >
              <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
              <circle cx="12" cy="12" r="3" />
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
              <path
                d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"
              />
              <line x1="1" y1="1" x2="23" y2="23" />
            </svg>
          </button>
        </div>
      </div>

      <p class="login-error" v-if="errorMsg">
        <svg
          width="14"
          height="14"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
          stroke-linecap="round"
          stroke-linejoin="round"
        >
          <circle cx="12" cy="12" r="10" />
          <line x1="15" y1="9" x2="9" y2="15" />
          <line x1="9" y1="9" x2="15" y2="15" />
        </svg>
        {{ errorMsg }}
      </p>

      <button type="submit" class="btn-login" :disabled="loading">
        <span v-if="!loading">Entrar</span>
        <span v-else class="spinner"></span>
      </button>
    </form>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { useRouter, useRoute } from "vue-router";
import { useAuthStore } from "@/stores/auth";
import { login as apiLogin } from "@/api/endpoints/auth";

const router = useRouter();
const route = useRoute();
const auth = useAuthStore();

const email = ref("");
const password = ref("");
const loading = ref(false);
const errorMsg = ref("");
const showPassword = ref(false);

async function onSubmit() {
  errorMsg.value = "";
  loading.value = true;
  try {
    const res = await apiLogin({
      email: email.value,
      password: password.value,
    });
    auth.setSession(res.accessToken, res.usuario);

    // Redirecionamento pós-login: só aceita caminho interno. Precisa começar
    // com uma "/" e a segunda posição não pode ser "/" nem "\" — "//evil.com"
    // e "/\evil.com" são lidos como URL externa por parte dos navegadores.
    const redirect = (route.query.redirect as string) || null;
    const interno = !!redirect && /^\/(?![/\\])/.test(redirect);
    if (redirect && interno && redirect !== "/login") {
      router.replace(redirect);
    } else {
      router.replace("/dashboard");
    }
  } catch (err: unknown) {
    const e = err as {
      response?: {
        data?: { errors?: Record<string, string[]>; erro?: string };
        status?: number;
      };
      message?: string;
    };
    if (e?.response?.status === 401) {
      errorMsg.value = "E-mail ou senha inválidos.";
    } else if (e?.response?.data?.erro) {
      errorMsg.value = e.response.data.erro;
    } else if (e?.response?.data?.errors) {
      const msgs = Object.values(e.response.data.errors).flat();
      errorMsg.value = msgs.join("; ");
    } else if (e?.message) {
      errorMsg.value = e.message;
    } else {
      errorMsg.value = "E-mail ou senha inválidos.";
    }
  } finally {
    loading.value = false;
  }
}
</script>

<style scoped>
.login-view {
  width: 100%;
}

.login-header {
  text-align: center;
  margin-bottom: 1.75rem;
}

.login-title {
  font-size: 22px;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0 0 0.25rem;
  letter-spacing: -0.02em;
}

.login-subtitle {
  font-size: 14px;
  color: var(--text-muted);
  margin: 0;
}

.login-form {
  display: flex;
  flex-direction: column;
  gap: 1.125rem;
}

.form-field {
  display: flex;
  flex-direction: column;
  gap: 0.375rem;
}

.form-field label {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-secondary);
}

.input-wrapper {
  position: relative;
  display: flex;
  align-items: center;
}

.input-icon {
  position: absolute;
  left: 12px;
  color: var(--text-muted);
  pointer-events: none;
}

.form-field input {
  width: 100%;
  height: 44px;
  padding: 0 2.5rem 0 2.5rem;
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  font-size: 14px;
  font-family: var(--font-family);
  background: var(--surface-page);
  color: var(--text-primary);
  outline: none;
  transition: all 150ms ease;
}

.form-field input:focus {
  border-color: var(--accent);
  box-shadow: 0 0 0 3px var(--accent-suave);
  background: var(--surface-card);
}

.form-field input:disabled {
  opacity: 0.5;
}

.toggle-pw {
  position: absolute;
  right: 8px;
  background: none;
  border: none;
  cursor: pointer;
  color: var(--text-muted);
  padding: 4px;
  border-radius: 4px;
  display: flex;
  align-items: center;
  transition: color 120ms;
}

.toggle-pw:hover {
  color: var(--text-secondary);
}

.login-error {
  font-size: 13px;
  color: var(--erro);
  margin: 0;
  display: flex;
  align-items: center;
  gap: 6px;
  background: var(--erro-suave);
  padding: 10px 12px;
  border-radius: var(--radius-sm);
}

.btn-login {
  height: 44px;
  background: var(--accent-gradient);
  color: var(--accent-gradient-texto);
  border: none;
  border-radius: var(--radius-md);
  font-size: 15px;
  font-weight: 600;
  font-family: var(--font-family);
  cursor: pointer;
  margin-top: 0.25rem;
  transition: all 150ms ease;
  box-shadow: 0 4px 12px rgba(var(--accent-rgb), 0.3);
  display: flex;
  align-items: center;
  justify-content: center;
}

.btn-login:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 6px 20px rgba(var(--accent-rgb), 0.4);
}

.btn-login:active:not(:disabled) {
  transform: translateY(0);
}

.btn-login:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.spinner {
  width: 20px;
  height: 20px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
</style>
