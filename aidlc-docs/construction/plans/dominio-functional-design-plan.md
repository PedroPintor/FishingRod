# Functional Design Plan — U1 `dominio`

**Fase:** CONSTRUCTION · **Unidade:** `U1 dominio` · **Profundidade:** comprehensive
**Data:** 2026-08-25
**Base:** `unit-of-work.md` §3 (U1), `unit-of-work-story-map.md`, `components.md` §2,
`component-methods.md` §1, código atual `Ambiente/ambiente.py`, `Ambiente/memoria.py`,
`Ambiente/sessao.py`, `model/mensagem.py`

---

## 1. Contexto da unidade

| Campo | Conteúdo |
|---|---|
| **Componentes** | `Identidade`, `Ambiente`, `Frente`, `Tarefa`, `Chat`, `Etapa`, `Memoria`, `RaizWiki`, `Agente` (configuração) + `politica.py` (rodada 4) |
| **Histórias** | US-04, US-05 (estrutura), US-15, US-16 (invariantes de criação) |
| **Dívidas** | **TD-03** — `Memoria.anotar()` lança `KeyError` na primeira escrita de chave nova |
| **Depende de** | U0 (concluída e aprovada) |
| **Estágios** | FD **EXECUTE** (aqui) · NFR-R SKIP · NFR-D SKIP · INFRA SKIP · CG EXECUTE |
| **Extensões** | `property-based-testing` (Full) — a primeira propriedade da iteração é desta unidade |

**Fronteira, repetida porque é a regra que o resto do sistema depende:** o domínio guarda estado e
invariantes. Não persiste a si mesmo, não roteia comando, não conhece sessão viva, e não importa
`claude_agent_sdk`, `sqlite3` nem `textual` (RF-F04).

---

## 2. Achado técnico verificado antes de perguntar

**`uuid.uuid7()` não existe no Python 3.13.** Verifiquei no interpretador do projeto:
`dir(uuid)` devolve apenas `uuid1`, `uuid3`, `uuid4`, `uuid5`. A função `uuid7` entrou na stdlib
no **3.14**. Como `component-methods.md` §1.1 especifica UUIDv7 e o `requires-python` da U0 é
`>=3.13`, isso precisa de decisão — é a **Q3** abaixo. Registro como achado, não como opinião:
nenhum artefato anterior errou, a especificação foi escrita antes de alguém checar a versão.

---

## 3. Passos do Functional Design

- [x] **Step 1** — Consolidar respostas às perguntas da §4 e analisar ambiguidades
- [x] **Step 2** — Se houver resposta vaga ou contraditória, criar
      `dominio-functional-design-clarification-questions.md` e **não** prosseguir
      → **criado em 2026-08-25 com CQ1 (bloqueante), CQ2 e CQ3; execução parada aqui**
- [x] **Step 3** — Gerar `construction/dominio/functional-design/domain-entities.md`
      (entidades, atributos, tipos, relacionamentos, ciclo de vida)
- [x] **Step 4** — Gerar `construction/dominio/functional-design/business-rules.md`
      (invariantes, validações, regras de erro, com identificador por regra)
- [x] **Step 5** — Gerar `construction/dominio/functional-design/business-logic-model.md`
      (operações de domínio, pré e pós-condições, fluxos de criação)
- [x] **Step 6** — Nomear as **propriedades PBT** desta unidade com estratégia `hypothesis`
      (exigência da extensão `property-based-testing`, PBT-01 a PBT-10)
- [x] **Step 7** — Registrar conformidade das extensões habilitadas e apresentar o portão

**Sem `frontend-components.md`** — U1 não tem UI (isso é U9).

---

## 4. Perguntas

Responda preenchendo a tag `[Answer]:` de cada uma. Onde eu tenho recomendação, ela está declarada
com o motivo — mas a escolha é sua.

---

### Q1 — `Ambiente` nasce com uma frente padrão?

O código atual cria `projeto-padrao` automaticamente no `__post_init__`, com a justificativa
escrita no próprio código: *"um Ambiente sem projeto nenhum não consegue responder nada"*. Isso era
verdade porque `self.projeto` acessava `projetos[indice_ativo]` e estourava `IndexError`. Com
identidade opaca substituindo índice (ESC-14), essa razão **deixou de existir**.

A) **Nasce vazio.** Nenhuma frente é criada automaticamente. Quem garante que o usuário tem onde
   trabalhar é a interface (U9). *Custo*: a TUI precisa lidar com o estado "ambiente sem frente".
   *Ganho*: nada é criado sem o usuário pedir, e o domínio fica sem comportamento mágico.
B) **Mantém a frente padrão.** `Ambiente` recém-criado já tem uma frente com nome fixo.
   *Custo*: toda leitura de "quantas frentes existem" carrega uma frente que ninguém pediu, e o
   nome padrão vira decisão de produto escondida no domínio.
C) **Nasce vazio, mas com invariante de que só pode ser salvo com pelo menos uma frente.**
   *Custo*: acopla domínio a um momento de persistência que ele não conhece.

**Minha recomendação: A.** A razão técnica que justificava B morreu com a identidade opaca, e US-15
("criar uma frente dentro do ambiente") fica mais honesta se a primeira frente também for criada
pelo usuário.

[Answer]: A - vamos seguir com essa opcao e tem mais um motivo que penso para seguir com essa opcoa. realmente a frente nao é criada automaticamente pois ela é criada quando é em um ambiente. o novo motivo é ter a tela de inicio, tem uma tela de inicio onde o usuairo seleciona um ambiente ja criado ou cria um novo é assim que a TUI lida com a criacao de frente, e o ambiente que se preocupa em relacao de criar sem frente ou nao, a frente é parte da wiki e nao se relaciona com o ambiente diretamente. quem se relaciona com o ambiente diretamente é a wiki , e a wiki que tem as frentes e suas regras de funcionalidade.

---

### Q2 — Nome duplicado de frente ou de tarefa é permitido?

Hoje `criar_projeto` e `criar_sessao` recusam nome repetido e devolvem `None`, porque o nome era a
chave de busca. Com `Identidade`, o nome deixou de identificar.

A) **Permitido.** Duas frentes podem se chamar "campanha de verão"; a identidade as distingue.
   *Custo*: a TUI precisa mostrar algo além do nome para o usuário diferenciar.
B) **Proibido, invariante de domínio.** Criar com nome repetido levanta erro.
   *Custo*: o usuário é bloqueado por uma regra que não tem razão técnica; renomear duas frentes
   para o mesmo nome depois continuaria possível a menos que `renomear` também valide.
C) **Permitido, mas a interface avisa.** Domínio não valida; U9 mostra aviso não bloqueante.

[Answer]: A

---

### Q3 — Como gerar UUIDv7 sem `uuid.uuid7` (ver §2)?

A) **Implementar em `dominio/identidade.py`.** São ~15 linhas: 48 bits de timestamp em
   milissegundos + 74 bits aleatórios + os bits de versão e variante, conforme a RFC 9562.
   *Ganho*: zero dependência de runtime — o domínio continua importando só a stdlib, o que é o que
   torna verificável o critério de RF-F04 e o de TD-02 em U6. *Custo*: código criptografado por
   ninguém; precisa de teste que confirme monotonicidade e formato.
B) **Adicionar dependência** (`uuid6` ou `uuid-utils`). *Ganho*: implementação de terceiros já
   testada. *Custo*: primeira dependência de runtime do projeto, e ela entra **no domínio** — a
   camada que os artefatos exigem manter mais limpa (RF-F04). Também amplia a superfície de
   SECURITY-10.
C) **Usar `uuid4` por enquanto.** *Custo*: perde a ordenação por tempo, que é exatamente o que
   ESC-14 e `component-methods.md` §1.1 usam para paginar transcrição sem coluna extra — a decisão
   voltaria como dívida em U2.

**Minha recomendação: A.** A propriedade que precisamos (ordenável por tempo, único) é testável por
PBT, e manter o domínio sem dependência é uma das poucas regras que atravessa a arquitetura inteira.

[Answer]: tenha uma observacao : realmente usar o uuidv7 é bom para termos o rastro de tempo . eu vi em algum lugar que vc pensou que a versao do python que temos definida é abaixo e nao temo o uuidv7. pq nos somente nao aumentamos a nossa versao de uso do python para esse projeto? 

---

### Q4 — Quem fornece o `Agente` orquestrador quando uma tarefa é criada?

`component-methods.md` §1.3 diz que `Frente.criar_tarefa(nome)` cria a tarefa **já com um `Chat` do
orquestrador padrão**. Mas o domínio não pode conhecer a instância concreta do orquestrador — ela é
configuração montada no composition root (U9).

A) **`criar_tarefa(nome, agente_orquestrador: Agente)`** — quem chama passa o agente.
   *Ganho*: domínio puro, sem conhecer instância. *Custo*: a assinatura de `component-methods.md`
   §1.3 muda (emenda declarada).
B) **A tarefa nasce sem chat**; quem cria o chat inicial é `ServicoDeAmbiente` (U4).
   *Ganho*: mesma pureza, e a criação do chat fica junto da persistência.
   *Custo*: existe um instante em que a tarefa não tem chat nenhum — a invariante "toda tarefa tem
   um orquestrador" deixa de valer no domínio e vira regra de serviço.
C) **Constante de domínio** com o orquestrador padrão. *Custo*: solda configuração ao domínio;
   contradiz `components.md` §2.9.

**Minha recomendação: A.** Mantém a invariante dentro do domínio, onde ela é testável sem serviço.

[Answer]: A 

---

### Q5 — `Etapa`: `concluir()` é reversível? Existe ordem?

`component-methods.md` §1.6 define `descricao`, `executor`, `concluida` e `concluir()`. Faltam duas
regras.

**5a — reabrir**
A) `concluir()` é idempotente e **não** existe `reabrir()` — etapa concluída fica concluída.
B) Existe `reabrir()`; o usuário pode desmarcar.

**5b — ordem**
A) As etapas têm ordem (posição na lista), e concluir uma não exige que as anteriores estejam
   concluídas.
B) As etapas têm ordem **e** dependência: só se conclui a próxima se a anterior estiver concluída.
C) Sem ordem — é um conjunto.

[Answer 5a]: B

[Answer 5b]: A 

---

### Q6 — `Memoria`: o que sobrevive do código atual?

Hoje existem `versao: int`, `anotar_plano()` (que recusa se já houver plano) e `formatar()` (que
devolve só o plano). O desenho novo (`component-methods.md` §1.7) mostra apenas `anotar()`.

A) **Só `anotar()`.** `versao`, `anotar_plano` e `formatar` saem. *Motivo a favor*: `anotar_plano`
   é regra de um fluxo específico que ainda não existe nesta iteração, e `formatar` mistura
   apresentação com domínio.
B) **Mantém `versao`** (útil para detectar escrita concorrente em U2), sai o resto.
C) Mantém tudo.

**Minha recomendação: A**, com a ressalva honesta de que, se U2 precisar de detecção de conflito, o
`versao` volta — e voltar é barato, porque é um campo.

[Answer]: B - vamos usar anotar() e manteer versao para entender ordem

---

### Q7 — Violação de invariante: exceção ou valor de retorno?

Hoje o código devolve `None` (`criar_projeto` recusando duplicata) e a camada de cima interpreta.
Os casos desta unidade: nome vazio, segundo orquestrador na mesma tarefa (`components.md` §2.4),
identidade inexistente em `buscar_*`.

A) **Exceções de domínio tipadas** (`ErroDeDominio` e subclasses); `buscar_*` continua devolvendo
   `None` porque "não achei" não é violação de regra.
B) **Nunca exceção**: toda operação devolve `Resultado` tipado. *Custo*: `Resultado` é conceito da
   camada de aplicação (`component-methods.md` §2.4); trazê-lo para o domínio inverte a dependência.
C) Misto por caso, decidido regra a regra.

**Minha recomendação: A.**
 
[Answer]: A - garante uma boa forma de comunicar o erro e passar adiante e temos o controle de como tratar.

---

### Q8 — Assinatura de `exige_aprovacao(...)` em `dominio/politica.py`

Da rodada 4: a política é constante nesta iteração (sempre `True`), mas a assinatura decide o quanto
custa torná-la configurável depois.

A) **`exige_aprovacao(chamador: Chamador) -> bool`**, com `Chamador = AGENTE | USUARIO`.
   Devolve `True` só para `AGENTE`. *Ganho*: expressa a regra real (`/comando` do usuário executa
   direto) e é o mínimo que já responde certo.
B) **`exige_aprovacao(chamador: Chamador, acao: str) -> bool`** — permite granularidade por ação
   quando a configuração voltar. *Custo*: um parâmetro que nada usa hoje.
C) **`exige_aprovacao() -> bool`** sem parâmetro. *Custo*: U5 teria que decidir por fora quem é o
   chamador, espalhando a regra.

**Minha recomendação: A.**

[Answer]: A

---

### Q9 — Quem monta o localizador da `RaizWiki`?

`components.md` §2.8 fixa o formato `dados:wikis/<id_ambiente>` e diz que o domínio **não** resolve
o esquema em caminho real.

A) **O próprio `Ambiente`**, no construtor, a partir da própria identidade. *Ganho*: impossível
   existir ambiente sem raiz coerente. *Custo*: o formato do localizador fica escrito no domínio.
B) **`ServicoDeAmbiente` (U4)** monta e injeta. *Custo*: `Ambiente` pode existir com raiz vazia.

**Minha recomendação: A** — é o que torna a coerência uma invariante em vez de uma convenção.

[Answer]: A 

---

## 5. O que este estágio **não** decide

- Nada de SQLite, tabela, serialização ou round-trip — isso é U2
- Nada sobre como a wiki é escrita no disco — U3
- Nada sobre o catálogo de ações nem sobre o fluxo de confirmação na tela — U5 e U9
- Nenhum código: Functional Design produz especificação; a implementação é o Code Generation de U1
