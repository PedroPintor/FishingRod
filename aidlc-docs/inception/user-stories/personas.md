# Personas — FishingRod (Iteração 1)

**Versão:** v1 · **Data:** 2026-08-18 · **Estágio:** INCEPTION — User Stories
**Origem:** `vision.md` §2.2, `produto/cenarios/01`, `produto/cenarios/02`, `produto/cenarios/03`,
`produto/glossario.md`, respostas do usuário em `story-generation-plan.md` (Pergunta 1) e
`story-generation-plan-clarification-questions.md` (Questão 1)

> **Por que duas personas nesta iteração de um usuário só.** `requirements.md` fechou o escopo
> desta iteração como um usuário por ambiente (ESC-09, FOR-01, FOR-02 — sem multiusuário nem
> governança). As duas personas abaixo **não** representam multiusuário dentro de um mesmo
> ambiente — representam **dois ambientes diferentes, cada um com um usuário só**, usados para
> testar se a estrutura do software generaliza (`E1=A`, CS-01, `produto/cenarios/02`). O alvo
> principal de validação desta iteração é o João operando sozinho; o Pedro reforça a
> generalidade. Comportamentos que só fazem sentido com mais de uma pessoa no mesmo ambiente
> ficam registrados como aspiração fora de escopo — ver seção H de `stories.md`.

---

## Persona 1 — João Nishi

| Campo | Descrição |
|---|---|
| **Papel** | Dono do ambiente **Nexo Aquisição** — agência/operação de aquisição de clientes |
| **Perfil** | Foco em negócio, não em tecnologia. Cobre nove funções, com três horas por dia já comprometidas em atendimento a clientes |
| **Necessidade dominante** | Tocar 5–6 tarefas distintas por dia sem deixar nada cair, sendo uma pessoa só |
| **Dores associadas** | D-10 (muita função para uma pessoa só), D-11 (trabalho para quando depende de humano ou de outro trabalho, e ninguém é avisado quando destrava) |
| **Meta do ambiente dele** | Gerar MRR recorrente |
| **Frentes do ambiente dele** | `oferta e mensagem` · `instrumentação` · `conteúdo` · `mídia paga` · `outbound` · `comercial e ticket` |
| **Citação que define o uso** | *"eu posso fazer tudo nesses chats (…) abro um agente aqui de design (…) spawno um agente LP, converso com ele, pá pá, aprovo com o orquestrador, aí eu subo a campanha, chamo o MCP"* |
| **Papel nesta iteração** | **Alvo principal de validação.** Ele opera **sozinho** — se o software funcionar para ele nesse modo, a iteração está validada. As partes do trabalho real dele que dependem de outra pessoa (D-12, time da Nexus) ficam **fora do escopo desta iteração** e aparecem só como histórias de rastreabilidade (ver `stories.md`, seção H) |
| **Critério de sucesso ligado a ele** | CS-01 — reconstituir dentro do FishingRod o ambiente Nexo Aquisição que hoje existe em Markdown |

---

## Persona 2 — Pedro Pintor

| Campo | Descrição |
|---|---|
| **Papel** | Dono do ambiente **Meus estudos do semestre** — uso pessoal, para estudar matérias da faculdade |
| **Perfil** | É também quem monta o FishingRod — mas nesta persona ele é **usuário final**, testando o software como alguém que ainda não tem o método pronto |
| **Necessidade dominante** | Aprender o máximo possível e sair com um mapa mental de tudo o que estudou no semestre, sem método definido de antemão |
| **Meta do ambiente dele** | Aprender o máximo possível e sair com um mapa mental de tudo o que aprendeu |
| **Frentes do ambiente dele** | `estudo do material de sala` · `pesquisa de aprofundamento` · `exercícios` · `planejamento de estudos` |
| **Citação que define o uso** | *"estou fazendo uma tarefa de estudo, eu crio uma tarefa de estudo e não sei muito bem ainda que sub etapas eu vou seguir. Aí quando eu começo essa tarefa eu inicio um chat de IA e começo a falar com o orquestrador (…) conversando com o orquestrador eu consigo montar um plano de etapas legal que gostei"* |
| **Papel nesta iteração** | **Segundo domínio de validação.** Ele também opera sozinho, desde o primeiro dia — ninguém é convidado (`cenarios/02`). Serve para provar que a estrutura pensada para o ambiente do João não é, sem querer, específica de marketing — é o par que `vision.md` §2.4 identifica como faltante para CS-01 |
| **Diferença chave frente ao João** | Chega em branco, sem método — descobre as etapas de uma tarefa **conversando** com o orquestrador, em vez de trazê-las prontas (`cenarios/03`, "Duas entradas: partida em branco × partida carregada") |

---

## Agentes que nascem do trabalho de cada persona (contexto, não histórias)

Referência para redigir critérios de aceite realistas — nenhum destes é requisito desta
iteração além dos dois agentes especiais (rod-maker, bibliotecário) já definidos em
`requirements.md`:

| No ambiente do João | No ambiente do Pedro |
|---|---|
| Agente de design, agente de LP, arquiteto-meta (lê Meta Ads) | Leitor de material, questionador/filósofo, revisor de progresso |

---

## Como usar estas personas em `stories.md`

- Toda história em domínio `colaborativo-solo`, `sessao-llm`, `persistencia`, `wiki` ou
  `agentes-especiais` é escrita da perspectiva de **uma das duas personas operando sozinha** —
  o comportamento é o mesmo para as duas, o que muda é o domínio de exemplo.
- Histórias de domínio `wiki` trazem **sempre** os dois exemplos (marketing e estudos), porque
  ESC-12 exige validar a generalidade da wiki nos dois domínios.
- Histórias de domínio `colaborativo-time` (seção H) são atribuídas só ao João, e estão
  marcadas **fora do escopo desta iteração**.
