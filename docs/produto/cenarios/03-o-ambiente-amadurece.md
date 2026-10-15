# Cenário 03 — O ambiente amadurece (montagem e evolução)

**Narrado por:** Pedro Pintor, em 2026-08-14
**Confiança:** alta como intenção · ⚠️ hipotético como uso
**Papel deste cenário:** é o que faltava. Os cenários 01 e 02 começavam com tudo pronto —
este mostra o ambiente **ficando** pronto. Responde `abertas.md` A-08.

---

## O ponto de partida: incompleto e já utilizável

> **Pedro:** "estou nesse ambiente totalmente novo, tem as frentes que eu já pensei
> inicialmente, eu tenho **uma wiki inicializada (não completa, mas já funcional, e pode
> crescer)**."

Repare no que existe e no que não existe no dia zero:

| Existe | Não existe |
|---|---|
| O ambiente, com a meta declarada | Cards prontos |
| As frentes que o usuário já pensou | As sub-etapas de qualquer tarefa |
| Uma wiki inicializada — vazia de conteúdo, viva de estrutura | Agentes próprios (só o orquestrador) |

**A estrutura precede o conteúdo.** O usuário chega com uma ideia de como quer trabalhar
(as frentes), e o ambiente aceita isso sem exigir que esteja completo.

---

## Movimento 1 — A tarefa nasce sem saber como se faz

> "estou fazendo uma tarefa de estudo, eu crio uma tarefa de estudo e **não sei muito bem
> ainda que sub etapas eu vou seguir**. Aí quando eu começo essa tarefa eu inicio um chat de
> IA e começo a falar com o orquestrador para fazer a tarefa. Conversando com o orquestrador
> eu consigo montar um plano de etapas legal que gostei, aí são criadas as sub etapas para
> essa tarefa."

O plano de trabalho **é resultado da conversa**, não pré-requisito dela. O usuário não precisa
saber o método antes de começar — ele descobre o método conversando, e o que foi descoberto
fica registrado como as etapas daquela tarefa.

No exemplo dele, a tarefa de estudo termina com: leitura do material → aprofundamento do
estudo → realizar exercícios → anotar no mapa mental.

## Movimento 2 — A tarefa é reaproveitada e refinada

> "aí em um outro dia qualquer eu posso **reaproveitar essa tarefa com esses passos** para
> fazer novamente. E eu posso perceber que quero melhorar alguma etapa da tarefa, aí eu falo
> com o meu orquestrador e **juntos melhoramos** as sub tarefas."

A tarefa vira um molde. E o molde melhora — não por configuração, mas por conversa, no momento
em que o usuário percebe o atrito.

## Movimento 3 — A etapa vira agente

> "aí em um outro dia eu vou fazer essa mesma tarefa e eu percebo que **eu poderia fazer um
> agente que me ajuda a realizar alguma das sub etapas**. Aí eu faço ele junto com o
> orquestrador."

O agente não nasce de planejamento inicial — nasce de uma etapa que já se repetiu vezes
suficientes para valer a pena. É a terceira execução que revela o candidato.

O fluxo de criação: o usuário planeja com o orquestrador → o orquestrador aciona o rod-maker →
**o usuário escolhe** se conversa direto com o rod-maker ou volta ao orquestrador.
*"Ele fica livre em escolher em qual chat ele vai conversar e falar."*
(Ver `hipoteses-de-solucao.md` H-02 — o rod-maker é hipótese, não decisão.)

---

## A curva, em uma linha

```
dia 1     tarefa sem etapas  →  conversa  →  etapas existem
dia N     mesma tarefa       →  atrito    →  etapas melhores
dia N+M   mesma tarefa       →  repetição →  agente dedicado
```

Cada volta deixa o ambiente mais capaz de fazer aquilo. **O usuário não configura o ambiente:
ele trabalha, e o ambiente vai ficando configurado.**

---

---

## A curva oposta: quem chega com o modelo mental pronto

**[Pedro, 2026-08-14]** O cenário acima é de quem começa em branco. O do cliente é o inverso,
e pelo melhor motivo possível:

> "ele sabe exatamente o que quer, pois está pensando nisso há muito tempo, e **ele é o dono
> do domínio de negócio** — entende muito bem do negócio e já trabalha com isso há anos, então
> ele já tem um modelo mental inteiro na cabeça de como trabalhar. Por isso o ambiente dele,
> quando for inicializado, já vai estar bem mais completo: mais tipos de tarefa criados, mais
> regras e configurações feitas."

Isso bate com o material: as seis frentes, as três naturezas, os 14 verbos, as regras de corte
e a escada de oferta já existiam **antes** de qualquer software — estão escritos em
`frentes.md`, `painel.md` e nos knowledges, e foram levados prontos para a interface.

### Duas entradas, não uma

| | Partida em branco (estudos) | Partida carregada (aquisição) |
|---|---|---|
| **Quem** | quem ainda não sabe como faz | dono do domínio, método já formado |
| **No dia zero existe** | meta, frentes iniciais, wiki com poucas categorias | meta, frentes, **tipos de tarefa, regras, configurações**, wiki mais estruturada |
| **Como o método aparece** | descoberto conversando com o orquestrador | trazido pronto de fora |
| **O risco** | desistir antes de o valor aparecer | ser obrigado a redescobrir por conversa o que já sabe |

Obrigar o especialista a chegar ao método por conversa seria lento e irritante — ele já pagou
esse custo, anos atrás. Obrigar o iniciante a configurar antes de usar o empurraria para
decisões que ele ainda não tem como tomar.

## Criar um ambiente é um processo, com etapas mínimas

**[Pedro, 2026-08-14]** O ambiente não passa a existir por decreto: há uma configuração inicial
básica sem a qual ele não está de pé. **Uma dessas etapas é a criação da wiki.**

> "quando se cria um ambiente você vai ter que fazer alguns processos de configurações iniciais
> básicas para o ambiente ser inicializado e criado de fato. Uma dessas etapas básicas eu penso
> que é **a criação inicial da wiki**, porque a wiki é parte do ambiente."

E ela nasce pequena, com poucas **categorias** de informação a guardar — e cresce pelo mesmo
mecanismo de tudo o mais aqui, conversando:

> "mesmo que a wiki comece pequena com poucas categorias de informações para serem salvas, o
> usuário, quando já tiver o ambiente feito, pode a qualquer momento, conversando com um chat
> de IA, **melhorar a wiki e criar novas categorias** para armazenar o contexto."

## O que **não** pode ser trazido pronto — nos dois casos

Estrutura pode vir pronta, inclusive a da wiki. Duas coisas não podem.

> ⚠️ **A tabela separa origem, não permanência.** Nada nela é imutável: meta, frentes, tipos de
> tarefa, regras e categorias da wiki **são editáveis a qualquer momento** pelo dono do
> ambiente — *"a ideia é ir melhorando sempre"*. O que a coluna da esquerda diz é apenas que
> essas coisas **precisam existir para o ambiente estar de pé**, ainda que inicializadas de
> forma simples. — *[Pedro, 2026-08-14]*

| Camada | Vem na criação do ambiente? | Por quê |
|---|---|---|
| Meta, frentes, tipos de tarefa, regras | ✅ sim | é estrutura — o usuário pode já tê-la na cabeça |
| **Estrutura da wiki** (as categorias) | ✅ sim, é etapa da criação | começa pequena e cresce por conversa |
| Etapas de uma tarefa | 🟡 em parte | quem sabe o método traz; quem não sabe descobre |
| **Conteúdo da wiki** | ❌ não | é contexto **aprendido dentro do ambiente**, nos chats. Não se importa conhecimento que ainda não foi produzido ali |
| **Agentes** | ❌ não | nascem de **necessidade sentida na repetição** — *"o usuário vai sentir a necessidade de automatizar uma tarefa com um agente pois já fez aquilo várias e várias vezes"* |

**Estrutura se importa; conteúdo e agentes se vivem.**

E há uma consequência incômoda: as duas camadas que não podem vir prontas são exatamente as
que dão o valor de longo prazo. **Todo ambiente novo começa com a prateleira montada e vazia** —
inclusive o do cliente, que em tudo o mais já nasce completo. Isso liga direto ao risco A-09:
o valor aparece depois, e é preciso que o usuário chegue até lá.

---

## O achado: o ambiente aprende por duas vias, não uma

Até aqui, "o ambiente aprende" significava wiki. Este cenário mostra uma segunda via, distinta:

| Via | O que guarda | Como cresce | Onde vive |
|---|---|---|---|
| **Wiki** | o que se **sabe** — diretrizes, contexto, decisões | discovery promove | no ambiente inteiro |
| **Etapas da tarefa** | como se **faz** aquele trabalho | refinamento por atrito, na conversa | na tarefa |
| *(e a terceira, derivada)* | **quem faz** — o agente dedicado | repetição justifica a criação | no ambiente, reutilizável |

São memórias diferentes com regimes diferentes. Confundi-las custa caro: método de trabalho
registrado como conhecimento vira texto que ninguém executa; conhecimento registrado como
etapa vira instrução presa a uma tarefa só.

---

## O que este cenário ainda não resolve

- **Quem cria as frentes iniciais, e com base em quê?** O usuário "já pensou" nelas — mas
  ninguém mostrou esse pensar acontecendo. É o resto de A-08.
- **O que é uma "wiki inicializada"?** Vazia com estrutura, ou com algum conteúdo semente?
- **Quando o ambiente é de time**, quem pode editar as etapas de uma tarefa que outra pessoa
  montou? Nada foi dito.
- Continua **hipotético**: nenhuma parte foi operada.
