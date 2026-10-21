# Eu escolho a estrutura da wiki do meu ambiente

Estado: ideia
De onde veio: história de usuário US-09, escrita na fase do AI-DLC (tag `aidlc-congelado`).

Quando crio um ambiente, escolho os assuntos iniciais da wiki, com o vocabulário do meu
trabalho. O João, num ambiente de aquisição de clientes, poderia ter `ICP`, `oferta`,
`narrativa`, `provas`. O Pedro, num ambiente de estudos, poderia ter `conceitos por disciplina`,
`resumos`, `dúvidas recorrentes`. O software não impõe a estrutura de nenhum domínio.

O que já existe no código: `EsquemaWiki` em `src/fishingrod/aplicacao/esquema_wiki.py` descreve
os assuntos iniciais, e `criar_ambiente` cria a wiki a partir dele. Falta a tela onde eu escolho.

Ver também a decisão [D12](../decisoes/D12-wiki-em-dois-niveis.md).
