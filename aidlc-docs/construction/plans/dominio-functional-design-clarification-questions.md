# Functional Design — U1 `dominio` — perguntas de clarificação (rodada 2)

**Data:** 2026-08-25 · **Origem:** análise obrigatória do Step 5 da regra
`construction/functional-design.md` sobre as 9 respostas da rodada 1

**Resultado da análise:** 8 das 9 respostas estão claras e sem contradição entre si
(Q2=A, Q4=A, Q5a=B, Q5b=A, Q7=A, Q8=A, Q9=A, e a **letra** da Q1=A). **Não prossegui para os
passos 3 a 7** por três motivos, abaixo — um deles bloqueante.

---

# CQ1 — BLOQUEANTE: "a wiki é que tem as frentes"

## O que você escreveu na Q1

> *"a frente é parte da wiki e nao se relaciona com o ambiente diretamente. quem se relaciona com o
> ambiente diretamente é a wiki, e a wiki que tem as frentes e suas regras de funcionalidade."*

## Por que eu parei aqui

Se lida ao pé da letra, essa frase **derruba o modelo de domínio aprovado**, e não só em U1:

| Artefato aprovado | O que diz |
|---|---|
| `components.md` §2.2 | `Ambiente` guarda "coleção de `Frente`" e a invariante "toda frente pertence a este ambiente" |
| `component-methods.md` §1.2 | `Ambiente.frentes: list[Frente]`, `Ambiente.criar_frente(nome) -> Frente` |
| `components.md` §2.8 | A **única** coisa que o domínio sabe sobre a wiki é a `RaizWiki` — um localizador |
| `unit-of-work.md` U3/U4 | Wiki é pasta de markdown no filesystem; `Frente` é entidade de domínio persistida em SQLite (U2) |

Ou seja: hoje `Frente` é objeto de domínio salvo no banco, e a wiki é um diretório de arquivos
markdown. São dois substratos diferentes. "A wiki tem as frentes" só pode significar uma destas
três coisas, e elas custam preços muito diferentes:

**A) Foi vocabulário — o modelo aprovado continua.** Você quis dizer que a **wiki nasce junto com o
ambiente** (o que já é verdade: `ServicoDeAmbiente.criar_ambiente` materializa a wiki, e a Q9=A que
você acabou de responder põe a `RaizWiki` dentro do `Ambiente`), e que a frente é criada pelo
usuário e não automaticamente — que é exatamente o que a letra A da Q1 decidiu.
*Custo*: zero. Nada muda.

**B) Mudança real de modelo: `Frente` deixa de ser entidade de domínio e vira entidade da wiki**
(uma pasta com páginas markdown). *Custo*: alto e fora de U1 — `Ambiente` perde `frentes`,
`Frente.criar_tarefa` muda de dono, U2 deixa de persistir frente, U3 ganha a responsabilidade,
U4 e U5 mudam. Isso reabre Application Design, não só Functional Design.

**C) Meio-termo: `Frente` continua entidade de domínio e *também* ganha uma página na wiki**
quando é criada — a wiki como reflexo navegável da estrutura. *Custo*: médio; não muda U1 (o
domínio segue igual), acrescenta um passo em U4 e um critério em U3. Vale notar que **nenhuma das
14 histórias da linha fina pede isso** — seria escopo novo, do mesmo tipo que você retirou na
rodada 4.

**Minha leitura, declarada para você corrigir:** acho que é **A**, porque tudo o mais que você
respondeu é coerente com o modelo atual — a Q9=A põe a raiz da wiki *dentro* do `Ambiente`, o que é
o oposto de a wiki conter o ambiente. Mas não vou assumir: se for B, gerar os artefatos de U1 agora
seria gerar especificação para um modelo que você acabou de descartar.

[Answer]: **A** — respondida em prosa na mensagem de 2026-08-25T21:00:00Z: *"as frentes não
pertencem ao Wiki. As frentes pertencem ao ambiente"*, com o pedido explícito de reverter a
observação anterior. Ver a **Parte B** abaixo, que registra a correção e o que ela ensina.

---

# CQ2 — Sua pergunta na Q3: por que não subir a versão do Python?

Você não escolheu A, B nem C — perguntou:

> *"pq nos somente nao aumentamos a nossa versao de uso do python para esse projeto?"*

**É uma boa pergunta e a resposta é: podemos, e é melhor que as três opções que eu ofereci.** Fui
verificar antes de responder, em vez de opinar:

| Verificação | Comando | Resultado |
|---|---|---|
| 3.14 disponível na máquina? | `uv python list` | `cpython-3.14.4-windows-x86_64` — download disponível, o `uv` baixa sozinho |
| `uuid7` existe no 3.14? | `uv run --python 3.14 python -c "import uuid; uuid.uuid7()"` | **Sim** — devolveu `01a03bf1-8adc-728c-bd56-e8451ec278bd` |
| As dependências futuras resolvem em 3.14? | `uv lock` com `claude-agent-sdk` + `textual` | **Sim** — 49 pacotes, `claude-agent-sdk 0.2.144`, `textual 8.2.8` |
| Elas **importam** em 3.14, não só resolvem? | `import claude_agent_sdk, textual` | **Sim**, ambos importaram na 3.14.4 |

**Por que eu não ofereci isso desde o início — admissão honesta:** eu tratei o `requires-python
>=3.13` do U0 como restrição, quando ele era uma decisão minha, tomada no plano de U0 há duas
horas, com o motivo "é a versão em uso". Não era restrição de ninguém. Você viu o que eu não vi.

### Opção D — subir para `>=3.14` (recomendada)

*Ganho*: `Identidade` vira três linhas usando `uuid.uuid7()` da stdlib; zero dependência nova; zero
código de geração de UUID escrito por nós para manter e testar; e o domínio continua importando só
a stdlib, preservando RF-F04.

*Custo real, declarado*:
1. **U0 precisa de emenda** — `requires-python` passa a `>=3.14` e o `uv.lock` é regerado. É uma
   unidade já aprovada; a emenda fica registrada como as outras, riscando e não apagando.
2. **Quem for rodar o FishingRod precisa de 3.14.** Na prática o `uv` resolve isso sozinho
   (baixa o interpretador), então o custo recai sobre quem instalar sem `uv` — que nesta iteração
   não é ninguém.
3. **3.14 é recente.** Se algum pacote futuro não a suportar, descer de volta custa mais do que ter
   ficado em 3.13. O teste acima cobre os dois pacotes que sabemos que virão (`claude-agent-sdk`,
   `textual`); não cobre o que ainda não foi decidido.

Responda **D** para subir, ou **A**/**B**/**C** para ficar em 3.13 com a opção original.

[Answer]: vamos subir a versao do python

---

# CQ3 — Não bloqueante: o que `versao` faz na `Memoria`

Você respondeu **Q6=B**: *"vamos usar anotar() e manter versao para entender ordem"*.

Preciso alinhar uma coisa pequena antes de escrever a regra, porque "ordem" pode significar duas
coisas e o campo só entrega uma:

- **O que `versao` faz**: conta quantas escritas a memória sofreu. Serve para detectar que alguém
  mais escreveu entre a leitura e a gravação — é o uso clássico em U2 (bloqueio otimista).
- **O que `versao` não faz**: ordenar as anotações entre si. A ordem em que as anotações
  aconteceram já está garantida de graça — pela posição na lista de cada chave, e, quando a
  identidade entrar, pelo próprio UUIDv7 ordenável por tempo.

Então:

A) **Mantém `versao` como contador de escritas** (uso: detecção de conflito em U2). A ordem das
   anotações continua sendo a ordem da lista.
B) **Você quer outra coisa por "ordem"** — por exemplo, cada anotação carregar um carimbo de tempo
   próprio para ser exibida em ordem cronológica misturando chaves diferentes. Isso é um campo em
   `Anotacao`, não em `Memoria`, e eu especifico assim.
C) **As duas coisas**: `versao` na `Memoria` **e** carimbo em `Anotacao`.

[Answer]:  C - é exatamente isso. eu tinha me esquecido a ideia do uso da 'versao' . agora que lembrei faz sentido mantermos para uso em funcoes.

---

## Nota de método

Não preenchi nenhuma resposta por você e não gerei nenhum artefato de design. A CQ1 é bloqueante; a
CQ2 muda a U0 já aprovada, então precisa da sua palavra; a CQ3 é pequena e não impede nada, mas
mudaria o texto de uma regra de negócio se eu adivinhasse errado.

---

# Parte B — Rodada 3 (2026-08-25T21:00:00Z): correção do usuário e o que ela move

## B.1 — CQ1 fechada: **as frentes pertencem ao ambiente**

Palavras do usuário: *"eu cometi um erro (…) as frentes não pertencem ao Wiki. As frentes pertencem
ao ambiente."*

**Efeito no modelo: nenhum.** É a leitura **A** da CQ1 — o modelo aprovado continua exatamente como
está. `Ambiente.frentes`, `Frente.tarefas`, `Frente` persistida em SQLite (U2), wiki como diretório
de markdown à parte (U3), `RaizWiki` como única coisa que o domínio sabe sobre ela. Nada foi
redesenhado e nada precisa ser desfeito, porque a análise do Step 5 parou antes de gerar artefato.

> **Observação de método, registrada porque é o ponto do processo funcionando.** A frase original
> foi escrita em uma resposta, revisada na rodada seguinte e corrigida antes de virar código. O
> custo total do erro foi uma pergunta. Se eu tivesse aceitado a frase e gerado os artefatos, o
> custo teria sido U1, U2, U3 e U4 refeitos.

## B.2 — O fluxo de criação de ambiente, como o usuário descreveu

Registro aqui porque é a descrição mais completa que existe deste fluxo — e ela vive em **U9**
(tela) e **U4** (serviço), não em U1:

| Campo da tela de criação | Obrigatório? | Onde vive |
|---|---|---|
| **Nome do ambiente** | **Sim** | `Ambiente.nome` (U1); tela em U9 |
| **Esquema/maquete da wiki** | **Não** | `EsquemaWiki` (U3); tela em U9 |
| → opção 1: **escolher uma maquete pronta** entregue pelo software | | U3 (as maquetes) + U9 (a escolha) |
| → opção 2: **escrever entidades e propriedades à mão** | | U9 (formulário, US-09) |
| → opção 3: **não escolher nada — a wiki nasce vazia** | | U3/U4 |

Antes disso, a **tela de início** lista ambientes existentes e permite criar um novo (Q10=B da
Units Generation, já atribuída a U9).

## B.3 — Consequência que contradiz um artefato aprovado — declarada para objeção

*"a Wiki pode começar vazia dentro do ambiente, não tem problema, ela é inicializada mas ela é
criada vazia dentro do ambiente, e o usuário dentro do ambiente depois pode criar essas entidades e
propriedades."*

Isso **revoga uma invariante aprovada** em Application Design (Pergunta 16B):

| Artefato | Texto atual | Situação |
|---|---|---|
| `services.md` §2, passo 4 | *"O serviço valida a invariante de criação (ao menos uma entidade — Pergunta 16B). Se falhar…"* | **Revogado** pela decisão acima |
| `unit-of-work.md` U4, critério 1 | *"…numa operação só; invariante de criação: ao menos uma entidade."* | **Revogado** — o critério de pronto de U4 muda |

**O que passa a valer**: criar ambiente materializa a raiz da wiki e renderiza o `index.md`
**mesmo que não haja entidade alguma** — um índice vazio é um estado válido, não um erro.

**Custo real, declarado:** o `index.md` vazio precisa ser um arquivo legível e não um vazio
ambíguo, senão o agente que começa a leitura por ele (Q13=A, sem `buscar`) não distingue "wiki
vazia" de "wiki quebrada". Isso vira critério de aceite de **U3**, não de U1.

**As três maquetes prontas** ("o software já quer disponibilizar algumas maquetes prontas") são
escopo de **U3** — quantas, de quais domínios e com que conteúdo é pergunta do Functional Design
daquela unidade, não desta. Registro aqui para não se perder.

**Nada disso bloqueia U1.** Se você discordar de alguma linha desta §B.3, é só dizer — as emendas
nos artefatos de U3/U4 só serão escritas quando aquelas unidades chegarem.

## B.4 — Estado das clarificações

| # | Resposta | Efeito |
|---|---|---|
| CQ1 | **A** (corrigida em prosa) | Modelo de domínio intacto; U1 destravada |
| CQ2 | **D** — *"vamos subir a versao do python"* | `requires-python >=3.14`; U0 emendada e revalidada (2 testes passando em 3.14.4); `Identidade` usa `uuid.uuid7()` da stdlib |
| CQ3 | **C** — *"eu tinha me esquecido a ideia do uso da 'versao'"* | `Memoria.versao` (contador de escritas) **e** carimbo de tempo em `Anotacao` |

**Nenhuma ambiguidade pendente.** Steps 3 a 7 do Functional Design de U1 liberados.
