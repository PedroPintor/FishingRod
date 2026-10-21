# Modelo de card

Um card nasce de uma sessão de aprofundamento de uma ideia de `docs/ideias/`. Ele diz o que vai
ser construído e como saber que ficou pronto; uma sessão de implementação segue o card.

Copie o bloco abaixo para `docs/cards/00X-nome-curto.md` e preencha.

```markdown
# 00X — Nome

Estado: a fazer | em andamento | pronto
Ideia de origem: [nome da ideia](../ideias/nome-da-ideia.md)

## Objetivo

Uma frase no formato *jobs to be done*, em linguagem de usuário: **Quando** <a situação>,
**quero** <o que eu faço>, **para** <o resultado que eu espero>.

## Partes

As partes são o plano inicial e podem mudar. Quando mudarem, registre aqui o que mudou e por quê.

- [ ] Parte 1
- [ ] Parte 2

## Como testar

O que o Pedro faz na tela e o que tem que acontecer. Ao lado de cada item, o teste automático que
confere; o nome exato entra quando o teste existir.

- [ ] Faço X → acontece Y. *Teste:* o que o teste automático confere.
- [ ] Faço Z → acontece W. *Teste:* o que o teste automático confere.

## Decisões usadas

- [D0X — nome](../decisoes/D0X-nome.md)

## Pode melhorar

Escolhas feitas para começar simples, para não esquecer. Uma por linha: **o quê** — por quê.
Quando uma virar trabalho de verdade, ganha um arquivo em `docs/ideias/` e a linha aponta para ele.

- **O quê:** como é hoje e como poderia ser — por quê: o que se ganha.

## Ao terminar

- [ ] Rodar os testes automáticos (`uv run pytest`).
- [ ] Acrescentar a funcionalidade em `docs/funcionalidades.md`.
- [ ] Mudar o estado da ideia de origem para "virou o card 00X".
- [ ] Fazer o commit.
```
