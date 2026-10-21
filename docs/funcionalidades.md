# Funcionalidades

O que o FishingRod já faz. Cada linha diz o que o usuário pode (ou vai poder) fazer.

## Na tela

Ainda nada: o FishingRod não tem tela. A primeira funcionalidade a entrar aqui vem do card 001
(ideia [primeira tela](ideias/primeira-tela.md)).

## Pronto no código, ainda sem tela

Funciona e tem testes automáticos, mas ainda não há como usar abrindo o programa.

- Conversar com o Claude usando a assinatura, sem chave de API, e com a resposta chegando aos
  pedaços enquanto é escrita. (`src/fishingrod/adaptadores/sessao/`)
- Criar um ambiente, que já nasce com a sua wiki. (`ServicoDeAmbiente.criar_ambiente`)
- Ver a lista dos ambientes, do mais recentemente mexido para o mais antigo.
  (`ServicoDeAmbiente.listar_ambientes`)
- Apagar um ambiente com tudo o que há dentro, inclusive a wiki. (`ServicoDeAmbiente.apagar_ambiente`)
- Criar frentes dentro de um ambiente. (`ServicoDeAmbiente.criar_frente`)
- Criar tarefas dentro de uma frente; cada tarefa já vem com o chat do orquestrador.
  (`ServicoDeAmbiente.criar_tarefa`)
- Fechar e reabrir: ambientes, frentes, tarefas e wiki continuam lá, guardados no banco local e
  em pastas no disco. (`src/fishingrod/adaptadores/persistencia/`)
- Guardar a wiki em pastas de markdown, com um `index.md` que lista os assuntos e as páginas.
  (`src/fishingrod/adaptadores/wiki/`)
- Usar comandos com `/` (criar frente, tarefa, chat, etapa, concluir etapa, anotar na memória),
  que o orquestrador também pode usar, sempre pedindo confirmação. (`src/fishingrod/aplicacao/catalogo/`)
