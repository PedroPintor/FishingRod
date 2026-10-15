# NFR Design Plan — U3 `wiki`

**Fase:** CONSTRUCTION · **Unidade:** `U3 wiki` · **Portão 3 de 4** · **Data:** 2026-09-23
**Entrada:** `construction/wiki/nfr-requirements/` (aprovado em 2026-09-23T16:00:00Z)

O portão 1 fixou **comportamento** (37 regras, 4 operações, 7 erros). O portão 2 fixou **alvos e
tecnologia** (`NFR-W-01..20`, `TS-W-01..08`). Este estágio decide **forma**: onde as coisas moram,
com que assinatura, em quantos módulos, e qual padrão garante que uma regra não possa ser esquecida.

**Continua sem escrever código** — isso é o portão 4.

> Enquanto houver `[Answer]:` vazio abaixo, **nenhum artefato de NFR Design é gerado**.

---

## 1. Passos

- [x] **1.** Ler `nfr-requirements.md` (20 requisitos) e `tech-stack-decisions.md` (8 decisões)
- [x] **2.** Reler o Functional Design: contrato de 4 operações, 37 regras `RN-W-nn`, 7 propriedades `PBT-U3-nn`
- [x] **3.** Inspecionar a árvore existente (`src/fishingrod/`, `tests/`) para saber o que U0/U1/U2 já deixaram pronto
- [x] **4.** Registrar os dois achados da §2 e escrever este plano com as perguntas
- [x] **5.** Respostas coletadas em 2026-09-23. **Nenhuma ambiguidade** — as 9 vieram fechadas. **Q5=B foi contra a recomendacao, com argumento**, e o argumento venceu: as duas leituras tem politicas de tolerancia diferentes por decisao do Functional Design (`RN-W-15`), e um parser compartilhado as obrigaria a compartilhar a politica tambem. Consequencia aceita e registrada em `DP-W-06`
- [x] **6.** Gerado `construction/wiki/nfr-design/nfr-design-patterns.md` (12 padroes `DP-W-01..12`)
- [x] **7.** Gerado `construction/wiki/nfr-design/logical-components.md` (8 modulos em `src/`, 7 em `tests/`, matriz sem ciclo)
- [x] **8.** Checkboxes marcados, `audit.md` e `aidlc-state.md` atualizados
- [x] **9.** Portao 3/4 apresentado em 2026-09-23

---

## 2. Dois achados, antes das perguntas

### Achado 1 — `pasta_de_dados()` está no lugar errado para U3

Ela mora em `src/fishingrod/adaptadores/persistencia/localizacao.py`, e o docstring **já antecipa
esta unidade**:

> *"É também a raiz que resolve o esquema `dados:` de RaizWiki: U3 materializa `wikis/<id_ambiente>/`
> debaixo desta pasta. Anotado aqui para não ser redescoberto lá."*

O problema é que `R-FD3-1` diz, com todas as letras, que **nenhum adaptador importa outro adaptador**.
A anotação foi correta e a casa não. Isso não é ambiguidade: é uma decisão de forma que este estágio
precisa tomar, e é a **Q3**.

### Achado 2 — o slug idempotente já resolve "título ou slug?", e isso não precisa virar pergunta

`PaginaProposta.entidade` é documentado como *"título da entidade; o slug é derivado dele"*. Mas o
agente que acabou de ler o índice viu `[[clientes/dr-marcelo]]` — **slugs**, não títulos. Ao propor
uma propriedade nova em `clientes`, ele vai passar `"clientes"`, que é o slug.

Isso funciona **por construção**, e a razão tem nome: `PBT-U3-05` exige `slug(slug(x)) == slug(x)`.
Passar o slug onde se espera o título dá o mesmo resultado. Nenhuma decisão é necessária; fica
registrado aqui para que ninguém "conserte" isso depois achando que é confusão de vocabulário.

O que **não** é resolvido por isso, e vira a `Q2`: quem mais, além do adaptador, precisa calcular
slug — e portanto onde a função mora.

---

## 3. Perguntas

### Q1 — Em quantos módulos o adaptador se parte? *(Logical Components)*

U2 virou 4 arquivos (`localizacao`, `esquema`, `mapeamento`, `repositorio_sqlite` — 930 linhas).
U3 é menor, mas tem quatro assuntos bem separáveis: caminhos e confinamento, frontmatter,
renderização do índice, e a classe que implementa a porta.

A) **Quatro módulos** em `adaptadores/wiki/`:
   `caminhos.py` (slug + `resolver_sob`) · `frontmatter.py` (montar, ler cabeçalho, ler página
   inteira) · `indice.py` (a gramática de `RN-W-18` e a renderização) · `wiki_de_arquivos.py` (a
   classe, o `to_thread`, a tradução de erro).
   *Ganho*: `caminhos.py` fica sendo **o** arquivo de segurança da unidade — pequeno, sem I/O
   além do `resolve()`, e alvo direto de `PBT-U3-01` e `PBT-U3-05`. `indice.py` fica puro o
   bastante para ser testado sem disco.
   *Custo*: quatro arquivos para ~600 linhas.
B) **Dois módulos**: `caminhos.py` e `wiki_de_arquivos.py` (tudo o mais junto).
   *Ganho*: menos navegação. *Custo*: a gramática do índice e o parsing de frontmatter ficam
   dentro da classe, e só se testam através dela.
C) **Um módulo só.** *Custo*: o código de confinamento deixa de ser visivelmente isolável.

**Recomendação: A.** O argumento decisivo não é tamanho, é revisão: `RN-W-07` é a regra mais
importante da unidade, e quero poder abrir **um** arquivo curto e ver a verificação inteira.

[Answer]: A


---

### Q2 — Onde mora a função de slug? *(Logical Components / Security)*

Parece detalhe de adaptador — é ele que nomeia arquivos. Mas o slug produz o **caminho lógico**
(`clientes/dr-marcelo`), e caminho lógico é **vocabulário da porta** (`RN-W-08`): é o que
`listar` devolve, o que `ler` recebe e o que aparece dentro de `[[...]]` no índice.

A) **No adaptador** (`adaptadores/wiki/caminhos.py`). *Ganho*: onde o I/O está; ninguém fora
   precisa dele hoje. *Custo*: se U8 algum dia precisar prever o caminho de algo que ainda não
   existe — para montar um `[[link]]` antes de escrever a página —, importaria de `adaptadores/`,
   o que a arquitetura proíbe. Aí a função é copiada, e passam a existir dois slugs.
B) **Na aplicação**, ao lado da porta (`aplicacao/portas/wiki.py` ou `aplicacao/caminho_wiki.py`),
   e o adaptador importa dali. *Ganho*: uma implementação só, do lado que qualquer unidade pode
   importar; a regra `RN-W-04` fica onde o vocabulário dela já está.
   *Custo*: a porta ganha uma função, não só tipos — deixa de ser puramente declarativa.
C) **No domínio**, junto de `RaizWiki`. *Custo*: o slug é convenção de nomeação da wiki, não regra
   de negócio; o domínio não deveria saber que existe arquivo.

**Recomendação: B.** O teste é simples: se dois lugares podem precisar calcular o mesmo caminho, a
função não pode morar no lado que só um deles enxerga. E `PBT-U3-05` é uma propriedade sobre o
**caminho lógico**, não sobre o disco — ela roda sem tocar em arquivo nenhum.

[Answer]: B

---

### Q3 — Onde `pasta_de_dados()` passa a morar? *(Logical Components)* — ver Achado 1

A) **Mover para `aplicacao/localizacao.py`** (ou `fishingrod/localizacao.py`), e os **dois**
   adaptadores importam de lá. *Ganho*: uma função, uma verdade; `R-FD3-1` fica respeitada sem
   truque. *Custo*: mexe em U2, que está aprovada e com 84 testes passando — emenda em
   `DP-P-05`/`TS-P-*` e um import a trocar.
B) **Deixar onde está e o composition root (U9) resolve**: U9 importa de
   `adaptadores/persistencia/localizacao.py`, monta o `Path` da raiz da wiki e passa pelo
   construtor. O adaptador de wiki nunca importa nada de persistência.
   *Ganho*: **zero mudança em U2**; `R-FD3-1` já dizia que a raiz chega pelo construtor.
   *Custo*: a função de localização continua num pacote cujo nome não a descreve mais — dívida de
   organização, visível mas inofensiva.
C) **Duplicar** as ~12 linhas no adaptador de wiki. *Custo*: duas definições de onde os dados do
   usuário moram, que vão divergir no dia em que uma mudar.

**Recomendação: B nesta iteração**, com a dívida registrada por escrito. O ganho de (A) é
organização; o custo é tocar numa unidade fechada e aprovada para obter exatamente o mesmo
comportamento em tempo de execução. Se você preferir a casa certa agora, é (A) e eu emendo U2 —
diga, porque isso é escolha sua, não minha.

[Answer]: B

---

### Q4 — O confinamento é um ponto único, ou uma verificação em cada método? *(Security Patterns)*

`NFR-W-05` exige a verificação em **cada caminho de arquivo**. A questão é como garantir que um
método futuro não a esqueça.

A) **Ponto único obrigatório**: uma função `resolver_sob(raiz: Path, caminho_logico: str) -> Path`
   é o **único** lugar do adaptador que produz um `Path` de arquivo. Nenhum método monta caminho
   por conta própria; quem precisa de um caminho, chama. *Ganho*: a regra passa a ser estrutural —
   para violá-la é preciso escrever `raiz / algo` à mão, o que salta aos olhos em revisão e pode
   virar teste de inspeção. *Custo*: nenhum relevante.
B) **Verificação no início de cada método público.** *Custo*: quatro cópias hoje, e a quinta
   operação que alguém acrescentar em 2027 é a que vai faltar.
C) **Decorador** que intercepta e valida. *Custo*: esconde onde a validação acontece, e o
   caminho ainda precisa ser montado por alguém antes de ser validado.

**Recomendação: A.** É o mesmo raciocínio que fez U2 escolher conexão viva em vez de conexão por
operação: ligar o PRAGMA uma vez para que não haja preâmbulo a esquecer.

[Answer]: A

---

### Q5 — Um parser de frontmatter com dois modos, ou dois leitores? *(Performance Patterns)*

`NFR-W-01` lê só o cabeçalho (teto de 64 linhas); `ler` precisa do cabeçalho **e** do corpo.
`NFR-W-20` exige que os dois concordem para toda entrada.

A) **Um parser sobre um iterador de linhas**, e dois chamadores: a renderização passa um iterador
   que para cedo; `ler` passa o arquivo inteiro. *Ganho*: a lógica de `RN-W-11/15/16` existe **uma
   vez**; `NFR-W-20` fica verdadeiro por construção, e o teste que o verifica passa a ser
   confirmação, não rede. *Custo*: a função precisa ser escrita em cima de iterador, não de string.
B) **Duas funções independentes**, `ler_cabecalho` e `ler_pagina`. *Ganho*: cada uma é direta.
   *Custo*: duas implementações da mesma gramática — exatamente o risco 2 do portão anterior.
C) **Sempre ler o arquivo inteiro** e fatiar na memória, ignorando `NFR-W-01`. *Custo*: revoga uma
   decisão sua de um portão já aprovado.

**Recomendação: A.** Transforma o risco 2 (dois caminhos podem divergir) em impossibilidade, em vez
de deixá-lo para os testes pegarem.

[Answer]: B - acho que temos que seguir com a B mesmo. o risco que vc falou de dois caminhos podem divergir aqui eu acho que nao se aplica, pois a funcao de ler o cabeçalho nao vai mudar, vai ter um regra fixa sempre e vai manter o funcionamento de acordo com o frontmatter, so mudaria se o frontmatter mudar, ai talvez a funcao ler_cabecalho poderia se adaptar. e a funcao ler_pagina fica separada assim pode ser otimizada do seu proprio jeito para ler melhor a pagina. acredito que separando seria melhor pois as duas funcoes podem ser otimizadas e apresentar comportamentos diferentes de verificacoes.

---

### Q6 — Como o erro do sistema operacional é traduzido? *(Resilience Patterns)*

`NFR-W-13` proíbe `OSError` de atravessar a porta. Falta a forma.

A) **Um context manager** `traduzindo_erros(caminho_logico)` que envolve todo bloco de I/O e mapeia
   `FileNotFoundError` → `PaginaInexistente`/`EntidadeInexistente`, `PermissionError` e o resto de
   `OSError` → `ArmazenamentoIndisponivel`. *Ganho*: um só lugar conhece `errno`; a mensagem sai com
   o **caminho lógico**, nunca o absoluto (`NFR-W-17`). *Custo*: o mapeamento de
   `FileNotFoundError` depende do contexto (página ou entidade), então o context manager recebe
   qual erro usar.
B) **`try/except` explícito em cada método.** *Ganho*: o leitor vê o mapeamento onde ele acontece.
   *Custo*: quatro a oito blocos repetidos, e o esquecimento é silencioso — o `OSError` sobe cru e
   só aparece na tela do usuário.
C) **Capturar no limite da classe**, um `except OSError` envolvendo cada método público.
   *Custo*: perde a distinção entre "não existe" e "não deu para ler", que são erros diferentes na
   hierarquia já aprovada.

**Recomendação: A.**

[Answer]: A

---

### Q7 — A escrita atômica é um helper geral ou específica do índice? *(Resilience Patterns)*

`NFR-W-11` manda publicar o `index.md` por temporário + `os.replace`; `NFR-W-12` mantém as páginas
escritas direto (Q7=A do Functional Design).

A) **Helper geral `escrever_atomico(caminho, texto)`**, usado **hoje só** pelo índice. As páginas
   usam a escrita direta. *Ganho*: o dia em que você quiser revisar Q7=A, a peça já existe e a
   mudança é de uma linha por chamada. *Custo*: uma função com um chamador só, o que sempre levanta
   a pergunta "por que isto é genérico?" — respondida por um comentário.
B) **Inline dentro de `renderizar_index`.** *Ganho*: nenhuma generalidade especulativa.
   *Custo*: se a decisão mudar, o código se repete ou se refatora.
C) **Atômico para tudo**, índice e páginas. *Custo*: **revoga Q7=A**, que é decisão sua de um
   portão aprovado. Não faço sem você pedir.

**Recomendação: A**, com o comentário explicando que a assimetria é deliberada e apontando para
`NFR-W-11`/`NFR-W-12`. A alternativa (C) eu registro como disponível, não como recomendada.

[Answer]: A

---

### Q8 — O teste de 500 páginas fica no repositório? *(Scalability / Performance Patterns)*

`NFR-W-02` fixou ≤ 500 ms para uma wiki de 500 páginas, "teste lento e pulável, não portão de
merge". `NFR-W-04` diz que a escala real projetada é de **dezenas**.

A) **Fica, marcado `@pytest.mark.lento`**, fora da execução padrão (`-m "not lento"` no
   `pyproject.toml`), rodado quando alguém quiser medir. *Ganho*: o sensor existe e o número está
   escrito em código, não só em documento. *Custo*: uma marca nova no `pyproject.toml` e um teste
   que quase nunca roda — e teste que não roda apodrece.
B) **Fica e roda sempre.** Gerar 500 arquivos em `tmp_path` custa poucos décimos de segundo.
   *Ganho*: nunca apodrece; a regressão aparece no dia em que entra. *Custo*: a suíte inteira fica
   alguns décimos mais lenta, sempre.
C) **Não fica.** O alvo é documento, e mede-se quando houver conteúdo real. *Custo*: `NFR-W-02`
   vira afirmação não verificada.

**Recomendação: B.** U2 escolheu (A) para o teste equivalente, e lá havia motivo: gerar 5.000
anotações num banco é caro. Aqui são 500 arquivos vazios numa pasta temporária — o custo não
justifica o risco de o único sensor de desempenho da unidade nunca rodar.

[Answer]: B

---

### Q9 — Nomes *(Logical Components)*

Vocabulário fica, então prefiro perguntar do que decidir sozinho. U2 chamou a classe
`RepositorioSQLite` e o pacote `adaptadores/persistencia/`.

A) Pacote `adaptadores/wiki/`, classe **`WikiDeArquivos`**.
B) Pacote `adaptadores/wiki/`, classe **`WikiEmArquivos`**.
C) Pacote `adaptadores/wiki_filesystem/`, classe **`WikiFilesystem`**.

**Recomendação: A.** `WikiDeArquivos` diz do que ela é feita, que é a mesma forma de
`RepositorioSQLite` (o quê + a tecnologia), e mantém o português consistente do projeto.

[Answer]: A

---

## 4. Reconciliações declaradas

Aplico **sem pergunta**, a menos que você objete.

| # | Reconciliação |
|---|---|
| **R-ND3-1** | **O `to_thread` fica no limite da classe.** Cada método público é `async def` e faz `await asyncio.to_thread(self._x_sincrono, ...)`; **todo** o resto — caminhos, frontmatter, índice — é síncrono e testável sem `asyncio`. É o que cumpre `NFR-W-03` e o que mantém `PBT-U3-02/03/05` livres do helper `executar(coro)` |
| **R-ND3-2** | **Testes em `tests/wiki/`**, espelhando `tests/persistencia/`: `estrategias.py` (geradores, incluindo o **alfabeto hostil** de títulos, compartilhado entre `PBT-U3-01` e `PBT-U3-05`), `test_caminhos.py`, `test_frontmatter.py`, `test_indice.py`, `test_wiki_de_arquivos.py`, `test_propriedades.py`. Sem `tests/dobles/wiki.py` (`NFR-W-19`) |
| **R-ND3-3** | **O perfil de Hypothesis já existente em `tests/conftest.py` (`deadline=None`) cobre esta unidade** sem mudança — o motivo dado lá (I/O real transforma o prazo padrão em falha intermitente) vale igual aqui |
| **R-ND3-4** | **`aplicacao/portas/wiki.py` é o único arquivo de U3 que outras unidades importam.** U4, U8 e o composition root de U9 dependem dali — nunca de `adaptadores/wiki/`. É a mesma regra que `DP-P-11` fixou para U2, e ela está escrita no topo de `portas/persistencia.py` |

---

## 5. Categorias obrigatórias — onde cada uma é tratada

| Categoria | Onde |
|---|---|
| **Resilience Patterns** | Q6 (tradução de erro), Q7 (escrita atômica). `resiliency-baseline` continua **N/A** — nenhum retry, circuit breaker ou bulkhead, porque não há chamada remota |
| **Scalability Patterns** | Q8, mais `NFR-W-01`/`NFR-W-04` já fixados |
| **Performance Patterns** | Q5 (parser único), Q8, `R-ND3-1` |
| **Security Patterns** | Q2 (onde o slug mora), Q4 (ponto único de confinamento), Q1-A (isolar o arquivo de segurança) |
| **Logical Components** | Q1, Q2, Q3, Q9, `R-ND3-2`, `R-ND3-4` |

---

**9/9 passos concluidos em 2026-09-23.** Nenhuma resposta obrigou emenda ao Functional Design nem ao NFR Requirements; `Q5=B` e compativel com `NFR-W-20`, que ja fora escrito prevendo dois caminhos verificados por teste.
