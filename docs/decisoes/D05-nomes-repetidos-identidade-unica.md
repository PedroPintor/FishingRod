# D05 — Nomes repetidos são permitidos; por baixo, cada coisa tem uma identidade única

Status: revisada
Data do status: 2026-10-20

## O que é

Duas frentes (ou tarefas, ou chats) podem ter o mesmo nome. O que distingue uma da outra é uma
identidade única, criada no momento em que a coisa nasce e que nunca muda. Essa identidade é um
UUIDv7: um código aleatório que também carrega a hora de criação.

## Por quê

No código antigo, as coisas eram achadas pela posição numa lista ou pelo nome. Posição muda e
nome também muda (o código antigo já tinha um comando para renomear chat). Com uma identidade fixa, renomear não
quebra nenhuma referência. Proibir nomes repetidos bloquearia o usuário sem motivo técnico. O
UUIDv7 foi escolhido porque é ordenável por tempo (ajuda a listar mensagens na ordem) e porque o
Python 3.14 já o traz pronto, sem precisar de biblioteca extra. Foi por isso que o projeto passou
a usar o Python 3.14.

## Onde aparece no código

- `src/fishingrod/dominio/identidade.py`
- os construtores em `src/fishingrod/dominio/` (`ambiente.py`, `frente.py`, `tarefa.py`, `chat.py`, `etapa.py`)
