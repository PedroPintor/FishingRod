# Code Generation Plan — U2 `persistencia`

**Fase:** CONSTRUCTION · **Unidade:** `U2 persistencia` · **Portão 4 de 4** · **Data:** 2026-08-27
**Base:** os 3 artefatos de `functional-design/` (aprovados em 2026-08-26T03:10Z), os 2 de
`nfr-requirements/` (aprovados em 2026-08-26T04:40Z) e os 2 de `nfr-design/` (aprovados em
2026-08-27T15:10Z)
**Estágios da unidade:** FD ✅ · NFR-R ✅ · NFR-D ✅ · INFRA SKIP · **CG EXECUTE**

> **Este plano é a única fonte de verdade da geração de código de U2.** A Parte 2 executa
> exatamente estes passos, na ordem, marcando `[x]` a cada conclusão. Nada fora daqui é gerado.

> **Executado em 2026-08-27 — 16/16 passos concluídos.** `uv run pytest` = **84 passed, 1 skipped**
> (era 41 antes desta unidade). Evidências, decisões de execução e a inspeção de `NFR-P-13` em
> `aidlc-docs/construction/persistencia/code/code-summary.md`.
>
> **Um achado obrigou emenda de contrato durante a geração**: `anotar` e `inserir_mensagem` exigem
> que o ambiente exista, e agora levantam `AmbienteInexistente` (`RN-P-27`). Sem isso,
> `sqlite3.IntegrityError` atravessava a porta e as duas implementações discordavam. Descoberto por
> `PBT-U2-04`, não por revisão.

---

## 1. Contexto da unidade

| Campo | Conteúdo |
|---|---|
| **Histórias** | **US-05** (fechar e reabrir reconstitui o ambiente), **US-06** (transcrição visível e paginada) |
| **Dívida que morre aqui** | **TD-04** — persistência inexistente |
| **Depende de** | U0 (`uv`, `src/`, pytest, hypothesis) e U1 (entidades de domínio) — ambas aprovadas |
| **Entrega para** | U4 (`ServicoDeAmbiente`), U7 (`conversa`), U8 (`bibliotecario`), U9 (composition root) |
| **Especificação** | 26 regras `RN-P-01..26`, 8 propriedades `PBT-U2-01..08`, 21 requisitos `NFR-P-01..21`, 13 padrões `DP-P-01..13` |
| **Destino do código** | `src/fishingrod/aplicacao/portas/` e `src/fishingrod/adaptadores/persistencia/` |
| **Destino dos testes** | `tests/persistencia/` e `tests/dobles/` |
| **Dependências novas** | **zero** — `NFR-P-12` permanece verdadeiro (`sqlite3`, `json`, `uuid`, `logging`, `asyncio` são stdlib) |

**Interface publicada por esta unidade.** Um arquivo só: `aplicacao/portas/persistencia.py`. U4, U7,
U8 e U9 importam dele — nunca do adaptador (`DP-P-11`). O adaptador é escolhido no composition root
de U9.

**Critério de pronto de U2** (`unit-of-work.md` §3, com a emenda de 2026-08-26): CS-01 · round-trip
PBT · transcrição append-only paginada · uma transação por operação · memória sobrevive a escrita
concorrente · bloqueio otimista funciona · `apagar_ambiente` não deixa órfão · **dublê e real passam
o mesmo teste de contrato**.

---

## 2. Reconciliações entre artefatos aprovados

Divergências que os três portões deixaram entre si. Cada uma é resolvida aqui, e a resolução é a que
o código segue.

| # | Divergência | Resolução e motivo |
|---|---|---|
| **R-CG-1** | `domain-entities.md` §3 declara `idx_anotacao_tarefa(id_tarefa, id)`; `logical-components.md` §4 declara `idx_anotacao_ambiente(id_ambiente, id_tarefa, id)` | Vale o **segundo**. `RN-P-11` diz que a carga traz a memória de **todas** as tarefas de uma vez: o único caminho de leitura filtra por `id_ambiente`, nunca por tarefa isolada. Um índice que começa em `id_tarefa` não serve a essa consulta. `idx_mensagem_chat` e `idx_uso_mensagem` ficam como estão |
| **R-CG-2** | O diagrama de `logical-components.md` §4 escreve as colunas de `anotacao` como `texto`/`criado_em` | Valem os nomes de `domain-entities.md` §3: **`valor`** e **`criada_em`**, que são os campos reais de `dominio.memoria.Anotacao`. O diagrama era esboço; o DDL é o normativo |
| **R-CG-3** | A tabela `ambiente` tem `criado_em` e `atualizado_em`, mas a entidade `Ambiente` não tem esses campos | São **metadados do adaptador**, não do domínio (`DP-P-06` / Q8=A): `criado_em` é escrito na inserção, `atualizado_em` em toda gravação, ambos ISO-8601 UTC. É deles que `ResumoAmbiente.atualizado_em` sai e é por eles que `RN-P-24` ordena. O domínio continua sem saber que existe disco |
| **R-CG-4** | Onde encaixar `versao` em `Ambiente` sem quebrar chamadas existentes | Entra como **último campo**, depois de `raiz_wiki`, com padrão `0`. Nenhuma chamada posicional existente muda de significado |
| **R-CG-5** | `versao` e `versao_esquema` são colunas — e o documento JSON? | O mapeador **não** escreve nem lê essas duas chaves no JSON. Na carga, `Ambiente.versao` vem da coluna. É o que `domain-entities.md` §4 chama de ausência deliberada, e é o que faz `listar_ambientes` responder sem desserializar (`RN-P-24`) |

---

## 3. Decisões de implementação declaradas (não perguntadas)

Escolhas de forma que os três portões anteriores não fixaram. Reversíveis; se discordar, é hora.

| Decisão | Escolha | Motivo |
|---|---|---|
| **Como o teste chama código `async`** | Um auxiliar `executar(coro)` sobre `asyncio.run`, em testes **síncronos**. **Sem `pytest-asyncio`** | Evita uma dependência de desenvolvimento nova e evita o atrito conhecido entre Hypothesis e laço de eventos por função — cada exemplo gerado precisaria de laço próprio. `asyncio.run` dá exatamente isso, sem plugin |
| Assinatura dos auxiliares | `_ler(fn)` / `_escrever(fn)` recebendo `Callable[[sqlite3.Cursor], T]` | `DP-P-03`: quem escreve um método novo recebe um cursor e nada mais — não tem como abrir transação por conta própria |
| Serialização de tempo | `datetime.isoformat()` na escrita, `datetime.fromisoformat()` na leitura, sempre com fuso UTC explícito | Round-trip exato em Python 3.14, sem formato inventado. `RN-P-10` pede UTC explícito |
| Serialização de enum | `Papel.value` e `ExecutorEtapa.value` (texto) | Já é o vocabulário do documento em `domain-entities.md` §4 |
| Geradores Hypothesis | Constroem `Ambiente` **só pela API pública** (`criar_frente`, `criar_tarefa`, `criar_chat`, `criar_etapa`) e memória **só por `anotar()`** | `domain-entities.md` §5.2: uma `Memoria` montada à mão não faz round-trip, e isso é correto, não defeito |
| **Como `PBT-U2-08` é escrito** | As propriedades `PBT-U2-01..07` são escritas **uma vez** e a fixture do repositório é parametrizada nas duas implementações; mais **um** teste diferencial que executa a mesma sequência gerada nos dois e compara o observável a cada passo | Parametrizar prova que cada regra vale nos dois. O teste diferencial prova o que a parametrização não alcança: que os dois **concordam entre si** numa sequência arbitrária, inclusive nos erros (`RN-P-26`) |
| Onde ficam os geradores | `tests/persistencia/estrategias.py` | Usados pelo teste de contrato e pelos testes só-SQLite; um lugar só |
| Layout dos testes | `tests/persistencia/` com `__init__.py`, espelhando `tests/dominio/` | Mantém `tests/` como pacote — a condição que `DP-P-10` registrou |
| Nome de teste | `test_rn_p_05_*`, `test_pbt_u2_03_*`, `test_nfr_p_06_*` | Mesma convenção de U1: o nome diz qual regra quebrou |
| Reexportação | `adaptadores/persistencia/__init__.py` exporta `abrir_repositorio` e `RepositorioSQLite` | U9 escreve um import só, sem conhecer a divisão interna |

---

## 4. Passos de geração

### Step 1 — Emenda de U1: `Ambiente.versao`
- [x] `src/fishingrod/dominio/ambiente.py`: acrescentar `versao: int = 0` como último campo, com comentário citando a origem (`domain-entities.md` §5.1, Q4=C)
- [x] `tests/dominio/test_ambiente.py`: teste de que o padrão é `0` e de que o campo não interfere na criação da `RaizWiki`
- [x] Rodar `uv run pytest` e confirmar que os **41 testes existentes continuam passando**
- **Rastreio**: emenda pendente desde o portão 1/4 · `RN-P-05`, `RN-P-06`

### Step 2 — `aplicacao/portas/persistencia.py`
- [x] `PortaPersistencia` (`Protocol`) com as 9 operações do contrato final
- [x] `ResumoAmbiente`, `MensagemPersistida`, `UsoDeFerramenta` (todos `frozen`)
- [x] Hierarquia `ErroDePersistencia` → `ConflitoDeVersao`, `EsquemaIncompativel`, `BancoIlegivel`, `MensagemInexistente`
- [x] Verificar por inspeção que nenhum import de `sqlite3`/`json` entrou aqui
- **Rastreio**: `RN-P-16`, `D-ARQ-04`, `DP-P-11`, `NFR-P-16`

### Step 3 — `adaptadores/persistencia/localizacao.py` + testes
- [x] `caminho_do_banco() -> Path` resolvendo Windows / Linux (com `XDG_DATA_HOME`) / macOS
- [x] Testes por plataforma com `monkeypatch` em `sys.platform` e nas variáveis de ambiente — **sem tocar disco e sem banco**
- **Rastreio**: `DP-P-05`, Q1=A, Q1a=B, `domain-entities.md` §7

### Step 4 — `adaptadores/persistencia/esquema.py` + testes
- [x] `VERSAO_ESQUEMA_FISICO = 1`, `VERSAO_DOCUMENTO = 1`
- [x] `aplicar_pragmas(conexao)`: `journal_mode=WAL`, `synchronous=NORMAL`, `foreign_keys=ON`, `busy_timeout=5000`
- [x] `criar_esquema(conexao)`: as 4 tabelas com `IF NOT EXISTS` e os 3 índices (ver **R-CG-1**, **R-CG-2**)
- [x] `verificar_versao(conexao)`: lê `PRAGMA user_version`; `0` grava `1`; maior que `1` levanta `EsquemaIncompativel`
- [x] Testes: os 4 PRAGMAs realmente valem na conexão; `criar_esquema` duas vezes é inofensivo; `user_version` futuro levanta
- **Rastreio**: `NFR-P-05`, `NFR-P-06`, `NFR-P-10`, `NFR-P-19`, `NFR-P-20`, `DP-P-07`

### Step 5 — `adaptadores/persistencia/mapeamento.py` + testes
- [x] `documento_de(ambiente) -> dict` e `ambiente_de(documento, versao) -> Ambiente`
- [x] Sem `versao`/`versao_esquema` dentro do JSON (**R-CG-5**); sem memória e sem mensagem (`domain-entities.md` §4)
- [x] Teste de exemplo com um ambiente de duas frentes, cobrindo agente, ferramentas, regras e etapas
- **Rastreio**: `DP-P-06`, `RN-P-01`, `RN-P-08`

### Step 6 — `repositorio_sqlite.py` (1/3): abertura, transação, ciclo de vida
- [x] `abrir_repositorio(caminho)` com os 7 passos de `DP-P-01`, na ordem, e `BancoIlegivel` envolvendo `sqlite3.DatabaseError`
- [x] Permissões `0o700` no diretório e `0o600` no arquivo, sob `if os.name != "nt"` (`DP-P-08`)
- [x] `RepositorioSQLite.__init__(conexao)` recebendo conexão já pragmada; `_lock`; `fechar()`
- [x] `_ler` (`BEGIN`) e `_escrever` (`BEGIN IMMEDIATE`), ambos com `Lock` → `to_thread` → transação → `COMMIT`/`ROLLBACK`+log
- [x] Logger `fishingrod.persistencia` com `NullHandler`, usado **só** no `except` de `_escrever`
- **Rastreio**: `DP-P-01..04`, `DP-P-08`, `DP-P-09`, `NFR-P-07..11`, `NFR-P-14`, `NFR-P-17`, `NFR-P-18`

### Step 7 — `repositorio_sqlite.py` (2/3): ambiente e memória
- [x] `salvar_ambiente` — lê versão, compara, `INSERT` ou `UPDATE`, incrementa disco **e** objeto
- [x] `carregar_ambiente` — checa `versao_esquema`, desserializa, carrega **todas** as anotações e reconstrói cada `Memoria` com `versao = total`
- [x] `listar_ambientes` — só colunas nomeadas, ordem decrescente de `atualizado_em`
- [x] `apagar_ambiente` — `DELETE` na linha do ambiente; cascata faz o resto; id inexistente é no-op
- [x] `anotar` — `INSERT` puro, `id` UUIDv7 novo, nada comparado
- **Rastreio**: `RN-P-01..11`, `RN-P-20..24`, `NFR-P-01`, `NFR-P-02`

### Step 8 — `repositorio_sqlite.py` (3/3): transcrição
- [x] `inserir_mensagem` devolvendo a `Identidade` gerada
- [x] `atualizar_mensagem` alterando **só** `texto` e `em_andamento`; `rowcount == 0` levanta `MensagemInexistente`
- [x] `registrar_uso_ferramenta`
- [x] `listar_mensagens` com `ORDER BY id DESC LIMIT ?`, `antes_de` opcional, saída reordenada crescente, usos de ferramenta anexados
- **Rastreio**: `RN-P-12..14`, `RN-P-17..19`, `NFR-P-04`

### Step 9 — `adaptadores/persistencia/__init__.py`
- [x] Reexporta `abrir_repositorio` e `RepositorioSQLite`
- **Rastreio**: `logical-components.md` §1.2

### Step 10 — Infraestrutura de teste
- [x] `tests/conftest.py` com o perfil Hypothesis `deadline=None` (`NFR-P-21`)
- [x] `tests/dobles/__init__.py` — **obrigatório** (`DP-P-10`)
- [x] `tests/persistencia/__init__.py`
- **Rastreio**: `NFR-P-21`, `DP-P-10`

### Step 11 — `tests/dobles/repositorio_memoria.py`
- [x] `RepositorioEmMemoria` à mão, com dicionários e listas — **sem `sqlite3`**
- [x] Reimplementa versão, ordem de escrita, cascata de exclusão e paginação por cursor
- [x] Levanta os **mesmos** erros do real (`RN-P-26`)
- **Rastreio**: `DP-P-10`, `RN-P-25`, `RN-P-26`

### Step 12 — `tests/persistencia/estrategias.py`
- [x] Geradores de `Agente`, `Etapa`, `Chat`, `Tarefa`, `Frente`, `Ambiente` — só pela API pública
- [x] Gerador de roteiro de anotações (tarefa, chave, autor, valor) para replay por `anotar()`
- [x] Auxiliar `executar(coro)`
- **Rastreio**: `domain-entities.md` §5.2, `business-logic-model.md` §3

### Step 13 — `tests/persistencia/test_contrato.py` — as propriedades nas duas implementações
- [x] Fixture do repositório parametrizada: `RepositorioSQLite` (em `tmp_path`) e `RepositorioEmMemoria`
- [x] `PBT-U2-01` round-trip (salvando o ambiente **e** repassando a memória por `anotar`, já que `RN-P-08` proíbe `salvar_ambiente` de tocar anotação)
- [x] `PBT-U2-02` ordem e `versao` da memória · `PBT-U2-03` conflito não grava nada · `PBT-U2-04` limite e ordem · `PBT-U2-05` paginação sem lacuna nem repetição · `PBT-U2-06` anotações concorrentes sobrevivem · `PBT-U2-07` exclusão sem órfão
- [x] `PBT-U2-08` diferencial: mesma sequência gerada nos dois repositórios, comparando resultado **e** exceção a cada passo
- **Rastreio**: `PBT-U2-01..08`, extensão `property-based-testing` (Full)

### Step 14 — `tests/persistencia/test_sqlite.py` — o que só o real tem
- [x] PRAGMAs efetivos · `user_version` incompatível levanta · `versao_esquema` de documento futuro levanta
- [x] Arquivo corrompido levanta `BancoIlegivel` **na abertura** (`NFR-P-07`)
- [x] Permissões `0o600`/`0o700` (teste marcado para pular em Windows)
- [x] `apagar_ambiente` sem `foreign_keys` deixaria órfão — teste que prova que o pragma está ligado
- [x] Fumaça de `NFR-P-01`: 5.000 anotações carregam dentro do alvo
- **Rastreio**: `NFR-P-01`, `NFR-P-05..07`, `NFR-P-14`, `NFR-P-20`

### Step 15 — Verificação
- [x] **Inspeção `NFR-P-13`**: varrer o código gerado e confirmar que **nenhuma** consulta é montada por concatenação ou f-string — todo valor entra por `?`
- [x] Confirmar por inspeção que `dominio/` não ganhou import novo e que `portas/` não importa `sqlite3`
- [x] `uv run pytest` — registrar o número de testes e o resultado **como saiu**, inclusive se falhar
- [x] `uv sync` — confirmar `dependencies = []` intacto (`NFR-P-12`)
- **Rastreio**: `NFR-P-12`, `NFR-P-13`, `security-baseline`

### Step 16 — `aidlc-docs/construction/persistencia/code/code-summary.md`
- [x] Arquivos criados e modificados, com contagem de linhas
- [x] Resultado real dos testes e da inspeção do Step 15
- [x] Decisões tomadas **durante** a execução que este plano não previu
- [x] O que fica para U9 (abrir e fechar o repositório) e para U4 (tratar `ConflitoDeVersao`)
- **Rastreio**: `code-generation.md` Step 11

---

## 5. Rastreio história → passo

| História / Dívida | Passos que a implementam | Verificada por |
|---|---|---|
| **US-05** — reabrir e reconstituir o ambiente | 1, 2, 5, 6, 7 | `PBT-U2-01`, `PBT-U2-02` (Step 13) |
| **US-06** — transcrição visível e paginada | 2, 8 | `PBT-U2-04`, `PBT-U2-05` (Step 13) |
| **TD-04** — persistência inexistente | 2 a 9 | Steps 13, 14, 15 |
| **CS-01** — fechar e reabrir o processo | 6, 7 | `PBT-U2-01` + fumaça do Step 14 |

---

## 6. O que este plano **não** faz

- **Não remove o código antigo** (`Ambiente/`, `model/`, `cli.py`, `tui.py`). A regra de U1 vale:
  o antigo sai quando o substituto for executável, o que só acontece em U9.
- **Não escreve composition root.** `caminho_do_banco()` existe e é testada, mas ninguém a chama em
  produção ainda — quem chama é U9.
- **Não implementa o throttle de gravação.** Saiu desta unidade no portão anterior; é o critério 6
  de U7 (`DP-P-12`).
- **Não cria migração.** Só existe a versão `1`. O mecanismo que recusa versão futura existe
  (Step 4); o que **converte** entre versões não, porque não há de onde converter.

---

## 7. Escopo

**16 passos.** 6 arquivos novos em `src/`, 8 em `tests/`, 2 arquivos existentes modificados
(`dominio/ambiente.py` e `tests/dominio/test_ambiente.py`), 1 resumo em `aidlc-docs/`.
Nenhuma dependência nova, de runtime ou de desenvolvimento.
