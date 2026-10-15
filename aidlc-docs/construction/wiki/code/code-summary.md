# Code Summary — U3 `wiki`

**Fase:** CONSTRUCTION · **Unidade:** `U3 wiki` · **Portão 4 de 4, Parte 2** · **Data:** 2026-10-01
**Plano executado:** `construction/plans/wiki-code-generation-plan.md` — **16/16 passos**

---

## 1. Resultado

```
uv run pytest     ->  ~~270 passed, 7 skipped, 2 failed~~   (era 84 passed, 1 skipped)
                      272 passed, 7 skipped               (2026-10-02, depois de D1=A e D2=A)
pyproject.toml    ->  dependencies = []                  (pyproject.toml e uv.lock sem diff)
```

> **Atualização de 2026-10-02 — as duas falhas da §3 foram resolvidas por decisão do usuário**
> (`construction/plans/wiki-cg-decisoes.md`): **D1=A**, o orçamento de `NFR-W-02` subiu para
> **≤ 1 s** (emenda em `nfr-requirements.md` e `nfr-design-patterns.md`); **D2=A**, `PBT-U2-08`
> passou a usar um instante fixo na operação `anotar` (emenda registrada em
> `construction/persistencia/code/code-summary.md` §6). Só testes mudaram; nenhum código de
> produção foi tocado.

**As duas falhas não são defeito do código de produção de U3**, e as duas precisam de decisão sua —
estão na §3. Em resumo: o sensor de desempenho `NFR-W-02` estoura os 500 ms quando roda dentro da
suíte nesta máquina (passa sozinho, 8 de 8); e `PBT-U2-08`, de **U2**, tem um defeito latente no
próprio teste, que o Hypothesis só agora sorteou.

| | |
|---|--:|
| Testes novos | **194** (85 → 279) |
| Linhas em `src/` | **1.059** |
| Linhas em `tests/` | **1.846** |
| Dependências novas | **0** |

Os 7 pulados, todos nomeados: 5 de symlink (`NFR-W-18` — o Windows desta máquina recusa criar
symlink sem privilégio, WinError 1314), 1 de permissão POSIX de U3 (`R-CG3-5`) e o de U2 que já
existia (`NFR-P-14`).

---

## 2. Arquivos

### Criados em `src/`

| Arquivo | Linhas | Conteúdo |
|---|--:|---|
| `aplicacao/portas/wiki.py` | 186 | `PortaWiki` (~~4~~ **5** operações), 3 tipos de fronteira, `ErroDeWiki` + 7 subclasses (`DP-W-09`) |
| `aplicacao/caminho_wiki.py` | 99 | `slug`, `slug_valido`, `caminho`, `normalizar_valor`, os 22 nomes reservados (`DP-W-02`) |
| `aplicacao/esquema_wiki.py` | 76 | `PropriedadeSemente`, `EntidadeSemente`, `EsquemaWiki` com `vazio()` e `a_partir_do_formulario()` |
| `adaptadores/wiki/__init__.py` | 17 | reexporta `WikiDeArquivos`; instala o `NullHandler` de `fishingrod.wiki` |
| `adaptadores/wiki/caminhos.py` | 89 | `resolver_raiz`, `resolver_sob` — **o arquivo de segurança** (`DP-W-01`) |
| `adaptadores/wiki/frontmatter.py` | 148 | a gramática escrita uma vez no topo; `montar`, `ler_cabecalho`, `ler_pagina` (`DP-W-06`) |
| `adaptadores/wiki/indice.py` | 48 | `montar_indice`, função pura (`DP-W-07`) |
| `adaptadores/wiki/wiki_de_arquivos.py` | 396 | `WikiDeArquivos`, `traduzindo_erros`, `escrever_atomico` (`DP-W-03/04/05/10`) |

### Criados em `tests/wiki/`

| Arquivo | Testes | O que carrega |
|---|--:|---|
| `estrategias.py` | — | `executar`, alfabeto hostil (`DP-W-12`), geradores de título, descrição, corpo e proposta |
| `test_caminhos.py` | 89 | `RN-W-04/05`, **`PBT-U3-05`**, `RN-W-07/09`, **`PBT-U3-01`** (camada de unidade), symlink `skipif` |
| `test_frontmatter.py` | 38 | `RN-W-11/13/15/16`, `NFR-W-01`, **`PBT-U3-07`**, as **duas** propriedades de concordância (`NFR-W-20`) |
| `test_indice.py` | 6 | `RN-W-18/19/21`, sem disco |
| `test_wiki_de_arquivos.py` | 57 | as ~~4~~ **5** operações, os 7 erros, `US-08`/`US-09` de ponta a ponta, `NFR-W-03/06/07/10/11/13/16/17`, sensor `NFR-W-02` |
| `test_propriedades.py` | 4 | **`PBT-U3-02`, `03`, `04`, `06`** (a 06 carrega a camada de ponta a ponta da 01) — e, desde U4, **`PBT-U3-08`** |

> **/!\ Emenda 2026-10-02 — U3 reaberta pelo Code Generation de U4 (Q6=A do FD de U4).** Acréscimo
> de uma operação, sem mudar nenhuma das quatro anteriores:
> - `aplicacao/portas/wiki.py`: **`apagar(localizador)`** no `Protocol`;
> - `adaptadores/wiki/wiki_de_arquivos.py`: `apagar` / `_apagar` — `resolver_raiz`, raiz inexistente
>   é operação vazia, raiz sem `index.md` é `CaminhoForaDaRaiz` (`R-CG4-2`), `shutil.rmtree` dentro de
>   `traduzindo_erros`;
> - `tests/wiki/test_wiki_de_arquivos.py`: **+8 testes** (57 → 65), entre eles o de link para fora da
>   wiki com **junction** — a possibilidade que a §5 abaixo deixou registrada, agora executada: roda
>   nesta máquina, sem privilégio;
> - `tests/wiki/test_propriedades.py`: **`PBT-U3-08`** (4 → 5), `apagar` idempotente e sem tocar o
>   vizinho (`R-CG4-4`, exigida por `PBT-04`).
>
> Detalhes em `construction/ambiente/code/code-summary.md`.

### Emendados (texto riscado, nada apagado)

| Artefato | Emenda |
|---|---|
| `inception/application-design/unit-of-work.md` §3 | `R-CG3-1`: ~~`AdaptadorWikiFilesystem`~~ **`WikiDeArquivos`**, com nota de correspondência |
| `inception/application-design/components.md` **§5.3** | `R-CG3-1`, idem. O plano dizia §3.7, mas a §3.7 é a do `EsquemaWiki`; a classe é definida na §5.3. A nota também registra que a validação de link listada ali foi para U8 (`RN-W-34`) |

**Nada do código antigo foi removido nem tocado.** `Ambiente/`, `model/`, `cli.py` e `tui.py` saem
quando o substituto for executável (U9), pela regra emendada em `unit-of-work.md` §4. **Nada de U2
foi modificado** — inclusive o teste da §3.2.

---

## 3. O que precisa da sua decisão

### 3.1 O sensor `NFR-W-02` não fecha nesta máquina dentro da suíte

**O que acontece.** O teste mede uma aprovação (10 páginas escritas + índice renderizado) numa wiki
de 500 páginas, contra ≤ 500 ms, rodando na suíte padrão (`DP-W-11`).

| Contexto | Resultado |
|---|---|
| Sozinho, 8 execuções | **8 de 8 passam** (teste inteiro em 0,73–0,87 s, incluindo montar as 500 páginas) |
| Dentro da suíte, 5 execuções | **5 de 5 falham**: 521, 615, 620 ms e duas outras acima de 500 |

**Por quê.** Esta máquina alterna entre dois regimes, e o segundo é provocado pelo próprio I/O da
suíte (as propriedades com disco rodam antes do sensor):

| Medida (500 arquivos) | Regime normal | Regime lento |
|---|--:|--:|
| `os.stat` | 8 ms | 50 ms |
| `os.path.realpath` | 32 ms | 215 ms |
| abrir + ler o cabeçalho | 22 ms | 135 ms |
| laço de CPU puro (referência) | 1× | ~2× |
| **renderização inteira** | **~95 ms** | **~490 ms** |
| **aprovação (escrita + renderização)** | **~140–280 ms** | **~520–870 ms** |

O I/O de metadados fica 6–7× mais lento enquanto a CPU só dobra — assinatura de filtro de sistema de
arquivos (antivírus ou similar). Não é algo que o código controle.

**O piso.** `NFR-W-05` exige `resolve()` em cada arquivo. No Windows, `os.path.realpath` chama
`_getfinalpathname` **duas vezes** (verificado na fonte do Python 3.14.4) — duas aberturas de
handle —, mais a abertura que lê o cabeçalho. São três aberturas por página, e no regime lento isso
sozinho encosta nos 500 ms.

**O que já foi feito dentro do desenho** (§4, decisão 14): a raiz passou a ser resolvida uma vez por
operação, e não uma vez por arquivo, e a listagem passou a usar `os.scandir`. A renderização caiu de
~160 para ~95 ms no regime normal e de ~800 para ~490 ms no lento. Abaixo disso, só mudando o
mecanismo de confinamento — o que não é decisão de execução.

**Opções** (todas mudam um artefato aprovado — `NFR-W-02` ou `DP-W-11`):

| | Opção | Consequência |
|---|---|---|
| **A** | Subir o orçamento para **≤ 1 s** a 500 páginas | Uma linha. Depois da otimização, todas as medidas ficaram abaixo de 870 ms — inclusive com a wiki crescendo até 700 páginas. Para o uso real (dezenas de páginas, `NFR-W-04`) não muda nada: lá a aprovação leva dezenas de milissegundos |
| **B** | Manter 500 ms e medir a **100** páginas | Continua 2–4× acima da escala projetada; no regime lento fica em ~150 ms |
| **C** | Trocar a natureza do sensor: medir a **razão** entre renderizar páginas grandes e páginas pequenas | Mede direto o que `NFR-W-01` garante (o custo não cresce com o tamanho da página) e não depende da máquina — mas deixa de verificar um orçamento absoluto |
| **D** | Manter como está | É o risco que `DP-W-11` declarou — mas nesta máquina a suíte fica vermelha quase toda vez, e teste que falha sem regressão ensina a ignorar a falha |

**Recomendo A**: preserva a intenção (orçamento absoluto, dez vezes a escala real) e só corrige o
número para o hardware em que o produto roda.

### 3.2 `PBT-U2-08` (U2) falha — defeito latente no teste, não em U3

**O que é.** `_rodar_roteiro`, em `tests/persistencia/test_contrato.py`, cria a anotação com
`est.anotacao_agora(...)` — `datetime.now()` — **separadamente** na execução real e na do duplo, e
depois compara os `Ambiente` carregados, que carregam esse instante. Qualquer roteiro
`salvar → anotar → carregar` sobre uma tarefa falha: os dois `criada_em` diferem por microssegundos.

**Reprodução mínima** (sem Hypothesis): `Ambiente` com uma tarefa, operações
`[("salvar",), ("anotar", 0, "0", ""), ("carregar",)]` → `real != duplo`, e o único campo diferente
é `Anotacao.criada_em`.

**Por que só agora.** A propriedade gera 30 exemplos por execução, e essa sequência exata não tinha
sido sorteada nas execuções de U2. Desta vez foi — e o Hypothesis guardou o contraexemplo em
`.hypothesis/`, então ele passa a ser repetido em toda execução até o teste ser corrigido.
**Nenhum arquivo de U2 foi tocado por U3.**

**Correção proposta** (não aplicada — U2 está fechada): dar à operação `anotar` um instante fixo,
igual nas duas execuções — por exemplo, construir a `Anotacao` com um `criada_em` constante em vez de
`anotacao_agora`. O contrato que a propriedade verifica (mesmo resultado observável nas duas
implementações) fica intacto; só sai o relógio da comparação.

---

## 4. Decisões tomadas durante a execução

| # | Decisão | Motivo |
|---|---|---|
| 1 | **`normalizar_valor` tira aspas externas até não sobrar par**, não "um par" como o plano dizia | Com um par só, `'""x""'` sairia `'"x"'` e o leitor devolveria `'x'`; `'" x "'` sobraria com espaço na borda. Caíam o round-trip e a idempotência que o próprio plano exige. Registrado também no docstring |
| 2 | A tabela pré-slug (`&` → ` e `) roda **depois** da NFKD | Assim o `&` de largura cheia (U+FF06) também vira `e`. Continua antes da peneira do slug |
| 3 | **Nome no disco que não é slug válido é ignorado** por `listar` e pela renderização | Leitura de `RN-W-02` + `RN-W-03`: só o app escreve slug. Garante que todo nome que o índice e `listar` mostram é legível por `ler` — sem isso, `Notas.md` feito à mão apareceria como link quebrado |
| 4 | `ler_cabecalho` recebe **linhas** e `ler_pagina` recebe **texto**, não um caminho | `logical-components.md` declara `frontmatter.py` como "pura manipulação de texto"; a abertura do arquivo fica em `wiki_de_arquivos.py`, dentro de `traduzindo_erros` (`DP-W-04`) |
| 5 | `caminhos.py` importa `portas/wiki` (os erros) e `dominio/raiz_wiki` (`ESQUEMA_PADRAO`) | A linha dele na matriz de dependência omitia os dois; a lista "Podem importar" do mesmo documento já os permitia. A matriz continua sem ciclo |
| 6 | Na validação, o **confinamento vem antes da existência da entidade** | O Functional Design listava a ordem inversa; assim nem a consulta de existência olha um caminho fora da raiz |
| 7 | **Texto que não cabe em UTF-8** (surrogate isolado, que um JSON com escape produz) é recusado **na validação**, como `ArmazenamentoIndisponivel` | Descoberto depois de abrir o arquivo para escrita, a página que já existia estaria truncada. Também fecha `RN-W-36`: sem isso, `UnicodeEncodeError` atravessaria a porta |
| 8 | `traduzindo_erros` traduz também `UnicodeError` | `NFR-W-10` na leitura; a decisão 7 na escrita |
| 9 | `escrever_proposta` **cria a raiz** (e os ancestrais) quando cria entidades | O fluxo de `business-logic-model.md` §6 escreve a semente **antes** de renderizar. `NFR-W-06` ("só `renderizar_index` cria") foi lido como "`listar` e `ler` não criam" — que é o que o requisito protege |
| 10 | Toda pasta criada recebe `0o700` em POSIX, **inclusive ancestrais** (`dados/`, `wikis/`) | Mesma política de `NFR-P-14`; uma raiz de dados criada pela wiki não fica mais aberta que a criada pelo banco |
| 11 | A renderização ignora, com `WARNING`, também **entrada que resolve fora da raiz** e **página que não abre** (`OSError`) | Uma entrada ruim não derruba o índice inteiro. Só falha de listar pasta ou de publicar o índice vira erro |
| 12 | `montar_indice` troca quebra de linha por espaço no nome do ambiente e na descrição | A gramática de `RN-W-18` é de linha; um nome com quebra partiria o cabeçalho. Para descrição escrita pelo app, não muda nada |
| 13 | Formato de `a_partir_do_formulario`: `{"entidades": [{"titulo", "propriedades": [{"titulo", "descricao"}]}]}` | Nenhum artefato fixava. Ausência vale lista vazia; nada é aparado — quem decide o nome é o slug, na escrita |
| 14 | **`resolver_sob` recebe a raiz já resolvida** (é o que `resolver_raiz` devolve) e a listagem usa `os.scandir` | Medido contra `NFR-W-02` (§3.1). Os dois lados continuam passando por `resolve()` — a raiz uma vez por operação. Raiz passada sem resolver não abre brecha: só pode recusar demais, e há teste fixando isso |
| 15 | Índice publicado sem `fsync` | Hoje o único chamador de `escrever_atomico` é o índice, que é projeção: refaz-se na próxima renderização. Registrado no docstring para quem quiser reaproveitar o auxiliar |

---

## 5. Os geradores, testados por mutação

Uma propriedade que nunca vê o caso que importa passa sem provar nada. Cada propriedade relevante
foi verificada injetando um defeito de propósito (por monkeypatch, sem tocar no código) e
confirmando que ela falha:

| Defeito injetado | Antes | Depois |
|---|---|---|
| A listagem perde a última página | `PBT-U3-04` pega | — |
| O cabeçalho corta a descrição no `:` | **escapava** de `PBT-U3-04` e da concordância | pega nas duas |
| A leitura de página tira aspas duas vezes | **escapava** da concordância em arquivo editado à mão | pega |
| O delimitador deixa de tolerar CR | — | pega |
| Slug + etapas 1 e 3 do confinamento desligados | **escapava** de `PBT-U3-06` | pega (5 falhas distintas) |
| Só a etapa 3 (`resolve()`) desligada | não pega | não pega — **esperado**, ver abaixo |

**O que mudou nos geradores para isso:**

- Os caracteres da gramática (`:`, aspas, `#`, `-`, CR, LF, TAB) entram como **fragmentos**, não como
  caracteres. O Hypothesis funde um `one_of` de caracteres num intervalo só, e dez caracteres somem no
  meio de um milhão: só 3% das descrições tinham `:`. Agora são 43%.
- `sequencias_de_propostas`: propostas em série sobre o mesmo punhado de entidades. Antes, só 4 de 300
  propostas geradas eram aceitas com página; agora um terço das sequências escreve página.
- `propostas_hostis`: bem formadas em tudo, menos nos títulos. Uma proposta hostil que caísse por outro
  motivo nunca chegava ao disco, e um confinamento quebrado passava despercebido.
- A concordância em arquivo editado à mão monta abertura, miolo, fechamento e corpo — antes quase todo
  exemplo comparava `("", "")` com `("", "")`.
- `PBT-U3-06` ganhou pasta própria por exemplo (o custo era quadrático: 11 s → 5,6 s) e sentinelas fora
  da wiki — um `fishingrod.db` falso na raiz de dados e um arquivo fora dela —, então "nada vazou"
  passou a significar "nada criado **nem sobrescrito**".

**A linha que não pega, dita por extenso.** Com o slug intacto, nenhum título escapa
lexicamente; a etapa 3 só importa para symlink, e o Windows desta máquina recusa criar symlink. Os 5
testes de symlink existem, estão nomeados e rodam em Linux — aqui são pulados. É o risco aceito nº 1
de `tech-stack-decisions.md`, agora **medido** em vez de presumido. Fica uma possibilidade, não
executada por estar fora do plano: *junction* do Windows não exige privilégio, e um teste com junction
exercitaria a etapa 3 nesta máquina.

---

## 6. Rastreio

| Especificação | Onde se verifica |
|---|---|
| **US-08** — o ambiente nasce com wiki, mesmo vazia | `test_us_08_esquema_vazio_nasce_com_indice_vazio` |
| **US-09** — a estrutura é do dono | `test_us_09_o_esquema_do_formulario_vira_a_primeira_proposta` |
| **US-13** — promover conteúdo "no formato certo" (parte de U3; o plano listava só US-08/09, o mapa de histórias atribui também esta) | o formato é do adaptador, não do agente (`RN-W-13`): `test_rn_w_13_*`, `PBT-U3-03`. A promoção em si é de U8 |
| `RN-W-01/02` dois níveis, o que conta como wiki | `test_rn_w_01_*`, `test_rn_w_02_listar_so_ve_o_que_e_da_wiki`, `PBT-U3-04`, `PBT-U3-06` |
| `RN-W-03..06` slug e nomes | `test_rn_w_03/04/05/06_*`, `PBT-U3-05` |
| **`RN-W-07..10` confinamento** | `test_rn_w_07_*` (14 casos + 5 symlink), `test_rn_w_09_*`, `PBT-U3-01` (unidade), `PBT-U3-06` (ponta a ponta) |
| `RN-W-11..16` frontmatter | `test_rn_w_11/13/15/16_*`, `PBT-U3-07`, concordância |
| `RN-W-17..25` índice | `test_rn_w_17/18/19/20/21/25_*`, `PBT-U3-02`, `PBT-U3-04` |
| `RN-W-26..32` escrita | `test_rn_w_26/28/31_*`, `test_rn_w_14_*` |
| `RN-W-33..35` links | `test_rn_w_33_*` (caminho qualificado); validação de link é de **U8** (`RN-W-34`) |
| `RN-W-36/37` vocabulário | `test_rn_w_36_*`, `test_nfr_w_13_*`, `listar` devolve só nomes |
| `NFR-W-01` só o cabeçalho | `test_nfr_w_01_*` — iterador que falha se alguém ler além do bloco ou do teto |
| `NFR-W-02` desempenho | `test_nfr_w_02_*` — **ver §3.1** |
| `NFR-W-03` uma ida ao thread | `test_nfr_w_03_cada_operacao_e_uma_unica_ida_ao_thread` |
| `NFR-W-05..10` segurança | `test_rn_w_07_*`, `test_nfr_w_06/07/10_*` |
| `NFR-W-11..15` confiabilidade | `test_nfr_w_11_*` (`os.replace` falhando no último passo), `test_rn_w_31_*` |
| `NFR-W-16/17` observabilidade | `test_rn_w_20_*`, `test_nfr_w_10_*`, `test_nfr_w_16_*`, mensagens sem caminho absoluto |
| `NFR-W-18..20` testes | 5 symlink `skipif`; sem duplo (`NFR-W-19`); concordância dedicada (`NFR-W-20`) |
| Critérios de pronto de U3 | 1 → `PBT-U3-04` · 2 → `test_rn_w_14_*` · ~~3~~ revogado · 4 → `RN-W-22`, estrutural: página fica sempre no nível 2, e `PBT-U3-06` verifica que no nível 1 só existem pastas e o `index.md` que `renderizar_index` publica · 5 → `PBT-U3-01` · 6 → `PBT-U3-06` |

---

## 7. Conformidade das extensões

| Extensão | Estado | Rationale |
|---|:--:|---|
| **`security-baseline`** | ✅ Conforme, com as ressalvas já registradas | Confinamento em três etapas, num ponto único, verificado em cada arquivo; nenhum erro de SO atravessa a porta; nenhum caminho absoluto em mensagem; `0o700`/`0o600` em POSIX; zero dependência nova. A ressalva de **RNF-14** continua como está no Functional Design. **A etapa 3 não roda nesta máquina** (§5) — risco aceito nº 1, agora medido |
| **`property-based-testing` (Full)** | ✅ Conforme | As 7 propriedades `PBT-U3-01..07` implementadas, mais as duas de concordância; geradores verificados por mutação (§5). Sem `.filter()` que esconda domínio: a normalização ampliou o domínio do round-trip em vez de restringi-lo |
| **`resiliency-baseline`** | **N/A** | Desativada em Requirements Analysis. `escrever_atomico` e `traduzindo_erros` são integridade de escrita local e tradução de erro, não resiliência distribuída |

---

## 8. Observações e o que fica para as próximas unidades

- **U4 (`ServicoDeAmbiente`)**: o fluxo de `business-logic-model.md` §6 está provado de ponta a ponta
  em `test_us_08_*` e `test_us_09_*`. Com esquema vazio, `escrever_proposta` não cria nada e
  `renderizar_index` cria a raiz. Erros de título e descrição do formulário chegam como
  `TituloInvalido` e `DescricaoObrigatoria`, antes de qualquer escrita — o formulário pode
  pré-validar com `caminho_wiki.slug_valido(slug(...))` e `normalizar_valor(...)`, que são os
  mesmos critérios.
- **U8 (`ServicoBibliotecario`)**: `PaginaProposta.entidade` aceita título ou slug indiferentemente
  (`PBT-U3-05`). Para validar `[[link]]`, `listar(localizador, entidade)` devolve os slugs das
  páginas; entidade que não existe levanta `EntidadeInexistente`.
- **U9 (composition root)**: `WikiDeArquivos(pasta_de_dados())`, importando de
  `fishingrod.adaptadores.wiki`; o destino do logger `fishingrod.wiki` é decisão de lá.
- **Limitação conhecida, fora de `RN-W-15`**: arquivo salvo com BOM UTF-8 por um editor externo
  perde o frontmatter na leitura — a primeira linha vira `﻿---`. A página sai do índice com
  `WARNING`, e `ler` devolve o texto inteiro como corpo. Nenhum dado se perde.
- **Texto antigo encontrado, não emendado por estar fora do escopo**: o parágrafo "Por que esta
  unidade fecha sem o bibliotecário existir", em `unit-of-work.md` §3, ainda diz que "uma página
  criada fora do app aparece no índice na próxima renderização" — superado pela Q2 do Functional
  Design, que revogou o critério 3 logo abaixo dele.
