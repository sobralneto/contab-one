## ADDED Requirements

### Requirement: A troca de foco reemite o acesso sem recomeçar a sessão

O sistema DEVE (MUST) permitir que uma sessão viva troque o escritório em foco reemitindo
apenas o token de acesso, mantendo válida a credencial de renovação daquela sessão. A troca
NÃO DEVE (MUST NOT) derrubar a sessão nem as demais sessões do mesmo usuário.

#### Scenario: Troca de foco em uma aba

- **WHEN** um usuário com sessões abertas em dois navegadores troca o foco em um deles
- **THEN** aquele navegador passa a operar no novo escritório e o outro continua no
  anterior, ambas as sessões vivas

#### Scenario: Renovação depois da troca

- **WHEN** a sessão que trocou de foco renova o acesso
- **THEN** o novo acesso vem com o foco escolhido na troca, e não com o foco original do
  login

### Requirement: Perder o vínculo do escritório em foco encerra a sessão

O sistema DEVE (MUST) recusar a renovação de uma sessão cujo escritório em foco não esteja
mais entre os vínculos atuais do usuário.

Sem isso, revogar o acesso de alguém a um escritório só teria efeito ao fim da validade da
credencial de renovação — o mesmo furo que motivou invalidar as sessões na troca de senha.

#### Scenario: Vínculo revogado durante a sessão

- **WHEN** o vínculo de um usuário com o escritório em foco da sua sessão é removido e essa
  sessão tenta renovar
- **THEN** a renovação é recusada e a sessão termina

#### Scenario: Vínculo revogado de escritório que não está em foco

- **WHEN** um usuário vinculado a A e B está com A em foco e o vínculo com B é removido
- **THEN** a sessão continua válida em A, e B deixa de aparecer entre as opções de foco

## MODIFIED Requirements

### Requirement: Troca de senha e desativação encerram as sessões existentes

O sistema DEVE (MUST) invalidar todas as credenciais de renovação de um usuário quando a
senha dele é trocada (por ele mesmo ou por um administrador), quando o usuário é desativado
ou quando ele **perde o vínculo com todos os escritórios**.

Sem isso, uma senha trocada por suspeita de comprometimento deixa o invasor com acesso pela
validade inteira da credencial de renovação.

#### Scenario: Usuário troca a própria senha

- **WHEN** um usuário troca a própria senha
- **THEN** as credenciais de renovação emitidas antes da troca deixam de ser aceitas,
  exceto a da sessão que fez a troca

#### Scenario: Administrador redefine a senha de um usuário

- **WHEN** um administrador redefine a senha de outro usuário
- **THEN** todas as credenciais de renovação daquele usuário deixam de ser aceitas

#### Scenario: Usuário é desativado

- **WHEN** um administrador desativa um usuário
- **THEN** as credenciais de renovação daquele usuário deixam de ser aceitas imediatamente

#### Scenario: Usuário perde o último vínculo

- **WHEN** um usuário com papel de escritório fica sem nenhum escritório vinculado
- **THEN** todas as credenciais de renovação daquele usuário deixam de ser aceitas
