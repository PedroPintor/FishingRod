# D17 — A memória da sessão é um quadro branco entre os agentes

Status: revisada
Data do status: 2026-10-21

## O que é

Cada sessão de uma tarefa tem uma memória compartilhada por todos os chats e agentes dela. Até
2026-10-21 a memória era da tarefa; com as sessões ([D21](D21-sessoes-dentro-da-tarefa.md)), passou
a ser de cada sessão, e uma sessão nova começa com a memória limpa. Cada anotação guarda
quem escreveu, o que escreveu e quando. Anotar de novo sob o mesmo assunto não apaga a anotação
anterior: as duas ficam.

## Por quê

O valor está na comunicação entre agentes, não dentro de um só. O caso que define o desenho: o
orquestrador manda um agente fazer algo em outro chat; esse agente anota o que decidiu; quando o
usuário volta ao orquestrador, ele já sabe o que foi feito, sem ninguém copiar e colar. Por isso a
anotação carrega autor, e a memória precisa ser lida de novo a cada conversa, para um chat ver o que
o outro escreveu depois. Não é um rascunho de raciocínio de um agente: isso já existe nas próprias
mensagens do chat.

## Onde aparece no código

- `src/fishingrod/dominio/memoria.py`
- `src/fishingrod/aplicacao/servicos/servico_de_ambiente.py` (`anotar_memoria`)
- `src/fishingrod/adaptadores/persistencia/repositorio_sqlite.py` (`anotar`)
