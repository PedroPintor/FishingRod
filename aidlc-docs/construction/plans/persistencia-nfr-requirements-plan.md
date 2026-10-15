# NFR Requirements — U2 `persistencia`

**Fase:** CONSTRUCTION · **Unidade:** `U2 persistencia` · **Portão 2 de 4** · **Data:** 2026-08-26
**Entrada:** `construction/persistencia/functional-design/` (aprovado em 2026-08-26T03:10:00Z)

> Enquanto houver `[Answer]:` vazio abaixo, **nenhum artefato de NFR é gerado**.

---

## 1. Fronteira deste estágio

O Functional Design decidiu **comportamento** e deixou uma lista explícita de mecanismos para cá
(`business-logic-model.md` §5). Este estágio decide **como o comportamento é sustentado**: conexão,
modo de journal, durabilidade, orçamento de tempo, limites de tamanho, criação de esquema.

**Não se reabre aqui:** o esquema de 4 tabelas, as 26 regras `RN-P-*`, o contrato de 9 métodos, as
8 propriedades `PBT-U2-*`. Se alguma resposta abaixo tornar uma regra impossível de cumprir, isso é
achado bloqueante e volta como emenda ao Functional Design — não como silêncio.

**Uma dívida herdada, com nome:** `PRAGMA foreign_keys = ON`. Sem ele, `ON DELETE CASCADE` não age e
`apagar_ambiente` (RN-P-20) deixa órfãos **em silêncio**. Q2 abaixo é onde isso deixa de ser risco.

## 2. Passos

- [x] **Step 1** — Ler os artefatos de Functional Design de U2
- [x] **Step 2** — Criar este plano com passos em checkbox
- [x] **Step 3** — Gerar perguntas por categoria de NFR, com tag `[Answer]:`
- [x] **Step 4** — Salvar o plano em `construction/plans/`
- [x] **Step 5** — Respostas coletadas em 2026-08-26. **Contradição detectada entre Q1=C e Q10=A** (aiosqlite vs stdlib): criado `persistencia-nfr-clarificacao.md` com a Q13, **respondida B** (stdlib). Q1 passa a valer como **A**; Q10=A confirmada
- [x] **Step 6** — Gerado `nfr-requirements/nfr-requirements.md` (21 requisitos `NFR-P-01..21`)
- [x] **Step 7** — Gerado `nfr-requirements/tech-stack-decisions.md` (9 decisões `TS-P-01..09`, 5 riscos aceitos)
- [x] **Step 8** — Portão apresentado em 2026-08-26

---

## 3. Perguntas

### Q1 — Como o `async` da porta alcança o `sqlite3`, que é síncrono?

O contrato é `async def` em todos os 9 métodos. O `sqlite3` da stdlib é bloqueante. Alguém precisa
atravessar essa fronteira.

A) **`asyncio.to_thread` por operação.** Cada chamada da porta empurra o trabalho para o pool de
   threads do asyncio. *Ganho*: ~1 linha por método, sem infraestrutura nova, sem dependência.
   *Custo*: o `sqlite3` recusa usar a mesma conexão em thread diferente por padrão — isso amarra
   com Q2.
B) **Uma thread dedicada com fila de comandos.** Toda operação vira mensagem para um worker único.
   *Ganho*: a conexão nunca sai da thread dela; serialização natural. *Custo*: é um pequeno motor
   de concorrência escrito por nós, com desligamento e propagação de exceção para acertar.
C) **`aiosqlite`** (dependência de runtime). *Ganho*: já resolve isso — e é exatamente (B) empacotado.
   *Custo*: a primeira dependência de runtime do projeto, logo depois de você ter escolhido Q1a=B
   justamente para não ter nenhuma.

**Recomendação: A.** É (B) sem escrever (B), porque o `to_thread` já é o pool. E o motivo de (B)
existir — proteger a conexão — some se Q2 for respondida com um `Lock`.

[Answer]: C - vamos usar, assim ja facilita a nossa vida , ja vamos ter uma ferramenta pronta e ja testada e validada.

---

### Q2 — Uma conexão por operação, ou uma conexão viva?

A) **Abrir e fechar a cada operação.** *Ganho*: nenhum estado compartilhado, nenhuma pergunta sobre
   thread. *Custo*: **todo `PRAGMA` precisa ser reaplicado em toda chamada** — inclusive
   `foreign_keys = ON`. Um método novo que esqueça o preâmbulo deixa a cascata desligada em
   silêncio. O risco vira permanente em vez de pontual.
B) **Uma conexão viva por processo**, criada com `check_same_thread=False`, protegida por um
   `asyncio.Lock`. *Ganho*: os PRAGMAs são ligados **uma vez, na abertura** — o defeito silencioso
   de RN-P-20 deixa de ser possível de esquecer. *Custo*: o `Lock` serializa as operações dentro do
   processo, então não há paralelismo real de banco aqui.
C) **Uma conexão por thread** (`threading.local`). *Custo*: o pool do `to_thread` cria threads
   arbitrárias; acaba-se com N conexões e N conjuntos de PRAGMA, que é (A) disfarçado.

**Recomendação: B.**

**Declaro a consequência para não parecer que ela some:** o `Lock` serializa as *instruções*, não a
janela de leitura-e-escrita. Um agente que carrega o ambiente na versão 7, passa 30s chamando o
modelo e então salva, ainda encontra `ConflitoDeVersao` se outro salvou nesse meio-tempo — **dentro
do mesmo processo**. O bloqueio otimista de Q4=C continua sendo necessário e continua disparando;
o `Lock` não o substitui.

[Answer]: B — Uma conexão viva por processo, criada uma vez na inicialização. Com aiosqlite, a serialização e segurança de thread ficam automáticas. Os PRAGMAs são ligados uma vez na conectar() e nunca se perdem.


---

### Q3 — Modo WAL e nível de durabilidade

`RNF-05` proíbe **corrupção silenciosa**. Durabilidade absoluta é outra coisa, e tem preço.

A) **WAL + `synchronous = NORMAL`.** *Ganho*: leitura não bloqueia escrita (útil porque o streaming
   escreve enquanto a tela lê), e sem `fsync` a cada commit. *Custo declarado*: numa **queda de
   energia ou kernel panic**, os últimos commits podem ser perdidos. O banco **não corrompe** — a
   perda é de fim de arquivo, não de integridade. Crash do processo Python não perde nada.
B) **WAL + `synchronous = FULL`.** *Ganho*: nem a queda de energia perde commit confirmado.
   *Custo*: um `fsync` por commit — e Q4 abaixo pode gerar dezenas de commits por resposta do
   modelo. É o item que mais pode custar em desempenho percebido.
C) **Journal padrão (`DELETE`).** *Custo*: leitor e escritor se bloqueiam; para uma TUI que mostra
   transcrição enquanto o agente escreve, é o pior dos três.

**Recomendação: A.** Ler `RNF-05` como "não perder dado em silêncio por defeito nosso", não como
"sobreviver a queda de energia" — sobreviver a queda de energia é o que (B) compra, e o preço é
pago em toda mensagem de streaming. Se você lê `RNF-05` de forma mais dura, é (B) e eu aplico.

[Answer]: A 

---

### Q4 — De quanto em quanto tempo a mensagem em andamento é gravada?

`Q6=A` decidiu que uma mensagem órfã `em_andamento` **permanece marcada** — o que só faz sentido se
o texto parcial tiver chegado ao disco antes do crash. Falta dizer com que frequência.

A) **Uma escrita por trecho recebido do modelo.** *Custo*: centenas a milhares de `UPDATE` por
   resposta. Com Q3=B isso vira milhares de `fsync`.
B) **Throttle de ~500 ms, mais uma escrita final garantida** ao terminar o turno.
   *Ganho*: o disco vê no máximo 2 escritas por segundo; a parcial existe se o app morrer; o texto
   final é sempre exato porque a escrita final não é opcional. *Custo*: até 500 ms do turno se
   perdem num crash — meia frase.
C) **Só ao final do turno.** *Custo*: **contradiz `Q6=A`** — se nada é gravado durante o streaming,
   não existe mensagem órfã para preservar, e a decisão já aprovada perde o objeto.

**Recomendação: B.** O intervalo exato (500 ms) é um número que declaro para poder ser testado, não
uma constante sagrada; se preferir outro, diga qual.

[Answer]:   B — Throttle de ~500ms, com escrita final garantida ao terminar o turno. Assim recuperamos texto parcial em caso de crash, sem sobrecarregar o disco.

---

### Q5 — Quanto tempo pode levar abrir um ambiente?

`Q2a=A` carrega **toda** a memória de **todas** as tarefas na abertura. Você aceitou isso para a
primeira entrega. A pergunta agora é qual número torna essa aceitação verificável.

A) **Alvo declarado: até ~1 s para 5.000 anotações**, medido por um teste de fumaça com dado
   gerado. *Ganho*: vira número, e número regride de forma visível. *Custo*: um teste a manter.
B) **Sem alvo nesta iteração.** *Custo*: quando ficar lento, não haverá como saber quando começou —
   e `Q2a=B` (carga sob demanda) fica sem gatilho objetivo para ser acionada depois.
C) Outro alvo — diga qual.

**Recomendação: A.** Não porque 1 s seja especial, mas porque é o número que transforma "está bom
para a primeira versão" em algo que um teste pode contestar.

[Answer]:  A - vamos de A , ja vamos ter uma maneira de testar e saber se esta bom e um ponto de partida com um valor real para melhorias

---

### Q6 — Quem limita o tamanho de `resultado_resumo`?

O Functional Design nomeou as colunas `args_resumo` e `resultado_resumo` — o nome pressupõe que
**alguém resume**, e nenhum estágio disse quem. O caso concreto: uma ferramenta lê um arquivo de
10 MB e devolve tudo. Sem limite, o banco vira depósito de conteúdo de arquivo, o que também
tensiona `RNF-12` no espírito.

A) **A porta trunca** em N KB ao gravar, marcando que truncou.
B) **Grava íntegro.** *Custo*: crescimento sem teto vindo de fora do controle do usuário.
C) **Quem chama (U6/U7) resume**, a porta não interfere. *Custo*: se um chamador esquecer, (B) volta.
D) **Quem chama resume, e a porta impõe um teto rígido** (ex.: 8 KB por campo) como rede de
   segurança, marcando o truncamento.

**Recomendação: D.** Quem sabe o que é relevante num resultado de ferramenta é quem a chamou —
truncar por tamanho na porta é burro. Mas o teto rígido garante que um chamador distraído não
transforme o banco em outra coisa. O valor do teto é discutível; a existência dele, menos.

[Answer]: **SAIR DA ITERAÇÃO** — Remover `resultado_resumo` completamente. Manter apenas `args_resumo`.

**Justificativa:**

1. **Nenhuma US nesta iteração exige histórico de resultados de ferramenta.** Revisão de `stories.md`:
   - US-05, US-06: focam em estrutura do ambiente e transcrição de mensagens
   - Nenhuma pede "quero ver o resultado que a ferramenta devolveu"
   - Sem caso de uso, é especulação — exatamente o que você rejeitou ("encher linguiça")

2. **A pergunta pressupõe um "resumidor" que não existe:**
   - (A) truncar = perder informação cegamente (10 MB vira 8 KB — perdi 99,92%)
   - (B) guardar tudo = crescimento sem teto (problema que estávamos tentando evitar)
   - (C) quem chama resume = confiança em U6/U7 nunca esquecerem (voltamos a B se esquecerem)
   - (D) dois mecanismos (resumo inteligente + teto rígido) = complexidade para o que não é usado

3. **`args_resumo` é auto-limitado e sempre útil:**
   - Argumentos de uma ferramenta são estruturados e pequenos por natureza
   - Não precisam de truncamento inteligente — "chamei a ferramenta X com Y" cabe sempre
   - Mantém para auditoria e debug: "qual config foi usada?"

4. **Quando a necessidade aparecer, adiciona com ela:**
   - Uma US futura que diga "auditoria de ferramentas" vira oportunidade de desenhar direito
   - Quem resumiria? Um LLM? Regra fixa? Fica evidente lá, não especulado aqui
   - Não paga custo de design agora por algo que pode não existir

**Emenda resultante:** `uso_ferramenta` perde coluna `resultado_resumo`. RN-P-19 vira:
> Um uso de ferramenta pertence a uma mensagem; uma mensagem pode ter vários. Os **argumentos usados** voltam junto com a mensagem, na ordem em que foram registrados.

**Consequência:** nenhuma — US-06 funciona igual, tabela é mais simples, zero dívida técnica.

---

### Q7 — O que fazer quando o arquivo do banco não abre ou está corrompido?

A) **Falhar alto**: erro claro, nome do arquivo, e o app não inicia. *Ganho*: o dado do usuário
   continua lá para recuperação manual. *Custo*: o app fica inutilizável até intervenção.
B) **Renomear o arquivo e começar do zero.** *Custo*: o usuário abre o FishingRod e todo o trabalho
   dele "sumiu" — tecnicamente preservado num arquivo `.corrompido`, na prática invisível. É
   exatamente a perda silenciosa que `RNF-05` proíbe.
C) **Tentar reparo automático.**

**Recomendação: A.** Entre travar visível e apagar invisível, `RNF-05` já escolheu.

[Answer]: A

---

### Q8 — Duas instâncias do FishingRod na mesma máquina, no mesmo banco

A) **Suportado.** WAL permite múltiplos processos; `busy_timeout` absorve a espera; o bloqueio
   otimista de Q4=C já protege a estrutura. *Custo*: nenhum trabalho novo — cai fora do que já foi
   decidido.
B) **Impedir** com arquivo de trava, uma instância por vez. *Custo*: travas órfãs depois de um
   crash são um problema clássico e chato, e a proteção que ela dá já existe por outro meio.

**Recomendação: A.**

[Answer]: A

---

### Q9 — Onde o esquema é criado e verificado?

A) **Na abertura da conexão**, com `CREATE TABLE IF NOT EXISTS` idempotente. *Ganho*: instalação
   nova e existente seguem o mesmo caminho; nada a lembrar de rodar. `Q3=A` (`versao_esquema`) já
   guarda a porta para migração futura.
B) **Comando de migração separado.** *Custo*: cerimônia para um esquema que hoje é criado uma vez
   na vida de cada usuário.

**Recomendação: A.**

[Answer]: A

---

### Q10 — Confirmação de stack

`ESC-13` escolheu SQLite; `Q1a=B` manteve zero dependências de runtime. Confirmando explicitamente
para que fique registrado como decisão e não como inércia:

A) **`sqlite3` da stdlib**, sem dependência nova. Testes com `pytest` + `hypothesis` (já em dev).
B) Outra coisa — diga qual e por quê.

**Recomendação: A.**

[Answer]: A

---

### Q11 — Registro de falha (observabilidade)

O projeto não tem infraestrutura de log decidida em unidade alguma até aqui.

A) **Nenhuma nesta unidade**: a exceção sobe, e quem mostra é U9. *Custo declarado como dívida*: um
   `ConflitoDeVersao` reabsorvido por U4 com recarga e repetição fica **invisível** — se ele
   acontecer o tempo todo, ninguém descobre.
B) **`logging` da stdlib** com um logger nomeado, sem configurar destino nesta unidade. *Ganho*: o
   ponto de observação existe e U9 escolhe se mostra. *Custo*: quase nada — é stdlib.

**Recomendação: B**, restrita a falha e conflito (não a toda operação). É a diferença entre poder
diagnosticar depois e não poder.

[Answer]: B

---

### Q12 — Dado em repouso

O banco vai conter transcrições inteiras de conversa, que podem ser sensíveis. `security-baseline`
está ligada.

A) **Em claro, com permissão de arquivo restrita ao usuário** (`0600` em POSIX; no Windows, a pasta
   `%LOCALAPPDATA%` do usuário já é restrita). *Ganho*: sem gestão de chave. *Custo*: quem tiver a
   conta do usuário lê tudo — que é o mesmo que vale para os arquivos dele.
B) **Cifrado.** *Custo*: exige guardar uma chave em algum lugar da mesma máquina, o que quase sempre
   é teatro; e o SQLite da stdlib não cifra, então (B) implica dependência nativa.

**Recomendação: A.** O modelo de ameaça aqui é máquina pessoal de um usuário selecionado, não
servidor multiusuário.

[Answer]: A

---

## 4. Extensões aplicáveis a este estágio

| Extensão | Estado | Como incide aqui |
|---|:--:|---|
| `security-baseline` | ativa | Q12 (dado em repouso), Q7 (falha sem perda silenciosa), Q10 (superfície de dependências), SECURITY-15 (exceção explícita) |
| `property-based-testing` | ativa (Full) | As 8 propriedades `PBT-U2-*` já existem; este estágio acrescenta os alvos mensuráveis de Q5 e o teto de Q6 |
| `resiliency-baseline` | desativada | N/A — registrada em `aidlc-state.md` |

---

## 5. Execução (2026-08-26)

**Respostas canônicas:** Q1=**A** (corrigida por Q13), Q2=B, Q3=A, Q4=B, Q5=A, **Q6=fora da
iteração** (`resultado_resumo` removido), Q7=A, Q8=A, Q9=A, Q10=A, Q11=B, Q12=A, **Q13=B**.

**Emendas aplicadas por Q6**, todas com texto riscado e nada apagado:

| Artefato | O que mudou |
|---|---|
| `persistencia/functional-design/domain-entities.md` | coluna e campo removidos; §5.3 nova com o motivo |
| `persistencia/functional-design/business-rules.md` | RN-P-19 passa a falar só de argumentos |
| `persistencia/functional-design/business-logic-model.md` | assinatura e §2 e §6 |
| `inception/application-design/component-methods.md` | §4.1 e §4.2 |
| `inception/application-design/components.md`, `services.md`, `unit-of-work.md` (U7) | descrição do que a transcrição persiste |
| `inception/plans/application-design-clarification-questions.md` | **Pergunta F=B parcialmente revogada**, resposta original preservada |
