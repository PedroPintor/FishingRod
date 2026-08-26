# Units Generation — Plano de Decomposição (Parte 1: Planejamento)

**Estágio:** INCEPTION — Units Generation · **Profundidade:** comprehensive
**Data:** 2026-08-25
**Regra aplicada:** `inception/units-generation.md` (Parte 1, passos 1 a 11)
**Entradas:** `application-design/components.md`, `component-methods.md`, `services.md`,
`component-dependency.md`, `application-design.md` (aprovado em 2026-08-25),
`requirements.md` v2, `stories.md` (linha fina, 14 histórias),
`plans/execution-plan.md` v2 (aprovado em 2026-08-20)

> **Como usar este documento**: responda cada pergunta da §3 preenchendo a tag `[Answer]:` com a
> letra da opção. Se nenhuma servir, escolha a última opção (Other) e descreva. **Nenhum artefato
> de unidade é gerado antes de todas as respostas existirem** — a §4 (Parte 2) só executa depois.

---

## 1. Contexto herdado — o que já está decidido e não se discute aqui

| Fato herdado | Origem |
|---|---|
| 18 componentes nomeados em 5 camadas (`dominio/`, `aplicacao/`, `aplicacao/portas/`, `adaptadores/`, `interface/`) | `components.md` |
| Regra de import por camada, verificável por inspeção estática; `__main__` é o único ponto autorizado a atravessar tudo | `component-dependency.md` §1 |
| 14 histórias na linha fina; 5 adiadas (US-07, US-10, US-11, US-12, US-18); 4 já fora | `stories.md` v2, FOR-14 |
| 5 dívidas técnicas com unidade destino já indicada por componente (TD-01, TD-02, TD-03, TD-04, TD-11) | `application-design.md` §5 |
| Infrastructure Design é SKIP; não há deploy, servidor nem nuvem nesta iteração | `execution-plan.md` v2 |
| Profundidade comprehensive para Functional Design, NFR Requirements e NFR Design **por unidade** | `execution-plan.md` §Decisões de profundidade |
| Extensões: `security-baseline` habilitada, `property-based-testing` habilitada (Full), `resiliency-baseline` desabilitada | `aidlc-state.md` §Extension Configuration |

### A sequência de 11 passos do plano aprovado **não** é a definição das unidades

O plano de execução v2 (§Sequência recomendada) lista 11 passos e diz textualmente: *"A divisão
acima é sequência de dependências, não a definição final das unidades. Units Generation decidirá os
limites e o mapa história-unidade após Application Design."* É exatamente o que este documento faz.

### Estado atual do código (brownfield)

```
FishingRod/
  Ambiente/     agente.py, ambiente.py, memoria.py, sessao.py
  model/        comando.py, mensagem.py
  cli.py        (fora de garantias — FOR-11)
  tui.py        (protótipo atual)
  testes-de-aprendizado/  spike_claudeSDK.py, teste-dict.py
```

Não existe `pyproject.toml`, `uv.lock`, `src/`, nem runner de testes. ESC-15 decidiu scaffolding com
`uv` e layout `src/`. Isso torna as perguntas de organização de código (Q8, Q9) reais, e não
formalidade — apesar de o projeto ser brownfield, o layout de destino ainda não existe.

---

## 1.1 Respostas do usuário aos pontos abertos de Application Design §7

Escritas diretamente em `application-design/application-design.md` §7 em 2026-08-25, depois da
aprovação do estágio. **Três dos cinco pontos foram respondidos** (1, 3 e 5); os pontos 2 e 4
ficaram em branco.

| Ponto | Resposta | O que muda |
|---|---|---|
| **1** — `propor_entidade` vs US-10 adiada | **Incluir.** É tool do bibliotecário, "é o agente bibliotecário que cria entidades e propriedades na wiki e todos os processos relacionados à wiki"; propor-antes-de-escrever já agrega valor mesmo simples | **Confirma o desenho, sem mudança.** Reforça a Q6 (o único caminho de escrita na wiki é o bibliotecário) |
| **2** — Catálogo local de ambientes | **Sem resposta** | Continua aberto → **Q10** |
| **3** — Qualidade da tool `buscar` | Busca "sempre começa através do `index.md`": o índice tem entidades + lista de propriedades **com descrição do conteúdo**, e o agente lê o índice e depois lê as páginas que encontrou | **Contradiz `components.md` §5.4**, que diz que `buscar` "pode usar `ripgrep` confinado à raiz". A descrição do usuário não precisa de `ripgrep` — precisa de `ler`. E promove o `index.md` de navegação a **mecanismo de recuperação**, o que muda o critério de aceite da unidade de wiki → **Q13** |
| **4** — Conclusão de etapa por agente | **Sem resposta** | Fica como desenhado (confirmação do usuário; regra fina em Functional Design). Nada a decidir aqui |
| **5** — Orquestrador acionando ações do catálogo | **Decidido em princípio**: o orquestrador é "o agente principal do software" e recebe as ações como ferramentas — via função-como-tool **ou** via MCP próprio (mecanismo não escolhido). Novo conceito declarado: **escopo de ferramentas por tipo de agente** — "o orquestrador pode mais e os outros tipos de agentes vão ser limitados pelo seu escopo de trabalho" | **Aumenta o escopo desta iteração.** A Q10 original (que oferecia "nenhum dos dois entra") ficou obsoleta e foi reescrita. Desdobra em → **Q11** (mecanismo), **Q12** (onde mora a capacidade), **Q14** (consequência de segurança) |

### O que a resposta 5 **não** exige redesenhar

O tipo `Agente` já tem `lista de ferramentas permitidas` e `papel` (`ORQUESTRADOR | SUB_AGENTE`)
— `components.md` §2.9. Então "orquestrador pode mais" já tem onde morar: é dado de configuração
do agente, não código condicional. E `component-dependency.md` §3.5 já descreve o padrão de
exposição de tools in-process (medido pelo spike: `create_sdk_mcp_server`), montado pelo
`AdaptadorSessaoClaude` na abertura da sessão. A resposta 5 **instancia** mecanismos que já
existem no desenho; não os substitui.

### O que a resposta 5 muda de fato

1. **US-17 muda de caráter.** `services.md` §7 dizia que as 14 histórias "não exigem que o
   orquestrador crie etapas de forma autônoma". Com ações como ferramentas, "descobrir etapas
   conversando" passa a ser o agente chamando `criar_etapa`, não o usuário digitando `/criar-etapa`
   depois da conversa. Isso é mais fiel à história, e é mais escopo.
2. **Aparece uma capacidade compartilhada**: "expor um conjunto de funções como ferramentas a uma
   sessão, respeitando o escopo do agente". Ela tem **dois** consumidores nesta iteração
   (`FerramentasWiki` para o bibliotecário, `CatalogoDeAcoes` para o orquestrador). Duas unidades
   diferentes precisando da mesma coisa é exatamente o tipo de fato que decide limite de unidade
   → Q12.
3. **A emenda precisa voltar para os artefatos aprovados.** `components.md` §3.1/§5.4 e
   `services.md` §7 hoje dizem coisas que as respostas 3 e 5 contradizem. A correção está na §4
   deste plano como passo da Parte 2, para não editar artefato aprovado antes de as perguntas
   fecharem.

---

## 2. Decomposição **candidata** — base concreta para as perguntas, não decisão

Apresentada para que as perguntas da §3 tenham referência concreta. **Sujeita integralmente às
respostas**; se a Q1 ou a Q2 mudarem de forma, esta tabela é reescrita na Parte 2.

| # | Unidade candidata | Componentes | Histórias | Dívidas |
|---|---|---|---|---|
| U0 | `fundacao` | `pyproject.toml`, `uv.lock`, layout `src/fishingrod/`, runner de testes | nenhuma | — |
| U1 | `dominio` | `Identidade`, `Ambiente`, `Frente`, `Tarefa`, `Chat`, `Etapa`, `Memoria`, `RaizWiki`, `Agente` (config) | US-04, e a parte de domínio de US-15/US-16 | TD-03 |
| U2 | `persistencia` | `PortaPersistencia`, `RepositorioSQLite` | US-05, US-06 (armazenamento) | TD-04 |
| U3 | `sessao` | `PortaSessao`, `AdaptadorSessaoClaude` | US-01, US-02, US-03 (adaptador) | TD-01, TD-02 |
| U4 | `conversa` | `ServicoConversa` | US-01, US-03, US-06 | — |
| U5 | `acoes` | `CatalogoDeAcoes`, `ParserDeComando`, `ServicoDeAmbiente` | US-15, US-16, US-17, US-19 | TD-11 |
| U6 | `wiki` | `PortaWiki`, `AdaptadorWikiFilesystem`, `EsquemaWiki` | US-08, US-09 | — |
| U7 | `bibliotecario` | `ServicoBibliotecario`, `FerramentasWiki` (MCP in-process) | US-13, US-14 | — |
| U8 | `interface` | `FishingRodTUI`, `ComposicaoRoot` (`__main__`) | superfície de todas as 14 | — |
| U? | `ferramentas-de-agente` (candidata nova, ver §1.1 e Q12) | exposição de funções como tools a uma sessão + escopo por `Agente.ferramentas` | atravessa US-13/US-14 (wiki) e US-17/US-19 (catálogo) | — |

**Custo que essa granularidade implica** (declarado antes de você escolher): profundidade
comprehensive significa que cada unidade percorre Functional Design → NFR Requirements → NFR
Design → Code Generation, e **cada um desses estágios tem portão de aprovação**. Nove unidades são
da ordem de 36 portões de aprovação seus. Quatro unidades, da ordem de 16.

---

## 3. Perguntas

### Q1 — Granularidade: quantas unidades?

Cada opção agrupa os mesmos 18 componentes de forma diferente.

A) **9 unidades finas**, como na tabela da §2 (fundação, domínio, persistência, sessão, conversa,
   ações, wiki, bibliotecário, interface). Cada portão revisa pouca coisa; o plano de Code
   Generation de cada unidade é pequeno e fácil de auditar. Custo: ~36 portões de aprovação.

B) **6 unidades**: `fundacao+dominio`, `persistencia`, `sessao+conversa`, `acoes`,
   `wiki+bibliotecario`, `interface+composicao`. Agrupa porta com seu consumidor natural (a porta de
   sessão sem o serviço de conversa é contrato sem cliente). Custo: ~24 portões.

C) **4 unidades grossas**: `fundacao+dominio+persistencia`, `conversa` (sessão + serviço),
   `wiki+bibliotecario`, `interface+acoes+composicao`. Custo: ~16 portões. Risco real: planos de
   Code Generation grandes, onde é mais fácil eu desviar do combinado sem que apareça na revisão.

X) Other (descreva depois da tag `[Answer]:`)

[Answer]: A

---

### Q2 — Camada horizontal ou fatia vertical? (a pergunta mais consequente deste estágio)

A decomposição candidata da §2 é **horizontal**: cada unidade é uma camada ou um substrato. Isso
herda a sequência de dependências do plano aprovado, mas tem uma consequência que precisa estar
explícita antes de você escolher: **nenhuma história fica demonstrável na tela até U8** — a
verificação até lá é por teste automatizado, não por uso.

A) **Horizontal** (como a §2). Vantagem: contratos estáveis antes de qualquer consumidor; nenhuma
   unidade revisita arquivo de outra; combina com a regra de import por camada. Desvantagem
   honesta: concentra o risco de integração no fim, e você só vê o software funcionando na última
   unidade.

B) **Vertical por capacidade** (ex.: unidade "conversar" atravessando domínio + persistência +
   sessão + TUI; unidade "wiki" atravessando domínio + filesystem + TUI). Vantagem: a primeira
   unidade já é demonstrável de ponta a ponta. Desvantagem honesta: várias unidades escrevem nos
   mesmos arquivos (`FishingRodTUI`, `__main__`, `PortaPersistencia`), o que quebra a premissa de
   unidades disjuntas e faz cada unidade posterior editar código que uma anterior já entregou e
   aprovou.

C) **Híbrido**: fundação + domínio + as três portas (contratos) como unidades horizontais
   primeiro; depois fatias verticais por capacidade, cada uma crescendo a sua parte da TUI.
   Vantagem: contrato estável e demonstrabilidade cedo. Desvantagem: a TUI passa a ser tocada por
   3–4 unidades, e o critério "esta unidade está pronta" fica mais difícil de escrever.

X) Other (descreva depois da tag `[Answer]:`)

[Answer]: A

---

### Q3 — A fundação (`uv`, `pyproject.toml`, layout `src/`, runner de testes) é unidade?

Ela não carrega nenhuma história, e a definição da regra diz que unidade de trabalho é *"um
agrupamento lógico de histórias"*. Uma unidade com zero histórias é uma esticada na definição.

A) **Unidade própria** (U0), com o loop de Construction reduzido ao que se aplica (Functional
   Design provavelmente N/A, NFR Requirements sim — RNF-01, lockfile, `exclude-newer`).

B) **Primeiro passo da primeira unidade de código** (a que a Q1/Q2 puser em primeiro lugar), sem
   ser unidade separada.

C) **Executar já, agora, fora do loop de unidades**, porque é passo mecânico sem decisão de
   arquitetura em jogo, e o plano aprovado diz que hoje custa pouco e depois custa caro.

X) Other (descreva depois da tag `[Answer]:`)

[Answer]: C

---

### Q4 — Como uma unidade prova que está pronta antes de existir interface?

Consequência direta da Q2. Se a decomposição for horizontal, U1 a U7 fecham sem tela.

A) **Só testes automatizados** (exemplo + property-based, conforme `property-based-testing` Full).
   Nada interativo até a unidade de interface.

B) **Testes + um roteiro/harness descartável por unidade** (ex.: script que cria ambiente, mata o
   processo, reabre e imprime a estrutura — CS-01 verificável sem TUI). Custo: código jogado fora
   depois, e a tentação de esse harness virar uma segunda interface não mantida (é exatamente o que
   `cli.py` já é hoje).

C) **Testes + TUI mínima antecipada**: puxar uma casca de interface para o começo e crescê-la. Isso
   contradiz a sequência aprovada no plano v2 (TUI no passo 10) e deve ser escolhido de olhos
   abertos.

X) Other (descreva depois da tag `[Answer]:`)

[Answer]: A

---

### Q5 — Onde mora `ServicoDeAmbiente`?

Ele é o serviço de aplicação central: usa **duas** portas (persistência e wiki), é chamado pelo
`CatalogoDeAcoes` e é quem materializa a wiki na criação do ambiente (`services.md` §2). Ele não
cabe limpo em nenhuma unidade candidata.

A) Junto de `CatalogoDeAcoes` + `ParserDeComando` (unidade `acoes`) — é quem as ações chamam.

B) **Unidade própria** (serviço de aplicação), porque depender de duas portas o torna o ponto de
   integração real do sistema e ele carrega histórias de dois grupos diferentes (US-08/US-09 de
   wiki, US-15/US-16 de estrutura).

C) Junto de domínio + persistência, tratando-o como a fachada de escrita do agregado.

X) Other (descreva depois da tag `[Answer]:`)

[Answer]: B

---

### Q6 — Wiki e bibliotecário: uma unidade ou duas?

Sua resposta ao ponto 1 da §7 reforça esta pergunta: você escreveu que é o bibliotecário que faz
"todos os processos relacionados à wiki".

A) **Duas.** `AdaptadorWikiFilesystem`/`FerramentasWiki` são funções puras, testáveis sem LLM
   (inclusive o confinamento de caminho, que é gate PBT-03); `ServicoBibliotecario` depende de
   sessão viva e de julgamento em prompt, que não é testável de forma determinística. Separar
   mantém o gate de segurança dentro de uma unidade 100% determinística.

B) **Uma.** O adaptador de wiki sem o bibliotecário é quase contrato sem cliente: o único caminho
   de **escrita por agente** é a proposta do bibliotecário (decisão 9A/13A), então fechar a unidade
   de wiki sozinha significa aprovar código que quase ninguém chama ainda.

**Fato que corrige o "quase"** (não estava explícito antes): a wiki tem **um segundo cliente que
não é o bibliotecário** — `ServicoDeAmbiente.criar_ambiente` materializa a wiki a partir do
`EsquemaWiki` e chama `renderizar_index` (`services.md` §2, passos 7 e 8), e isso **não** é
proposta de agente, é ação do sistema. Então US-08 e US-09 fecham sem o bibliotecário existir, o
que torna (A) viável de verdade e não só no papel.

X) Other (descreva depois da tag `[Answer]:`)

[Answer]: A - eu me precipitei no momento que eu falei "todos os processos relacionados a wiki". na verdade o bibliotecario simplificando a ideia logica é uma funcionalidade que estamos fazendo para auxiliar o usuario usar a wiki por meio de um agente. 

---

### Q7 — Propriedade e paralelismo das unidades

Contexto real: um dono (você) + eu, e um usuário de validação (João) que não escreve código.
D-ARQ-09 diz que cada usuário roda na própria máquina.

A) **Estritamente sequencial**: uma unidade por vez, você revisando cada portão. Mais lento, mas
   nenhuma chance de duas unidades se atropelarem nos mesmos arquivos.

B) **Sequencial nas dependências, paralelo quando os arquivos forem disjuntos** (ex.: `wiki` e
   `sessao` não se tocam depois que domínio e portas existem). Mais rápido; exige que a matriz de
   dependência da Parte 2 declare quais pares são seguros em paralelo.

C) Outra divisão de propriedade (ex.: João valida alguma unidade antes do portão) — descreva.

X) Other (descreva depois da tag `[Answer]:`)

[Answer]: A

---

### Q8 — Destino do código existente (`Ambiente/`, `model/`, `cli.py`, `tui.py`)

A) **Construir `src/fishingrod/` novo e apagar `Ambiente/` e `model/`** quando a última unidade que
   os substitui fechar. `cli.py`/`tui.py` sobrevivem até a unidade de interface. Período com dois
   conjuntos de código coexistindo, e o risco de alguém (eu, numa sessão futura) editar o arquivo
   morto por engano.

B) **Mover arquivo por arquivo (`git mv`), unidade por unidade**, preservando histórico e mostrando
   diff real. Ressalva honesta: o domínio muda de forma (`Chat` deixa de guardar mensagens, `Agente`
   perde `responder()`), então "mover" pode dar uma ilusão de continuidade sobre o que na prática é
   reescrita.

C) Manter os pacotes atuais e reorganizar só internamente, sem `src/` — **contradiz ESC-15**, listado
   apenas para você poder recusá-lo explicitamente.

X) Other (descreva depois da tag `[Answer]:`)

[Answer]: A

---

### Q9 — Layout de diretórios dentro de `src/fishingrod/`

A) **Camada no topo**: `src/fishingrod/{dominio,aplicacao,adaptadores,interface}/`, com as unidades
   espalhadas dentro. Combina com a regra de import de `component-dependency.md` §1 e torna o
   checklist de conformidade (§7 do mesmo arquivo) verificável por `grep` de diretório.

B) **Unidade no topo**: `src/fishingrod/{unidade}/`, com camadas dentro de cada uma. Combina com a
   decomposição e com o padrão "greenfield multi-unit (monolith)" da regra de Code Generation, mas
   a verificação de violação de camada deixa de ser um `grep` por diretório e passa a exigir
   varredura por AST.

X) Other (descreva depois da tag `[Answer]:`)

[Answer]: A

---

### Q10 — Catálogo local de ambientes (ponto 2 da §7, que você deixou em branco)

Hoje existe de forma degenerada: uma linha `ambiente` no SQLite local, sempre modo local, sem
tabela nem componente dedicado. Sua ressalva na Pergunta D de Application Design foi *"para essa
iteração vamos focar no local, single-user, com o meu usuário conseguindo criar um ambiente que
salva localmente"* — o que sugere (A), mas não decide entre um e vários ambientes.

A) **Fica degenerado**: um ambiente por instalação, nenhum componente de catálogo, nenhuma unidade.
   Se o usuário quiser um segundo ambiente, não dá nesta iteração.

B) **Vários ambientes na mesma instalação, sem unidade própria**: é só uma tabela com N linhas e
   uma tela de seleção na TUI. Custo baixo, mas cria a pergunta "qual ambiente está ativo" em todo
   o resto do sistema.

C) **Unidade/componente próprio de catálogo de ambientes**, preparando o modo compartilhado do
   futuro. Escopo maior sem história que o exija nesta iteração.

X) Other (descreva depois da tag `[Answer]:`)

[Answer]: B - vou explicar como eu vejo isso funcionando. eu vejo isso funcionando da seguinte forma, o usuario faz a instalcao, tem uma tela de inicio, essa tela de inicio o usaurio conseguir criar um novo ambiente. nessa primeira versao na hora que o usuario for criar um novo ambiente ele vai ter a opcao de criar localmente, quando essa opcao é acionada é criada um novo registro local desse ambiente salva, e o usuario poderia criar novos, pois seria so mais uma linha no SQLite . em uma proxima versao poderia ser implementado o modo compartilhado, onde o usuario poderia criar um ambiente compartilhado, e outros usuarios poderiam se juntar a esse ambiente e esse ambiente seria salvo em um servidor, mas isso nao esta incluso para agora, eu expliquei a ideia apenas para demostrar como seria o fluxo de criacao de um novo ambiente e como isso se conecta ao salvamento local.

---

### Q11 — Mecanismo de exposição das ações do catálogo ao orquestrador

Sua resposta ao ponto 5 diz que será "ou passar como uma função como uma ferramenta ou criar um MCP
para dar para o orquestrador", e que você ainda não escolheu. Fato relevante: o spike já mediu
`create_sdk_mcp_server` **in-process** — ou seja, no SDK do Claude, "função como ferramenta" e "MCP
in-process" acabam sendo a mesma coisa por baixo (despacho de função no mesmo processo, sem
serialização real). A diferença prática é de forma, não de arquitetura.

A) **Mesmo padrão da wiki**: MCP in-process, um servidor por conjunto de ferramentas (um para wiki,
   um para catálogo). Um só mecanismo no sistema; o `allowed_tools` de cada `Agente` decide quem vê
   o quê. É o que o desenho aprovado já descreve em `component-dependency.md` §3.5.

B) **Função-como-tool direto** para o catálogo (sem embrulhar num servidor MCP) e MCP só para a
   wiki. Menos indireção onde não precisa, ao custo de dois mecanismos coexistindo.

C) **Não decidir aqui**: registrar como decisão de Functional Design da unidade que ficar dona da
   capacidade. Units Generation só garante que a capacidade tem dono e critério de aceite.

X) Other (descreva depois da tag `[Answer]:`)

[Answer]: A

---

### Q12 — Onde mora a capacidade "expor ferramentas a uma sessão, respeitando o escopo do agente"?

Independente da Q11: com a sua resposta ao ponto 5, essa capacidade passa a ter **dois** consumidores
(`FerramentasWiki` e `CatalogoDeAcoes`). Quem for dono dela precisa entregar também o escopo por
agente (`Agente.ferramentas` + `papel`), que é a parte que faz "o orquestrador pode mais" ser dado
e não `if`.

A) **Dentro da unidade de sessão** (U3), porque é o `AdaptadorSessaoClaude` que monta
   `mcp_servers`/`allowed_tools`/`tools=[]` ao abrir a sessão. Vantagem: um único lugar sabe
   configurar sessão. Desvantagem: a unidade de sessão passa a ter que existir antes de wiki e de
   ações, e fica maior.

B) **Unidade própria** (`ferramentas-de-agente`), consumida por wiki e por ações. Vantagem: o
   escopo de ferramenta por agente — que é controle de segurança, RNF-14 — fica num lugar só, com
   teste próprio. Desvantagem: unidade sem história diretamente atribuída (o mesmo problema da Q3).

C) **Duplicada por consumidor**: a unidade de wiki monta as suas tools, a de ações monta as suas.
   Vantagem: unidades independentes de verdade. Desvantagem honesta: é a opção que mais provavelmente
   produz duas implementações divergentes do mesmo controle de permissão.

X) Other (descreva depois da tag `[Answer]:`)

[Answer]: A - acho que assim seria o melhor forma, pois o Agente vai ser um pacote de dados de configuracoes, se o Agente passado para o AdaptadorSessaoClaude ter as informacoes de quais tools o Agente tem, eu penso que ele saberia como montar o Agente corretamente somente tendo as ferramentas permitidas.

---

### Q13 — A tool `buscar` existe nesta iteração?

Sua resposta ao ponto 3 descreve a busca como: o agente lê o `index.md` (entidades + propriedades
**com descrição do conteúdo**) e depois lê as páginas que encontrou. Isso **não usa** `ripgrep` —
usa `ler`. Mas `components.md` §5.4 hoje diz que `buscar` "pode usar `ripgrep` confinado à raiz", e
você escreveu que "a tool de busca vai ser implementada de forma simples inicialmente". As duas
frases não descrevem a mesma coisa, então preciso da sua escolha.

A) **`buscar` sai desta iteração.** As tools de leitura são `listar` e `ler`; a recuperação é o
   fluxo que você descreveu (índice → páginas). Consequência boa e concreta: nenhuma dependência de
   binário externo (`ripgrep`), o que remove uma superfície de supply chain (SECURITY-10) e um
   caminho de execução de processo externo que precisaria de confinamento próprio.

B) **`buscar` fica, mas trivial**: grep literal em Python (`str.find` sobre os arquivos da raiz),
   sem `ripgrep`, como rede de segurança para quando a descrição do índice não bastar.

C) **`buscar` fica com `ripgrep`**, como está escrito em `components.md` §5.4 hoje.

X) Other (descreva depois da tag `[Answer]:`)

[Answer]: A

~~**Consequência da sua resposta 3 que vale independente desta escolha**: o `index.md` deixa de ser
navegação e passa a ser **o mecanismo de recuperação**. Isso muda o critério de aceite da unidade de
wiki: `renderizar_index` tem que produzir descrição útil por propriedade, e o teste da unidade
passa a ser "um agente encontra o contexto certo lendo só o índice", não apenas "o índice lista
todas as páginas". Vou escrever isso no `unit-of-work.md` da unidade de wiki de qualquer forma.~~

> **CORRIGIDO em 2026-08-25** — o parágrafo riscado acima é meu e estava errado em dois pontos: o
> índice **é** navegação e continua sendo (a sua leitura está certa), e ele já era o ponto de
> entrada obrigatório desde a Decisão 6 de Application Design, então a sua resposta 3 não mudou
> nada nisso. O critério de aceite que eu propus também não presta, porque exige um LLM no laço e
> não é determinístico. Resposta completa e critério refeito em
> `unit-of-work-clarification-questions.md`, Parte A e **CQ1**.

- quero fazer uma observacao aqui. acho que estamos confundindo o caminho sobre a questao da minha resposta 3. vou esclarecer melhor e vemos como tomar a mehor decisao ,quero que vc esclareça o seu entendimento.  
Escrevi alguma coisa errada na minha explicação, porque você disse que o índice deixa de ser a navegação e passa a ser o mecanismo de recuperação.Eu acho que o caminho mais correto é pensar o index como um mecanismo de navegação mesmo. Eu acho que eu devo ter falado alguma coisa errada aqui que me desentendeu diferente. Vou explicar de novo. A ideia do index, ele ser o ponto de entrada ali onde quando a gente começar a fazer uma busca dentro da Wiki pra buscar o contexto, ele começa pelo index. Por quê? Porque o index ele armazena as informações de uma maneira boa para a LLM saber como buscar informações lá dentro. Qual que é essa maneira que ele organiza? Ele organiza em como cada título é uma entidade, como se fosse isso. E dentro de cada título da entidade, tem essa lista das propriedades marcando ali qual que é o nome do arquivo e uma breve descrição. Então eu não entendi como assim ele passa a ser mecanismo de recuperação?
---

### Q14 — Orquestrador com ferramentas de mutação + wiki como entrada não confiável

Esta pergunta existe porque a extensão `security-baseline` está habilitada e a sua resposta ao
ponto 5 mexe numa premissa do desenho aprovado. A decisão 3-bis isolava o contexto: o bibliotecário
lê a wiki (entrada não confiável, RNF-14) e o orquestrador **não tem ferramentas de wiki**. Se agora
o orquestrador ganha ferramentas que **mudam estado** (criar frente, criar tarefa, criar etapa,
concluir etapa), e em algum momento conteúdo da wiki chega ao contexto dele — repassado pelo
bibliotecário ou colado pelo usuário — então texto escrito por terceiro dentro de uma página pode
induzir mutação de estrutura sem você aprovar.

A) **Aceitar o risco nesta iteração** e registrar. Justificativa disponível: single-user, wiki
   escrita pelo próprio usuário via propostas que ele aprovou, e o dano máximo é estrutura errada
   num banco local (reversível). Nenhum controle novo é construído.

B) **Ações mutantes do orquestrador exigem confirmação do usuário** (o mesmo regime de proposta da
   wiki, aplicado ao catálogo). Simétrico e defensável, mas é mais escopo e pode virar fadiga de
   aprovação — o mesmo risco de "proposta virar carimbo" que você já conhece.

C) **Orquestrador só recebe ações de leitura/navegação como ferramenta nesta iteração**; mutação
   continua vindo de `/` e de botão. Menor escopo, mas esvazia parte de US-17 (o agente não cria a
   etapa, só sugere).

D) **Tratar em NFR Requirements da unidade**, não aqui: Units Generation só registra que a unidade
   dona das ações-como-ferramenta carrega este requisito.

X) Other (descreva depois da tag `[Answer]:`)

[Answer]:X - vou explicar a ideia e vai ficar clara a solucao. realmente o orquestrador na minha primeira ideia nao podia usar ferramentas da wiki isso por um motivo de manter um agente dedicado para a escrita na wiki para garantir o formato correto de escrita. ai tem o problema de, e se o usuario quiser pedir para o orquestador criar uma nova entidade na wiki ? isso se resolve com uma nova ferramenta que o orquestrador tera que eu acho que nao comentei ainda mas ja estava no meu radar, o orquestrador vai ser capaz de criar novos chats dentro da sessao para usar agentes , para essa minha pergunta no caso o orquestrador criaria um novo chat do bibliotecario e avisaria algo assim para o usuario no chat do orquestador - "eu <orquestrador> criei um novo chat aqui dentro da sessao com o bibliotecario , eu pedi para ele adicionar essa entidiade que conversamos, o bibliotecario ira pedir uma aprovacao da proposta, aceite no chat do bibliotecario". 

---

## 4. Passos da Parte 2 (Geração) — só executam após as respostas e a aprovação do plano

- [x] Consolidar as respostas das Q1 a Q14 e registrar cada decisão com o motivo — feito em `unit-of-work-clarification-questions.md` (rodada 2, tabela de decisões fechadas; rodada 3 para CQ1–CQ4)
- [x] Analisar as respostas em busca de ambiguidade, contradição e resposta que mistura opções — três rodadas de análise; resultado: 0 contradições entre respostas, 1 tensão letra/observação resolvida em R8, 4 perguntas de acompanhamento (CQ1–CQ4) todas fechadas
      (passo 7 da regra); se houver, gerar `unit-of-work-clarification-questions.md` e **parar**
- [x] Definir as unidades finais conforme a granularidade e o eixo escolhidos (Q1, Q2)
- [x] Gerar `aidlc-docs/inception/application-design/unit-of-work.md` — definição, responsabilidade,
      componentes e critério de conclusão de cada unidade
- [x] Documentar no `unit-of-work.md` a estratégia de organização de código (Q8, Q9) e o destino de
      `Ambiente/`, `model/`, `cli.py` e `tui.py`
- [x] Gerar `aidlc-docs/inception/application-design/unit-of-work-dependency.md` — matriz de
      dependência entre unidades, ordem de execução e, se Q7=B, os pares seguros em paralelo
- [x] Gerar `aidlc-docs/inception/application-design/unit-of-work-story-map.md` — mapa
      história → unidade, com as 14 histórias da linha fina atribuídas
- [x] Verificar que **toda** história da linha fina está em pelo menos uma unidade, e que nenhuma
      história adiada (US-07, US-10, US-11, US-12, US-18) foi atribuída por engano
- [x] Verificar que as 5 dívidas técnicas (TD-01, TD-02, TD-03, TD-04, TD-11) têm unidade destino
      coerente com `application-design.md` §5
- [x] Verificar limites e ausência de ciclo entre unidades
- [x] **Emendar os artefatos aprovados de Application Design** com as consequências das respostas
      3 e 5 da §7 (§1.1 deste plano), marcando o texto substituído em vez de apagá-lo, como foi
      feito na emenda v2 de `requirements.md`: `components.md` §5.4 (escopo de `buscar`, conforme
      Q13), `components.md` §3.1 (o catálogo também é exposto como ferramentas ao orquestrador),
      `components.md` §2.9 (escopo de ferramenta por `papel` de agente), `services.md` §7 (deixa de
      ser "não decidido" e passa a apontar para a decisão da Q11/Q12), e o critério de aceite de
      `renderizar_index` em `components.md` §5.3
- [x] Registrar a conformidade das extensões habilitadas neste estágio (ver §6)
- [x] Atualizar `aidlc-state.md` e `audit.md`; apresentar a mensagem de conclusão e aguardar
      aprovação explícita antes de CONSTRUCTION

---

## 5. Critérios de conclusão deste estágio

- [x] As 14 perguntas respondidas, sem ambiguidade pendente — **mais** CQ1=A, CQ2=A+parâmetro, CQ3=A, CQ4=A. Total: 18/18 decisões fechadas
- [x] Os três artefatos obrigatórios criados
- [x] Artefatos de Application Design emendados onde as respostas 3 e 5 da §7 os contradizem
- [x] 14/14 histórias da linha fina mapeadas a unidade
- [x] 5/5 dívidas técnicas com unidade destino
- [x] Grafo de dependência entre unidades acíclico e com ordem de execução declarada
- [x] Estratégia de organização de código escrita, incluindo o destino do código atual
- [x] Aprovação explícita do usuário antes de entrar em CONSTRUCTION

---

## 6. Conformidade das extensões habilitadas — avaliação neste estágio

| Extensão | Aplicável a Units Generation? | Como é atendida |
|---|---|---|
| `security-baseline` | Parcialmente | Este estágio não produz código nem configuração de rede, então as regras de HTTP/IAM/load balancer/CORS são **N/A**. O que se aplica é **rastreabilidade**: o confinamento de caminho (RNF-10, SECURITY-05) e a wiki como entrada não confiável (RNF-14) precisam ficar dentro de uma unidade nomeada com gate próprio — é o que a Q6 decide. SECURITY-10 (dependências travadas) precisa de unidade destino — é o que a Q3 decide, e a Q13 pode remover `ripgrep` da lista de dependências externas. **Achado novo desta rodada, não bloqueante mas registrado**: a resposta 5 da §7 (orquestrador com ferramentas de mutação) enfraquece o isolamento de contexto que sustentava RNF-14 no desenho aprovado — a Q14 existe para você decidir se aceita, restringe ou empurra para NFR Requirements. Não trato isso como conformidade resolvida até a Q14 ser respondida. |
| `property-based-testing` (Full) | Sim | PBT-01 exige que as propriedades identificadas em Application Design tenham dono: round-trip de serialização do `Ambiente` (unidade de persistência) e "nenhum caminho gerado escapa da raiz da wiki" (unidade de wiki). A Parte 2 registra essa atribuição no `unit-of-work.md`. A especificação formal (estratégias Hypothesis, invariantes exatos) continua sendo de Functional Design/NFR Requirements por unidade. |
| `resiliency-baseline` | **N/A** | Desabilitada por decisão de 2026-08-17 registrada em `aidlc-state.md`. Não enforçada. |
