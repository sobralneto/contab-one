<template>
  <div class="hub animate-fade-in">
    <div v-if="!catalogo.carregado && catalogo.carregando" class="loading-msg">
      Carregando...
    </div>

    <div v-else-if="catalogo.falhou" class="erro-carga">
      <p>Não foi possível carregar suas ferramentas.</p>
      <button class="btn-secondary" @click="catalogo.carregar()">Tentar novamente</button>
    </div>

    <EstadoVazio
      v-else-if="catalogo.carregado && catalogo.produtos.length === 0"
      title="Nenhuma ferramenta disponível"
      description="Fale com a Contab One para contratar uma ferramenta para o seu escritório."
    />

    <template v-else>
      <section v-for="grupo in catalogo.porDominio" :key="grupo.dominio.codigo" class="dominio-secao">
        <h2 class="dominio-titulo">{{ grupo.dominio.nome }}</h2>

        <div class="cards-grid">
          <template v-for="produto in grupo.produtos" :key="produto.id">
            <RouterLink
              v-if="produto.contratado || auth.isPlatformAdmin"
              :to="`/f/${produto.codigo}`"
              class="ferramenta-card"
            >
              <div class="ferramenta-icone">
                <IconeCatalogo :nome="grupo.dominio.icone" />
              </div>
              <div class="ferramenta-corpo">
                <div class="ferramenta-nome">{{ produto.nome }}</div>
                <p class="ferramenta-desc">{{ produto.descricao || '—' }}</p>

                <div v-if="produto.codigo === 'nfse' && kpisNfse" class="ferramenta-stats">
                  <div class="stat">
                    <span class="stat-valor">{{ kpisNfse.notasBaixadasMes.toLocaleString('pt-BR') }}</span>
                    <span class="stat-label">notas no mês</span>
                  </div>
                  <div class="stat">
                    <span class="stat-valor">{{ kpisNfse.totalClientes.toLocaleString('pt-BR') }}</span>
                    <span class="stat-label">clientes</span>
                  </div>
                </div>

                <!-- Admin entra em qualquer ferramenta ativa, mas o rótulo
                     ainda diz que ESTE escritório em foco não contratou —
                     informação, não bloqueio. -->
                <span v-if="!produto.contratado" class="pill-indisponivel">Não contratada</span>
              </div>
            </RouterLink>

            <!-- Ferramenta ativa, não contratada: só informativo — nenhum
                 atalho, nenhum link, nenhum contato comercial (design.md). -->
            <div v-else class="ferramenta-card ferramenta-card--indisponivel">
              <div class="ferramenta-icone ferramenta-icone--indisponivel">
                <IconeCatalogo :nome="grupo.dominio.icone" />
              </div>
              <div class="ferramenta-corpo">
                <div class="ferramenta-nome">{{ produto.nome }}</div>
                <p class="ferramenta-desc">{{ produto.descricao || '—' }}</p>
                <span class="pill-indisponivel">Não contratada</span>
              </div>
            </div>
          </template>
        </div>
      </section>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import EstadoVazio from '@/components/comum/EstadoVazio.vue'
import IconeCatalogo from '@/components/comum/IconeCatalogo.vue'
import { useCatalogoStore } from '@/stores/catalogo'
import { useAuthStore } from '@/stores/auth'
import { fetchKpis } from '@/api/endpoints/dashboard'
import type { DashboardKpis } from '@/api/types'

const catalogo = useCatalogoStore()
const auth = useAuthStore()

// Número no card só para a ferramenta cujo resumo a API já sabe escopar —
// hoje só o NFS-e. As demais mostram card sem número, não um número errado.
const kpisNfse = ref<DashboardKpis | null>(null)

onMounted(async () => {
  try {
    kpisNfse.value = await fetchKpis()
  } catch {
    // Card do NFS-e some os números; o resto da tela continua de pé.
  }
})
</script>

<style scoped>
.hub {
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.dominio-secao {
  display: flex;
  flex-direction: column;
  gap: 0.875rem;
}

.dominio-titulo {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
  letter-spacing: -0.01em;
}

.cards-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 14px;
}

.ferramenta-card {
  display: flex;
  gap: 14px;
  background: var(--surface-card);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: 18px;
  text-decoration: none;
  color: inherit;
  box-shadow: var(--shadow-xs);
  transition: all 180ms ease;
}

a.ferramenta-card:hover {
  box-shadow: var(--shadow-md);
  transform: translateY(-2px);
  border-color: var(--border-forte);
}

.ferramenta-card--indisponivel {
  opacity: 0.65;
}

.ferramenta-icone {
  flex-shrink: 0;
  width: 40px;
  height: 40px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--accent);
  background: var(--accent-suave);
}

.ferramenta-icone--indisponivel {
  color: var(--text-muted);
  background: var(--surface-page);
}

.ferramenta-corpo {
  min-width: 0;
  flex: 1;
}

.ferramenta-nome {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 2px;
}

.ferramenta-desc {
  font-size: 12.5px;
  color: var(--text-secondary);
  line-height: 1.5;
  margin: 0 0 10px;
}

.ferramenta-stats {
  display: flex;
  gap: 18px;
}

.stat {
  display: flex;
  flex-direction: column;
}

.stat-valor {
  font-size: 16px;
  font-weight: 700;
  color: var(--text-primary);
  font-variant-numeric: tabular-nums;
}

.stat-label {
  font-size: 11px;
  color: var(--text-muted);
}

.pill-indisponivel {
  display: inline-block;
  font-size: 11px;
  font-weight: 600;
  color: var(--text-muted);
  background: var(--surface-page);
  padding: 2px 8px;
  border-radius: 10px;
}

.loading-msg {
  padding: 32px;
  text-align: center;
  color: var(--text-muted);
  font-size: 14px;
}

.erro-carga {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 48px 16px;
  text-align: center;
  color: var(--text-secondary);
}

.btn-secondary {
  height: 38px;
  padding: 0 16px;
  background: transparent;
  color: var(--text-secondary);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  font-size: 13px;
  font-family: var(--font-family);
  cursor: pointer;
  transition: all 120ms ease;
}

.btn-secondary:hover {
  background: var(--surface-page);
}
</style>
