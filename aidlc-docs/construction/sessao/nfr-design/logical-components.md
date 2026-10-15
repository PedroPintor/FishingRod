# Logical Components — U6 `sessao`

**Fase:** CONSTRUCTION · **Unidade:** `U6 sessao` · **Portão 3 de 4** · **Data:** 2026-10-13
**Decisões:** Q1=A (tarefa dona por conexão), Q7=A (seis módulos no adaptador), Q8=A (falso
independente) · `R-ND6-1` (`Familia` e erros na porta), `R-ND6-2` (validação na porta), `R-ND6-3`
(`acoes` não reexportado), `R-ND6-12` (testes) e `R-ND6-14` (log)

Este documento diz **quais arquivos existem, o que cada um pode importar, e por quê**. Os padrões
citados (`DP-S-nn`, `N1..N6`) estão em `nfr-design-patterns.md`.

---

## 1. Os arquivos

### 1.1 A porta

```
src/fishingrod/aplicacao/portas/sessao.py
```

| Conteúdo | Notas |
|---|---|
| `PortaSessao` (`Protocol`: `abrir`, `enviar`, `fechar`) | FD §2.1 |
| `ContextoDaSessao`, `SessaoViva` | imutáveis |
| `MensagemEntregue`, `PedacoDeTexto`, `UsoDeFerramenta`, `FimDeTurno`, `FalhaDoTurno` e o tipo `EventoConversa` | imutáveis; `argumentos` em cópia somente leitura |
| `MotivoFalhaDeSessao` (9 valores) e **`Familia`** (`AMBIENTE`, `WIKI`) | `R-ND6-1`: U7 lê `Familia` em `UsoDeFerramenta` sem importar ferramentas |
| `ErroDeSessao`, `ConfiguracaoDeSessaoInvalida`, `AdaptadorEncerrado`, `RegistroInvalido` | `R-ND6-1`, `DP-P-11` de U2: os erros moram com o contrato |
| `MAXIMO_DE_CARACTERES = 100_000` e `validar_mensagem(texto) -> FalhaDoTurno \| None` | `R-ND6-2`, DP-S-20, DP-S-21: função pura, usada pelo real e pelo falso |

**Pode importar:** `dominio/` (`Agente`, `Identidade`), `dataclasses`, `enum`, `typing`,
`collections.abc`, `types`.
**Não pode importar:** nada de `aplicacao/ferramentas/`, nada de `adaptadores/`, `claude_agent_sdk`.

### 1.2 As ferramentas, sem SDK

```
src/fishingrod/aplicacao/ferramentas/__init__.py
src/fishingrod/aplicacao/ferramentas/tipos.py
src/fishingrod/aplicacao/ferramentas/registro.py
src/fishingrod/aplicacao/ferramentas/acoes.py
```

| Arquivo | Conteúdo | Notas |
|---|---|---|
| `__init__.py` | reexporta `tipos` e `registro` | **não** reexporta `acoes` (`R-ND6-3`, DP-S-23) |
| `tipos.py` | `Ferramenta`, `RespostaDaFerramenta`, `Fabrica`, `EntradaDoRegistro` | FD §4.2, §4.3 |
| `registro.py` | `RegistroDeFerramentas` (verificado na construção: RN-S-13, 14), `Violacao`, `verificar_escopo(agentes)` e **`preparar(agente, contexto)`** | DP-S-21: `preparar` verifica (RN-S-06, 07) e fabrica (RN-S-08) com o mesmo código de `verificar_escopo`, devolve as ferramentas agrupadas por família, ou levanta `ConfiguracaoDeSessaoInvalida`. O padrão de nome é o de RN-AC-07, repetido aqui com um teste que confere que os dois aceitam os mesmos nomes, para que `registro.py` não carregue o catálogo |
| `acoes.py` | `entradas_de_acoes(catalogo)`, `esquema_de(parametros)`, `texto_do_resultado(resultado)` | RN-S-46..51. Só U9 importa este arquivo. Registra em `fishingrod.sessao.ferramentas` (`R-ND6-14`): o aviso de `dado` desconhecido (G12) |

**Podem importar:** `dominio/`, `aplicacao/portas/sessao.py`; `acoes.py` também
`aplicacao/catalogo/` (U5).
**Não podem importar:** `adaptadores/`, `claude_agent_sdk`. `tipos.py` e `registro.py` também não
importam `aplicacao/catalogo/`.

### 1.3 O adaptador (Q7=A)

```
src/fishingrod/adaptadores/sessao/__init__.py
src/fishingrod/adaptadores/sessao/opcoes.py
src/fishingrod/adaptadores/sessao/ferramentas.py
src/fishingrod/adaptadores/sessao/traducao.py
src/fishingrod/adaptadores/sessao/falhas.py
src/fishingrod/adaptadores/sessao/conexao.py
src/fishingrod/adaptadores/sessao/adaptador.py
```

| Arquivo | Conteúdo | Notas |
|---|---|---|
| `__init__.py` | reexporta `AdaptadorSessaoClaude` | o que U9 importa |
| `opcoes.py` | `localizar_cli()`, `VARIAVEIS_DE_CREDENCIAL`, `TEMPO_LIMITE_DE_FERRAMENTA_MS`, `permissao_exata(nomes)` (o `can_use_tool`), `montar_opcoes(...)` | **O arquivo de segurança da unidade.** DP-S-11..17, §5 dos padrões. Recebe os servidores MCP já montados e os nomes permitidos; não importa nenhum outro módulo do adaptador. Registra a negação (WARNING) e a saída de erro do CLI (DEBUG) |
| `ferramentas.py` | `nome_qualificado(familia, nome)`, `separar(nome_qualificado)`, `Execucoes` (as tarefas de ferramenta em andamento de uma sessão), `servidores(ferramentas_por_familia, execucoes)` | DP-S-18, N4. Converte `Ferramenta` para o SDK; o esquema passa sem conversão (A13). Registra exceção dentro da ferramenta em ERROR, sem os argumentos (RN-S-43) |
| `traducao.py` | `Tradutor`: recebe as mensagens do SDK de um turno e devolve eventos e avisos; `final()` decide o evento final | DP-S-10, DP-S-19. Sem `asyncio`, sem I/O, sem log. Alvo de PBT-U6-01 e 02 |
| `falhas.py` | `Fase` (`SUBIDA`, `ENTREGA`, `RESPOSTA`), `classificar(fase, causa)` | DP-S-09, §4 dos padrões. Pura e total. Alvo de PBT-U6-03 |
| `conexao.py` | `ClienteDoSdk` (`Protocol` com `connect`, `query`, `receive_response`, `interrupt`, `disconnect`), `cliente_real(opcoes)`, `Conexao` (a tarefa dona) | DP-S-01..05, DP-S-08. O **único** arquivo com temporizador. Detalhe no §3 |
| `adaptador.py` | `AdaptadorSessaoClaude(registro, pasta_de_trabalho, fabrica_de_cliente=cliente_real, prazo_de_subida=60, prazo_de_interrupcao=5)`: as sessões, os estados, `abrir`, `enviar`, `fechar`, `encerrar()` | DP-S-05, DP-S-06, DP-S-07. Toda mudança de estado passa por uma função só, que confere a tabela do FD §5; transição fora da tabela é defeito e vai ao log em ERROR. **Não importa o SDK**: tudo do SDK chega pelos outros cinco módulos |

**Podem importar:** `aplicacao/portas/sessao.py`, `aplicacao/ferramentas/` (`tipos`, `registro`),
`dominio/`, `claude_agent_sdk` (menos `adaptador.py`), `asyncio`, `logging`, `importlib.resources`,
`pathlib`, `json`, `datetime`.
**Não podem importar:** `aplicacao/ferramentas/acoes.py` e `aplicacao/catalogo/` (DP-S-23), nenhum
outro adaptador, nada de `interface/`.

Cada módulo que registra instala o próprio `NullHandler` em `fishingrod.sessao` (`R-ND6-14`).

### 1.4 Os testes (`R-ND6-12`)

```
tests/sessao/__init__.py
tests/sessao/estrategias.py
tests/sessao/cliente_roteirizado.py
tests/sessao/modelo.py
tests/sessao/test_porta.py
tests/sessao/test_registro.py
tests/sessao/test_ferramentas_de_acoes.py
tests/sessao/test_opcoes.py
tests/sessao/test_ferramentas.py
tests/sessao/test_traducao.py
tests/sessao/test_falhas.py
tests/sessao/test_conexao.py
tests/sessao/test_adaptador.py
tests/sessao/test_propriedades.py
tests/sessao/test_contrato.py
tests/sessao/test_fronteira.py
tests/sessao/test_sdk_real.py
tests/dobles/sessao_falsa.py
```

| Arquivo | O que carrega |
|---|---|
| `estrategias.py` | Geradores: roteiro de provedor no formato do SDK, exceções do SDK e quaisquer, `Agente`, listas de `Parametro`, `Resultado`, comandos de ciclo de vida. Reaproveita `tests/ambiente/estrategias.py` e `tests/acoes/estrategias.py` (PBT-07) |
| `cliente_roteirizado.py` | Um `ClienteDoSdk` falso: segue um roteiro de mensagens do SDK, pode falhar em qualquer fase, pode travar até ser liberado, e **conta processos vivos**. Os testes esperam por ele (ele sabe quando o processo simulado parou), e não por um método extra do adaptador |
| `modelo.py` | O modelo de estados de PBT-U6-09, com a cauda do ESC (N2) |
| `test_porta.py` | `validar_mensagem` (PBT-U6-12 no nível da função) e a imutabilidade dos tipos |
| `test_registro.py` | RN-S-13, 14, 15; `preparar`; PBT-U6-08; o padrão de nome igual ao de RN-AC-07 |
| `test_ferramentas_de_acoes.py` | PBT-U6-05, 06 e 07, com o catálogo de U5 de verdade; R10 com os 6 nomes reais |
| `test_opcoes.py` | A inspeção do §5 dos padrões, linha por linha, inclusive as ausentes; `localizar_cli` sem o CLI |
| `test_ferramentas.py` | PBT-U6-04; RN-S-42, 43; DP-S-18 (a nossa tarefa é a cancelada; resposta `interrompida`) |
| `test_traducao.py` | PBT-U6-01 e 02 no tradutor puro; RN-S-19..23; os avisos devolvidos |
| `test_falhas.py` | A tabela do §4 dos padrões, linha por linha, e que ela é total |
| `test_conexao.py` | As fases do §3 com prazos curtos; o recado em cada fase; a dona nunca termina cancelada |
| `test_adaptador.py` | Exemplos de ciclo de vida, ESC antes e depois da entrega, cauda (N2), `fechar` no meio do turno, `encerrar` em paralelo, níveis de log com `caplog` (NFR-S-17), nada de mensagem ou argumento no log, e a varredura de temporizadores (DP-S-08) |
| `test_propriedades.py` | PBT-U6-01, 03, 09, 10, 11 e 12 de ponta a ponta, no adaptador real com o cliente roteirizado |
| `test_contrato.py` | NFR-S-09: o mesmo contrato no falso, no real com o cliente roteirizado e, com `sdk_real`, no real com o CLI |
| `test_fronteira.py` | Varreduras estáticas de import; o Python novo com bloqueador de import (NFR-S-07, TS-S-05); `adaptador.py` sem `import claude_agent_sdk`; importar `aplicacao.ferramentas` não carrega `aplicacao.catalogo` (DP-S-23) |
| `test_sdk_real.py` | Marcador `sdk_real`. As medições 1–16 |
| `tests/dobles/sessao_falsa.py` | `SessaoFalsa` (DP-S-22): roteiro de eventos da porta por turno; um passo pode executar a `Ferramenta` de verdade da sessão; usa `preparar` e `validar_mensagem`; guarda as mensagens recebidas, para U7 conferir o que chegou. Não importa o SDK nem `adaptadores/` |

O perfil de Hypothesis de `tests/conftest.py` (`deadline=None`) vale sem mudança.

### 1.5 `pyproject.toml`

| Onde | Muda para |
|---|---|
| `dependencies` | `["claude-agent-sdk==0.2.143"]` (NFR-S-01, NFR-S-02), com o comentário atualizado |
| `[tool.pytest.ini_options]` | `markers = ["sdk_real: usa o CLI do Claude de verdade; fora da suite padrao"]` e `addopts = "-m 'not sdk_real'"` (DP-S-24) |
| `[tool.uv]` | sem mudança: `exclude-newer` continua em 2026-08-25 (TS-S-03) |

---

## 2. Matriz de dependência

`→` significa "importa". A matriz é triangular: **não há ciclo**. As colunas `SDK` e `catálogo` são
externas a U6.

| De ↓ / Para → | `dominio` | `portas/sessao` | `ferr/tipos` | `ferr/registro` | `catálogo` | `SDK` | `opcoes` | `ferramentas` | `falhas` | `traducao` | `conexao` |
|---|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|
| `portas/sessao.py` | → | | | | | | | | | | |
| `ferramentas/tipos.py` | → | → | | | | | | | | | |
| `ferramentas/registro.py` | → | → | → | | | | | | | | |
| `ferramentas/acoes.py` | → | → | → | | → | | | | | | |
| `sessao/opcoes.py` | | | | | | → | | | | | |
| `sessao/ferramentas.py` | | → | → | | | → | | | | | |
| `sessao/falhas.py` | | → | | | | → | | | | | |
| `sessao/traducao.py` | | → | | | | → | | → | → | | |
| `sessao/conexao.py` | | | | | | → | | | → | | |
| `sessao/adaptador.py` | → | → | → | → | | | → | → | → | → | → |
| `dobles/sessao_falsa.py` | → | → | → | → | | | | | | | |

`conexao.py` importa `falhas.py` só pelo `Fase`, para marcar em que fase a dona caiu.

Duas linhas carregam a fronteira: **`ferramentas/acoes.py` é o único que importa o catálogo**, e
**`adaptador.py` não importa o SDK**. A seta nova U6 → U5 de `unit-of-work-dependency.md` (Q9=A do
FD) passa só por `acoes.py`.

---

## 3. A conexão por dentro (`conexao.py`)

A `Conexao` tem uma tarefa dona, uma fila de entrada e dois recados. Ela vive do pedido de subida até
o processo morrer; uma reconexão é uma `Conexao` nova.

| Fase da dona | Espera | Prazo | Recado `interromper` | Recado `descartar` |
|---|---|---|---|---|
| **subida** | `connect()`: processo, checagem de versão, inicialização | 60 s; vencido, vira `Caiu(SUBIDA, ...)` | não acontece: nada foi entregue (N3) | vence o prazo; vai a fechamento |
| **ociosa** | o próximo `Turno` na fila de entrada | nenhum | a resposta já tinha acabado (o leitor saiu antes de ler o fim): nada a interromper; a dona avisa o adaptador, e a sessão vai a `OCIOSA` | vence; vai a fechamento |
| **entrega** | `query(texto)` | nenhum | não acontece (N3) | vence na hora; vai a fechamento |
| **resposta** | a próxima mensagem do SDK, até o `ResultMessage` | nenhum (NFR-S-12) | vence; vai à cauda | vence; vai a fechamento |
| **cauda** | `interrupt()` e o resto da resposta, jogado fora | 5 s; vencido, vai a fechamento | já está nela | vence; vai a fechamento |
| **fechamento** | `disconnect()` | nenhum nosso (o SDK limita a ~15 s, A12) | ignorado | ignorado |

- **Ao terminar a cauda** com o `ResultMessage` dentro do prazo, a dona avisa o adaptador: a sessão
  vai a `OCIOSA`, e quem espera a cauda (N2) é liberado.
- **Ao terminar o fechamento**, a dona avisa o adaptador: a sessão vai a `SEM_CONEXAO`, ou fica em
  `FECHADA` se foi `fechar`. Quem espera por ela com `asyncio.wait` é liberado (DP-S-06, DP-S-07).
- **Qualquer exceção na dona** vira `Caiu(fase, causa)` na fila do turno corrente, se houver, e leva
  ao fechamento. A dona sempre termina passando pelo fechamento.
- **`conversa_nova`**: a dona sabe se esta é a primeira entrega dela, e a manda em
  `Entregue(primeira)`.

---

## 4. Composição em U9

```
U9 (composition root)
  catalogo   = CatalogoDeAcoes(...)                                  # U5
  registro   = RegistroDeFerramentas(entradas_de_acoes(catalogo)     # U6, aplicacao/ferramentas/acoes.py
                                     + entradas_de_wiki(...))        # U8
  sessoes    = AdaptadorSessaoClaude(registro, pasta_de_trabalho)    # prazos padrao: 60 s e 5 s
  conversa   = ServicoDeConversa(sessoes, ...)                       # U7 recebe a PortaSessao
  ...
  no fim do programa:  await sessoes.encerrar()
```

- **U9 resolve `pasta_de_trabalho`**, como resolve a pasta de dados (G11). O adaptador não procura
  pasta nenhuma.
- **`fechar` pode levar até ~15 s** no pior caso (A12). Para não travar a tela, U9 pode disparar o
  fechamento de um chat sem esperar; `encerrar()` fecha o que faltar.
- **U7 pode chamar `enviar` de qualquer tarefa**: o cliente do SDK vive inteiro na tarefa dona. A
  herança (7) de U7 (usar cada sessão sempre do mesmo contexto async) deixa de existir.

---

## 5. Rastreio

### 5.1 Padrões → arquivos

| Padrão | Arquivo |
|---|---|
| DP-S-01..05, DP-S-08 | `adaptadores/sessao/conexao.py` (DP-S-05 também em `adaptador.py`) |
| DP-S-06, DP-S-07 | `adaptadores/sessao/adaptador.py` |
| DP-S-09 | `adaptadores/sessao/falhas.py` |
| DP-S-10 | `adaptadores/sessao/traducao.py` + a rede de `enviar` em `adaptador.py` |
| DP-S-11..17 | `adaptadores/sessao/opcoes.py` |
| DP-S-18 | `adaptadores/sessao/ferramentas.py` |
| DP-S-19 | `traducao.py` e `falhas.py` devolvem; `adaptador.py` registra |
| DP-S-20 | `aplicacao/portas/sessao.py` |
| DP-S-21 | `aplicacao/ferramentas/registro.py` + `validar_mensagem` na porta |
| DP-S-22 | `tests/dobles/sessao_falsa.py` |
| DP-S-23 | `aplicacao/ferramentas/__init__.py` + `tests/sessao/test_fronteira.py` |
| DP-S-24 | `pyproject.toml` |

### 5.2 Propriedades → alvo e teste

| Propriedade | Alvo | Teste |
|---|---|---|
| PBT-U6-01 gramática do turno | `traducao.py`; o adaptador inteiro | `test_traducao.py`, `test_propriedades.py` |
| PBT-U6-02 texto preservado | `traducao.py` | `test_traducao.py` |
| PBT-U6-03 nunca levanta | `falhas.py`; o adaptador inteiro | `test_falhas.py`, `test_propriedades.py` |
| PBT-U6-04 nome qualificado | `adaptadores/sessao/ferramentas.py` | `test_ferramentas.py` |
| PBT-U6-05 esquema fiel | `aplicacao/ferramentas/acoes.py` | `test_ferramentas_de_acoes.py` |
| PBT-U6-06 esquema e catálogo concordam | `acoes.py` + catálogo de U5 | `test_ferramentas_de_acoes.py` |
| PBT-U6-07 texto do agente | `acoes.py` | `test_ferramentas_de_acoes.py` |
| PBT-U6-08 R10 | `aplicacao/ferramentas/registro.py` | `test_registro.py` |
| PBT-U6-09 ciclo de vida | `adaptador.py` + `conexao.py`, com `modelo.py` | `test_propriedades.py` |
| PBT-U6-10 sessões isoladas | `adaptador.py` | `test_propriedades.py` |
| PBT-U6-11 interromper cancela tudo | `adaptador.py` + `ferramentas.py` | `test_propriedades.py` |
| PBT-U6-12 mensagem inválida | `validar_mensagem`; o adaptador | `test_porta.py`, `test_propriedades.py` |

---

## 6. O que **não** existe nesta unidade

| Não existe | Por quê |
|---|---|
| Nova tentativa, disjuntor, bulkhead | `resiliency-baseline` desabilitada; NFR-S-18 |
| Teto de sessões, pool de processos | NFR-S-14 |
| Prazo de silêncio ou de duração de turno | NFR-S-12; a defesa é o ESC |
| Fechamento por inatividade | NFR-S-13 |
| Trava (`Lock`) | um só event loop; a vaga é tomada sem `await` antes (DP-S-05) |
| Thread | o SDK e o adaptador vivem no event loop do programa |
| `resume` do CLI, cópia da conversa em `~/.claude/` | DP-S-13; a retomada da próxima iteração reconstrói pela transcrição do FishingRod |
| Hooks do SDK | DP-S-14: o `can_use_tool` basta, com `setting_sources=[]` e `allowed_tools=[]` |
| Modo "sem LLM" em `src/` | o falso mora em `tests/dobles/` (FD §6.2) |
| Dependência direta além do SDK | NFR-S-01 |
