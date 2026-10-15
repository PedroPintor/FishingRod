# Business Rules — U3 `wiki`

**Fase:** CONSTRUCTION · **Unidade:** `U3 wiki` · **Data:** 2026-09-23

Identificadores `RN-W-nn` são **estáveis** e entram no nome dos testes (`test_rn_w_07_*`), como em
U1 e U2: quando um teste falha, o nome diz qual regra quebrou.

---

## Estrutura e nomes

| # | Regra | Origem |
|---|---|---|
| **RN-W-01** | A wiki tem **exatamente dois níveis**: entidade (pasta) e propriedade (arquivo `.md` dentro dela). Nenhum parâmetro da porta ou das ferramentas aceita um terceiro — a violação é irrepresentável, não validada. | ESC-17, critério 6 de U3 |
| **RN-W-02** | Só pasta na raiz é entidade; só `.md` dentro de entidade é propriedade. `index.md` na raiz não é propriedade. Qualquer outra coisa no disco é ignorada. | ESC-17, Q2 |
| **RN-W-03** | O nome no disco é o **slug do título, gerado uma vez na criação e nunca recalculado**. Mudar o título no frontmatter não renomeia o arquivo. | **C2=C** |
| **RN-W-04** | O slug é determinístico: minúsculas, decomposição Unicode com descarte de acentos, tudo que não for `a-z0-9` vira hífen, hifens consecutivos colapsam, hifens das bordas são aparados. `Dr. Marcelo & Cia` → `dr-marcelo-e-cia`. | Q5=A |
| **RN-W-05** | Título cujo slug sai **vazio** (só símbolos) ou é **reservado pelo sistema** (`con`, `prn`, `aux`, `nul`, `com1`–`com9`, `lpt1`–`lpt9`) é recusado com `TituloInvalido`. | Q5=A, portabilidade Windows |
| **RN-W-06** | Criar entidade que já existe é **no-op idempotente**, não erro. Duas propostas que criam `clientes` produzem uma pasta. | C4=A, Q6 |

> **RN-W-05 não é zelo excessivo.** O usuário roda em Windows, e `nul.md` é um arquivo que o sistema
> operacional se recusa a criar — a falha apareceria como `OSError` no meio de uma aprovação, longe
> da causa. Recusar no nome custa uma lista de treze palavras.

---

## Confinamento — o núcleo de segurança desta unidade

| # | Regra | Origem |
|---|---|---|
| **RN-W-07** | **Nenhum caminho gerado escreve ou lê fora da raiz da wiki.** A verificação tem três etapas, nesta ordem: (1) slug do título, que já elimina `/`, `\` e `..`; (2) montagem do caminho sob a raiz; (3) `resolve()` — que **resolve symlink** — e comparação com a raiz resolvida. Falha levanta `CaminhoForaDaRaiz`. | **RNF-10, SECURITY-05, RF-F14**, PBT-U3-01 |
| **RN-W-08** | A porta recebe **caminho lógico** (`clientes/dr-marcelo`) e **localizador** (`dados:wikis/<id>`). Nunca caminho de sistema, em nenhuma assinatura. | RNF-11, D-ARQ-08 |
| **RN-W-09** | Localizador com esquema diferente de `dados` levanta `LocalizadorNaoReconhecido`. Não assume, não adivinha. | Pergunta D, `RaizWiki.esquema()` |
| **RN-W-10** | A raiz de dados chega **pelo construtor** do adaptador, vinda do composition root (U9). O adaptador não a descobre e não importa o adaptador de persistência para isso. | R-FD3-1 |

> **A etapa 3 é a que fecha o buraco.** Sanitizar o nome não alcança symlink: o título pode ser
> perfeitamente inocente e o link já existir no disco, apontando para fora. É a comparação **depois**
> do `resolve()` que impede a escrita. As três etapas juntas é que satisfazem PBT-03 — nenhuma delas
> sozinha.

---

## Frontmatter

| # | Regra | Origem |
|---|---|---|
| **RN-W-11** | Frontmatter é um bloco delimitado por `---`, na **primeira linha** do arquivo. Chaves: `titulo` e `descricao`. | Q1=B |
| **RN-W-12** | **Só `descricao` é lida por código.** `titulo` é registro visual e nenhum caminho de execução depende dele. | C2=C |
| **RN-W-13** | O frontmatter é montado e interpretado **apenas pelo adaptador**. A proposta chega com `titulo`, `descricao` e `conteudo` em campos separados; nem U8 nem o agente escrevem `---`. | Pergunta 15D, C4=A |
| **RN-W-14** | `descricao` não vazia é **obrigatória** em toda página escrita pelo app. Proposta sem ela levanta `DescricaoObrigatoria` **antes de tocar o disco**. | Pergunta 15D, critério 2 de U3 |
| **RN-W-15** | O leitor de frontmatter é **tolerante**: linha `chave: valor`, valor é o resto da linha com aspas externas removidas; linha que não casa é ignorada; chave desconhecida é ignorada; bloco ausente ou não fechado devolve título e descrição vazios, **sem levantar**. | Q1=B |
| **RN-W-16** | O corpo pode conter uma linha `---` sem quebrar a releitura: só o **primeiro** bloco, começando na primeira linha, é frontmatter. | PBT-U3-07 |

> **RN-W-16 existe porque o corpo é markdown escrito por um agente**, e `---` é régua horizontal —
> vai aparecer. Um leitor que procurasse o primeiro `---` em qualquer posição partiria a página ao
> meio na segunda leitura.

---

## O índice

| # | Regra | Origem |
|---|---|---|
| **RN-W-17** | `index.md` é **projeção pura**: tudo que ele mostra é derivável do disco. Nenhuma informação vive só nele. Apagá-lo e renderizar de novo devolve o mesmo arquivo. | **C6**, critério 4 de U3 |
| **RN-W-18** | A gramática é fixa: `# Wiki — <nome>`, `## Entidades`, `### [[<entidade>]]` por entidade, e `- [[<entidade>/<propriedade>]]: <descricao>` por propriedade. | C1, C6, D2 |
| **RN-W-19** | Wiki sem entidade mostra `(vazio — ainda não tem nenhuma entidade)`. Entidade sem propriedade legível mostra `(sem propriedades)`. | Q9=A, Parte B.3 de U1 |
| **RN-W-20** | Página **sem `descricao` legível e não vazia é ignorada** pelo índice, e o arquivo **não é tocado**. | Q2, E1 |
| **RN-W-21** | A ordem é **alfabética do slug**, em entidades e em propriedades. Não é ordem de criação, e não depende da ordem do filesystem. | PBT-U3-02 |
| **RN-W-22** | O `index.md` é escrito **só** por `renderizar_index`. Nenhum agente o escreve, e nenhuma ferramenta o expõe para escrita. | critério 4 de U3, CQ1=A |
| **RN-W-23** | A renderização é **inteiramente determinística**: nenhum LLM no laço. | CQ1=A |
| **RN-W-24** | O nome do ambiente do cabeçalho chega **por parâmetro** de `renderizar_index`. O adaptador não conhece `Ambiente` nem a persistência. | emenda a `component-methods.md` §4.3 |
| **RN-W-25** | `renderizar_index` **cria a raiz** se ela não existir. É o que faz a wiki nascer mesmo com esquema vazio. | US-08, Parte B.3 de U1 |

> **RN-W-17 é o que a C6 comprou.** Enquanto havia descrição de wiki e de entidade, essas duas linhas
> não tinham onde morar a não ser no próprio índice — e aí ele deixaria de ser projeção e viraria
> fonte parcial de si mesmo, com perda definitiva se fosse corrompido. Removê-las devolveu a
> propriedade mais forte do desenho, e de quebra dispensou um arquivo de metadados.

---

## Escrita

| # | Regra | Origem |
|---|---|---|
| **RN-W-26** | `escrever_proposta` grava o **conteúdo completo** de cada página, substituindo o arquivo. Não anexa, não mescla. | **C4=A** |
| **RN-W-27** | A porta **não verifica** se o autor preservou o que havia. Pode haver perda de conteúdo, e a rede de proteção é a **aprovação humana** da proposta — humana, não técnica. | C4=A, US-14 |
| **RN-W-28** | Escrever propriedade sob entidade que não existe e não está em `entidades_novas` levanta `EntidadeInexistente`. | espelha `RN-P-27` de U2 |
| **RN-W-29** | `escrever_proposta` cria **primeiro** as entidades, **depois** as páginas. Não é atômica: falha no meio deixa o que já foi escrito. `renderizar_index`, chamada em seguida, reflete o que aterrissou. | Q7=A |
| **RN-W-30** | Sem trava e sem escrita atômica. Um escritor por processo; edição externa simultânea é risco declarado. | **Q7=A** |
| **RN-W-31** | Todo arquivo é escrito em **UTF-8** com quebra de linha **LF explícita**, nunca a do sistema. | R-FD3-4 |
| **RN-W-32** | Não há limite de tamanho em leitura nem em escrita de página. | Q11=A |

> **RN-W-29 é honesta em vez de segura.** A alternativa — escrever tudo num diretório temporário e
> promover — foi recusada na Q7. O desfecho ruim é uma proposta pela metade no disco, que o índice
> mostra tal como está. Como cada página é escrita inteira (RN-W-26), nenhuma página fica truncada;
> o que pode faltar é uma página inteira da proposta.

---

## Links

| # | Regra | Origem |
|---|---|---|
| **RN-W-33** | Link é sempre **qualificado**: `[[entidade/propriedade]]`. Nome simples não é resolvido. | **Q4=A**, C3=A |
| **RN-W-34** | A validação de link acontece **no momento da escrita** e é responsabilidade de **U8** (`ServicoBibliotecario.aprovar`). U3 oferece `listar` como o meio de checar existência. | `component-methods.md` §3.3, FOR-12 |
| **RN-W-35** | Depois de escrito, um link que quebre (alvo renomeado ou removido) **não é detectado por nada** nesta iteração: não há seção de links quebrados (Q3=A) e não há `lint` (C5=A). Risco aceito. | E4, FOR-12 |

---

## Vocabulário da porta

| # | Regra | Origem |
|---|---|---|
| **RN-W-36** | Nenhuma assinatura de `PortaWiki` menciona `Path`, `open`, extensão de arquivo ou erro do sistema operacional. Toda falha é exceção nomeada da porta. Se mencionar, a abstração é decorativa. | **D-ARQ-08**, R-FD3-7, espelha `RN-P-16` |
| **RN-W-37** | `listar` devolve **nomes**, e só. Descrição vem do índice. Duas fontes para a mesma informação seriam duas coisas para manter sincronizadas. | R-FD3-5 |

---

## Nota de conformidade — RNF-14 relaxada nesta iteração

> **Risco aceito, decidido pelo usuário em 2026-09-22 (Q10), sem objeção à redação em 2026-09-23.**
>
> `RNF-14` dizia que a wiki é **entrada não confiável** para o agente e que a defesa valia *"na
> leitura (U3) e no contexto do agente (U8)"*. Nesta iteração **a parte de U3 não existe**:
> `ConteudoPagina` devolve caminho, título, descrição e conteúdo, sem marca de proveniência, e o
> embrulho *"isto é dado, não instrução"* fica inteiramente com U8.
>
> **Justificativa do usuário**: no máximo dois usuários próximos, acompanhados por ele, e o conteúdo
> da wiki é do próprio usuário; o software precisa nascer antes de tratar esse detalhe.
>
> **O que permanece, e é a maior parte da defesa**: o bibliotecário não recebe ferramenta nativa de
> escrita (`tools=[]`, medido pelo spike), toda escrita passa por aprovação humana (US-14), e o
> orquestrador não recebe ferramenta de wiki nenhuma (Q14=X). Essas três são estruturais e
> continuam inteiras.
>
> **Condição de reabertura, e é dura**: no momento em que a wiki receber conteúdo que **não veio do
> próprio usuário** — importação, compartilhamento entre ambientes, pasta `raw/`, wiki em nuvem —
> isto volta a ser bloqueante para `security-baseline`.
