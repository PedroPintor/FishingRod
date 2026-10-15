# Clarificação — NFR Requirements U2 `persistencia`

**Data:** 2026-08-26 · **Origem:** Step 5 do `persistencia-nfr-requirements-plan.md`
**Motivo:** duas respostas se contradizem. Uma pergunta aqui; o resto são correções e aceites
declarados.

> Enquanto o `[Answer]:` da Q13 estiver vazio, **nenhum artefato de NFR é gerado**.

---

## 1. O bloqueio: Q1=C e Q10=A não podem valer juntas

| Resposta | O que diz |
|---|---|
| **Q1 = C** | "vamos usar [aiosqlite], assim já facilita a nossa vida, já vamos ter uma ferramenta pronta e já testada e validada" |
| **Q10 = A** | "`sqlite3` da stdlib, **sem dependência nova**" |
| **Q1a = B** (portão anterior) | 12 linhas próprias em vez de `platformdirs`, *para manter zero dependências de runtime* |

`aiosqlite` **é** uma dependência de runtime. Q10=A diz que não há nenhuma. Uma das duas cai.

Sua Q2 menciona aiosqlite pelo nome, então minha leitura é que Q1=C é a intenção e Q10=A foi
marcada no automático. Mas não vou decidir isso por dedução.

### O que medi antes de perguntar

```
$ uv pip compile - --exclude-newer 2026-08-25T00:00:00Z --python-version 3.14
Resolved 1 package
aiosqlite==0.22.1
```

Resolve sob a política de idade de `ESC-15` e tem **zero dependências transitivas**. A superfície de
cadeia de suprimentos é um pacote, não uma árvore — isso enfraquece bastante o argumento de
`security-baseline` contra ela. É honesto registrar isso a favor de (C).

### Uma correção ao raciocínio da sua Q2

Você escreveu: *"Com aiosqlite, a serialização e segurança de thread ficam automáticas."*

Metade disso é verdade e a outra metade é o oposto do que parece:

- **Verdade**: `aiosqlite` roda cada conexão numa thread própria e enfileira as instruções. Nenhum
  erro de "conexão usada em outra thread".
- **Não é verdade**: isso **não** substitui o `asyncio.Lock`. Cada instrução é um `await` separado,
  então duas corrotinas na mesma conexão podem intercalar instruções **dentro de uma transação
  aberta**. Isso quebra **RN-P-03** ("toda operação que muda estado acontece em uma transação; ou
  tudo, ou nada"), que é regra aprovada. O `Lock` de Q2=B continua obrigatório.

E aqui aparece a assimetria que muda a comparação:

| | Como uma operação executa | Se o `Lock` for esquecido um dia |
|---|---|---|
| **stdlib + `to_thread`** | todo o SQL da operação é uma função síncrona, executada num único `to_thread` — **sem ponto de `await` no meio** | a transação continua atômica: não há onde intercalar |
| **aiosqlite** | cada instrução é um `await` | duas operações intercalam dentro da transação; RN-P-03 quebra em silêncio |

Ou seja: com Q2=B (conexão viva + `Lock`), o que (C) compra sobre (A) é **ergonomia de escrita**, não
segurança de thread — e (A) tem uma rede de proteção estrutural que (C) não tem.

---

### Q13 — Decida a contradição

A) **`aiosqlite`** — Q1=C vence, e **Q10 passa a ser B**. Uma dependência de runtime entra no
   projeto; `pyproject.toml` deixa de ter `dependencies = []`. O `Lock` continua obrigatório.
B) **`sqlite3` da stdlib + `asyncio.to_thread`** — Q10=A vence, e **Q1 passa a ser A**. Zero
   dependências de runtime, coerente com Q1a=B. O `Lock` continua obrigatório, com a rede extra da
   tabela acima.

**Recomendação: B** — não por purismo de dependências, e sim pela linha da direita da tabela: a
única regra que este estágio pode quebrar em silêncio é RN-P-03, e (B) a torna difícil de quebrar
por construção. Dito isso, o seu argumento de "ferramenta pronta e validada" é legítimo e o custo de
(A) é baixo e medido (1 pacote, 0 transitivas). Se você escolher (A), aplico sem reabrir.

[Answer]: B - eu entendi o seu argumento e faz sentido. 

---

## 2. Aceites declarados (não são perguntas)

### 2.1 Q6 — `resultado_resumo` sai. Aceito, com a justificativa corrigida

A decisão está tomada e eu a aplico. Mas o registro precisa ficar correto, porque um item da sua
justificativa não bate com o histórico:

> "Nenhuma US nesta iteração exige histórico de resultados de ferramenta... Sem caso de uso, é
> especulação."

A coluna **não** nasceu de especulação: nasceu da **Pergunta F = B** da Application Design, que você
aprovou, e que dizia com todas as letras *"qual tool, parâmetros resumidos, **resultado resumido**"*,
com o motivo declarado de tornar auditável *"por que o bibliotecário propôs aquilo"*.

**Fui verificar se esse motivo se sustenta hoje, e ele não se sustenta.** US-14 pede revisão do
conteúdo **antes** de salvar — é aprovação em fluxo vivo, não leitura de histórico. Nenhum critério
de aceite desta iteração lê resultado de ferramenta depois do fato. Então a sua conclusão está
certa; o que estava errado era dizer que ninguém tinha decidido.

**E há um argumento a favor da remoção que a sua resposta não usou, mais forte que os quatro que
usou:** no stream do SDK, o **resultado não existe** no instante em que o evento de uso de
ferramenta chega. A assinatura
`registrar_uso_ferramenta(id_mensagem, tool, args_resumo, resultado_resumo)` assume que os dois são
conhecidos ao mesmo tempo, e **nenhuma unidade tem desenhada** a correlação entre a chamada e o
resultado que a preencheria. A coluna não era só não-usada: ela era **não-preenchível** sem trabalho
que ninguém orçou. Remover fecha um buraco, não só uma coluna.

**Emendas que isso dispara** (todas com texto riscado, nada apagado):

| Artefato | Emenda |
|---|---|
| `persistencia/functional-design/domain-entities.md` | `uso_ferramenta` perde a coluna `resultado_resumo`; `UsoDeFerramenta` perde o campo |
| `persistencia/functional-design/business-rules.md` | RN-P-19 passa a falar só de argumentos |
| `persistencia/functional-design/business-logic-model.md` | assinatura de `registrar_uso_ferramenta` perde o parâmetro |
| `inception/application-design/component-methods.md` §4.1 e §4.2 | idem, e a Pergunta F=B fica **parcialmente revogada** |
| `inception/application-design/components.md`, `services.md`, `unit-of-work.md` (U7) | "resultado resumido" sai da descrição do que a transcrição persiste |
| `inception/plans/application-design-clarification-questions.md` (Pergunta F) | nota de revogação parcial, sem apagar a resposta original |

### 2.2 Q11=B — escopo do log

`logging` da stdlib, um logger nomeado `fishingrod.persistencia`, **sem** configurar destino nesta
unidade (quem configura é o composition root de U9). Registra **falha e conflito**, nunca operação
bem-sucedida — um log por `anotar` seria ruído em volume de blackboard.

### 2.3 Q3=A + Q4=B — o número que vira teste

`synchronous = NORMAL` com throttle de 500 ms significa que uma queda de energia pode custar **até
meia frase** do turno em andamento. Está declarado assim no artefato, para que ninguém o descubra
depois como surpresa.

### 2.4 Q5=A — o alvo de 1 s

Vira um teste de fumaça com dado gerado (5.000 anotações), marcado para poder ser pulado em máquina
lenta de CI. Ele **não** é portão de merge: é o sensor que avisa quando `Q2a=B` (carga sob demanda)
precisa deixar de ser hipótese.
