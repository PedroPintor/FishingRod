# Glossário — a linguagem do usuário

**Atualizado:** 2026-08-14
**Origem:** reunião João × Pintor de 2026-08-14 (transcrição) + `interface-v3-nexus.html`

> Este é o vocabulário **do usuário**, não o do código. Quando as duas listas divergem, o
> registro aqui é o que o usuário fala — a decisão sobre renomear código é de outro chat.
>
> Marcação de origem: **[acordado]** = negociado ao vivo na reunião, com as duas partes
> concordando · **[fala]** = dito pelo João, não contestado · **[interface]** = está no HTML
> que ele produziu, mas não foi verbalizado na reunião.

---

## Ambiente

**[acordado]** O espaço de trabalho inteiro, definido por **um objetivo de negócio com meta**.
No caso: "Nexo Aquisição", cuja meta é gerar MRR recorrente.

A palavra foi negociada em tempo real. O João chamou de "projeto"; o Pedro propôs "ambiente";
o João aceitou na hora:

> **João:** "esse nexo aquisição é o meu projeto"
> **Pedro:** "isso eu tô chamando de ambiente"
> **João:** "vamos chamar de ambiente, faz sentido. Melhor."

E ele reforçou depois que o que guia tudo não é o container, é a meta:
*"não é um ambiente, é pela meta"* — antes de aceitar que a meta é um atributo do ambiente.

**Implicação:** um ambiente sem meta declarada não organiza nada. A meta é o que classifica
o que entra e o que não entra.

## Frente

**[acordado]** Uma área de atuação dentro do ambiente. São os **canais e capacidades** que
precisam existir para a meta acontecer.

As seis do João: `oferta e mensagem` · `instrumentação` · `conteúdo` · `mídia paga` ·
`outbound` · `comercial e ticket`.

> **João:** "p***, a gente tem que ter uma frente de conteúdo. A gente tem que rodar mídia
> paga. A gente tem que ter um canal Outbound."

**Cuidado registrado:** o João corrigiu o Pedro quando ele tratou conteúdo como *etapa*:
*"Conteúdo não é uma etapa dentro de mídia paga, é um canal."* Frente é canal, não fase.

**Nota:** "projeto" foi abandonado por ambiguidade. O próprio João: *"eu tô na dúvida... a
gente tratava projeto como se fosse as áreas."* A palavra não sobreviveu à conversa.

## Card (= tarefa)

**[acordado]** A unidade de trabalho. Um contêiner com objetivo próprio, uma linha do tempo
interna de etapas, agentes conversando e memória própria.

> **Pedro:** "esses cards eu tô chamando de tarefa" — **João:** "com certeza, à vontade."

O João pediu explicitamente cards **grandes com subetapas**, e não tarefas picadas:
*"tá vendo que as tasks eu deixei maiores do que as outras? Porque as outras são subtasks."*

## Natureza da tarefa

**[acordado]** Todo card é de uma de três naturezas. O critério que as separa não é o assunto
— é **onde cada uma escreve**:

| Natureza | Escreve em | Artefato que produz |
|---|---|---|
| **Discovery** | na **Wiki** | uma **diretriz** — regra nova que passa a valer em todo card futuro |
| **Execução** | no **mundo** (via conexões) | uma **peça** — campanha no ar, página, vídeo, e-mail enviado |
| **Análise** | numa **decisão** | um **veredito** — cortar, escalar, manter |

Todas as três foram ditas por ele:
> "a execução escreve pro mundo — pra LP, pro CRM, pra campanha"
> "o discover ele faz uma diretriz, sempre vai criando uma estratégia"
> "a análise ela gera decisões"

## Tipo de tarefa

**[Pedro, 2026-08-14]** A abstração que generaliza a "natureza" do cliente. Tarefas têm tipos,
e **cada tipo carrega uma configuração de "objetivo e checagem"** — a garantia daquele tipo:
o que a tarefa precisa produzir para poder fechar.

Os tipos do João (`discovery` / `execução` / `análise`) passam a ser **configuração do ambiente
dele**, não estrutura do software. Um ambiente de estudos configura outros tipos, com outras
checagens. Ver `abertas.md`, A-11.

## Admin do ambiente (= usuário principal)

**[Pedro, 2026-08-14]** Quem criou o ambiente. Existe por uma razão nomeada: **governança** —
*"o software, como é compartilhado e vai ter usuários, precisa ter um certo tipo de
governança"*.

Tem permissões a mais: alterar meta, frentes, tipos de tarefa, regras e categorias da wiki, e
**bloquear funcionalidades** para os demais. Não é quem distribui o trabalho — todo usuário
aloca tarefas (ver P-20 e RF-01 a RF-07).

## Impeditivo

**[Pedro, 2026-08-14]** Sinalização **humana** de que uma sub-etapa está bloqueada. Distinto do
estado `travado`, que o ambiente detecta sozinho a partir de um artefato que ainda não existe.

Um é declarado por alguém; o outro é deduzido do contrato do card. Ver `abertas.md`, A-15.

## Conexão (ferramenta externa / MCP)

**[Pedro + cliente]** Serviço externo configurado no ambiente e **associado a um ou mais
agentes**, que passam a dispor dele. Kairogen, Google Ads, HubSpot, Meta Ads, WordPress são os
casos reais do ambiente do cliente.

**A ferramenta é do agente, não da etapa.** `/criar + Kairogen`, na interface do cliente, é
notação abreviada de "agente responsável que dispõe da tool Kairogen". Ver H-05.

## Sub-etapa e executor (= responsável)

**[interface + Pedro]** A tarefa é composta de **sub-etapas**, cada uma com um **executor**.

**[Pedro, 2026-08-14]** A leitura proposta é que o executor seja o **responsável** pela etapa,
sempre uma entidade do software: um **agente** (que pode ser acionado automaticamente, gerando
trabalho paralelo) ou um **usuário** — inclusive outro usuário do ambiente compartilhado.
É hipótese, não decisão: ver `hipoteses-de-solucao.md`, H-04.

Na interface do cliente o campo aparece com valores mais variados — agente, comando
(`/escrever`), conector (`/criar + Kairogen`), pessoa nomeada (`Pintor`), **outro card**, e
**VOCÊ**.

Três executores geram comportamentos de primeira importância: `VOCÊ` produz o
[momento humano](#momento-humano); `outro card` produz a dependência que trava e destrava
sozinha; comando que toca o mundo real dispara confirmação.

As etapas de uma tarefa nascem da primeira conversa com o orquestrador e são refinadas com o
uso — ver `cenarios/03`. **Se são parte da tarefa ou entidades reutilizáveis, segue em aberto**
(`hipoteses-de-solucao.md`, H-03).

## Rod-maker

**[Pedro + cliente + código]** O responsável por construir agentes novos. O usuário planeja com
o orquestrador, que aciona o rod-maker; a partir daí o usuário escolhe com quem conversa.

Palavra com lastro nos três lugares: existe no código (`Ambiente/agente.py`), no material do
cliente (*"construir via rodmaker o agente qualificador de MQL"*) e na fala do Pedro. É
**hipótese de solução**, não decisão — ver H-02.

## Bibliotecário

**[Pedro + cliente]** O responsável por escrever na wiki, garantindo o formato. O cliente já
usa a palavra (*"sobe pra wiki via bibliotecário"*). Também é **hipótese de solução** — ver H-01.

## Recorrente

**[acordado]** Subtipo, não natureza. Um card que **não fecha**: reabre sozinho no ciclo.
A revisão semanal de canal é o exemplo — existe para a regra de corte valer sem depender
da memória de ninguém.

> **Pedro:** "ela também tem um subtipo que é recorrente, ou seja, eu vou estar sempre
> fazendo" — **João:** "perfeito."

## Etapa (subetapa)

**[acordado]** Os passos dentro de um card, na linha do tempo. Cada etapa tem um executor:
um comando, um agente, um conector, uma pessoa nomeada, ou **VOCÊ**.

Uma etapa pode ser trabalho de outra frente — e é justamente aí que os cards se cruzam.

## Momento humano

**[fala]** Etapa que só a pessoa faz, e que trava o card enquanto não acontece.

> **João:** "a gravação é a única coisa que é offline do total"
> "a única coisa que vai dar realmente trabalho mesmo parece que é a gravação"

O card fica parado, mas **o usuário não** — ele opera outros cards enquanto isso.

## Consome / Entrega (o contrato do card)

**[acordado, e o item mais elogiado]** Todo card declara o que precisa receber para andar
e o que vai produzir. Cada insumo aparece **verde** (existe) ou **vermelho** (falta).

> **João:** "ele fica verde com o que tem já e vermelho com o que não tem. O legal é que
> você sabe exatamente o que vai produzir nessa tarefa. Ô, é uma visualização legal."
>
> "o cara vê isso aqui em vermelho... Ele vem aqui e fala: 'Orquestrador, sou eu, abre aí
> o bagulho de LP'."

## Travado

**[acordado]** Estado do card que espera um artefato que outro card ainda não produziu.
Destrava **sozinho** quando o artefato existir.

> **João:** "o que tá travado esperando o artefato, porque a ideia é que tudo trabalhar
> realmente nesse artefato"

## Wiki

**[acordado]** O repositório de inteligência do ambiente — o contexto universal, lido por
todo agente antes de escrever qualquer coisa. É onde a diretriz do discovery vai parar.

> **Pedro:** "ele armazenaria esse contexto universal ali" — **João:** "exatamente, é isso."

É o que faz o reaproveitamento entre frentes acontecer:
> **João:** "esse discover sobe também do que o outro discover tem na wiki, porque ele
> documentou. (…) quando for a hora esse cara vai saber das ideias."

**Distinção que já existia no material anterior:** wiki = **memória** (o que se sabe e por
que decidimos) · ambiente = **estado** (o que muda toda semana).

**[Pedro, 2026-08-14]** Tecnicamente, um **grafo de arquivos `.md`** que cresce sem esquema
prévio. A wiki é **criada junto com o ambiente** — é uma das etapas mínimas de configuração
inicial — e nasce pequena.

### Categoria (da wiki)

**[Pedro, 2026-08-14 — termo provisório, entre aspas na fala dele]** As divisões de informação
que a wiki guarda. Começam poucas, na criação do ambiente, e o usuário cria novas a qualquer
momento conversando com um chat.

É o que separa as duas metades da wiki: a **estrutura** (as categorias) pode vir pronta; o
**conteúdo** só se acumula com o uso. Ver `principios.md`, P-19.

## Aba (= chat de agente dentro do card)

**[fala]** Dentro de um card, cada agente tem sua aba de conversa. O usuário abre agentes
conforme precisa.

> **João:** "eu posso fazer tudo nesses chats, por exemplo, que é os agentes que você vai
> spawnando depois" · "abro um agente aqui de design"

## Orquestrador

**[fala]** O interlocutor principal do card. É com ele que o usuário fala, e é ele que aciona
os demais agentes, abre cards novos e pede confirmação.

> **João:** "Todo mundo conversa com o mesmo orquestrador"

## Memória (do card)

**[interface]** Anotações da sessão de trabalho daquele card, cada uma com **chave, autor e
valor**. No HTML aparecem coisas como `travado-por`, `regra-aplicada`, `origem-do-card`.

## Comando (verbo com `/`)

**[interface]** Os verbos do trabalho não são tipos de card — são comandos digitados:
`/criar` `/escrever` `/preparar` `/subir` `/enviar` `/responder` `/cortar` `/gravar`
`/analisar` `/verificar` `/decidir` `/discovery` `/pesquisar` `/promover`

Regra associada, **[interface]**: *"verbo que toca o mundo real pede confirmação; verbo que
só produz rascunho, não."*

## Conexões

**[fala/interface]** As ferramentas externas alcançáveis por prompt (MCPs, APIs). É por elas
que a execução "escreve no mundo".

---

## ⚠️ Divergência entre a fala do usuário e o código atual

O código hoje usa `Ambiente > Projeto > Sessao > Chat`. O usuário usa
`Ambiente > Frente > Card > Aba`. O mapa aproximado:

| Usuário fala | Código tem | Observação |
|---|---|---|
| Ambiente | `Ambiente` | ✅ mesma palavra, mesmo sentido — mas o usuário carrega **meta** junto |
| Frente | `Projeto` | ⚠️ "projeto" foi descartado na conversa por ambiguidade |
| **Card / tarefa** | `Sessao` | ⚠️ o card tem `agentes[]` + `memoria[]`, exatamente como a Sessão tem `chats[]` + `memoria` |
| Aba | `Chat` | ✅ mesmo conceito, palavra diferente |
| Memória do card | `Memoria` / `Anotacao` | ✅ o HTML usa `{chave, autor, valor}`, o mesmo formato |
| Natureza, contrato consome/entrega, travado, etapas | — | ❌ não existem no código |

**Isto é uma observação, não uma decisão.** O que fazer com ela — renomear, mapear, manter —
é trabalho do chat de planejamento, não deste.
