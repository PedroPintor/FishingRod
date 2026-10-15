"""Porta de confirmacao: a pergunta "sim ou nao?" feita a pessoa (U5, G6).

Mora em aplicacao/portas/ como as outras portas: a aplicacao define o contrato,
uma camada de fora o implementa. A dona e U5; quem implementa e a tela (U9).
U8 reaproveita a mesma porta para a proposta do bibliotecario (criterio 6 de
U8).

O pedido vem de catalogo/tipos.py, e nao daqui, porque e vocabulario do
catalogo. Por isso catalogo/__init__.py fica vazio: se reexportasse o
catalogo, importar esta porta primeiro entraria em ciclo.
"""

from typing import Protocol

from fishingrod.aplicacao.catalogo.tipos import PedidoDeConfirmacao


class PortaDeConfirmacao(Protocol):
    """Uma operacao, que espera a pessoa responder."""

    async def confirmar(self, pedido: PedidoDeConfirmacao) -> bool:
        """Mostra o pedido e ESPERA a resposta (Q4=A): a chamada do agente fica
        parada ate a pessoa decidir.

        Contrato com o catalogo:
        - so `True` confirma (RN-AC-27, RN-AC-30). Qualquer outro valor - False,
          None, 1, "sim" - e recusa: na duvida, nada executa;
        - responde sim ou nao, e nada mais. O pedido e somente leitura e nao
          existe "editar e aprovar" (RN-AC-31): o que executa e exatamente o que
          foi mostrado;
        - se levantar, o catalogo trata como falha inesperada e nada executa;
          se a espera for cancelada (o turno do agente foi interrompido), o
          cancelamento passa e tambem nada executa (RN-AC-30). Tirar da tela o
          pedido cancelado e de quem implementa (U9).

        Nenhuma trava de ambiente esta presa enquanto esta chamada espera
        (RN-AC-32): a pessoa pode continuar agindo no mesmo ambiente.
        """
        ...
