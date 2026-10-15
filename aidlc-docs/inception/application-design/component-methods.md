# Application Design — Métodos e Contratos de Fronteira

**Estágio:** INCEPTION — Application Design · **Profundidade:** comprehensive
**Data:** 2026-08-25 · **Base:** `components.md`, `application-design-plan.md`

> Este documento fixa **assinatura, entrada, saída e propósito** de cada método de fronteira.
> **Não** contém regra de negócio detalhada (fica para Functional Design por unidade) nem
> implementação. Tipos são descritos conceitualmente (Python-like), não é código final.
> Convenção: nomes de domínio em português, como o resto do projeto (D-ARQ-02 mantém vocabulário
> atual).

---

## 1. Domínio — tipos de valor e entidades

### 1.1 `Identidade`

```
class Identidade:
    valor: str   # UUIDv7 em texto canônico

    @staticmethod
    def nova() -> "Identidade": ...   # gera UUIDv7 no momento da chamada
                                      # [emenda U1, 2026-08-26] usa uuid.uuid7()
                                      # da stdlib do Python 3.14 (CQ2=D)
```

- **Propósito de `nova()`**: única forma de criar uma identidade. Chamada no `__init__` de toda
  entidade de domínio — nunca pelo adaptador de persistência (Pergunta 4B).
- **Entrada**: nenhuma. **Saída**: `Identidade` nova, ordenável por tempo de criação.
- Imutável, comparável por igualdade de `valor`.

### 1.2 `Ambiente`

```
class Ambiente:
    id: Identidade
    nome: str
    frentes: list[Frente]
    raiz_wiki: RaizWiki

    def criar_frente(self, nome: str) -> Frente: ...
    def buscar_frente(self, id: Identidade) -> Frente | None: ...
```

- `criar_frente(nome)` — **entrada**: nome (string não vazia). **Saída**: `Frente` nova, já
  anexada à coleção, com `Identidade.nova()`. Não persiste (persistência é responsabilidade da
  aplicação, via `PortaPersistencia`).
- `buscar_frente(id)` — busca por identidade, nunca por índice posicional ou nome (RF-F16).

### 1.3 `Frente`

```
class Frente:
    id: Identidade
    nome: str
    tarefas: list[Tarefa]

    def criar_tarefa(self, nome: str, agente_orquestrador: Agente) -> Tarefa: ...
    # [emenda U1, 2026-08-26] ~~criar_tarefa(self, nome)~~ - Q4=A. O dominio nao
    # pode conhecer a instancia concreta do orquestrador (components.md 2.9 faz
    # de Agente configuracao montada no composition root), entao ela vem por
    # parametro. AgenteInvalido se o papel nao for ORQUESTRADOR.
    def buscar_tarefa(self, id: Identidade) -> Tarefa | None: ...
```

- ~~`criar_tarefa(nome)` — mesma forma de `criar_frente`. A tarefa nasce com um `Chat` cujo agente é
  o orquestrador padrão~~ **[emenda U1, 2026-08-26 — Q4=A]** `criar_tarefa(nome, agente_orquestrador)`
  — a tarefa nasce com um `Chat` cujo agente é **o orquestrador recebido por parâmetro**. "Orquestrador
  padrão" não podia existir no domínio: qual é o padrão é decisão do composition root. Preserva o
  comportamento de `Projeto.criar_sessao` de hoje, adaptado a identidade em vez de nome único.

### 1.4 `Tarefa`

```
class Tarefa:
    id: Identidade
    nome: str
    chats: list[Chat]
    etapas: list[Etapa]
    memoria: Memoria

    def criar_chat(self, agente: Agente) -> Chat: ...
    def buscar_chat(self, id: Identidade) -> Chat | None: ...
    def contar_orquestradores(self) -> int: ...
```

- `criar_chat(agente)` — **entrada**: `Agente` (configuração). **Saída**: `Chat` novo. Levanta
  erro de domínio se `agente.papel == ORQUESTRADOR` e `contar_orquestradores() >= 1` (invariante
  preservada de `Sessao.__post_init__`).

### 1.5 `Chat`

```
class Chat:
    id: Identidade
    nome: str
    agente: Agente

    def renomear(self, novo_nome: str) -> None: ...
```

- Note a ausência de `mensagens: list[Mensagem]` — mudança deliberada da Pergunta 3B. A
  transcrição de um chat é obtida via `PortaPersistencia.listar_mensagens(chat_id, ...)`, composta
  pelo serviço de aplicação, não carregada dentro da entidade de domínio.
- `renomear` — **entrada**: novo nome. **Saída**: nenhuma (efeito no próprio objeto). Não afeta
  identidade nem referências existentes (RF-F16).

### 1.6 `Etapa`

```
class Etapa:
    id: Identidade
    descricao: str
    executor: ExecutorEtapa   # AGENTE | USUARIO
    concluida: bool

    def concluir(self) -> None: ...
```

### 1.7 `Memoria`

```
class Memoria:
    anotacoes: dict[str, list[Anotacao]]
    versao: int = 0                 # [emenda U1] contador de escritas (CQ3=C)

    def anotar(self, chave: str, valor: str, autor: str) -> Anotacao: ...

class Anotacao:                     # [emenda U1, 2026-08-26]
    autor: str
    valor: str
    criada_em: datetime             # carimbo UTC proprio (CQ3=C)
```

- `anotar(chave, valor, autor)` — **entrada**: chave (string), valor (string), autor (string).
  **Saída**: nenhuma. **Correção de TD-03**: usa `self.anotacoes.setdefault(chave, []).append(...)`
  — nunca lança `KeyError` na primeira escrita de uma chave nova (RF-F06, critério de aceite de
  US-04: "sem lançar erro nem interromper a conversa").

### 1.8 `RaizWiki`

```
class RaizWiki:
    localizador: str   # ex.: "dados:wikis/<id_ambiente>"

    def esquema(self) -> str: ...   # parte antes de ":" — "dados" nesta iteração
```

- Nunca contém caminho absoluto (RNF-11). O domínio não resolve o esquema em caminho real.

### 1.9 `Agente` (configuração)

```
class Agente:
    nome: str
    papel: Papel   # ORQUESTRADOR | SUB_AGENTE
    modelo: str
    ferramentas: list[str]     # nomes qualificados de tool, não Callable
    regras: list[str]

# Sem responder(). Sem estado de sessão.
```

- Mudança em relação ao código atual: `ferramentas` deixa de ser `list[Callable]` (que soldava
  função Python à configuração) e passa a ser `list[str]` com os nomes qualificados que a
  `PortaSessao` usa para montar `allowed_tools` (medido pelo spike: nome qualificado é
  `mcp__<chave>__<tool>`).

---

## 2. Aplicação — catálogo de ações e parser

### 2.1 `Acao` (registro)

```
class Acao:
    nome: str
    descricao: str
    parametros: list[Parametro]     # nome, tipo, obrigatório
    escopo: Escopo                  # AMBIENTE | FRENTE | TAREFA
    executar: Callable[[Alvo, dict], Awaitable[Resultado]]
```

- `executar` é **assíncrono** (Pergunta E1) — `Awaitable[Resultado]`, nunca `Resultado` puro.
- **Entrada de `executar`**: `Alvo` (identidade explícita do que a ação afeta — nunca "o item
  ativo" implícito) e `dict` de argumentos já validados contra `parametros`.
- **Saída de `executar`**: `Resultado` tipado (ver 2.4).

### 2.2 `CatalogoDeAcoes`

```
class CatalogoDeAcoes:
    def listar(self, escopo: Escopo | None = None) -> list[Acao]: ...
    def buscar(self, nome: str) -> Acao | None: ...
    async def executar(self, nome: str, alvo: Alvo, args: dict) -> Resultado: ...
```

- `listar(escopo)` — **entrada**: escopo opcional para filtrar. **Saída**: lista de `Acao`,
  usada tanto pela paleta `/` quanto por botões (mesma fonte, RF-F17).
- `executar(nome, alvo, args)` — **entrada**: nome da ação, alvo explícito, argumentos.
  **Saída**: `Resultado`. Ponto único de execução, testável sem TUI e sem string.

### 2.3 `ParserDeComando`

```
class ParserDeComando:
    def detectar(self, entrada: str) -> bool: ...
    def interpretar(self, entrada: str, alvo_default: Alvo) -> tuple[str, dict]: ...
```

- `detectar(entrada)` — **entrada**: texto digitado. **Saída**: `True` se começa com `/`.
- `interpretar(entrada, alvo_default)` — **entrada**: texto (`"/nova-tarefa campanha de verao"`) e
  o alvo default vindo da tela atual. **Saída**: `(nome_da_acao, args)`. Corrige TD-11: parsing
  tolerante a argumento com espaço (usa o restante da string após o nome do comando como um único
  argumento textual, não `split()` ingênuo).

### 2.4 `Resultado`

```
class Resultado:
    sucesso: bool
    motivo: MotivoFalha | None    # estruturado, não string livre
    dado: Any | None              # payload de sucesso, se houver
```

- A TUI decide como renderizar (mensagem de sistema no modo `/`, toast ou validação inline no
  modo botão). O núcleo nunca produz string em português.

> **/!\ Emenda 2026-10-02 - Functional Design de U5 `acoes`.** As seções 2.1 a 2.4 acima ficam
> preservadas como registro de Application Design; valem as formas abaixo. Detalhe em
> `construction/acoes/functional-design/domain-entities.md`.
>
> - **2.1** ~~`executar: Callable[[Alvo, dict], Awaitable[Resultado]]`~~ → `efetivar(servico, alvo,
>   argumentos, referencias, acionamento) -> Awaitable[objeto]`: devolve o objeto ou levanta, e
>   **só o catálogo devolve `Resultado`** (G1). `Acao` ganha `chamadores` (Q2=B) e `Parametro`
>   ganha `descricao`, `opcoes` e `maximo` (G10).
> - **2.2** `executar` passa a receber **quem aciona** (R-FD5-2), e nasce `executar_comando` para a
>   barra, que aciona sempre como usuário (G8):
>
>   ```
>   class CatalogoDeAcoes:
>       def __init__(self, servico: ServicoDeAmbiente, confirmacao: PortaDeConfirmacao, acoes=...): ...
>       def listar(self, escopo: Escopo | None = None, chamador: Chamador | None = None) -> tuple[Acao, ...]: ...
>       def buscar(self, nome: str) -> Acao | None: ...
>       async def executar(self, nome: str, alvo: Alvo, argumentos: Mapping[str, object],
>                          acionamento: Acionamento) -> Resultado: ...
>       async def executar_comando(self, comando: ComandoDigitado, alvo: Alvo) -> Resultado: ...
>   ```
>
> - **2.3** ~~`interpretar(entrada, alvo_default) -> tuple[str, dict]`~~ → `interpretar(entrada) ->
>   ComandoDigitado(nome, texto)`: o parser não conhece o catálogo nem o alvo (Q9=A, R-FD5-3). Ganha
>   `formatar(comando) -> str`, a inversa (PBT-U5-01).
> - **2.4** `Resultado` ganha `detalhe: Mapping[str, str]` (estruturado, só na falha), e
>   `MotivoFalha` fica com 10 motivos (Q10=A, Q11=A).
> - **Novo** — `PortaDeConfirmacao.confirmar(pedido: PedidoDeConfirmacao) -> bool`, em
>   `aplicacao/portas/`, implementada por U9; **espera** a resposta, e só `True` confirma (Q4=A).

---

## 3. Aplicação — serviços

### 3.1 `ServicoDeAmbiente`

```
class ServicoDeAmbiente:
    async def criar_ambiente(self, nome: str, esquema: EsquemaWiki) -> Ambiente: ...
    async def carregar_ambiente(self, id: Identidade) -> Ambiente: ...
    async def criar_frente(self, id_ambiente: Identidade, nome: str) -> Resultado: ...
    async def criar_tarefa(self, id_frente: Identidade, nome: str) -> Resultado: ...
    async def anotar_memoria(self, id_tarefa: Identidade, chave: str, valor: str, autor: str) -> Resultado: ...
    async def concluir_etapa(self, id_etapa: Identidade) -> Resultado: ...
```

- `criar_ambiente(nome, esquema)` — **entrada**: nome do ambiente, `EsquemaWiki` (de maquete
  embutida ou formulário — US-09). **Saída**: `Ambiente` persistido, com `raiz_wiki` já apontando
  para uma wiki materializada (invariante: ao menos uma entidade — Pergunta 16B). Levanta erro de
  domínio se `esquema` não tiver nenhuma entidade.
- `carregar_ambiente(id)` — **entrada**: identidade. **Saída**: `Ambiente` reconstituído a partir
  do documento salvo (US-05). Chamada assíncrona; internamente pode envolver
  `asyncio.to_thread` no adaptador (Pergunta E1).
- `criar_frente`/`criar_tarefa`/`anotar_memoria`/`concluir_etapa` — cada uma delega a invariante ao
  objeto de domínio correspondente, persiste via `PortaPersistencia` numa transação por operação
  (Pergunta A/8B), e devolve `Resultado` tipado. Estas são as funções que o `CatalogoDeAcoes`
  referencia em `Acao.executar`.

> **/!\ Emenda 2026-10-02 - Functional Design de U4 `ambiente`.** O bloco acima foi substituído
> (texto preservado). ~~"invariante: ao menos uma entidade… Levanta erro de domínio se `esquema`
> não tiver nenhuma entidade"~~ (R-FD4-2, já revogado pela Parte B.3 de U1). ~~`-> Resultado`~~:
> o serviço devolve o objeto afetado ou levanta exceção tipada, e quem traduz para `Resultado` é o
> `CatalogoDeAcoes` de U5 (Q3=A). Toda operação recebe `id_ambiente` explícito (Q2=A); o
> orquestrador vem do construtor (Q8=A); `criar_chat` recebe o **nome** de um agente da lista
> fechada (Q9=A). São **10 operações** (Q7=X + C1=A):
>
> ```
> class ServicoDeAmbiente:
>     def __init__(self, persistencia, wiki, orquestrador: Agente, agentes_de_chat: tuple[Agente, ...]): ...
>     async def criar_ambiente(self, nome: str, esquema: EsquemaWiki) -> Ambiente: ...
>     async def carregar_ambiente(self, id_ambiente: Identidade) -> Ambiente: ...   # AmbienteInexistente (Q12=B)
>     async def listar_ambientes(self) -> list[ResumoAmbiente]: ...
>     async def apagar_ambiente(self, id_ambiente: Identidade) -> None: ...
>     async def criar_frente(self, id_ambiente, nome: str) -> Frente: ...
>     async def criar_tarefa(self, id_ambiente, id_frente, nome: str) -> Tarefa: ...
>     async def criar_chat(self, id_ambiente, id_tarefa, nome_agente: str, nome: str = "") -> Chat: ...
>     async def criar_etapa(self, id_ambiente, id_tarefa, descricao: str, executor: ExecutorEtapa) -> Etapa: ...
>     async def concluir_etapa(self, id_ambiente, id_etapa) -> Etapa: ...
>     async def anotar_memoria(self, id_ambiente, id_tarefa, chave: str, valor: str, autor: str) -> Anotacao: ...
> ```
>
> `reabrir_etapa` fica fora desta iteração. Detalhe em `construction/ambiente/functional-design/`.

### 3.2 `ServicoConversa`

```
class ServicoConversa:
    async def enviar(self, id_chat: Identidade, mensagem: str) -> AsyncIterator[EventoConversa]: ...
    async def carregar_transcricao(self, id_chat: Identidade, limite: int = 50) -> list[MensagemPersistida]: ...
```

- `enviar(id_chat, mensagem)` — **entrada**: identidade do chat, texto da mensagem do usuário.
  **Saída**: iterador assíncrono de `EventoConversa` (pedaço de texto | uso de ferramenta | fim de
  turno — Pergunta 5B). **Não devolve `Resultado`** — é por isso que conversar fica fora do
  `CatalogoDeAcoes` (Pergunta E2).
  - Efeito colateral especificado (Pergunta A/8B): insere a mensagem do usuário e uma linha de
    mensagem do agente com marca "em andamento" no início do turno; conforme o iterador emite
    pedaços de texto, atualiza essa linha; ao receber o evento de fim de turno, remove a marca.
    Persiste também um registro resumido de cada uso de ferramenta (Pergunta F/B) — não o stream
    de tokens parciais. **[Emenda 2026-08-26 / NFR Requirements de U2, Q6]** O registro guarda
    **tool + argumentos resumidos**; o ~~resultado resumido~~ **sai desta iteração** — no stream do
    SDK ele não existe no instante do evento, e nenhuma unidade desenha a correlação que o
    preencheria. **Pergunta F=B parcialmente revogada.**
  - ~~Se `PortaSessao` levantar erro de provedor, o iterador emite um `EventoConversa` do tipo erro e
    encerra~~ **[Emenda 2026-10-02 / FD de U6, R-FD6-2]** `PortaSessao.enviar` **nunca levanta**:
    a falha já chega como o evento final `FalhaDoTurno`, e o serviço o repassa — a exceção não
    escapa para a TUI como traceback (US-03, RNF-06).
- `carregar_transcricao(id_chat, limite)` — **entrada**: identidade do chat, limite de mensagens.
  **Saída**: lista de `MensagemPersistida` (papel, texto, uso de ferramenta resumido, timestamp),
  em ordem cronológica (garantida pela ordenabilidade de UUIDv7 — Pergunta 4B). Usada por US-06 ao
  reabrir uma aba.

### 3.3 `ServicoBibliotecario`

```
class ServicoBibliotecario:
    async def enviar(self, mensagem: str) -> AsyncIterator[EventoConversa]: ...
    def propostas_pendentes(self) -> list[PropostaWiki]: ...
    async def aprovar(self, id_proposta: Identidade) -> Resultado: ...
    async def rejeitar(self, id_proposta: Identidade) -> Resultado: ...
```

- `enviar(mensagem)` — mesma forma de `ServicoConversa.enviar`, mas dirigida à sessão viva própria
  do bibliotecário (Pergunta 3-bis). Quando o agente chama `propor_entidade`/`propor_propriedade`
  através das `FerramentasWiki`, o resultado da tool é uma `PropostaWiki` capturada aqui, não uma
  escrita efetiva.
- `propostas_pendentes()` — **saída**: lista de `PropostaWiki` aguardando decisão do usuário. Uma
  proposta pode conter várias páginas (reconciliação registrada no plano, §5.4) — é isso que
  transforma "aprovar" num ato por promoção.
- `aprovar(id_proposta)` — **entrada**: identidade da proposta. **Saída**: `Resultado`. Efetiva a
  escrita via `PortaWiki`, valida links (recusa ou converte em nova proposta — Pergunta 14B), e
  aciona a renderização do `index.md` (Pergunta 15D).
- `rejeitar(id_proposta)` — descarta sem tocar o filesystem.

### 3.4 `EsquemaWiki`

```
class EsquemaWiki:
    nome: str                          # [REVOGADO 2026-09-23 / C6] era o nome da maquete
    descricao: str                     # [REVOGADO 2026-09-23 / C6] a wiki nao tem descricao
    entidades: list[EntidadeSemente]   # cada uma: nome, list[PropriedadeSemente(nome, descricao)]

    @staticmethod
    def carregar_toml(caminho: Path) -> "EsquemaWiki": ...   # [ADIADA 2026-09-23 / Q8]
    @staticmethod
    def a_partir_do_formulario(dados: dict) -> "EsquemaWiki": ...
    @staticmethod
    def vazio() -> "EsquemaWiki": ...  # [NOVA 2026-09-23] estado valido (Parte B.3 de U1)
```

> **/!\ Emenda 2026-09-23 - Functional Design de U3 `wiki`.** **`carregar_toml` ADIADA**: as maquetes prontas saíram desta iteração (Q8),
> e sem elas o método fica sem nenhum chamador. A assinatura fica preservada acima, não apagada,
> para a iteração que as trouxer de volta. **`nome` e `descricao` REVOGADOS** (C6): a wiki não tem
> descrição, e o nome era o da maquete. **`vazio()` acrescentada**: a invariante "ao menos uma
> entidade" foi revogada na Parte B.3 do FD de U1, então esquema sem entidade é estado válido e
> precisa de construtor nomeado. Forma final em
> `construction/wiki/functional-design/domain-entities.md` §5.

- `carregar_toml(caminho)` — **entrada**: caminho de uma maquete embutida. **Saída**:
  `EsquemaWiki`. Usa `tomllib` (stdlib), **só leitura** (Pergunta 16B/C) — não existe
  `salvar_toml` nesta iteração.
- `a_partir_do_formulario(dados)` — **entrada**: estrutura preenchida pelo usuário na criação do
  ambiente (US-09). **Saída**: `EsquemaWiki` equivalente, mesma validação de invariante.

---

## 4. Portas (interfaces assíncronas)

### 4.1 `PortaPersistencia`

```
class PortaPersistencia(Protocol):
    async def salvar_ambiente(self, ambiente: Ambiente) -> None: ...
    async def carregar_ambiente(self, id: Identidade) -> Ambiente | None: ...
    async def inserir_mensagem(self, id_chat: Identidade, papel: str, texto: str, em_andamento: bool) -> Identidade: ...
    async def atualizar_mensagem(self, id_mensagem: Identidade, texto: str, em_andamento: bool) -> None: ...
    async def registrar_uso_ferramenta(self, id_mensagem: Identidade, tool: str, args_resumo: str) -> None: ...  # [emenda 2026-08-26 / NFR Q6] sem resultado_resumo
    async def listar_mensagens(self, id_chat: Identidade, limite: int) -> list[MensagemPersistida]: ...
```

> **[Emenda — Functional Design de U2, 2026-08-26]** O bloco acima está **incompleto**. O contrato
> final tem três métodos a mais e dois parâmetros novos:
>
> ```
>     async def listar_ambientes(self) -> list[ResumoAmbiente]: ...            # RN-P-24
>     async def apagar_ambiente(self, id: Identidade) -> None: ...             # Q8=B
>     async def anotar(self, id_ambiente, id_tarefa, chave, anotacao) -> None  # Q2=B
>     # inserir_mensagem ganha id_ambiente (sem ela apagar_ambiente nao acha as mensagens)
>     # listar_mensagens ganha antes_de: Identidade | None  (cursor, Q5=A)
> ```
>
> `salvar_ambiente` passa a poder levantar **`ConflitoDeVersao`** (Q4=C): não é mais "sempre
> funciona". Semântica completa em `construction/persistencia/functional-design/business-logic-model.md`.

- Todas as assinaturas são `async` uniformemente (Pergunta E1). Nenhuma menciona `sqlite3`,
  `cursor`, `conexão` ou SQL — vocabulário de domínio, como D-ARQ-04 exige.
- `inserir_mensagem(..., em_andamento=True)` e `atualizar_mensagem(...)` juntas implementam a
  política de gravação da Pergunta A/8B (linha inserida no início do turno, atualizada durante o
  streaming).

### 4.2 `PortaSessao`

```
class PortaSessao(Protocol):
    async def abrir(self, agente: Agente) -> SessaoViva: ...
    async def enviar(self, sessao: SessaoViva, mensagem: str) -> AsyncIterator[EventoConversa]: ...
    async def fechar(self, sessao: SessaoViva) -> None: ...
```

- `abrir(agente)` — **entrada**: configuração do agente. **Saída**: `SessaoViva` (objeto opaco de
  aplicação, dono é o chat/serviço — nunca o domínio, Pergunta 6A). Suporta múltiplas sessões vivas
  simultâneas no mesmo processo (medido pelo spike) — é o que permite orquestrador e bibliotecário
  conversarem em paralelo.
- `enviar(sessao, mensagem)` — **saída**: iterador assíncrono de `EventoConversa`
  (`PedacoDeTexto | UsoDeFerramenta | FimDeTurno | ErroProvedor`).
- `fechar(sessao)` — libera recursos do ciclo de vida do SDK.

> **/!\ Emenda 2026-08-25 - Units Generation.** **R4 / Q12=A**: o `AdaptadorSessaoClaude` recebe no construtor um **registro nome->função** de ferramentas, montado pelo composition root. `abrir(agente)` resolve os nomes que `Agente` carrega contra esse registro e monta o servidor MCP in-process da sessão (**Q11=A**). ~~A assinatura de `abrir` não muda; o que muda é de onde vem a função por trás de cada nome.~~ Unidade dona: **U6**.

> **/!\ Emenda 2026-10-02 - Functional Design de U6 `sessao`.** A frase riscada acima não se
> sustentou: uma função fixa no construtor não sabe de que chat é a sessão, e U5 exige a ferramenta
> amarrada à tarefa do chat (R-FD6-1). Contrato final:
>
> ```
> class PortaSessao(Protocol):
>     async def abrir(self, agente: Agente, contexto: ContextoDaSessao) -> SessaoViva: ...  # Q8=A
>     def enviar(self, sessao: SessaoViva, mensagem: str) -> AsyncIterator[EventoConversa]: ...
>     async def fechar(self, sessao: SessaoViva) -> None: ...
>
> EventoConversa = MensagemEntregue | PedacoDeTexto | UsoDeFerramenta | FimDeTurno | FalhaDoTurno
> ```
>
> - O registro é de **fábricas**: cada nome aponta para uma família e uma
>   `fabrica(contexto, agente) -> Ferramenta`, chamada em `abrir` (Q8=A).
> - `abrir` só levanta erro de montagem (`ConfiguracaoDeSessaoInvalida`, `AdaptadorEncerrado`),
>   nunca por causa do provedor (Q2=B, G5). `enviar` **nunca levanta** (R-FD6-2).
> - ~~`ErroProvedor`~~ → **`FalhaDoTurno(motivo, detalhe)`**, com 9 motivos (G1, Q4=A).
> - `MensagemEntregue(conversa_nova)` abre todo turno entregue (C2=A, D-C2-1, G2).
> - `enviar` deixa de ser `async def`: devolve o iterador direto, e o turno começa na primeira
>   iteração.
> - Detalhe em `construction/sessao/functional-design/`.

### 4.3 `PortaWiki`

```
class PortaWiki(Protocol):
    async def listar(self, localizador: str, caminho: str) -> list[str]: ...
    async def ler(self, localizador: str, caminho_pagina: str) -> ConteudoPagina: ...
    # [emenda Q13=A] removida desta iteracao:
    # async def buscar(self, localizador: str, termo: str) -> list[ResultadoBusca]: ...
    async def escrever_proposta(self, localizador: str, proposta: PropostaWiki) -> None: ...
    async def renderizar_index(self, localizador: str, nome: str) -> None: ...  # [emenda 2026-09-23]
```

> **/!\ Emenda 2026-09-23 - Functional Design de U3 `wiki`.** **`renderizar_index` ganha `nome`.** O cabeçalho do índice é
> `# Wiki — <nome do ambiente>` (formato fixado pelo usuário na C1/C6), e o adaptador não pode
> descobrir esse nome sem conhecer `Ambiente` ou a persistência — o que violaria D-ARQ-08. Quem
> chama é `ServicoDeAmbiente` (U4) e `ServicoBibliotecario` (U8), que já têm o ambiente em mãos.
> **É a única mudança de assinatura da porta nesta unidade**: as quatro operações continuam quatro,
> e a materialização do `EsquemaWiki` não virou operação nova — o esquema é convertido em
> `PropostaWiki` e passa por `escrever_proposta`.

> **/!\ Emenda 2026-10-02 - Functional Design de U4 `ambiente` (Q6=A).** **`PortaWiki` ganha uma
> quinta operação**, `async def apagar(self, localizador: str) -> None`: remove a raiz inteira,
> confinada por `resolver_raiz`; raiz inexistente é no-op; falha de I/O vira
> `ArmazenamentoIndisponivel`. Único chamador: `ServicoDeAmbiente.apagar_ambiente`, que cumpre assim
> o critério 6 de U4 sem tocar o disco diretamente. A frase acima, "as quatro operações continuam
> quatro", valia para U3 e foi superada por esta emenda. Implementada em `WikiDeArquivos` durante o
> Code Generation de U4 (U3 reaberta para este acréscimo).

- Todas recebem `localizador` (o valor de `RaizWiki.localizador`, com esquema — Pergunta D) em vez
  de caminho físico. A resolução do esquema para caminho real acontece dentro do adaptador.
- `escrever_proposta` só é chamada por `ServicoBibliotecario.aprovar` — nunca diretamente por
  código que responde a uma chamada de tool do agente (Pergunta 9A).

---

## 5. Ferramentas do bibliotecário (`FerramentasWiki`, expostas por MCP)

```
async def listar(args: {"caminho": str}) -> ToolResult: ...
async def ler(args: {"caminho_pagina": str}) -> ToolResult: ...
# [emenda Q13=A] removida desta iteracao:
# async def buscar(args: {"termo": str}) -> ToolResult: ...
async def propor_entidade(args: {"nome": str}) -> ToolResult: ...
async def propor_propriedade(args: {
    "entidade": str,
    "propriedade": str,
    "conteudo": str,
    "descricao": str,       # obrigatório — Pergunta 15D
    "links": list[str],
}) -> ToolResult: ...
```

- Assinaturas são o schema exposto ao modelo via MCP in-process (nome qualificado:
  `mcp__wiki__propor_propriedade`, seguindo o padrão medido pelo spike). **Nenhum parâmetro admite
  um terceiro nível de profundidade** — a violação do esquema de dois níveis é irrepresentável
  (Pergunta 10B/13A).
- `descricao` é campo obrigatório em `propor_propriedade` — não existe chamada válida sem ele
  (Pergunta 15D, elimina o esquecimento por construção, não por instrução).
- Todas as chamadas de proposta retornam um identificador de proposta pendente
  (`ServicoBibliotecario.propostas_pendentes()`), nunca confirmam escrita efetiva.
- Ferramentas nativas de escrita são negadas na configuração da sessão do bibliotecário
  (`tools=[]`, medido pelo spike) — reforço estrutural de RF-F14/RNF-10, independente do prompt.

---

## 6. Adaptadores — pontos de conversão (sem expor tipo do SDK/SQLite fora daqui)

### 6.1 `AdaptadorSessaoClaude.enviar` — conversão de tipos

**Entrada interna**: mensagens concretas do SDK (`AssistantMessage`, `TextBlock`, `ToolUseBlock`,
`ToolResultBlock`, `ResultMessage`, medidos pelo spike).
**Saída pública**: `EventoConversa` (tipo de aplicação). Esta função é o único lugar do sistema
onde um tipo do `claude_agent_sdk` é lido — a conversão acontece antes de qualquer dado atravessar
a fronteira da porta (RF-F04).

> **/!\ Emenda 2026-10-02 - Functional Design de U6 `sessao`.** `ToolResultBlock` é **lido e
> descartado**: resultado de ferramenta não vira evento desde a NFR Q6 de U2 (R-FD6-3). Entram
> também as **mensagens parciais** do SDK, porque o texto chega aos poucos (Q1=B). A tabela
> completa da conversão está em `construction/sessao/functional-design/business-logic-model.md` §3.1.

### 6.2 `AdaptadorWikiFilesystem.resolver` — resolução de localizador

```
def resolver(self, localizador: str) -> Path: ...
```

**Entrada**: `"dados:wikis/<id_ambiente>"`. **Saída**: `Path` absoluto no disco, calculado a
partir da raiz de dados recebida no construtor do adaptador (vinda do composition root). Levanta
erro se o esquema (parte antes de `:`) não for reconhecido — hoje só `dados:` existe.

---

## 7. Resumo de conformidade com as decisões do plano

| Decisão | Onde aparece nas assinaturas |
|---|---|
| Identidade opaca (Pergunta 4B) | Todo método usa `Identidade`, nunca índice ou nome, para referenciar |
| Catálogo assíncrono, conversa fora (E1/E2) | `Acao.executar` é `Awaitable[Resultado]`; `ServicoConversa.enviar`/`ServicoBibliotecario.enviar` devolvem `AsyncIterator`, não `Resultado` |
| Composição toda na borda (Pergunta 11A) | Nenhum serviço ou porta constrói adaptador; construtores recebem porta já pronta |
| Núcleo sem SDK/SQL (RF-F04, D-ARQ-04) | Tipos do SDK só aparecem dentro de `AdaptadorSessaoClaude`; vocabulário de `PortaPersistencia` não menciona SQL |
| Wiki só por proposta (9A/13A) | Não existe método de escrita direta em `FerramentasWiki`; só `propor_*` |
| Descrição obrigatória (15D) | `propor_propriedade` não tem chamada válida sem `descricao` |
| Confinamento de caminho (RNF-10/11) | `PortaWiki` e `FerramentasWiki` só recebem `localizador`/`caminho` lógico, nunca caminho físico |
