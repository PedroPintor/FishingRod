# Code Generation Plan — U3 `wiki`

**Fase:** CONSTRUCTION · **Unidade:** `U3 wiki` · **Portão 4 de 4** · **Data:** 2026-09-23
**Base:** os 3 artefatos de `functional-design/` (aprovados em 2026-09-23T14:00Z), os 2 de
`nfr-requirements/` (aprovados em 2026-09-23T16:00Z) e os 2 de `nfr-design/` (aprovados em
2026-09-23T17:30Z)
**Estágios da unidade:** FD ✅ · NFR-R ✅ · NFR-D ✅ · INFRA SKIP · **CG EXECUTE**

> **Este plano é a única fonte de verdade da geração de código de U3.** A Parte 2 executa
> exatamente estes passos, na ordem, marcando `[x]` a cada conclusão. Nada fora daqui é gerado.

---

## 1. Contexto da unidade

| Campo | Conteúdo |
|---|---|
| **Histórias** | **US-08** (ambiente novo nasce com wiki, mesmo vazia) e **US-09** (a estrutura da wiki é do dono) |
| **Dívidas que morrem aqui** | Nenhuma |
| **Depende de** | U0 (`uv`, `src/`, pytest, hypothesis) e U1 (`RaizWiki`) — ambas aprovadas |
| **Entrega para** | U4 (`ServicoDeAmbiente`), U8 (`ServicoBibliotecario`), U9 (composition root) |
| **Especificação** | 37 regras `RN-W-01..37` · 7 propriedades `PBT-U3-01..07` · 20 requisitos `NFR-W-01..20` · 12 padrões `DP-W-01..12` |
| **Destino do código** | `src/fishingrod/aplicacao/` e `src/fishingrod/adaptadores/wiki/` |
| **Destino dos testes** | `tests/wiki/` |
| **Dependências novas** | **zero** — `NFR-W-08` / `TS-W-08` permanecem verdadeiros (`pathlib`, `os`, `unicodedata`, `re`, `asyncio`, `logging`, `contextlib`, `tempfile` são stdlib) |

**Interface publicada por esta unidade.** Um arquivo: `aplicacao/portas/wiki.py`. U4, U8 e U9
importam dele — nunca do adaptador (`DP-W-09`). Exceção nomeada: `aplicacao/caminho_wiki.py` é
importável por qualquer unidade **por decisão** (`DP-W-02`), porque produz caminho lógico.

**Critério de pronto de U3** (`unit-of-work.md` §3, com as emendas de 2026-09-23): (1) toda página
escrita pelo app aparece no índice regenerado · (2) nenhuma propriedade com `descricao` vazia ·
~~(3) revogado~~ · (4) o `index.md` nunca é escrito por agente · (5) **PBT-03** nenhum caminho escapa
da raiz · (6) dois níveis estruturalmente irrepresentáveis.

**Baseline de testes antes desta unidade:** `84 passed, 1 skipped`.

---

## 2. Reconciliações entre artefatos aprovados

Divergências que os portões deixaram entre si. A resolução é o que o código segue.

| # | Divergência | Resolução e motivo |
|---|---|---|
| **R-CG3-1** | `unit-of-work.md` §3 e `components.md` §3.7 chamam a classe de **`AdaptadorWikiFilesystem`**; `Q9=A` do NFR Design escolheu **`WikiDeArquivos`** | Vale **`WikiDeArquivos`**. O nome antigo é de Application Design, anterior à decisão de vocabulário; os dois artefatos recebem emenda no passo 16 (texto riscado, nada apagado) |
| **R-CG3-2** | O adaptador recebe `localizador: str`, e U1 já tem `RaizWiki` com `esquema()` e validação própria (`LocalizadorInvalido`) | O adaptador **não constrói `RaizWiki`**: interpreta a string diretamente e levanta `LocalizadorNaoReconhecido` (`RN-W-09`) para esquema diferente de `dados`. Quem cria `RaizWiki` é U4, no domínio. Dois erros parecidos, dois donos distintos: `LocalizadorInvalido` é "o usuário/domínio montou errado"; `LocalizadorNaoReconhecido` é "este adaptador não atende este esquema" |
| **R-CG3-3** | `ConteudoPagina.caminho` — o valor devolvido é o que veio na chamada, ou o normalizado? | O **normalizado** (`caminho_wiki.caminho(...)` sobre os dois segmentos). É o que `PBT-U3-05` torna seguro: passar slug onde se espera título dá o mesmo resultado, então a saída é sempre canônica |
| **R-CG3-4** | `component-methods.md` §3.4 diz que `EsquemaWiki` mora "em `aplicacao/`", sem arquivo | `aplicacao/esquema_wiki.py` (`logical-components.md` §1.1). Não é emenda, é precisão |
| **R-CG3-5** | `business-logic-model.md` §5 diz que a raiz é criada com `0o700`; `NFR-W-07` acrescenta `0o600` para arquivos | Valem os dois, só em POSIX (`os.name == "posix"`). No Windows nada é chamado — é o que já vale para o banco em `NFR-P-14` |

---

## 3. Decisões de implementação declaradas (não perguntadas)

Escolhas de forma que os três portões não fixaram. Reversíveis; se discordar, é agora.

| Decisão | Escolha | Motivo |
|---|---|---|
| **Como o teste chama código `async`** | Auxiliar `executar(coro)` sobre `asyncio.run`, em testes **síncronos**. **Sem `pytest-asyncio`** | Mesma decisão de U2, mesmo motivo: nenhuma dependência nova, e Hypothesis precisaria de laço por exemplo |
| **Normalização do valor de frontmatter** | `normalizar_valor(s)`: colapsa `\r\n`/`\n`/`\t` em espaço, apara as bordas, e remove **um** par de aspas externas balanceadas. Aplicada **na montagem** | Sem isso, um título com quebra de linha quebraria o bloco, e um título literalmente `"x"` voltaria como `x`. Com isso, `PBT-U3-03` vale para **qualquer** entrada, comparando contra o normalizado — e `normalizar(normalizar(x)) == normalizar(x)` |
| **Tabela pré-slug** | Uma entrada: `&` → ` e `. Nada mais | `RN-W-04` exige `Dr. Marcelo & Cia` → `dr-marcelo-e-cia`. Uma tabela maior seria invenção sem regra que a peça |
| **Publicação atômica** | `tempfile.mkstemp(dir=<mesma pasta>)` → escrever → `os.replace` | Mesmo diretório garante mesmo volume, que é a condição de `os.replace` ser atômico no Windows |
| **Teto de `ler_cabecalho`** | 64 linhas, constante nomeada no módulo | `NFR-W-01` |
| **Permissões** | `os.chmod` após criar diretório (`0o700`) e após escrever arquivo (`0o600`), envolto em `if os.name == "posix"` | `R-CG3-5` |
| **Logger** | `logging.getLogger("fishingrod.wiki")` com `NullHandler` no `__init__.py` do pacote | `NFR-W-16`, igual a `TS-P-07` |
| **Nome de teste** | `test_rn_w_07_*`, `test_pbt_u3_01_*`, `test_nfr_w_02_*` | Convenção de U1 e U2: o nome diz qual regra quebrou |
| **Layout dos testes** | `tests/wiki/` com `__init__.py`, espelhando `tests/persistencia/` | Mantém `tests/` como pacote |
| **Reexportação** | `adaptadores/wiki/__init__.py` exporta `WikiDeArquivos` | U9 escreve um import só |
| **Ordenação** | `sorted()` sobre os slugs, que são ASCII puro depois de `RN-W-04` | `RN-W-21` — ordem estável entre plataformas, independente do filesystem |

---

## 4. Os passos

### Camada de aplicação

- [x] **Passo 1** — `src/fishingrod/aplicacao/portas/wiki.py`: `PortaWiki` (`Protocol`, 4 operações),
      `ConteudoPagina`, `PaginaProposta`, `PropostaWiki`, `ErroDeWiki` + as 7 subclasses.
      Sem `pathlib`, sem `os`. `DP-W-09` · **US-08, US-09**
- [x] **Passo 2** — `src/fishingrod/aplicacao/caminho_wiki.py`: `slug()`, `caminho()`,
      `normalizar_valor()`, a lista de nomes reservados do Windows. Sem `pathlib`. `DP-W-02`,
      `RN-W-04`, `RN-W-05`
- [x] **Passo 3** — `src/fishingrod/aplicacao/esquema_wiki.py`: `PropriedadeSemente`,
      `EntidadeSemente`, `EsquemaWiki` com `vazio()` e `a_partir_do_formulario()`. **US-09**
- [x] **Passo 4** — `tests/wiki/__init__.py` e `tests/wiki/estrategias.py`: geradores Hypothesis,
      o **alfabeto hostil** compartilhado e `executar(coro)`. `DP-W-12`
- [x] **Passo 5** — `tests/wiki/test_caminhos.py`, parte de slug: `RN-W-04`, `RN-W-05` e
      **`PBT-U3-05`** (`slug(slug(x)) == slug(x)`), sem tocar disco

### Adaptador

- [x] **Passo 6** — `src/fishingrod/adaptadores/wiki/caminhos.py`: `resolver_raiz()` e
      `resolver_sob()`. **O arquivo de segurança.** `DP-W-01`, `RN-W-07`, `RN-W-09`, `NFR-W-05/06`
- [x] **Passo 7** — `tests/wiki/test_caminhos.py`, parte de confinamento: `RN-W-07` em unidade e
      **`PBT-U3-01`** (título hostil, toda plataforma) · o caso **symlink** em teste próprio
      marcado `skipif`. `NFR-W-18`
- [x] **Passo 8** — `src/fishingrod/adaptadores/wiki/frontmatter.py`: `montar()`,
      `ler_cabecalho()`, `ler_pagina()`, com a gramática de `RN-W-11/15/16` escrita **uma vez no
      topo**. `DP-W-06`
- [x] **Passo 9** — `tests/wiki/test_frontmatter.py`: as duas leituras, **`PBT-U3-07`** (corpo com
      `---`) e a **propriedade dedicada de concordância** exigida por `DP-W-06`/`NFR-W-20`
- [x] **Passo 10** — `src/fishingrod/adaptadores/wiki/indice.py`: `montar_indice()`, **função
      pura**. `DP-W-07`, `RN-W-18`, `RN-W-19`
- [x] **Passo 11** — `tests/wiki/test_indice.py`: a gramática, a wiki vazia
      (`(vazio — ainda não tem nenhuma entidade)`), a entidade sem propriedade (`(sem propriedades)`),
      a ordenação de `RN-W-21` — tudo sem disco
- [x] **Passo 12** — `src/fishingrod/adaptadores/wiki/wiki_de_arquivos.py`: `WikiDeArquivos` com as
      4 operações, `traduzindo_erros()` e `escrever_atomico()`. `DP-W-03/04/05/10`
- [x] **Passo 13** — `src/fishingrod/adaptadores/wiki/__init__.py`: reexporta `WikiDeArquivos` e
      instala o `NullHandler` do logger

### Verificação

- [x] **Passo 14** — `tests/wiki/test_wiki_de_arquivos.py`: as 4 operações contra `tmp_path`, os 7
      erros nomeados, a criação da raiz por `renderizar_index`, o `os.replace` do índice, as
      permissões POSIX (`skipif` no Windows) e o **sensor de `NFR-W-02`** rodando na suíte padrão
      (`DP-W-11`)
- [x] **Passo 15** — `tests/wiki/test_propriedades.py`: **`PBT-U3-02`** (índice determinístico e
      idempotente, bytes idênticos), **`PBT-U3-03`** (round-trip), **`PBT-U3-04`** (o índice lista
      exatamente o que foi escrito), **`PBT-U3-06`** (profundidade > 2 irrepresentável)
- [x] **Passo 16** — Emendas e fechamento: aplicar `R-CG3-1` em `unit-of-work.md` §3 e
      `components.md` §3.7 (texto riscado, nada apagado); rodar `uv run pytest`; escrever
      `aidlc-docs/construction/wiki/code/code-summary.md` com evidências, decisões tomadas durante a
      execução e o resultado da suíte

---

## 5. Rastreio — cada especificação tem passo

| Especificação | Passo |
|---|---|
| `RN-W-01`, `RN-W-02` (dois níveis) | 6, 12, 15 |
| `RN-W-03..06` (slug e nomes) | 2, 5 |
| **`RN-W-07..10` (confinamento)** | **6, 7** |
| `RN-W-11..16` (frontmatter) | 8, 9 |
| `RN-W-17..25` (índice) | 10, 11, 12, 15 |
| `RN-W-26..32` (escrita) | 12, 14 |
| `RN-W-33..35` (links) | — nenhum: validação de link é de **U8** (`RN-W-34`) |
| `RN-W-36..37` (vocabulário) | 1, 12 |
| `PBT-U3-01` | 7 |
| `PBT-U3-02`, `03`, `04`, `06` | 15 |
| `PBT-U3-05` | 5 |
| `PBT-U3-07` | 9 |
| `NFR-W-01..04` (desempenho) | 8, 12, 14 |
| `NFR-W-05..10` (segurança) | 6, 7, 12, 14 |
| `NFR-W-11..15` (confiabilidade) | 12, 14 |
| `NFR-W-16..17` (observabilidade) | 12, 13 |
| `NFR-W-18..20` (testes) | 4, 7, 9, 15 |
| `DP-W-01..12` | 6, 2, 12, 12, 12, 8, 10, 12, 1, 12, 14, 4 |

**16 passos.** 8 arquivos novos em `src/` (3 na aplicação, 5 no adaptador incluindo `__init__.py`),
7 em `tests/`, 2 artefatos aprovados emendados, 1 resumo de código. Nenhum arquivo existente é
modificado além das emendas de documentação — **o código antigo (`Ambiente/`, `model/`, `cli.py`,
`tui.py`) permanece intocado**, pela regra emendada em `unit-of-work.md` §4: o antigo sai quando o
substituto for executável, não quando a unidade fecha.

---

## 6. Registro da execução (2026-10-01)

**16/16 passos executados.** Resultado e decisões completos em
`construction/wiki/code/code-summary.md`. O que divergiu deste plano, e por quê, em uma linha cada:

- **`normalizar_valor`** tira aspas externas **até não sobrar par**, e não "um par": com um só, o
  round-trip e a idempotência prometidos na §3 quebravam (`'""x""'`). Resumo §4, decisão 1.
- **Emenda `R-CG3-1`** aplicada em `components.md` **§5.3**, não §3.7: a §3.7 é a do `EsquemaWiki`.
- **`resolver_sob` recebe a raiz já resolvida** e a listagem usa `os.scandir` — otimização medida
  contra `NFR-W-02`, sem mudar a regra (`NFR-W-05` continua: cada arquivo passa por `resolve()`).
- **Geradores endurecidos por mutação** (resumo §5): três defeitos injetados escapavam das
  propriedades como escritas no passo 4.
- **Dois achados que dependem de decisão do usuário** (resumo §3): o sensor `NFR-W-02` falha dentro
  da suíte nesta máquina; e `PBT-U2-08`, de U2, tem defeito latente no teste. Nenhum dos dois foi
  "resolvido" por conta própria.
