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

**Estágios**: FD **EXECUTE** (fronteira documento vs tabela, política de gravação) · NFR-R
**EXECUTE** (RNF-05 durabilidade; comportamento sob escrita concorrente de duas sessões vivas) ·
NFR-D **EXECUTE** · CG **EXECUTE**.

---

### U3 — `wiki`

| Campo | Conteúdo |
|---|---|
| **Componentes** | `PortaWiki`, `AdaptadorWikiFilesystem`, `EsquemaWiki` |
| **Histórias** | US-08, US-09 |
| **Dívidas** | Nenhuma |
| **Depende de** | U0, U1 (`RaizWiki`) |

**Por que esta unidade fecha sem o bibliotecário existir** (o que sustenta Q6=A como separação real
e não arrumação — reconciliação R6): quem materializa a wiki na criação do ambiente é
`ServicoDeAmbiente`, não o bibliotecário, e `renderizar_index` é **projeção do disco**, então uma
página criada fora do app aparece no índice na próxima renderização.

**Critério de pronto (CQ1=A — só determinístico).**
1. Toda entidade e toda propriedade presente no disco aparece no `index.md` regenerado.
2. Nenhuma propriedade com `descricao` vazia no frontmatter.
3. Uma página criada fora do app aparece no índice após regeneração.
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
   operação só; invariante de criação: ao menos uma entidade.
2. Criar frente / criar tarefa / criar chat / concluir etapa / anotar memória delegam a invariante ao
   objeto de domínio e persistem via porta.
3. Nenhum `import` de `sqlite3` nem de `claude_agent_sdk`.
4. Vários ambientes locais coexistem na mesma instalação (Q10=B): `carregar_ambiente(id)` devolve o
   ambiente certo, e cada um tem sua raiz de wiki própria.

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

**Estágios**: FD **EXECUTE** (13 ações, escopos, parâmetros tipados, ponto de consulta ao parâmetro
de aprovação) · NFR-R **SKIP** (sem I/O próprio, sem rede; a superfície de segurança relevante —
escopo de ferramenta — é de U6) · NFR-D **SKIP** · CG **EXECUTE**.

---

### U6 — `sessao`

| Campo | Conteúdo |
|---|---|
| **Componentes** | `PortaSessao`, `AdaptadorSessaoClaude`, servidor MCP in-process, registro nome→função de ferramentas |
| **Histórias** | US-01, US-02, US-03 (adaptador), US-13/US-17 (exposição de ferramentas) |
| **Dívidas** | **TD-01**, **TD-02** |
| **Depende de** | U1 (`Agente`) |

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
   bruto de tokens.
4. Falha em um chat não propaga para outro chat (RNF-06, US-03).
5. Mantém o mapeamento `chat.id → SessaoViva`; não guarda estado de sessão em `Agente`.

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

**Regra**: o código antigo só é apagado quando a unidade que o substitui fecha, nunca antes. Até lá
os dois coexistem — o antigo continua rodando enquanto o novo não está pronto.

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
