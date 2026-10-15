# Code Summary — U6 `sessao`

**Fase:** CONSTRUCTION · **Unidade:** `U6 sessao` · **Portão 4 de 4 (Code Generation)** · **Data:** 2026-10-13
**Plano:** `construction/plans/sessao-code-generation-plan.md` (27 passos, todos `[x]`)
**Base:** FD (G1–G15), NFR Requirements, NFR Design (N1–N6), todos aprovados.

---

## 1. O que existe agora

**12 arquivos novos em `src/`** (2.244 linhas). Nenhum arquivo existente de `src/` foi modificado
por U6. O código antigo (`Ambiente/agente.py`, `cli.py`, `tui.py`) não foi tocado.

| Arquivo | Linhas | O que tem |
|---|--:|---|
| `aplicacao/portas/sessao.py` | 252 | `PortaSessao`, `ContextoDaSessao`, `SessaoViva`, os 5 eventos, `MotivoFalhaDeSessao` (9), `Familia`, os 4 erros, `MAXIMO_DE_CARACTERES`, `validar_mensagem` |
| `aplicacao/ferramentas/__init__.py` | 33 | reexporta `tipos` e `registro`, **não** `acoes` (DP-S-23) |
| `aplicacao/ferramentas/tipos.py` | 60 | `Ferramenta`, `RespostaDaFerramenta`, `Fabrica`, `EntradaDoRegistro` |
| `aplicacao/ferramentas/registro.py` | 158 | `RegistroDeFerramentas` (`preparar`, `verificar_escopo`), `Violacao`, `Regra`, `PADRAO_DE_NOME` |
| `aplicacao/ferramentas/acoes.py` | 161 | `entradas_de_acoes`, `esquema_de`, `texto_do_resultado` — o único módulo de U6 que importa o catálogo |
| `adaptadores/sessao/__init__.py` | 9 | reexporta `AdaptadorSessaoClaude` |
| `adaptadores/sessao/opcoes.py` | 211 | `localizar_cli`, `VARIAVEIS_DE_CREDENCIAL` (37), `TEMPO_LIMITE_DE_FERRAMENTA_MS`, `permissao_exata`, `montar_opcoes` |
| `adaptadores/sessao/ferramentas.py` | 168 | `nome_qualificado`, `separar`, `Execucoes`, `servidores`, `dict_puro` |
| `adaptadores/sessao/falhas.py` | 171 | `Fase`, as causas tipadas, `Classificacao`, `classificar`, `Aviso` |
| `adaptadores/sessao/traducao.py` | 226 | `Tradutor` (puro: sem asyncio, sem I/O, sem log) |
| `adaptadores/sessao/conexao.py` | 343 | `ClienteDoSdk`, `cliente_real`, `Conexao` (a tarefa dona) — o único arquivo com temporizador |
| `adaptadores/sessao/adaptador.py` | 452 | `AdaptadorSessaoClaude` (`abrir`, `enviar`, `fechar`, `encerrar`, `estado`) — não importa o SDK |

**18 arquivos de teste novos** (6.113 linhas): 17 em `tests/sessao/` e `tests/dobles/sessao_falsa.py`.

**Modificados:** `pyproject.toml` (a dependência, o comentário, `markers` e `addopts`) e `uv.lock`.

## 2. A suíte

| Momento | Resultado |
|---|---|
| Antes de U6 (baseline) | 691 passed, 7 skipped |
| Depois de U6, `uv run pytest` | **979 passed, 7 skipped, 20 deselected** |

Os 20 *deselected* são os testes `sdk_real`: 13 de medição e os 7 casos `real` do teste de contrato.
Nenhum aparece como *skipped* (NFR-S-08).

## 3. Dependência e `uv audit` (NFR-S-01..06)

- `claude-agent-sdk==0.2.143` entrou em `dependencies`. É a única dependência direta de runtime.
- O `uv.lock` traz o SDK e 31 transitivos, **32 pacotes** com hash, como medido no NFR.
- O CLI embutido conferido é `_bundled/claude.exe` **2.1.238** (`claude.exe --version`).
- `exclude-newer` continua em 2026-08-25.

**`uv audit`: 28 vulnerabilidades conhecidas, todas em `pyjwt 2.13.0`**, que é transitivo de `mcp`.

| Pergunta (política A1/A2) | Resposta medida |
|---|---|
| U6 usa o `pyjwt`? | **Não.** No `mcp` e no SDK, só `mcp/client/auth/extensions/client_credentials.py` o importa: é o login OAuth de cliente MCP por HTTP. Medido em execução: importar o SDK, criar um servidor in-process e carregar o transporte **não carrega `jwt`** |
| Existe versão corrigida? | 2.14.0 e 2.15.0, **depois do corte** de 2026-08-25. Sob o corte, o uv só acha até 2.13.0 |
| Decisão | **A2: risco aceito.** `pyjwt` já estava listado em NFR-S-05 entre os transitivos instalados sem uso. Reavaliar quando o corte de `exclude-newer` andar |

## 4. Decisões tomadas na execução

As reconciliações R-CG6-1..3 do plano foram seguidas como escritas. Na execução, apareceu mais uma e
alguns ajustes, todos registrados.

| # | O que | Por quê |
|---|---|---|
| **R-CG6-4** | O esquema leva `pattern: "\S"` em texto obrigatório e `maximum: 999999999` em `POSICAO` | Com A16, o esquema que o SDK confere não pode ser mais frouxo que a conferência de forma de U5. Sem isso, texto só de espaços e posição gigante passariam pelo SDK e seriam recusados pelo catálogo. Emenda em RN-S-47 e PBT-U6-05 |
| Passo 2 | `VARIAVEIS_DE_CREDENCIAL` com **37 nomes**, tirados das listas do próprio CLI 2.1.238 (`QDe`, `EN_`, `ZDe`/`tZt`, `JDe`). Proxy e certificado da máquina ficam fora | O CLI lê essas variáveis por um ambiente tipado que faz `trim() \|\| undefined`, então vazio vale como ausente. A medição 5 confirmou. Emenda em `nfr-design-patterns.md` §5 |
| Passo 5 | "Esquema de objeto" quer dizer `type: "object"` **com** `properties` | A17: sem `properties`, o SDK troca o esquema por um vazio sem avisar |
| Passo 8 | `Execucoes.bloquear()` cancela as ferramentas **e recusa as que chegarem depois**, até o próximo turno | O CLI pode chamar uma ferramenta depois do ESC, antes de processar a interrupção. PBT-U6-11 cobre o caso ("chamada na cauda") |
| Passo 11 | Um `CancelledError` solto que vem de dentro do SDK, sem ninguém ter cancelado a dona, vira queda (`FALHA_INESPERADA`) | A dona nunca termina cancelada por um defeito do SDK. O cancelamento de verdade (o laço fechando) continua passando, depois do fechamento |
| Passo 12 | A vaga do turno é solta **antes** de entregar o evento final | Quem para de ler no evento final, sem esgotar o iterador, já pode mandar a próxima mensagem |
| Passo 12 | `estado(sessao)` no adaptador, fora da porta | Para os testes e para o log de U9. Sessão desconhecida ou já fechada aparece como `FECHADA` |
| Passo 13 | `SessaoFalsa`: `fechar` acorda um turno parado num `Esperar`, como o real | Uma ferramenta em execução no falso **não** é cancelada por `fechar`, porque roda na tarefa de quem lê. Fica documentado para U7 |
| Passo 1 | O primeiro `uv add` falhou com "Access is denied" numa pasta do `.venv` marcada como somente leitura pelo OneDrive | Tirei a marca (`attrib -R`) e repeti. Nada fora do `.venv` mudou |

**Defeitos de teste achados e corrigidos.** Nenhum deles era defeito do código.

| Onde | O que |
|---|---|
| PBT-U6-07 | Exigia nenhum `\u` no texto, mas o JSON escapa caractere de controle (ex.: `\u0007`). Passou a aceitar só escape abaixo de U+0020 |
| PBT-U6-09 | Com duas sessões, o motorista do teste vigiava o cliente da outra sessão. Passou a vigiar o total de consultas |
| `test_porta.py` | O id de um caso com 200.000 espaços estourou o limite de variável de ambiente do Windows (`PYTEST_CURRENT_TEST`). Os casos ganharam nome |
| `test_sdk_real.py` | A listagem de processos lia o PowerShell no código de página do Windows, e "Área de Trabalho" quebrava a leitura. Além disso, o `python` do ambiente virtual do uv é um lançador. As medições 1/8/11/12/13, 10, 14 e 16 **não chegaram a medir** na primeira rodada. Corrigido (UTF-8; árvore de processos inteira; a medição 14 mata o Python dono do CLI) e repetido só para elas |

## 5. Geradores medidos e endurecidos (PBT-07)

`--hypothesis-show-statistics` antes e depois:

| Propriedade | Medido antes | Depois |
|---|---|---|
| PBT-U6-09 | 42% das sequências não abriam sessão | Toda sequência começa com `abrir`, e `enviar` pesa 4. Os 6 comandos aparecem |
| PBT-U6-10 | 62% sem perturbação | Parametrizada (nenhuma, ESC, fechar × 20). Perturbação efetiva em 91% dos casos |
| PBT-U6-07 | `Frente` em 48% dos exemplos; 4 dos 10 motivos ausentes | Parametrizada pelos 15 tipos × 10. Todos aparecem |
| PBT-U6-06 | Ações sem o caminho de "sim" ou de "não"; `concluir_etapa` caía em 94% em `alvo_inexistente` | Parametrizada pelas 6 ações × 17. `concluir_etapa` ganha ambiente com 4 etapas (35% ok, 53% recusada) |
| PBT-U6-03 | Desbalanceada entre os pontos de falha | Parametrizada pelos 5 pontos × 30. As 10 exceções e os 7 sinais aparecem por igual |
| PBT-U6-02 (divergente) | 49% dos exemplos descartados por `assume` | Gerador construtivo. Só 1% abortado |

Teste acrescentado depois de pensar a mutação 12: no **adaptador**, o resto de um turno abandonado não
vaza para o turno seguinte (DP-S-04). Antes, isso só era coberto no nível da conexão.

## 6. Mutação: 18 de 18 mortas

Um defeito por vez, com o arquivo restaurado depois de cada um (hashes conferidos no fim).

| # | Defeito | Morto por |
|--:|---|---|
| 1 | nomes em `allowed_tools` (A15) | `test_dp_s_14_allowed_tools_vazio_e_can_use_tool_decide` |
| 2 | `setting_sources=None` | `test_rn_s_10_nenhuma_configuracao_da_maquina` |
| 3 | `env` sem as variáveis de credencial | `test_dp_s_12_e_dp_s_16_o_ambiente_do_processo` |
| 4 | permissão por prefixo `mcp__ambiente__` | `test_nfr_s_17_niveis_do_log` (e `test_rn_s_11_*`) |
| 5 | recado sempre `interromper` (N3) | `test_n3_esc_no_instante_da_entrega_*` |
| 6 | `FimDeTurno` sem conferir texto ou ferramenta (TD-01) | `test_motivo_resposta_vazia_mantem_a_conexao` |
| 7 | `UsoDeFerramenta` do trecho parcial | `test_rn_s_44_fechar_cancela_a_ferramenta_em_execucao` |
| 8 | causa desconhecida como `INDISPONIVEL` | a tabela literal, linha por linha |
| 9 | evento final antes de a dona terminar (N5) | `test_motivo_nao_autenticado_derruba_e_so_sai_com_o_processo_morto` |
| 10 | ESC sem cancelar as execuções | PBT-U6-11 |
| 11 | cauda sem prazo | a varredura de temporizadores (DP-S-08) |
| 12 | uma fila só para todos os turnos | `test_rn_s_34_reconexao_com_conversa_nova` |
| 13 | esquema sem `additionalProperties: false` | PBT-U6-05 |
| 14 | id no texto do resultado | PBT-U6-07 `[frente]` |
| 15 | `abrir` sem R10 | `test_rn_s_06_abrir_recusa_agente_invalido` |
| 16 | texto da mensagem no log | `test_rn_s_54_nenhum_registro_leva_*` |
| 17 | `fechar` que não é idempotente | `test_rn_s_37_fechar_duas_vezes_e_como_fechar_uma` |
| 18 | esquema entregue como `Mapping` (A17) | o teste de fumaça de A16 |

## 7. As 17 medições com o CLI de verdade

Rodadas em 2026-10-13 com `uv run pytest -m sdk_real`, pelo login da assinatura, modelo `haiku`
(`claude-haiku-4-5-20251001`).
- **Primeira rodada:** 20 testes. 16 passaram, e 4 falharam por defeito do instrumento (§4); essas 4
  não chegaram a medir.
- **Segunda e terceira rodadas:** só essas 4. Todas passaram.

O teste de contrato também passou no CLI real, nos 7 casos: **TD-01 fechado com o provedor de
verdade**.

| # | O que | Medido | Consequência |
|--:|---|---|---|
| 1 | Mensagens parciais | 184 `StreamEvent` num turno, com deltas `text_delta`, `thinking_delta` e `signature_delta`; 33 pedaços num turno de três frases; **nenhum trecho divergente** | RN-S-19 vale como escrita |
| **2** | **Tempo-limite da ferramenta que espera você** | Com `MCP_TOOL_TIMEOUT=3000`, o CLI cortou em **3,0 s** (*"MCP server "wiki" tool "esperar" timed out after 3s"*), e a nossa tarefa foi **cancelada** junto | **Configurável → U5 não é reaberta.** O valor máximo de DP-S-16 vale. ✅ bloqueante |
| 3 | Interromper com ferramenta em espera | Ferramenta cancelada; cauda de **0,22 s**; sessão `OCIOSA`; o turno seguinte responde | Os 5 s de folga da cauda são ~20× o medido |
| 4 | Sem login | O CLI **sobe**; o sinal vem na primeira resposta, `authentication_failed`, seguido de resultado com erro → `NAO_AUTENTICADO` | Sinal tipado confirmado. A linha "subida" da tabela fica sem caso (emenda no §4) |
| 5 | Chave falsa no ambiente | Com `ANTHROPIC_API_KEY` falsa e `ANTHROPIC_BASE_URL` apontando para o nada, a sessão **respondeu pela assinatura** (`apiKeySource: "none"`) | DP-S-12 confirmado: a opção B da Q5 não é necessária |
| 6 | Sem limite de passos | 8 chamadas de ferramenta seguidas, `num_turns` 9, `success`, `FimDeTurno` | O SDK não corta o turno sozinho (D-Q12-1) |
| 7 | CLI ausente | `PROVEDOR_AUSENTE` sem subir nada | Sinal de DP-S-15 confirmado |
| 8 | Prompt vazio | Não traz o prompt do Claude Code. **Achado A19:** o CLI sempre põe a linha *"You are a Claude agent, built on Anthropic's Claude Agent SDK."* antes das regras (lida no binário) | Emenda em RN-S-10. Não há opção que a tire |
| 9 | JSON Schema completo | As 6 ações aparecem como `mcp__ambiente__*`; o modelo chamou `criar_etapa` com `{"executor":"usuario","descricao":"revisar o briefing"}`, e a etapa foi criada pelo catálogo real | Esquema aceito como está |
| **10** | **Critério 3: duas sessões vivas** | **2 processos ao mesmo tempo**, os dois turnos em `FimDeTurno`, conversa mantida; 0 processos depois de `encerrar` | ✅ bloqueante |
| **11** | **O CLI que roda é o embutido e enxerga o login** | O processo filho é exatamente `…\.venv\…\claude_agent_sdk\_bundled\claude.exe`, versão 2.1.238, `apiKeySource: "none"`, sem nenhuma ferramenta nativa | ✅ bloqueante |
| 12 | Memória de um processo ocioso | **≈ 385 MB** | Sem teto, por NFR-S-14. Ver §9 |
| 13 | Tempos | Conectar: **1,5 s**. Checagem de versão do SDK: **0,18 s**. Até o primeiro pedaço: **1,3 s** num turno simples e 26 s num turno em que o modelo pensou antes de responder | Linha de base, sem portão (NFR-S-15) |
| 14 | Queda dura do Python | Com o Python dono do CLI morto à força (`taskkill /F`), o CLI **terminou sozinho** em menos de 10 s | O risco de NFR-S-16 **some** |
| 15 | Cópia da conversa | Nenhum arquivo em `~/.claude/projects/` com a pasta da sessão | DP-S-13 funciona, e não precisa de risco aceito |
| **16** | **ESC e prazo vencido não deixam processo** | ESC na subida: 1 processo → **0**. ESC na resposta: `OCIOSA`, cauda de 0,21 s, **0** depois de fechar. Prazo de subida vencido: `INDISPONIVEL` com **0** processos no instante do evento (N5) | ✅ bloqueante |
| 17 | Modelo do Agente (R-CG6-3) | `haiku` → `claude-haiku-4-5-20251001`, turno bom. Nome inexistente: o CLI aceita na subida e devolve `model_not_found` (fora do `Literal` do SDK) → `FALHA_INESPERADA` | Categoria registrada (emenda no §4 de `nfr-design-patterns.md`) |

## 8. Emendas feitas

Todas marcadas no próprio arquivo, sem apagar o texto anterior.

| Arquivo | Emenda |
|---|---|
| `functional-design/business-rules.md` | RN-S-42 e RN-S-50 (R-CG6-1, A16); RN-S-47 (R-CG6-4); RN-S-10 (A19, medição 8) |
| `functional-design/business-logic-model.md` | PBT-U6-05 (R-CG6-4) |
| `nfr-design/nfr-design-patterns.md` | §5: `model = agente.modelo` (R-CG6-3) e a lista final de 37 variáveis; §4: login sinalizado na resposta (medição 4) e `model_not_found` (medição 17) |
| `plans/sessao-code-generation-plan.md` | R-CG6-4 no §3, marcada como achada na execução |

## 9. O que passa para outras unidades

| Unidade | O quê |
|---|---|
| **U7 `conversa`** | Usar `PortaSessao` e o `SessaoFalsa`. O falso aceita roteiro de eventos, executa a `Ferramenta` de verdade e guarda as mensagens que chegaram. `fechar` no falso não cancela ferramenta em execução |
| **U8 `bibliotecario`** | Entradas da família `WIKI` com `Fabrica = (contexto, agente) -> Ferramenta`. O esquema precisa de `type: "object"` **e** `properties`. O teste R10 das instâncias reais chama `verificar_escopo` |
| **U9 `interface`** | Montar `RegistroDeFerramentas(entradas_de_acoes(catalogo) + …)`, a pasta de trabalho e o `encerrar()`. **Cada sessão conectada custa ≈ 385 MB** (medição 12). Por isso vale fechar a sessão dos chats que você deixa (sair do ambiente, fechar o chat). Também cabe a U9 escrever a frase de `model_not_found` (`falha_inesperada`) para quem configurou o agente |

## 10. Conformidade das extensões

| Regra | Estado | Onde |
|---|:--:|---|
| SECURITY-03 (log) | ✅ | Só metadados (`fishingrod.sessao`); `test_rn_s_54_*` confere que nenhum registro leva mensagem, argumento ou texto do modelo; a saída do CLI vai em DEBUG; mutação 16 morta |
| SECURITY-05 (entrada) | ✅ | `validar_mensagem` (PBT-U6-12); esquema conferido pelo SDK e argumentos revalidados por U5 (R-CG6-1, R-CG6-4) |
| SECURITY-08 (acesso) | ✅ | `permissao_exata`, num ponto só (mutações 1 e 4 mortas); alvo amarrado pelo contexto; R10 em duas camadas (mutação 15 morta) |
| SECURITY-09 (endurecimento) | ✅ | Opções inspecionadas linha por linha, inclusive as que ficam no padrão; CLI embutido ou nenhum (medições 7 e 11) |
| SECURITY-10 (dependências) | ✅ | Versão exata com hash; `uv audit` com a política A1/A2 aplicada (§3) |
| SECURITY-11 (desenho seguro) | ✅ | R-CG6-1..4 e as decisões declaradas; riscos aceitos só com medição (`pyjwt`; NFR-S-16 dispensado pela medição 14) |
| SECURITY-12 (credencial) | ✅ | 37 variáveis sobrescritas sem leitura (medição 5); nenhuma cópia em `~/.claude/projects/` (medição 15) |
| SECURITY-13 (integridade) | ✅ | Nada do modelo vira efeito sem passar por U5 (medição 9; PBT-U6-06, PBT-U6-11) |
| SECURITY-15 (falha segura) | ✅ | `enviar` nunca levanta (PBT-U6-03); processo nunca sem dono (PBT-U6-09, medições 14 e 16); erro genérico ao agente |
| SECURITY-01, 02, 04, 06, 07, 14 | N/A | Sem armazenamento próprio, rede exposta, servidor, IAM ou infraestrutura de alerta |
| PBT-01..10 | ✅ | As 12 propriedades; ida e volta (04, 07); invariantes; idempotência (09); oráculos independentes (tabela literal, `ModeloDeSessoes`); com estado (09); geradores medidos e endurecidos (§5); semente e encolhimento padrão; exemplos e contrato separados |
| `resiliency-baseline` | N/A | Desabilitada; nenhuma nova tentativa além da reconexão |

## 11. Critérios de pronto de U6

| # | Critério | Estado |
|--:|---|---|
| 1 | Resposta não vazia; falso e real passam pelo mesmo contrato (TD-01) | ✅ Contrato nos três, inclusive no CLI real |
| 2 | `dominio/` e `aplicacao/` importam sem o SDK (TD-02) | ✅ Python novo com bloqueador de import |
| 3 | Duas sessões vivas ao mesmo tempo, com a versão travada | ✅ Medição 10 |
| 4 | Falha vira `FalhaDoTurno` com 9 motivos; `enviar` nunca levanta | ✅ PBT-U6-03, tabela literal |
| 5 | Um servidor MCP in-process por família | ✅ `test_rn_s_12_*`, medição 9 |
| 6 | R10 em duas camadas | ✅ `preparar` e `verificar_escopo`, PBT-U6-08 |
| 7 | Nenhuma ferramenta nativa nem configuração do Claude Code da máquina | ✅ Inspeção das opções, medições 8 e 11 (ferramentas nativas: nenhuma) |

**TD-01 e TD-02 estão mortas.** US-01, US-02, US-03, US-13 e US-17 ficam prontas do lado da sessão e
fecham em U9.
