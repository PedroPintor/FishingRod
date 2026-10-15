# Units of Work — Definição das unidades

**Estágio:** INCEPTION — Units Generation, Parte 2 · **Profundidade:** comprehensive
**Data:** 2026-08-25
**Base:** `plans/unit-of-work-plan.md` (Q1–Q14) e `plans/unit-of-work-clarification-questions.md`
(CQ1–CQ4, R1–R10), todas aprovadas em 2026-08-25
**Entradas de desenho:** `components.md`, `component-methods.md`, `services.md`,
`component-dependency.md`, `application-design.md`

---

## 1. Como estas unidades foram formadas

| Decisão | Efeito na decomposição |
|---|---|
| **Q1=A** granularidade fina | Uma unidade por responsabilidade técnica, não uma por camada inteira |
| **Q2=A** decomposição horizontal | O eixo é camada/substrato, não fatia vertical de história |
| **Q3=C** fundação primeiro | `U0` existe, mas **fora do loop de design por unidade** (ver R5) |
| **Q5=B** | `ServicoDeAmbiente` é unidade própria, não parte da unidade de ações |
| **Q6=A** | Wiki e bibliotecário são unidades separadas |
| **Q7=A** | Execução estritamente sequencial; nenhuma unidade em paralelo |
| **Q8=A / Q9=A** | Código novo em `src/fishingrod/`, camada no topo (ver §4) |
| **Q12=A** | A exposição de ferramentas a uma sessão mora na unidade de sessão — **não** existe unidade `ferramentas-de-agente` |

**Total: 10 unidades** (`U0` a `U9`), conforme a reconciliação R1.

> **Consequência declarada de Q2=A, repetida aqui porque é o custo real desta forma:** nenhuma
> história fica demonstrável na tela antes de `U9`. Até lá, "pronto" significa teste automatizado
> passando (Q4=A), não interação sua. Você escolheu isso sabendo; está registrado para não virar
> surpresa em `U5`.

---

## 2. Achado desta geração — a ordem candidata do plano estava errada

O plano da Parte 1 listava `ServicoDeAmbiente` (U5 candidata) **antes** da wiki (U6 candidata). Ao
montar a matriz de dependência, isso não fecha: `ServicoDeAmbiente.criar_ambiente` materializa a
wiki a partir do `EsquemaWiki` e chama `renderizar_index` (`services.md` §2, passos 7 e 8). Logo a
unidade de ambiente **depende** da unidade de wiki, e não o contrário.

**Correção aplicada nesta numeração final**: a wiki passa a ser `U3`, antes da unidade de ambiente
(`U4`). Isso não muda nenhuma decisão sua — muda a ordem de execução, que era exatamente o produto
que faltava calcular. A numeração deste documento é a que vale; a do plano era candidata.

---

## 3. As 10 unidades

Cada unidade declara: componentes, histórias, dívidas técnicas, critério de pronto **determinístico**
(Q4=A e CQ1=A — nenhum portão com LLM no laço), e quais estágios do CONSTRUCTION executam.

Legenda dos estágios: **FD** Functional Design · **NFR-R** NFR Requirements · **NFR-D** NFR Design ·
**INFRA** Infrastructure Design · **CG** Code Generation.
`INFRA` é **SKIP em todas as unidades** por decisão do `execution-plan.md` v2 (não há deploy,
servidor nem nuvem nesta iteração) — não repito o motivo unidade por unidade.

---

### U0 — `fundacao`

**Fora do loop de design por unidade** (Q3=C / R5). É o passo 0 do CONSTRUCTION.

| Campo | Conteúdo |
|---|---|
| **Componentes** | `pyproject.toml`, `uv.lock`, layout `src/fishingrod/`, runner de testes, `hypothesis` como dependência de teste |
| **Histórias** | Nenhuma |
| **Dívidas** | Nenhuma |
| **Depende de** | — |

**Critério de pronto.** `uv sync` funciona em máquina limpa; `uv run pytest` executa e coleta 0
testes sem erro; `uv.lock` versionado; as dependências diretas estão fixadas (SECURITY-10 —
registrado aqui como critério de aceite em vez de virar um estágio de NFR Requirements próprio, que
seria caro demais para o que é).

**Estágios**: FD **SKIP** (não há regra de negócio) · NFR-R **SKIP** (o único requisito aplicável é
SECURITY-10, já absorvido acima como critério de aceite) · NFR-D **SKIP** · CG **EXECUTE**.

---

### U1 — `dominio`

| Campo | Conteúdo |
|---|---|
| **Componentes** | `Identidade`, `Ambiente`, `Frente`, `Tarefa`, `Chat`, `Etapa`, `Memoria`, `RaizWiki`, `Agente` (configuração) |
| **Histórias** | US-04, US-05 (parte de estrutura), US-15 e US-16 (invariantes de criação) |
| **Dívidas** | **TD-03** (`Memoria.anotar()` lança `KeyError`) |
| **Depende de** | U0 |

**Escopo novo desta rodada** ~~`Ambiente` ganha `aprovacao_de_agente_obrigatoria: bool = True`
(CQ3=A).~~ **Revisto em 2026-08-25 (rodada 4): CQ3=A revogada pelo usuário.** `Ambiente` **não**
ganha campo e nada novo é persistido. No lugar entra `dominio/politica.py`, com a constante
`APROVACAO_DE_AGENTE_OBRIGATORIA = True` e a função `exige_aprovacao(...)` que **U5** e **U8**
consultam. **Nem a constante nem a função têm história de origem** entre as 14 da linha fina — é
decisão de produto, declarada como tal no `unit-of-work-story-map.md` §4.

**Critério de pronto.**
1. `Memoria.anotar` em chave nova funciona (mata TD-03), com a propriedade PBT correspondente.
2. Invariantes: toda frente pertence ao ambiente; toda tarefa pertence à frente. ~~`Ambiente` novo
   nasce com o parâmetro de aprovação ligado.~~ **[rodada 4]** No lugar: `exige_aprovacao(...)`
   devolve `True` para toda ação acionada por agente, verificado por teste direto da política — sem
   estado, sem persistência, sem configuração.
3. Nenhum `import` de `claude_agent_sdk`, `sqlite3` ou `textual` em `dominio/` — teste de importação
   com os pacotes ausentes (RF-F04).
4. `Identidade` é UUIDv7, ordenável por tempo, criada no construtor da entidade e nunca no adaptador.

**Estágios**: FD **EXECUTE** (invariantes e o novo campo são regra de negócio) · NFR-R **SKIP**
(camada sem I/O, sem rede, sem concorrência; os RNF aplicáveis são de U2, U3 e U6) · NFR-D **SKIP**
(sem NFR-R, não há padrão a incorporar) · CG **EXECUTE**.

---

### U2 — `persistencia`

| Campo | Conteúdo |
|---|---|
| **Componentes** | `PortaPersistencia`, `RepositorioSQLite` |
| **Histórias** | US-05, US-06 (armazenamento) |
| **Dívidas** | **TD-04** (persistência inexistente) |
| **Depende de** | U0, U1 |

**Critério de pronto.**
1. **CS-01**: fechar e reabrir o processo reconstitui o ambiente idêntico (mata TD-04).
2. Round-trip de serialização do `Ambiente` — propriedade PBT, exigida pela extensão
   `property-based-testing`.
3. ~~**Compatibilidade regressiva do parâmetro de aprovação (CQ3=A)**: um documento `Ambiente`
   serializado **sem** o campo carrega com o padrão ligado e não levanta exceção.~~ **[rodada 4]
   Critério removido** — com a CQ3 revogada, `Ambiente` não ganha campo novo e esta unidade não
   herda obrigação alguma do tema de aprovação. Foi o único custo que a revogação apagou por
   inteiro.
4. Transcrição é tabela append-only indexada por `(chat_id, id)`; `listar_mensagens` pagina.
5. Uma transação por operação que muda estado.

> **[Emenda — Functional Design de U2, 2026-08-26]** Três critérios acrescentados:
> 6. **Memória é tabela, não documento** (Q2=B): duas anotações concorrentes na mesma tarefa
>    sobrevivem ambas, e `anotar` nunca levanta `ConflitoDeVersao`.
> 7. **Bloqueio otimista funciona** (Q4=C): salvar com versão obsoleta levanta `ConflitoDeVersao`
>    e não grava nada.
> 8. **`apagar_ambiente` não deixa órfão** em nenhuma tabela (Q8=B), e **adaptador falso e real
>    passam o mesmo teste de contrato** (Q9=A).

**Estágios**: FD **EXECUTE** (fronteira documento vs tabela, política de gravação) · NFR-R
**EXECUTE** (RNF-05 durabilidade; comportamento sob escrita concorrente de duas sessões vivas) ·
NFR-D **EXECUTE** · CG **EXECUTE**.

---

### U3 — `wiki`

| Campo | Conteúdo |
|---|---|
| **Componentes** | `PortaWiki`, ~~`AdaptadorWikiFilesystem`~~ **`WikiDeArquivos`** [emendado], `EsquemaWiki` |
| **Histórias** | US-08, US-09 |
| **Dívidas** | Nenhuma |
| **Depende de** | U0, U1 (`RaizWiki`) |

> **/!\ Emenda 2026-10-01 - Code Generation de U3 `wiki`.** O adaptador se chama **`WikiDeArquivos`**
> e mora em `src/fishingrod/adaptadores/wiki/` (`R-CG3-1`): o nome foi decidido em Q9=A do NFR Design,
> e `AdaptadorWikiFilesystem` era o nome de Application Design, anterior a essa decisão. O nome
> antigo continua citado em `services.md`, `component-dependency.md`, `component-methods.md` §6.2 e
> `application-design.md`, como registro do desenho daquela fase — a correspondência fica declarada
> aqui e em `components.md` §5.3. `EsquemaWiki` mora em `aplicacao/esquema_wiki.py` (`R-CG3-4`).

**Por que esta unidade fecha sem o bibliotecário existir** (o que sustenta Q6=A como separação real
e não arrumação — reconciliação R6): quem materializa a wiki na criação do ambiente é
`ServicoDeAmbiente`, não o bibliotecário, e `renderizar_index` é **projeção do disco**, então uma
página criada fora do app aparece no índice na próxima renderização.

**Critério de pronto (CQ1=A — só determinístico).**
1. ~~Toda entidade e toda propriedade presente no disco aparece no `index.md` regenerado.~~
   **[emendado]** Toda entidade e toda propriedade **escrita pelo app** aparece no `index.md`
   regenerado. Página sem frontmatter legível com `descricao` não vazia é ignorada, e o arquivo
   não é tocado (`RN-W-20`).
2. Nenhuma propriedade com `descricao` vazia no frontmatter.
3. ~~Uma página criada fora do app aparece no índice após regeneração.~~ **[REVOGADO]**

> **/!\ Emenda 2026-09-23 - Functional Design de U3 `wiki`.** Critério 3 **revogado** e critério 1 **emendado**, por decisão do
> usuário na Q2: *"normalmente não pode editar ou criar os arquivos da wiki manualmente fora do app.
> Se o usuário fizer isso, eu penso que devemos apenas ignorar (…) a wiki em algum momento vai ser
> um tipo de armazenamento que o usuário não vai mais conseguir mexer fora do app."* Os critérios 1
> e 3 se contradiziam para uma página criada à mão sem frontmatter, e a decisão resolve a
> contradição a favor do critério 2. Consequência declarada: o `index.md` continua sendo projeção
> pura (`RN-W-17`), e o que mudou é o que conta como conteúdo.
4. O `index.md` nunca é escrito por agente — é sempre projeção.
5. **PBT-03**: nenhum caminho gerado escapa da raiz da wiki, inclusive com `..`, caminho absoluto ou
   symlink (RNF-10, SECURITY-05).
6. Esquema de dois níveis (ESC-17) é estruturalmente irrepresentável: não existe parâmetro que
   permita um terceiro nível.

> **A qualidade da descrição fica fora do portão** (CQ1=A). Com `buscar` removida (Q13=A), existe um
> caminho só até o conteúdo, então descrição ruim torna o conteúdo invisível ao agente — e a rede de
> segurança é humana, não técnica. Registrado como risco aceito, não como defeito a testar.

**Estágios**: FD **EXECUTE** · NFR-R **EXECUTE** (RNF-10 confinamento, RNF-11/RNF-12 substrato
trocável, RNF-14 entrada não confiável na leitura) · NFR-D **EXECUTE** · CG **EXECUTE**.

---

### U4 — `ambiente`

| Campo | Conteúdo |
|---|---|
| **Componentes** | `ServicoDeAmbiente` |
| **Histórias** | US-05, US-08, US-09, US-15, US-16 (orquestração) |
| **Dívidas** | Nenhuma |
| **Depende de** | U1, U2, **U3** (ver §2) |

**Critério de pronto.**
1. Criar ambiente materializa a wiki a partir do `EsquemaWiki` e chama `renderizar_index`, numa
   operação só; ~~invariante de criação: ao menos uma entidade.~~

   > **/!\ Emenda 2026-09-23 - Functional Design de U3 `wiki`.** Invariante **revogada**, como a Parte B.3 do FD de U1 havia
   > prometido aplicar quando U3 chegasse. A wiki nasce mesmo sem entidade alguma; quem cria a raiz
   > nesse caso é `renderizar_index` (`RN-W-25`), e o índice vazio é legível (`RN-W-19`).
   > **Detalhe de como**: não existe operação de materialização na porta — o `EsquemaWiki` é
   > convertido em `PropostaWiki` e passa por `escrever_proposta`, e `renderizar_index` agora recebe
   > o nome do ambiente. Ver `construction/wiki/functional-design/business-logic-model.md` §6.
2. Criar frente / criar tarefa / criar chat / concluir etapa / anotar memória delegam a invariante ao
   objeto de domínio e persistem via porta.
3. Nenhum `import` de `sqlite3` nem de `claude_agent_sdk`.
4. Vários ambientes locais coexistem na mesma instalação (Q10=B): `carregar_ambiente(id)` devolve o
   ambiente certo, e cada um tem sua raiz de wiki própria.

> **[Emenda — Functional Design de U2, 2026-08-26]** Dois critérios acrescentados:
> 5. **Tratar `ConflitoDeVersao`**: quando `salvar_ambiente` recusa, o serviço recarrega, reaplica a
>    mudança e salva de novo — sem propagar exceção para a tela. É o custo declarado de Q4=C.
> 6. **Apagar ambiente é orquestrado aqui**: primeiro `apagar_ambiente` (banco), depois o diretório
>    da wiki. Nessa ordem — se travar no meio, sobra diretório órfão inofensivo em vez de ambiente
>    vivo apontando para wiki inexistente.

> **/!\ Emenda 2026-10-02 - Functional Design de U4 `ambiente`.** **Histórias: 5 → 7**, alinhando
> com `unit-of-work-story-map.md`, que já atribuía **US-04** (`anotar_memoria`) e **US-19**
> (`concluir_etapa`) a U4 (R-FD4-3). A gravação de etapas de **US-17** também passa por aqui
> (`criar_etapa`, C1=A). **Critério 6** é cumprido por uma operação nova, `PortaWiki.apagar` (Q6=A),
> que **reabre U3** para esse acréscimo no Code Generation de U4. Critério 5 detalhado: até 3
> tentativas, depois `ConflitoDeVersao` com a memória igual ao disco (Q4=A).

**Estágios**: FD **EXECUTE** (é onde mora a coordenação de criação de ambiente) · NFR-R **SKIP**
(não tem RNF próprio; durabilidade é de U2, confinamento é de U3, e esta unidade só consome portas) ·
NFR-D **SKIP** · CG **EXECUTE**.

---

### U5 — `acoes`

| Campo | Conteúdo |
|---|---|
| **Componentes** | `CatalogoDeAcoes`, `ParserDeComando` |
| **Histórias** | US-04, US-15, US-16, US-17, US-19 |
| **Dívidas** | **TD-11** (argumento com espaço quebra comando) |
| **Depende de** | U1, U4 |

**Vocabulário (R9).** As ações deste catálogo, quando expostas a um agente, são as
**ferramentas de ambiente** — tocam `Ambiente`, `Frente`, `Tarefa`, `Etapa`, `Chat`. São do
orquestrador; nenhum sub-agente as recebe.

**Critério de pronto.**
1. `/nova-tarefa campanha de verao` interpreta o argumento inteiro (mata TD-11), com teste.
2. Toda ação é dado no registro, não `match/case`: paleta, botão e atalho leem o mesmo registro.
3. Toda ação é `async` e devolve `Resultado` tipado, nunca string.
4. Conversar **não** está no catálogo (Pergunta E2).
5. Uma ação acionada por agente consulta ~~`ambiente.aprovacao_de_agente_obrigatoria`~~
   **[rodada 4]** `exige_aprovacao(...)` (`dominio/politica.py`, U1) antes de executar e, como a
   política devolve `True` nesta iteração, **sempre** devolve pedido de confirmação em vez de
   efetivar. Uma ação acionada pelo usuário via `/comando` executa direto — a política só governa o
   chamador agente.
6. `criar_chat(agente=...)` só aceita agente de lista fechada — nesta iteração `{bibliotecário}`
   (R3). Um sub-agente não pode instanciar agente algum.

> **/!\ Emenda 2026-10-02 - Functional Design de U5 `acoes`.** Detalhe em
> `construction/acoes/functional-design/`.
> - **São 6 ações** (Q1=A): `criar_frente`, `criar_tarefa`, `criar_chat`, `criar_etapa`,
>   `concluir_etapa`, `anotar_memoria`. Ciclo de vida do ambiente e navegação ficam na tela (U9).
>   O "13" da linha de estágios abaixo vinha dos 13 itens do `enum Comando` antigo (R-FD5-1).
> - **O orquestrador pode acionar as 6** (Q2=B), sempre com confirmação, e sempre na tarefa do chat
>   dele: o alvo é amarrado pelo sistema e nenhum parâmetro é identidade (Q3=A). `criar_tarefa`
>   pelo agente cria na frente da própria tarefa (C1=A).
> - **Critério 1**: ~~`/nova-tarefa campanha de verao`~~ → `/criar-tarefa campanha de verao`. O
>   comando é o nome da ação com hífen (Q6=A).
> - **Critério 3**: o `Resultado` existe na fronteira do catálogo, que é o único caminho para
>   executar uma ação; a função de cada ação devolve o objeto ou levanta (G1).
> - **Critério 5**: ~~"sempre devolve pedido de confirmação em vez de efetivar"~~ → **nunca efetiva
>   antes de você confirmar**: a chamada do agente **espera** a sua resposta pela
>   `PortaDeConfirmacao` e recebe o resultado real, ou `RECUSADA` (Q4=A, R-FD5-6). Só `True`
>   confirma.
> - **Critério 6** já é cumprido por U4 (RN-A-22); U5 só traduz `AgenteDesconhecido` (R-FD5-5).

**Estágios**: FD **EXECUTE** (~~13~~ **6** ações, escopos, parâmetros tipados, ponto de consulta ao parâmetro
de aprovação) · NFR-R **SKIP** (sem I/O próprio, sem rede; a superfície de segurança relevante —
escopo de ferramenta — é de U6) · NFR-D **SKIP** · CG **EXECUTE**.

---

### U6 — `sessao`

| Campo | Conteúdo |
|---|---|
| **Componentes** | `PortaSessao`, `AdaptadorSessaoClaude`, servidor MCP in-process, registro nome→função de ferramentas |
| **Histórias** | US-01, US-02, US-03 (adaptador), US-13/US-17 (exposição de ferramentas) |
| **Dívidas** | **TD-01**, **TD-02** |
| **Depende de** | U1 (`Agente`) · **U5** (`CatalogoDeAcoes`, só no módulo `aplicacao/ferramentas/` — emenda FD de U6, Q9=A) |

**Por que a exposição de ferramentas mora aqui e não em unidade própria** (Q12=A + R4): `Agente`
carrega apenas **nomes** de ferramentas; o composition root (`U9`) monta o registro nome→função,
juntando ferramentas de wiki e ferramentas de ambiente; este adaptador resolve os nomes ao abrir a
sessão. Assim `ServicoConversa` **não** importa `CatalogoDeAcoes`, e a matriz de
`component-dependency.md` não ganha seta nova entre unidades que Q2=A quer independentes.

**Critério de pronto.**
1. Contrato da porta exige resposta não vazia; adaptador falso e real passam pelo mesmo teste
   (mata TD-01).
2. Importar `dominio/` e `aplicacao/` com o SDK **desinstalado** funciona (mata TD-02); este é o
   único módulo que importa `claude_agent_sdk`.
3. Duas sessões vivas simultâneas no mesmo processo (orquestrador e bibliotecário), medido pelo
   spike.
4. Falha do provedor vira erro tipado, sem exceção crua atravessando a porta (RNF-06).
5. Exposição via MCP in-process, um servidor por conjunto de ferramentas (Q11=A).
6. **R10 — invariante de escopo, testável sem LLM**: percorrer as instâncias de `Agente`
   configuradas e verificar que nenhuma com `papel = SUB_AGENTE` carrega nome de ferramenta da
   família ambiente. Teste de configuração, milissegundos, sem assinatura.
7. A sessão do bibliotecário abre com ferramentas nativas de escrita fechadas (`tools=[]`).

> **/!\ Emenda 2026-10-02 - Functional Design de U5 `acoes`** (`business-logic-model.md` §9).
> Herdado por U6: (1) a família de ferramentas de ambiente são as **6 ações** do catálogo, e o
> critério 6 (R10) verifica os 6 nomes; onde o teste mora é decisão desta unidade (R-FD5-8);
> (2) o esquema de cada ferramenta sai do `Parametro` (tipo, obrigatório, opções, máximo,
> descrição); (3) **medir** se uma ferramenta MCP in-process pode esperar uma pessoa responder
> sem tempo limite — é o risco declarado de Q4=A de U5, e, se houver limite, U5 é reaberta;
> (4) o texto que o agente recebe é montado a partir do `Resultado`, incluindo a posição da etapa.

> **/!\ Emenda 2026-10-02 - Functional Design de U6 `sessao`.** Detalhe em
> `construction/sessao/functional-design/` (54 regras `RN-S-01..54`, 12 propriedades
> `PBT-U6-01..12`).
> - **Critério 1** (TD-01): "resposta não vazia" passa a ser **texto não vazio ou ao menos um uso de
>   ferramenta**; sem nenhum dos dois, o turno termina em `RESPOSTA_VAZIA` (Q3=B). O teste de
>   contrato roda no adaptador falso e no real.
> - **Critério 3**: ~~"medido pelo spike"~~ → **re-medido** no Code Generation com a versão
>   travada do SDK (R-FD6-4).
> - **Critério 4**: o erro tipado é o evento **`FalhaDoTurno`** (G1), com 9 motivos (Q4=A).
>   `enviar` nunca levanta; `abrir` só levanta erro de montagem (G5).
> - **Critério 6** (R10) vale **em duas camadas**: `abrir` recusa a sessão, e
>   `verificar_escopo` é chamada no teste das instâncias reais, em U8 e U9 (Q14=A).
> - **Critério 7**: ~~só o bibliotecário~~ → **nenhum agente** recebe ferramenta nativa nem a
>   configuração do Claude Code da máquina (Q11=A).
> - **Novo**: `abrir(agente, contexto)` e registro de **fábricas** (Q8=A, R-FD6-1); a conversão
>   ação→ferramenta é um módulo de aplicação sem SDK, por isso U6 depende de U5 (Q9=A); variáveis de
>   credencial de API não chegam ao processo do agente (Q13=A); sem limite de passos por turno
>   (Q12=B, risco aceito em D-Q12-1).
> - **Toda sessão nasce sem o histórico do chat** (R-FD6-10): US-07 continua adiada.

**Estágios**: FD **EXECUTE** (contrato de eventos: pedaço de texto, uso de ferramenta, fim de
turno) · NFR-R **EXECUTE** (RNF-06 isolamento de falha; escopo de ferramenta por papel é controle de
segurança, não conveniência) · NFR-D **EXECUTE** · CG **EXECUTE**.

---

### U7 — `conversa`

| Campo | Conteúdo |
|---|---|
| **Componentes** | `ServicoConversa` |
| **Histórias** | US-01, US-02, US-03, US-06, US-17, US-19 |
| **Dívidas** | Nenhuma |
| **Depende de** | U1, U2, U6 |

**Critério de pronto.**
1. Política de gravação (Pergunta A): a mensagem do agente entra no banco no **início** do turno com
   marca "em andamento", é atualizada durante o streaming, e a marca sai no fim.
2. Se o processo morre no meio do turno, a mensagem parcial permanece marcada — não some nem se
   apresenta como completa.
3. Persiste texto **e** registro resumido de uso de ferramenta (Pergunta F/B); não persiste o stream
   bruto de tokens. **[Emenda 2026-08-26 / NFR Q6]** o registro é **tool + argumentos**; o
   ~~resultado resumido~~ sai desta iteração.
4. Falha em um chat não propaga para outro chat (RNF-06, US-03).
5. Mantém o mapeamento `chat.id → SessaoViva`; não guarda estado de sessão em `Agente`.
6. **[Emenda 2026-08-27 / NFR Design de U2, Q5=A]** A **cadência** de gravação durante o streaming
   é responsabilidade desta unidade: intervalo mínimo de ~500 ms entre atualizações da mesma
   mensagem, mais **uma escrita final obrigatória** ao fim do turno. A porta de persistência sempre
   escreve o que lhe pedem — ela não descarta chamadas. É aqui que `NFR-P-03` de U2 é cumprido e
   medido.

> **/!\ Emenda 2026-10-02 - Functional Design de U5 `acoes`** (D-Q2-2). Herdado por U7: (1) o
> estado da tarefa que chega ao orquestrador a cada chamada traz **as etapas, com posição e
> situação**, e não só a memória — sem isso, o orquestrador não sabe qual posição concluir
> (Q8=A e Q12=A de U5); (2) cancelar o turno cancela o pedido de confirmação pendente, e nada
> executa (RN-AC-30).

> **/!\ Emenda 2026-10-02 - Functional Design de U6 `sessao`** (`business-logic-model.md` §10).
> Herdado por U7: (1) **a fila** de mensagens é daqui (C1=B): o que você escreve durante um turno
> sai junto, numa mensagem só, quando o turno acaba; (2) depois de um turno com falha, a fila **não**
> sai sozinha (C3=A); (3) uma mensagem só fica na transcrição se chegou ao agente
> (`MensagemEntregue`); interrompida depois disso, fica marcada como interrompida (C2=A);
> (4) `conversa_nova` num chat com transcrição pede um aviso de que o agente não lembra o que veio
> antes (R-FD6-10); (5) decidir qual `Agente` abre a sessão de um chat salvo — a cópia guardada ou a
> configuração atual (R-FD6-9); (6) montar o `ContextoDaSessao` a partir do chat; (7) ~~usar cada
> sessão sempre a partir do mesmo contexto async~~ **(dispensado pela emenda de 2026-10-13 abaixo)**; (8) prompt do orquestrador: depois de agir, contar
> o que fez e onde (D-Q3-1); (9) quando fechar a sessão, e o que mostrar se `abrir` recusar a
> configuração. Isso **muda o passo 3 de `services.md` §3**, que grava a mensagem do usuário antes
> de enviar.

> **/!\ Emenda 2026-10-13 - NFR Design de U6 `sessao`** (`nfr-design-patterns.md` §3). Para U7:
> a herança (7) acima **deixa de existir**: `enviar` pode ser chamado de qualquer tarefa, porque o
> cliente do SDK vive inteiro na tarefa dona da conexão (Q1=A). E, depois de um ESC, uma mensagem
> enviada logo em seguida **espera** o adaptador terminar de interromper o provedor (até 5 s), em vez
> de voltar com `TURNO_EM_ANDAMENTO` (N2).

**Estágios**: FD **EXECUTE** (a política de gravação é regra de negócio com casos de borda reais) ·
NFR-R **EXECUTE** (RNF-06; responsividade percebida do streaming) · NFR-D **EXECUTE** · CG
**EXECUTE**.

---

### U8 — `bibliotecario`

| Campo | Conteúdo |
|---|---|
| **Componentes** | `ServicoBibliotecario`, `FerramentasWiki` (MCP in-process), prompts `AgenteBibliotecario`/`AgenteOrquestrador` |
| **Histórias** | US-13, US-14 |
| **Dívidas** | Nenhuma |
| **Depende de** | U1, U3, U6 |

**Vocabulário (R9).** As tools desta unidade são as **ferramentas de wiki** — tocam páginas e
índice. São do bibliotecário; o orquestrador não as recebe (Q14=X). Quando o orquestrador precisa de
algo na wiki, ele cria um chat com o bibliotecário (`criar_chat`, ferramenta de ambiente) e avisa
você no chat.

**Critério de pronto.**
1. `propor_entidade` e `propor_propriedade` **nunca** escrevem — produzem proposta (Pergunta 9A);
   nem em área de rascunho dentro da raiz.
2. Uma proposta pode conter várias páginas; aprovar é um ato por promoção, não por arquivo.
3. Ao aprovar: escreve, valida links `[[...]]` (recusa ou converte em proposta de página nova) e
   aciona `renderizar_index`.
4. Ao rejeitar: nada toca o filesystem.
5. `buscar` **não existe** (Q13=A): leitura é `listar` + `ler`, começando pelo `index.md`.
6. A consulta à política de aprovação é o **mesmo** mecanismo de U5, não um segundo caminho
   paralelo — a proposta do bibliotecário (Decisão 15) e a ferramenta de ambiente do orquestrador
   passam pela mesma função e pela mesma tela.

> **/!\ Emenda 2026-10-02 - Functional Design de U5 `acoes`.** O "mesmo mecanismo" do critério 6
> passa a ter nome: a **`PortaDeConfirmacao`** (`aplicacao/portas/`, dona U5), que **espera** a
> resposta e só aceita `True` como confirmação (Q4=A de U5). Como a proposta entra nela é decisão
> do FD desta unidade. O nome do bibliotecário deve ser ASCII minúsculo (ex.: `bibliotecario`),
> porque é o que se digita em `/criar-chat` e U4 compara o nome exatamente.

> **/!\ Emenda 2026-10-02 - Functional Design de U6 `sessao`.** Herdado por U8: (1) as ferramentas
> de wiki entram no `RegistroDeFerramentas` como entradas da família `WIKI`, com fábrica
> `(contexto, agente) -> Ferramenta` (tipo neutro, sem SDK); o texto que o bibliotecário lê é
> daqui; (2) o teste R10 das instâncias reais chama `verificar_escopo` (Q14=A de U6); (3) o
> bibliotecário abre sessão pela mesma porta e, como todo agente, sem ferramenta nativa (Q11=A
> de U6).

**Estágios**: FD **EXECUTE** (ciclo propor→aprovar→escrever, com estados) · NFR-R **EXECUTE**
(RNF-14: conteúdo de wiki é entrada não confiável que chega ao contexto deste agente) · NFR-D
**EXECUTE** · CG **EXECUTE**.

---

### U9 — `interface`

| Campo | Conteúdo |
|---|---|
| **Componentes** | `FishingRodTUI` (Textual), `ComposicaoRoot` (`__main__`) |
| **Histórias** | Superfície de todas as 14 |
| **Dívidas** | Nenhuma |
| **Depende de** | **Todas** (U1–U8) |

**Escopo novo desta rodada (CQ4=A).** O fluxo de confirmação é construído aqui: quando uma
ferramenta acionada por agente precisa de aprovação, a TUI mostra a ação e os parâmetros e espera
sim/não. **Um fluxo só** — atende ferramentas de ambiente e propostas do bibliotecário. ~~Mais a tela
onde o parâmetro é desligado~~ (**[rodada 4] a tela de configuração sai**: não há parâmetro a
desligar nesta iteração), e a tela de início que cria ou escolhe ambiente (Q10=B / R7).

> **Por que o fluxo permanece mesmo com o parâmetro revogado.** Ele não era escopo do parâmetro: a
> **US-14** ("revisar antes de o bibliotecário escrever") já o exige, e é história aprovada da linha
> fina (critério 4 abaixo). Retirar o parâmetro tira a tela de configuração e o campo persistido —
> não a confirmação.

**Critério de pronto.**
1. Entrada com `/` vai para `ParserDeComando`; entrada sem `/` vai para `ServicoConversa`.
2. Streaming renderiza incrementalmente, sem travar a TUI.
3. Erro em um chat/aba não derruba as demais (US-03).
4. Propostas pendentes do bibliotecário aparecem e podem ser aprovadas/rejeitadas (US-14).
5. Formulário de estrutura de wiki na criação de ambiente (US-09).
6. Tela de início lista os ambientes locais e cria um novo (Q10=B).
7. `ComposicaoRoot` é o **único** módulo que importa todas as camadas e monta o registro
   nome→função de ferramentas (R4).

> **[Emenda — Functional Design de U2, 2026-08-26]** Dois critérios acrescentados:
> 8. **Aviso e confirmação antes de apagar ambiente** (Q8=B): a tela avisa que apagar destrói tudo
>    que existe dentro do ambiente — frentes, tarefas, chats, transcrição, memória e wiki — e exige
>    confirmação explícita. `PortaPersistencia.apagar_ambiente` apaga sem perguntar; **a única
>    proteção do usuário mora aqui**.
> 9. **`ComposicaoRoot` resolve a pasta de dados do sistema operacional** (Q1=A / Q1a=B), em ~12
>    linhas sobre `sys.platform`, sem dependência nova. É o único lugar que conhece caminho de disco.

> **/!\ Emenda 2026-10-02 - Functional Design de U5 `acoes`** (`business-logic-model.md` §9).
> Herdado por U9: implementar a `PortaDeConfirmacao` (mostrar quem pede, a ação, as referências
> pelo nome e os argumentos; em `concluir_etapa`, posição **e** descrição da etapa); enfileirar
> pedidos de chats diferentes que chegam juntos e tirar da tela o pedido cancelado; montar o `Alvo`
> a partir da seleção e o `Acionamento` do usuário; amarrar `Alvo` e `Acionamento` de cada chat às
> ferramentas do agente; escrever a frase de cada `MotivoFalha`; chamar o ciclo de vida do
> ambiente direto no serviço (fora do catálogo, Q1=A de U5); não criar comando de tela com nome de
> ação; **escapar o texto** ao desenhar (marcação do Textual); dar destino ao log
> `fishingrod.acoes`.

> **/!\ Emenda 2026-10-02 - Functional Design de U6 `sessao`.** Herdado por U9: montar o
> `RegistroDeFerramentas` (`entradas_de_acoes(catalogo)` + as entradas de U8); resolver a pasta de
> trabalho das sessões e entregá-la ao adaptador; chamar `encerrar()` no fim do programa; **ESC**
> cancela a tarefa que lê o turno, devolve ao campo o texto da mensagem interrompida e o da fila, e
> mostra a mensagem interrompida se ela chegou ao agente (C2=A); mostrar a fila; escrever a frase de
> cada `MotivoFalhaDeSessao` (em `NAO_AUTENTICADO`, como fazer o login); mostrar o aviso de conversa
> nova; dar destino ao log `fishingrod.sessao`. O teste R10 das instâncias reais (critério 6 de U6)
> chama `verificar_escopo`.

> **/!\ Emenda 2026-10-13 - NFR Design de U6 `sessao`** (`R-ND6-9`, `logical-components.md` §4).
> Herdado por U9: `fechar` só volta com o processo do CLI morto, o que pode levar até ~15 s no pior
> caso; para não travar a tela, U9 pode disparar o fechamento de um chat sem esperar, e `encerrar()`
> fecha o que faltar. O registro é montado com `entradas_de_acoes(catalogo)`, de
> `aplicacao/ferramentas/acoes.py`, que **só U9 importa** (`R-ND6-3`).

**Estágios**: FD **EXECUTE** (fluxo de confirmação, navegação, tela de início) · NFR-R **EXECUTE**
(responsividade sob streaming, isolamento de falha por aba) · NFR-D **EXECUTE** · CG **EXECUTE**.

---

## 4. Estratégia de organização de código (Q8=A, Q9=A)

### Layout de destino

```
FishingRod/
├── pyproject.toml          U0
├── uv.lock                 U0
├── src/
│   └── fishingrod/
│       ├── __main__.py         U9  (composition root)
│       ├── dominio/            U1
│       ├── aplicacao/
│       │   ├── portas/         U2 (persistencia), U3 (wiki), U6 (sessao)
│       │   ├── catalogo/       U5
│       │   └── servicos/       U4, U7, U8
│       ├── adaptadores/        U2, U3, U6, U8
│       └── interface/          U9
├── tests/
└── testes-de-aprendizado/  (mantido; fora de garantias)
```

**Camada no topo** (Q9=A): o primeiro nível dentro de `fishingrod/` é a camada, não a feature. Isso
faz a regra de import de `component-dependency.md` §1 ser verificável por inspeção do caminho do
módulo, sem convenção extra.

### Destino do código atual (Q8=A)

| Hoje | Destino | Quando é apagado |
|---|---|---|
| `Ambiente/ambiente.py`, `memoria.py` | reescrito em `src/fishingrod/dominio/` | ao fechar **U1** |
| `Ambiente/agente.py` | dividido: configuração → `dominio/`, sessão → `adaptadores/` | ao fechar **U6** |
| `Ambiente/sessao.py` | reescrito em `aplicacao/servicos/` | ao fechar **U7** |
| `model/comando.py` | reescrito em `aplicacao/catalogo/` | ao fechar **U5** |
| `model/mensagem.py` | reescrito em `dominio/` | ao fechar **U1** |
| `tui.py` | reescrito em `interface/` | ao fechar **U9** |
| `cli.py` | **permanece como está** — fora de garantias (FOR-11), sem quality gate | nunca |
| `testes-de-aprendizado/` | permanece | nunca |

~~**Regra**: o código antigo só é apagado quando a unidade que o substitui fecha, nunca antes. Até lá
os dois coexistem — o antigo continua rodando enquanto o novo não está pronto.~~

> **/!\ Emenda 2026-08-26 — U1 fechada.** A regra muda de **"quando a unidade fechar"** para
> **"quando o substituto estiver executável"**, e a coluna "quando é apagado" da tabela acima passa
> a valer com esse critério. Dois motivos, o segundo descoberto na prática:
>
> 1. **A preservação já está resolvida por fora**: o trabalho passou a viver na branch
>    `iteracao-1-linha-fina`, e o código antigo continua íntegro na `main` (commit `14f81eb`).
>    Apagar deixou de ser a forma de preservar histórico.
> 2. **Apagar cedo destrói a única forma de rodar o software.** `cli.py` e `tui.py` importam
>    `Ambiente.ambiente` e `Ambiente.sessao`, e `sessao.py` importa `memoria.py`. Remover os três
>    arquivos que U1 substitui quebraria o app imediatamente — e o substituto (`U9`) está oito
>    unidades adiante. A regra original não previa isso porque foi escrita antes de existir código
>    novo para comparar.
>
> **Decisão do usuário em 2026-08-26**: manter o código antigo até U9. Nada foi removido no
> fechamento de U1.

---

## 5. Conta de portões de aprovação

A promessa da R1 era declarar isto antes de você pagar.

| Unidade | FD | NFR-R | NFR-D | CG | Portões |
|---|:--:|:--:|:--:|:--:|:--:|
| U0 `fundacao` | SKIP | SKIP | SKIP | ✔ | 1 |
| U1 `dominio` | ✔ | SKIP | SKIP | ✔ | 2 |
| U2 `persistencia` | ✔ | ✔ | ✔ | ✔ | 4 |
| U3 `wiki` | ✔ | ✔ | ✔ | ✔ | 4 |
| U4 `ambiente` | ✔ | SKIP | SKIP | ✔ | 2 |
| U5 `acoes` | ✔ | SKIP | SKIP | ✔ | 2 |
| U6 `sessao` | ✔ | ✔ | ✔ | ✔ | 4 |
| U7 `conversa` | ✔ | ✔ | ✔ | ✔ | 4 |
| U8 `bibliotecario` | ✔ | ✔ | ✔ | ✔ | 4 |
| U9 `interface` | ✔ | ✔ | ✔ | ✔ | 4 |
| **Total** | | | | | **31** |

`INFRA` é SKIP nas 10 (sem deploy nesta iteração). A estimativa da Parte 1 era "da ordem de 36"; o
número real é **31**, porque quatro unidades não têm RNF próprio e duas não têm regra de negócio.

---

## 6. Conformidade das extensões habilitadas

| Extensão | Situação neste estágio |
|---|---|
| `security-baseline` | **Conforme.** As regras de HTTP/IAM/CORS/load balancer são **N/A** (não há rede nem deploy). As aplicáveis têm unidade dona nomeada: SECURITY-05 confinamento de caminho → **U3** (critério 5); SECURITY-10 dependências travadas → **U0** (critério de aceite); entrada não confiável (RNF-14) → **U3** na leitura e **U8** no contexto do agente. **A ressalva aberta na rodada 2 está fechada**: a Q14=X manteve o isolamento de contexto intacto — o orquestrador não recebe ferramentas de wiki — e o risco residual de mutação sem aprovação virou ~~o parâmetro de CQ2/CQ3~~ **[rodada 4]** a política constante `exige_aprovacao(...)`, com dono (`U1`), ponto de consulta (`U5` e `U8`) e fluxo (`U9`). **A revogação do parâmetro reforça a conformidade em vez de enfraquecê-la**: o estado seguro deixa de ser um padrão que o usuário pode desligar e passa a ser o único comportamento desta iteração. |
| `property-based-testing` (Full) | **Conforme.** PBT-01 satisfeito: as propriedades identificadas em Application Design têm unidade dona — round-trip de serialização do `Ambiente` → **U2** (critério 2); confinamento de caminho (PBT-03) → **U3** (critério 5); `Memoria.anotar` em chave nova → **U1** (critério 1). A especificação formal (estratégias `hypothesis`, invariantes exatos) é de Functional Design/NFR Requirements por unidade, não deste estágio. |
| `resiliency-baseline` | **N/A** — desabilitada por decisão de 2026-08-17. Não enforçada. |
