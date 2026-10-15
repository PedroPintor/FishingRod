# Tech Stack Decisions — U2 `persistencia`

**Fase:** CONSTRUCTION · **Unidade:** `U2 persistencia` · **Data:** 2026-08-26

---

## 1. Decisões

| # | Decisão | Origem | Alternativa rejeitada |
|---|---|---|---|
| **TS-P-01** | **`sqlite3` da biblioteca padrão** | ESC-13, Q10=A, Q13=B | `aiosqlite` — ver §2 |
| **TS-P-02** | **`asyncio.to_thread`** atravessa a fronteira `async` → síncrono | Q1=A via Q13=B | Thread dedicada com fila (é o que o `to_thread` já é); `aiosqlite` (§2) |
| **TS-P-03** | **Uma conexão viva por processo** (`check_same_thread=False`) + `asyncio.Lock` | Q2=B, NFR-P-09 | Conexão por operação — obrigaria reaplicar os PRAGMAs em toda chamada, e o esquecimento de `foreign_keys` seria silencioso |
| **TS-P-04** | **WAL + `synchronous = NORMAL`**, `busy_timeout = 5000`, `foreign_keys = ON` | Q3=A, NFR-P-05/06/10 | `synchronous = FULL` (um `fsync` por escrita de streaming); journal `DELETE` (leitor e escritor se bloqueiam) |
| **TS-P-05** | **`json` da stdlib** serializa o documento do ambiente | ESC-13 | Nenhuma biblioteca de serialização externa |
| **TS-P-06** | **`uuid.uuid7()`** da stdlib para identidade e ordem | ESC-14, requires-python 3.14 | Coluna de sequência — dispensada porque o próprio id ordena |
| **TS-P-07** | **`logging` da stdlib**, logger `fishingrod.persistencia` com `NullHandler` | Q11=B, NFR-P-17 | Nenhuma infraestrutura de log; deixaria `ConflitoDeVersao` invisível |
| **TS-P-08** | Testes: **`pytest` + `hypothesis`** (já em `dependency-groups.dev`) | `property-based-testing` Full | — |
| **TS-P-09** | **Zero dependências de runtime.** `dependencies = []` permanece | Q1a=B, Q13=B, NFR-P-12 | — |

Nada aqui acrescenta pacote ao `pyproject.toml`. O primeiro pacote de runtime do projeto continua
sendo o `claude-agent-sdk`, em **U6**.

---

## 2. A decisão que exigiu uma pergunta: `aiosqlite` (Q13)

**Q1=C** escolheu `aiosqlite` e **Q10=A** afirmou "sem dependência nova". As duas não podiam valer
juntas, e `Q1a=B` — do portão anterior — tinha escolhido 12 linhas próprias em vez de
`platformdirs` justamente para manter `dependencies = []`. A contradição foi levada à **Q13**, e a
resposta foi **B: stdlib**.

### O que foi medido antes de perguntar

```
$ uv pip compile - --exclude-newer 2026-08-25T00:00:00Z --python-version 3.14
Resolved 1 package
aiosqlite==0.22.1
```

`aiosqlite` resolve sob a política de idade de `ESC-15` e tem **zero dependências transitivas**. A
objeção de cadeia de suprimentos era fraca, e isso fica registrado a favor da opção rejeitada.

### O argumento que decidiu, e que não é sobre dependências

A justificativa original de `aiosqlite` era que ele daria "serialização e segurança de thread
automáticas". Metade é verdade — ele roda cada conexão numa thread própria. A outra metade é o
oposto: **ele não dispensa o `Lock`**, porque cada instrução é um `await` separado e duas corrotinas
na mesma conexão podem intercalar instruções **dentro de uma transação aberta**, quebrando
**RN-P-03** ("ou tudo, ou nada").

| | Como uma operação executa | Se o `Lock` for esquecido um dia |
|---|---|---|
| **stdlib + `to_thread`** (escolhido) | todo o SQL de uma operação numa função síncrona, um único `to_thread`, **sem `await` no meio** | a transação continua atômica: não há onde intercalar |
| `aiosqlite` | cada instrução é um `await` | duas operações intercalam dentro da transação; RN-P-03 quebra em silêncio |

Dado `TS-P-03`, o que `aiosqlite` compraria era **ergonomia de escrita**, não segurança — e a stdlib
traz de brinde a rede da coluna da direita. É isso que **NFR-P-08** registra como requisito.

---

## 3. Riscos aceitos

| Risco | Mitigação | Quem cobre |
|---|---|---|
| Queda de energia perde até ~500 ms do turno em andamento | Aceito (Q3=A + Q4=B). Não há corrupção — a perda é de fim de arquivo | NFR-P-03, NFR-P-05 |
| `foreign_keys = ON` esquecido → órfãos silenciosos | Pragma ligado uma vez na abertura da conexão única; **`PBT-U2-07` falha se faltar** | NFR-P-06 |
| Carregar 5.000 anotações na abertura fica lento | Alvo mensurável e gatilho declarado para `Q2a=B`, sem migração de dados | NFR-P-01, §7 de `nfr-requirements.md` |
| `to_thread` usa o pool padrão do asyncio, compartilhado com outros usos | O `Lock` garante uma operação de banco por vez; o pool não é gargalo em single-user | TS-P-02, TS-P-03 |
| Escrever à mão a resolução da pasta de dados do SO pode errar uma convenção | Falha visível (dado no lugar errado), não silenciosa; coberta por teste por plataforma | Q1a=B |
