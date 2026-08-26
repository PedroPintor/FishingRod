# API Documentation — FishingRod

**Data da análise**: 2026-08-16

---

## REST APIs

**Nenhuma.** O sistema não expõe rede. É um processo local de terminal.

---

## Interface de Comando (a "API" que o usuário realmente usa)

Comandos são strings iniciadas por `/`, definidos em `model/comando.py` e resolvidos pela cadeia.

| Comando | Atendido por | Argumento | Efeito | Erro possível |
|---|---|---|---|---|
| `/ajuda` | `Ambiente` | — | Lista todos os comandos do enum | — |
| `/sair` | `Ambiente` | — | `ativo = False`; a UI decide o que fazer | — |
| `/projetos` | `Ambiente` | — | Lista projetos, marcando o ativo com `*` | — |
| `/novo-projeto` | `Ambiente` | `<nome>` | Cria projeto | falta nome; nome já existe |
| `/trocar-projeto` | `Ambiente` | `<indice>` | Troca o projeto ativo | falta índice; não numérico; fora do intervalo |
| `/sessoes` | `Projeto` | — | Lista sessões do projeto ativo | — |
| `/nova-sessao` | `Projeto` | `<nome>` | Cria sessão | falta nome; nome já existe |
| `/trocar-sessao` | `Projeto` | `<indice>` | Troca a sessão ativa | falta índice; não numérico; fora do intervalo |
| `/chats` | `Sessao` | — | Lista chats com papel do agente | — |
| `/agentes` | `Sessao` | — | Lista o catálogo `AgenteDoSistema` | — |
| `/nome-chat` | `Sessao` | `<novo nome>` | Renomeia o chat ativo | falta nome |
| `/novo-chat` | `Sessao` | `<agente>` | Abre chat com um agente do catálogo | agente inexistente; já há orquestrador |
| `/trocar-chat` | `Sessao` | `<indice>` | Troca o chat ativo | falta índice; não numérico; fora do intervalo |

**Comportamentos observados**:
- Argumentos são obtidos por `mensagem.split()` — **nomes com espaço não funcionam**; só o
  primeiro token é usado.
- Comando desconhecido iniciado por `/` cai na `Sessao` e devolve
  `"Erro - comando desconhecido: <cmd> (veja: /ajuda)"` (`sessao.py:88-90`).
- Comando de outro andar não implementado lá cai no `case _` e devolve a mesma mensagem
  (`sessao.py:131-133`).

---

## Internal APIs

### `Ambiente` (`Ambiente/ambiente.py`)
| Método | Assinatura | Retorno |
|---|---|---|
| `projeto` | `@property projeto -> Projeto` | Projeto ativo. **Estoura `IndexError`** se a lista estiver vazia — daí a defesa em `__post_init__` |
| `trocar_projeto` | `(indice: int) -> bool` | `False` se índice fora do intervalo |
| `buscar_projeto` | `(nome: str) -> tuple[int, Projeto] \| None` | Índice e objeto, ou `None` |
| `criar_projeto` | `(nome: str) -> Projeto \| None` | `None` se o nome já existe |
| `listar_projetos` | `() -> list[str]` | Nomes na ordem de criação |
| `obter_status` | `() -> dict` | `{"nome_ambiente", **status do projeto}` |
| `enviar` | `(mensagem: str) -> list[Mensagem]` | Ponto de entrada único das interfaces |

### `Projeto` (`Ambiente/ambiente.py`)
| Método | Assinatura | Retorno |
|---|---|---|
| `sessao` | `@property sessao -> Sessao` | Sessão ativa |
| `trocar_sessao` | `(indice: int) -> bool` | `False` se fora do intervalo |
| `_buscar_sessao` | `(nome: str) -> Sessao \| None` | Privado |
| `criar_sessao` | `(nome: str) -> Sessao \| None` | `None` se o nome já existe. Cria com um chat de `OrquestradorTeste` |
| `listar_sessoes` | `() -> list[str]` | Nomes |
| `obter_status` | `() -> dict` | `{"nome_projeto", **status da sessão}` |
| `enviar` | `(mensagem: str) -> list[Mensagem]` | Atende ou delega |

### `Sessao` (`Ambiente/sessao.py`)
| Método | Assinatura | Retorno |
|---|---|---|
| `chat` | `@property chat -> Chat` | Chat ativo |
| `trocar_chat` | `(indice: int) -> bool` | `False` se fora do intervalo |
| `listar_agentes` | `() -> list[Agente]` | **Devolve o catálogo global**, não os agentes desta sessão |
| `buscar_agente` | `(nome: str) -> Agente \| None` | Busca no catálogo global |
| `criar_chat` | `(agente: Agente) -> bool` | `False` se violaria a invariante do orquestrador |
| `obter_status` | `() -> dict` | `{"nome_sessao", "n_iteracoes", "nome_chat", "memoria"}` |
| `enviar` | `(mensagem: str) -> list[Mensagem]` | Grava em `chat.mensagens` e soma iteração |

### `Memoria` (`Ambiente/memoria.py`)
| Método | Assinatura | Comportamento |
|---|---|---|
| `anotar` | `(chave, valor, autor) -> bool` | ⚠️ **`KeyError` se a chave não existir** — acessa `self.anotacoes[chave]` sem `setdefault` |
| `anotar_plano` | `(valor, autor) -> bool` | `False` se `"plano"` já existe (escrita única) |
| `formatar` | `() -> dict \| None` | Devolve **apenas** a lista de anotações de `"plano"`, ou `None` |

### `Agente` (`Ambiente/agente.py`)
| Método | Assinatura | Comportamento |
|---|---|---|
| `responder` | `(mensagem: str) -> str` | **Abstrato** |
| `AgenteTeste.responder` | `(mensagem) -> str` | String fixa: *"...EU NAO SEI SOU APENAS UM TESTE"* |
| `AgenteClaude.construir_agente` | `() -> ClaudeAgentOptions` | Devolve opções **vazias** |
| `AgenteClaude.responder` | `(mensagem)` | ⚠️ **`return` nu — devolve `None`.** Ligá-lo hoje quebraria `Mensagem.texto` |

---

## Data Models

### `Mensagem` (`model/mensagem.py`)
- **Fields**: `autor: str` (texto livre — para agentes vem de `caixa_de_texto`);
  `texto: str`; `tipo: Literal["usuario", "sistema", "agente"]`.
- **Relationships**: acumulada em `Chat.mensagens`.
- **Validation**: `Literal` não é verificado em runtime (dataclass simples).
- **Nota de risco**: a construção posicional é **inconsistente entre os andares**.
  `Sessao.enviar` usa `Mensagem("<NOME_USUARIO>", mensagem, "usuario")` — posicional, correto.
  `Ambiente`/`Projeto` usam `Mensagem(autor=..., tipo=..., texto=...)` — nomeado, também correto.
  Qualquer construção posicional futura que siga a ordem do `Ambiente` produzirá campos trocados.

### `Comando` (`model/comando.py`)
- **Fields**: enum de 13 valores string, agrupados por andar em comentários.
- **Validation**: `Comando(str)` levanta `ValueError` para valor desconhecido — usado
  deliberadamente como teste de pertinência nos `_detectar_comando_*`.

### `Anotacao` (`Ambiente/memoria.py`)
- **Fields**: `autor: str`, `valor: str`.
- **Relationships**: agrupada por chave em `Memoria.anotacoes: dict[str, list[Anotacao]]`.
- **Racional**: carrega autor porque o valor está na comunicação **entre** agentes.

### `Agente` (`Ambiente/agente.py`)
- **Fields**: `nome`, `papel: Papel`, `modelo: str`, `ferramentas: list[Callable]`,
  `regras: list[str]`, `caixa_de_texto: str = "[Agente]"`.
- **Relationships**: um `Chat` aponta para um `Agente`.
- **⚠️ Observação**: `ferramentas: list[Callable]` guarda **callables** — o que colide com a
  decisão de manter a `Memoria` serializável e, no desenho validado pelo spike, as ferramentas
  são **fabricadas pela Sessão**, não carregadas pelo agente.

### `Chat` (`Ambiente/sessao.py`)
- **Fields**: `agente`, `mensagens: list[Mensagem]`, `nome: str = None`, `iteracoes: int = 0`.
- **Validation**: `__post_init__` herda o nome do agente quando `nome` vem vazio.
- **Decisão registrada**: `mensagens` é **cópia para a UI**, não fonte da verdade do histórico —
  com sessão viva, o histórico fica do lado do client (vision.md §6.3).

### `Papel` (`Ambiente/agente.py`)
- **Values**: `ORQUESTRADOR = "orquestrador"`, `SUB_AGENTE = "sub-agente"`.
