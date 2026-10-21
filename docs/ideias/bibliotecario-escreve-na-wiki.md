# O bibliotecário escreve na wiki por mim

Estado: ideia
De onde veio: história de usuário US-13, escrita na fase do AI-DLC (tag `aidlc-congelado`).

Quando descubro algo que quero guardar (um critério novo de cliente ideal, um conceito aprendido
em aula), peço ao bibliotecário, um agente especial que cuida da wiki. Ele salva o conteúdo no
assunto certo e no formato da wiki daquele ambiente, sem eu precisar saber como a wiki é
organizada por dentro.

O que já existe no código: a wiki em arquivos já sabe gravar uma proposta de páginas novas
(`escrever_proposta` em `src/fishingrod/adaptadores/wiki/wiki_de_arquivos.py`) e refazer o
`index.md`. O agente bibliotecário ainda não existe.

Ver também as decisões [D13](../decisoes/D13-so-o-bibliotecario-escreve-na-wiki.md) e
[D14](../decisoes/D14-busca-comeca-pelo-index.md).
