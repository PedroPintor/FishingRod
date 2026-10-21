# 003 — Interface em áreas e ficha do agente

Estado: feito
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

A ficha tem duas partes. A **configuração** é feita de campos, como um formulário que um dia vai
poder ser editado; a de **instruções** é o texto que o agente recebe. Neste card a ficha só
mostra: nada é editável.

```
orquestrador                                        do software

CONFIGURAÇÃO
  Papel                    abre cada sessão
  Modelo                   opus
  Esforço de raciocínio    padrão do Claude
  Ferramentas              criar_frente · criar_tarefa · criar_chat ·
                           criar_etapa · concluir_etapa · anotar_memoria
  Ferramentas da máquina   nenhuma

INSTRUÇÕES
  Nenhuma instrução escrita.
```

Cada valor sai do que está configurado de verdade, para a ficha nunca desmentir o que o Claude
recebe:

| Campo | O que é | De onde sai |
|---|---|---|
| Nome | o nome do agente, no topo, com a marca "do software" | o agente |
| Papel | "abre cada sessão" ou "pode ser chamado num chat" | o papel do agente |
| Modelo | opus, sonnet, haiku | o modelo do agente |
| Esforço de raciocínio | o quanto ele pensa antes de responder | as opções que vão para o Claude; hoje não é escolhido, então é "padrão do Claude" |
| Ferramentas | as ações do FishingRod que ele pode pedir, só pelo nome | as ferramentas do agente, conferidas no catálogo |
| Ferramentas da máquina | arquivos, terminal, internet | as opções que vão para o Claude; hoje "nenhuma" ([D16](../decisoes/D16-agentes-sem-ferramentas-da-maquina.md)) |
| Instruções | o texto exato que o Claude recebe como instrução | as regras do agente; vazio vira "Nenhuma instrução escrita." |

Ficam de fora as outras opções do SDK. O limite de gasto em dólares só serve para quem usa chave
de API, e aqui é só a assinatura ([D09](../decisoes/D09-so-assinatura-do-claude.md)). O limite de
passos por resposta é "sem limite" de propósito. O modelo reserva, o formato de saída, os
subagentes do SDK, as skills e os plugins estão desligados ou não são usados. O resto é encanamento
(pasta de trabalho, retomada da conversa, credenciais, permissões internas).

O bibliotecário tem a sua ficha também, do mesmo jeito e só para leitura: hoje ele não tem
ferramentas nem instruções.

## Partes

As partes são o plano inicial e podem mudar. Quando mudarem, registre aqui o que mudou e por quê.

- [x] **Nova lateral e área de trabalho:** a lateral fica só com frentes e tarefas; a área de
  trabalho só abre tarefas.
- [x] **Painel de explicação:** o botão "explicar" na tarefa, o painel à direita do chat e as três
  abas; a memória muda de lugar para dentro dele.
- [x] **Wiki no painel:** a árvore da wiki e a página aberta dentro da aba "wiki".
- [x] **Ficha do agente:** a aba "ficha", montada a partir do agente e do catálogo.

### O que mudou no caminho

- **A escolha da sessão subiu para a linha das abas dos chats.** Antes ela tinha uma linha só
  dela; agora a barra de cima da tarefa é `sessão ▾ [+ sessão] [chats…] [+ chat] [explicar]`, como
  no desenho do card, e o chat e o painel ocupam o resto da altura.
- **O botão "explicar" e as abas do painel não recebem foco no clique.** É o que deixa o cursor no
  campo de digitação (a regra "o foco não pula sozinho"). O preço: hoje não se chega a eles com o
  Tab do teclado. Os atalhos de teclado, no "Pode melhorar", resolvem isso.
- **O painel só se mostra e se esconde; ele não redesenha a tarefa.** Antes o botão "memória"
  redesenhava a tarefa inteira, e o campo de digitação perdia o foco e o que já estava escrito
  nele. Por isso a memória no painel aberto se confere sozinha a cada segundo: os agentes anotam
  enquanto conversam.
- **As opções que a ficha mostra são lidas da mesma função que liga o chat.** O
  `opcoes_do_claude` (em `montagem.py`) chama o `montar_opcoes` do adaptador e lê dele o esforço,
  as ferramentas da máquina e as instruções. Assim, se as opções mudarem, a ficha muda junto. As
  instruções vêm do `system_prompt`, que é o texto exato que o Claude recebe.

## Como testar

O que o Pedro faz na tela e o que tem que acontecer. Ao lado de cada item, o teste automático que
confere, em `tests/interface/test_explicacao.py`.

- [x] Entro num ambiente → a lateral mostra só frentes e tarefas. *Teste:* a tela do ambiente não
  tem mais a wiki nem a lista de agentes na lateral (`test_a_lateral_mostra_so_frentes_e_tarefas`).
- [x] Abro uma tarefa e aperto "explicar" → o painel abre à direita do chat, na aba "ficha";
  aperto de novo → fecha. *Teste:* o botão mostra e esconde o painel
  (`test_o_botao_explicar_mostra_e_esconde_o_painel`).
- [x] Com o chat do orquestrador na frente, olho a ficha → vejo papel, modelo "opus", esforço
  "padrão do Claude", as seis ferramentas pelo nome (sem "criar_sessao"), ferramentas da máquina
  "nenhuma" e "Nenhuma instrução escrita.". *Teste:* cada campo da ficha sai do agente, do
  catálogo e das opções que vão para o Claude
  (`test_cada_campo_da_ficha_sai_do_agente_do_catalogo_e_das_opcoes`,
  `test_a_ficha_le_as_mesmas_opcoes_que_vao_para_o_claude` e
  `test_a_ficha_muda_quando_a_configuracao_muda`).
- [x] Troco para o chat do bibliotecário → a ficha troca para a dele. *Teste:* a ficha segue o
  chat ativo (`test_a_ficha_segue_o_chat_ativo`).
- [x] Abro a aba "memória" → vejo a memória da sessão, como antes. *Teste:* a aba mostra as
  anotações da sessão escolhida (`test_a_aba_memoria_mostra_as_anotacoes_da_sessao_escolhida`).
- [x] Abro a aba "wiki" e clico no `index` e numa página → o conteúdo aparece no painel, e nenhuma
  aba nova abre na área de trabalho. *Teste:* abrir uma página da wiki não cria aba de tarefa
  (`test_abrir_uma_pagina_da_wiki_nao_cria_aba_de_tarefa`).
- [x] Mando uma mensagem e, enquanto o agente responde, abro e fecho o painel e troco de aba nele
  → a resposta continua chegando e o cursor continua no campo de digitação. *Teste:* mexer no
  painel não interrompe a conversa nem tira o foco do campo
  (`test_mexer_no_painel_nao_interrompe_a_conversa_nem_tira_o_foco`).
- [x] Com duas tarefas abertas, abro o painel numa → a outra continua como estava. *Teste:* o
  painel é de cada tarefa (`test_o_painel_e_de_cada_tarefa`).

## Decisões usadas

- [D07 — começar pelo terminal](../decisoes/D07-comecar-pelo-terminal.md)
- [D09 — só a assinatura do Claude](../decisoes/D09-so-assinatura-do-claude.md)
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
- **Editar a configuração na ficha:** hoje a ficha só mostra — trocar o modelo e o esforço (em
  todos os agentes) e tirar e pôr ferramentas (nos agentes comuns) faz da ficha o lugar de
  reconfigurar o agente. Quem pode mexer em quê está em
  [ver a ficha do agente](../ideias/ver-a-ficha-do-agente.md).
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

- [x] Rodar os testes automáticos (`uv run pytest`).
- [x] Acrescentar a funcionalidade em `docs/funcionalidades.md`.
- [x] Mudar o estado das ideias de origem para "virou o card 003".
- [x] Fazer o commit.
