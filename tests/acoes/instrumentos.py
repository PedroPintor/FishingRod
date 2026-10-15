"""Instrumentos para ver e perturbar o que o catalogo faz (plano de CG, 4).

Como em U4, nao sao segunda implementacao de nada: os do servico embrulham o
ServicoDeAmbiente REAL e delegam tudo; os da porta de confirmacao sao as
respostas que a tela de U9 poderia dar - inclusive as erradas.
"""

import asyncio
from collections.abc import Callable
from typing import Any

from fishingrod.aplicacao.catalogo.tipos import PedidoDeConfirmacao

# A unica operacao de leitura que o catalogo usa. Todas as outras mudam o
# ambiente.
OPERACAO_DE_LEITURA = "carregar_ambiente"


class ServicoEspiao:
    """Anota cada chamada - operacao e argumentos - antes de delegar ao
    servico de verdade."""

    def __init__(self, interno: Any) -> None:
        self.interno = interno
        self.chamadas: list[tuple[str, tuple]] = []

    def __getattr__(self, nome: str) -> Any:
        funcao = getattr(self.interno, nome)

        async def chamar(*argumentos: Any) -> Any:
            self.chamadas.append((nome, argumentos))
            await self._antes(nome)
            return await funcao(*argumentos)

        return chamar

    async def _antes(self, nome: str) -> None:
        """Ponto de perturbacao, para ServicoSabotado."""

    def mudancas(self) -> list[tuple[str, tuple]]:
        """As chamadas que mudam o ambiente, sem as leituras."""
        return [chamada for chamada in self.chamadas if chamada[0] != OPERACAO_DE_LEITURA]


class ServicoSabotado(ServicoEspiao):
    """Igual ao espiao, mas levanta UMA vez o erro escolhido: na primeira
    leitura (o passo 5 do catalogo) ou na primeira operacao de mudanca (o
    passo 7). Depois disso, delega normalmente."""

    def __init__(self, interno: Any, erro: Callable[[], BaseException], onde: str) -> None:
        super().__init__(interno)
        self.erro = erro
        self.onde = onde
        self.disparou = False

    async def _antes(self, nome: str) -> None:
        e_leitura = nome == OPERACAO_DE_LEITURA
        if not self.disparou and e_leitura == (self.onde == "leitura"):
            self.disparou = True
            raise self.erro()


class ConfirmacaoFixa:
    """Responde sempre a mesma coisa - qualquer coisa, nao so bool - e guarda
    os pedidos que recebeu."""

    def __init__(self, resposta: Any) -> None:
        self.resposta = resposta
        self.pedidos: list[PedidoDeConfirmacao] = []

    async def confirmar(self, pedido: PedidoDeConfirmacao) -> Any:
        self.pedidos.append(pedido)
        return self.resposta


class ConfirmacaoQueLevanta:
    """A tela que quebra ao perguntar."""

    def __init__(self, erro: Callable[[], BaseException]) -> None:
        self.erro = erro
        self.pedidos: list[PedidoDeConfirmacao] = []

    async def confirmar(self, pedido: PedidoDeConfirmacao) -> bool:
        self.pedidos.append(pedido)
        raise self.erro()


class ConfirmacaoQueEspera:
    """Fica parada ate o teste liberar: e a pessoa pensando. `chegou` avisa o
    teste de que o pedido esta na tela."""

    def __init__(self, resposta: Any = True) -> None:
        self.resposta = resposta
        self.pedidos: list[PedidoDeConfirmacao] = []
        self.chegou = asyncio.Event()
        self.liberada = asyncio.Event()

    async def confirmar(self, pedido: PedidoDeConfirmacao) -> Any:
        self.pedidos.append(pedido)
        self.chegou.set()
        await self.liberada.wait()
        return self.resposta


class PerguntaProibida(BaseException):
    """BaseException de proposito: o catalogo captura Exception, e uma
    AssertionError comum viraria FALHA_INESPERADA em silencio. Esta atravessa
    o catalogo e derruba o teste."""


class ConfirmacaoProibida:
    """Para provar que o caminho do usuario, e toda validacao, nunca
    perguntam (RN-AC-21, RN-AC-29)."""

    def __init__(self) -> None:
        self.perguntou = False

    async def confirmar(self, pedido: PedidoDeConfirmacao) -> bool:
        self.perguntou = True
        raise PerguntaProibida(f"a porta foi chamada para [{pedido.acao}]")
