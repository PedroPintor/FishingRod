# Vision Document — FishingRod

**Versão:** v0 · **Data:** 2026-08-14 · **Autor:** Pedro Pintor
**Tipo:** documento de entrada do AI-DLC (brownfield)
**Fonte:** `produto/` — descoberta com o cliente (12 arquivos de trabalho + reunião de 2026-08-14)

> **Como ler este documento.** Cada afirmação carrega uma marcação de origem e confiança:
>
> - **[confirmado]** — o usuário disse, sobre a ferramenta
> - **[inferido]** — derivado de comportamento observado, ainda não validado
> - **[decisão]** — escolha de produto ou de desenho já tomada
> - **[estado]** — como as coisas estão hoje, sem juízo de valor
> - **[dívida]** — sabidamente errado, tolerado por ora
> - **⚠️ [revisar]** — proposta minha que precisa da sua confirmação
>
> **Não trate `inferido` como fato.** É a regra que a pasta `produto/` estabelece, e ela
> vale aqui.

---

## 1. Resumo executivo

O FishingRod é um **ambiente de trabalho colaborativo com IA**: um lugar onde uma pessoa ou
um time monta a própria estrutura de trabalho — meta, frentes, tarefas, agentes e uma wiki de
contexto — e opera esse trabalho conversando com agentes de IA.

A aposta central é que **o contexto acumulado é o ativo**, não a conversa. Um ambiente que
guarda o que se aprendeu faz cada trabalho futuro começar adiantado; um que não guarda obriga
a reexplicar tudo a cada pedido.

O produto não entrega método. Entrega o lugar e a estrutura onde o usuário monta o método
dele. **[decisão — P-12]**

---

## 2. Contexto de negócio

### 2.1 O problema

O achado que enquadra tudo: o material de descoberta **não descreve** um ambiente de trabalho
com IA — ele **é** um, rodando hoje, montado à mão em Markdown e skills. Ambiente nomeado,
orquestrador, sub-agentes, fábrica de agentes, contexto de longo prazo, separação memória ×
estado, 43 tarefas com dono e critério de pronto, fluxo com portão de qualidade, rituais.

**Consequência para o produto:** a pergunta não é *"o usuário usaria isso?"* — ele já construiu
uma versão manual e paga o custo de mantê-la. A pergunta é **"por que a versão manual dói?"**

**As duas dores ditas pelo usuário, sobre a ferramenta:**

| ID | Dor | Evidência |
|---|---|---|
| **D-10** | *"É muita função. Como eu garanto que faço todas, sendo um só?"* — falta **capacidade de execução paralela com garantia**, não organização. Ele sabe o que fazer: 43 tarefas, 9 papéis, 6 frentes mapeados. | **[confirmado]** |
| **D-11** | O trabalho **para** quando depende de um humano ou de outro trabalho. Hoje a dependência vive na cabeça de alguém; quando o artefato fica pronto, ninguém é avisado. | **[confirmado]** |

**As duas dores inferidas que a reunião confirmou:**

| ID | Dor | Evidência |
|---|---|---|
| **D-04** | O contexto que impede a IA de sair genérica está espalhado e é remontado a cada pedido. *"Sem biblioteca, você reescreve o mesmo pedido todo dia com resultado diferente."* | **[confirmado]** — *"ou seja, eu não repito mais isso"* |
| **D-05** | O que foi resolvido num projeto não chega ao próximo. Reaproveitamento depende de alguém lembrar que o arquivo existe. | **[confirmado]** |

**As dores que continuam inferidas** — nenhuma foi tocada na reunião, e **não devem sustentar
decisão pesada sem validação**: D-01 (manutenção manual concentrada num ponto), D-02 (memória
de longo prazo degrada em silêncio — falhou por ~3 meses no arranjo manual), D-03 (o elo entre
decisão e execução é remontado à mão), D-06 (aprovação humana é o gargalo declarado e não tem
instrumentação), D-07 (criar agente é rotineiro mas artesanal), D-08 (trabalho começa e não
termina — *"oito projetos de inovação registrados e nenhum concluído"*), D-09 (ferramenta não
legível por máquina devolve trabalho manual).

**A dor de segunda persona** — D-12, times que trabalham com IA não compartilham o contexto que
produzem. **[inferido — observado pelo Pedro, não validado em campo]**. É a dor que justifica o
multiusuário, e por isso merece evidência própria antes de virar base de decisão pesada.

### 2.2 Quem usa

| Persona | Perfil | Necessidade dominante |
|---|---|---|
| **João Nishi** (cliente) | **Opera**, em primeira pessoa. Focado em negócio, não em tecnologia. Nove funções, três horas/dia já comprometidas em clientes. | Tocar 5–6 tarefas por dia sem deixar nada cair |
| **Pedro Pintor** | Segundo operador, com necessidade diferente: **montar** × usar | Reconstituir e generalizar o ambiente |

**[confirmado — A-01]** A leitura anterior de que o João seria destinatário das saídas e não
operador estava errada. Ele se descreve operando, no detalhe: *"abro um agente aqui de design
(…) spawno um agente LP, converso com ele, aprovo com o orquestrador, aí eu subo a campanha,
chamo o MCP"*.

**Consequência de desenho:** o produto precisa ser operável por alguém focado em negócio.

### 2.3 O que dirige as decisões

Duas restrições do próprio usuário, que valem como régua do produto:

> **"Não há braço. Essa restrição não é um problema a contornar. É o que define a arquitetura
> inteira."**

> **"Isso escala ou é hora vendida?"**

**Aplicada ao FishingRod:** toda função que exigir manutenção manual recorrente é hora vendida
disfarçada de recurso — e recria exatamente a dor que o produto promete resolver.

### 2.4 Critérios de sucesso

| ID | Critério | Verificável? |
|---|---|---|
| **CS-01** | **Teste de reconstituição** — o FishingRod consegue reconstituir, dentro dele, o ambiente *Nexo Aquisição* que hoje existe em Markdown: seis frentes, tipos de tarefa, regras, wiki e cards em andamento | ✅ o alvo já existe e é conferível |
| **CS-02** | O usuário toca **5–6 tarefas distintas num dia** sem perder o fio de nenhuma; o que estava travado volta a andar sem ele lembrar | ✅ por observação |
| **CS-03** | Depois de N semanas, a wiki é lida e usada **sem que ninguém precise corrigi-la antes de confiar nela** | 🟡 falta definir N e "continua correto" |
| **CS-04** | *"Isso escala ou é hora vendida?"* aplicada a cada função | régua, não teste de aceite |

**A lacuna mais séria, registrada honestamente:** nunca perguntamos ao João como **ele** saberia
que valeu. Todos os critérios acima são do Pedro ou derivados de falas sobre outros assuntos.

**Cuidado sobre CS-01:** reconstituir o ambiente do João prova que o software serve **àquele**
ambiente — não prova generalidade. O par natural é reconstituir também o ambiente de estudos
(`cenarios/02`) e ver se as mesmas peças bastam.

---

## 3. Estado atual

Há **dois** estados atuais, e confundi-los é o principal risco deste documento.

### 3.1 O ambiente do usuário (existe e opera)

Montado à mão em Markdown + skills + MCPs. Funciona, e é a evidência mais forte do produto.
Também é onde as dores foram medidas — inclusive a falha de ~3 meses na ingestão da wiki,
descoberta só numa auditoria.

### 3.2 O código do FishingRod (existe e é embrionário)

**[estado]** ~900 linhas de Python em 6 arquivos:

| Peça | Situação |
|---|---|
| Cadeia `Ambiente → Projeto → Sessão → Chat` | implementada, com delegação de comandos por andar |
| `Memoria` (blackboard `chave → {autor, valor}`) | implementada como dados puros |
| TUI (`tui.py`) + CLI (`cli.py`) | funcionais |
| `interface_ilustrativa.html` | maquete — WIKI, kanban, memória da sessão |
| `AgenteTeste` | **stub** — devolve string fixa |
| `AgenteClaude.responder()` | **[dívida]** devolve `None`; não implementado |
| Persistência | ❌ não existe |
| Testes automatizados | ❌ não existem |
| Multiusuário | ❌ não existe |

**[dívida] `Ambiente/agente.py:6` importa `ClaudeAgentOptions` dentro do núcleo.** É acoplamento
ao provedor num lugar onde ele não deveria estar. Não é decisão — é estágio inicial.

### 3.3 A divergência de vocabulário — o item mais importante desta seção

O código e o usuário falam línguas diferentes:

| Usuário fala | Código tem | Observação |
|---|---|---|
| Ambiente | `Ambiente` | ✅ mesma palavra — mas o usuário carrega **meta** junto |
| **Frente** | `Projeto` | ⚠️ "projeto" foi **descartado** na reunião por ambiguidade |
| **Card / tarefa** | `Sessao` | ⚠️ o card tem `agentes[]` + `memoria[]`, como a Sessão tem `chats[]` + `memoria` |
| Aba | `Chat` | ✅ mesmo conceito, palavra diferente |
| Memória do card | `Memoria` | ✅ mesmo formato `{chave, autor, valor}` |
| Tipo de tarefa, contrato consome/entrega, travado, etapas | — | ❌ **não existem no código** |

**Isto é observação, não decisão.** O que fazer — renomear, mapear ou manter — é trabalho de
planejamento. Mas o AI-DLC precisa saber que a divergência existe, senão vai gerar código com
o vocabulário errado.

---

## 4. O que estamos construindo

O ambiente tem uma estrutura que o usuário preenche:

- **Ambiente** — definido por **um objetivo de negócio com meta**. Sem meta declarada, nada se
  organiza: a meta é o que classifica o que entra e o que não entra. **[acordado]**
- **Frente** — área de atuação; **canal ou capacidade**, não fase. **[acordado]**
- **Tarefa (card)** — unidade de trabalho com objetivo próprio, etapas, agentes conversando e
  memória própria. Grande, com subetapas — não picada. **[acordado]**
- **Etapa** — passo dentro da tarefa, com um **executor**.
- **Aba** — o chat de um agente dentro da tarefa. **[fala]**
- **Wiki** — o repositório de inteligência do ambiente; contexto universal lido por todo agente
  antes de escrever qualquer coisa. Um grafo de `.md` que cresce sem esquema prévio. **[acordado]**

**Os comportamentos que dão o valor** (e que o arranjo manual não tem — ver A-04):

1. **Contrato consome/entrega** — cada tarefa declara o que precisa receber e o que vai produzir;
   verde no que existe, vermelho no que falta. Foi o item mais elogiado pelo usuário.
2. **Travamento e destravamento por artefato** — a tarefa espera o que outra produz e **destrava
   sozinha**. É o que permite trabalho paralelo: *"o card trava; o usuário não"*.
3. **Momento humano** — etapa que só a pessoa faz, e que trava a tarefa sem travar a pessoa.
4. **Promoção de achado a diretriz** — o que o discovery descobre sobe para a wiki e passa a
   valer sozinho em todo card futuro. *"Ou seja, eu não repito mais isso."*
5. **Tipo de tarefa com objetivo e checagem configuráveis** — cada tipo carrega a garantia do que
   precisa existir para fechar. **[confirmado — A-11]**

**O mínimo colaborativo (RF-01 a RF-07)** — todo usuário do ambiente, não só o dono, pode: criar
tarefas, criar agentes, escrever na wiki por caminho verificado, alocar tarefa a outro usuário
ou agente, sinalizar impeditivo, sinalizar tarefa finalizada, acionar chats de IA.
**[confirmado]**

**Governança (RF-08 a RF-10)** — o ambiente tem um **admin** (quem o criou) que pode alterar a
estrutura e **bloquear** funcionalidades. **A direção importa: o padrão é aberto e o admin fecha,
não o contrário.** **[confirmado]**

**Alcance externo (RF-11, RF-12)** — o ambiente configura serviços MCP externos, associados a um
ou mais agentes. **A ferramenta é do agente, não da etapa.** **[confirmado como hipótese — H-05]**

---

## 5. Escopo desta iteração

> ⚠️ **[revisar] Esta seção está incompleta de propósito — a decisão é sua.**
>
> O AI-DLC precisa saber o recorte **desta** iteração, não do produto inteiro. Escrever isto
> errado faz todo o resto ser dimensionado errado.
>
> **Candidato mais forte, derivado do seu próprio critério (CS-01):** o caminho mínimo até
> reconstituir um ambiente — criar ambiente com meta, criar frentes, criar tarefa, conversar
> com um agente real. Isso exigiria fechar a dívida do `AgenteClaude.responder()`, que hoje
> devolve `None`.
>
> **Candidatos do seu kanban atual:** tornar a cadeia `enviar()` assíncrona · dividir `Agente`
> em definição reusável e client vivo · persistir e retomar sessão · abstrair a porta do LLM.
>
> Preencha antes de acionar o workflow.

### 5.1 Dentro do escopo

*(a preencher)*

### 5.2 Explicitamente fora do escopo

*(a preencher — esta metade é tão importante quanto a outra)*

**Candidatos naturais a ficar fora agora**, dado o estado do código: multiusuário e concorrência ·
nuvem e deploy · conexões MCP externas · dashboard (o usuário **rejeitou** visualização de
números como interface — P-09: *"esse painel não é para eu olhar, é só um insumo. Então se é um
insumo, ele não precisa de uma tela"*).

---

## 6. O que NÃO pode mudar

> Esta é a seção que a documentação do AI-DLC chama de crítica: sem ela, o workflow propõe
> rever decisões já fechadas.

### 6.1 Decisões de desenho **[decisão]**

| Item | Por quê |
|---|---|
| A cadeia `Ambiente → Projeto → Sessão → Chat` **por composição** | *"cada andar acrescenta o próprio nome e delega o resto. Não é repasse: é composição"* — está escrito em `ambiente.py:55-56` |
| Cada andar atende só os comandos que são dele; a Sessão é o último e responde "não conheço" | `sessao.py:76-81` |
| `Memoria` é **blackboard**: dados puros e serializáveis, `chave → {autor, valor}`, sem callables | O valor está na comunicação **entre** agentes — por isso carrega autor e é relida a cada chamada. Os verbos vivem fora, fabricados pela Sessão |
| Uma Sessão tem **no máximo um orquestrador** | Invariante ativa em `sessao.py:42-44` |
| O núcleo **não guarda estado de interface** | *"A interface pergunta ao núcleo, compara antes e depois, e redesenha. Trocar a interface não deve tocar em nenhuma regra"* |
| A porta do LLM é abstraída com vocabulário de **sessão viva** (abrir / enviar / fechar) | Um adaptador stateless consegue simular sessão guardando histórico interno; o contrário não funciona |

### 6.2 Restrições de produto **[decisão]**

| Princípio | Regra |
|---|---|
| **P-12** | O software garante a **estrutura**, não o conteúdo nem o método. Item que precise ser igual em todos os ambientes exige justificativa explícita |
| **P-10** | Regra de negócio do usuário ≠ regra do software. O ambiente **não** embute a hierarquia de frentes do João |
| **P-13** | Convidar é opcional. Trabalho solo **não é modo degradado** — é o caso de um participante só |
| **P-14** | Nada entra na wiki por caminho não verificado, e há **revisão humana** antes de virar contexto oficial |
| **P-16** | O ambiente é utilizável **antes** de estar completo |
| **P-17** | Duas entradas: método trazido pronto **e** método descoberto no uso. Nenhuma das duas pode ser o único caminho |
| **P-19** | Estrutura se importa; conteúdo da wiki e agentes **se vivem** — não podem vir prontos |
| **P-20** | Colaborativo por padrão; o admin **restringe**. O padrão é aberto |
| **P-07** | Verbo que toca o mundo real pede confirmação; rascunho não |

### 6.3 Proibições, com motivo e alternativa

| Proibido | Motivo | Use no lugar |
|---|---|---|
| Acoplar tipos do `claude_agent_sdk` ao núcleo (`Ambiente`, `Projeto`, `Sessao`, `Chat`) | Quebra o agnosticismo a provedor de LLM | Tipos do SDK confinados ao adaptador |
| Tratar `Chat.mensagens` como fonte da verdade do histórico | Com sessão viva, o loop e o histórico ficam do lado do client | `Chat.mensagens` é cópia para a UI |
| Embutir os tipos de tarefa do cliente (discovery/execução/análise) como estrutura do software | São **configuração do ambiente dele**, não do produto — e não sobreviveram ao teste do segundo domínio | Tipo de tarefa configurável, com objetivo e checagem próprios |
| Construir dashboard de números como interface | O usuário rejeitou explicitamente (P-09) | Documento consumido por agente |

### 6.4 O que **não** é restrição — correção importante

**O FishingRod deve ser agnóstico a modelos de IA.** O `claude-agent-sdk` é o **primeiro
adaptador**, escolhido para consumir a assinatura Claude já paga — é **[estado]**, uma escolha
circunstancial de partida, **não** uma decisão de arquitetura.

O que não pode mudar é a **porta de sessão viva** (6.1), não o SDK que está atrás dela.

---

## 7. Riscos e perguntas em aberto

### 7.1 Riscos

| # | Risco | Estado |
|---|---|---|
| **A-09** | **A primeira impressão do usuário foi ruim.** *"No começo eu tava enzado… eu achei uma m****."* E, mesmo convencido: *"não parece muito usual isso aqui."* O valor só aparece depois de pensar e clicar — um usuário que não é sócio da ideia não dá esse tempo | 🔴 sem resposta |
| **P-19** | **Todo ambiente novo começa com a prateleira montada e vazia.** As duas camadas que dão valor de longo prazo (conteúdo da wiki e agentes) são exatamente as que não podem vir prontas. O dia um precisa valer por si | 🔴 estrutural |
| **A-03** | **Generalidade não provada.** Toda a estrutura discutida é de marketing. O teste com um segundo domínio foi **de mesa** — o ambiente de estudos é hipotético, ninguém o operou. Resultado: a maioria das abstrações generaliza, mas as **três naturezas** e parte dos 14 verbos **não** | 🟡 testada, não resolvida |
| **A-06** | Não sabemos **quantas horas por semana** a manutenção manual consome. É o número que transforma D-01 de argumento em caso | 🔴 aberto |
| — | **Premissa contestada:** "um operador só" caiu (A-07). Multiusuário muda persistência, identidade, concorrência e onde o processo roda | 🔴 muda o desenho |

### 7.2 Perguntas em aberto

| # | Pergunta |
|---|---|
| **A-08** | Quem cria as frentes iniciais, e com base em quê? Nos dois cenários o usuário "já pensou" nelas — ninguém mostrou esse pensar acontecendo |
| **A-08** | Quais são as **etapas mínimas** de criação de um ambiente? Sabemos que a wiki é uma; não sabemos as outras nem quanto custam antes do primeiro trabalho útil |
| **A-10** | Até onde vai o configurável? Frentes claramente sim — mas e os tipos de tarefa? E a wiki como destino obrigatório do discovery? Cada item fixo é uma opinião imposta a todo usuário futuro |
| **A-14** | Alocar uma etapa a outro usuário é **designação ou pedido**? Muda o que acontece quando a pessoa não faz — é a diferença entre coordenação e comando |
| **A-15** | Quando o usuário sinaliza "finalizada" e a checagem do tipo não passou: o software **impede, avisa, ou registra a exceção com motivo**? Há precedente para a terceira via |
| **A-07** | Multiusuário é da v1 ou visão de futuro? O *o quê* está decidido; o *quando* é planejamento |
| — | Credenciais: *"instalar MCP de terceiro é dar token de conta real a um pacote de comunidade"*. Confiança e credencial não foram discutidas para o FishingRod |
| — | Como o usuário saberia que valeu? (a lacuna de CS) |

### 7.3 Hipóteses ainda não decididas

**Nada abaixo está escolhido.** Registrado para que o workflow não trate como decisão:

| # | Hipótese | Alternativa conhecida |
|---|---|---|
| **H-01** | Agente **bibliotecário** como único que escreve na wiki | Tools de wiki com garantia de formato embutida, usáveis por qualquer agente |
| **H-02** | Agente **rod-maker** para construir agentes | Tools de construção de agente |
| **H-03** | Etapas nascem com a tarefa e são editáveis | Etapas como entidades próprias, reaproveitáveis entre tarefas |
| **H-04** | Executor é sempre **agente ou usuário** | 🟢 consistente, falta validar em uso |
| **H-05** | MCP configurável associado a agentes | — |

---

## 8. Rastreabilidade

Toda afirmação deste documento vem de `produto/`, que por sua vez aponta para `produto/bruto/`
— o registro do que o usuário disse, com a palavra dele. `bruto/` nunca é editado.

| Seção | Origem |
|---|---|
| 2.1 Problema | `produto/dores.md` |
| 2.2 Personas | `produto/abertas.md` A-01 |
| 2.4 Sucesso | `produto/criterios-de-sucesso.md` |
| 3.2, 3.3 Código | leitura direta do repositório + `produto/glossario.md` |
| 4 Construção | `produto/glossario.md`, `produto/requisitos/funcionais.md`, `produto/cenarios/` |
| 6.2 Restrições | `produto/principios.md` |
| 7 Riscos | `produto/abertas.md`, `produto/hipoteses-de-solucao.md` |
