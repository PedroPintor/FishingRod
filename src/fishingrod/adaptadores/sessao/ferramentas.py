"""De Ferramenta neutra para servidor MCP in-process do SDK (RN-S-12, RN-S-42..44).

Um servidor por familia presente na sessao, com a familia como chave: o agente
ve `mcp__ambiente__criar_etapa` e `mcp__wiki__ler`. Sessao sem ferramenta nao
tem servidor.

DP-S-18: quando o SDK chama uma ferramenta, a funcao roda numa tarefa NOSSA,
registrada nas Execucoes da sessao. Interromper e fechar cancelam a nossa
tarefa, nunca a do SDK, e a ferramenta cancelada responde `interrompida` (N4):
o cancelamento fica do nosso lado, e a tarefa do SDK termina normalmente.
"""

import asyncio
import logging
from collections.abc import Mapping, Sequence
from typing import Any

from claude_agent_sdk import McpSdkServerConfig, SdkMcpTool, create_sdk_mcp_server

from fishingrod.aplicacao.ferramentas import PADRAO_DE_NOME, Ferramenta, RespostaDaFerramenta
from fishingrod.aplicacao.portas.sessao import Familia, somente_leitura

_log = logging.getLogger("fishingrod.sessao")
_log.addHandler(logging.NullHandler())

# O que o agente le quando a ferramenta nao respondeu por conta propria.
# Generico de proposito (RN-S-43): nada do erro chega ao provedor.
INTERROMPIDA = RespostaDaFerramenta('{"ok":false,"motivo":"interrompida"}', erro=True)
FALHA_INESPERADA = RespostaDaFerramenta('{"ok":false,"motivo":"falha_inesperada"}', erro=True)


# --------------------------------------------------------------------------
# O nome que o agente ve (RN-S-12, PBT-U6-04)
# --------------------------------------------------------------------------

_FAMILIAS = {familia.value: familia for familia in Familia}


def nome_qualificado(familia: Familia, nome: str) -> str:
    return f"mcp__{familia.value}__{nome}"


def separar(nome_qualificado: object) -> tuple[Familia, str] | None:
    """A inversa de `nome_qualificado`. Texto fora do formato - familia que
    nao existe, `__` sobrando, nome fora do padrao - devolve None: e um pedido
    "de fora da sessao"."""
    if not isinstance(nome_qualificado, str):
        return None
    partes = nome_qualificado.split("__")
    if len(partes) != 3 or partes[0] != "mcp":
        return None
    familia = _FAMILIAS.get(partes[1])
    if familia is None or not PADRAO_DE_NOME.fullmatch(partes[2]):
        return None
    return familia, partes[2]


def nomes_qualificados(ferramentas: Mapping[Familia, Sequence[Ferramenta]]) -> frozenset[str]:
    """Os nomes que a permissao exata deixa passar (DP-S-14)."""
    return frozenset(
        nome_qualificado(familia, ferramenta.nome)
        for familia, da_familia in ferramentas.items()
        for ferramenta in da_familia
    )


# --------------------------------------------------------------------------
# As execucoes em andamento (RN-S-44, DP-S-18, N4)
# --------------------------------------------------------------------------


class Execucoes:
    """As tarefas de ferramenta em andamento de uma sessao.

    `bloquear` e o que interromper e fechar chamam, sem `await` (DP-S-02):
    cancela todas e recusa as que chegarem depois - um pedido de ferramenta
    pode chegar do CLI depois do ESC, antes de ele processar a interrupcao, e
    nada pode executar depois do ESC (RN-S-35, PBT-U6-11). `liberar` reabre no
    comeco do proximo turno.
    """

    def __init__(self) -> None:
        self._tarefas: set[asyncio.Task[RespostaDaFerramenta]] = set()
        self._bloqueada = False

    def __len__(self) -> int:
        return len(self._tarefas)

    def bloquear(self) -> None:
        self._bloqueada = True
        for tarefa in tuple(self._tarefas):
            tarefa.cancel()

    def liberar(self) -> None:
        self._bloqueada = False

    async def executar(self, ferramenta: Ferramenta, argumentos: Mapping[str, Any]) -> RespostaDaFerramenta:
        if self._bloqueada:
            return INTERROMPIDA
        tarefa = asyncio.create_task(_rodar(ferramenta, somente_leitura(argumentos)))
        self._tarefas.add(tarefa)
        tarefa.add_done_callback(self._tarefas.discard)
        try:
            await asyncio.wait({tarefa})
        except asyncio.CancelledError:
            # A14: o SDK cancelou a chamada (disconnect, por exemplo). A nossa
            # tarefa vai junto, e o cancelamento continua subindo.
            tarefa.cancel()
            raise
        if tarefa.cancelled():
            return INTERROMPIDA
        erro = tarefa.exception()
        if erro is not None:
            # RN-S-43: com a pilha, SEM os argumentos.
            _log.error("ferramenta [%s] falhou (%s)", ferramenta.nome, type(erro).__name__, exc_info=erro)
            return FALHA_INESPERADA
        resposta = tarefa.result()
        if not isinstance(resposta, RespostaDaFerramenta):
            _log.error("ferramenta [%s] devolveu %s, e nao uma resposta", ferramenta.nome, type(resposta).__name__)
            return FALHA_INESPERADA
        return resposta


async def _rodar(ferramenta: Ferramenta, argumentos: Mapping[str, object]) -> RespostaDaFerramenta:
    """Dentro da tarefa: ate um erro sincrono de `executar` vira erro da
    tarefa, e nao escapa para o SDK com a mensagem dentro."""
    return await ferramenta.executar(argumentos)


# --------------------------------------------------------------------------
# Os servidores (RN-S-12)
# --------------------------------------------------------------------------


def servidores(
    ferramentas: Mapping[Familia, Sequence[Ferramenta]], execucoes: Execucoes
) -> dict[str, McpSdkServerConfig]:
    return {
        familia.value: create_sdk_mcp_server(
            familia.value, tools=[_para_o_sdk(ferramenta, execucoes) for ferramenta in da_familia]
        )
        for familia, da_familia in ferramentas.items()
        if da_familia
    }


def _para_o_sdk(ferramenta: Ferramenta, execucoes: Execucoes) -> SdkMcpTool[Any]:
    async def chamar(argumentos: dict[str, Any]) -> dict[str, Any]:
        resposta = await execucoes.executar(ferramenta, argumentos)
        return {"content": [{"type": "text", "text": resposta.texto}], "is_error": resposta.erro}

    return SdkMcpTool(
        name=ferramenta.nome,
        description=ferramenta.descricao,
        input_schema=dict_puro(ferramenta.esquema),
        handler=chamar,
    )


def dict_puro(valor: object) -> Any:
    """R-CG6-2: o esquema vai ao SDK como `dict` e `list` de verdade. Qualquer
    outro Mapping - o MappingProxyType da Ferramenta, por exemplo - o SDK troca,
    sem avisar, por um esquema vazio (A17)."""
    if isinstance(valor, Mapping):
        return {chave: dict_puro(item) for chave, item in valor.items()}
    if isinstance(valor, (list, tuple)):
        return [dict_puro(item) for item in valor]
    return valor
