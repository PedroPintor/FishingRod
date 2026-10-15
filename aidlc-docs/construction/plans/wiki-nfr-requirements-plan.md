# NFR Requirements — U3 `wiki`

**Fase:** CONSTRUCTION · **Unidade:** `U3 wiki` · **Portão 2 de 4** · **Data:** 2026-09-23
**Entrada:** `construction/wiki/functional-design/` (aprovado em 2026-09-23T14:00:00Z)

> Enquanto houver `[Answer]:` vazio abaixo, **nenhum artefato de NFR é gerado**.

---

## 1. Fronteira deste estágio

O Functional Design decidiu **comportamento**: 37 regras, 4 operações, 7 erros, 7 propriedades.
Este estágio decide **como esse comportamento é sustentado** — a fronteira entre `async` e o
filesystem síncrono, a mecânica exata do confinamento, o orçamento de tempo da renderização do
índice, codificação, permissões, log e a forma dos testes de propriedade.

**Não se reabre aqui:** a gramática do `index.md`, os dois níveis, o slug, o frontmatter de duas
chaves, a não-atomicidade de `escrever_proposta` (Q7=A), a ausência de `buscar` e de `lint`. Se
alguma resposta abaixo tornar uma regra `RN-W-*` impossível de cumprir, isso é achado bloqueante e
volta como emenda ao Functional Design — não como silêncio.

**Uma dívida herdada, com nome:** `RN-W-07` diz *o quê* (três etapas, a terceira depois do
`resolve()`), e não diz *como* quando a raiz **ainda não existe** — que é exatamente o estado em que
`renderizar_index` a cria. Q2 abaixo é onde isso deixa de ser ambiguidade.

## 2. Passos

- [x] **Step 1** — Ler os artefatos de Functional Design de U3
- [x] **Step 2** — Criar este plano com passos em checkbox
- [x] **Step 3** — Gerar perguntas por categoria de NFR, com tag `[Answer]:`
- [x] **Step 4** — Salvar o plano em `construction/plans/`
- [x] **Step 5** — Respostas coletadas em 2026-09-23. **Nenhuma ambiguidade**: as 10 vieram fechadas e a unica que trouxe texto livre (Q4) respondeu as duas metades — **E** para a leitura e **dezenas de paginas** para a escala. Nenhum arquivo de clarificacao foi necessario
- [x] **Step 6** — Gerado `wiki/nfr-requirements/nfr-requirements.md` (20 requisitos `NFR-W-01..20`)
- [x] **Step 7** — Gerado `wiki/nfr-requirements/tech-stack-decisions.md` (8 decisoes `TS-W-01..08`, 5 riscos aceitos)
- [x] **Step 8** — Portao 2/4 apresentado em 2026-09-23

---

## 3. Perguntas

### Q1 — Como o `async` da porta alcança o filesystem, que é síncrono? *(Tech Stack / Performance)*

As 4 operações são `async def`. `pathlib` e `open` são bloqueantes. Em U2 a mesma fronteira existiu
e foi resolvida com `asyncio.to_thread` (TS-P-02), depois de a Q13 recusar `aiosqlite`.

A) **`asyncio.to_thread` por operação da porta.** Toda a operação — inclusive o laço que lê N
   páginas em `renderizar_index` — vira **uma** função síncrona empurrada para o pool.
   *Ganho*: consistente com U2, nenhuma dependência, e a operação inteira fica atômica em relação
   ao laço de eventos (não há `await` no meio para outra corrotina intercalar).
   *Custo*: uma renderização longa ocupa uma thread do pool inteira.
B) **Chamada síncrona direta**, sem thread, e as funções ficam `async def` só para cumprir a porta.
   *Ganho*: mais simples de ler e de depurar; I/O local de arquivo pequeno é da ordem de
   microssegundos. *Custo*: **bloqueia o laço de eventos** — durante a renderização a TUI congela,
   e o streaming da resposta do modelo para de ser consumido.
C) **`aiofiles`** (dependência de runtime). *Custo*: quebra `dependencies = []`, que a Q13 de U2
   defendeu explicitamente; e não resolve `Path.iterdir`/`mkdir`, que continuariam síncronos.

**Recomendação: A.** É a mesma escolha de U2, pelo mesmo motivo, e o motivo ficou mais forte aqui:
`renderizar_index` é a única operação do sistema que toca **todos** os arquivos da wiki de uma vez,
e ela é chamada logo depois de cada aprovação — exatamente quando o usuário está olhando a tela.

[Answer]: A 

---

### Q2 — Como o confinamento se verifica quando a raiz **ainda não existe**? *(Security)*

`RN-W-07` manda comparar o caminho resolvido com a raiz resolvida. Mas `renderizar_index` **cria** a
raiz (RN-W-25), e antes disso ela não existe no disco. Em Python, `Path.resolve()` sobre caminho
inexistente não falha (desde 3.6, `strict=False` é o padrão), mas também **não resolve symlink que
ainda não está lá** — resolve só o prefixo existente.

A) **Criar a raiz primeiro, resolver depois.** Toda operação começa garantindo a raiz
   (`mkdir(parents=True, exist_ok=True)`), e só então resolve e compara. *Ganho*: a comparação é
   sempre entre dois caminhos reais, e o symlink — se existir — já foi atravessado.
   *Custo*: `listar` e `ler` passam a **criar** diretório, o que hoje elas não fazem (`listar` sobre
   raiz inexistente devolve lista vazia, e isso é comportamento especificado).
B) **Resolver a raiz sem criá-la, e exigir que o resultado esteja sob a pasta de dados.** A
   comparação usa `Path.resolve()` em ambos os lados e `is_relative_to`. Se a raiz não existe, a
   resolução cobre o prefixo que existe, que é o que importa — o atacante precisaria de um symlink
   **dentro** da pasta de dados do usuário. *Ganho*: `listar` e `ler` continuam sem efeito
   colateral. *Custo*: a garantia é de prefixo, não de folha, até a raiz existir.
C) **Recusar qualquer operação enquanto a raiz não existir**, exceto `renderizar_index`.
   *Ganho*: o estado "raiz ausente" deixa de ter duas leituras. *Custo*: contradiz o que o FD já
   especificou para `listar` (devolve vazio, não levanta) — seria emenda.

**Recomendação: B**, com a etapa 3 de `RN-W-07` aplicada **em cada caminho de arquivo** e não só na
raiz. O modelo de ameaça aqui não é um invasor remoto: é um título hostil vindo do modelo, e um
symlink plantado dentro da própria pasta de dados. (B) cobre os dois sem dar efeito colateral a
`listar`.

[Answer]: B

---

### Q3 — Como `PBT-U3-01` é verificada no Windows, onde criar symlink exige privilégio? *(Reliability / Maintainability)*

A etapa que fecha o buraco é a comparação **depois** do `resolve()`, e o que ela defende é o
symlink. Só que no Windows `os.symlink` levanta `OSError` sem *Developer Mode* ou admin — e é o
Windows que você usa. U2 já tem um precedente: o teste de permissão POSIX é `skip` no Windows
(o "1 skipped" dos 84+1).

A) **Duas camadas.** A propriedade de **título hostil** (`..`, `/etc/passwd`, `C:\Windows`, `~`,
   Unicode) roda em toda plataforma, porque não precisa de symlink nenhum. O caso de **symlink** é
   um teste separado, marcado `skipif` quando o SO recusa criá-lo.
   *Ganho*: a maior parte da propriedade roda sempre; o que não roda está nomeado.
   *Custo*: a etapa 3 fica sem cobertura executada na sua máquina — cobre só em CI Linux.
B) **Substituir o symlink por um duplo**: injetar um resolvedor falso que finge que o caminho
   aponta para fora. *Ganho*: roda em toda plataforma. *Custo*: testa o código de comparação, não o
   comportamento do filesystem — e é justamente o filesystem que surpreende.
C) **Só o título hostil**, sem teste de symlink em plataforma nenhuma. *Custo*: a etapa 3 de
   `RN-W-07` passa a ser afirmação de documento, não de teste.

**Recomendação: A.** É a mesma forma do skip que U2 já carrega, e ela é honesta: o teste existe,
está nomeado, e a saída do pytest diz quando ele não rodou.

[Answer]: A 

---

### Q4 — Quanto custa `renderizar_index`, e qual o tamanho que ela precisa aguentar? *(Scalability / Performance)*

Ela é chamada **depois de cada proposta aprovada**, e lê o frontmatter de **todas** as páginas.
Preciso de um número para dimensionar, e de uma decisão sobre quanto de cada arquivo ler.

**Sobre o tamanho** — quantas páginas uma wiki realista tem ao fim de alguns meses de uso?

A) **Dezenas** (até ~100 páginas). B) **Centenas** (~100 a 1.000). C) **Milhares** (>1.000).

**Sobre a leitura de cada página**:

D) **Ler o arquivo inteiro** e separar o frontmatter na memória. *Ganho*: uma função de parsing só,
   compartilhada com `ler`. *Custo*: uma página de 2 MB (permitida, Q11=A) é lida inteira só para
   pegar duas linhas — e são lidas todas, a cada aprovação.
E) **Ler só o cabeçalho**: abrir o arquivo e parar na linha que fecha o frontmatter, com um teto de
   segurança (por exemplo 64 linhas). *Ganho*: o custo da renderização deixa de depender do tamanho
   das páginas. *Custo*: dois caminhos de leitura de frontmatter, que precisam concordar —
   `PBT-U3-03` e `PBT-U3-04` juntas pegam a divergência, mas é código a mais.

**Recomendação: E**, e o orçamento que eu proporia é **≤ 300 ms para 500 páginas**, medido como
teste lento e não como portão de merge — o mesmo tratamento que `NFR-P-01` recebeu em U2. Se sua
resposta ao tamanho for (A), (D) também serve e é mais simples; a escolha de (E) é o que impede o
custo de crescer com o conteúdo.

[Answer]: vamos seguir de E e ler apenas o cabecalho apenas o cabeçalho é necessario para fazer a renderizacao do index. ao longo de meses de uso a wiki vai ter algumas dezenas de paginas.

---

### Q5 — O `index.md` é escrito direto, ou por arquivo temporário + rename? *(Reliability)*

Q7=A decidiu **sem escrita atômica** para a unidade, e eu não estou reabrindo isso para as páginas.
Mas o índice é diferente das páginas em dois aspectos: é **o único caminho até o conteúdo** (sem
`buscar`, sem `lint`), e é **projeção pura** — sempre reconstruível.

A) **Escrita direta, como as páginas.** *Ganho*: uma regra só para toda a unidade; nada de especial
   para lembrar. *Custo*: um crash no meio da escrita deixa o índice **truncado**, e o próximo
   agente que o ler vê meia wiki sem nenhum sinal de que está incompleta — falha silenciosa, que é
   o que `RNF-05` proíbe em U2.
B) **Temp + `os.replace`** só para o `index.md`. *Ganho*: o índice é sempre completo ou é o
   anterior, nunca meio. `os.replace` é atômico em POSIX e no Windows (mesmo volume).
   *Custo*: uma exceção à regra de Q7=A, que precisa estar escrita para não parecer esquecimento.
C) **Escrita direta, mais um marcador de fim** (uma linha final reconhecível) que o leitor confere.
   *Custo*: inventa um protocolo próprio dentro de um arquivo que é markdown para humano ler.

**Recomendação: B.** O argumento de Q7=A era que uma proposta pela metade no disco é um desfecho
aceitável porque cada página é escrita inteira e o índice mostra o que aterrissou. Esse argumento
**depende** de o índice estar inteiro. Custa três linhas e não muda o contrato.

[Answer]: B

---

### Q6 — O que acontece ao ler um arquivo que não é UTF-8 válido? *(Reliability / Availability)*

`RN-W-31` fixa a escrita em UTF-8. A leitura encontra o que estiver lá — e o usuário pode abrir a
pasta num editor que salva em outra codificação.

A) **Estrito.** `UnicodeDecodeError` vira `ArmazenamentoIndisponivel` em `ler`; em
   `renderizar_index`, a página é **ignorada** como qualquer página sem descrição legível
   (RN-W-20), sem tocar no arquivo. *Ganho*: nenhum dado é silenciosamente deformado; o arquivo
   fica intacto para o usuário consertar. *Custo*: a página some do índice sem explicação visível
   na tela.
B) **Tolerante.** `errors="replace"` — o arquivo é lido com `` no lugar dos bytes ruins.
   *Ganho*: nada some. *Custo*: o agente lê texto corrompido como se fosse bom, e uma reescrita
   posterior **grava a corrupção de volta** (RN-W-26 escreve a página inteira) — perda silenciosa
   e permanente.
C) **Tentar UTF-8, cair para a codificação do sistema.** *Custo*: o mesmo de (B), com resultado
   dependente da máquina.

**Recomendação: A.** É a mesma leitura de `RNF-05` que U2 fez em `NFR-P-07`: entre travar visível e
deformar invisível, travar visível.

[Answer]: A 

---

### Q7 — Permissões e localização dos arquivos da wiki *(Security)*

`NFR-P-14` de U2 fixou `0o700` para diretório e `0o600` para o banco, em POSIX, com a nota de que no
Windows a raiz do usuário já é restrita. A wiki nasce sob a mesma pasta de dados.

A) **Mesma política de U2**: diretórios da wiki com `0o700`, arquivos `.md` com `0o600`, em POSIX;
   nada de especial no Windows.
B) **Diretórios `0o700`, arquivos com o padrão do processo** (respeitando `umask`). *Ganho*: o
   diretório já barra o acesso; o arquivo herdar o padrão é o comportamento que um editor externo
   espera. *Custo*: divergência de U2, que precisa estar escrita.
C) **Sem definir permissão**, herdando tudo do sistema.

**Recomendação: A**, por consistência — a wiki e o banco guardam o mesmo tipo de informação e ficam
lado a lado; duas políticas diferentes na mesma pasta é a espécie de detalhe que ninguém lembra
seis meses depois.

[Answer]: A

---

### Q8 — O que a unidade registra em log? *(Maintainability)*

`TS-P-07` de U2 criou o logger `fishingrod.persistencia` com `NullHandler`. Aqui há um evento que
é **silencioso por desenho** e por isso merece atenção: `RN-W-20` manda **ignorar** a página sem
descrição legível, sem tocar no arquivo. Ela simplesmente não aparece no índice.

A) **Logger `fishingrod.wiki` com `NullHandler`**, em nível `WARNING` para página ignorada
   (com o caminho e o motivo) e `DEBUG` para renderização concluída (contagem e tempo).
   *Ganho*: o único evento invisível do desenho passa a ter rastro, sem poluir a tela.
B) **Só `DEBUG`**, inclusive para página ignorada. *Custo*: para ver por que a página sumiu do
   índice é preciso ligar `DEBUG` no app inteiro.
C) **Sem log nesta unidade.** *Custo*: "escrevi a página e ela não aparece no índice" vira
   depuração por leitura de código.

**Recomendação: A.**

[Answer]: A

---

### Q9 — Como U4 e U8 testam contra a wiki: duplo em memória ou adaptador real? *(Maintainability)*

Q12=B de U2 criou `tests/dobles/` com um duplo em memória da porta de persistência, e a decisão se
provou certa lá. Aqui a equação é outra, porque o "banco" é uma pasta e o `tmp_path` do pytest já
dá uma pasta descartável por teste.

A) **Adaptador real sobre `tmp_path`**, sem duplo. *Ganho*: uma implementação só; nenhum risco de
   o duplo e o real divergirem no ponto mais perigoso (o confinamento). *Custo*: os testes de U4 e
   U8 tocam disco — rápido, mas não instantâneo.
B) **Duplo em memória**, como em U2. *Ganho*: testes de U4/U8 sem I/O. *Custo*: uma segunda
   implementação das 4 operações, que precisa reproduzir slug, frontmatter e ordenação para não
   mentir — e um duplo que não tem filesystem **não pode** reproduzir o confinamento, que é a regra
   mais importante da unidade.
C) **Os dois**, com uma bateria de testes de contrato rodada contra ambos.
   *Custo*: é o mais correto e o mais caro; em U2 isso não foi feito nem para o banco.

**Recomendação: A.** O argumento que sustentou o duplo em U2 — evitar SQLite em teste de serviço —
não se transfere: `tmp_path` já é o duplo, e é o real.

[Answer]: A

---

### Q10 — Qual o orçamento de tempo de uma aprovação inteira, do ponto de vista de quem espera? *(Performance / Usability)*

`ServicoBibliotecario.aprovar` chama `escrever_proposta` e em seguida `renderizar_index`. O usuário
acabou de clicar "aprovar" e está olhando.

A) **≤ 500 ms** para uma proposta de até 10 páginas numa wiki de até 500 páginas, medido como teste
   lento e não como portão de merge (tratamento de `NFR-P-01`).
B) **≤ 2 s**, com indicação de progresso na TUI (o que empurra trabalho para U9).
C) **Sem orçamento declarado** nesta iteração — mede-se quando houver conteúdo real.

**Recomendação: A.** Não porque 500 ms seja mágico, mas porque um número escrito é o que faz a
resposta de Q4 ter consequência: sem alvo, a escolha entre ler a página inteira e ler só o cabeçalho
vira gosto.

[Answer]:  A

---

## 4. Reconciliações declaradas

Estas eu aplico **sem pergunta**, a menos que você objete. Estão aqui para ficarem visíveis.

| # | Reconciliação |
|---|---|
| **R-NFR3-1** | **Zero dependências de runtime permanece.** Nada nesta unidade acrescenta pacote ao `pyproject.toml`: `pathlib`, `os`, `unicodedata` e `asyncio` são stdlib. O primeiro pacote de runtime do projeto continua sendo o `claude-agent-sdk`, em U6 (`TS-P-09`) |
| **R-NFR3-2** | **O slug usa `unicodedata.normalize("NFKD", ...)`** e descarte de combinantes, que é como `RN-W-04` se cumpre sem dependência. `Dr. Marcelo & Cia` → `dr-marcelo-e-cia` exige uma tabela mínima de substituição antes da normalização (`&` → `e`), declarada no artefato |
| **R-NFR3-3** | **Toda escrita usa `newline="\n"` explícito** em `open`, nunca o padrão do sistema (`RN-W-31`). No Windows o padrão traduziria para CRLF e `PBT-U3-02` (bytes idênticos) falharia entre plataformas |
| **R-NFR3-4** | **A raiz de dados chega pelo construtor** do adaptador (`RN-W-10`). O composition root de U9 é quem chama `pasta_de_dados()`; o adaptador de wiki **não importa** o adaptador de persistência (R-FD3-1) |
| **R-NFR3-5** | **`resiliency-baseline` é N/A** nesta unidade, como nas anteriores — desativada em Requirements Analysis. Nenhum retry, circuit breaker ou bulkhead é desenhado |

---

## 5. Conformidade das extensões, tal como estará no artefato

| Extensão | Onde se decide neste estágio |
|---|---|
| `security-baseline` | Q2 (mecânica do confinamento), Q3 (como ele é testado), Q6 (codificação), Q7 (permissões), R-NFR3-1 (SECURITY-10) |
| `property-based-testing` (Full) | Q3 e Q9 — estratégias `hypothesis` e onde os testes de propriedade rodam |
| `resiliency-baseline` | N/A — R-NFR3-5 |

---

**8/8 passos concluidos em 2026-09-23.** Nenhuma resposta tornou uma regra `RN-W-*` impossivel de cumprir; nenhuma emenda ao Functional Design foi necessaria.
