# 001 — Primeira tela

Estado: pronto
Ideia de origem: [primeira tela](../ideias/primeira-tela.md)

## Objetivo

Abro o FishingRod, vejo meus ambientes, crio um e entro nele; lá dentro vejo as frentes, as
tarefas, a wiki e os agentes, crio frentes e tarefas com cliques, abro tarefas em abas, escolho ou
crio uma sessão da tarefa e vejo os chats dela; volto para a lista de ambientes quando quiser;
fecho, abro de novo e está tudo lá.

## Como a tela fica

São duas telas. Tudo se faz com cliques (a Textual aceita o mouse no terminal). Os comandos com
`/` ficam para depois.

**Tela de início:** a lista dos meus ambientes, do mais mexido para o mais antigo, com os botões
para criar, entrar e apagar.

```
┌ FishingRod ─────────────────────────────────────┐
│ Meus ambientes                                   │
│   nexus-aquisicao        mexido hoje             │
│   faculdade              mexido há 3 dias        │
│                                                  │
│ [+ novo ambiente]  [entrar]  [apagar]            │
└──────────────────────────────────────────────────┘
```

**Tela do ambiente:** é onde eu trabalho. À esquerda, a árvore de frentes e tarefas, a wiki e os
agentes. À direita, uma aba para cada tarefa (ou página da wiki) que abri. Dentro da aba da tarefa,
escolho uma das sessões dela ou crio uma nova; dentro da sessão, uma aba para cada chat. Os níveis
estão na decisão [D21](../decisoes/D21-sessoes-dentro-da-tarefa.md).

```
┌ nexus-aquisicao ──────────────────────────────────── [← ambientes] ┐
│ FRENTES E TAREFAS    │ [Campanha LP] [Lista B2B] [wiki: index]      │
│ ▼ Mídia  [+ tarefa]  │ sessão: [sessão 1 ▾]  [+ sessão]  [memória]  │
│   • Campanha LP      │ [orquestrador]                    [+ chat]   │
│ ▼ Comercial [+ tar.] │                                              │
│   • Lista B2B        │   o chat escolhido                           │
│ [+ frente]           │                                              │
│                      │                                              │
│ WIKI                 │                                              │
│   index              │                                              │
│                      │                                              │
│ AGENTES              │                                              │
│   orquestrador       │                                              │
│   bibliotecário      │                                              │
└─────────────────────────────────────────────────────────────────────┘
```

Para criar um ambiente, uma frente ou uma tarefa, um botão abre uma janelinha que pede o nome.
Com o nome vazio, ela não deixa criar e mostra "precisa de um nome".

Para apagar um ambiente, aparece um aviso em maiúsculas, que pede confirmação:

> ATENÇÃO: APAGAR O AMBIENTE "nexus-aquisicao" APAGA TODAS AS FRENTES, TAREFAS, CHATS E A WIKI
> DELE. ISSO NÃO TEM VOLTA.
>
> [Cancelar] [Apagar]

## Fica de fora

- **Conversar com a IA de verdade:** o chat aparece na tela, mas mandar mensagem e receber resposta
  fica para o card da ideia [conversar com um agente](../ideias/conversar-com-agente.md).
- **Os comandos com `/`.**
- **Escolher a estrutura da wiki:** o ambiente nasce com a wiki vazia, só com o `index`
  (ideia [escolher a estrutura da wiki](../ideias/escolher-estrutura-da-wiki.md)).
- **Login:** virou a ideia [entrar com login](../ideias/entrar-com-login.md).
- **Apagar ou renomear frentes e tarefas:** o serviço ainda não faz isso.

## Partes

As partes são o plano inicial e podem mudar. Quando mudarem, registre aqui o que mudou e por quê.

- [x] Pôr a sessão entre a tarefa e o chat (domínio, banco, serviço, catálogo e testes). Entrou em
      2026-10-21, no começo da implementação: o Pedro explicou que uma tarefa tem várias sessões e
      cada sessão tem os seus chats ([D21](../decisoes/D21-sessoes-dentro-da-tarefa.md)).
- [x] Pôr a Textual no `pyproject.toml` (versão exata, 8.2.8) e criar o jeito de abrir o programa
      (`uv run fishingrod`).
- [x] Montar o programa (`src/fishingrod/interface/montagem.py`): o `ServicoDeAmbiente` com o
      banco SQLite, a wiki em arquivos e a lista de agentes, na pasta de dados do sistema. Os
      modelos dos agentes são provisórios: `opus` para o orquestrador e `sonnet` para o
      bibliotecário, pelo apelido que o Claude entende.
- [x] Tela de início: listar, criar, entrar e apagar ambientes, com a janelinha do nome e o aviso
      de apagar. Mudou no caminho: um clique só marca o ambiente (é o que deixa escolher qual
      apagar); entrar é com Enter, duplo clique ou o botão "entrar".
- [x] Tela do ambiente: a árvore de frentes e tarefas, com os botões de criar frente e tarefa, e o
      botão de voltar para a tela de início. Mudou no caminho: há um botão "+ tarefa" só, e não um
      por frente como no desenho; a tarefa nasce na frente escolhida na árvore.
- [x] Abas: abrir uma tarefa numa aba; dentro dela, escolher ou criar uma sessão, e as abas dos
      chats da sessão. Mudou no caminho: "+ sessão" cria a sessão direto, sem pedir nome, porque
      ela já se chama "sessão N".
- [x] Wiki e agentes na lateral: abrir uma página da wiki numa aba e ver a lista de agentes. Mudou
      no caminho: a porta da wiki não tinha como ler o `index`, e ganhou `ler_index`.
- [x] Botão "+ chat" na linha das abas de chat: abre uma janelinha com os agentes que podem ter
      chat (todos menos o orquestrador, que cada sessão já tem e só pode ter um) e abre o chat novo.
      Entrou em 2026-10-21, a pedido do Pedro depois de ver a tela; antes, abrir chat com outro
      agente estava em "Fica de fora".
- [x] Botão "memória" na linha da sessão: mostra e esconde, à direita dos chats, a memória da
      sessão escolhida (as anotações dos agentes, em markdown, por assunto). Trocando de sessão, a
      memória que aparece é a da sessão nova. Entrou em 2026-10-21, a pedido do Pedro. Por
      enquanto ela fica vazia: quem anota é o agente, e o agente ainda não conversa na tela.

## Como testar

O que o Pedro faz na tela e o que tem que acontecer. Cada item também tem um teste automático em
`tests/interface/test_telas.py`, que dirige a tela como uma pessoa faria; os quadrinhos abaixo
ficam para o Pedro marcar quando conferir com as próprias mãos; ele conferiu em 2026-10-21.

- [x] Abro o programa → vejo a lista dos meus ambientes (vazia na primeira vez).
- [x] Crio um ambiente → ele aparece na lista.
- [x] Tento criar com o nome vazio → aparece "precisa de um nome" e nada é criado.
- [x] Entro num ambiente → vejo a tela do ambiente, com a wiki mostrando o `index`.
- [x] Crio uma frente e uma tarefa dentro dela → as duas aparecem na árvore.
- [x] Clico numa tarefa → ela abre numa aba, na "sessão 1", com a aba do chat do orquestrador.
- [x] Crio uma sessão nova na tarefa → ela aparece como "sessão 2", já com o chat do orquestrador,
      e posso voltar para a "sessão 1".
- [x] Clico em "+ chat" e escolho o bibliotecário → aparece a aba "bibliotecario" ao lado da do
      orquestrador, já aberta; o orquestrador não aparece na escolha.
- [x] Clico em "memória" → aparece, à direita, a memória da sessão (vazia por enquanto); clico de
      novo → ela some.
- [x] Abro duas tarefas → as duas ficam em abas e eu passo de uma para a outra.
- [x] Clico no `index` da wiki → o conteúdo dele aparece numa aba.
- [x] Clico em voltar → estou de novo na lista de ambientes e posso entrar em outro.
- [x] Dois ambientes não se misturam: as frentes de um não aparecem no outro.
- [x] Fecho o programa, abro de novo → ambientes, frentes e tarefas continuam lá.
- [x] Apago um ambiente → aparece o aviso em maiúsculas; em "Cancelar", nada muda; em "Apagar",
      ele some da lista.

## Decisões usadas

- [D02 — O ambiente nasce vazio](../decisoes/D02-ambiente-nasce-vazio.md)
- [D03 — A tarefa nasce com o orquestrador](../decisoes/D03-tarefa-nasce-com-orquestrador.md)
- [D04 — Uma wiki por ambiente](../decisoes/D04-wiki-por-ambiente.md)
- [D05 — Nomes repetidos, identidade única](../decisoes/D05-nomes-repetidos-identidade-unica.md)
- [D07 — Começar pelo terminal](../decisoes/D07-comecar-pelo-terminal.md)
- [D08 — Apagar o ambiente apaga tudo](../decisoes/D08-apagar-ambiente-apaga-tudo.md)
- [D20 — Lista fixa de agentes](../decisoes/D20-lista-fixa-de-agentes.md)
- [D21 — Sessões dentro da tarefa](../decisoes/D21-sessoes-dentro-da-tarefa.md)

## Ao terminar

- [x] Rodar os testes automáticos (`uv run pytest`): 1017 passaram em 2026-10-21.
- [x] Acrescentar a funcionalidade em `docs/funcionalidades.md`.
- [x] Mudar o estado da ideia de origem para "virou o card 001".
- [x] Fazer o commit.
