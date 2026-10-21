# Anotar uma informação na memória da tarefa

Estado: a revisar
De onde veio: história de usuário US-04, escrita na fase do AI-DLC (tag `aidlc-congelado`).

Quando um agente (ou eu) descobre algo importante numa tarefa, anota na memória da tarefa. A
primeira anotação sob um assunto novo funciona sempre, sem erro. Anotar de novo sob o mesmo
assunto não apaga a anterior: as duas ficam, cada uma com quem escreveu e o que escreveu.

O que já existe no código: `Memoria.anotar` em `src/fishingrod/dominio/memoria.py`, a operação
`anotar_memoria` em `src/fishingrod/aplicacao/servicos/servico_de_ambiente.py` e o comando
`/anotar_memoria` no catálogo de ações. A memória é salva no banco.

Ver também a decisão [D17](../decisoes/D17-memoria-e-quadro-branco.md).
