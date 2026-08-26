# Application Design — FishingRod, Iteração 1 (Consolidação)

**Estágio:** INCEPTION — Application Design · **Profundidade:** comprehensive
**Data:** 2026-08-25
**Entradas:** `application-design-plan.md` (rodadas 1 e 2, 17/17 decisões fechadas),
`application-design-clarification-questions.md`, `requirements.md` v2, `stories.md` (linha fina,
14 histórias), artefatos de Reverse Engineering
**Artefatos consolidados:** `components.md`, `component-methods.md`, `services.md`,
`component-dependency.md`

> Este documento não repete conteúdo dos quatro artefatos — consolida a visão, fecha a
> rastreabilidade história-a-história e apresenta o resultado da verificação dos critérios de
> conclusão do estágio (regra `inception/application-design.md`).

---

## 1. O que este estágio decidiu

Application Design fechou as oito decisões arquiteturais deixadas abertas por Requirements
Analysis (`requirements.md` §6, §9.8) e mais uma que surgiu durante a própria rodada de perguntas
(natureza de bibliotecário/rod-maker como agentes). Resumo executivo de cada uma:

| # | Decisão | Resolução | Componentes que a materializam |
|---|---|---|---|
| 1 | Cadeia `Ambiente → Projeto → Sessao` | Hierarquia de dados preservada; roteamento e delegação saem do domínio para a aplicação | `Ambiente`/`Frente`/`Tarefa` (domínio, sem roteamento) + `CatalogoDeAcoes`/`ParserDeComando`/`ServicoDeAmbiente` (aplicação) |
| 1-bis | Natureza de bibliotecário/rod-maker | Agentes de primeira classe (julgamento), com tools próprias como cerca determinística | `Agente` (config) + `ServicoBibliotecario` + `FerramentasWiki` |
| 2 | Identidade | UUIDv7, gerada no construtor da entidade de domínio | `Identidade` |
| 3 | Fronteira do agregado / persistência | `Ambiente` como documento; transcrição como tabela append-only separada | `PortaPersistencia` / `RepositorioSQLite` |
| 4 | Porta de sessão viva | Assíncrona nativa, com iterador de eventos (streaming) | `PortaSessao` / `AdaptadorSessaoClaude` |
| 5 | Critério entidade vs propriedade | Toda escrita é proposta; critério semântico (substantivo novo vs característica) mora no prompt do bibliotecário; estrutura de dois níveis mora em código | `FerramentasWiki.propor_entidade`/`propor_propriedade` |
| 6 | Grafo que manda na recuperação | `index.md` como passo obrigatório; hierarquia localiza, links associam e são validados na escrita | `AdaptadorWikiFilesystem.renderizar_index` |
| 7 | Assinaturas e permissão das tools de wiki | Tools próprias via MCP in-process; ferramentas nativas de escrita negadas | `FerramentasWiki` |
| 8 | Ordem de correção das dívidas TD-01 a TD-04 | Cada dívida morre na unidade que reescreve o componente, com critério de aceite nomeado e teste de regressão | Ver §5 deste documento |

Mais as seis decisões da rodada 2 (política de gravação, lint fora, maquetes embutidas, localizador
com esquema, catálogo assíncrono com conversa fora dele, conteúdo da transcrição) — todas
detalhadas em `application-design-plan.md` §4 e refletidas nos quatro artefatos.

---

## 2. Visão geral da arquitetura

```
interface/     FishingRodTUI (Textual) — única interface entregável (D-ARQ-07)
     │
aplicacao/     CatalogoDeAcoes, ParserDeComando, ServicoDeAmbiente, ServicoConversa,
               ServicoBibliotecario, EsquemaWiki, e as portas (PortaPersistencia,
               PortaSessao, PortaWiki)
     │
dominio/       Identidade, Ambiente, Frente, Tarefa, Chat, Etapa, Memoria,
               Agente (configuração imutável), RaizWiki
     │
adaptadores/   RepositorioSQLite, AdaptadorSessaoClaude, AdaptadorWikiFilesystem,
               FerramentasWiki (MCP in-process)

__main__       composition root — único ponto que constrói tudo e injeta (Pergunta 11A)
```

Ver `component-dependency.md` §5 para o diagrama Mermaid completo (com fallback textual) e §1 para
a regra de import por camada.

### Garantias estruturais que este desenho entrega

- **RF-F04 / TD-02**: núcleo sem `claude_agent_sdk`. Prova executável: teste que importa
  `dominio/`/`aplicacao/` com o SDK desinstalado.
- **D-ARQ-04**: persistência atrás de porta em vocabulário de domínio, sem menção a SQL.
- **RF-F17**: uma regra, N superfícies — catálogo de ações é dado, não `match/case`; paleta `/`,
  botões e atalhos leem o mesmo registro.
- **RNF-10/RNF-11/RNF-14**: confinamento de caminho e escrita só por proposta aprovada,
  estruturalmente irrepresentáveis de violar (assinatura das tools não tem parâmetro para
  terceiro nível de profundidade).
- **RNF-12**: banco não guarda nada sobre a wiki alem da referência à raiz.
- **RNF-06/US-03**: falha de provedor convertida em evento de erro tipado na fronteira do
  adaptador, nunca exceção crua até a TUI.

---

## 3. Rastreabilidade — história → componentes → RF/RNF

| História | Componentes responsáveis | RF/RNF/ESC |
|---|---|---|
| **US-01** — Conversar com agente real | `Chat`, `Agente`, `ServicoConversa`, `PortaSessao`, `AdaptadorSessaoClaude` | RF-F01, ESC-01 |
| **US-02** — Sessão por assinatura, sem API key | `PortaSessao`, `AdaptadorSessaoClaude` (único adaptador, sem contraparte de API key) | RF-F03, ESC-18, D-ARQ-06 |
| **US-03** — Falha do provedor não derruba a interface | `ServicoConversa`/`ServicoBibliotecario` (tratamento de erro, §8 de `services.md`), `AdaptadorSessaoClaude` | RF-F01, RNF-06 |
| **US-04** — Anotar sem erro na primeira chave | `Memoria.anotar` (corrige TD-03) | RF-F06, ESC-06 |
| **US-05** — Estrutura sobrevive a fechar/reabrir | `PortaPersistencia`, `RepositorioSQLite`, `ServicoDeAmbiente.carregar_ambiente` | RF-F05, ESC-05 |
| **US-06** — Transcrição antiga continua visível | `ServicoConversa.carregar_transcricao`, tabela de mensagens (Pergunta 3B) | RF-F05 (transcrição), ESC-05 |
| **US-08** — Todo ambiente nasce com wiki | `ServicoDeAmbiente.criar_ambiente`, `EsquemaWiki`, `PortaWiki` | RF-F07, ESC-07 |
| **US-09** — Estrutura da wiki definida pelo dono | `EsquemaWiki.a_partir_do_formulario`/`carregar_toml`, maquetes embutidas | RF-F08, ESC-07, RNF-09 |
| **US-13** — Promover conteúdo via bibliotecário | `ServicoBibliotecario`, `FerramentasWiki.propor_propriedade`/`propor_entidade` | RF-F10, ESC-08 |
| **US-14** — Revisar antes de confirmar escrita | `ServicoBibliotecario.propostas_pendentes`/`aprovar`/`rejeitar` | RF-F10, RNF-14 |
| **US-15** — Criar frente | `Ambiente.criar_frente`, `ServicoDeAmbiente.criar_frente`, `CatalogoDeAcoes` | RF-F11 |
| **US-16** — Criar tarefa dentro de frente | `Frente.criar_tarefa`, `ServicoDeAmbiente.criar_tarefa` | RF-F11, RF-01 |
| **US-17** — Descobrir etapas conversando | `Etapa`, `ServicoConversa` + `ServicoDeAmbiente` (ver `services.md` §7) | RF-F12, RF-07 |
| **US-19** — Executar etapa via chat | `Etapa.concluir`, `ServicoConversa`, `ServicoDeAmbiente.concluir_etapa` | RF-F12, RF-07 |

**Todas as 14 histórias da linha fina têm pelo menos um componente responsável.** Nenhuma história
da linha fina ficou sem rastreio.

### Histórias adiadas (FOR-14) — o que o desenho preserva sem implementar

| História adiada | O que o desenho já preserva |
|---|---|
| US-07 (continuidade real de memória) | `PortaSessao.abrir` pode evoluir para aceitar identificador de retomada sem mudar a assinatura pública — best-effort já é o comportamento natural de `SessaoViva` não persistida entre reaberturas |
| US-10 (criar categoria conversando) | `FerramentasWiki.propor_entidade` já existe (decisão da Pergunta 13) e cobre parte do valor; formalmente, US-10 continua fora de escopo e sem critério de aceite nesta iteração (registrado como ponto de objeção no plano, §5) |
| US-11, US-12 (rod-maker) | `Papel.SUB_AGENTE` permanece no tipo `Agente`; nenhuma instância nem implementação de rod-maker é desenhada |
| US-18 (reaproveitar tarefa) | Nenhuma estrutura de "modelo de tarefa" é criada; `Tarefa`/`Etapa` não impedem isso no futuro, mas nada é construído agora |

---

## 4. Rastreabilidade — RNF e extensões habilitadas

| RNF | Cumprido por |
|---|---|
| RNF-01 (deps com lockfile) | ESC-15, fora do escopo de Application Design (Units Generation/Code Generation) |
| RNF-02/RNF-03 (testes, PBT) | Ver §5 abaixo — critérios de aceite nomeados por dívida; PBT-01/PBT-03 apontam para round-trip de serialização e confinamento de caminho |
| RNF-04 (credenciais não hardcoded) | `AdaptadorSessaoClaude` usa autenticação por assinatura via CLI do provedor; nenhuma credencial em código ou banco |
| RNF-05 (integridade de dados persistidos) | `PortaPersistencia` com transação por operação (Pergunta A/8B) |
| RNF-06 (fail-safe) | §8 de `services.md` |
| RNF-09 (generalização entre domínios) | `EsquemaWiki` plugável; nenhum componente de domínio referencia vocabulário de marketing ou de estudos |
| RNF-10 (confinamento de caminho, gate de teste) | `AdaptadorWikiFilesystem`, assinatura de `FerramentasWiki` sem parâmetro de terceiro nível |
| RNF-11 (endereçamento lógico, sem caminho absoluto) | `RaizWiki.localizador` com esquema explícito (`dados:...`, Pergunta D) |
| RNF-12 (banco não guarda conteúdo/índice da wiki) | `Ambiente` só guarda `RaizWiki`; ver Pergunta 12D |
| RNF-13 (sem assumir escritor único) | Não implementado (fora de escopo), não tornado impossível — registrado como ponta solta na Pergunta 12 |
| RNF-14 (wiki como entrada não confiável) | Isolamento de contexto do bibliotecário (Pergunta 3-bis) + confinamento de código (Pergunta 10B) — duas defesas em profundidade |

### Conformidade de extensões (regra global do workflow)

| Extensão | Situação | Avaliação nesta etapa |
|---|---|---|
| `security-baseline` | Habilitada | **Conforme.** SECURITY-05/13 (confinamento de caminho, wiki como entrada não confiável) atendidos por `AdaptadorWikiFilesystem` e pelo regime de proposta. SECURITY-12 (credenciais) atendido — nenhuma credencial em código/banco, autenticação delegada ao CLI do provedor. SECURITY-15 (fail-safe) atendido pelo tratamento de erro de `ServicoConversa`/`ServicoBibliotecario`. Regras de rede/HTTP/IAM/load balancer: **N/A** — processo local, sem porta de rede exposta nesta iteração. |
| `property-based-testing` | Habilitada (Full) | **Conforme nesta etapa** (nomeação, não especificação). PBT-01 pede identificação de propriedades no desenho: (a) round-trip de serialização do agregado `Ambiente` — nomeado em `RepositorioSQLite`; (b) nenhum caminho gerado escapa da raiz da wiki — nomeado em `AdaptadorWikiFilesystem`/`FerramentasWiki`, RNF-10. Especificação formal (Hypothesis, estratégias, invariantes exatos) fica para Functional Design/NFR Requirements, como a regra do estágio prevê. |
| `resiliency-baseline` | Desabilitada | **N/A** por decisão registrada em 2026-08-17 (`aidlc-state.md`). Não enforçada. |

---

## 5. Rastreabilidade — dívidas técnicas (Pergunta 17A)

| Dívida | Descrição | Critério de aceite nomeado | Onde morre |
|---|---|---|---|
| TD-01 | `AgenteClaude.responder()` devolve `None` | Teste da porta de sessão exige resposta não vazia; adaptador falso e real passam pelo mesmo contrato | Unidade da porta de sessão (`PortaSessao`/`AdaptadorSessaoClaude`) |
| TD-02 | SDK importado no núcleo (`agente.py:6`) | Teste que importa `dominio/`/`aplicacao/` com SDK desinstalado | Unidade do adaptador Claude |
| TD-03 | `Memoria.anotar()` lança `KeyError` | Teste (e propriedade PBT) de que anotar em chave nova funciona | Unidade de domínio (`Memoria`) |
| TD-04 | Persistência inexistente | Critério de aceite é CS-01: fechar e reabrir reconstitui o ambiente | Unidade de persistência (`PortaPersistencia`/`RepositorioSQLite`) |
| TD-11 | Argumento com espaço quebra comando | Bug de uma função (`ParserDeComando.interpretar`), com um teste | Unidade da camada de ações/comandos |

Nenhuma dívida fica sem unidade destino — todas apontam para um componente já nomeado em
`components.md`, o que satisfaz a condição da Pergunta 17A de que "morrer sozinha" não signifique
"ninguém verifica se morreu".

---

## 6. Verificação dos critérios de conclusão do estágio

Conforme `application-design-plan.md` §7:

- [x] **Todas as 17 respostas presentes e sem ambiguidade não resolvida.** 16 respondidas na
      rodada 1; a 17ª (Pergunta 8) foi refeita e respondida como Pergunta A na rodada 2; as demais
      6 ambiguidades detectadas (B a G) também foram resolvidas na rodada 2.
- [x] **Os cinco artefatos obrigatórios criados**: `components.md`, `component-methods.md`,
      `services.md`, `component-dependency.md`, e este `application-design.md`.
- [x] **As oito decisões abertas da §1 do plano fechadas e escritas, cada uma com o motivo** — ver
      §1 deste documento e o raciocínio integral em `application-design-plan.md` §3.
- [x] **Nenhum componente de domínio dependendo de `claude_agent_sdk`, `sqlite3` ou Textual**,
      verificável pela matriz e checklist de `component-dependency.md` §1 e §7.
- [x] **Cada uma das 14 histórias da linha fina rastreada a pelo menos um componente** — ver §3
      deste documento.
- [ ] **Aprovação explícita do usuário antes de Units Generation.** Pendente — ver §7.

---

## 7. Pontos abertos registrados para o portão de aprovação

> **/!\ Emenda 2026-08-25 - Units Generation. Esta seção está FECHADA.** Os cinco pontos deixaram
> de estar abertos: **1, 3 e 5** foram respondidos pelo usuário no corpo desta própria seção (as
> respostas ficam abaixo, no lugar onde foram escritas); **2** foi fechado por **Q10=B** (vários
> ambientes locais na mesma instalação, sem unidade própria — `RaizWiki` e `carregar_ambiente(id)`
> já eram multi-ambiente; entra apenas a tela de início, em **U9**); **4** permanece como desenhado
> (conclusão de etapa é confirmação do usuário; regra fina em Functional Design de **U4**/**U5**).
> O desdobramento das respostas 3 e 5 está em `plans/unit-of-work-plan.md` §1.1 e em
> `plans/unit-of-work-clarification-questions.md` (Q11-Q14, CQ1-CQ4, R1-R10).

Nenhum destes bloqueia a conclusão do estágio; estão aqui para o usuário confirmar ou objetar
antes de Units Generation, conforme reconciliações do plano (§5):

1. **`propor_entidade` entrega parte do valor de US-10**, formalmente adiada. Se isso for
   indesejado, a alternativa é restringir `propor_entidade` a exigir uma flag de configuração
   fora desta iteração — não foi feito porque o regime "toda escrita é proposta" (9A/13A) ficaria
   com um buraco sem ela.

- temos que incluir o propor_entidade. o propor_entidade é uma tool do agente bibliotecario, pois é ele quem pode mexer na wiki , ou seja ,é o agente bibliotecario que cria entidades e propriedades na wiki e todos os processos relacionados a wiki. mesmo implementando de forma simples e basica a funcionalidade de primeiro propor para depois escrever, ja agrega valor.

2. **Catálogo local de ambientes** (Pergunta 12, ponta solta): nesta iteração existe de forma
   degenerada (uma linha `ambiente` no SQLite local, sempre modo local). Não há tabela nem
   componente dedicado — se Units Generation achar que vale nomear isso como unidade própria, é
   uma extensão barata sobre o desenho atual, não uma mudança nele.
3. **Qualidade de busca da tool `buscar`** (Pergunta 10) é risco aberto explicitamente registrado,
   não segurança. Fica como item a iterar em Functional Design/NFR Design da unidade da wiki.

- a tool de busca vai ser implementada de forma simples inicialmente. a ideia da busca de informacoes na wiki pela agente bibliotecario sempre começa atravez do arquivo index.md da wiki. oq eu ja expliquei que é onde tem a estrutura da wiki e os links para as outras paginas. a estrutura é composta pelos nomes das entidades e uma lista de propriedades para cada entidade. as propriedades recebem uma descricao do conteudo presente nelas, com isso o agente bibliotecario consegue encontrar o contexto necessario. entao a funcionalidade de busca seria fazer o agente ler o index.md e deixar ele ler as paginas que ele foi encontrando.


4. **Automação de conclusão de etapa por agente** (US-19, nota em `services.md` §6): esta iteração
   trata conclusão de etapa como confirmação do usuário mesmo quando o executor é agente; regra
   fina fica para Functional Design.


5. **Como o orquestrador aciona ações do catálogo como ferramenta** (`services.md` §7): sinalizado
   para Units Generation/Functional Design, não decidido aqui — as 14 histórias da linha fina não
   exigem essa autonomia.

- o orquestrador eu penso ele como o agente principal do software , oq eu quero dizer com isso é que o orquestrador vai ter muitas ferramentas para conseguir interagir com o software. eu expliquei isso pois temos a questao aqui é, como dar para o orquestrador diversas ferramentas ? as ferramentas de agentes de ia hj em dia nos permitem passar funcoes como ferramentas e tambem passar mcp servers como ferramentas, podemos montar as nossas mcps tambem. entao a decisao de como o orquestrador vai usar as acoes do catalogo vai ser ou passar como uma funcao como uma ferramenta ou criar um mcp para dar para o orquestrador. uma observacao - o software tem diferentes tipos de agentes , como ja falei aqui o orquestrador vai ser o principal do software , ou seja, ele tem ferramentas adicionais que outros agentes nao teriam. nao pensei em detalhes ainda doque o orquestrador pode tem de ferramentas que os outros agentes nao tem, mas a ideia é simples é que o orquestrador pode mais e os outros tipos de agentes vao ser limitados mais pelo seu escopo de trabalho. 

---

## 8. Mensagem de conclusão do estágio

**Application Design (comprehensive) — concluído, pendente de aprovação do usuário.**

Resumo do que foi produzido:
- 17/17 decisões de desenho fechadas (rodadas 1 e 2), com raciocínio integral preservado em
  `application-design-plan.md` (versão limpa) e o bruto integral em
  `application-design-plan.bruto-2026-08-23.md`.
- 5 artefatos de desenho: `components.md`, `component-methods.md`, `services.md`,
  `component-dependency.md`, `application-design.md`.
- 14/14 histórias da linha fina rastreadas a componente e a RF/RNF.
- Prova estrutural de que o núcleo não depende de `claude_agent_sdk`, `sqlite3` nem Textual.
- 5 dívidas técnicas (TD-01, TD-02, TD-03, TD-04, TD-11) endereçadas com unidade destino e critério
  de aceite nomeado.

**Próximo estágio, se aprovado**: Units Generation — decomposição em unidades independentemente
construíveis e testáveis (provável agrupamento: domínio+persistência; sessão/conversa;
catálogo de ações/comandos; wiki+bibliotecário; TUI; composition root), seguido pelo loop de
Construction por unidade (Functional Design → NFR Requirements → NFR Design → Code Generation) e
Build and Test ao final.

~~**Aguardando aprovação explícita do usuário para prosseguir a Units Generation.**~~

> **/!\ Emenda 2026-08-25 - Units Generation.** **Aprovado pelo usuário em 2026-08-25** ("eu aprovo o plano. vamos continuar o ai-dlc").
Units Generation foi executado e produziu `unit-of-work.md` (10 unidades), `unit-of-work-dependency.md`
e `unit-of-work-story-map.md`. O agrupamento "provável" previsto acima **não** foi o adotado: a
granularidade fina (Q1=A) separou domínio de persistência, `ServicoDeAmbiente` virou unidade própria
(Q5=B), e wiki e bibliotecário ficaram separados (Q6=A). Registro a divergência em vez de reescrever
a previsão.
