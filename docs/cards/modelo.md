# Modelo de card

Um card nasce de uma sessão de aprofundamento de uma ideia de `docs/ideias/`. Ele diz o que vai
ser construído e como saber que ficou pronto; uma sessão de implementação segue o card.

Copie o bloco abaixo para `docs/cards/00X-nome-curto.md` e preencha.

```markdown
# 00X — Nome

Estado: em andamento | pronto
Ideia de origem: [nome da ideia](../ideias/nome-da-ideia.md)

## Objetivo

Uma frase, em linguagem de usuário: o que eu consigo fazer quando este card estiver pronto.

## Partes

As partes são o plano inicial e podem mudar. Quando mudarem, registre aqui o que mudou e por quê.

- [ ] Parte 1
- [ ] Parte 2

## Como testar

O que o Pedro faz na tela e o que tem que acontecer.

- [ ] Faço X → acontece Y
- [ ] Faço Z → acontece W

## Decisões usadas

- [D0X — nome](../decisoes/D0X-nome.md)

## Ao terminar

- [ ] Rodar os testes automáticos (`uv run pytest`).
- [ ] Acrescentar a funcionalidade em `docs/funcionalidades.md`.
- [ ] Mudar o estado da ideia de origem para "virou o card 00X".
- [ ] Fazer o commit.
```
