## Context

`AgentEndpoints.cs` (handshake) faz `existente.Nome = c.Nome;` para todo cliente existente. Os demais campos de edição humana já têm proteção: regime e situação ficam fora da lista de campos do agente, a validade só avança, e o CNPJ respeita `CnpjConfirmadoManualmente`. O `Nome` é a lacuna. O agente (`Nfse.Agent/nfse.py`, `ler_certificado`) deriva o nome do arquivo `.pfx`; quando o nome não casa com `PADRAO_CERTIFICADO` nem com `PADRAO_CERTIFICADO_SEM_SENHA`, usa o stem inteiro, sufixo de senha e validade incluídos. Em produção isso desfez 36 nomes corrigidos por carga manual.

## Goals / Non-Goals

**Goals:**
- Um nome definido por uma pessoa não é mais sobrescrito pelo agente.
- Comportamento atual preservado para clientes que ninguém editou.
- Mesmo padrão já usado para o CNPJ, para o código continuar previsível.

**Non-Goals:**
- Mudar o contrato do agente ou exigir nova versão do robô em campo.
- Normalizar ou limpar nomes existentes automaticamente.
- Indicador de interface (opcional, fora do escopo mínimo).

## Decisions

**D1 — Flag nova `NomeEditadoManualmente`, não reuso de `CnpjConfirmadoManualmente`.** Nome e CNPJ têm ciclos de vida independentes: alguém pode confirmar o CNPJ sem tocar no nome e vice-versa. Reusar a flag travaria o nome de todo cliente que já teve CNPJ confirmado — 106 em produção — e quebraria a semântica da existente. Alternativa descartada: normalizar o nome no servidor (heurística sobre o sufixo) — frágil e não distingue nome correto de nome ruim.

**D2 — A tela liga a flag só quando o nome muda** (`cliente.Nome != req.Nome`, comparado antes de atribuir). A tela reenvia o formulário inteiro; ligar a flag em todo PUT travaria o nome em qualquer edição. A flag nunca é desligada por este fluxo.

**D3 — O handshake só atribui `Nome` quando a flag é falsa.** Cliente novo é criado como hoje (nome do agente, flag falsa). A atribuição fica no mesmo bloco que preserva regime e situação, com comentário dizendo por quê, como nos campos vizinhos.

**D4 — Carga de dados em produção fica fora da migration.** A migration só adiciona a coluna com padrão `false`. Marcar as 106 linhas e regravar os 36 nomes é um `UPDATE` pontual feito depois do deploy, com confirmação explícita — dado de produção específico não pertence a uma migration que também roda nos testes e em ambiente local.

**D5 — Complemento no agente é opcional e posterior.** Com o servidor protegido, o agente deixa de ser a causa do estrago, mas continua mandando um nome ruim para clientes novos. Corrigir `ler_certificado` evita isso na origem; só vale depois do passo do servidor, e exige rodar a suíte Python do `Nfse.Agent`.

## Risks / Trade-offs

- [Migration e código precisam ir no mesmo deploy] → o campo é lido pelo handshake; a coluna precisa existir antes. Deploy único; migrations rodam no startup.
- [Árvore da API com alterações não commitadas de outra sessão (`Entities.cs`, migration `RemoverPaginasMensagensEExecucoesDoDet`)] → gerar a migration só depois delas estarem commitadas, para a ordem do snapshot ficar correta; não editar o snapshot à mão.
- [Cliente de nome ruim nunca editado continua sendo sobrescrito] → comportamento atual preservado de propósito; a proteção vale só para quem alguém corrigiu.
- [Quem quiser voltar ao nome do agente não tem como desligar a flag] → fora do escopo; se a necessidade aparecer, vira uma ação explícita na tela.
- [Agente em campo] → nenhuma mudança necessária; a correção é toda no servidor.

## Migration Plan

1. Commitar o trabalho pendente da outra sessão; gerar a migration `AdicionaNomeEditadoManualmenteEmCliente`.
2. Deploy do código + migration.
3. Pós-deploy, com confirmação do usuário: `UPDATE` das 106 linhas (`NomeEditadoManualmente = true`) e regravação dos 36 nomes que voltaram.
4. Verificar com uma sincronização real que os nomes não voltam.
5. Rollback: reverter o deploy; a coluna extra é inofensiva.
