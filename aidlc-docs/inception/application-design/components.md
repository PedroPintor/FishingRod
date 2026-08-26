# Application Design — Componentes

**Estágio:** INCEPTION — Application Design · **Profundidade:** comprehensive
**Data:** 2026-08-25 · **Base:** `application-design-plan.md` (rodadas 1 e 2, todas as perguntas
respondidas), `requirements.md` v2, `stories.md` (linha fina, 14 histórias)

> Este documento responde **o que existe** — propósito, responsabilidades e interface de alto
> nível de cada componente. Assinaturas completas de método estão em `component-methods.md`.
> Regra de negócio detalhada fica para Functional Design, por unidade.

---

## 1. Visão geral por camada

Pacotes conforme Pergunta 2 (A): `dominio/`, `aplicacao/`, `adaptadores/`, `interface/`. A regra
"quem pode importar quem" está em `component-dependency.md`.

```
interface/        (Textual TUI)
     │ usa
aplicacao/         (serviços, portas, catálogo de ações, comandos, DTOs)
     │ usa (interfaces/portas)          │ implementadas por
dominio/           (entidades, agregados)   adaptadores/  (SQLite, Claude SDK, wiki-fs, MCP)
```

O `__main__` (composition root, Pergunta 11) importa todas as camadas e monta a árvore de
dependências. Nenhuma outra parte do sistema sabe qual adaptador concreto está em uso.

---

## 2. Domínio (`dominio/`)

Não importa `claude_agent_sdk`, `sqlite3` nem Textual (RF-F04, verificável por inspeção — ver
`component-dependency.md`). Contém estado e invariantes; não roteia comando, não delega para
sessão viva, não persiste a si mesmo (Pergunta 1B).

### 2.1 `Identidade`

**Propósito.** Tipo de valor opaco e estável (RF-F16, ESC-14) que substitui índice posicional e
nome como referência.

**Responsabilidades.**
- Nascer no construtor de toda entidade de domínio (Pergunta 4B) — nunca no adaptador de
  persistência.
- Ser UUIDv7: ordenável por tempo, o que dá ordenação de transcrição e paginação sem coluna extra.
- Ser imutável e comparável por valor.

**Rastreio.** RF-F16, ESC-14, D-ARQ-05. Sustenta US-05, US-06, US-15, US-16, US-19 (qualquer
história que referencie frente/tarefa/chat por identidade, não por posição ou nome).

### 2.2 `Ambiente` (agregado raiz)

**Propósito.** Representa o espaço de trabalho de um usuário — frentes, e uma referência lógica à
raiz da própria wiki. É o agregado que o repositório carrega, valida e salva como documento
(Pergunta 3B).

**Responsabilidades.**
- Guardar identidade, nome, coleção de `Frente` e o localizador de wiki (`RaizWiki`, ver 2.6).
- ~~**[emenda]** Guardar `aprovacao_de_agente_obrigatoria: bool = True` — o parâmetro que decide se
  uma ferramenta acionada por agente executa direto ou pede confirmação do usuário.~~
  **REVOGADO em 2026-08-25 (rodada 4) — ver emenda 2 abaixo. `Ambiente` não ganha campo algum.**
- Garantir a invariante "toda frente pertence a este ambiente".
- **[emenda U1, 2026-08-26 — Q1=A]** `Ambiente` recém-criado tem **zero frentes**. A criação
  automática de uma frente padrão (`projeto-padrao` no código atual) **não** é preservada: ela
  existia porque `projetos[indice_ativo]` estourava `IndexError`, razão que morreu quando ESC-14
  trocou índice por identidade opaca. Quem garante que o usuário tem onde trabalhar é a tela de
  início (U9).
- **Não** guarda transcrição de mensagens (isso é tabela separada — ver `RepositorioTranscricao`
  em `component-methods.md`) e **não** guarda nada sobre o conteúdo da wiki (RNF-12, Pergunta 12D).
- Não conhece sintaxe `/`, não sabe formatar mensagem de sistema (Pergunta 7B).

**Rastreio.** RF-F05, RF-F07, RF-F11, ESC-05, ESC-07, D-ARQ-04. Sustenta US-05, US-08, US-15.

> ~~**/!\ Emenda 2026-08-25 - Units Generation.** O campo `aprovacao_de_agente_obrigatoria` entra por **CQ3=A**, com padrão **ligado**. Vale para as duas famílias de ferramenta (ambiente e wiki), viaja no documento que o repositório já serializa, e **não tem história de origem** entre as 14 da linha fina — é decisão de produto, declarada como tal em `unit-of-work-story-map.md` §4. Dono: unidade **U1**; compatibilidade com documento antigo sem o campo: **U2**.~~

> **/!\ Emenda 2 — 2026-08-25 (rodada 4), revoga a emenda acima.** O usuário retirou o parâmetro configurável desta iteração: *"essa decisao ficou muito jogada para essa iteracao, vamos descartar isso para essa iteracao"*. **CQ3=A fica revogada**: `Ambiente` **não** ganha campo, nada novo é persistido e a unidade **U2** perde a obrigação de compatibilidade regressiva. No lugar entra uma **constante de política** — `APROVACAO_DE_AGENTE_OBRIGATORIA = True` em `dominio/politica.py` (unidade **U1**), consultada por **U5** e **U8** através de uma função única `exige_aprovacao(...)`. Comportamento desta iteração: **toda ferramenta acionada por agente pede confirmação, sempre.** Quando a configuração voltar, só o corpo dessa função muda — nenhum chamador, nenhuma tela e nenhum contrato de porta é tocado.

### 2.3 `Frente`

**Propósito.** Área de atuação dentro de um ambiente (vocabulário do usuário: "frente"; código
atual: `Projeto`). Contém tarefas.

**Responsabilidades.**
- Guardar identidade, nome, coleção de `Tarefa`.
- Garantir a invariante "toda tarefa pertence a esta frente".
- Expor `criar_tarefa(nome) -> Tarefa` como operação de domínio (a ação de aplicação é uma casca
  fina sobre isso — Pergunta 7).

**Rastreio.** RF-F11. Sustenta US-15, US-16.

### 2.4 `Tarefa`

**Propósito.** Unidade de trabalho dentro de uma frente (vocabulário do usuário: "card"; código
atual: `Sessao`). Contém chats, etapas e memória própria.

**Responsabilidades.**
- Guardar identidade, nome, coleção de `Chat`, coleção de `Etapa`, `Memoria` própria (a memória já
  pende de `Sessao` hoje — verdade estrutural preservada).
- Garantir no máximo um `Chat` cujo agente tem `papel = ORQUESTRADOR` (invariante já existente em
  `Sessao.__post_init__`, preservada).
- **Não** decide se uma etapa é executada por agente ou por confirmação do usuário — isso é
  conteúdo de `Etapa`, decidido em Functional Design.

**Rastreio.** RF-F11, RF-F12, RF-F17. Sustenta US-16, US-17, US-19.

### 2.5 `Chat`

**Propósito.** Uma aba de conversa dentro de uma tarefa, associada a um `Agente` (configuração) e,
quando aberta, a uma `SessaoViva` (ver 3.4, que é objeto de aplicação, não de domínio).

**Responsabilidades.**
- Guardar identidade, nome (editável, não é identidade — `/nome-chat` continua existindo),
  referência ao `Agente` configurado.
- **Não guarda a lista de mensagens dentro de si** (mudança em relação ao código atual): a
  transcrição é composição feita pelo serviço de aplicação a partir da tabela de mensagens
  (Pergunta 3B). `Chat` guarda apenas o que é pequeno e estável.
- **Não guarda a sessão viva do SDK.** Isso resolve o risco da instância compartilhada
  (`AgenteDoSistema`, Pergunta 6A): a sessão viva é objeto de aplicação, dono é o chat/serviço, não
  o domínio.

**Rastreio.** RF-F01, RF-F17, ESC-01. Sustenta US-01, US-06, US-19.

### 2.6 `Etapa`

**Propósito.** Passo de execução de uma tarefa, descoberto conversando com o orquestrador
(US-17) ou definido de antemão pelo dono do domínio.

**Responsabilidades.**
- Guardar identidade, descrição, executor (agente ou usuário) e estado de conclusão.
- Expor `concluir()` como operação de domínio.

**Rastreio.** RF-F12. Sustenta US-17, US-19.

### 2.7 `Memoria`

**Propósito.** Blackboard por tarefa (RF-F06 corrige TD-03: `anotar()` não pode lançar `KeyError`
na primeira escrita de uma chave nova).

**Responsabilidades.**
- Guardar anotações por chave, cada uma com autor e valor; múltiplas anotações por chave não se
  substituem (US-04, segundo critério de aceite).
- `anotar(chave, valor, autor)` funciona mesmo quando a chave é inédita (fix de TD-03: usar
  `setdefault` ou `defaultdict`).

**Rastreio.** RF-F06, ESC-06, TD-03. Sustenta US-04.

### 2.8 `RaizWiki`

**Propósito.** Localizador lógico da wiki de um ambiente, guardado dentro de `Ambiente` (Pergunta
12D). É a única coisa que o domínio sabe sobre a wiki.

**Responsabilidades.**
- Guardar uma string com **esquema explícito** (Pergunta D): `dados:wikis/<id_ambiente>` nesta
  iteração. O domínio não resolve o esquema em caminho real — isso é trabalho do adaptador de
  wiki, montado no composition root.
- Nunca conter caminho absoluto (RNF-11).

**Rastreio.** RNF-11, RNF-12, ESC-17. Sustenta US-08, US-09.

### 2.9 `Agente` (configuração)

**Propósito.** Configuração imutável de um agente — nome, papel, modelo, ferramentas, regras
(Pergunta 6A). Substitui o atual `Agente` abstrato com `responder()`.

**Responsabilidades.**
- Guardar `nome`, `papel` (`ORQUESTRADOR` | `SUB_AGENTE`), `modelo`, lista de ferramentas
  permitidas (**[emenda]**: são **nomes** de ferramenta, não funções), lista de regras/prompt.
- **Não tem método `responder()`.** Não guarda estado de sessão. Pode continuar compartilhada
  entre chats sem risco, porque não há mais estado mutável nela.

**Rastreio.** ESC-01, ESC-08, TD-01 (parte "quem não é mais responsável por responder").
Sustenta US-01, US-13, US-19.

**Instâncias conhecidas nesta iteração**: orquestrador (`papel = ORQUESTRADOR`) e bibliotecário
(`papel = SUB_AGENTE`) — ver Pergunta 3-bis. O rod-maker permanece como `papel = SUB_AGENTE`
suportado no tipo, mas **sem instância nem implementação** nesta iteração (US-11/US-12 adiadas,
FOR-14).

> **/!\ Emenda 2026-08-25 - Units Generation.** Por **Q12=A** e **R4**, `Agente` guarda apenas os **nomes** das ferramentas permitidas. O registro nome->função é montado pelo composition root (`U9`) e resolvido pelo `AdaptadorSessaoClaude` (`U6`) ao abrir a sessão. Sem isso, `ServicoConversa` teria de importar `CatalogoDeAcoes` e a matriz de dependência ganharia uma seta entre duas unidades que Q2=A quer independentes.
>
> **Vocabulário oficial (R9)**: as ferramentas se dividem em **ferramentas de ambiente** (tocam `Ambiente`/`Frente`/`Tarefa`/`Etapa`/`Chat`; são do orquestrador) e **ferramentas de wiki** (tocam páginas e índice; são do bibliotecário). Invariante testável sem LLM (**R10**): nenhum `Agente` com `papel = SUB_AGENTE` carrega nome da família ambiente.

---

## 3. Aplicação (`aplicacao/`)

Orquestra domínio e portas. Depende de `dominio/` e das **portas** (interfaces), nunca dos
adaptadores concretos.

### 3.1 `CatalogoDeAcoes`

**Propósito.** Registro declarativo das ações do ambiente (Pergunta 7B). Cada ação é dado, não
`match/case` — permite que a paleta `/`, botões e atalhos leiam o mesmo registro.

**Responsabilidades.**
- Listar ações disponíveis, cada uma com nome, descrição, parâmetros tipados e escopo
  (`AMBIENTE | FRENTE | TAREFA`).
- Cada ação é `async` (Pergunta E1) e devolve `Resultado` tipado, nunca string.
- **Conversar não está aqui** (Pergunta E2) — conversa é caminho separado, ver `ServicoConversa`.
- **[emenda]** Inclui `criar_chat(agente)` — ver a nota de emenda abaixo.

**Rastreio.** RF-F17, ESC-09. Sustenta todas as histórias que hoje usam comando `/`: US-15, US-16
(criar frente/tarefa), navegação de US-17/US-19.

> **/!\ Emenda 2026-08-25 - Units Generation.** Este catálogo passa a ser exposto ao **orquestrador** como as **ferramentas de ambiente** (R9), via MCP in-process (**Q11=A**). Três consequências registradas: (1) entra a ação `criar_chat(agente)`, que é como o orquestrador delega ao bibliotecário sem receber ferramentas de wiki (**Q14=X**) — não é componente novo, `ServicoDeAmbiente` §3.3 e `Chat` §2.5 já a previam (R2); (2) `criar_chat` só aceita agente de **lista fechada**, nesta iteração o bibliotecário, senão seria escalonamento de privilégio (R3); (3) toda ação acionada por agente consulta ~~`ambiente.aprovacao_de_agente_obrigatoria`~~ **[rodada 4]** `exige_aprovacao(...)` de `dominio/politica.py` antes de executar — hoje constante `True`, sem configuração. Unidade dona: **U5**.

### 3.2 `ParserDeComando`

**Propósito.** Adaptador de entrada fino que traduz `"/nova-tarefa campanha de verao"` em
`("nova-tarefa", {"nome": "campanha de verao"})` (Pergunta 7).

**Responsabilidades.**
- Detectar se uma string de entrada é comando (`startswith("/")`).
- Fazer parsing tolerante a espaços em argumentos (corrige TD-11).
- Resolver o alvo default (o item "ativo" na tela) quando o comando não especifica identidade
  explícita.
- **Não conhece regra de negócio.** Traduz sintaxe; não decide nada.

**Rastreio.** RF-F17, TD-11. Sustenta a mesma lista de US-15/US-16/US-17/US-19 via `/`.

### 3.3 `ServicoDeAmbiente`

**Propósito.** Serviço de aplicação central: recebe uma ação (via catálogo) ou uma mensagem de
conversa, coordena domínio + portas, e devolve resultado tipado (Pergunta 1B).

**Responsabilidades.**
- Criar ambiente, materializar a wiki a partir de um `EsquemaWiki` (ver 3.7) na criação
  (invariante: ao menos uma entidade — Pergunta 16).
- Criar frente, criar tarefa, criar chat, concluir etapa, anotar memória — cada uma delegando a
  invariante ao objeto de domínio correspondente e persistindo via `PortaPersistencia`.
- Gravar ao fim de cada operação que muda estado, uma transação por operação (Pergunta A/8B).
- **Não conhece SQLite nem Claude SDK** — só as portas.

**Rastreio.** RF-F05, RF-F07, RF-F11, RF-F15, ESC-05, ESC-13, ESC-19. Sustenta US-05, US-08, US-09,
US-15, US-16.

### 3.4 `ServicoConversa`

**Propósito.** Orquestra o ciclo de uma mensagem de conversa em um chat: abre/reusa a
`SessaoViva`, envia a mensagem, consome o stream de eventos, persiste incrementalmente (Pergunta
A/8B), devolve o stream para a interface consumir.

**Responsabilidades.**
- Manter o mapeamento `chat.id → SessaoViva` (aqui, não em `Agente` — Pergunta 6A).
- Ao enviar mensagem: inserir a mensagem do agente no banco **no início** do turno com marca "em
  andamento", atualizar conforme o streaming avança (`PortaSessao.enviar`), remover a marca no
  fim (Pergunta A).
- Persistir **texto + registro resumido de uso de ferramenta** (tool, parâmetros resumidos,
  resultado resumido) — não o stream inteiro de tokens parciais (Pergunta F/B).
- Isolar falha do provedor: uma falha de `PortaSessao` não propaga além do chat onde ocorreu
  (US-03, RNF-06).
- **Conversar não é uma ação do `CatalogoDeAcoes`** (Pergunta E2): tem assinatura própria porque
  devolve um iterador assíncrono de eventos, não um `Resultado`.

**Rastreio.** RF-F01, RF-F03, RF-F05 (transcrição), RNF-06, ESC-01, ESC-05, ESC-18. Sustenta US-01,
US-02, US-03, US-06, US-19.

### 3.5 `ServicoBibliotecario`

**Propósito.** Coordena o ciclo "o agente bibliotecário propõe → o usuário aprova/rejeita → a
escrita se efetiva" (US-13, US-14).

**Responsabilidades.**
- Abrir uma `SessaoViva` própria para o bibliotecário (sub-agente — Pergunta 3-bis), isolada da
  sessão do orquestrador.
- Receber propostas produzidas pelas `FerramentasWiki` (`propor_entidade`,
  `propor_propriedade`) através da conversa do bibliotecário.
- Guardar propostas pendentes; permitir que **uma proposta contenha várias páginas**, para que
  aprovar seja um ato por promoção, não por arquivo (reconciliação registrada no plano, §5).
- Ao aprovar: escrever no adaptador de wiki, validar links (Pergunta 14B — recusar ou converter em
  proposta de página nova), e acionar `renderizar_index()` (Pergunta 15D).
- Ao rejeitar: descartar a proposta sem tocar o filesystem.
- **Nunca escreve sem aprovação prévia** (Pergunta 9A) — nem sequer numa área de rascunho dentro da
  raiz.

**Rastreio.** RF-F10, RNF-14, ESC-08, ESC-20. Sustenta US-13, US-14.

### 3.6 `ComposicaoRoot` (`__main__` / entrypoint)

**Propósito.** Ponto único que constrói adaptadores concretos e injeta nos serviços (Pergunta
11A). Não é uma camada — é o lado de fora, onde a regra "não atravesse camadas" não se aplica.

**Responsabilidades.**
- Ler configuração de implantação (raiz de dados privada, raiz de wikis — Pergunta D) de arquivo
  de config ou variável de ambiente, nunca do banco.
- Montar `RepositorioSQLite`, `AdaptadorSessaoClaude`, `AdaptadorWikiFilesystem`,
  `FerramentasWiki`/adaptador MCP, e os serviços de aplicação, nessa ordem.
- Entregar a raiz da árvore (`ServicoDeAmbiente`, `ServicoConversa`, `ServicoBibliotecario`,
  `CatalogoDeAcoes`) para a TUI.

**Rastreio.** D-ARQ-04, D-ARQ-06, D-ARQ-08. Não é rastreado a história de usuário — é infra de
todas elas.

### 3.7 `EsquemaWiki`

**Propósito.** Representação em memória do esquema semente (lista de entidades e propriedades
iniciais) que materializa a wiki de um ambiente novo (ESC-19, Pergunta 16B).

**Responsabilidades.**
- Carregar-se a partir de um arquivo `.toml` (maquete embutida ou, nesta iteração, apenas leitura —
  Pergunta C/16B) ou a partir dos dados de um formulário preenchido pelo usuário (US-09).
- Validar a invariante de criação: ao menos uma entidade; propriedade não é exigida.
- **Não sabe escrever `.toml`** nesta iteração — "salvar como maquete" está fora de escopo
  (Pergunta C).

**Rastreio.** RF-F08, RF-F15, ESC-19, RNF-09. Sustenta US-08, US-09.

---

## 4. Portas (interfaces em `aplicacao/portas/`, implementadas em `adaptadores/`)

### 4.1 `PortaPersistencia`

**Propósito.** Fronteira de domínio para salvar/carregar `Ambiente` (documento) e para a tabela de
transcrição (Pergunta 3B, D-ARQ-04). Vocabulário de domínio, não SQL.

**Responsabilidades (assinatura conceitual).** `salvar_ambiente`, `carregar_ambiente`,
`inserir_mensagem`, `atualizar_mensagem`, `listar_mensagens(chat_id, limite)`. Assíncrona
(Pergunta E1); o `asyncio.to_thread` para `sqlite3` mora dentro do adaptador, não na porta.

**Rastreio.** D-ARQ-04, RNF-05. Sustenta US-05, US-06.

### 4.2 `PortaSessao`

**Propósito.** Fronteira sobre o ciclo assíncrono do SDK medido pelo spike (Pergunta 5B).

**Responsabilidades (assinatura conceitual).** `abrir(agente) -> SessaoViva` async;
`enviar(sessao, mensagem) -> AsyncIterator[EventoConversa]` async; `fechar(sessao)` async. Eventos:
pedaço de texto, uso de ferramenta, fim de turno.

**Rastreio.** ESC-18, D-ARQ-06, RF-F01, RF-F03. Sustenta US-01, US-02, US-03.

### 4.3 `PortaWiki`

**Propósito.** Fronteira sobre o substrato 2 (filesystem hoje, serviço/drive no futuro — Pergunta
12). O domínio e a aplicação nunca sabem se é pasta local ou serviço remoto.

**Responsabilidades (assinatura conceitual).** `listar`, `ler`, ~~`buscar`~~ **[emenda: `buscar` sai
por Q13=A]**, `escrever_proposta`
(efetiva uma proposta já aprovada), `renderizar_index`. Resolve o esquema do localizador
(`dados:...` — Pergunta D) internamente.

**Rastreio.** RNF-11, RNF-12, ESC-17, ESC-20. Sustenta US-08, US-09, US-13, US-14.

---

## 5. Adaptadores (`adaptadores/`)

### 5.1 `RepositorioSQLite`

**Propósito.** Implementação de `PortaPersistencia` sobre `sqlite3` (stdlib).

**Responsabilidades.**
- Serializar/desserializar `Ambiente` como documento (JSON) numa tabela; ler/escrever a tabela de
  mensagens normalizada, append-only, indexada por `(chat_id, id)` (Pergunta 3B).
- Envolver chamadas bloqueantes em `asyncio.to_thread` nos pontos que valem a pena (abertura do
  ambiente) — Pergunta E1, nota sobre `sqlite3`.
- É o único lugar do sistema que sabe o que é documento e o que é tabela.

**Rastreio.** ESC-13, D-ARQ-04, RNF-05.

### 5.2 `AdaptadorSessaoClaude`

**Propósito.** Implementação de `PortaSessao` sobre `claude-agent-sdk` (Pergunta 5B, ESC-18).

**Responsabilidades.**
- Encapsular o ciclo medido pelo spike: `async with ClaudeSDKClient(...)` → `query()` →
  `receive_response()`.
- Converter os tipos concretos do SDK (`AssistantMessage`, `TextBlock`, `ToolUseBlock`,
  `ResultMessage`, ...) nos tipos de evento da `PortaSessao` — é o **único** lugar do sistema que
  importa `claude_agent_sdk` (RF-F04, corrige TD-02).
- Suportar duas sessões vivas simultâneas no mesmo processo (medido pelo spike): uma para o
  orquestrador, uma para o bibliotecário.
- Isolar falha do provedor num erro tipado, sem propagar exceção crua (RNF-06, US-03).

**Rastreio.** ESC-01, ESC-04, ESC-18, TD-01, TD-02, RNF-06.

### 5.3 `AdaptadorWikiFilesystem`

**Propósito.** Implementação de `PortaWiki` sobre arquivos markdown no disco (ESC-17, Pergunta
12D).

**Responsabilidades.**
- Resolver o esquema `dados:wikis/<id_ambiente>` (Pergunta D) para um caminho real, a partir da
  raiz de dados recebida do composition root.
- Confinar toda escrita à raiz da wiki do ambiente — nenhum caminho gerado (inclusive contendo
  `..`, caminho absoluto ou symlink) escreve fora dela (RF-F14, RNF-10). Este confinamento é o
  ponto de PBT-03 (property-based testing).
- Renderizar `index.md` por código, a partir de estrutura de pastas + frontmatter (Pergunta 15D) —
  nunca aceita edição de agente. **[emenda]** O índice é **projeção do disco**: página criada fora
  do app aparece na próxima renderização; nenhuma propriedade pode ter `descricao` vazia.
- Validar links `[[...]]` na escrita (Pergunta 14B): recusar ou converter em proposta de criação
  da página de destino.

**Rastreio.** ESC-17, RF-F13, RF-F14, RNF-10, RNF-11, RNF-12.

> **/!\ Emenda 2026-08-25 - Units Generation.** Critério de aceite do índice fixado por **CQ1=A** como **exclusivamente determinístico** — nenhum portão com LLM no laço, porque um portão não determinístico falha por causa do prompt e não da unidade. A qualidade da descrição fica **fora** do portão. Com `buscar` removida (Q13=A), existe um único caminho até o conteúdo, então descrição ruim torna o conteúdo invisível ao agente: risco **aceito e declarado**, com rede de segurança humana. Unidade dona: **U3**.

### 5.4 `FerramentasWiki` (bibliotecário) + adaptador MCP

**Propósito.** As tools próprias que o agente bibliotecário usa para acessar a wiki (Pergunta 10B)
— a "cerca determinística". Implementadas como funções Python puras, testáveis sem LLM; exposição
ao modelo via MCP in-process é casca fina por cima (medido pelo spike:
`create_sdk_mcp_server`/closure).

**Responsabilidades.**
- `listar`, `ler`, ~~`buscar` (leitura; `buscar` pode usar `ripgrep` confinado à raiz)~~ — **[emenda:
  `buscar` removida desta iteração]** a leitura é `listar` + `ler`, sempre a partir do `index.md`.
- `propor_entidade(nome)`, `propor_propriedade(entidade, propriedade, conteudo, descricao, links)`
  — nunca escrevem; produzem proposta consumida por `ServicoBibliotecario` (Pergunta 13A, 9A).
- Nenhum parâmetro representa um terceiro nível de profundidade — a violação do esquema de dois
  níveis (ESC-17) é estruturalmente irrepresentável, não apenas proibida por prompt.
- Fechar ferramentas nativas de escrita (`tools=[]` na configuração da sessão do bibliotecário,
  medido pelo spike) — RF-F14/RNF-10 não dependem de configuração de permissão nativa não medida.

**Rastreio.** RF-F10, RF-F14, RNF-10, RNF-14, ESC-08, ESC-20. Sustenta US-13, US-14.

> **/!\ Emenda 2026-08-25 - Units Generation.** **Q13=A** remove `buscar`. Ganho colateral registrado: some a dependência do binário externo `ripgrep` e o caminho de execução de processo que precisaria de confinamento próprio (SECURITY-10). Estas são as **ferramentas de wiki** (R9); o orquestrador não as recebe (Q14=X). Unidade dona: **U8**.

### 5.5 `AgenteBibliotecario` / `AgenteOrquestrador` (prompts)

**Propósito.** Não são componentes de código no sentido estrutural — são a configuração de
`Agente` (2.9) mais o prompt que carrega o julgamento (Pergunta 3-bis, 13, 14). Registrados aqui
porque Application Design precisa nomear onde mora o critério semântico entidade-vs-propriedade:
**no prompt do bibliotecário**, nunca em código.

**Rastreio.** Mesmo rastreio de 2.9 e 5.4.

---

## 6. Interface (`interface/`)

### 6.1 `FishingRodTUI` (Textual)

**Propósito.** Única interface entregável desta iteração (D-ARQ-07, ESC-16). Recebe os serviços
prontos do composition root; não constrói nada, não sabe que SQLite ou Claude existem.

**Responsabilidades.**
- Renderizar ambiente, frentes, tarefas, chats a partir do estado carregado por
  `ServicoDeAmbiente`.
- Encaminhar entrada de texto: se começar com `/`, passar por `ParserDeComando` → `CatalogoDeAcoes`;
  senão, tratar como conversa → `ServicoConversa`.
- Renderizar o stream de eventos de conversa incrementalmente (streaming — Pergunta 5B).
- Apresentar propostas pendentes do bibliotecário e capturar aprovação/rejeição do usuário (US-14).
- Isolar erro de um chat/aba sem derrubar as demais (US-03).

**Rastreio.** RF-F17, ESC-16, D-ARQ-07. Sustenta todas as 14 histórias na superfície de interação
(ver `application-design.md` para a matriz completa).

### 6.2 `cli.py` (fora de garantias)

**Propósito.** Ambiente de experimentação pessoal do dono (FOR-11). Não é um componente com
responsabilidade de design — registrado aqui apenas para deixar explícito que ele **não** carrega
critério de aceite, não entra em quality gate, e não tem direito de veto sobre o desenho do
núcleo (D-ARQ-07).

---

## 7. Diagrama de componentes (visão consolidada)

```
                        ┌───────────────────────────┐
                        │   FishingRodTUI (Textual) │
                        └─────────────┬─────────────┘
                                      │ usa
          ┌───────────────────────────┼───────────────────────────┐
          ▼                           ▼                           ▼
 CatalogoDeAcoes/               ServicoDeAmbiente          ServicoConversa
 ParserDeComando                        │                         │
          │                             │                         │
          └───────────────┬─────────────┴─────────────┬───────────┘
                           ▼                           ▼
                   PortaPersistencia              PortaSessao
                           │                           │
                           ▼                           ▼
                  RepositorioSQLite          AdaptadorSessaoClaude
                                                        │
                                              (bibliotecário usa
                                               sessão própria)
                                                        │
                                                        ▼
                                              ServicoBibliotecario
                                                        │
                                                        ▼
                                              FerramentasWiki (MCP)
                                                        │
                                                        ▼
                                                    PortaWiki
                                                        │
                                                        ▼
                                          AdaptadorWikiFilesystem
```

**Alternativa textual** (para acessibilidade / fallback do diagrama acima): a TUI usa o catálogo
de ações (para comandos `/`), o serviço de ambiente (para estrutura) e o serviço de conversa (para
chats). O serviço de ambiente e o de conversa dependem da porta de persistência, implementada pelo
repositório SQLite. O serviço de conversa também depende da porta de sessão, implementada pelo
adaptador Claude. O serviço de bibliotecário usa a mesma porta de sessão (uma segunda sessão viva)
e as ferramentas de wiki, expostas por MCP in-process, que por sua vez dependem da porta de wiki,
implementada pelo adaptador de filesystem. Tudo isso é montado pelo composition root, fora deste
diagrama.

---

## 8. Rastreabilidade — componente → história

| Componente | Histórias |
|---|---|
| `Identidade` | US-05, US-06, US-15, US-16, US-19 |
| `Ambiente`, `ServicoDeAmbiente` | US-05, US-08, US-09, US-15 |
| `Frente` | US-15, US-16 |
| `Tarefa`, `Etapa` | US-16, US-17, US-19 |
| `Chat`, `ServicoConversa`, `PortaSessao`, `AdaptadorSessaoClaude` | US-01, US-02, US-03, US-06, US-19 |
| `Memoria` | US-04 |
| `RaizWiki`, `PortaWiki`, `AdaptadorWikiFilesystem` | US-08, US-09 |
| `EsquemaWiki` | US-08, US-09 |
| `ServicoBibliotecario`, `FerramentasWiki` | US-13, US-14 |
| `Agente` (config), `AgenteOrquestrador`, `AgenteBibliotecario` | US-01, US-13, US-17, US-19 |
| `CatalogoDeAcoes`, `ParserDeComando` | US-15, US-16, US-17, US-19 (via `/`) |
| `PortaPersistencia`, `RepositorioSQLite` | US-05, US-06 |
| `FishingRodTUI` | Todas — superfície única de interação |

Todas as 14 histórias da linha fina (US-01 a US-06, US-08, US-09, US-13 a US-17, US-19) têm pelo
menos um componente responsável. Ver `application-design.md` §-final para a matriz consolidada com
RF/RNF.
