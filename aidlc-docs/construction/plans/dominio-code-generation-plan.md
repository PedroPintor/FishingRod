# Code Generation Plan — U1 `dominio`

**Fase:** CONSTRUCTION · **Unidade:** `U1 dominio` · **Data:** 2026-08-26
**Base:** `construction/dominio/functional-design/` (os 3 artefatos aprovados em 2026-08-26T00:30Z)
**Estágios da unidade:** FD ✅ concluído e aprovado · NFR-R SKIP · NFR-D SKIP · INFRA SKIP · **CG EXECUTE**

> **Este plano é a única fonte de verdade da geração de código de U1.** A Parte 2 executa
> exatamente estes passos, na ordem, marcando `[x]` a cada conclusão.

---

## 1. Contexto da unidade

| Campo | Conteúdo |
|---|---|
| **Histórias** | US-04, US-05 (estrutura), US-15, US-16 (invariantes de criação) |
| **Dívidas** | **TD-03** — `Memoria.anotar()` lança `KeyError` |
| **Depende de** | U0 (aprovada; projeto em Python 3.14 com `uuid.uuid7()`) |
| **Entrega para** | U2 (persiste estas entidades), U4 (orquestra), U5, U6, U7, U8 (consultam `politica`) |
| **Especificação** | 15 regras `RN-01`..`RN-15`, 7 propriedades `PBT-U1-01`..`07` |
| **Destino do código** | `src/fishingrod/dominio/` |
| **Destino dos testes** | `tests/dominio/` |

---

## 2. Decisões de implementação declaradas (não perguntadas)

Escolhas de forma que o Functional Design não fixou. Reversíveis; se discordar, é hora de dizer.

| Decisão | Escolha | Motivo |
|---|---|---|
| Estilo das classes | `@dataclass` | O código atual já usa; mantém a leitura familiar |
| Tipos de valor | `@dataclass(frozen=True)` para `Identidade`, `RaizWiki`, `Anotacao`, `Agente` | RN-15 exige imutabilidade — `frozen` a torna estrutural, não uma promessa |
| Validação | `__post_init__` levantando erro de domínio | Impede entidade inválida de existir, em vez de validar no chamador |
| Um arquivo por conceito | `identidade.py`, `erros.py`, `agente.py`, `memoria.py`, `etapa.py`, `chat.py`, `tarefa.py`, `frente.py`, `ambiente.py`, `politica.py` | Arquivos pequenos e nomeáveis; o `__init__.py` reexporta |
| `__init__.py` do pacote | Reexporta os nomes públicos | Quem usa escreve `from fishingrod.dominio import Ambiente` sem conhecer a divisão interna |
| Enums | `enum.Enum` para `Papel`, `ExecutorEtapa`, `Chamador` | stdlib; comparável e serializável em U2 |
| `criada_em` | `datetime.now(UTC)` | RN-10 pede UTC explícito; sem `utcnow()`, que é ingênuo quanto a fuso |
| Layout dos testes | Um arquivo por conceito, espelhando o código | Falha aponta direto para o conceito |
| Nome de teste | `test_rn_09_*`, `test_pbt_u1_03_*` | O identificador da regra no nome torna rastreável qual regra quebrou |

---

## 3. Passos de geração

> **Executado em 2026-08-26 — 14/14 passos concluídos.** `uv run pytest` = **41 passed** (39 de U1
> + 2 de U0), na primeira execução. Evidências e decisões da execução em
> `aidlc-docs/construction/dominio/code/code-summary.md`.


### Step 1 — `erros.py`
- [x] `ErroDeDominio`, `NomeInvalido`, `OrquestradorDuplicado`, `AgenteInvalido`
- [x] Helper interno de validação de texto não vazio (usado por todas as entidades — RN-02)
- **Rastreio**: RN-02, Q7=A

### Step 2 — `identidade.py` + testes
- [x] `Identidade` (frozen) com `nova()` usando `uuid.uuid7()`
- [x] Testes: `PBT-U1-01` (ordenação e unicidade), `PBT-U1-02` (versão 7 e formato canônico)
- **Rastreio**: RN-01, ESC-14, CQ2=D

### Step 3 — `agente.py`
- [x] `Papel` (`ORQUESTRADOR` | `SUB_AGENTE`), `Agente` (frozen) com `nome`, `papel`, `modelo`,
      `ferramentas: list[str]`, `regras: list[str]`
- [x] Sem `responder()`, sem estado de sessão
- **Rastreio**: `components.md` §2.9, emenda R4/Q12=A

### Step 4 — `memoria.py` + testes
- [x] `Anotacao` (frozen) com `autor`, `valor`, `criada_em`
- [x] `Memoria` com `anotacoes`, `versao`, `anotar(chave, valor, autor)` — **mata TD-03**
- [x] Testes: `test_rn_09` (chave inédita não levanta; acumula), `PBT-U1-03`, `PBT-U1-04`
- **Rastreio**: RN-09, RN-10, TD-03, US-04

### Step 5 — `etapa.py` + testes
- [x] `ExecutorEtapa`, `Etapa` com `concluir()` e `reabrir()` idempotentes
- [x] Teste `PBT-U1-05` (sequência arbitrária reflete a última chamada)
- **Rastreio**: RN-07, RN-08, Q5a=B, Q5b=A

### Step 6 — `chat.py`
- [x] `Chat` com `id`, `nome`, `agente`, `renomear()`
- [x] **Sem** `mensagens` e **sem** sessão viva — ausências deliberadas (Pergunta 3B, 6A)
- **Rastreio**: RN-02

### Step 7 — `tarefa.py` + testes
- [x] `Tarefa` com `criar_chat`, `buscar_chat`, `contar_orquestradores`, `criar_etapa`
- [x] Testes: `test_rn_06` (segundo orquestrador levanta `OrquestradorDuplicado`), sub-agente sempre
      permitido, `criar_etapa` anexa ao fim
- **Rastreio**: RN-05, RN-06, RN-08

### Step 8 — `frente.py` + testes
- [x] `Frente` com `criar_tarefa(nome, agente_orquestrador)` e `buscar_tarefa`
- [x] Testes: tarefa nasce com 1 chat de orquestrador (RN-05); agente não-orquestrador levanta
      `AgenteInvalido`; nome duplicado é permitido (RN-04)
- **Rastreio**: RN-02, RN-04, RN-05

### Step 9 — `raiz_wiki.py` e `ambiente.py` + testes
- [x] `RaizWiki` (frozen) com `esquema()`; nunca caminho absoluto
- [x] `Ambiente` com `frentes=[]` ao nascer, `raiz_wiki` derivada do `id`, `criar_frente`,
      `buscar_frente`
- [x] Testes: `test_rn_03` (nasce sem frente), `test_rn_11` (formato `dados:wikis/<id>`),
      `PBT-U1-06`, `PBT-U1-07`
- **Rastreio**: RN-03, RN-04, RN-11, Q1=A, Q9=A

### Step 10 — `politica.py` + teste
- [x] `Chamador`, `APROVACAO_DE_AGENTE_OBRIGATORIA = True`, `exige_aprovacao(chamador)`
- [x] Teste `test_rn_12` (AGENTE → True, USUARIO → False)
- **Rastreio**: RN-12, rodada 4 de Units Generation

### Step 11 — `__init__.py` do pacote e teste de fronteira
- [x] Reexportar os nomes públicos em `dominio/__init__.py`
- [x] **Teste `test_rn_13`**: nenhum módulo de `dominio/` importa `claude_agent_sdk`, `sqlite3` ou
      `textual` — varredura do grafo de import, não `try/except ImportError`
- **Rastreio**: **RF-F04**, RN-13, TD-02 (que fecha em U6, mas cuja garantia começa aqui)

### Step 12 — Execução e verificação
- [x] `uv run pytest` — todos os testes de U1 e os 2 de U0 passando
- [x] Conferir que nenhum arquivo antigo (`Ambiente/`, `model/`) foi tocado (Q8=A)
- [x] Conferir ausência de duplicatas (`*_new.py`, `*_modified.py`)
- **Rastreio**: critério de pronto de U1 em `unit-of-work.md` §3

### Step 13 — Emendas nos artefatos de Application Design
- [x] `component-methods.md` §1.3 — `criar_tarefa(nome, agente_orquestrador)`
- [x] `component-methods.md` §1.7 — `Memoria.versao` e `Anotacao.criada_em`
- [x] `component-methods.md` §1.1 — `uuid.uuid7()` da stdlib
- [x] `components.md` §2.2 — `Ambiente` nasce sem frente
- [x] Sempre riscando o texto substituído, nunca apagando
- **Rastreio**: `business-logic-model.md` §10

### Step 14 — Resumo
- [x] `aidlc-docs/construction/dominio/code/code-summary.md` com arquivos, saída real dos testes e
      o estado de cada critério de pronto
- **Rastreio**: regra de localização de `construction/code-generation.md`

---

## 4. Critério de pronto de U1 (`unit-of-work.md` §3) e onde cada um é provado

| # | Critério | Passo que o prova |
|:--:|---|---|
| 1 | `Memoria.anotar` em chave nova funciona, com a propriedade PBT | Step 4 |
| 2 | Invariantes: frente pertence ao ambiente; tarefa pertence à frente | Steps 8 e 9 |
| 3 | Nenhum import de `claude_agent_sdk`, `sqlite3` ou `textual` em `dominio/` | Step 11 |
| 4 | `Identidade` é UUIDv7, ordenável por tempo, criada no construtor | Step 2 |

> O critério 2 original citava "`Ambiente` novo nasce com o parâmetro de aprovação ligado" — texto
> já riscado na rodada 4, substituído pela política constante, coberta no Step 10.

---

## 5. O que este plano **não** faz

- Não persiste nada — `PortaPersistencia` e SQLite são U2
- Não toca na wiki — U3
- Não cria serviço de aplicação, ação de catálogo ou tela — U4, U5, U9
- **Não apaga `Ambiente/ambiente.py`, `Ambiente/memoria.py` nem `model/mensagem.py`.** Por Q8=A o
  código antigo só morre quando a unidade que o substitui **fecha**; o Step 12 confirma que
  continuam intactos. A remoção acontece na aprovação desta unidade, não durante a geração
- Não instala dependência nova — o domínio usa só a stdlib

---

## 6. Escopo

14 passos: 10 módulos de domínio, 9 arquivos de teste, 1 verificação, 4 emendas e 1 resumo.
4 histórias, 15 regras, 7 propriedades, 1 dívida técnica morta (TD-03).
