# Plano — Dashboard web de relatório

> ## ⚠️ Documento histórico — recurso removido
>
> Este plano foi implementado (`dashboard.py` + `dashboard.html`, gerando
> `_dashboard.json`/`_dashboard.data.js` dentro de `notas/`) e depois
> **removido em 09/08/2026**. O painel do escritório é o frontend web do
> SaaS (`../ContabOne.Frontend/`), alimentado pelas métricas que o agente já reporta;
> manter uma segunda implementação do mesmo relatório — com nome e CNPJ
> completo dos clientes em texto claro no disco — não se justificava.
>
> Leia daqui para baixo só como registro de decisões de design. **Não é
> uma lista de tarefas**, e nenhum arquivo citado abaixo existe mais no
> projeto. Ver "Decisões que valem lembrar" no [HANDOFF.md](HANDOFF.md).

Status original do documento: **plano, nada implementado ainda**. Este
documento existe para uma sessão futura (com Claude ou não) executar sem
precisar redescobrir as decisões de design. Se algo aqui parecer errado
depois de ler o código atual, o código manda — este plano pode estar
desatualizado.

Pré-requisito de contexto: leia [HANDOFF.md](HANDOFF.md) primeiro. Este
plano assume que você já sabe como `nfse.py`, `_controle.json` e a estrutura
de pastas em `notas/` funcionam.

## Objetivo

Uma página web que mostra, a partir dos dados já salvos pela ferramenta:

1. Quantidade de certificados presentes (na pasta configurada).
2. Clientes com mais notas baixadas (ranking).
3. Quantidade de notas baixadas por mês, por cliente.

Sem backend, sem instalação, sem depender de internet — mesma filosofia de
fricção zero do `nfse.exe`.

## Fonte de dados: `_dashboard.json`

### Por que não usar `_controle.json` diretamente

Cada cliente já tem um `_controle.json` (ver HANDOFF.md), mas ele:
- é por cliente, não dá visão agregada sem ler todos e cruzar;
- guarda uma lista achatada de chaves por tipo, não uma contagem por mês;
- não sabe quantos certificados existem na pasta de certificados (isso é
  informação de configuração, não de execução).

Por isso, um arquivo agregado novo, calculado a partir do que existe em
disco — não um contador incremental mantido à parte, que poderia dessincronizar
se alguém mover/arquivar uma pasta de mês manualmente. Mesmo princípio já
usado em `baixar_xml`: disco é fonte de verdade.

### Onde e quando é gerado

- Caminho: `{pasta_saida}/_dashboard.json` (raiz de `notas/`, um nível acima
  das pastas de cliente — é dado agregado de todos os clientes, não de um só).
- Gerado no fim de `main()`, em **toda execução**, independente de
  `--somente-lista`, `--empresa` ou `--tipos`. A geração é uma varredura
  completa da pasta de saída, então sempre reflete a realidade atual do
  disco — não só o que essa execução específica processou. Rodar
  `--empresa 0001` atualiza o dashboard com dados de **todos** os clientes,
  não só do 0001.
- Custo: uma varredura de `notas/` contando arquivos `.xml` por pasta de mês.
  Para a escala de um escritório de contabilidade (dezenas de clientes,
  milhares de notas), isso é da ordem de segundos, não minutos.

### Esquema proposto

```json
{
  "gerado_em": "2026-07-21T23:47:19-03:00",
  "certificados": {
    "total": 2,
    "vencidos": 0,
    "lista": [
      {
        "codigo": "0001",
        "nome": "SOLUTION FARMA CONTABILIDADE LTDA",
        "cnpj": "54.283.546/0001-26",
        "validade": "2027-03-04",
        "vencido": false
      }
    ]
  },
  "clientes": [
    {
      "codigo": "0001",
      "nome": "SOLUTION FARMA CONTABILIDADE LTDA",
      "pasta": "0001_SOLUTION FARMA CONTABILIDADE LTDA",
      "total_notas": 373,
      "total_recebidas": 75,
      "total_emitidas": 298,
      "backfill_concluido": {"recebidas": true, "emitidas": true},
      "por_mes": {
        "2026-01": {"recebidas": 11, "emitidas": 43},
        "2026-02": {"recebidas": 11, "emitidas": 4},
        "2026-03": {"recebidas": 12, "emitidas": 94},
        "2026-04": {"recebidas": 13, "emitidas": 47},
        "2026-05": {"recebidas": 14, "emitidas": 57},
        "2026-06": {"recebidas": 14, "emitidas": 53}
      }
    }
  ]
}
```

Campos `backfill_concluido` e `vencido` não foram pedidos explicitamente,
mas custam quase nada (os dados já existem em `_controle.json` e no nome do
certificado) e têm valor óbvio num dashboard operacional: sinalizar
certificado vencido ou cliente com histórico incompleto. Tratar como
extensão de baixo custo, não como escopo adicional que precisa de aprovação
separada.

**Fora de escopo deste esquema** (mencionar só para deixar explícito que foi
uma escolha, não um esquecimento): soma de valores em R$ por cliente/mês. O
CSV já tem `preco_servico`, então é uma extensão barata depois — mas não é
uma das três métricas pedidas, então não faz parte da primeira versão.

### Onde essa função vive no código

Sugestão: novo arquivo `dashboard.py` (mesmo padrão de `danfse.py` — módulo
separado, importável isolado), com uma função pura:

```python
def gerar_dados(pasta_saida: Path, certificados: list[Empresa]) -> dict:
    ...

def salvar_dashboard(pasta_saida: Path, dados: dict) -> None:
    ...
```

`gerar_dados` não deve precisar de rede nem do `config` inteiro — só do
caminho de saída e da lista de certificados já carregada (`listar_empresas`,
que `main()` já chama). Isso facilita testar sem mockar HTTP: monta uma
estrutura de pastas fake com alguns `.xml` e confere a contagem.

## A página: `dashboard.html`

### O problema a resolver antes de escrever qualquer HTML

A forma óbvia — `fetch('./_dashboard.json')` de dentro de `dashboard.html`
aberto por duplo clique (`file://...`) — **não funciona no Chrome/Edge**:
navegadores bloqueiam `fetch`/XHR de arquivos locais por CORS. Isso quebraria
a experiência de "duplo clique e pronto" que o resto do projeto preserva.

**Decisão recomendada:** gerar dois arquivos a partir dos mesmos dados:

- `_dashboard.json` — o dado canônico, formato pedido, inspecionável em
  qualquer editor ou reaproveitável por outra ferramenta (Excel Power
  Query, por exemplo) no futuro.
- `_dashboard.data.js` — o mesmo conteúdo, envolvido em
  `window.DASHBOARD_DATA = {...};`, carregado via
  `<script src="_dashboard.data.js"></script>` normal. Carregar um `<script
  src>` local funciona sem servidor nem CORS, ao contrário de `fetch`. É o
  mesmo dado, só embrulhado de um jeito que o navegador aceita ler sem
  servidor.

Alternativa considerada e não recomendada como padrão: um pequeno servidor
HTTP local (`python -m http.server` ou equivalente embutido, atrás de um
flag `nfse.exe --dashboard` que abre o navegador sozinho). Funciona e evita
o problema de CORS de outra forma, mas adiciona um processo rodando e uma
porta — mais fricção que o necessário para o caso comum. Vale como
possível adição futura (seção "Fora do MVP"), não como a solução inicial.

### Onde os arquivos ficam

Tudo dentro de `pasta_saida` (ou seja, dentro de `notas/`, ao lado das
pastas de cliente), para que onde quer que o usuário aponte `pasta_saida`
no config (pode ser em outro disco), o relatório vá junto:

```
notas/
├── dashboard.html          gerado/copiado a cada execução (sempre sobrescrito)
├── _dashboard.json         dado agregado, gerado a cada execução
├── _dashboard.data.js      mesmo dado, formato consumível pela pagina
├── 0001_SOLUTION FARMA.../
│   ├── _controle.json
│   └── ...
└── ...
```

`dashboard.html` é estático (não muda entre versões dos dados) e pode ser
**sempre sobrescrito** a partir de um molde embutido no `.exe` — isso faz
uma atualização futura do layout se propagar sozinha, sem o usuário precisar
substituir manualmente um arquivo antigo. Segue o mesmo padrão já usado para
`logo_nfse.png`/`municipios_ibge.json` embutidos via PyInstaller
(`sys._MEIPASS`).

Instrução para o usuário (a documentar no README/LEIA-ME): "abra
`notas/dashboard.html` no navegador".

### Estrutura de conteúdo da página

Sem framework, sem CDN, HTML+CSS+JS num arquivo só (ou dois: o `.html` e o
`.data.js` irmão) — nada de build step. Coerente com o resto do projeto:
zero dependência para o usuário final.

Seções sugeridas, na ordem:

1. **Cabeçalho** — título e "atualizado em `{gerado_em}`" (formatado em
   pt-BR, não ISO cru).
2. **Cartões de resumo (KPIs)** — total de certificados (com destaque se
   algum vencido), total de clientes com dado, total de notas baixadas
   (soma geral recebidas+emitidas).
3. **Ranking de clientes** — tabela ou gráfico de barras horizontal,
   ordenado por `total_notas` decrescente. Mostrar recebidas e emitidas
   separadas (barra empilhada ou duas colunas), não só o total, porque a
   composição importa tanto quanto o total.
4. **Detalhe mensal por cliente** — um seletor (dropdown) de cliente +
   gráfico de barras (eixo X = ano-mês, duas séries: recebidas/emitidas).
   Evitar tentar mostrar todos os clientes no mesmo gráfico mensal de uma
   vez — com múltiplos clientes isso vira ilegível rápido; um seletor
   resolve sem complicar.
5. **Alertas** — lista curta: certificados vencidos, clientes com
   `backfill_concluido` ainda `false` para alguma listagem (histórico
   incompleto).

Ao implementar os gráficos, seguir a skill `dataviz` já disponível no
projeto (paleta, espaçamento, texto de eixo/legenda) em vez de inventar
estilo do zero — ela já resolve as decisões de cor/contraste/tema
claro-escuro que este plano não precisa repetir.

A página deve funcionar em tema claro e escuro (`prefers-color-scheme`),
por ser aberta em navegadores/configurações variadas sem controle sobre
qual tema o usuário usa.

## Fases de implementação

**Fase 1 — Agregação (backend, Python).**
`dashboard.py` com `gerar_dados()` + `salvar_dashboard()`. Chamado ao fim de
`main()` em `nfse.py`. Testável sem rede: monta pastas fake com alguns
`.xml`, confere a contagem por mês/tipo/cliente bate.

**Fase 2 — Página estática (frontend).**
`dashboard.html` autocontido, consumindo `_dashboard.data.js`. Construir e
testar abrindo o arquivo direto no navegador (duplo clique), não com
servidor — é exatamente o cenário real de uso.

**Fase 3 — Empacotamento.**
`build.py` copia `dashboard.html` para dentro de `dist/nfse/` (o molde) e
`nfse.py` garante que uma cópia dele exista (e seja atualizada) dentro de
`pasta_saida` a cada execução — mesmo mecanismo de recurso embutido via
`sys._MEIPASS` já usado para `logo_nfse.png`. Atualizar `README.md` e o
`LEIA-ME.txt` do pacote.

**Fora do MVP (mencionar, não implementar agora):**
- Flag `--dashboard` que abre o navegador automaticamente
  (`webbrowser.open()`) ao fim da execução.
- Servidor HTTP local opcional, só se o double-click com `.data.js` se
  mostrar insuficiente na prática (não deveria).
- Soma de valores em R$ (o CSV já tem o dado; é extensão barata depois).
- Exportar o relatório como imagem/PDF a partir da própria página.

## Perguntas para resolver quando a implementação começar

Não são bloqueios para começar a Fase 1, mas valem confirmar com o usuário
antes ou durante a Fase 2:

- Ranking de clientes: mostrar todos ou só um top N (ex.: top 10 + "outros")
  quando houver muitos clientes?
- Vale ordenar/filtrar o ranking por período (ex.: "últimos 3 meses") em vez
  de sempre o acumulado desde `primeira_busca_desde`?
- O dashboard deve refletir só clientes com pelo menos uma pasta de dados,
  ou também listar certificados presentes que ainda nunca rodaram (0 notas)?
  (Recomendação: incluir também — é informação útil, "este certificado está
  aqui mas nunca foi processado" é um alerta por si só.)

## Testes previstos

Seguindo o padrão já estabelecido no projeto (suítes offline, sem rede):

- `gerar_dados()` com uma árvore de pastas fake (criada em `tempfile`,
  alguns `.xml` distribuídos em 2-3 meses e 2 clientes) → confere contagens
  exatas por mês/tipo/cliente e que o total bate com a soma das partes.
- Certificado vencido → aparece marcado `vencido: true`.
- Cliente com `backfill_concluido` parcial (`{"recebidas": true}`, sem a
  chave `"emitidas"`) → aparece como `false` no dashboard, não quebra por
  chave ausente.
- Pasta de saída vazia (nenhum cliente processado ainda) → dashboard válido
  com listas vazias, não erro.
- `dashboard.html` abrindo `_dashboard.data.js` de um caminho relativo,
  verificado abrindo o arquivo de verdade no navegador (não só validação
  de sintaxe do JS).
