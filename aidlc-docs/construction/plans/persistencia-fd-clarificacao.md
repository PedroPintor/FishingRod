# Clarificação — Functional Design U2 `persistencia`

**Data:** 2026-08-26 · **Origem:** Step 2 do `persistencia-functional-design-plan.md`
**Motivo:** Q2 reaberta pelo usuário ("vamos pensar melhor... ele vai chegar a usar megabytes").
Q1=A e Q8=B abriram consequências que o plano original não previa.

> Enquanto este arquivo tiver `[Answer]:` vazio, **nenhum artefato de Functional Design é gerado**.

---

## Parte 1 — A medição que faltava (leia antes de Q2)

Você disse que o usuário vai chegar a megabytes. Concordo — mas vale separar **o que** chega lá,
porque metade já está resolvida.

`ESC-13` já tirou a **transcrição** do documento: mensagem é linha de tabela. Então o documento do
`Ambiente` **não contém texto de conversa**. Sobra a estrutura. Estimando o JSON:

| Parte do documento | Tamanho unitário | Volume plausível | Total |
|---|--:|--:|--:|
| Chat (`id`, `nome`, `Agente` com ferramentas e regras) | ~300 B | 100 chats | ~30 KB |
| Etapa (`descricao`, `executor`, `concluida`, `id`) | ~150 B | 500 etapas | ~75 KB |
| Frente / Tarefa (nome + ids) | ~100 B | 50 | ~5 KB |
| **Anotação** (`autor`, `valor` livre escrito por agente, `criada_em`) | **~1 KB** | **5.000** | **~5 MB** |

A estrutura é limitada por quanto **uma pessoa** consegue criar clicando: centenas de itens, ~100 KB.
A **memória não é** — quem escreve nela é o agente, em toda chamada, e `anotar()` nunca substitui,
só acumula (US-04, RN-09). Os megabytes que você previu moram aí, e em nenhum outro lugar do
documento.

Isso muda a pergunta. Não é "como dividir o ambiente em pedaços menores" — é **"a memória tem a
mesma forma da transcrição, e a transcrição já saiu do documento"**: as duas são apêndices
append-only, escritas por agente, sem limite superior.

### O argumento que decide, e que não é sobre tamanho

Você aprovou **Q4=C** (bloqueio otimista por versão do documento). Combine com "memória dentro do
documento" e aparece um defeito de comportamento, não de desempenho:

> Orquestrador e bibliotecário anotam na mesma tarefa ao mesmo tempo. Os dois leram a versão 7. O
> primeiro salva → versão 8. O segundo é **rejeitado por conflito** e precisa recarregar e repetir.

Isso está errado para um blackboard. Duas anotações concorrentes não são conflito: elas são o uso
normal — e sobreviver é justamente o que RN-09 promete. Com a memória em tabela append-only,
o `INSERT` de um não invalida o `INSERT` do outro e nenhum dos dois é rejeitado. O bloqueio otimista
fica onde faz sentido: sobre a **estrutura**, onde duas edições concorrentes realmente são conflito.

---

## Parte 2 — Perguntas

---

### Q2 (reaberta) — O que é documento e o que é tabela?

A) **Tudo no documento** (recomendação original). Ambiente inteiro, memória incluída, reescrito a
   cada `salvar_ambiente`.
   *Custo real*: reescrever ~5 MB para marcar uma etapa como concluída; e o falso conflito de
   anotação descrito acima.

B) **Estrutura no documento, anotações em tabela.** ⭐
   - Documento (`ambiente`): frentes → tarefas → chats → etapas, `versao`, `versao_esquema`.
     Cresce com o que a pessoa cria; ~100 KB no cenário pesado, reescrito inteiro sem dor.
   - Tabela `anotacao(id, id_tarefa, chave, autor, valor, criada_em)`, append-only, índice por
     `(id_tarefa, criada_em)`.
   *Ganho*: aplica à memória exatamente o princípio que ESC-13 aplicou à transcrição — o mesmo tipo
   de dado tratado do mesmo jeito. Anotar vira um `INSERT`, não uma reescrita. Anotações
   concorrentes nunca conflitam. Abre paginação de memória depois sem mudar o formato do documento.
   *Custo*: `carregar_ambiente` faz 2 consultas em vez de 1; `Memoria.versao` (que hoje conta
   escritas em memória) deixa de ser o que o disco usa para detectar conflito — passa a ser
   `Ambiente.versao`. É preciso decidir Q2a abaixo.

C) **Um documento por Frente**, ambiente guarda só ids.
   *Custo*: não resolve nada — o crescimento está **dentro** da frente (as anotações), e ainda perde
   a atomicidade de salvar o ambiente.

D) **Um documento por Tarefa.** Granularidade estrutural mais fina possível.
   *Custo*: `carregar_ambiente` vira N+1 leituras, atomicidade some, e uma única tarefa com 5.000
   anotações continua com o problema inteiro.

**Minha recomendação: B.** Não por causa dos megabytes — por causa do conflito falso. Se fosse só
tamanho, (A) sobreviveria mais tempo do que parece. É Q4=C que torna (A) errado.

[Answer]: B

---

### Q2a — Se B: ao carregar um ambiente, quanta memória vem junto?

A) **Toda a memória de todas as tarefas.** *Ganho*: `carregar_ambiente` devolve um `Ambiente` de
   domínio completo, idêntico ao de hoje; U4/U5/U7 não mudam nada. *Custo*: abrir um ambiente lê os
   5 MB — o problema volta, só que na leitura.
B) **Toda a memória, mas carregada por tarefa, sob demanda.** O ambiente carrega com as memórias
   vazias e `carregar_memoria(id_tarefa)` preenche quando a tarefa é aberta. *Ganho*: abrir o
   ambiente é instantâneo, e ninguém lê memória de tarefa que não vai olhar. *Custo*: a porta ganha
   uma operação, e existe um estado "memória ainda não carregada" que U4 precisa respeitar.
C) **As N anotações mais recentes por tarefa**, resto sob demanda. *Custo*: o blackboard fica
   parcial sem avisar — um agente lê memória incompleta achando que leu tudo. Pior defeito possível
   aqui.

**Minha recomendação: A nesta iteração.** Motivo: 5 MB de leitura sequencial em SQLite local são
dezenas de milissegundos, e (B) introduz um estado parcial que atravessa U4, U5 e U7 — custo de
complexidade grande para um ganho que ninguém vai sentir agora. E (B) continua possível depois
**sem mudar o formato**, porque a tabela já estará lá: é acrescentar um método, não migrar dados.
Se você prefere pagar já, é (B) — mas então U4 precisa saber disso desde o começo.

[Answer]: A - para a primeira versao de entrega , esse nivel de performance esta bom.

---

### Q1a — Q1=A precisa descobrir a pasta do usuário. Dependência ou 12 linhas?

Você escolheu a pasta de dados do sistema operacional. Falta dizer como se chega nela. Hoje o
projeto tem **zero dependências de runtime**.

A) **`platformdirs`.** *Ganho*: cobre Windows, Linux e Mac com as convenções corretas, testado por
   muita gente. *Custo*: a primeira dependência de runtime do projeto.
B) **~12 linhas escritas por nós** no composition root: `%LOCALAPPDATA%` no Windows,
   `$XDG_DATA_HOME` ou `~/.local/share` no Linux, `~/Library/Application Support` no Mac.
   *Ganho*: dependências de runtime continuam em zero — o que `security-baseline` favorece, e o que
   mantém `uv sync` sem superfície de cadeia de suprimentos. *Custo*: é código nosso para manter, e
   se errarmos uma convenção o dado vai para o lugar errado (falha visível, não silenciosa).

**Minha recomendação: B.** Não é economia de bytes: são três `if`s sobre `sys.platform` cujo
comportamento cabe em um teste, contra uma dependência que carrega mais do que precisamos.

[Answer]: B 

---

## Parte 3 — Consequências de Q8=B que estou **declarando**, não perguntando

Você aprovou apagar ambiente com aviso e confirmação. Quatro decisões saem disso; declaro com o
motivo e sigo, salvo objeção sua.

1. **A porta ganha só `apagar_ambiente(id) -> None`, que apaga linhas do banco.**
   Ela não toca no disco da wiki: RNF-12 diz que persistência não conhece conteúdo de wiki. Quem
   apaga o diretório é o serviço de U4, que já será o dono do ciclo de vida do ambiente.
2. **Ordem: primeiro as linhas do banco, depois o diretório da wiki.**
   Se o processo morrer no meio, sobra um diretório órfão no disco — invisível, inofensivo e
   removível depois. A ordem inversa deixaria um ambiente vivo apontando para uma wiki que não
   existe mais: quebrado e visível. Entre as duas falhas possíveis, escolho a benigna.
3. **O aviso e a confirmação são de U9 (interface), não desta unidade.**
   `apagar_ambiente` apaga sem perguntar — persistência não faz diálogo. A confirmação é tela.
   Registro para não ser esquecido: **entra no critério de pronto de U9.**
4. **Apagar é ação de usuário, não de agente.** Nenhuma ferramenta de ambiente (U5) exporá apagar
   nesta iteração — um agente não deve ser capaz de destruir o ambiente em que trabalha.

Objete em qualquer um destes escrevendo abaixo; caso contrário, seguem como estão.

[Objeções]: nao tenho objecoes.
