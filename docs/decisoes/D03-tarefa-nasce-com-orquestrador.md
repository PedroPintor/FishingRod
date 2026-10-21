# D03 — Toda tarefa nasce com um chat do orquestrador, no máximo um

Status: revisada
Data do status: 2026-10-21

## O que é

Quando uma tarefa é criada, ela já vem com um chat aberto com o orquestrador, o agente principal
do software. Quem cria a tarefa não escolhe esse agente.

Desde 2026-10-21 os chats moram nas sessões da tarefa ([D21](D21-sessoes-dentro-da-tarefa.md)), e a
regra passou a valer por sessão: a tarefa nasce com uma sessão, toda sessão nasce com o chat do
orquestrador, e uma sessão nunca tem dois chats de orquestrador; os outros chats são com outros
agentes.

## Por quê

O orquestrador é a porta de entrada de cada tarefa: é com ele que o usuário planeja e é ele quem
tem mais ferramentas para mexer no software (nas palavras do Pedro, "o orquestrador pode mais").
Ter exatamente um por tarefa evita dúvida sobre quem coordena. A regra de "no máximo um" já
existia no código antigo e foi preservada.

## Onde aparece no código

- `src/fishingrod/dominio/tarefa.py` (`criar_sessao`)
- `src/fishingrod/dominio/sessao.py` (o "no máximo um")
- `src/fishingrod/dominio/agente.py` (o papel `ORQUESTRADOR`)
- `src/fishingrod/aplicacao/servicos/servico_de_ambiente.py` (`criar_tarefa`, `criar_sessao`, `criar_chat`)
