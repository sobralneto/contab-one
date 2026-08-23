# ciclo-de-vida-da-sessao Specification

## Purpose

Define como uma sessão de usuário do painel nasce, se renova e — sobretudo — como ela morre, para que sair do sistema, trocar a senha ou perder o acesso tenham efeito imediato em vez de esperar o vencimento natural do token.

## Requirements

### Requirement: Sair do sistema encerra a sessão de verdade

O sistema DEVE (MUST) invalidar a credencial de renovação no servidor quando o usuário sai, de modo que uma cópia dessa credencial capturada antes do logout deixe de servir para obter novos acessos. Apagar o cookie do navegador NÃO É (MUST NOT be) suficiente.

#### Scenario: Renovação com credencial de sessão encerrada

- **WHEN** um pedido de renovação apresenta uma credencial de refresh de uma sessão já encerrada pelo logout
- **THEN** a API responde 401 e nenhum novo acesso é emitido

#### Scenario: Logout não derruba as outras sessões do mesmo usuário

- **WHEN** um usuário com sessões abertas em dois navegadores sai em um deles
- **THEN** a sessão do outro navegador continua válida

### Requirement: Troca de senha e desativação encerram as sessões existentes

O sistema DEVE (MUST) invalidar todas as credenciais de renovação de um usuário quando a senha dele é trocada (por ele mesmo ou por um administrador) ou quando o usuário é desativado.

Sem isso, uma senha trocada por suspeita de comprometimento deixa o invasor com acesso pela validade inteira da credencial de renovação.

#### Scenario: Usuário troca a própria senha

- **WHEN** um usuário troca a própria senha
- **THEN** as credenciais de renovação emitidas antes da troca deixam de ser aceitas, exceto a da sessão que fez a troca

#### Scenario: Administrador redefine a senha de um usuário

- **WHEN** um administrador redefine a senha de outro usuário
- **THEN** todas as credenciais de renovação daquele usuário deixam de ser aceitas

#### Scenario: Usuário é desativado

- **WHEN** um administrador desativa um usuário
- **THEN** as credenciais de renovação daquele usuário deixam de ser aceitas imediatamente

### Requirement: A renovação de sessão funciona no domínio publicado

O sistema DEVE (MUST) entregar a credencial de renovação de um modo que o navegador realmente a devolva nas chamadas que o frontend publicado faz à API, considerando que frontend e API podem estar em domínios distintos. A configuração do cookie NÃO DEVE (MUST NOT) impedir o envio no arranjo de domínios em produção.

Se o arranjo exigir cookie enviado entre sites, o sistema DEVE (MUST) proteger as rotas que mudam estado contra requisição forjada de outro site.

#### Scenario: Sessão além da validade do acesso

- **WHEN** um usuário permanece no sistema por mais tempo que a validade do token de acesso, sem fechar a aba
- **THEN** a sessão é renovada em silêncio e o usuário não é levado à tela de login

#### Scenario: Pedido de renovação partindo de outro site

- **WHEN** uma página de terceiro tenta disparar a renovação ou uma escrita usando o cookie do usuário
- **THEN** o pedido é recusado

### Requirement: O login responde de forma uniforme

O sistema DEVE (MUST) responder a credenciais inválidas com a mesma resposta e sem diferença observável de tempo, tenha o e-mail informado uma conta ou não. NÃO DEVE (MUST NOT) ser possível descobrir quais e-mails existem medindo o tempo de resposta.

#### Scenario: Login com e-mail inexistente

- **WHEN** alguém tenta entrar com um e-mail que não existe
- **THEN** a resposta é indistinguível — em conteúdo e em tempo — da resposta a um e-mail existente com senha errada

### Requirement: A conta bloqueia após tentativas seguidas com senha errada

O sistema DEVE (MUST) bloquear temporariamente a conta após um número definido de tentativas seguidas com senha errada, com o limite e a duração configurados de forma explícita e não herdados de padrão implícito.

#### Scenario: Sequência de senhas erradas

- **WHEN** são feitas tentativas com senha errada até o limite configurado
- **THEN** a conta passa a recusar login até o fim do período de bloqueio, mesmo com a senha correta

#### Scenario: Acerto antes do limite

- **WHEN** o usuário erra a senha algumas vezes e acerta antes do limite
- **THEN** o login é aceito e o contador de tentativas volta a zero

### Requirement: O token de acesso declara e valida sua procedência

O sistema DEVE (MUST) emitir tokens de acesso identificando quem os emitiu e para qual destinatário, e DEVE (MUST) recusar tokens que não tragam essa identificação esperada — mesmo quando a assinatura confere.

#### Scenario: Token assinado com a chave certa mas de outra procedência

- **WHEN** chega um token corretamente assinado porém sem a identificação de emissor e destinatário esperada
- **THEN** a API responde 401

### Requirement: O destino após o login é sempre interno

O sistema DEVE (MUST) aceitar como destino pós-login apenas caminhos internos da própria aplicação, e NÃO DEVE (MUST NOT) enviar o usuário para um endereço externo indicado na URL da tela de login.

#### Scenario: Tela de login recebe destino externo

- **WHEN** a tela de login é aberta com um destino que aponta para fora da aplicação
- **THEN** após entrar, o usuário vai para a página inicial do sistema, e não para o endereço externo
