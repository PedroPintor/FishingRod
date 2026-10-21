# Descobrir as etapas de uma tarefa conversando com o orquestrador

Estado: ideia
De onde veio: história de usuário US-17, escrita na fase do AI-DLC (tag `aidlc-congelado`).

Crio uma tarefa sem saber ainda o passo a passo e converso com o orquestrador sobre ela. No fim
da conversa, a tarefa tem etapas definidas (por exemplo: ler o material → aprofundar → fazer
exercícios → anotar no mapa mental). Se eu já chego com o método pronto, o orquestrador só
registra o que eu já tinha em mente, sem me fazer redescobrir.

O que já existe no código: a operação `criar_etapa` no serviço de ambiente e o comando
`/criar_etapa` no catálogo de ações. O orquestrador já consegue usar essa ação como ferramenta,
sempre pedindo a minha confirmação (ver [D15](../decisoes/D15-orquestrador-age-com-confirmacao.md)).
Falta a conversa na tela.
