# Funcionalidades

O que o FishingRod já faz. Cada linha diz o que o usuário pode (ou vai poder) fazer.

## Na tela

Abrir com `uv run fishingrod`. Veio do [card 001](cards/001-primeira-tela.md).

- Ver a lista dos meus ambientes, do mais mexido para o mais antigo, e criar, entrar e apagar um
  ambiente com cliques. Apagar mostra um aviso em maiúsculas e pede confirmação.
- Criar com nome vazio não deixa: a janela avisa "precisa de um nome".
- Dentro do ambiente: criar frentes e tarefas e vê-las numa árvore.
- Abrir tarefas em abas; em cada tarefa, escolher uma sessão ou criar uma nova, e ver as abas dos
  chats da sessão; abrir um chat novo com um agente da lista pelo botão "+ chat".
- Voltar para a lista de ambientes e entrar em outro.
- Fechar e abrir de novo: está tudo lá.

### Entender o agente: o painel de explicação

Veio do [card 003](cards/003-interface-em-areas-e-ficha-do-agente.md).

- A lateral mostra só frentes e tarefas, e a área de trabalho só abre tarefas.
- Em cada tarefa, o botão "explicar" abre e fecha, à direita do chat, o painel de explicação, com
  três abas:
  - **ficha:** a ficha do agente do chat que está na frente — nome, papel, modelo, esforço de
    raciocínio, ferramentas, ferramentas da máquina e instruções —, tirada do que está
    configurado de verdade. Trocar de chat troca a ficha. Só para ler.
  - **memória:** o que os agentes da sessão anotaram uns para os outros, atualizado sozinho.
  - **wiki:** a árvore da wiki do ambiente; clicar no `index` ou numa página mostra o conteúdo ali
    mesmo.
- Cada tarefa tem o seu painel. Abrir, fechar ou trocar de aba nele não interrompe a resposta de
  nenhum agente e não tira o cursor do campo de digitação.

### Conversar com o agente

Veio do [card 002](cards/002-conversar-com-o-agente.md).

- Conversar no chat com o agente pela assinatura do Claude, sem chave de API, vendo a resposta
  chegar aos pedaços enquanto é escrita.
- Cada chat usa um só processo do Claude: ele liga na primeira mensagem e continua de pé entre
  uma mensagem e outra. Chats diferentes conversam ao mesmo tempo, sem travar a tela.
- Ver no topo do ambiente quantas conexões com o Claude estão abertas, e na faixa de cada chat se
  ele está pronto, ligado ou respondendo.
- Mandar mensagem enquanto o agente responde: ela espera numa fila e sai sozinha depois.
- Apertar Esc para interromper a resposta: o que já apareceu fica, marcado "(interrompida)", e as
  mensagens da fila voltam para o campo de digitação.
- Desligar um chat pelo botão "desligar"; sair do ambiente desliga os chats dele, e fechar o
  programa desliga todos. Nenhum processo do Claude fica para trás.
- Fechar e abrir de novo: a conversa continua na tela, e o agente lembra dela (pela memória do
  próprio Claude). Se o Claude não tiver mais a conversa, o chat avisa e recomeça do zero.
- Uma falha do Claude (fora do ar, limite da assinatura, sem login) aparece como aviso só naquele
  chat; o resto do programa continua.
- O orquestrador pode pedir ações (criar frente, tarefa…), mas, enquanto confirmar na tela não
  existe, toda ação que pede confirmação é recusada, e o chat avisa.

## Pronto no código, ainda sem tela

Funciona e tem testes automáticos, mas ainda não há como usar abrindo o programa.

- Criar um ambiente, que já nasce com a sua wiki. (`ServicoDeAmbiente.criar_ambiente`)
- Ver a lista dos ambientes, do mais recentemente mexido para o mais antigo.
  (`ServicoDeAmbiente.listar_ambientes`)
- Apagar um ambiente com tudo o que há dentro, inclusive a wiki. (`ServicoDeAmbiente.apagar_ambiente`)
- Criar frentes dentro de um ambiente. (`ServicoDeAmbiente.criar_frente`)
- Criar tarefas dentro de uma frente; cada tarefa já vem com uma sessão, e nela o chat do
  orquestrador. (`ServicoDeAmbiente.criar_tarefa`)
- Abrir sessões novas numa tarefa, cada uma com o seu chat do orquestrador e a sua memória.
  (`ServicoDeAmbiente.criar_sessao`)
- Fechar e reabrir: ambientes, frentes, tarefas e wiki continuam lá, guardados no banco local e
  em pastas no disco. (`src/fishingrod/adaptadores/persistencia/`)
- Guardar a wiki em pastas de markdown, com um `index.md` que lista os assuntos e as páginas.
  (`src/fishingrod/adaptadores/wiki/`)
- Usar comandos com `/` (criar frente, tarefa, sessão, chat, etapa, concluir etapa, anotar na
  memória), que o orquestrador também pode usar, sempre pedindo confirmação; abrir sessão é só do
  usuário. (`src/fishingrod/aplicacao/catalogo/`)
