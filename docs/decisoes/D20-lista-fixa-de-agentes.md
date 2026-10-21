# D20 — Os agentes com que se pode abrir chat são uma lista fixa do software

Status: revisada
Data do status: 2026-10-20

## O que é

Abrir um chat numa tarefa só é possível com um agente de uma lista fechada, definida no próprio
software (por enquanto, a ideia é o bibliotecário). O pedido é feito pelo nome do agente; um nome
fora da lista é recusado, venha da tela ou de um agente. O orquestrador não está nessa lista,
porque cada tarefa já nasce com o seu (ver [D03](D03-tarefa-nasce-com-orquestrador.md)).

## Por quê

Se o orquestrador pudesse abrir chat com qualquer agente, poderia criar para si um agente com mais
poder do que deveria. Verificar a lista num lugar só (o serviço de ambiente) fecha esse caminho
para todo mundo, inclusive para a tela. Criar agentes novos é outra ideia, para depois
([criar agente com o rod-maker](../ideias/criar-agente-com-rod-maker.md)).

## Onde aparece no código

- `src/fishingrod/aplicacao/servicos/servico_de_ambiente.py` (`agentes_de_chat`, `criar_chat`, `AgenteDesconhecido`)
- A lista em si é montada por quem liga o programa, que ainda não existe.
