"""U6 - de Ferramenta neutra para o SDK (RN-S-12, RN-S-42..44, DP-S-18, R-CG6-2, PBT-U6-04).

O teste de fumaca (passo 14 do plano) abre o arquivo: uma chamada do CLI chega
a Ferramenta pelo caminho de verdade do SDK, e um argumento fora do esquema
NAO chega (A16).
"""

import asyncio
import json
import logging
from types import MappingProxyType

import pytest
from claude_agent_sdk._internal.sdk_mcp_bridge import SdkMcpBridge
from hypothesis import given, settings
from hypothesis import strategies as st

from fishingrod.adaptadores.sessao.ferramentas import (
    FALHA_INESPERADA,
    INTERROMPIDA,
    Execucoes,
    dict_puro,
    nome_qualificado,
    nomes_qualificados,
    separar,
    servidores,
)
from fishingrod.aplicacao.ferramentas import EntradaDoRegistro, Ferramenta, RegistroDeFerramentas, RespostaDaFerramenta
from fishingrod.aplicacao.portas.sessao import Familia, FimDeTurno, UsoDeFerramenta
from tests.sessao.cliente_roteirizado import (
    ChamarFerramenta,
    FabricaRoteirizada,
    Mensagem,
    RoteiroDoTurno,
    assistente,
    pedido,
    resultado,
)
from tests.sessao.estrategias import adaptador, agente, coletar, contexto_novo, executar

ESQUEMA = {
    "type": "object",
    "properties": {"chave": {"type": "string", "minLength": 1}, "lista": {"type": "array"}},
    "required": ["chave"],
    "additionalProperties": False,
}


class Gravadora:
    """Uma ferramenta que anota o que recebeu."""

    def __init__(self, resposta: RespostaDaFerramenta | None = None, erro: BaseException | None = None) -> None:
        self.recebidos: list = []
        self.resposta = resposta or RespostaDaFerramenta('{"ok":true}')
        self.erro = erro

    async def __call__(self, argumentos):
        self.recebidos.append(argumentos)
        if self.erro is not None:
            raise self.erro
        return self.resposta


def _registro(executar_, nome: str = "ler", esquema: dict = ESQUEMA) -> RegistroDeFerramentas:
    def fabricar(contexto, quem):
        return Ferramenta(nome, "le", esquema, executar_)

    return RegistroDeFerramentas([EntradaDoRegistro(nome, Familia.WIKI, fabricar)])


def _turno_que_chama(*chamadas: ChamarFerramenta) -> RoteiroDoTurno:
    return RoteiroDoTurno(
        [Mensagem(pedido(c.nome, c.argumentos)) for c in chamadas]
        + list(chamadas)
        + [Mensagem(assistente()), resultado()]
    )


def _rodar_turno(registro, *chamadas: ChamarFerramenta):
    fabrica = FabricaRoteirizada(turnos=[_turno_que_chama(*chamadas)])

    async def cenario():
        sessoes = adaptador(fabrica, registro)
        sessao = await sessoes.abrir(agente(ferramentas=tuple(e.nome for e in registro.entradas)), contexto_novo())
        eventos = await coletar(sessoes.enviar(sessao, "oi"))
        await sessoes.encerrar()
        return eventos

    eventos = executar(cenario())
    return eventos, fabrica.clientes[0].textos_dos_resultados()


# --------------------------------------------------------------------------
# Fumaca (passo 14): o caminho de verdade do SDK
# --------------------------------------------------------------------------


def test_fumaca_a_chamada_do_cli_chega_a_ferramenta():
    gravadora = Gravadora()

    eventos, resultados = _rodar_turno(_registro(gravadora), ChamarFerramenta("mcp__wiki__ler", {"chave": "k"}))

    assert gravadora.recebidos == [{"chave": "k"}]
    assert resultados == [("mcp__wiki__ler", '{"ok":true}', False)]
    assert eventos[-1] == FimDeTurno()


def test_fumaca_a16_argumento_fora_do_esquema_nao_chega_a_ferramenta():
    """R-CG6-1: o SDK confere o esquema ANTES da funcao. O agente le o erro do
    SDK, e a ferramenta nem e chamada."""
    gravadora = Gravadora()

    _, resultados = _rodar_turno(_registro(gravadora), ChamarFerramenta("mcp__wiki__ler", {"outra": "k"}))

    assert gravadora.recebidos == []
    [(nome, texto, erro)] = resultados
    assert erro is True and texto.startswith("Input validation error")


# --------------------------------------------------------------------------
# RN-S-42, RN-S-43
# --------------------------------------------------------------------------


def test_rn_s_42_a_ferramenta_recebe_os_argumentos_como_vieram_em_copia_somente_leitura():
    gravadora = Gravadora()

    _rodar_turno(_registro(gravadora), ChamarFerramenta("mcp__wiki__ler", {"chave": "k", "lista": [1, {"a": 2}]}))

    [recebido] = gravadora.recebidos
    assert recebido == {"chave": "k", "lista": [1, {"a": 2}]}
    with pytest.raises(TypeError):
        recebido["chave"] = "outra"


def test_rn_s_43_excecao_na_ferramenta_vira_erro_generico_e_log_sem_os_argumentos(caplog):
    gravadora = Gravadora(erro=KeyError("segredo-do-usuario"))

    with caplog.at_level(logging.DEBUG, logger="fishingrod.sessao"):
        eventos, resultados = _rodar_turno(
            _registro(gravadora), ChamarFerramenta("mcp__wiki__ler", {"chave": "valor-sigiloso"})
        )

    assert resultados == [("mcp__wiki__ler", '{"ok":false,"motivo":"falha_inesperada"}', True)]
    assert eventos[-1] == FimDeTurno()  # o turno e a sessao continuam
    erros = [r for r in caplog.records if r.levelno == logging.ERROR]
    assert len(erros) == 1 and "ler" in erros[0].getMessage() and "KeyError" in erros[0].getMessage()
    assert erros[0].exc_info is not None
    assert "valor-sigiloso" not in caplog.text


def test_rn_s_43_resposta_que_nao_e_resposta_vira_erro_generico(caplog):
    async def errada(argumentos):
        return {"ok": True}

    _, resultados = _rodar_turno(_registro(errada), ChamarFerramenta("mcp__wiki__ler", {"chave": "k"}))

    assert resultados == [("mcp__wiki__ler", FALHA_INESPERADA.texto, True)]


# --------------------------------------------------------------------------
# DP-S-18, N4: a nossa tarefa e a cancelada
# --------------------------------------------------------------------------


class Pendurada:
    """Uma ferramenta que espera para sempre - a espera da sua confirmacao."""

    def __init__(self) -> None:
        self.comecou = asyncio.Event()
        self.cancelada = False

    async def executar(self, argumentos):
        self.comecou.set()
        try:
            await asyncio.Event().wait()
        except asyncio.CancelledError:
            self.cancelada = True
            raise

    def ferramenta(self) -> Ferramenta:
        return Ferramenta("ler", "le", ESQUEMA, self.executar)


def test_dp_s_18_interromper_cancela_a_nossa_tarefa_e_a_do_sdk_termina_bem():
    async def cenario():
        execucoes, pendurada = Execucoes(), Pendurada()
        do_sdk = asyncio.create_task(execucoes.executar(pendurada.ferramenta(), {}))
        await pendurada.comecou.wait()
        assert len(execucoes) == 1
        execucoes.bloquear()
        resposta = await do_sdk
        await asyncio.sleep(0)
        return resposta, pendurada.cancelada, do_sdk.cancelled(), len(execucoes)

    resposta, cancelada, sdk_cancelada, em_andamento = executar(cenario())

    assert resposta == INTERROMPIDA
    assert json.loads(resposta.texto) == {"ok": False, "motivo": "interrompida"}
    assert cancelada is True
    assert sdk_cancelada is False
    assert em_andamento == 0


def test_dp_s_18_a14_se_o_sdk_cancela_a_chamada_a_nossa_vai_junto():
    async def cenario():
        execucoes, pendurada = Execucoes(), Pendurada()
        do_sdk = asyncio.create_task(execucoes.executar(pendurada.ferramenta(), {}))
        await pendurada.comecou.wait()
        do_sdk.cancel()
        with pytest.raises(asyncio.CancelledError):
            await do_sdk
        await asyncio.sleep(0)
        return pendurada.cancelada, len(execucoes)

    assert executar(cenario()) == (True, 0)


def test_rn_s_35_depois_de_bloquear_nada_mais_executa_ate_liberar():
    async def cenario():
        execucoes, gravadora = Execucoes(), Gravadora()
        ferramenta = Ferramenta("ler", "le", ESQUEMA, gravadora)
        execucoes.bloquear()
        bloqueada = await execucoes.executar(ferramenta, {"chave": "k"})
        execucoes.liberar()
        liberada = await execucoes.executar(ferramenta, {"chave": "k"})
        return bloqueada, liberada, gravadora.recebidos

    bloqueada, liberada, recebidos = executar(cenario())

    assert bloqueada == INTERROMPIDA
    assert liberada == RespostaDaFerramenta('{"ok":true}')
    assert len(recebidos) == 1


# --------------------------------------------------------------------------
# Os servidores (RN-S-12, R-CG6-2)
# --------------------------------------------------------------------------


def _ferramenta(nome: str, esquema=ESQUEMA) -> Ferramenta:
    return Ferramenta(nome, f"faz {nome}", esquema, Gravadora())


def test_rn_s_12_um_servidor_por_familia_presente():
    porfamilia = {Familia.AMBIENTE: (_ferramenta("criar_etapa"),), Familia.WIKI: (_ferramenta("ler"), _ferramenta("listar"))}

    montados = servidores(porfamilia, Execucoes())

    assert list(montados) == ["ambiente", "wiki"]
    assert servidores({Familia.WIKI: ()}, Execucoes()) == {}
    assert servidores({}, Execucoes()) == {}
    assert nomes_qualificados(porfamilia) == {"mcp__ambiente__criar_etapa", "mcp__wiki__ler", "mcp__wiki__listar"}


def test_r_cg6_2_o_esquema_chega_inteiro_ao_servidor():
    """A Ferramenta guarda o esquema em MappingProxyType; o SDK trocaria esse
    esquema por um vazio, sem avisar (A17). O servidor tem que listar o
    esquema inteiro."""
    ferramenta = _ferramenta("ler")
    assert isinstance(ferramenta.esquema, MappingProxyType)

    async def cenario():
        servidor = servidores({Familia.WIKI: (ferramenta,)}, Execucoes())["wiki"]
        ponte = SdkMcpBridge("wiki", servidor["instance"])
        await ponte.handle(
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-06-18", "capabilities": {}, "clientInfo": {"name": "t", "version": "0"}}}
        )
        lista = await ponte.handle({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
        await ponte.aclose()
        return lista["result"]["tools"]

    [listada] = executar(cenario())

    assert listada["name"] == "ler"
    assert listada["inputSchema"] == ESQUEMA


def test_r_cg6_2_dict_puro_converte_ate_o_fundo():
    convertido = dict_puro(MappingProxyType({"a": MappingProxyType({"b": (1, MappingProxyType({"c": 2}))})}))

    assert convertido == {"a": {"b": [1, {"c": 2}]}}
    assert type(convertido) is dict and type(convertido["a"]) is dict
    assert type(convertido["a"]["b"]) is list and type(convertido["a"]["b"][1]) is dict


# --------------------------------------------------------------------------
# PBT-U6-04: nome qualificado, ida e volta
# --------------------------------------------------------------------------

_NOMES = st.from_regex(r"[a-z][a-z0-9]{0,8}(_[a-z0-9]{1,5}){0,3}", fullmatch=True)


@settings(max_examples=200)
@given(st.sampled_from(list(Familia)), _NOMES)
def test_pbt_u6_04_nome_qualificado_ida_e_volta(familia, nome):
    assert separar(nome_qualificado(familia, nome)) == (familia, nome)


_QUASE = st.sampled_from(
    [
        "mcp_ambiente__x",
        "mcp__ambiente__x__y",
        "mcp__inexistente__ler",
        "MCP__ambiente__ler",
        "mcp__ambiente__",
        "mcp__ambiente__Ler",
        "mcp____ler",
        "mcp__wiki__ler_",
        "mcp__wiki__ler__",
        "ler",
        "",
    ]
)


@settings(max_examples=200)
@given(st.one_of(_QUASE, st.text(st.sampled_from("mcp_awikebntlr"), max_size=20), st.text(max_size=20)))
def test_pbt_u6_04_texto_fora_do_formato_nao_e_separado(texto):
    separado = separar(texto)

    if separado is not None:
        assert nome_qualificado(*separado) == texto
    if texto in ("mcp_ambiente__x", "mcp__ambiente__x__y", "mcp__inexistente__ler", "mcp__ambiente__Ler"):
        assert separado is None


def test_separar_o_que_nao_e_texto():
    assert separar(None) is None
    assert separar(42) is None


def test_uso_de_ferramenta_sai_do_bloco_completo_com_a_familia():
    """Fecha o ciclo com o tradutor: o pedido qualificado vira o par certo."""
    gravadora = Gravadora()
    eventos, _ = _rodar_turno(_registro(gravadora), ChamarFerramenta("mcp__wiki__ler", {"chave": "k"}))

    assert UsoDeFerramenta(Familia.WIKI, "ler", {"chave": "k"}) in eventos
