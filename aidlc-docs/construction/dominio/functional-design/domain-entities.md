# U1 `dominio` — Entidades de domínio

**Estágio:** CONSTRUCTION — Functional Design · **Unidade:** `U1 dominio` · **Profundidade:** comprehensive
**Data:** 2026-08-26
**Decisões que governam este documento:** Q1=A, Q2=A, Q3→CQ2=D, Q4=A, Q5a=B, Q5b=A, Q6=B, Q7=A,
Q8=A, Q9=A, CQ1=A, CQ3=C

> Especificação, não código. A implementação é o Code Generation de U1.
> **Fronteira:** nada aqui importa `claude_agent_sdk`, `sqlite3` ou `textual` (RF-F04); nada aqui
> persiste a si mesmo, roteia comando ou conhece sessão viva.

---

## 1. Mapa de composição

```
Ambiente
├── id: Identidade
├── nome: str
├── raiz_wiki: RaizWiki          (montada no construtor a partir do id — Q9=A)
└── frentes: list[Frente]        (vazia ao nascer — Q1=A)
    └── Frente
        ├── id, nome
        └── tarefas: list[Tarefa]
            └── Tarefa
                ├── id, nome
                ├── chats: list[Chat]      (nasce com 1 chat do orquestrador — Q4=A)
                ├── etapas: list[Etapa]    (ordenada — Q5b=A)
                └── memoria: Memoria
```

**Alternativa textual** (obrigatória por `common/content-validation.md`): `Ambiente` contém zero ou
mais `Frente`; cada `Frente` contém zero ou mais `Tarefa`; cada `Tarefa` contém um ou mais `Chat`,
zero ou mais `Etapa` e exatamente uma `Memoria`. `Ambiente` contém exatamente uma `RaizWiki`.
`Chat` referencia um `Agente`, que **não** é contido — é configuração compartilhada.

**Fora da composição, e é deliberado:**
- `Agente` é configuração imutável, compartilhável entre chats (`components.md` §2.9)
- A **transcrição** não está em `Chat` — é composta pelo serviço a partir de U2 (Pergunta 3B)
- A **wiki** não está aqui — o domínio só conhece a `RaizWiki` como localizador (CQ1=A)

---

## 2. `Identidade` — tipo de valor

| Campo | Tipo | Regra |
|---|---|---|
| `valor` | `str` | UUIDv7 em texto canônico |

**Criação.** `Identidade.nova()` é a única forma. Usa `uuid.uuid7()` da stdlib do Python 3.14
(CQ2=D — a versão do projeto foi elevada exatamente para isto).

**Propriedades.**
- Imutável; comparável por igualdade de `valor`; usável como chave de dicionário
- **Ordenável por tempo de criação**: duas identidades criadas em sequência ordenam na ordem de
  criação quando comparadas como texto. É isso que dá paginação de transcrição sem coluna extra
  em U2 (ESC-14)
- Criada **no construtor da entidade**, nunca no adaptador de persistência (Pergunta 4B). O
  repositório de U2 lê a identidade existente; não a gera

---

## 3. `Ambiente` — agregado raiz

| Campo | Tipo | Padrão | Regra |
|---|---|---|---|
| `id` | `Identidade` | `Identidade.nova()` | RN-01 |
| `nome` | `str` | obrigatório | não vazio (RN-02) |
| `raiz_wiki` | `RaizWiki` | derivada do `id` | RN-11 (Q9=A) |
| `frentes` | `list[Frente]` | `[]` | **vazia ao nascer** (RN-03, Q1=A) |

**Operações**: `criar_frente(nome) -> Frente` · `buscar_frente(id) -> Frente | None`

**Ciclo de vida.** Nasce vazio de frentes. Não há mais criação automática de "projeto-padrao" — a
razão técnica que a justificava (o `IndexError` de `projetos[indice_ativo]`) morreu com a identidade
opaca (ESC-14). Quem garante que o usuário tem onde trabalhar é a tela de início (U9).

> **Registro da correção da CQ1**: as frentes pertencem ao **ambiente**, não à wiki. O `Ambiente`
> conhece a wiki apenas pela `RaizWiki` — nunca o contrário.

---

## 4. `Frente`

| Campo | Tipo | Padrão | Regra |
|---|---|---|---|
| `id` | `Identidade` | `Identidade.nova()` | RN-01 |
| `nome` | `str` | obrigatório | não vazio (RN-02); **duplicata permitida** (RN-04, Q2=A) |
| `tarefas` | `list[Tarefa]` | `[]` | — |

**Operações**: `criar_tarefa(nome, agente_orquestrador) -> Tarefa` · `buscar_tarefa(id) -> Tarefa | None`

---

## 5. `Tarefa`

| Campo | Tipo | Padrão | Regra |
|---|---|---|---|
| `id` | `Identidade` | `Identidade.nova()` | RN-01 |
| `nome` | `str` | obrigatório | não vazio (RN-02); duplicata permitida (RN-04) |
| `chats` | `list[Chat]` | 1 chat do orquestrador | RN-05, RN-06 |
| `etapas` | `list[Etapa]` | `[]` | ordem = posição (RN-08) |
| `memoria` | `Memoria` | `Memoria()` | — |

**Operações**: `criar_chat(agente) -> Chat` · `buscar_chat(id) -> Chat | None` ·
`contar_orquestradores() -> int` · `criar_etapa(descricao, executor) -> Etapa`

**Ciclo de vida.** Nasce com **exatamente um** chat, cujo agente é o orquestrador recebido em
`Frente.criar_tarefa` (Q4=A). Isso mantém no domínio a invariante "toda tarefa tem um orquestrador",
onde ela é testável sem serviço.

---

## 6. `Chat`

| Campo | Tipo | Regra |
|---|---|---|
| `id` | `Identidade` | RN-01 |
| `nome` | `str` | não vazio; editável por `renomear` |
| `agente` | `Agente` | referência a configuração compartilhada |

**Operações**: `renomear(novo_nome)`

**Ausência deliberada de `mensagens`** (Pergunta 3B): a transcrição vem de
`PortaPersistencia.listar_mensagens(chat_id, …)` em U2 e é composta pelo serviço de U7. `Chat`
guarda só o que é pequeno e estável. **Ausência deliberada de sessão viva** (Pergunta 6A): sessão é
objeto de aplicação, não de domínio.

---

## 7. `Etapa`

| Campo | Tipo | Padrão | Regra |
|---|---|---|---|
| `id` | `Identidade` | `Identidade.nova()` | RN-01 |
| `descricao` | `str` | obrigatório | não vazia (RN-02) |
| `executor` | `ExecutorEtapa` | obrigatório | `AGENTE` \| `USUARIO` |
| `concluida` | `bool` | `False` | — |

**Operações**: `concluir()` · `reabrir()` (Q5a=B)

**Ordem** (Q5b=A): a ordem é a posição na lista de `Tarefa.etapas`. **Não há dependência entre
etapas** — concluir a terceira sem ter concluído a primeira é permitido.

---

## 8. `Memoria` e `Anotacao`

### `Anotacao`

| Campo | Tipo | Regra |
|---|---|---|
| `autor` | `str` | não vazio |
| `valor` | `str` | livre |
| `criada_em` | `datetime` (UTC) | **carimbo próprio** — CQ3=C |

O carimbo em `Anotacao` é o que permite exibir anotações de **chaves diferentes** em ordem
cronológica única. Sem ele, só existe ordem dentro de cada chave.

### `Memoria`

| Campo | Tipo | Padrão | Regra |
|---|---|---|---|
| `anotacoes` | `dict[str, list[Anotacao]]` | `{}` | RN-09 |
| `versao` | `int` | `0` | contador de escritas — CQ3=C |

**Operações**: `anotar(chave, valor, autor)`

**O que `versao` é e o que não é** (alinhado na CQ3): conta quantas escritas a memória sofreu, para
detecção de conflito em U2. **Não** ordena anotações — isso é `Anotacao.criada_em` e a posição na
lista.

**Saíram do código atual** (Q6=B): `anotar_plano()` — regra de um fluxo que não existe nesta
iteração — e `formatar()` — mistura apresentação com domínio.

---

## 9. `RaizWiki` — tipo de valor

| Campo | Tipo | Regra |
|---|---|---|
| `localizador` | `str` | formato `dados:wikis/<id_ambiente>` (RN-11) |

**Operações**: `esquema() -> str` (a parte antes de `:`; `"dados"` nesta iteração)

Montada pelo próprio `Ambiente` no construtor, a partir da própria identidade (Q9=A) — o que torna
a coerência entre ambiente e raiz uma **invariante**, não uma convenção. Nunca contém caminho
absoluto (RNF-11). O domínio **não** resolve o esquema em caminho real: isso é o adaptador de U3.

---

## 10. `Agente` — configuração

| Campo | Tipo | Regra |
|---|---|---|
| `nome` | `str` | não vazio |
| `papel` | `Papel` | `ORQUESTRADOR` \| `SUB_AGENTE` |
| `modelo` | `str` | identificador do modelo |
| `ferramentas` | `list[str]` | **nomes** de ferramenta, não funções (emenda R4/Q12=A) |
| `regras` | `list[str]` | linhas de prompt |

Imutável. Sem `responder()`, sem estado de sessão — por isso pode ser compartilhada entre chats sem
o risco da instância única que existe hoje (`AgenteDoSistema`, Pergunta 6A).

**Invariante R10, verificada em U6**: nenhum `Agente` com `papel = SUB_AGENTE` carrega nome de
ferramenta da família ambiente. Não é verificada aqui porque aqui não existem instâncias — U1
define o tipo, U6 verifica a configuração.

---

## 11. `politica.py` — política de aprovação

Não é entidade; é módulo de domínio sem estado (rodada 4 de Units Generation).

```
APROVACAO_DE_AGENTE_OBRIGATORIA = True

class Chamador(Enum): AGENTE | USUARIO

def exige_aprovacao(chamador: Chamador) -> bool
```

`exige_aprovacao(AGENTE)` → `True`; `exige_aprovacao(USUARIO)` → `False` (Q8=A). Consultada por U5
(ferramentas de ambiente) e U8 (propostas do bibliotecário). Quando a configuração voltar, só o
corpo desta função muda.

**Sem história de origem** — declarado em `unit-of-work-story-map.md` §4.

---

## 12. Erros de domínio (Q7=A)

```
ErroDeDominio                     (base)
├── NomeInvalido                  (nome ou descrição vazia)
├── OrquestradorDuplicado         (segundo ORQUESTRADOR na mesma tarefa)
└── AgenteInvalido                (papel incompatível com a operação)
```

`buscar_frente`, `buscar_tarefa` e `buscar_chat` **continuam devolvendo `None`** — "não encontrei"
não é violação de regra, é resultado (Q7=A).
