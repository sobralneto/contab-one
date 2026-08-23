<template>
  <div class="config-view animate-fade-in">
    <div class="view-header">
      <h1>Configuração</h1>
    </div>

    <!-- Plan limits -->
    <div class="plano-card" v-if="plano">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/>
      </svg>
      <span>
        Plano: <strong>{{ plano.maxClientes }}</strong> clientes · <strong>{{ plano.maxAgentes }}</strong> agentes · Emitidas: <strong>{{ plano.permiteEmitidas ? 'Sim' : 'Não' }}</strong>
      </span>
    </div>

    <!-- Admin: seleciona o escritório cuja configuração será editada -->
    <div class="escritorio-select" v-if="auth.isPlatformAdmin">
      <label>Escritório</label>
      <select v-model="escritorioId" @change="carregar()">
        <option :value="null" disabled>Selecione o escritório</option>
        <option v-for="e in escritorios" :key="e.id" :value="e.id">{{ e.nome }}</option>
      </select>
    </div>

    <div class="config-aviso">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
      <span>As alterações abaixo valem a partir da <strong>próxima execução do agente</strong>:
      ele recebe estas configurações no handshake e as aplica por cima do config.toml local.
      O limite do plano (<strong>Emitidas</strong>) prevalece sobre o que estiver salvo aqui,
      e valores inválidos são ignorados pelo agente, mantendo os do arquivo local.</span>
    </div>

    <div class="erro-box" v-if="erro">✗ {{ erro }}</div>

    <div class="config-card" v-if="!loading && (escritorioId || !auth.isPlatformAdmin)">
      <form @submit.prevent="salvar" class="config-form">
        <div class="form-field">
          <label>Tipos de nota</label>
          <div class="checkbox-group">
            <label class="checkbox-label">
              <input type="checkbox" v-model="form.recebidas" />
              <span class="checkbox-custom"></span>
              Recebidas
            </label>
            <label class="checkbox-label" :class="{ 'checkbox-disabled': !plano?.permiteEmitidas }">
              <input
                type="checkbox"
                v-model="form.emitidas"
                :disabled="!plano?.permiteEmitidas"
              />
              <span class="checkbox-custom"></span>
              Emitidas
              <span v-if="!plano?.permiteEmitidas" class="field-hint" style="color: var(--text-muted)">
                (não incluso no plano)
              </span>
            </label>
          </div>
        </div>

        <div class="form-field">
          <label>Primeira busca desde</label>
          <input type="date" v-model="form.primeira_busca_desde" />
          <span class="field-hint">Data inicial para o backfill de clientes novos.</span>
        </div>

        <div class="form-field">
          <label>Pasta de saída sugerida</label>
          <input type="text" v-model="form.pasta_saida" placeholder="notas" />
          <span class="field-hint">Caminho relativo à pasta do agente.</span>
        </div>

        <div class="form-field">
          <label>Período padrão de busca (dias)</label>
          <input type="number" min="1" step="1" v-model.number="form.dias_busca_padrao" />
          <span class="field-hint">
            Quando o agente roda sem período explícito, ele busca esses últimos dias a partir de
            hoje. Pode passar de 31 dias — o agente já quebra a consulta em janelas menores.
          </span>
        </div>

        <div class="form-field">
          <label class="checkbox-label">
            <input type="checkbox" v-model="form.gerar_pdf" />
            <span class="checkbox-custom"></span>
            Gerar DANFSe em PDF
          </label>
        </div>

        <div class="form-actions">
          <button type="submit" class="btn-primary" :disabled="salvando">
            {{ salvando ? 'Salvando...' : 'Salvar configuração' }}
          </button>
          <span class="save-msg" v-if="salvo">✓ Salvo com sucesso</span>
          <span class="erro-msg" v-if="erroSalvar">✗ {{ erroSalvar }}</span>
        </div>
      </form>
    </div>

    <div v-else-if="loading" class="loading-msg">Carregando...</div>
    <div v-else-if="auth.isPlatformAdmin && !escritorioId" class="loading-msg">
      Selecione um escritório acima para editar sua configuração.
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { obterConfiguracao, salvarConfiguracao } from '@/api/endpoints/configuracao'
import { listarEscritorios } from '@/api/endpoints/admin'
import type { PlanoLimites, EscritorioDto } from '@/api/types'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()

const loading = ref(true)
const salvando = ref(false)
const salvo = ref(false)
const erro = ref('')
const erroSalvar = ref('')
const plano = ref<PlanoLimites | null>(null)
const escritorios = ref<EscritorioDto[]>([])
const escritorioId = ref<string | null>(null)

const form = reactive({
  recebidas: true,
  emitidas: false,
  primeira_busca_desde: '2026-01-01',
  pasta_saida: 'notas',
  gerar_pdf: true,
  dias_busca_padrao: 31,
})

async function carregar() {
  loading.value = true
  erro.value = ''
  try {
    const cfg = await obterConfiguracao(escritorioId.value ?? undefined)
    plano.value = cfg.plano
    const valores = cfg.valores
    if (valores.tipos) {
      form.recebidas = valores.tipos.includes('recebidas')
      form.emitidas = valores.tipos.includes('emitidas')
    }
    if (valores.primeira_busca_desde) form.primeira_busca_desde = valores.primeira_busca_desde
    if (valores.pasta_saida) form.pasta_saida = valores.pasta_saida
    if (valores.gerar_pdf !== undefined) form.gerar_pdf = valores.gerar_pdf === 'true'
    if (valores.dias_busca_padrao) {
      const n = parseInt(valores.dias_busca_padrao, 10)
      if (Number.isFinite(n) && n > 0) form.dias_busca_padrao = n
    }
  } catch (e: any) {
    erro.value = e?.response?.data?.erro || 'Não foi possível carregar a configuração.'
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  if (auth.isPlatformAdmin) {
    try {
      escritorios.value = await listarEscritorios()
    } catch { /* interceptor handles */ }
  }
  if (!auth.isPlatformAdmin) {
    await carregar()
  } else {
    loading.value = false
  }
})

async function salvar() {
  salvando.value = true
  salvo.value = false
  erroSalvar.value = ''
  try {
    const tipos: string[] = []
    if (form.recebidas) tipos.push('recebidas')
    if (form.emitidas && plano.value?.permiteEmitidas) tipos.push('emitidas')

    const diasBuscaPadrao =
      Number.isFinite(form.dias_busca_padrao) && form.dias_busca_padrao > 0
        ? Math.trunc(form.dias_busca_padrao)
        : 31

    await salvarConfiguracao(
      {
        tipos: tipos.join(','),
        primeira_busca_desde: form.primeira_busca_desde,
        pasta_saida: form.pasta_saida,
        gerar_pdf: form.gerar_pdf ? 'true' : 'false',
        dias_busca_padrao: String(diasBuscaPadrao),
      },
      escritorioId.value ?? undefined,
    )
    salvo.value = true
    setTimeout(() => (salvo.value = false), 3000)
  } catch (e: any) {
    erroSalvar.value = e?.response?.data?.erro || 'Não foi possível salvar a configuração.'
  } finally {
    salvando.value = false
  }
}
</script>

<style scoped>
.config-view { max-width: 680px; }

.view-header { margin-bottom: 16px; }
.view-header h1 { margin: 0; }

.escritorio-select {
  display: flex; align-items: center; gap: 10px;
  margin-bottom: 16px;
}
.escritorio-select label { font-size: 13px; font-weight: 500; color: var(--text-secondary); }
.escritorio-select select {
  height: 38px; padding: 0 12px;
  border: 1px solid var(--border); border-radius: var(--radius-sm);
  font-size: 13px; font-family: var(--font-family);
  background: var(--surface-card); color: var(--text-primary); outline: none;
  transition: border-color 150ms, box-shadow 150ms;
}
.escritorio-select select:focus { border-color: var(--accent); box-shadow: 0 0 0 3px var(--accent-suave); }

.erro-box {
  font-size: 13px; color: var(--erro); background: var(--erro-suave);
  border: 1px solid var(--erro); border-radius: var(--radius-sm);
  padding: 12px 14px; margin-bottom: 16px; line-height: 1.6;
}
.erro-msg { font-size: 13px; color: var(--erro); font-weight: 600; }

.plano-card {
  display: flex; align-items: center; gap: 10px;
  font-size: 13px; color: var(--text-secondary);
  background: var(--surface-card); border: 1px solid var(--border);
  border-radius: var(--radius-md); padding: 12px 16px; margin-bottom: 16px;
  box-shadow: var(--shadow-xs);
}
.plano-card svg { color: var(--accent); flex-shrink: 0; }
.plano-card strong { color: var(--text-primary); }

.config-aviso {
  font-size: 13px; color: var(--atencao); background: var(--atencao-suave);
  border: 1px solid var(--atencao); border-radius: var(--radius-sm);
  padding: 12px 14px; margin-bottom: 20px; line-height: 1.6;
  display: flex; align-items: flex-start; gap: 8px;
}
.config-aviso svg { flex-shrink: 0; margin-top: 1px; }

.config-card {
  background: var(--surface-card); border: 1px solid var(--border);
  border-radius: var(--radius-lg); padding: 28px;
  box-shadow: var(--shadow-xs);
}

.config-form { display: flex; flex-direction: column; gap: 18px; }

.form-field { display: flex; flex-direction: column; gap: 6px; }
.form-field label { font-size: 13px; font-weight: 500; color: var(--text-secondary); }
.form-field input[type="text"],
.form-field input[type="date"] {
  height: 40px; padding: 0 12px;
  border: 1px solid var(--border); border-radius: var(--radius-sm);
  font-size: 14px; font-family: var(--font-family);
  background: var(--surface-page); color: var(--text-primary); outline: none;
  transition: border-color 150ms, box-shadow 150ms;
}
.form-field input:focus { border-color: var(--accent); box-shadow: 0 0 0 3px var(--accent-suave); }

.checkbox-group { display: flex; gap: 24px; align-items: center; flex-wrap: wrap; }
.checkbox-label {
  display: flex; align-items: center; gap: 8px;
  font-size: 14px; color: var(--text-primary); cursor: pointer;
}
.checkbox-label input[type="checkbox"] {
  width: 18px; height: 18px; accent-color: var(--accent); cursor: pointer;
}
.checkbox-disabled { opacity: 0.5; cursor: not-allowed; }

.field-hint { font-size: 12px; color: var(--text-muted); }

.form-actions { display: flex; align-items: center; gap: 14px; margin-top: 4px; }
.btn-primary {
  height: 40px; padding: 0 22px;
  background: var(--accent-gradient);
  color: var(--accent-gradient-texto); border: none; border-radius: var(--radius-sm);
  font-size: 14px; font-weight: 600; font-family: var(--font-family); cursor: pointer;
  box-shadow: 0 2px 8px rgba(var(--accent-rgb), 0.25);
  transition: all 150ms ease;
}
.btn-primary:hover:not(:disabled) { transform: translateY(-1px); box-shadow: 0 4px 14px rgba(var(--accent-rgb), 0.35); }
.btn-primary:disabled { opacity: 0.5; cursor: not-allowed; transform: none; }

.save-msg { font-size: 13px; color: var(--sucesso); font-weight: 600; }
.loading-msg { padding: 32px; text-align: center; color: var(--text-muted); font-size: 14px; }
</style>
