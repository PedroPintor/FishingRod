# D11 — A wiki são pastas de markdown no disco; os arquivos são a verdade

Status: a revisar
Data do status: 2026-10-20

## O que é

A wiki de cada ambiente é uma pasta comum no disco, com arquivos markdown dentro. O que está nos
arquivos é a versão oficial da wiki. O banco não guarda conteúdo nem índice da wiki: só sabe onde
fica a pasta de cada ambiente.

## Por quê

Arquivos markdown podem ser abertos e lidos por qualquer pessoa ou programa, e um agente consegue
navegar por eles sem ferramenta especial de busca. Guardar a wiki em um lugar só (os arquivos)
elimina o risco de o banco e o disco discordarem. A ideia segue o estilo do Obsidian.

## Onde aparece no código

- `src/fishingrod/aplicacao/portas/wiki.py` (a interface)
- `src/fishingrod/adaptadores/wiki/wiki_de_arquivos.py`
- `src/fishingrod/dominio/raiz_wiki.py` (a única coisa da wiki que o ambiente guarda)
