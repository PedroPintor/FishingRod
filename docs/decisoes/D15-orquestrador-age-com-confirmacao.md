# D15 — O orquestrador faz ações no software, sempre com a confirmação do usuário

Status: revisada
Data do status: 2026-10-20

## O que é

O orquestrador pode fazer as mesmas ações que o usuário faz (criar frente, tarefa, chat, etapa,
concluir etapa, anotar na memória), usando-as como ferramentas. Toda ação pedida por ele para e
pergunta ao usuário. Com "sim", executa e o agente recebe o resultado; com "não", recebe
"recusada". É uma pergunta por ação, sem "aprovar tudo".

## Por quê

O orquestrador é o agente principal e terá muitas ferramentas, mas o que uma IA pede não deve
virar efeito no software sem o usuário ver. O agente espera a resposta (em vez de seguir em
frente) para saber, na mesma conversa, se a ação aconteceu; senão tenderia a pedir de novo e
duplicar etapas. Se algo der errado na pergunta, nada é executado. Foi testado com o Claude de
verdade que um agente consegue esperar a confirmação sem a ferramenta ser cortada por tempo.

## Onde aparece no código

- `src/fishingrod/aplicacao/catalogo/catalogo.py` e `registro.py` (as ações e quem pode chamá-las)
- `src/fishingrod/aplicacao/portas/confirmacao.py` (a pergunta ao usuário)
- `src/fishingrod/aplicacao/ferramentas/acoes.py` (as ações viram ferramentas do agente)
- `src/fishingrod/adaptadores/sessao/opcoes.py` (`TEMPO_LIMITE_DE_FERRAMENTA_MS`)
