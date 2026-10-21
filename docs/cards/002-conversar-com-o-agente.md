# 002 — Conversar com o agente

Estado: a fazer
Ideias de origem:
- [conversar com um agente](../ideias/conversar-com-agente.md)
- [ver a conversa antiga depois de reabrir](../ideias/ver-conversa-antiga.md)
- [o agente lembra da conversa antiga](../ideias/agente-lembra-conversa-antiga.md)
- [uma falha do Claude não derruba o programa](../ideias/falha-do-claude-nao-derruba.md)

## Objetivo

**Quando** eu abro o chat de uma tarefa, **quero** conversar com o agente como no Claude Code
(mando, vejo a resposta chegar, fecho e depois continuo de onde parei), **para** trabalhar com a IA
dentro do FishingRod sem medo de deixar sessões fantasmas gastando a minha assinatura.

## O medo que este card resolve

Num código antigo, cada Enter parecia abrir uma sessão nova do Claude, e as velhas ficavam abertas,
fantasmas. O adaptador de sessão (`src/fishingrod/adaptadores/sessao/`) já foi feito para não
deixar isso acontecer: um processo do Claude por chat, que só sobe na primeira mensagem, fica
vivo entre uma mensagem e outra e só termina quando alguém fecha. O que falta é a tela usar o
adaptador do jeito certo. Por isso este card vira regra e teste:

- **Um processo por chat:** a tela abre a conexão de um chat uma vez e a reaproveita em toda
  mensagem.
- **Chats em paralelo:** cada chat tem a sua conexão; mandar mensagem num não trava a tela nem os
  outros.
- **Nada fica aberto sem eu ver:** a tela mostra quantas conexões estão abertas, e as três formas
  de desligar levam esse número a zero.

## Como a tela fica

**Mostrador de conexões**, na tela do ambiente: `Claude: 2 conexões abertas`. Conta os processos
do Claude vivos agora.

**Faixa do chat**, embaixo do chat, logo acima do campo de digitação, com o estado e o botão:

```
│ ○ pronto para conversar                      [ligar]    │
│ > _                                                      │
```
```
│ ● ligado · respondendo…                     [desligar]  │
│ > _                                                      │
```

- **Chat novo, ou reaberto depois de fechar o programa:** "pronto para conversar". Não há processo,
  e ele não conta no mostrador.
- **Mandar mensagem:** liga sozinho. O botão "ligar" é opcional: sobe o processo antes, para a
  primeira resposta vir mais rápido.
- **Desligar:** o processo termina, o mostrador desce 1 e o chat volta a "pronto para conversar".
  Mandando outra mensagem, ele liga de novo e retoma a conversa.

Os textos dos estados podem mudar depois.

**Mensagens:**

- A resposta aparece em pedaços, enquanto é escrita.
- Mando mensagem enquanto ele responde: ela entra numa **fila** e é enviada sozinha quando a
  resposta acabar.
- **Esc** interrompe a resposta: o que já tinha aparecido fica, marcado "(interrompida)", e as
  mensagens da fila voltam para o campo de digitação, para eu reescrever.

**As três formas de desligar:**

1. Fechar o programa: desliga todos os chats.
2. Sair do ambiente (voltar para a lista): desliga todos os chats do ambiente. Uma resposta em
   andamento é interrompida, como no Esc.
3. O botão "desligar" na faixa do chat: desliga só aquele chat.

**Avisos no chat:**

- Falha do Claude (fora do ar, limite da assinatura, sem login): um aviso claro só naquele chat;
  os outros chats e o resto do programa continuam.
- Conversa que o Claude não achou mais (pasta apagada, outro computador): "não consegui retomar a
  conversa; ela recomeça do zero". O texto antigo continua visível na tela.

## Fica de fora

- **Confirmar na tela as ações do orquestrador:** por enquanto, toda ação dele que pede
  confirmação é recusada (`ConfirmacaoRecusada`, em `src/fishingrod/interface/montagem.py`), e o
  chat mostra que foi recusada. Confirmar fica para um card próprio: ideia
  [confirmar no chat as ações que os agentes pedem](../ideias/confirmar-acoes-dos-agentes-no-chat.md).
- **Executar uma etapa pelo chat:** ideia [executar etapa pelo chat](../ideias/executar-etapa-pelo-chat.md).
- **O bibliotecário escrevendo na wiki:** ideia [bibliotecário escreve na wiki](../ideias/bibliotecario-escreve-na-wiki.md).
- **Os comandos com `/`.**
- **Desligar todos os chats de uma vez:** está em "Pode melhorar".

## Partes

As partes são o plano inicial e podem mudar. Quando mudarem, registre aqui o que mudou e por quê.

- [ ] **Retomar pela memória do Claude** ([D22](../decisoes/D22-conversa-continua-pelo-claude.md)).
      Tirar o `no-session-persistence` de `opcoes.py`; guardar no banco, para cada chat, o código da
      conversa do Claude (o `session_id` da mensagem de resultado); ao conectar um chat que já tem
      código, passar o `resume`. A porta de sessão ganha um jeito de abrir "retomando de onde
      parou", com um marcador opaco, sem tipo do SDK ([D19](../decisoes/D19-nucleo-nao-depende-do-claude.md)).
      A pasta de trabalho do Claude é sempre a mesma: o `resume` procura a conversa por ela. Se o
      Claude não achar a conversa, o adaptador avisa e começa uma nova. A medição 15 passa a conferir
      o contrário (a conversa é guardada), e os testes de `test_opcoes.py` acompanham.
- [ ] **Montagem:** `montar` cria o adaptador de sessão, e `Programa.fechar` chama `encerrar`
      antes de fechar o banco.
- [ ] **Serviço de conversa** (camada de aplicação, um por programa): guarda a sessão viva de cada
      chat (abre uma vez e reaproveita), a fila de mensagens de cada chat, grava as mensagens no
      banco (`inserir_mensagem`) e sabe quantas conexões estão abertas. É ele que a tela usa; a
      tela nunca fala direto com o adaptador.
- [ ] **Tela do chat:** a conversa antiga ao abrir, o campo de digitação, a resposta em pedaços, a
      fila e o Esc. O envio roda em segundo plano (worker da Textual), para a tela nunca travar.
- [ ] **Faixa do chat** com o estado e o botão ligar/desligar.
- [ ] **Mostrador de conexões** na tela do ambiente.
- [ ] **Desligar ao sair:** sair do ambiente desliga os chats dele; fechar o programa desliga
      todos.
- [ ] **Avisos:** falha do Claude e conversa não encontrada, cada um no seu chat.

## Como testar

O que o Pedro faz na tela e o que tem que acontecer. Ao lado de cada item, o teste automático que
confere; o nome exato entra quando o teste existir. Os marcados `sdk_real` usam o Claude de
verdade e gastam a assinatura (`uv run pytest -m sdk_real`); os outros usam um Claude de mentira,
roteirizado.

- [ ] Mando "oi" no chat do orquestrador → a resposta aparece em pedaços e o mostrador diz 1.
      *Teste:* tela do chat com Claude roteirizado; e um `sdk_real` de ponta a ponta.
- [ ] Mando 5 mensagens seguidas no mesmo chat (esperando cada resposta) → o mostrador continua
      em 1. *Teste:* o Claude roteirizado foi criado uma vez só.
- [ ] Mando duas mensagens sem esperar → a segunda espera e sai sozinha quando a primeira resposta
      acaba. *Teste:* a fila do serviço de conversa.
- [ ] Aperto Esc no meio da resposta → ela para, fica "(interrompida)", e a mensagem da fila volta
      para o campo. *Teste:* tela do chat; o processo morto já é conferido pela medição 16.
- [ ] Mando mensagem na tarefa A e, enquanto ela responde, mando outra na tarefa B → as duas
      respondem, cada uma no seu chat, e a tela não trava. *Teste:* dois chats roteirizados ao
      mesmo tempo; a medição 10 já confere dois processos de verdade.
- [ ] Clico em "desligar" → o mostrador desce 1 e o chat mostra "pronto para conversar"; mando
      outra mensagem → ele liga de novo. *Teste:* tela do chat.
- [ ] Saio do ambiente com chats ligados → o mostrador vai a 0. *Teste:* tela do ambiente.
- [ ] Fecho o programa → nenhum processo do Claude fica rodando. *Teste:* `sdk_real` que conta os
      processos antes e depois.
- [ ] Fecho o programa, abro de novo e abro o chat → as mensagens estão lá. *Teste:* tela com
      banco numa pasta temporária.
- [ ] Digo "meu número da sorte é 42", fecho o programa, abro e pergunto o número → ele responde
      42. *Teste:* `sdk_real` com `resume`.
- [ ] A conversa do Claude sumiu → aparece o aviso, a conversa recomeça do zero e o texto antigo
      continua na tela. *Teste:* Claude roteirizado que não acha a conversa.
- [ ] O Claude falha num chat → o aviso aparece só nele, e outro chat continua conversando.
      *Teste:* Claude roteirizado que falha em um dos dois chats.

## Decisões usadas

- [D09 — Só a assinatura do Claude](../decisoes/D09-so-assinatura-do-claude.md)
- [D16 — Agentes sem as ferramentas da máquina](../decisoes/D16-agentes-sem-ferramentas-da-maquina.md)
- [D19 — O núcleo não depende do Claude](../decisoes/D19-nucleo-nao-depende-do-claude.md)
- [D21 — Sessões dentro da tarefa](../decisoes/D21-sessoes-dentro-da-tarefa.md)
- [D22 — A conversa continua pela memória do Claude](../decisoes/D22-conversa-continua-pelo-claude.md)

## Pode melhorar

- **Retomar quando a conversa do Claude sumiu:** hoje recomeça do zero, com um aviso; dá para
  conferir a instalação e a pasta do Claude e reenviar o histórico do nosso banco — por quê: o
  usuário não perde o contexto se apagar a pasta ou trocar de computador. Ideia:
  [conferir o Claude e retomar sem ele](../ideias/conferir-o-claude-e-retomar-sem-ele.md).
- **Voltar a um chat antigo: o que é lido e como:** hoje a tela mostra a conversa inteira e o
  Claude retoma tudo — por quê: em conversas longas dá para mostrar e carregar menos, resumir, ou
  escolher o que a IA relê, gastando menos e achando mais rápido o que importa.
- **Desligar todos os chats de uma vez:** hoje é um por um, no botão de cada chat — por quê: com
  muitos chats ligados, desligar um a um cansa.

## Ao terminar

- [ ] Rodar os testes automáticos (`uv run pytest`).
- [ ] Rodar os testes com o Claude de verdade (`uv run pytest -m sdk_real`).
- [ ] Acrescentar a funcionalidade em `docs/funcionalidades.md`.
- [ ] Mudar o estado deste card para "pronto".
- [ ] Fazer o commit.
