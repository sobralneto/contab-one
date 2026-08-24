## ADDED Requirements

### Requirement: Menu de ferramentas só aparece com o catálogo resolvido

O sistema DEVE (MUST) manter o menu de ferramentas ausente enquanto o
catálogo da sessão não tiver sido resolvido. Nenhum item de ferramenta pode
ser renderizado a partir de suposição, valor padrão ou resíduo de sessão
anterior — só a partir do catálogo daquela sessão.

#### Scenario: Layout montado antes do catálogo chegar

- **WHEN** a sessão já está confirmada e a carga do catálogo ainda está em
  andamento
- **THEN** o layout exibe a área de navegação sem nenhum item de ferramenta
  e sem título de domínio, e passa a exibi-los quando o catálogo chega

#### Scenario: Catálogo não carrega

- **WHEN** a carga do catálogo da sessão falha
- **THEN** a aplicação mantém o acesso à página inicial e aos itens que não
  dependem de ferramenta, sinaliza a falha e oferece nova tentativa, sem
  encerrar a sessão

### Requirement: Troca de sessão descarta o catálogo anterior

O sistema DEVE (MUST) descartar o catálogo carregado ao encerrar a sessão,
de modo que o menu de um escritório nunca seja exibido para a sessão
seguinte.

#### Scenario: Logout seguido de login de outro escritório

- **WHEN** um usuário sai e outro usuário, de escritório diferente, entra na
  mesma aba
- **THEN** o menu exibido é o do catálogo do segundo escritório, sem nenhum
  item remanescente do primeiro
