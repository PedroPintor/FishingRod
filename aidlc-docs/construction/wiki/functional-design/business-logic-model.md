# Business Logic Model — U3 `wiki`

**Fase:** CONSTRUCTION · **Unidade:** `U3 wiki` · **Data:** 2026-09-23

Semântica de cada operação da porta, o algoritmo de renderização do índice, e as propriedades
`PBT-U3-nn`.

---

## 1. A porta, como fica

```python
class PortaWiki(Protocol):
    async def listar(self, localizador: str, caminho: str) -> list[str]: ...
    async def ler(self, localizador: str, caminho_pagina: str) -> ConteudoPagina: ...
    async def escrever_proposta(self, localizador: str, proposta: PropostaWiki) -> None: ...
    async def renderizar_index(self, localizador: str, nome: str) -> None: ...
```

**Quatro operações, as mesmas de `component-methods.md` §4.3.** A única mudança é o parâmetro `nome`
em `renderizar_index` — o cabeçalho do índice traz o nome do ambiente, e o adaptador não pode
descobri-lo sozinho sem conhecer `Ambiente` ou a persistência (RN-W-24). Quem chama é
`ServicoDeAmbiente` (U4), que tem o ambiente em mãos.

`buscar` continua fora (Q13=A). Nenhuma operação de `lint` foi acrescentada (C5=A).

---

## 2. `listar(localizador, caminho) -> list[str]`

| | |
|---|---|
| **Entrada** | localizador; `caminho` vazio para entidades, ou o slug de uma entidade para suas propriedades |
| **Saída** | nomes (slugs), em ordem alfabética |
| **Erros** | `LocalizadorNaoReconhecido`, `CaminhoForaDaRaiz`, `EntidadeInexistente` |

- `caminho` vazio → subdiretórios da raiz. `index.md` e qualquer arquivo solto ficam de fora
  (RN-W-02).
- `caminho` com o slug de uma entidade → arquivos `.md` dentro dela, **sem a extensão**.
- Raiz inexistente devolve lista vazia; não levanta. A wiki ainda não foi renderizada, e isso não é
  erro.
- Devolve **nome, e só** (RN-W-37). Quem quer descrição lê o índice.

**Para que serve, na prática**: é como U8 checa a existência do alvo de um `[[link]]` antes de
aprovar (RN-W-34). Não há operação dedicada a isso porque `listar` já responde.

---

## 3. `ler(localizador, caminho_pagina) -> ConteudoPagina`

| | |
|---|---|
| **Entrada** | localizador; caminho lógico qualificado, `clientes/dr-marcelo`, sem `.md` |
| **Saída** | `ConteudoPagina(caminho, titulo, descricao, conteudo)` |
| **Erros** | `LocalizadorNaoReconhecido`, `CaminhoForaDaRaiz`, `PaginaInexistente`, `ArmazenamentoIndisponivel` |

**Pré-condição**: o caminho tem exatamente dois segmentos. Três ou mais é `CaminhoForaDaRaiz` — não
existe nível 3 (RN-W-01).

**Pós-condição**: `conteudo` é o corpo **sem** o bloco de frontmatter. `titulo` e `descricao` vêm do
frontmatter; ausentes, vêm vazios, e a leitura **não falha** (RN-W-15) — é leitura, não escrita, e
recusar uma página legível por causa de metadado faltando trocaria um defeito visível por um
inacessível.

**Sem limite de tamanho** (Q11=A). Uma página de 2 MB é lida inteira, e a falha, se houver, aparece
como erro do provedor lá adiante. Custo declarado.

---

## 4. `escrever_proposta(localizador, proposta) -> None`

| | |
|---|---|
| **Entrada** | localizador; `PropostaWiki` com entidades novas e páginas |
| **Saída** | nada |
| **Erros** | `LocalizadorNaoReconhecido`, `CaminhoForaDaRaiz`, `TituloInvalido`, `DescricaoObrigatoria`, `EntidadeInexistente`, `ArmazenamentoIndisponivel` |

**Chamada só por `ServicoBibliotecario.aprovar`** (U8), depois da aprovação humana — nunca em
resposta direta a uma chamada de tool do agente (Pergunta 9A).

### Ordem de execução

```
1. validar a proposta INTEIRA, antes de tocar o disco:
   - todo titulo produz slug valido            -> TituloInvalido
   - toda pagina tem descricao nao vazia       -> DescricaoObrigatoria
   - toda entidade referida existe ou esta em entidades_novas
                                               -> EntidadeInexistente
   - todo caminho resolvido cai sob a raiz     -> CaminhoForaDaRaiz
2. criar as entidades de entidades_novas (mkdir; existente e no-op)
3. escrever cada pagina: frontmatter + corpo, arquivo inteiro
```

**O passo 1 é o que torna a não-atomicidade suportável.** Tudo que é verificável sem tocar o disco é
verificado antes; o que pode falhar no passo 3 é I/O real, que nenhuma ordem de execução evita. Se
falhar no meio, o que já foi escrito fica (RN-W-29), e o índice, renderizado em seguida, mostra
exatamente o que aterrissou.

### Cada página é escrita inteira

`conteudo` é a página completa (RN-W-26, C4=A). O bibliotecário leu a página, decidiu o texto final
— incluindo o que virou `~~riscado~~` — e devolve o todo. O adaptador monta:

```
---
titulo: <PaginaProposta.titulo>
descricao: <PaginaProposta.descricao>
---

<PaginaProposta.conteudo>
```

**A porta não compara com o que havia.** Se o bibliotecário apagou metade da página sem querer, ela
some — a rede é a aprovação humana (RN-W-27). É a mesma natureza da rede que já protege a qualidade
da descrição, registrada como risco aceito desde o critério de pronto de U3.

### Escrever numa página que já existe é normal

Não há conflito a resolver, e este é o ponto que a Q6 corrigiu no desenho: a página nasce com uma
descrição, que lhe dá sentido; informação que combina com essa descrição vai para lá; informação
que ficou velha é marcada `~~assim~~` e explicada, nunca apagada. Isso é trabalho de rotina do
bibliotecário — `ingest` — e não um caso excepcional.

O **formato** da marcação (dois tis, GFM) é convenção registrada aqui; **quando** e **o quê** marcar
é decisão do bibliotecário, e portanto de U8.

---

## 5. `renderizar_index(localizador, nome) -> None`

| | |
|---|---|
| **Entrada** | localizador; nome do ambiente, para o cabeçalho |
| **Saída** | nada; `index.md` reescrito por inteiro |
| **Erros** | `LocalizadorNaoReconhecido`, `ArmazenamentoIndisponivel` |

### Algoritmo

```
1. raiz = resolver(localizador)
2. se raiz nao existe -> criar (0o700 em POSIX, como o diretorio de dados de U2)
3. entidades = subdiretorios de raiz, ordenados por slug
4. para cada entidade:
     paginas = arquivos *.md da entidade, ordenados por slug
     para cada pagina: ler o frontmatter
       - descricao vazia ou ilegivel -> IGNORAR a pagina, sem tocar no arquivo
5. montar o texto conforme a gramatica de RN-W-18
6. escrever index.md (UTF-8, LF)
```

**Nenhum LLM em passo nenhum** (CQ1=A). Nenhuma leitura do `index.md` anterior — ele é saída, nunca
entrada (RN-W-17).

### Quem chama, e quando

| Momento | Quem | Por quê |
|---|---|---|
| Criação do ambiente | `ServicoDeAmbiente` (U4) | US-08 — a wiki nasce junto, mesmo vazia. É este passo que cria a raiz |
| Após cada proposta aprovada | `ServicoBibliotecario` (U8) | o índice é o único caminho até o conteúdo; página fora dele é inalcançável |

### Idempotência

Renderizar duas vezes seguidas produz **bytes idênticos**, e o resultado não depende da ordem em que
as páginas foram criadas nem da ordem que o filesystem devolve (RN-W-21). É `PBT-U3-02`, e é o que
permite chamar a renderização sem medo depois de qualquer escrita.

---

## 6. `EsquemaWiki` vira a primeira proposta

Não há operação de materialização na porta. `ServicoDeAmbiente` (U4) faz:

```
proposta = PropostaWiki(
    entidades_novas = tuple(e.titulo for e in esquema.entidades),
    paginas = tuple(
        PaginaProposta(entidade=e.titulo, titulo=p.titulo,
                       descricao=p.descricao, conteudo="")
        for e in esquema.entidades for p in e.propriedades
    ),
)
await wiki.escrever_proposta(raiz.localizador, proposta)
await wiki.renderizar_index(raiz.localizador, ambiente.nome)
```

A semente de propriedade nasce **com descrição e sem conteúdo** — que é exatamente o estado certo:
a descrição é o que o índice usa para recuperação, e o conteúdo vem do trabalho real, não de texto
que o produto inventou (Q8, alternativa D).

Com `EsquemaWiki.vazio()`, a proposta é vazia, nada é escrito, e `renderizar_index` cria a raiz e
escreve o índice com `(vazio — ainda não tem nenhuma entidade)`. **É assim que a Parte B.3 de U1 se
cumpre**: índice vazio é estado válido, e legível.

---

## 7. Propriedades `PBT-U3-nn`

`property-based-testing` está ligada em modo **Full**. Estas são as propriedades desta unidade; a
especificação das estratégias `hypothesis` é de NFR Requirements/Design.

| # | Propriedade | Origem |
|---|---|---|
| **PBT-U3-01** | **Confinamento.** Para qualquer título gerado — incluindo `..`, `../..`, `/etc/passwd`, `C:\Windows`, `~`, separadores repetidos, nomes reservados e Unicode hostil — nenhum caminho produzido por escrita ou leitura resolve fora da raiz. É `PBT-03` de Application Design, atribuída a esta unidade | RNF-10, SECURITY-05, RF-F14 |
| **PBT-U3-02** | **Índice determinístico e idempotente.** Renderizar duas vezes produz bytes idênticos; o resultado independe da ordem de criação das páginas | RN-W-21, RN-W-17 |
| **PBT-U3-03** | **Round-trip de página.** Para qualquer título, descrição e corpo, `ler(escrever(p))` devolve os três iguais | RN-W-13 |
| **PBT-U3-04** | **O índice lista exatamente as páginas escritas pelo app** — nem mais, nem menos, para qualquer conjunto de propostas aplicadas | RN-W-20, critério 1 de U3 |
| **PBT-U3-05** | **Slug idempotente e determinístico**: `slug(slug(x)) == slug(x)`, e o mesmo título sempre dá o mesmo slug | RN-W-04 |
| **PBT-U3-06** | **Dois níveis irrepresentáveis.** Nenhuma entrada, por qualquer operação, produz arquivo com profundidade maior que 2 sob a raiz | RN-W-01, critério 6 de U3 |
| **PBT-U3-07** | **Corpo com `---` sobrevive.** Para qualquer corpo, inclusive contendo linhas `---`, a releitura devolve o corpo intacto e o frontmatter correto | RN-W-16 |

> **PBT-U3-07 não é caso de borda.** O corpo é markdown escrito por um agente, e `---` é régua
> horizontal — vai aparecer. Um leitor ingênuo partiria a página ao meio na segunda leitura, e o
> defeito só apareceria depois de a wiki já ter conteúdo real.

---

## 8. Rastreio

| Origem | Onde se cumpre |
|---|---|
| **US-08** — ambiente novo nasce com wiki, mesmo vazia | §6 + RN-W-25 + RN-W-19 |
| **US-09** — a estrutura é do dono | `EsquemaWiki.a_partir_do_formulario` + §6; nenhuma entidade é hardcodada |
| **RF-F13** — diretório markdown com entidades, propriedades e `index.md` | `domain-entities.md` §1 |
| **RF-F14** — escrita confinada à raiz | RN-W-07 |
| **RF-F15** — ambiente nasce com wiki materializada de esquema plugável | §6 |
| **RNF-10** — confinamento é gate de segurança e de teste | RN-W-07 + PBT-U3-01 |
| **RNF-11** — caminho lógico, nunca absoluto | RN-W-08, RN-W-10 |
| **RNF-12** — o banco não guarda conteúdo nem índice de wiki | já garantido por `RN-P-15` (U2); nada aqui grava no banco |
| **RNF-14** — entrada não confiável | **relaxada nesta iteração**; risco aceito e condição de reabertura em `business-rules.md` |
| **ESC-17** — dois níveis, arquivo é a fonte da verdade | RN-W-01, RN-W-02, §1 de `domain-entities.md` |
| **ESC-19** — esquema plugável como semente | §6 |
| **ESC-20** — acesso só pelas ferramentas do bibliotecário | as ferramentas são de U8; esta unidade não expõe nada ao modelo |
| **CQ1=A** — portão do índice só determinístico | RN-W-23 |
| **Critérios de pronto de U3** | 1 → PBT-U3-04 (emendado por E1) · 2 → RN-W-14 · ~~3~~ **revogado** (E1) · 4 → RN-W-22 · 5 → PBT-U3-01 · 6 → PBT-U3-06 |
