# AI-DLC State Tracking — FishingRod

## Project Information
- **Project Type**: Brownfield
- **Start Date**: 2026-08-16T01:07:01Z
- **Current Stage**: INCEPTION — Units Generation (comprehensive) **CONCLUÍDO** em 2026-08-25T17:00:00Z. Parte 1 aprovada pelo usuário ("aprovado, pode gerar os artefatos"); Parte 2 executada: 3 artefatos de unidade + 11 emendas nos artefatos de Application Design. **Aguardando aprovação explícita antes da CONSTRUCTION PHASE.** Application Design **aprovado pelo usuário** em 2026-08-25T12:00:00Z. Workflow Planning v2 **aprovada** em 2026-08-20T00:00:00Z

## Workspace State
- **Existing Code**: Yes
- **Programming Languages**: Python **3.14** (elevado de 3.13 em 2026-08-25 por CQ2=D — `uuid.uuid7()` na stdlib; U0 emendada e revalidada)
- **Build System**: nenhum declarado (sem `pyproject.toml`, `requirements.txt` ou equivalente)
- **Project Structure**: aplicação monolítica embrionária (núcleo + 2 interfaces)
- **Reverse Engineering Needed**: Yes (nenhum artefato prévio encontrado)
- **Workspace Root**: `C:\Users\pedro\OneDrive\Área de Trabalho\dev\FishingRod`

## Input Documents (fornecidos pelo usuário)
- `docs/aidlc-inputs/vision.md` — Vision Document v0, documento de entrada oficial do AI-DLC
- `produto/` — material de descoberta (dores, princípios, glossário, cenários, requisitos funcionais, critérios de sucesso, hipóteses, questões abertas)
- `informacoes-usuario/` — material bruto (transcrições e insumos do usuário)
- `informacoes-usuario/interface-v3-nexus.html` — maquete feita pelo **usuário de validação** (João); referência de **layout e navegação apenas** para a TUI (ESC-16). Contém elementos fora de escopo: painel de números (FOR-05), conectores MCP (FOR-04) e os cinco comportamentos diferenciais (FOR-06)
- `interface_ilustrativa.html` — maquete de interface (versão anterior, do dono)

## Reverse Engineering Status
- [x] Reverse Engineering — concluída em 2026-08-16T01:07:01Z (pendente de aprovação do usuário)
- **Artifacts Location**: `aidlc-docs/inception/reverse-engineering/`
- **Baseline**: commit `14f81eb`

## Code Location Rules
- **Application Code**: raiz do workspace (NUNCA em `aidlc-docs/`)
- **Documentation**: apenas em `aidlc-docs/`
- **Structure patterns**: ver `construction/code-generation.md`

## Notas retidas para Application Design
Dúvidas de arquitetura levantadas pelo usuário que **não** devem ser resolvidas em Requirements
Analysis — ficam registradas aqui para serem retomadas quando Application Design executar
(depois do escopo desta iteração estar definido):

- **Chain of Responsibility em `Ambiente → Projeto → Sessao`**: o usuário não tem certeza se é
  a decisão certa olhando para a visão de futuro do software, mesmo reconhecendo que foi o
  caminho natural de como chegou implementando. Levantado em 2026-08-16.
- **Pedido explícito do usuário (Questão B1)**: quer revisar as decisões de arquitetura desta
  iteração "com o software system lead" antes de fechá-las — sinal para tratar Application
  Design e NFR Requirements/Design com profundidade completa (comprehensive), não superficial,
  quando esses estágios rodarem. Levantado em 2026-08-16.
- **Forma concreta da porta de sessão viva**: Requirements Analysis fixou apenas o **quê**
  (aceitar autenticação por assinatura e por API key como conceitos de primeira classe, só
  assinatura implementada agora — Questão C2, clarificação respondida em 2026-08-17). O **como**
  (assinaturas de `abrir`/`enviar`/`fechar`, forma de modelar o modo de autenticação) fica para
  Application Design.
- **Sequenciamento das dívidas técnicas críticas (TD-01 a TD-04)**: o usuário pediu
  explicitamente (Questão D2) que a correção só aconteça **depois** de as decisões de
  arquitetura desta iteração estarem fechadas, para não corrigir código que Application Design
  pode redesenhar. Levantado em 2026-08-17.

Acrescentadas na revisão do plano de execução em 2026-08-19 (ver `requirements.md` §9.8):

- **Critério de decisão do bibliotecário entre entidade e propriedade.** O usuário escolheu que
  "propriedade pode ser instância" (um arquivo dentro de `clientes/` pode ser tanto
  `criterios-de-icp.md` quanto `dr-marcelo.md`). Isso é mais fiel ao uso real, mas deixa em
  aberto a regra que o bibliotecário usa para decidir entre criar entidade nova e criar arquivo
  dentro de entidade existente. **É o risco número um do desenho da wiki**: sem regra, ele decide
  diferente a cada vez e a wiki apodrece em semanas.
- **Qual grafo manda na recuperação**: a hierarquia de pastas ou os links `[[...]]`, quando
  discordarem. Determina como o `index.md` é construído e mantido atualizado.
- **Desenho concreto da wiki**: formato do arquivo de esquema, frontmatter (se houver), sintaxe e
  resolução dos links, geração e manutenção do `index.md`, política de conflito quando duas
  escritas tocam a mesma página.
- **Estratégia interna do SQLite** — o que exatamente é documento e o que é tabela — e desenho da
  identidade (UUID vs ULID, onde é gerada, como atravessa a serialização).
- **Assinaturas das ferramentas do bibliotecário** e escopo de permissão das ferramentas de
  arquivo nativas do agente. O spike mediu permissão de ferramenta **MCP**; escopo de ferramenta
  de **arquivo** não foi medido e precisa ser verificado, não assumido.
- **Forma concreta da porta de sessão** sobre o ciclo assíncrono já medido pelo spike
  (`async with ClaudeSDKClient(...)` → `query()` → `receive_response()`), e como o streaming da
  resposta chega à TUI.

## Extension Configuration

| Extension | Enabled | Decided At | Nota |
|---|---|---|---|
| security-baseline | Yes | Requirements Analysis, 2026-08-17 | Aplicar de forma proporcional: hoje é processo local single-process, sem rede exposta, sem servidor web — a maioria das 15 regras (headers HTTP, load balancer, IAM de nuvem, CORS, rede) tende a N/A neste estágio. As que já se aplicam agora: SECURITY-10 (dependências travadas, ver Questão D3), SECURITY-12 (gestão de credenciais — chaves de API de LLM e, mais à frente, tokens de MCP), SECURITY-13 (integridade de dados, relevante quando a persistência entrar), SECURITY-15 (tratamento de exceção e fail-safe). Reavaliar a cada estágio, sem travar a decisão aqui. |
| resiliency-baseline | No | Requirements Analysis, 2026-08-17 | Overengineering para o estágio atual — uso inicial restrito a até ~20 usuários selecionados pelo dono |
| property-based-testing | Yes (Full) | Requirements Analysis, 2026-08-17 | Enforcement completo, não parcial. Regras PBT-01 a PBT-10 passam a valer a partir de Functional Design / NFR Requirements — nada bloqueante ainda em Requirements Analysis |

## Execution Plan Summary

- **Artifact**: `aidlc-docs/inception/plans/execution-plan.md` (**v2**, 2026-08-19)
- **Risk Level**: High
- **Total Stages**: 14 (7 INCEPTION, 6 CONSTRUCTION, 1 OPERATIONS placeholder)
- **Stages to Execute**: Application Design, Units Generation, Functional Design, NFR Requirements, NFR Design, Code Generation, Build and Test
- **Stage to Skip**: Infrastructure Design — sem infraestrutura ou deploy; reforçado na v2 (interface web fora de escopo, cada usuário roda na própria máquina, não existe nem servidor local)
- **Depth**: comprehensive para todos os estágios de design; detalhe de Code Generation adaptado por unidade sem reduzir quality gates
- **Next Stage after Approval**: Application Design

### Decisões fechadas na revisão v2 (2026-08-19)

| # | Decisão | Rastreio em `requirements.md` |
|---|---|---|
| 1 | Persistência SQLite (`sqlite3`, stdlib) atrás de porta de domínio; híbrida (documento para estrutura, tabela para transcrição) | ESC-13, D-ARQ-04 |
| 2 | Identidade opaca e estável (UUID/ULID) substitui índice e nome | ESC-14, RF-F16, D-ARQ-05 |
| 3 | Uma porta de sessão, um adaptador Claude; API key fora inclusive do desenho; **RF-F04 mantido** | ESC-18, FOR-09, D-ARQ-06 |
| 4 | Scaffolding com `uv`, layout `src/`, lockfile, `exclude-newer` | ESC-15 |
| 5 | TUI (Textual) é a única interface entregável; `cli.py` é experimentação sem garantias; web adiada | ESC-16, FOR-10, FOR-11, D-ARQ-07 |
| 6 | Wiki no filesystem em markdown (fonte da verdade); entidade=pasta / propriedade=arquivo em dois níveis; `index.md`; links `[[...]]`; acesso só por tools do bibliotecário; esquema plugável como semente; `raw/` e `lint` fora | ESC-17, ESC-19, ESC-20, FOR-12, RF-F13/14/15, D-ARQ-08 |
| 7 | Cada usuário roda na própria máquina, com a própria assinatura | D-ARQ-09 |
| 8 | Linha fina de 14 histórias; US-07, US-10, US-11, US-12, US-18 adiadas | §9.6, FOR-14 |

**Revogações da v1**: ESC-02, RF-F02 e D-ARQ-01 (dupla autenticação) revogados; ESC-03
substituído por ESC-18; FOR-07 endurecido por FOR-09. **RF-F04 permanece integralmente em vigor.**

**Hipótese que a iteração valida**: o loop ambiente → conversa → wiki torna o ambiente mais
inteligente com o tempo.

## Stage Progress

### INCEPTION
- [x] Workspace Detection — concluída em 2026-08-16T01:07:01Z
- [x] Reverse Engineering — **aprovada pelo usuário** em 2026-08-16T01:25:00Z
- [x] Requirements Analysis — **aprovada pelo usuário** em 2026-08-18T00:05:00Z; **emendada (v2) em 2026-08-19** por decisão do usuário na revisão do plano. Artefato: `aidlc-docs/inception/requirements/requirements.md` (§9 = emenda, com tabela de revogações)
- [x] User Stories — **aprovada pelo usuário** em 2026-08-18T00:50:00Z; **escopo revisado (v2) em 2026-08-19** — texto das 23 histórias preservado, 14 na linha fina, 5 adiadas, 4 já fora. Artefatos: `aidlc-docs/inception/user-stories/personas.md`, `aidlc-docs/inception/user-stories/stories.md`
- [x] Workflow Planning — **v2** concluída em 2026-08-19T18:40:00Z; **aprovada pelo usuário** em 2026-08-20T00:00:00Z ("esta aprovado. vamos continuar"). Artefato: `aidlc-docs/inception/plans/execution-plan.md`
- [x] Application Design — EXECUTE (comprehensive) — **aprovado pelo usuário** em 2026-08-25T12:00:00Z ("eu aprovo o plano. vamos continuar o ai-dlc"); os 5 pontos abertos da §7 de `application-design.md` foram aprovados sem objeção. Parte 1: `application-design-plan.md` (17/17 decisões fechadas — 16 na rodada 1 em 2026-08-23, mais a Pergunta 8 refeita e as 6 clarificações A–G respondidas e fechadas em 2026-08-23/24) + `application-design-clarification-questions.md`. Plano original preservado íntegro em `application-design-plan.bruto-2026-08-23.md`; `application-design-plan.md` reescrito limpo (G=A) em 2026-08-25. Parte 2: os 5 artefatos obrigatórios gerados em `aidlc-docs/inception/application-design/` — `components.md`, `component-methods.md`, `services.md`, `component-dependency.md`, `application-design.md`. 14/14 histórias da linha fina rastreadas a componente; núcleo sem `claude_agent_sdk`/`sqlite3`/Textual verificável por checklist
- [x] Units Generation — EXECUTE (comprehensive) — **APROVADO pelo usuário em 2026-08-25T19:00:00Z** ("concordo com a abordagem de sempre pedir, com essa mudança e entendimento, podemos aprovar e continuar"), após a rodada 4 de mudanças (CQ2/CQ3/CQ4 revogadas). Parte 1: 18 decisões fechadas (Q1–Q14, CQ1–CQ4) em 3 rodadas; Parte 2: 3 artefatos de unidade + 11 emendas marcadas (nunca apagadas) nos artefatos de Application Design. Artefato: `aidlc-docs/inception/plans/unit-of-work-plan.md` (decomposição candidata de 9 unidades + 10 perguntas com tag `[Answer]:` cobrindo as seis categorias obrigatórias). Aguardando respostas do usuário; Parte 2 (geração de `unit-of-work.md`, `unit-of-work-dependency.md`, `unit-of-work-story-map.md`) bloqueada até as respostas serem analisadas e o plano aprovado

### CONSTRUCTION
- [ ] Functional Design — EXECUTE por unidade aplicável (comprehensive)
- [ ] NFR Requirements — EXECUTE por unidade aplicável (comprehensive)
- [ ] NFR Design — EXECUTE por unidade aplicável (comprehensive)
- [ ] Infrastructure Design — SKIP (sem infraestrutura ou deploy; reforçado na v2 — sem interface web e sem servidor local)
- [~] Code Generation — EXECUTE por unidade (obrigatório)
  - [x] **U0 `fundacao`** — Parte 1 (plano) aprovada e Parte 2 executada em 2026-08-25T19:30:00Z; 7/7 passos, `uv sync` + `uv run pytest` (2 passando) verificados. Artefatos: `pyproject.toml`, `uv.lock`, `src/fishingrod/` (7 camadas), `tests/`. Resumo: `construction/fundacao/code/code-summary.md`. **APROVADO pelo usuário em 2026-08-25T20:00:00Z** ("aprovado, vamos para o U1")
  - [~] **U1 `dominio`** — Functional Design **concluído** em 2026-08-26 (3 rodadas: 9 respostas + 3 clarificações). Artefatos: `construction/dominio/functional-design/{domain-entities,business-rules,business-logic-model}.md` — 15 regras RN-01..RN-15, 7 propriedades PBT nomeadas, 4 emendas a aplicar em Application Design. **APROVADO pelo usuário em 2026-08-26T00:30:00Z** ("aprovado. continue") — inclui a revogação da Parte B.3 (invariante 'ao menos uma entidade' na criação da wiki), a aplicar como emenda quando U3/U4 chegarem. Code Generation **executado** em 2026-08-26: 11 módulos (491 linhas) em `src/fishingrod/dominio/`, 7 arquivos de teste (375 linhas, 39 testes), **41 passed**. TD-03 morta. 4 emendas aplicadas em Application Design. Resumo: `construction/dominio/code/code-summary.md`. **Aguardando aprovação do código**
  - [ ] U2 `persistencia` → U9 `interface` (sequencial)
- [ ] Build and Test — EXECUTE após todas as unidades (obrigatório)

### OPERATIONS
- [ ] Operations — PLACEHOLDER

## Current Status
- **Lifecycle Phase**: **CONSTRUCTION** (INCEPTION encerrada e aprovada em 2026-08-25T19:00:00Z)
- **Current Stage**: Units Generation (comprehensive) — **concluído**. Parte 1 aprovada em 2026-08-25T17:00:00Z; Parte 2 executada. **10 unidades** (U0 `fundacao` fora do loop, U1 `dominio`, U2 `persistencia`, U3 `wiki`, U4 `ambiente`, U5 `acoes`, U6 `sessao`, U7 `conversa`, U8 `bibliotecario`, U9 `interface`+composition root). Ordem de execução estritamente sequencial U0→U9; grafo acíclico (matriz triangular inferior). **31 portões** de aprovação no CONSTRUCTION, com cada SKIP justificado por unidade. Artefatos: `unit-of-work.md`, `unit-of-work-dependency.md`, `unit-of-work-story-map.md`. **Correção de ordem descoberta na geração**: a unidade de ambiente depende da unidade de wiki (`criar_ambiente` materializa a wiki), então wiki passou a ser U3 e ambiente U4 — a ordem candidata do plano estava invertida. **Aguardando aprovação explícita antes da CONSTRUCTION PHASE**
- **Next Stage**: **Code Generation de U1** (Parte 1: plano; Parte 2: código do domínio). ~~**CONSTRUCTION — U0 `fundacao`, Code Generation**~~ (único estágio de U0; FD/NFR-R/NFR-D/INFRA são SKIP justificados em `unit-of-work.md` §3). Depois: U1 `dominio` → ... → U9 `interface`, estritamente sequencial
- **Decisões fechadas na Parte 1**: Q1=A granularidade fina · Q2=A decomposição horizontal · Q3=C fundação `uv` primeiro, fora do loop (executada como passo 0 do CONSTRUCTION, ver R5) · Q4=A só teste automatizado até a interface · Q5=B `ServicoDeAmbiente` unidade própria · Q6=A wiki e bibliotecário separados · Q7=A estritamente sequencial · Q8=A `src/` novo · Q9=A camada no topo · Q10=B vários ambientes locais, sem unidade própria · Q11=A MCP in-process · Q12=A exposição de ferramentas na unidade de sessão · Q13=A `buscar` sai desta iteração · Q14=X orquestrador sem ferramentas de wiki, delega criando chat do bibliotecário
- **Fechadas na rodada 3**: **CQ1=A** portão do índice só determinístico (sem LLM no laço) · **CQ2=A + parâmetro** — não há confirmação embutida no código; existe um parâmetro de aprovação de ação por agente, **ligado por padrão** e desligável pelo usuário (a letra A passa a descrever o estado desligado, ver R8)
- **Vocabulário oficial adotado em 2026-08-25 (R9)**: **`ferramentas de ambiente`** (tocam `Ambiente`/`Frente`/`Tarefa`/`Etapa`/`Chat`; são do orquestrador; unidade de ações) vs **`ferramentas de wiki`** (tocam páginas e índice; são do bibliotecário; unidade de wiki/bibliotecário). Substitui "ferramentas que mudam estado", que era classificação por efeito colateral e não coincidia com limite de unidade. **Ressalva registrada**: as duas famílias mudam estado, então o parâmetro de aprovação vale para as duas, unificando a aprovação de proposta do bibliotecário (Decisão 15) no mesmo mecanismo
- **Reconciliações novas da rodada 3**: R8 (tensão entre a letra A e a observação, resolvida a favor da observação), R9 (vocabulário), R10 (o invariante "só o orquestrador tem ferramenta de ambiente" é teste de configuração determinístico, na unidade de sessão)
- **Total de unidades**: **10** (Q1=A + Q5=B). Nenhuma unidade `ferramentas-de-agente` — Q12=A a colocou dentro da unidade de sessão
- **Rodada 4 (2026-08-25T18:30:00Z) — mudanças pedidas no portão**: o usuário confirmou a correção de ordem (já aplicada), aceitou o risco de nada ser demonstrável antes de `U9` e **revogou CQ2/CQ3/CQ4** — o parâmetro configurável de aprovação sai desta iteração. No lugar: política constante `exige_aprovacao(...)` em `dominio/politica.py` (U1), sempre `True`, consultada por U5 e U8; `Ambiente` não ganha campo; U2 perde o critério de compatibilidade regressiva; U9 perde a tela de configuração mas **mantém o fluxo de confirmação, que já era exigido por US-14**. 31 portões inalterados. Registrado na Parte H de `unit-of-work-clarification-questions.md`; 6 artefatos emendados com texto riscado, nunca apagado
- **Aberto**: nada de conteúdo — só o portão de aprovação do plano. **CQ3=A** (o campo `aprovacao_de_agente_obrigatoria`, padrão ligado, mora em `Ambiente` → unidade de domínio; a persistência ganha o critério de carregar `Ambiente` antigo sem o campo) e **CQ4=A** (o fluxo de confirmação é construído nesta iteração, na unidade de interface, **um só fluxo** para ferramentas de ambiente e para a proposta do bibliotecário). Registrado que o parâmetro **não tem história de origem** entre as 14 da linha fina e vai aparecer assim no story map. Mais 7 reconciliações declaradas na Parte C do arquivo de clarificação, aguardando objeção — com destaque para **R4**, que evita uma dependência nova `ServicoConversa → CatalogoDeAcoes` na matriz de `component-dependency.md`, e **R1**, que promete declarar por unidade quais estágios CONDITIONAL do CONSTRUCTION executam e quais são SKIP
- **Correção registrada**: minha frase sobre o `index.md` "deixar de ser navegação" estava errada e foi riscada (não apagada) no `unit-of-work-plan.md`; o índice é navegação e já era o ponto de entrada obrigatório desde a Decisão 6. O que Q13=A muda é a remoção do plano B (grep), não o papel do índice
- **Respostas do usuário aos pontos abertos de Application Design §7** (escritas inline em `application-design.md` §7 em 2026-08-25, registradas na §1.1 de `unit-of-work-plan.md`): ponto 1 = incluir `propor_entidade` (confirma o desenho); ponto 3 = busca começa sempre pelo `index.md`, agente lê o índice e depois as páginas (**contradiz `components.md` §5.4**, que menciona `ripgrep` → Q13); ponto 5 = orquestrador é o agente principal e recebe as ações do catálogo como ferramentas, com escopo de ferramenta por tipo de agente (**aumenta escopo** → Q11, Q12, Q14). Pontos 2 e 4 sem resposta (2 → Q10; 4 fica como desenhado). Consequência registrada: o `index.md` deixa de ser navegação e passa a ser o mecanismo de recuperação, mudando o critério de aceite da unidade de wiki; e o isolamento de contexto que sustentava RNF-14 fica enfraquecido enquanto a Q14 não for respondida — conformidade de `security-baseline` **não** declarada resolvida até então
- **Status de Application Design (encerrado)**: 17/17 decisões de desenho fechadas (16 na rodada 1 em 2026-08-23; Pergunta 8 refeita e as 6 clarificações A–G da rodada 2 respondidas e fechadas em 2026-08-23/24). Plano limpo em 2026-08-25 (G=A), original íntegro preservado em `application-design-plan.bruto-2026-08-23.md`. Os 5 artefatos obrigatórios foram gerados: `components.md`, `component-methods.md`, `services.md`, `component-dependency.md`, `application-design.md` (todos em `aidlc-docs/inception/application-design/`). As 14 histórias da linha fina estão rastreadas a componente e a RF/RNF em `application-design.md` §3. 5 dívidas técnicas (TD-01, TD-02, TD-03, TD-04, TD-11) têm unidade destino e critério de aceite nomeado. Conformidade das extensões `security-baseline` e `property-based-testing` registrada (nomeação de propriedades, não especificação — isso é de Functional Design). 5 pontos abertos não bloqueantes registrados em `application-design.md` §7 para o portão de aprovação. **Aguardando aprovação explícita do usuário antes de Units Generation.**
- **Escopo desta iteração**: 14 histórias (linha fina), interface TUI, SQLite + wiki no filesystem, um adaptador Claude
