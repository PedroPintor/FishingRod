# Ver a conversa antiga depois de reabrir

Estado: ideia
De onde veio: história de usuário US-06, escrita na fase do AI-DLC (tag `aidlc-congelado`).

Fecho o programa, volto dias depois, abro um chat antigo e vejo tudo o que foi dito ali. Cada
chat mostra só a própria conversa, sem misturar com a de outro agente.

O que já existe no código: o banco tem uma tabela só para as mensagens (`inserir_mensagem` e
`listar_mensagens` em `src/fishingrod/adaptadores/persistencia/repositorio_sqlite.py`). Falta
gravar as mensagens durante a conversa e mostrá-las na tela.
