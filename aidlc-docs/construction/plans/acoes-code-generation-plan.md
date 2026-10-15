# Code Generation Plan — U5 `acoes`

**Fase:** CONSTRUCTION · **Unidade:** `U5 acoes` · **Portão 2 de 2** · **Data:** 2026-10-02
**Base:** os 3 artefatos de `construction/acoes/functional-design/`, aprovados em
2026-10-02T19:01:43Z, com as decisões G1–G10
**Estágios da unidade:** FD ✅ · NFR-R SKIP · NFR-D SKIP · INFRA SKIP · **CG EXECUTE**

> **Este plano é a única fonte de verdade da geração de código de U5.** A Parte 2 executa
> exatamente estes passos, na ordem, marcando `[x]` a cada conclusão. Nada fora daqui é gerado.

---

## 1. Contexto da unidade

| Campo | Conteúdo |
|---|---|
| **Histórias** | **US-04** (`anotar_memoria`), **US-15** (`criar_frente`), **US-16** (`criar_tarefa`), **US-17** (`criar_etapa` pelo orquestrador, com confirmação), **US-19** (`concluir_etapa`). U5 é a superfície de acionamento delas; **nenhuma fecha aqui** — todas fecham em U9 |
| **Dívida que morre aqui** | **TD-11** (argumento com espaço quebra comando) |
| **Depende de** | U1 (`Chamador`, `exige_aprovacao`, `ExecutorEtapa`, entidades), U4 (`ServicoDeAmbiente` e seus erros), U2 e U3 (só os **tipos de erro** das portas, para o mapeamento). Todas aprovadas |
| **Entrega para** | U6 (as 6 ações viram ferramentas do orquestrador), U8 (`PortaDeConfirmacao`), U9 (paleta, botões, barra `/`, a implementação da porta) |
| **Especificação** | 42 regras `RN-AC-01..42` · 10 propriedades `PBT-U5-01..10` · decisões G1–G10 · critérios de pronto 1–6 de `unit-of-work.md` §3 (com a emenda de U5) |
| **Destino do código** | `src/fishingrod/aplicacao/catalogo/` (5 módulos novos) e `src/fishingrod/aplicacao/portas/confirmacao.py` |
| **Destino dos testes** | `tests/acoes/` (novo) |
| **Dependências novas** | **Nenhuma.** `unicodedata`, `re`, `types`, `logging` e `dataclasses` são stdlib; `dependencies = []` continua verdadeiro |

**Interface publicada por esta unidade.**

| Módulo | O que outras unidades importam |
|---|---|
| `aplicacao/catalogo/catalogo.py` | `CatalogoDeAcoes`, `comando_de`, `nome_de` |
| `aplicacao/catalogo/tipos.py` | `Alvo`, `Acionamento`, `Resultado`, `MotivoFalha`, `PedidoDeConfirmacao`, `Referencias`, `EtapaNaPosicao`, `Acao`, `Parametro`, `TipoParametro`, `Escopo`, `CatalogoInvalido` |
| `aplicacao/catalogo/parser.py` | `ParserDeComando`, `ComandoDigitado` |
| `aplicacao/portas/confirmacao.py` | `PortaDeConfirmacao` |

**Critério de pronto de U5** (`unit-of-work.md` §3, com a emenda de U5): (1)
`/criar-tarefa campanha de verao` interpreta o argumento inteiro (TD-11) · (2) toda ação é dado no
registro · (3) toda ação, pelo catálogo, devolve `Resultado` · (4) conversar não está no catálogo ·
(5) ação de agente nunca efetiva antes de você confirmar; ação sua executa direto · (6)
`criar_chat` só com agente da lista fechada (cumprido por U4, traduzido aqui).

**Baseline de testes antes desta unidade:** `343 passed, 7 skipped` (medido em 2026-10-02).

---

## 2. Reconciliações

Lacunas que só aparecem ao escrever o código. A resolução é o que o código segue; as que mudam
texto de artefato aprovado viram emenda no passo 18.

| # | Lacuna | Resolução e motivo |
|---|---|---|
| **R-CG5-1** | `domain-entities.md` §5.2 diz que `ARGUMENTO_INVALIDO` cobre o caso em que "sobrou" texto, mas a lista de valores de `problema` não tem um valor para isso | Acrescentar **`problema="sobrando"`**. Só é alcançável por ação **sem** parâmetro — nenhuma das 6 —, porque o último parâmetro sempre leva o resto. Existe para a gramática ser total em qualquer registro. Emenda em `domain-entities.md` §5.2 |
| **R-CG5-2** | RN-AC-38 fixa a ordem das verificações, mas pela barra o texto precisa ser repartido **antes** de existir argumento. Repartir cedo faria um erro de texto aparecer antes de `NAO_PERMITIDA` ou `ALVO_AUSENTE` | `executar` e `executar_comando` **compartilham um pipeline interno**, e repartir o texto é parte do **passo 4**. A ordem de RN-AC-38 vale igual para as duas entradas |
| **R-CG5-3** | O FD diz que a posição aponta uma etapa "da tarefa-alvo", mas não diz o que impede um `POSICAO` numa ação de escopo `FRENTE` | `POSICAO` sempre se refere a uma etapa da tarefa-alvo. RN-AC-08 ganha duas verificações: `POSICAO` só em ação de escopo `TAREFA`, e no máximo um por ação. Emenda em `business-rules.md` |
| **R-CG5-4** | `Parametro` não tem campo de valor padrão, e o FD diz "opcional ausente recebe o padrão" | O dicionário convertido **omite** o opcional ausente, e o `efetivar` da ação aplica o padrão (`criar_chat`: `nome=""`, que U1 troca pelo nome do agente). `None` vindo do agente (JSON `null`) conta como ausente. Sem campo novo |
| **R-CG5-5** | RN-AC-30 manda erro **da porta de confirmação** virar `FALHA_INESPERADA`. Pelo `except` geral do pipeline, uma porta que levantasse, por exemplo, `ErroDePersistencia` cairia em `FALHA_DE_ARMAZENAMENTO` | A chamada à porta tem um `try` próprio: **qualquer** `Exception` dela vira `FALHA_INESPERADA`, com log, e nada executa |
| **R-CG5-6** | "Espaço" aparece no parser, na repartição, em G3 ("só espaços") e na RN-02 de U1 (`strip()`), sem definição comum | Espaço é o que `str.isspace()` diz que é, em todos os quatro lugares — a mesma definição de `strip()` e `split()`. Assim, um texto que o catálogo aceita nunca é recusado por vazio no domínio, e vice-versa |

---

## 3. Decisões de implementação declaradas (não perguntadas)

Escolhas de forma que o Functional Design não fixou. São reversíveis; se discordar de alguma, o
momento é agora.

| Decisão | Escolha | Motivo |
|---|---|---|
| **Módulos** | `tipos.py` (os tipos), `parser.py`, `argumentos.py` (repartir e converter), `registro.py` (as 6 ações), `catalogo.py` (o pipeline), e `portas/confirmacao.py` | Cada um testável sozinho; `parser.py` e `argumentos.py` são puros e não importam nada do projeto além de `tipos.py` |
| **`catalogo/__init__.py`** | Fica **vazio**, sem reexportar | `portas/confirmacao.py` importa `PedidoDeConfirmacao` de `catalogo/tipos.py`, e `catalogo/catalogo.py` importa a porta. Com um `__init__` que reexportasse o catálogo, importar a porta primeiro entraria em ciclo. É também a decisão de `servicos/__init__.py` em U4 |
| **Tipos** | `dataclass(frozen=True)` e `Enum`; `Resultado.ok(dado)` e `Resultado.falha(motivo, **detalhe)`, com os valores do detalhe convertidos para `str` | Imutáveis por construção; o detalhe é texto curto, e já serializável para o agente |
| **Argumentos do pedido** | `types.MappingProxyType` sobre uma cópia | RN-AC-31: a porta não consegue mudar o que vai executar, nem por engano |
| **G4 (escolha sem maiúscula nem acento)** | `unicodedata.normalize("NFKD")`, tira as marcas combinantes, `casefold()`; devolve a opção **canônica** | `Usuário`, `USUARIO` e `usuario` viram `usuario` |
| **`POSICAO`** | `int` que não é `bool`, ≥ 1; ou texto que casa com `[0-9]{1,9}` e vale ≥ 1 | Só dígitos ASCII: `int("٢")` vale 2 em Python, e isso não é o que se quer aceitar. Nove dígitos evitam converter texto gigante |
| **Ordem dentro de `ARGUMENTO_INVALIDO`** | Primeiro chaves desconhecidas (em ordem alfabética); depois os parâmetros, na ordem do registro: ausente → tipo → opção → tamanho | Determinística: a mesma entrada dá sempre o mesmo `parametro` e o mesmo `problema` |
| **Resolução das referências** | `carregar_ambiente` do serviço (o mesmo objeto aberto, RN-A-03) e travessia própria por id, levantando os erros de **U4** (`FrenteInexistente`, `TarefaInexistente`) para a tabela de mapeamento tratar; posição além do fim é um erro interno do catálogo, com `posicao` e `total` | Um caminho só de erro para o passo 5 e o passo 7 |
| **Posição devolvida** | `efetivar` de `criar_etapa` e `concluir_etapa` acha de novo a tarefa **pelo id** no ambiente aberto depois de executar, e devolve `EtapaNaPosicao` | Depois de uma recarga por conflito, os objetos de dentro do ambiente são outros (RN-A-03) |
| **Logger** | `logging.getLogger("fishingrod.acoes")` com `NullHandler` no próprio `catalogo.py`; `error(..., exc_info=erro)` com nome da ação, tipo de quem acionou e tipo do erro | RN-AC-37. Mesmo motivo de U2–U4: sem destino configurado, nada vaza para a tela |
| **Teste de código `async`** | `executar(coro)` de `tests/ambiente/estrategias.py`, um laço por exemplo. **Sem `pytest-asyncio`** | Mesma decisão de U2–U4 |
| **Portas usadas nos testes** | `RepositorioEmMemoria` e `WikiDeArquivos` sobre `tmp_path`, com o `ServicoDeAmbiente` **real**. O SQLite real entra só em `test_integracao.py` | O catálogo é testado contra o serviço de verdade, e não contra um falso dele, a não ser onde o teste precisa sabotar |
| **Reaproveitamento** | `ambientes_de_partida`, `semear`, `novo_servico`, `ORQUESTRADOR`, `BIBLIOTECARIO` e `executar` de `tests/ambiente/estrategias.py`; `ModeloDeAmbientes` e `projetar` de `tests/ambiente/modelo.py` | PBT-07: geradores centralizados; o oráculo de U4 vale para U5 sem ser reescrito |
| **Instrumentação** | `tests/acoes/instrumentos.py` | Mesma razão de U4: embrulham o serviço real, não são segunda implementação |
| **Nome de teste** | `test_rn_ac_16_*`, `test_pbt_u5_04_*` | Convenção de U1–U4: o nome diz qual regra quebrou |

---

## 4. Especificação das propriedades

NFR Requirements e NFR Design foram SKIP, então as estratégias ficam fixadas aqui. Os geradores
moram em `tests/acoes/estrategias.py`.

**Os instrumentos (`tests/acoes/instrumentos.py`).**

| Instrumento | Para quê |
|---|---|
| `ServicoEspiao` | Embrulha o `ServicoDeAmbiente` real e anota cada chamada (operação e argumentos) antes de delegar |
| `ServicoSabotado` | Igual, mas levanta uma exceção escolhida em `carregar_ambiente` (passo 5) ou na operação (passo 7) |
| `ConfirmacaoFixa(resposta)` | Responde sempre a mesma coisa e guarda os pedidos que recebeu |
| `ConfirmacaoQueLevanta(erro)` | Levanta ao ser perguntada |
| `ConfirmacaoQueEspera` | Fica parada até o teste liberar, para RN-AC-32 e para o cancelamento |
| `ConfirmacaoProibida` | Falha o teste se for chamada: prova que o caminho do usuário, e a validação, nunca perguntam |

**O modelo (`tests/acoes/modelo.py`).** `forma(ambiente)`: a projeção de U4 **sem identidades**,
para comparar dois ambientes que criaram objetos com ids diferentes. `prever(comando, vista)`: o
`MotivoFalha` esperado para um comando do catálogo, na ordem de RN-AC-38 — a parte de
`ARGUMENTO_INVALIDO` e `ALVO_AUSENTE` é nova; a de alvo e lista fechada traduz a previsão de U4. No
sucesso, o efeito é aplicado pelo `ModeloDeAmbientes.aplicar` de U4, com o autor do
`Acionamento`.

| # | Propriedade | Geração | Verificação | Exemplos |
|---|---|---|---|---|
| **PBT-U5-01** | Ida e volta do parser | nome sem espaço (inclusive vazio, com `/`, acentos e Unicode); texto sem espaço nas pontas, com espaços, tabulações e espaço não separável por dentro | `interpretar(formatar(c)) == c` | 200 |
| **PBT-U5-02** | Nome e comando | nomes `snake_case` gerados; textos quaisquer como comando | `nome_de(comando_de(n)) == n`; nenhum texto acha mais de uma ação | 100 |
| **PBT-U5-03** | Nunca levanta | nome do registro ou lixo; alvo com identidades existentes, inexistentes ou ausentes; argumentos com chaves e tipos quaisquer (`str`, `int`, `bool`, `None`, `float`, listas); os dois acionamentos; resposta qualquer da porta; sabotagem: nenhuma, ou uma exceção de **toda** linha da tabela de §5.3 mais `RuntimeError`, `KeyError`, `TypeError`, no passo 5 ou no 7. As duas entradas (`executar` e `executar_comando` com linha gerada) | sempre `Resultado`; invariantes de RN-AC-35; com entrada válida e sabotagem no passo 7, o motivo é o da tabela | 150 |
| **PBT-U5-04** | TD-11 | por ação: uma palavra válida para cada parâmetro que não é o último (opção com maiúscula e acento sorteados; posição válida; `bibliotecario` para o agente) e texto livre para o último, com espaços variados por dentro; separadores entre as palavras de 1 a 3 caracteres de espaço quaisquer | o `ServicoEspiao` recebe exatamente esses valores — a opção na forma canônica, a posição como o id da etapa —, e o último com os espaços de dentro intactos | 100 |
| **PBT-U5-05** | Falha fechada | ação e argumentos válidos, pelo agente; a porta responde `False`, `None`, `0`, `1`, `"sim"`, `"True"`, `[]`, ou levanta (inclusive um erro de tipo conhecido, R-CG5-5) | nenhuma operação de mudança chega ao `ServicoEspiao`; `forma` e `versao` iguais às de antes; motivo `RECUSADA`, ou `FALHA_INESPERADA` quando a porta levantou | 100 |
| **PBT-U5-06** | Oráculo com sequência | ambiente de partida de U4; sequência de **0** a 15 comandos do usuário, pela barra ou por argumentos, com alvo existente, inexistente ou ausente, argumentos válidos ou com uma violação, posição dentro ou fora | **depois de cada comando**: o motivo é o previsto, e `projetar(aberto) == modelo`; a `ConfirmacaoProibida` nunca é chamada | 60 |
| **PBT-U5-07** | Confirmado é igual a usuário | ambiente de partida semeado em **dois** repositórios; uma ação válida, aplicada pelo agente com "sim" num e pelo usuário no outro | `forma` igual nos dois, a não ser pelo autor da anotação, que é o nome do agente num e `usuario` no outro | 60 |
| **PBT-U5-08** | Posição | tarefa com 0 a 6 etapas, algumas já concluídas; k entre −2 e N+3, como `int` ou como texto | 1 ≤ k ≤ N: só a k-ésima muda, e `posicao == k`; k > N: `ALVO_INEXISTENTE` com `posicao` e `total`; k < 1: `ARGUMENTO_INVALIDO`; nos dois últimos, nenhuma escrita | 60 |
| **PBT-U5-09** | Idempotência | tarefa com 1 a 4 etapas; a mesma posição concluída r ∈ 1..3 vezes | `forma` igual à de concluir uma vez | 40 |
| **PBT-U5-10** | Validação antes de tudo | por ação, argumentos válidos com **exatamente uma** violação: obrigatório faltando, `None`, só espaços, chave a mais, tipo errado, fora das opções, acima do máximo; pelo agente | `ARGUMENTO_INVALIDO` com o `parametro` e o `problema` previstos; `ConfirmacaoProibida` não chamada; `ServicoEspiao` sem **nenhuma** chamada, nem de leitura | 100 |

Encolhimento e semente ficam no padrão do Hypothesis (perfil `fishingrod` de `tests/conftest.py`,
`deadline=None`). Nada desliga o encolhimento. Os geradores são medidos com
`--hypothesis-show-statistics` no passo 17, como em U4, e endurecidos se não alcançarem os ramos.

---

## 5. Os passos

### Código de aplicação

- [x] **Passo 1** — `src/fishingrod/aplicacao/catalogo/tipos.py`: `Escopo`, `TipoParametro`,
      `Parametro`, `Acao`, `Alvo`, `Acionamento` (com `usuario()` e `agente(nome)`),
      `Referencias`, `EtapaNaPosicao`, `PedidoDeConfirmacao`, `MotivoFalha` (os 10), `Resultado`
      (com `ok` e `falha` e as invariantes de RN-AC-35 verificadas no `__post_init__`),
      `ErroDoCatalogo` e `CatalogoInvalido`. Sem I/O. **Critérios 2, 3**
- [x] **Passo 2** — `src/fishingrod/aplicacao/portas/confirmacao.py`: `PortaDeConfirmacao`
      (`Protocol`), com a semântica de RN-AC-28/30/31 na docstring (espera; só `True` confirma; não
      altera o pedido). **Critério 5**
- [x] **Passo 3** — `src/fishingrod/aplicacao/catalogo/parser.py`: `ComandoDigitado` e
      `ParserDeComando` com `detectar` (G9), `interpretar` (RN-AC-40, `ValueError` para o que não é
      comando) e `formatar` (RN-AC-41). **TD-11, critério 1**
- [x] **Passo 4** — `src/fishingrod/aplicacao/catalogo/argumentos.py`: `repartir(parametros, texto)`
      (Q7=A, RN-AC-16, `R-CG5-1`, `R-CG5-6`) e `converter(parametros, argumentos)` (RN-AC-17..19,
      G3, G4, G10, `R-CG5-4`), com o erro interno que carrega `parametro`, `problema` e `maximo`.
      **TD-11, critério 1**
- [x] **Passo 5** — `src/fishingrod/aplicacao/catalogo/registro.py`: as **6 ações** de
      `domain-entities.md` §2.5, na ordem, com descrição, parâmetros (tipos, opções e máximos de
      G10), escopo, `chamadores = {USUARIO, AGENTE}` e `efetivar` (G1, G5, RN-AC-13, RN-AC-14,
      `R-CG5-4`). **US-04, US-15, US-16, US-17, US-19 · critérios 2, 4, 6**
- [x] **Passo 6** — `src/fishingrod/aplicacao/catalogo/catalogo.py`: `comando_de` e a inversa
      `nome_de` (RN-AC-07, G7);
      `CatalogoDeAcoes` com a verificação do registro (RN-AC-08 e `R-CG5-3`), `listar`, `buscar`,
      `executar` e `executar_comando` sobre o pipeline comum (RN-AC-38, `R-CG5-2`): escopo
      (RN-AC-10), referências (G2, RN-AC-22, RN-AC-23), política e confirmação (RN-AC-27..33,
      `R-CG5-5`), tabela de mapeamento (RN-AC-34..36) e log (RN-AC-37). Sem `os`, `pathlib`,
      `sqlite3`, `claude_agent_sdk`, `textual` nem adaptador (RN-AC-01). **Critérios 1, 3, 5, 6**

### Os testes

- [x] **Passo 7** — `tests/acoes/__init__.py` e `tests/acoes/estrategias.py`: fábrica de catálogo
      sobre o serviço real (`RepositorioEmMemoria` + `WikiDeArquivos`); geradores de §4 (linhas de
      comando, textos com espaço por dentro, alvos, acionamentos, argumentos válidos por ação e
      com uma violação, exceções da tabela, respostas da porta)
- [x] **Passo 8** — `tests/acoes/instrumentos.py`: os 6 instrumentos de §4
- [x] **Passo 9** — `tests/acoes/modelo.py`: `forma`, `prever` e a ponte para o
      `ModeloDeAmbientes` de U4 (§4)
- [x] **Passo 10** — `tests/acoes/test_fronteira.py`: RN-AC-01 pelo grafo de import (AST), como em
      U4, para os 5 módulos do catálogo e para a porta; `catalogo/__init__.py` vazio; `parser.py` e
      `argumentos.py` não importam o serviço. **Critério 4** (nenhuma ação de conversa no registro)
- [x] **Passo 11** — `tests/acoes/test_parser.py`: os exemplos de `business-logic-model.md` §3.1,
      G9 e o `ValueError`
- [x] **Passo 12** — `tests/acoes/test_argumentos.py`: a tabela de §3.2; G3 (só espaços, nas duas
      entradas); G4 (`Usuário`); G10 (cada máximo, no limite e um acima); `None` como ausente;
      `bool` e `float` em `POSICAO`; `sobrando` (`R-CG5-1`); a ordem dentro de
      `ARGUMENTO_INVALIDO`
- [x] **Passo 13** — `tests/acoes/test_registro.py`: as 6 ações com escopo, parâmetros,
      `chamadores` e comando; `listar` por escopo e por chamador; `buscar`; um `CatalogoInvalido`
      para **cada** defeito de RN-AC-08 e de `R-CG5-3`
- [x] **Passo 14** — `tests/acoes/test_catalogo.py`, os exemplos (PBT-10): **critério 1 literal**
      (`/criar-tarefa campanha de verao`); um exemplo por `MotivoFalha` (os 10); `NAO_PERMITIDA`
      com um registro de teste só de usuário (RN-AC-06); C1=A, a tarefa do agente nasce na frente
      da tarefa do chat (RN-AC-14); autor da anotação pelo usuário e pelo agente, e `autor` passado
      pelo agente recusado (RN-AC-12, 13); a barra aciona como usuário (RN-AC-15); argumento ruim
      do agente não pergunta (RN-AC-21); o pedido de `concluir_etapa` traz posição **e** descrição
      (D-Q2-2); pedido imutável (RN-AC-31); "sim", "não", porta que levanta (com o log **sem** os
      argumentos) e cancelamento durante a espera (RN-AC-28..30, 33); **pedido pendente não bloqueia
      uma ação sua no mesmo ambiente** (RN-AC-32); falha inesperada do serviço vai para o log
      (RN-AC-37). **Critérios 1, 3, 5, 6**
- [x] **Passo 15** — `tests/acoes/test_propriedades.py`: **`PBT-U5-01` a `PBT-U5-10`**, como em §4
- [x] **Passo 16** — `tests/acoes/test_integracao.py`: com os adaptadores **reais**
      (`RepositorioSQLite` e `WikiDeArquivos` sobre `tmp_path`). Cria um ambiente pelo serviço; pela
      barra, `/criar-frente`, `/criar-tarefa campanha de verao`; pelo agente com "sim",
      `criar_etapa` e `anotar_memoria`; pela barra, `/concluir-etapa 1` e
      `/anotar-memoria travado-por esperando o cliente`. Fecha o repositório, abre um serviço novo, e
      tudo volta igual, com os dois autores na memória. **US-04, US-15, US-16, US-17, US-19 de ponta
      a ponta, sem tela**

### Verificação e fechamento

- [x] **Passo 17** — Rodar `uv run pytest`. Medir os geradores com `--hypothesis-show-statistics`.
      Depois, **testar os testes por mutação**, um defeito de cada vez, e confirmar que cada um
      derruba pelo menos um teste: (1) agente executa sem perguntar; (2) `if resposta:` em vez de
      `is True`; (3) `split()` ingênuo no último parâmetro; (4) validação depois da confirmação;
      (5) `ErroDePersistencia` antes de `AmbienteInexistente` no mapeamento; (6) `except
      BaseException`, engolindo o cancelamento; (7) posição sem o `- 1`; (8) autor vindo do
      argumento; (9) sem a verificação de `chamadores`; (10) escolha sem tirar o acento; (11) sem o
      limite de tamanho; (12) o parser apertando os espaços de dentro. Registrar o resultado e
      endurecer o gerador que deixar passar
- [x] **Passo 18** — Emendas e fechamento: `domain-entities.md` §5.2 (`sobrando`, `R-CG5-1`) e
      `business-rules.md` RN-AC-08 (`R-CG5-3`), com texto marcado, nada apagado. Escrever
      `aidlc-docs/construction/acoes/code/code-summary.md` com arquivos, decisões tomadas na
      execução, resultado da suíte e da mutação e conformidade das extensões

---

## 6. Rastreio

| Especificação | Passo |
|---|---|
| RN-AC-01..04 (fronteira) | 1–6, 10 |
| RN-AC-05..09 (registro) | 5, 6, 13 |
| RN-AC-10..15 (alvo e quem aciona) | 1, 5, 6, 14, 15 |
| RN-AC-16..21 (argumentos) | 3, 4, 6, 12, 14, 15 |
| RN-AC-22..26 (etapa pela posição) | 5, 6, 14, 15 |
| RN-AC-27..33 (confirmação) | 2, 6, 14, 15 |
| RN-AC-34..38 (resultado e falhas) | 1, 6, 14, 15 |
| RN-AC-39..42 (parser) | 3, 11, 15 |
| `PBT-U5-01..10` | 15 |
| G1–G10 | 1, 4, 5, 6 (G6 no 2) |
| `R-CG5-1..6` | 2, 4, 5, 6, 12, 13, 18 |
| Critérios de pronto 1–6 | 1 → 3, 4, 14 · 2 → 5, 13 · 3 → 1, 6, 15 · 4 → 10 · 5 → 2, 6, 14, 15 · 6 → 14 |
| US-04 · US-15 · US-16 · US-17 · US-19 | 5, 14, 16 |
| TD-11 | 3, 4, 14, 15 |

**18 passos.** 5 arquivos novos em `src/fishingrod/aplicacao/catalogo/` e 1 em
`src/fishingrod/aplicacao/portas/`; nenhum arquivo de `src/` modificado; 11 arquivos novos em
`tests/acoes/`; 1 resumo de código e 2 emendas de documentação. O código antigo
(`model/comando.py`, `Ambiente/`, `cli.py`, `tui.py`) **não é tocado** (R-FD5-7).

---

## 7. Conformidade das extensões (planejada)

| Extensão / regra | Estado | Como o plano cumpre |
|---|:--:|---|
| `security-baseline` SECURITY-05 (validação de entrada) | ✅ | Tipo, opções e tamanho conferidos antes de qualquer efeito (passo 4); `PBT-U5-10` e exemplos de cada limite |
| SECURITY-08 (controle de acesso) | ✅ | `chamadores` conferido no catálogo (passo 6, exemplo `NAO_PERMITIDA`); nenhum parâmetro é identidade |
| SECURITY-11 (desenho seguro) | ✅ | A política num ponto só; teste de que pedido pendente não trava o ambiente |
| SECURITY-15 (falha segura) | ✅ | `PBT-U5-03` (nunca levanta) e `PBT-U5-05` (falha fechada); `R-CG5-5`; cancelamento passa |
| SECURITY-03 (log) | ✅ | Exemplo verifica que os argumentos não aparecem no log |
| SECURITY-10 (dependências) | ✅ | Nenhuma dependência nova |
| Demais regras de `security-baseline` | N/A | Sem rede, servidor, IAM, HTTP ou credencial |
| PBT-01 (identificação) | ✅ | As 10 propriedades do FD, especificadas em §4 |
| PBT-02 (round-trip) | ✅ | `PBT-U5-01`, `PBT-U5-02` |
| PBT-03 (invariantes) | ✅ | `PBT-U5-03`, `04`, `05`, `08`, `10` |
| PBT-04 (idempotência) | ✅ | `PBT-U5-09` |
| PBT-05 (oráculo) | ✅ | `PBT-U5-06` (modelo de U4) e `PBT-U5-07` |
| PBT-06 (com estado) | ✅ | `PBT-U5-06`: sequências de 0 a 15 comandos, verificação depois de cada um |
| PBT-07 (geradores) | ✅ | Geradores de domínio em `tests/acoes/estrategias.py`, reaproveitando U2–U4; medidos no passo 17 |
| PBT-08 (encolhimento e semente) | ✅ | Padrão do Hypothesis, nada desligado. A parte de CI fica para Build and Test |
| PBT-09 (framework) | ✅ | Hypothesis, já em `dev` desde U0 |
| PBT-10 (complementar) | ✅ | Exemplos (passos 11–14, 16) e propriedades (passo 15) em arquivos separados |
