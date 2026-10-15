# Functional Design Plan — U3 `wiki`

**Fase:** CONSTRUCTION · **Unidade:** `U3 wiki` · **Profundidade:** comprehensive
**Data:** 2026-09-01
**Base:** `unit-of-work.md` §3 (U3), `components.md` §2.8/§3.7/§4.3/§5.3, `component-methods.md`
§1.8/§3.4/§4.3/§5/§6.2, `requirements.md` (ESC-17, ESC-19, ESC-20, RF-F13/14/15, RNF-09/10/11/12/14),
`stories.md` US-08 e US-09, e a **Parte B.3** do FD de U1 (que adiou três decisões para cá).
**Estado da base de código:** U0, U1 e U2 implementadas — 84 testes passando, `dependencies = []`.

---

## 1. Contexto da unidade

| Campo | Conteúdo |
|---|---|
| **Componentes** | `PortaWiki` (`aplicacao/portas/`), `AdaptadorWikiFilesystem` (`adaptadores/`), `EsquemaWiki` (`aplicacao/`) |
| **Histórias** | US-08 (ambiente novo nasce com wiki, mesmo vazia), US-09 (a estrutura é do dono, não do produto) |
| **Dívidas** | Nenhuma |
| **Depende de** | U0, U1 (`RaizWiki`) |
| **Estágios** | FD **EXECUTE** (aqui) · NFR-R **EXECUTE** · NFR-D **EXECUTE** · INFRA **SKIP** · CG **EXECUTE** |
| **Portões** | 4 |

**Contrato herdado** (`component-methods.md` §4.3), que este estágio detalha mas não reabre:

```
class PortaWiki(Protocol):
    async def listar(self, localizador: str, caminho: str) -> list[str]: ...
    async def ler(self, localizador: str, caminho_pagina: str) -> ConteudoPagina: ...
    async def escrever_proposta(self, localizador: str, proposta: PropostaWiki) -> None: ...
    async def renderizar_index(self, localizador: str) -> None: ...
    # [emenda Q13=A] `buscar` removida desta iteração
```

**Decisões já fechadas** que este estágio não reabre:

- **ESC-17**: entidade = pasta, propriedade = arquivo markdown dentro dela, **dois níveis, travados**.
  O arquivo é a fonte da verdade; `index.md` é sumário e porta de entrada de leitura.
- **ESC-19**: esquema plugável **como semente** — materializa na criação e depois a wiki evolui livre.
- **ESC-20**: acesso exclusivamente pelas ferramentas do bibliotecário (as ferramentas são de U8;
  a porta é daqui).
- **Q13=A**: `buscar` sai desta iteração. **O índice é o único caminho até o conteúdo.**
- **CQ1=A**: o portão do índice é só determinístico — nenhum LLM no laço de renderização.
- **Pergunta 15D**: `descricao` é obrigatória em `propor_propriedade`; o índice é renderizado por
  código a partir de estrutura de pastas + frontmatter, nunca por agente.

---

## 2. Fronteira desta unidade

**Faz**: o formato físico da wiki no disco (frontmatter, nomes, links), a semântica de cada operação
da porta, o confinamento de caminho, a renderização do `index.md`, e o `EsquemaWiki` com as maquetes
prontas.

**Não faz**:

- As **ferramentas** `propor_entidade` / `propor_propriedade` e o `ServicoBibliotecario` com suas
  propostas pendentes — são **U8**. Esta unidade oferece `escrever_proposta`, que U8 chama depois de
  o usuário aprovar.
- **Quem chama** `renderizar_index` na criação do ambiente — é `ServicoDeAmbiente`, **U4**.
- O prompt do bibliotecário — **U8**.
- Qualquer tela — **U9**.

---

## 3. O que a Parte B.3 do FD de U1 deixou marcado para chegar aqui

Três coisas foram declaradas naquele portão como "escopo de U3, a resolver no Functional Design
daquela unidade". Chegaram:

1. **A invariante "ao menos uma entidade" está revogada.** Criar ambiente materializa a raiz e
   renderiza o `index.md` **mesmo sem entidade alguma**. Índice vazio é estado válido, não erro.
2. **O custo declarado**: um `index.md` vazio precisa ser *legível*, não ambíguo — senão o agente
   que começa a leitura por ele não distingue "wiki vazia" de "wiki quebrada". Vira critério de
   aceite desta unidade → **Q9**.
3. **As maquetes prontas**: quantas, de quais domínios, com que conteúdo → **Q8**.

---

## 4. Passos do Functional Design

- [x] **Step 1** — Ler a definição da unidade (`unit-of-work.md` §3 U3), as histórias US-08/US-09 e
      os artefatos de Application Design que descrevem os três componentes
- [x] **Step 2** — Criar este plano com passos em checkbox
- [x] **Step 3** — Gerar as perguntas de contexto com tag `[Answer]:` (§6) e declarar as
      reconciliações (§5)
- [x] **Step 4** — Guardar o plano em `construction/plans/wiki-functional-design-plan.md`
- [x] **Step 5** — 12 respostas analisadas. **7 fecharam limpas** (Q3=A, Q4=A, Q5=A, Q7=A,
      Q9=A reformulada, Q11=A, Q12=B). **5 abriram ambiguidade** e **4 revogam artefato aprovado**:
      `wiki-fd-clarificacao.md` criado com C1..C5, D1/D2 e E1..E4.
      **Parado, aguardando as respostas de C1 a C5.** C1 é a que trava — sem ela não há como
      renderizar o índice que a Q12=B pediu
- [x] **Step 6a** — Gerar `construction/wiki/functional-design/domain-entities.md`
      (`ConteudoPagina`, `PropostaWiki`, `EsquemaWiki`, `EntidadeSemente`, `PropriedadeSemente`,
      `ItemDeIndice`, e o layout físico no disco)
- [x] **Step 6b** — Gerar `construction/wiki/functional-design/business-rules.md` — **37 regras
      `RN-W-01..37`**
      (regras `RN-W-nn`: confinamento, dois níveis, nomes, links, índice como projeção, colisão)
- [x] **Step 6c** — Gerar `construction/wiki/functional-design/business-logic-model.md`
      (semântica de cada operação da porta, com pré/pós-condição, erros nomeados e o algoritmo de
      renderização do índice)
- [x] **Step 7** — **7 propriedades `PBT-U3-01..07`** nomeadas em `business-logic-model.md` §7.
      `PBT-U3-01` **é** o `PBT-03` de Application Design (confinamento)
- [x] **Step 8** — **4 artefatos emendados**, texto riscado e nada apagado: `services.md` §2 passo 4
      (passo revogado por inteiro) · `components.md` §3.7 (maquetes adiadas, `nome`/`descricao`
      revogados, invariante revogada) e §5.3 (reconhecer página criada fora do app revogado) ·
      `component-methods.md` §3.4 (`carregar_toml` adiada, `vazio()` nova) e §4.3 (`renderizar_index`
      ganha `nome`) · `unit-of-work.md` U3 critérios 1 e 3, e U4 critério 1.
      Conformidade das extensões no portão
- [x] **Step 9** — Portão 1/4 apresentado

**9/9 passos concluídos em 2026-09-23.** 12 perguntas + 6 clarificações em 2 rodadas, 3 artefatos
gerados, 37 regras, 7 propriedades, 4 artefatos aprovados emendados.

---

## 5. Reconciliações declaradas — diga se discorda

Coisas que decidi sozinho por já estarem determinadas por decisão anterior. Registro para você poder
objetar; não são perguntas.

### R-FD3-1 — Onde `dados:` resolve, e quem sabe disso

A **Q1 de U2** foi respondida **A**: os dados moram na pasta de dados do usuário, e
`adaptadores/persistencia/localizacao.py` já implementa `pasta_de_dados()`. Então
`dados:wikis/<id_ambiente>` resolve para `pasta_de_dados() / "wikis" / <id_ambiente>`.

**Quem chama `pasta_de_dados()` é o composition root (U9)**, que passa a raiz pronta ao construtor do
`AdaptadorWikiFilesystem` — como `component-methods.md` §6.2 já dizia. **Nenhum adaptador importa
outro adaptador**: o de wiki não vai importar o de persistência para reaproveitar a função.

### R-FD3-2 — A invariante revogada vive em **três** artefatos, não dois

A Parte B.3 listou `services.md` §2 e `unit-of-work.md` U4 critério 1. Falta um: `components.md` §3.7
diz que `EsquemaWiki` deve *"validar a invariante de criação: ao menos uma entidade"*. Está revogado
pela mesma decisão. Os três serão emendados no Step 8, com texto riscado.

### R-FD3-3 — Confinamento são **três** verificações, não uma

`PBT-03` / RNF-10 / SECURITY-05 não se satisfazem só sanitizando o nome. O que vai valer: sanitizar o
nome → montar o caminho → `Path.resolve()` (que **resolve symlink**) → verificar que o resultado está
sob a raiz resolvida. **É a verificação depois do `resolve()` que fecha o buraco do symlink** —
sanitizar sozinho não o alcança, porque o nome pode ser inocente e o symlink já existir no disco.

### R-FD3-4 — Formato físico

`.md`, **UTF-8**, quebra de linha **LF** escrita explicitamente (não a do sistema — senão o mesmo
conteúdo gera arquivo diferente no Windows e no Linux, e o teste de round-trip fica dependente da
máquina). Nomes de pasta e de arquivo em minúsculas.

### R-FD3-5 — `listar` devolve nomes, e só

`PortaWiki.listar` devolve a lista de nomes (entidades quando `caminho` é vazio, propriedades quando
é o nome de uma entidade). Descrição não vem por aí — vem do índice. Duas fontes para a mesma
informação seriam duas coisas para manter sincronizadas.

### R-FD3-6 — Esta unidade não tem busca

Com Q13=A, o único caminho até o conteúdo é `index.md` → `ler`. Isso muda o peso do índice: ele não é
conveniência de navegação, é **o mecanismo de recuperação**. Toda decisão sobre o índice nas
perguntas abaixo deve ser lida com esse peso.

### R-FD3-7 — Erros nomeados, como em U2

A porta levanta exceções próprias (`ErroDeWiki` e subclasses), nunca `OSError` cru. É a mesma regra
que U2 aprendeu na marra durante a geração de código (`AmbienteInexistente`, `RN-P-27`): driver não
atravessa porta. Aqui já entra desenhado.

---

## 6. Perguntas

Responda escrevendo depois de `[Answer]:`. Onde eu tiver recomendação, ela está marcada — pode
recusá-la sem justificar.

---

### Q1 — O que é o frontmatter, em que formato

O índice é renderizado a partir de estrutura de pastas **+ frontmatter** (Pergunta 15D). Então cada
página de propriedade carrega metadados no topo. O formato importa porque `dependencies = []` é regra
desta iteração e **não existe parser de YAML na stdlib**.

A) **TOML entre `+++`** (estilo Hugo). `tomllib` é stdlib, parser de verdade, erro claro.
   *Custo*: o Obsidian não lê esse bloco — se você abrir a wiki no Obsidian, ele mostra o `+++` como
   texto.
B) **Subconjunto de YAML entre `---`**, escrito e lido por ~30 linhas nossas (só `chave: valor` de
   string e lista simples). *Ganho*: é o que o Obsidian entende, e ESC-17 já escolheu links no estilo
   Obsidian — a wiki fica abrível numa ferramenta que você já conhece.
   *Custo*: parser escrito à mão precisa ser **tolerante**, porque o critério 3 exige que página
   criada fora do app apareça no índice (ver Q2), e uma página criada no Obsidian pode ter YAML que o
   nosso parser não entende.
C) **Nenhum frontmatter**: primeira linha do arquivo é o título, segunda é a descrição, por
   convenção. *Ganho*: nada para parsear. *Custo*: convenção sem estrutura quebra em silêncio, e o
   critério 2 ("nenhuma propriedade com descrição vazia") vira adivinhação.

**Minha recomendação: B.** O ganho de a wiki ser abrível no Obsidian é real — é o produto sendo
honesto sobre "o arquivo é a fonte da verdade" — e o custo do parser tolerante nós vamos pagar de
qualquer jeito por causa de Q2.

[Answer]: B - quero fazer uma observacao que vai simplificar a questao de como sera montado o indice. vamos usar a frontmatter entre '---' para localizar as informacoes, e a informacoe que precisamos do frontmatter para montar o indice é apenas a descricao, ai o indice ficaria mais ou menos no formato assim -> [<nome do arquivo>]: (descricao do frontmatter)

---

### Q2 — Página criada fora do app, sem descrição: o índice faz o quê

Dois critérios de pronto da unidade se encostam aqui:

- critério 2: *"nenhuma propriedade com `descricao` vazia no frontmatter"*
- critério 3: *"uma página criada fora do app aparece no índice após regeneração"*

Se eu criar `clientes/anotacao-rapida.md` na mão, sem frontmatter, os dois não podem valer ao mesmo
tempo. O que ganha?

A) **Aparece no índice, marcada** — algo como `- anotacao-rapida — *(sem descrição)*`.
   *Ganho*: nunca some conteúdo, e o defeito fica visível a você e ao agente.
   *Custo*: o critério 2 passa a valer só para o que **o app escreve**, não para o disco inteiro.
B) **Não aparece no índice.** *Custo*: com `buscar` removida, invisível no índice = **inalcançável**.
   Você criaria um arquivo e ele simplesmente não existiria para o sistema.
C) **A renderização falha** e avisa. *Custo*: um arquivo mal formado quebra a wiki inteira.
D) **Descrição inferida** da primeira linha não vazia do conteúdo. *Ganho*: índice sempre útil.
   *Custo*: descrição inventada parece descrição escrita — e a descrição é o mecanismo de recuperação
   (R-FD3-6), então uma ruim é pior do que uma ausente e marcada.

**Minha recomendação: A.** Perder conteúdo é o pior desfecho dos quatro, e a marca `(sem descrição)` é
exatamente o tipo de defeito que o humano conserta quando vê.

[Answer]: nenhuma alternativa - acho que o criteiro 3 nos demovemos descartar. a questao é o seguinte, normalmente nao pode editar ou criar os arquivos da wiki manualmente fora do app. se o usuario fizer isso, eu penso que vemos apenas ignorar. eu estou falando para termos esse comportamento, pois a wiki em algum momento vai ser um tipo de armazenamento que o usuario nao vai mais conseguir mexer fora do app. entao ja vamos tirar o criterio 3 que nao vai ser aplicado mais e nao vai fazer sentido manter esse criterio.

---

### Q3 — Qual grafo manda no índice: as pastas ou os links `[[...]]`

Está aberto desde a revisão do plano de execução em 2026-08-19, com estas palavras: *"qual grafo manda
na recuperação: a hierarquia de pastas ou os links `[[...]]`, quando discordarem"*.

A) **As pastas mandam, e só.** O índice é a projeção literal do disco: entidades, e sob cada uma suas
   propriedades com descrição. Links são navegação *dentro* do conteúdo e não entram no índice.
   *Ganho*: o índice é reprodutível de olhos fechados, e o critério 1 vira uma verificação trivial.
   *Custo*: a relação "dr-marcelo é cliente do ICP tal" só existe dentro do texto.
B) **Pastas mandam, mais uma seção de links quebrados** no fim do índice. *Ganho*: (A) mais um defeito
   visível — link para página que não existe é a forma mais comum de wiki apodrecer.
   *Custo*: uma varredura de todo o conteúdo a cada renderização.
C) **Pastas mandam, mais backlinks por página** ("quem aponta para esta página"). *Ganho*: começa a
   parecer wiki de verdade. *Custo*: índice cresce em O(links), e a Q13=A já disse que o agente lê o
   índice inteiro — índice grande é contexto gasto.

**Minha recomendação: B.** (A) é o núcleo certo, e a seção de links quebrados custa uma varredura que
a wiki desta escala aguenta sem sentir. (C) eu deixaria para quando `buscar` voltar.

[Answer]: A - vamos seguir com a A que é a idei central e eu ja sei que funciona dessa maneira. essa maneira é a maneira onde que eu vi na estrutura que estou me baseando , essa estrutura é otima para agora e ja agrega valor e resolve os nossos problemas de dar para os agentes contextos . esse nao é o momento de pensar em algum tipo de melhoria para o index.md ser mais otimizado. vamos seguir com a A.

---

### Q4 — Como um `[[link]]` resolve

Com dois níveis (entidade/propriedade), um link pode ser escrito de duas formas.

A) **Sempre qualificado**: `[[clientes/dr-marcelo]]`. *Ganho*: resolução trivial, ambiguidade
   impossível, e a validação no momento da escrita é uma checagem de existência.
   *Custo*: mais verboso; e se a página mudar de entidade, o link quebra (mas quebra visivelmente, ver
   Q3).
B) **Nome simples**, resolvido globalmente: `[[dr-marcelo]]`, como no Obsidian. *Ganho*: é o que um
   humano escreve. *Custo*: dois arquivos com o mesmo nome em entidades diferentes tornam o link
   ambíguo, e aí é preciso uma regra de desempate.
C) **Simples quando único, qualificado quando não.** *Custo*: o mesmo link muda de significado quando
   alguém cria uma página com nome repetido em outro lugar.

**Minha recomendação: A.** Quem escreve o link é um agente chamando uma ferramenta, não uma pessoa
digitando — verbosidade não custa nada, e (C) tem a pior propriedade possível: um link válido hoje
vira ambíguo amanhã por causa de um arquivo criado longe dali.

[Answer]: A 

---

### Q5 — Do nome proposto ao nome de arquivo

O bibliotecário propõe `propor_entidade({"nome": "Dr. Marcelo & Cia"})`. O que vira no disco?

A) **Slug determinístico** — minúsculas, sem acento, não-alfanumérico vira hífen:
   `dr-marcelo-e-cia/`. O nome original fica no frontmatter (`titulo`) e é o que o índice exibe.
   *Ganho*: nome de arquivo previsível em qualquer sistema; e o slug é também a primeira barreira de
   confinamento, porque `..` e `/` não sobrevivem a ele.
   *Custo*: dois nomes diferentes podem gerar o mesmo slug (ver Q6).
B) **Nome literal**, recusando só o que é perigoso. *Ganho*: o disco fica igual ao que o usuário lê.
   *Custo*: espaço, acento e maiúscula em nome de arquivo atravessando Windows/Linux/OneDrive é uma
   fonte de defeito que não paga o ganho.
C) **Slug, sem guardar o original.** *Custo*: `dr-marcelo-e-cia` é o que aparece no índice para
   sempre; a wiki fica com cara de banco de dados.

**Minha recomendação: A.**

[Answer]: A - esse padrao é bom para seguir é simples e resolve.

---

### Q6 — Proposta aprovada para uma página que **já existe**

Item aberto desde 2026-08-19: *"política de conflito quando duas escritas tocam a mesma página"*. É o
caso central do loop que esta iteração valida — a segunda vez que o bibliotecário aprende algo sobre o
mesmo cliente.

A) **Recusa.** Página existente não é escrita; o bibliotecário tem que propor outro nome.
   *Custo*: o ambiente não fica mais inteligente sobre o que já conhece, só sobre o que é novo — que é
   justamente a hipótese que a iteração quer validar.
B) **Sobrescreve.** *Custo*: perda silenciosa. A rede de segurança é a aprovação humana, mas o usuário
   aprova a *proposta*, não vê o que está sendo apagado.
C) **Anexa** ao fim da página, sob um separador com data. *Ganho*: nunca perde nada, e o histórico
   fica dentro do próprio arquivo — mesma escolha que U1 fez para a memória de tarefa (anotação nova
   não substitui a anterior). *Custo*: páginas viram diário; alguém precisa consolidar, e ninguém vai.
D) **Vira proposta de atualização**, com o conteúdo novo e o antigo mostrados lado a lado na
   aprovação. *Ganho*: a decisão fica com quem tem contexto. *Custo*: exige que U9 saiba mostrar duas
   versões, o que hoje não está no escopo daquela unidade.

**Minha recomendação: C**, com a data no separador. É o comportamento que preserva a propriedade mais
valiosa (nada se perde) sem exigir nada de U8 nem de U9. Se você preferir (D), diga — mas então U9
ganha um requisito novo, e eu registro isso como emenda no `unit-of-work.md`.

[Answer]:  vou corrigir o direcionamento, nenhuma opcao refelte de fato como eu penso que vai funcionar a questao de atualizacoes de informacoes. o problema de "política de conflito quando duas escritas tocam a mesma página" nao é um problema. vou explicar - quando paginas sao criadas, elas sao criadas com uma descricao ou seja tem um sentido aquela pagina , a pagina vai carregar informacoes com base naquela descricao, o bibliotecario nao é um fator passivo, ele sabe moldar a wiki, a wiki é a sua biblioteca e ele sabe organizar e fazer os ajutes, isso quer dizer que o precesso de escrever na mesma pagina existe e é normal, esse processo acontece quando o bibliotecario decide adicionar mais informacoes de forma organizada sempre naquela pagina pois bate com a descricao, outro caso é quando o bibliotecario percebe que a informacao esta defasada entao ele tem aque atualizar , e ele nunca apaga, pela regra que eu penso me baseando no framework que aprendi, o bibliotecario marcaria a informacao defasada coloando entre ~(informacao defasada)~ poderia explicar e colocaria a informcao atualizada. entao o bibliotecario é um agente que cuida da wiki fazendo os seus processos de trabalho sendo seus processos - query: a busca de informacao, ingest: colocar novas informacoes na wiki da forma que achar mais apropriada seguindo um padrao de ingestao(por exemplo seguir o padrao do frontmatter), lint: analisas a wiki vendo se esta tudo correto fazendo uma limpeza e mantendo funcional. no processo de ingest o bibliotecario poderia fazer usar a marcaçao de informacao defasada na hora da escrita, e no processo de lint o bibliotecario pode encontrar informacao defasada sabendo que precisa atualizar. entao é assim que eu imagino essa questao.

---

### Q7 — Escrita concorrente e edição de fora enquanto o app roda

Um processo, um usuário, mas duas sessões vivas (orquestrador e bibliotecário) — e você pode ter a
pasta aberta no Obsidian ao mesmo tempo.

A) **Nada.** Toda escrita passa por `escrever_proposta`, chamada por um serviço só, depois de
   aprovação humana — não há dois escritores dentro do app. Edição externa simultânea é aceita como
   risco declarado. *Custo*: se você salvar no Obsidian no exato instante da aprovação, um dos dois
   vence e não avisa.
B) **Escrita atômica** (escreve em arquivo temporário na mesma pasta, depois `os.replace`).
   *Ganho*: nunca existe arquivo pela metade, nem se o processo morrer no meio. *Custo*: ~5 linhas.
C) **Arquivo de trava** por wiki. *Custo*: trava órfã depois de um crash é pior do que o problema que
   resolve, para um app local de um usuário.

**Minha recomendação: A + B.** Sem coordenação entre processos (A), mas com escrita atômica (B), que é
barata e elimina a única falha realmente feia — página truncada.

[Answer]: A - vamos seguir de A e assumir o risco. a questao de fazer o arquivo temporario pode dar problema se o arquivo for grande, tem o ganho de existir arquivo pela metade, porem nao vejo isso como vantagem agora, pensando que no futuro quando o software estiver em nuvem a wiki nem vai ser acessavel diretamente pelo usuario , assim o software fica com o controle maior e nao teria problema de arquivo ser sobreposto pq o usurio estaria mexendo ao mesmo tempo. eu penso assim pelo menos, nao consegui pensar em mais trade offs. 

---

### Q8 — As maquetes prontas

Da Parte B.3: *"o software já quer disponibilizar algumas maquetes prontas"*. Três perguntas de uma
vez, porque a resposta é uma só decisão.

**Quantas e de quê.** As personas dão dois domínios naturais (João: aquisição; Pedro: estudos).

A) **Três**: `aquisicao`, `estudos` e uma genérica `projeto` (entidades como `contexto`, `decisoes`,
   `pessoas`, `referencias`). *Ganho*: quem não se vê nas duas primeiras tem uma terceira que não é
   vazia. *Custo*: a genérica corre risco de ser genérica demais para servir.
B) **Duas**, só as dos dois usuários reais. *Ganho*: cada maquete vem de um domínio de verdade, e isso
   é visível na qualidade das descrições.
C) **Uma só**, genérica. *Custo*: contradiz o espírito de US-09, que existe para a wiki **não** ter
   forma imposta pelo produto.

**O que a maquete carrega.** Estrutura (entidades e propriedades com descrição), ou também conteúdo
inicial nos arquivos?

D) **Só estrutura + descrição**, arquivos de propriedade nascem vazios de conteúdo.
   *Ganho*: a descrição é o que o índice usa para recuperação — é ela que precisa ser boa; conteúdo
   inventado pelo produto seria o software fingindo saber do seu domínio.
E) **Estrutura + um parágrafo de exemplo** em cada arquivo. *Custo*: o exemplo vira ruído que ninguém
   apaga, e o agente vai lê-lo como se fosse conhecimento do ambiente.

**Minha recomendação: A + D.** E as maquetes são arquivos `.toml` versionados junto ao código
(`carregar_toml` já existe no contrato), não código Python — trocar ou acrescentar uma maquete não
deve exigir alterar módulo nenhum.

[Answer]: nao vamos fazer nessa iteracao nenhuma maquete. essas maquetes foram uma ideia minha. penso que faz mais sentido nos focarmos nessa iteracao fazer o software funcionar, e depois que estiver funcionar, nos podemos fazer alguma maquete para quando eu dar para o meu usuario ele ter uma referencia de uso e saber melhor como usar. entao vamos tirar isso da iteracao e deixar isso para depois como uma ideia futuro que pode ser feito em uma proxima iteracao. 

---

### Q9 — O que está escrito num `index.md` vazio

Custo declarado na Parte B.3: um índice vazio precisa ser legível, não ambíguo — o agente que começa a
leitura por ele tem que distinguir "wiki vazia" de "wiki quebrada".

A) **Cabeçalho, uma frase explícita e nada mais**:

```markdown
# Wiki — Nexo Aquisição

*Arquivo gerado automaticamente. Edições feitas aqui são perdidas na próxima renderização.*

Esta wiki ainda não tem nenhuma entidade.
```

B) **Cabeçalho e mais nada** (o vazio fala por si). *Custo*: é exatamente o vazio ambíguo que a Parte
   B.3 apontou.
C) **Cabeçalho + a frase + instrução de como criar a primeira entidade.** *Ganho*: o agente que lê sabe
   o que fazer a seguir. *Custo*: instrução dentro de dado — a wiki é entrada não confiável (RNF-14,
   ver Q10), e escrever instrução para o modelo dentro dela desfaz um pouco essa fronteira, mesmo
   sendo texto nosso.

**Minha recomendação: A.** A linha de aviso "gerado automaticamente" vale para **todo** índice, não só
para o vazio: o critério 4 diz que o índice nunca é escrito por agente, mas nada impede um humano de
editá-lo e perder o trabalho na renderização seguinte.

[Answer]: A - eu penso que temos que seguir o caminho da A porem de outra forma. a forma que vc escreveu fica algo como um contexto fixo no arquivo, penso que isso pdoe ser ruim pois a dinamica do arquivo pode mudar. penso que tem q ser algo estrutural apenas e se tiver vazio eu pensei em fazer uma frase indicando q esta vazio e nao tem nenhuma entidade na wiki ainda. pensei em algo assim:

```markdown
# Wiki — Nexo Aquisição

*descricao da wiki Nexo Aquisicao*

# Entidades
(vazio - ainda nao tem nenhum entidade)

```

E depois que fosse escrito a primeira entidade essa mensagem de "(vazio - ainda nao tem nenhum entidade)" iria sair. assim temos a estrutura do index e a mensagem que indica que nao tem entidades 

---

### Q10 — A wiki é entrada não confiável: quem embrulha o conteúdo

RNF-14 diz que o conteúdo da wiki é entrada não confiável mesmo sendo dado do próprio usuário — pode
conter instrução dirigida ao modelo. As defesas nomeadas são estruturais (bibliotecário sem ferramenta
de escrita nativa; aprovação humana). Falta dizer o que acontece no caminho de leitura.

A) **A porta devolve o conteúdo cru**, e o embrulho ("isto é dado de wiki, não instrução") é feito por
   **U8**, ao montar o resultado da ferramenta. *Ganho*: a porta continua sendo sobre arquivos, e quem
   sabe de prompt é quem fala com o modelo. *Custo*: se U8 esquecer, ninguém percebe — não há teste
   nesta unidade que pegue.
B) **A porta devolve `ConteudoPagina` com proveniência** (caminho, se veio de fora do app, tamanho), e
   U8 usa isso para embrulhar. *Ganho*: a informação necessária existe na fronteira, e o esquecimento
   de U8 vira uma coisa nomeada que dá para cobrar no portão daquela unidade. *Custo*: um tipo um
   pouco mais gordo.
C) **A porta já devolve o texto embrulhado** em delimitadores. *Custo*: a porta passa a saber o que é
   um prompt — vazamento de vocabulário na direção errada, exatamente o que `D-ARQ-04` proíbe do outro
   lado.

**Minha recomendação: B.** É a única que não deixa o requisito cair no vão entre duas unidades.

[Answer]: B - vamos seguir com essa opcao porem vamos fazer de forma mais enxuta, nao precisamos aidioncar algum parametro que diga se veio fora do app. esse parametro tem como objetivo a questao de segurança pois oq a rnf-14 diz que o conteudo da wiki nao é confiavel, mas isso realemte nos nao temos que nos preocupar com isso e é over fazer ter essa preocupacao agora e ter esse parametro somente para isso. o software precisa nascer primeiro antes de começar a pensar nesses pequenos detalhes, e outro ponto é que o software vai começar com no maixmo 2 usuarios proximos q eu conheço e vou estar perto para orientar e nao vai ter o problema de ter uma wiki perigosa que pode conter alguma instrucao malicioso. 

---

### Q11 — Limite de tamanho na leitura

Uma página pode crescer (ainda mais com a escolha C da Q6, que anexa). Ler uma página de 2 MB enche o
contexto do agente e a chamada falha longe daqui.

A) **Sem limite** nesta iteração. *Custo*: a falha aparece como erro do provedor, não como erro nosso.
B) **Trunca acima de um limite** (proponho 64 KB — umas 15 mil palavras, muito acima de qualquer página
   real), com uma marca explícita no fim: `[conteúdo truncado — página tem N KB]`.
   *Ganho*: degrada em vez de quebrar, e a marca diz ao agente que existe mais.
C) **Recusa acima do limite.** *Custo*: uma página grande demais fica inalcançável.

**Minha recomendação: B.**

[Answer]: A - sem limite, se colocarmos limite nao vai atender a necessidade de produto, limitaria muito o software, vamos seguir sem limite de tamanho das paginas.

---

### Q12 — O critério "entidade nova ou arquivo dentro de uma existente"

Está registrado como **o risco número um do desenho da wiki**: *"sem regra, ele decide diferente a cada
vez e a wiki apodrece em semanas"*. A decisão em si é do **prompt do bibliotecário** (U8). A pergunta
aqui é se U3 faz alguma coisa **estrutural** para tornar a decisão mais fácil, ou se ela sai inteira
desta unidade.

A) **Sai inteira para U8.** Esta unidade só oferece as operações. *Ganho*: fronteira limpa.
   *Custo*: o risco número um fica todo em cima de um prompt.
B) **U3 ajuda pelo índice**: o índice mostra, para cada entidade, sua **descrição** e a contagem de
   propriedades. O agente que lê o índice antes de propor vê o que cada entidade é para e decide com
   informação, não de memória. *Ganho*: barato, e é a informação certa no lugar onde ele já vai olhar
   de qualquer jeito.
C) **U3 impõe um teto** de entidades (por exemplo, 12) — passando disso, `propor_entidade` recusa e o
   bibliotecário precisa encaixar numa existente. *Ganho*: proliferação vira impossível, não
   improvável. *Custo*: número arbitrário, e a recusa pode cair no meio de um trabalho legítimo.

**Minha recomendação: B.** É o único que trata o risco sem inventar limite, e ainda melhora o índice
para o resto do sistema. A regra de decisão continua sendo de U8 — mas passa a ser tomada olhando para
dados, e não para lembrança.

[Answer]: B - realmetne o indice é uma das nossas formas de dar mais informacao certa e fazer o bibliotecario decidir melhor , isso esta certo. e sim por enquanto a decisao em si é do promtp do bibliotecario e vamos seguir com essa ideia ainda, pois ja funciona muito bem pois eu ja testei um POC do bibliotecario que eu ja fiz e funciona bem, no futuro posso pensar em melhorar essa questao de como melhorar a decisao do biblioteacario.

---

## 7. Depois das respostas

Step 5 relê tudo procurando resposta vaga ("depende", "talvez", "mistura de"). Se houver, abro
`wiki-fd-clarificacao.md` e paro ali. Sem ambiguidade, sigo para os três artefatos do Step 6 e depois
para o portão 1/4.
