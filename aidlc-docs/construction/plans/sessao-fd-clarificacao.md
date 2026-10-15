# Clarificação — Functional Design de U6 `sessao`

**Fase:** CONSTRUCTION · **Unidade:** `U6 sessao` · **Portão 1 de 4, Step 5**
**Data:** 2026-10-02
**Origem:** análise das 14 respostas em `sessao-functional-design-plan.md`

---

## 0. Onde estamos

**As 14 respostas valem como decisão**: Q1=B, Q2=B, Q3=B, Q4=A, Q5=A, **Q6=B**, **Q7=A com um
acréscimo seu**, Q8=A, Q9=A, Q10=A, Q11=A, **Q12=B**, Q13=A e Q14=A. As 11 reconciliações
`R-FD6-1..11` não receberam objeção.

Duas respostas foram diferentes da minha recomendação, e uma veio com um acréscimo:

- **Q6=B**: em vez de recusar a segunda mensagem, ela entra numa **fila**.
- **Q7=A + ESC**: você quer que interromper funcione como o ESC do Claude Code, em que a mensagem
  **volta para o campo de texto** para você reescrever.
- **Q12=B**: **sem limite** de passos por turno.

Fila e ESC se encontram, e juntas deixam três pontos em aberto (§2). Antes deles, há um fato que
muda a forma das perguntas (§1). Q12=B não precisa de pergunta, mas tem uma consequência que você
deve ver (§3).

---

## 1. Um fato antes das perguntas: mensagem entregue não volta

Quando uma mensagem **chega ao agente**, ela entra na conversa que o CLI do Claude mantém para
aquela sessão. O SDK que medimos não tem operação para apagar uma mensagem de uma sessão viva.
Daí em diante o agente **lembra dela**, mesmo que ela suma da tela.

Só há dois jeitos de o agente "desver" uma mensagem:

- abrir uma **sessão nova**, e ele esquece **todo** o chat, não só aquela mensagem (R-FD6-10);
- o **"voltar no tempo"** do Claude Code. No SDK isso não foi medido, e passaria pelo mesmo mecanismo
  de retomada que você deixou para a próxima iteração na Q5.

Por outro lado, uma mensagem que **ainda não chegou** pode voltar ao campo sem deixar rastro. Pela
Q2=B e pela Q6=B, isso acontece em dois casos: quando ela está na fila e quando a conexão ainda está
subindo na primeira mensagem do chat.

---

## 2. Clarificações

### C1 — Como funciona a fila?

Você escreveu: *"enquanto o usuario espera o Agente pensar ele pode digitar mais alguma informacao e
enviar"*.

A) **Cada mensagem é um turno, na ordem.** A espera fica na própria sessão (U6). Se você mandar três
mensagens enquanto o agente responde, ele vai responder três vezes depois que acabar.

B) **O que acumula na fila sai junto, numa mensagem só, quando chega a vez**, com as mensagens
separadas por quebra de linha. É como o Claude Code faz. A fila fica no serviço de conversa (U7), que
já é dono do mapa `chat → sessão`. A sessão continua aceitando **um turno por vez** e recusa um
segundo turno simultâneo, mas isso vira só proteção contra defeito de U7. Você nunca a vê.
**(Recomendado)**: o que você descreveu é "mais alguma informação", e ela chega inteira ao agente,
que responde uma vez levando tudo em conta. São menos turnos, gastam menos assinatura, e é o
comportamento que você já conhece.

C) **Injetar no turno em andamento**: o Claude Code recente entrega a mensagem entre um uso de
ferramenta e outro, e o agente a vê antes de terminar. Isso não foi medido no SDK, e mexe no meio de
um turno que pode estar esperando a sua confirmação.

X) Outro (descreva depois da tag [Answer]: abaixo)

[Answer]: B

---

### C2 — O que o ESC faz com a mensagem?

No momento do ESC pode haver um turno em andamento **e** mensagens na fila. Em qualquer opção,
valem as regras da Q7: o que está em execução é cancelado, inclusive a espera da confirmação, e
**o que já executou continua feito**. Uma etapa que você confirmou antes do ESC continua criada.

A) **Um ESC para tudo e devolve o que dá para devolver sem mentir.** Interrompe o turno e as
ferramentas. O texto da fila volta ao campo sem deixar rastro. O texto da mensagem interrompida
**também** volta ao campo, para você reescrever. Se ela já tinha chegado ao agente, continua na
transcrição, marcada como interrompida, porque ele a viu e vai lembrar dela. Se ainda não tinha
chegado, some sem rastro. **(Recomendado)**: a tela nunca mostra uma conversa diferente da que o
agente tem na cabeça. E você ganha o que pediu, que é o texto de volta para corrigir. Para a tela
saber qual dos dois casos aconteceu, o turno passa a avisar **quando a mensagem chegou ao agente**
(um evento novo, o primeiro do turno; ver D-C2-1).

B) **A mensagem interrompida some da transcrição** e volta ao campo, mesmo que o agente já a tenha
visto. Na aparência, fica igual ao Claude Code. Mas a tela e o agente passam a discordar: ele lembra
de uma mensagem que você não vê mais e pode responder a ela no próximo turno.

C) **O ESC abre uma sessão nova** para o agente esquecer a mensagem de verdade. Ele esquece também
todo o resto do chat (R-FD6-10).

X) Outro (descreva depois da tag [Answer]: abaixo)

[Answer]: A

---

### C3 — Se o turno falhar com mensagens na fila, elas seguem sozinhas?

A) **Não.** O texto da fila volta ao campo, junto com o aviso da falha, e você decide se manda.
**(Recomendado)**: se a conexão caiu, a próxima mensagem abre uma conversa sem o histórico (Q5=A).
Mandar sozinho algo que complementava a mensagem que falhou entregaria ao agente só a metade do
assunto, e sem contexto.

B) **Sim**: a fila é enviada assim que o turno que falhou termina.

X) Outro (descreva depois da tag [Answer]: abaixo)

[Answer]: A

---

## 3. Consequências que tirei das respostas (para objeção)

**D-Q12-1 — Sem limite de passos, a defesa contra um agente em laço é o ESC.** Com Q12=B, nada corta
um turno longo. As ferramentas de ambiente param na sua confirmação, mas as de leitura da wiki (U8)
não pedem confirmação e podem rodar em laço até você apertar ESC, gastando a assinatura. Registro
isso como **risco aceito** no caso de abuso de SECURITY-11, coberto pela interrupção (Q7) e pela
confirmação (U5). Não é achado bloqueante, porque a regra exige considerar o caso, e ele está
considerado. O item 6 da medição muda: em vez de "o que acontece ao atingir o limite", passa a ser
**confirmar que, sem o parâmetro, o SDK não corta o turno por conta própria**. O NFR perde o valor
do limite.

**D-C2-1 — O turno ganha um evento "mensagem entregue"** (só se C2=A). Ele é o primeiro evento do
turno e significa que a mensagem chegou ao agente. Interromper antes dele não deixa rastro;
interromper depois deixa a mensagem na transcrição. A gramática do turno vira: *entregue* →
pedaços e usos de ferramenta → exatamente um evento final. Uma falha antes da entrega, como a
conexão que não subiu, vai direto ao evento final.

**D-Q3-1 — Registrado para U7 (prompt do orquestrador).** O seu cenário em Q3 é o orquestrador
agindo no ambiente e dizendo o que fez: "ação X feita, agora Y está sendo feito no chat Z, você pode
me pedir mais coisas ou acompanhar o trabalho no outro chat". Isso é instrução de prompt ("depois de
agir, sempre conte o que fez e onde"), e mora em U7. Em U6, a Q3=B continua valendo: um turno só
com ferramentas não é falha.

**D-Q5-1 — Registrado para a próxima iteração.** Você considera a retomada do histórico (opção D da
Q5) o comportamento correto, deixado para depois. Ela entra na lista da próxima iteração junto com
US-07, e destrava também o "desver" da §1.

**D-Q7-1 — A tecla é de U9.** U6 entrega o mecanismo: interromper pelo cancelamento, e o aviso de
entrega se C2=A. U9 liga isso ao ESC, devolve o texto ao campo e mostra a mensagem interrompida. U7
grava, ou deixa de gravar, a mensagem conforme ela tenha chegado ou não ao agente.

[Objeção]: sem objecoes.
