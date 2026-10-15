# Hipóteses de solução

**Criado:** 2026-08-14 · **Motivo:** correção do Pedro, na conversa de 14/08

---

## Por que este arquivo existe

Esta pasta é de descoberta: registra **necessidade**, não solução (ver `README.md`). Mas
algumas ideias de solução aparecem cedo, são boas, e perdê-las seria desperdício.

O erro a evitar é o que eu cometi com o bibliotecário: registrei como **princípio** (*"o
usuário não escreve direto na wiki"*) algo que é **uma hipótese de como garantir uma
necessidade**. Princípio vira restrição imposta a todo usuário futuro; hipótese é uma aposta
a testar. Confundir os dois faz o produto ficar opinado sem que ninguém tenha decidido isso.

O Pedro nomeou a distinção:

> "eu vejo que o bibliotecário e o rod-maker são uma **hipótese minha de solução para garantir
> algumas funcionalidades** do software. (…) percebe que pode haver outras soluções talvez
> melhores. Penso que isso vai ser validado com o usuário quando eu conseguir dar na mão dele
> testar e avaliar."

**Regra deste arquivo:** cada item traz a **necessidade** que tenta atender, a **hipótese**,
as **alternativas conhecidas**, e **como seria validada**. Nada aqui é decisão. Quando uma
hipótese for escolhida, a decisão acontece no chat de planejamento — não aqui.

---

## H-01 — Como garantir que a wiki mantenha forma consistente

**Necessidade (esta é firme):** o que entra na wiki precisa ter forma consistente, porque a
wiki é lida por LLM antes de qualquer trabalho. Escrita livre degrada o formato, e formato
degradado destrói a utilidade do contexto.

**Hipótese:** um agente **bibliotecário**, único responsável por escrever. O fluxo: o usuário
(ou o próprio chat) percebe que algo merece ser guardado → o bibliotecário é acionado → o
usuário revisa e confere → é salvo no formato da wiki. O usuário **lê** a wiki, mas não
escreve direto.

**Alternativa conhecida (do próprio Pedro):** um conjunto de **tools de wiki** que qualquer
agente pode usar, com a garantia de formato embutida nas tools em vez de num agente dedicado.

**O que as duas têm em comum — e é o que importa preservar:** ninguém escreve na wiki por
caminho não verificado, e existe um passo de revisão humana antes de virar contexto oficial.

**Como validar:** dar as duas na mão do usuário e ver qual ele usa sem ser lembrado.

**Status:** 🟡 hipótese · o cliente já conhece o conceito de bibliotecário (foi apresentado a
ele anteriormente) e ele já o incorporou ao vocabulário — o que é adesão, não validação.

---

## H-02 — Como garantir que agentes criados sigam uma forma que o sistema entenda

**Necessidade (firme):** criar agente é operação rotineira do usuário (ver `dores.md` D-07 e
`cenarios/03`). O agente criado precisa nascer numa forma que o ambiente saiba executar,
versionar e reaproveitar — senão cada agente vira um caso especial.

**Hipótese:** um agente **rod-maker**, responsável por construir agentes. O fluxo: o usuário
planeja com o orquestrador → o orquestrador aciona o rod-maker → **o usuário escolhe** se
continua a conversa com o rod-maker diretamente ou volta a falar com o orquestrador.

> **Pedro:** "ele fica livre em escolher em qual chat ele vai conversar e falar."

**Alternativa conhecida (do próprio Pedro):** **tools de construção de agente**, disponíveis
a qualquer agente, em vez de um agente dedicado.

**Lastro:** o nome já existe nos dois lados. No código (`rod-maker`, em `Ambiente/agente.py`)
e no material do cliente — *"construir via rodmaker o agente qualificador de MQL"*
(`plano-10-dias.md`), com dois agentes construídos assim no cronograma de dez dias.

**Como validar:** o usuário consegue criar um agente útil sozinho, sem o Pedro? É a pergunta
que A-08 deixou em aberto.

**Status:** 🟡 hipótese, com uso real já observado no arranjo manual.

---

## H-04 — Executor como responsável atribuível

**Necessidade (firme):** uma etapa precisa dizer **quem** a faz. É disso que saem os três
comportamentos mais importantes já registrados: o momento humano que trava o card (D-11), a
possibilidade de trabalho paralelo (D-10), e — no ambiente de time — saber de quem se espera o
quê (D-12).

**Hipótese [Pedro, 2026-08-14]:** o executor é o **responsável** pela etapa, e é sempre uma
entidade do software:

- um **agente** — e aí, se o software oferecer isso, ele pode ser **acionado automaticamente**,
  o que produz execução paralela sem o usuário no meio;
- um **usuário** — inclusive **outro usuário** do ambiente compartilhado, o que dá ao
  multiusuário um mecanismo concreto no nível da tarefa, em vez de só "todo mundo acessa".

**Lastro na interface do cliente:** os dois casos já aparecem lá. `VOCÊ` como executor das
etapas de gravar e aprovar; e **`Pintor`** como executor de "tracking / UTM" e "formulário →
CRM" — isto é, literalmente outro humano responsável por etapas de um card que não é dele.

E o acionamento automático também tem lastro: a interface tem uma seção **"andou sozinho"**,
listando o que avançou sem o usuário (*"6 variações de criativo geradas na marca, esperando
sua aprovação"*).

### Os dois valores que pareciam não caber — resolvidos em 2026-08-14

**(a) Comando e conector** (`/criar + Kairogen`, `/subir + Meta`). **Resolvido:** Kairogen é
um MCP — uma **ferramenta**, informação que o Pedro tem do cliente. O responsável continua
sendo o **agente**; o MCP é uma tool de que o agente dispõe.

> **Pedro:** "o responsável continua sendo o agente nesse caso; a questão é que o agente teria
> a ferramenta MCP do Kairogen para fazer a tarefa."

Logo `/criar + Kairogen` é **notação abreviada** da maquete, não um terceiro tipo de executor.
A ferramenta é do agente, não da etapa — e não é preciso um segundo campo. Ver H-05.

**(b) "outro card"** (na etapa "LP" do card de campanha). **Resolvido:** não é responsável, é
**dependência entre trabalhos** — e ela já tem lugar próprio: o `consome` do card declara
*"url da LP no ar" ← lp-clinicas*, e disso saem o estado `travado` e o destravamento
automático. O valor no campo de executor é redundância da maquete.

**Status:** 🟢 hipótese consistente. O executor é sempre **agente ou usuário**.
Falta validar em uso — na dinâmica Chão de Fábrica (F-01), verificar se aparece alguma etapa
cujo responsável não seja nem pessoa nem agente.

---

## H-05 — Ferramentas externas como MCP configurável, associado a agentes

**Necessidade (firme):** o trabalho real acontece em ferramentas externas. Um ambiente que não
as alcança devolve trabalho manual ao usuário — que é a dor D-09, e o critério que o próprio
cliente usa para escolher ferramenta: *"entre ferramentas equivalentes, ganha a que pode ser
lida por máquina"*.

**Hipótese [Pedro, 2026-08-14]:** o ambiente permite **configurar serviços MCP externos**, e
cada ferramenta configurada é **associada a um ou mais agentes**, que passam a dispor dela.

**Consequência no modelo:** ferramenta é atributo do **agente**, não da etapa. É o que fecha o
buraco (a) de H-04.

**Lastro:** o ambiente atual do cliente já funciona assim — Google Ads MCP e Kairogen ativos,
HubSpot, Meta Ads, GA4, WordPress e Gmail em instalação, Snov.io a construir
(`setup-ambiente.md`). A associação ferramenta→agente também já existe na prática: o
`arquiteto-meta` é quem lê o Meta Ads.

**Ressalvas que o próprio material do cliente registra e que valem para o produto:**
maturidade dos pacotes varia, e *"instalar MCP de terceiro é dar token de conta real a um
pacote de comunidade"* — há uma questão de confiança e credencial que ainda não foi discutida
para o FishingRod.

**Como validar:** um agente criado pelo usuário consegue usar uma ferramenta configurada por
outra pessoa, sem intervenção técnica.

**Status:** 🟡 hipótese com lastro em uso real.

---

## H-03 — Sub-etapa: parte da tarefa ou entidade reutilizável?

**Necessidade (firme):** uma tarefa é composta de passos, e o usuário refina esses passos ao
longo do tempo, à medida que aprende como faz aquele trabalho.

**Duas hipóteses, levantadas pelo Pedro, ainda sem escolha:**

**(a) Etapas nascem com a tarefa e são editáveis.** Ao criar a tarefa, as etapas vêm junto
(propostas na conversa com o orquestrador) e o usuário edita depois.

**(b) Etapas são criadas separadamente e relacionadas a uma ou mais tarefas.** A tarefa é
composta por etapas que existem por conta própria e podem ser reaproveitadas entre tarefas.

**O que separa as duas:** (a) é mais simples e mantém a tarefa autocontida; (b) permite que
um passo bem resolvido — "portão de qualidade", "revisar entendimento" — seja reaproveitado
em várias tarefas sem ser reescrito, que é o mesmo instinto de reaproveitamento que
motiva a wiki.

**Como validar:** observar, na dinâmica Chão de Fábrica (F-01), se aparecem passos repetidos
entre tarefas diferentes. Se aparecerem, (b) ganha peso; se cada tarefa tiver passos próprios,
(a) basta.

**Status:** 🟡 duas hipóteses abertas.
