## MODIFIED Requirements

### Requirement: A identidade visual da dashboard vem do escritório

O sistema DEVE (MUST) montar a dashboard com o leiaute escolhido para o
escritório da sessão no cadastro daquele escritório, entre três identidades
fixas: a neutra da plataforma, a da L&J e a da MUDAHR. Cada identidade define ao
mesmo tempo a paleta do documento e o logotipo estampado no cabeçalho.

O sistema DEVE (MUST) usar a identidade neutra da plataforma para escritório
cujo leiaute não esteja definido ou não seja reconhecido — nunca a identidade de
outro escritório.

O leiaute escolhido DEVE (MUST) valer igualmente para a dashboard exibida na
tela, para o HTML exportado e para o PDF, que são o mesmo documento. A
identidade visual DEVE (MUST) estar disponível junto com os dados que ela pinta,
sem estado intermediário em que o painel já apareceu e ainda vai trocar de
cores.

O leiaute da dashboard NÃO DEVE (MUST NOT) ser afetado pelo tema da
plataforma — inclusive o modo escuro —, porque é documento entregue ao
cliente final e precisa sair igual na tela e no PDF.

#### Scenario: Escritório com identidade própria

- **WHEN** o escritório tem o leiaute de uma das duas marcas escolhido no seu
  cadastro
- **THEN** a dashboard usa as cores e o logotipo dessa identidade

#### Scenario: Escritório sem identidade configurada

- **WHEN** o escritório está no leiaute neutro, ou seu leiaute não é reconhecido
- **THEN** a dashboard é montada com a identidade neutra da plataforma, sem
  erro e sem logotipo de outro escritório

#### Scenario: Plataforma em modo escuro

- **WHEN** o usuário está com a plataforma em modo escuro e abre a dashboard
- **THEN** a dashboard é exibida com as próprias cores, idêntica ao que será
  exportado

#### Scenario: Exportação mantém o leiaute

- **WHEN** o usuário exporta a dashboard de um escritório em leiaute de marca,
  em HTML ou em PDF
- **THEN** o arquivo sai com as mesmas cores e o mesmo logotipo vistos na tela

#### Scenario: Abertura sem piscar de identidade

- **WHEN** o usuário abre a dashboard de um cliente com apurações gravadas
- **THEN** o painel aparece já no leiaute do escritório, sem passar antes pelo
  neutro

#### Scenario: Tela de ausência de dados

- **WHEN** a dashboard é aberta para um cliente sem nenhuma apuração no
  intervalo
- **THEN** a tela que informa a ausência de dados também respeita o leiaute do
  escritório, em vez de cair no neutro por falta de apurações
