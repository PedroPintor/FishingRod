# NFR Requirements — U3 `wiki`

**Fase:** CONSTRUCTION · **Unidade:** `U3 wiki` · **Portão 2 de 4** · **Data:** 2026-09-23
**Decisões que originam este documento:** Q1=A, Q2=B, Q3=A, **Q4=E + escala A (dezenas)**, Q5=B,
Q6=A, Q7=A, Q8=A, Q9=A, Q10=A · Reconciliações `R-NFR3-1..5` sem objeção

Identificadores `NFR-W-nn` são **estáveis** e entram no nome dos testes, como as `RN-W-nn` do
Functional Design e as `NFR-P-nn` de U2.

---

## 1. Desempenho e escala

| # | Requisito | Como se verifica |
|---|---|---|
| **NFR-W-01** | `renderizar_index` lê **apenas o cabeçalho** de cada página: abre o arquivo, consome linhas até fechar o frontmatter, e para. Teto de segurança de **64 linhas** — passou disso sem fechar, não há frontmatter | Q4=E. O custo da renderização passa a depender do **número** de páginas, nunca do **tamanho** delas |
| **NFR-W-02** | Uma aprovação inteira — `escrever_proposta` de até 10 páginas seguida de `renderizar_index` — leva ~~**≤ 500 ms**~~ **≤ 1 s** *(emenda de 2026-10-02, decisão D1=A no portão 4/4 — ver `construction/plans/wiki-cg-decisoes.md`: dentro da suíte o I/O de metadados desta máquina fica 6–7× mais lento e as medições ficaram entre 521 e 870 ms sem regressão)* numa wiki de até **500 páginas** | Q10=A. Teste com dado gerado, marcado como lento e **pulável**. **Não é portão de merge**: é o sensor que avisa quando NFR-W-01 deixa de ser suficiente |
| **NFR-W-03** | **Nenhuma operação da porta bloqueia o laço de eventos.** A operação inteira — inclusive o laço que lê N cabeçalhos — é uma função síncrona empurrada por **um único** `asyncio.to_thread` | Q1=A, igual a `TS-P-02` de U2. Verificável por inspeção: não existe `await` no meio de uma operação |
| **NFR-W-04** | A escala projetada é de **algumas dezenas de páginas** ao fim de meses de uso | Q4. `NFR-W-02` dimensiona para **500** — dez vezes a margem, de propósito |

> **A escala respondida torna `NFR-W-01` mais barata do que precisava ser, e isso é intencional.**
> Com dezenas de páginas, ler o arquivo inteiro (alternativa D) também caberia no orçamento. A
> escolha de E não é sobre o hoje: é sobre a página de 2 MB que `Q11=A` permite existir. Sem ela, o
> custo da renderização cresceria com o **conteúdo**, e a renderização acontece depois de **cada**
> aprovação.

> **O preço de E está declarado:** passam a existir **dois caminhos de leitura de frontmatter** — o
> do cabeçalho (`renderizar_index`) e o da página inteira (`ler`). Eles precisam concordar.
> `NFR-W-20` é a rede.

## 2. Segurança — `security-baseline` ativa

| # | Requisito | Regra / origem |
|---|---|---|
| **NFR-W-05** | **O confinamento é verificado em cada caminho de arquivo, não só na raiz.** Os dois lados passam por `Path.resolve()` e a comparação é `caminho_resolvido.is_relative_to(raiz_resolvida)`. Falha levanta `CaminhoForaDaRaiz` | **Q2=B**, RN-W-07, RNF-10, SECURITY-05, RF-F14 |
| **NFR-W-06** | **`listar` e `ler` não criam diretório.** A raiz é resolvida sem ser criada; raiz ausente faz `listar` devolver lista vazia, como o Functional Design especificou. Só `renderizar_index` cria | Q2=B. Preserva o comportamento já aprovado, sem efeito colateral |
| **NFR-W-07** | Diretórios da wiki criados com **`0o700`** e arquivos `.md` escritos com **`0o600`**, em POSIX. No Windows, a raiz do usuário já é restrita | **Q7=A**, idêntico a `NFR-P-14` de U2 — mesma pasta, mesma política |
| **NFR-W-08** | **Zero dependências de runtime.** `dependencies = []` continua verdadeiro depois desta unidade | SECURITY-10, `R-NFR3-1`, `TS-P-09` |
| **NFR-W-09** | Nenhum segredo em arquivo de wiki; nenhum conteúdo de wiki no banco | SECURITY-12; RNF-12 já garantido por `RN-P-15` (U2) |
| **NFR-W-10** | A leitura é **UTF-8 estrito**. `UnicodeDecodeError` vira `ArmazenamentoIndisponivel` em `ler`; em `renderizar_index` a página é **ignorada**, como qualquer página sem descrição legível, **sem tocar no arquivo** | **Q6=A**, RN-W-20, mesma leitura de `RNF-05` que produziu `NFR-P-07` |

> **Por que `NFR-W-05` fala em "cada caminho" e não em "a raiz".** Resolver só a raiz garante o
> prefixo. O que ataca aqui é um título hostil vindo do modelo, ou um symlink plantado **dentro** da
> pasta de dados: os dois produzem folhas, não prefixos. A etapa 3 de `RN-W-07` só vale alguma coisa
> se rodar no caminho final de cada arquivo.

> **`NFR-W-10` é a decisão de não deformar em silêncio.** A alternativa tolerante (`errors="replace"`)
> parecia mais gentil e é a pior: o agente leria texto corrompido como bom, e `RN-W-26` — que escreve
> a página **inteira** — gravaria a corrupção de volta. Perda silenciosa e permanente. Travar
> visível deixa o arquivo intacto para o usuário consertar.

## 3. Confiabilidade e integridade

| # | Requisito | Como se verifica |
|---|---|---|
| **NFR-W-11** | O **`index.md` é escrito por arquivo temporário no mesmo diretório + `os.replace`**. O índice é sempre o novo completo ou o anterior completo, nunca meio | **Q5=B**. `os.replace` é atômico em POSIX e no Windows dentro do mesmo volume |
| **NFR-W-12** | As **páginas** continuam escritas direto, sem temporário. `escrever_proposta` continua não-atômica (Q7=A, RN-W-29) | Assimetria **deliberada**, ver a nota abaixo |
| **NFR-W-13** | **Nenhum erro de sistema operacional atravessa a porta.** `OSError`, `PermissionError`, `FileNotFoundError` e afins são traduzidos para os 7 erros nomeados de `ErroDeWiki` | `R-FD3-7`, RN-W-36, espelha `RN-P-16` e a lição que U2 aprendeu na geração de código |
| **NFR-W-14** | Toda escrita usa `encoding="utf-8"` e **`newline="\n"` explícito**, nunca o padrão do sistema | `R-NFR3-3`, RN-W-31. No Windows o padrão traduziria para CRLF e `PBT-U3-02` (bytes idênticos) falharia entre plataformas |
| **NFR-W-15** | **Sem trava de arquivo.** Um escritor por processo; duas instâncias simultâneas na mesma wiki são risco declarado, não suportado | Q7=A do Functional Design, RN-W-30. Igual em espírito a `NFR-P-11`, sem a rede do bloqueio otimista |

> **A assimetria de `NFR-W-11` contra `NFR-W-12` tem um motivo, e ele é o próprio argumento de
> Q7=A.** A não-atomicidade foi aceita porque *"cada página é escrita inteira, e o índice mostra o
> que aterrissou"*. Essa frase **depende de o índice estar inteiro**. Um índice truncado mostra meia
> wiki sem nenhum sinal de que está incompleto — falha silenciosa, que é exatamente o que `RNF-05`
> proíbe. Três linhas de `os.replace` sustentam a decisão que já estava tomada, em vez de contradizê-la.
>
> E o índice é **projeção pura** (`RN-W-17`): mesmo no pior caso, re-renderizar conserta. É a página
> que não tem essa propriedade — e por isso é a página, não o índice, que depende da aprovação humana.

## 4. Observabilidade e manutenibilidade

| # | Requisito | Como se verifica |
|---|---|---|
| **NFR-W-16** | Logger **`fishingrod.wiki`** com `NullHandler`. **`WARNING`** para página ignorada pela renderização, com o caminho e o motivo (descrição ausente ou bytes ilegíveis). **`DEBUG`** para renderização concluída, com contagem de páginas e tempo | **Q8=A**, mesmo padrão de `TS-P-07` |
| **NFR-W-17** | Nenhum caminho absoluto de sistema aparece em mensagem de erro que suba para a interface | RNF-11, RN-W-08. O caminho lógico é o vocabulário da porta |

> **`NFR-W-16` existe por causa de um evento que é silencioso por desenho.** `RN-W-20` manda ignorar
> a página sem descrição legível **sem tocar no arquivo** — ela simplesmente não aparece no índice.
> Sem log, *"escrevi a página e ela não aparece"* vira depuração por leitura de código. `WARNING` é
> o nível certo: não polui a tela (o handler é nulo), e quem for investigar liga o logger e vê.

## 5. Testabilidade — `property-based-testing` Full

| # | Requisito | Como se verifica |
|---|---|---|
| **NFR-W-18** | As 7 propriedades `PBT-U3-01..07` são testadas com `hypothesis`. `PBT-U3-01` roda em **duas camadas**: a de **título hostil** (`..`, `../..`, `/etc/passwd`, `C:\Windows`, `~`, separadores repetidos, nomes reservados, Unicode) roda em **toda plataforma**; o caso de **symlink** é um teste separado, marcado `skipif` quando o SO recusa criá-lo | **Q3=A**. Mesma forma do skip que U2 já carrega (o "1 skipped" de `84 passed, 1 skipped`) |
| **NFR-W-19** | U4 e U8 testam contra o **adaptador real sobre `tmp_path`**. **Não há duplo em memória** de `PortaWiki` | **Q9=A**. Nenhum `tests/dobles/wiki.py` |
| **NFR-W-20** | Os dois caminhos de leitura de frontmatter — cabeçalho (`NFR-W-01`) e página inteira (`ler`) — **concordam para toda entrada**. Divergência é falha de teste, não de produção | Consequência de Q4=E. `PBT-U3-03` (round-trip) e `PBT-U3-04` (o índice lista exatamente o que foi escrito) cruzam os dois caminhos |

> **`NFR-W-19` inverte uma decisão de U2, e o motivo é que o argumento não se transfere.**
> `Q12=B` criou `tests/dobles/` para evitar SQLite em teste de serviço. Aqui o `tmp_path` do pytest
> **já é** uma pasta descartável por teste — o duplo seria o real, com mais passos. Pior: um duplo
> sem filesystem **não pode** reproduzir o confinamento, que é a regra mais importante da unidade.
> Um duplo que mente justamente onde o risco mora é pior que nenhum.

> **A honestidade de `NFR-W-18`, dita por extenso:** na **sua** máquina, a etapa 3 de `RN-W-07` — a
> que atravessa symlink — **não roda**. Ela roda em Linux. O que roda em toda parte é a camada de
> título hostil, que cobre as etapas 1 e 2. O teste existe, está nomeado, e a saída do pytest diz
> quando ele foi pulado; não é cobertura presumida.

## 6. Conformidade das extensões

| Extensão | Estado | Rationale |
|---|:--:|---|
| **`security-baseline`** | ✅ **Conforme, com a ressalva já registrada** | SECURITY-05 → `NFR-W-05`/`NFR-W-06` + `PBT-U3-01`; SECURITY-10 → `NFR-W-08`; SECURITY-12 → `NFR-W-09`; SECURITY-13 → `NFR-W-10`, `NFR-W-11`, `NFR-W-14`; SECURITY-15 → `NFR-W-13`. Regras de HTTP, CORS, IAM, load balancer e rede permanecem **N/A** — processo local, sem rede exposta. **A ressalva de RNF-14** (relaxada na leitura, com condição de reabertura dura) está em `business-rules.md` e **não é reaberta nem alterada aqui** |
| **`property-based-testing` (Full)** | ✅ Conforme | `NFR-W-18`, `NFR-W-19`, `NFR-W-20`. As 7 propriedades têm estratégia e local de execução definidos; a única exclusão (symlink no Windows) é nomeada, não silenciosa |
| **`resiliency-baseline`** | **N/A** | Desativada em Requirements Analysis. Nenhum retry, circuit breaker, timeout de rede ou bulkhead é desenhado — não há chamada remota nesta unidade | 

## 7. Rastreio

| Origem | Onde se cumpre |
|---|---|
| **RNF-10** — confinamento é gate de segurança e de teste | `NFR-W-05`, `NFR-W-06`, `NFR-W-18` |
| **RNF-11** — caminho lógico, nunca absoluto | `NFR-W-17`, `R-NFR3-4` |
| **RNF-12** — o banco não guarda conteúdo nem índice de wiki | `NFR-W-09` |
| **RNF-05** — nada de perda silenciosa | `NFR-W-10`, `NFR-W-11`, `NFR-W-13` |
| **RF-F14** — escrita confinada à raiz | `NFR-W-05` |
| **ESC-15** — `uv`, lockfile, política de idade | `NFR-W-08`, `TS-W-08` |
| **Critério 5 de U3** — confinamento verificável | `PBT-U3-01` via `NFR-W-18` |
