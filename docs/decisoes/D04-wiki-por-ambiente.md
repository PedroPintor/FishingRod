# D04 — Cada ambiente tem a própria wiki, criada junto com ele

Status: revisada
Data do status: 2026-10-20

## O que é

Todo ambiente tem uma wiki só dele, criada no mesmo momento em que o ambiente é criado, mesmo que
comece quase vazia. Não existe ambiente sem wiki, e a wiki de um ambiente não se mistura com a de
outro.

## Por quê

A aposta central do produto é que o contexto acumulado é o que tem valor: um ambiente que guarda
o que se aprendeu faz cada trabalho futuro começar adiantado. Por isso o lugar para guardar
precisa existir desde o primeiro dia, sem configuração à parte. A wiki é criada antes de o
ambiente ser salvo no banco: se algo falhar no meio, o pior que sobra é uma pasta sem uso, nunca
um ambiente apontando para uma wiki que não existe.

## Onde aparece no código

- `src/fishingrod/aplicacao/servicos/servico_de_ambiente.py` (`criar_ambiente`)
- `src/fishingrod/dominio/raiz_wiki.py` (o endereço da wiki guardado no ambiente)
- `src/fishingrod/adaptadores/wiki/wiki_de_arquivos.py`
