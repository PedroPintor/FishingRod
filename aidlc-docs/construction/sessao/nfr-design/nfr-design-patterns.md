# NFR Design Patterns — U6 `sessao`

**Fase:** CONSTRUCTION · **Unidade:** `U6 sessao` · **Portão 3 de 4** · **Data:** 2026-10-13
**Decisões:** Q1..Q8 = A (`construction/plans/sessao-nfr-design-plan.md`, respostas em
2026-10-13T19:28:57Z) · reconciliações `R-ND6-1..14` sem objeção; **`R-ND6-6` emendada nesta
geração** (N1, §3)
**Base:** os fatos A1–A14 do plano (§2), lidos no código do `claude-agent-sdk 0.2.143` e no CLI
2.1.238 embutido nele, mais **A15**, achado ao gerar este documento (§3, N1).

Identificadores `DP-S-nn` são **estáveis**, como os `DP-P-nn` de U2 e os `DP-W-nn` de U3.
Nenhuma linha de código é escrita aqui; isso é o portão 4.

---

## 1. Os padrões

### 1.1 Ciclo de vida e resiliência

| # | Padrão | Cumpre | Origem |
|---|---|---|---|
| **DP-S-01** | **Tarefa dona por conexão.** Quando o processo do CLI precisa subir, o adaptador cria uma `Conexao`, e com ela uma tarefa que sobe o cliente do SDK, entrega as mensagens, lê o provedor e desconecta. **Só ela toca o cliente.** O adaptador guarda uma referência forte a essa tarefa até ela terminar (o `asyncio` só guarda referência fraca de tarefas), e **ninguém a cancela** | RN-S-38, TS-S-09; anula A4 e A5 | Q1=A |
| **DP-S-02** | **Recado síncrono, escolhido pelo que o leitor viu.** Quem lê o turno, ao sair por cancelamento ou abandono, faz tudo **sem `await` e sem `yield`** no `finally`: cancela as execuções de ferramenta e deixa um recado na conexão. Se o leitor recebeu `MensagemEntregue`, o recado é **interromper**; se não recebeu, é **descartar** (N3) | RN-S-35, RN-S-36, G6 | Q1=A, N3 |
| **DP-S-03** | **Toda espera da dona é um prazo que o recado vence.** Cada fase em que a dona espera alguma coisa roda dentro de um `asyncio.timeout`. O recado reagenda esse prazo para "agora": a espera termina por prazo vencido, dentro da própria dona, que segue para a limpeza **sem estar cancelada**. Um recado que chega entre duas fases fica marcado, e a dona o confere antes de entrar na fase seguinte | A4, A5 (uma tarefa só), NFR-S-11 | Q1=A, Q3=A |
| **DP-S-04** | **Uma fila de saída por turno.** Cada turno entrega à dona a própria fila. O resto da resposta de um turno interrompido é lido pela dona e jogado fora; nunca chega a uma fila que alguém ainda lê | Q2 (o fechamento do turno interrompido não vaza para o seguinte), RN-S-17 | Q1=A, Q2=A |
| **DP-S-05** | **A vaga do turno é do leitor, não do processo.** A vaga é tomada na primeira chamada ao iterador, antes de qualquer `await` (RN-S-27), e é liberada quando o leitor sai. Depois de um ESC, a sessão continua `EM_TURNO` até a dona terminar de interromper (a "cauda", até 5 s), mas um `enviar` que chega nesse intervalo **não** recebe `TURNO_EM_ANDAMENTO`: ele toma a vaga e espera a cauda terminar. Depois de qualquer espera, o leitor confere o estado de novo | RN-S-26, RN-S-27, Q2 | N2 |
| **DP-S-06** | **A porta só responde com o processo morto.** `fechar` volta depois que a dona terminou (`R-ND6-9`). Numa falha que derruba a conexão, o evento final do turno só sai depois que a dona terminou (N5). `encerrar()` fecha todas as sessões em paralelo, porque cada fechamento pode levar até ~15 s (A12) | RN-S-37, RN-S-38, RN-S-39, PBT-U6-03, PBT-U6-09 | `R-ND6-9`, N5 |
| **DP-S-07** | **Ninguém faz `await` direto na tarefa dona.** Quem precisa esperar por ela usa `asyncio.wait`. Um `await tarefa` cancelaria a dona junto com quem espera, que é exatamente o caso de A4 | RN-S-38 | Q1=A |
| **DP-S-08** | **Prazos com nome, recebidos no construtor, e nenhum outro.** `prazo_de_subida = 60 s` (NFR-S-11) e `prazo_de_interrupcao = 5 s` (Q2=A). Os testes passam prazos curtos em vez de esperar. Uma varredura do código confere que nenhum outro temporizador existe em `adaptadores/sessao/` | NFR-S-11, NFR-S-12 | `R-ND6-8` |

### 1.2 Falhas

| # | Padrão | Cumpre | Origem |
|---|---|---|---|
| **DP-S-09** | **A categoria vem da fase e de sinal tipado, nunca de texto.** `falhas.py` recebe a fase (`SUBIDA`, `ENTREGA`, `RESPOSTA`) e a causa (exceção ou sinal tipado do SDK) e devolve motivo, se derruba e nível de log. Na subida, tudo é `INDISPONIVEL`, menos CLI ausente e falta de login reconhecida. Depois, valem os sinais tipados de A8. A tabela é **total** e **pura**: §4 | RN-S-28, RN-S-29, NFR-S-11, PBT-U6-03 | Q3=A, Q4=A |
| **DP-S-10** | **O evento final é decidido num lugar só.** O tradutor acumula o turno (houve texto? houve uso de ferramenta? chegou sinal de falha?) e só decide o evento final no fim da resposta ou na queda. O primeiro sinal tipado de falha vence; sem sinal, vale a mensagem de resultado; sem erro, vale RN-S-24. O corpo de `enviar` tem uma rede: qualquer exceção que não seja cancelamento vira `FALHA_INESPERADA` | RN-S-16, RN-S-17, RN-S-24 | FD §3.1 |

### 1.3 Segurança

| # | Padrão | Cumpre | Origem |
|---|---|---|---|
| **DP-S-11** | **As opções do SDK são escritas por extenso, num arquivo só.** `opcoes.py` monta todas as opções que importam, inclusive as que precisam ficar vazias, porque o padrão do SDK carrega a configuração da máquina (A1). Um teste de inspeção confere cada uma, inclusive as ausentes: §5 | RN-S-10, SECURITY-09 | `R-ND6-4`, Q7=A |
| **DP-S-12** | **Credencial sobrescrita com vazio.** Cada nome de `VARIAVEIS_DE_CREDENCIAL` vai para `options.env` com `""`. O adaptador nunca lê o valor, só escreve o vazio por cima. Se a medição 5 mostrar que o CLI trata vazio como valor, a saída já escrita é a opção B da Q5: apagar as variáveis do processo inteiro, em U9 | RN-S-52, RN-S-53, SECURITY-12 | Q5=A, A2 |
| **DP-S-13** | **Nenhuma cópia da conversa fora da pasta de dados.** O CLI roda com `--no-session-persistence` (por `extra_args`). A transcrição do FishingRod é a única cópia, e apagar um ambiente apaga a conversa. Se a medição 15 mostrar que a opção não vale no modo do SDK, vira risco aceito, com o local e o sintoma registrados | RN-S-03 (a sessão não grava nada; a transcrição é de U7), SECURITY-12 | Q6=A, A9 |
| **DP-S-14** | **A permissão é decidida num ponto só, por código nosso.** `allowed_tools` fica **vazio**, e o `can_use_tool` é o único que decide: permite os nomes exatos `mcp__<familia>__<nome>` da sessão, nega todo o resto e registra a negação em WARNING. Testável sem o CLI | RN-S-11, SECURITY-08 | `R-ND6-6` **emendada** (N1, A15) |
| **DP-S-15** | **O CLI que roda é o embutido, ou nenhum.** `localizar_cli()` acha o CLI dentro do pacote instalado do SDK. Se ele não existir, o turno termina em `PROVEDOR_AUSENTE` **sem tentar subir**, e o `claude` do `PATH` nunca é usado | NFR-S-03, SECURITY-09, SECURITY-10 | `R-ND6-10` |
| **DP-S-16** | **O tempo-limite de ferramenta fica explícito, no máximo aceito.** `MCP_TOOL_TIMEOUT=2147483647` (~24,8 dias) no `env` da sessão. A espera da sua confirmação não é cortada pelo CLI | herança 3 de U5, FD medição 2 | `R-ND6-7`, A10 |
| **DP-S-17** | **Nada do CLI chega ao terminal.** O callback de `stderr` fica sempre registrado e manda cada linha ao log em DEBUG. E nenhuma opção dispara o aviso Python que o SDK emite quando `allowed_tools` sombreia o `can_use_tool` (N1) | RN-S-54, NFR-S-17; a TUI de U9 não pode ser desenhada por cima | `R-ND6-5`, A3, A15 |

### 1.4 Ferramentas e observabilidade

| # | Padrão | Cumpre | Origem |
|---|---|---|---|
| **DP-S-18** | **A execução da ferramenta roda numa tarefa nossa, registrada na sessão.** Quando o SDK chama uma ferramenta, o adaptador cria uma tarefa própria para `Ferramenta.executar`, registra essa tarefa na sessão e espera por ela com `asyncio.wait`. Interromper e fechar cancelam **a nossa** tarefa, nunca a do SDK. A ferramenta cancelada responde ao SDK `{"ok": false, "motivo": "interrompida"}`, marcado como erro (N4). Se o SDK cancelar a chamada (A14), o adaptador cancela a nossa tarefa junto | RN-S-35, RN-S-44, PBT-U6-11, RN-AC-30 | N4 |
| **DP-S-19** | **O que é puro devolve aviso; quem registra é o adaptador.** `traducao.py` e `falhas.py` não registram nada: devolvem os avisos (trechos divergentes, pedido de fora da sessão, `dado` desconhecido) e o nível como dados. O adaptador os registra em `fishingrod.sessao`. As duas tabelas ficam testáveis por valor, sem `caplog` | NFR-S-17, RN-S-54 | `R-ND6-14` |

### 1.5 Fronteiras e testes

| # | Padrão | Cumpre | Origem |
|---|---|---|---|
| **DP-S-20** | **A porta é o contrato inteiro.** `aplicacao/portas/sessao.py` traz a porta, os tipos, os eventos, os motivos, **`Familia`**, os **erros** e a **validação da mensagem** (o teto de 100.000 caracteres). U7 e U8 importam só ela | RN-S-02, G4, `DP-P-11` de U2 | `R-ND6-1`, `R-ND6-2` |
| **DP-S-21** | **Abrir e validar são código da aplicação**, usado pelos dois adaptadores. `RegistroDeFerramentas.preparar(agente, contexto)` faz a verificação de RN-S-06/07 e a fabricação de RN-S-08 com o mesmo código de `verificar_escopo`; `validar_mensagem` faz RN-S-25. O real e o falso chamam os dois | RN-S-05..08, RN-S-15, RN-S-25 | Q8=A |
| **DP-S-22** | **O falso é um segundo enunciado do contrato.** `tests/dobles/sessao_falsa.py` responde por roteiro de **eventos da porta**, pode executar a `Ferramenta` de verdade da sessão, e tem a própria máquina de estados. O mesmo teste de contrato roda nele e no real | NFR-S-09, critério 1 | Q8=A, `DP-P-10` de U2 |
| **DP-S-23** | **O catálogo só entra por U9.** `aplicacao/ferramentas/__init__.py` não reexporta `acoes`, e nenhum módulo de U6 fora de `acoes.py` importa o catálogo | Q12=A de Units Generation | `R-ND6-3` |
| **DP-S-24** | **O SDK real fica atrás de um marcador.** `sdk_real` registrado em `markers`, mais `addopts = "-m 'not sdk_real'"`. Na suíte padrão esses testes aparecem como *deselected*; `uv run pytest -m sdk_real` os roda | NFR-S-08 | `R-ND6-11` |

---

## 2. O turno, de ponta a ponta

### 2.1 Turno normal

```
leitor (tarefa de U7)         adaptador.py                conexao.py (tarefa dona)    SDK + CLI
---------------------         ------------                ------------------------    ---------
enviar(sessao, texto)
 |-- validar_mensagem
 |-- toma a vaga ------------> EM_TURNO (sem await antes)
 |-- SEM_CONEXAO? -----------> localizar_cli, opcoes
 |                             cria Conexao -------------> [subida, prazo 60 s] -----> connect()
 |-- Turno(texto, fila) -----------------------------------> fila de entrada
 |                                                          [entrega] --------------> query(texto)
 |<----------------------------- Entregue(primeira) <------ fila do turno
 |   yield MensagemEntregue
 |<----------------------------- DoProvedor(msg) <--------- fila do turno <-------- receive_response()
 |   tradutor -> PedacoDeTexto / UsoDeFerramenta
 |<----------------------------- FimDaResposta <----------- fila do turno <-------- ResultMessage
 |   tradutor.final() -> FimDeTurno | FalhaDoTurno
 |-- libera a vaga ----------> OCIOSA  (ou SEM_CONEXAO, depois da dona terminar: DP-S-06)
```

### 2.2 ESC (ou iterador abandonado)

```
leitor: CancelledError no await da fila do turno
 finally, sem await e sem yield:
   cancela as execucoes de ferramenta da sessao              (DP-S-18)
   viu MensagemEntregue?
     sim -> conexao.interromper() --> dona: interrupt() + le o resto e joga fora, prazo 5 s
                                          deu certo ........ OCIOSA, com o historico
                                          passou do prazo .. disconnect() -> SEM_CONEXAO
     nao -> conexao.descartar()   --> dona: disconnect() -> SEM_CONEXAO
   libera a vaga; o cancelamento continua subindo ate quem cancelou
```

### 2.3 O que passa entre o leitor e a dona

| Item | De quem | Quando | O que acontece |
|---|---|---|---|
| `Turno(texto, fila)` | leitor → fila de entrada | depois de tomar a vaga | a dona entrega e passa a escrever naquela fila |
| `Entregue(primeira)` | dona → fila do turno | `query()` voltou | o leitor marca "viu a entrega" **imediatamente antes** do `yield MensagemEntregue(conversa_nova=primeira)` |
| `DoProvedor(mensagem)` | dona → fila do turno | cada mensagem do SDK | o leitor passa ao tradutor e emite o que ele devolver |
| `FimDaResposta(mensagem)` | dona → fila do turno | `ResultMessage` | o leitor pede o evento final ao tradutor (DP-S-10) |
| `Caiu(fase, causa)` | dona → fila do turno | exceção, prazo vencido ou fim do fluxo sem `ResultMessage` | o leitor classifica (DP-S-09), espera a dona terminar (DP-S-06) e emite `FalhaDoTurno` |
| `Fechada` | `fechar` → fila do turno | `fechar` com turno em andamento | o leitor emite `FalhaDoTurno(SESSAO_FECHADA)` |
| `interromper()` / `descartar()` | leitor ou `fechar` → dona | síncronos | vencem o prazo da fase atual (DP-S-03) |

As filas não têm limite de tamanho: o que cabe numa fila de turno é uma resposta só, e a dona nunca
pode ficar parada esperando um leitor lento.

---

## 3. Decisões tomadas nesta geração (para revisão no portão)

Nenhuma delas veio de pergunta. Estão aqui para você aprovar, mudar ou recusar junto com o resto.

| # | Decisão | Por quê |
|---|---|---|
| **N1** | **`R-ND6-6` emendada: `allowed_tools` fica vazio, e o `can_use_tool` decide tudo.** **A15**, lido no `types.py` da `0.2.143`: o `can_use_tool` **não é chamado** para ferramentas já liberadas por `allowed_tools`, e nesse caso o SDK emite um `CanUseToolShadowedWarning`, um aviso Python que sai no terminal | A intenção de `R-ND6-6` (negar por código nosso, testável sem o CLI) fica mais forte: um ponto de decisão em vez de dois. E o aviso desenharia por cima da TUI, o mesmo problema de A3 |
| **N2** | **Depois de um ESC, a próxima mensagem espera a cauda** (até 5 s, normalmente menos de 1 s) em vez de voltar com `TURNO_EM_ANDAMENTO` (DP-S-05) | Para você: mandar outra mensagem logo depois do ESC funciona, em vez de dar erro. RN-S-26 protege contra **dois leitores** ao mesmo tempo, e na cauda não há leitor. A transição do FD §5 continua a mesma; muda só quem segura a vaga |
| **N3** | **O recado depende do que o leitor viu** (DP-S-02). Se o ESC chega no instante em que a mensagem está sendo escrita para o CLI, e o leitor ainda não recebeu `MensagemEntregue`, o processo é **descartado**, mesmo que a escrita tenha terminado | Mantém a transcrição honesta (C2=A): o agente nunca lembra de uma mensagem que U7 não registrou. Custo: nesse instante raro, a próxima mensagem começa conversa nova |
| **N4** | **A ferramenta interrompida responde `{"ok": false, "motivo": "interrompida"}` ao SDK**, em vez de deixar o cancelamento entrar no SDK (DP-S-18) | O cancelamento fica na tarefa que é nossa; a do SDK termina normalmente. É o que fica no histórico do agente: honesto |
| **N5** | **Numa falha que derruba a conexão, o evento final só sai com o processo já morto** (DP-S-06) | Quando U7 recebe a falha, não há processo sobrando: PBT-U6-03 pode conferir isso no próprio evento. Custo: no pior caso, com o CLI vivo mas quebrado, o evento demora até ~15 s (A12) |
| **N6** | **Tabela de sinais tipados** (§4): `billing_error`, `server_error` e `unknown` viram `INDISPONIVEL`; `invalid_request` vira `FALHA_INESPERADA`; uma mensagem de resultado com erro e sem sinal nenhum vira `FALHA_INESPERADA` | RN-S-29: o que não se reconhece com certeza não vai para categoria errada. `invalid_request` é pedido malformado, ou seja, defeito nosso |

---

## 4. A tabela de falhas (`DP-S-09`, `DP-S-10`)

As linhas de login são confirmadas pela medição 4. As de limite de uso são **lidas** no código, não
provocadas (Q4=A).

| Fase | Causa | Motivo | Derruba? | Log |
|---|---|---|:--:|---|
| antes de subir | o CLI embutido não existe (DP-S-15) | `PROVEDOR_AUSENTE` | — (nada subiu) | WARNING |
| subida | `CLINotFoundError` | `PROVEDOR_AUSENTE` | sim | WARNING |
| subida | sinal de falta de login, como a medição 4 o fixar | `NAO_AUTENTICADO` | sim | WARNING |
| subida | prazo de 60 s, `Exception("Control request timeout: initialize")`, `CLIConnectionError`, `ProcessError`, **qualquer outra** | `INDISPONIVEL` | sim | WARNING **com a pilha** (Q3=A) |
| entrega, resposta | `AssistantMessage.error == "authentication_failed"` | `NAO_AUTENTICADO` | sim | WARNING |
| resposta | `AssistantMessage.error == "rate_limit"`, ou `RateLimitEvent` com `status == "rejected"` | `LIMITE_DE_USO`, com `libera_em` vindo de `resets_at` (ISO 8601, UTC) quando houver | **não** | WARNING |
| resposta | `RateLimitEvent` com `allowed` ou `allowed_warning` | nada: é informativo | — | — |
| resposta | `AssistantMessage.error` em `billing_error`, `server_error`, `unknown` | `INDISPONIVEL` | sim | WARNING |
| resposta | `AssistantMessage.error == "invalid_request"` | `FALHA_INESPERADA` | sim | ERROR, com o tipo do sinal |
| entrega, resposta | `CLIConnectionError`, `ProcessError` (inclui `ResultError`), `CLIJSONDecodeError`, fim do fluxo sem `ResultMessage` | `INDISPONIVEL` | sim | WARNING |
| resposta | `ResultMessage` com erro, sem nenhum sinal acima | `FALHA_INESPERADA` | sim | ERROR |
| qualquer | qualquer outra exceção, inclusive defeito no próprio adaptador | `FALHA_INESPERADA` | sim | ERROR **com a pilha** |
| qualquer | cancelamento | **não é falha**: passa (RN-S-16) | — | — |

> **/!\ Emenda 2026-10-13 — Code Generation de U6** (medições 4 e 17).
> - **Falta de login (medição 4):** sem login, o CLI **sobe normalmente**; o sinal chega na primeira
>   resposta, como `AssistantMessage.error == "authentication_failed"`, seguido de uma mensagem de
>   resultado com erro. A linha "subida | sinal de falta de login" fica **sem caso**: quem cobre é a
>   linha "entrega, resposta | `authentication_failed`", já escrita. `NAO_AUTENTICADO` tem sinal
>   tipado medido (RN-S-29 satisfeita).
> - **Modelo inexistente (medição 17):** o CLI aceita o nome na subida e devolve
>   `AssistantMessage.error == "model_not_found"` - um valor que **não** está no `Literal` do SDK
>   0.2.143. Cai na linha "sinal que esta versão não conhece": `FALHA_INESPERADA`, ERROR. É
>   configuração errada de quem montou o `Agente` (U8, U9), e não falha do provedor.

Falhas que não tocam o provedor: `MENSAGEM_INVALIDA` e `SESSAO_FECHADA` em INFO; `TURNO_EM_ANDAMENTO`
em WARNING, porque é defeito de quem chama (C1=B). Nenhuma linha leva texto da mensagem, argumento de
ferramenta ou credencial (RN-S-54). O `detalhe` do evento segue RN-S-31.

---

## 5. As opções do SDK, uma a uma (`DP-S-11..17`)

O teste de inspeção recebe as opções pela fábrica de cliente (G11) e confere cada linha.

| Opção | Valor | Por quê |
|---|---|---|
| `cli_path` | o CLI embutido, de `localizar_cli()` | DP-S-15 |
| `tools` | `[]` (o SDK passa `--tools ""`) | nenhuma ferramenta nativa (RN-S-10) |
| `allowed_tools` | `[]` | DP-S-14, N1 |
| `can_use_tool` | permite só os nomes exatos da sessão; nega e registra o resto | DP-S-14 |
| `setting_sources` | `[]` | A1: `None` carrega usuário, projeto e local |
| `skills` | `[]` | A1: `None` não desliga as skills |
| `strict_mcp_config` | `True` | só os servidores da sessão |
| `mcp_servers` | um servidor in-process por família presente; nenhum se a sessão não tem ferramenta | RN-S-12 |
| `system_prompt` | as `regras` unidas por linha em branco, sempre texto, mesmo vazio | RN-S-10, G15, medição 8 |
| `model` | **`agente.modelo`** | **Emenda 2026-10-13 (Code Generation, R-CG6-3, A18):** o campo existe no `Agente` de U1 e é o lugar de escolher o modelo de cada agente; deixá-lo ausente o tornaria letra morta. Medição 17 |
| `cwd` | a pasta de trabalho do construtor | RN-S-10 |
| `include_partial_messages` | `True` | Q1=B do FD |
| `env` | cada nome de `VARIAVEIS_DE_CREDENCIAL` com `""`, mais `MCP_TOOL_TIMEOUT="2147483647"` | DP-S-12, DP-S-16 |
| `extra_args` | `{"no-session-persistence": None}` | DP-S-13 |
| `stderr` | callback que registra cada linha em DEBUG | DP-S-17 |
| **ausentes**, conferidas no valor padrão | `resume`, `continue_conversation`, `fork_session`, `add_dirs`, `plugins`, `max_turns`, `hooks`, `agents`, `session_store`, `permission_mode`, `permission_prompt_tool_name`, ~~`model`~~, `user` | sem histórico emprestado (RN-S-41), sem diretório extra, sem limite de passos (D-Q12-1), ~~modelo padrão do CLI~~ **(`model` saiu desta linha: R-CG6-3)**. O teste de inspeção confere também que **toda outra** opção do SDK fica no valor padrão |

`VARIAVEIS_DE_CREDENCIAL` traz pelo menos `ANTHROPIC_API_KEY`, `ANTHROPIC_AUTH_TOKEN`,
`ANTHROPIC_BASE_URL`, `CLAUDE_CODE_USE_BEDROCK` e `CLAUDE_CODE_USE_VERTEX`. A lista completa é
conferida contra o CLI 2.1.238 no Code Generation, como RN-S-52 já manda. `CLAUDE_CONFIG_DIR`
**nunca** entra no `env` de produção; só o teste da medição 4 o usa.

> **/!\ Emenda 2026-10-13 — Code Generation de U6** (passo 2). A lista final tem **37 nomes**, tirados
> das listas que o próprio CLI 2.1.238 usa (lidas no binário embutido):
> - **credenciais** (a lista `QDe` do CLI): `ANTHROPIC_API_KEY`, `ANTHROPIC_AUTH_TOKEN`,
>   `CLAUDE_CODE_OAUTH_TOKEN`, `AWS_BEARER_TOKEN_BEDROCK`, `ANTHROPIC_FOUNDRY_API_KEY`,
>   `ANTHROPIC_FOUNDRY_AUTH_TOKEN`, `ANTHROPIC_AWS_API_KEY`;
> - **outras fontes de credencial** (a lista `EN_`, que o CLI proíbe a configuração remota de mudar):
>   `CLAUDE_CODE_API_KEY_FILE_DESCRIPTOR`, `CLAUDE_CODE_OAUTH_TOKEN_FILE_DESCRIPTOR`,
>   `CLAUDE_CODE_OAUTH_REFRESH_TOKEN`, `CLAUDE_CODE_SESSION_ACCESS_TOKEN`, `ANTHROPIC_IDENTITY_TOKEN`,
>   `ANTHROPIC_IDENTITY_TOKEN_FILE`, `ANTHROPIC_FEDERATION_RULE_ID`, `ANTHROPIC_PROFILE`,
>   `CLAUDE_CODE_HOST_CREDS_FILE`, `CLAUDE_CODE_HOST_AUTH_ENV_VAR`, `CLAUDE_CODE_PROVIDER_MANAGED_BY_HOST`;
> - **endereços** (as listas `ZDe` e `tZt`): `ANTHROPIC_BASE_URL`, `_CLAUDE_CODE_ASSUME_FIRST_PARTY_BASE_URL`,
>   `ANTHROPIC_BEDROCK_BASE_URL`, `ANTHROPIC_VERTEX_BASE_URL`, `ANTHROPIC_FOUNDRY_BASE_URL`,
>   `ANTHROPIC_AWS_BASE_URL`, `ANTHROPIC_GOOGLE_CLOUD_BASE_URL`, `ANTHROPIC_BEDROCK_MANTLE_BASE_URL`,
>   `ANTHROPIC_CUSTOM_HEADERS`, `ANTHROPIC_UNIX_SOCKET`, `CLAUDE_CODE_API_BASE_URL`,
>   `CLAUDE_CODE_CUSTOM_OAUTH_URL`;
> - **provedores alternativos** (as chaves da lista `JDe`): `CLAUDE_CODE_USE_BEDROCK`,
>   `CLAUDE_CODE_USE_VERTEX`, `CLAUDE_CODE_USE_FOUNDRY`, `CLAUDE_CODE_USE_ANTHROPIC_AWS`,
>   `CLAUDE_CODE_USE_ANTHROPIC_GOOGLE_CLOUD`, `CLAUDE_CODE_USE_MANTLE`, `CLAUDE_CODE_USE_GATEWAY`.
>
> Ficam **fora**, de propósito, proxy e certificado da máquina (`HTTPS_PROXY`, `NODE_EXTRA_CA_CERTS`):
> mudam a rota, não a credencial, e tirá-los quebraria a sessão de quem está atrás de um proxy. O CLI
> lê essas variáveis por um ambiente tipado que faz `trim() || undefined`, então o vazio vale como
> ausente (a medição 5 confirma na prática).

---

## 6. Medições: o que este estágio muda

As 14 medições de `nfr-requirements.md` §6 continuam. Este estágio muda o método de quatro e acrescenta
duas.

| # | O que muda | Se der errado |
|---|---|---|
| 2 | O teste põe `MCP_TOOL_TIMEOUT` **pequeno** (por exemplo, 3 s) e uma ferramenta que espera 10 s. Se ela for cortada perto de 3 s, a variável vale para servidor do SDK, e o valor máximo de DP-S-16 também vale | Como no FD: U5 é reaberta antes de U6 fechar |
| 3 | Registra também quanto dura a cauda da interrupção (o número que justifica os 5 s da Q2) | Só registro |
| 4 | Roda com `CLAUDE_CONFIG_DIR` apontando para uma pasta vazia e temporária (`R-ND6-13`) e registra o tipo e o campo do sinal | Sem sinal tipado: `NAO_AUTENTICADO` cai em `INDISPONIVEL` (RN-S-29) |
| 5 | Com uma chave **falsa** em `ANTHROPIC_API_KEY` no ambiente do processo de teste, a sessão responde pela assinatura (Q5=A) | DP-S-12 cai para a opção B da Q5, registrada |
| **15** | **Nova.** Depois de um turno real, nenhum arquivo novo em `~/.claude/projects/` (DP-S-13) | Risco aceito, com o local e o sintoma (Q6=A) |
| **16** | **Nova.** Com o CLI real: ESC durante a subida, ESC durante a resposta e prazo de subida vencido (com prazo curto) não deixam nenhum processo `claude` vivo depois que a dona termina (DP-S-01..03) | **Bloqueia U6** (RN-S-38) |

A medição 13 passa a registrar também o custo da checagem de versão que o SDK faz a cada conexão
(`R-ND6-10`).

---

## 7. Emendas feitas em artefatos aprovados

Marcadas no próprio arquivo, sem apagar o texto anterior.

| Arquivo | Emenda |
|---|---|
| `plans/sessao-nfr-design-plan.md` | `R-ND6-6` riscada e substituída por N1 |
| `nfr-requirements/nfr-requirements.md` | NFR-S-11: o prazo de 60 s também é do adaptador, em volta da subida inteira, e o teste usa prazo curto (Q3=A, `R-ND6-8`). NFR-S-17: WARNING passa a cobrir a falha ao subir, com a pilha, e as falhas vindas do provedor, só com o motivo (Q3=A, §4) |
| `nfr-requirements/tech-stack-decisions.md` | TS-S-09: "mesmo contexto assíncrono" passa a ser garantido pela tarefa dona; quem chama não precisa mais cuidar disso |
| `functional-design/business-rules.md` | RN-S-26 (N2) e RN-S-36 (N3) |
| `functional-design/business-logic-model.md` | §5 e §6 (N2, N3); §8 aponta para as medições 15 e 16; §10, herança (7) de U7 riscada |
| `inception/application-design/unit-of-work.md` | U7: herança (7) dispensada e mensagem depois do ESC espera a cauda. U9: `fechar` pode levar até ~15 s; para não travar a tela, U9 pode chamá-lo sem esperar, e `encerrar()` fecha o que faltar |

---

## 8. Categorias obrigatórias

| Categoria | Onde |
|---|---|
| **Resilience** | DP-S-01..10. `resiliency-baseline` continua desabilitada: nenhuma nova tentativa, nenhum disjuntor (NFR-S-18). Os dois prazos não são padrão de resiliência distribuída: são esperas com dono, exigidas por SECURITY-15 e NFR-S-11 |
| **Scalability** | Nada é compartilhado entre sessões além do registro, que não muda depois de montado. Cada sessão tem processo, servidores MCP, tarefa dona, filas e execuções próprios (RN-S-40). Sem teto (NFR-S-14). `encerrar()` em paralelo (DP-S-06) |
| **Performance** | Mensagens parciais ligadas, para o texto chegar aos poucos; prazo de 5 s na cauda (DP-S-05); filas sem limite, para a dona nunca esperar um leitor lento (§2.3); medição 13 com o custo da checagem de versão |
| **Security** | DP-S-11..17 e §5 |
| **Logical Components** | DP-S-20..24 e `logical-components.md` |

---

## 9. Conformidade das extensões

| Extensão | Estado | Justificativa |
|---|:--:|---|
| **`security-baseline`** | ✅ Conforme | **SECURITY-03**: log só de metadados, puro devolve aviso (DP-S-19), saída de erro do CLI em DEBUG (DP-S-17). **SECURITY-05**: `validar_mensagem` na porta (DP-S-20). **SECURITY-08**: permissão por nome exato, num ponto só (DP-S-14). **SECURITY-09**: opções por extenso, sem configuração da máquina, CLI embutido (DP-S-11, DP-S-15). **SECURITY-10**: CLI travado junto do SDK (DP-S-15); o resto é NFR-S-01..06, sem mudança. **SECURITY-11**: N1–N6 declaradas para revisão; riscos aceitos só com medição (15, e 2/5 com saída escrita). **SECURITY-12**: credencial sobrescrita sem ser lida (DP-S-12), nenhuma cópia da conversa fora da pasta de dados (DP-S-13). **SECURITY-13**: nada do modelo vira efeito sem passar por U5 (DP-S-18 só cancela, não decide). **SECURITY-15**: falha fechada e total (DP-S-09, DP-S-10), processo nunca sem dono (DP-S-01..07). **N/A**: SECURITY-01, 02, 04, 06, 07 e 14, pelos motivos já registrados no FD e no NFR Requirements |
| **`property-based-testing`** (Full) | ✅ Conforme | Cada uma das 12 propriedades tem módulo-alvo e arquivo de teste (`logical-components.md` §5). As duas tabelas puras (DP-S-09, DP-S-19) e o tradutor ficam testáveis sem asyncio e sem processo. O cliente roteirizado e o modelo de estados (`R-ND6-12`) são os geradores de PBT-U6-01, 03, 09, 10 e 11. Perfil `hypothesis` de `tests/conftest.py` sem mudança (PBT-08, PBT-09) |
| `resiliency-baseline` | **N/A** | Desabilitada em 2026-08-17. Nenhum retry, circuit breaker ou bulkhead é desenhado. Os prazos de DP-S-08 são esperas com dono, não padrão de resiliência |
