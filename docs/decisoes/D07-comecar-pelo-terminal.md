# D07 — Começar com uma interface no terminal (Textual)

Status: revisada
Data do status: 2026-10-20

## O que é

A primeira interface do FishingRod é no terminal, feita com a biblioteca Textual. Esta decisão é
sobre **por onde começar**, não um limite: o software pode ganhar depois uma interface de app ou
web. O núcleo já não depende da tela, o que mantém essa porta aberta.

## Por quê

O usuário de validação (o João) trabalha no terminal por preferência, usando o Claude Code. A
maquete que ele fez (`docs/produto/maquetes/interface-v3-nexus.html`) é, na estrutura, uma tela de
terminal desenhada em HTML: três regiões fixas, barra de status e comandos com `/`. Uma interface
no terminal valida a ideia mais rápido e mais barato do que uma web. A maquete serve de referência
de layout e navegação, não de visual.

## Onde aparece no código

- `src/fishingrod/interface/` (ainda vazia: a tela não foi construída)
- `tui.py` na raiz é o protótipo antigo, mantido como referência
- A Textual ainda não está em `pyproject.toml`: entra quando a primeira tela for construída
