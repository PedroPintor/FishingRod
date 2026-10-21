# 003 — Interface em áreas e ficha do agente

Estado: a fazer
Ideias de origem:
- [organizar a interface em áreas](../ideias/organizar-a-interface-em-areas.md)
- [ver a ficha do agente](../ideias/ver-a-ficha-do-agente.md)

## Objetivo

**Quando** estou trabalhando numa tarefa e um agente faz algo que eu não esperava, **quero**
abrir ao lado do chat o que explica aquele agente e aquela sessão (a ficha dele, a memória, a
wiki), **para** entender por que ele agiu assim sem sair da tarefa.

## O que este card resolve

A tela do ambiente ficou do jeito que saiu na primeira vez: uma lateral com frentes, wiki e
agentes empilhados, e abas que misturam tarefas e páginas da wiki. Este card dá a cada coisa o seu
lugar, pensando nos dois objetivos da interface: **explicabilidade** e **multitarefa**. A
estrutura é um começo: o Pedro vai olhar na tela e ela vai ser ajustada.

Duas regras da estrutura:

- **A explicação mora dentro da tarefa.** Tudo o que explica é de um chat ou de uma sessão, e
  mais para a frente vão existir duas tarefas lado a lado. Por isso cada tarefa tem o seu painel
  de explicação, e não existe um painel único na tela.
- **Nada trava, e o foco não pula sozinho.** Abrir e fechar o painel, trocar de aba nele ou de
  chat não interrompe a resposta de nenhum agente, e o cursor continua onde eu estava.

## Como a tela fica

```
┌ topo: ambiente · Claude: 2 conexões ─────────────────────── [← ambientes] ┐
│ FRENTES  │ [Tarefa A] [Tarefa B]                                          │
│ E TAREFAS│ sessão 1 ▾   [orquestrador] [bibliotecario] [+ chat] [explicar]  │
│          │ ┌ chat ──────────────────────────┐┌ [ficha][memória][wiki] ─┐   │
│ ▸ frente │ │                                ││                         │   │
│   tarefa │ │                                ││                         │   │
│          │ │                                ││                         │   │
│ [+ frente│ │ ○ pronto para conversar        ││                         │   │
│ [+ tarefa│ │ > _                            ││                         │   │
│          │ └────────────────────────────────┘└─────────────────────────┘   │
└──────────┴────────────────────────────────────────────────────────────────┘
```

- **Lateral:** só frentes e tarefas. A wiki e os agentes saem dela e vão para o painel.
- **Área de trabalho:** uma aba por tarefa aberta. Páginas da wiki não abrem mais aqui.
- **Dentro da tarefa:** a escolha da sessão, as abas dos chats e o botão **explicar**, que abre e
  fecha o painel de explicação à direita do chat. Ele toma o lugar do botão "memória" de hoje.
- **Painel de explicação**, com três abas:
  - **ficha:** a ficha do agente do chat que está na frente. Trocar de chat troca a ficha.
  - **memória:** a memória da sessão, como o botão "memória" já mostra hoje.
  - **wiki:** a árvore da wiki do ambiente (o `index`, os assuntos, as páginas); clico numa página
    e vejo o conteúdo ali mesmo, no painel. É simples de propósito: esta é a área que mais tarde
    vai mostrar o que a sessão leu.

Os textos e as larguras podem mudar depois que o Pedro vir na tela.

## A ficha do agente

Só mostra o que existe; nada é editável neste card.

```
orquestrador                                        do software
abre cada sessão · modelo: opus

CONFIGURAÇÃO
Pode pedir (sempre com a sua confirmação):
  • criar_frente — Cria uma frente de trabalho no ambiente.
  • criar_tarefa — Cria uma tarefa na frente, já com uma sessão e o chat do orquestrador.
  • …
Não pode:
  • criar_sessao — só você abre sessões.
  • usar nada da sua máquina: arquivos, terminal, internet.
  • abrir chat com um agente fora da lista do software.

INSTRUÇÕES
Nenhuma instrução escrita. Ele age com o que o modelo já sabe e com a descrição das
ações acima.
```

- **Cabeçalho:** nome, papel ("abre cada sessão" ou "pode ser chamado num chat"), modelo e a
  marca "do software" (os dois agentes de hoje são do software).
- **Pode pedir:** as ações do catálogo que o agente pode acionar, com a descrição de cada uma,
  tiradas do próprio catálogo, para a ficha nunca desmentir o que o agente recebe. Diz que toda
  ação pede confirmação ([D15](../decisoes/D15-orquestrador-age-com-confirmacao.md)).
- **Não pode:** as ações que são só do usuário (tiradas do catálogo), mais duas frases fixas: sem
  ferramentas da máquina ([D16](../decisoes/D16-agentes-sem-ferramentas-da-maquina.md)) e só a
  lista de agentes do software ([D20](../decisoes/D20-lista-fixa-de-agentes.md)).
- **Instruções:** o texto exato que o Claude recebe como instrução; quando é vazio, a frase
  "Nenhuma instrução escrita…".

O bibliotecário tem a sua ficha também, do mesmo jeito: hoje ele não pode pedir nenhuma ação e
não tem instruções.

## Partes

As partes são o plano inicial e podem mudar. Quando mudarem, registre aqui o que mudou e por quê.

- [ ] **Nova lateral e área de trabalho:** a lateral fica só com frentes e tarefas; a área de
  trabalho só abre tarefas.
- [ ] **Painel de explicação:** o botão "explicar" na tarefa, o painel à direita do chat e as três
  abas; a memória muda de lugar para dentro dele.
- [ ] **Wiki no painel:** a árvore da wiki e a página aberta dentro da aba "wiki".
- [ ] **Ficha do agente:** a aba "ficha", montada a partir do agente e do catálogo.

## Como testar

O que o Pedro faz na tela e o que tem que acontecer. Ao lado de cada item, o teste automático que
confere; o nome exato entra quando o teste existir.

- [ ] Entro num ambiente → a lateral mostra só frentes e tarefas. *Teste:* a tela do ambiente não
  tem mais a wiki nem a lista de agentes na lateral.
- [ ] Abro uma tarefa e aperto "explicar" → o painel abre à direita do chat, na aba "ficha";
  aperto de novo → fecha. *Teste:* o botão mostra e esconde o painel.
- [ ] Com o chat do orquestrador na frente, olho a ficha → vejo o modelo, as ações que ele pode
  pedir, "criar_sessao" em "não pode" e "Nenhuma instrução escrita". *Teste:* o texto da ficha do
  orquestrador sai do agente e do catálogo.
- [ ] Troco para o chat do bibliotecário → a ficha troca para a dele. *Teste:* a ficha segue o
  chat ativo.
- [ ] Abro a aba "memória" → vejo a memória da sessão, como antes. *Teste:* a aba mostra as
  anotações da sessão escolhida.
- [ ] Abro a aba "wiki" e clico no `index` e numa página → o conteúdo aparece no painel, e nenhuma
  aba nova abre na área de trabalho. *Teste:* abrir uma página da wiki não cria aba de tarefa.
- [ ] Mando uma mensagem e, enquanto o agente responde, abro e fecho o painel e troco de aba nele
  → a resposta continua chegando e o cursor continua no campo de digitação. *Teste:* mexer no
  painel não interrompe a conversa nem tira o foco do campo.
- [ ] Com duas tarefas abertas, abro o painel numa → a outra continua como estava. *Teste:* o
  painel é de cada tarefa.

## Decisões usadas

- [D07 — começar pelo terminal](../decisoes/D07-comecar-pelo-terminal.md)
- [D15 — o orquestrador age com confirmação](../decisoes/D15-orquestrador-age-com-confirmacao.md)
- [D16 — agentes sem ferramentas da máquina](../decisoes/D16-agentes-sem-ferramentas-da-maquina.md)
- [D17 — memória é quadro branco](../decisoes/D17-memoria-e-quadro-branco.md)
- [D20 — lista fixa de agentes](../decisoes/D20-lista-fixa-de-agentes.md)
- [D21 — sessões dentro da tarefa](../decisoes/D21-sessoes-dentro-da-tarefa.md)

## Pode melhorar

Escolhas feitas para começar simples, para não esquecer. Uma por linha: **o quê** — por quê.
Quando uma virar trabalho de verdade, ganha um arquivo em `docs/ideias/` e a linha aponta para ele.

- **Duas tarefas lado a lado:** hoje uma tarefa aparece de cada vez — a multitarefa pede ver e
  mexer em duas ao mesmo tempo. Ver [trabalhar em duas tarefas lado a lado](../ideias/trabalhar-em-duas-tarefas-lado-a-lado.md).
- **Atalhos de teclado:** hoje troca-se de tarefa, chat e aba com o mouse ou o Tab — atalhos dão a
  sensação de jogo que responde na hora.
- **Instruções do orquestrador:** hoje a ficha mostra "nenhuma instrução" e nada é editável — o
  usuário escrevendo as instruções faz o orquestrador ter sentido no ambiente. Ver
  [escrever as instruções do orquestrador](../ideias/escrever-instrucoes-do-orquestrador.md).
- **Configuração dos agentes comuns:** hoje só existem agentes do software — os agentes comuns
  vão ter a configuração escolhida numa lista e as instruções num modelo base. Ver
  [formato de agente](../ideias/formato-de-agente.md).
- **Mostrar ou não o bibliotecário:** hoje a ficha dele aparece como a do orquestrador — talvez
  ele nem precise aparecer, por ser a parte fixa do software que cuida da wiki.
- **Aba "wiki" mostrando o que a sessão leu:** hoje ela só mostra a wiki inteira — o caminho do
  agente aceso na wiki explica o que ele usou para responder. Ver
  [ver o que a sessão leu da wiki](../ideias/ver-o-que-a-sessao-leu-da-wiki.md).
- **Wiki sem tarefa aberta:** hoje a wiki só aparece dentro de uma tarefa — talvez faça falta ver
  a wiki do ambiente sem abrir tarefa nenhuma.

## Ao terminar

- [ ] Rodar os testes automáticos (`uv run pytest`).
- [ ] Acrescentar a funcionalidade em `docs/funcionalidades.md`.
- [ ] Mudar o estado das ideias de origem para "virou o card 003".
- [ ] Fazer o commit.
