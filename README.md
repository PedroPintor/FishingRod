# FishingRod

O FishingRod é um ambiente de trabalho com IA: um lugar onde uma pessoa monta a própria estrutura
de trabalho (ambientes, frentes, tarefas e uma wiki) e trabalha conversando com agentes de IA.
A aposta é que o contexto acumulado na wiki faz cada trabalho futuro começar adiantado.

## Instalar

Precisa do [uv](https://docs.astral.sh/uv/). Na pasta do projeto:

```bash
uv sync
```

## Rodar os testes

```bash
uv run pytest
```

Os testes marcados `sdk_real` usam o Claude de verdade e gastam a sua assinatura. Eles ficam fora
do comando acima e só rodam assim:

```bash
uv run pytest -m sdk_real
```

## Abrir o programa

Ainda não há tela para abrir. O núcleo já funciona e está testado; a primeira tela é a próxima
coisa a ser construída (ver `docs/ideias/primeira-tela.md`).

## Onde está cada coisa em `docs/`

| Pasta | O que tem |
|---|---|
| `docs/produto/` | A descoberta: dores e necessidades do usuário, a visão (`visao.md`) e as maquetes de tela (`maquetes/`) |
| `docs/ideias/` | Uma ideia por arquivo, com o estado de cada uma |
| `docs/cards/` | O que está sendo ou foi construído; `modelo.md` é o formato de um card |
| `docs/decisoes/` | Uma decisão por arquivo: o que é, por quê e onde aparece no código |
| `docs/funcionalidades.md` | O que o FishingRod já faz |

## Documentos antigos

Até outubro de 2026 o projeto seguiu a metodologia AI-DLC. Os documentos dessa fase saíram da
pasta, mas continuam no Git, na tag `aidlc-congelado`.
