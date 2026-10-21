# 002 — Conversar com o agente

Estado: pronto
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
│ ○ pronto para conversar                                  │
│ > _                                                      │
```
```
│ ● ligado · respondendo…                     [desligar]  │
│ > _                                                      │
```

- **Chat novo, ou reaberto depois de fechar o programa:** "pronto para conversar". Não há processo,
  e ele não conta no mostrador.
- **Mandar mensagem:** liga sozinho. Não há botão "ligar" (ver a mudança na parte "Faixa do
  chat").
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

- [x] **Retomar pela memória do Claude** ([D22](../decisoes/D22-conversa-continua-pelo-claude.md)).
      Saiu o `no-session-persistence` de `opcoes.py`. A medição 15 passou a conferir o contrário
      (a conversa é guardada), e os testes de `test_opcoes.py` acompanharam.
      **Mudou:** o código da conversa no Claude é o **id do próprio chat**, e não o `session_id`
      que o Claude devolve. Na primeira mensagem o adaptador cria a conversa com esse código
      (`session_id`); depois, retoma (`resume`). Antes de ligar, confere com o `get_session_info`
      do SDK se o Claude ainda guarda a conversa: se não guarda, cria de novo e a entrega diz
      `conversa_nova=True`. **Por quê:** o chat já nasce com tudo o que precisa para ser retomado
      (ideia do Pedro); o banco não ganha nada, e a porta não precisou do marcador opaco. Uma
      medição com o Claude de verdade (2026-10-21) confirmou: ele aceita o código escolhido, o
      `resume` continua na mesma conversa (lembrou o 42) e não faz cópia; criar com um código
      que já existe dá erro, por isso a conferência antes.
      **Mudou também:** `conversa_nova` passou a querer dizer "o agente não lembra de nada
      antes", e não "primeira mensagem do processo". Uma queda no meio da conversa agora também
      retoma (o teste `test_rn_s_34_reconexao_retoma_a_conversa` mudou junto).
      A pasta de trabalho do Claude é `claude/`, dentro da pasta de dados.
- [x] **Montagem:** `montar` cria o adaptador de sessão e o serviço de conversa, e
      `Programa.fechar` desliga os chats e chama `encerrar` antes de fechar o banco.
- [x] **Serviço de conversa** (`aplicacao/servicos/servico_de_conversa.py`, um por programa):
      guarda a sessão viva de cada chat (abre uma vez e reaproveita), a fila de mensagens de cada
      chat, grava as mensagens no banco (`inserir_mensagem`) e sabe quantas conexões estão
      abertas. É ele que a tela usa; a tela nunca fala direto com o adaptador.
- [x] **Tela do chat** (`interface/chat.py`): a conversa antiga ao abrir, o campo de digitação,
      a resposta em pedaços, a fila e o Esc.
      **Mudou:** o envio roda numa tarefa do serviço de conversa, e não num worker da Textual.
      **Por quê:** a tela redesenha o painel da tarefa (trocar de sessão, abrir a memória), e um
      worker preso a ele seria cancelado junto, o que para a porta é interromper a resposta. A
      tela só escuta o serviço.
- [x] **Faixa do chat** com o estado e o botão desligar.
      **Mudou:** não há botão "ligar"; a primeira mensagem liga. A porta ganhou `ligada()`, que
      diz se há processo de pé, para a faixa e o mostrador não contarem um processo que caiu.
      **Por quê:** decidido com o Pedro. O "ligar" abria um caso delicado no adaptador (o
      processo subindo sem ninguém esperando por ele) para ganhar só alguns segundos na
      primeira resposta; ficou no "Pode melhorar".
- [x] **Mostrador de conexões** na tela do ambiente. Ele também redesenha a árvore quando o
      orquestrador cria uma frente ou uma tarefa.
- [x] **Desligar ao sair:** sair do ambiente desliga os chats dele; fechar o programa desliga
      todos.
- [x] **Avisos:** falha do Claude e conversa não encontrada, cada um no seu chat. Ficam no banco
      como mensagens de papel "aviso", com um código; a frase em português é da tela
      (`frase_do_aviso`). Entrou mais um: a ação que o orquestrador pede e que é recusada
      aparece no chat dele.

## Como testar

O que o Pedro faz na tela e o que tem que acontecer. Ao lado de cada item, o teste automático que
confere. Os marcados `sdk_real` usam o Claude de verdade e gastam a assinatura
(`uv run pytest -m sdk_real`); os outros usam um Claude de mentira, roteirizado. Os testes de tela
estão em `tests/interface/test_chat.py`; os do serviço, em `tests/conversa/`. O Pedro conferiu
todos com as próprias mãos em 2026-10-21.

- [x] Mando "oi" no chat do orquestrador → a resposta aparece em pedaços e o mostrador diz 1.
      *Teste:* `test_mando_oi_e_a_resposta_aparece_em_pedacos_com_o_mostrador_em_1`; e o
      `sdk_real` `test_sdk_real_mando_oi_e_a_resposta_chega_com_uma_conexao`.
- [x] Mando 5 mensagens seguidas no mesmo chat (esperando cada resposta) → o mostrador continua
      em 1. *Teste:* `test_cinco_mensagens_seguidas_usam_um_processo_so`.
- [x] Mando duas mensagens sem esperar → a segunda espera e sai sozinha quando a primeira resposta
      acaba. *Teste:* `test_mensagem_mandada_durante_a_resposta_espera_na_fila`.
- [x] Aperto Esc no meio da resposta → ela para, fica "(interrompida)", e a mensagem da fila volta
      para o campo. *Teste:* `test_esc_interrompe_a_resposta_e_devolve_a_fila_ao_campo` e
      `test_interromper_marca_a_resposta_e_devolve_a_fila`; o processo morto já é conferido pela
      medição 16.
- [x] Mando mensagem na tarefa A e, enquanto ela responde, mando outra na tarefa B → as duas
      respondem, cada uma no seu chat, e a tela não trava. *Teste:*
      `test_dois_chats_respondem_ao_mesmo_tempo`; a medição 10 já confere dois processos de
      verdade.
- [x] Clico em "desligar" → o mostrador desce 1 e o chat mostra "pronto para conversar"; mando
      outra mensagem → ele liga de novo. *Teste:*
      `test_desligar_volta_a_pronto_e_a_mensagem_seguinte_liga_de_novo` e
      `test_desligar_e_mandar_de_novo_retoma_sem_aviso`.
- [x] Saio do ambiente com chats ligados → o mostrador vai a 0. *Teste:*
      `test_saio_do_ambiente_com_chats_ligados_e_o_mostrador_vai_a_zero`.
- [x] Fecho o programa → nenhum processo do Claude fica rodando. *Teste:* `sdk_real`
      `test_sdk_real_fecho_o_programa_e_nenhum_processo_fica`; com o Claude roteirizado,
      `test_fechar_o_programa_desliga_todos_os_chats`.
- [x] Fecho o programa, abro de novo e abro o chat → as mensagens estão lá. *Teste:*
      `test_fecho_o_programa_abro_de_novo_e_as_mensagens_estao_la` e
      `test_reabrir_o_programa_traz_a_conversa_do_banco`.
- [x] Digo "meu número da sorte é 42", fecho o programa, abro e pergunto o número → ele responde
      42. *Teste:* `sdk_real` `test_sdk_real_o_agente_lembra_do_numero_depois_de_reabrir`.
- [x] A conversa do Claude sumiu → aparece o aviso, a conversa recomeça do zero e o texto antigo
      continua na tela. *Teste:* `test_conversa_que_o_claude_perdeu_avisa_e_recomeca_do_zero`
      (serviço) e `test_d22_conversa_que_o_claude_nao_guarda_mais_recomeca_do_zero` (adaptador).
- [x] O Claude falha num chat → o aviso aparece só nele, e outro chat continua conversando.
      *Teste:* `test_falha_num_chat_avisa_so_nele_e_o_outro_continua`.
- [x] O orquestrador pede uma ação que precisa de confirmação → ela é recusada e o chat dele
      avisa. *Teste:* `test_acao_que_o_orquestrador_pede_e_recusada_e_o_chat_avisa`.

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
- **Ligar o chat antes da primeira mensagem:** hoje não há botão "ligar"; a primeira mensagem
  liga — por quê: a primeira resposta viria alguns segundos mais rápido. Pede cuidado no
  adaptador, com o processo subindo sem ninguém esperando por ele.
- **Redesenhar a conversa inteira a cada pedaço:** hoje a tela reescreve o chat todo a cada
  pedaço da resposta — por quê: em conversas longas, redesenhar só o fim fica mais leve.
- **Conversas paradas há mais de 30 dias:** o Claude apaga sozinho as conversas guardadas que
  ficam 30 dias sem uso (o padrão de `cleanupPeriodDays`), e o chat recomeça do zero, com o aviso.
  Fica o padrão por enquanto — por quê: dá para aumentar o prazo nas opções do adaptador, se um
  mês parado for comum.

## Ao terminar

- [x] Rodar os testes automáticos (`uv run pytest`).
- [x] Rodar os testes com o Claude de verdade (`uv run pytest -m sdk_real`).
- [x] Acrescentar a funcionalidade em `docs/funcionalidades.md`.
- [x] Mudar o estado deste card para "pronto".
- [x] Fazer o commit.
