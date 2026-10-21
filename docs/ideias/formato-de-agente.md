# Formato próprio de agente do FishingRod

Estado: ideia
De onde veio: backlog de ideias do Pedro (item 1 do antigo `docs/backlog-de-ideias/back-log.md`).

O FishingRod vai ter um formato próprio para criar agentes, pensado para que eles fiquem mais
inteligentes dentro do software. Um agente inteiro mora numa pasta só: uma pasta é um agente.

Material de apoio: https://agentskills.io/specification

Rascunho da estrutura da pasta:

```text
agente-fishing-rod/
├── AGENTE.md               # Obrigatório: dados do agente + instruções
├── REFERENCIAS_WIKI        # Obrigatório: links de referência para a wiki ([[wiki-referencia]])
├── conhecimentos/          # Opcional: conhecimentos do agente
│   └── index.md            # Obrigatório: sumário do conhecimento + descrição
└── resultados-validados/   # Obrigatório: resultados validados pelo usuário
```
