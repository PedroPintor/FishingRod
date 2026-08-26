# User Stories — Perguntas de Esclarecimento (Plano)

Analisei as 6 respostas em `story-generation-plan.md`. Quatro (Pergunta 3 a 6) estão claras e
decididas — vou seguir exatamente como escrito. Duas levantam pontos que preciso fechar antes de
gerar as histórias, porque mudam a estrutura e o conteúdo de `stories.md`/`personas.md`.

**Como responder**: mesmo formato de sempre — letra depois do `[Answer]:`, ou "Other" com
descrição.

---

## Questão 1 — João Nishi, multiusuário e o escopo desta iteração

Na Pergunta 1 você decidiu ter **as duas personas com histórias próprias**: João Nishi (uso em
equipe, seu cliente) e Pedro Pintor (uso próprio, para estudar). Mas `requirements.md` já fechou
o escopo desta iteração como **um usuário só** — ESC-09 ("mínimo colaborativo para um usuário,
sem multiusuário") e FOR-01/FOR-02 (multiusuário e governança explicitamente fora).

Uso em equipe, por definição, envolve mais de uma pessoa no mesmo ambiente (alocar tarefa a
outro usuário, ver o que o outro fez, etc.) — o que colide com ESC-09/FOR-01. Preciso saber como
tratar isso ao escrever as histórias do João:

A) **Histórias do João descrevem o uso em equipe completo, mas marcadas como fora do escopo
desta iteração.** Ficam documentadas em `stories.md`/`personas.md` para orientar Application
Design e iterações futuras, sem prometer que são construídas agora. Mantém o escopo de
`requirements.md` intacto.

B) **Histórias do João são reduzidas ao que um usuário só consegue fazer nesta iteração** — a
parte do fluxo dele que não depende de outra pessoa (ex.: ele opera sozinho, sem alocar tarefa
para colega). O que só faz sentido em equipe (alocação a outro usuário, visibilidade cruzada)
fica fora de `stories.md` por completo, mesmo como aspiração.

C) **Isso é um pedido para reabrir a decisão de escopo** — você quer trazer multiusuário/
governança de volta para dentro do escopo desta iteração, revisando ESC-09/FOR-01/FOR-02 em
`requirements.md`.

X) Other (descreva depois do [Answer]: abaixo)

[Answer]: A -  o objetivo dessa iteracao eu ainda penso que a decisao é para as
  hitorias do joao, porem eu falei para criar as historias das duas personas
  para termos mais contexto na hora da implementacao, como o software eu
  penso que ele tem que ser um ambiente de trbalho colaborativo com IA
  generico, ou seja, se adpata da maneria que o usaurio quer usar, se
  escrevermos as historias para as duas personas, vamos ter uma base de
  entendimento melhor na questao de generalizar o software. mas ainda
  continua pensando que a iteracao esse momento é para o joao, pois ele é o
  meu usuario teste principal, se funcionar para o joao usar sozinho, o software vai estar validado.

---

## Questão 2 — Mecânica de combinar as 3 abordagens de organização das histórias

Na Pergunta 2 você escolheu combinar as três abordagens que propus (Domain-Based, Feature-Based,
User Journey-Based) em vez de escolher uma, para ter o entendimento mais completo possível dado
que o uso do software ainda está nebuloso. Antes de gerar `stories.md`, preciso saber o mecanismo
exato — isso muda bastante o tamanho e a forma do arquivo:

A) **Uma lista única de histórias atômicas**, cada uma com três marcações (domínio, feature/RF
relacionado, passo da jornada). Nenhum conteúdo duplicado — as três abordagens viram três formas
de navegar o mesmo conjunto de histórias (por exemplo, três índices no topo do arquivo, cada um
apontando para as mesmas histórias).

B) **`stories.md` com três seções completas**, cada uma cobrindo o mesmo comportamento do
sistema, mas reorganizada por lente diferente (uma vez agrupado por domínio, uma vez pela
jornada de uso, uma vez por feature) — mais redundante, mas cada seção fica completa e legível
sozinha, sem precisar ir e voltar.

C) **Uma abordagem primária estrutura o documento** (escolha entre domínio/feature/jornada como
eixo principal), e as outras duas aparecem só como metadado em cada história (ex.: uma linha
"Domínio: X · Passo da jornada: Y"), não como estrutura própria do documento.

X) Other (descreva depois do [Answer]: abaixo)

[Answer]: C - uma abordagem primária com as outras duas como metadado/índice, não uma lista com triplicação de conteúdo.

Especificamente:

- Feature-Based como estrutura primária: cada história de usuário é escrita uma única vez, com seu corpo completo (título, descrição, critérios de aceitação), agrupada por funcionalidade concreta.
- Domain-Based e Journey-Based entram como índices de referência cruzada no topo do documento — tabelas leves que listam nome da história + link/ID, agrupadas por domínio e por jornada, sem repetir o texto da história.
- Cada história pode carregar metadados leves (domain:, journey:) para alimentar esses índices automaticamente.

Motivo: quero evitar que a mesma história seja reescrita três vezes (isso triplicaria o tamanho do stories.md e criaria risco de divergência — alguém atualiza a versão "por feature" e esquece de atualizar a versão "por jornada"). Feature-based é a granularidade que efetivamente vamos implementar e testar, então ela é a fonte única de verdade. Domain e Journey servem para navegação e para identificar lacunas (ex: uma jornada sem história cobrindo um passo), não para duplicar conteúdo. 