# Functional Design Plan — U5 `acoes`

**Fase:** CONSTRUCTION · **Unidade:** `U5 acoes` · **Profundidade:** comprehensive
**Data:** 2026-10-02
**Base:** `unit-of-work.md` §3 (U5, critérios 1–6), `unit-of-work-story-map.md`, `components.md`
§3.1 e §3.2, `component-methods.md` §2 e §3.1 (com a emenda de U4), `application-design-plan.md`
(Pergunta 7 e decisão E), `stories.md` (US-04, US-15, US-16, US-17, US-19), TD-11 em
`code-quality-assessment.md`, e o que U1–U4 já entregaram em código: `dominio/politica.py`
(`Chamador`, `exige_aprovacao`), `dominio/etapa.py` (`ExecutorEtapa`) e
`aplicacao/servicos/servico_de_ambiente.py` (as 10 operações e os 5 erros de U4).
**Estado da base de código:** U0–U4 implementadas — **343 passed, 7 skipped**, `dependencies = []`.
`aplicacao/catalogo/__init__.py` existe vazio desde U0.

---

## 1. Contexto da unidade

| Campo | Conteúdo |
|---|---|
| **Componentes** | `CatalogoDeAcoes`, `ParserDeComando` (e os tipos que eles trocam: `Acao`, `Parametro`, `Alvo`, `Escopo`, `Resultado`) |
| **Histórias** | US-04, US-15, US-16, US-17, US-19 — U5 é a **superfície de acionamento** delas; nenhuma fecha aqui (todas fecham em U9) |
| **Dívidas** | **TD-11** (argumento com espaço quebra comando) |
| **Depende de** | U1 (`Chamador`, `exige_aprovacao`, `ExecutorEtapa`), U4 (`ServicoDeAmbiente` e seus erros) |
| **Estágios** | FD **EXECUTE** (aqui) · NFR-R **SKIP** · NFR-D **SKIP** · INFRA **SKIP** · CG **EXECUTE** |
| **Portões** | 2 (este e Code Generation) |

**Critérios de pronto herdados** (`unit-of-work.md` §3, U5):

1. `/nova-tarefa campanha de verao` interpreta o argumento inteiro (mata TD-11), com teste.
2. Toda ação é dado no registro, não `match/case`: paleta, botão e atalho leem o mesmo registro.
3. Toda ação é `async` e devolve `Resultado` tipado, nunca string.
4. Conversar **não** está no catálogo (Pergunta E2).
5. Ação acionada por agente consulta `exige_aprovacao(...)` antes de executar e, como a política
   devolve `True` nesta iteração, **sempre** passa por confirmação. Ação acionada pelo usuário via
   `/comando` executa direto.
6. `criar_chat(agente=...)` só aceita agente de lista fechada — nesta iteração `{bibliotecário}`.

## 2. Fronteira desta unidade

**Faz:** registrar as ações como dado; converter e validar argumentos; consultar a política de
aprovação quando quem aciona é um agente; traduzir as exceções de U1–U4 em `Resultado` — **num
ponto só**, como U4 deixou combinado (Q3=A de U4); e o parser da barra `/`, que só traduz sintaxe.

**Não faz:**

- Regra de negócio: é do domínio (U1). Coordenar banco e wiki: é de U4.
- Expor as ações como ferramenta MCP ou montar servidor: **U6**.
- Montar o registro nome→função e amarrar a ferramenta a um chat: **U9** (composition root).
- Escrever a frase em português que a pessoa lê, ou desenhar a caixa de confirmação: **U9**.
- Conversar: **U7** (Pergunta E2). Propostas do bibliotecário: **U8**.

## 3. O que U4 entrega para o catálogo

As 10 operações de `ServicoDeAmbiente` e a natureza de cada uma:

| Operação de U4 | Natureza | Vira ação? |
|---|---|---|
| `criar_ambiente(nome, esquema)` | ciclo de vida; recebe um `EsquemaWiki` vindo de formulário (US-09) | **Q1** |
| `carregar_ambiente(id)` | navegação | **Q1** |
| `listar_ambientes()` | consulta | **Q1** |
| `apagar_ambiente(id)` | ciclo de vida, **destrutiva**; a confirmação é da tela (critério 8 de U9) | **Q1** |
| `criar_frente(id_amb, nome)` | estrutura — escopo AMBIENTE | sim |
| `criar_tarefa(id_amb, id_frente, nome)` | estrutura — escopo FRENTE | sim |
| `criar_chat(id_amb, id_tarefa, nome_agente, nome="")` | estrutura — escopo TAREFA | sim |
| `criar_etapa(id_amb, id_tarefa, descricao, executor)` | estrutura — escopo TAREFA | sim |
| `concluir_etapa(id_amb, id_etapa)` | estrutura — escopo TAREFA | sim |
| `anotar_memoria(id_amb, id_tarefa, chave, valor, autor)` | memória — escopo TAREFA | sim |

**Erros que chegam ao catálogo** e precisam virar `Resultado`:

| Família | Erros |
|---|---|
| Domínio (U1, `ErroDeDominio`) | `NomeInvalido`, `OrquestradorDuplicado`, `AgenteInvalido` |
| Serviço (U4, `ErroDeServicoDeAmbiente`) | `FrenteInexistente`, `TarefaInexistente`, `EtapaInexistente`, `AgenteDesconhecido` |
| Persistência (U2, `ErroDePersistencia`) | `AmbienteInexistente`, `ConflitoDeVersao` (depois das 3 tentativas de U4), `BancoIlegivel`, `EsquemaIncompativel` |
| Wiki (U3, `ErroDeWiki`) | só aparece se o ciclo de vida entrar no catálogo (Q1) |

---

## 4. Reconciliações declaradas (aguardam objeção; sem objeção, viram emenda na geração)

| # | Divergência encontrada | Proposta |
|---|---|---|
| **R-FD5-1** | `unit-of-work.md` diz que o FD de U5 trata **"13 ações"**. O número veio dos 13 itens do `enum Comando` antigo (`model/comando.py`), citado na Pergunta 7 ("~100–150 linhas a mais que `match/case` para 13 comandos"). Não é requisito | O conjunto real sai da **Q1**; o "13" é riscado em `unit-of-work.md` |
| **R-FD5-2** | `component-methods.md` §2.1 define `executar: Callable[[Alvo, dict], ...]`, **sem dizer quem aciona**. O critério 5 exige distinguir agente de usuário | `CatalogoDeAcoes.executar` recebe também **quem aciona** (o `Chamador` de U1, mais o autor — ver Q5). A política é consultada **uma vez, no catálogo**, e não dentro de cada ação: assim não existe ação que "esqueça" de consultar |
| **R-FD5-3** | `component-methods.md` §2.3: `interpretar(entrada, alvo_default) -> tuple[str, dict]` recebe o alvo mas **não o devolve** | O resultado do parser passa a carregar o alvo junto. A forma exata depende da **Q9** |
| **R-FD5-4** | `components.md` §3.1 fixa os escopos em `AMBIENTE \| FRENTE \| TAREFA`, e `concluir_etapa` age sobre uma **etapa** | `concluir_etapa` tem escopo TAREFA, e a etapa é **argumento** da ação, não escopo novo — salvo se a **Q8** escolher C |
| **R-FD5-5** | Critério 6 (`criar_chat` só com agente da lista fechada) **já é cumprido por U4** (RN-A-22, `AgenteDesconhecido`) | U5 não repete a regra, pelo mesmo motivo da RN-A-02 de U4. O teste de U5 verifica só que `AgenteDesconhecido` vira o `Resultado` certo |
| **R-FD5-6** | A redação do critério 5 ("sempre devolve pedido de confirmação em vez de efetivar") depende de **como** a confirmação acontece | Fica como está se a **Q4** for B; vira "nunca efetiva antes de o usuário confirmar" se a Q4 for A |
| **R-FD5-7** | `unit-of-work.md` §4 manda apagar `model/comando.py` "ao fechar U5" | Vale a emenda de 2026-08-26 (o antigo fica até U9, decisão sua). **Nada é removido ao fechar U5** |
| **R-FD5-8** | O critério R10 de **U6** (nenhum sub-agente carrega ferramenta da família ambiente) precisa da lista de nomes dessas ferramentas, que nasce aqui. U6 depende só de U1 | O catálogo expõe quais ações valem para agente (Q2). **Onde mora o teste R10** é decisão de U6, não deste FD — fica registrado para lá |

---

## 5. Passos do Functional Design

- [x] **Step 1** — Ler a definição da unidade, o story map, as histórias, o código de U1–U4 e o `model/comando.py` antigo
- [x] **Step 2** — Criar este plano com passos em checkbox
- [x] **Step 3** — Gerar as perguntas com tag `[Answer]:` (§6) e declarar as reconciliações (§4)
- [x] **Step 4** — Guardar o plano em `construction/plans/acoes-functional-design-plan.md`
- [x] **Step 5** — 12 respostas analisadas: Q1=A, **Q2=B**, Q3–Q12=A; R-FD5-1..8 sem objeção.
      **Q2=B + Q3=A deixavam `criar_tarefa` do orquestrador sem frente-alvo** →
      `acoes-fd-clarificacao.md`: **C1=A** (a frente da própria tarefa) e D-Q2-1..3 sem objeção
- [x] **Step 6** — `construction/acoes/functional-design/domain-entities.md` (`Acao`, `Parametro`, `Alvo`, `Escopo`, `Acionamento`, `PedidoDeConfirmacao`, `PortaDeConfirmacao`, `Resultado`, 10 motivos de falha, mapeamento total de exceções)
- [x] **Step 7** — `business-rules.md` (**42 regras `RN-AC-01..42`**) e `business-logic-model.md` (fluxos de `executar` e da barra, **10 propriedades `PBT-U5-01..10`**, 10 decisões G1–G10 declaradas para o portão)
- [x] **Step 8** — Emendas aplicadas, com texto riscado: `unit-of-work.md` (U5 e as heranças de U6, U7, U8, U9), `components.md` §3.1 e §3.2, `component-methods.md` §2
- [x] **Step 9** — Conclusão apresentada. **APROVADO pelo usuário em 2026-10-02T19:01:43Z**
      ("aprovado o functional design. vamos seguir para o code generation"), incluindo G1–G10

**Prévia das propriedades testáveis** (PBT-01 — a lista final sai no Step 7, ajustada às
respostas):

| Candidata | Categoria |
|---|---|
| O parser desfaz o que a formatação faz: `interpretar(formatar(nome, texto))` devolve o mesmo nome e o mesmo texto | Round-trip (PBT-02) |
| O último argumento sai com os espaços de dentro intactos, para qualquer texto (TD-11) | Invariante (PBT-03) |
| `executar` nunca levanta exceção — para qualquer nome, alvo e argumento gerado, inclusive lixo — e sempre devolve `Resultado` | Invariante (PBT-03) |
| Agente acionando + usuário respondendo "não": o ambiente fica idêntico ao de antes e nenhuma escrita chega à porta | Invariante de segurança (PBT-03) |
| Acionar pelo catálogo como usuário deixa o ambiente no mesmo estado que chamar o serviço direto | Oráculo (PBT-05) |

---

## 6. Perguntas

Cada pergunta traz a minha recomendação e o porquê. Responda com a letra; se nenhuma servir, use
`X` e descreva.

---

### Q1 — Quais operações de U4 viram ação do catálogo?

O catálogo é o que a barra `/`, os botões e o orquestrador enxergam. O que fica fora dele, a tela
(U9) chama direto no serviço.

A) **Só as 6 de dentro do ambiente**: `criar_frente`, `criar_tarefa`, `criar_chat`,
`criar_etapa`, `concluir_etapa`, `anotar_memoria`. As 4 de ciclo de vida (criar, carregar, listar
e apagar ambiente) ficam com a tela de início, que já é quem tem o formulário do esquema (US-09) e a
confirmação de apagar (critério 8 de U9). Comandos de navegação (`/ajuda`, `/sair`, trocar de chat)
também ficam na tela, porque não mudam o ambiente. **(Recomendado)**: o catálogo passa a ser
exatamente "o que se faz dentro de um ambiente", e nada destrutivo fica a uma chamada de distância
de um agente.

B) As 6 **mais** as 4 de ciclo de vida, com um escopo novo ("instalação"), para que a tela de início
também receba `Resultado` em vez de tratar exceção.

C) As 6, o ciclo de vida **e** a navegação, como os 13 comandos antigos de `model/comando.py`.

X) Outro (descreva depois da tag [Answer]: abaixo)

[Answer]: A

---

### Q2 — Quem pode acionar cada ação?

Cada ação vai declarar no registro quem pode acioná-la. É dessa declaração que U9 tira quais ações
viram ferramenta do orquestrador.

A) **Você: as 6. O orquestrador: só as 3 que a conversa precisa** — `criar_etapa` (US-17),
`anotar_memoria` (US-04) e `criar_chat` (é como ele delega ao bibliotecário, Q14=X). Criar frente,
criar tarefa e concluir etapa ficam só com você. **(Recomendado)**: US-15 e US-16 dizem "o dono
cria", e US-19 diz "quando **confirmo** que a fiz" — nenhuma história pede o agente fazendo isso. E
cada ferramenta a menos é uma confirmação a menos para você responder.

B) Você: as 6. O orquestrador: **as 6**, sempre com confirmação.

C) Você: as 6. O orquestrador: as 3 de A **mais** `concluir_etapa`, para ele marcar a etapa cujo
executor é ele mesmo.

X) Outro (descreva depois da tag [Answer]: abaixo)

[Answer]: B 

---

### Q3 — Quando o agente aciona uma ação, quem diz em qual ambiente e tarefa ela age?

A) **O sistema, nunca o agente.** A ferramenta é amarrada à tarefa do chat em que o agente está
(U9 faz isso ao abrir a sessão). O agente passa só os argumentos da ação, como a descrição da etapa;
não existe parâmetro de id para ele preencher. **(Recomendado)**: é o menor privilégio possível. O
agente não consegue mexer em outra tarefa nem em outro ambiente — nem por engano, nem por instrução
vinda de conteúdo não confiável que entrou no contexto dele. É também a forma que a memória já tinha
desde 2026-08-07: os verbos são fabricados para cada chat, não recebidos prontos.

B) O agente passa os ids (ambiente e tarefa) como argumentos, e o catálogo confere que existem.

X) Outro (descreva depois da tag [Answer]: abaixo)

[Answer]: A

---

### Q4 — O que acontece com a chamada do agente enquanto você não responde à confirmação?

Nesta iteração toda ação acionada por agente pede sua confirmação (critério 5). Falta decidir se o
agente **espera** a sua resposta ou segue em frente.

A) **Espera.** O catálogo recebe uma "porta de confirmação", que a tela (U9) implementa. A chamada do
agente fica aguardando: com "sim", a ação executa e o agente recebe o resultado real; com "não", ele
recebe "recusada". O agente sabe, no mesmo turno, se a etapa foi criada. **(Recomendado)**: no US-17
o orquestrador cria várias etapas seguidas; se ele não souber se cada uma foi criada, tende a pedir
de novo e duplicar. **Risco declarado:** não sabemos se o SDK impõe tempo limite a uma ferramenta
que fica esperando um humano — o spike não mediu isso. Vira item de verificação em U6; se houver
limite, U5 é reaberta.

B) **Não espera.** O catálogo devolve na hora um "pedido de confirmação" (ação e argumentos
congelados), e o agente segue. Quando você aprova depois, a tela executa o pedido. O agente não
fica sabendo do desfecho no mesmo turno. É a leitura literal do critério 5.

X) Outro (descreva depois da tag [Answer]: abaixo)

> A escolha aqui vira o padrão de U8: o critério 6 de U8 manda a proposta do bibliotecário passar
> pelo **mesmo mecanismo** de U5.

[Answer]: A

---

### Q5 — Numa anotação de memória, quem é o autor?

`ServicoDeAmbiente.anotar_memoria` recebe `autor` como texto livre. A memória é quadro branco entre
agentes, e o valor dela está em saber quem escreveu.

A) **Quem acionou, preenchido pelo sistema**: o nome do agente do chat quando é agente, e `usuario`
quando é você pela `/`. Não existe parâmetro `autor` para preencher. **(Recomendado)**: um autor que
o próprio agente escolhe pode ser qualquer coisa, inclusive o nome de outro agente.

B) Parâmetro livre, preenchido por quem aciona.

X) Outro (descreva depois da tag [Answer]: abaixo)

[Answer]: A

---

### Q6 — O nome do comando `/` é o nome da ação?

A ação tem um nome que vira o nome da ferramenta do agente (`criar_tarefa`). Na barra, você digita
um comando.

A) **Um nome só, escrito de dois jeitos derivados automaticamente**: a ação `criar_tarefa` é
`/criar-tarefa` na barra e `criar_tarefa` como ferramenta. Nada para manter em sincronia. O critério
1 passa a ser `/criar-tarefa campanha de verao`. **(Recomendado)**

B) Cada ação declara também um apelido para a barra, escolhido para soar natural (`/nova-tarefa`,
`/nova-frente`, `/anotar`); o nome da ação continua sendo o da ferramenta.

C) O mesmo nome nos dois lugares, sem conversão (`/criar_tarefa`).

X) Outro (descreva depois da tag [Answer]: abaixo)

[Answer]: A

---

### Q7 — Como o texto depois do comando vira argumentos? *(TD-11)*

Algumas ações têm mais de um parâmetro. Exemplos com a opção A:
`/criar-etapa usuario assistir a aula 3` · `/anotar-memoria travado-por esperando o cliente` ·
`/criar-chat bibliotecario pesquisa de ICP`.

A) **Posicional, e o último leva o resto**: cada parâmetro pega uma palavra, e o último pega o resto
da linha, com os espaços de dentro preservados (só os das pontas saem). Consequência: a chave da
memória digitada pela `/` não pode ter espaço (`travado-por` sim, `travado por` não); pelo agente ou
por botão, pode. **(Recomendado)**: é o que `component-methods.md` §2.3 já previa, e cabe numa regra
de uma linha.

B) **Aspas, estilo terminal**: `/anotar-memoria "travado por" esperando o cliente`. Mais poderoso,
mas aspa sem fechar vira um erro de digitação novo para tratar.

C) **Nome=valor**: `/criar-etapa executor=usuario descricao=assistir a aula 3`.

X) Outro (descreva depois da tag [Answer]: abaixo)

[Answer]: A

---

### Q8 — Como se aponta uma etapa em `concluir_etapa`?

Etapa não tem nome único, e o id é um UUID que ninguém digita.

A) **Pela posição na lista da tarefa** (1, 2, 3…), como a tela mostra, convertida no id no momento
de executar. Vale igual para `/`, botão e agente. A posição não é guardada em lugar nenhum — o
serviço continua recebendo o id (RF-F16 intacto). Hoje ela é estável porque etapa só é acrescentada
no fim; não há apagar nem reordenar etapa nesta iteração. **(Recomendado)**. **Risco declarado:** se
uma iteração futura trouxer apagar ou reordenar etapa, esta decisão é reaberta.

B) **Pelo id.** `/concluir-etapa` deixa de ser digitável na prática; só o botão, que conhece o id,
aciona a ação.

C) **A etapa selecionada na tela vira parte do alvo** (escopo novo, ETAPA), e o comando não leva
argumento.

X) Outro (descreva depois da tag [Answer]: abaixo)

[Answer]: A

---

### Q9 — O parser conhece o catálogo?

A) **Não.** O parser só separa `/nome` do resto do texto e devolve os dois. Quem amarra o texto aos
parâmetros é o catálogo, que é quem sabe os parâmetros de cada ação. Assim os comandos da tela
(`/ajuda`, `/sair`) usam o mesmo parser sem precisar estar no catálogo. **(Recomendado)**: o parser
fica do tamanho que a Pergunta 7 queria ("adaptador de entrada fino e descartável").

B) **Sim**, como em `component-methods.md` §2.3: o parser recebe o catálogo e já devolve nome e
argumentos amarrados. Os comandos da tela precisariam de um registro próprio, ou de entrar no
catálogo.

X) Outro (descreva depois da tag [Answer]: abaixo)

[Answer]: A

---

### Q10 — Quão detalhado é o motivo de uma falha?

O núcleo não escreve frase em português: devolve um motivo, e a tela escreve a frase. A tela também
decide **onde** mostrar — erro no campo do formulário ou aviso solto.

A) **Por categoria, com detalhe estruturado.** Cerca de 9 motivos: ação desconhecida, não
permitida para quem acionou, argumento inválido, alvo ausente na tela (ex.: `/criar-tarefa` sem
frente selecionada), alvo inexistente, regra do domínio violada, conflito com outro processo, falha
de armazenamento, recusada por você. Mais um campo de detalhe: qual parâmetro, qual id, qual regra.
**(Recomendado)**: o lugar onde a tela mostra o erro depende da categoria, não do tipo exato da
exceção — e a tela não precisa conhecer os erros de U2 e U3.

B) **Um motivo por tipo de erro**, espelho dos cerca de 12 erros de U1–U4.

C) **Só sucesso ou falha**, mais o texto do erro.

X) Outro (descreva depois da tag [Answer]: abaixo)

[Answer]: A

---

### Q11 — E quando aparece um erro que ninguém previu, ou seja, um defeito?

A) **Vira `Resultado` de "falha inesperada", e o erro completo vai para o log** (`fishingrod.acoes`,
nível ERROR, com a pilha de chamadas). A tela nunca recebe exceção crua e a aba não cai.
Cancelamento continua passando, porque não é falha. **(Recomendado)**: é o comportamento à prova de
falha que SECURITY-15 pede, e o defeito não some, porque fica no log.

B) **Propaga.** Só os erros conhecidos viram `Resultado`; um defeito sobe até a tela, que decide o
que fazer.

X) Outro (descreva depois da tag [Answer]: abaixo)

[Answer]: A

---

### Q12 — O catálogo tem ações só de leitura, como o agente consultar as etapas da tarefa?

A) **Não nesta iteração.** A tela desenha a árvore direto do objeto `Ambiente`, que é o mesmo do
serviço (Q1=A de U4). O agente recebe o estado da tarefa por outro caminho: a memória é relida a
cada chamada (decisão de 2026-08-07), e isso é de U7. **(Recomendado)**: toda ação do catálogo muda
estado, então a política de aprovação continua valendo sem exceção.

B) **Sim**: uma ação `ver_tarefa` (etapas com posição e estado, chats e memória), sem confirmação,
porque não muda nada. Exige que a política passe a distinguir leitura de escrita.

X) Outro (descreva depois da tag [Answer]: abaixo)

[Answer]: A
