# Logical Components — U2 `persistencia`

**Fase:** CONSTRUCTION · **Unidade:** `U2 persistencia` · **Portão 3 de 4** · **Data:** 2026-08-27
**Decisões:** Q11=A (cinco módulos), Q12=B (dublê em `tests/`), Q6=A (erros junto da porta)

Este documento diz **quais arquivos existem, o que cada um pode importar, e por quê**.
Nenhuma linha de código é escrita aqui — isso é Code Generation.

---

## 1. Os arquivos

### 1.1 Na camada de aplicação

```
src/fishingrod/aplicacao/portas/persistencia.py
```

| Conteúdo | Papel |
|---|---|
| `PortaPersistencia` (`Protocol`) | As 9 operações do contrato (`business-logic-model.md` §1) |
| `ResumoAmbiente`, `MensagemPersistida`, `UsoDeFerramenta` | Tipos de saída que não são entidades de domínio |
| `ErroDePersistencia` e as ~~4~~ **5** subclasses | `DP-P-11` — a quinta, `AmbienteInexistente`, é emenda de 2026-08-27 (`RN-P-27`) |

**Pode importar:** `dominio/`, `typing`, `dataclasses`, `datetime`.
**Não pode importar:** `sqlite3`, `json`, nada de `adaptadores/`.

É o único arquivo desta unidade que U4, U7 e U8 vão importar.

---

### 1.2 No adaptador — `src/fishingrod/adaptadores/persistencia/`

| Arquivo | Responsabilidade única | Muda quando |
|---|---|---|
| `__init__.py` | Exporta `abrir_repositorio` e `RepositorioSQLite` | Nunca, na prática |
| `localizacao.py` | `caminho_do_banco() -> Path` — a pasta de dados do SO (`DP-P-05`) | Um SO novo, ou uma convenção que mudou |
| `esquema.py` | DDL, PRAGMAs, as duas versões (`DP-P-07`) e sua verificação | O esquema físico muda |
| `mapeamento.py` | `Ambiente` ↔ dicionário JSON (`DP-P-06`) | O domínio ganha campo, ou o formato do documento muda |
| `repositorio_sqlite.py` | `abrir_repositorio`, `RepositorioSQLite`, `_ler`/`_escrever` e os `_x_sync` | Uma operação da porta é acrescentada ou muda de semântica |

**Cada arquivo tem um motivo distinto para mudar** — é isso que `Q11=A` comprou sobre `Q11=B`. Um
esquema alterado não faz `git diff` no mapeamento; uma convenção de pasta de SO não toca em SQL.

**Podem importar:** `sqlite3`, `json`, `asyncio`, `pathlib`, `os`, `logging`, `uuid`, `dominio/`,
`aplicacao/portas/persistencia`.
**Não podem importar:** `aplicacao/servicos/`, `interface/`, `adaptadores/` de outras unidades.

---

### 1.3 Nos testes

| Arquivo | Papel |
|---|---|
| `tests/dobles/__init__.py` | **Obrigatório** — é o que mantém `tests.dobles` importável (`DP-P-10`) |
| `tests/dobles/repositorio_memoria.py` | `RepositorioEmMemoria`, escrito à mão (`DP-P-10`) |
| `tests/conftest.py` | Perfil Hypothesis com `deadline=None` (`NFR-P-21`) |
| `tests/persistencia/test_contrato.py` | `PBT-U2-08` — as duas implementações sob a mesma bateria |
| `tests/persistencia/test_*.py` | `PBT-U2-01..07` e os casos de exemplo |

**Sobre `tests/dobles/` (Q12=B).** Eu havia recomendado publicar o dublê como código de produção,
alegando que importar de dentro de `tests/` funcionaria só por acidente de `sys.path`. Verifiquei
antes de acatar: `tests/` já é pacote, o pytest insere a raiz do projeto no caminho e
`import tests.dominio` funciona hoje — 41 testes coletados. A objeção era mais fraca do que eu a
enunciei. A escolha mantém o pacote instalado livre de código que só serve a teste, e a **condição
que a sustenta está registrada acima**: se `tests/dobles/__init__.py` faltar, os testes de U4, U7 e
U8 param de achar o dublê.

---

## 2. Como uma operação atravessa os componentes

```
  U4 / U7 / U8  (chamador assíncrono)
        │
        │  await repo.salvar_ambiente(ambiente)
        ▼
┌──────────────────────────────────────────────────────────────┐
│  RepositorioSQLite                     repositorio_sqlite.py │
│                                                              │
│   salvar_ambiente(a)                                         │
│      └─► _escrever(lambda cur: self._salvar_sync(cur, a))    │
│             │                                                │
│             ├─ async with self._lock          ← NFR-P-09     │
│             └─ await asyncio.to_thread(...)   ← NFR-P-08     │
│                   │                                          │
│                   │  (daqui para baixo, tudo síncrono:       │
│                   │   nenhum ponto de await no meio)         │
│                   ▼                                          │
│                BEGIN IMMEDIATE                ← NFR-P-10     │
│                   │                                          │
│                   ├─► _salvar_sync(cursor, ambiente)         │
│                   │      ├─ mapeamento.documento_de(a)  ─────┼──► mapeamento.py
│                   │      ├─ SELECT versao  (com ?)           │
│                   │      ├─ compara → ConflitoDeVersao?      │
│                   │      └─ UPDATE / INSERT  (com ?)         │
│                   │                                          │
│                COMMIT          ou   ROLLBACK + log  ← DP-P-09│
└──────────────────────────────────────────────────────────────┘
        │                                    │
        ▼                                    ▼
   None (sucesso)                    ConflitoDeVersao
                                     (definido em aplicacao/portas)
```

Duas coisas para ler neste desenho:

1. **A transação começa e termina dentro de um único `to_thread`.** Não há onde outra corrotina
   intercalar — é a garantia estrutural de `NFR-P-08`, e o motivo de `Q13=B` no portão anterior.
2. **O `ROLLBACK` e o `log` estão no mesmo lugar.** Toda falha desta unidade passa por essas duas
   linhas, o que faz `NFR-P-18` ("registrar apenas falha e conflito") acontecer sem que nenhum
   método precise lembrar disso.

---

## 3. Quem depende de quem

| De → Para | `dominio/` | `portas/persistencia` | `esquema` | `mapeamento` | `localizacao` |
|---|:--:|:--:|:--:|:--:|:--:|
| `portas/persistencia` | ✔ | — | ✖ | ✖ | ✖ |
| `repositorio_sqlite` | ✔ | ✔ | ✔ | ✔ | ✖ |
| `mapeamento` | ✔ | ✖ | ✖ | — | ✖ |
| `esquema` | ✖ | ✖ | — | ✖ | ✖ |
| `localizacao` | ✖ | ✖ | ✖ | ✖ | — |
| composition root (U9) | ✔ | ✔ | ✖ | ✖ | ✔ |
| `tests/dobles/repositorio_memoria` | ✔ | ✔ | ✖ | ✖ | ✖ |

Matriz triangular: **não há ciclo**. `esquema` e `localizacao` não dependem de nada do projeto —
são testáveis sozinhos, sem banco e sem domínio.

`repositorio_sqlite` **não** importa `localizacao`: quem resolve o caminho é o composition root, e é
por isso que todo teste passa um `tmp_path` sem monkeypatch (`DP-P-05`).

---

## 4. O esquema físico, em uma tela

```
ambiente            (documento JSON + versao + versao_esquema)
   ▲
   │ ON DELETE CASCADE          ← só age com PRAGMA foreign_keys = ON (NFR-P-06)
   ├── anotacao    (id_ambiente, id_tarefa, chave, autor, texto, criado_em)
   ├── mensagem    (id_ambiente, id_chat, papel, texto, em_andamento)
   │      ▲
   │      │ ON DELETE CASCADE
   │      └── uso_ferramenta  (id_mensagem, tool, args_resumo, criado_em)
   └──────────┘

PRAGMA user_version = 1        ← esquema físico   (DP-P-07)
coluna versao_esquema = 1      ← formato do JSON  (DP-P-07, RN-P-02 emendada)

índices:  idx_anotacao_ambiente (id_ambiente, id_tarefa, id)
          idx_mensagem_chat     (id_chat, id)
```

`uso_ferramenta` não tem `resultado_resumo` — removida pela `Q6` do portão anterior.

O `id` de toda tabela é **UUIDv7**, e é ele que ordena: não há coluna de sequência (`ESC-14`).
`idx_mensagem_chat` é o que faz `NFR-P-04` ser função de `limite`, não do tamanho do chat.

---

## 5. Componentes de infraestrutura: nenhum

`Infrastructure Design` é **SKIP** para toda unidade desta iteração — não há deploy, servidor,
fila, cache, ou serviço de nuvem. O único recurso externo é **um arquivo no disco local**, e o
componente que o administra é `abrir_repositorio` (`DP-P-01`).

`DP-P-13` registra, um a um, os componentes de infraestrutura que foram considerados e recusados,
com o motivo de cada recusa.

---

## 6. Contagem

| | |
|---|--:|
| Arquivos novos em `src/` | **6** (1 porta + 5 adaptador) |
| Arquivos novos em `tests/` | **4+** (dublê, `__init__`, `conftest`, testes) |
| Arquivos de U1 modificados | **1** (`ambiente.py`, ganhando `versao`) |
| Dependências novas | **0** — `NFR-P-12` intacto |
