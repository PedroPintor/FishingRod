# Princípios — as regras de decisão do ambiente

**Atualizado:** 2026-08-14 · **Origem:** reunião de 2026-08-14 + `interface-v3-nexus.html`

Regras que resolvem dúvida futura sem nova reunião. Cada uma traz o critério **e** o motivo —
princípio sem motivo envelhece e ninguém sabe se pode remover.

Marcação: **[acordado]** negociado ao vivo · **[fala]** dito pelo João · **[interface]** está
no HTML dele, não verbalizado.

---

## P-01 — O alcance da resposta decide onde ela mora

**[interface]** Se o resultado vale só para este objetivo, é **aba** dentro do card. Se vale
para todos os cards futuros, é **card próprio** — e vira diretriz.

> *"A pergunta que decide não é o assunto — é o alcance da resposta."*

**Por quê:** resposta de alcance amplo presa dentro de um card morre junto com ele. Foi o caso
concreto discutido: "qual é o estilo de LP da Nexus" não podia ser aba da campanha de clínicas,
porque vale para toda página futura.

## P-02 — O card mora na frente onde o resultado final acontece

**[acordado]** Uma tarefa pode atravessar várias frentes nas subetapas. O card fica onde o
**artefato final** nasce.

> **Pedro:** "qual é o critério para criar na frente certa?" — **João:** "o final. O final é
> mídia, certo? É uma campanha. Campanha é subir campanha."

## P-03 — O card se expande; não se duplica

**[acordado]** Quando um trabalho já feito numa frente pode render em outra, não se cria uma
tarefa nova do zero — estende-se a existente a partir de onde ela parou.

> **João:** "eu já fiz uma tarefa em conteúdo e aí eu tive uma ideia que eu posso também criar
> uma campanha e ela já está lá. **Eu crio só daqui para cá, porque daqui para cá eu já tenho.**"

## P-04 — Discovery só fecha quando existe diretriz escrita que muda o que se faz

**[interface]** Se o discovery terminou e nada mudou no que se faz, **era conversa** — e o card
não fecha.

**Por quê:** é o que impede o ambiente de acumular reflexão que não vira comportamento. Sem
esse critério, discovery vira desculpa para não executar.

## P-05 — A diretriz entra sozinha em todo card novo; o usuário não repete briefing

**[acordado]** Uma vez promovida à wiki, a regra é lida por todo agente antes de escrever
qualquer coisa. Nenhum card novo precisa ser reinformado.

> **João:** "ou seja, eu não repito mais isso."
> Do HTML: *"ele não entrega uma peça, entrega uma regra — e a regra trabalha sozinha em todo
> card futuro. É assim que o ambiente vira ativo em vez de esforço."*

## P-06 — A regra mora na wiki, não na cabeça

**[interface, ecoando `painel.md`]** Regras de corte e escala ficam escritas e são aplicadas
mesmo quando contrariam a vontade do momento.

> *"Valem mesmo quando doer. E é por isso que estão aqui, e não na sua cabeça."*

E quando o usuário decide contra a regra, o motivo é anotado — a exceção fica registrada, não
apagada. (No HTML: *"posso registrar «manter» — mas aí eu preciso anotar o motivo na memória"*.)

## P-07 — Verbo que toca o mundo real pede confirmação

**[interface]** Rascunho não pede. Gastar dinheiro, enviar para terceiro e publicar pedem
confirmação explícita.

> *"Ação que gasta dinheiro real sempre pede confirmação explícita antes de executar."*

## P-08 — O trabalho pede o card, não o usuário

**[interface]** Cards nascem de dentro do trabalho quando uma dependência aparece, não só de
planejamento prévio.

> Do HTML: *"Abri o card na frente de conteúdo quando o copy viu que a home não promete
> diagnóstico com as palavras do anúncio. **Você não pediu — o trabalho pediu.**"*

## P-09 — Painel não é tela; é insumo

**[fala]** O usuário rejeitou visualização de números como interface. Ele quer documento.

> **João:** "isso aqui para mim é um documento. Tem que ser um documento, mano. É um documento
> lá, que eu nem vejo, sabe? (…) esse painel não é para eu olhar, é só um insumo. **Então se é
> um insumo, ele não precisa de uma tela.**"

**Por quê importa:** contraria a intuição de construir dashboard. Vale como antídoto contra
investir esforço onde o usuário declarou não haver valor.

## P-10 — Regra de negócio do usuário ≠ regra do software

**[acordado]** Distinção feita na hora, e vale como método permanente.

O João estabeleceu que "conteúdo pode entrar dentro das outras frentes, mas as outras não
entram dentro de conteúdo". O Pedro respondeu:

> "isso aí é uma regra sua de execução. Isso independe de como as partes funcionam. É uma
> **regra de negócio**." — **João:** "uma regra de negócio."

**Como aplicar:** o ambiente não deve embutir a hierarquia de frentes do João. Ele deve
permitir que cada usuário escreva a sua.

## P-12 — O ambiente é do usuário; o software garante a estrutura, não o conteúdo

**[Pedro, 2026-08-14]** O software não entrega um ambiente pronto nem um método. Entrega o
lugar e a estrutura onde o usuário monta o ambiente colaborativo **do jeito que ele pensa**.

> **Pedro:** "o ambiente é um componente do software onde o usuário cria o seu ambiente de
> trabalho colaborativo da maneira que ele quer e pensa. O software tem que ser esse ambiente
> onde ele consiga criar isso e conseguir usar chats de IA para resolver os seus problemas."

**Como testar na prática:** frentes, cards, tipos de tarefa, agentes e regras de organização
são do ambiente. Se um item precisa ser igual em todos os ambientes, ele precisa de
justificativa explícita — e vira exceção documentada, não padrão silencioso.

## P-13 — Convidar é opcional: o mesmo ambiente serve a uma pessoa e a um time

**[Pedro, 2026-08-14]** O ambiente é de quem o criou. Ele pode convidar pessoas, ou não.
Trabalho solo não é um modo degradado — é o caso de um participante só.

> **Pedro:** "o ambiente é um lugar onde o usuário pode ou não convidar pessoas para fazer
> parte daquele ambiente colaborativo junto com ele."

**Por quê:** os dois cenários registrados provam a necessidade — o ambiente de aquisição da
Nexus é de time; o ambiente de estudos é de uma pessoa. Um desenho que só sirva a um dos dois
elimina metade do produto.

## P-14 — Nada entra na wiki por caminho não verificado

**[Pedro, 2026-08-14 — reformulado em 2026-08-14 após correção dele]** O que entra na wiki
tem **forma garantida**, e passa por **revisão humana** antes de virar contexto oficial.

**Por quê:** a wiki é lida por LLM antes de qualquer trabalho. Escrita livre degrada o
formato, e formato degradado destrói a utilidade do contexto — que é o ativo central do
produto.

> ⚠️ **O *como* não é princípio.** Agente bibliotecário e tools de wiki são duas hipóteses
> concorrentes para atender esta necessidade, e a escolha ainda não foi feita. Ver
> `hipoteses-de-solucao.md`, H-01. A versão anterior deste princípio dizia *"o usuário não
> escreve direto na wiki"* — isso era solução, não necessidade, e virava restrição imposta
> sem decisão.

## P-16 — O ambiente é utilizável antes de estar completo

**[Pedro, 2026-08-14]** Dia zero: a meta existe, as frentes que o usuário já pensou existem,
a wiki está **inicializada — não completa, mas já funcional**. Cards, etapas e agentes não
existem ainda, e isso não impede o trabalho de começar.

**Por quê:** um ambiente que exija configuração completa antes do primeiro uso empurra o
custo todo para o momento em que o usuário menos sabe o que quer — e é o momento em que ele
mais provavelmente desiste (ver `abertas.md`, A-09).

## P-17 — O ambiente aceita duas entradas: método trazido pronto e método descoberto no uso

**[Pedro, 2026-08-14 — corrigido no mesmo dia]** Quem já é dono do domínio chega com o modelo
mental formado e monta o ambiente completo de saída: tipos de tarefa, regras, configurações,
wiki mais estruturada. Quem não sabe ainda cria a tarefa sem etapas e as descobre conversando
com o orquestrador — depois melhora por atrito, e vira agente quando a repetição justifica.

**Nenhuma das duas pode ser o único caminho.** Obrigar o especialista a redescobrir por
conversa o que ele já sabe é lento e irritante; obrigar o iniciante a configurar antes de usar
o empurra para decisões que ele ainda não tem como tomar.

Ver `cenarios/03` — as duas curvas estão narradas lá.

> A versão anterior deste princípio dizia *"o usuário não configura o ambiente; ele trabalha e
> o ambiente vai ficando configurado"*. Isso descreve só a partida em branco — e é falso para
> o cliente, que é justamente o usuário principal.

## P-18 — Criar um ambiente tem etapas mínimas, e a wiki é uma delas

**[Pedro, 2026-08-14]** O ambiente não existe por decreto: há uma configuração inicial básica
sem a qual ele não está de pé, e **a criação da wiki faz parte dela** — porque a wiki é parte
do ambiente, não um acessório que se liga depois.

Ela nasce **pequena**: poucas categorias de informação a guardar. E cresce pelo mesmo mecanismo
de todo o resto — o usuário conversa com um chat e cria categorias novas quando precisa.

## P-19 — Estrutura se importa; conteúdo e agentes se vivem

> **O eixo é origem, não permanência.** Nada aqui é imutável. Meta, frentes, tipos de tarefa,
> regras e categorias da wiki **são editáveis a qualquer momento** pelo dono do ambiente — a
> ideia é justamente ir melhorando sempre. O que a tabela separa é o que **precisa existir para
> o ambiente estar de pé** (ainda que inicializado de forma simples) do que **só passa a existir
> depois de trabalhar ali**. — *[Pedro, 2026-08-14]*

**[Pedro, 2026-08-14]** Meta, frentes, tipos de tarefa, regras e **a estrutura da wiki** podem
vir prontos na criação, porque são estrutura e podem já existir na cabeça do usuário. Duas
camadas **não** podem:

- **O conteúdo da wiki**, porque é contexto aprendido dentro do ambiente, nos chats. Não se
  importa conhecimento que ainda não foi produzido ali.
- **Os agentes**, porque nascem de necessidade sentida na repetição. Criar antes é adivinhar.

**A consequência incômoda:** são exatamente as duas camadas que dão o valor de longo prazo.
Todo ambiente novo — inclusive o do cliente, completo em todo o resto — **começa com a
prateleira montada e vazia**. O que o ambiente entrega no dia um precisa valer por si, ou o
usuário não chega até onde o valor está (ver `abertas.md`, A-09).

## P-20 — O ambiente é colaborativo por padrão; restringir é opção do admin

**[Pedro, 2026-08-14]** Todo usuário do ambiente pode, por definição: criar tarefas, criar
agentes, escrever na wiki, alocar tarefa a outro usuário ou agente, sinalizar impeditivo,
sinalizar tarefa finalizada e acionar chats de IA. É o **mínimo que faz um ambiente ser
colaborativo** — ver `requisitos/funcionais.md`, RF-01 a RF-07.

O **admin** (quem criou o ambiente) tem permissões a mais — alterar meta, frentes, tipos de
tarefa e regras — e pode **bloquear** funcionalidades para os demais.

**A direção importa:** o padrão é aberto e o admin fecha, não o contrário.

> **Pedro:** "temos que garantir o básico para ser o ambiente colaborativo para todos."

**O trade-off, dito em voz alta:** um ambiente que nasce aberto pode ser desarrumado por
qualquer um, e a arrumação depende de o admin perceber. O caminho oposto protegeria a estrutura
ao custo de o ambiente nascer inerte — e um ambiente colaborativo inerte não é colaborativo.

## P-15 — A wiki cresce sem forma fixa

**[Pedro, 2026-08-14]** Um grafo de arquivos `.md` que se expande conforme o ambiente aprende.
Não há esquema definido de antemão; há regra de formato.

**Consequência:** "toda tarefa de discovery obrigatoriamente anota na wiki" **não é regra do
software** — é como o João configurou a wiki dele. Outro ambiente usa a wiki de outro jeito.

## P-11 — O card trava; o usuário não

**[fala]** Quando um card espera um artefato ou um momento humano, ele para. A pessoa segue
operando outros.

> **João:** "fica só o chat aqui travado esperando… posso mudar de card aqui também. Continuar."

**Por quê:** é o que transforma "sou um só e tenho muitas funções" em trabalho paralelo real.
