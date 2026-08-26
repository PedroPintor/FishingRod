# User Stories — FishingRod (Iteração 1)

**Versão:** v1 · **Data:** 2026-08-18 · **Estágio:** INCEPTION — User Stories
**Base:** `aidlc-docs/inception/requirements/requirements.md`, `aidlc-docs/inception/user-stories/personas.md`
**Metodologia de organização:** aprovada em `story-generation-plan.md` + esclarecimento —
estrutura primária **Feature-Based** (cada história escrita uma única vez, corpo completo);
**Domain-Based** e **Journey-Based** entram como índices de referência cruzada abaixo, sem
duplicar o texto das histórias.

## Como ler este documento

- Cada história segue o formato **Como / eu quero / para que**, com critério **INVEST**, e
  critérios de aceite em **Given/When/Then** (Dado/Quando/Então).
- Cada história carrega `domain:` e `journey:` (metadados usados pelos índices) e `rastreio:`
  (requisito de origem em `requirements.md`).
- Histórias marcadas **[FORA DE ESCOPO NESTA ITERAÇÃO]** (seção H) não são construídas agora —
  ficam registradas para orientar Application Design e iterações futuras, conforme decisão do
  usuário na Questão 1 do esclarecimento do plano.
- **RF-F02** (porta de sessão viva desenhada para dois modos de autenticação) e **RF-F04**
  (núcleo desacoplado do SDK) **não** viram histórias de usuário: são restrições de desenho
  internas, não comportamento observável por quem usa o software. Ficam como requisito técnico
  em `requirements.md` e serão detalhadas em Application Design — incluí-las aqui violaria a
  regra de não antecipar decisão de arquitetura.
- Histórias de domínio `wiki` trazem sempre dois exemplos (ambiente do João, ambiente do Pedro),
  por exigência de ESC-12/CS-01 (validar generalidade nos dois domínios).

---

---

## Escopo da linha fina — revisão v2 (2026-08-19)

> Emenda posterior à aprovação deste documento. O texto das histórias **não muda**; muda apenas
> qual delas é construída nesta iteração. Fonte: `requirements.md` §9.6.

Critério: *o software já entrega uso e já pode ser posto na mão do usuário de validação*.
Hipótese escolhida para validar: **o loop ambiente → conversa → wiki torna o ambiente mais
inteligente com o tempo**.

| Situação | Histórias | Total |
|---|---|---|
| ✅ **Dentro da linha fina** | US-01, US-02, US-03, US-04, US-05, US-06, US-08, US-09, US-13, US-14, US-15, US-16, US-17, US-19 | 14 |
| ⏸ **Adiadas** (estavam dentro na v1) | US-07, US-10, US-11, US-12, US-18 | 5 |
| ❌ **Já fora desde a v1** | US-20, US-21, US-22, US-23 | 4 |

Motivo de cada adiamento em `requirements.md` §9.6. Resumo: US-07 é *best-effort* e a
continuidade percebida já vem de US-06; US-10 é o esquema de wiki mutando em runtime (o esquema
como semente, que cobre US-09, está dentro); US-11/US-12 (rod-maker) caem com a escolha da
hipótese; US-18 só tem valor depois de existir histórico de tarefas concluídas.

**Nota sobre a interface**: a v2 fixou a **TUI (Textual)** como única interface entregável desta
iteração (`requirements.md` ESC-16, FOR-10). Onde estas histórias dizem "aba", "tela" ou
"interface", leia TUI. As histórias foram escritas de forma neutra de interface e continuam
válidas sem alteração de texto.

---

## Índice por domínio

| Domínio | Histórias |
|---|---|
| `sessao-llm` — conversa com LLM e autenticação | US-01, US-02, US-03 |
| `memoria` — confiabilidade da memória da tarefa | US-04 |
| `persistencia` — sobreviver ao restart | US-05, US-06, US-07 |
| `wiki` — repositório de inteligência do ambiente | US-08, US-09, US-10 |
| `agentes-especiais` — rod-maker e bibliotecário | US-11, US-12, US-13, US-14 |
| `colaborativo-solo` — mínimo colaborativo, um usuário | US-15, US-16, US-17, US-18, US-19 |
| `colaborativo-time` — **fora de escopo** | US-20, US-21, US-22, US-23 |

## Índice por jornada de uso

| Passo da jornada | Histórias |
|---|---|
| Criar o ambiente (meta, frentes, wiki inicial) | US-08, US-09, US-15 |
| Criar uma tarefa e descobrir/reaproveitar etapas | US-04, US-16, US-17, US-18 |
| Conversar com um agente / executar tarefa | US-01, US-02, US-03, US-19 |
| Criar um agente novo (rod-maker) | US-11, US-12 |
| Escrever na wiki (bibliotecário) | US-10, US-13, US-14 |
| Fechar e retomar o trabalho depois | US-05, US-06, US-07 |
| Colaborar em equipe (fora de escopo) | US-20, US-21, US-22, US-23 |

---

# A. Domínio `sessao-llm`

### US-01 — Conversar com um agente real dentro de uma tarefa

**Como** dono do ambiente (João ou Pedro), **eu quero** enviar uma mensagem a um agente numa
aba e receber uma resposta de um LLM real, **para que** eu consiga de fato trabalhar com o
agente, não com um placeholder.

`domain: sessao-llm` · `journey: conversar-com-agente` · `rastreio: RF-F01, ESC-01`

**Critérios de aceite**
- Dado um agente existente numa tarefa, quando envio uma mensagem na aba dele, então recebo uma
  resposta gerada por um modelo de linguagem real — nunca `None` nem uma string fixa de teste.
- Dado que enviei uma mensagem, quando a resposta chega, então ela aparece na aba certa, sem se
  misturar com a conversa de outro agente da mesma tarefa.

---

### US-02 — Abrir uma sessão autenticada por assinatura, sem precisar de API key

**Como** dono do ambiente, **eu quero** que o software use minha assinatura já paga para
autenticar o agente, **para que** eu não precise gerenciar chave de API para começar a usar.

`domain: sessao-llm` · `journey: conversar-com-agente` · `rastreio: RF-F03, ESC-02, ESC-03`

**Critérios de aceite**
- Dado que estou logado via assinatura (CLI do provedor), quando abro uma sessão viva com um
  agente, então consigo enviar e receber mensagens sem configurar nenhuma chave de API.
- Dado que não tenho uma API key configurada, quando uso o software normalmente, então nada me
  pede uma — o modo assinatura é suficiente para operar esta iteração.

---

### US-03 — Uma falha do provedor de LLM não derruba a interface

**Como** dono do ambiente, **eu quero** que um erro de conexão com o LLM apareça como aviso, não
como travamento do programa, **para que** eu não perca o que estava fazendo nas outras tarefas.

`domain: sessao-llm` · `journey: conversar-com-agente` · `rastreio: RF-F01, RNF-06`

**Critérios de aceite**
- Dado que envio uma mensagem a um agente, quando o provedor de LLM falha ou está indisponível,
  então vejo uma mensagem de erro clara na aba, e a TUI/CLI continua respondendo normalmente.
- Dado que uma aba falhou, quando volto a uma tarefa diferente, então ela funciona normalmente —
  o erro fica contido na aba/agente onde aconteceu.

---

# B. Domínio `memoria`

### US-04 — Anotar uma informação nova na memória da tarefa sem erro

**Como** dono do ambiente, **eu quero** que anotar algo pela primeira vez na memória de uma
tarefa funcione sempre, **para que** eu confie que o ambiente registra o que os agentes
descobrem, sem quebrar no meio do trabalho.

`domain: memoria` · `journey: criar-tarefa` · `rastreio: RF-F06, ESC-06`

**Critérios de aceite**
- Dado uma tarefa sem nenhuma anotação sob uma determinada chave (ex.: `travado-por`), quando um
  agente ou o orquestrador anota algo sob essa chave pela primeira vez, então a anotação é salva
  com sucesso — sem lançar erro nem interromper a conversa.
- Dado uma chave já anotada antes, quando uma nova anotação é feita sob a mesma chave, então a
  anotação anterior não é perdida — ambas ficam disponíveis, com autor e valor próprios.

---

# C. Domínio `persistencia`

### US-05 — A estrutura do ambiente sobrevive a fechar e reabrir o processo

**Como** dono do ambiente, **eu quero** que meus ambientes, frentes, tarefas e wiki continuem lá
depois de eu fechar e abrir o programa de novo, **para que** eu use o FishingRod no meu dia a
dia real, não só numa sessão contínua.

`domain: persistencia` · `journey: retomar-trabalho` · `rastreio: RF-F05 (estrutura), ESC-05`

**Critérios de aceite**
- Dado um ambiente com frentes, tarefas e uma wiki, quando encerro o processo e abro o programa
  de novo, então encontro o mesmo ambiente, com as mesmas frentes, tarefas e categorias da wiki.
- Dado que criei uma tarefa nova e fechei o programa antes de conversar com nenhum agente nela,
  quando reabro, então a tarefa ainda existe, vazia de conversa, pronta para eu continuar.

---

### US-06 — A transcrição de uma conversa antiga continua visível depois de reabrir

**Como** dono do ambiente, **eu quero** ver o que já foi dito numa aba antiga, mesmo depois de
dias sem usar o programa, **para que** eu não perca o histórico do que já decidi ou descobri
com aquele agente.

`domain: persistencia` · `journey: retomar-trabalho` · `rastreio: RF-F05 (transcrição), ESC-05`

**Critérios de aceite**
- Dado que conversei com um agente numa aba e fechei o programa, quando reabro e volto a essa
  aba, então vejo a transcrição completa da conversa anterior, independente de qual adaptador
  de LLM estava ativo quando ela aconteceu.
- Dado duas abas diferentes na mesma tarefa, quando reabro o programa, então cada uma mostra
  só a própria transcrição — sem misturar histórico entre agentes.

---

### US-07 — [ADIADA NA v2] Retomar uma conversa com continuidade real de memória do agente

**Como** dono do ambiente, **eu quero** que o agente, quando o adaptador ativo permitir,
realmente se lembre do contexto de uma conversa antiga (não só eu ver o texto), **para que** eu
não precise reexplicar tudo de novo quando volto a uma tarefa parada.

`domain: persistencia` · `journey: retomar-trabalho` · `rastreio: RF-F05 (retomada), ESC-05`

**Critérios de aceite**
- Dado que o adaptador ativo é o de assinatura (que suporta retomada nativa de sessão), quando
  reabro uma aba antiga e envio uma nova mensagem, então o agente responde levando em conta o
  contexto da conversa anterior, não como se fosse uma conversa nova.
- Dado que o adaptador ativo não suporta retomada nativa, quando reabro uma aba antiga, então a
  transcrição salva (US-06) continua disponível, mesmo que a continuidade de memória do agente
  não seja garantida da mesma forma — é um comportamento **best-effort**, dependente da
  capacidade do adaptador, não uma promessa igual para todo modo de autenticação.
- **Nota:** a forma concreta de como o identificador de retomada é guardado e usado fica para
  Application Design — este critério só fixa o comportamento observável.

---

# D. Domínio `wiki`

### US-08 — Todo ambiente novo já nasce com uma wiki, mesmo vazia

**Como** dono do ambiente, **eu quero** que criar um ambiente já crie a wiki dele, **para que**
eu tenha, desde o primeiro dia, um lugar para guardar o que aprendo, sem precisar configurar
isso à parte.

`domain: wiki` · `journey: criar-ambiente` · `rastreio: RF-F07, ESC-07`

**Critérios de aceite**
- Dado que crio o ambiente "Nexo Aquisição" (João), quando a criação termina, então uma wiki
  existe para ele, vazia de conteúdo, mas com estrutura mínima de categorias pronta para uso.
- Dado que crio o ambiente "Meus estudos do semestre" (Pedro), quando a criação termina, então
  uma wiki existe para ele também, do mesmo jeito — nenhum ambiente fica sem wiki.

---

### US-09 — A estrutura da wiki é definida pelo dono do ambiente, não fixa no produto

**Como** dono do ambiente, **eu quero** escolher as categorias da minha wiki, **para que** ela
reflita o meu domínio de trabalho, não um formato genérico imposto pelo software.

`domain: wiki` · `journey: criar-ambiente` · `rastreio: RF-F08, ESC-07`

**Critérios de aceite**
- Dado o ambiente do João, quando ele define as categorias iniciais da wiki, então elas podem
  ser algo como `ICP`, `oferta`, `narrativa`, `provas` — vocabulário do domínio de aquisição.
- Dado o ambiente do Pedro, quando ele define as categorias iniciais da wiki, então elas podem
  ser algo como `conceitos por disciplina`, `resumos`, `dúvidas recorrentes` — vocabulário do
  domínio de estudos, sem nenhuma categoria de marketing pré-definida pelo software.
- Dado os dois ambientes acima, quando comparo as duas wikis, então nenhuma delas depende de
  código escrito especificamente para o domínio do outro.

---

### US-10 — [ADIADA NA v2] Criar uma nova categoria da wiki conversando com um agente

**Como** dono do ambiente, **eu quero** criar uma categoria nova na wiki a qualquer momento, só
de conversar, **para que** a wiki cresça junto com o que vou descobrindo, sem eu precisar
editar configuração.

`domain: wiki` · `journey: escrever-na-wiki` · `rastreio: RF-F08`

**Critérios de aceite**
- Dado o ambiente do João já em uso, quando ele percebe que precisa guardar "regras de corte de
  canal" e isso não existe ainda, quando conversa com um agente pedindo para criar essa
  categoria, então a categoria passa a existir na wiki dele.
- Dado o ambiente do Pedro já em uso, quando ele percebe que precisa de uma categoria
  "fórmulas por matéria" que não existe, quando conversa com um agente pedindo para criá-la,
  então a categoria passa a existir na wiki dele, sem afetar a wiki do João.

---

# E. Domínio `agentes-especiais`

### US-11 — [ADIADA NA v2] Criar um agente novo através do rod-maker

**Como** dono do ambiente, **eu quero** pedir a criação de um agente novo e ter o rod-maker
construindo-o, **para que** eu não precise configurar um agente manualmente toda vez que uma
tarefa se repete o suficiente para merecer um.

`domain: agentes-especiais` · `journey: criar-agente` · `rastreio: RF-F09, ESC-08, H-02`

**Critérios de aceite**
- Dado que estou conversando com o orquestrador sobre uma tarefa, quando peço para criar um
  agente (ex.: João pedindo um "agente qualificador de MQL"), então o orquestrador aciona o
  rod-maker e, ao final, o agente novo passa a existir e a poder ser conversado no ambiente.
- Dado que uma etapa de estudo se repetiu várias vezes (ex.: Pedro questionando o próprio
  entendimento manualmente), quando ele pede um agente para isso, então o rod-maker constrói um
  agente "questionador" disponível dali em diante.

---

### US-12 — [ADIADA NA v2] Escolher com quem conversar depois que o rod-maker constrói o agente

**Como** dono do ambiente, **eu quero** decidir se continuo falando com o rod-maker ou volto
para o orquestrador depois que um agente é criado, **para que** eu tenha controle sobre o fluxo
da conversa, em vez de ser redirecionado automaticamente.

`domain: agentes-especiais` · `journey: criar-agente` · `rastreio: RF-F09, H-02`

**Critérios de aceite**
- Dado que o rod-maker acabou de criar um agente, quando decido continuar a conversa com o
  rod-maker (ex.: para ajustar o agente recém-criado), então isso é possível sem voltar ao
  orquestrador primeiro.
- Dado a mesma situação, quando decido voltar a falar com o orquestrador em vez disso, então
  isso também é possível — a escolha é sempre minha, não automática.

---

### US-13 — Promover conteúdo à wiki através do bibliotecário, no formato certo

**Como** dono do ambiente, **eu quero** que o bibliotecário escreva na wiki por mim, garantindo
o formato, **para que** o conteúdo salvo seja consistente e realmente utilizável por outros
agentes depois.

`domain: agentes-especiais` · `journey: escrever-na-wiki` · `rastreio: RF-F10, ESC-08, H-01`

**Critérios de aceite**
- Dado que o João descobriu algo que quer virar diretriz (ex.: um novo critério de ICP), quando
  aciona o bibliotecário para promover isso à wiki, então o conteúdo é salvo na categoria certa,
  no formato da wiki daquele ambiente.
- Dado que o Pedro quer guardar um conceito aprendido em aula, quando aciona o bibliotecário,
  então o conteúdo é salvo na wiki do ambiente de estudos dele, sem precisar saber o formato
  interno da wiki de antemão.

---

### US-14 — Revisar o conteúdo antes de o bibliotecário confirmar a escrita na wiki

**Como** dono do ambiente, **eu quero** revisar o que vai entrar na wiki antes de ser salvo,
**para que** nada errado vire contexto oficial sem eu confirmar.

`domain: agentes-especiais` · `journey: escrever-na-wiki` · `rastreio: RF-F10, H-01, P-14`

**Critérios de aceite**
- Dado que o bibliotecário preparou um conteúdo para a wiki, quando apresenta esse conteúdo
  antes de salvar, então eu vejo o texto final e posso aprovar ou pedir ajuste antes da escrita
  se efetivar.
- Dado que peço um ajuste, quando o bibliotecário atualiza o conteúdo, então a versão anterior
  não é salva — só a versão que eu confirmei entra na wiki.

---

# F. Domínio `colaborativo-solo`

### US-15 — Criar uma frente dentro do ambiente

**Como** dono do ambiente, **eu quero** criar uma frente nova a qualquer momento, **para que**
o ambiente reflita as áreas de atuação reais do meu trabalho, mesmo que elas mudem com o tempo.

`domain: colaborativo-solo` · `journey: criar-ambiente` · `rastreio: RF-F11`

**Critérios de aceite**
- Dado o ambiente "Nexo Aquisição", quando o João cria a frente "comercial e ticket", então ela
  passa a existir e pode receber tarefas.
- Dado o ambiente "Meus estudos do semestre", quando o Pedro cria a frente "planejamento de
  estudos", então ela passa a existir do mesmo jeito, sem depender de vocabulário do outro
  domínio.

---

### US-16 — Criar uma tarefa dentro de uma frente

**Como** dono do ambiente, **eu quero** criar uma tarefa dentro de uma frente, **para que** eu
tenha um lugar próprio, com objetivo e memória próprios, para tocar aquele trabalho.

`domain: colaborativo-solo` · `journey: criar-tarefa` · `rastreio: RF-F11, RF-01`

**Critérios de aceite**
- Dado a frente "mídia paga" do João, quando ele cria a tarefa "campanha de oferta para donos
  de clínica", então ela aparece disponível para receber etapas e conversas.
- Dado a frente "exercícios" do Pedro, quando ele cria a tarefa "lista de cálculo 2 — capítulo
  4", então ela aparece disponível do mesmo jeito.

---

### US-17 — Descobrir as etapas de uma tarefa conversando com o orquestrador

**Como** dono do ambiente, **eu quero** montar o plano de etapas de uma tarefa conversando com
o orquestrador, **para que** eu não precise saber o método antes de começar a trabalhar.

`domain: colaborativo-solo` · `journey: criar-tarefa` · `rastreio: RF-F12, RF-07`

**Critérios de aceite**
- Dado que o Pedro cria uma tarefa de estudo sem saber ainda quais sub-etapas seguir, quando
  conversa com o orquestrador sobre isso, então, ao final da conversa, a tarefa tem etapas
  definidas (ex.: leitura do material → aprofundamento → exercícios → anotar no mapa mental).
- Dado que o João já chega com o método formado (ele é dono do domínio de negócio), quando cria
  uma tarefa e conversa brevemente com o orquestrador, então as etapas refletem o que ele já
  tinha em mente, sem ser forçado a redescobrir por conversa o que já sabe.

---

### US-18 — [ADIADA NA v2] Reaproveitar e refinar uma tarefa já feita antes

**Como** dono do ambiente, **eu quero** reaproveitar os passos de uma tarefa que já fiz, e
ajustá-los se algo incomodou, **para que** eu não recomece do zero toda vez que o trabalho se
repete.

`domain: colaborativo-solo` · `journey: criar-tarefa` · `rastreio: RF-F12`

**Critérios de aceite**
- Dado que o Pedro já fez a tarefa "resumir capítulo" antes, quando cria uma tarefa nova do
  mesmo tipo, então pode reaproveitar os mesmos passos em vez de defini-los de novo.
- Dado que, ao reaproveitar, ele percebe que uma etapa incomoda, quando conversa com o
  orquestrador sobre isso, então os dois ajustam essa etapa junto, e o ajuste fica valendo da
  próxima vez que a tarefa for reaproveitada.

---

### US-19 — Executar uma tarefa através de um chat com agente

**Como** dono do ambiente, **eu quero** acionar um agente para executar uma etapa da tarefa,
**para que** eu avance o trabalho sem sair do ambiente.

`domain: colaborativo-solo` · `journey: conversar-com-agente` · `rastreio: RF-F12, RF-07`

**Critérios de aceite**
- Dado uma etapa cujo executor é um agente (ex.: "escrever copy" no ambiente do João), quando
  aciono esse agente na aba correspondente, então ele produz o resultado esperado da etapa
  dentro da conversa.
- Dado uma etapa cujo executor é o próprio usuário (ex.: "assistir à aula" no ambiente do
  Pedro), quando confirmo que a fiz, então a etapa é marcada como concluída.
- **Nota de escopo:** este critério cobre execução via agente conversacional. Execução que
  dependa de uma ferramenta MCP externa configurada fica fora do escopo desta iteração
  (`requirements.md`, FOR-04).

---

# H. Domínio `colaborativo-time` — [FORA DE ESCOPO NESTA ITERAÇÃO]

> Histórias abaixo descrevem o uso em equipe do João (persona real, uso de time), registradas
> por decisão explícita do usuário (esclarecimento da Pergunta 1) para dar contexto de
> generalização e orientar Application Design/iterações futuras. **Nenhuma delas é construída
> nesta iteração** — colidem com ESC-09/FOR-01/FOR-02 de `requirements.md`. Esta seção é
> representativa, não exaustiva: a lista completa de comportamentos diferenciais fora de escopo
> está em `requirements.md`, FOR-06.

### US-20 — [FORA DE ESCOPO] Alocar uma etapa a outro usuário do ambiente

**Como** João, **eu quero** alocar uma etapa a um colega de time, **para que** o trabalho seja
distribuído sem eu precisar fazer tudo sozinho.

`domain: colaborativo-time` · `journey: colaborar-em-equipe` · `rastreio: RF-04 (fora de escopo)`

**Esboço de critério (não implementado nesta iteração)**
- Dado uma etapa com executor "outro usuário", quando alocada a um colega nomeado, então esse
  colega vê a etapa como responsabilidade dele.

---

### US-21 — [FORA DE ESCOPO] Admin bloqueia uma funcionalidade para os demais usuários

**Como** João (admin do ambiente), **eu quero** restringir o que os demais usuários podem fazer,
**para que** o ambiente não fique desorganizado por decisões de terceiros.

`domain: colaborativo-time` · `journey: colaborar-em-equipe` · `rastreio: RF-08–RF-10 (fora de escopo)`

**Esboço de critério (não implementado nesta iteração)**
- Dado um ambiente com mais de um usuário, quando o admin bloqueia uma funcionalidade, então os
  demais usuários deixam de conseguir executá-la, mas continuam com o mínimo colaborativo
  padrão nas demais.

---

### US-22 — [FORA DE ESCOPO] Ver o contrato consome/entrega de uma tarefa

**Como** João, **eu quero** ver o que uma tarefa precisa receber e o que vai produzir, verde no
que existe e vermelho no que falta, **para que** eu saiba exatamente onde entrar sem precisar
de um dashboard.

`domain: colaborativo-time` · `journey: colaborar-em-equipe` · `rastreio: comportamento diferencial #1 (fora de escopo)`

**Esboço de critério (não implementado nesta iteração)**
- Dado uma tarefa com insumos declarados, quando um insumo ainda não existe, então ele aparece
  marcado como faltante; quando passa a existir, então muda para existente, sem ação manual.

---

### US-23 — [FORA DE ESCOPO] Tarefa trava e destrava sozinha esperando artefato de outro card

**Como** João, **eu quero** que uma tarefa que depende de outra espere sozinha e destrave
sozinha quando o artefato existir, **para que** eu não precise ficar checando manualmente.

`domain: colaborativo-time` · `journey: colaborar-em-equipe` · `rastreio: comportamento diferencial #2 (fora de escopo)`

**Esboço de critério (não implementado nesta iteração)**
- Dado uma tarefa que depende de um artefato de outra, quando o artefato ainda não existe,
  então a tarefa fica marcada como travada; quando o artefato passa a existir, então ela
  destrava sozinha, sem o usuário precisar agir.

---

## Mapeamento persona → histórias

| Persona | Histórias em que aparece |
|---|---|
| **João Nishi** | US-01 a US-19 (como um dos dois exemplos), US-20 a US-23 (exclusivo, fora de escopo) |
| **Pedro Pintor** | US-01 a US-19 (como um dos dois exemplos) |

Nenhuma história de US-01 a US-19 é exclusiva de uma persona — ambas ilustram o mesmo
comportamento em domínios diferentes, para sustentar a validação de generalidade (CS-01, E1=A).
Only US-20–US-23 são exclusivas do João, porque descrevem uso em equipe que só existe no
ambiente dele nesta fase de descoberta.
