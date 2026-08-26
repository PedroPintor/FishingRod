# Plano de Application Design — FishingRod, Iteração 1

**Estágio:** INCEPTION — Application Design · **Profundidade:** comprehensive
**Data:** 2026-08-20 · **Limpo em:** 2026-08-23 (autorizado pela Pergunta G = A)
**Base:** `execution-plan.md` v2 (aprovado), `requirements.md` v2 (§9), `stories.md` (linha fina,
14 histórias), artefatos de Reverse Engineering, notas retidas em `aidlc-state.md`

> **Higiene deste documento.** A versão anterior tinha 1.951 linhas, das quais ~1.180 eram
> transcrição de conversa colada, com os blocos das Perguntas 7, 9, 10, 11, 12, 13 e 14
> duplicados e tags `[Answer]:` vazias em cópias repetidas. O usuário autorizou a limpeza na
> Pergunta G. O arquivo original está preservado integralmente em
> **`application-design-plan.bruto-2026-08-23.md`**, no mesmo diretório — nada foi perdido.
> Esta versão mantém, para cada pergunta: o enunciado, as opções, a resposta canônica e **todo o
> raciocínio do usuário**, sem as cópias duplicadas nem os fragmentos de interface
> ("Your modified files", "+51 -2", "Read application-design-plan.md #L60-169").

---

## 1. Escopo deste estágio

Application Design responde **quais componentes existem, o que cada um responde por, qual é a
assinatura de fronteira e quem depende de quem**. Não responde regra de negócio detalhada — isso é
Functional Design, por unidade, na fase de CONSTRUCTION.

### Decisões que este estágio precisa fechar

Vindas de `requirements.md` §6 e §9.8 e das notas retidas em `aidlc-state.md`:

| # | Decisão aberta | Por que ela é deste estágio | Fechada em |
|---|---|---|---|
| 1 | Forma da cadeia `Ambiente → Projeto → Sessao` | O usuário registrou dúvida explícita sobre ela olhando para o futuro do produto | Pergunta 1 |
| 2 | Desenho da identidade (tipo, onde nasce, como atravessa serialização) | Decisão de maior alcance da iteração — atravessa domínio, banco, wiki e TUI | Pergunta 4 |
| 3 | Fronteira da porta de persistência e o que é documento vs tabela | D-ARQ-04 exige porta em vocabulário de domínio; a divisão híbrida ainda não existe | Perguntas 3, 8, A, F |
| 4 | Forma concreta da porta de sessão sobre o ciclo assíncrono do SDK | ESC-18 fixou o ciclo medido pelo spike; falta a assinatura e como o streaming chega à TUI | Perguntas 5, 6 |
| 5 | Critério do bibliotecário entre criar entidade e criar propriedade | **Risco número um do desenho da wiki**; sem regra, a wiki apodrece em semanas | Pergunta 13 |
| 6 | Qual grafo manda na recuperação: hierarquia de pastas ou links `[[...]]` | Determina como o `index.md` é construído e mantido | Perguntas 14, 15 |
| 7 | Assinaturas das tools de wiki e escopo de permissão das ferramentas de arquivo | O spike mediu permissão de tool **MCP**; escopo de ferramenta de **arquivo** não foi medido | Perguntas 9, 10 |
| 8 | Ordem técnica das dívidas TD-01 a TD-04 | O usuário pediu que a correção venha **depois** de a arquitetura fechar | Pergunta 17 |

### Fora deste estágio

Regras de negócio detalhadas, esquema SQL literal, prompts dos agentes, layout de tela,
decomposição em unidades (Units Generation), stack de teste e política de NFR (NFR Requirements).

---

## 2. Fatos verificados no código, que sustentam as perguntas

Levantados por inspeção, não presumidos:

- `Ambiente/agente.py:6` importa `ClaudeAgentOptions` do SDK no núcleo — viola RF-F04 hoje.
- `AgenteClaude.responder()` (`agente.py:45-46`) retorna `None`.
- `AgenteDoSistema` (`agente.py:72-75`) é uma **lista de instâncias compartilhadas** no nível do
  módulo. `Chat(agente=OrquestradorTeste)` guarda referência à *mesma* instância em todos os
  chats de todos os ambientes. Qualquer estado de sessão colocado no agente vaza entre chats.
- `Sessao.enviar()` (`sessao.py:135-144`) é **síncrono** e chama `chat.agente.responder(mensagem)`
  direto. O ciclo do SDK é assíncrono. Esse é o ponto exato onde a porta de sessão entra.
- Endereçamento é posicional (`indice_ativo` em `Ambiente`, `Projeto` e `Sessao`) e nominal
  (`_buscar_sessao(nome)`, `buscar_projeto(nome)`), e `/nome-chat` renomeia chat em runtime
  (`sessao.py:94-98`) — por isso nome não serve como identidade.
- `Memoria.anotar()` (`memoria.py:16-19`) levanta `KeyError` na primeira escrita de chave nova.
- Roteamento de comando está **dentro do domínio**: cada andar tem `_detectar_comando_*` e
  `_acionar_comando`, e `enviar()` decide entre executar comando e delegar para o andar de baixo.
- Vocabulário: `Projeto` ≈ frente, `Sessao` ≈ tarefa, `Memoria` pende de `Sessao` (logo, memória
  por tarefa já é verdade estrutural).

### Fatos medidos pelo spike (`testes-de-aprendizado/spike_claudeSDK.py`)

São medições de execução real, não leitura de documentação. Sustentam as Perguntas 5, 6 e 10:

- **Ciclo de vida**: `async with ClaudeSDKClient(options=...)` → `await client.query(txt)` →
  `async for msg in client.receive_response()`.
- **Dois clients vivos simultaneamente no mesmo event loop funcionam** (`async with A, B:`). A
  restrição da docstring do SDK é usar *um* client em contextos async diferentes, não ter dois.
  Isso é o que torna o bibliotecário-como-sub-agente barato: ele ganha a própria sessão viva.
- **Tools MCP in-process com closure**: `create_sdk_mcp_server` roda no mesmo processo, sem
  serialização. Argumentos amarrados por closure (ex.: autor, raiz da wiki) são **inalcançáveis
  pelo modelo** — não existem no schema, então não há onde escrever uma mentira. Medido: mesmo
  instruído a forjar o autor, o agente não conseguiu.
- **Nome qualificado da tool**: `mcp__<chave de options.mcp_servers>__<nome da tool>`.
- **`tools=[]` desliga todas as ferramentas nativas** (Read/Write/Edit/Bash/...) sem afetar as
  tools MCP. É o mecanismo concreto de "ferramentas nativas de escrita negadas" (Pergunta 10).
- **Permissão**: com `permission_mode` padrão, tool MCP não é auto-aprovada. Ou o nome
  qualificado entra em `allowed_tools`, ou existe `can_use_tool`. Sem nenhum dos dois o SDK não
  trava — o CLI nega, o handler Python nunca roda, e a negação aparece em
  `ResultMessage.permission_denials`.
- **Isolamento**: `strict_mcp_config=True` e `setting_sources=[]` impedem que `.mcp.json` do
  projeto e `CLAUDE.md` do disco entrem na sessão.

---

## 3. Perguntas de decisão — rodada 1

### Categoria A — Identificação de componentes

#### Pergunta 1 — A cadeia `Ambiente → Projeto → Sessao`

Hoje cada andar faz três trabalhos ao mesmo tempo: guarda estado, roteia comando e delega
mensagem. Isso funciona no console porque só existe uma entrada (uma string). Com persistência,
TUI e agente com ferramentas, a mesma classe passaria a decidir também quando salvar e como tratar
falha do provedor — quatro responsabilidades numa classe.

O custo de mexer: é a mudança de maior superfície da iteração, toca os três arquivos do núcleo e a
TUI. O custo de **não** mexer: cada capacidade nova entra empilhando `if` em `enviar()`.

A) Manter a cadeia como está: estado, roteamento e delegação juntos em cada andar

B) **(recomendo)** Manter a hierarquia de dados (ambiente contém frentes, frente contém tarefas),
mas **tirar o roteamento e a delegação de dentro dela**: o domínio passa a ter estado e
invariantes; um serviço de aplicação recebe a mensagem, decide se é comando ou conversa, chama o
domínio e a porta de sessão, e salva

C) Achatar a hierarquia: um único agregado `Ambiente` com coleções indexadas por identidade, sem
os andares intermediários como objetos com comportamento

D) Other (please describe after [Answer]: tag below)

[Answer]: B — essa cadeia eu tinha feito inicialmente, mas já percebi que era ruim depois de um
tempo que eu estava implementando. Temos que adaptar a cadeia para se adequar às nossas
necessidades do software.

---

#### Pergunta 2 — Organização dos pacotes dentro de `src/`

ESC-15 já fixou layout `src/` com pacote real. Falta a divisão interna. Note que o núcleo precisa
rodar **sem** `claude_agent_sdk` instalado (RF-F04), o que fica trivial de provar se a fronteira
for visível no nome do pacote.

A) **(recomendo)** Por camada: `dominio/`, `aplicacao/` (serviços + portas), `adaptadores/`
(SQLite, Claude, wiki), `interface/` (TUI). A regra "quem pode importar quem" é verificável por
inspeção do import

B) Por fatia vertical: `ambiente/`, `tarefa/`, `wiki/`, `agente/`, cada uma com seu domínio e seu
adaptador dentro

C) Manter a divisão atual traduzida (`ambiente/`, `model/`) e acrescentar pacotes novos conforme
necessário

D) Other (please describe after [Answer]: tag below)

[Answer]: A — vamos seguir com essa organização. Eu gostei.

---

#### Pergunta 3 — Fronteira do agregado para persistência

Isto decide o que é salvo atomicamente junto. Com um agregado só, cada mensagem nova reescreve o
documento do ambiente inteiro. Com agregados separados, salvar uma tarefa não toca as outras, mas
a integridade entre eles passa a ser responsabilidade do código.

A) Um agregado único `Ambiente` (frentes, tarefas, chats, memória tudo dentro) — salvo inteiro a
cada mudança

B) **(recomendo)** `Ambiente` guarda a estrutura (frentes, tarefas, chats: identidade, nome,
etapas, agente, memória) como documento; **transcrição de mensagens é tabela separada**,
append-only, referenciada por identidade de chat. Salvar um turno de conversa escreve uma linha, e
não o documento todo

C) Cada tarefa é seu próprio agregado persistido, e o ambiente guarda só referências

D) Other (please describe after [Answer]: tag below)

[Answer]: B — vamos comprar a escrita constante, paralelismo e consultabilidade pagando com um
mapeamento a mais e integridade referencial manual.

**Raciocínio preservado da discussão.** Agregado é a unidade que é carregada inteira, validada
inteira e salva inteira, numa transação. A pergunta prática é: qual é o menor *write* possível
quando o usuário manda uma mensagem?

Os dois dados têm comportamentos opostos, e é isso que justifica separá-los:

| | estrutura (frentes/tarefas/chats/memória) | transcrição |
|---|---|---|
| tamanho | pequeno, limitado | cresce sem limite |
| muda quando | usuário cria/renomeia/avança etapa (raro) | cada turno (constante) |
| forma da mudança | edição no meio | só append |
| invariante entre itens | sim | não — mensagem só precisa de um `id_chat` |

Com (A), o fluxo de uma mensagem é: ler a linha → parsear o JSON inteiro → acrescentar 2 itens →
serializar tudo → `UPDATE` da linha inteira. Custo O(tamanho total do histórico) por turno.
Com (B), é um `INSERT` de tamanho fixo.

Três fatos do software empurram para (B):

1. **Frentes paralelas são o propósito do produto.** Um único documento como ponto de escrita é
   contradição arquitetural com a feature principal: dois chats de tarefas diferentes escreveriam
   a mesma linha, e um sobrescreveria o outro sem versão otimista e merge.
2. **A transcrição é o único dado ilimitado.** Todo o resto (nomes, etapas, memória) é minúsculo e
   estável. (A) colocaria o único dado que cresce sem limite dentro do único documento reescrito
   por inteiro.
3. **Streaming do SDK.** A resposta chega em pedaços; append-only é a forma natural disso, e (A) é
   a forma mais hostil (ou acumula tudo em memória e perde se cair, ou reescreve o documento a
   cada chunk).

Ganho lateral que fecha com a Pergunta 4: UUIDv7 é ordenável por tempo, então `ORDER BY id` já é a
ordem cronológica — sem coluna extra nem contador. E paginação vira SQL
(`WHERE id_chat = ? ORDER BY id DESC LIMIT 50`), o que importa para a TUI abrir uma tarefa sem
carregar o histórico todo.

Custos aceitos conscientemente: dois mapeamentos em vez de um; integridade referencial manual
(`id_chat` aponta para um id que vive dentro do JSON, e o SQLite não tem FK para isso); transação
atravessando os dois (resolvível com a mesma conexão); e `Chat` deixa de carregar a lista de
mensagens dentro de si — carregar um chat completo vira composição feita pelo serviço.

---

#### Pergunta 3-bis — Bibliotecário e rod-maker são agentes ou módulos? *(surgida durante a rodada 1)*

Esta pergunta não estava no plano original. Ela nasceu de uma **imprecisão minha**: ao resumir a
Pergunta 10 eu escrevi "o bibliotecário implementado como funções Python puras", o que descreve as
*ferramentas* do bibliotecário, não o bibliotecário. O usuário percebeu a colagem e levantou a
suspeita. Registro aqui por rastreabilidade honesta.

[Answer]: **Agentes de primeira classe.** Palavra do usuário: *"você tem razão, eu me precipitei
com a ideia de transformar o bibliotecário e o rod-maker em apenas ferramentas; realmente eles
precisam ser agentes, pois eles têm e precisam ter julgamento para executar as tarefas, e isso se
faz com os agentes."*

O teste que separa os dois: **é agente se a função exige julgamento que não se reduz a regra; é
ferramenta se o comportamento é determinístico dado o input.** O bibliotecário escolhe o título da
propriedade, redige o markdown no estilo da wiki, decide quais `[[links]]` fazem sentido, percebe
que a informação nova contradiz algo já escrito, e decide entre entidade e propriedade (Pergunta
13, o "risco número um"). Nada disso é expressável como `if`. O código atual já dizia isso:
`Papel.SUB_AGENTE` e `NOME_SUB_AGENTE_ROD_MAKER` existem em `agente.py` desde o começo.

**O que discrimina a decisão — e o que não discrimina.** O modelo de uso desejado pelo usuário
(falar com o orquestrador, que aciona bibliotecário e rod-maker) é bom, mas **não** é argumento:
o orquestrador poderia receber as tools de wiki diretamente e a experiência seria indistinguível.
O que discrimina de verdade são três coisas:

1. **Isolamento de contexto.** O bibliotecário precisa carregar esquema da wiki, `index.md`, regra
   entidade-vs-propriedade, convenções de redação e o conteúdo que leu para decidir. Se tudo isso
   entra na janela do orquestrador, o orquestrador piora a cada registro na wiki.
2. **Quarentena de conteúdo não confiável** — o argumento mais forte e menos óbvio. RNF-14 trata a
   wiki como entrada não confiável. Se o orquestrador lê a wiki direto, uma injeção entra na
   conversa que tem autoridade sobre tudo. Com sub-agente, o conteúdo suspeito é absorvido por um
   agente com poucas ferramentas e nenhuma autoridade (ele nem escreve — Pergunta 9A), e o que
   volta é uma proposta estruturada, não texto livre. Isso dá **duas defesas em profundidade** para
   RNF-14: confinamento no código (cerca) e isolamento de contexto (quarentena).
3. **Afinar independente.** A qualidade da wiki depende do prompt do bibliotecário, e ele vai ser
   iterado muito. Fundido com o do orquestrador, cada ajuste arrisca degradar a conversa e não há
   como atribuir causa.

**Custo, e por que ele é menor do que parecia.** Mais uma chamada de LLM (latência e consumo) e
encanamento agente-para-agente. Na hora em que essa discussão aconteceu, o custo aberto era "a
porta de sessão precisa ser reentrante ou aninhável?". **O spike já respondeu**: dois
`ClaudeSDKClient` vivos ao mesmo tempo no mesmo event loop funcionam. Então não há reentrância a
inventar — o bibliotecário abre a **própria** sessão viva pela mesma porta.

**Escopo**: o rod-maker fica **fora desta iteração** (US-11 e US-12 adiadas por FOR-14). Ele
permanece no desenho apenas como `Papel.SUB_AGENTE` já suportado, sem implementação.

**Alerta registrado**: "o orquestrador sugerir armazenar informação" e "sugerir construir um
agente" são **proatividade** — provavelmente FOR-06, fora desta iteração. A arquitetura permite
(o orquestrador conhece o catálogo de ações e as capacidades dos sub-agentes), mas a implementação
da sugestão fica para depois.

---

### Categoria B — Métodos e contratos de fronteira

#### Pergunta 4 — Desenho da identidade

RF-F16 e ESC-14 já fixaram identidade opaca e estável. Falta o tipo e o lugar onde ela nasce. Se a
identidade nascer no adaptador de persistência, o domínio fica com objeto sem identidade até ser
salvo — e a TUI precisa referenciar coisas que ainda não foram salvas.

A) `uuid.uuid4()` da stdlib, gerada no construtor da entidade de domínio

B) **(recomendo)** UUIDv7 (ordenável por tempo, `uuid.uuid7()` existe a partir do Python 3.14; no
3.13 é gerado por implementação própria de ~10 linhas ou dependência mínima), gerada no construtor
da entidade de domínio. Ordenável por tempo dá ordenação estável de transcrição e paginação sem
coluna extra

C) ULID via dependência externa, gerada no construtor da entidade de domínio

D) Identidade gerada pela persistência (autoincremento do SQLite), e o domínio só a recebe depois
de salvar

E) Other (please describe after [Answer]: tag below)

[Answer]: B — vamos seguir com a ordenabilidade e o tempo de criação da identidade.

---

#### Pergunta 5 — Forma da porta de sessão viva

O spike mediu o ciclo real: `async with ClaudeSDKClient(...)` → `query()` → `receive_response()` →
saída do contexto. O Textual roda em asyncio e `on_input_submitted` já é async. A pergunta é o que
a porta expõe para o serviço de aplicação.

A) Porta síncrona (`abrir`/`enviar`/`fechar` normais) e o adaptador esconde o asyncio internamente
(`asyncio.run` ou loop próprio em thread). Núcleo simples, mas paga ponte thread↔loop e perde
streaming natural

B) **(recomendo)** Porta assíncrona nativa: `abrir()` async retornando uma sessão, `enviar()` async
devolvendo um **iterador assíncrono de eventos** (pedaço de texto, uso de ferramenta, fim de
turno), `fechar()` async. Casa com o Textual sem ponte e entrega streaming de graça. Custo: o
serviço de aplicação que a usa também é async, e teste de domínio precisa de `pytest-asyncio`

C) Porta assíncrona que devolve a resposta **completa** de uma vez (sem iterador). Mais simples de
testar; sem streaming — o usuário espera a resposta inteira olhando para uma tela parada

D) Other (please describe after [Answer]: tag below)

[Answer]: B — vamos seguir com a porta assíncrona nativa.

---

#### Pergunta 6 — Agente vs sessão viva (o problema da instância compartilhada)

`AgenteDoSistema` são instâncias compartilhadas entre todos os chats. Se a sessão do SDK morar
dentro do objeto agente, dois chats abertos com o mesmo agente compartilham histórico — que é
exatamente o risco 7 do plano ("misturar histórico entre chats").

A) **(recomendo)** `Agente` vira **configuração imutável** (nome, papel, modelo, ferramentas,
regras) e pode continuar compartilhada; a **sessão viva** é um objeto separado, criado por chat,
cujo dono é o chat/serviço. `Agente.responder()` deixa de existir

B) Cada chat recebe uma **cópia** do agente, e a sessão viva mora dentro da cópia

C) Manter `Agente.responder()` como método, e o agente resolve internamente qual sessão usar a
partir de um identificador de chat recebido como parâmetro

D) Other (please describe after [Answer]: tag below)

[Answer]: A — vamos seguir com a configuração imutável e a sessão viva separada.

---

### Categoria C — Camada de serviço

#### Pergunta 7 — Onde mora o roteamento de comando (`/frentes`, `/nova-tarefa`, `/nome-chat`)

Hoje mora no domínio. O mockup do usuário mantém paleta acionada por `/`, então o vocabulário de
comando sobrevive. RF-F17 exige que "a regra que a TUI aciona é a mesma que um comando aciona".

A) Manter no domínio, como hoje (`_detectar_comando` + `_acionar_comando` por andar)

B) **(recomendo)** Um serviço de comandos na camada de aplicação: traduz a string em uma chamada
de serviço e devolve mensagem de sistema. Domínio não conhece a sintaxe `/`, e a TUI ganha os
mesmos comandos sem duplicar regra

C) Na interface (TUI), que traduz o comando e chama os serviços diretamente

D) Other (please describe after [Answer]: tag below)

[Answer]: B — **com a ressalva de que "serviço de comandos" deve ser lido como "catálogo de ações
+ parser separado", não como uma função que recebe string.**

Formulação da decisão, na palavra do usuário:

> Comandos não são um recurso da interface de texto — são o vocabulário de ações do ambiente. A
> sintaxe `/` é uma de várias formas de acionar esse vocabulário, ao lado de botões, atalhos e,
> futuramente, do próprio agente. Portanto o catálogo de ações pertence à camada de aplicação, o
> parser `/` é um adaptador de entrada descartável, e o domínio permanece sem conhecimento de
> qualquer sintaxe. Isso torna o RF-F17 uma propriedade da arquitetura em vez de uma convenção a
> ser mantida manualmente.

**O problema real, nomeado.** Não é "comandos". É: *um conjunto de ações sobre o ambiente, exposto
por múltiplas superfícies (botão, atalho, texto `/`, e mais tarde o próprio agente), sem que a
regra seja reimplementada em cada superfície.* Três partes hoje estão coladas:

| parte | pergunta que responde | hoje mora em |
|---|---|---|
| catálogo de ações | o que dá para fazer com o ambiente? | espalhado: `enum Comando` + `match/case` em 3 classes |
| sintaxe/parsing | como `"/nova-tarefa X"` vira "ação nova-tarefa com argumento X"? | `mensagem.split()` dentro do domínio |
| execução | quem realmente muda o estado? | os mesmos `match/case` |

**Quatro efeitos observáveis do desenho atual** (nenhum deles se resolve só "mudando de camada"):

1. **O roteamento depende de onde você está.** `Ambiente.enviar → Projeto.enviar → Sessao.enviar`
   roteia pelo nó ativo, então `/nome-chat` age sobre o chat ativo da sessão ativa do projeto
   ativo. Um botão numa lista precisa dizer *qual* item, e a cadeia não tem como receber isso.
2. **O resultado é uma string.** `_acionar_comando` devolve `"Erro - Sessao indice [3] nao existe"`.
   A TUI não tem como saber se deu certo, nem testar sem comparar texto em português.
3. **O catálogo não é consultável.** A paleta `/` precisa listar comandos, mostrar descrição e
   saber quantos argumentos cada um pede. `match/case` é código, não dado — exigiria uma segunda
   lista mantida à mão, que vai dessincronizar.
4. **`Sessao` é o pega-tudo.** Ela assume qualquer `/` porque é o último andar, inclusive para
   dizer "não conheço". O erro de comando desconhecido é regra de interface implementada na camada
   mais profunda do domínio.

**A forma adotada** — quatro peças:

```
TUI: paleta "/"  ──► Parser (aplicação) ──┐
TUI: botão       ─────────────────────────┤
TUI: atalho      ─────────────────────────┼──► Ação (aplicação) ──► Domínio
Agente (futuro)  ─────────────────────────┘         │
                                            ┌───────┴───────┐
                                         Catálogo      Resultado
                                      (metadados)   (tipado, não string)
```

1. **Ação como objeto de primeira classe na aplicação.** Um registro (dado), não um `match/case`.
   A paleta itera sobre ele, filtra por escopo, gera o formulário de argumentos e valida antes de
   executar. Um `match/case` não pode ser lido por ninguém.
2. **O parser `/` é adaptador de entrada, e é fino.** Única responsabilidade:
   `"/nova-tarefa campanha de verao"` → `("nova-tarefa", {"nome": "campanha de verao"})`. Não
   conhece regra de negócio. Um botão pula essa etapa e chama a ação direto com argumentos já
   tipados. TD-11 (espaços quebram argumento) deixa de ser bug espalhado por 3 classes: vira um
   bug de uma função, com um teste.
3. **Alvo explícito, em vez de "o ativo".** A ação recebe a identidade daquilo sobre o que age
   (encaixe direto com a Pergunta 4). "O item ativo" vira um *default* que o parser preenche
   quando se digita `/`, não uma verdade embutida no domínio.
4. **Resultado tipado.** Sucesso/falha com motivo estruturado. A mensagem em português vira
   responsabilidade da interface, não do núcleo.

**O domínio fica sem saber que comandos existem.** `Frente.criar_tarefa(nome)` continua sendo onde
a invariante mora; a ação é uma casca fina que chama isso, coordena com a persistência e traduz o
resultado — consistente com a Pergunta 1B.

**Ganha**: uma regra, N superfícies (RF-F17 estruturalmente garantido); paleta e botões gerados do
mesmo catálogo; testável sem TUI e sem string; quando o agente ganhar ferramentas, o catálogo já
*é* a lista de tools; autorização contextual tem um lugar único para morar.
**Custa**: ~100–150 linhas a mais que `match/case` para 13 comandos, e uma indireção ao ler.

**Risco explicitamente recusado**: a versão exagerada disso (plugins, descoberta dinâmica,
middleware, undo/redo, decoradores `@comando`) é framework. O registro é um dict literal escrito à
mão. O valor está na separação, não na maquinaria.

---

#### Pergunta 8 — Política de gravação

*Ficou em branco na rodada 1 e foi refeita como **Pergunta A** na rodada 2, porque as respostas 3B
e 5B mudaram a forma da pergunta. Ver §4.*

---

#### Pergunta 9 — Onde mora o portão de revisão humana da escrita na wiki (US-14)

RNF-14 trata a wiki como entrada não confiável e aponta a revisão humana como uma das duas
defesas. A pergunta é quem segura a escrita.

A) **(recomendo)** A ferramenta do bibliotecário **não escreve**: ela devolve uma *proposta* de
escrita (caminho lógico, conteúdo, links). Um serviço de aplicação guarda a proposta pendente, a
TUI mostra, e a escrita só acontece na aprovação. O agente nunca tem poder de escrita direto

B) A ferramenta escreve, mas antes chama um callback de confirmação que a TUI responde

C) A ferramenta escreve em área de rascunho dentro da raiz da wiki, e a aprovação move o arquivo
para o lugar definitivo

D) Other (please describe after [Answer]: tag below)

[Answer]: A — a segurança vai ser via ferramentas que vamos disponibilizar para o bibliotecário.
Eu penso o bibliotecário como a camada de funcionalidades que o agente vai usar para interagir com
a wiki; e para o agente interagir com a wiki ele vai utilizar ferramentas que aplicam regras de
segurança — nesse caso a regra de escrita, onde vai ser feito um processo de aprovação antes de a
escrita ser realizada.

---

### Categoria D — Dependências e comunicação

#### Pergunta 10 — Como o bibliotecário acessa a wiki

ESC-20 diz "exclusivamente pelas ferramentas do bibliotecário". Falta decidir se essas ferramentas
são as nativas do SDK com permissão restrita, ou tools nossas. **Fato relevante**: o spike mediu
permissão de tool **MCP**; permissão de ferramenta de **arquivo** nativa não foi medida. Escolher
(A) transforma uma coisa não medida em fundação da segurança da wiki.

A) Ferramentas de arquivo nativas do agente (Read/Write/Glob/Grep) com permissão restrita à raiz
da wiki, confiando na configuração do SDK

B) **(recomendo)** Tools nossas, expostas ao agente por MCP in-process (caminho já medido pelo
spike): `listar`, `ler`, `buscar`, `propor_escrita`. Ferramentas nativas de escrita **negadas**. O
confinamento de caminho é código nosso, num ponto único, testável sem credencial — e é o que
RF-F14 e RNF-10 pedem

C) Híbrido: leitura pelas nativas (Read/Grep/Glob, baratas e boas), escrita só pela nossa tool

D) Other (please describe after [Answer]: tag below)

[Answer]: B — tools nossas para a wiki, expostas por MCP in-process; ferramentas nativas de
escrita negadas.

**Precisão de vocabulário**: as tools são a *cerca* determinística sobre a wiki. Quem as usa é o
**agente** bibliotecário, que continua sendo agente de primeira classe (ele carrega o julgamento
de curadoria — Perguntas 3-bis e 13). Esta pergunta decide apenas a camada de acesso, não a
natureza do bibliotecário.

**A regra de decisão adotada** (vale para toda tool futura, não só para a wiki):

> Tool nossa quando o acesso carrega uma invariante que o software precisa garantir.
> Ferramenta nativa quando o acesso é genérico e o dano de um mau uso é local.

Classificação por store:

| store | tool | motivo |
|---|---|---|
| wiki | **nossa** | esquema de dois níveis, confinamento de caminho, escrita só por proposta |
| estado do ambiente / transcrição | **nossa** | invariantes de domínio; não existe equivalente nativo |
| busca na web | **nativa** | sem invariante do software; reimplementar é puro retrabalho |
| arquivos do usuário (ex.: a PPT da reunião) | **nativa** (decisão futura) | área livre por definição; classificada aqui só para registrar que a Pergunta 10 **não** decidiu que "tudo é tool nossa" |

**Por que a wiki cai do lado "nossa" — o motivo principal não é segurança, é integridade do
esquema.** ESC-17 trava a wiki em entidade=pasta / propriedade=arquivo, dois níveis. Com `Write`
nativo nada impede `wiki/clientes/acme/2024/q3/notas.md`: a regra vira instrução de prompt, ou
seja, sugestão estatística. Com tool nossa, a assinatura *é* a regra — `propor_propriedade(entidade,
propriedade, ...)` não tem parâmetro para um terceiro nível, e a violação deixa de ser
representável. Isso ataca diretamente o "risco número um" registrado na Pergunta 13.

Isso **não é reinventar `Write`**: `Write` grava bytes num caminho; a tool cria uma propriedade
numa entidade, valida o esquema e devolve uma proposta. Vocabulários diferentes, níveis de
abstração diferentes.

**Por que (A) está descartada** — três motivos independentes, qualquer um suficiente:
1. **Incompatível com a Pergunta 9A**, já decidida: o agente não tem poder de escrita direto. Não
   existe configuração de permissão que transforme "escrever" em "propor".
2. **Incompatível com RNF-11**: ferramenta nativa opera com caminho real do disco, e esse caminho
   aparece na chamada de tool, que entra na transcrição persistida (Perguntas 3 e F). Caminho
   absoluto vazaria para o banco pelo caminho lateral.
3. **Funda a segurança da wiki em algo não medido** — o spike mediu permissão de tool MCP, não
   escopo de ferramenta de arquivo nativa.

**Por que (C) está descartada**, apesar de `Grep`/`Glob` serem genuinamente bons:
- C **não escapa do risco não medido**: para leitura nativa não virar acesso ao disco inteiro, ela
  precisa exatamente da restrição de caminho nativa que não foi verificada.
- Quebra ESC-20 na letra ("exclusivamente pelas ferramentas do bibliotecário").
- **Leitura é o vetor de injeção, não escrita** (RNF-14). Com `ler`/`buscar` nossas, existe um
  ponto único para envelopar o conteúdo como dado (não instrução), truncar e marcar procedência.
  Com `Read` nativo o conteúdo entra cru no contexto, sem ponto de intervenção.
- Vaza o layout físico: sabendo que é filesystem, o agente tenta escrever como filesystem e falha,
  gastando turnos.
- O ganho de qualidade de busca é recuperável sem C: `buscar` pode usar `ripgrep` por baixo,
  confinado à raiz. Reusa-se a ferramenta **sem** reusar a exposição dela ao modelo.

**MCP é formato de exposição, não fronteira de segurança.** In-process, MCP é despacho de função.
A garantia vem do código dentro da tool (confinamento, validação de esquema, fila de aprovação) e
da negação das nativas de escrita (`tools=[]`, medido pelo spike). O valor do MCP é outro:
portabilidade. As tools são funções Python puras — testáveis sem LLM e sem credencial — e o
adaptador MCP é uma casca de schema por cima. Outro modelo no futuro = outro adaptador fino,
**sem reescrever regra**. É o mesmo padrão já aceito na Pergunta 7 (catálogo declarativo +
adaptadores de entrada finos), aplicado a uma segunda família de superfícies.

**Custo assumido**: 4–5 tools (~150–250 linhas); confinamento de caminho ~15 linhas mais o teste de
propriedade que RNF-10/PBT-03 já exigem em qualquer cenário; adaptador MCP em dezenas de linhas
sobre caminho já medido. O risco aberto real não é segurança, é **qualidade da busca** — item a
iterar, registrado como tal.

---

#### Pergunta 11 — Composição de dependências (quem monta quem)

O domínio não pode construir adaptador, senão a fronteira é decorativa.

A) **(recomendo)** Um único ponto de composição no ponto de entrada (`__main__` / entrypoint do
`uv run`), que constrói adaptadores e injeta nos serviços; a TUI recebe serviços prontos e não
sabe que SQLite ou Claude existem

B) A TUI monta suas dependências no `on_mount`, como faz hoje com `Ambiente(nome=...)`

C) Um módulo container/registry consultado por quem precisar

D) Other (please describe after [Answer]: tag below)

[Answer]: A — porque construir e usar são responsabilidades diferentes. Empurre toda a construção
para a borda do programa; o miolo só recebe.

**Raciocínio preservado (o padrão se chama Composition Root).** Toda vez que se escreve `X()`,
faz-se uma solda: aquele pedaço de código fica grudado permanentemente naquela classe concreta, e
não dá para desgrudar de fora. Hoje `tui.py:338` faz `ambiente = Ambiente(nome="meu-ambiente")` —
inofensivo enquanto `Ambiente` é dataclass pura. Depois da persistência, essa linha viraria
`sqlite3.connect(...)` + `RepositorioSQLite(...)` + `AdaptadorClaude(...)` dentro do `on_mount`, e
a regra de camadas da Pergunta 2 morreria numa função de 6 linhas.

As dependências formam uma árvore: folhas são coisas concretas do mundo (arquivo, rede, SDK), raiz
é o que a interface usa. A pergunta é literalmente **quem monta essa árvore**. Em (A), uma função
só, no topo, monta de baixo para cima e entrega a raiz pronta; nenhuma classe chama o construtor
de outra — todas recebem pelo `__init__`.

`__main__` **não é uma camada, é o lado de fora**: é o único ponto onde a regra "não atravesse
camadas" não se aplica, e é por concentrar essa violação num lugar só que todo o resto fica limpo.
A fábrica parafusa motor, rodas e volante; o motorista recebe o carro montado.

**Por que (B) falha, concretamente**: (i) a TUI vira intestável — Textual chama `on_mount` sozinho,
e não existe ponto onde dizer "use um repositório em memória"; com (A) o teste é uma linha; (ii)
"o que esse sistema usa?" vira caça ao tesouro por `sqlite3.connect`; (iii) duplicação silenciosa
quando existirem duas superfícies montando de jeitos diferentes.

**Por que (C) falha**: a assinatura mente. `TelaAmbiente()` diz "não preciso de nada", e é falso.
Com (A) o `__init__` é documentação honesta e verificada pelo type checker. Além disso, container é
estado global mutável — testes vazam um no outro, ordem de inicialização vira bug fantasma, e
`container.get("servico")` transforma erro de digitação em erro de runtime.

Nada de biblioteca de DI: uma função `montar()` com construtores em ordem resolve o caso. São
uns 6 objetos, não centenas.

**Padrão que se repete**: na Pergunta 7 separou-se "o que a ação é" de "como ela é acionada"; na
10, "a regra" de "como ela é exposta ao modelo"; aqui, "o que o objeto faz" de "quem decide qual
objeto é". É sempre separar a decisão do uso e concentrar as decisões num ponto único.

---

#### Pergunta 12 — Fronteira entre os dois substratos

RNF-12 diz que o banco não guarda conteúdo nem índice da wiki, "no máximo a referência da raiz".
RNF-11 proíbe caminho absoluto persistido. As duas juntas deixam uma pergunta: o banco guarda
alguma coisa sobre a wiki?

A) O banco guarda a raiz da wiki do ambiente como **caminho relativo** a um diretório de dados
conhecido da aplicação

B) **(recomendo)** O banco não guarda **nada** sobre a wiki. A raiz é derivada por convenção da
identidade do ambiente (ex.: `<dados>/ambientes/<id>/wiki/`). Zero chance de divergência, e mover
o diretório de dados inteiro continua funcionando

C) O banco guarda um espelho de metadados da wiki (páginas existentes) para busca rápida

D) Other (please describe after [Answer]: tag below)

[Answer]: D — variante de (A): o banco guarda uma **referência à raiz** da wiki, e só isso. Nunca
caminho absoluto, nunca nada sobre o conteúdo.

**Correção da recomendação (B).** A opção B derivava a raiz por convenção a partir da identidade do
ambiente. Isso assume que o software é o dono da localização da wiki — verdade no modo local, falsa
em qualquer outro. Se a wiki mora num drive compartilhado ou, no futuro, num serviço, a localização
é escolhida por quem configurou o compartilhamento, não calculada pelo software. Uma convenção fixa
não tem como representar isso: no modo nuvem a "raiz" nem é uma pasta. **Convenção é boa para gerar
o valor inicial da raiz no modo local; é errada como única forma de saber onde a wiki está.**

**O que fica em cada substrato.** Substrato 1 (SQLite) guarda o ambiente: frentes, tarefas, chats,
memória, transcrição — mais uma referência à raiz da wiki daquele ambiente. Substrato 2 (a wiki)
guarda o conteúdo, e o arquivo continua sendo a fonte da verdade (ESC-17). O banco não guarda
página, não guarda índice, não guarda espelho de estrutura. RNF-12 é cumprido na letra: "no máximo,
a referência da raiz" — e é exatamente a raiz, nada além dela.

**Por que apontar só para a raiz — estabilidade referencial.** Só se persiste referência a coisas
cujo ciclo de vida o software controla. A raiz nasce quando o ambiente é criado e morre quando o
ambiente é apagado: ciclo de vida controlado, referência estável. O conteúdo dentro da raiz é o
oposto — o usuário renomeia pasta no Obsidian, move arquivo, faz `git pull`, e o software não é
avisado. Persistir referência a qualquer coisa dentro da raiz é criar dado que apodrece sozinho.
Saber a raiz é suficiente: a partir dela o bibliotecário navega e descobre o resto em tempo de
leitura, sempre atualizado por construção. Corolário operacional: apagar a raiz é apagar a wiki —
uma operação, um efeito, sem resíduo espalhado no banco.

**Por que isso não viola RNF-11.** A referência persistida não é caminho absoluto de disco. Ela é
resolvida em tempo de execução no ponto de composição (Pergunta 11): o banco guarda o localizador,
e quem o transforma em caminho real é o adaptador, com a raiz que recebeu do `main`. Mover ou
sincronizar o diretório de dados inteiro continua funcionando, e nenhum caminho de máquina entra em
arquivo ou banco. *(A forma exata do localizador foi refinada na **Pergunta D** da rodada 2.)*

**Como isso se conecta ao modo do ambiente (local × nuvem).** Um ambiente nasce em um de dois
modos, e o modo determina a **forma** da referência de raiz, não a existência dela:

| | ambiente local (esta iteração) | ambiente na nuvem (futuro) |
|---|---|---|
| estado do ambiente | SQLite na máquina do usuário | serviço remoto |
| wiki | pasta em raiz de dados criada pelo software | drive/serviço compartilhado |
| referência de raiz | localizador relativo à raiz de dados | localizador do serviço |
| escopo | um usuário, uma máquina (D-ARQ-09) | compartilhado no ambiente (FOR-13) |

No modo local, o software gera a raiz por convenção no momento da criação e a registra. Convenção
como semente, referência como verdade — a mesma lógica de ESC-19 para o esquema da wiki.

**Por que (C) está descartada.** Viola RNF-12 diretamente e é divergência garantida: qualquer edição
feita fora do software (Obsidian, `git pull`) deixa o espelho velho, e com wiki compartilhada
(FOR-13, RNF-13) ele estaria errado a partir do segundo usuário. Se busca rápida virar necessidade,
resolve-se dentro do substrato 2 (índice derivado, descartável, reconstruível), nunca no banco.

**O que esta decisão preserva para o futuro, sem custo hoje.** O domínio e a aplicação nunca sabem
onde a wiki está nem qual é o modo do ambiente: os dois chegam por porta e adaptador, montados no
ponto de composição. Trocar pasta local por serviço remoto é escrever outro adaptador de wiki e
outro adaptador de repositório — não é redesenhar o núcleo.

**Duas pontas soltas registradas, fora do escopo desta iteração:**

1. **Catálogo local de ambientes.** Se um dia o usuário puder ter um ambiente local *e* estar
   conectado a um ambiente compartilhado ao mesmo tempo, o modo passa a ser propriedade **do
   ambiente**, não da instalação — e alguém precisa guardar "que ambientes eu conheço e como chego
   neles" (`id | nome | modo | localizador`). Isso é uma peça real, mas é identificação de
   componente, não fronteira de substrato; nesta iteração o catálogo existe de forma degenerada
   (uma tabela `ambiente` no SQLite local, sempre modo local). Registrado para que o modo nuvem
   seja uma opção nova e não uma reforma.
2. **O gêmeo de RNF-13 para o estado do ambiente.** O modo nuvem quebra a suposição de escritor
   único no estado do ambiente; hoje RNF-13 cobre apenas a wiki. Nada a implementar agora; apenas
   nada a tornar impossível. A decisão da Pergunta 3 (transcrição em tabela separada, append-only)
   já sobrevive a esse futuro sem redesenho, o que é evidência a favor dela.

**Alerta aceito**: "tem que evoluir para nuvem" não pode virar justificativa para construir
abstração de nuvem agora. A defesa correta contra esse futuro já está decidida — porta de
persistência em vocabulário de domínio (D-ARQ-04), porta de wiki, e composition root (Pergunta 11).

---

### Categoria E — Padrões de desenho e decisões da wiki

#### Pergunta 13 — Critério do bibliotecário entre entidade (pasta) e propriedade (arquivo)

O risco número um do desenho da wiki. O usuário escolheu "propriedade pode ser instância", o que é
fiel ao uso real (`clientes/dr-marcelo.md` e `clientes/criterios-de-icp.md` convivem) mas deixa o
bibliotecário sem regra: sem critério, ele decide diferente a cada vez e a wiki apodrece.
Profundidade está travada em dois níveis, então "criar entidade" é sempre uma decisão de topo.

A) **(recomendo)** Entidade nova é **decisão humana**. O bibliotecário só cria arquivo dentro de
entidade existente; quando o conteúdo não couber em nenhuma, ele **propõe** a entidade nova e
espera aprovação. O esquema-semente já dá as entidades iniciais, então o caso comum não pede
aprovação nenhuma

B) Regra explícita para o agente decidir sozinho: cria entidade quando o conteúdo é substantivo
que terá múltiplas páginas; caso contrário, arquivo dentro da entidade mais próxima

C) O esquema é fechado: entidades são só as do esquema, e criar entidade nova exige editar o
esquema fora da conversa

D) Other (please describe after [Answer]: tag below)

[Answer]: A — com uma precisão que simplifica a regra: **não há dois regimes**. Toda escrita na
wiki é proposta, então "criar entidade" e "criar propriedade" passam pelo mesmo mecanismo.

**O critério semântico vem da abstração da wiki, não de uma regra extra.** Entidade é substantivo —
a coisa sobre a qual se sabe algo. Propriedade é característica que define ou restringe aquela
entidade, e pode ser faceta (`clientes/criterios-de-icp.md`) ou instância (`clientes/dr-marcelo.md`).
Dois níveis, travados. O bibliotecário não precisa de heurística inventada: ele pergunta *"isto é um
substantivo novo, ou é algo que caracteriza um substantivo que já existe?"*. Se caracteriza uma
entidade existente, é propriedade. Se introduz um substantivo que não existe, é entidade.

**A regra de funcionamento do bibliotecário é propor.** Ele tem duas operações de escrita —
`propor_entidade` e `propor_propriedade` — e nenhuma delas escreve. Ambas produzem uma proposta que
o usuário aceita ou recusa (Pergunta 9A). Isso elimina a pergunta "quando ele pode decidir
sozinho?": nunca. Não existe caminho de escrita sem aprovação, então não existe caso de borda onde
o julgamento dele vira fato sem revisão.

**O que mudou em relação ao enunciado de (A)**: (A) dizia "cria arquivo dentro de entidade
existente; quando não couber, propõe entidade" — dois comportamentos diferentes. Como a Pergunta 9
já decidiu que ele nunca escreve, o comportamento é um só: **propõe sempre**. Mais simples de
implementar e de explicar, e remove o caso de borda.

**Por que isso não vira atrito no uso comum.** O esquema-semente (ESC-19) já entrega as entidades
iniciais do domínio, então a esmagadora maioria das escritas é propriedade dentro de entidade que
já existe. Propor entidade nova é evento raro — e quando acontece, é exatamente o momento em que
uma decisão estrutural sobre a wiki está sendo tomada, que é quando revisão humana tem mais valor.

**Por que não (B).** B pede ao modelo que decida sozinho por heurística ("substantivo que terá
múltiplas páginas"). Heurística em prompt é sugestão estatística: ele decide diferente em dias
diferentes, e o erro estrutural só aparece semanas depois, quando a wiki já tem entidade duplicada
e conteúdo espalhado. O custo do erro é assimétrico — errar propriedade se corrige apagando um
arquivo; errar entidade contamina a organização inteira.

**Por que não (C).** Esquema fechado tira o crescimento orgânico da wiki e obriga o usuário a sair
da conversa para editar configuração. Contraria ESC-19, que trata o esquema como semente e não como
cerca.

**Onde cada parte mora.** O critério semântico é **prompt** do bibliotecário (é julgamento — ver
Perguntas 3-bis e 10). A profundidade de dois níveis e o confinamento de caminho são **código** na
tool (é garantia). O agente pode errar o julgamento; não pode violar a estrutura.

---

#### Pergunta 14 — Qual grafo manda na recuperação

Hierarquia de pastas e links `[[...]]` são dois grafos e podem discordar.

A) A hierarquia de pastas manda; links são conveniência de leitura

B) **(recomendo)** A hierarquia manda para **localizar** (é ela que o filesystem garante) e os
links são **arestas de navegação validadas na escrita** — link para página inexistente faz a
escrita ser recusada ou vira proposta de criar a página. Nenhum dos dois "vence" porque eles não
respondem a mesma pergunta

C) Os links mandam; a pasta é só armazenamento

D) Other (please describe after [Answer]: tag below)

[Answer]: B — com a precisão de que a recuperação tem um **passo obrigatório antes** dos dois
grafos: o `index.md`.

**Os dois grafos não competem porque respondem perguntas diferentes.** A hierarquia responde *onde
a informação mora* — é estrutura, garantida pelo filesystem, e é o que torna a wiki legível fora do
software. Os links respondem *com o que esta informação se relaciona* — é semântica, criada pelo
conteúdo, e é o que permite associação livre entre propriedades de entidades diferentes. Nenhum dos
dois "vence" porque nenhum substitui o outro.

**A regra de uso da wiki: toda leitura começa no `index.md`.** Ele é a porta de entrada obrigatória
(ESC-17). O `index.md` lista as entidades e, dentro de cada uma, as propriedades — cada uma com seu
link e uma **descrição curta** do que há ali. Essa descrição é o ponto central: é ela que permite ao
agente decidir onde buscar sem precisar ler a wiki inteira. Sem descrição, o índice seria só uma
lista de nomes de arquivo, e o agente teria que abrir tudo para descobrir o que importa — caro em
contexto e pouco confiável.

**A partir daí, o grafo de links assume.** Dentro das propriedades existem os `[[...]]`, que
conectam propriedades entre si livremente, inclusive atravessando entidades. Recuperação típica:
`index.md` → localiza a propriedade candidata pela descrição → lê → segue os links relevantes.
Primeiro salto por estrutura, saltos seguintes por associação.

**Links validados na escrita.** Link para página inexistente não passa: ou a escrita é recusada, ou
a criação da página vira parte da proposta. Como toda escrita já é proposta (Pergunta 13), isso não
adiciona mecanismo novo — o link pendente entra na mesma proposta que o usuário aprova. O efeito é
que o grafo nunca tem aresta quebrada, por construção.

**Nota do usuário sobre o formato das páginas**: existe uma estrutura de escrita de páginas já
usada, vinda da skill pública **WIKI LLM**, que ensina um agente a criar as páginas. A intenção é
reaproveitar ideias dessa estrutura quando arquivos forem criados na wiki. O detalhamento fica para
o momento adequado (prompt do bibliotecário, em Functional Design).

---

#### Pergunta 15 — Como o `index.md` se mantém atualizado

Ele é a porta de entrada de leitura do agente. Se mentir, o agente busca no lugar errado.

A) **(recomendo)** Derivado: regerado a partir da varredura do diretório depois de cada escrita
aprovada. Não pode divergir, porque não é fonte de nada — é projeção

B) Mantido pelo bibliotecário, que edita o `index.md` junto com a página

C) Híbrido: seção de estrutura derivada + seção de notas escrita pelo agente

D) Other (please describe after [Answer]: tag below)

[Answer]: D — variante de (B) na **responsabilidade** e de (A) no **mecanismo**: o bibliotecário é
dono da *descrição*; o `index.md` é projeção renderizada por código. O agente nunca edita o
`index.md`.

**Por que (A) pura não serve.** O `index.md` precisa de descrições, e descrição é julgamento — só
quem entendeu o conteúdo sabe dizer o que há na página. Estrutura de pastas não produz isso.

**Por que (B) pura é arriscada.** Se o bibliotecário editar o `index.md` como texto livre, aparecem
os cenários que queremos evitar: ele esquece de atualizar, reescreve o bloco errado, apaga entrada
de outra entidade, ou muda o formato e o próximo agente não consegue mais ler. Isso é
responsabilidade sustentada por disciplina de prompt — frágil por natureza.

**A solução: transformar responsabilidade em estrutura.** Duas decisões:

1. **A descrição é campo obrigatório da tool de escrita.**

   ```
   propor_propriedade(entidade, propriedade, conteudo, descricao, links)
   ```

   Não existe caminho de escrita sem descrição. O esquecimento deixa de ser possível — não por
   instrução ao modelo, mas porque a chamada é inválida sem o campo.

2. **A descrição mora na própria página, em frontmatter de estrutura fixa.**

   ```markdown
   ---
   descricao: Critérios de qualificação de lead usados na triagem inicial
   ---
   # Critérios de ICP
   ```

   Toda propriedade criada segue essa estrutura fixa — garantia de código na tool, não convenção. O
   frontmatter é extensível: campos obrigatórios podem ser acrescentados depois (datas, procedência,
   tags, estado de revisão) sem mudar o mecanismo do índice.

Com isso o `index.md` volta a ser projeção pura, renderizada por código a partir de
(estrutura de pastas) + (frontmatter de cada página):

```markdown
# Índice

## clientes
- [[clientes/criterios-de-icp]] — Critérios de qualificação de lead usados na triagem inicial
- [[clientes/dr-marcelo]] — Histórico e preferências do cliente Dr. Marcelo

## campanhas
- [[campanhas/lancamento-q3]] — Peças, verba e resultados da campanha de lançamento do Q3
```

**Entidade não tem descrição.** O nome da entidade (a pasta) é o título do bloco, e isso basta: o
nome já diz o suficiente sobre o que há dentro, e a navegação real acontece pelas descrições das
propriedades. Isso simplifica o desenho — não é preciso arquivo de metadados de entidade, nem
`propor_entidade` carregando descrição, nem lugar convencional para guardá-la.

**Consequências práticas:**

- **Não pode divergir.** O índice não é fonte de nada. Se sumir, regenera; se ficar estranho,
  regenera. Não existe o estado "índice desatualizado precisando de conserto".
- **Um só caminho de código.** Não há cenários de atualização por tipo de mudança. Existe
  `renderizar_index(raiz)`, executada após qualquer proposta aprovada. Um teste cobre tudo.
- **Formato garantido.** Gerado por código, o formato nunca deriva.
- **Sem dano colateral.** O agente não pode apagar nem corromper entradas de outras entidades,
  porque não escreve no índice.
- **Edição externa se resolve sozinha.** Pasta renomeada no Obsidian aparece corrigida na próxima
  renderização. Arquivo criado à mão sem frontmatter aparece no índice sem descrição — visível.

**Divisão de responsabilidade**, coerente com as Perguntas 10 e 13: a descrição é julgamento do
bibliotecário; a montagem do índice é código. O agente pode escrever uma descrição ruim; não pode
quebrar o índice.

> **Nota de escopo.** A resposta original trazia junto um segundo mecanismo de manutenção — o
> **lint** (páginas sem descrição, descrição desatualizada, link quebrado, propriedade que deveria
> ser entidade, duplicação, página órfã), ideia tomada da skill pública WIKI LLM. Isso entrou em
> conflito com FOR-12, e a **Pergunta B** da rodada 2 resolveu: **o lint fica fora, e não é
> registrado como ponto de extensão** — ver §4.

---

#### Pergunta 16 — Formato do arquivo de esquema de wiki

ESC-19: o esquema é semente e precisa ser plugável sem mexer em código (RF-F15).

A) Markdown com lista aninhada (mesma linguagem do resto da wiki, legível por humano e por LLM)

B) **(recomendo)** TOML (stdlib `tomllib` no 3.13, sem dependência, erro de sintaxe explícito,
mesmo formato do `pyproject.toml` que o projeto já vai ter)

C) YAML (exige dependência)

D) JSON

E) Other (please describe after [Answer]: tag below)

[Answer]: B — TOML. O esquema é **dado estruturado** (lista de entidades e propriedades); o arquivo
`.toml` é apenas sua serialização.

**Esclarecimento do que a pergunta decide.** Não é o formato das páginas da wiki — esse já está
fixado (markdown com frontmatter e links `[[...]]`, Perguntas 14 e 15). É o formato da **maquete**
que materializa a wiki na criação do ambiente (ESC-19, RF-F15).

**O esquema tem duas origens, e ambas convergem no mesmo dado.** Na tela de criação de ambiente, o
usuário ou escolhe uma maquete pronta ou digita as entidades ali mesmo. Como o formulário produz
dados, o esquema é dados — e o arquivo é só a forma de guardá-lo:

```
maquete pronta (.toml)   ──┐
                           ├──► Esquema (dado) ──► materializa a wiki
formulário preenchido    ──┘
```

**Por que TOML.** `tomllib` é biblioteca padrão (3.11+), então ler maquetes não custa dependência
nenhuma; erro de sintaxe vem explícito com número de linha, o que importa num arquivo editado à
mão; aceita comentário; e é o mesmo formato do `pyproject.toml` que o projeto já terá — um formato
de configuração no sistema, não dois. Ressalva conhecida: `tomllib` **só lê**.

**Por que não os outros.** Markdown exigiria parser de lista aninhada, que aceita variação de
sintaxe e produz estrutura errada em silêncio. YAML cobra uma dependência e traz fragilidade de
indentação — exatamente o erro silencioso que se quer evitar. JSON não aceita comentário e é hostil
à edição manual.

**Forma do arquivo:**

```toml
nome = "Marketing"
descricao = "Wiki inicial para trabalho de marketing e campanhas"

[[entidade]]
nome = "clientes"
propriedades = [
  { nome = "criterios-de-icp", descricao = "Critérios de qualificação de lead" },
]

[[entidade]]
nome = "campanhas"
propriedades = []
```

As `descricao` viram frontmatter das páginas criadas (Pergunta 15), então a wiki já nasce com
índice útil.

**Invariante de criação.** Ambiente não pode ser criado sem wiki materializada (ESC-19): exige-se ao
menos uma entidade. Propriedade **não** é exigida — obrigar o usuário a inventar uma propriedade
antes de ter conteúdo é pedir que ele adivinhe; entidade vazia é lugar legítimo para o bibliotecário
propor a primeira página. A regra vale para os dois caminhos de criação, logo mora no **domínio**; a
TUI apenas exibe a mensagem.

> **Nota de escopo.** A resposta original também previa "salvar como maquete" (maquetes do usuário
> no diretório de dados, exigindo um serializador TOML próprio, já que `tomllib` só lê). Isso não
> está em nenhuma das 14 histórias, e a **Pergunta C** da rodada 2 resolveu: **fica para depois**;
> nesta iteração há maquetes **embutidas, somente leitura** — ver §4. Sem "salvar como maquete", o
> serializador não existe e a dependência de escrita de TOML some.

---

#### Pergunta 17 — Ordem de correção das dívidas TD-01 a TD-04

O usuário pediu que a correção venha depois de a arquitetura fechar. Ela fechou aqui. As dívidas
são: SDK importado no núcleo, `responder()` retornando `None`, `Memoria.anotar()` com `KeyError`,
ausência de teste/persistência.

A) **(recomendo)** Não existe "correção de dívida" como trabalho separado: cada dívida morre dentro
da unidade que reescreve aquele componente (o import do SDK morre na unidade do adaptador,
`responder()` morre na unidade da porta de sessão, `Memoria` morre na unidade de domínio). Zero
trabalho jogado fora

B) Uma unidade de saneamento primeiro, corrigindo as quatro dívidas sobre a estrutura atual, e
depois a arquitetura nova em cima

C) Corrigir só o que bloqueia (o import do SDK, porque quebra teste sem credencial) e deixar o
resto para as unidades

D) Other (please describe after [Answer]: tag below)

[Answer]: A — **com uma emenda**. A fraqueza real de A não é técnica, é de rastreabilidade: dívida
que "morre sozinha" é dívida que ninguém verifica se morreu. E "eu reescrevi, então acabou" não é
evidência.

A correção é barata: **cada dívida vira critério de aceite nomeado da unidade que a mata, com um
teste que provaria seu retorno.**

| Dívida | O que é | Teste que impede o retorno |
|---|---|---|
| **TD-01** | `AgenteClaude.responder()` devolve `None` | Teste da porta de sessão que exige resposta não vazia; adaptador falso e real passam pelo **mesmo contrato** |
| **TD-02** | SDK importado no núcleo (`agente.py:6`) | Teste que **importa o pacote de domínio com o SDK desinstalado**. Prova RF-F04 de forma executável; só falha se alguém reintroduzir o import |
| **TD-03** | `Memoria.anotar()` levanta `KeyError` na primeira chave | Teste (e propriedade, já que PBT está ligado) de que anotar em chave nova funciona |
| **TD-04** | Persistência inexistente | Critério de aceite é CS-01: fechar e reabrir reconstitui o ambiente |
| **TD-11** | Argumento com espaço quebra o comando | Morre no parser `/` (Pergunta 7): um bug de uma função, com um teste |

Com isso, (A) deixa de ser "confia que some" e passa a ser "some, e existe um teste que impede
voltar".

**Detalhe prático aceito**: TD-03 é literalmente uma linha (`setdefault` ou `defaultdict`). Se em
algum momento a memória precisar funcionar antes da unidade que a reescreve, conserta-se na hora
sem cerimônia — é um caso onde a regra não precisa ser rígida.

---

## 4. Perguntas de acompanhamento — rodada 2

A análise obrigatória das respostas (regra `inception/application-design.md`, passos 8 e 9)
encontrou 1 pergunta sem resposta e 5 pontos de decisão, 3 deles em conflito com escopo aprovado.
As perguntas e as respostas completas estão em
**`application-design-clarification-questions.md`**. Resumo das decisões:

| # | Assunto | Resposta | Efeito no desenho |
|---|---|---|---|
| **A** | Política de gravação (refaz a Pergunta 8) | **B** | Grava ao fim de cada operação que muda estado, uma transação por operação. A mensagem do agente é **inserida no começo do turno** e atualizada conforme o streaming avança, com marca "em andamento" removida no fim. Queda no meio preserva o que já chegou; o carregamento distingue turno interrompido de turno completo |
| **B** | O lint entra nesta iteração? | **A** | **Fora, e nem registrado como ponto de extensão.** Palavra do usuário: *"não precisa ser pensado agora nem anotado; isso se resolve apenas tendo o bibliotecário. Se implementarmos o bibliotecário eu não vou esquecer dessa ideia do lint, pois vou ter que pensar o bibliotecário em mais detalhes no futuro, e esse vai ser o momento mais correto de detalhar o lint e implementá-lo de fato."* FOR-12 permanece intacto |
| **C** | Quanto do fluxo de maquetes entra agora | **B** | **Formulário + maquetes embutidas** (somente leitura, `tomllib`). Pelo menos uma maquete pronta: a do cliente João, para ele começar com uma wiki de aquisição em vez de tela em branco. O formulário garante que ele consiga criar outros ambientes para testar, e que a wiki do João seja **sugestão**, não hardcode. *"Salvar como maquete"* fica para depois — o usuário ainda não pensou nos detalhes de o que seria salvo |
| **D** | Forma do localizador da raiz da wiki | **B** | Localizador **com esquema explícito**: `dados:wikis/<id_ambiente>`. A parte antes de `:` diz **como resolver**; o adaptador conhece os esquemas. Hoje existe um só. Amanhã, `compartilhado:` ou `remoto:` entram sem caminho absoluto e sem migração de dado. Ressalva do usuário: *"para essa iteração vamos focar no local — single-user, o meu usuário criando um ambiente que salva localmente"* |
| **E** | Catálogo de ações é síncrono ou assíncrono? | **D** (duas decisões separadas) | **E1: catálogo uniformemente assíncrono** — `executar: Callable[[Alvo, dict], Awaitable[Resultado]]`. **E2: conversar fica FORA do catálogo** |
| **F** | O que a transcrição persiste | **B** | Mensagens de texto **+ registro do uso de ferramenta** (qual tool, parâmetros resumidos, resultado resumido). É o que torna auditável *por que* o bibliotecário propôs aquilo |
| **G** | Higiene deste arquivo | **A** | Limpeza autorizada; original preservado em `application-design-plan.bruto-2026-08-23.md` |

### Raciocínio integral da resposta E (é a que mais muda o desenho)

> A pergunta acoplava duas decisões independentes, e elas se separam.

**Motivo de E1 (catálogo assíncrono).** Async aqui não é sobre desempenho, é sobre a **forma da
fronteira**. A porta de persistência nasce assíncrona, e no dia em que o armazenamento virar nuvem
**só o adaptador muda** — nenhuma ação, nenhum serviço de aplicação e nenhum teste de ação é
reescrito. Com porta síncrona, esse dia é o dia em que tudo vira async de uma vez, porque rede não
tem versão síncrona aceitável numa TUI. A contaminação do `async` não custa nada nesta iteração: o
topo da cadeia (Textual, `on_input_submitted`) já é assíncrono de fábrica. A feiura aceita
conscientemente: por ora existirão `async def` que não esperam nada de demorado.

Sobre o `sqlite3` ser síncrono: a ação não chama `sqlite3`, chama a **porta** (decisão 3B /
D-ARQ-04). O `asyncio.to_thread` mora **dentro do adaptador**, aplicado nos pontos que valem a pena
(carregar ambiente na abertura), e não vaza para a assinatura de ninguém.

**Motivo de E2 (conversar fora do catálogo).** Conversar **não devolve `Resultado`** — devolve o
iterador assíncrono de eventos da decisão 5B (pedaço de texto, uso de ferramenta, fim de turno).
Enfiá-la no catálogo exigiria alargar `Resultado` para "ou um `Resultado`, ou um stream", e todo
consumidor de ação na TUI ganharia um `if`. São duas naturezas de saída, então são duas formas de
saída. Mesma camada de aplicação, mesma porta, entrada diferente. O "custo" de a paleta não listar
conversar é falso: a paleta lista ações, e conversar se aciona digitando texto **sem** `/` —
ninguém procura "conversar" numa lista de comandos.

**Opção (C) recusada explicitamente**: transforma "esta ação bloqueia a TUI?" em algo que só se
descobre lendo a implementação de cada ação, em vez de saber pela assinatura.

---

## 5. Reconciliações feitas sem nova pergunta

Registradas para o usuário poder discordar no portão de aprovação. Nenhuma bloqueia:

1. **Nome das tools.** A Pergunta 10 falava em `propor_escrita`; as Perguntas 13 e 15 refinaram para
   `propor_entidade` e `propor_propriedade(entidade, propriedade, conteudo, descricao, links)`.
   Adotado o par das Perguntas 13/15. Conjunto final: `listar`, `ler`, `buscar`, `propor_entidade`,
   `propor_propriedade`.
2. **Mensagens órfãs** (consequência de 3B): quando um chat é apagado, o serviço de aplicação apaga
   as mensagens dele **na mesma transação**. Sem varredura, sem lixo tolerado.
3. **Materialização da wiki na criação do ambiente não é proposta**: é ação do sistema a partir do
   esquema, não escrita do agente. O regime "toda escrita é proposta" vale para o bibliotecário.
4. **Uma proposta carrega várias páginas.** Registro do risco: "toda escrita na wiki é proposta"
   (9A + 13A) tem um custo de uso — se aprovar for frequente e chato, a revisão vira carimbo, e a
   defesa principal de RNF-14 passa a existir no papel e não na prática. Isso não muda a decisão; é
   motivo para o desenho permitir que **uma proposta carregue várias páginas de uma vez**, para que
   aprovar seja um ato **por promoção**, e não um ato por arquivo.
5. **Fronteira entre `propor_entidade` e US-10 (adiada).** US-10 foi adiada por ser "o esquema
   mutando em runtime". `propor_entidade` cria entidade nova em runtime, sob aprovação — logo
   entrega **parte** do valor de US-10. Adotado: a tool existe porque a Pergunta 13 a decidiu
   explicitamente e porque sem ela o regime "toda escrita é proposta" teria um buraco; **US-10
   permanece formalmente adiada e não carrega critério de aceite nesta iteração.** Ponto marcado
   para objeção no portão de aprovação.
6. **Rod-maker fora.** US-11 e US-12 adiadas (FOR-14). `Papel.SUB_AGENTE` permanece no domínio
   porque o bibliotecário o usa; nenhuma implementação de rod-maker é desenhada.

---

## 6. Plano de execução do estágio

### Parte 1 — Planejamento (este documento)

- [x] Ler `requirements.md` v2, `stories.md`, `execution-plan.md` v2 e notas retidas
- [x] Verificar no código os fatos que sustentam as perguntas (§2)
- [x] Levantar as decisões abertas herdadas de §6 e §9.8
- [x] Gerar perguntas nas cinco categorias exigidas pela regra do estágio
- [x] Usuário respondeu 16 das 17 tags `[Answer]:` (a Pergunta 8 ficou em branco)
- [x] Analisar respostas em busca de vagueza, contradição e critério indefinido
- [x] Ambiguidades encontradas — 7 perguntas de acompanhamento criadas
- [x] **Rodada 2 respondida** em 2026-08-23 (A=B, B=A, C=B, D=B, E=D, F=B, G=A)
- [x] Limpeza do artefato autorizada e executada; original em
      `application-design-plan.bruto-2026-08-23.md`

### Parte 2 — Geração dos artefatos

- [x] `application-design/components.md` — componentes, propósito, responsabilidades e interfaces
- [x] `application-design/component-methods.md` — assinaturas, entrada e saída, propósito de cada
      método (regra de negócio detalhada fica para Functional Design)
- [x] `application-design/services.md` — serviços de aplicação, responsabilidades e orquestração
- [x] `application-design/component-dependency.md` — matriz de dependência, regra de import
      permitida, padrão de comunicação e fluxo de dados
- [x] `application-design/application-design.md` — consolidação
- [x] Rastrear cada componente às 14 histórias da linha fina e aos RF/RNF que ele atende
- [x] Validar sintaxe de Mermaid e alinhamento de diagrama ASCII antes de gravar, com alternativa
      textual (regra `common/content-validation.md`)
- [x] Registrar conformidade das extensões habilitadas
- [x] Atualizar `aidlc-state.md` e `audit.md`

### Extensões aplicáveis a este estágio

| Extensão | Situação | Como aparece no desenho |
|---|---|---|
| `security-baseline` | Habilitada | SECURITY-05 e SECURITY-13 (confinamento de caminho na tool de wiki, wiki como entrada não confiável), SECURITY-12 (credencial por usuário, nunca no código nem no banco), SECURITY-15 (falha do provedor e de I/O isolada na fronteira do adaptador, sem vazar detalhe interno para a tela). Regras de rede, HTTP, IAM e balanceador: N/A — processo local, sem porta de rede |
| `property-based-testing` | Habilitada (Full) | PBT-01 pede identificação de propriedades no desenho: round-trip de serialização do agregado, e nenhum caminho gerado escapa da raiz da wiki. As propriedades são **nomeadas** aqui e **especificadas** em Functional Design |
| `resiliency-baseline` | Desabilitada | Não enforçada, por decisão registrada em 2026-08-17 |

---

## 7. Critérios de conclusão do estágio

- [x] Todas as 17 respostas presentes e sem ambiguidade não resolvida (16 na rodada 1 + Pergunta 8
      refeita como Pergunta A na rodada 2).
- [x] Os cinco artefatos obrigatórios criados.
- [x] As oito decisões abertas da §1 fechadas e escritas, cada uma com o motivo.
- [x] Nenhum componente de domínio dependendo de `claude_agent_sdk`, `sqlite3` ou Textual,
      verificável pela matriz de dependência.
- [x] Cada uma das 14 histórias da linha fina rastreada a pelo menos um componente.
- [ ] **Aprovação explícita do usuário antes de Units Generation.**
