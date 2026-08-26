# U1 `dominio` — Regras de negócio

**Estágio:** CONSTRUCTION — Functional Design · **Unidade:** `U1 dominio` · **Data:** 2026-08-26

Cada regra tem identificador estável (`RN-nn`), enunciado verificável, comportamento em violação e
rastreio. Os identificadores são usados pelo Code Generation de U1 para nomear testes.

---

## 1. Tabela de regras

| # | Regra | Em violação | Rastreio |
|---|---|---|---|
| **RN-01** | Toda entidade (`Ambiente`, `Frente`, `Tarefa`, `Chat`, `Etapa`) nasce com `Identidade.nova()`, gerada no próprio construtor | — (não é violável de fora) | RF-F16, ESC-14, Pergunta 4B |
| **RN-02** | `nome` de ambiente, frente, tarefa e chat, e `descricao` de etapa, não podem ser vazios nem só espaços | `NomeInvalido` | US-15, US-16 |
| **RN-03** | `Ambiente` recém-criado tem **zero** frentes | — | Q1=A |
| **RN-04** | Nome duplicado de frente ou tarefa é **permitido**; a identidade distingue | — (não é erro) | Q2=A, RF-F16 |
| **RN-05** | `Tarefa` recém-criada tem **exatamente um** `Chat`, cujo agente tem `papel = ORQUESTRADOR` | `AgenteInvalido` se o agente passado não for orquestrador | Q4=A, `components.md` §2.4 |
| **RN-06** | Uma `Tarefa` tem **no máximo um** chat com agente de `papel = ORQUESTRADOR` | `OrquestradorDuplicado` | `components.md` §2.4 (invariante preservada de `Sessao.__post_init__`) |
| **RN-07** | `Etapa.concluir()` é idempotente; `Etapa.reabrir()` desfaz a conclusão e também é idempotente | — | Q5a=B |
| **RN-08** | As etapas de uma tarefa são **ordenadas** pela posição na lista; **não** há dependência entre elas — concluir a n-ésima não exige as anteriores concluídas | — | Q5b=A |
| **RN-09** | `Memoria.anotar(chave, valor, autor)` funciona com chave inédita e **acumula** — nunca substitui anotação anterior da mesma chave | — | **TD-03**, RF-F06, US-04 |
| **RN-10** | Cada `anotar` incrementa `Memoria.versao` em 1 e grava `Anotacao.criada_em` em UTC | — | CQ3=C |
| **RN-11** | `Ambiente.raiz_wiki` é montada no construtor como `dados:wikis/<id>`, nunca caminho absoluto | — | Q9=A, RNF-11, `components.md` §2.8 |
| **RN-12** | `exige_aprovacao(AGENTE)` é `True`; `exige_aprovacao(USUARIO)` é `False` | — | Q8=A, rodada 4 |
| **RN-13** | Nenhum módulo de `dominio/` importa `claude_agent_sdk`, `sqlite3` ou `textual` | falha de teste de importação | **RF-F04**, TD-02 |
| **RN-14** | `buscar_frente`, `buscar_tarefa` e `buscar_chat` devolvem `None` quando não encontram — não levantam | — | Q7=A |
| **RN-15** | Toda entidade de domínio é mutável apenas por suas operações; `Identidade`, `RaizWiki` e `Agente` são imutáveis | — | `components.md` §2.9 |

---

## 2. Regras detalhadas onde o enunciado não basta

### RN-02 — o que é "nome vazio"

Vazio é `""`, e também qualquer texto cujo `strip()` seja vazio. O nome **não** é normalizado
(sem `strip` automático, sem `title case`): o domínio recusa o inválido, mas não reescreve o
válido — reescrever seria surpresa para quem digitou.

**Não há limite máximo de tamanho nesta iteração.** Registro como decisão consciente: um limite
seria arbitrário sem uma restrição real de tela ou de banco, e nenhuma das duas foi estabelecida.
Se U2 ou U9 descobrir uma, a regra volta com número próprio.

### RN-05 e RN-06 — como as duas convivem

RN-05 é sobre o **nascimento** (a tarefa nasce com um orquestrador); RN-06 é sobre a **vida**
(nunca chega a dois). Juntas produzem: exatamente um orquestrador por tarefa, do início ao fim.
`criar_chat(agente)` com `papel = SUB_AGENTE` é sempre permitido — é assim que o chat do
bibliotecário nasce (Q14=X).

### RN-09 — a correção de TD-03, com precisão

O código atual faz `self.anotacoes[chave].append(...)`, que levanta `KeyError` quando a chave é
nova. A regra exige acumulação por chave: **duas anotações na mesma chave produzem uma lista de
dois elementos, na ordem em que foram feitas** — não uma substituindo a outra (segundo critério de
aceite de US-04).

### RN-13 — como se verifica

Teste de importação executado com os pacotes **ausentes** do ambiente. Hoje isso é gratuito: o
`.venv` do projeto não tem `claude-agent-sdk` nem `textual` instalados (U0 não os instalou
deliberadamente). O teste continua válido quando U6 e U9 os instalarem, porque o que ele verifica é
o grafo de import de `dominio/`, não a ausência global.

---

## 3. Mapa história → regra

| História | Regras que a sustentam |
|---|---|
| **US-04** — anotar na memória sem erro | RN-09, RN-10 |
| **US-05** — a estrutura sobrevive a fechar e reabrir | RN-01 (a identidade é o que permite reconstituir), RN-11 |
| **US-15** — criar uma frente | RN-02, RN-03, RN-04 |
| **US-16** — criar uma tarefa | RN-02, RN-04, RN-05, RN-06 |

**Regras sem história de origem, declaradas**: RN-12 (política de aprovação — decisão de produto da
rodada 4, já registrada em `unit-of-work-story-map.md` §4). Todas as demais têm origem em história,
requisito ou dívida técnica.

---

## 4. Dívida técnica morta nesta unidade

| Dívida | Regra que a mata | Como se prova |
|---|---|---|
| **TD-03** — `Memoria.anotar()` lança `KeyError` na primeira escrita | RN-09 | Teste direto + propriedade PBT-U1-03 (ver `business-logic-model.md` §5) |
