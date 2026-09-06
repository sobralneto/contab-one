## 1. API

- [x] 1.1 `ListarAsync`: aceitar `string? ordenarPor` e `string? direcao`, e
  resolver a ordenação por `switch` fechado (D1) — código, nome, certificado,
  atualização e escritório. Valor desconhecido cai em nome crescente.
- [x] 1.2 Toda ordenação termina em `ThenBy(c => c.Id)` (D2), inclusive a
  padrão, para a paginação não repetir nem omitir linha no empate.
- [x] 1.3 Ordenação por certificado precede o critério real com
  `c.CertificadoValidade == null`, para os sem certificado ficarem no fim nas
  duas direções (D3).
- [x] 1.4 `TraducaoLinqTest`: provar que as cinco ordenações traduzem, incluindo
  a de certificado com o ramo de nulos.

## 2. Frontend

- [x] 2.1 `api/endpoints/clientes.ts`: `ordenarPor` e `direcao` nos parâmetros.
- [x] 2.2 `assets/styles/components.css`: variante ordenável de `.data-table th`
  no padrão compartilhado (D5), com o indicador de direção.
- [x] 2.3 `views/ClientesView.vue`: cabeçalhos acionáveis com dois estados (D4),
  `aria-sort` na coluna ativa, e troca de ordenação voltando à primeira página.
- [x] 2.4 Descoberta: glifo neutro em TODA coluna ordenável, não só na ativa
  (D6). Antes, coluna ordenável inativa era idêntica à de CNPJ e a única pista
  era o cursor — que só aparece depois de o ponteiro já estar lá.
- [x] 2.5 `tabindex`, Enter/Espaço, `title` e foco visível nos cabeçalhos:
  cabeçalho que só responde a clique deixa a ordenação inalcançável por teclado.
- [x] 2.6 A ordem das colunas do `<thead>` passa a sair de uma lista única, com
  a coluna sem `chave` marcando a que não ordena — é onde o cabeçalho sai do
  compasso com o corpo quando alguém acrescenta coluna.

## 3. Testes

- [x] 3.1 `ContabOne.Api.Tests/ClientesTest.cs`: ordem padrão inalterada;
  ordenação por código nas duas direções; clientes sem certificado no fim nas
  duas direções; coluna desconhecida cai no padrão sem erro.
- [x] 3.2 `ContabOne.Api.Tests/ClientesTest.cs`: percorrer todas as páginas de
  uma listagem ordenada por coluna com empate total e verificar que o conjunto
  não repete nem omite cliente — o defeito que o desempate existe para impedir.
- [x] 3.3 `ClientesView.spec.ts`: clicar num cabeçalho pede a coluna crescente;
  clicar de novo inverte; clicar em outra coluna volta a crescente; o cabeçalho
  de CNPJ não é acionável.

## 4. Verificação

- [ ] 4.1 `dotnet test` — **continua impedido**, pelos mesmos erros de
  `MensagemDet` anteriores a esta change. Compilando para diretório separado
  (o lock do `.exe` pelo dev server mascara o resultado), o código desta change
  **não acrescenta nenhum erro**: os testes novos compilam, só não podem ser
  executados.
- [x] 4.2 `npm --prefix ContabOne.Frontend run build` (`vue-tsc -b` + vite) e a
  suíte de frontend: **230/230 em 22 arquivos**.
