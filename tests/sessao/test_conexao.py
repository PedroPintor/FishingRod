"""U6 - a conexao e a tarefa dona (DP-S-01..05, DP-S-07, DP-S-08, N3, RN-S-33..38).

Cada fase da dona com prazos curtos (nenhum teste espera os 60 s ou os 5 s), o
recado em cada fase, conforme a tabela do §3 de logical-components.md, e as
duas garantias que sustentam o resto: a dona NUNCA termina cancelada, e
SEMPRE passa pelo fechamento.
"""

import asyncio
import logging

import pytest
from claude_agent_sdk import ClaudeAgentOptions, CLIConnectionError, ResultMessage

from fishingrod.adaptadores.sessao.conexao import (
    Caiu,
    Conexao,
    DoProvedor,
    Encerrada,
    Entregue,
    Etapa,
    FimDaResposta,
)
from fishingrod.adaptadores.sessao.falhas import Fase, FimSemResultado, PrazoVencido
from tests.sessao.cliente_roteirizado import (
    Acabar,
    Bem,
    FabricaRoteirizada,
    Falha,
    Levantar,
    Mensagem,
    Parar,
    RoteiroDoTurno,
    Trava,
    assistente,
    resultado,
    turno_de_texto,
)
from tests.sessao.estrategias import esperar_que, executar

PRAZO = 0.2


class Avisos:
    def __init__(self) -> None:
        self.sossegou = 0
        self.terminou = 0


def _conexao(fabrica: FabricaRoteirizada, prazo_de_subida: float = PRAZO, prazo_de_interrupcao: float = PRAZO):
    cliente = fabrica(ClaudeAgentOptions())
    avisos = Avisos()

    def sossegou():
        avisos.sossegou += 1

    def terminou():
        avisos.terminou += 1

    conexao = Conexao(
        cliente,
        prazo_de_subida=prazo_de_subida,
        prazo_de_interrupcao=prazo_de_interrupcao,
        ao_sossegar=sossegou,
        ao_terminar=terminou,
    )
    return conexao, cliente, avisos


async def _ate(fila: asyncio.Queue, tipo: type, limite: float = 2.0):
    """Le a fila ate um item do tipo; devolve todos os lidos."""
    lidos = []
    while True:
        item = await asyncio.wait_for(fila.get(), limite)
        lidos.append(item)
        if isinstance(item, tipo):
            return lidos


async def _fim(conexao: Conexao) -> None:
    await asyncio.wait({conexao.tarefa}, timeout=2.0)
    assert conexao.tarefa.done(), "a dona nao terminou"
    assert not conexao.tarefa.cancelled(), "a dona terminou cancelada"


# --------------------------------------------------------------------------
# O caminho bom
# --------------------------------------------------------------------------


def test_um_turno_e_outro_na_mesma_conexao():
    fabrica = FabricaRoteirizada(turnos=[turno_de_texto("um"), turno_de_texto("dois")])

    async def cenario():
        conexao, cliente, avisos = _conexao(fabrica)
        primeira, segunda = asyncio.Queue(), asyncio.Queue()
        conexao.entregar("oi", primeira)
        um = await _ate(primeira, FimDaResposta)
        conexao.entregar("de novo", segunda)
        dois = await _ate(segunda, FimDaResposta)
        assert conexao.etapa in (Etapa.OCIOSA, Etapa.RESPOSTA)
        vivo = cliente.vivo
        conexao.descartar()
        await _fim(conexao)
        return um, dois, vivo, cliente.consultas, avisos.terminou

    um, dois, vivo, consultas, terminou = executar(cenario())

    assert um[0] == Entregue(primeira=True) and dois[0] == Entregue(primeira=False)
    assert [type(i) for i in um] == [Entregue, DoProvedor, FimDaResposta]
    assert vivo is True
    assert consultas == ["oi", "de novo"]
    assert terminou == 1


# --------------------------------------------------------------------------
# Subida (prazo 60 s; aqui, curto)
# --------------------------------------------------------------------------


def test_nfr_s_11_subida_que_nao_termina_no_prazo_cai_e_fecha():
    fabrica = FabricaRoteirizada(subidas=[Trava()])

    async def cenario():
        conexao, cliente, avisos = _conexao(fabrica)
        fila = asyncio.Queue()
        conexao.entregar("oi", fila)
        lidos = await _ate(fila, Encerrada)
        await _fim(conexao)
        return lidos, cliente.vivo, avisos.terminou

    lidos, vivo, terminou = executar(cenario())

    assert lidos == [Caiu(Fase.SUBIDA, PrazoVencido()), Encerrada()]
    assert vivo is False and terminou == 1
    assert fabrica.vivos == 0


def test_subida_que_falha_cai_com_a_causa():
    erro = CLIConnectionError("nao subiu")
    fabrica = FabricaRoteirizada(subidas=[Falha(erro)])

    async def cenario():
        conexao, _, _ = _conexao(fabrica)
        fila = asyncio.Queue()
        conexao.entregar("oi", fila)
        lidos = await _ate(fila, Encerrada)
        await _fim(conexao)
        return lidos

    assert executar(cenario()) == [Caiu(Fase.SUBIDA, erro), Encerrada()]
    assert fabrica.vivos == 0


@pytest.mark.parametrize("recado", ["descartar", "interromper"])
def test_n3_recado_na_subida_fecha_sem_cair(recado):
    """Na subida nada foi entregue: qualquer recado e descarte (N3)."""
    fabrica = FabricaRoteirizada(subidas=[Trava()])

    async def cenario():
        conexao, cliente, avisos = _conexao(fabrica, prazo_de_subida=60)
        fila = asyncio.Queue()
        conexao.entregar("oi", fila)
        await esperar_que(lambda: cliente.vivo)
        getattr(conexao, recado)()
        lidos = await _ate(fila, Encerrada)
        await _fim(conexao)
        return lidos, avisos

    lidos, avisos = executar(cenario())

    assert lidos == [Encerrada()]
    assert (avisos.sossegou, avisos.terminou) == (0, 1)
    assert fabrica.vivos == 0


def test_dp_s_03_recado_entre_fases_e_conferido_antes_da_proxima():
    """O recado chega antes de a dona dar o primeiro passo: ela nem chega a
    subir o processo."""
    fabrica = FabricaRoteirizada()

    async def cenario():
        conexao, _, avisos = _conexao(fabrica)
        conexao.descartar()
        await _fim(conexao)
        return avisos.terminou

    assert executar(cenario()) == 1
    assert fabrica.nascidos == 0


# --------------------------------------------------------------------------
# Ociosa
# --------------------------------------------------------------------------


def test_ociosa_interromper_e_so_sossegar():
    """O leitor saiu depois de a resposta acabar: nada a interromper."""
    fabrica = FabricaRoteirizada(turnos=[turno_de_texto("um"), turno_de_texto("dois")])

    async def cenario():
        conexao, cliente, avisos = _conexao(fabrica)
        fila = asyncio.Queue()
        conexao.entregar("oi", fila)
        await _ate(fila, FimDaResposta)
        await esperar_que(lambda: conexao.etapa is Etapa.OCIOSA)
        conexao.interromper()
        await esperar_que(lambda: avisos.sossegou == 1)
        outra = asyncio.Queue()
        conexao.entregar("de novo", outra)
        lidos = await _ate(outra, FimDaResposta)
        conexao.descartar()
        await _fim(conexao)
        return lidos, cliente.interrupcoes

    lidos, interrupcoes = executar(cenario())

    assert lidos[0] == Entregue(primeira=False)
    assert interrupcoes == 0


def test_ociosa_descartar_fecha():
    fabrica = FabricaRoteirizada(turnos=[turno_de_texto("um")])

    async def cenario():
        conexao, cliente, avisos = _conexao(fabrica)
        fila = asyncio.Queue()
        conexao.entregar("oi", fila)
        await _ate(fila, FimDaResposta)
        conexao.descartar()
        await _fim(conexao)
        return cliente.vivo, avisos.terminou

    assert executar(cenario()) == (False, 1)


# --------------------------------------------------------------------------
# Entrega
# --------------------------------------------------------------------------


def test_entrega_que_falha_cai():
    erro = CLIConnectionError("processo morreu")
    fabrica = FabricaRoteirizada(turnos=[RoteiroDoTurno(entrega=Falha(erro))])

    async def cenario():
        conexao, _, _ = _conexao(fabrica)
        fila = asyncio.Queue()
        conexao.entregar("oi", fila)
        lidos = await _ate(fila, Encerrada)
        await _fim(conexao)
        return lidos

    assert executar(cenario()) == [Caiu(Fase.ENTREGA, erro), Encerrada()]


def test_n3_recado_na_entrega_descarta():
    fabrica = FabricaRoteirizada(turnos=[RoteiroDoTurno(entrega=Trava())])

    async def cenario():
        conexao, _, _ = _conexao(fabrica)
        fila = asyncio.Queue()
        conexao.entregar("oi", fila)
        await esperar_que(lambda: conexao.etapa is Etapa.ENTREGA)
        conexao.interromper()
        lidos = await _ate(fila, Encerrada)
        await _fim(conexao)
        return lidos

    assert executar(cenario()) == [Encerrada()]
    assert fabrica.vivos == 0


# --------------------------------------------------------------------------
# Resposta (sem prazo, NFR-S-12) e cauda (prazo 5 s; aqui, curto)
# --------------------------------------------------------------------------


def _turno_parado(liberar=None, chegou=None) -> RoteiroDoTurno:
    return RoteiroDoTurno([Mensagem(assistente()), Parar(liberar, chegou), Mensagem(assistente()), resultado()])


def test_dp_s_04_interromper_na_resposta_vai_a_cauda_e_o_resto_e_jogado_fora():
    chegou = asyncio.Event()
    fabrica = FabricaRoteirizada(turnos=[_turno_parado(chegou=chegou), turno_de_texto("depois")])
    fabrica.turnos[0].cauda = [Mensagem(assistente()), Mensagem(assistente()), resultado(erro=True)]

    async def cenario():
        conexao, cliente, avisos = _conexao(fabrica)
        fila = asyncio.Queue()
        conexao.entregar("oi", fila)
        await chegou.wait()
        conexao.interromper()
        await esperar_que(lambda: avisos.sossegou == 1)
        sobras = []
        while not fila.empty():
            sobras.append(fila.get_nowait())
        proxima = asyncio.Queue()
        conexao.entregar("de novo", proxima)
        lidos = await _ate(proxima, FimDaResposta)
        conexao.descartar()
        await _fim(conexao)
        return sobras, lidos, cliente.interrupcoes

    sobras, lidos, interrupcoes = executar(cenario())

    assert [type(i) for i in sobras] == [Entregue, DoProvedor]  # nada da cauda
    assert lidos[0] == Entregue(primeira=False)
    assert interrupcoes == 1


@pytest.mark.parametrize(
    "interrupcao, cauda",
    [
        (Falha(CLIConnectionError("aviso falhou")), None),
        (Trava(), None),
        (Bem(), [Acabar()]),
        (Bem(), [Parar()]),
    ],
    ids=["aviso-falha", "aviso-trava", "cauda-sem-resultado", "cauda-que-nao-acaba"],
)
def test_rn_s_35_cauda_que_nao_termina_bem_descarta_o_processo(interrupcao, cauda):
    chegou = asyncio.Event()
    fabrica = FabricaRoteirizada(turnos=[_turno_parado(chegou=chegou)], interrupcao=interrupcao)
    if cauda is not None:
        fabrica.turnos[0].cauda = cauda

    async def cenario():
        conexao, cliente, avisos = _conexao(fabrica)
        fila = asyncio.Queue()
        conexao.entregar("oi", fila)
        await chegou.wait()
        conexao.interromper()
        await _fim(conexao)
        return avisos.sossegou, avisos.terminou, cliente.vivo

    assert executar(cenario()) == (0, 1, False)


def test_descartar_na_cauda_fecha():
    chegou = asyncio.Event()
    fabrica = FabricaRoteirizada(turnos=[_turno_parado(chegou=chegou)], interrupcao=Trava())

    async def cenario():
        conexao, _, avisos = _conexao(fabrica, prazo_de_interrupcao=60)
        fila = asyncio.Queue()
        conexao.entregar("oi", fila)
        await chegou.wait()
        conexao.interromper()
        await esperar_que(lambda: conexao.etapa is Etapa.CAUDA)
        conexao.descartar()
        await _fim(conexao)
        return avisos.sossegou

    assert executar(cenario()) == 0


def test_descartar_na_resposta_fecha():
    chegou = asyncio.Event()
    fabrica = FabricaRoteirizada(turnos=[_turno_parado(chegou=chegou)])

    async def cenario():
        conexao, cliente, _ = _conexao(fabrica)
        fila = asyncio.Queue()
        conexao.entregar("oi", fila)
        await chegou.wait()
        conexao.descartar()
        await _fim(conexao)
        return cliente.interrupcoes

    assert executar(cenario()) == 0


def test_nfr_s_12_resposta_parada_nao_termina_sozinha():
    """Nenhum prazo de silencio: depois de varios prazos de subida, a dona
    continua esperando."""
    chegou = asyncio.Event()
    fabrica = FabricaRoteirizada(turnos=[_turno_parado(chegou=chegou)])

    async def cenario():
        conexao, _, _ = _conexao(fabrica)
        fila = asyncio.Queue()
        conexao.entregar("oi", fila)
        await chegou.wait()
        await asyncio.sleep(PRAZO * 4)
        parada = (conexao.etapa, conexao.tarefa.done())
        conexao.descartar()
        await _fim(conexao)
        return parada

    assert executar(cenario()) == (Etapa.RESPOSTA, False)


@pytest.mark.parametrize(
    "passo, causa",
    [
        (Acabar(), FimSemResultado()),
        (Levantar(CLIConnectionError("caiu")), None),
        (Levantar(RuntimeError("defeito")), None),
        (Levantar(asyncio.CancelledError()), None),
    ],
    ids=["fim-do-fluxo", "conexao-caiu", "defeito", "cancelamento-solto"],
)
def test_queda_na_resposta_vai_para_a_fila_do_turno(passo, causa):
    fabrica = FabricaRoteirizada(turnos=[RoteiroDoTurno([Mensagem(assistente()), passo])])

    async def cenario():
        conexao, _, avisos = _conexao(fabrica)
        fila = asyncio.Queue()
        conexao.entregar("oi", fila)
        lidos = await _ate(fila, Encerrada)
        await _fim(conexao)
        return lidos, avisos.terminou

    lidos, terminou = executar(cenario())

    caiu = lidos[-2]
    assert isinstance(caiu, Caiu) and caiu.fase is Fase.RESPOSTA
    if causa is not None:
        assert caiu.causa == causa
    else:
        assert caiu.causa is passo.excecao
    assert terminou == 1
    assert fabrica.vivos == 0


# --------------------------------------------------------------------------
# Fechamento e as garantias
# --------------------------------------------------------------------------


def test_desconectar_que_falha_ainda_termina_e_avisa(caplog):
    fabrica = FabricaRoteirizada(desconexao=Falha(RuntimeError("nao desconectou")))

    async def cenario():
        conexao, _, avisos = _conexao(fabrica)
        conexao.descartar()
        await _fim(conexao)
        return avisos.terminou

    with caplog.at_level(logging.WARNING, logger="fishingrod.sessao"):
        assert executar(cenario()) == 1
    assert "RuntimeError" in caplog.text


def test_dp_s_07_cancelar_quem_espera_nao_cancela_a_dona():
    fabrica = FabricaRoteirizada(turnos=[turno_de_texto("um")])

    async def cenario():
        conexao, _, _ = _conexao(fabrica)
        fila = asyncio.Queue()
        conexao.entregar("oi", fila)
        await _ate(fila, FimDaResposta)
        quem_espera = asyncio.create_task(asyncio.wait({conexao.tarefa}))
        await asyncio.sleep(0)
        quem_espera.cancel()
        await asyncio.sleep(0.01)
        viva = not conexao.tarefa.done()
        conexao.descartar()
        await _fim(conexao)
        return viva

    assert executar(cenario()) is True


def test_recado_depois_de_a_dona_terminar_nao_faz_nada():
    fabrica = FabricaRoteirizada()

    async def cenario():
        conexao, _, avisos = _conexao(fabrica)
        conexao.descartar()
        await _fim(conexao)
        conexao.interromper()
        conexao.descartar()
        await asyncio.sleep(0.01)
        return avisos.terminou, avisos.sossegou

    assert executar(cenario()) == (1, 0)


def test_o_resultado_e_o_fim_da_resposta():
    fabrica = FabricaRoteirizada(turnos=[turno_de_texto("um")])

    async def cenario():
        conexao, _, _ = _conexao(fabrica)
        fila = asyncio.Queue()
        conexao.entregar("oi", fila)
        lidos = await _ate(fila, FimDaResposta)
        conexao.descartar()
        await _fim(conexao)
        return lidos[-1]

    assert isinstance(executar(cenario()).mensagem, ResultMessage)
