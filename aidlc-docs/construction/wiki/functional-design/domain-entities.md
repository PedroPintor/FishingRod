# Domain Entities — U3 `wiki`

**Fase:** CONSTRUCTION · **Unidade:** `U3 wiki` · **Portão 1 de 4** · **Data:** 2026-09-23
**Base:** 12 respostas do plano + 6 clarificações (`wiki-fd-clarificacao.md`), todas fechadas.

Esta unidade não tem entidade de domínio própria — a única que existe é `RaizWiki`, já implementada
em U1. O que este documento descreve é **o modelo de dados da wiki no disco** e os tipos de
fronteira que atravessam a porta.

---

## 1. O disco é o modelo

Não há banco, não há índice em memória, não há cache. **O que está no disco é o estado inteiro**, e
tudo o que o sistema mostra é derivável dele. Foi o que a C6 fechou: sem descrição de wiki e sem
descrição de entidade, não sobrou nenhuma informação que precisasse de um lugar próprio para morar.

```
<raiz>/                              resolvida de "dados:wikis/<id_ambiente>"
├── index.md                         projeção; nunca escrita por agente
├── clientes/                        NÍVEL 1 — entidade (pasta)
│   ├── dr-marcelo.md                NÍVEL 2 — propriedade (arquivo)
│   └── nexo-b2b.md
└── ofertas/
    └── plano-anual.md
```

**Dois níveis, travados** (ESC-17). Não existe parâmetro, em lugar nenhum da porta ou das
ferramentas, que aceite um terceiro — a violação é irrepresentável, não proibida por validação.

A raiz é resolvida pelo adaptador a partir do localizador, e só ele sabe o caminho real (RNF-11).

---

## 2. A página

```markdown
---
titulo: Dr. Marcelo & Cia
descricao: dentista, ticket alto, fechou em duas reuniões
---

Conversou com a gente em março. Objeção principal foi prazo, não preço.

~~Trabalha sozinho no consultório.~~ Desatualizado em setembro: contratou duas
auxiliares e uma recepcionista.

Ver também [[ofertas/plano-anual]].
```

| Parte | Quem escreve | Quem lê |
|---|---|---|
| `titulo` | adaptador, a partir do título proposto | **ninguém, em código** — é registro visual (C2=C) |
| `descricao` | adaptador, a partir da proposta | o renderizador do índice, e só ele |
| corpo | o bibliotecário, inteiro (C4=A) | `ler`, e o agente |

**O frontmatter é escrito e lido apenas pelo adaptador.** Nem o agente nem U8 compõem o bloco
`---`: a proposta chega com `titulo`, `descricao` e `conteudo` em campos separados, e é o adaptador
que monta o arquivo. Isso torna frontmatter malformado **irrepresentável pela via normal**, em vez
de detectável — a mesma escolha que `propor_propriedade` já fazia ao tornar `descricao` obrigatória
na assinatura (Pergunta 15D).

### Por que `titulo` fica, se ninguém o lê

Decisão C2=C, e a razão é sua: o nome do arquivo nasce do título **na criação e nunca mais muda**,
porque renomear arquivo gera discrepância. O `titulo` preserva o nome original — `Dr. Marcelo & Cia`
contra o `dr-marcelo-e-cia` do arquivo — para quem abrir a página. É contexto para humano e para
agente que já está lendo a página, não entrada de código.

Registro o custo, que eu havia levantado na C2 e que continua valendo: **chave que nenhum código lê
é chave que pode ficar errada sem ninguém notar.** Aceito.

---

## 3. O `index.md`

A porta de entrada obrigatória. Com `buscar` fora (Q13=A), é **o único caminho até o conteúdo** — não
é conveniência de navegação, é o mecanismo de recuperação.

### Com conteúdo

```markdown
# Wiki — Nexo Aquisição

## Entidades

### [[clientes]]

- [[clientes/dr-marcelo]]: dentista, ticket alto, fechou em duas reuniões
- [[clientes/nexo-b2b]]: agência parceira, indica leads

### [[ofertas]]

- [[ofertas/plano-anual]]: preço, prazo e o que entra em cada faixa
```

### Vazia

```markdown
# Wiki — Nexo Aquisição

## Entidades

(vazio — ainda não tem nenhuma entidade)
```

### Entidade sem propriedade legível

```markdown
### [[clientes]]

(sem propriedades)
```

**Três diferenças em relação ao seu esboço**, todas declaradas e nenhuma objetada:

| Seu esboço | Aqui | Por quê |
|---|---|---|
| `# Entidades` | `## Entidades` | D2 — dois H1 no mesmo arquivo confundem o renderizador e o agente que lê o índice como estrutura |
| `[[nome da propriedade]]` | `[[clientes/dr-marcelo]]` | Q4=A e C3=A — link sempre qualificado; assim o agente passa o caminho direto ao `ler`, sem montá-lo |
| `## [[entidade]]:` | `### [[entidade]]` | os dois-pontos sobraram de quando a entidade tinha descrição; sem descrição, não há o que separar |

A linha `(sem propriedades)` é extensão minha, pela mesma razão que você deu para a wiki vazia: o
agente precisa distinguir **"entidade vazia"** de **"entidade quebrada"**, e um cabeçalho seguido de
nada não distingue.

---

## 4. Tipos de fronteira

Moram em `aplicacao/portas/wiki.py`, junto da porta. Nenhum importa `pathlib`, `os` ou qualquer
coisa de filesystem.

```python
@dataclass(frozen=True)
class ConteudoPagina:
    caminho: str      # logico e qualificado: "clientes/dr-marcelo", sem ".md"
    titulo: str       # do frontmatter; "" quando ausente
    descricao: str    # do frontmatter
    conteudo: str     # o corpo, ja sem o bloco de frontmatter
```

> **Q10, versão enxuta.** Não carrega proveniência nem tamanho. A decisão e o risco aceito estão
> registrados em `business-rules.md`, na nota de RNF-14.

```python
@dataclass(frozen=True)
class PaginaProposta:
    entidade: str     # titulo da entidade; o slug e derivado dele
    titulo: str       # titulo da propriedade
    descricao: str    # obrigatoria, nao vazia
    conteudo: str     # a pagina INTEIRA (C4=A), nao um fragmento


@dataclass(frozen=True)
class PropostaWiki:
    entidades_novas: tuple[str, ...] = ()      # titulos de entidades a criar
    paginas: tuple[PaginaProposta, ...] = ()
```

`PropostaWiki` carrega **várias** páginas e várias entidades porque `aprovar` é um ato por promoção
(`component-methods.md` §3.3): o bibliotecário propõe um conjunto coerente, e o usuário aprova o
conjunto.

`entidades_novas` existe para a entidade que nasce vazia — `propor_entidade` sem `propor_propriedade`
junto.

---

## 5. `EsquemaWiki`, depois da Q8

Mora em `aplicacao/`, é puro, não toca disco.

```python
@dataclass(frozen=True)
class PropriedadeSemente:
    titulo: str
    descricao: str


@dataclass(frozen=True)
class EntidadeSemente:
    titulo: str
    propriedades: tuple[PropriedadeSemente, ...] = ()


@dataclass(frozen=True)
class EsquemaWiki:
    entidades: tuple[EntidadeSemente, ...] = ()

    @staticmethod
    def vazio() -> "EsquemaWiki": ...

    @staticmethod
    def a_partir_do_formulario(dados: dict) -> "EsquemaWiki": ...
```

**O que saiu, e por quê:**

| Saiu | Motivo |
|---|---|
| `carregar_toml(caminho)` | Q8 — sem maquetes prontas, ficaria sem nenhum chamador. Assinatura preservada anotada em `component-methods.md` para a iteração que as trouxer de volta |
| `nome` | era o nome da maquete |
| `descricao` | C6 — a wiki não tem descrição |
| a validação *"ao menos uma entidade"* | revogada na Parte B.3 do FD de U1; `EsquemaWiki.vazio()` é estado válido |

**`EsquemaWiki` continua valendo a pena** mesmo sem maquete: é o que o formulário de criação produz
(US-09) e o que `ServicoDeAmbiente` materializa (US-08). A estrutura continua sendo definida pelo
dono do ambiente — digitando, em vez de escolhendo.

### O esquema é a primeira proposta

`ServicoDeAmbiente` (U4) converte o `EsquemaWiki` numa `PropostaWiki` e chama `escrever_proposta` —
não existe operação de materialização separada na porta. A semente é simplesmente a primeira
proposta, já aprovada por construção.

Consequência boa: `PortaWiki` fica com as **quatro** operações que `component-methods.md` §4.3 já
tinha, sem ganhar nenhuma. E `EsquemaWiki.vazio()` gera uma proposta vazia, que não escreve nada —
aí quem cria a raiz é `renderizar_index`, o que faz a wiki nascer mesmo sem entidade (US-08).

---

## 6. Erros

Espelha a lição que U2 aprendeu na geração de código: **driver não atravessa porta** (R-FD3-7).
Nenhum `OSError`, `PermissionError` ou `FileNotFoundError` escapa.

```
ErroDeWiki
├── LocalizadorNaoReconhecido    esquema diferente de "dados:"
├── CaminhoForaDaRaiz            PBT-U3-01 / RNF-10 / SECURITY-05
├── PaginaInexistente            ler uma pagina que nao existe
├── EntidadeInexistente          escrever propriedade sob entidade que nao existe
├── DescricaoObrigatoria         proposta com descricao vazia, recusada antes do disco
├── TituloInvalido               titulo cujo slug e vazio ou reservado pelo sistema
└── ArmazenamentoIndisponivel    falha de I/O traduzida; nunca o erro do sistema cru
```

`EntidadeInexistente` é o mesmo tipo de pré-condição que `AmbienteInexistente` foi em U2
(`RN-P-27`) — só que lá ela foi descoberta por um teste de propriedade durante a geração de código,
e aqui entra desenhada. A diferença entre as duas unidades é essa lição.

---

## 7. O que **não** existe, e por quê

Registro explícito, para que ninguém procure depois:

| Não existe | Decisão |
|---|---|
| `wiki.toml` ou qualquer arquivo de metadados na raiz | C6 — sem descrição de wiki nem de entidade, não sobrou o que guardar. O índice é projeção pura |
| Descrição de entidade | C6 |
| Descrição da wiki | C6 |
| Maquetes prontas | Q8 — adiadas para depois do software funcionar |
| `buscar` | Q13=A |
| `lint` | `FOR-12`; confirmado em C5=A |
| Pasta `raw/` | `FOR-12` |
| Seção de links quebrados no índice | Q3=A |
| Backlinks | Q3=A |
| Limite de tamanho na leitura | Q11=A |
| Trava de arquivo ou escrita atômica | Q7=A |
| Reconhecimento de página criada fora do app | Q2 — o critério 3 de U3 foi revogado |
