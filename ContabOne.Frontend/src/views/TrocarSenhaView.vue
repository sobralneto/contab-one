<template>
  <div class="troca-view">
    <div class="troca-header">
      <h2 class="troca-title">Defina uma nova senha</h2>
      <p class="troca-subtitle">
        Sua senha atual foi definida por um administrador. Escolha uma senha nova
        para continuar.
      </p>
    </div>

    <form class="troca-form" @submit.prevent="onSubmit">
      <div class="form-field">
        <label for="senha-atual">Senha atual</label>
        <input
          id="senha-atual"
          v-model="senhaAtual"
          type="password"
          autocomplete="current-password"
          :disabled="loading"
          required
        />
      </div>

      <div class="form-field">
        <label for="nova-senha">Nova senha</label>
        <input
          id="nova-senha"
          v-model="novaSenha"
          type="password"
          autocomplete="new-password"
          :disabled="loading"
          required
        />
        <MedidorSenha :senha="novaSenha" />
      </div>

      <div class="form-field">
        <label for="confirmacao">Confirme a nova senha</label>
        <input
          id="confirmacao"
          v-model="confirmacao"
          type="password"
          autocomplete="new-password"
          :disabled="loading"
          required
        />
        <span class="field-erro" v-if="confirmacao && !confere">As senhas não coincidem</span>
      </div>

      <p class="troca-erro" v-if="errorMsg">{{ errorMsg }}</p>

      <button type="submit" class="btn-troca" :disabled="loading || !podeEnviar">
        <span v-if="!loading">Salvar nova senha</span>
        <span v-else class="spinner"></span>
      </button>

      <button type="button" class="btn-sair" @click="onLogout" :disabled="loading">
        Sair
      </button>
    </form>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import MedidorSenha from '@/components/comum/MedidorSenha.vue'
import { useAuthStore } from '@/stores/auth'
import { useSenha } from '@/composables/useSenha'
import { trocarSenha, logout as apiLogout } from '@/api/endpoints/auth'

const router = useRouter()
const auth = useAuthStore()
const { avaliarForca } = useSenha()

const senhaAtual = ref('')
const novaSenha = ref('')
const confirmacao = ref('')
const loading = ref(false)
const errorMsg = ref('')

const confere = computed(() => novaSenha.value === confirmacao.value)
const podeEnviar = computed(
  () => senhaAtual.value.length > 0 && confere.value && avaliarForca(novaSenha.value).valida,
)

async function onSubmit() {
  errorMsg.value = ''
  loading.value = true
  try {
    const res = await trocarSenha({
      senhaAtual: senhaAtual.value,
      novaSenha: novaSenha.value,
    })
    // O token novo já vem sem a flag; setAccessToken a ressincroniza, o que
    // libera o guard para deixar a navegação sair desta tela.
    auth.setAccessToken(res.accessToken)
    router.replace('/')
  } catch (err: unknown) {
    const e = err as {
      response?: { data?: { errors?: Record<string, string[]>; erro?: string }; status?: number }
    }
    if (e?.response?.data?.errors) {
      errorMsg.value = Object.values(e.response.data.errors).flat().join('; ')
    } else if (e?.response?.data?.erro) {
      errorMsg.value = e.response.data.erro
    } else {
      errorMsg.value = 'Não foi possível trocar a senha. Confira a senha atual.'
    }
  } finally {
    loading.value = false
  }
}

async function onLogout() {
  try {
    await apiLogout()
  } catch {
    // Logout é best-effort — a sessão local é limpa de qualquer forma.
  }
  auth.clearSession()
  router.replace('/login')
}
</script>

<style scoped>
.troca-view { width: 100%; }

.troca-header { text-align: center; margin-bottom: 1.75rem; }

.troca-title {
  font-size: 22px; font-weight: 700; color: var(--text-primary);
  margin: 0 0 0.25rem; letter-spacing: -0.02em;
}

.troca-subtitle {
  font-size: 14px; color: var(--text-muted); margin: 0; line-height: 1.6;
}

.troca-form { display: flex; flex-direction: column; gap: 1.125rem; }

.form-field { display: flex; flex-direction: column; gap: 0.375rem; }

.form-field label { font-size: 13px; font-weight: 500; color: var(--text-secondary); }

.form-field input {
  width: 100%; height: 44px; padding: 0 0.875rem;
  border: 1px solid var(--border); border-radius: var(--radius-md);
  font-size: 14px; font-family: var(--font-family);
  background: var(--surface-page); color: var(--text-primary);
  outline: none; transition: all 150ms ease;
}

.form-field input:focus {
  border-color: var(--accent);
  box-shadow: 0 0 0 3px var(--accent-suave);
  background: var(--surface-card);
}

.form-field input:disabled { opacity: 0.5; }

.field-erro { font-size: 12px; color: var(--erro); }

.troca-erro {
  font-size: 13px; color: var(--erro); margin: 0;
  background: var(--erro-suave); padding: 10px 12px; border-radius: var(--radius-sm);
}

.btn-troca {
  height: 44px; background: var(--accent-gradient); color: var(--accent-gradient-texto);
  border: none; border-radius: var(--radius-md);
  font-size: 15px; font-weight: 600; font-family: var(--font-family);
  cursor: pointer; margin-top: 0.25rem; transition: all 150ms ease;
  box-shadow: 0 4px 12px rgba(var(--accent-rgb), 0.3);
  display: flex; align-items: center; justify-content: center;
}

.btn-troca:hover:not(:disabled) { transform: translateY(-1px); box-shadow: 0 6px 20px rgba(var(--accent-rgb), 0.4); }
.btn-troca:disabled { opacity: 0.6; cursor: not-allowed; }

.btn-sair {
  height: 38px; background: transparent; color: var(--text-muted);
  border: none; font-size: 13px; font-family: var(--font-family);
  cursor: pointer; transition: color 120ms;
}
.btn-sair:hover:not(:disabled) { color: var(--text-secondary); }

.spinner {
  width: 20px; height: 20px;
  border: 2px solid rgba(255, 255, 255, 0.3); border-top-color: #fff;
  border-radius: 50%; animation: spin 0.6s linear infinite;
}

@keyframes spin { to { transform: rotate(360deg); } }
</style>
