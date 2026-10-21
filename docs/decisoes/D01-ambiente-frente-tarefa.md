# D01 — Ambiente → Frente → Tarefa

Status: revisada
Data do status: 2026-10-20

## O que é

O trabalho é organizado em três níveis. O **ambiente** é o lugar inteiro (por exemplo, "Nexo
Aquisição" ou "Meus estudos do semestre"). Dentro dele há **frentes**, as áreas de atuação. Dentro
de cada frente há **tarefas**. É na tarefa que o trabalho acontece: ela guarda os chats com os
agentes, as etapas (o passo a passo) e a memória compartilhada pelos agentes.

## Por quê

Vem do jeito de trabalhar descrito na descoberta (`docs/produto/`): uma meta, áreas de atuação e
trabalhos concretos dentro delas. O código antigo já tinha essa forma (`Ambiente → Projeto →
Sessao`) e ela foi mantida. O que mudou foi tirar dos dados a responsabilidade de rotear comandos:
isso passou para a camada de aplicação. As frentes pertencem ao ambiente, não à wiki (o Pedro
corrigiu isso em 2026-08-25).

## Onde aparece no código

- `src/fishingrod/dominio/ambiente.py`
- `src/fishingrod/dominio/frente.py`
- `src/fishingrod/dominio/tarefa.py`
- `src/fishingrod/dominio/chat.py`, `src/fishingrod/dominio/etapa.py`, `src/fishingrod/dominio/memoria.py`
