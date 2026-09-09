## Context

Ver [proposal.md](proposal.md) — Why. O que importa aqui é onde a validade é
escrita hoje, que são dois lugares:

- `UpsertClientesAsync` (`Features/Agent/AgentEndpoints.cs`) — o agente grava
  `CertificadoValidade` incondicionalmente no bloco de atualização, junto com
  nome, CNPJ e nome do arquivo.
- `AtualizarAsync` (`Features/Clientes/ClientesEndpoints.cs`) — o `PUT` grava
  `req.CertificadoValidade` incondicionalmente, sob a policy `EscritorioUsuario`.

A trava de hoje é só de tela (`:disabled` em `ClientesView.vue`): a API já
aceitava a validade de qualquer usuário do escritório, para cliente de qualquer
origem. Ou seja, a mudança de front não abre nada que já não estivesse aberto no
contrato — apenas para de esconder.

## Goals / Non-Goals

**Goals:**

- Uma única regra de precedência entre a data que a pessoa informa e a que o
  agente descobre, aplicada no servidor.
- Que o campo liberado na tela não seja uma promessa falsa — o valor digitado
  precisa sobreviver à próxima sincronização.

**Non-Goals:**

- Não mexe no CNPJ, que continua travado na tela para cliente de origem agente:
  ali o agente é a única fonte, e não há caso de uso de correção manual.
- Não registra proveniência da data (quem escreveu por último, quando). A regra
  de precedência dispensa isso; guardar a origem do valor seria coluna nova e
  migration, sem demanda que justifique.
- Não valida a data informada contra nada — data no passado é justamente o que
  descreve um certificado vencido.

## Decisions

**1. A comparação é contra a data gravada, não contra hoje.**

O agente grava se `recebida > gravada`. A alternativa considerada foi
`recebida > hoje` — "o agente só registra certificado que ainda vale".
Descartada por dois motivos:

- Cliente novo cujo `.pfx` já está vencido entraria com validade vazia e
  desapareceria dos alertas e do filtro de vencidos, que é exatamente a
  população que o escritório precisa enxergar.
- Não protegeria a correção manual no caso mais provável: certificado renovado
  até 2028 digitado na tela, agente ainda enxergando o `.pfx` válido até 2027 —
  data futura, portanto aceita por essa alternativa, e a correção some.

`recebida > gravada` cobre os dois casos e tem uma leitura simples: **a validade
nunca anda para trás sozinha**.

**2. Nulo recebido não apaga.**

`null` não é "maior que" nada, então cai na cláusula de não-alterar sem precisar
de tratamento próprio. Isso muda um comportamento atual (hoje um upsert sem
validade zera o campo), na mesma direção do resto da mudança: o agente não
destrói o que a tela informou.

**3. Cliente novo grava sem comparar.**

Não há valor anterior. Escrever direto mantém o cadastro inicial fiel ao que
existe na máquina do escritório, vencido ou não.

**4. `CertificadoNomeArquivo` continua sendo atualizado sempre.**

É o nome do `.pfx` que o agente encontrou — um fato sobre a máquina, não uma
opinião sobre a validade. Deixá-lo em lockstep com a data faria o painel mostrar
um nome de arquivo que não corresponde ao que está lá.

**5. A regra fica no servidor, não no agente.**

O robô Python não conhece o estado gravado; só a API conhece. Além disso, uma
regra no cliente valeria apenas para a versão do `nfse.exe` que a implementasse,
e o parque de agentes instalados é heterogêneo por definição.

## Risks / Trade-offs

- **Certificado substituído por outro de validade mais curta** (troca de
  emissor, revogação e reemissão) → o painel mantém a data mais longa, que passa
  a ser otimista demais. Aceito: é o caso raro, e o campo agora é editável — a
  pessoa corrige pela tela, que é justamente o caminho que esta mudança abre.
  O caminho inverso (data curta congelada, sem correção possível) era o estado
  anterior e não tinha saída nenhuma.
- **Data digitada errada — um "2039" por engano** → congela o alerta daquele
  cliente, porque nenhuma sincronização vai conseguir baixá-la. Mitigação: a
  própria tela, que agora permite corrigir para baixo. É a assimetria deliberada
  do desenho — pessoa manda em qualquer direção, agente só para frente.
- **Comportamento silencioso** → uma sincronização que ignora a data não avisa
  ninguém. A dica ao lado do campo é o que torna a regra previsível para quem
  digita; não há tela onde um aviso por cliente ignorado caberia hoje.
