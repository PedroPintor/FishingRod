# Organizar a interface em áreas

Estado: virou o [card 003](../cards/003-interface-em-areas-e-ficha-do-agente.md)
De onde veio: conversa do Pedro com a IA sobre o próximo card, em 2026-10-21.

A tela de hoje ficou do jeito que saiu na primeira vez: uma lateral com frentes, wiki e agentes
empilhados, e uma área de abas. Funciona, mas cada coisa nova vai disputar espaço nessa lateral.
A ideia é dar a cada tipo de coisa o seu lugar na tela, para que as próximas funcionalidades já
tenham onde encaixar. A estrutura é um começo, não fica fixa: vai sendo melhorada.

A interface tem dois objetivos.

**Explicabilidade.** Eu entendo por que os agentes fazem o que fazem. Quero saber o que um agente
é, o que está escrito nele e como ele foi feito. Se o orquestrador abre um chat que eu não pedi,
abro a ficha dele e encontro a pista: "está escrito aqui que ele sempre chama tal agente quando
acontece tal coisa". E quero saber que contexto a sessão usou: que partes da wiki os chats leram,
o que está na memória da sessão.

**Multitarefa.** Quem é astuto no uso de IA trabalha em várias tarefas ao mesmo tempo, e eu quero
que os usuários do FishingRod virem pessoas astutas no trabalho com IA. A interface tem que deixar
isso fácil: várias tarefas abertas, e duas lado a lado, mexendo numa enquanto acompanho a outra. A
tarefa é o nível mais alto de cada lado da tela, porque é ela que carrega a sessão e os chats
abertos nela.

A sensação que eu quero é a de um jogo gostoso de jogar: responde na hora, é confortável, parece
que estou dentro dele.

Ideias que saem daqui:

- [ver a ficha do agente](ver-a-ficha-do-agente.md)
- [ver o que a sessão leu da wiki](ver-o-que-a-sessao-leu-da-wiki.md)
- [trabalhar em duas tarefas lado a lado](trabalhar-em-duas-tarefas-lado-a-lado.md)

Ligado aos princípios P-11 ("o card trava; o usuário não") e à dor D-10 ("é muita função") em
`docs/produto/`.
