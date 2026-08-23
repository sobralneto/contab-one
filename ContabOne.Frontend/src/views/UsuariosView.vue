<template>
  <div class="usuarios-view">
    <div class="view-header">
      <h1>Usuários</h1>
      <button class="btn-primary" @click="abrirCriar">+ Novo usuário</button>
    </div>

    <div class="table-card">
      <table class="data-table" v-if="usuarios.length > 0">
        <thead>
          <tr>
            <th>Nome</th>
            <th>E-mail</th>
            <th>Papel</th>
            <th v-if="auth.isPlatformAdmin">Escritório</th>
            <th>Status</th>
            <th>Último login</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="u in usuarios" :key="u.id">
            <td class="col-nome">{{ u.nome }}</td>
            <td class="col-email">{{ u.email }}</td>
            <td>{{ papelLabel(u.papel) }}</td>
            <td v-if="auth.isPlatformAdmin">{{ u.escritorioNome || '—' }}</td>
            <td>
              <span class="status-chip" :class="u.ativo ? 'status-ok' : 'status-off'">
                {{ u.ativo ? 'Ativo' : 'Inativo' }}
              </span>
              <span class="chip-provisoria" v-if="u.deveTrocarSenha" title="O usuário precisa trocar a senha no próximo acesso">
                senha provisória
              </span>
            </td>
            <td class="col-login">{{ u.ultimoLoginEm ? formatDateTime(u.ultimoLoginEm) : 'nunca' }}</td>
            <td class="col-actions">
              <button class="btn-edit" @click="abrirEditar(u)" title="Editar">✎</button>
              <button class="btn-edit" @click="abrirResetar(u)" title="Redefinir senha">🔑</button>
              <button
                class="btn-edit"
                :class="{ 'btn-off': u.ativo }"
                @click="alternarAtivo(u)"
                :title="u.ativo ? 'Desativar' : 'Reativar'"
              >
                {{ u.ativo ? '⏻' : '↺' }}
              </button>
            </td>
          </tr>
        </tbody>
      </table>

      <div v-if="loading" class="loading-msg">Carregando...</div>
      <EstadoVazio
        v-else-if="usuarios.length === 0"
        title="Nenhum usuário cadastrado"
        description="Cadastre o primeiro usuário para dar acesso ao painel."
        action-label="+ Novo usuário"
        @action="abrirCriar"
      />
    </div>

    <!-- Modal: criar / editar -->
    <Teleport to="body">
      <div class="modal-overlay" v-if="modalAberto">
        <div class="modal-card">
          <h2 class="modal-title">{{ editando ? 'Editar usuário' : 'Novo usuário' }}</h2>

          <form @submit.prevent="salvar" class="modal-form" autocomplete="off">
            <div class="form-field">
              <label>Nome <span class="req">*</span></label>
              <input v-model="form.nome" required maxlength="200" />
            </div>

            <div class="form-field" v-if="!editando">
              <label>E-mail <span class="req">*</span></label>
              <input v-model="form.email" type="email" required autocomplete="off" />
            </div>

            <!--
              O campo é `type="text"` de propósito. Com um `type="password"` ao
              lado de um campo de e-mail, o navegador reconhece o modal como
              formulário de cadastro e oferece para salvar a credencial NO
              PERFIL DO ADMIN — que passava a ver o login do usuário recém-criado
              autocompletado na tela de login. `autocomplete="new-password"` só
              bloqueia o preenchimento, não a oferta de salvar.
              Esta senha também não é segredo do admin: ele precisa lê-la para
              entregar, e ela é exibida em texto logo depois da criação.
            -->
            <div class="form-field" v-if="!editando">
              <label>Senha provisória <span class="req">*</span></label>
              <div class="senha-linha">
                <input
                  v-model="form.senha"
                  type="text"
                  required
                  autocomplete="off"
                  name="senha-provisoria"
                  spellcheck="false"
                  class="campo-senha"
                />
                <button type="button" class="btn-secondary btn-mini" @click="form.senha = gerarSenha()">
                  Gerar
                </button>
              </div>
              <MedidorSenha :senha="form.senha" />
              <span class="field-hint">
                Visível para você conseguir entregá-la. O usuário troca no primeiro acesso.
              </span>
            </div>

            <div class="form-field">
              <label>Papel <span class="req">*</span></label>
              <select v-model="form.papel">
                <option v-for="p in papeisDisponiveis" :key="p" :value="p">
                  {{ PAPEL_USUARIO[p].label }}
                </option>
              </select>
              <span class="field-hint">{{ PAPEL_USUARIO[form.papel].descricao }}</span>
            </div>

            <div class="form-field" v-if="auth.isPlatformAdmin && form.papel !== 'PlatformAdmin'">
              <label>Escritório <span class="req">*</span></label>
              <select v-model="form.escritorioId">
                <option :value="null">—</option>
                <option v-for="e in escritorios" :key="e.id" :value="e.id">{{ e.nome }}</option>
              </select>
            </div>

            <p class="modal-erro" v-if="erroModal">{{ erroModal }}</p>

            <div class="modal-actions">
              <button type="button" class="btn-secondary" @click="fecharModal">Cancelar</button>
              <button type="submit" class="btn-primary" :disabled="salvando">
                {{ salvando ? 'Salvando...' : 'Salvar' }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </Teleport>

    <!-- Modal: redefinir senha -->
    <Teleport to="body">
      <div class="modal-overlay" v-if="modalResetAberto">
        <div class="modal-card">
          <h2 class="modal-title">Redefinir senha</h2>
          <p class="modal-sub">
            Nova senha para <strong>{{ usuarioAlvo?.nome }}</strong>. Ele precisará
            trocá-la no próximo acesso.
          </p>

          <form @submit.prevent="confirmarReset" class="modal-form" autocomplete="off">
            <!-- `type="text"` pelo mesmo motivo do modal de criação. -->
            <div class="form-field">
              <label>Nova senha provisória <span class="req">*</span></label>
              <div class="senha-linha">
                <input
                  v-model="novaSenha"
                  type="text"
                  required
                  autocomplete="off"
                  name="nova-senha-provisoria"
                  spellcheck="false"
                  class="campo-senha"
                />
                <button type="button" class="btn-secondary btn-mini" @click="novaSenha = gerarSenha()">
                  Gerar
                </button>
              </div>
              <MedidorSenha :senha="novaSenha" />
            </div>

            <p class="modal-erro" v-if="erroModal">{{ erroModal }}</p>

            <div class="modal-actions">
              <button type="button" class="btn-secondary" @click="modalResetAberto = false">Cancelar</button>
              <button type="submit" class="btn-primary" :disabled="salvando">
                {{ salvando ? 'Salvando...' : 'Redefinir' }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </Teleport>

    <!-- Modal: senha definida (exibida uma única vez) -->
    <Teleport to="body">
      <div class="modal-overlay" v-if="senhaEntregue">
        <div class="modal-card">
          <h2 class="modal-title">Senha definida</h2>
          <p class="modal-sub">
            Entregue esta senha a <strong>{{ senhaEntregue.nome }}</strong>. Ela não
            será exibida novamente — e será trocada por ele no primeiro acesso.
          </p>
          <div class="senha-entregue">
            <code>{{ senhaEntregue.senha }}</code>
            <button type="button" class="btn-secondary btn-mini" @click="copiar(senhaEntregue.senha)">
              {{ copiado ? 'Copiado' : 'Copiar' }}
            </button>
          </div>
          <div class="modal-actions">
            <button type="button" class="btn-primary" @click="senhaEntregue = null">Entendi</button>
          </div>
        </div>
      </div>
    </Teleport>

    <ConfirmarAcao
      :visible="confirmDesativar"
      title="Desativar usuário"
      :message="`Desativar ${usuarioAlvo?.nome}? Ele perde o acesso ao painel no próximo login.`"
      confirm-label="Desativar"
      @confirm="executarDesativar"
      @cancel="confirmDesativar = false"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import ConfirmarAcao from '@/components/comum/ConfirmarAcao.vue'
import EstadoVazio from '@/components/comum/EstadoVazio.vue'
import MedidorSenha from '@/components/comum/MedidorSenha.vue'
import { useAuthStore } from '@/stores/auth'
import { useFormatters } from '@/composables/useFormatters'
import { useSenha } from '@/composables/useSenha'
import { PAPEL_USUARIO } from '@/constants/papelUsuario'
import {
  listarUsuarios,
  criarUsuario,
  atualizarUsuario,
  resetarSenha,
  alterarAtivo,
} from '@/api/endpoints/usuarios'
import { listarEscritorios } from '@/api/endpoints/admin'
import type { UsuarioListaDto, EscritorioDto, Papel } from '@/api/types'

const auth = useAuthStore()
const { formatDateTime } = useFormatters()
const { gerarSenha } = useSenha()

const loading = ref(true)
const usuarios = ref<UsuarioListaDto[]>([])
const escritorios = ref<EscritorioDto[]>([])

const modalAberto = ref(false)
const modalResetAberto = ref(false)
const confirmDesativar = ref(false)
const editando = ref(false)
const salvando = ref(false)
const copiado = ref(false)
const erroModal = ref('')
const novaSenha = ref('')
const usuarioAlvo = ref<UsuarioListaDto | null>(null)
const senhaEntregue = ref<{ nome: string; senha: string } | null>(null)

const form = reactive({
  nome: '',
  email: '',
  senha: '',
  papel: 'EscritorioUsuario' as Papel,
  escritorioId: null as string | null,
})

// Só a plataforma concede o papel de plataforma — a API devolve 403 se um
// admin de escritório tentar, e esconder a opção evita o erro previsível.
const papeisDisponiveis = computed<Papel[]>(() =>
  auth.isPlatformAdmin
    ? ['PlatformAdmin', 'EscritorioAdmin', 'EscritorioUsuario']
    : ['EscritorioAdmin', 'EscritorioUsuario'],
)

function papelLabel(p: Papel): string {
  return PAPEL_USUARIO[p]?.label ?? p
}

async function carregar() {
  loading.value = true
  try {
    usuarios.value = await listarUsuarios()
    // A listagem de escritórios é rota de PlatformAdmin: pedi-la como admin de
    // escritório devolveria 403 e sujaria a tela com um erro inútil.
    if (auth.isPlatformAdmin) {
      escritorios.value = await listarEscritorios()
    }
  } catch {
    /* interceptor */
  } finally {
    loading.value = false
  }
}

function abrirCriar() {
  editando.value = false
  usuarioAlvo.value = null
  erroModal.value = ''
  form.nome = ''
  form.email = ''
  form.senha = ''
  form.papel = 'EscritorioUsuario'
  form.escritorioId = null
  modalAberto.value = true
}

function abrirEditar(u: UsuarioListaDto) {
  editando.value = true
  usuarioAlvo.value = u
  erroModal.value = ''
  form.nome = u.nome
  form.email = u.email
  form.senha = ''
  form.papel = u.papel
  form.escritorioId = u.escritorioId
  modalAberto.value = true
}

function abrirResetar(u: UsuarioListaDto) {
  usuarioAlvo.value = u
  novaSenha.value = ''
  erroModal.value = ''
  modalResetAberto.value = true
}

function fecharModal() {
  modalAberto.value = false
}

async function salvar() {
  erroModal.value = ''
  salvando.value = true
  try {
    if (editando.value && usuarioAlvo.value) {
      await atualizarUsuario(usuarioAlvo.value.id, {
        nome: form.nome,
        papel: form.papel,
        escritorioId: form.escritorioId ?? undefined,
      })
    } else {
      await criarUsuario({
        nome: form.nome,
        email: form.email,
        senha: form.senha,
        papel: form.papel,
        escritorioId: form.escritorioId ?? undefined,
      })
      senhaEntregue.value = { nome: form.nome, senha: form.senha }
    }
    modalAberto.value = false
    await carregar()
  } catch (err: unknown) {
    erroModal.value = mensagemDeErro(err)
  } finally {
    salvando.value = false
  }
}

async function confirmarReset() {
  if (!usuarioAlvo.value) return
  erroModal.value = ''
  salvando.value = true
  try {
    await resetarSenha(usuarioAlvo.value.id, { novaSenha: novaSenha.value })
    senhaEntregue.value = { nome: usuarioAlvo.value.nome, senha: novaSenha.value }
    modalResetAberto.value = false
    await carregar()
  } catch (err: unknown) {
    erroModal.value = mensagemDeErro(err)
  } finally {
    salvando.value = false
  }
}

async function alternarAtivo(u: UsuarioListaDto) {
  usuarioAlvo.value = u
  if (u.ativo) {
    confirmDesativar.value = true
    return
  }
  await aplicarAtivo(u, true)
}

async function executarDesativar() {
  confirmDesativar.value = false
  if (usuarioAlvo.value) await aplicarAtivo(usuarioAlvo.value, false)
}

async function aplicarAtivo(u: UsuarioListaDto, ativo: boolean) {
  try {
    await alterarAtivo(u.id, ativo)
    await carregar()
  } catch {
    /* interceptor */
  }
}

async function copiar(texto: string) {
  try {
    await navigator.clipboard.writeText(texto)
    copiado.value = true
    setTimeout(() => (copiado.value = false), 2000)
  } catch {
    // Sem permissão de clipboard: a senha continua visível para cópia manual.
  }
}

/** Achata o ValidationProblem da API na primeira mensagem legível. */
function mensagemDeErro(err: unknown): string {
  const e = err as {
    response?: { data?: { errors?: Record<string, string[]>; erro?: string }; status?: number }
  }
  if (e?.response?.data?.errors) {
    return Object.values(e.response.data.errors).flat().join('; ')
  }
  if (e?.response?.data?.erro) return e.response.data.erro
  if (e?.response?.status === 403) return 'Você não tem permissão para esta ação.'
  return 'Não foi possível concluir a operação.'
}

onMounted(carregar)
</script>

<style scoped>
.usuarios-view { max-width: 1200px; }

.view-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; }
.view-header h1 { margin: 0; }

.btn-primary {
  height: 38px; padding: 0 18px;
  background: var(--accent-gradient);
  color: var(--accent-gradient-texto); border: none; border-radius: var(--radius-md);
  font-size: 13px; font-weight: 600; font-family: var(--font-family);
  cursor: pointer; white-space: nowrap;
  display: inline-flex; align-items: center; gap: 6px;
  box-shadow: 0 2px 8px rgba(var(--accent-rgb), 0.25);
  transition: all 150ms ease;
}
.btn-primary:hover:not(:disabled) { transform: translateY(-1px); box-shadow: 0 4px 14px rgba(var(--accent-rgb), 0.35); }
.btn-primary:disabled { opacity: 0.5; cursor: not-allowed; transform: none; }

.table-card {
  background: var(--surface-card); border: 1px solid var(--border);
  border-radius: var(--radius-lg); overflow: hidden; box-shadow: var(--shadow-xs);
}
.data-table { width: 100%; border-collapse: collapse; font-size: 14px; }
.data-table th {
  text-align: left; font-weight: 600; font-size: 11px; text-transform: uppercase;
  letter-spacing: 0.04em; color: var(--text-muted); padding: 10px 14px;
  background: var(--surface-page); border-bottom: 1px solid var(--border);
}
.data-table td {
  padding: 10px 14px; border-bottom: 1px solid var(--border);
  color: var(--text-primary); vertical-align: middle;
}
.data-table tbody tr { transition: background-color 120ms; }
.data-table tbody tr:hover { background: var(--surface-page); }
.data-table tbody tr:last-child td { border-bottom: none; }
.col-nome { font-weight: 500; }
.col-email, .col-login { font-size: 13px; color: var(--text-secondary); }
.col-actions { text-align: right; white-space: nowrap; }

.status-chip { display: inline-block; font-size: 11px; font-weight: 600; padding: 3px 10px; border-radius: 12px; letter-spacing: 0.02em; }
.status-ok { background: var(--sucesso-suave); color: var(--sucesso); }
.status-off { background: var(--border); color: var(--text-muted); }
.chip-provisoria {
  display: inline-block; margin-left: 6px; font-size: 10px; font-weight: 600;
  padding: 2px 8px; border-radius: 10px;
  background: var(--atencao-suave); color: var(--atencao);
}

.btn-edit {
  background: none; border: 1px solid var(--border); cursor: pointer;
  padding: 6px 8px; border-radius: 6px; color: var(--text-muted);
  display: inline-flex; align-items: center; transition: all 120ms; margin-left: 4px;
}
.btn-edit:hover { color: var(--accent); border-color: var(--accent); background: var(--accent-suave); }
.btn-off:hover { color: var(--erro); border-color: var(--erro); background: var(--erro-suave); }

.loading-msg { padding: 32px; text-align: center; color: var(--text-muted); font-size: 14px; }

/* Modal */
.modal-overlay {
  position: fixed; inset: 0;
  background: rgba(0,0,0,0.4); backdrop-filter: blur(4px);
  display: flex; align-items: center; justify-content: center; z-index: 1000;
}
.modal-card {
  background: var(--surface-card); border: 1px solid var(--border);
  border-radius: var(--radius-lg); padding: 28px;
  max-width: 520px; width: 90%; box-shadow: var(--shadow-lg);
}
.modal-title { font-size: 18px; font-weight: 700; margin: 0 0 8px; letter-spacing: -0.01em; }
.modal-sub { font-size: 13px; color: var(--text-secondary); margin: 0 0 18px; line-height: 1.6; }
.modal-form { display: flex; flex-direction: column; gap: 14px; }
.form-field { display: flex; flex-direction: column; gap: 4px; }
.form-field label { font-size: 13px; font-weight: 500; color: var(--text-secondary); }
.form-field input, .form-field select {
  height: 40px; padding: 0 12px; border: 1px solid var(--border); border-radius: var(--radius-sm);
  font-size: 14px; font-family: var(--font-family);
  background: var(--surface-page); color: var(--text-primary); outline: none;
  transition: border-color 150ms, box-shadow 150ms;
}
.form-field input:focus, .form-field select:focus { border-color: var(--accent); box-shadow: 0 0 0 3px var(--accent-suave); }
.req { color: var(--erro); }
.field-hint { font-size: 12px; color: var(--text-muted); }

.senha-linha { display: flex; gap: 6px; align-items: center; }
.senha-linha input { flex: 1; min-width: 0; }
.campo-senha { font-family: ui-monospace, monospace; letter-spacing: 0.04em; }
.btn-mini { height: 40px; padding: 0 12px; font-size: 12px; white-space: nowrap; }

.senha-entregue {
  display: flex; align-items: center; gap: 8px;
  background: var(--surface-page); border: 1px dashed var(--border);
  border-radius: var(--radius-sm); padding: 12px; margin-bottom: 18px;
}
.senha-entregue code {
  flex: 1; font-family: ui-monospace, monospace; font-size: 15px;
  letter-spacing: 0.06em; color: var(--text-primary); word-break: break-all;
}

.modal-erro {
  font-size: 13px; color: var(--erro); margin: 0;
  background: var(--erro-suave); padding: 10px 12px; border-radius: var(--radius-sm);
}
.modal-actions { display: flex; justify-content: flex-end; gap: 8px; margin-top: 8px; }
.btn-secondary {
  height: 38px; padding: 0 16px;
  background: transparent; color: var(--text-secondary);
  border: 1px solid var(--border); border-radius: var(--radius-sm);
  font-size: 13px; font-family: var(--font-family); cursor: pointer;
  transition: all 120ms;
}
.btn-secondary:hover { background: var(--surface-page); }
</style>
