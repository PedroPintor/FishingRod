# Units Generation — Clarificação (rodada 2)

**Estágio:** INCEPTION — Units Generation, Parte 1 · **Data:** 2026-08-25
**Base:** `unit-of-work-plan.md` com 14/14 tags `[Answer]:` preenchidas
**Regra aplicada:** `inception/units-generation.md` passos 7 e 8 (análise obrigatória das respostas)

> **Este arquivo tem duas rodadas.** A rodada 2 (Partes A a D) foi respondida em 2026-08-25 e está
> fechada. A **rodada 3 (Partes E e F)**, no fim do arquivo, analisa as respostas de CQ1/CQ2 e traz
> as duas perguntas abertas hoje: **CQ3** e **CQ4**.

## Resultado da análise

| Verificação | Resultado |
|---|---|
| Todas as tags `[Answer]:` preenchidas | **Sim**, 14/14 |
| Contradição entre respostas | **Nenhuma encontrada** |
| Resposta que mistura opções sem critério de decisão | Nenhuma |
| Resposta vaga ("depende", "mais ou menos") | Nenhuma |
| **Pontos que ainda precisam de você** | **2** — CQ1 (aberta por você na Q13) e CQ2 (resíduo da Q14) |
| Consequências resolvidas sem perguntar | 7, declaradas na Parte C para você objetar |

### Decisões registradas como fechadas

| # | Decisão |
|---|---|
| Q1 | **A** — granularidade fina |
| Q2 | **A** — decomposição horizontal por camada/substrato |
| Q3 | **C** — fundação `uv` executada primeiro, fora do loop de unidades (ver R5) |
| Q4 | **A** — verificação por teste automatizado apenas; nada interativo até a unidade de interface |
| Q5 | **B** — `ServicoDeAmbiente` é unidade própria |
| Q6 | **A** — wiki e bibliotecário são unidades separadas; correção sua: *"o bibliotecário [...] é uma funcionalidade que estamos fazendo para auxiliar o usuário usar a wiki por meio de um agente"* |
| Q7 | **A** — estritamente sequencial |
| Q8 | **A** — `src/fishingrod/` novo; `Ambiente/` e `model/` apagados quando a unidade que os substitui fechar |
| Q9 | **A** — camada no topo (`dominio/`, `aplicacao/`, `adaptadores/`, `interface/`) |
| Q10 | **B** — vários ambientes locais na mesma instalação, sem unidade própria; tela de início cria/escolhe ambiente; modo compartilhado fica para versão futura |
| Q11 | **A** — MCP in-process, um servidor por conjunto de ferramentas |
| Q12 | **A** — a capacidade mora na unidade de sessão; `Agente` é pacote de configuração e o `AdaptadorSessaoClaude` monta a sessão a partir das ferramentas permitidas |
| Q13 | **A** — `buscar` sai desta iteração; leitura é `listar` + `ler` |
| Q14 | **X** — o orquestrador **não** ganha ferramentas de wiki; ganha a ferramenta de **criar chats** dentro da tarefa e delega ao bibliotecário, avisando o usuário no chat |

---

# Parte A — Resposta à sua observação na Q13

> *"você disse que o índice deixa de ser a navegação e passa a ser o mecanismo de recuperação [...]
> Eu acho que o caminho mais correto é pensar o index como um mecanismo de navegação mesmo [...]
> Então eu não entendi como assim ele passa a ser mecanismo de recuperação?"*

**Você está certo e minha frase estava errada.** Não em espírito, mas na palavra "deixa de ser" —
ela sugere que algo mudou no seu desenho, e não mudou nada no seu desenho. Deixa eu ser preciso
sobre o que eu quis dizer e onde eu errei.

**O que eu errei.** O índice é navegação, sim, e continua sendo. Ele não "vira" outra coisa. Além
disso, o índice já era o ponto de entrada obrigatório antes da sua resposta 3 — isso foi fechado na
Decisão 6 de Application Design (*"`index.md` como passo obrigatório; hierarquia localiza, links
associam"*). Eu escrevi como se a sua resposta tivesse promovido o índice a alguma coisa nova.
Não promoveu. Ela confirmou o que já estava decidido.

**O que eu quis dizer.** "Recuperação" é o nome técnico para *o que decide quais páginas vão ser
lidas*. Nesse sentido, navegar e recuperar são a mesma operação quando quem navega é o agente —
ele lê o índice, escolhe, e o que ele escolheu é o contexto que vai usar. Eu deveria ter dito isso
em vez de inventar uma distinção.

**O que realmente muda, e é o único ponto que importa.** Não é o nome; é a **ausência de plano B**.
Antes da Q13, o desenho tinha dois caminhos até o conteúdo: o índice (caminho principal) e `buscar`
com grep (rede de segurança para quando a descrição não bastasse). Com Q13=A, sobra um caminho só.
Consequência concreta: **se a descrição de uma propriedade no índice for ruim ou estiver
desatualizada, aquele conteúdo fica invisível para o agente, e não existe grep para salvar.** A
rede de segurança passa a ser humana — você percebe e corrige.

Isso não é argumento contra a sua escolha. Q13=A me parece certo: `ripgrep` era dependência de
binário externo e um caminho de execução de processo que precisaria de confinamento próprio, e o
seu fluxo (índice → páginas) é o que um agente de fato faz bem. Só significa que a unidade de wiki
tem três coisas que passam a ser obrigatórias em vez de desejáveis:

1. toda propriedade tem `descricao` não vazia no frontmatter;
2. o índice é **regenerado a partir do disco**, então uma página criada fora do app aparece nele;
3. o índice nunca é editado por agente — é sempre projeção (isso já era a Decisão 15D).

**E uma autocorreção.** O critério de aceite que eu tinha escrito — *"um agente encontra o contexto
certo lendo só o índice"* — não presta como portão de unidade, porque exige um LLM no laço e é
não determinístico: ele pode falhar por causa do prompt e não por causa da wiki. Escrevi um
critério que eu não sei avaliar. É disso que trata a CQ1.

---

# Parte B — Perguntas

## CQ1 — Critério de aceite do índice, na unidade de wiki

A) **Só determinístico.** O portão verifica: toda entidade e propriedade aparece no índice; nenhuma
   propriedade com descrição vazia; índice regenerado do disco reflete página criada fora do app;
   índice nunca escrito por agente. A qualidade da descrição fica **fora** do portão — é conteúdo,
   não código, e conteúdo é responsabilidade do prompt do bibliotecário e sua.

B) **Determinístico como portão + um teste exploratório com LLM como informação.** O exploratório
   roda, o resultado é registrado, mas não bloqueia a unidade. Custo: um teste que consome
   assinatura e que ninguém sabe se está "passando".

C) **Determinístico + LLM como portão que bloqueia.** Aviso honesto: portão não determinístico
   falha de forma intermitente e, quando falhar, você não vai saber se a culpa é da wiki, do prompt
   ou do modelo do dia.

X) Other (descreva depois da tag `[Answer]:`)

[Answer]: A

---

## CQ2 — Ação que muda estado, acionada pelo agente: executa direto ou pede confirmação?

**Antes da pergunta, o que a sua resposta X resolveu.** Ela é melhor do que qualquer opção que eu
tinha oferecido na Q14: em vez de dar ferramentas de wiki ao orquestrador com salvaguardas, você
**mantém o isolamento intacto** e resolve o caso de uso por delegação — o orquestrador cria um chat
do bibliotecário e avisa você. O bibliotecário continua sendo o único que escreve na wiki, o
formato continua garantido por um agente dedicado, e a aprovação continua acontecendo no lugar
certo. A preocupação central da Q14 (conteúdo de wiki chegando ao contexto de um agente com
ferramentas de mutação) **deixa de existir**, porque o orquestrador continua sem ler a wiki.

**O que sobrou.** O orquestrador passa a ter ferramentas que mudam estado: `criar_frente`,
`criar_tarefa`, `criar_etapa` e agora `criar_chat`. Isso é independente da wiki — vale para
qualquer texto que entre na conversa dele, inclusive um e-mail de cliente que você cole. A pergunta
é só se essas ações executam direto quando quem chama é o agente.

A) **Executa direto.** Single-user, dano local e reversível (criar uma frente errada custa apagar
   uma frente), e pedir confirmação a cada ação recria a fadiga de aprovação que já preocupava no
   regime da wiki.

B) **Sempre pede confirmação** quando o chamador é agente (ação por `/` ou botão continua direta,
   porque aí quem chamou foi você).

C) **Só para ação destrutiva ou irreversível.** Nesta iteração não existe nenhuma — não há excluir
   nem renomear em massa — então hoje é idêntico a (A) na prática, mas deixa a regra escrita para
   quando existir.

X) Other (descreva depois da tag `[Answer]:`)

[Answer]: A - com uma observacao: oq eu penso é que temos que tratar a aprovacao pelo usuario algo como um parametro de ativacao , onde ele pode escolher se quer que aprovacao seja necessaria ou nao. como padrao pode vir ativado a aprovacao necessaria, mas pode ser desativada. quero fazer mais uma observacao de visao que tenho, vc chamou a ferramentas que o orquestrador iria receber de ferramentas que mudam o estado, eu tenho em mente uma maneira melhor de chamarmos isso que vai fazer mais sentido para pensarmos e planejarmos melhor. oque o orquestrador tem como ferramentas (mas nao estou limitando) sao ferramentas que mechem no ambiente como criar frente, tarefa, etapa, chat, etc. e os outros agentes nao teriam essas ferramentas, pois essas ferramentas sao do orquestrador.

---

# Parte C — Reconciliações declaradas (resolvi sem perguntar; objete se discordar)

### R1 — São **10** unidades, não 9; e o número de portões é menor que você pode estar imaginando

Q1=A (granularidade fina) somada a Q5=B (`ServicoDeAmbiente` como unidade própria) dá 10 unidades.
Mas os três estágios de design do CONSTRUCTION são **CONDITIONAL por unidade**, não obrigatórios: a
unidade de domínio (sete dataclasses e duas invariantes) dificilmente justifica NFR Design; a
unidade de fundação não tem Functional Design. Vou declarar no `unit-of-work.md`, unidade por
unidade, quais estágios executam e quais são SKIP **com motivo** — assim você aprova a conta antes
de pagá-la, em vez de descobrir no meio.

### R2 — `criar_chat` como ferramenta não é componente novo

`ServicoDeAmbiente` já lista "criar chat" entre suas responsabilidades (`components.md` §3.3) e
`Chat` já guarda referência ao `Agente` configurado (§2.5). Então a ferramenta que a sua resposta
X descreve é uma ação do catálogo exposta pelo mesmo mecanismo da Q11/Q12. Nada a redesenhar.

### R3 — O orquestrador só pode instanciar agente de uma lista fechada

`criar_chat(agente=X)` com X livre seria escalonamento de privilégio: o orquestrador criaria um
agente com ferramentas que ele mesmo não tem. Nesta iteração existem duas instâncias de `Agente` —
orquestrador e bibliotecário (`components.md` §2.9, rod-maker sem instância) — então a lista é
`{bibliotecário}`, e ela é dado de configuração, não `if` no código. Registro como invariante da
unidade de ações.

### R4 — Q11=A + Q12=A **não** cria dependência da unidade de conversa para a unidade de ações

Esse era o risco escondido: se `ServicoConversa` precisasse montar a lista de ferramentas do
orquestrador, ele passaria a importar `CatalogoDeAcoes`, e a matriz de `component-dependency.md`
ganharia uma seta nova bem no meio de duas unidades que Q2=A quer independentes.

Sua justificativa na Q12 já resolve isso e eu só estou tornando explícito: `Agente` carrega os
**nomes** das ferramentas permitidas; o composition root monta um registro nome → função (tools da
wiki e ações do catálogo juntas); `AdaptadorSessaoClaude` recebe esse registro e resolve os nomes ao
abrir a sessão. Ninguém além do `__main__` conhece os dois lados — exatamente o papel dele.

### R5 — Q3=C vira "passo 0 do CONSTRUCTION", executado imediatamente

Sua intenção ("é mecânico, vem primeiro, fora do loop de unidades") fica preservada inteira. A única
diferença é o rótulo: o INCEPTION não tem estágio onde escrever código, e eu prefiro não abrir
exceção sem você saber. Na prática, é a primeira coisa que acontece assim que este estágio for
aprovado. **Se você quiser literalmente agora, antes da aprovação, é uma frase sua e eu faço.**

### R6 — Sua correção na Q6 tem uma consequência boa que vale registrar

Você corrigiu: o bibliotecário é auxílio para o usuário usar a wiki, não dono dela. Então editar a
wiki por fora (no seu editor, direto no markdown) é **esperado**, não anomalia. O desenho já
aguenta, porque `renderizar_index` é projeção do disco e não estado interno (Decisão 15D) — uma
página que você criou na mão aparece no índice na próxima renderização. Isso é o que dá à unidade
de wiki um critério de aceite que não depende do bibliotecário existir, que é justamente o que
Q6=A precisa para ser verdade e não só arrumação.

### R7 — Q10=B não exige componente nem unidade nova

`RaizWiki` já é `dados:wikis/<id_ambiente>` e `carregar_ambiente(id)` já recebe identidade — o
desenho já é multi-ambiente sem saber. Vários ambientes locais = N linhas na tabela + tela de
seleção. O que entra de escopo é a **tela de início** (criar ou escolher ambiente), que atribuo à
unidade de interface. O modo compartilhado que você descreveu fica registrado como direção futura,
sem nada construído agora.

---

# Parte D — Emendas aos artefatos aprovados de Application Design

Executadas na Parte 2, depois de CQ1 e CQ2, marcando o texto substituído em vez de apagá-lo (mesmo
padrão da emenda v2 de `requirements.md`):

| Artefato | Trecho | Motivo |
|---|---|---|
| `components.md` §4.3 | `PortaWiki` lista `buscar` na assinatura conceitual | Q13=A |
| `components.md` §5.4 | `FerramentasWiki`: `buscar` "pode usar `ripgrep` confinado à raiz" | Q13=A |
| `components.md` §5.3 | critério de `renderizar_index` | Q13 + CQ1 + R6 |
| `components.md` §3.1 | `CatalogoDeAcoes` ganha `criar_chat` e passa a ser exposto como ferramentas ao orquestrador | Q14=X, R2, R3 |
| `components.md` §2.9 | `Agente` carrega nomes de ferramentas resolvidos por registro do composition root | Q12=A, R4 |
| `component-methods.md` | `PortaSessao.abrir` e construtor do `AdaptadorSessaoClaude` recebem o registro de ferramentas | R4 |
| `services.md` §7 | deixa de ser "não decidido em Application Design" e aponta para Q11/Q12/Q14 | Q11, Q12, Q14 |
| `application-design.md` §7 | os cinco pontos deixam de ser "abertos": 1, 3 e 5 respondidos por você; 2 fechado pela Q10=B; 4 permanece como desenhado | esta rodada |
| `components.md` §2.2 | `Ambiente` ganha o parâmetro de aprovação de ação por agente | CQ2, R8, CQ3 |
| `components.md` §3.1 + `components.md` §5.4 | vocabulário: "ferramentas de ambiente" e "ferramentas de wiki" como as duas famílias nomeadas | R9 |
| `components.md` §5.3 | critério determinístico do índice (sem LLM no portão) | CQ1=A |

---

# Parte E — Rodada 3: análise das respostas CQ1 e CQ2

**Data:** 2026-08-25 · **Regra aplicada:** `inception/units-generation.md` passos 7 e 8 (a análise
obrigatória vale para cada rodada de respostas, não só para a primeira)

| Verificação | Resultado |
|---|---|
| CQ1 e CQ2 respondidas | **Sim**, 2/2 |
| Resposta vaga | Nenhuma |
| **Tensão entre a letra escolhida e a observação** | **Uma**, na CQ2 — resolvida em R8, sem nova pergunta |
| Conceito novo trazido por você | **Um** — "ferramentas de ambiente" (R9) |
| Pontos que ainda precisam de você | **2** — CQ3 e CQ4, ambas geradas pela sua observação da CQ2, ambas com recomendação minha declarada |

### Decisões registradas como fechadas nesta rodada

| # | Decisão |
|---|---|
| CQ1 | **A** — portão da unidade de wiki é só determinístico; qualidade de descrição fica fora do portão |
| CQ2 | **A + parâmetro** — não existe confirmação embutida no código; existe um parâmetro de aprovação, ligado por padrão, que você pode desligar (ver R8) |

---

## R8 — A letra A e a sua observação dizem coisas diferentes; registrei a observação como a decisão

Escrito com franqueza porque a diferença é material: a opção (A) que você marcou dizia *"executa
direto"*, e a sua observação diz *"como padrão pode vir ativado a aprovação necessária"*. Lidas ao
pé da letra, uma é o oposto da outra. **Não estou tratando isso como erro seu** — a leitura que faz
sentido é a que junta as duas, e é a que registro:

> O comportamento **não** é decidido dentro do código de cada ação. É um parâmetro do sistema.
> Com o parâmetro ligado (padrão de fábrica), uma ação acionada por agente pede sua confirmação.
> Com o parâmetro desligado, ela executa direto — e aí vale exatamente o que (A) descrevia.

Ou seja: (A) deixou de ser *o comportamento* e virou *um dos dois estados do parâmetro*, o estado
não-padrão.

**A consequência que isso tem, e que nem (A) nem (B) sozinhas teriam.** As duas opções originais
eram baratas: (A) não constrói nada, (B) constrói um fluxo fixo. O parâmetro custa **as duas
coisas**: o fluxo de confirmação precisa existir nesta iteração (senão o padrão de fábrica não tem
como funcionar) **e** precisa existir o lugar onde o parâmetro mora e a tela onde você o desliga.
Isso é escopo real acrescentado à unidade de interface e a mais uma unidade — qual, é a CQ3.

Não considero isso argumento contra a sua decisão. Considero argumento a favor: o padrão ligado é o
que protege contra a fadiga de aprovação virar carimbo, porque quem desliga é você depois de
confiar, não o desenho antes de você ver funcionar.

---

## R9 — Adoto "ferramentas de ambiente"; e o nome resolve uma coisa que o meu nome não resolvia

Sua observação: *"o que o orquestrador tem como ferramentas [...] são ferramentas que mexem no
ambiente como criar frente, tarefa, etapa, chat, etc. e os outros agentes não teriam essas
ferramentas, pois essas ferramentas são do orquestrador."*

**Adotado como vocabulário oficial do projeto a partir daqui**: `ferramentas de ambiente`. Passa a
valer nos três artefatos da Parte 2 e nas emendas da Parte D.

**Por que o seu nome é melhor que o meu, tecnicamente.** "Ferramenta que muda estado" classifica
por *efeito colateral*; "ferramenta de ambiente" classifica por *objeto de domínio que a ferramenta
toca*. A segunda classificação é a que coincide com o limite de unidade — e por isso é a que serve
para planejar:

| Família | Toca | Quem tem | Unidade dona |
|---|---|---|---|
| **ferramentas de ambiente** | `Ambiente`, `Frente`, `Tarefa`, `Etapa`, `Chat` | orquestrador | unidade de ações |
| **ferramentas de wiki** | páginas e índice da wiki | bibliotecário | unidade de wiki / bibliotecário |

**Uma correção que o nome novo obriga, e que eu preciso declarar em vez de deixar passar.** As duas
famílias mudam estado — `propor_entidade` e a escrita de página do bibliotecário mudam estado
também. Então "ferramentas de ambiente" **não é sinônimo** de "ferramentas que mudam estado"; é um
subconjunto. Isso importa porque tudo que eu escrevi na CQ2 sobre risco de mutação sem aprovação
vale para as duas famílias, não só para a do orquestrador — e é justamente por isso que o parâmetro
da R8 precisa valer para as duas (a aprovação da proposta do bibliotecário, que já existia no
desenho pela Decisão 15, passa a ser o mesmo mecanismo, não um segundo mecanismo paralelo).

**Corolário de graça**: a R3 (lista fechada de agentes que o orquestrador pode instanciar) deixa de
ser regra avulsa e vira consequência do vocabulário — `criar_chat` é ferramenta de ambiente, e
ferramenta de ambiente é do orquestrador; se um sub-agente pudesse criar chat, ele estaria segurando
uma ferramenta de ambiente, o que a sua frase proíbe.

---

## R10 — O invariante "só o orquestrador tem ferramenta de ambiente" é testável sem LLM

Registro como critério de aceite determinístico, na mesma linha da CQ1=A: percorrer as instâncias de
`Agente` configuradas e verificar que nenhuma com `papel = SUB_AGENTE` carrega nome de ferramenta da
família ambiente. É teste de configuração, roda em milissegundos, não precisa de sessão nem de
assinatura. Fica na unidade dona da configuração de agentes (unidade de sessão, por Q12=A).

---

# Parte F — Perguntas da rodada 3

## CQ3 — Onde mora o parâmetro de aprovação?

Pergunto porque a resposta decide **qual unidade é dona do campo**, e isso é literalmente o produto
deste estágio. Consequência de cada opção declarada; a minha recomendação está marcada.

A) **Um campo em `Ambiente`** (`aprovacao_de_agente_obrigatoria: bool = True`). Vale para o ambiente
   inteiro, vale para as duas famílias de ferramenta, viaja junto no documento que o repositório já
   salva (`components.md` §2.2 — `Ambiente` é o agregado serializado), e não cria tabela nem arquivo
   de configuração novo. Dona: **unidade de domínio**. Custo: para ligar/desligar por agente no
   futuro, o campo vira estrutura em vez de `bool` — mas isso é migração de um documento JSON, não
   de esquema relacional. ← **minha recomendação**

B) **Um campo em `Agente`** (cada agente tem o seu). Mais granular desde o começo — "confio no
   bibliotecário, não confio no orquestrador". Custo: `Agente` é **configuração imutável de código**
   nesta iteração (`components.md` §2.9), não é dado editável pelo usuário; então desligar pela tela
   exigiria antes tornar `Agente` persistido, o que é escopo que hoje não existe.

C) **Um campo por ação, no `CatalogoDeAcoes`** (cada ação declara se exige aprovação). Máxima
   granularidade e casa com a opção (C) da CQ2, que você não escolheu. Custo: 13 decisões em vez de
   uma, e nenhuma delas você pediu.

D) **Arquivo de configuração da aplicação**, fora do domínio. Custo: é o único que cria um conceito
   novo (config de app) que não existe em lugar nenhum do desenho hoje.

X) Other (descreva depois da tag `[Answer]:`)

[Answer]: A - vamos fazer a A por ser mais simples e ja dar a possibilidade para o usuario. assim da para testar e ver se o usuario usaria essa funcionalidade e ja grega valor.

---

## CQ4 — O fluxo de confirmação é construído nesta iteração?

A R8 mostrou que o padrão ligado exige o fluxo existir. Confirmo com você porque é escopo que
nenhuma das 14 histórias da linha fina pede explicitamente.

A) **Sim, construído nesta iteração**, na unidade de interface: quando uma ferramenta de ambiente é
   chamada por agente e o parâmetro está ligado, a TUI mostra a ação e os parâmetros e espera seu
   sim/não. O mesmo mecanismo atende a aprovação de proposta do bibliotecário (R9), então não são
   dois fluxos, é um. ← **minha recomendação**, porque sem ele o padrão de fábrica não funciona e
   você entregaria uma iteração cujo padrão é o estado que você não escolheu

B) **Não; nesta iteração o parâmetro nasce desligado** e o fluxo de confirmação vira dívida técnica
   com unidade destino nomeada. Honesto sobre o custo: entrega mais rápida, mas o padrão de fábrica
   fica sendo "executa direto", que é o oposto do que você pediu.

C) **Sim, mas só para as ferramentas de ambiente**; a aprovação de proposta do bibliotecário
   continua sendo o fluxo próprio dela, como já estava desenhado. Custo: dois caminhos de aprovação
   na tela, que tendem a divergir em comportamento com o tempo.

X) Other (descreva depois da tag `[Answer]:`)

[Answer]: A

---

# Parte G — Fecho da rodada 3

**Data:** 2026-08-25 · CQ3 e CQ4 respondidas · **Parte 1 de Units Generation encerrada**

| Verificação (passos 7 e 8) | Resultado |
|---|---|
| CQ3 e CQ4 respondidas | **Sim**, 2/2 |
| Resposta vaga, contraditória ou que mistura opções | **Nenhuma** |
| Perguntas de acompanhamento novas | **Nenhuma** — nada nas duas respostas abre decisão nova |
| **Decisões fechadas no estágio inteiro** | **18** (Q1–Q14, CQ1–CQ4) |

## Decisões da rodada 3

| # | Decisão | Motivo registrado |
|---|---|---|
| CQ3 | **A** — `Ambiente` ganha o campo do parâmetro de aprovação | *"vamos fazer a A por ser mais simples e já dar a possibilidade para o usuário. assim dá para testar e ver se o usuário usaria essa funcionalidade e já agrega valor."* |
| CQ4 | **A** — o fluxo de confirmação é construído nesta iteração, um só fluxo para as duas famílias de ferramenta | — |

## O que estas duas respostas fixam para a Parte 2

1. **Unidade de domínio** ganha o campo `aprovacao_de_agente_obrigatoria` (padrão ligado) em
   `Ambiente`, e ele viaja no documento que o repositório já serializa — sem tabela nova, sem
   arquivo de configuração novo, sem componente novo.
2. **Unidade de persistência** herda o campo de graça, mas ganha uma obrigação: um `Ambiente` salvo
   antes do campo existir precisa carregar com o padrão ligado, e não quebrar. Registro isso como
   critério de aceite da unidade de persistência, junto com a propriedade de round-trip que a
   extensão `property-based-testing` já exigia.
3. **Unidade de interface** ganha o fluxo de confirmação — mostra ação e parâmetros, espera sim/não —
   e a tela onde o parâmetro é desligado. **Um fluxo, não dois**: a aprovação de proposta do
   bibliotecário (Decisão 15) passa pelo mesmo caminho, por CQ4=A somada à ressalva da R9.
4. **Unidade de ações** e **unidade de bibliotecário** passam a ter, cada uma, o mesmo ponto de
   consulta ao parâmetro antes de executar uma ferramenta acionada por agente. Isso **não** cria
   dependência entre elas: as duas leem um campo do `Ambiente`, que ambas já conhecem por serem
   camada de aplicação sobre o mesmo agregado.
5. **Rastreabilidade honesta**: nenhuma das 14 histórias da linha fina pede este parâmetro. Ele
   entra como decisão de produto sua, registrada aqui, e vai aparecer no `unit-of-work-story-map.md`
   como escopo **sem história de origem** — declarado como tal em vez de camuflado dentro de US-17
   ou US-19.

**Parte 1 encerrada.** Nada mais a perguntar. O próximo movimento é a aprovação do plano (passo 9 da
regra) e então a Parte 2: os três artefatos obrigatórios de unidade mais as 11 emendas da Parte D.

---

# Parte H — Rodada 4 (2026-08-25): revogação do parâmetro de aprovação

**Origem**: resposta do usuário ao portão de aprovação de Units Generation, sobre os três pontos que
eu havia declarado por conta própria.

## H.1 — Ponto 1 (ordem de execução): confirmado, nada a fazer

O usuário aprovou a correção ("vamos fazer o ajuste da ordem então para implementar"). A correção
**já estava aplicada** nos artefatos gerados na Parte 2: wiki é `U3`, ambiente é `U4`, a matriz de
`unit-of-work-dependency.md` §2 é triangular inferior e a ordem é `U0 → U1 → ... → U9`. Nenhuma
edição foi necessária — registro isto para que a aprovação não pareça ter mudado algo que não mudou.

## H.2 — Ponto 2 (parâmetro de aprovação): **CQ2, CQ3=A e CQ4=A revogadas**

**Decisão do usuário**: *"essa decisao ficou muito jogada para essa iteracao, vamos descartar isso
para essa iteracao, podemos deixar como tudo para aprovacao de inicio e depois mudar, ou deixar sem
pedir aprovacao, oq vc acha que é mais fácil e faz mais sentido para depois no futuro podermos
alterar essa questão de aprovação facilmente por meio de algum tipo de configuração."*

Ele delegou a escolha entre as duas alternativas. **Escolha aplicada: sempre pedir aprovação**, sem
parâmetro, com o ponto de decisão centralizado numa função só.

### O argumento decisivo, que eu não tinha visto nas rodadas anteriores

O fluxo de confirmação **não é custo do parâmetro**. A **US-14** — "revisar antes de o bibliotecário
escrever" — é história aprovada da linha fina e já exige uma tela onde você aprova ou rejeita antes
da escrita. Então:

- **"Sem pedir aprovação"** não economiza o fluxo: ele teria que existir na `U9` de qualquer jeito
  para a US-14. Economizaria apenas a ligação das ferramentas de ambiente a ele — e deixaria a
  iteração rodando com o orquestrador criando frente, tarefa, etapa e chat sem você ver, que é
  exatamente o risco tratado na Q14.
- **"Sempre pedir aprovação"** reaproveita um fluxo que já é obrigatório e cobre as duas famílias de
  ferramenta pelo mesmo caminho (era a intenção original da CQ4=A, agora obtida de graça).

### Por que esta é a forma mais barata de virar configuração depois

A política mora em **um lugar só**: `dominio/politica.py` (unidade `U1`), com

```
APROVACAO_DE_AGENTE_OBRIGATORIA = True

def exige_aprovacao(...) -> bool: ...
```

`U5` (ferramentas de ambiente) e `U8` (propostas do bibliotecário) chamam `exige_aprovacao(...)`.
Quando a configuração voltar — campo em `Ambiente`, arquivo de config, o que for —, **só o corpo
dessa função muda**: nenhum chamador, nenhuma tela, nenhum contrato de porta e nenhuma seta da
matriz de dependência é tocado. A alternativa "sem aprovação" pagaria depois a construção do ponto
de consulta *e* da ligação do fluxo, que agora saem prontos.

### O que a revogação apaga, honestamente

| Item | Situação |
|---|---|
| Campo `aprovacao_de_agente_obrigatoria` em `Ambiente` (`U1`) | **Sai** — vira constante de módulo, sem estado |
| Compatibilidade regressiva de documento antigo (`U2`) | **Sai por inteiro** — único custo eliminado de verdade |
| Tela para desligar o parâmetro (`U9`) | **Sai** |
| Ponto de consulta em `U5` e `U8` | **Fica** |
| Fluxo de confirmação na `U9` | **Fica** — já pedido por US-14 |
| Conta de portões (31) | **Não muda** — nenhum estágio EXECUTE/SKIP foi alterado |

### O custo que fica, declarado

Toda ação de ambiente disparada pelo orquestrador vai pedir sim/não nesta iteração, sem opção de
desligar. Se isso incomodar no uso real, é sinal a favor de a configuração existir na próxima
iteração — e o desenho acima faz esse retorno custar poucas linhas. Ação disparada por você via
`/comando` continua executando direto: a política governa apenas o chamador agente.

## H.3 — Ponto 3 (nada demonstrável antes de `U9`): aceito pelo usuário

*"tudo bem, isso não será um problema, pois o teste já ajuda a verificar, e o final da iteração que é
o objetivo e que tem que funcionar."* Risco de integração concentrado em `U9` permanece registrado
em `unit-of-work-dependency.md` §5, agora como risco **aceito explicitamente**, não apenas declarado.

## H.4 — Artefatos emendados nesta rodada

| Artefato | O que mudou |
|---|---|
| `components.md` §2.2 | Bullet do campo riscado + **Emenda 2** revogando a emenda anterior |
| `components.md` §3.1 | Consulta passa de campo do `Ambiente` para `exige_aprovacao(...)` |
| `services.md` §7 | Mesma troca, com o motivo |
| `unit-of-work.md` U1, U2, U5, U8, U9, §6 | Escopo, critérios de pronto e conformidade atualizados |
| `unit-of-work-dependency.md` §3.1 | Justificativa da seta ausente `U5`↔`U8` atualizada; matriz inalterada |
| `unit-of-work-story-map.md` §4 | Escopo sem história de origem reduzido; US-14 assume o fluxo |

Nenhum texto foi apagado — tudo riscado com a data e o motivo, no mesmo padrão das rodadas
anteriores.
