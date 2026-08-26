# User Stories — Plano de Geração (Planning)

**Papel assumido:** product owner
**Base:** `aidlc-docs/inception/requirements/requirements.md` (RF-F01–RF-F12, RNF-01–RNF-09,
escopo dentro/fora), `vision.md` (personas, princípios), `produto/` (hipóteses, cenários)

Este plano só entra na Parte 2 (Geração) depois que todas as perguntas abaixo estiverem
respondidas e eu tiver validado as respostas quanto a ambiguidade (Step 9 de `user-stories.md`).

---

## Checklist de execução (Parte 2 — preenchido depois da aprovação deste plano)

**Decisões finais consolidadas** (respostas do plano + esclarecimento em
`story-generation-plan-clarification-questions.md`):

- [x] Gerar `aidlc-docs/inception/user-stories/personas.md` com **duas personas**: João Nishi
      (uso em equipe, cliente, **alvo principal de validação desta iteração** — se o software
      funcionar para ele operando sozinho, está validado) e Pedro Pintor (uso próprio/pessoal,
      estudo — reforça a generalidade da estrutura)
- [x] Gerar `aidlc-docs/inception/user-stories/stories.md` com histórias no critério INVEST,
      **fatiadas em partes menores que os 12 RF-F** (Pergunta 3=C) sempre que houver mais de um
      cenário de aceite distinto por requisito
- [x] **Estrutura primária: Feature-Based.** Cada história é escrita uma única vez (título,
      descrição, critérios de aceite), agrupada por funcionalidade concreta — sem duplicar o
      corpo da história por domínio ou por jornada
- [x] Cada história recebe metadados leves `domain:` e `journey:` para alimentar dois **índices
      de referência cruzada** no topo de `stories.md` (tabela por domínio, tabela por jornada de
      uso) — só nome da história + ID, sem repetir o texto
- [x] Toda história que dependa de mais de um usuário (alocar a outro usuário, visibilidade
      cruzada, etc.) é escrita para o João, mas **marcada explicitamente "Fora do escopo desta
      iteração — ver ESC-09/FOR-01/FOR-02"**; documentada para orientar Application Design e
      iterações futuras, não prometida para esta iteração
- [x] Histórias buildáveis nesta iteração cobrem o que é executável por **um usuário só**
      (qualquer uma das duas personas operando sozinha) — é este subconjunto que valida o
      software nesta iteração
- [x] Cada história recebe critérios de aceite em **Given/When/Then** (Pergunta 4=A)
- [x] Histórias que tocam RF-F07/RF-F08 (wiki) trazem **sempre** dois exemplos ilustrativos —
      um do domínio de marketing (`cenarios/01`), um do domínio de estudos (`cenarios/02`) —
      no corpo do critério de aceite (Pergunta 5=A)
- [x] História(s) de persistência (RF-F05) cobrem, no critério de aceite: (a) estrutura
      (ambientes, frentes, tarefas, wiki, quais chats existem); (b) transcrição completa de
      cada chat, sempre persistida, independente do adaptador ativo; (c) identificador de
      retomada por chat, persistido de forma opcional quando o adaptador ativo suportar
      retomada nativa (hoje, assinatura), usado como atalho e nunca como única coisa
      persistida; (d) continuidade de memória do agente como best-effort dependente da
      capacidade do adaptador, não garantia incondicional igual entre assinatura e API key
      (Pergunta 6)
- [x] Mapear cada persona às histórias relevantes (incluindo as marcadas fora de escopo, para
      rastreabilidade)
- [x] Revisar que nenhuma história introduz decisão de arquitetura reservada a Application
      Design (Chain of Responsibility, forma concreta da porta de sessão viva, onde o
      identificador de retomada vive) — histórias descrevem comportamento observável, não
      implementação

---

## Perguntas de planejamento

**Como responder**: mesmo formato de sempre — letra depois do `[Answer]:`, ou "Other" com
descrição, para cada pergunta.

### Pergunta 1 — Escopo de personas

`vision.md` traz duas personas: **João Nishi** (opera, multiusuário, fora do escopo desta
iteração — ESC-09/FOR-01) e **Pedro Pintor** (monta e usa, é quem opera de fato nesta iteração
como único usuário). Como tratar o João em `personas.md`?

A) **Só Pedro Pintor como persona ativa desta iteração.** João aparece apenas numa nota de
"personas futuras", sem história própria — nenhuma história é escrita pensando nele agora.

B) **As duas personas, com histórias só para Pedro Pintor.** `personas.md` documenta os dois
arquétipos (útil para Application Design/Workflow Planning entenderem quem vem depois), mas
nenhuma história em `stories.md` é atribuída ao João nesta rodada.

C) **Uma persona única e genérica ("dono do ambiente"), sem nomear João ou Pedro.** Evita
acoplar as histórias a uma pessoa específica, já que o requisito é sobre o papel (dono/admin
operando solo), não sobre o indivíduo.

X) Other (descreva depois do [Answer]: abaixo)

[Answer]: X - vamos fazer as duas persona, uma para o joao que é o meu cliente nas historias em /produto e vamos fazer para o Pedro Pintor que seria para um outro caso de usuario onde essa pessoa usuaria para uso proprio o ambiente e o Joao ja usuaria para trabalhar em equipe . essas duas persona sao boas de fazer pois assim temos os dois tipos de pessoas que usuariam o software, uma que usuaria para o software para trabalhar no dia a dia na empresa junto com o seu time ( esse usuario seria o Joao), e um usuario que usuaria mais para uso proprio no dia a dia para estudar materias da faculdade ( esse usuario seria o Pedro Pintor)

---

### Pergunta 2 — Abordagem de organização das histórias

`user-stories.md` oferece 5 abordagens: User Journey-Based, Feature-Based, Persona-Based,
Domain-Based, Epic-Based. Dado que esta iteração tem uma persona só (Pergunta 1) mas vários
domínios técnicos distintos (sessão viva/LLM, persistência, wiki, agentes especiais, mínimo
colaborativo), qual organiza melhor `stories.md`?

A) **Domain-Based.** Agrupar por domínio: (1) Conversa com LLM e autenticação, (2)
Persistência, (3) Wiki, (4) Agentes especiais (rod-maker, bibliotecário), (5) Mínimo
colaborativo (criar tarefa/agente, acionar chat). Cada grupo é uma seção com suas histórias.

B) **Feature-Based.** Uma história por funcionalidade concreta e observável (mais próxima de
RF-F01–RF-F12 individualmente), sem agrupamento por domínio — lista plana.

C) **User Journey-Based.** Organizar pela jornada de uso: criar ambiente → criar wiki → criar
frente/tarefa → conversar com agente → acionar rod-maker/bibliotecário → persistir e retomar.

X) Other (descreva depois do [Answer]: abaixo)

[Answer]: X - eu penso que para conseguirmos ter o melhor entendimento de como o software deve ter de usos pelo usuario, eu acredito que temos que fazer as 3 abordagens de historia de usuario para cada caso. eu penso que fazendo assim vamos ter um entendimento mais completo do software e evitar duvidas, pois o software e o uso dele ainda esta nebulo e é complexo.

---

### Pergunta 3 — Granularidade das histórias

Os 12 requisitos funcionais (RF-F01–RF-F12) já têm um critério de pronto cada. Como convertê-los
em histórias?

A) **Uma história por requisito funcional** — 12 histórias, mapeamento 1:1 com RF-F01–RF-F12,
sem fundir nem dividir.

B) **Histórias fundidas por coesão** — requisitos muito próximos (ex.: RF-F02+RF-F03, os dois
lados da porta de sessão viva; RF-F09+RF-F10, os dois agentes especiais) tornam-se uma história
só, resultando em menos de 12 histórias, mais coesas.

C) **Histórias divididas em fatias menores** — cada requisito pode virar 2 ou mais histórias se
tiver múltiplos cenários de aceite distintos (ex.: RF-F05 persistência pode separar "salvar
estado" de "restaurar estado"), resultando em mais de 12 histórias.

X) Other (descreva depois do [Answer]: abaixo)

[Answer]: C - penso que essa é a melhor abordagem, pois eu penso que o software ainda esta meio nebuloso de como vai ser usado de fato. como eu penso que estamos inovando a maneira de usa da IA no dia a dia, as historias de usos podem ser incompletas para abrangir as novos tipos de usos q eu imagino e penso. entao quanto mais fatiado e mais detalhado melhor para conseguir abrangir uma gama de usos e deixar bem claro as ideias de uso.

---

### Pergunta 4 — Formato dos critérios de aceite

A) **Given/When/Then (Gherkin).** Cada critério de aceite segue o formato "Dado [contexto],
quando [ação], então [resultado observável]" — mais formal, mais fácil de espelhar depois em
testes automatizados (inclusive os baseados em propriedade).

B) **Checklist de condições em linguagem natural.** Cada critério de aceite é uma lista de
condições verificáveis ("a wiki existe desde a criação do ambiente"; "reabrir o processo mantém
as tarefas"), sem formato Gherkin — mais direto de escrever e ler, menos formal.

X) Other (descreva depois do [Answer]: abaixo)

[Answer]: A - vamos nesse formato que eu ja conheço e acho bom para o nosso cenario.

---

### Pergunta 5 — Ilustrar histórias com os dois domínios de validação (ESC-12)

O requisito ESC-12 pede validar a estrutura contra dois domínios (o ambiente de marketing do
usuário, `cenarios/01`, e o ambiente de estudos, `cenarios/02`). Histórias que tocam wiki e
estrutura configurável (RF-F07/RF-F08) correm o risco de, sem querer, hardcodar vocabulário de
um domínio só.

A) **Toda história relevante a RF-F07/RF-F08 traz dois exemplos ilustrativos** (um do domínio
de marketing, um do domínio de estudos) no corpo do critério de aceite, para forçar a
generalidade a aparecer já na história.

B) **Nenhum exemplo de domínio nas histórias.** Manter as histórias abstratas (sem citar
marketing nem estudos) e deixar a validação de generalidade (ESC-12) inteiramente para
Build and Test / testes de propriedade, não para o texto da história.

X) Other (descreva depois do [Answer]: abaixo)

[Answer]: A - de novo aqui eu penso que temos que fazer toda historia relevante para ter o maximo de contexto possivel sobre as  historias de usuario,como eles usariam e deixar mais claro possivel as manerias  de uso.

---

### Pergunta 6 — Critério de aceite de persistência (RF-F05) e o que "sobreviver ao restart" significa

`vision.md` §6.3 estabelece que `Chat.mensagens` é cópia para a UI, não fonte da verdade do
histórico — com sessão viva, o histórico da conversa fica do lado do client/provedor, não do
núcleo. Isso limita o que a história de persistência pode prometer sobre o histórico de chat.

A) **Persistência cobre a estrutura (ambientes, frentes, tarefas, wiki, quais chats existem),
não o conteúdo integral das conversas.** Reabrir o processo restaura a estrutura; o histórico
de uma conversa em andamento pode não ser recuperável linha a linha, dependendo do provedor.

B) **Persistência cobre estrutura E histórico de conversa completo**, exigindo que o núcleo (ou
o adaptador) guarde/recupere as mensagens trocadas, mesmo que isso signifique tratar
`Chat.mensagens` como algo mais que cópia de UI nesta iteração — reabrindo a restrição de
`vision.md` §6.3 para decisão em Application Design.

X) Other (descreva depois do [Answer]: abaixo)

[Answer]: X - Eu preciso das duas coisas — mostrar as mensagens ao trocar de chat/sessão (mesmo depois de dias) e o agente lembrar de verdade quando eu volto numa conversa antiga. Não dá pra escolher só a estrutura (A) porque perderia o histórico visível, mas também não quero fechar a porta B do jeito que está escrita, porque isso faria o núcleo depender de como a assinatura resolve memória (retomar sessão por ID), e esse mecanismo não existe pra API key — lá não tem sessão pra retomar do lado do servidor, só dá pra simular reenviando o histórico.

Minha decisão: a persistência sempre guarda a transcrição completa de cada chat (isso já resolve o caso barato — reabrir e ver o que foi dito, independente de qual adaptador está ativo). Além disso, quando o adaptador ativo suportar retomada nativa de sessão (o caso da assinatura, via SDK), a persistência também guarda um identificador de retomada por chat, usado como atalho por esse adaptador — mas como algo opcional, associado ao adaptador, nunca como a única coisa persistida.

Com isso, "o agente lembrar de verdade" não é uma garantia única e igual pra sempre — é best-effort por capacidade do adaptador: hoje, via assinatura, a retomada é nativa (o provedor guarda o contexto do lado dele); no futuro, via API key, a continuidade vem de reenviar a transcrição guardada pra "primar" uma sessão nova, com o custo de tokens que isso implica e sem garantia de que todo estado interno (ex.: chamadas de tool) volte idêntico. Isso é aceitável — o que não é aceitável é a persistência ter sido desenhada só em função do mecanismo da assinatura e precisar ser refeita quando a API key chegar.

Isso não reabre a restrição de vision.md §6.3: a transcrição persistida continua sendo um registro passivo, não uma fonte que o núcleo consulta para lógica de negócio — ela só vira base para reconstruir uma sessão dentro do adaptador, que é o lugar que a própria porta de sessão viva já previu para isso.

A forma concreta disso (onde o identificador de retomada vive, como o adaptador recebe a transcrição para "primar" uma sessão nova) fica para Application Design, como já registrado nas notas retidas. Aqui estou fechando a intenção: RF-F05 precisa cobrir estrutura + transcrição completa por chat (sempre) + continuidade de memória do agente como best-effort dependente da capacidade do adaptador ativo, não como promessa incondicional igual para os dois modos de autenticação.

---

## Aprovação do plano

Depois de todas as respostas acima e da minha análise de ambiguidade (Step 9), vou apresentar
o prompt de aprovação do plano em si — antes de gerar `stories.md`/`personas.md`.
