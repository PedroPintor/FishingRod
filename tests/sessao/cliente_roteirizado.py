"""O cliente roteirizado: entra no lugar do ClaudeSDKClient, sem CLI (G11, R-ND6-12).

Nao e uma segunda implementacao do SDK: e o CLI fingido. Ele segue um roteiro
de mensagens NO FORMATO DO SDK (os tipos de verdade de `claude_agent_sdk`), e
cada fase - subir, entregar, interromper, desconectar - pode ir bem, falhar,
travar ate o teste liberar ou demorar.

Duas coisas ele faz como o CLI de verdade:
- pede permissao pelo `can_use_tool` das opcoes antes de chamar uma
  ferramenta, e chama a ferramenta pelo `SdkMcpBridge` do proprio SDK, com o
  JSON-RPC que o CLI manda. Passa pelo caminho real, inclusive a validacao do
  esquema (A16) e a conversao do resultado;
- conta PROCESSOS VIVOS: um processo nasce no comeco de `connect` e morre em
  `disconnect`, ou quando `connect` falha ou e cancelado - o SDK desconecta
  sozinho nesses casos. E o que deixa conferir RN-S-38 e N5 sem processo de
  verdade.

A fabrica guarda as opcoes que recebeu (para `test_opcoes.py`).
"""

import asyncio
import itertools
from collections import deque
from collections.abc import AsyncIterator, Iterable
from dataclasses import dataclass, field
from typing import Any

import mcp.types
from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    RateLimitEvent,
    RateLimitInfo,
    ResultMessage,
    StreamEvent,
    SystemMessage,
    TextBlock,
    ThinkingBlock,
    ToolPermissionContext,
    ToolResultBlock,
    ToolUseBlock,
    UserMessage,
)
from claude_agent_sdk._internal.sdk_mcp_bridge import SdkMcpBridge

# --------------------------------------------------------------------------
# Comportamentos de uma fase
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class Bem:
    pass


@dataclass(frozen=True)
class Falha:
    excecao: BaseException


@dataclass(frozen=True)
class Trava:
    """Fica parado ate `liberar` (ou para sempre, sem ele). Depois de liberado,
    vai bem."""

    liberar: asyncio.Event | None = None


@dataclass(frozen=True)
class Lento:
    segundos: float


type Comportamento = Bem | Falha | Trava | Lento


async def _comportar(comportamento: Comportamento) -> None:
    match comportamento:
        case Falha(excecao=excecao):
            raise excecao
        case Trava(liberar=liberar):
            if liberar is None:
                await asyncio.Event().wait()
            else:
                await liberar.wait()
        case Lento(segundos=segundos):
            await asyncio.sleep(segundos)


# --------------------------------------------------------------------------
# Passos de uma resposta
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class Mensagem:
    """Uma mensagem do SDK, entregue como veio."""

    mensagem: object


@dataclass(frozen=True)
class ChamarFerramenta:
    """O CLI chama a ferramenta: permissao, depois `tools/call` pela ponte.
    `concorrente` nao espera a resposta antes do proximo passo."""

    nome: str
    argumentos: dict[str, Any] = field(default_factory=dict)
    concorrente: bool = False


@dataclass(frozen=True)
class Levantar:
    """O fluxo do SDK levanta esta excecao."""

    excecao: BaseException


@dataclass(frozen=True)
class Acabar:
    """O fluxo acaba sem mensagem de resultado."""


@dataclass(frozen=True)
class Parar:
    """O fluxo fica parado ate `liberar` (ou para sempre). `chegou` avisa o
    teste de que o turno esta parado ali."""

    liberar: asyncio.Event | None = None
    chegou: asyncio.Event | None = None


type Passo = Mensagem | ChamarFerramenta | Levantar | Acabar | Parar


def resultado(erro: bool = False, subtipo: str = "success", status: int | None = None) -> Mensagem:
    return Mensagem(
        ResultMessage(
            subtype=subtipo,
            duration_ms=1,
            duration_api_ms=1,
            is_error=erro,
            num_turns=1,
            session_id="sessao-roteirizada",
            api_error_status=status,
        )
    )


_INTERROMPIDA = resultado(erro=True, subtipo="error_during_execution")


@dataclass
class RoteiroDoTurno:
    """Uma resposta. `cauda` e o que o fluxo manda depois de `interrupt()`."""

    passos: list[Passo] = field(default_factory=list)
    entrega: Comportamento = field(default_factory=Bem)
    cauda: list[Passo] = field(default_factory=lambda: [_INTERROMPIDA])


def turno_de_texto(*blocos: str) -> RoteiroDoTurno:
    """O caso comum: os blocos inteiros, sem trechos, e o resultado."""
    return RoteiroDoTurno([*(Mensagem(assistente(TextBlock(b))) for b in blocos), resultado()])


# --------------------------------------------------------------------------
# Construtores de mensagem do SDK
# --------------------------------------------------------------------------

_UUIDS = itertools.count()


def _uuid() -> str:
    return f"u-{next(_UUIDS)}"


def assistente(*blocos: Any, erro: str | None = None) -> AssistantMessage:
    return AssistantMessage(content=list(blocos), model="modelo-roteirizado", error=erro)


def evento(dados: dict[str, Any]) -> StreamEvent:
    return StreamEvent(uuid=_uuid(), session_id="sessao-roteirizada", event=dados)


def inicio_de_mensagem() -> StreamEvent:
    return evento({"type": "message_start", "message": {}})


def inicio_de_texto(indice: int) -> StreamEvent:
    return evento({"type": "content_block_start", "index": indice, "content_block": {"type": "text", "text": ""}})


def trecho(indice: int, texto: str) -> StreamEvent:
    return evento({"type": "content_block_delta", "index": indice, "delta": {"type": "text_delta", "text": texto}})


def inicio_de_ferramenta(indice: int, nome: str) -> StreamEvent:
    return evento(
        {
            "type": "content_block_start",
            "index": indice,
            "content_block": {"type": "tool_use", "id": f"t-{indice}", "name": nome, "input": {}},
        }
    )


def trecho_de_ferramenta(indice: int, json_parcial: str) -> StreamEvent:
    return evento(
        {"type": "content_block_delta", "index": indice, "delta": {"type": "input_json_delta", "partial_json": json_parcial}}
    )


def trecho_de_pensamento(indice: int) -> StreamEvent:
    return evento({"type": "content_block_delta", "index": indice, "delta": {"type": "thinking_delta", "thinking": "hm"}})


def pedido(nome: str, argumentos: dict[str, Any] | None = None) -> AssistantMessage:
    return assistente(ToolUseBlock(id=_uuid(), name=nome, input=dict(argumentos or {})))


def pensamento() -> AssistantMessage:
    return assistente(ThinkingBlock(thinking="pensando", signature="assinatura"))


def resultado_de_ferramenta() -> UserMessage:
    return UserMessage(content=[ToolResultBlock(tool_use_id="t", content="feito", is_error=False)])


def sistema(subtipo: str = "init") -> SystemMessage:
    return SystemMessage(subtype=subtipo, data={})


def limite(status: str, resets_at: int | None = None) -> RateLimitEvent:
    return RateLimitEvent(
        rate_limit_info=RateLimitInfo(status=status, resets_at=resets_at),
        uuid=_uuid(),
        session_id="sessao-roteirizada",
    )


# --------------------------------------------------------------------------
# O cliente
# --------------------------------------------------------------------------


class ClienteRoteirizado:
    def __init__(self, fabrica: "FabricaRoteirizada", opcoes: ClaudeAgentOptions, subida: Comportamento) -> None:
        self._fabrica = fabrica
        self.opcoes = opcoes
        self._subida = subida
        self._vivo = False
        self._passos: deque[Passo] = deque()
        self._turno: RoteiroDoTurno | None = None
        self._pontes: dict[str, SdkMcpBridge] = {}
        self._iniciadas: set[str] = set()
        self._ids = itertools.count(1)
        self._chamadas: set[asyncio.Task[None]] = set()
        self.consultas: list[str] = []
        self.interrupcoes = 0
        self.negadas: list[str] = []
        self.resultados: list[tuple[str, dict[str, Any]]] = []
        self.desconectado = asyncio.Event()

    # O processo -----------------------------------------------------------

    def _nascer(self) -> None:
        if not self._vivo:
            self._vivo = True
            self._fabrica.vivos += 1
            self._fabrica.nascidos += 1

    def _morrer(self) -> None:
        if self._vivo:
            self._vivo = False
            self._fabrica.vivos -= 1
        self.desconectado.set()

    @property
    def vivo(self) -> bool:
        return self._vivo

    # A API do ClaudeSDKClient ----------------------------------------------

    async def connect(self, prompt: object = None) -> None:
        self._nascer()
        try:
            await _comportar(self._subida)
        except BaseException:
            # Como o SDK: connect que falha (ou e cancelado) desconecta.
            await self._encerrar_pontes()
            self._morrer()
            raise

    async def query(self, prompt: str, session_id: str = "default") -> None:
        if not self._vivo:
            raise RuntimeError("query sem processo")
        self._turno = self._fabrica.proximo_turno()
        self.consultas.append(prompt)
        await _comportar(self._turno.entrega)
        self._passos = deque(self._turno.passos)

    async def receive_response(self) -> AsyncIterator[Any]:
        while self._passos:
            passo = self._passos.popleft()
            match passo:
                case Mensagem(mensagem=mensagem):
                    yield mensagem
                    if isinstance(mensagem, ResultMessage):
                        return
                case ChamarFerramenta(nome=nome, argumentos=argumentos, concorrente=concorrente):
                    # Como no SDK, a chamada roda numa tarefa filha: quem le o
                    # fluxo pode ser cancelado sem cancelar a ferramenta.
                    tarefa = asyncio.create_task(self._chamar(nome, argumentos))
                    self._chamadas.add(tarefa)
                    tarefa.add_done_callback(self._chamadas.discard)
                    if not concorrente:
                        await asyncio.wait({tarefa})
                case Levantar(excecao=excecao):
                    raise excecao
                case Acabar():
                    return
                case Parar(liberar=liberar, chegou=chegou):
                    if chegou is not None:
                        chegou.set()
                    await (liberar.wait() if liberar is not None else asyncio.Event().wait())
        # Sem passos: o fluxo nao acaba sozinho - como o SDK, que espera.
        await asyncio.Event().wait()

    async def interrupt(self) -> None:
        self.interrupcoes += 1
        await _comportar(self._fabrica.interrupcao)
        self._passos = deque(self._turno.cauda if self._turno is not None else [_INTERROMPIDA])

    async def disconnect(self) -> None:
        try:
            await _comportar(self._fabrica.desconexao)
        finally:
            for tarefa in tuple(self._chamadas):
                tarefa.cancel()  # como o SDK: o que ainda roda e cancelado (A14)
            await self._encerrar_pontes()
            self._morrer()

    # As ferramentas, pelo caminho do CLI ----------------------------------

    async def _chamar(self, nome: str, argumentos: dict[str, Any]) -> None:
        decisao = await self.opcoes.can_use_tool(nome, dict(argumentos), ToolPermissionContext(tool_use_id=_uuid()))
        if decisao.behavior != "allow":
            self.negadas.append(nome)
            return
        partes = nome.split("__")
        servidor = self.opcoes.mcp_servers.get(partes[1]) if len(partes) == 3 else None
        if servidor is None:
            self.negadas.append(nome)
            return
        ponte = await self._ponte(partes[1], servidor)
        resposta = await ponte.handle(
            {
                "jsonrpc": "2.0",
                "id": next(self._ids),
                "method": "tools/call",
                "params": {"name": partes[2], "arguments": dict(argumentos)},
            }
        )
        self.resultados.append((nome, resposta))

    async def _ponte(self, chave: str, servidor: Any) -> SdkMcpBridge:
        ponte = self._pontes.get(chave)
        if ponte is None:
            ponte = self._pontes[chave] = SdkMcpBridge(chave, servidor["instance"])
        if chave not in self._iniciadas:
            self._iniciadas.add(chave)
            await ponte.handle(
                {
                    "jsonrpc": "2.0",
                    "id": next(self._ids),
                    "method": "initialize",
                    "params": {
                        "protocolVersion": mcp.types.LATEST_PROTOCOL_VERSION,
                        "capabilities": {},
                        "clientInfo": {"name": "cliente-roteirizado", "version": "0"},
                    },
                }
            )
            await ponte.handle({"jsonrpc": "2.0", "method": "notifications/initialized"})
        return ponte

    async def _encerrar_pontes(self) -> None:
        pontes, self._pontes = self._pontes, {}
        for ponte in pontes.values():
            await ponte.aclose()

    def textos_dos_resultados(self) -> list[tuple[str, str, bool]]:
        """(nome, texto, erro) de cada chamada de ferramenta que voltou."""
        saida = []
        for nome, resposta in self.resultados:
            corpo = resposta.get("result", {})
            texto = "".join(c.get("text", "") for c in corpo.get("content", []))
            saida.append((nome, texto, bool(corpo.get("isError"))))
        return saida


class FabricaRoteirizada:
    """Entra no lugar de `cliente_real`. Cada conexao pega a proxima subida de
    `subidas` (sem mais, vai bem); cada `query` pega o proximo turno de
    `turnos` (sem mais, responde um texto)."""

    def __init__(
        self,
        *,
        subidas: Iterable[Comportamento] = (),
        turnos: Iterable[RoteiroDoTurno] = (),
        interrupcao: Comportamento = Bem(),
        desconexao: Comportamento = Bem(),
    ) -> None:
        self.subidas: deque[Comportamento] = deque(subidas)
        self.turnos: deque[RoteiroDoTurno] = deque(turnos)
        self.interrupcao = interrupcao
        self.desconexao = desconexao
        self.opcoes: list[ClaudeAgentOptions] = []
        self.clientes: list[ClienteRoteirizado] = []
        self.vivos = 0
        self.nascidos = 0

    def __call__(self, opcoes: ClaudeAgentOptions) -> ClienteRoteirizado:
        self.opcoes.append(opcoes)
        cliente = ClienteRoteirizado(self, opcoes, self.subidas.popleft() if self.subidas else Bem())
        self.clientes.append(cliente)
        return cliente

    def proximo_turno(self) -> RoteiroDoTurno:
        return self.turnos.popleft() if self.turnos else turno_de_texto("resposta padrao")
