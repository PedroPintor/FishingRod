# Uma falha do Claude não derruba o programa

Estado: virou o [card 002](../cards/002-conversar-com-o-agente.md)
De onde veio: história de usuário US-03, escrita na fase do AI-DLC (tag `aidlc-congelado`).

Se o Claude cair, ficar fora do ar ou eu bater no limite da assinatura, vejo um aviso claro no
chat onde aconteceu, e o resto do programa continua funcionando. As outras tarefas e os outros
chats não são afetados.

O que já existe no código: o adaptador de sessão nunca deixa um erro do Claude escapar como
travamento. Ele devolve uma falha com motivo (sem login, limite atingido, fora do ar etc.), em
`src/fishingrod/adaptadores/sessao/falhas.py`. Falta a tela mostrar o aviso.
