# D12 — Wiki em dois níveis, com index.md gerado e links [[...]]

Status: revisada
Data do status: 2026-10-20

## O que é

A wiki tem só dois níveis. Cada **assunto** é uma pasta (por exemplo, `oferta/`). Cada
**característica** desse assunto é um arquivo dentro da pasta (por exemplo, `oferta/preco.md`).
Não há pasta dentro de pasta. Um arquivo `index.md`, gerado pelo programa, lista os assuntos, as
características e uma descrição de cada uma. As páginas se ligam com links no formato
`[[assunto/caracteristica]]`. No código, assunto se chama "entidade" e característica, "propriedade".

## Por quê

Travar a profundidade em dois níveis impede que a wiki vire um labirinto de pastas e apodreça com
o uso. O `index.md` é o mapa: lendo só ele, um agente sabe o que existe e onde procurar (ver
[D14](D14-busca-comeca-pelo-index.md)). Os links ligam ideias de assuntos diferentes. A estrutura
inicial de cada wiki é definida por quem cria o ambiente, sem nenhum vocabulário de domínio fixo
no código.

## Onde aparece no código

- `src/fishingrod/adaptadores/wiki/indice.py` (gera o `index.md`)
- `src/fishingrod/adaptadores/wiki/wiki_de_arquivos.py`
- `src/fishingrod/aplicacao/caminho_wiki.py` (o caminho `assunto/caracteristica`)
- `src/fishingrod/aplicacao/esquema_wiki.py` (a estrutura inicial)
