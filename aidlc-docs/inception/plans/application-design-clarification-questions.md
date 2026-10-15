# Application Design — Rodada 2: consolidação e perguntas de acompanhamento

**Data:** 2026-08-23 · **Estágio:** INCEPTION — Application Design, Parte 1 (ainda em planejamento)
**Origem:** análise obrigatória das respostas dadas em `application-design-plan.md`
(regra `inception/application-design.md`, passos 8 e 9)

> **Por que este arquivo existe.** A regra do estágio manda analisar as respostas antes de gerar
> qualquer artefato e, se houver resposta vaga, contraditória ou com critério indefinido, fazer
> pergunta de acompanhamento em vez de prosseguir. Encontrei **uma pergunta sem resposta** e
> **cinco pontos que precisam de decisão** — três deles porque a resposta abre escopo que os
> requisitos aprovados fecharam, ou fecha algo que os requisitos deixaram aberto.
>
> O `application-design-plan.md` recebeu cerca de mil linhas de transcrição de conversa colada,
> com blocos de pergunta duplicados e tags `[Answer]:` vazias em cópias repetidas. Eu **não apaguei
> nada** — `aidlc-docs/` não está sob Git, então não há como desfazer. A §1 abaixo é a minha
> leitura canônica; confira se bate com a sua intenção.

---

## 1. Consolidação — como eu li as suas 16 respostas

Confira esta tabela. Se alguma linha estiver errada, corrija na §3.

| # | Decisão | Escolha | Precisão que você acrescentou |
|---|---|---|---|
| 1 | Cadeia `Ambiente → Projeto → Sessao` | **B** | Hierarquia de dados fica; roteamento e delegação saem do domínio |
| 2 | Pacotes em `src/` | **A** | `dominio/`, `aplicacao/`, `adaptadores/`, `interface/` |
| 3 | Fronteira do agregado | **B** | Estrutura como documento; transcrição em tabela append-only |
| 4 | Identidade | **B** | UUIDv7, gerada no construtor da entidade de domínio |
| 5 | Porta de sessão | **B** | Assíncrona nativa, com iterador de eventos (streaming) |
| 6 | Agente vs sessão viva | **A** | `Agente` = configuração imutável; sessão viva é objeto separado por chat |
| 7 | Roteamento de comando | **B+** | Não é "serviço que recebe string": é **catálogo de ações** (dado, iterável) + **parser `/` como adaptador de entrada fino** + **alvo explícito por identidade** + **resultado tipado**. O domínio não conhece sintaxe |
| 8 | Política de gravação | **— sem resposta —** | Ver Pergunta A |
| 9 | Portão de revisão da wiki | **A** | A tool não escreve; produz proposta; escrita só na aprovação |
| 10 | Acesso do bibliotecário à wiki | **B** | Tools nossas via MCP in-process; nativas de escrita negadas. Regra geral: tool nossa quando o acesso carrega invariante do software; nativa quando é genérico |
| 11 | Composição de dependências | **A** | Construção toda na borda; o miolo só recebe |
| 12 | Fronteira entre substratos | **D** (variante de A) | O banco guarda **só a referência à raiz** da wiki, nunca caminho absoluto, nunca conteúdo. Convenção como semente, referência como verdade |
| 13 | Entidade vs propriedade | **A+** | Não há dois regimes: `propor_entidade` e `propor_propriedade`, ambas propostas. Critério é semântico (substantivo novo vs característica de substantivo existente), mora no prompt; estrutura de 2 níveis e confinamento moram no código |
| 14 | Qual grafo manda | **B+** | Passo obrigatório **antes** dos dois grafos: `index.md`. Hierarquia localiza, links associam, links validados na escrita |
| 15 | Manutenção do `index.md` | **D** | `descricao` é campo **obrigatório** da tool e mora no **frontmatter** da página; `index.md` é projeção renderizada por código; o agente nunca o edita. Entidade não tem descrição |
| 16 | Formato do esquema de wiki | **B** | TOML, lido por `tomllib`; serializador próprio para gravar; esquema é dado, arquivo é serialização |
| 17 | Dívidas TD-01 a TD-04 | **A+** | Morrem dentro da unidade que reescreve o componente, **mas** cada uma vira critério de aceite nomeado com teste de regressão |

### Reconciliações que eu faço sozinho, sem perguntar

Anoto para você poder discordar, mas não bloqueiam:

- **Nome das tools.** A Pergunta 10 falava em `propor_escrita`; as Perguntas 13 e 15 refinaram para
  `propor_entidade` e `propor_propriedade(entidade, propriedade, conteudo, descricao, links)`.
  Adoto o par das Perguntas 13/15. Conjunto final: `listar`, `ler`, `buscar`, `propor_entidade`,
  `propor_propriedade`.
- **Mapeamento das dívidas.** Confirmei contra `code-quality-assessment.md`: TD-01 = `responder()`
  devolve `None`; TD-02 = SDK no núcleo; TD-03 = `KeyError` na primeira anotação; TD-04 =
  persistência inexistente. O seu mapeamento na resposta 17 está correto. TD-11 (argumentos com
  espaços) também existe e morre no parser, como você escreveu.
- **Mensagens órfãs** (consequência de 3B): quando um chat é apagado, o serviço de aplicação apaga
  as mensagens dele na mesma transação. Sem varredura, sem lixo tolerado.
- **Materialização da wiki na criação do ambiente** não é proposta: é ação do sistema a partir do
  esquema, não escrita do agente. O regime "toda escrita é proposta" vale para o bibliotecário.

### Risco que eu registro, e que não vira pergunta porque você já respondeu duas vezes

"Toda escrita na wiki é proposta" (9A + 13A) tem um custo de uso: se aprovar for frequente e
chato, a revisão vira carimbo, e aí a defesa principal de RNF-14 existe no papel e não na prática.
Isso não é motivo para mudar a decisão — é motivo para o desenho permitir que **uma proposta
carregue várias páginas de uma vez**, para que aprovar seja um ato por promoção, e não um ato por
arquivo. Vou desenhar assim, salvo objeção.

---

## 2. O que está bloqueando

| # | Problema | Tipo |
|---|---|---|
| A | Pergunta 8 sem resposta | Resposta ausente |
| B | A resposta 15 traz o **lint** de volta; FOR-12 o tirou do escopo | Contradição com requisito aprovado |
| C | A resposta 16 acrescenta catálogo de maquetes e "salvar como maquete" | Escopo novo, fora das 14 histórias |
| D | A resposta 12 quer representar wiki fora da raiz de dados, mas o localizador escolhido não consegue | Inconsistência interna |
| E | Resposta 5 (tudo assíncrono) × resposta 7 (`executar: Callable[...]`, síncrono) | Contradição entre duas respostas |
| F | O que exatamente a transcrição persiste nunca foi decidido | Critério indefinido |

---

## 3. Perguntas

### Pergunta A — Política de gravação (Pergunta 8, sem resposta)

Ficou em branco. E ela mudou de forma depois que você respondeu 3B e 5B: com transcrição em tabela
append-only e resposta chegando por streaming, existe uma decisão embutida que a versão original
não expunha — **quando a mensagem do agente vira linha no banco**.

Se ela só é gravada no fim do turno, uma queda no meio de uma resposta longa perde a resposta
inteira. Se é gravada incrementalmente, nada se perde, mas o banco recebe um `UPDATE` por pedaço
de texto, e passa a existir o estado "mensagem incompleta" que o carregamento precisa saber tratar.

A) Gravar ao fim de cada operação que muda estado, numa transação por operação; a mensagem do
agente é gravada **uma vez, no fim do turno**

B) **(recomendo)** Igual a (A), mas a mensagem do agente é inserida **no começo** do turno e
atualizada conforme o streaming avança, com marca de "em andamento" removida no fim. Queda no meio
preserva o que já chegou; o carregamento sabe distinguir turno interrompido de turno completo

C) Gravar por comando explícito do usuário (`/salvar`)

D) Gravar periodicamente em segundo plano

E) Other (please describe after [Answer]: tag below)

[Answer]: B 

---

### Pergunta B — O lint entra nesta iteração?

**O conflito, na letra.** FOR-12 (aprovado na v2 de `requirements.md`) diz: *"Operações de wiki
`ingest` (pasta `raw/`) e `lint` — fora de escopo"*. A sua resposta 15 descreve o lint como um dos
**dois mecanismos de manutenção da wiki**, com escopo detalhado (páginas sem descrição, descrição
desatualizada, link quebrado, propriedade que deveria ser entidade, duplicação, página órfã) e diz
"a intenção é reaproveitar esse processo aqui — o detalhamento fica para o momento adequado".

Ler isso como "está dentro" muda requisitos, histórias e plano. Ler como "está fora" e seguir
adiante seria eu escolher por você numa contradição que eu detectei.

Vale notar o que mudou desde que FOR-12 foi decidido: naquele momento o argumento foi *"links são
validados no momento da escrita, o que evita a maior parte do apodrecimento sem existir processo
de lint"*. Isso continua verdade para link quebrado — mas **não** cobre descrição desatualizada
nem propriedade que virou entidade, que são exatamente os itens que a sua resposta 15 lista.

A) **Fora**, FOR-12 mantido como está. O desenho não menciona lint

B) **(recomendo)** **Fora nesta iteração, com ponto de extensão explícito e registrado**: o lint
não é implementado, mas o desenho garante que ele é acrescentável sem redesenho — ele seria mais
um produtor de propostas, usando o mesmo mecanismo de proposta e aprovação que o bibliotecário já
usa. Custo hoje: zero linhas, um parágrafo no documento de desenho

C) **Dentro**: o lint entra nesta iteração. Exige emenda v3 em `requirements.md` (revogar FOR-12),
uma história nova, e mais superfície na TUI

D) Other (please describe after [Answer]: tag below)

[Answer]: A - vamos deixar de fora, nao temos que pensar nisso nesse momento, eu tinha explicado somente para deixar a expliacao completa. a questao do lint nao precisa ser pensado agora nem anotado pois isso se resolve apenas tento o bibliotecario. se nos implementarmos o bibliotecario eu nao vou esquecer dessa questao da ideia do lint pois eu vou ter que pensar o bibliotecario em mais detalhes depois no futuro, e nesse momento vai ser o momento mais correto de detalhar o lint e implementa-lo de fato. 

---

### Pergunta C — Quanto do fluxo de maquetes de wiki entra agora?

A resposta 16 descreve três coisas, e só parte delas está nas histórias aprovadas.

Fui checar US-09: os critérios de aceite dizem *"quando ele **define** as categorias iniciais da
wiki"* — ou seja, **o usuário digitar as entidades na criação do ambiente já está dentro**, é o
que a história pede. Já *"escolher entre maquetes prontas distribuídas com o software"* e
*"salvar como maquete para reusar e distribuir"* não aparecem em nenhuma das 14 histórias.

"Salvar como maquete" também é o único motivo pelo qual precisamos **escrever** TOML — `tomllib`
só lê. Sem ele, o serializador próprio (~20 linhas) e seu teste não existem.

A) Só o formulário: o usuário digita as entidades na criação. É o mínimo que satisfaz US-09 e
RF-F15. Nenhum arquivo `.toml` é lido nem escrito nesta iteração

B) **(recomendo)** Formulário **+ maquetes embutidas** distribuídas com o software (somente
leitura, `tomllib`). Cobre US-09, entrega o "não hardcodar a wiki do João" que motivou ESC-19, e o
João começa com uma wiki de aquisição pronta em vez de tela em branco. Sem serializador

C) B **+ "salvar como maquete"** (serializador próprio, maquetes do usuário no diretório de dados)

D) Other (please describe after [Answer]: tag below)

[Answer]: B - vamos fazer a B com boas razoes. vamos ter as maquetes reutilizaveis nessa iteracao e vamos fazer pelo menos uma que é a do meu cliente joao. ai quando eu der o software na mao dele ele consegue usar a maquete pre pronta. e o formulario é bom para ele conseguir testar o software criando outros ambientes. dessa forma tambem ja garantimos que nao estamos hardcodando a wiki do ambiente do joao, e que so estamos montando uma maquela ja de sugestao.  vamos deixar a ideia de salvar como maquete para depois, pois nao pensei nos detalhes ainda de como seria salva e oque seria salva para dentro da maquete.

---

### Pergunta D — Forma do localizador da raiz da wiki

Aqui há uma inconsistência dentro da própria resposta 12, e ela é da sua argumentação, não da
escolha.

Você justificou (D) dizendo que a convenção é errada como única forma de saber onde a wiki está,
porque *"se a wiki mora num drive compartilhado, a localização é escolhida por quem configurou o
compartilhamento"*. Mas o localizador que você escolheu é `wikis/<id_ambiente>`, **relativo à raiz
de dados**. Um caminho relativo a uma raiz não consegue apontar para fora dessa raiz — e apontar
para fora exigiria caminho absoluto, que RNF-11 proíbe.

Ou seja: a escolha está certa para esta iteração, mas do jeito que está ela **não** entrega a
representabilidade futura que foi o argumento para escolhê-la. Isso se conserta barato, agora.

A) Manter `wikis/<id_ambiente>`, string relativa simples. Nesta iteração a wiki sempre mora sob a
raiz de dados, e a representabilidade do caso compartilhado fica para quando existir

B) **(recomendo)** Localizador **com esquema explícito** — `dados:wikis/<id_ambiente>` — em que a
parte antes de `:` diz **como resolver** e o adaptador conhece os esquemas. Hoje existe um só
esquema. Amanhã, `compartilhado:` ou `remoto:` entram sem caminho absoluto e sem migração de dado.
Custo hoje: uma função de resolução e um parse trivial

C) O usuário pode escolher um diretório arbitrário na criação do ambiente **já nesta iteração** —
o que exige decidir como isso convive com RNF-11

D) Other (please describe after [Answer]: tag below)

[Answer]: B - acho bom seguir dessa maneira pois ficamos mais flexiveis e ajustaveis. so um ponto que quero colocar é que para essa iteracao vamos focar no local , no caso que eu imagino para esse primeira iteracao é single-user com o meu usuario conseguindo criar um ambiente que salva localmente para ele usar. 

---

### Pergunta E — O catálogo de ações é síncrono ou assíncrono?

Duas respostas suas se chocam. Na 5 você escolheu porta de sessão **assíncrona nativa**. Na 7 você
escreveu a ação como `executar: Callable[[Alvo, dict], Resultado]` — assinatura **síncrona**.

A pergunta prática: *conversar com o agente é uma ação do catálogo, como as outras?* Se for, o
catálogo precisa ser assíncrono. Se não for, existem duas formas de acionar coisas no sistema, e
a paleta lista uma delas só.

**Fato que precisa entrar na decisão, escolha você o que escolher**: o `sqlite3` é síncrono.
Declarar uma ação `async` não a torna não-bloqueante — a chamada ao banco bloqueia o event loop e,
com ele, a TUI inteira. Para escrita local de poucos KB isso é sub-milissegundo e ninguém percebe;
para carregar um ambiente grande na abertura, pode piscar. A saída padrão é rodar a chamada de
banco num executor de thread nesses pontos. Isso vale para (A) e para (B) igualmente.

A) **(recomendo)** Catálogo **uniformemente assíncrono**; conversar é uma ação como qualquer outra.
Uma superfície só, e a paleta lista tudo. Envelhece melhor: no modo nuvem que você descreveu na
resposta 12, o repositório vira remoto e **toda** ação vira genuinamente assíncrona. Custo: hoje
existe `async` que não espera nada — o que é honestamente uma mentira contida —, e todo teste de
ação precisa de `pytest-asyncio`, que a resposta 5B já obrigou de qualquer forma

B) Catálogo **síncrono** para ações de estrutura (criar frente, renomear, concluir etapa) e a
conversa como caminho separado, assíncrono, fora do catálogo. Ações de estrutura ficam triviais de
testar; em troca, existem duas formas de acionar coisas e a paleta cobre uma

C) Cada ação **declara** se é síncrona ou assíncrona, e quem executa se adapta

D) Other (please describe after [Answer]: tag below)

[Answer]: D — a pergunta acoplava duas decisões independentes, e elas se separam. **E1: catálogo
uniformemente assíncrono** (`executar: Callable[[Alvo, dict], Awaitable[Resultado]]`) — igual ao
(A) nesta parte. **E2: conversar fica FORA do catálogo** — ao contrário do que o (A) propunha.

Motivo de E1: async aqui não é sobre desempenho, é sobre a **forma da fronteira**. A porta de
persistência nasce assíncrona, e no dia em que o armazenamento virar nuvem **só o adaptador muda** —
nenhuma ação, nenhum serviço de aplicação e nenhum teste de ação é reescrito. Com porta síncrona,
esse dia é o dia em que tudo vira async de uma vez, porque rede não tem versão síncrona aceitável
numa TUI. A contaminação do `async` não custa nada nesta iteração: o topo da cadeia (Textual,
`on_input_submitted`) já é assíncrono de fábrica. A feiura aceita conscientemente: por ora existirão
`async def` que não esperam nada de demorado.

Sobre o `sqlite3`: a ação não chama `sqlite3`, chama a porta (decisão 3B / D-ARQ-04). O
`asyncio.to_thread` mora **dentro do adaptador**, aplicado nos pontos que valem a pena (carregar
ambiente na abertura), e não vaza para a assinatura de ninguém.

Motivo de E2: conversar **não devolve `Resultado`** — devolve o iterador assíncrono de eventos da
decisão 5B (pedaço de texto, uso de ferramenta, fim de turno). Enfiá-la no catálogo exigiria alargar
`Resultado` para "ou um `Resultado`, ou um stream", e todo consumidor de ação na TUI ganharia um
`if`. São duas naturezas de saída, então são duas formas de saída. Mesma camada de aplicação, mesma
porta, entrada diferente. O "custo" de a paleta não listar conversar é falso: a paleta lista ações,
e conversar se aciona digitando texto **sem** `/` — ninguém procura "conversar" numa lista de
comandos.

Opção (C) recusada explicitamente: transforma "esta ação bloqueia a TUI?" em algo que só se descobre
lendo a implementação de cada ação, em vez de saber pela assinatura.

Escopo desta iteração reafirmado: single-user, armazenamento **local**. A escolha async é o que
mantém essa simplicidade sem hipotecar o modo nuvem.

---

### Pergunta F — O que a transcrição persiste?

Nunca foi decidido, e agora precisa ser: a resposta 3B criou a tabela de mensagens, e a resposta 5B
fez a porta emitir eventos de tipos diferentes (pedaço de texto, uso de ferramenta, fim de turno).

Isso decide o que o usuário vê ao reabrir uma tarefa (US-06) e o que fica auditável de uma
promoção à wiki.

**Nota de honestidade sobre a sua resposta 10**: um dos três argumentos que você usou para
descartar a opção (A) foi que o caminho absoluto de uma ferramenta nativa *"aparece na chamada de
tool, que entra na transcrição persistida"*. Esse argumento **só é válido se a resposta aqui for
(B) ou (C)**. Os outros dois argumentos que você deu (incompatível com 9A; funda a segurança em
algo não medido) se sustentam sozinhos, então a decisão 10B não muda — mas a justificativa dela
precisa perder essa perna se você responder (A).

A) Só as mensagens de texto de usuário e agente. É o que a TUI mostra hoje

B) **(recomendo)** Mensagens de texto **+ registro do uso de ferramenta** (qual tool, parâmetros
resumidos, resultado resumido). É o que torna auditável *por que* o bibliotecário propôs aquilo, e
o que faz a transcrição reabrir contando a história completa em vez de saltos inexplicados

C) Todos os eventos do stream, incluindo pedaços parciais de texto

D) Other (please describe after [Answer]: tag below)

[Answer]: B

> **[Revogação parcial — 2026-08-26, NFR Requirements de U2, Q6]** A metade "**resultado
> resumido**" desta resposta **sai desta iteração**; "qual tool + parâmetros resumidos" continua
> valendo. Dois motivos: (1) a justificativa registrada aqui era auditoria do que o bibliotecário
> propôs, mas **US-14 pede revisão antes de salvar**, em fluxo vivo — nenhum critério de aceite
> desta iteração lê resultado de ferramenta depois do fato; (2) no stream do SDK o resultado **não
> existe** no instante do evento de uso, e nenhuma unidade tem desenhada a correlação entre chamada
> e resultado que preencheria o campo. A resposta original fica registrada como foi dada.

---

## 4. Higiene do `application-design-plan.md`

O arquivo tem hoje 1.951 linhas. Da linha ~509 até ~1.690 há transcrição de conversa colada, com
os blocos das Perguntas 7, 9, 10, 11, 12, 13 e 14 duplicados — algumas cópias com `[Answer]:`
vazia. Extraí as respostas canônicas pela **última** ocorrência preenchida de cada pergunta, que é
o que a §1 registra.

Isso é um problema de artefato, não de conteúdo: o plano é documento de auditoria do AI-DLC, e
hoje ele tem três respostas diferentes para a mesma pergunta. Sugiro reescrevê-lo preservando
**todo o seu raciocínio** (que é bom e precisa ficar registrado) na resposta canônica de cada
pergunta, e removendo as cópias duplicadas e os fragmentos de interface colados ("19h 17h Read
application-design-plan.md", "Your modified files", "+51 -2").

Não faço isso sem a sua palavra, porque não há Git em `aidlc-docs/` e a remoção seria irreversível.


### Pergunta G — Posso limpar o plano?

A) **(recomendo)** Sim: reescrever `application-design-plan.md` preservando integralmente o
raciocínio de cada resposta, removendo blocos duplicados e fragmentos de interface

B) Sim, mas salvando antes uma cópia integral do arquivo atual como
`application-design-plan.raw.md`

C) Não, deixe como está

D) Other (please describe after [Answer]: tag below)

[Answer]: A - sim faca o ajuste de limpeza no documento para manter organizado
