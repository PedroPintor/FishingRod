# Ver o que a sessão leu da wiki

Estado: ideia
De onde veio: conversa do Pedro com a IA sobre o próximo card, em 2026-10-21. Faz parte de
[organizar a interface em áreas](organizar-a-interface-em-areas.md).

De um lado da tela está o chat; do outro, o grafo da wiki. Quando o agente lê alguma coisa da
wiki, o caminho dele vai sendo pintado no grafo. Passo o mouse por cima de um ponto e vejo que é
o arquivo X. Assim sei o que ele leu, e entendo por que respondeu ou agiu daquele jeito.

O mesmo vale para a sessão inteira: que contextos da wiki os chats dela já acessaram.

Para pensar:

- Hoje os agentes não leem a wiki: nenhum tem uma ação para isso. Antes de pintar o caminho, eles
  precisam poder ler (ver [D14](../decisoes/D14-busca-comeca-pelo-index.md)).
- No terminal, um grafo com o mouse por cima é difícil. Uma versão possível é a árvore da wiki,
  que já aparece na tela, com os arquivos lidos acesos.
