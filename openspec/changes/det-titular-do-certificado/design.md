## Context

Cada empresa começa com um `goto` ao portal. O recarregamento da SPA volta o
DET ao perfil do próprio usuário logado (confirmado contra o portal em
22/08/2026, ver `ErroEmpregadorDivergente`). Depois disso o agente sempre
abria a troca de perfil e digitava o CNPJ da empresa. Para o titular do
certificado, o portal recusa a troca, e o agente registrava erro na etapa
"Selecionar perfil".

## Goals / Non-Goals

**Goals:**

- Ler a Caixa Postal do titular sem abrir a troca de perfil.
- Nenhuma mudança para as demais empresas.

**Non-Goals:**

- Reconhecer o titular nos modos sem `.pfx` (`manual`, `politica_chrome`).
  Neles o navegador escolhe o certificado e o agente não tem o arquivo.
- Reordenar a carteira.

## Decisions

- **Reconhecer o titular pelo certificado, não pela tela.** As alternativas
  eram ler a faixa "Empregador:" logo depois do login ou tratar a recusa do
  portal depois de tentar a troca. A faixa depende do tempo de renderização,
  e tratar a recusa obriga a abrir a troca de perfil, que é justamente o que
  se quer evitar. O `.pfx` diz quem é o titular antes de abrir o navegador.
- **CNPJ do conteúdo do certificado, nunca do nome do arquivo.** O nome muda
  a cada renovação e não segue padrão obrigatório. É a mesma leitura do
  `certificado.py` removido em `remover-conferencia-certificado-det`, agora
  sem conferência nenhuma.
- **Falha ao ler o certificado gera só aviso.** Senha errada derruba o
  navegador logo depois, com mensagem própria. Sem CNPJ legível, o agente
  segue o comportamento de antes.
- **Sem reordenar a carteira.** O recarregamento no início de cada empresa
  já devolve o DET ao perfil do titular. Ler o titular na posição em que ele
  vem da carteira é seguro.
- **A conferência do empregador continua.** Se a tela não estiver no perfil
  do titular, `ErroEmpregadorDivergente` interrompe a leitura sem atribuir
  mensagens.

## Risks / Trade-offs

- [Sessão do perfil persistente aberta por outro certificado] → A faixa
  "Empregador:" mostra outro CNPJ e a conferência do empregador barra a
  leitura do titular. `--limpar-perfil` resolve, e o agente já sai do portal
  ao fim de cada execução.
- [O portal deixar de voltar ao perfil próprio no recarregamento] → Mesmo
  desfecho: a conferência barra a leitura e nenhuma mensagem vai para o CNPJ
  errado.

## Migration Plan

1. Distribuir o `det.exe` novo.
2. Rollback: voltar ao `det.exe` anterior. O titular volta a falhar na troca
   de perfil, sem efeito nos demais clientes.
