# NFR Design Plan — U6 `sessao`

**Fase:** CONSTRUCTION · **Unidade:** `U6 sessao` · **Portão 3 de 4** · **Data:** 2026-10-06
**Entrada:** `construction/sessao/nfr-requirements/` (aprovado em 2026-10-06T22:26:08Z)

O portão 1 fixou o **comportamento**: a porta de 3 operações, 5 eventos, 4 estados e 54 regras. O
portão 2 fixou os **alvos e a tecnologia**: `NFR-S-01..18` e `TS-S-01..09`. Este estágio decide a
**forma**: quem é dono de quê, em quantos módulos, com que prazos, e qual padrão garante que uma regra
não possa ser esquecida.

**Ainda não se escreve código.** Isso é o portão 4.

> Enquanto houver `[Answer]:` vazio abaixo, **nenhum artefato de NFR Design é gerado**.

---

## 1. Passos

- [x] **1.** Ler `nfr-requirements.md` (18 requisitos) e `tech-stack-decisions.md` (9 decisões)
- [x] **2.** Reler o Functional Design: porta, regras `RN-S-01..54`, propriedades `PBT-U6-01..12`, as 10 medições e G1–G15
- [x] **3.** Inspecionar a árvore existente (`src/fishingrod/`, `tests/`) para saber o que U0–U5 deixaram pronto
- [x] **4.** Ler o código-fonte da `0.2.143` e o CLI embutido nela. O pacote Windows foi baixado do PyPI e o hash conferido (`5887e737…048e09`); o CLI é o **2.1.238**. Resultado: os 14 fatos da §2
- [x] **5.** Escrever este plano com as perguntas
- [x] **6.** Coletar e analisar as respostas. Recebidas em 2026-10-13T19:28:57Z: **Q1..Q8 = A**, todas iguais à recomendação, sem comentário; nenhuma objeção a `R-ND6-1..14`. Sem ambiguidade, sem arquivo de clarificação
- [x] **7.** Gerar `construction/sessao/nfr-design/nfr-design-patterns.md`: **24 padrões `DP-S-01..24`**, 6 decisões de geração `N1..N6` para o portão (N1 emenda `R-ND6-6` por causa de **A15**), tabela de falhas, as opções do SDK uma a uma, medições 15 e 16
- [x] **8.** Gerar `construction/sessao/nfr-design/logical-components.md`: 4 arquivos de aplicação, 7 do adaptador, 17 de teste mais o falso; matriz sem ciclo (`adaptador.py` não importa o SDK; só `acoes.py` importa o catálogo); as 6 fases da tarefa dona; rastreio padrões → arquivos e propriedades → testes. Emendas marcadas em 6 artefatos aprovados (`nfr-design-patterns.md` §7)
- [x] **9.** Marcar os checkboxes, atualizar `audit.md` e `aidlc-state.md`, apresentar o portão 3/4. Conclusão apresentada em 2026-10-13T19:42:19Z

---

## 2. O que o código da versão travada mostrou, antes das perguntas

Lido em 2026-10-06 no código-fonte do `claude-agent-sdk 0.2.143` e no CLI que vem dentro do pacote
Windows dele. Cada linha diz de onde veio o fato.

| # | Fato | Onde | Consequência |
|---|---|---|---|
| **A1** | `setting_sources=None` **carrega todas as fontes**: usuário, projeto e local (`CLAUDE.md`, hooks, plugins, permissões). Para isolar, é preciso passar `[]`. Com `skills` é igual: `None` não desliga as skills, `[]` desliga | `types.py`, documentação de `setting_sources` e `skills` | RN-S-10 só vale com as opções escritas por extenso. Sem pergunta: `R-ND6-4` |
| **A2** | `env` **só acrescenta**. O processo do CLI recebe `{**os.environ, ..., **options.env}`. Nenhuma opção **remove** uma variável herdada | `subprocess_cli.py`, `connect()` | RN-S-52 ("deixa de repassar") precisa de uma forma: **Q5** |
| **A3** | Sem callback de `stderr`, a saída de erro do CLI **vai para o terminal do FishingRod**. Na TUI de U9, ela desenharia por cima da tela | `subprocess_cli.py`, `connect()` | O callback fica sempre registrado. Sem pergunta: `R-ND6-5` |
| **A4** | O `close()` do SDK é protegido contra o cancelamento do **anyio**, mas **não** contra `task.cancel()` do **asyncio**. O próprio SDK escreve que, nesse caso, a escalada `terminate`/`kill` é pulada e o processo fica esperando o fim do programa | `subprocess_cli.py`, docstring de `close()` | O ESC de U9 é exatamente um `task.cancel()` (D-Q7-1). Se a limpeza rodar na tarefa cancelada, RN-S-38 quebra: **Q1** |
| **A5** | A documentação do cliente ainda diz que conexão e uso precisam acontecer **no mesmo contexto async**. O código interno já usa tarefas soltas (`spawn_detached`). Documentação e código discordam | `client.py`, docstring da classe; `_task_compat.py` | TS-S-09 veio do spike, na `0.2.125`. Mais um motivo para a **Q1** |
| **A6** | `interrupt()` espera a resposta do CLI por até **60 s**, o padrão das requisições de controle | `query.py`, `_send_control_request` | Sem prazo próprio, um ESC pode deixar a sessão em `EM_TURNO` por um minuto: **Q2** |
| **A7** | Quando estoura, o prazo de subida do próprio SDK levanta uma **`Exception` genérica** (`"Control request timeout: initialize"`), não um erro tipado | `query.py`, `_send_control_request` | Pela tabela do FD, isso cairia em `FALHA_INESPERADA`, mas NFR-S-11 promete `INDISPONIVEL`: **Q3** |
| **A8** | Existe **sinal tipado** de falta de login e de limite de uso: `AssistantMessage.error` (`authentication_failed`, `rate_limit`, …) e `RateLimitEvent` com `status="rejected"` e `resets_at` | `types.py` | A medição 4 deixa de depender de texto. Mas não dá para atingir o limite de uso de propósito: **Q4** |
| **A9** | O CLI **grava a transcrição de cada sessão em disco**, em `~/.claude/projects/<pasta>/`. O CLI 2.1.238 tem `--no-session-persistence`, que a ajuda diz funcionar só com `--print`. O SDK roda o CLI sem terminal, em `stream-json`; se isso conta como `--print` é medição | `types.py`, documentação de `SessionStore`; `claude.exe --help` | As conversas ficariam copiadas fora da pasta de dados do FishingRod, e apagar um ambiente (U4) não apagaria essas cópias: **Q6** |
| **A10** | Tempo-limite de ferramenta MCP no CLI 2.1.238: o `timeout` do servidor; se não houver, `MCP_TOOL_TIMEOUT`; se não houver, **10⁸ ms (~27,8 h)**. O máximo aceito é **2.147.483.647 ms (~24,8 dias)** | `claude.exe`, função que lê `MCP_TOOL_TIMEOUT` (código minificado) | A medição 2 do FD tem resposta provável: o limite é **configurável**, e o FD manda pôr o maior valor aceito. U5 provavelmente não é reaberta. Sem pergunta: `R-ND6-7` |
| **A11** | O SDK guarda os processos do CLI que subiu e manda `terminate` a todos quando o Python termina (`atexit`) | `subprocess_cli.py`, `_ACTIVE_CHILDREN` | Saída normal e exceção não tratada já não deixam processo órfão. Sobra só a queda dura (medição 14) |
| **A12** | O `close()` do transporte espera até 5 s o processo sair, mais 5 s depois do `terminate` e mais 5 s depois do `kill`: **até ~15 s por processo**, no pior caso | `subprocess_cli.py`, `close()` | `encerrar()` fechando uma sessão de cada vez somaria os piores casos. Sem pergunta: `R-ND6-9` |
| **A13** | Um esquema que já é JSON Schema completo (`type` + `properties`) **passa sem conversão** | `__init__.py`, `_build_input_schema` | A medição 9 tem resposta no código; o teste real só confirma |
| **A14** | Com `mcp` 1.x, as ferramentas do SDK **não eram canceladas** quando o CLI abandonava a chamada. Com 2.x, são. A `0.2.143` resolve `mcp 2.1.0` | `types.py`, documentação de `McpSdkServerConfig` | Mais um ganho da `0.2.143` sobre a `0.2.125` do spike, a favor de RN-S-35 |

**Observado de passagem:** o CLI da máquina foi de 2.1.288 (medido em 2026-10-02) para **2.1.292** sem
ninguém pedir. É exatamente o motivo de TS-S-02 usar o CLI embutido, que fica travado junto do SDK.

---

## 3. Perguntas

### Q1 — Quem é dono do cliente do SDK? *(Logical Components / Resilience)* — ver A4 e A5

Toda conexão tem um cliente do SDK que sobe o processo, conversa e desconecta. A pergunta é **em que
tarefa** isso acontece.

A) **Uma tarefa dona por conexão.** Quando o processo sobe, o adaptador cria uma tarefa própria que
   conecta, entrega as mensagens, lê o provedor e desconecta. Ela morre junto com o processo.
   `enviar` conversa com ela por duas filas: uma leva o texto, a outra traz os eventos.

   ```
   U7 (qualquer tarefa)            adaptador                     SDK + CLI
   enviar(sessao, texto) ---texto---> fila de entrada --+
                                                        |
                                    tarefa dona <-------+----> cliente do SDK
                                        |                       (conecta, conversa,
   eventos do turno  <---eventos--- fila de saída <-----+        desconecta)
   ESC: cancela quem lê
        -> recado "interromper" ---> tarefa dona (ninguém a cancela)
   ```

   Cancelar quem lê o turno (o ESC) **não** cancela a dona. Só deixa um recado de interrupção. Deixar
   o recado é síncrono e funciona de qualquer tarefa, inclusive do finalizador que o Python roda
   quando um iterador é abandonado sem ser fechado (G6).
   *Ganho*: a limpeza do processo **nunca** roda numa tarefa cancelada. A4 deixa de existir, e
   RN-S-38 vale por construção. A5 deixa de importar, porque o cliente vive inteiro numa tarefa só.
   E U7 pode chamar `enviar` de uma tarefa diferente a cada mensagem.
   *Custo*: mais engrenagem (duas filas e uma tarefa por conexão). Os testes precisam esperar a dona
   terminar antes de contar processos.
B) **Uma tarefa dona por sessão**, viva de `abrir` a `fechar`, mesmo sem processo.
   *Ganho*: o mesmo de A, e a reconexão acontece dentro da mesma tarefa.
   *Custo*: uma tarefa viva para cada chat aberto, mesmo parado, e `SEM_CONEXAO` deixa de significar
   "nada rodando".
C) **Na tarefa de quem chama.** `enviar` usa o cliente direto, e o caminho do cancelamento protege a
   limpeza com `asyncio.shield`.
   *Ganho*: menos código.
   *Custo*: depende de A5 (o SDK aceitar uso em tarefas diferentes, coisa que a documentação dele
   nega). Um segundo ESC durante a limpeza ainda a interrompe. E um iterador abandonado e
   finalizado pelo Python roda a limpeza numa tarefa que o adaptador não controla.

**Recomendação: A.** O ESC é o jeito mais comum de interromper, e é justamente o caso que o SDK
admite não cobrir. Com a tarefa dona, interromper vira deixar um recado, e quem fecha o processo é
sempre uma tarefa que ninguém cancela.

[Answer]: A

---

### Q2 — Quanto tempo o ESC espera o provedor parar? *(Performance / Resilience)* — ver A6

Depois do ESC, o adaptador avisa o provedor e espera duas coisas: a confirmação do aviso e o fim da
resposta interrompida. O CLI ainda manda o fechamento daquele turno, e esse fechamento não pode vazar
para o turno seguinte. Enquanto isso, a sessão fica em `EM_TURNO`, e a próxima mensagem espera na
fila de U7.

A) **5 s para as duas coisas juntas.** Passou disso, o processo é descartado e a sessão vai a
   `SEM_CONEXAO`, como RN-S-35 já manda quando o aviso falha. A próxima mensagem reconecta, com o
   aviso de conversa nova (RN-S-34).
B) **60 s**, o padrão do SDK.
   *Custo*: um CLI travado segura a sessão e a fila por um minuto depois do ESC.
C) **Não avisar**: todo ESC descarta o processo.
   *Custo*: todo ESC apaga a memória do agente sobre a conversa, o que contradiz C2=A (a mensagem
   interrompida fica no histórico).

**Recomendação: A.** Num CLI saudável, a confirmação deve chegar bem antes de 1 s; a medição 3
registra o número real. 5 s dão folga a um CLI lento e são curtos o bastante para a fila não ficar
presa. O número fica num lugar só (`R-ND6-8`).

[Answer]: A

---

### Q3 — Falha ao subir: a categoria vem da fase ou da exceção? *(Resilience)* — ver A7

NFR-S-11 promete `INDISPONIVEL` quando subir passa de 60 s. Mas o prazo do próprio SDK levanta uma
`Exception` genérica, e a tabela do FD (RN-S-28) manda o que não reconhece para `FALHA_INESPERADA`.

A) **Pela fase, com prazo próprio.** O adaptador põe o próprio prazo de 60 s em volta da subida
   inteira: processo, checagem de versão e inicialização. Qualquer falha nessa fase vira
   `INDISPONIVEL`, menos duas: CLI ausente (`PROVEDOR_AUSENTE`) e falta de login reconhecida
   (`NAO_AUTENTICADO`). A pilha vai para o log em **WARNING**. Isso acrescenta um caso à tabela de
   níveis de NFR-S-17, que hoje não o cita.
   *Ganho*: NFR-S-11 vale sem depender do texto de uma exceção do SDK. Para você, uma conexão que não
   abriu aparece como "indisponível, tente de novo", que é o que de fato se sabe.
   *Custo*: um defeito nosso que só aparecesse na subida seria mostrado como "indisponível", e não
   como defeito. O teste de inspeção das opções (`R-ND6-4`) e a pilha no log reduzem esse risco.
B) **Pela exceção, reconhecendo o texto** `"Control request timeout: initialize"`.
   *Custo*: depende de casar texto, e quebra sem aviso se o SDK mudar a frase.
C) **Pela exceção, sem reconhecer**: estourar o prazo vira `FALHA_INESPERADA`.
   *Custo*: contradiz NFR-S-11, que já foi aprovado.

**Recomendação: A.** A regra do FD é usar, na dúvida, a categoria que não mente. Na fase de subida
ainda não há turno nem resposta, então "indisponível" é exatamente o que se sabe.

[Answer]: A

---

### Q4 — O sinal tipado de limite de uso conta como "sinal medido"? *(Resilience)* — ver A8

RN-S-29 só aceita `NAO_AUTENTICADO` e `LIMITE_DE_USO` com **sinal medido**.
- **A falta de login pode ser medida de verdade**, sem mexer no seu login: o teste `sdk_real` roda o
  CLI apontando para uma pasta de configuração vazia e temporária (`R-ND6-13`).
- **O limite de uso, não**: não dá para atingir o limite da assinatura de propósito.

A) **Sim.** `AssistantMessage.error == "rate_limit"` e `RateLimitEvent(status="rejected")` fazem
   parte da API pública da versão travada. Eles contam como sinal, e `libera_em` sai de `resets_at`.
   O teste com cliente roteirizado cobre a tradução. Fica registrado que esse sinal foi **lido** no
   código, não **provocado**.
B) **Não.** `LIMITE_DE_USO` cai em `INDISPONIVEL` até alguém atingir o limite e registrar o sinal
   real.
   *Custo*: no dia em que você atingir o limite, a tela vai dizer "indisponível, tente de novo", e
   não "limite da assinatura atingido, libera às 18h".

**Recomendação: A.** O tipo existe exatamente para isso. Ler um campo tipado é mais seguro do que ler
texto, que era o risco que RN-S-29 queria evitar.

[Answer]: A

---

### Q5 — Como as variáveis de credencial deixam de chegar ao CLI? *(Security)* — ver A2

RN-S-52: o processo do agente não recebe chave de API, token, URL base nem seletor de provedor
alternativo. O SDK não tem opção para remover uma variável herdada.

A) **Sobrescrever com texto vazio** em `options.env` (por exemplo, `ANTHROPIC_API_KEY=""`).
   *Ganho*: usa só a API pública, vale por sessão e não mexe no resto do programa.
   *Custo*: depende de o CLI tratar vazio como ausente. Por isso a medição 5 passa a ser feita assim:
   com uma chave **falsa** no ambiente do processo Python, a sessão precisa continuar funcionando pela
   assinatura. Se o CLI tratar vazio como valor, a decisão cai para B, registrada.
B) **Apagar de `os.environ` na montagem do programa (U9)**, antes de qualquer sessão.
   *Ganho*: a variável realmente não existe.
   *Custo*: muda o processo inteiro do FishingRod, e qualquer biblioteca que leia o ambiente perde as
   variáveis. A regra sai de U6 e vai para U9, e os testes precisam isolar `os.environ`.
C) **Transporte próprio**, herdando o transporte interno do SDK para montar o ambiente.
   *Custo*: depende de um módulo `_internal`, que pode mudar em qualquer versão.

**Recomendação: A**, com B já escrita como saída se a medição falhar.

[Answer]: A

---

### Q6 — A transcrição que o CLI grava em disco *(Security — dados em repouso)* — ver A9

Se nada for feito, cada conversa do FishingRod também fica em
`~/.claude/projects/<pasta de trabalho>/<sessão>.jsonl`, fora da pasta de dados do FishingRod.

A) **Desligar a gravação do CLI** com `--no-session-persistence`. Uma medição nova confirma, com o
   CLI de verdade, que nenhum arquivo é criado. Se a opção não funcionar no modo do SDK, vira risco
   aceito, com o local e o sintoma registrados.
   *Ganho*: a transcrição do FishingRod fica sendo a única cópia. Apagar um ambiente apaga a conversa.
   Nada cresce sem limpeza fora da pasta de dados.
   *Custo*: a retomada do histórico, prevista para a próxima iteração (Q5=D do FD), não poderá usar o
   `resume` do CLI. Terá de reconstruir a conversa a partir da transcrição do FishingRod.
B) **Aceitar e registrar.** As cópias ficam, todas numa pasta só (a da pasta de trabalho neutra).
   *Ganho*: a retomada da próxima iteração pode usar o `resume` do CLI.
   *Custo*: o contrário de cada ganho de A.
C) **Apagar os arquivos da sessão ao fechar.**
   *Custo*: depende do formato e do local internos do CLI, e uma queda dura deixa os arquivos para trás.

**Recomendação: A.** O custo de A é, na verdade, um alinhamento: o FishingRod não depende de um LLM
específico. Uma retomada pelo `resume` do CLI só funcionaria com o Claude. Reconstruir a partir da
própria transcrição funciona com qualquer provedor.

[Answer]: A

---

### Q7 — Em quantos módulos o adaptador se parte? *(Logical Components)*

U3 dividiu o adaptador por assunto para que o arquivo de segurança pudesse ser lido sozinho. Aqui há
seis assuntos separáveis.

A) **Seis módulos** em `adaptadores/sessao/`:

   | Módulo | O que faz | Alvo de |
   |---|---|---|
   | `opcoes.py` | Acha o CLI embutido e monta as opções isoladas. É **o** arquivo de segurança da unidade (RN-S-10, 11 e 52) | teste de inspeção |
   | `ferramentas.py` | Passa `Ferramenta` para o formato do SDK, monta e separa o nome `mcp__<familia>__<nome>`, e registra cada execução (RN-S-42..44) | PBT-U6-04 |
   | `traducao.py` | Transforma mensagens do SDK em eventos. Função pura | PBT-U6-01 e 02 |
   | `falhas.py` | A tabela de falhas, total e pura | PBT-U6-03 |
   | `conexao.py` | A tarefa dona da Q1 | — |
   | `adaptador.py` | `AdaptadorSessaoClaude`: estados, sessões e `encerrar` | PBT-U6-09 a 11 |

   *Ganho*: as duas tabelas do FD (tradução e falhas) podem ser testadas sem asyncio e sem processo,
   e `opcoes.py` cabe numa leitura só.
   *Custo*: seis arquivos.
B) **Três módulos**: `opcoes.py` (com a ponte das ferramentas), `traducao.py` (com as falhas) e
   `adaptador.py` (com a conexão).
   *Custo*: as duas tabelas e a ponte só podem ser testadas através de módulos maiores.
C) **Um módulo só.**
   *Custo*: o isolamento deixa de poder ser lido sozinho.

**Recomendação: A.**

[Answer]: A

---

### Q8 — O adaptador falso: independente, ou o real com roteiro? *(Logical Components)*

O falso mora em `tests/dobles/` (FD §6.2) e passa pelo mesmo teste de contrato que o real. É o que U7
e U8 vão usar nos testes deles.

A) **Independente, com um roteiro de eventos da porta.** Os testes escrevem o roteiro com
   `PedacoDeTexto`, `UsoDeFerramenta` e `FalhaDoTurno`.
   - Um passo do roteiro pode mandar **executar uma ferramenta da sessão**. O falso chama a
     `Ferramenta` de verdade, e assim U7 e U8 testam o caminho até U5 e a confirmação sem o SDK.
   - A máquina de estados é escrita uma segunda vez e conferida pelo mesmo teste de contrato. É o
     padrão de U2 (`DP-P-10`: o dublê é um segundo enunciado do contrato).
   - A verificação de `abrir` e a validação da mensagem usam o mesmo código do real (RN-S-15 e G4).
B) **O adaptador real com um cliente roteirizado.**
   *Ganho*: uma máquina de estados só.
   *Custo*: U7 e U8 escrevem os roteiros em mensagens do SDK, e os testes deles passam a importar o
   SDK e a depender do formato dele.

**Recomendação: A.** O falso existe justamente para U7 e U8 **não** conhecerem o SDK. O real com
cliente roteirizado continua existindo, mas só nos testes de U6.

[Answer]: A

---

## 4. Reconciliações declaradas

Aplico sem pergunta, a menos que você objete.

| # | Reconciliação |
|---|---|
| **R-ND6-1** | **`Familia` e os erros moram na porta** (`aplicacao/portas/sessao.py`), e não em `aplicacao/ferramentas/`, como o FD propôs (o FD disse que o layout era proposta). Primeiro motivo: U7 lê `Familia` em `UsoDeFerramenta` e não deve precisar importar ferramentas. Segundo: a fábrica de ferramentas usa `ContextoDaSessao`, que é da porta; com `Familia` em `ferramentas/`, porta e ferramentas importariam uma à outra. Os erros seguem `DP-P-11` de U2: moram junto do contrato |
| **R-ND6-2** | **O teto de 100.000 caracteres e a validação da mensagem moram na porta**, numa função pura que o adaptador real e o falso usam. Um número só (G4) |
| **R-ND6-3** | **`aplicacao/ferramentas/__init__.py` não reexporta `acoes`.** Quem importa só os tipos ou o registro (U8) não carrega o catálogo. Só U9 importa `ferramentas/acoes.py` (Q12=A de Units Generation) |
| **R-ND6-4** | **O isolamento é escrito por extenso** (A1): `cli_path` do CLI embutido, `tools=[]`, `setting_sources=[]`, `skills=[]`, `strict_mcp_config=True`, `system_prompt` com as regras em texto, `cwd` na pasta de trabalho e `include_partial_messages=True`. O teste de inspeção confere **cada** opção, inclusive as que precisam ficar ausentes (`resume`, `continue_conversation`, `add_dirs`, `plugins`, `max_turns`) |
| **R-ND6-5** | **O callback de saída de erro fica sempre registrado** (A3) e manda cada linha para o log em DEBUG |
| **R-ND6-6** | **A permissão é negada por código nosso, e não pelo padrão do CLI.** ~~`allowed_tools` leva os nomes exatos, e um `can_use_tool` permite só os nomes exatos da sessão, nega o resto e registra a negação em WARNING.~~ **Emenda 2026-10-13 (N1 de `nfr-design-patterns.md`, fato A15): `allowed_tools` fica vazio, e o `can_use_tool` é o único que decide: permite os nomes exatos da sessão, nega o resto e registra a negação em WARNING. Com os nomes em `allowed_tools`, o SDK não chama o `can_use_tool` para eles e emite um `CanUseToolShadowedWarning` no terminal.** Assim RN-S-11 pode ser testada sem o CLI |
| **R-ND6-7** | **O tempo-limite de ferramenta fica explícito, no máximo aceito**: `MCP_TOOL_TIMEOUT=2147483647` (~24,8 dias) no `env` da sessão, como o FD manda quando o limite é configurável (A10). A medição 2 confirma que é esse o limite que vale para servidor do SDK. Se confirmar, U5 não é reaberta |
| **R-ND6-8** | **Todo prazo tem nome e é recebido no construtor**: o de subida (60 s, NFR-S-11) e o de interrupção (Q2). Os testes passam prazos curtos em vez de esperar. Nenhum outro temporizador existe no adaptador (NFR-S-12), e uma varredura do código confere isso |
| **R-ND6-9** | **`fechar` só volta com o processo morto**, para que PBT-U6-09 possa contar processos depois de cada passo. **`encerrar()` fecha todas as sessões em paralelo** (A12). Quando U9 não quiser esperar o fechamento de um chat, chama `fechar` sem aguardar; no fim do programa, `encerrar` fecha o que faltar |
| **R-ND6-10** | **O CLI embutido é localizado pelo pacote instalado** (`claude_agent_sdk/_bundled/claude.exe`, no Windows). Se o arquivo não existir, a falha é `PROVEDOR_AUSENTE`, sem tentar subir (NFR-S-03). A checagem de versão que o SDK faz a cada conexão (um `claude -v` com prazo de 2 s) continua: desligá-la exige mudar o ambiente do processo inteiro. A medição 13 mostra quanto ela custa |
| **R-ND6-11** | **Como funciona o marcador** (NFR-S-08): `sdk_real` registrado em `markers`, mais `addopts = "-m 'not sdk_real'"` no `pyproject.toml`. `uv run pytest -m sdk_real` sobrepõe isso. Na suíte padrão, esses testes aparecem como *deselected*, e não como *skipped* |
| **R-ND6-12** | **Testes em `tests/sessao/`**, como nas unidades anteriores, com `cliente_roteirizado.py` e `modelo.py` (o modelo de estados de PBT-U6-09). O falso fica em `tests/dobles/sessao_falsa.py`. O perfil de Hypothesis de `tests/conftest.py` (`deadline=None`) vale sem mudança |
| **R-ND6-13** | **A medição de login (4) não toca no seu login**: o teste `sdk_real` aponta `CLAUDE_CONFIG_DIR` para uma pasta vazia e temporária, só naquela sessão |
| **R-ND6-14** | **Log**: o adaptador usa `fishingrod.sessao`, e o módulo que transforma ações em ferramentas usa o filho `fishingrod.sessao.ferramentas`, que vai para o mesmo destino. Cada módulo que registra instala o próprio `NullHandler`, como em U5 |

---

## 5. Categorias obrigatórias — onde cada uma é tratada

| Categoria | Onde |
|---|---|
| **Resilience Patterns** | Q1, Q2, Q3 e Q4; `R-ND6-8` e `R-ND6-9`. `resiliency-baseline` continua desabilitada: nenhuma nova tentativa nem disjuntor (NFR-S-18). A reconexão na próxima mensagem já vem do FD (RN-S-34) |
| **Scalability Patterns** | **Sem pergunta**, com motivo: NFR-S-14 tirou o teto de sessões e NFR-S-15 tirou o alvo de desempenho. O que o desenho garante é que **nada é compartilhado entre sessões** além do registro, que não muda depois de montado: cada sessão tem processo, servidores MCP, tarefa e filas próprios (RN-S-40). `R-ND6-9` evita que `encerrar` some os piores casos |
| **Performance Patterns** | Q2 (prazo do ESC); `R-ND6-10` (checagem de versão, medida); medição 13 (tempos) |
| **Security Patterns** | Q5 e Q6; `R-ND6-4`, `5`, `6`, `7` e `10`; a opção A da Q7 isola o arquivo de segurança |
| **Logical Components** | Q1, Q7 e Q8; `R-ND6-1`, `2`, `3`, `12` e `14` |
