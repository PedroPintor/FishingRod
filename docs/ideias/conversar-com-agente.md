# Conversar com um agente de verdade dentro de uma tarefa

Estado: ideia
De onde veio: história de usuário US-01, escrita na fase do AI-DLC (os documentos daquela fase estão na tag `aidlc-congelado`).

Dentro de uma tarefa, escrevo uma mensagem para um agente e recebo a resposta de uma IA de
verdade, não um texto de teste. Cada agente tem o seu chat: a resposta aparece no chat certo e
não se mistura com a conversa de outro agente da mesma tarefa.

O que já existe no código: a conversa com o Claude funciona pelo adaptador de sessão
(`src/fishingrod/adaptadores/sessao/`), com a resposta chegando em pedaços enquanto é escrita.
Falta ligar isso a uma tarefa e a uma tela.
