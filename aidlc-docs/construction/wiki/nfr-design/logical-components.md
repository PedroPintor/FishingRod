# Logical Components — U3 `wiki`

**Fase:** CONSTRUCTION · **Unidade:** `U3 wiki` · **Portão 3 de 4** · **Data:** 2026-09-23
**Decisões:** Q1=A (quatro módulos no adaptador), Q2=B (slug na aplicação), Q3=B (`pasta_de_dados()`
fica onde está), Q5=B (dois leitores), Q9=A (`adaptadores/wiki/`, `WikiDeArquivos`)

Este documento diz **quais arquivos existem, o que cada um pode importar, e por quê**.
Nenhuma linha de código é escrita aqui — isso é o portão 4.

---

## 1. Os arquivos

### 1.1 Na camada de aplicação

```
src/fishingrod/aplicacao/portas/wiki.py
src/fishingrod/aplicacao/caminho_wiki.py
src/fishingrod/aplicacao/esquema_wiki.py
```

| Arquivo | Conteúdo | Papel |
|---|---|---|
| `portas/wiki.py` | `PortaWiki` (`Protocol`, ~~4~~ **5** operações) · `ConteudoPagina`, `PaginaProposta`, `PropostaWiki` · `ErroDeWiki` e as **7** subclasses | `DP-W-09` — o **único** arquivo de U3 que U4, U8 e U9 importam |
| `caminho_wiki.py` | `slug(titulo) -> str` · `caminho(entidade, propriedade) -> str` · a lista de nomes reservados do Windows | `DP-W-02` — produz o **caminho lógico**, que é vocabulário da porta |
| `esquema_wiki.py` | `PropriedadeSemente`, `EntidadeSemente`, `EsquemaWiki` com `vazio()` e `a_partir_do_formulario()` | O que o formulário de criação (US-09) produz e U4 materializa |

> **/!\ Emenda 2026-10-02 — Code Generation de U4 `ambiente`.** `PortaWiki` ganhou a quinta
> operação, **`apagar(localizador)`** (Q6=A do FD de U4), implementada em `WikiDeArquivos`. Usa o
> mesmo `resolver_raiz` (`DP-W-01`), não segue link, e só remove uma raiz que tenha `index.md`
> (`R-CG4-2`). Nenhum módulo novo e nenhuma aresta nova na matriz: o adaptador passou a importar
> `shutil`, da stdlib. Semântica em `construction/ambiente/functional-design/domain-entities.md` §5.

**Podem importar:** `dataclasses`, `typing`, `unicodedata`, `re`.
**Não podem importar:** `pathlib`, `os`, `open`, nada de `adaptadores/`.

> `caminho_wiki.py` **não importa `pathlib`** de propósito: ele manipula string de caminho lógico,
> não caminho de sistema. No dia em que importar, a fronteira terá vazado.

### 1.2 No adaptador

```
src/fishingrod/adaptadores/wiki/__init__.py
src/fishingrod/adaptadores/wiki/caminhos.py
src/fishingrod/adaptadores/wiki/frontmatter.py
src/fishingrod/adaptadores/wiki/indice.py
src/fishingrod/adaptadores/wiki/wiki_de_arquivos.py
```

| Arquivo | Conteúdo | Notas |
|---|---|---|
| `caminhos.py` | `resolver_sob(raiz: Path, caminho_logico: str) -> Path` · `resolver_raiz(raiz_de_dados, localizador) -> Path` | **O arquivo de segurança da unidade.** Pequeno, sem I/O além de `resolve()`. Alvo direto de `PBT-U3-01` |
| `frontmatter.py` | `montar(titulo, descricao, conteudo) -> str` · `ler_cabecalho(caminho) -> tuple[str, str]` · `ler_pagina(caminho) -> tuple[str, str, str]` | `DP-W-06`. A gramática de `RN-W-11/15/16` fica escrita **uma vez, no topo**, com as duas funções abaixo dela |
| `indice.py` | `montar_indice(nome, entidades) -> str` | `DP-W-07` — **função pura**: recebe dados já lidos, devolve texto. Testável sem disco |
| `wiki_de_arquivos.py` | `WikiDeArquivos` · `traduzindo_erros(...)` · `escrever_atomico(caminho, texto)` | A casca `async` (`DP-W-03`), a tradução de erro (`DP-W-04`) e a publicação atômica (`DP-W-05`) |

**Podem importar:** `aplicacao/portas/wiki.py`, `aplicacao/caminho_wiki.py`, `dominio/raiz_wiki.py`,
`pathlib`, `os`, `asyncio`, `logging`, `contextlib`.
**Não podem importar:** nada de `adaptadores/persistencia/` (`R-FD3-1`, `DP-W-08`), nada de
`interface/`.

### 1.3 Nos testes

```
tests/wiki/__init__.py
tests/wiki/estrategias.py
tests/wiki/test_caminhos.py
tests/wiki/test_frontmatter.py
tests/wiki/test_indice.py
tests/wiki/test_wiki_de_arquivos.py
tests/wiki/test_propriedades.py
```

Espelha `tests/persistencia/` (`R-ND3-2`). **Não existe `tests/dobles/wiki.py`** (`NFR-W-19`):
U4 e U8 testam contra `WikiDeArquivos` real sobre `tmp_path`.

| Arquivo | O que carrega |
|---|---|
| `estrategias.py` | Geradores Hypothesis, incluindo o **alfabeto hostil** compartilhado (`DP-W-12`) e o helper `executar(coro)` |
| `test_caminhos.py` | Confinamento e slug em unidade, sem I/O de wiki |
| `test_frontmatter.py` | As duas leituras **e a propriedade de concordância** exigida por `DP-W-06` |
| `test_indice.py` | A gramática de `RN-W-18` como texto, sem disco |
| `test_wiki_de_arquivos.py` | As 4 operações contra `tmp_path`, mais o sensor de `NFR-W-02` (`DP-W-11`, roda sempre) |
| `test_propriedades.py` | `PBT-U3-01..07`, com o caso de symlink em teste próprio marcado `skipif` (`NFR-W-18`) |

O perfil de Hypothesis já existente em `tests/conftest.py` (`deadline=None`) cobre esta unidade sem
mudança (`R-ND3-3`).

---

## 2. Matriz de dependência

`→` significa "importa". A matriz é triangular: **não há ciclo**.

| De ↓ / Para → | `dominio/` | `portas/wiki` | `caminho_wiki` | `caminhos` | `frontmatter` | `indice` |
|---|:--:|:--:|:--:|:--:|:--:|:--:|
| `aplicacao/portas/wiki.py` | — | — | — | — | — | — |
| `aplicacao/caminho_wiki.py` | — | — | — | — | — | — |
| `aplicacao/esquema_wiki.py` | — | — | — | — | — | — |
| `adaptadores/wiki/caminhos.py` | — | — | **→** | — | — | — |
| `adaptadores/wiki/frontmatter.py` | — | — | — | — | — | — |
| `adaptadores/wiki/indice.py` | — | — | — | — | — | — |
| `adaptadores/wiki/wiki_de_arquivos.py` | **→** | **→** | **→** | **→** | **→** | **→** |

Três dos quatro módulos do adaptador **não importam nada do projeto**: `frontmatter.py` e
`indice.py` são pura manipulação de texto, e `caminhos.py` importa só o slug. Toda a costura está
em `wiki_de_arquivos.py`, que é o único que conhece `asyncio`.

---

## 3. Composição — quem monta o quê (`DP-W-08`)

```
U9 (composition root)
  raiz_de_dados = pasta_de_dados()            # de adaptadores/persistencia/localizacao.py
  wiki = WikiDeArquivos(raiz_de_dados)
  servico_ambiente = ServicoDeAmbiente(repositorio, wiki, ...)
  servico_bibliotecario = ServicoBibliotecario(wiki, ...)
```

**`WikiDeArquivos` recebe a raiz de dados, não a raiz da wiki.** A raiz da wiki depende do
ambiente, e chega em cada chamada pelo `localizador` (`dados:wikis/<id>`), que `resolver_raiz`
traduz. Um adaptador serve todos os ambientes.

### A dívida que Q3=B deixa registrada

`pasta_de_dados()` continua em `adaptadores/persistencia/localizacao.py`, e o docstring dela já diz
que serve a U3. **Nenhum adaptador importa outro adaptador**: quem lê de lá é **U9**, que é
composition root e pode conhecer os dois.

O que fica torto é o **nome do pacote**, não o comportamento: uma função que localiza os dados do
usuário mora num pacote chamado `persistencia`. Custo de mover agora: emendar uma unidade fechada,
com 84 testes passando, para obter em tempo de execução exatamente o mesmo resultado. **Dívida
aceita e escrita** — o momento natural de pagá-la é quando um terceiro consumidor aparecer.

---

## 4. O que **não** existe nesta unidade

| Não existe | Por quê |
|---|---|
| `tests/dobles/wiki.py` | `NFR-W-19`, Q9=A — `tmp_path` já é o duplo, e é o real |
| Cache de índice ou de página | `RN-W-17` — o disco é o estado inteiro |
| Fila, worker, pool próprio | `DP-W-03` — o pool do `asyncio` já é o pool |
| Retry, circuit breaker, timeout | `resiliency-baseline` desativada; não há chamada remota |
| Trava de arquivo | Q7=A do Functional Design, `NFR-W-15` |
| Qualquer dependência nova em `pyproject.toml` | `TS-W-08` — `dependencies = []` permanece |

---

## 5. Rastreio dos padrões aos arquivos

| Padrão | Arquivo |
|---|---|
| `DP-W-01` ponto único de resolução | `adaptadores/wiki/caminhos.py` |
| `DP-W-02` slug na aplicação | `aplicacao/caminho_wiki.py` |
| `DP-W-03` fio síncrono, casca `async` | `adaptadores/wiki/wiki_de_arquivos.py` |
| `DP-W-04` tradução de erro | `adaptadores/wiki/wiki_de_arquivos.py` |
| `DP-W-05` publicação atômica | `adaptadores/wiki/wiki_de_arquivos.py` |
| `DP-W-06` dois leitores + concordância | `adaptadores/wiki/frontmatter.py` + `tests/wiki/test_frontmatter.py` |
| `DP-W-07` índice puro | `adaptadores/wiki/indice.py` |
| `DP-W-08` raiz injetada | construtor de `WikiDeArquivos`; composição em U9 |
| `DP-W-09` porta é a fronteira | `aplicacao/portas/wiki.py` |
| `DP-W-10` validar antes de escrever | `WikiDeArquivos.escrever_proposta` |
| `DP-W-11` sensor na suíte padrão | `tests/wiki/test_wiki_de_arquivos.py` |
| `DP-W-12` alfabeto hostil | `tests/wiki/estrategias.py` |
