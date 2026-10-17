## 1. Agrupamento

- [x] 1.1 Em `MensagensDet.vue`, criar `computed` que agrupa as mensagens por assunto normalizado (trim + minúsculas), com grupo "Sem assunto", contagem de mensagens, de clientes distintos e envio mais recente
- [x] 1.2 Estado `modo` (`'agrupado' | 'lista'`, padrão `'agrupado'`) e `Set` de grupos expandidos

## 2. Interface

- [x] 2.1 Controle segmentado de 2 botões (Agrupado / Lista) com `aria-pressed`, usando classes compartilhadas ou novas em `components.css` e tokens de cor
- [x] 2.2 Tabela agrupada: linha por assunto expansível (`aria-expanded`) listando cliente, envio, prazo e botão de leitura
- [x] 2.3 Manter a tabela plana atual como modo "Lista"; garantir que filtro por cliente e modal de leitura funcionam nos dois modos e que trocar de modo não limpa o filtro

## 3. Testes e verificação

- [x] 3.1 Teste Vitest: padrão é agrupado; mesmo assunto em clientes diferentes vira um grupo (contagens); variação de caixa/espaços; "Sem assunto"
- [x] 3.2 Teste Vitest: alternar para Lista e voltar; expandir grupo e abrir mensagem; filtro preservado na troca
- [x] 3.3 Rodar `npm test` e `npm --prefix ContabOne.Frontend run build`
