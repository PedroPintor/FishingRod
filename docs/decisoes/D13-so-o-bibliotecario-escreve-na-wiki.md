# D13 — Só o bibliotecário escreve na wiki, e toda escrita é uma proposta revisada pelo usuário

Status: a revisar
Data do status: 2026-10-20

## O que é

Nenhum agente nem tela escreve direto na wiki. Quem escreve é o bibliotecário, um agente especial
que cuida dela, e só por ferramentas próprias. Toda escrita é primeiro uma proposta: o usuário vê
o texto e aprova ou recusa antes de qualquer coisa ser gravada.

## Por quê

Ter um ponto único de entrada na wiki concentra num lugar só as regras de formato, a validação e a
segurança (por exemplo, impedir que um caminho escape da pasta da wiki). O conteúdo que chega à
wiki pode trazer instruções escondidas dirigidas à IA, mesmo vindo do próprio usuário; a revisão
humana antes de gravar é uma das defesas. O Pedro registrou: mesmo simples, "primeiro propor para
depois escrever" já agrega valor.

Revisar junto com a ideia US-14 ([revisar antes de salvar na wiki](../ideias/revisar-antes-de-salvar-na-wiki.md)).

## Onde aparece no código

- `src/fishingrod/aplicacao/portas/wiki.py` (`PropostaWiki`, `escrever_proposta`)
- `src/fishingrod/adaptadores/wiki/wiki_de_arquivos.py` (recusa caminho fora da raiz)
- O agente bibliotecário e a tela de revisão ainda não existem.
