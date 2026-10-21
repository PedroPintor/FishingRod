# Funcionalidades

O que o FishingRod já faz. Cada linha diz o que o usuário pode (ou vai poder) fazer.

## Na tela

Abrir com `uv run fishingrod`. Veio do [card 001](cards/001-primeira-tela.md).

- Ver a lista dos meus ambientes, do mais mexido para o mais antigo, e criar, entrar e apagar um
  ambiente com cliques. Apagar mostra um aviso em maiúsculas e pede confirmação.
- Criar com nome vazio não deixa: a janela avisa "precisa de um nome".
- Dentro do ambiente: criar frentes e tarefas e vê-las numa árvore.
- Abrir tarefas em abas; em cada tarefa, escolher uma sessão ou criar uma nova, e ver as abas dos
  chats da sessão; abrir um chat novo com um agente da lista pelo botão "+ chat" (ainda sem
  conversa com a IA); ver a memória da sessão pelo botão "memória".
- Ver a wiki do ambiente (o `index` e as páginas) e a lista de agentes.
- Voltar para a lista de ambientes e entrar em outro.
- Fechar e abrir de novo: está tudo lá.

## Pronto no código, ainda sem tela

Funciona e tem testes automáticos, mas ainda não há como usar abrindo o programa.

- Conversar com o Claude usando a assinatura, sem chave de API, e com a resposta chegando aos
  pedaços enquanto é escrita. (`src/fishingrod/adaptadores/sessao/`)
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
