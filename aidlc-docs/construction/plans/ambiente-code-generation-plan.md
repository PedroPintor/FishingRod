# Code Generation Plan — U4 `ambiente`

**Fase:** CONSTRUCTION · **Unidade:** `U4 ambiente` · **Portão 2 de 2** · **Data:** 2026-10-02
**Base:** os 3 artefatos de `construction/ambiente/functional-design/`, aprovados em
2026-10-02T15:54:41Z, com as decisões G1–G5
**Estágios da unidade:** FD ✅ · NFR-R SKIP · NFR-D SKIP · INFRA SKIP · **CG EXECUTE**

> **Este plano é a única fonte de verdade da geração de código de U4.** A Parte 2 executa
> exatamente estes passos, na ordem, marcando `[x]` a cada conclusão. Nada fora daqui é gerado.

---

## 1. Contexto da unidade

| Campo | Conteúdo |
|---|---|
| **Histórias** | **US-04** (anotar), **US-05** (sobreviver a fechar e reabrir; **U4 fecha esta história**), **US-08** e **US-09** (wiki nasce do esquema), **US-15** (frente), **US-16** (tarefa), **US-19** (concluir etapa). Mais a parte de gravação de **US-17** (`criar_etapa`, C1=A) |
| **Dívidas que morrem aqui** | Nenhuma |
| **Depende de** | U1 (domínio), U2 (`PortaPersistencia`), U3 (`PortaWiki`, `EsquemaWiki`). As três estão aprovadas |
| **Entrega para** | U5 (ferramentas de ambiente do orquestrador), U8 (`criar_chat` do bibliotecário), U9 (telas e composition root) |
| **Especificação** | 26 regras `RN-A-01..26` · 5 propriedades `PBT-U4-01..05`, mais 2 acrescentadas aqui (`R-CG4-4`) · critérios de pronto 1–6 de `unit-of-work.md` §3 |
| **Destino do código** | `src/fishingrod/aplicacao/servicos/` (serviço) e, por U3 reaberta, `aplicacao/portas/wiki.py` e `adaptadores/wiki/` |
| **Destino dos testes** | `tests/ambiente/` (novo) e `tests/wiki/` (acréscimo) |
| **Dependências novas** | **Nenhuma.** `asyncio`, `dataclasses`, `logging` e `shutil` são stdlib; `dependencies = []` continua verdadeiro |

**Interface publicada por esta unidade.** Um módulo, `aplicacao/servicos/servico_de_ambiente.py`,
com `ServicoDeAmbiente`, os 5 erros novos e `proposta_do_esquema`. U5, U8 e U9 importam dele.

**Critério de pronto de U4** (`unit-of-work.md` §3, com as emendas): (1) criar ambiente materializa a
wiki e renderiza o índice numa operação só · (2) as operações delegam a invariante ao domínio e
persistem pela porta · (3) nenhum `import` de `sqlite3` nem de `claude_agent_sdk` · (4) vários
ambientes coexistem, cada um com a sua raiz · (5) `ConflitoDeVersao` é tratado com até 3 tentativas ·
(6) apagar é banco primeiro, wiki depois, por `PortaWiki.apagar`.

**Baseline de testes antes desta unidade:** `272 passed, 7 skipped` (medido em 2026-10-02).

---

## 2. Reconciliações

Pontos que o Functional Design deixou em aberto, ou que só aparecem ao escrever o código. A
resolução é o que o código segue.

| # | Lacuna | Resolução e motivo |
|---|---|---|
| **R-CG4-1** | `business-logic-model.md` §1.2 diz que, quando a gravação falha, o serviço recarrega e "levanta o erro original". Não diz o que acontece se **a recarga também falhar** | Sobe o erro **da gravação**, que é o motivo de a operação ter falhado. A falha da recarga vai junto, como nota (`add_note`), e o ambiente é fechado (RN-A-09). Nada é engolido. No caminho de **conflito** é diferente: lá a recarga faz parte do fluxo normal, então o erro dela é o que sobe (`AmbienteInexistente` por RN-A-12, ou o erro de leitura) |
| **R-CG4-2** | `domain-entities.md` §5 não diz o que `PortaWiki.apagar` faz com um localizador que aponta para um lugar que **não é uma wiki**. Exemplo: `dados:wikis`, adulterado no banco, passa pelo confinamento (está dentro da pasta de dados) e removeria **todas** as wikis | `apagar` só remove uma raiz que tenha `index.md`. Raiz existente sem índice é recusada com `CaminhoForaDaRaiz`, e o serviço registra o `WARNING` de RN-A-18. Toda wiki criada pelo app tem índice, porque `criar_ambiente` só grava no banco depois de `renderizar_index` (RN-A-14). São 3 linhas, e limitam o estrago de um localizador errado a uma wiki só |
| **R-CG4-3** | `PBT-U4-02` (dois serviços sobre a mesma porta) não diz de onde o "processo A" tira os ids dos alvos. Um gerador ingênuo faria A mirar uma frente que só B conhece, e o serviço responderia `FrenteInexistente`, porque a memória de A está velha | O gerador escolhe os alvos de A **entre os ids que estão na memória de A**. É o caso real: quem chama, seja a tela ou um agente, só conhece ids do objeto aberto no próprio processo. Como não existe operação que remova frente, tarefa ou etapa, todo alvo visível na memória existe no disco. Por isso o serviço **não** precisa recarregar quando não acha o alvo. Pela mesma razão, a `PBT-U4-02` verifica o disco contra o modelo e **não** verifica memória ≡ disco: depois de uma anotação de B, a memória de A fica sem ela até a próxima recarga, e isso é RN-A-26, não defeito |
| **R-CG4-4** | A extensão `property-based-testing` (Full) exige, em `PBT-04`, uma propriedade para **toda operação declarada idempotente**. O FD declara duas, sem propriedade: `concluir_etapa` (RN-A-23) e `PortaWiki.apagar` (raiz inexistente é operação vazia) | Duas propriedades novas. **`PBT-U4-06`**: concluir k vezes deixa o mesmo estado que concluir uma, fora `versao`, que sobe a cada gravação por RN-A-23. **`PBT-U3-08`**, na sequência de U3, que é a dona do adaptador: apagar k vezes deixa o mesmo que apagar uma, e a wiki vizinha fica idêntica byte a byte |
| **R-CG4-5** | RN-A-09 cobre "falha na gravação", mas **cancelamento** (`asyncio.CancelledError`, que não é `Exception`) não é falha. Se a TUI fechar no meio de um `salvar_ambiente`, a memória pode ficar com uma mudança que o disco talvez tenha, talvez não | O ambiente é **fechado** (sai dos abertos) sem esperar nada, e o cancelamento segue. A próxima operação reabre do disco. É a forma de RN-A-09 que não precisa de `await` dentro de um cancelamento |

---

## 3. Decisões de implementação declaradas (não perguntadas)

Escolhas de forma que o Functional Design não fixou. São reversíveis; se discordar de alguma, o
momento é agora.

| Decisão | Escolha | Motivo |
|---|---|---|
| **Arquivo** | `aplicacao/servicos/servico_de_ambiente.py`, com os erros no topo, como as portas de U2 e U3 | Um import só para U5, U8 e U9 |
| **`servicos/__init__.py`** | Fica **vazio**, sem reexportar | O pacote é compartilhado por U4, U7 e U8. Reexportar faria quem importa um serviço importar os três |
| **Intenção** | `Callable[[Ambiente], T]`, escrita como função local em cada operação; `_mutar` é genérico em `T` | É a "intenção, não objeto" de RN-A-10, sem classe de comando |
| **Recarga no mesmo objeto** (G2) | Copia campo a campo com `dataclasses.fields(Ambiente)` | Se `Ambiente` ganhar um campo, a recarga continua completa sem ninguém lembrar de mexer aqui |
| **Travas** | `dict[Identidade, asyncio.Lock]`, criadas sob demanda e **nunca removidas**, nem ao apagar | Remover a trava de um ambiente apagado deixaria uma corrotina que esperava a trava antiga rodar junto com outra que pegou uma trava nova. Custam alguns bytes por ambiente aberto na sessão |
| **Erros do construtor** | `AgenteInvalido` (U1) para os três casos: orquestrador sem papel `ORQUESTRADOR`, orquestrador dentro de `agentes_de_chat` (G3), e nomes repetidos na lista | É o tipo que `domain-entities.md` §1.1 já nomeia. Erro de montagem do composition root, não de uso |
| **Resolução do agente** | Comparação **exata** do nome, sem normalizar | O catálogo de U5 vai oferecer os nomes da lista ao orquestrador; normalizar criaria um segundo nome que funciona sem estar listado |
| **Logger** | `logging.getLogger("fishingrod.ambiente")`, com `NullHandler` instalado no próprio módulo do serviço | Mesmo motivo de U2 e U3: sem destino configurado, o aviso não pode vazar para a tela da TUI. Fica no módulo, e não no `__init__`, pela linha acima |
| **Mensagem do `WARNING` de RN-A-18** | id do ambiente e **nome do tipo** do erro, sem o texto do erro | RN-A-18 pede "sem caminho de disco". O texto de `ErroDeWiki` já não tem caminho absoluto, mas o tipo basta e não depende disso |
| **`proposta_do_esquema`** | Função pura de módulo, pública | RN-A-13 testável sem I/O, por exemplo e por propriedade |
| **Teste de código `async`** | `executar(coro)` sobre `asyncio.run`, um laço por exemplo, cenário inteiro dentro de uma corrotina. **Sem `pytest-asyncio`** | Mesma decisão de U2 e U3 |
| **Portas usadas nos testes** | `RepositorioEmMemoria` (Q12=B de U2) e `WikiDeArquivos` sobre `tmp_path` (Q9=A de U3, sem dublê de wiki). O SQLite real entra só em `test_integracao.py` | `PBT-U2-08` já prova que o dublê e o real concordam |
| **Instrumentação** | Invólucros em `tests/ambiente/instrumentos.py`, e não em `tests/dobles/` | Não são uma segunda implementação do contrato: embrulham uma e anotam a ordem das chamadas, injetam falha ou forçam conflito |
| **Junction no Windows** | O teste de confinamento de `apagar` usa `_winapi.CreateJunction` no Windows e `os.symlink` no POSIX | Em U3, o teste de symlink é `skipif` no Windows (Q3=A). Junction não exige privilégio, então nesta máquina o teste roda de verdade. `_winapi` é módulo privado da stdlib, usado pelos próprios testes do CPython |
| **Nome de teste** | `test_rn_a_09_*`, `test_pbt_u4_01_*` | Convenção de U1–U3: o nome diz qual regra quebrou |

---

## 4. Especificação das propriedades

NFR Requirements e NFR Design foram SKIP, então as estratégias que o FD deixou para cá ficam fixadas
aqui. Todos os geradores moram em `tests/ambiente/estrategias.py` e reaproveitam os de U2
(`texto_nao_vazio`) e de U3 (`titulos_validos`, `titulos_hostis`, `descricoes_validas`).

**O modelo (`tests/ambiente/modelo.py`).** `ModeloDeAmbiente` é a versão simplificada que
`PBT-06` pede: frentes, tarefas, chats (agente e nome), etapas (descrição, executor, concluída) e
anotações (chave, autor, valor), em listas na ordem de criação, sem `versao` e sem carimbo de tempo.
`projetar(ambiente)` produz a mesma forma a partir de um `Ambiente`. Para cada comando, o modelo
**prevê** o resultado: sucesso ou o tipo do erro, na ordem em que o serviço verifica
(`AmbienteInexistente` → `AgenteDesconhecido` → alvo inexistente → `NomeInvalido`).

**Os comandos.** As 10 operações, com alvo escolhido por índice entre os ids que existem **ou** um
id novo (alvo inexistente). Nomes válidos na maior parte das vezes, e às vezes `""` ou só espaços.
`nome_agente` sorteado entre o bibliotecário, o nome do orquestrador e um texto qualquer.
Sequências de **0** a 15 comandos.

| # | Propriedade | Geração | Verificação, depois de **cada** comando | Exemplos |
|---|---|---|---|---|
| **PBT-U4-01** | Memória ≡ disco (fecha US-05) | um ambiente e uma sequência de comandos | (a) o ambiente aberto é igual (`==`) ao que um serviço **novo**, sobre a mesma porta, carrega · (b) `projetar(aberto) == modelo` · (c) o erro, quando há, é o que o modelo previu | 60 |
| **PBT-U4-02** | Conflito não perde mudança | dois serviços, A e B, sobre a mesma porta; comandos `(ator, operação)`, sem `apagar`. Alvos do ator vêm da memória **dele** (`R-CG4-3`) | `projetar(disco) == modelo`, com o modelo recebendo o efeito de todo comando que retornou com sucesso, de A ou de B | 40 |
| **PBT-U4-03** | A wiki nasce igual ao esquema | `EsquemaWiki` válido **ou** hostil (títulos hostis, descrição vazia), incluindo o vazio | se aceito: `listar` devolve os slugs únicos das entidades e, em cada uma, os das propriedades; cada página tem a descrição normalizada da semente (a última, quando o slug se repete) e conteúdo vazio; o `index.md` existe. Se recusado: `TituloInvalido` ou `DescricaoObrigatoria`, nenhum ambiente no banco e nenhuma pasta na pasta de dados | 40 |
| **PBT-U4-04** | Isolamento entre ambientes | dois ambientes; sequência de comandos (com `apagar`) só no primeiro | o segundo, carregado do disco, é igual à foto tirada antes; a listagem da wiki dele também | 30 |
| **PBT-U4-05** | Falha não deixa rastro | comandos (com `criar_ambiente`) sobre portas que falham na n-ésima chamada, **antes** ou **depois** de delegar | para todo ambiente listado: aberto ≡ disco (serviço novo sobre as portas sem falha) e o `index.md` dele existe | 40 |
| **PBT-U4-06** | `concluir_etapa` é idempotente (`R-CG4-4`) | tarefa com 1–4 etapas; uma delas concluída k ∈ 1..3 vezes | `projetar` igual ao de concluir uma vez; `versao` subiu k (RN-A-23) | 30 |
| **PBT-U3-08** | `PortaWiki.apagar` é idempotente e não toca o vizinho (`R-CG4-4`) | duas wikis com `propostas_validas` de U3; a primeira apagada k ∈ 1..3 vezes | a raiz da primeira não existe e `listar` devolve `[]`; os arquivos da segunda são idênticos byte a byte | 25 |

Encolhimento e semente ficam no padrão do Hypothesis (perfil `fishingrod` de `tests/conftest.py`,
`deadline=None`). Nada desliga o encolhimento.

---

## 5. Os passos

### U3 reaberta: `PortaWiki.apagar` (Q6=A)

- [x] **Passo 1** — `src/fishingrod/aplicacao/portas/wiki.py`: quinta operação
      `async def apagar(self, localizador: str) -> None` no `Protocol`, com a semântica de
      `domain-entities.md` §5 e de `R-CG4-2` na docstring; "quatro operações" passa a "cinco"
- [x] **Passo 2** — `src/fishingrod/adaptadores/wiki/wiki_de_arquivos.py`: `apagar` na casca async e
      `_apagar` no miolo. A raiz sai de `resolver_raiz` (`DP-W-01`); raiz inexistente é operação
      vazia; raiz sem `index.md` é `CaminhoForaDaRaiz` (`R-CG4-2`); `shutil.rmtree` dentro de
      `traduzindo_erros` (`NFR-W-13`, sem caminho absoluto)
- [x] **Passo 3** — `tests/wiki/test_wiki_de_arquivos.py` (exemplos) e `tests/wiki/test_propriedades.py`
      (**`PBT-U3-08`**): remove a raiz inteira; raiz inexistente; raiz sem índice; localizador de
      outro esquema e localizador que sai da pasta de dados; falha de I/O traduzida, sem caminho
      absoluto na mensagem; **link para fora da wiki não é seguido** (junction no Windows, symlink
      no POSIX)

### O serviço

- [x] **Passo 4** — `src/fishingrod/aplicacao/servicos/servico_de_ambiente.py`, de cima para baixo:
      os erros (`ErroDeServicoDeAmbiente` e as 4 subclasses); `proposta_do_esquema` (RN-A-13); os
      localizadores de alvo por identidade (RN-A-08); `ServicoDeAmbiente` com o construtor e as
      suas validações (RN-A-22, G3), o estado (abertos e travas), os auxiliares `_abrir`,
      `_recarregar` e `_mutar` (RN-A-03, 06, 09–12, `R-CG4-1`, `R-CG4-5`), e as **10 operações**
      (RN-A-13–25). Sem `os`, `pathlib`, `shutil`, `sqlite3`, `claude_agent_sdk` nem `textual`
      (RN-A-01). **US-04, US-05, US-08, US-09, US-15, US-16, US-17, US-19**

### Os testes

- [x] **Passo 5** — `tests/ambiente/__init__.py` e `tests/ambiente/estrategias.py`: `executar`, os
      agentes fixos (orquestrador e bibliotecário), as fábricas de serviço e de portas, os geradores
      de esquema (válido e hostil), de nome e de comando (§4)
- [x] **Passo 6** — `tests/ambiente/modelo.py`: `ModeloDeAmbiente`, `projetar()` e a previsão de
      resultado por comando (§4)
- [x] **Passo 7** — `tests/ambiente/instrumentos.py`: `PersistenciaEspia` e `WikiEspia`, com um
      diário de chamadas compartilhado pelas duas, falha injetada na n-ésima chamada (antes ou
      depois de delegar), conflito forçado e um ponto de suspensão opcional, para o teste da trava
- [x] **Passo 8** — `tests/ambiente/test_fronteira.py`: RN-A-01 pelo grafo de import (AST), como
      `tests/dominio/test_fronteira.py`. Proíbe também qualquer `fishingrod.adaptadores`.
      **Critério 3**
- [x] **Passo 9** — `tests/ambiente/test_servico_de_ambiente.py`, os exemplos (PBT-10): construção
      e `AgenteInvalido`; ordem wiki → banco ao criar e banco → wiki ao apagar (RN-A-14, 17); o
      `WARNING` de RN-A-18; mesmo objeto em `carregar` e depois de uma recarga (RN-A-03, G2);
      abertura implícita (RN-A-04); os 4 erros de ausência e `AmbienteInexistente` (RN-A-05, 08);
      trava: mesmo ambiente serializa, ambientes diferentes não esperam (RN-A-06); uma gravação
      por operação (RN-A-07); falha de gravação recarrega (RN-A-09, `R-CG4-1`); conflito reaplica
      (RN-A-10); 3 tentativas e desiste (RN-A-11); ambiente apagado por outro processo (RN-A-12);
      nascer sem frente (RN-A-15); falha parcial na criação (RN-A-16); nome repetido (RN-A-19);
      listar sem abrir (RN-A-20); orquestrador do construtor (RN-A-21); `AgenteDesconhecido`,
      inclusive com o nome do orquestrador (RN-A-22); `anotar_memoria` sem `salvar_ambiente` e sem
      mudar `versao` (RN-A-25); cancelamento fecha o ambiente (`R-CG4-5`). **Critérios 1, 2, 4,
      5, 6**
- [x] **Passo 10** — `tests/ambiente/test_propriedades.py`: **`PBT-U4-01` a `PBT-U4-06`**, como
      especificadas em §4
- [x] **Passo 11** — `tests/ambiente/test_integracao.py`: com os adaptadores **reais**
      (`RepositorioSQLite` e `WikiDeArquivos` sobre `tmp_path`). Cria um ambiente com esquema,
      frente, tarefa, chat do bibliotecário, etapa concluída e anotação; fecha o repositório;
      abre um repositório e um serviço novos; o ambiente volta igual (**US-05 de ponta a ponta**).
      Depois apaga, e nem o banco nem a pasta da wiki guardam nada

### Verificação e fechamento

- [x] **Passo 12** — Rodar `uv run pytest`. Depois, **testar os testes por mutação**, como em U3:
      injetar no serviço, um de cada vez, defeitos que as propriedades precisam pegar (tirar a
      recarga depois da falha; tirar a nova tentativa; inverter a ordem wiki/banco; trocar o
      objeto na recarga em vez de atualizá-lo; esquecer a trava) e confirmar que cada um derruba
      pelo menos um teste. Registrar o resultado, e endurecer o gerador que deixar passar
- [x] **Passo 13** — Emendas e fechamento: em U3, marcar a quinta operação em
      `construction/wiki/nfr-design/logical-components.md` (§1, "4 operações") e em
      `construction/wiki/code/code-summary.md` (§2), com texto riscado, nada apagado. Escrever
      `aidlc-docs/construction/ambiente/code/code-summary.md` com arquivos, decisões tomadas na
      execução, resultado da suíte e conformidade das extensões

---

## 6. Rastreio

| Especificação | Passo |
|---|---|
| RN-A-01 (fronteira) | 4, 8 |
| RN-A-02, RN-A-08 (domínio primeiro; alvo por identidade) | 4, 9, 10 |
| RN-A-03..07 (estado, abertura, trava, uma gravação) | 4, 9, 10 |
| RN-A-09..12 (falha e conflito) | 4, 9, 10 |
| RN-A-13..20 (ciclo do ambiente) | 1, 2, 4, 9, 10, 11 |
| RN-A-21..24 (estrutura) | 4, 9, 10 |
| RN-A-25..26 (memória) | 4, 9, 10 |
| `PBT-U4-01..06` | 10 |
| `PBT-U3-08` | 3 |
| `R-CG4-1..5` | 2, 4, 9, 10 |
| Critérios de pronto 1–6 | 1 → 4, 9, 10 · 2 → 4, 9 · 3 → 8 · 4 → 9, 10 · 5 → 9, 10 · 6 → 2, 3, 9, 11 |
| US-04 · US-05 · US-08 · US-09 · US-15 · US-16 · US-17 · US-19 | 4, 9, 10, 11 (US-05 também em 11, com os adaptadores reais) |

**13 passos.** 1 arquivo novo em `src/` e 2 modificados (U3 reaberta); 8 arquivos novos em
`tests/ambiente/` e 2 modificados em `tests/wiki/`; 1 resumo de código e 2 emendas de
documentação. O código antigo (`Ambiente/`, `model/`, `cli.py`, `tui.py`) **não é tocado**: pela
regra emendada em `unit-of-work.md` §4, ele sai quando o substituto for executável, e isso só
acontece em U9.

---

## 7. Conformidade das extensões (planejada)

| Extensão / regra | Estado | Como o plano cumpre |
|---|:--:|---|
| `security-baseline` SECURITY-05 (confinamento) | ✅ | `apagar` usa `resolver_raiz` e só remove raiz com índice (`R-CG4-2`); teste de link para fora roda nesta máquina (junction) |
| SECURITY-10 (dependências) | ✅ | Nenhuma dependência nova |
| SECURITY-13 (integridade) | ✅ | RN-A-09/14/16/17 testadas por exemplo e por `PBT-U4-05` |
| SECURITY-15 (falha segura) | ✅ | Erros tipados; único erro não propagado é o de RN-A-18, com log; `R-CG4-1` não engole a falha da recarga |
| Demais regras de `security-baseline` | N/A | Sem rede, servidor, IAM ou HTTP |
| PBT-01 (identificação) | ✅ | As 5 propriedades do FD, mais 2 de `R-CG4-4`, estão em §4 |
| PBT-02 (round-trip) | ✅ | `PBT-U4-01`: memória → disco → serviço novo |
| PBT-03 (invariantes) | ✅ | `PBT-U4-03`, `04`, `05` |
| PBT-04 (idempotência) | ✅ | `PBT-U4-06` e `PBT-U3-08` (`R-CG4-4`) |
| PBT-05 (oráculo) | ✅ | `ModeloDeAmbiente` em `PBT-U4-01/02`; o slug como oráculo em `PBT-U4-03` |
| PBT-06 (com estado) | ✅ | Sequências de 0 a 15 comandos, verificação depois de cada comando, modelo simplificado |
| PBT-07 (geradores) | ✅ | Geradores de domínio centralizados em `tests/ambiente/estrategias.py`, reaproveitando U2 e U3 |
| PBT-08 (encolhimento e semente) | ✅ | Padrão do Hypothesis, nada desligado. A parte de CI fica para Build and Test |
| PBT-09 (framework) | ✅ | Hypothesis, já em `dev` desde U0 |
| PBT-10 (complementar) | ✅ | Exemplos e propriedades em arquivos separados; caminhos críticos com os dois |
| `resiliency-baseline` | N/A | Desativada em Requirements Analysis |

---

## 8. Registro da execução (2026-10-02)

**13/13 passos executados.** Resultado e decisões completos em
`construction/ambiente/code/code-summary.md`. O que divergiu deste plano, e por quê, em uma linha
cada:

- **Quarto auxiliar, `_gravar`**: a reação a falha (RN-A-09, `R-CG4-1`, `R-CG4-5`) é a mesma em
  `_mutar` e em `anotar_memoria`, e ficou num lugar só. Resumo §3, decisão 1.
- **Geradores reescritos depois de medidos**: as 6 propriedades passaram de primeira, mas
  `PBT-U4-02` não teve conflito em nenhum dos 40 exemplos, `PBT-U4-05` disparava a falha em ~22%, e
  `DescricaoObrigatoria` nunca era alcançada em `PBT-U4-03`. Resumo §4.
- **`ambientes_de_partida`**, **`ponderado`** e descrição construída sem filtro entraram em
  `estrategias.py`, além do que o passo 5 listava.
- **`PBT-U4-01` gera também `criar_ambiente`**, para as 10 operações estarem na propriedade de
  estado. Resumo §3, decisão 4.
- **Um terceiro teste de integração**: conflito entre duas conexões reais ao mesmo banco. Resumo §3,
  decisão 5.
- **Mutação**: 16/16 defeitos mortos, inclusive os dois de `apagar` (link seguido, guarda do índice
  removida). Resumo §4.
