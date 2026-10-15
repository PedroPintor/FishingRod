# Functional Design Plan — U4 `ambiente`

**Fase:** CONSTRUCTION · **Unidade:** `U4 ambiente` · **Profundidade:** comprehensive
**Data:** 2026-10-02
**Base:** `unit-of-work.md` §3 (U4, critérios 1–6 com as emendas de U2 e U3),
`unit-of-work-story-map.md`, `components.md` §3.3, `component-methods.md` §3.1, `services.md` §2,
§5 e §6, `stories.md` (US-04, US-05, US-08, US-09, US-15, US-16, US-19), e o que U1, U2 e U3 já
entregaram em código: `dominio/`, `aplicacao/portas/persistencia.py`, `aplicacao/portas/wiki.py`,
`aplicacao/esquema_wiki.py` e `construction/wiki/functional-design/business-logic-model.md` §6.
**Estado da base de código:** U0–U3 implementadas — **272 passed, 7 skipped**, `dependencies = []`.

---

## 1. Contexto da unidade

| Campo | Conteúdo |
|---|---|
| **Componente** | `ServicoDeAmbiente` (`aplicacao/servicos/`) |
| **Histórias** | US-05 (**U4 fecha** a história), US-08, US-09, US-15, US-16 — e, pelo story map, também US-04 e US-19 (ver R-FD4-3) |
| **Dívidas** | Nenhuma |
| **Depende de** | U1 (domínio), U2 (`PortaPersistencia`), U3 (`PortaWiki`, `EsquemaWiki`) |
| **Estágios** | FD **EXECUTE** (aqui) · NFR-R **SKIP** · NFR-D **SKIP** · INFRA **SKIP** · CG **EXECUTE** |
| **Portões** | 2 (este e Code Generation) |

**Critérios de pronto herdados** (`unit-of-work.md` §3, U4):

1. Criar ambiente materializa a wiki a partir do `EsquemaWiki` (convertido em `PropostaWiki`) e
   chama `renderizar_index`, numa operação só. Wiki sem entidade é válida.
2. Criar frente / tarefa / chat, concluir etapa e anotar memória **delegam a invariante ao domínio**
   e persistem via porta.
3. Nenhum `import` de `sqlite3` nem de `claude_agent_sdk`.
4. Vários ambientes locais coexistem; `carregar_ambiente(id)` devolve o certo, cada um com a sua
   raiz de wiki.
5. **Tratar `ConflitoDeVersao`**: recarregar, reaplicar e salvar de novo, sem propagar exceção para
   a tela.
6. **Apagar ambiente é orquestrado aqui**: primeiro o banco, depois o diretório da wiki.

## 2. Fronteira desta unidade

**Faz:** coordenar domínio + `PortaPersistencia` + `PortaWiki` para cada operação de estrutura;
decidir o que acontece quando uma das portas falha no meio; reaplicar a mudança quando há conflito
de versão.

**Não faz:**

- Expor as operações como `/comando` ou como ferramenta de agente: isso é o `CatalogoDeAcoes` (**U5**).
- Consultar `exige_aprovacao(...)`: isso também é **U5** (e U8). U4 executa o que já foi decidido.
- Conversar, abrir sessão ou gravar transcrição: **U7**.
- Escrever na wiki depois da criação: **U8**.
- Qualquer tela, inclusive o formulário que produz o `EsquemaWiki` e a tela inicial: **U9**.

---

## 3. Reconciliações declaradas (aguardam objeção; sem objeção, viram emenda na geração)

| # | Divergência encontrada | Proposta |
|---|---|---|
| **R-FD4-1** | `services.md` §2, passo 5, diz que o ambiente nasce com uma **frente padrão**. O FD de U1 (**Q1=A**) decidiu o contrário, e o código de `Ambiente` já segue isso: o ambiente nasce **sem** frente, e quem garante onde trabalhar é a tela (U9) | Vale U1. Passo 5 riscado em `services.md` |
| **R-FD4-2** | `component-methods.md` §3.1 ainda diz que `criar_ambiente` "levanta erro de domínio se `esquema` não tiver nenhuma entidade" | Já revogado pela Parte B.3 de U1 e aplicado em U3. Só falta riscar esta frase |
| **R-FD4-3** | `unit-of-work.md` lista 5 histórias para U4; o `unit-of-work-story-map.md` lista **7** (acrescenta US-04 e US-19) | O story map está certo: `anotar_memoria` (US-04) e `concluir_etapa` (US-19) são operações de U4. Este FD rastreia as 7, e `unit-of-work.md` é emendado |
| **R-FD4-4** | `component-methods.md` §3.1 escreve `criar_tarefa(id_frente, nome)`, mas `Frente.criar_tarefa` exige o `Agente` orquestrador (**Q4=A** de U1) | A assinatura do serviço precisa resolver de onde vem o agente → **Q8** |
| **R-FD4-5** | `component-methods.md` §3.1 escreve `anotar_memoria(id_tarefa, ...)`, mas `PortaPersistencia.anotar` exige `id_ambiente` (emenda de U2) | Resolvido junto com **Q2** (como o serviço identifica o ambiente) |
| **R-FD4-6** | O critério 6 manda U4 apagar o diretório da wiki, mas **`PortaWiki` não tem operação de apagar**, e U4 não pode tocar o disco direto (critério 3 + D-ARQ-08) | Precisa de decisão → **Q6** |

---

## 4. Passos do Functional Design

- [x] **Step 1** — Ler a definição da unidade, o story map, as histórias e o código já entregue por U1–U3
- [x] **Step 2** — Criar este plano com passos em checkbox
- [x] **Step 3** — Gerar as perguntas com tag `[Answer]:` (§5) e declarar as reconciliações (§3)
- [x] **Step 4** — Guardar o plano em `construction/plans/ambiente-functional-design-plan.md`
- [x] **Step 5** — 12 respostas analisadas. **11 fecharam limpas** (Q1-Q6=A, Q8-Q11=A, Q12=B);
      R-FD4-1..6 sem objeção. **Q7=X abriu conflito de escopo** com US-17 e US-19 (linha fina):
      `ambiente-fd-clarificacao.md` com **C1=A** (incluir `criar_etapa` e `concluir_etapa`; 10
      operações) e D-Q12-1/2 aceitas sem objeção
- [x] **Step 6** — `construction/ambiente/functional-design/domain-entities.md`
- [x] **Step 7** — `business-rules.md` (**26 regras `RN-A-01..26`**) e `business-logic-model.md` (**5 propriedades `PBT-U4-01..05`**, 5 decisões G1–G5 declaradas para o portão)
- [x] **Step 8** — Emendas aplicadas: `services.md` §2, `component-methods.md` §3.1 e §4.3, `components.md` §3.3, `unit-of-work.md` §3 (U4)
- [x] **Step 9** — Conclusão apresentada. **APROVADO pelo usuário em 2026-10-02T15:54:41Z**
      ("aprovado o function design. vamos seguir para o proximo estagio."), incluindo G1–G5

---

## 5. Perguntas

Cada pergunta traz a minha recomendação e o porquê. Responda com a letra; se nenhuma servir, use
`X` e descreva.

---

### Q1 — O serviço guarda o ambiente aberto em memória, ou carrega da porta a cada operação?

Hoje a TUI vai segurar um `Ambiente` para desenhar a árvore. Se o serviço carregar uma cópia nova a
cada operação, o objeto que a tela tem fica velho depois de cada mudança, e a tela precisa
recarregar. Se o serviço guardar uma cópia, existe um objeto só por ambiente no processo, e a tela e
os agentes veem a mesma coisa.

A) **O serviço guarda os ambientes abertos em memória** (um objeto por id). Toda operação muda esse
objeto e depois persiste; a TUI lê do mesmo objeto. Carregar da porta só acontece ao abrir o
ambiente e ao tratar conflito. **(Recomendado)**: um objeto só elimina a classe inteira de defeito
"tela mostrando estado velho", e é o que torna a Q10 barata.

B) **Sem estado**: cada operação carrega da porta, muda e salva, e devolve o `Ambiente` atualizado
para quem chamou substituir o seu.

X) Outro (descreva depois da tag [Answer]: abaixo)

[Answer]: A

---

### Q2 — Como cada operação sabe de qual ambiente se trata?

`criar_tarefa(id_frente, nome)` não diz em qual ambiente a frente está. A porta exige `id_ambiente`
em `anotar` (R-FD4-5), e salvar exige o ambiente inteiro.

A) **Toda operação recebe `id_ambiente` explicitamente**, mais o id do alvo
(`criar_tarefa(id_ambiente, id_frente, nome)`). Bate com o `Alvo` explícito do `CatalogoDeAcoes`
("nunca o item ativo implícito", `component-methods.md` §2.1). **(Recomendado)**

B) O serviço tem um "ambiente ativo" e todas as operações valem para ele.

C) O serviço procura o id do alvo em todos os ambientes abertos.

X) Outro (descreva depois da tag [Answer]: abaixo)

[Answer]: A

---

### Q3 — Como o serviço devolve falha: `Resultado` ou exceção?

`component-methods.md` §3.1 diz que as operações devolvem `Resultado` tipado. Mas `Resultado` é do
`CatalogoDeAcoes`, que é **U5**, e U5 vem **depois** de U4. Hoje o domínio levanta exceções tipadas
(`NomeInvalido`, `OrquestradorDuplicado`…) e as portas também (`ErroDePersistencia`, `ErroDeWiki`).

A) **O serviço devolve o objeto criado ou levanta exceção tipada**; quem traduz para `Resultado` é o
`CatalogoDeAcoes` (U5), num ponto só. O serviço continua testável sem U5, e a TUI nunca vê exceção
crua porque sempre chama através do catálogo. **(Recomendado)**

B) **O serviço devolve `Resultado`**, e o tipo `Resultado` nasce agora em U4 (em `aplicacao/`), para
U5 reaproveitar.

X) Outro (descreva depois da tag [Answer]: abaixo)

[Answer]: A

---

### Q4 — Quantas vezes o serviço tenta de novo quando há `ConflitoDeVersao`?

O critério 5 manda recarregar, reaplicar e salvar de novo. Isso só acontece se **outro processo**
gravou o mesmo ambiente no meio, por exemplo dois FishingRod abertos ao mesmo tempo. Falta dizer
quando o serviço desiste.

A) **Até 3 tentativas**; na terceira falha, levanta `ConflitoDeVersao` para quem chamou, e o estado
em memória fica igual ao do disco (recarregado). **(Recomendado)**: conflito repetido três vezes
seguidas é sinal de algo errado, e repetir sem limite pode travar a tela.

B) Uma tentativa só: reaplica uma vez e, se falhar de novo, desiste.

C) Sem limite: tenta até conseguir.

X) Outro (descreva depois da tag [Answer]: abaixo)

[Answer]: A

---

### Q5 — Em `criar_ambiente`, qual porta é chamada primeiro, e o que acontece se a segunda falhar?

São dois substratos sem transação comum: o banco (U2) e o disco da wiki (U3). Se o segundo falhar,
sobra o primeiro sozinho.

A) **Wiki primeiro, banco depois.** Se a wiki falhar, nada foi salvo no banco e o ambiente
simplesmente não existe (a pasta parcial fica órfã e inofensiva). Se o banco falhar, sobra uma pasta
de wiki órfã, também inofensiva. Em nenhum caso existe ambiente apontando para wiki inexistente. É o
espelho da regra de apagar (critério 6). **(Recomendado)**

B) **Banco primeiro, wiki depois**, como em `services.md` §2. Se a wiki falhar, o serviço apaga o
ambiente do banco (compensação).

C) Banco primeiro, wiki depois, e se a wiki falhar o ambiente fica salvo **sem** wiki; a wiki é
recriada na próxima abertura.

X) Outro (descreva depois da tag [Answer]: abaixo)

[Answer]: A 

---

### Q6 — Como U4 apaga o diretório da wiki, se a `PortaWiki` não tem operação de apagar? *(R-FD4-6)*

Nenhuma das 14 histórias da linha fina pede apagar ambiente; o critério 6 veio do FD de U2
(Q8=B), junto com o critério de U9 "aviso e confirmação antes de apagar".

A) **Acrescentar `apagar(localizador)` à `PortaWiki`**: uma 5ª operação, implementada em
`WikiDeArquivos` com o mesmo confinamento de `resolver_raiz`. Isso reabre U3 (que está fechada) para
um acréscimo pequeno, registrado como emenda. **(Recomendado)**: é a única opção que cumpre o
critério 6 sem furar a fronteira.

B) **Tirar "apagar ambiente" desta iteração**: o critério 6 de U4 e o critério de U9 são adiados
juntos, e `apagar_ambiente` da porta fica sem chamador até lá.

C) Apagar só do banco e deixar o diretório da wiki no disco (órfão), revogando a segunda metade do
critério 6.

X) Outro (descreva depois da tag [Answer]: abaixo)

[Answer]: A

---

### Q7 — Quais operações o `ServicoDeAmbiente` tem nesta iteração?

`component-methods.md` §3.1 lista 6 (`criar_ambiente`, `carregar_ambiente`, `criar_frente`,
`criar_tarefa`, `anotar_memoria`, `concluir_etapa`). Mas outras partes do desenho já aprovado pedem
mais:

- `criar_chat`: `components.md` §3.3 e a emenda de U5 (**Q14=X**, é como o orquestrador delega ao
  bibliotecário);
- `criar_etapa`: US-17, via ferramenta de ambiente do orquestrador (`services.md` §7);
- `reabrir_etapa`: o domínio já permite desmarcar (**Q5a=B** de U1);
- `listar_ambientes` e `apagar_ambiente`: tela inicial (Q10=B) e critério 6.

A) **As 6 originais + `criar_chat` + `criar_etapa` + `reabrir_etapa` + `listar_ambientes` +
`apagar_ambiente`** (este último conforme a Q6). Tudo que U5 e U9 vão precisar chamar já existe
quando elas chegarem. **(Recomendado)**

B) Só as 6 originais; o resto entra quando a unidade que precisa dele chegar (emendando U4 de novo).

C) As 6 originais + `criar_chat` + `criar_etapa` (o que U5 precisa), sem `reabrir_etapa`, sem
listar e sem apagar.

X) Outro (descreva depois da tag [Answer]: abaixo)

[Answer]: X - vamos criar as operacoe mais importantes que eu vejo que sao - criar_ambiente, carregar_ambiente, criar_frente, criar_tarefa, anotar_memoria, criar_chat, lista_ambientes, apagar_ambiente. esses sao os importante pq eu vejo que com ele ja da para usar o ambiente. eu vejo uma separacao assim 

basico que precisa ter , pq é parte da criação:
- criar_ambiente
- carregar_ambiente
- lista_ambientes
- apagar_ambiente

funcionalidades basicas dentro do ambiente para ter o funcionamento:
- criar_frente
- criar_tarefa
- anotar_memoria
- criar_chat

sem esses nao da nem para usar o ambiente. criar chat é essencial para eu ter um chat de IA. criar frentes e tarefas sao parte da ideia do software onde tem frentes e tarefas nas frentes. e anotar memoria é outra parte da ideia principal do software de ter uma forma de armazenar conhecimento.

entao eu vejo que esses sao os mais importantes. outro como criar_etapa e reabrir_etapa nao sao necessarios agora pois eu vejo que seria so um a mais do software, isso podemos deixar para um momento futuro.

---

### Q8 — De onde vem o agente orquestrador que toda tarefa nova recebe? *(R-FD4-4)*

`Frente.criar_tarefa(nome, agente_orquestrador)` exige o agente. A configuração concreta do
orquestrador é montada no composition root (U9).

A) **O serviço recebe o `Agente` orquestrador no construtor**, junto com as portas, e usa esse em
toda tarefa. A assinatura pública fica `criar_tarefa(id_ambiente, id_frente, nome)`. **(Recomendado)**:
nesta iteração existe um orquestrador só, e quem chama (tela ou agente) não deveria precisar
conhecê-lo.

B) O agente vem por parâmetro em cada chamada de `criar_tarefa`.

X) Outro (descreva depois da tag [Answer]: abaixo)

[Answer]: A

---

### Q9 — `criar_chat` aceita qualquer agente, ou só os de uma lista fechada?

A emenda de U5 (**R3**) diz que, quando o **orquestrador** cria um chat, só pode ser com agente de
lista fechada (nesta iteração, só o bibliotecário); senão seria escalonamento de privilégio. Falta
dizer se a lista é verificada no serviço (vale para todo chamador) ou só no catálogo (vale para o
agente).

A) **A lista é verificada no serviço**: `criar_chat` recebe um **nome** de agente e o resolve contra
os agentes que o serviço recebeu no construtor (orquestrador e bibliotecário). Nome desconhecido é
erro. Não existe caminho, nem pela tela, de criar chat com um agente arbitrário. **(Recomendado)**

B) **O serviço aceita qualquer `Agente`**, e a restrição vale só para o chamador agente, no catálogo
(U5).

X) Outro (descreva depois da tag [Answer]: abaixo)

[Answer]: A

---

### Q10 — Duas operações no mesmo ambiente, ao mesmo tempo, dentro do mesmo processo

Com a TUI e os agentes rodando no mesmo laço `async`, o orquestrador pode estar criando uma etapa
enquanto você cria uma frente pelo `/comando`. Cada operação faz "mudar o objeto → `await`
salvar"; duas intercaladas podem salvar um estado que uma delas ainda não terminou de montar.

A) **Uma trava (`asyncio.Lock`) por ambiente** no serviço: operações no mesmo ambiente são
executadas uma de cada vez; ambientes diferentes não esperam um pelo outro. Assim o
`ConflitoDeVersao` fica restrito ao caso de dois processos. **(Recomendado)**

B) Sem trava; o conflito de versão da porta pega o caso.

X) Outro (descreva depois da tag [Answer]: abaixo)

[Answer]: A

---

### Q11 — Dois ambientes podem ter o mesmo nome?

A identidade distingue (o domínio já permite frentes de mesmo nome, RN-04). Mas a tela inicial
lista ambientes **por nome**, e o cabeçalho da wiki é `# Wiki — <nome>`.

A) **Pode.** A identidade é o que distingue; a tela inicial mostra também a data de atualização
(`ResumoAmbiente.atualizado_em`), que basta para diferenciar. **(Recomendado)**: mesma regra das
frentes, e recusar seria a regra antiga de "nome é chave", que o ESC-14 matou.

B) Não pode: `criar_ambiente` recusa nome já usado por outro ambiente local.

X) Outro (descreva depois da tag [Answer]: abaixo)

[Answer]: A

---

### Q12 — O que `carregar_ambiente` faz quando o id não existe?

A porta devolve `None` (RN-P-04: ausência é resultado, não erro).

A) **O serviço também devolve `None`**, e quem chama decide (a tela inicial volta para a lista).
**(Recomendado)**

B) O serviço levanta `AmbienteInexistente`.

X) Outro (descreva depois da tag [Answer]: abaixo)

[Answer]: B - dar uma resposta tipada eu penso que seria melhor para que tenhamos uma resposta mais facil de identificar qual foi o problema. eu penso que se apenas devolvermos None fica implicito a ideia de que nao existe o ambiente, e deixar implicito ao meu ver pode gerar confusao no futuro. eu penso que ter um tipo para tipar o erro nao vai gerar ou pelo menos dificultar a duvida na hora que tiver esse problema. 

---

## 6. O que vai sair deste estágio (prévia, para a resposta ser informada)

- **Regras `RN-A-nn`**, cobrindo: ordem de chamada das portas e falha parcial (Q5, Q6); política de
  conflito (Q4); serialização por ambiente (Q10); de onde vêm os agentes (Q8, Q9).
- **Propriedades `PBT-U4-nn`** (a extensão `property-based-testing` está em modo Full). Candidatas:
  1. **Coerência memória ↔ disco**: para qualquer sequência de operações do serviço, o ambiente em
     memória é igual ao que `carregar_ambiente` devolve de uma porta nova (fecha US-05).
  2. **Conflito não perde mudança**: com outro escritor intercalado, depois da reaplicação as duas
     mudanças estão no disco.
  3. **A wiki nasce igual ao esquema**: para qualquer `EsquemaWiki`, as entidades e as páginas
     listadas pela `PortaWiki` são exatamente os slugs do esquema, e o índice existe mesmo com
     esquema vazio (US-08, US-09).
  4. **Isolamento entre ambientes**: operar em um ambiente nunca altera outro (critério 4).
