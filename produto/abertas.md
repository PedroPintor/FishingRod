# Perguntas em aberto, premissas e riscos

**Atualizado:** 2026-08-14 (v2, após a reunião de 14/08)

Item resolvido não é apagado — ganha a resposta e a data. Item novo entra no fim.

---

## ✅ A-01 — Quem é o usuário do FishingRod? — RESPONDIDA em 2026-08-14

**A resposta é: o João opera.** Minha leitura anterior estava errada.

Eu havia inferido do `LEIA-ME.md` (*"João: decide, grava, vende, aprova. Só isso"*) que ele
seria destinatário das saídas, não operador. A transcrição desmente isso de forma direta —
ele descreve a si mesmo operando, em primeira pessoa e no detalhe:

> "eu venho aqui, venho nesse chat aqui (…) **abro um agente aqui de design** (…) spawno um
> agente LP, converso com ele, aprovo com o orquestrador, aí eu subo a campanha, chamo o MCP"
> "fica muito fácil eu **operar cinco, seis tasks diferentes durante o dia**"

**Consequência:** o produto precisa ser operável por alguém focado em negócio, não em
tecnologia. E o Pedro é um segundo operador, com necessidades diferentes (montar × usar).

---

## ✅ A-02 — A dor formulada era do Pedro ou do João? — RESPONDIDA em 2026-08-14

Nenhuma das duas formulações estava certa. A dor do João, dita por ele, é **capacidade de
execução paralela com garantia**, não falta de organização nem custo de manutenção:

> "é muita função (…) **como que eu vou garantir que eu vou fazer todas** e ainda fazer a
> gravação que é externo?"

Ver `dores.md`, D-10 e D-11.

---

## 🟡 A-03 — O que prova que o FishingRod é genérico? — TESTADA em 2026-08-14

**Segundo domínio obtido:** o Pedro descreveu um ambiente de estudos da faculdade (ver
`cenarios/02`). Cada abstração foi testada contra os dois mundos. Resultado:

- ✅ **Generalizam:** ambiente com meta · frente · card com objetivo · etapas com executor ·
  aba/agente · agente nascendo de tarefa repetida · wiki · consome/entrega · travado ·
  momento humano · recorrente · multiusuário opcional.
- 🔴 **Não generalizam:** as **três naturezas** — a definição depende de "escrever no mundo",
  e no ambiente de estudos não existe mundo externo. E os **14 verbos**, em parte: cinco são
  universais, os outros são de marketing.

**Segue aberto:** o que fazer com a natureza (ver A-11). E o teste ainda é de mesa — o
ambiente de estudos é hipotético, ninguém o operou.

*(Registro do enquadramento original, que continua válido como alerta:)*

A reunião **aumentou** este risco em vez de reduzi-lo. Toda a estrutura discutida é de
marketing: as seis frentes são F1–F6 do plano da Nexus; os 14 comandos são verbos de operação
de mídia (`/subir`, `/cortar`, `/analisar` CPL); os cards de exemplo são campanha, LP, leva de
vídeos, lista B2B.

**O que talvez seja genérico embaixo disso:** ambiente com meta → frentes → cards com natureza
→ etapas com executor → agentes por aba → wiki. As três naturezas (descobrir / fazer / avaliar)
parecem universais. O resto parece de domínio.

**Precisa responder:** existe um segundo domínio para testar cada abstração? O próprio Pedro
desenvolvendo software é o candidato de custo zero — e está acontecendo agora, nesta pasta.

---

## A-04 — Onde o FishingRod termina e o Claude Code começa? (com resposta candidata)

A reunião deu uma resposta que antes não existia. O que o arranjo atual (pastas + skills + MCP)
**não** faz:

1. Card com **contrato declarado** — o que consome, o que entrega, verde/vermelho.
2. **Travamento e destravamento por artefato** entre tarefas.
3. **Paralelismo com estado visível** — cinco ou seis tarefas vivas ao mesmo tempo.
4. **Promoção de achado a diretriz**, que passa a valer sozinha em todo card futuro.
5. **Natureza de tarefa** como classificação que define onde o resultado é escrito.

Ainda é candidata: precisa ser confirmada contra o que ele de fato sente falta hoje — e a
dinâmica "Chão de Fábrica" (ver F-01) foi desenhada exatamente para isso.

---

## A-05 — Validar as dores inferidas com o usuário (parcialmente feita)

D-04 e D-05 foram confirmadas na reunião. D-01, D-02, D-03, D-06, D-07, D-08 e D-09 continuam
inferidas — nenhuma foi tocada. Ver tabela de reclassificação em `dores.md`.

---

## A-06 — O ambiente de hoje: o que roda onde, e quanto custa manter

Segue aberta. Falta o mapa do arranjo atual e, sobretudo, **quantas horas por semana a
manutenção consome**. É o número que transforma D-01 de argumento em caso.

---

## ✅ A-07 — Multiusuário: requisito ou entusiasmo? — RESPONDIDA em 2026-08-14

**É intenção de produto do Pedro, não só entusiasmo do cliente.** O FishingRod é pensado como
**ambiente de trabalho com IA colaborativo**, e o multiusuário existe para resolver D-12 —
times que trabalham com IA sem compartilhar contexto.

Com uma qualificação importante: **convidar é opcional** (ver `principios.md`, P-13). O
ambiente serve a um time e a uma pessoa só; solo não é modo degradado.

**O que continua aberto — mas é do outro chat:** *quando*. "Requisito" e "meta" foram usados
pelo Pedro na mesma resposta, e sequenciamento de release é decisão de planejamento, não de
descoberta. O que fica registrado aqui é o **o quê**: o ambiente suporta mais de uma pessoa.

*(Enquadramento original preservado:)*

O João defendeu, com convicção, um modelo que **contradiz o desenho atual** (TUI local,
usuário único):

> "imagina que aqui é um site mesmo, **é um servidor, tá na nuvem, todo mundo usa ao mesmo
> tempo** (…) Eu tô nesse chat, o cara tá nesse, o cara tá nesse. **O multiuso é muito fácil.
> Todo mundo conversa com o mesmo orquestrador.** Assim, para time parece que faz sentido."

E o Pedro respondeu imaginando distribuição de trabalho por pessoa: *"a tarefa chega pro cara,
ele abre ali a tarefa (…) ele abre lá o chat dele e começa a resolver com os agentes dele"* —
ao que o João corrigiu o eixo: *"eu não diria frente, eu diria tarefa."*

**Precisa responder:** isso é requisito da v1 ou visão de futuro? A diferença é grande — muda
persistência, identidade, concorrência e onde o processo roda. Hoje a Nexus tem **um operador**;
o argumento multiusuário é sobre um time que ainda não existe.

---

## ✅ A-08 — Quem monta o ambiente da primeira vez? — RESPONDIDA em 2026-08-14

**O usuário monta, do jeito que quiser.** O software garante a **estrutura** que torna o
ambiente bom para trabalho colaborativo com IA — não o conteúdo dele. Ver `principios.md`,
P-12.

**Atualização de 2026-08-14 — o buraco foi em boa parte preenchido.** O `cenarios/03` narra as
duas curvas de montagem (método trazido pronto × descoberto no uso), a criação do ambiente como
processo com etapas mínimas, e o que não pode vir pronto (conteúdo da wiki e agentes).

**O que ainda sobra:**

- **Quem cria as frentes iniciais, e com base em quê?** Nos dois cenários o usuário "já pensou"
  nelas. Ninguém mostrou esse pensar acontecendo — e é o único momento em que os dois perfis
  (especialista e iniciante) precisam da mesma coisa.
- **Quais são as etapas mínimas de criação do ambiente?** Sabemos que a wiki é uma. Não sabemos
  as outras, nem quantas são, nem quanto custam ao usuário antes do primeiro trabalho útil.
- **Tudo continua hipotético.** Nenhuma montagem foi observada acontecendo — nem a do cliente,
  que já rodou na prática em Markdown e seria evidência real se fosse reconstituída.

*(Enquadramento original preservado:)*

O cenário narrado começa com tudo já montado: frentes definidas, cards existindo, wiki
carregada, agentes disponíveis. Ninguém falou sobre **a criação**.

Se montar exigir o Pedro, o produto tem dois usuários com habilidades muito diferentes e uma
dependência embutida. Se o João montar sozinho, isso é uma exigência de desenho enorme e ainda
não discutida.

---

## A-09 — A primeira impressão do usuário foi ruim (nova — risco de adoção)

Registrado porque é fácil de esquecer depois que deu certo:

> **João:** "no começo eu tava enzado (…) eu falei 'que p**** é essa?' **eu achei uma m****.**
> Quando eu comecei a pensar, mano, essa aqui é uma das ideias mais geniais que tem."

E, mesmo convencido, ao fim: *"não parece muito usual isso aqui."*

**O risco:** o valor do produto só aparece **depois** de pensar e clicar. Se o usuário
comum abandonar antes disso, a qualidade do desenho não salva. Um usuário que não é sócio da
ideia não dá esse tempo.

---

## A-10 — Frentes e naturezas: estrutura do produto ou configuração do usuário? (nova)

O João estabeleceu a regra "conteúdo entra dentro das outras frentes; as outras não entram
dentro de conteúdo". O Pedro classificou corretamente como **regra de negócio dele**, não do
software (ver `principios.md`, P-10).

**Precisa responder até onde isso vai:** as frentes são configuráveis (claro que sim), mas
e as três naturezas? E os 14 comandos? E a wiki como destino obrigatório do discovery? Cada
item que for fixo no produto é uma opinião imposta a todo usuário futuro.

---

## ✅ A-11 — Natureza: rótulo ou estrutura? — RESPONDIDA em 2026-08-14

**A abstração é: tarefas têm tipos, e cada tipo carrega uma configuração de "objetivo e
checagem".**

> **Pedro:** "cada tipo de tarefa criada pode ter uma configuração de **'objetivo e checagem'**,
> onde a ideia é configurar uma garantia para aquele tipo de tarefa."

Isso resolve a divergência sem sacrificar nenhum dos dois lados:

- **A garantia sobrevive** — a regra do João (*"discovery só fecha com diretriz escrita"*)
  deixa de ser combinado entre pessoas e vira **checagem configurada** naquele tipo. O
  software sabe o que fecha um card.
- **O genérico sobrevive** — "execução / análise / discovery" são os tipos que **o João
  configurou no ambiente dele**, não os tipos do software. O ambiente de estudos configura
  outros, com outras checagens.
- **A rachadura do cenário 02 desaparece** — a definição não precisa mais depender de
  "escrever no mundo", porque cada ambiente define o que conta como pronto para os seus tipos.

**Termo a adotar:** *tipo de tarefa*. "Natureza" fica registrada como a palavra do cliente.

*(Enquadramento original, preservado como memória da discussão:)*

**Há divergência real entre o João e o Pedro, e ela não é sobre palavra — é sobre o que o
software garante.**

**Como o João usa** (interface v3): natureza é **estrutura com comportamento**. Ela define
onde o resultado é escrito e **o que conta como fechamento**. Daí sai a regra dura *"discovery
só fecha quando existe diretriz escrita que muda o que a gente faz; se nada mudou, era
conversa e o card não fecha"* (P-04).

**Como o Pedro descreve:** natureza é **rótulo de organização** que o usuário atribui —
*"ele vai criando as tarefas e dando um 'tipo' para conseguir se organizar"*.

**O que está em jogo:** se natureza é só rótulo, o software não sabe o que fecha um card, e
P-04 deixa de ser garantia — vira combinado entre pessoas, que é exatamente o tipo de coisa
que degrada (ver D-02). Se natureza é estrutura fixa, o software impõe três tipos a todo
ambiente futuro, contra P-12 — e o teste do cenário 02 mostrou que a definição atual **não
sobrevive** fora de operação de marketing.

**Meio-termo aparente, não decidido:** *tipo de tarefa* como conceito do software, com
**critério de fechamento configurável pelo ambiente**. O João configura três tipos com as
regras dele; o ambiente de estudos configura outros. Preserva a garantia sem impor o
vocabulário. Registrado como observação — a escolha é do chat de planejamento.

---

## ✅ A-12 — A wiki escrita só por agente — RESOLVIDA em 2026-08-14, e eu estava errado

Não era exceção a P-12. Era **solução prematura registrada como princípio** — erro meu de
classificação, do mesmo tipo que o dos ADRs no começo desta pasta.

**A correção, do Pedro:** bibliotecário e rod-maker são **hipóteses de solução** para garantir
funcionalidades, não regras do produto. Ele próprio apresentou uma alternativa — tools de wiki
e tools de construção de agente — o que prova que a hipótese é substituível.

**O que ficou:** a necessidade (nada entra na wiki por caminho não verificado, e há revisão
humana) permanece em `principios.md` P-14, reformulado. As hipóteses foram para
`hipoteses-de-solucao.md` H-01 e H-02, com alternativas e critério de validação.

**A lição, que vale como método:** antes de escrever um princípio, perguntar *"isto é o que o
usuário precisa, ou é como eu pretendo atender?"*. Se houver uma segunda maneira de atender,
é hipótese.

*(Enquadramento original preservado:)*

O Pedro definiu que o usuário **lê** a wiki mas não escreve nela direto: quem escreve é o
bibliotecário, e o usuário revisa (P-14). O motivo é bom — escrita livre degrada o formato,
e formato degradado destrói a utilidade do contexto para o LLM.

Mas isso é o software **impondo comportamento**, na mesma conversa em que se estabeleceu que
o software não impõe método (P-12). Não é contradição fatal; é exceção que precisa ser
consciente.

**Precisa responder:** existem outras imposições desse tipo já assumidas sem terem sido
nomeadas? Cada uma precisa do seu motivo escrito, senão o "genérico" se perde por acúmulo de
pequenas opiniões.

---

## A-13 — Etapa e executor são a mesma coisa? (nova)

A generalização proposta foi: *"os verbos na verdade são as sub etapas relacionadas à tarefa"*.
Isso **quase** funciona, mas colapsa dois campos que a interface do cliente mantém separados.

Cada etapa lá tem **nome** e **executor**:

| Etapa (nome) | Executor |
|---|---|
| copy dos anúncios | `/escrever` |
| criativo (6 variações) | `/criar + Kairogen` |
| GRAVAR | **VOCÊ** |
| LP | **outro card** |
| tracking / UTM | **Pintor** |
| portão de qualidade | agente `revisor` |

O verbo aparece no campo **executor** — é *como* a etapa é feita, não a etapa. E os outros
valores possíveis de executor são justamente os que produzem os comportamentos mais
importantes já registrados:

- executor **VOCÊ** → é o **momento humano**, que trava o card (D-11)
- executor **outro card** → é a **dependência por artefato**, que trava e destrava sozinha
- executor **verbo que toca o mundo** → é o que dispara **confirmação** (P-07)

**Evidência a favor da distinção — do próprio exemplo do Pedro:** as etapas que ele listou
para a tarefa de estudo foram *"leitura de material, aprofundamento do estudo, realizar
exercícios, anotar no mapa mental"*. Nenhuma delas é um verbo do cliente. São **etapas com
nome próprio**, e cada uma teria um executor diferente (agente leitor, agente questionador,
VOCÊ, quem escreve na wiki).

**Atualização de 2026-08-14 — resposta encaminhada.** Sim, o executor é campo próprio, e a
leitura proposta é que ele seja o **responsável**: agente ou usuário (ver H-04). Isso confirma
que os verbos do João são vocabulário do ambiente, não estrutura do software — como as frentes.

**O que sobra:** dois valores observados não são responsáveis — **comando/conector** (é o
*como*, não o *quem*) e **"outro card"** (é dependência, e já tem lugar no `consome`). Se a
etapa precisa de dois campos — *quem responde* e *como se faz* — segue em aberto em H-04.

---

## ✅ A-14 — Papéis dentro de um ambiente compartilhado — RESPONDIDA em 2026-08-14

**Existe um admin — quem criou o ambiente — e o motivo é governança.** Mas ele não é quem
distribui trabalho: o padrão é **colaborativo por definição**, e o admin **restringe** se
quiser.

Todo usuário pode: criar tarefas, criar agentes, escrever na wiki, alocar tarefa a outro
usuário ou agente, sinalizar impeditivo, sinalizar tarefa finalizada, acionar chats de IA para
planejar, criar agentes e executar. Ver `requisitos/funcionais.md` RF-01 a RF-10 e
`principios.md` P-20.

**Isso derruba a leitura que eu tinha proposto** — de que o material apontava para "especialista
com ajudantes". Aponta para o contrário: ambiente aberto, com governança por exceção.

**O que sobra em aberto:** alocar uma etapa a outro usuário é **designação ou pedido**? A
resposta muda o que acontece quando a pessoa não faz — e é a diferença entre uma ferramenta de
coordenação e uma de comando.

---

## A-15 — Sinalização humana × verificação automática: quem decide que está pronto? (nova)

Três mecanismos de estado coexistem, e ninguém definiu como se relacionam:

| Mecanismo | Quem aciona | Registrado em |
|---|---|---|
| **Travado** — falta um artefato que outro card produz | o ambiente deduz do `consome` | glossário, cenário 01 |
| **Impeditivo** — alguém declara que a etapa está bloqueada | um usuário | RF-05 |
| **Checagem do tipo de tarefa** — o que precisa existir para fechar | configurado no tipo | A-11, P-04 |
| **Tarefa finalizada** — alguém declara concluída | um usuário | RF-06 |

**A tensão:** se o tipo de tarefa carrega uma checagem (*"discovery só fecha com diretriz
escrita"*), o que acontece quando o usuário sinaliza finalizada e a checagem não passou? O
software impede, avisa, ou registra a exceção com motivo?

Há precedente no material do cliente para a terceira via — quando o João quis manter um canal
que a regra mandava cortar, a resposta foi *"posso registrar «manter», mas aí preciso anotar o
motivo na memória"*. Exceção registrada, não bloqueada nem silenciosa. Vale considerar como
padrão geral.

*(Enquadramento original de A-14, preservado:)*

Apareceu pela primeira vez a ideia de **dono do ambiente**: *"o usuário principal, dono do
ambiente, poderia alterar essas coisas"* (meta, frentes, tipos de tarefa, regras).

Isso implica papéis com poderes diferentes, o que nunca foi discutido. Perguntas que nascem
juntas:

- Quem pode editar a **estrutura** (meta, frentes, tipos, regras, categorias da wiki)?
- Quem pode editar as **etapas de uma tarefa** que outra pessoa montou?
- Quem pode **criar agentes**, que passam a valer para o ambiente inteiro?
- Quem **aprova** o que o bibliotecário escreve na wiki — qualquer um, ou só o dono?
- E o mais delicado: quando alguém **atribui uma etapa a outro usuário** (H-04), isso é
  designação ou pedido?

**Por que importa agora:** cada resposta muda o que "colaborativo" significa. Um ambiente onde
só o dono edita a estrutura é uma ferramenta de um especialista com ajudantes; um onde todos
editam é outro produto. O material atual sugere o primeiro — na Nexus o João decide e o resto
executa — mas isso pode ser o desenho da operação dele, não do software (P-10).

---

## A-09 — segue sem resposta

A tensão da **primeira impressão ruim** (o valor só aparece depois de pensar e clicar) não foi
endereçada na rodada de 14/08. Continua aberta como risco de adoção.

---

## Fontes de material futuro

| # | O que | Quando | Por que importa |
|---|---|---|---|
| **F-01** | **Dinâmica "Chão de Fábrica"** — 3 dias, Pedro como operador geral, João como head, executando um fluxo completo **sem ferramenta**, de propósito | acordada na reunião de 14/08 | É um experimento de descoberta desenhado para achar onde trava. O João: *"é legal para ver onde que trava — p***, precisamos de tal MCP mesmo para fazer isso"*. Deve virar `bruto/` |
| **F-02** | Gravação em vídeo da reunião | Pedro citou querer usar | Recupera o que a transcrição perdeu (a tela sendo apontada) |

---

## Premissas assumidas (se caírem, muda o desenho)

| # | Premissa | Estado | Se for falsa |
|---|---|---|---|
| P-01 | O usuário quer manter a autoria do método — o ambiente não impõe metodologia | 🟢 reforçada (ver A-10, P-10) | Vira produto opinado, com fluxo fixo |
| P-02 | O trabalho acontece em ferramentas externas; o ambiente precisa alcançá-las | 🟢 confirmada — "execução escreve no mundo via conexões" | Vira caderno fechado, e recai em D-09 |
| P-03 | Contexto de longo prazo é o ativo central, não o histórico de conversa | 🟢 confirmada — a wiki lida por todo agente antes de escrever | Muda o que persiste e o que é descartável |
| P-04 | Criar agentes é operação rotineira do usuário | 🟢 confirmada — "abro um agente aqui de design" | Muda quem é o operador |
| P-05 | Um operador só | 🔴 **contestada** por A-07 | Muda persistência, identidade e concorrência |
