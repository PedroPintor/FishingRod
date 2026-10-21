# D10 — Banco SQLite local: o ambiente salvo inteiro, as conversas à parte

Status: revisada
Data do status: 2026-10-20

## O que é

Os dados ficam num arquivo SQLite (`fishingrod.db`) na pasta de dados do sistema. Cada ambiente é
salvo inteiro, como um único documento (frentes, tarefas, chats e etapas juntos). As mensagens
das conversas ficam numa tabela à parte, porque só crescem. A memória das tarefas também tem
tabela própria.

## Por quê

O SQLite já vem com o Python: nenhuma dependência nova. Salvar o ambiente inteiro de uma vez é
simples e permite perceber quando duas gravações disputam o mesmo ambiente (cada gravação conta
uma versão). As conversas crescem sem parar e só recebem coisas novas no fim; regravar tudo a cada
mensagem seria desperdício, por isso ficam numa tabela separada. O resto do código só conversa com
o banco por uma interface em palavras do domínio ("salvar ambiente", "carregar ambiente"), sem SQL.

## Onde aparece no código

- `src/fishingrod/aplicacao/portas/persistencia.py` (a interface)
- `src/fishingrod/adaptadores/persistencia/` (`repositorio_sqlite.py`, `esquema.py`, `mapeamento.py`, `localizacao.py`)
