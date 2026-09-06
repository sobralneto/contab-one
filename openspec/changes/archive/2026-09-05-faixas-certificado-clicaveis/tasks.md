## 1. API — faixas como predicado compartilhado

- [x] 1.1 Criar `ContabOne.Api/Features/Clientes/CertificadoFiltros.cs` com as
  três faixas como `Expression<Func<Cliente, bool>>` (D2), disjuntas e presas ao
  horizonte de 30 dias, e um resolvedor que traduz o token do parâmetro
  (`vencidos`, `vencendoMais3d`) na expressão correspondente.
- [x] 1.2 `KpisAsync`: trocar os três `CountAsync` inline pelo predicado
  compartilhado, sem mudar os valores devolvidos.
- [x] 1.3 `ListarAsync`: aceitar `string? faixaCertificado` e aplicar a expressão
  quando o token for conhecido; token desconhecido é ignorado, não é erro.
- [x] 1.4 `TraducaoLinqTest`: provar com `ToQueryString()` que as três faixas
  traduzem.

## 2. Frontend — contrato e listagem

- [x] 2.1 `api/endpoints/clientes.ts`: `faixaCertificado?: string` nos parâmetros
  de `listarClientes`.
- [x] 2.2 `views/ClientesView.vue`: mover o seletor de certificado para fora do
  `v-if="auth.isPlatformAdmin"` (D3) e passar a mandar o parâmetro para todos os
  papéis.
- [x] 2.3 `views/ClientesView.vue`: seletor único com exatamente as três faixas
  do painel — Vencidos, Vencendo em até 3 dias, Vencendo de 4 a 30 dias (D4). Os
  períodos avulsos saem da tela; o valor do seletor é o próprio token enviado à
  API, sem tabela de conversão.
- [x] 2.4 `views/ClientesView.vue`: ler a escolha do endereço
  (`?faixaCertificado=` / `?diasVencimentoCert=`), como já se faz com
  `emOnboarding`.

## 3. Frontend — os cards viram links

- [x] 3.1 `views/HubView.vue`: `para` nos três `CartaoContador` —
  `/clientes?faixaCertificado=vencidos`, `/clientes?diasVencimentoCert=3` e
  `/clientes?faixaCertificado=vencendoMais3d`.

## 4. Testes

- [x] 4.1 `ContabOne.Api.Tests/ClientesTest.cs`: `faixaCertificado=vencidos` e
  `=vencendoMais3d` devolvem exatamente os mesmos clientes que os contadores
  correspondentes de `/api/dashboard/kpis` contam, no mesmo cenário de bordas
  (ontem, hoje, +3, +4, +30, +31); token desconhecido não filtra nada.
- [x] 4.2 `ContabOne.Frontend/src/views/ClientesView.spec.ts`: a tela aberta com
  `?faixaCertificado=vencidos` já pede a faixa à API e reflete a escolha no
  seletor; o seletor aparece também para admin de plataforma.

## 5. Verificação

- [ ] 5.1 `dotnet test` — **continuou impedido**, pelo mesmo motivo anterior a
  esta change: `ContabOne.Api.Tests` não compila contra o `main` da API. São 18
  erros, **todos** de `MensagensDet` / `MensagemDet` em `DetMensagensTest.cs`,
  `IsolamentoTest.cs` e `TraducaoLinqTest.cs` — tipo que só existe no branch
  `det-agent-paridade-nfse`, nunca mesclado.
  <br>O que se pôde apurar: **nenhum erro vem do código desta change**. Como o
  compilador reporta tudo numa passada, os testes novos (coerência
  contador↔lista nas seis bordas, token desconhecido, tradução das três faixas)
  compilam — só não podem ser executados por causa dos arquivos vizinhos. O
  código de produção da API compila.
  <br>Cuidado ao reverificar: com o dev server de pé, o build falha antes de
  compilar (lock do `.exe`) e devolve "sem erros", que engana. Compilar com
  `-p:BaseOutputPath=` para um diretório separado dá o sinal real.
- [x] 5.2 `npm --prefix ContabOne.Frontend run build` (`vue-tsc -b` + vite) e a
  suíte de frontend: **227/227 em 22 arquivos**.
