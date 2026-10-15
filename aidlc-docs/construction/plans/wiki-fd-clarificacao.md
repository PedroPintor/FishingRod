# Clarificações — Functional Design de U3 `wiki`

**Fase:** CONSTRUCTION · **Unidade:** `U3 wiki` · **Portão 1 de 4, Step 5**
**Data:** 2026-09-22
**Origem:** análise das 12 respostas em `wiki-functional-design-plan.md`

---

## 0. Onde estamos

**Sete respostas fecharam limpas** e já são decisão: Q3=A (só as pastas mandam), Q4=A (link sempre
qualificado), Q5=A (slug determinístico), Q7=A (sem coordenação, risco assumido), Q9=A reformulada
(estrutura do índice), Q11=A (sem limite de leitura), Q12=B (índice ajuda a decisão do
bibliotecário).

**Cinco abriram ambiguidade** que eu não consigo resolver sozinho sem inventar desenho — e uma
delas (**C1**) trava o Step 6, porque sem ela eu não sei renderizar o índice que a Q12=B pediu.

Além disso, **quatro respostas revogam texto de artefato já aprovado** (§3). Estão declaradas para
objeção; se você não discordar, viram emenda no Step 8.

---

## 1. Clarificações — preciso destas respostas

---

### C1 — Onde mora a descrição de uma **entidade**? *(esta é a que trava)*

A **Q12=B** decidiu: *"o índice mostra, para cada entidade, sua descrição e a contagem de
propriedades"*. A **Q1** decidiu que a descrição vem do frontmatter.

O problema: **entidade é uma pasta**, e pasta não tem frontmatter. Propriedade é arquivo e tem;
entidade não tem onde guardar a própria descrição.

Não posso tirar a descrição do próprio `index.md`, porque o índice é **projeção do disco** — ele é
regenerado a partir do que existe, então não pode ser a fonte daquilo que ele mesmo mostra. Na
primeira renderização, a descrição sumiria.

A) **Um arquivo de metadados dentro da pasta** — `clientes/_entidade.md`, só com frontmatter
   (`titulo`, `descricao`) e sem conteúdo. *Ganho*: mesma mecânica de leitura das propriedades, um
   parser só. *Custo*: um arquivo que não é propriedade morando junto das propriedades — o
   renderizador e o `listar` precisam sabê-lo e pulá-lo.
B) **`clientes/index.md`** — cada entidade tem o próprio índice local, com sua descrição e a lista
   das propriedades dela. O `index.md` da raiz lista as entidades com descrição.
   *Ganho*: o agente pode ler só a entidade que interessa em vez do índice inteiro, o que importa
   quando a wiki crescer. *Custo*: dois níveis de índice para manter — mais código de renderização.
C) **A descrição da entidade não existe**: o índice mostra só o nome da entidade e, sob ela, as
   propriedades com descrição. *Ganho*: nada novo no disco. *Custo*: **a Q12=B deixa de valer** — a
   informação que faria o bibliotecário decidir entre entidade nova e arquivo em entidade existente
   é justamente a descrição da entidade.
D) **`clientes.md` ao lado da pasta `clientes/`** (estilo Obsidian: nota da pasta como irmã).
   *Custo*: dois itens com o mesmo nome no mesmo nível, e o esquema de dois níveis fica confuso de
   ler no disco.

**Minha recomendação: A.** É a que custa menos código e mantém um parser só. (B) é melhor quando a
wiki for grande, mas hoje o agente lê o índice inteiro de qualquer jeito (Q13=A) — o ganho ainda não
existe, e o custo sim.

[Answer]: C - vou explicar melhor como eu imagino. o formato que eu imagino para o index.md é:

1 - dessa forma quando nao tiver entidades
```markdown
# Wiki — Nexo Aquisição

*descricao da wiki Nexo Aquisicao*

# Entidades
(vazio - ainda nao tem nenhum entidade)

```
2. dessa forma quando tiver entidades 
```markdown
# Wiki — Nexo Aquisição

*descricao da wiki Nexo Aquisicao*

# Entidades

## [[nome da entidade]]: <descricao>

[[nome da propriedade]]: <descricao da propriedade>
[[nome da propriedade]]: <descricao da propriedade>


## [[nome da entidade]]: <descricao>

[[nome da propriedade]]: <descricao da propriedade>
```

como pode ver dessa forma o index tem a descricao da entidade q é criada na hora, e nao vai alterar, e para cada entidade tem a sua propria lista de propriedades com suas proprias descricoes que vem do fronttmatter das propriedades. assim esta claro como eu imagino que seja o index e como isso vai ajudar o bibliotecario encontrar as informacoes que precisa tendo como via de entrada o arquivo index.md da wiki. 

---

### C2 — O `titulo` no frontmatter: fica ou sai?

Duas respostas suas discordam entre si, e as duas são razoáveis:

| Resposta | O que diz |
|---|---|
| **Q5=A** | *"O nome original fica no frontmatter (`titulo`) **e é o que o índice exibe**"* |
| **Q1=B** | *"a informação que precisamos do frontmatter para montar o índice é **apenas a descrição**"*, e o item é `[<nome do arquivo>]: (descrição)` |

Ou seja: o índice mostra `Dr. Marcelo & Cia` (o título) ou `dr-marcelo-e-cia` (o nome do arquivo)?

A) **Só o nome do arquivo.** `titulo` não existe no frontmatter; a única chave lida é `descricao`.
   *Ganho*: frontmatter mínimo, uma chave, nada para dessincronizar. *Custo*: o índice mostra slug —
   `dr-marcelo-e-cia` em vez de `Dr. Marcelo & Cia`.
B) **`titulo` existe e o índice o exibe**, com o nome do arquivo entre parênteses ou como o alvo do
   link. *Ganho*: o índice fica legível para humano. *Custo*: uma chave a mais, e o renderizador
   precisa de um caso para quando ela falta.
C) **`titulo` existe no frontmatter mas o índice não o usa** — fica só como registro do nome
   original. *Custo*: uma chave que ninguém lê é uma chave que vai ficar errada sem ninguém notar.

**Minha recomendação: A**, coerente com a sua observação na Q1 (frontmatter enxuto, uma chave). O
slug de `Dr. Marcelo & Cia` é `dr-marcelo-e-cia`, que continua legível — e a descrição ao lado
resolve o resto. Se você quiser (B), é barato, mas aí a Q1 muda: o índice passa a ler duas chaves.

[Answer]: realmente eu me contradizi e eu cometi um erro. no exemplo da minha resposata da pergunga C1 esta claro como deve ficar. o nome da propriedade é o nome do arquivo e como é ruim ficar trocando o nome do arquivo a todo momento pois pode gerar discrepancia em algum momento ,portanto o nome da propriedade vai ser o nome do arquivo quando criado, o nome do arquivo vai ser criado baseado no titulo inicialmente, porem com slug para manter o padrao. entao vamos de alternativa C - o titulo é visual e é bom para ter contexto, vamos manter nao vai gerar muito custo adicional e como nao vamos ler essa chave para usar com algo, nao vai ter problema.

---

### C3 — O item do índice é link navegável?

Você escreveu o formato como `[<nome do arquivo>]: (descricao do frontmatter)`, com **um** par de
colchetes. A **Q4=A** decidiu que link é `[[entidade/propriedade]]`, com **dois**.

A) **É link**: `[[clientes/dr-marcelo]]: descrição da página`. *Ganho*: o agente lê o índice e já
   tem o caminho exato para passar ao `ler` — o índice vira navegação de verdade, que é o que a
   Q13=A exige dele. *Custo*: nenhum que eu veja.
B) **É texto**, como você escreveu: `[dr-marcelo]: descrição`. O agente monta o caminho juntando a
   entidade da seção com o nome. *Custo*: o agente monta caminho por conta própria — mais uma coisa
   que pode sair errada.

**Minha recomendação: A.** Suspeito que você quis dizer isto e escreveu um colchete só de passagem —
mas prefiro perguntar a assumir.

[Answer]: A - eu cometi o um erro. relamente é um link eu cometi um deslise e digitei errado.

---

### C4 — `escrever_proposta` recebe a página inteira ou um pedaço?

A sua resposta da Q6 mudou a pergunta, e com razão: escrever de novo na mesma página é
**trabalho normal do bibliotecário**, não conflito. Ele lê a página, entende que a informação nova
combina com a descrição dela, marca o que ficou defasado e devolve a página atualizada.

Essa descrição implica uma coisa mecânica que nenhuma opção minha cobria, e preciso que você
confirme: **a proposta carrega o conteúdo completo da página**, e `escrever_proposta` substitui o
arquivo inteiro.

A) **Conteúdo completo, substitui o arquivo.** É o que a sua descrição implica: quem decide o texto
   final — incluindo o que virou `~~riscado~~` — é o bibliotecário, que leu a página antes.
   *Ganho*: a porta fica burra e previsível; toda a inteligência é do agente, que é onde você a
   colocou. *Custo*: se o bibliotecário ler a página, demorar, e a página mudar nesse meio-tempo, a
   escrita apaga a mudança. Pela Q7=A, assumimos esse risco — e o único outro escritor é ele mesmo.
B) **Fragmento anexado ao fim.** *Custo*: contradiz a sua resposta — não dá para marcar
   `~~defasado~~` num texto que está acima do fragmento se você só sabe anexar.

**Minha recomendação: A.** Registro junto a consequência: a porta **não** valida se o bibliotecário
preservou o que havia. Ele pode apagar conteúdo sem querer, e a rede de proteção é a aprovação
humana da proposta (US-14) — humana, não técnica, como já é o caso da qualidade da descrição.

[Answer]: A

---

### C5 — `query`, `ingest` e `lint`: o que entra nesta iteração?

Você descreveu os três processos do bibliotecário, e eu concordo com o modelo. Mas dois deles têm
texto aprovado dizendo que estão **fora**:

| Processo | Texto aprovado | Onde |
|---|---|---|
| `ingest` | *"Operações de wiki `ingest` (**pasta `raw/`**) e `lint`"* — **FORA de escopo** | `requirements.md` FOR-12 |
| `lint` | idem, e a justificativa: *"Links são validados no momento da escrita, o que evita a maior parte do apodrecimento **sem existir processo de lint**"* | `requirements.md` FOR-12 |
| `query` | `buscar` removida da porta | Q13=A |

Minha leitura, que pode estar errada:

- **`ingest` não é o mesmo `ingest`.** O que FOR-12 tirou foi o fluxo da **pasta `raw/`** (jogar
  arquivos numa pasta e o agente digerir). O seu `ingest` é "escrever na wiki seguindo um padrão",
  que é exatamente `propor_propriedade` + `escrever_proposta` — **está dentro** e sempre esteve.
- **`query` também não é o mesmo.** O que Q13=A tirou foi a operação `buscar` (grep). O seu `query`
  é "ler o índice e depois as páginas", que é o caminho que sobrou — **está dentro**.
- **`lint` está genuinamente fora**, por FOR-12, e não tem substituto.

A) **A minha leitura está certa**: `ingest` e `query` como você os descreveu já estão dentro com
   outros nomes; `lint` fica fora desta iteração e volta depois. A marcação `~~defasado~~` continua
   valendo — ela acontece no momento da escrita, não numa varredura.
B) **`lint` entra nesta iteração.** Aí ele precisa de dono: seria um processo do bibliotecário
   (**U8**) e uma operação nova na porta (varrer, listar páginas com `~~defasado~~`, links
   quebrados). *Custo*: U8 ganha escopo, esta unidade ganha uma operação, e `FOR-12` precisa ser
   revogado por escrito.
C) **Outra leitura** — me diga qual.

**Minha recomendação: A.** O modelo dos três processos fica registrado como o desenho-alvo do
bibliotecário (ele é bom e vale guardar), mas nesta iteração só dois deles têm código.

[Answer]: A - sim sua leitura esta certa, ainda vamos manter apenas o ingest e query nessa iteracao. eu apenas inclui o lint para ficar uma explicacao completa.

---

## 2. Duas decisões menores que eu tomo sozinho se você não objetar

### D1 — A marcação de defasado é `~~texto~~`, com **dois** tis

Você escreveu `~(informacao defasada)~`. Em markdown padrão (GFM, que é o que o Obsidian usa), um
til só **não** é tachado — vira texto literal ou subscrito, dependendo do renderizador. Dois tis é
tachado de verdade: ~~assim~~.

Vou adotar `~~texto~~`. O conteúdo da marcação (o texto explicando por que ficou defasado) é
decisão do bibliotecário, não formato — então é regra de **U8**, e U3 só registra a convenção para
que o `lint` futuro saiba o que procurar.

### D2 — `# Entidades` vira `## Entidades`

No seu esboço do índice os dois títulos são `#`. Um documento com dois H1 confunde qualquer
renderizador e, principalmente, o agente que lê o índice como estrutura. O título da wiki fica `#`,
a seção fica `##`.

---

## 3. Quatro revogações de artefato aprovado — declaradas para objeção

Nenhuma destas é pergunta. São consequências das suas respostas, e viram emenda no Step 8 (texto
anotado, nunca apagado) se você não discordar.

### E1 — A Q2 revoga o **critério 3** de U3 e enfraquece o **critério 1**

Sua decisão: página criada fora do app é **ignorada**, e o critério 3 sai — a wiki vai ser
armazenamento que o usuário não mexe por fora.

| Artefato | Texto atual | Situação |
|---|---|---|
| `unit-of-work.md` U3, critério 3 | *"Uma página criada fora do app aparece no índice após regeneração"* | **Revogado** |
| `unit-of-work.md` U3, critério 1 | *"Toda entidade e toda propriedade **presente no disco** aparece no `index.md` regenerado"* | **Emendado**: passa a valer para o que o app escreveu. O que não tem frontmatter legível com `descricao` não vazia é ignorado silenciosamente |
| `components.md` §5.3 | *"O índice é projeção do disco: **página criada fora do app aparece na próxima renderização**"* | **Revogado** na segunda metade; "projeção do disco" continua |

**Efeito colateral que vale notar**: isso deixa a Q9 mais coerente do que eu tinha proposto. Eu
queria uma linha de aviso *"arquivo gerado automaticamente"* no índice para proteger quem o
editasse à mão — e você a recusou. Com o critério 3 revogado, editar à mão deixa de ser um caso que
o sistema reconhece, e o aviso perde a razão de existir. Sua versão do índice fica.

### E2 — A Q8 tira as maquetes, e leva `carregar_toml` junto

Sem maquetes nesta iteração, `EsquemaWiki.carregar_toml` fica sem nenhum chamador. Vou tirá-la do
contrato desta unidade (`component-methods.md` §3.4) e registrar como reativável — a assinatura fica
anotada, não apagada, para a iteração que trouxer as maquetes de volta.

`EsquemaWiki` **continua existindo**, com `a_partir_do_formulario` (US-09, o formulário de criação
em U9) e com o caso vazio (US-08). É o que sustenta US-09 sem maquete: a estrutura continua sendo
definida pelo dono, só que digitando em vez de escolhendo.

| Artefato | Texto atual | Situação |
|---|---|---|
| `components.md` §3.7 | *"Carregar-se a partir de um arquivo `.toml` (maquete embutida...)"* | **Adiado** para iteração futura |
| `component-methods.md` §3.4 | `carregar_toml(caminho)` | **Adiado**, assinatura preservada anotada |
| `components.md` §3.7 | *"Validar a invariante de criação: ao menos uma entidade"* | **Revogado** — já era, pela Parte B.3 de U1 (R-FD3-2) |

### E3 — A Q10 relaxa **RNF-14** na leitura, e isso precisa ficar escrito

Você escolheu B mas tirou o que fazia B diferente de A: sem o campo de proveniência,
`ConteudoPagina` carrega caminho e conteúdo, e o embrulho fica **inteiramente** com U8.

Registro como está, porque é a sua decisão e a justificativa é boa (dois usuários próximos, você por
perto, o software precisa nascer). Mas registro **honestamente**, porque RNF-14 é requisito da
extensão `security-baseline`, que está ligada:

> **Risco aceito, 2026-09-22.** RNF-14 dizia que a wiki é entrada não confiável e que a defesa vale
> *"na leitura (U3) e no contexto do agente (U8)"*. Nesta iteração a parte de U3 não existe: a porta
> devolve o conteúdo sem marca de proveniência. A defesa que **permanece** é estrutural e continua
> valendo inteira — o bibliotecário não tem ferramenta nativa de escrita (`tools=[]`) e toda escrita
> passa por aprovação humana. O que se perde é a marca que diria ao modelo "isto é dado, não
> instrução". **Condição de reabertura**: no momento em que a wiki receber conteúdo que não veio do
> próprio usuário — importação, compartilhamento, `raw/` — isto volta a ser bloqueante.

Se você preferir que eu não registre assim, diga — mas eu não consigo declarar `security-baseline`
conforme sem esta linha.

### E4 — Q3=A + sem `lint`: link quebrado depois da escrita fica invisível

Consequência combinada, para você saber que ela existe: o link é validado **quando é escrito**
(é U8 quem valida, em `aprovar`). Depois disso, se a página-alvo mudar de nome ou de entidade, o
link quebra e **nada no sistema percebe** — não há seção de links quebrados no índice (Q3=A) e não
há `lint` (C5=A).

Isso é exatamente o que `FOR-12` previu: *"links são validados no momento da escrita, o que evita a
**maior parte** do apodrecimento"*. Maior parte, não tudo. O resto é risco aceito desta iteração.

---

## 3-bis. C6 — a última, e é uma só *(rodada 2, 2026-09-23)*

### O formato do índice está fechado. Falta dizer **onde a descrição mora**.

O seu exemplo na C1 resolveu o formato e eu não tenho mais dúvida sobre ele:

```markdown
# Wiki — Nexo Aquisição

*descrição da wiki Nexo Aquisição*

## Entidades

### [[clientes]]: empresas e pessoas com quem já conversamos

[[clientes/dr-marcelo]]: dentista, ticket alto, fechou em duas reuniões
[[clientes/nexo-b2b]]: agência parceira, indica leads
```

Mas ele mostra **duas descrições que não vêm de frontmatter de propriedade**, e nenhuma das duas tem
onde morar hoje:

1. **a descrição da wiki** (a linha em itálico no topo) — vem do formulário de criação;
2. **a descrição de cada entidade** (`### [[clientes]]: ...`) — você escreveu *"é criada na hora, e
   não vai alterar"*.

Você marcou **C** — que na minha redação queria dizer *"a descrição da entidade não existe"*. Mas o
seu exemplo a mostra, então o que você recusou foi o **arquivo `_entidade.md` dentro da pasta**, não
a descrição. É disso que eu preciso: de onde o renderizador lê essas duas linhas.

E não pode ser do próprio `index.md`: ele é regenerado do disco a cada aprovação, então se ele for a
única fonte da descrição, na primeira regeneração ela some.

A) **Um arquivo de metadados na raiz da wiki** — `wiki.toml`, com o nome da wiki, a descrição dela e
   a descrição de cada entidade. O renderizador lê esse arquivo mais as pastas mais o frontmatter das
   propriedades, e monta exatamente o seu formato.
   *Ganho*: um lugar só, e o `index.md` continua sendo **projeção pura** — nunca fonte de si mesmo.
   E tem uma coerência que me parece forte: esse arquivo é literalmente o `EsquemaWiki` materializado.
   O formulário de criação (`a_partir_do_formulario`, US-09) produz exatamente isto — nome, descrição,
   entidades com descrição — e o arquivo segue vivo como registro conforme entidades novas entram.
   *Custo*: um arquivo que não é markdown dentro da wiki.
B) **O `index.md` guarda, e o renderizador lê o índice anterior** para recuperar as descrições antes
   de reescrevê-lo. *Ganho*: nada novo no disco. *Custo*: o índice deixa de ser projeção e vira fonte
   parcial de si mesmo; se ele for corrompido ou apagado, as descrições das entidades somem **para
   sempre**, porque não existem em nenhum outro lugar.
C) **`_entidade.md` dentro de cada pasta** (a opção A da rodada anterior), mais a descrição da wiki em
   algum arquivo na raiz. *Custo*: é a que você já recusou, e ainda precisaria do arquivo na raiz de
   qualquer jeito, por causa da descrição da wiki.

**Minha recomendação: A.** É a única que mantém o índice como projeção pura, resolve as duas
descrições de uma vez, e não põe arquivo estranho dentro das pastas de entidade.

[Answer]: vamos reformular eu entendi o meu erro. vamos fazer o seguinte para simplificar. vamos remover a descricao da wiki e a descricao das entidades. nao precisa. eu ja usei uma wiki para aprender e na wiki que eu ja usei e testei nao tem descricao da wiki nem  descricao da entidade. so tem descricao a propriedade. a propriedade é uma lista dentro de cada propriedade ficando assim: 

```markdown
# Wiki — Nexo Aquisição

# Entidades

## [[nome da entidade]]: 

- [[nome da propriedade]]: <descricao da propriedade>
- [[nome da propriedade]]: <descricao da propriedade>


## [[nome da entidade]]: 

- [[nome da propriedade]]: <descricao da propriedade>
```

---

## 4. O que acontece depois

Com C1 a C5 respondidas, eu sigo direto para o Step 6 (os três artefatos), o Step 7 (as
propriedades `PBT-U3-nn`), o Step 8 (as emendas da §3) e o portão 1/4. Nenhum artefato será gerado
antes.
