# Executar uma etapa da tarefa pelo chat com um agente

Estado: ideia
De onde veio: história de usuário US-19, escrita na fase do AI-DLC (tag `aidlc-congelado`).

Quando uma etapa é feita por um agente (por exemplo, "escrever o texto do anúncio"), abro o chat
dele e ele produz o resultado ali dentro. Quando a etapa é feita por mim (por exemplo, "assistir
à aula"), confirmo que fiz e ela fica marcada como concluída.

O que já existe no código: a operação `concluir_etapa` no serviço de ambiente e o comando
`/concluir_etapa` no catálogo de ações. Cada etapa sabe se quem a executa é um agente ou o
usuário (`src/fishingrod/dominio/etapa.py`).
