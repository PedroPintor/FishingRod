# Clarificação — Functional Design de U5 `acoes`

**Fase:** CONSTRUCTION · **Unidade:** `U5 acoes` · **Portão 1 de 2, Step 5**
**Data:** 2026-10-02
**Origem:** análise das 12 respostas em `acoes-functional-design-plan.md`

---

## 0. Onde estamos

**As 12 respostas valem como decisão**: Q1=A, **Q2=B**, Q3=A, Q4=A, Q5=A, Q6=A, Q7=A, Q8=A, Q9=A,
Q10=A, Q11=A e Q12=A. As 8 reconciliações `R-FD5-1..8` não receberam objeção.

Na Q2 você foi além da minha recomendação: o orquestrador pode acionar **as 6 ações**, sempre com
confirmação. Isso é coerente com o resto. Mas, somada à Q3=A, deixa **uma** ação sem resposta. É a
única coisa que preciso de você antes de gerar os artefatos.

Também tirei **três consequências da Q2=B**. Estão na §2 para você objetar; se não objetar, valem.

---

## 1. Clarificação

### C1 — Com Q2=B e Q3=A, em qual frente o orquestrador cria uma tarefa?

Pela Q3=A, o sistema amarra as ferramentas do orquestrador à tarefa do chat dele, e o agente não
passa id nenhum. Para 5 das 6 ações, isso basta:

| Ação | Onde age, com o alvo amarrado |
|---|---|
| `criar_frente` | no ambiente do chat |
| `criar_chat`, `criar_etapa`, `concluir_etapa`, `anotar_memoria` | na tarefa do chat |
| **`criar_tarefa`** | **precisa de uma frente**, e a Q3=A não deixa o agente apontar nenhuma |

Para você, pela `/`, nada muda: a frente é a que está selecionada na tela, como sempre.

A) **Na frente da própria tarefa, sempre.** A tarefa nova nasce na mesma frente da tarefa em que o
orquestrador está. Se ele criar uma frente nova, ela fica vazia até **você** criar uma tarefa nela.
A Q3=A fica inteira: o agente não aponta nada. **(Recomendado)**: é reversível de graça. Acrescentar
um parâmetro opcional depois não quebra nada; tirar um parâmetro que o agente já usa quebra. E a
opção B exige um parâmetro que existe só para o agente, porque, pela `/`, a gramática posicional da
Q7=A leria a primeira palavra do nome da tarefa como se fosse a frente.

B) **Na frente da própria tarefa por padrão, ou numa frente que ele indicar.** `criar_tarefa` ganha
um parâmetro opcional `frente`, que só aceita o id de uma frente **do mesmo ambiente**. O ambiente
continua amarrado pelo sistema. O agente fica sabendo do id porque `criar_frente` o devolve no
resultado. É uma abertura pequena e deliberada da Q3=A, restrita ao ambiente do chat. O registro
ganha a noção de "parâmetro só para agente", que não aparece na `/` nem no botão.

X) Outro (descreva depois da tag [Answer]: abaixo)

[Answer]: A

---

## 2. Consequências que tirei da Q2=B (para objeção)

**D-Q2-1 — A família de ferramentas de ambiente são as 6 ações.** O invariante R10 de U6 ("nenhum
sub-agente carrega ferramenta de ambiente") passa a verificar os 6 nomes. O catálogo continua
declarando, ação por ação, quem pode acionar, embora hoje as 6 aceitem os dois chamadores. Assim, se
uma ação nova for só sua, isso cabe no registro sem mudar a forma.

**D-Q2-2 — `concluir_etapa` pelo agente depende de ele saber as posições.** Pela Q8=A, a etapa é
apontada pela posição. Pela Q12=A, não há ação de consulta. Então ficam duas coisas:

- **Para U7 (registrado lá):** o estado da tarefa que chega ao orquestrador a cada chamada precisa
  trazer **as etapas, com posição e situação**, e não só a memória. Sem isso, ele adivinha a
  posição.
- **Em U5:** a confirmação mostra a etapa **já resolvida** (posição **e** descrição), e não só o
  número. Se o agente errar a posição, você vê qual etapa seria concluída antes de dizer "sim".

**D-Q2-3 — Mais confirmações.** Com as 6 ações, o orquestrador montar uma frente com 3 tarefas são
4 confirmações seguidas, uma por chamada. É o custo da política constante: a rodada 4 de Units
Generation tirou o "aprovar tudo" desta iteração. Fica registrado como custo aceito, e não como algo
a resolver em U5.

[Objeção]: sem objecoes
