# Code Generation Plan — U6 `sessao`

**Fase:** CONSTRUCTION · **Unidade:** `U6 sessao` · **Portão 4 de 4** · **Data:** 2026-10-13
**Base:** os artefatos aprovados de `construction/sessao/`:

- `functional-design/`, aprovado em 2026-10-02T22:28:28Z, com G1–G15;
- `nfr-requirements/`, aprovado em 2026-10-06T22:26:08Z;
- `nfr-design/`, aprovado em 2026-10-13T21:06:07Z, com N1–N6.

**Estágios da unidade:** FD ✅ · NFR-R ✅ · NFR-D ✅ · INFRA SKIP · **CG EXECUTE**

> **Este plano é a única fonte de verdade da geração de código de U6.** A Parte 2 executa
> exatamente estes passos, na ordem, marcando `[x]` a cada conclusão. Nada fora daqui é gerado.

---

## 1. Contexto da unidade

| Campo | Conteúdo |
|---|---|
| **Histórias** | **US-01** (conversar com um agente real), **US-02** (sessão pela assinatura, sem chave de API), **US-03** (falha do provedor não derruba a interface), **US-13** e **US-17** (exposição de ferramentas: a família `WIKI` fica pronta para U8; as 6 ações viram ferramentas do orquestrador). **Nenhuma fecha aqui**: todas fecham em U9 |
| **Dívidas que morrem aqui** | **TD-01** (`responder()` devolve `None`) e **TD-02** (SDK importado no núcleo) |
| **Depende de** | U1 (`Agente`, `Papel`, `Identidade`) e U5 (`CatalogoDeAcoes` e seus tipos, **só** em `aplicacao/ferramentas/acoes.py`). Nos testes, também U2, U3 e U4 (serviço real atrás do catálogo). Todas aprovadas |
| **Entrega para** | U7 (`PortaSessao` e o falso `SessaoFalsa`), U8 (registro de fábricas e `verificar_escopo`), U9 (`AdaptadorSessaoClaude`, `entradas_de_acoes`, `encerrar()`) |
| **Especificação** | 54 regras `RN-S-01..54` · 12 propriedades `PBT-U6-01..12` · 18 requisitos `NFR-S-01..18` · 9 decisões `TS-S-01..09` · 24 padrões `DP-S-01..24` · decisões G1–G15 e N1–N6 · 16 medições · critérios de pronto 1–7 de `unit-of-work.md` §3, com as emendas de U5 e de U6 |
| **Destino do código** | `src/fishingrod/aplicacao/portas/sessao.py`, `src/fishingrod/aplicacao/ferramentas/` (4 arquivos) e `src/fishingrod/adaptadores/sessao/` (7 arquivos) |
| **Destino dos testes** | `tests/sessao/` (17 arquivos, novo) e `tests/dobles/sessao_falsa.py` |
| **Dependência nova** | **`claude-agent-sdk==0.2.143`**, a primeira e única dependência direta de runtime (NFR-S-01, NFR-S-02). `exclude-newer` continua em 2026-08-25 (TS-S-03) |

**Interface publicada por esta unidade.**

| Módulo | O que outras unidades importam |
|---|---|
| `aplicacao/portas/sessao.py` | `PortaSessao`, `ContextoDaSessao`, `SessaoViva`, `EventoConversa` e os 5 eventos, `MotivoFalhaDeSessao`, `Familia`, `ErroDeSessao`, `ConfiguracaoDeSessaoInvalida`, `AdaptadorEncerrado`, `RegistroInvalido`, `MAXIMO_DE_CARACTERES`, `validar_mensagem` |
| `aplicacao/ferramentas/` | `Ferramenta`, `RespostaDaFerramenta`, `Fabrica`, `EntradaDoRegistro`, `RegistroDeFerramentas`, `Violacao` |
| `aplicacao/ferramentas/acoes.py` | `entradas_de_acoes` (**só U9 importa**, DP-S-23) |
| `adaptadores/sessao/` | `AdaptadorSessaoClaude` (só U9) |
| `tests/dobles/sessao_falsa.py` | `SessaoFalsa` (testes de U7 e U8) |

**Critério de pronto de U6** (`unit-of-work.md` §3, com as emendas):

1. Resposta não vazia (texto **ou** uso de ferramenta), com falso e real passando pelo mesmo teste
   de contrato (TD-01).
2. `dominio/` e `aplicacao/` importam com o SDK indisponível (TD-02).
3. Duas sessões vivas ao mesmo tempo, **re-medido** com a versão travada.
4. Falha do provedor vira `FalhaDoTurno`, com 9 motivos; `enviar` nunca levanta.
5. Um servidor MCP in-process por família.
6. R10 em duas camadas: `abrir` recusa, e `verificar_escopo` existe para U8 e U9.
7. **Nenhum** agente recebe ferramenta nativa nem configuração do Claude Code da máquina.

**Baseline de testes antes desta unidade:** `691 passed, 7 skipped` (medido em
2026-10-13T21:06:07Z).

**Código antigo:** `Ambiente/agente.py` **não é tocado**. Ele importa o SDK, mas `cli.py` e `tui.py`
dependem dele, e a decisão de 2026-08-26 manda manter o código antigo até U9 (`unit-of-work.md` §4,
emenda de U1).

---

## 2. O que a releitura do SDK mostrou ao planejar

Lido em 2026-10-13 no mesmo código-fonte da `0.2.143` usado no NFR Design. Os fatos A1–A15 continuam
valendo. Estes três são novos e viram reconciliação (§3).

| # | Fato | Onde | Consequência |
|---|---|---|---|
| **A16** | O servidor in-process do SDK **confere os argumentos contra o esquema** (`jsonschema.validate`) **antes** de chamar a função da ferramenta. Argumento fora do esquema não chega à função: o agente recebe `Input validation error: …` como resultado de erro | `__init__.py`, `create_sdk_mcp_server`, `run_tool` | `R-CG6-1` |
| **A17** | O esquema só passa sem conversão se for **`dict`** de verdade (`isinstance(…, dict)`). Um `MappingProxyType` ou outro `Mapping` vira, **sem aviso**, um esquema vazio `{"type": "object", "properties": {}}` | `__init__.py`, `_build_input_schema` | `R-CG6-2` |
| **A18** | `Agente.modelo` (U1) é obrigatório e não vazio, e o código antigo passava `modelo="opus"`, um apelido que o CLI aceita. O §5 de `nfr-design-patterns.md` deixou `model` entre as opções **ausentes**, o que tornaria o campo letra morta | `dominio/agente.py`; `Ambiente/agente.py` | `R-CG6-3` |

---

## 3. Reconciliações

Lacunas que só aparecem ao escrever o código. A resolução é o que o código segue; as que mudam texto
de artefato aprovado viram emenda no passo 27, com o texto antigo riscado.

| # | Lacuna | Resolução e motivo |
|---|---|---|
| **R-CG6-1** | RN-S-42 diz que a ferramenta recebe os argumentos "como vieram", e RN-S-50 que o agente sempre lê JSON. **A16**: argumento fora do esquema é barrado pelo SDK antes, e o agente lê o texto de erro do SDK | **Aceitar.** O SDK é **mais estrito** que o catálogo, nunca mais frouxo: o que o esquema aceita, o catálogo aceita (PBT-U6-06). O que passa pelo SDK chega à ferramenta como veio, e U5 valida de novo. Para você, nada muda; o agente lê outro formato de erro nesse caso raro e tenta de novo. O texto do SDK vai só ao agente, nunca ao log. Emenda em RN-S-42 e RN-S-50 |
| **R-CG6-2** | `Ferramenta.esquema` é `Mapping`, e a porta entrega tudo em cópia somente leitura. **A17**: o SDK descartaria esse esquema sem avisar | `adaptadores/sessao/ferramentas.py` converte o esquema numa **cópia funda de `dict` e `list` puros** antes de entregá-lo ao SDK. Teste: uma `Ferramenta` com esquema em `MappingProxyType` chega ao servidor com o esquema inteiro. Sem emenda: é detalhe de tradução |
| **R-CG6-3** | **A18**: `model` ausente ignora `Agente.modelo` | `montar_opcoes` passa **`model = agente.modelo`**. O campo existe no domínio aprovado (`components.md` §2.9) e é o lugar certo para escolher o modelo de cada agente; quem escolhe o valor é quem cria a instância (U8 e U9). Nova **medição 17**: um apelido (`haiku`) funciona, e um nome inexistente cai numa categoria registrada. Emenda em `nfr-design-patterns.md` §5 |
| **R-CG6-4** *(achada na execução, passo 17)* | Com A16, o esquema que o SDK confere precisa ser tão estrito quanto a conferência de forma do catálogo. RN-S-47 deixava passar texto obrigatório só de espaços (U5 o trata como ausente) e posição acima de 999.999.999 (o teto de U5) | Texto obrigatório leva `pattern: "\S"`; `POSICAO` leva `maximum: 999999999`. A lista fechada de agentes de U4 não cabe no esquema: o agente lê `fora_da_lista`. Emenda em RN-S-47 e em PBT-U6-05 |

---

## 4. Decisões de implementação declaradas (não perguntadas)

Escolhas de forma que os portões anteriores não fixaram. São reversíveis; se discordar de alguma, o
momento é agora.

| Decisão | Escolha | Motivo |
|---|---|---|
| **Tipos** | `dataclass(frozen=True)` e `Enum`. `UsoDeFerramenta.argumentos` é `MappingProxyType` sobre uma **cópia funda** do `input` do bloco | Imutáveis por construção (RN-S-02); a cópia funda impede que um valor aninhado mude por fora |
| **`SessaoViva.id`** | `Identidade.nova()` (UUIDv7 de U1) | Mesmo tipo de identidade do resto do sistema, ordenável no log |
| **`enviar`** | `async def` com `yield`: chamar devolve o iterador, e a vaga é tomada no primeiro `__anext__`, antes de qualquer `await` (DP-S-05) | É o que a porta descreve como `AsyncIterator`; o `finally` síncrono cobre o cancelamento e o abandono (DP-S-02, G6) |
| **JSON para o agente** | `json.dumps(…, ensure_ascii=False, separators=(",", ":"))` | RN-S-50: compacto, com acento como acento |
| **`libera_em`** | `datetime.fromtimestamp(resets_at, UTC).isoformat()`; ausente se `resets_at` for `None` | `resets_at` é um instante Unix (`types.py`, `RateLimitInfo`) |
| **Resposta ao SDK** | `{"content": [{"type": "text", "text": texto}], "is_error": erro}` | Formato que o `run_tool` da `0.2.143` converte para MCP |
| **Loggers** | `fishingrod.sessao` nos módulos do adaptador; `fishingrod.sessao.ferramentas` em `acoes.py`. Cada módulo que registra instala o próprio `NullHandler` | `R-ND6-14`, NFR-S-17; sem destino configurado, nada vaza para a tela |
| **Testes de código `async`** | `executar(coro)` de `tests/ambiente/estrategias.py`: um laço por exemplo. **Sem `pytest-asyncio`** | Mesma decisão de U2 a U5 |
| **Prazos nos testes** | Os do construtor, curtos (décimos de segundo). Nenhum teste dorme esperando os 60 s ou os 5 s | DP-S-08 |
| **Ferramenta no cliente roteirizado** | O cliente roteirizado chama a ferramenta pelo **`SdkMcpBridge` do próprio SDK** (`_internal/sdk_mcp_bridge.py`), com o mesmo JSON-RPC que o CLI manda (`initialize`, `tools/call`) | Passa pelo caminho de verdade, inclusive a validação de A16 e a conversão do resultado. É módulo interno, mas a versão é travada (`==0.2.143`); se mudar, o teste quebra alto, não em silêncio |
| **Oráculo da tabela de falhas** | `test_falhas.py` escreve a tabela do §4 de `nfr-design-patterns.md` como dado **literal**, e as propriedades de ponta a ponta comparam com esse dado, não com `classificar` | Um oráculo que chama o código testado não testa nada |
| **Reaproveitamento** | `executar`, `ambientes_de_partida`, `semear`, `novo_servico`, `ORQUESTRADOR` e `BIBLIOTECARIO` de U4; `montar`, `tarefas_de`, `alvo_da_tarefa`, `ambientes_de_uma_tarefa` e os instrumentos `ServicoEspiao`, `ConfirmacaoFixa`, `ConfirmacaoQueEspera` e `ConfirmacaoProibida` de U5 | PBT-07: geradores centralizados; o catálogo é testado com o serviço real atrás |
| **Medições com o CLI real** | Usam `modelo="haiku"`, a não ser a 17, que compara apelidos | Gastam o seu limite de uso da assinatura. O apelido mais barato basta para medir comportamento de sessão |
| **Processos nas medições** | Uma função de teste lista os processos `claude` filhos do Python pelo sistema (PowerShell `Get-CimInstance Win32_Process` no Windows, `ps` nos outros) | As medições 12, 14 e 16 precisam ver o processo de verdade, não o contador do falso |
| **Nome de teste** | `test_rn_s_26_*`, `test_pbt_u6_09_*`, `test_dp_s_14_*`, `test_nfr_s_07_*`, `test_medicao_16_*` | Convenção de U1 a U5: o nome diz o que quebrou |

---

## 5. Especificação das propriedades

As estratégias moram em `tests/sessao/estrategias.py`. O NFR Design fixou **onde** cada propriedade
roda (`logical-components.md` §5.2); aqui fica **como** ela é gerada.

**Os instrumentos.**

| Instrumento | Arquivo | Para quê |
|---|---|---|
| `FabricaRoteirizada` | `cliente_roteirizado.py` | Entra no lugar de `cliente_real`. Guarda as opções que recebeu (para `test_opcoes.py`), cria um `ClienteRoteirizado` por conexão e conta **processos vivos** |
| `ClienteRoteirizado` | idem | Segue um roteiro: subida (bem, falha com uma exceção, trava), e por turno uma lista de passos (trechos e blocos de texto, pensamento, pedido de ferramenta da sessão ou de fora, chamada de ferramenta pelo `SdkMcpBridge`, resultado de ferramenta, mensagem de sistema, `RateLimitEvent`, sinal tipado, `ResultMessage` com ou sem erro, exceção, fim do fluxo, trava até ser liberado). `interrupt` e `disconnect` também têm roteiro: bem, falha, trava, lento |
| `ModeloDeSessoes` | `modelo.py` | O modelo de estados de PBT-U6-09: estado de cada sessão, processos vivos, `conversa_nova` da próxima entrega, com a cauda do ESC (N2) |
| `ServicoEspiao`, `ConfirmacaoQueEspera`, `ConfirmacaoFixa`, `ConfirmacaoProibida` | `tests/acoes/instrumentos.py` (U5) | O catálogo real atrás das ferramentas de ambiente |

| # | Propriedade | Geração | Verificação | Exemplos |
|---|---|---|---|---|
| **PBT-U6-01** | Gramática do turno | Roteiros de 0 a 4 blocos de texto partidos em 0 a 5 trechos; 0 a 3 pedidos de ferramenta da sessão e 0 a 2 de fora; pensamento, resultado de ferramenta, mensagem de sistema e `RateLimitEvent` informativo intercalados; desfecho sorteado: `ResultMessage` sem erro, com erro, sinal tipado, exceção ou fim do fluxo; falha também sorteada na subida e na entrega. Em dois níveis: o `Tradutor` puro e o adaptador inteiro | Os tipos dos eventos casam com a gramática de RN-S-17; `FimDeTurno` só se houve `PedacoDeTexto` ou `UsoDeFerramenta`; nada depois do evento final | 200 no tradutor, 100 no adaptador |
| **PBT-U6-02** | Texto preservado | Blocos de texto Unicode não vazios (espaços, tabulações, quebras de linha, acentos, emoji); cada bloco partido em trechos de forma arbitrária, cobrindo o bloco todo, só o começo dele, ou nenhum trecho | A concatenação dos pedaços é igual aos blocos unidos por `"\n\n"`; nenhum pedaço vazio. Caso à parte: trechos que **divergem** do bloco devolvem um aviso e nada mais sai daquele bloco | 200 |
| **PBT-U6-03** | Nunca levanta | Exceções do SDK (`CLINotFoundError`, `CLIConnectionError`, `ProcessError`, `CLIJSONDecodeError`, `Exception("Control request timeout: initialize")`) e quaisquer outras (`RuntimeError`, `KeyError`, `OSError`, `ValueError`), mais os sinais tipados de `AssistantMessage.error` e `RateLimitEvent`; em qualquer ponto: subida, entrega, meio da resposta, cauda | O último evento é `FalhaDoTurno` com o motivo da tabela **literal**; o estado é o do FD §5; quando a falha derruba, **nenhum processo vivo no instante do evento** (N5). Só o cancelamento passa | 150 |
| **PBT-U6-04** | Nome qualificado, ida e volta | Toda `Familia` e nomes que casam com o padrão de RN-AC-07; textos quaisquer, inclusive quase certos (`mcp_ambiente__x`, família inexistente, `__` sobrando) | `separar(nome_qualificado(f, n)) == (f, n)`; texto fora do formato devolve `None` | 200 |
| **PBT-U6-05** | Esquema fiel | Listas de 0 a 6 `Parametro` válidas por RN-AC-08: nomes únicos, os três tipos, opcionais, opções, máximos | Exatamente os nomes dos parâmetros; `required` igual aos obrigatórios; `enum` igual às opções; `maxLength` igual ao máximo; `minLength: 1` só em texto obrigatório; `POSICAO` inteiro com mínimo 1; `additionalProperties: false`; nada além | 200 |
| **PBT-U6-06** | Esquema e catálogo concordam | Para cada uma das 6 ações, argumentos gerados **a partir do esquema** (texto não vazio dentro do máximo, valor do `enum`, inteiro ≥ 1, opcionais presentes ou não), conferidos com `jsonschema` antes de usar; ambiente de uma tarefa de U5; confirmação "sim" ou "não" | O catálogo real nunca devolve `ARGUMENTO_INVALIDO` | 100 |
| **PBT-U6-07** | Texto do agente, ida e volta | `Resultado` de sucesso com os 5 tipos de `dado`, tirados de um ambiente gerado por U4, e de falha com os 10 motivos e `detalhe` gerado | `json.loads` devolve `ok`, `motivo` e `detalhe`; `erro == not sucesso`; o texto **não contém** nenhuma identidade do ambiente | 150 |
| **PBT-U6-08** | R10 | `Agente` com os dois papéis e ferramentas sorteadas entre os 6 nomes de ação, 4 nomes de wiki de teste e nomes inexistentes, com repetição | `preparar` levanta **se e somente se** o oráculo do teste acha violação; `verificar_escopo` aponta exatamente as violações do oráculo, com agente, nome e regra | 200 |
| **PBT-U6-09** | Ciclo de vida com estado | Sequências de 1 a 20 comandos: `abrir`; `enviar` com desfecho sorteado (bem, vazio, limite, falha que derruba, falha na subida); ESC antes e depois da entrega; `enviar` durante a cauda (N2); `fechar`; `fechar` de novo; `encerrar` | **Depois de cada passo**: o estado de cada sessão, os processos vivos e o `conversa_nova` da próxima entrega batem com o `ModeloDeSessoes`. Fechar duas vezes deixa tudo como fechar uma | 60 |
| **PBT-U6-10** | Sessões isoladas | Duas sessões com roteiros gerados; uma ordem de intercalação gerada, com falha, ESC ou `fechar` em uma delas | Os eventos de cada sessão são exatamente os que ela produz sozinha, com o mesmo roteiro | 60 |
| **PBT-U6-11** | Interromper cancela tudo | k ∈ 1..4 ferramentas em execução ao mesmo tempo no catálogo real, algumas esperando a sua confirmação (`ConfirmacaoQueEspera`); ESC em ponto sorteado: antes da entrega, com as ferramentas rodando, durante a cauda | As k execuções terminam canceladas; o `ServicoEspiao` não recebe nenhuma mudança depois do ESC; a sessão termina em `OCIOSA` ou `SEM_CONEXAO`, conforme o FD §6 | 60 |
| **PBT-U6-12** | Mensagem inválida não sai | Texto vazio ou só de espaços, de qualquer caractere para o qual `str.isspace()` é verdadeiro; texto de 100.001 a 100.100 caracteres | `FalhaDoTurno(MENSAGEM_INVALIDA)` com o `problema` certo (e `maximo` quando longa); o cliente roteirizado **não foi criado** nem recebeu nada. Na função `validar_mensagem` e no adaptador | 300 na função, 100 no adaptador |

Encolhimento e semente ficam no padrão do Hypothesis (perfil `fishingrod` de `tests/conftest.py`,
`deadline=None`). Nada desliga o encolhimento. Os geradores são medidos com
`--hypothesis-show-statistics` no passo 25, como em U4 e U5, e endurecidos se não alcançarem os ramos.

---

## 6. Os passos

### Preparação

- [x] **Passo 1** — **Dependência.** `uv add claude-agent-sdk==0.2.143`; conferir no `uv.lock` os
      32 pacotes com hash e, no ambiente, o CLI embutido (`_bundled/claude.exe`, versão
      **2.1.238**). Atualizar o comentário de `dependencies`. Em `[tool.pytest.ini_options]`:
      `markers` com `sdk_real` e `addopts = "-m 'not sdk_real'"` (DP-S-24). Rodar **`uv audit`** e
      registrar a saída (NFR-S-04): vulnerabilidade em pacote que U6 usa **para a geração** e volta
      para você (A1); em pacote que U6 não usa, vira risco aceito com motivo (A2). Rodar a suíte e
      confirmar `691 passed, 7 skipped`. **NFR-S-01..06, TS-S-01..04, TS-S-06**
- [x] **Passo 2** — **Lista de credenciais.** Conferir no CLI 2.1.238 embutido quais variáveis de
      ambiente trocam a credencial ou o endereço (`ANTHROPIC_*`, `CLAUDE_CODE_USE_*` e afins) e fixar
      `VARIAVEIS_DE_CREDENCIAL`, com a origem de cada nome. **RN-S-52, DP-S-12**

### Aplicação, sem SDK

- [x] **Passo 3** — `src/fishingrod/aplicacao/portas/sessao.py`:
      - `PortaSessao` (`Protocol`), `ContextoDaSessao` e `SessaoViva`;
      - os 5 eventos e `EventoConversa`;
      - `MotivoFalhaDeSessao` (9) e `Familia` (2);
      - os 4 erros;
      - `MAXIMO_DE_CARACTERES` e `validar_mensagem`.

      **Critério 4 · RN-S-02, RN-S-16..18, RN-S-25, RN-S-31 · DP-S-20 · G1, G4**
- [x] **Passo 4** — `src/fishingrod/aplicacao/ferramentas/tipos.py`: `Ferramenta`,
      `RespostaDaFerramenta`, `Fabrica` e `EntradaDoRegistro`. `__init__.py` reexporta `tipos` e
      `registro`, **não** `acoes`. **DP-S-23**
- [x] **Passo 5** — `src/fishingrod/aplicacao/ferramentas/registro.py`:
      - `RegistroDeFerramentas`, verificado na construção;
      - `Violacao`, `verificar_escopo(agentes)` e `preparar(agente, contexto)`, com o mesmo código
        de verificação;
      - o padrão de nome de RN-AC-07, repetido sem importar o catálogo.

      **Critério 6 · RN-S-06..08, RN-S-13..15 · DP-S-21**
- [x] **Passo 6** — `src/fishingrod/aplicacao/ferramentas/acoes.py`:
      - `entradas_de_acoes(catalogo)`, com uma entrada por ação que aceita o chamador `AGENTE`;
      - `esquema_de(parametros)` e `texto_do_resultado(resultado)`;
      - a fábrica que amarra alvo e autor e chama `CatalogoDeAcoes.executar`;
      - o aviso de `dado` desconhecido em `fishingrod.sessao.ferramentas`.

      **US-17 · RN-S-46..51 · G12, G14**

### Adaptador

- [x] **Passo 7** — `src/fishingrod/adaptadores/sessao/opcoes.py`: `localizar_cli`,
      `VARIAVEIS_DE_CREDENCIAL` (do passo 2), `TEMPO_LIMITE_DE_FERRAMENTA_MS = 2147483647`,
      `permissao_exata(nomes)` e `montar_opcoes(...)`. As opções seguem, linha por linha, o §5 de
      `nfr-design-patterns.md`; a única diferença é `model = agente.modelo`, por `R-CG6-3`.
      **Critério 7, US-02 · RN-S-10..12, RN-S-52, RN-S-53 · DP-S-11..17 · N1**
- [x] **Passo 8** — `src/fishingrod/adaptadores/sessao/ferramentas.py`:
      - `nome_qualificado` e `separar`;
      - `Execucoes`, as tarefas de ferramenta em andamento;
      - `servidores(...)`, com um `create_sdk_mcp_server` por família presente e o esquema em cópia
        de `dict` puro (`R-CG6-2`);
      - a execução numa tarefa nossa, com `interrompida` quando cancelada (N4);
      - exceção da ferramenta em ERROR, sem os argumentos.

      **Critério 5 · RN-S-12, RN-S-42..44 · DP-S-18**
- [x] **Passo 9** — `src/fishingrod/adaptadores/sessao/falhas.py`: `Fase` e
      `classificar(fase, causa)`, a tabela do §4 de `nfr-design-patterns.md`, pura e total, com
      motivo, se derruba e nível de log. **Critério 4 · RN-S-28..31 · DP-S-09 · N6**
- [x] **Passo 10** — `src/fishingrod/adaptadores/sessao/traducao.py`: o `Tradutor`. Cuida de:
      - trechos parciais e blocos completos (RN-S-19);
      - a linha em branco entre blocos (G3);
      - pensamento, resultados e mensagens de sistema descartados;
      - `UsoDeFerramenta` tirado do bloco completo, e pedido de fora da sessão como aviso;
      - sinais tipados.

      `final()` decide o evento final (DP-S-10, RN-S-24). Sem `asyncio`, sem I/O e sem log.
      **Critério 1, TD-01 · RN-S-17..24 · DP-S-10, DP-S-19**
- [x] **Passo 11** — `src/fishingrod/adaptadores/sessao/conexao.py`: `ClienteDoSdk` (`Protocol`),
      `cliente_real(opcoes)` e `Conexao`, a tarefa dona com as 6 fases do §3 de
      `logical-components.md`:
      - os recados síncronos `interromper` e `descartar`;
      - cada espera dentro de um `asyncio.timeout` que o recado reagenda;
      - uma fila de saída por turno;
      - `Entregue(primeira)`.

      É o **único** arquivo com temporizador.
      **RN-S-33..38 · DP-S-01..05, DP-S-08 · N3 · TS-S-09**
- [x] **Passo 12** — `src/fishingrod/adaptadores/sessao/adaptador.py` e `__init__.py`:
      `AdaptadorSessaoClaude(registro, pasta_de_trabalho, fabrica_de_cliente=cliente_real,
      prazo_de_subida=60, prazo_de_interrupcao=5)`. Contém:
      - `abrir`, `enviar`, `fechar` e `encerrar()`;
      - toda mudança de estado por uma função só, que confere a tabela do FD §5;
      - a vaga do leitor e a cauda (N2);
      - o evento final só com o processo morto (N5);
      - `encerrar` em paralelo;
      - a rede de `FALHA_INESPERADA`;
      - o log de metadados.

      **Não importa o SDK.**
      **Critérios 1, 3, 4, US-01, US-03 · RN-S-05, RN-S-16, RN-S-26, RN-S-27, RN-S-32..41, RN-S-54 ·
      DP-S-05..07, DP-S-19 · G6, G7, G11 · N2, N5**

### Dublê

- [x] **Passo 13** — `tests/dobles/sessao_falsa.py`: `SessaoFalsa` (DP-S-22).
      - Responde por roteiro de **eventos da porta**.
      - Um passo pode executar a `Ferramenta` de verdade da sessão.
      - Usa `preparar` e `validar_mensagem`.
      - Tem a própria máquina de estados.
      - Guarda as mensagens recebidas, para U7 conferir o que chegou.

      Não importa o SDK nem `adaptadores/`.
      **Critério 1, TD-01 · NFR-S-09**

### Os testes

- [x] **Passo 14** — `tests/sessao/__init__.py`, `estrategias.py`, `cliente_roteirizado.py` e
      `modelo.py`: os geradores e os instrumentos do §5. O cliente roteirizado chama ferramentas
      pelo `SdkMcpBridge`. Um teste de fumaça confere duas coisas:
      - uma chamada chega à `Ferramenta`;
      - um argumento fora do esquema **não** chega (A16).
- [x] **Passo 15** — `tests/sessao/test_fronteira.py`:
      - varreduras estáticas de import;
      - um **Python novo com bloqueador de import** (`sys.meta_path`) importa **todos** os módulos
        de `dominio/` e `aplicacao/`;
      - `adaptador.py` sem `import claude_agent_sdk`;
      - importar `aplicacao.ferramentas` não carrega `aplicacao.catalogo`.

      **Critério 2, TD-02 · RN-S-01 · NFR-S-07 · TS-S-05 · DP-S-23**
- [x] **Passo 16** — `tests/sessao/test_porta.py` e `tests/sessao/test_registro.py`:
      - `validar_mensagem` e a imutabilidade dos tipos;
      - RN-S-13, 14 e 15;
      - `preparar`, com fábrica que levanta, que devolve outro nome e que devolve esquema que não é
        de objeto;
      - o padrão de nome igual ao de RN-AC-07;
      - **PBT-U6-08**;
      - R10 com os 6 nomes reais.
- [x] **Passo 17** — `tests/sessao/test_ferramentas_de_acoes.py`, com o catálogo de U5 de verdade:
      - **PBT-U6-05, 06 e 07**;
      - o exemplo de `business-logic-model.md` §7 (`criar_etapa`, "sim" e "não");
      - `anotar_memoria` assinada pelo nome do agente;
      - o modelo sem onde passar id nem autor (RN-S-48).
- [x] **Passo 18** — `tests/sessao/test_opcoes.py` e `tests/sessao/test_ferramentas.py`:
      - a inspeção do §5 de `nfr-design-patterns.md`, **linha por linha, inclusive as ausentes**;
      - `model` vindo do `Agente` (`R-CG6-3`);
      - `localizar_cli` sem o CLI, que dá `PROVEDOR_AUSENTE` sem subir;
      - `permissao_exata`, que nega curinga e nome de outra sessão;
      - **PBT-U6-04**;
      - RN-S-42 e RN-S-43;
      - DP-S-18: a nossa tarefa é a cancelada, e a resposta é `interrompida`;
      - `R-CG6-2`.
- [x] **Passo 19** — `tests/sessao/test_traducao.py` e `tests/sessao/test_falhas.py`:
      - **PBT-U6-01 e 02** no tradutor puro;
      - RN-S-19..23 por exemplo;
      - os avisos devolvidos;
      - a tabela do §4 **literal**, linha por linha, e que ela é total.
- [x] **Passo 20** — `tests/sessao/test_conexao.py`:
      - cada fase da dona com prazos curtos;
      - o recado em cada fase, conforme a tabela do §3 de `logical-components.md`;
      - recado entre duas fases;
      - a dona **nunca termina cancelada** e sempre passa pelo fechamento;
      - `interrupt` que falha ou trava, que leva ao descarte.
- [x] **Passo 21** — `tests/sessao/test_adaptador.py`. Um exemplo por motivo de falha (os 9), mais:
      - reconexão com `conversa_nova`;
      - `TURNO_EM_ANDAMENTO`;
      - ESC antes e depois da entrega, e ESC no instante da entrega (N3);
      - a cauda (N2);
      - `fechar` no meio do turno;
      - `encerrar` em paralelo, e `abrir` depois dele;
      - iterador abandonado;
      - um turno parado por muito tempo que não termina sozinho (NFR-S-12);
      - níveis de log com `caplog` (NFR-S-17), sem texto de mensagem nem argumento em nenhum
        registro;
      - a varredura de temporizadores (DP-S-08).
- [x] **Passo 22** — `tests/sessao/test_propriedades.py`: **PBT-U6-01, 03, 09, 10, 11 e 12** de
      ponta a ponta, no adaptador real com o cliente roteirizado, como no §5.
- [x] **Passo 23** — `tests/sessao/test_contrato.py`. Um único módulo de contrato, parametrizado:
      - roda no `SessaoFalsa`;
      - roda no adaptador real com o cliente roteirizado;
      - com `sdk_real`, roda no adaptador real com o CLI.

      Cobre resposta não vazia, gramática, falha tipada, `fechar` idempotente e mensagem inválida.
      **Critério 1, TD-01 · NFR-S-09**
- [x] **Passo 24** — `tests/sessao/test_sdk_real.py`, com o marcador `sdk_real`, cobrindo as
      **medições 1 a 17**:
      - as 10 do FD;
      - as 11 a 14 do NFR Requirements;
      - as 15 e 16 do NFR Design;
      - a 17 de `R-CG6-3`.

      Cada medição grava o que viu num registro que o passo 26 copia para o resumo.

### Verificação e fechamento

- [x] **Passo 25** — Rodar `uv run pytest`: a suíte padrão passa, e os testes `sdk_real` aparecem
      como *deselected*. Medir os geradores com `--hypothesis-show-statistics`. Depois, **testar
      os testes por mutação**, um defeito de cada vez, e confirmar que cada um derruba pelo menos
      um teste:
      1. nomes em `allowed_tools` (A15);
      2. `setting_sources=None`;
      3. `env` sem as variáveis de credencial;
      4. permissão por prefixo `mcp__ambiente__`;
      5. recado sempre `interromper`, ignorando o que o leitor viu (N3);
      6. `FimDeTurno` sem conferir texto ou ferramenta (TD-01);
      7. `UsoDeFerramenta` tirado do trecho parcial;
      8. causa desconhecida classificada como `INDISPONIVEL`;
      9. evento final antes de a dona terminar (N5);
      10. ESC sem cancelar as execuções de ferramenta;
      11. cauda sem prazo;
      12. uma fila só para todos os turnos (DP-S-04);
      13. esquema sem `additionalProperties: false`;
      14. id no texto do resultado;
      15. `abrir` sem a verificação de R10;
      16. texto da mensagem no log;
      17. `fechar` que não é idempotente;
      18. esquema entregue como `Mapping` (A17).

      Registrar o resultado e endurecer o gerador que deixar passar.
- [x] **Passo 26** — Rodar **`uv run pytest -m sdk_real`** uma vez, com o seu login da assinatura, e
      registrar cada medição. **Quatro medições bloqueiam**, e qualquer uma que falhar **para a
      geração e volta para você** antes de qualquer ajuste:
      - **2**: tempo-limite da ferramenta não configurável reabre U5;
      - **10**: duas sessões vivas, que é o critério 3;
      - **11**: o CLI que roda é o embutido e enxerga o login;
      - **16**: ESC e prazo vencido não deixam processo.

      As outras só registram, ou acionam a saída já escrita (5 → opção B da Q5; 15 → risco aceito;
      4 → `INDISPONIVEL`).
- [x] **Passo 27** — Emendas e fechamento, com o texto antigo riscado e nada apagado:
      - **emendas**: RN-S-42 e RN-S-50 (`R-CG6-1`); `nfr-design-patterns.md` §5, com `model` e a
        lista final de `VARIAVEIS_DE_CREDENCIAL` (`R-CG6-3`, passo 2); as que a execução e as
        medições exigirem.
      - **resumo**: `aidlc-docs/construction/sessao/code/code-summary.md`, com os arquivos, as
        decisões tomadas na execução, `uv audit`, a suíte, a mutação, as 17 medições com os
        números e a conformidade das extensões.

---

## 7. Rastreio

| Especificação | Passo |
|---|---|
| RN-S-01..04 (fronteira) | 3–12, 15 |
| RN-S-05..15 (abertura e configuração) | 3, 5, 7, 8, 12, 16, 18 |
| RN-S-16..27 (o turno) | 3, 10, 11, 12, 19, 21, 22 |
| RN-S-28..31 (falhas) | 3, 9, 19, 21, 22 |
| RN-S-32..41 (ciclo de vida) | 11, 12, 20, 21, 22 |
| RN-S-42..45 (execução de ferramentas) | 8, 18, 22 |
| RN-S-46..51 (ações como ferramentas) | 6, 17 |
| RN-S-52..53 (credencial) | 2, 7, 18, 26 |
| RN-S-54 (log) | 7–12, 21 |
| `PBT-U6-01..12` | 16, 17, 18, 19, 22 |
| NFR-S-01..06 (suprimentos) | 1, 27 |
| NFR-S-07..10 (fronteira e testes) | 1, 15, 22, 23 |
| NFR-S-11..13 (tempo) | 11, 12, 20, 21 |
| NFR-S-14..18 (capacidade, confiabilidade, log) | 12, 21, 26 |
| DP-S-01..24 | 1 (24), 3 (20), 5 (21), 7 (11..17), 8 (18), 9 (9), 10 (10, 19), 11 (01..05, 08), 12 (05..07, 19), 13 (22), 4 e 15 (23) |
| G1–G15 · N1–N6 | 3, 6, 7, 10, 11, 12 |
| `R-CG6-1..3` | 7, 8, 14, 18, 24, 27 |
| Medições 1–17 | 24, 26 |
| Critérios de pronto 1–7 | 1 → 10, 13, 23 · 2 → 15 · 3 → 12, 26 · 4 → 3, 9, 12, 22 · 5 → 8 · 6 → 5, 16 · 7 → 7, 18 |
| US-01 · US-02 · US-03 · US-13 · US-17 | 12, 23, 26 · 7, 26 · 9, 12, 22 · 4, 5, 8 · 6, 17 |
| TD-01 · TD-02 | 10, 13, 23 · 15 |

**27 passos.** 12 arquivos novos em `src/`: 1 em `aplicacao/portas/`, 4 em `aplicacao/ferramentas/` e
7 em `adaptadores/sessao/`. Nenhum arquivo existente de `src/` é modificado. São modificados
`pyproject.toml` e `uv.lock`. São criados 18 arquivos de teste (17 em `tests/sessao/` e 1 em
`tests/dobles/`), 1 resumo de código e as emendas de documentação. O código antigo não é tocado.

---

## 8. Conformidade das extensões (planejada)

| Extensão / regra | Estado | Como o plano cumpre |
|---|:--:|---|
| `security-baseline` SECURITY-03 (log) | ✅ | Só metadados (passos 7–12); teste de que nenhum registro leva mensagem ou argumento (passo 21); saída do CLI em DEBUG |
| SECURITY-05 (entrada) | ✅ | `validar_mensagem` (passo 3, PBT-U6-12); argumentos validados por U5 depois do esquema do SDK (`R-CG6-1`) |
| SECURITY-08 (acesso) | ✅ | `permissao_exata`, num ponto só (passo 7, N1); alvo amarrado pelo contexto (passo 6); R10 em duas camadas (passos 5, 16) |
| SECURITY-09 (endurecimento) | ✅ | Opções por extenso e inspecionadas linha por linha, inclusive as ausentes; CLI embutido ou nenhum (passos 7, 18) |
| SECURITY-10 (dependências) | ✅ | Versão exata com hash, `uv audit` com política de bloqueio (passo 1) |
| SECURITY-11 (desenho seguro) | ✅ | `R-CG6-1..3` e as decisões do §4 declaradas para revisão; riscos aceitos só com medição (passo 26) |
| SECURITY-12 (credencial) | ✅ | Lista conferida no CLI (passo 2), sobrescrita sem leitura, medições 5 e 15 |
| SECURITY-13 (integridade) | ✅ | Nada do modelo vira efeito sem passar por U5 (passos 6, 17) |
| SECURITY-15 (falha segura) | ✅ | `enviar` nunca levanta (PBT-U6-03); processo nunca sem dono (PBT-U6-09, medição 16); erro genérico ao agente |
| SECURITY-01, 02, 04, 06, 07, 14 | N/A | Sem armazenamento próprio, rede exposta, servidor, IAM ou infraestrutura de alerta |
| PBT-01 (identificação) | ✅ | As 12 propriedades do FD, especificadas no §5 |
| PBT-02 (ida e volta) | ✅ | `PBT-U6-04`, `PBT-U6-07` |
| PBT-03 (invariantes) | ✅ | `PBT-U6-01`, `02`, `03`, `05`, `07`, `08`, `10`, `11`, `12` |
| PBT-04 (idempotência) | ✅ | `PBT-U6-09` (`fechar` duas vezes) |
| PBT-05 (oráculo) | ✅ | `PBT-U6-02`, `06`, `08`; tabela de falhas literal como oráculo de `PBT-U6-03` |
| PBT-06 (com estado) | ✅ | `PBT-U6-09`, conferido depois de cada passo contra o `ModeloDeSessoes` |
| PBT-07 (geradores) | ✅ | `tests/sessao/estrategias.py`, reaproveitando U4 e U5; medidos no passo 25 |
| PBT-08 (encolhimento e semente) | ✅ | Padrão do Hypothesis, nada desligado; propriedades nunca chamam o provedor |
| PBT-09 (framework) | ✅ | Hypothesis, já em `dev` desde U0 |
| PBT-10 (complementar) | ✅ | Exemplos (passos 16–21, 23) e propriedades (passos 16–19, 22) separados; contrato e medições reais à parte |
| `resiliency-baseline` | N/A | Desabilitada; nenhuma nova tentativa além da reconexão (NFR-S-18) |
