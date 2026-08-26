# Requirements — FishingRod (Iteração 1)

**Versão:** v2 · **Data base:** 2026-08-17 · **Emendada em:** 2026-08-19 · **Estágio:** INCEPTION — Requirements Analysis
**Origem:** `docs/aidlc-inputs/vision.md`, `produto/`, Reverse Engineering, e 19 respostas do usuário
(18 em `requirement-verification-questions.md` + 1 em `requirement-verification-clarification-questions.md`)

> **Emenda v2 (2026-08-19)**: durante a revisão do plano de execução, o usuário reabriu e mudou
> decisões de escopo. As alterações estão na **§9 — Emenda v2**, com tabela de revogações e
> rastreio. Itens revogados foram marcados no corpo do documento, **não apagados**, para
> preservar a auditabilidade do que foi aprovado na v1.

---

## 1. Resumo da análise de intenção

| Campo | Avaliação |
|---|---|
| **Pedido do usuário** | Iniciar desenvolvimento de software usando AI-DLC, a partir de um código brownfield embrionário e de um Vision Document que deixou o escopo da iteração (§5) intencionalmente em branco para ser decidido neste estágio |
| **Tipo de pedido** | Novo produto sobre base existente — mistura de **New Project** (a maior parte do valor de negócio ainda não existe) e **Enhancement/Refactoring** (parte do código embrionário precisa ser corrigido e reorganizado antes) |
| **Clareza do pedido** | Inicialmente vaga apenas num ponto (o escopo da iteração); o restante do material de descoberta (`produto/`) já era denso e consistente |
| **Estimativa de escopo** | Sistema inteiro — toca núcleo (`Ambiente/`), interfaces (`cli.py`, `tui.py`) e introduz conceitos novos (porta de sessão viva, persistência, wiki) |
| **Estimativa de complexidade** | Moderada a complexa — não pela quantidade de código, mas pelo número de decisões de arquitetura ainda em aberto (porta de sessão viva com autenticação dupla, Chain of Responsibility, sequenciamento de dívida técnica) |
| **Profundidade adotada** | **Comprehensive** — múltiplas decisões arquiteturais com impacto de longo prazo, pedido explícito do usuário de revisão profunda ("com o software system lead") antes de fechar decisões, e necessidade de rastreabilidade com o material de descoberta já existente |

---

## 2. Escopo desta iteração

Esta seção **preenche `vision.md` §5**, que foi deixada em branco de propósito para ser decidida
neste estágio do AI-DLC.

### 2.1 Dentro do escopo

| # | Item | Fonte |
|---|---|---|
| **ESC-01** | Corrigir `AgenteClaude.responder()` para de fato conversar com um LLM real (hoje devolve `None` — TD-01) | B1=A, D2=A |
| **ESC-02** | ~~Desenhar a **porta de sessão viva** (`abrir`/`enviar`/`fechar`) already prevista para **dois tipos de autenticação** de LLM como conceitos de primeira classe: por assinatura (login, cota da assinatura) e por API key (paga por uso)~~ — **REVOGADO na v2**, ver §9 | C2 (clarificação, resposta A) |
| **ESC-03** | ~~**Implementar apenas o adaptador por assinatura** (via `claude-agent-sdk`) nesta iteração; o adaptador por API key fica previsto no desenho, não construído~~ — **SUBSTITUÍDO na v2 por ESC-18**, ver §9 | C2 (clarificação, resposta A) |
| **ESC-04** | Desacoplar o núcleo do `claude_agent_sdk` — nenhum tipo do SDK importado fora do adaptador (hoje violado em `Ambiente/agente.py:6` — TD-02) | vision.md §6.3, D2=A |
| **ESC-05** | Persistência de ambiente/sessão suficiente para uso diário real (criar, fechar o processo, reabrir e continuar) — corrige TD-04 | B3=A |
| **ESC-06** | Corrigir `Memoria.anotar()` para não lançar `KeyError` na primeira escrita de uma chave nova (TD-03) | D2=A |
| **ESC-07** | Wiki mínima, **por ambiente**, presente desde a criação — formato/estrutura é abstração customizável do ambiente, não um esquema fixo do produto | B4=A (com correção do usuário) |
| **ESC-08** | Dois agentes especiais, em versões simples: **rod-maker** (constrói agentes) e **bibliotecário** (escreve na wiki) | C3=D, H-01, H-02 |
| **ESC-09** | Mínimo colaborativo para **um usuário** (o dono/admin, sem multiusuário): criar tarefas (RF-01), criar agentes (RF-02), escrever na wiki por caminho verificado (RF-03), acionar chats de IA para planejar/criar agentes/executar (RF-07 parcial) | B2=A (multiusuário fora), RF-01/02/03/07 |
| **ESC-10** | Gestão de dependências declarada (arquivo de build/lockfile) | D3=A |
| **ESC-11** | Suíte de testes automatizados desde já, incluindo testes baseados em propriedade (Hypothesis) a partir de Functional Design/NFR Requirements | D3=A, property-based-testing=Yes(Full) |
| **ESC-12** | Validar a generalidade da estrutura contra **dois domínios**: o ambiente de marketing do usuário (`cenarios/01`, alvo de CS-01) e o ambiente de estudos (`cenarios/02`) | E1=A |

### 2.2 Explicitamente fora do escopo

| # | Item | Motivo |
|---|---|---|
| **FOR-01** | Multiusuário e concorrência | B2=A — decisão explícita do usuário |
| **FOR-02** | Governança/admin (RF-08 a RF-10) | Derivado de FOR-01 — restringir outros usuários não faz sentido sem outros usuários |
| **FOR-03** | Nuvem e deploy | vision.md §5, candidato natural dado o estado do código |
| **FOR-04** | Conexões MCP externas configuráveis (RF-11, RF-12) | E2=A — credenciais/MCP ainda não relevantes |
| **FOR-05** | Dashboard de números como interface | P-09 — rejeitado explicitamente pelo usuário |
| **FOR-06** | Os 5 comportamentos diferenciais: contrato consome/entrega, travamento por artefato, momento humano, promoção de diretriz, tipo de tarefa configurável | C1=A — nenhum ainda |
| **FOR-07** | ~~Adaptador de autenticação por API key **implementado** (fica só desenhado — ver ESC-02/ESC-03)~~ — **ENDURECIDO na v2 por FOR-09**: a autenticação por API key sai inteira, nem desenhada | C2 (clarificação, resposta A) |
| **FOR-08** | Renomear vocabulário do código (`Projeto`→Frente, `Sessao`→Tarefa/Card, etc.) | D1=B — manter vocabulário atual por ora |

---

## 3. Requisitos funcionais

| ID | Requisito | Critério de pronto | Rastreio |
|---|---|---|---|
| **RF-F01** | O ambiente conversa com um LLM real através de um agente (`AgenteClaude` ou equivalente) | Uma mensagem enviada a um agente real recebe resposta do modelo, não `None` nem stub | ESC-01, TD-01 |
| **RF-F02** | ~~A porta de sessão viva aceita, como conceito de desenho, autenticação por assinatura e por API key~~ — **REVOGADO na v2**, ver §9 | — | ESC-02 |
| **RF-F03** | Apenas o adaptador por assinatura está implementado e funcional nesta iteração | Um usuário consegue abrir uma sessão viva, enviar mensagens e fechar, autenticado via login de assinatura (`claude-agent-sdk`) | ESC-03 |
| **RF-F04** | O núcleo (`Ambiente`, `Projeto`, `Sessao`, `Chat`) não importa nenhum tipo do `claude_agent_sdk` | Inspeção de imports do núcleo não encontra `claude_agent_sdk`; o núcleo roda mesmo sem o pacote instalado | ESC-04, TD-02 |
| **RF-F05** | Estado de um ambiente sobrevive ao encerramento do processo | Encerrar e reabrir a aplicação restaura ambientes, tarefas e conversas anteriores | ESC-05, TD-04 |
| **RF-F06** | `Memoria.anotar()` aceita a primeira escrita de uma chave nova sem lançar exceção | Anotar uma chave inédita no blackboard não levanta `KeyError` | ESC-06, TD-03 |
| **RF-F07** | Todo ambiente tem uma wiki própria desde a criação, mesmo que pequena | Criar um ambiente cria também sua wiki (vazia ou mínima); não existe ambiente sem wiki | ESC-07, RF-03 |
| **RF-F08** | A estrutura/formato da wiki é configurável por ambiente, não fixa no produto | Dois ambientes podem organizar a wiki de formas diferentes sem mudança de código | ESC-07, P-12 |
| **RF-F09** | Existe um agente rod-maker capaz de construir outros agentes (versão simples) | Acionar o rod-maker resulta num novo agente disponível no ambiente | ESC-08, RF-02, H-01 |
| **RF-F10** | Existe um agente bibliotecário capaz de escrever na wiki por caminho verificado (versão simples) | Acionar o bibliotecário resulta em conteúdo adicionado à wiki, na categoria/formato do ambiente | ESC-08, RF-03, H-02 |
| **RF-F11** | O usuário (dono) cria tarefas dentro de uma frente/projeto | Uma tarefa criada aparece na estrutura do ambiente e pode receber etapas | ESC-09, RF-01 |
| **RF-F12** | O usuário aciona chats de IA para planejar tarefas, criar agentes e executar tarefas | Cada uma das três ações é alcançável sem sair do ambiente | ESC-09, RF-07 |

---

## 4. Requisitos não funcionais

| ID | Requisito | Origem |
|---|---|---|
| **RNF-01** | Dependências do projeto declaradas em arquivo de build com lockfile (ex.: `pyproject.toml` + lock) | D3=A |
| **RNF-02** | Suíte de testes automatizados criada desde esta iteração, cobrindo ao menos as correções de TD-01 a TD-04 | D3=A |
| **RNF-03** | Testes baseados em propriedade (Hypothesis) aplicados com enforcement completo a partir de Functional Design/NFR Requirements/Code Generation/Build and Test — ver `property-based-testing.md`, regras PBT-01 a PBT-10 | property-based-testing=Yes (Full) |
| **RNF-04** | Gestão de credenciais de autenticação de LLM (token de assinatura e, futuramente, API key) não fica hardcoded nem versionada — ver SECURITY-12 | security-baseline=Yes |
| **RNF-05** | Integridade dos dados persistidos (ambiente/sessão) — escrita e leitura consistentes, sem corrupção silenciosa — ver SECURITY-13 | security-baseline=Yes, ESC-05 |
| **RNF-06** | Tratamento de exceção com fail-safe (uma falha no adaptador de LLM não derruba a TUI/CLI) — ver SECURITY-15 | security-baseline=Yes |
| **RNF-07** | Regras de `security-baseline.md` orientadas a rede/nuvem (headers HTTP, load balancer, IAM, CORS) são **N/A** nesta iteração — processo local, single-process, sem servidor exposto. Reavaliar a cada estágio seguinte, sem travar a decisão aqui | security-baseline=Yes (proporcional) |
| **RNF-08** | resiliency-baseline não se aplica nesta iteração (overengineering para uso restrito a poucos usuários selecionados pelo dono) | resiliency-baseline=No |
| **RNF-09** | A estrutura montada (ambiente, frente, tarefa, wiki) deve generalizar entre pelo menos dois domínios distintos, sem hardcode de vocabulário de um domínio específico | E1=A, CS-01, vision.md §2.4 |

---

## 5. Decisões de arquitetura tomadas nesta iteração

| Decisão | Descrição |
|---|---|
| **D-ARQ-01** | ~~A porta de sessão viva nasce desenhada para dois modos de autenticação (assinatura, API key) como conceitos de primeira classe, mas só o modo assinatura é implementado agora — resposta do usuário à ambiguidade da Questão C2~~ — **REVOGADO na v2 e substituído por D-ARQ-06**, ver §9 |
| **D-ARQ-02** | O vocabulário do código (`Projeto`, `Sessao`, `Chat`) é mantido nesta iteração, apesar da divergência conhecida com o vocabulário do usuário (Frente, Card/Tarefa, Aba) — decisão D1=B, revisitável depois |
| **D-ARQ-03** | Correção das dívidas técnicas críticas (TD-01 a TD-04) é sequenciada **depois** de as decisões de arquitetura desta metodologia (Application Design) estarem fechadas — ressalva explícita do usuário na Questão D2, para evitar corrigir código que a próxima etapa pode redesenhar |

## 6. Decisões de arquitetura explicitamente NÃO tomadas aqui (adiadas para Application Design)

Conforme `aidlc-state.md` § Notas retidas para Application Design:

- **Chain of Responsibility em `Ambiente → Projeto → Sessao`** — o usuário tem dúvida se é o
  padrão certo olhando para a visão de futuro do software, mesmo reconhecendo que foi o caminho
  natural de implementação. Não resolvida aqui; será retomada em Application Design.
- **Forma concreta da porta de sessão viva** (assinaturas exatas de `abrir`/`enviar`/`fechar`,
  como o modo de autenticação é modelado — parâmetro, estratégia, objeto de configuração) —
  Requirements Analysis fixou **o quê** (dois modos, um implementado), não **como**.
- **Sequenciamento técnico exato de TD-01 a TD-04** — a ordem relativa entre si e frente às
  decisões de Application Design será definida quando esse estágio rodar.

O usuário pediu explicitamente (Questão B1) revisão profunda dessas decisões "com o software
system lead" antes de fechá-las — sinal para tratar Application Design e NFR Requirements/Design
com profundidade **comprehensive** quando esses estágios rodarem.

---

## 7. Rastreabilidade

| Seção deste documento | Origem |
|---|---|
| 2. Escopo | Respostas B1–B4, C1–C3, D1–D3, E1–E2, clarificação C2 |
| 3. Requisitos funcionais | `produto/requisitos/funcionais.md` (RF-01, 02, 03, 07), `code-quality-assessment.md` (TD-01 a TD-04), respostas B/C |
| 4. Requisitos não funcionais | `security-baseline.md`, `property-based-testing.md`, resposta D3 |
| 5–6. Decisões de arquitetura | Questão C2 (clarificação), `aidlc-state.md` § Notas retidas para Application Design |
| Fora de escopo | `vision.md` §5 (candidatos naturais), P-09, respostas B2, C1, C2, E2 |

---

## 8. Resumo executivo

Esta iteração fecha a **fundação técnica** do FishingRod para um único usuário: conversa real
com LLM através de uma porta de sessão viva já pensada para dois modos de autenticação (mas só
assinatura implementada), núcleo desacoplado do SDK, persistência mínima, wiki obrigatória e
customizável por ambiente, e dois agentes especiais (rod-maker, bibliotecário) em versões
simples. Os cinco comportamentos diferenciais de negócio (contrato consome/entrega, travamento
por artefato, momento humano, promoção de diretriz, tipo de tarefa configurável) e o
multiusuário ficam explicitamente fora, para uma iteração futura. Duas decisões de arquitetura
seguem em aberto de propósito — o padrão Chain of Responsibility e a forma concreta da porta de
sessão viva — e serão resolvidas em Application Design, com profundidade comprehensive, a pedido
do usuário.

> **Nota v2**: o trecho acima descreve a v1. A v2 removeu a dupla autenticação e acrescentou
> decisões de substrato (SQLite, filesystem para wiki), de interface (TUI) e de escopo de
> histórias. Ver §9.

---

## 9. Emenda v2 — 2026-08-19

**Contexto**: durante a revisão do plano de execução (INCEPTION — Workflow Planning), o usuário
levantou cinco pontos e, após discussão com argumentação de custo/benefício, mudou decisões que
haviam sido aprovadas na v1. Registro completo da discussão em `audit.md`.

### 9.1 Revogações e substituições

| Item da v1 | Estado na v2 | Motivo |
|---|---|---|
| **ESC-02** — porta desenhada para dois modos de autenticação | **Revogado** | Generalidade especulativa. `claude-agent-sdk` é orientado a sessão e assíncrono; um cliente por API key é stateless request/response. As formas são genuinamente diferentes, e desenhar uma porta para a segunda sem construí-la tem alta chance de estar errada. |
| **ESC-03** — só o adaptador por assinatura implementado | **Substituído por ESC-18** | Não existe mais "só um dos dois": existe um único adaptador, sem contraparte prevista. |
| **RF-F02** — porta aceita dois modos de autenticação | **Revogado** | Consequência direta da revogação de ESC-02. |
| **D-ARQ-01** — dupla autenticação como conceito de primeira classe | **Revogado, substituído por D-ARQ-06** | Idem. |
| **FOR-07** — adaptador por API key não implementado (só desenhado) | **Endurecido por FOR-09** | Sai inteiro do escopo, inclusive do desenho. |

**RF-F04 permanece integralmente em vigor.** A revogação acima elimina a *abstração de dupla
autenticação*, **não** a fronteira com o SDK. Manter o núcleo livre de `claude_agent_sdk`
continua obrigatório, por três motivos independentes de arquitetura: (a) testar o núcleo sem
credencial e sem rede, pré-requisito para PBT determinístico e para automação; (b) manter
`AgenteTeste` funcional; (c) isolar falha do provedor (US-03 / RNF-06).

### 9.2 Novos itens dentro do escopo

| # | Item | Origem |
|---|---|---|
| **ESC-13** | Persistência local em **SQLite** (`sqlite3` da biblioteca padrão), atrás de uma **porta modelada pelo domínio**, com estratégia **híbrida**: estrutura do ambiente serializada como documento; mensagens/transcrição normalizadas em tabela. | Discussão 2026-08-19, ponto 1 |
| **ESC-14** | **Identidade opaca e estável** (UUID/ULID) para as entidades do domínio, gerada na criação. Nem posicional (`indice_ativo`) nem nominal (nome muda: existe `/nome-chat`). | Discussão 2026-08-19 |
| **ESC-15** | Scaffolding do projeto com **uv**: `pyproject.toml`, `uv.lock`, layout `src/` com pacote real (hoje `Ambiente/` e `model/` são namespace packages que só resolvem da raiz), política de idade mínima de versão (`exclude-newer`). | Discussão 2026-08-19, ponto 3 |
| **ESC-16** | **TUI (Textual)** é a única interface entregável da iteração, evoluindo `tui.py`. O mockup `informacoes-usuario/interface-v3-nexus.html` serve como referência de **layout e navegação apenas**. | Discussão 2026-08-19, pontos 4 e observação sobre o João ser usuário de terminal |
| **ESC-17** | **Wiki é um diretório de arquivos markdown no filesystem, e o arquivo é a fonte da verdade.** Abstração: **entidade** = pasta (substantivo; cresce na vertical), **propriedade** = arquivo markdown dentro dela (cresce na horizontal; pode ser faceta *ou* instância). Profundidade travada em dois níveis. `index.md` como sumário e porta de entrada de leitura. Grafo por links `[[pagina]]` no estilo Obsidian. | Discussão 2026-08-19, explicação do usuário sobre a wiki |
| **ESC-18** | **Um único adaptador de LLM** (`claude-agent-sdk`, autenticação por assinatura), atrás de uma porta de sessão modelada para *esse* ciclo de vida. O ciclo já foi medido empiricamente pelo spike: `async with ClaudeSDKClient(...)` → `query()` → `receive_response()` → saída do contexto. | Discussão 2026-08-19, ponto 2 |
| **ESC-19** | **Esquema de wiki plugável, como semente**: na criação do ambiente, um esquema (lista de entidades e propriedades iniciais) gera as pastas e o `index.md`; depois a wiki evolui livre. É o mecanismo que torna RF-F08 verdadeiro sem hardcodar a wiki de nenhum domínio. | Discussão 2026-08-19, resposta "Semente" |
| **ESC-20** | Acesso à wiki **exclusivamente** pelas ferramentas do agente bibliotecário — ponto único de estrangulamento para regra de negócio, validação e segurança. | Discussão 2026-08-19, explicação do usuário |

### 9.3 Novos itens fora do escopo

| # | Item | Motivo |
|---|---|---|
| **FOR-09** | Autenticação por API key, **inclusive no desenho** | Substitui FOR-07. Evita abstração especulativa. |
| **FOR-10** | Interface **web** | Fica para iteração futura. O usuário-alvo opera Claude Code no terminal por preferência; o mockup dele é, na estrutura, uma TUI desenhada em HTML (layout de 3 regiões fixas, barra de status, paleta por `/`, sem responsividade). TUI valida melhor e mais barato. |
| **FOR-11** | `cli.py` como **entregável** | Continua existindo como ambiente de experimentação do dono. Não carrega critério de aceite, não entra nos quality gates, e não tem direito de veto sobre o desenho do núcleo. |
| **FOR-12** | Operações de wiki `ingest` (pasta `raw/`) e `lint` | Fluxos separados. A linha fina precisa de ler/buscar e escrever com revisão. Links são validados **no momento da escrita**, o que evita a maior parte do apodrecimento sem existir processo de lint. |
| **FOR-13** | Wiki **compartilhada** entre usuários e sincronização em tempo real | Derivado de FOR-01 (multiusuário fora). Ver RNF-11 para o que é protegido de graça agora. |
| **FOR-14** | Histórias **US-07, US-10, US-11, US-12, US-18** | Adiadas por aplicação do critério de linha fina. Ver §9.6. |

### 9.4 Novos requisitos funcionais

| ID | Requisito | Critério de pronto | Rastreio |
|---|---|---|---|
| **RF-F13** | A wiki de um ambiente é um diretório de arquivos markdown com entidades (pastas), propriedades (arquivos) e um `index.md` | Inspeção do disco mostra a estrutura; um agente com ferramentas de arquivo consegue navegar sem ferramenta de busca customizada | ESC-17 |
| **RF-F14** | Toda escrita na wiki passa por ferramenta do bibliotecário que **resolve e confina** o caminho na raiz da wiki do ambiente | Nenhum caminho gerado — inclusive contendo `..`, caminho absoluto ou symlink — escreve fora da raiz; a tentativa é recusada | ESC-20, RF-F10, SECURITY-05/13 |
| **RF-F15** | Ambiente novo nasce com a wiki materializada a partir de um esquema plugável | Dois ambientes criados com esquemas diferentes produzem estruturas de wiki diferentes, sem alteração de código | ESC-19, RF-F08, RNF-09 |
| **RF-F16** | O estado do domínio usa identificadores opacos e estáveis | Renomear um chat, uma tarefa ou uma frente não invalida nenhuma referência a ela | ESC-14 |
| **RF-F17** | A interface TUI carrega o ambiente na abertura e persiste as mudanças, sem conter regra de negócio | A regra que a TUI aciona é a mesma que um comando aciona; trocar a camada de tela não muda comportamento | ESC-16, RF-F05 |

### 9.5 Novos requisitos não funcionais

| ID | Requisito | Origem |
|---|---|---|
| **RNF-10** | Confinamento de caminho na escrita da wiki é gate de segurança **e** de teste, incluindo teste de propriedade (nenhum caminho gerado escapa da raiz) | SECURITY-05, SECURITY-13, PBT-03 |
| **RNF-11** | A wiki é endereçada por **caminho lógico relativo** à raiz da wiki do ambiente, nunca por caminho absoluto do disco. Nenhum caminho absoluto é persistido em arquivo ou banco | Preserva FOR-13 (wiki compartilhada) sem custo hoje |
| **RNF-12** | O banco **não guarda conteúdo nem índice da wiki**. No máximo, a referência da raiz. Elimina por construção o risco de divergência entre dois stores | ESC-13, ESC-17, RNF-05 |
| **RNF-13** | Nenhuma parte do desenho pode assumir que existe **um único escritor** na wiki. Concorrência não é implementada; apenas não é tornada impossível | Preserva FOR-13 |
| **RNF-14** | A wiki é tratada como **entrada não confiável** para o agente, mesmo sendo dado do próprio usuário: conteúdo vindo de fora pode conter instrução dirigida ao modelo (prompt injection). Defesas: confinamento fixo no código e revisão humana antes da escrita | SECURITY-05, US-14 |

### 9.6 Escopo de histórias — linha fina

Critério adotado, definido pelo usuário: *o software já entrega uso e já pode ser posto na mão do
usuário de validação*. Hipótese que a iteração precisa validar, escolhida pelo usuário: **o loop
ambiente → conversa → wiki torna o ambiente mais inteligente com o tempo**.

| Situação | Histórias | Total |
|---|---|---|
| **Dentro da linha fina** | US-01, US-02, US-03, US-04, US-05, US-06, US-08, US-09, US-13, US-14, US-15, US-16, US-17, US-19 | 14 |
| **Adiadas (estavam dentro na v1)** | US-07, US-10, US-11, US-12, US-18 | 5 |
| **Já fora desde a v1** | US-20, US-21, US-22, US-23 | 4 |

Justificativa de cada adiamento:

- **US-07** (retomada nativa de memória do agente) — já era *best-effort*. A continuidade
  percebida é entregue por US-06 (transcrição sobrevive e fica visível). Otimização, não linha.
- **US-10** (criar categoria da wiki conversando) — é o esquema **mutando em runtime**, coisa
  diferente do esquema-semente de ESC-19.
- **US-11, US-12** (rod-maker constrói agentes) — cortadas pela escolha de hipótese. Se o que se
  valida é o loop da wiki, customização de agentes não é necessária para a validação.
- **US-18** (reaproveitar e refinar tarefa) — por definição só tem valor depois de existir
  histórico de tarefas concluídas; valor na segunda semana de uso, não no primeiro dia.

**US-09 foi mantida na linha fina em revisão da recomendação inicial**: com esquema-como-semente
(ESC-19), ela custa quase nada e é exatamente o que evita hardcodar a wiki do João.

### 9.7 Novas decisões de arquitetura

| Decisão | Descrição |
|---|---|
| **D-ARQ-04** | Persistência em SQLite atrás de porta de domínio, híbrida (documento para estrutura, normalizada para transcrição). A porta é modelada por vocabulário de domínio; se a assinatura mencionar algo que só existe em SQL, a abstração é decorativa. |
| **D-ARQ-05** | Identidade opaca e estável no domínio, substituindo endereçamento posicional. |
| **D-ARQ-06** | Uma porta de sessão, um adaptador. Substitui D-ARQ-01. |
| **D-ARQ-07** | TUI é a única interface entregável; `cli.py` é experimentação sem garantias. |
| **D-ARQ-08** | Wiki no filesystem, arquivo como fonte da verdade, banco alheio à wiki. |
| **D-ARQ-09** | Software roda na máquina de cada usuário, cada um com a própria assinatura. Nenhuma credencial serve mais de uma pessoa. |

### 9.8 Decisões adicionais adiadas para Application Design

Somam-se às três já registradas na §6:

- **Critério de decisão do bibliotecário entre entidade e propriedade.** Consequência direta da
  escolha "propriedade pode ser instância": sem uma regra, o bibliotecário decide diferente a
  cada vez e a wiki apodrece em semanas. É o risco número um do desenho da wiki.
- **Qual grafo manda na recuperação**: a hierarquia de pastas ou os links `[[...]]`, quando
  discordarem. Determina como o `index.md` é construído e mantido.
- **Formato do arquivo de esquema de wiki**, frontmatter (se houver), sintaxe e resolução dos
  links, geração e manutenção do `index.md`, política de conflito quando duas escritas tocam a
  mesma página.
- **Estratégia interna do SQLite** (o que exatamente é documento e o que é tabela) e desenho da
  identidade (UUID vs ULID, onde é gerada, como atravessa a serialização).
- **Assinaturas das ferramentas do bibliotecário** e escopo de permissão das ferramentas de
  arquivo nativas do agente. O spike mediu permissão de ferramenta MCP; **escopo de ferramenta
  de arquivo não foi medido** e precisa ser verificado, não assumido.

### 9.9 Rastreabilidade da emenda

| Seção | Origem |
|---|---|
| 9.1 Revogações | Discussão 2026-08-19, ponto 2 do usuário |
| 9.2 ESC-13/14 | Ponto 1 (SQLite) + observação do usuário sobre IDs |
| 9.2 ESC-15 | Ponto 3 (uv) |
| 9.2 ESC-16, 9.3 FOR-10/11 | Ponto 4 (interface) + observação de que o usuário-alvo prefere terminal |
| 9.2 ESC-17/19/20, 9.4 RF-F13-15, 9.5 RNF-10-14 | Explicação do usuário sobre a wiki (2026-08-19) |
| 9.6 Linha fina | Ponto 5 (linha fina) + escolha da hipótese a validar |
| 9.7 D-ARQ-04 a 09 | Consolidação das seis decisões fechadas na discussão |
