"""A conexao com o CLI e a tarefa dona dela (DP-S-01..05, DP-S-08, N3).

O `close()` do SDK nao resiste a `task.cancel()` (A4, A5), e o ESC da tela e
exatamente um cancelamento. Por isso o cliente do SDK vive inteiro numa tarefa
so - a DONA -, que sobe o cliente, entrega as mensagens, le o provedor e
desconecta. Ninguem cancela a dona: quem precisa que ela pare deixa um RECADO
(`interromper` ou `descartar`), sincrono, e o recado vence o prazo da espera em
que ela estiver. A espera termina por prazo vencido, dentro da propria dona,
que segue para a limpeza sem estar cancelada.

| fase       | espera                        | prazo      | interromper         | descartar      |
|------------|-------------------------------|------------|---------------------|----------------|
| subida     | connect()                     | 60 s       | (nao acontece, N3)  | fechamento     |
| ociosa     | o proximo turno               | -          | avisa que sossegou  | fechamento     |
| entrega    | query(texto)                  | -          | (nao acontece, N3)  | fechamento     |
| resposta   | mensagens ate o resultado     | - (NFR-S-12) | cauda             | fechamento     |
| cauda      | interrupt() + o resto, fora   | 5 s        | ja esta nela        | fechamento     |
| fechamento | disconnect()                  | o do SDK   | ignorado            | ignorado       |

Uma reconexao e uma Conexao nova. E o UNICO modulo de U6 com temporizador
(DP-S-08): os dois prazos chegam no construtor.
"""

import asyncio
import logging
from collections.abc import AsyncIterator, Callable, Coroutine
from dataclasses import dataclass
from enum import Enum
from typing import Any, Protocol

from claude_agent_sdk import ClaudeAgentOptions, ClaudeSDKClient, ResultMessage

from fishingrod.adaptadores.sessao.falhas import Causa, Fase, FimSemResultado, PrazoVencido

_log = logging.getLogger("fishingrod.sessao")
_log.addHandler(logging.NullHandler())


# --------------------------------------------------------------------------
# O cliente do SDK
# --------------------------------------------------------------------------


class ClienteDoSdk(Protocol):
    """O pedaco de `ClaudeSDKClient` que a dona usa. Os testes entregam um
    cliente roteirizado, com mensagens no formato do SDK, sem CLI (G11)."""

    async def connect(self) -> None: ...

    async def query(self, prompt: str) -> None: ...

    def receive_response(self) -> AsyncIterator[Any]: ...

    async def interrupt(self) -> None: ...

    async def disconnect(self) -> None: ...


type FabricaDeCliente = Callable[[ClaudeAgentOptions], ClienteDoSdk]


def cliente_real(opcoes: ClaudeAgentOptions) -> ClienteDoSdk:
    return ClaudeSDKClient(options=opcoes)


# --------------------------------------------------------------------------
# O que a dona escreve na fila do turno (nfr-design-patterns.md 2.3)
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class Entregue:
    """`query()` voltou: a mensagem chegou ao provedor. `primeira` e o
    `conversa_nova` - a primeira entrega desta conexao."""

    primeira: bool


@dataclass(frozen=True)
class DoProvedor:
    mensagem: object


@dataclass(frozen=True)
class FimDaResposta:
    mensagem: ResultMessage


@dataclass(frozen=True)
class Caiu:
    """A dona caiu numa fase, e vai ao fechamento."""

    fase: Fase
    causa: Causa


@dataclass(frozen=True)
class Encerrada:
    """A dona terminou. Chega depois de tudo; quem le um turno so a ve se a
    dona terminou sem avisar a queda - o que so `fechar` faz."""


type ItemDoTurno = Entregue | DoProvedor | FimDaResposta | Caiu | Encerrada


# --------------------------------------------------------------------------
# A dona
# --------------------------------------------------------------------------


class Recado(Enum):
    INTERROMPER = "interromper"
    DESCARTAR = "descartar"


class Etapa(Enum):
    """As seis fases da dona."""

    SUBIDA = "subida"
    OCIOSA = "ociosa"
    ENTREGA = "entrega"
    RESPOSTA = "resposta"
    CAUDA = "cauda"
    FECHAMENTO = "fechamento"


class _Recadada(Exception):
    """Interna: um recado venceu a espera."""


class _Vencida(Exception):
    """Interna: o prazo da fase venceu sem recado."""


class Conexao:
    """Uma conexao: uma tarefa dona, uma fila de entrada e dois recados.

    O adaptador guarda a referencia forte a `tarefa` (o asyncio so guarda
    referencia fraca) e espera por ela com `asyncio.wait`, nunca com `await
    tarefa` - que cancelaria a dona junto com quem espera (DP-S-07).

    `ao_sossegar` e chamado quando um turno interrompido termina de vez com o
    processo vivo (a cauda acabou, ou a resposta ja tinha acabado);
    `ao_terminar`, quando a dona termina. Os dois sao sincronos.
    """

    def __init__(
        self,
        cliente: ClienteDoSdk,
        *,
        prazo_de_subida: float,
        prazo_de_interrupcao: float,
        ao_sossegar: Callable[[], None],
        ao_terminar: Callable[[], None],
    ) -> None:
        self._cliente = cliente
        self._prazo_de_subida = prazo_de_subida
        self._prazo_de_interrupcao = prazo_de_interrupcao
        self._ao_sossegar = ao_sossegar
        self._ao_terminar = ao_terminar
        self._entrada: asyncio.Queue[str] = asyncio.Queue()
        self._fila: asyncio.Queue[ItemDoTurno] | None = None
        self._recado: Recado | None = None
        self._limite: asyncio.Timeout | None = None
        self.etapa = Etapa.SUBIDA
        self.tarefa = asyncio.create_task(self._dona())

    # ----------------------------------------------------------------------
    # O que o adaptador chama - tudo sincrono
    # ----------------------------------------------------------------------

    def entregar(self, texto: str, fila: asyncio.Queue[ItemDoTurno]) -> None:
        """Um turno: a dona entrega o texto e passa a escrever nesta fila. Uma
        fila por turno (DP-S-04): o resto de um turno interrompido nunca chega
        a uma fila que alguem ainda le."""
        self._fila = fila
        self._entrada.put_nowait(texto)

    def interromper(self) -> None:
        self._recadar(Recado.INTERROMPER)

    def descartar(self) -> None:
        self._recadar(Recado.DESCARTAR)

    def _recadar(self, recado: Recado) -> None:
        """DP-S-03: reagenda o prazo da espera atual para agora. Fora de uma
        espera, o recado fica marcado e a dona o confere antes da proxima
        fase. Descartar vence interromper."""
        if self.tarefa.done():
            return
        if self._recado is not Recado.DESCARTAR:
            self._recado = recado
        if self._limite is not None:
            try:
                self._limite.reschedule(asyncio.get_running_loop().time())
            except RuntimeError:
                pass  # o prazo ja estava vencendo; a dona ve o recado ao sair dele

    # ----------------------------------------------------------------------
    # A tarefa
    # ----------------------------------------------------------------------

    async def _dona(self) -> None:
        try:
            await self._viver()
        except asyncio.CancelledError as erro:
            tarefa = asyncio.current_task()
            if tarefa is not None and tarefa.cancelling():
                raise  # um cancelamento de verdade (o laco fechando): passa, depois do fechamento
            # Um CancelledError solto de dentro do SDK, sem ninguem ter
            # cancelado a dona, e defeito - e queda, nao fim silencioso.
            self._cair(_FASE_DA_ETAPA.get(self.etapa, Fase.RESPOSTA), erro)
        except Exception as erro:
            # Um defeito aqui dentro tambem e queda: quem le o turno nunca
            # fica esperando uma fila que ninguem mais vai escrever.
            self._cair(_FASE_DA_ETAPA.get(self.etapa, Fase.RESPOSTA), erro)
        finally:
            await self._fechar()

    async def _viver(self) -> None:
        try:
            await self._esperar(Etapa.SUBIDA, self._prazo_de_subida, self._cliente.connect())
        except _Recadada:
            return
        except _Vencida:
            self._cair(Fase.SUBIDA, PrazoVencido())
            return
        except Exception as erro:
            self._cair(Fase.SUBIDA, erro)
            return

        primeira = True
        while True:
            try:
                texto = await self._esperar(Etapa.OCIOSA, None, self._entrada.get())
            except _Recadada:
                if self._recado is Recado.DESCARTAR:
                    return
                # O leitor saiu depois de a resposta acabar, sem le-la ate o
                # fim: nada a interromper.
                self._recado = None
                self._ao_sossegar()
                continue

            fila = self._fila
            try:
                await self._esperar(Etapa.ENTREGA, None, self._cliente.query(texto))
            except _Recadada:
                return  # N3: o leitor nao viu a entrega, entao descarta
            except Exception as erro:
                self._cair(Fase.ENTREGA, erro)
                return
            fila.put_nowait(Entregue(primeira))
            primeira = False

            try:
                completa = await self._esperar(Etapa.RESPOSTA, None, self._ler(fila))
            except _Recadada:
                if self._recado is Recado.DESCARTAR:
                    return
                self._recado = None
                try:
                    await self._esperar(Etapa.CAUDA, self._prazo_de_interrupcao, self._cauda())
                except Exception:
                    # Recado de descartar, prazo vencido, aviso que falhou ou
                    # fluxo que acabou: o processo e descartado.
                    return
                self._ao_sossegar()
                continue
            except Exception as erro:
                self._cair(Fase.RESPOSTA, erro)
                return
            if not completa:
                self._cair(Fase.RESPOSTA, FimSemResultado())
                return

    async def _esperar[T](self, etapa: Etapa, prazo: float | None, aguardavel: Coroutine[Any, Any, T]) -> T:
        """Uma espera dentro de um prazo que o recado vence (DP-S-03).
        Levanta `_Recadada` se foi o recado, `_Vencida` se foi o prazo; o
        resto passa como veio."""
        self.etapa = etapa
        if self._recado is not None:
            aguardavel.close()  # recado entre duas fases
            raise _Recadada
        limite = asyncio.timeout(prazo)
        try:
            async with limite:
                self._limite = limite
                try:
                    return await aguardavel
                finally:
                    self._limite = None
        except Exception as erro:
            if limite.expired():
                raise (_Recadada() if self._recado is not None else _Vencida()) from erro
            raise

    async def _ler(self, fila: asyncio.Queue[ItemDoTurno]) -> bool:
        """A resposta: cada mensagem do SDK vai para a fila do turno, ate a
        mensagem de resultado. False se o fluxo acabou sem ela."""
        async for mensagem in self._cliente.receive_response():
            if isinstance(mensagem, ResultMessage):
                fila.put_nowait(FimDaResposta(mensagem))
                return True
            fila.put_nowait(DoProvedor(mensagem))
        return False

    async def _cauda(self) -> None:
        """Avisa o provedor e le o resto da resposta interrompida, jogando
        fora (DP-S-04): nada dela chega a fila de ninguem."""
        await self._cliente.interrupt()
        async for mensagem in self._cliente.receive_response():
            if isinstance(mensagem, ResultMessage):
                return
        raise _CaudaSemFim

    def _cair(self, fase: Fase, causa: Causa) -> None:
        if self._fila is not None:
            self._fila.put_nowait(Caiu(fase, causa))

    async def _fechar(self) -> None:
        """A dona sempre termina aqui. O `disconnect` do SDK tem prazo proprio
        (~15 s, A12); nenhum nosso."""
        self.etapa = Etapa.FECHAMENTO
        try:
            await self._cliente.disconnect()
        except Exception as erro:
            _log.warning("o cliente do SDK falhou ao desconectar (%s)", type(erro).__name__, exc_info=erro)
        finally:
            if self._fila is not None:
                self._fila.put_nowait(Encerrada())
            self._ao_terminar()


class _CaudaSemFim(Exception):
    """Interna: a resposta interrompida acabou sem mensagem de resultado."""


_FASE_DA_ETAPA = {
    Etapa.SUBIDA: Fase.SUBIDA,
    Etapa.ENTREGA: Fase.ENTREGA,
    Etapa.RESPOSTA: Fase.RESPOSTA,
}
