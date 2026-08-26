# Requirements Analysis — Perguntas de Esclarecimento

Li todo o material de `produto/` (dores, princípios, glossário, hipóteses, requisitos
funcionais, critérios de sucesso, cenários, questões abertas) e o `docs/aidlc-inputs/vision.md`.
O material é rico e bem fundamentado — a maior parte do **necessidade** já está resolvida ali.
O que falta, e é o propósito destas perguntas, é a **decisão de escopo**: o que entra nesta
iteração especificamente, já que `vision.md` §5 foi deixada em branco de propósito.

**Como responder**: preencha a letra da opção depois de `[Answer]:` em cada pergunta. Se nenhuma
opção servir, escolha a última (Other) e descreva depois do `[Answer]:`. Pode deixar comentários
adicionais em qualquer pergunta — eles ajudam a evitar uma rodada extra de perguntas.

Avise quando terminar.

---

## Parte A — Extensões do processo AI-DLC

Estas três perguntas vêm de extensões do próprio workflow, não do seu projeto. Cada uma liga ou
desliga um conjunto de regras que passam a ser aplicadas (ou não) nas próximas etapas.

### Questão A1 — Extensão de Segurança
O FishingRod hoje é um protótipo local, single-user, sem rede exposta, sem persistência. Ainda
assim, cabe perguntar: as regras de segurança (baseline) devem valer como restrição obrigatória
a partir de agora?

A) Sim — aplicar as regras de segurança como restrição obrigatória (recomendado para aplicações de produção)

B) Não — pular por enquanto (adequado para protótipos e projetos experimentais, como é o estágio atual do FishingRod)

X) Other (descreva depois do [Answer]: abaixo)

[Answer]: A - sim eu penso que temos que pensar sobre segurança. mas como eu penso que o software vai crescer e de inicio vai ter apenas usuarios selecionados por mim para usar, a segurança nao precisa ser a mais refinidada do mundo. portanto eu quero aplicar a segurança, mas de maneira simples pois assim ja temos uma base de segurança feita e que pode ser melhorada depois.

### Questão A2 — Extensão de Resiliência
Aplica boas práticas de design para tolerância a falhas, alta disponibilidade e observabilidade
(derivadas do AWS Well-Architected). Não certifica produção — é um ponto de partida.

A) Sim — aplicar a baseline de resiliência como orientação de design (recomendado se o FishingRod for para produção ou uso crítico em breve)

B) Não — pular por enquanto (adequado enquanto o foco é iteração rápida sobre um protótipo local)

X) Other (descreva depois do [Answer]: abaixo)

[Answer]: B - eu penso que aqui ja é overengineering fazer agora. a segurança eu penso que é mais simples que pensar nessas questoes de extensao e resiliencia, entao penso que nao precisamos. outro motivo é que vai ter usuarios selecionados inicialemnte , vao ter no maximo 20 usuarios.

### Questão A3 — Extensão de Testes Baseados em Propriedade (Property-Based Testing)
O FishingRod tem lógica de domínio não-trivial (composição de status pela cadeia, invariante do
orquestrador único, contrato consome/entrega quando existir).

A) Sim — aplicar PBT como regra obrigatória (recomendado dado que há lógica de negócio, transformação de dados e componentes com estado)

B) Parcial — aplicar só a funções puras e serialização (ex.: `Memoria.formatar`, composição de status)

C) Não — pular por enquanto (adequado se o foco desta iteração for só fechar dívidas de fundação, sem lógica de negócio nova)

X) Other (descreva depois do [Answer]: abaixo)

[Answer]: A - concorco com essa regra de testes pois temos que validar comportamentos e garantir regas.

---

## Parte B — O escopo desta iteração (a decisão central)

`vision.md` §5 foi deixada em branco com o bilhete: *"preencha antes de acionar o workflow."*
Estas perguntas existem para preencher essa lacuna.

### Questão B1 — Qual é o alvo principal desta iteração?
`vision.md` lista dois tipos de candidato: fechar dívida de fundação (SDK, assincronia,
persistência) ou entregar uma fatia de valor de negócio (criar ambiente → frente → tarefa →
conversar com agente real). São coisas relacionadas mas de tamanho e natureza diferentes.

A) **Fundação técnica primeiro** — fechar as dívidas que bloqueiam tudo o mais: ligar o `AgenteClaude` de verdade (assíncrono), abstrair a porta de sessão viva do núcleo, resolver a dependência do SDK dentro do núcleo. Sem necessariamente entregar frente/tarefa/wiki como conceitos de produto ainda.

B) **Fatia vertical mínima de negócio** — um caminho fino mas completo: criar ambiente com meta, criar frentes, criar uma tarefa, conversar com um agente real dentro dela. Aceita persistência zero por enquanto (perde tudo ao fechar o processo).

C) **Caminho completo até CS-01** — reconstituir o ambiente *Nexo Aquisição* inteiro: as seis frentes, os tipos de tarefa do João, as regras, a wiki e os cards em andamento.

D) Other (descreva a combinação ou outro alvo depois do [Answer]: abaixo)

[Answer]: A - eu penso que a nossa primeira itereacao deve ser sobre a funcacao tecnica do software. temos que ter a base bem feita para conseguir caminhar de maneira limpa e clara, sem ficar tropeçando em problemas o tempo todo. essa parte que vejo importante rever e pensar profundamente com o software system lead para pensamos melhor sobre as decisoes do software.

### Questão B2 — Multiusuário está dentro ou fora desta iteração?
`abertas.md` A-07 registra que multiusuário é intenção de produto confirmada, mas o **quando**
segue em aberto — e muda persistência, identidade e concorrência.

A) Fora — esta iteração continua single-user, local, sem autenticação nem concorrência

B) Dentro — já considerar identidade e concorrência de mais de um usuário nesta iteração

X) Other (descreva depois do [Answer]: abaixo)

[Answer]: A - vamos deixar de fora isso, eu penso que esse tipo de funcioalidade é complexa e teria que fazer um monte de coisa. para validarmos a ideia do produto , um ambiente single-user ja é o suficiente e ja agregaria muito valor. vamos focar nisso primeiro.

### Questão B3 — Persistência (salvar e retomar o trabalho) entra nesta iteração?
Hoje todo o estado morre com o processo. É pré-requisito de CS-01 e CS-03, mas é também uma
peça grande (formato de armazenamento, ciclo de vida, migração de estado do domínio).

A) Sim — sem persistência básica esta iteração não prova nada que sobreviva ao fechamento do processo

B) Não — esta iteração aceita perder o estado ao encerrar; persistência fica para uma iteração futura

X) Other (descreva depois do [Answer]: abaixo)

[Answer]: A - eu penso que sim, pois se queremos entregar um ambiente single-user para ja testar se agrega valor, a funcionalidade de persistencia ja deve existir, assim fica uma forma de testabilidade do software real para o usuario, onde o usuario pode usar todos os dias e testar a ferramenta.

### Questão B4 — A Wiki (mesmo mínima) entra nesta iteração?
`principios.md` P-16/P-18 diz que o ambiente é utilizável antes de estar completo, e que a wiki
nasce pequena mas **funcional** desde o dia zero — não é um acessório que se liga depois.

A) Sim — ao menos a wiki inicializada e funcional (mesmo vazia de conteúdo), como manda P-18

B) Não — o campo `wiki_local` continua placeholder por enquanto; a wiki fica para depois

X) Other (descreva depois do [Answer]: abaixo)

[Answer]: A - sim a wiki ja vai vir junta nessa primeira versao de uso para o usuario single-user. pois a wiki é uma das partes fundamentais do software pois agrega a funcionalidade de armazenamento de contexto ao longo prazo, a wiki é uma solucao para um dor do cliente que precisa estar no software na primeira versao realmente para testar e ver. e sobre essa questao de a wiki nascer pequena, aqui eu quero esclarecer um ponto pois esta parecendo que vc entendeu que a wiki teria um formato pronto, na verdade a wiki é uma solucao de abstracao que vai ser implementada no software onde o usuario pode criar wiki personalizavel para o ambiente dele, quando eu expliquei que a wiki iria nascer pequena no ambiente eu quis dizer que , para todo ambiente é obrigatorio ter uma wiki pois o ambiente depende dele para funcionar(pelo menos é assim que eu penso por enquanto) e eu penso o seguitne cenario - se o usuario estivesse ta tela do software e clicasse no botao para criar um novo ambiente, ele teria que configurar a wiki , pelo menos uma wiki pequena e simples para começar o ambiente. perecebe que no caso eu quero dizer que a wiki quando criada em um ambiente novo tem que existir mesmo que seja simples e pequena de começo.

---

## Parte C — Requisitos funcionais: o que entra agora

### Questão C1 — Dos cinco comportamentos que dão o valor diferencial (vision.md §4), quais entram nesta iteração?
São: (1) contrato consome/entrega, (2) travamento/destravamento automático por artefato,
(3) momento humano, (4) promoção de achado a diretriz na wiki, (5) tipo de tarefa configurável
com objetivo e checagem.

A) Nenhum ainda — esta iteração é só fundação técnica, sem esses comportamentos de negócio

B) Só o contrato consome/entrega (verde/vermelho) — é o item mais elogiado pelo usuário e o mais simples de mostrar

C) Contrato consome/entrega + travamento/destravamento por artefato — os dois trabalham juntos e um dá sentido ao outro

D) Todos os cinco

X) Other (descreva a combinação exata depois do [Answer]: abaixo)

[Answer]: A - esses comportamentos vao ser melhor pensados e detalhados mais para a frente. temos que focar na fundacao primeiro e criar o direcionamento correto do software.

### Questão C2 — "Conversar com um agente" — qual é o alvo mínimo nesta iteração?
Hoje `AgenteTeste` devolve string fixa e `AgenteClaude.responder()` devolve `None`.

A) Ligar o `AgenteClaude` de verdade via `claude-agent-sdk`, com a porta de sessão viva (abrir/enviar/fechar) abstraída do núcleo — inclusive tornando a cadeia `enviar()` assíncrona onde necessário

B) Manter o stub por enquanto e priorizar outras partes do sistema nesta iteração

X) Other (descreva depois do [Answer]: abaixo)

[Answer]: A - so quero esclarecer um ponto sobre o claude agent sdk. o objetivo minimo para o mvp é conseguir conversar com um modelo LLM. no caso o claude agent sdk nos permiti fazer isso. eu tinha usado ele pois era uma maneira boa para eu usar pois eu ja assino o claude, e consigo fazer login de autenticacao com a minha conta claude no claude agent sdk. mas perceba, vamos olhar pelo lado certo , o software a ideia é ser adnostico de LLM , ou seja, aceita qualquer modelo, de alguma forma o software vai aceitar diferentes modelos LLM entao o modelo do claude vai ser uma opcao. eu acabei de perceber que temos uma coisa difernete que é a autenticacao, no caso eu estava usando a minha autenticacao do claude para usar a minha assinatura, se o software permitir isso vai ser muito bom pois ja da mais uma opcao para o usuario( incluse o meu cliente teste ele assina o claude , entao ja seria uma opcao para ele, mais um motivo para eu ter usado o claude agent sdk). entao aqui temos que entender melhor as opcoes que temos, eu vejo da seguinte forma -> o software aceita modelos de llm e tipos de autenticacao, no caso teria duas opcoes de usar os modelos llm, via api, ai o usuario configura oq precisa, e via autenticacao de alguma assinatura por exemplo a assinatura do claude, ai dessa forma o usuario pode usar chats de IA dentro dos ambientes. ficou claro ? temos que esclarecer alguma decisao sobre essa ponto ? 

### Questão C3 — Os agentes especiais "bibliotecário" (H-01) e "rod-maker" (H-02) — construir nesta iteração?
Ambos são hipóteses de solução, não decisões fechadas (`hipoteses-de-solucao.md`).

A) Nenhum dos dois ainda

B) Só o rod-maker (criar agentes é operação rotineira segundo o material de descoberta)

C) Só o bibliotecário (escrita verificada na wiki, relevante só se B4 = wiki entra)

D) Os dois

X) Other (descreva depois do [Answer]: abaixo)

[Answer]: D - temos que criar os dois , mesmos que siples inicialmente e sem muitas funcionalidades apenas as principais. eu vejo que temos que ter eles de alguma forma implementado do software para ser um produto de valor , pois o rod-maker vem como uma proposta minha de solucao com o seguinte objetivo - pessoas nao tecnicas nao conseguem pensar e construir agentes de qualidade para uso pessoal e automatizar tarefas, a minha ideia do rod-maker é que ele aplica uma metodologia propria que eu criei que facilita o usuario nao tecnicos a pensar, planejar e construir agentes. e o bibliotecario eu tinha pensado nele como a camada que garanta a qualidade da wiki e fazer processos em cima da wiki para manter limpa e sempre de alta qualidade. 

---

## Parte D — Decisões que afetam todo o resto do workflow

### Questão D1 — Divergência de vocabulário: renomear o código agora?
O código usa `Ambiente → Projeto → Sessao → Chat`; você usa `Ambiente → Frente → Card → Aba`.
"Projeto" foi uma palavra que você descartou explicitamente por ambiguidade.

A) Renomear o código agora para o seu vocabulário (Frente, Card/Tarefa, Aba) — evita acumular mais dívida de tradução em código novo

B) Manter os nomes atuais por enquanto; tradução fica só na interface (se houver)

X) Other (descreva depois do [Answer]: abaixo)

[Answer]: B - vamos manter por enquanto. eu acho precipitado pensar em renomear os nomes agora, pois oque eu penso é que quando começarmos a entender melhor sobre o software que vamos construir, novos nomes vao surgir e novas estruturas portanto a ideia de renomear prematuramente sem entender antes um estrutura nova e maior nao é necessario.

### Questão D2 — Dívida técnica crítica: quanto resolver nesta iteração?
`code-quality-assessment.md` lista quatro dívidas críticas: `AgenteClaude` devolve `None`, SDK
importado dentro do núcleo, `Memoria.anotar()` quebra na primeira escrita de qualquer chave,
persistência inexistente.

A) Todas as críticas listadas

B) Só as que bloqueiam a transação central de conversar com um agente real (as três primeiras; persistência já foi tratada em B3)

C) Nenhuma agora — esta iteração foca em funcionalidade nova, dívida fica para depois

X) Other (descreva depois do [Answer]: abaixo)

[Answer]: A - vamos resolver todas as criticas, penso que nao sao tao complexas para resovler. so tenho um ponto de atencao, temos que fazer por partes para serem corrigidas seguindo a estrutura do software que for definida na aplicacao da metodologia. pensa comigo, se fizermos o ajuste antes de fazer algumas decisoes do software, a correçao pode ficar obsoleta pois nao esta seguindo a nova decisao de software tomada. so tenho esse ponto de atencao.

### Questão D3 — Base de qualidade: dependências declaradas e testes automatizados
Hoje não há `pyproject.toml`/`requirements.txt` nem nenhum teste automatizado (cobertura 0%).

A) Estabelecer as duas coisas nesta iteração: arquivo de dependências + suíte de testes automatizados rodando (mesmo que pequena)

B) Só o arquivo de dependências agora; testes automatizados ficam para depois

C) Nenhuma das duas agora — funcionalidade primeiro

X) Other (descreva depois do [Answer]: abaixo)

[Answer]: A 

---

## Parte E — Validação e segurança

### Questão E1 — Segundo domínio: validar generalidade nesta iteração?
`vision.md` avisa que reconstituir só o ambiente do João prova que o software serve **àquele**
ambiente, não que é genérico. O par natural seria testar contra `cenarios/02` (ambiente de
estudos).

A) Sim — validar as abstrações contra os dois domínios (marketing + estudos) desde já

B) Não — focar só no domínio de marketing por enquanto; generalidade fica para depois

X) Other (descreva depois do [Answer]: abaixo)

[Answer]: A - validar para os dois ambientes vai nos ajudar a pensar e nao perder o foco de fazer um software que consegue generalizar. 

### Questão E2 — Credenciais de MCP externo — relevante nesta iteração?
`abertas.md` registra, sem resposta: *"instalar MCP de terceiro é dar token de conta real a um
pacote de comunidade."* Nenhuma conexão MCP externa foi decidida como parte desta iteração
(ver B1), mas vale confirmar.

A) Não é relevante ainda — nenhuma conexão MCP externa está prevista nesta iteração

B) Sim, precisa ser pensado desde já, mesmo que a conexão em si não entre ainda

X) Other (descreva depois do [Answer]: abaixo)

[Answer]: A - ainda nao é relevante, vamos deixar isso para uma proxima etapa. isso vai ser muito importante depois que ja tivermos o mvp do software ja na mao do usuario e ja validado que agrega valor.

---

## Nota — dúvida de arquitetura registrada para depois

Você levantou uma dúvida sobre se o padrão Chain of Responsibility (`Ambiente → Projeto →
Sessao`) é a decisão certa olhando para o futuro do software. Essa dúvida **não** precisa de
resposta aqui — ela pertence ao estágio de **Application Design**, que roda depois deste, já
com o escopo desta iteração definido. Fica registrada em `aidlc-docs/aidlc-state.md` para não
se perder.
