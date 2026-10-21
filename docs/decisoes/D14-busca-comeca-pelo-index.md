# D14 — A busca na wiki começa sempre pelo index.md

Status: revisada
Data do status: 2026-10-20

## O que é

Para achar algo na wiki, o agente lê primeiro o `index.md`. Lá estão os assuntos, a lista de
características de cada um e uma descrição do conteúdo de cada página. A partir disso, o agente
abre as páginas que lhe interessam e segue os links que for encontrando.

## Por quê

É a busca mais simples que funciona, nas palavras do Pedro: "a funcionalidade de busca seria fazer
o agente ler o index.md e deixar ele ler as páginas que ele foi encontrando". Não precisa de
índice de busca à parte nem de banco. A qualidade da busca depende de as descrições no
`index.md` serem boas; esse é um risco conhecido, para melhorar com o uso.

## Onde aparece no código

- `src/fishingrod/adaptadores/wiki/indice.py` (monta o `index.md` com as descrições)
- `src/fishingrod/adaptadores/wiki/wiki_de_arquivos.py` (`renderizar_index`, `ler`, `listar`)
- A ferramenta de busca do agente ainda não existe.
