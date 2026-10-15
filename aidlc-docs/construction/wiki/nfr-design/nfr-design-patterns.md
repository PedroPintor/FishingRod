# NFR Design Patterns — U3 `wiki`

**Fase:** CONSTRUCTION · **Unidade:** `U3 wiki` · **Portão 3 de 4** · **Data:** 2026-09-23
**Decisões:** Q1=A, Q2=B, Q3=B, Q4=A, **Q5=B**, Q6=A, Q7=A, Q8=B, Q9=A ·
Reconciliações `R-ND3-1..4` sem objeção

Identificadores `DP-W-nn` são **estáveis**, como os `DP-P-nn` de U2.

---

## 1. Os padrões

| # | Padrão | Cumpre | Origem |
|---|---|---|---|
| **DP-W-01** | **Ponto único de resolução de caminho.** `resolver_sob(raiz, caminho_logico) -> Path` é o **único** lugar do adaptador que produz um `Path` de arquivo. Nenhum método monta caminho por conta própria | `NFR-W-05`, `RN-W-07`, `PBT-U3-01` | Q4=A |
| **DP-W-02** | **O slug mora na aplicação**, não no adaptador: o caminho lógico é vocabulário da porta, e qualquer unidade que precise prever um caminho importa a mesma função | `RN-W-04`, `RN-W-08`, `PBT-U3-05` | Q2=B |
| **DP-W-03** | **Fio síncrono com casca `async`.** Cada método público é `async def` e faz um único `await asyncio.to_thread(self._x, ...)`; todo o miolo — caminhos, frontmatter, índice — é síncrono | `NFR-W-03` | `R-ND3-1`, Q1=A |
| **DP-W-04** | **Tradução de erro por context manager.** `traduzindo_erros(...)` envolve todo bloco de I/O; só ele conhece `OSError` e `errno`, e a mensagem sai com o **caminho lógico** | `NFR-W-13`, `NFR-W-17`, `RN-W-36` | Q6=A |
| **DP-W-05** | **Publicação atômica por helper geral.** `escrever_atomico(caminho, texto)` grava num temporário no mesmo diretório e publica com `os.replace`. Hoje o **único** chamador é o `index.md` | `NFR-W-11` | Q7=A |
| **DP-W-06** | **Dois leitores de frontmatter, especializados.** `ler_cabecalho` (para em `NFR-W-01`) e `ler_pagina` (arquivo inteiro) são independentes e podem se otimizar e verificar de formas diferentes | `NFR-W-01`, `NFR-W-20` | **Q5=B** — ver §2 |
| **DP-W-07** | **O índice é uma função pura.** `montar_indice(nome, entidades) -> str` recebe dados já lidos e devolve texto; não abre arquivo, não lista diretório, não escreve | `PBT-U3-02`, `RN-W-18`, `RN-W-23` | Q1=A |
| **DP-W-08** | **A raiz chega pelo construtor.** `WikiDeArquivos(raiz_de_dados: Path)`. Quem chama `pasta_de_dados()` é o composition root de U9; o adaptador de wiki **não importa nada de `adaptadores/persistencia/`** | `RN-W-10`, `R-FD3-1` | Q3=B |
| **DP-W-09** | **A porta é a única fronteira de importação.** `aplicacao/portas/wiki.py` é o único arquivo de U3 que U4, U8 e U9 importam | `D-ARQ-08` | `R-ND3-4`, espelha `DP-P-11` |
| **DP-W-10** | **Validar tudo antes de tocar o disco.** `escrever_proposta` roda as quatro validações sobre a proposta inteira e só então escreve | `RN-W-29` — é o que torna a não-atomicidade suportável | Functional Design §4 |
| **DP-W-11** | **O sensor de desempenho roda na suíte padrão.** O teste de 500 páginas não é marcado como lento nem excluído | `NFR-W-02` | **Q8=B** — ver §3 |
| **DP-W-12** | **Alfabeto hostil compartilhado.** Um único gerador de títulos adversariais em `tests/wiki/estrategias.py` alimenta `PBT-U3-01` e `PBT-U3-05` | `NFR-W-18` | `R-ND3-2` |

---

## 2. `DP-W-06` — a decisão que foi contra a minha recomendação, e por quê ela fica

Eu recomendei **um** parser sobre iterador, para tornar `NFR-W-20` verdadeiro por construção.
A resposta foi **B**, com o argumento registrado aqui na sua forma:

> *"o risco que vc falou de dois caminhos podem divergir aqui eu acho que nao se aplica, pois a
> funcao de ler o cabeçalho nao vai mudar, vai ter um regra fixa sempre e vai manter o funcionamento
> de acordo com o frontmatter, so mudaria se o frontmatter mudar, ai talvez a funcao ler_cabecalho
> poderia se adaptar. e a funcao ler_pagina fica separada assim pode ser otimizada do seu proprio
> jeito para ler melhor a pagina. acredito que separando seria melhor pois as duas funcoes podem ser
> otimizadas e apresentar comportamentos diferentes de verificacoes."*

**O argumento tem um ponto forte que eu não tinha considerado:** as duas funções não fazem a mesma
coisa. `ler_cabecalho` responde *"esta página entra no índice, e com que descrição?"* e tem direito
de ser severa. `ler_pagina` responde *"me dê o conteúdo"* e é deliberadamente tolerante
(`RN-W-15`: frontmatter ausente devolve vazio, e a leitura **não falha**). Forçá-las a compartilhar
um parser as obrigaria a compartilhar também a política de tolerância, que já é diferente por
decisão do Functional Design.

**O que muda em consequência, e está aceito:** `NFR-W-20` deixa de ser verdadeiro por construção e
passa a depender de teste. Isso **não** contradiz o portão anterior — `NFR-W-20` foi escrito
exatamente assim: *"os dois caminhos concordam para toda entrada; divergência é falha de teste, não
de produção"*.

**O que isso obriga neste desenho**, e é a contrapartida:

- `tests/wiki/test_frontmatter.py` ganha uma propriedade **dedicada** de concordância —
  para qualquer título, descrição e corpo, `ler_cabecalho(p)` e `ler_pagina(p)` devolvem **o mesmo
  `titulo` e a mesma `descricao`**. Não basta contar com `PBT-U3-03` e `PBT-U3-04`, que cruzam os
  dois caminhos de lado.
- A gramática de `RN-W-11/15/16` é escrita **uma vez, em comentário, no topo de `frontmatter.py`**,
  com as duas funções abaixo dela. Se o frontmatter mudar — o caso que você mesmo nomeou —, as duas
  estão à vista uma da outra.
- O teto de 64 linhas de `NFR-W-01` vive só em `ler_cabecalho`. `ler_pagina` não tem teto, porque
  `Q11=A` não impôs limite de tamanho.

## 3. `DP-W-11` — por que o sensor roda sempre, e por que U2 fez diferente

U2 marcou o teste equivalente (`NFR-P-01`, 5.000 anotações) como lento e fora da execução padrão, e
lá havia motivo: gerar 5.000 anotações num SQLite real custa segundos.

Aqui são **500 arquivos vazios numa pasta temporária**. O custo não paga o risco de o único sensor
de desempenho da unidade nunca rodar — e teste que não roda apodrece até virar falso.

**O que isso significa na prática:** se `NFR-W-02` (~~≤ 500 ms~~ **≤ 1 s**, emenda D1=A de 2026-10-02) falhar, a suíte falha. Em uma máquina
com disco lento ou antivírus ativo isso pode acontecer sem regressão nenhuma. A margem é grande de
propósito — a escala real é de **dezenas** de páginas (`NFR-W-04`), e o alvo é medido em **500** —,
mas fica declarado que este é o único teste da unidade cujo resultado depende da máquina.

## 4. `DP-W-01` + `DP-W-02` — como a segurança vira estrutura

As duas juntas são o desenho de segurança desta unidade, e a divisão é esta:

```
aplicacao/caminho_wiki.py       slug(titulo) -> str          puro, sem disco
                                caminho(entidade, propriedade) -> str
                                                             |
                                                             v
adaptadores/wiki/caminhos.py    resolver_sob(raiz, logico) -> Path
                                  1. o caminho logico ja vem de slug            (etapa 1)
                                  2. monta sob a raiz                           (etapa 2)
                                  3. resolve() dos dois lados + is_relative_to  (etapa 3)
```

- **Etapa 1 mora na aplicação** porque produz o caminho lógico, que é vocabulário da porta e o que
  aparece dentro de `[[...]]` no índice.
- **Etapas 2 e 3 moram no adaptador** porque só ele conhece a raiz real.
- **`resolver_sob` é o único produtor de `Path`** (`DP-W-01`): para violar o confinamento é preciso
  escrever `raiz / algo` à mão em outro arquivo, o que salta aos olhos em revisão.

É o mesmo raciocínio que fez U2 escolher conexão viva em vez de conexão por operação: ligar o
PRAGMA **uma vez** para que não haja preâmbulo a esquecer.

## 5. Conformidade das extensões

| Extensão | Estado | Rationale |
|---|:--:|---|
| **`security-baseline`** | ✅ Conforme, com a ressalva já registrada | `DP-W-01`, `DP-W-02`, `DP-W-04` (nenhum caminho absoluto em mensagem), `DP-W-08` (raiz injetada, sem descoberta). A ressalva de RNF-14 permanece como está no Functional Design — **não reaberta** |
| **`property-based-testing` (Full)** | ✅ Conforme | `DP-W-12`, mais a propriedade de concordância exigida por `DP-W-06`. As 7 propriedades têm módulo e gerador definidos |
| **`resiliency-baseline`** | **N/A** | Desativada em Requirements Analysis. `DP-W-04` e `DP-W-05` são tratamento de erro e integridade de escrita local — **não** são padrões de resiliência distribuída. Nenhum retry, circuit breaker, bulkhead ou timeout de rede é desenhado, porque não há chamada remota nesta unidade |
