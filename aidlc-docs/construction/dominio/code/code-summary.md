# Code Generation — U1 `dominio` — resumo da execução

**Fase:** CONSTRUCTION · **Unidade:** `U1 dominio` · **Data:** 2026-08-26
**Plano executado:** `aidlc-docs/construction/plans/dominio-code-generation-plan.md` (14/14 passos)

---

## 1. Arquivos criados — código (`src/fishingrod/dominio/`, 491 linhas)

| Arquivo | Linhas | Conteúdo |
|---|--:|---|
| `erros.py` | 33 | `ErroDeDominio`, `NomeInvalido`, `OrquestradorDuplicado`, `AgenteInvalido`, `exigir_texto` |
| `identidade.py` | 28 | `Identidade` (frozen) com `nova()` via `uuid.uuid7()` |
| `agente.py` | 33 | `Papel`, `Agente` (frozen), `e_orquestrador` |
| `memoria.py` | 50 | `Anotacao` (frozen, com `criada_em`), `Memoria` (`anotar`, `versao`) |
| `etapa.py` | 38 | `ExecutorEtapa`, `Etapa` com `concluir`/`reabrir` |
| `chat.py` | 33 | `Chat` com `renomear`; sem mensagens, sem sessão viva |
| `tarefa.py` | 61 | `criar_chat`, `buscar_chat`, `contar_orquestradores`, `criar_etapa`, `buscar_etapa` |
| `frente.py` | 42 | `criar_tarefa(nome, agente_orquestrador)`, `buscar_tarefa` |
| `raiz_wiki.py` | 44 | `RaizWiki` (frozen), `esquema()`, `para_ambiente()`, `LocalizadorInvalido` |
| `ambiente.py` | 47 | `Ambiente` — nasce sem frente, raiz derivada da identidade |
| `politica.py` | 31 | `Chamador`, `APROVACAO_DE_AGENTE_OBRIGATORIA`, `exige_aprovacao` |
| `__init__.py` | 44 | Reexporta 19 nomes públicos |

## 2. Arquivos criados — testes (`tests/dominio/`, 375 linhas, 39 testes)

| Arquivo | Testes que carrega |
|---|---|
| `test_identidade.py` | PBT-U1-01, PBT-U1-02, RN-01 |
| `test_memoria.py` | RN-09 (×2), RN-10, RN-02 (×4), PBT-U1-03, PBT-U1-04 |
| `test_etapa.py` | RN-07, RN-02 (×3), PBT-U1-05 |
| `test_tarefa_e_frente.py` | RN-04, RN-05 (×2), RN-06 (×2), RN-08, RN-14 (×2) |
| `test_ambiente.py` | RN-03, RN-04, RN-11 (×5), PBT-U1-06, PBT-U1-07 |
| `test_politica.py` | RN-12 (×2) |
| `test_fronteira.py` | RN-13 (×2) |

**Diferença declarada em relação ao plano**: o plano previa "9 arquivos de teste"; entreguei **7**,
porque `Tarefa` e `Frente` compartilham as mesmas invariantes (RN-05/RN-06 nascem em uma e vivem na
outra) e separá-las duplicaria o mesmo cenário de montagem. Nenhum teste foi cortado — todas as 15
regras e as 7 propriedades estão cobertas.

## 3. Arquivos modificados

| Arquivo | Mudança |
|---|---|
| `component-methods.md` §1.1 | `Identidade.nova()` usa `uuid.uuid7()` da stdlib |
| `component-methods.md` §1.3 | `criar_tarefa(nome, agente_orquestrador)` — texto anterior riscado |
| `component-methods.md` §1.7 | `Memoria.versao` e classe `Anotacao` com `criada_em` |
| `components.md` §2.2 | `Ambiente` nasce sem frente, com o motivo |

Todas marcadas como emenda, com data e origem; nenhum texto apagado.

**Não modificados, deliberadamente**: `Ambiente/ambiente.py`, `Ambiente/memoria.py`,
`Ambiente/sessao.py`, `Ambiente/agente.py`, `model/`, `cli.py`, `tui.py`. Por Q8=A o código antigo
só morre quando a unidade que o substitui **fecha** — a remoção é assunto da aprovação desta
unidade, não da geração.

---

## 4. Saída real dos testes

```
$ uv run pytest -q
.........................................                                [100%]
41 passed in 0.67s
```

41 = 39 de U1 + 2 de U0. **Passaram na primeira execução**, sem correção intermediária.

### O que passou e não era garantido

**PBT-U1-01 (ordenação de identidades)** dependia de o `uuid.uuid7()` do CPython 3.14 ser monotônico
*dentro do mesmo milissegundo* — sem isso, duas identidades criadas no mesmo instante poderiam
ordenar ao contrário e a paginação de U2 quebraria em transcrições rápidas. A propriedade gera até
200 identidades em sequência e verifica a ordenação textual; passou em 25 exemplos. É a evidência
de que a decisão de ESC-14 (identidade substitui coluna de ordenação) se sustenta na prática.

---

## 5. Critério de pronto de U1 (`unit-of-work.md` §3)

| # | Critério | Estado | Evidência |
|:--:|---|:--:|---|
| 1 | `Memoria.anotar` em chave nova funciona, com propriedade PBT | ✅ | `test_rn_09_anotar_em_chave_inedita_nao_levanta` + PBT-U1-03/04. **TD-03 morta** |
| 2 | Invariantes: frente pertence ao ambiente; tarefa pertence à frente | ✅ | `test_pbt_u1_06`, `test_rn_05_*`, `test_rn_14_*` |
| 3 | Nenhum import de `claude_agent_sdk`, `sqlite3` ou `textual` em `dominio/` | ✅ | `test_fronteira.py` — 2 testes |
| 4 | `Identidade` é UUIDv7, ordenável por tempo, criada no construtor | ✅ | PBT-U1-01, PBT-U1-02 |

### Verificações adicionais (Step 12)

- **Código antigo intacto**: `git status -- Ambiente model cli.py tui.py` não devolve nada
- **Sem duplicatas**: zero arquivos `*_new.py` / `*_modified.py`

---

## 6. Decisões da execução que vale registrar

1. **`test_fronteira.py` inspeciona o grafo de import com `ast`, não `try/except ImportError`.**
   A diferença importa: um teste que só verificasse "o pacote não está instalado" passaria hoje por
   acidente (U0 não instalou nada) e **deixaria de significar qualquer coisa** quando U6 instalasse
   o `claude-agent-sdk`. Lendo o AST de cada módulo de `dominio/`, o que se proíbe é a aresta, e o
   teste continua valendo pelo resto do projeto.
2. **Segundo teste de fronteira, mais forte que o exigido**: `dominio/` só pode importar stdlib
   (`dataclasses`, `enum`, `uuid`, `datetime`, `typing`, `collections`) e ele mesmo. RN-13 pedia
   três nomes proibidos; esta versão pega qualquer dependência de terceiros que alguém tente
   introduzir aqui no futuro — é o que mantém verificável o critério de TD-02 em U6.
3. **`RaizWiki` ganhou `LocalizadorInvalido`**, erro que o Functional Design não nomeou. RN-11 dizia
   "nunca caminho absoluto" sem dizer o que acontece se alguém tentar; a alternativa era aceitar em
   silêncio. Cobre `/`, `\`, e `C:/` (Windows), além de localizador sem esquema.
4. **`Agente.ferramentas` e `regras` são `tuple`, não `list`.** `frozen=True` não congela uma lista
   interna; com tupla, a imutabilidade de RN-15 é real e não decorativa.
5. **`Chat` recebe nome padrão do agente** quando nenhum é passado, em vez de nascer com nome vazio
   e violar RN-02 no próprio construtor.

---

## 7. O que U1 entrega para as próximas unidades

- **U2** tem as entidades a serializar, com `Identidade` já ordenável (paginação sem coluna extra) e
  `Memoria.versao` disponível para bloqueio otimista
- **U4** tem `criar_frente`/`criar_tarefa`/`criar_chat` com as invariantes já garantidas no domínio
- **U5** e **U8** têm `exige_aprovacao(Chamador)` — o ponto único de decisão sobre aprovação
- **U6** tem `Agente` como configuração imutável, com nomes de ferramenta prontos para resolver
