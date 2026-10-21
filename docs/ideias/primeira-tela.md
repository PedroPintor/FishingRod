# Primeira tela

Estado: ideia
De onde veio: conversa do Pedro com a IA, de 2026-10-15 a 2026-10-20.

Objetivo: abro o FishingRod, vejo meus ambientes, crio um, entro nele, crio frentes e tarefas e
vejo tudo numa árvore; fecho, abro de novo e está tudo lá.

A interface é no terminal (ver a decisão [D07](../decisoes/D07-comecar-pelo-terminal.md)).

Usa o que já existe no código:

- `ServicoDeAmbiente` (`src/fishingrod/aplicacao/servicos/servico_de_ambiente.py`): criar,
  listar, abrir e apagar ambientes; criar frentes e tarefas.
- `RepositorioSQLite` (`src/fishingrod/adaptadores/persistencia/`): guarda tudo no banco local.
- `WikiDeArquivos` (`src/fishingrod/adaptadores/wiki/`): cria a wiki junto com o ambiente.
- A pasta de dados do sistema (`src/fishingrod/adaptadores/persistencia/localizacao.py`): onde o
  banco e as wikis ficam na máquina.

Fica de fora: o chat com o Claude, os comandos com `/` e o bibliotecário.

Rascunho de como testar:

- [ ] Crio um ambiente e ele aparece na lista.
- [ ] Crio uma frente e uma tarefa e as vejo na árvore.
- [ ] Fecho o programa, abro de novo e está tudo lá.
- [ ] Dois ambientes não se misturam.
- [ ] Nome vazio mostra uma mensagem, sem quebrar o programa.
- [ ] Apagar um ambiente avisa o que vai acontecer e pede confirmação.

Esta ideia será aprofundada numa sessão de chat, que vai gerar o card 001.
