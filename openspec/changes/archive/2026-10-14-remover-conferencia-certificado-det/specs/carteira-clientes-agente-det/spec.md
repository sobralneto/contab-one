## REMOVED Requirements

### Requirement: A resposta traz o hash do CNPJ do escritório

**Reason**: O hash só servia à conferência do certificado no `Det.Agent`, que
foi removida. O escritório é o da chave que faz a chamada.

**Migration**: Nenhuma. O agente 1.0.0 trata a ausência do campo como
escritório sem CNPJ no painel: avisa e segue.
