"""U6 - o adaptador inteiro, por exemplo (RN-S-05, RN-S-16, RN-S-26..41, N2, N3, N5, NFR-S-12, NFR-S-17, DP-S-08).

Um exemplo por motivo de falha (os 9), o ciclo de vida, o ESC antes, depois e
no instante da entrega, a cauda, `fechar` no meio, `encerrar` em paralelo, o
iterador abandonado, o log e a varredura de temporizadores. As propriedades
estao em test_propriedades.py.
"""

import asyncio
import logging
import pathlib
import re

import pytest
from claude_agent_sdk import CLIConnectionError, CLINotFoundError, TextBlock

from fishingrod.adaptadores.sessao import adaptador as modulo_adaptador
from fishingrod.adaptadores.sessao.adaptador import Estado
from fishingrod.adaptadores.sessao.traducao import Tradutor
from fishingrod.aplicacao.ferramentas import EntradaDoRegistro, Ferramenta, RegistroDeFerramentas, RespostaDaFerramenta
from fishingrod.aplicacao.portas.sessao import (
    AdaptadorEncerrado,
    ConfiguracaoDeSessaoInvalida,
    FalhaDoTurno,
    Familia,
    FimDeTurno,
    MensagemEntregue,
    MotivoFalhaDeSessao as M,
    PedacoDeTexto,
    UsoDeFerramenta,
)
from tests.sessao.cliente_roteirizado import (
    ChamarFerramenta,
    FabricaRoteirizada,
    Falha,
    Lento,
    Levantar,
    Mensagem,
    Parar,
    RoteiroDoTurno,
    Trava,
    assistente,
    inicio_de_texto,
    limite,
    pedido,
    resultado,
    trecho,
    turno_de_texto,
)
from tests.sessao.estrategias import (
    PRAZO_DE_SUBIDA,
    adaptador,
    agente,
    coletar,
    contexto_novo,
    esperar_que,
    executar,
    fabrica_simples,
)

SESSAO = pathlib.Path(modulo_adaptador.__file__).parent


def _turno_parado(chegou: asyncio.Event, liberar: asyncio.Event | None = None) -> RoteiroDoTurno:
    return RoteiroDoTurno([Mensagem(assistente(TextBlock("parcial"))), Parar(liberar, chegou), resultado()])


async def _abrir(fabrica, quem=None, registro=None, **prazos):
    sessoes = adaptador(fabrica, registro, **prazos)
    sessao = await sessoes.abrir(quem or agente(), contexto_novo())
    return sessoes, sessao


# --------------------------------------------------------------------------
# abrir (RN-S-05, G7)
# --------------------------------------------------------------------------


def test_rn_s_05_abrir_so_prepara_e_nao_sobe_processo():
    fabrica = FabricaRoteirizada()

    async def cenario():
        sessoes, sessao = await _abrir(fabrica)
        return sessoes.estado(sessao), sessao.nome_agente

    assert executar(cenario()) == (Estado.SEM_CONEXAO, "bibliotecario")
    assert fabrica.clientes == []


def test_rn_s_06_abrir_recusa_agente_invalido():
    async def cenario():
        await _abrir(FabricaRoteirizada(), agente(ferramentas=("criar_etapa",)))

    with pytest.raises(ConfiguracaoDeSessaoInvalida):
        executar(cenario())


def test_rn_s_39_depois_de_encerrar_abrir_levanta_e_enviar_e_sessao_fechada():
    async def cenario():
        sessoes, sessao = await _abrir(FabricaRoteirizada())
        await sessoes.encerrar()
        eventos = await coletar(sessoes.enviar(sessao, "oi"))
        with pytest.raises(AdaptadorEncerrado):
            await sessoes.abrir(agente(), contexto_novo())
        return eventos

    assert executar(cenario()) == [FalhaDoTurno(M.SESSAO_FECHADA)]


# --------------------------------------------------------------------------
# Os 9 motivos, um exemplo cada
# --------------------------------------------------------------------------


def _um_turno(fabrica, mensagem="oi"):
    async def cenario():
        sessoes, sessao = await _abrir(fabrica)
        eventos = []
        vivos_no_fim = None
        async for evento in sessoes.enviar(sessao, mensagem):
            eventos.append(evento)
            vivos_no_fim = fabrica.vivos
        return eventos, sessoes.estado(sessao), vivos_no_fim

    return executar(cenario())


def test_motivo_provedor_ausente():
    eventos, estado, vivos = _um_turno(FabricaRoteirizada(subidas=[Falha(CLINotFoundError("sem cli"))]))

    assert eventos == [FalhaDoTurno(M.PROVEDOR_AUSENTE)]
    assert (estado, vivos) == (Estado.SEM_CONEXAO, 0)


def test_motivo_nao_autenticado_derruba_e_so_sai_com_o_processo_morto():
    fabrica = FabricaRoteirizada(
        turnos=[RoteiroDoTurno([Mensagem(assistente(TextBlock("Please run /login"), erro="authentication_failed")), resultado(erro=True)])]
    )

    eventos, estado, vivos = _um_turno(fabrica)

    assert eventos == [MensagemEntregue(True), FalhaDoTurno(M.NAO_AUTENTICADO)]
    assert (estado, vivos) == (Estado.SEM_CONEXAO, 0)  # N5


def test_motivo_limite_de_uso_mantem_a_conexao_e_diz_quando_libera():
    fabrica = FabricaRoteirizada(
        turnos=[RoteiroDoTurno([Mensagem(limite("rejected", resets_at=1_767_225_600)), resultado(erro=True)])]
    )

    eventos, estado, vivos = _um_turno(fabrica)

    assert eventos[-1] == FalhaDoTurno(M.LIMITE_DE_USO, {"libera_em": "2026-01-01T00:00:00+00:00"})
    assert (estado, vivos) == (Estado.OCIOSA, 1)


def test_motivo_indisponivel_na_subida_e_no_meio_da_resposta():
    na_subida = FabricaRoteirizada(subidas=[Falha(CLIConnectionError("x"))])
    no_meio = FabricaRoteirizada(
        turnos=[RoteiroDoTurno([Mensagem(assistente(TextBlock("meio"))), Levantar(CLIConnectionError("caiu"))])]
    )

    assert _um_turno(na_subida)[0] == [FalhaDoTurno(M.INDISPONIVEL)]
    eventos, estado, vivos = _um_turno(no_meio)
    assert eventos == [MensagemEntregue(True), PedacoDeTexto("meio"), FalhaDoTurno(M.INDISPONIVEL)]
    assert (estado, vivos) == (Estado.SEM_CONEXAO, 0)


def test_nfr_s_11_subida_alem_do_prazo_e_indisponivel():
    eventos, estado, vivos = _um_turno(FabricaRoteirizada(subidas=[Trava()]))

    assert eventos == [FalhaDoTurno(M.INDISPONIVEL)]
    assert (estado, vivos) == (Estado.SEM_CONEXAO, 0)


def test_motivo_resposta_vazia_mantem_a_conexao():
    eventos, estado, vivos = _um_turno(FabricaRoteirizada(turnos=[RoteiroDoTurno([resultado()])]))

    assert eventos == [MensagemEntregue(True), FalhaDoTurno(M.RESPOSTA_VAZIA)]
    assert (estado, vivos) == (Estado.OCIOSA, 1)


def test_motivo_mensagem_invalida_nao_toca_o_provedor():
    fabrica = FabricaRoteirizada()

    eventos, estado, _ = _um_turno(fabrica, "   \t ")

    assert eventos == [FalhaDoTurno(M.MENSAGEM_INVALIDA, {"problema": "vazia"})]
    assert estado is Estado.SEM_CONEXAO
    assert fabrica.clientes == []


def test_motivo_turno_em_andamento_nao_toca_o_turno_que_esta_andando():
    chegou = asyncio.Event()
    liberar = asyncio.Event()
    fabrica = FabricaRoteirizada(turnos=[_turno_parado(chegou, liberar)])

    async def cenario():
        sessoes, sessao = await _abrir(fabrica)
        primeiro = asyncio.create_task(coletar(sessoes.enviar(sessao, "um")))
        await chegou.wait()
        segundo = await coletar(sessoes.enviar(sessao, "dois"))
        liberar.set()
        return segundo, await primeiro, fabrica.clientes[0].consultas

    segundo, primeiro, consultas = executar(cenario())

    assert segundo == [FalhaDoTurno(M.TURNO_EM_ANDAMENTO)]
    assert primeiro == [MensagemEntregue(True), PedacoDeTexto("parcial"), FimDeTurno()]
    assert consultas == ["um"]


def test_rn_s_27_a_vaga_e_tomada_antes_de_qualquer_espera():
    """Dois envios na mesma volta do laco: o segundo ve a vaga tomada."""

    async def cenario():
        sessoes, sessao = await _abrir(FabricaRoteirizada())
        um, dois = sessoes.enviar(sessao, "um"), sessoes.enviar(sessao, "dois")
        primeiro, segundo = await asyncio.gather(anext(um), anext(dois))
        await um.aclose()
        return primeiro, segundo

    primeiro, segundo = executar(cenario())

    assert segundo == FalhaDoTurno(M.TURNO_EM_ANDAMENTO)
    assert primeiro == MensagemEntregue(True)


def test_motivo_sessao_fechada_antes_e_durante_o_turno():
    chegou = asyncio.Event()
    fabrica = FabricaRoteirizada(turnos=[_turno_parado(chegou)])

    async def cenario():
        sessoes, sessao = await _abrir(fabrica)
        turno = asyncio.create_task(coletar(sessoes.enviar(sessao, "um")))
        await chegou.wait()
        await sessoes.fechar(sessao)
        vivos_ao_voltar = fabrica.vivos
        durante = await turno
        depois = await coletar(sessoes.enviar(sessao, "dois"))
        return durante, depois, vivos_ao_voltar, sessoes.estado(sessao)

    durante, depois, vivos, estado = executar(cenario())

    assert durante == [MensagemEntregue(True), PedacoDeTexto("parcial"), FalhaDoTurno(M.SESSAO_FECHADA)]
    assert depois == [FalhaDoTurno(M.SESSAO_FECHADA)]
    assert vivos == 0  # DP-S-06: fechar volta com o processo morto
    assert estado is Estado.FECHADA


def test_motivo_falha_inesperada_por_sinal():
    fabrica = FabricaRoteirizada(turnos=[RoteiroDoTurno([Mensagem(assistente(erro="invalid_request")), resultado(erro=True)])])

    eventos, estado, vivos = _um_turno(fabrica)

    assert eventos[-1] == FalhaDoTurno(M.FALHA_INESPERADA)
    assert (estado, vivos) == (Estado.SEM_CONEXAO, 0)


def test_dp_s_10_a_rede_defeito_no_adaptador_vira_falha_inesperada(monkeypatch, caplog):
    def quebrado(self, mensagem):
        raise ZeroDivisionError("defeito no tradutor")

    monkeypatch.setattr(Tradutor, "traduzir", quebrado)

    with caplog.at_level(logging.ERROR, logger="fishingrod.sessao"):
        eventos, estado, vivos = _um_turno(FabricaRoteirizada())

    assert eventos == [MensagemEntregue(True), FalhaDoTurno(M.FALHA_INESPERADA)]
    assert (estado, vivos) == (Estado.SEM_CONEXAO, 0)
    assert any(r.exc_info and r.exc_info[0] is ZeroDivisionError for r in caplog.records)


# --------------------------------------------------------------------------
# Reconexao (RN-S-34, RN-S-41, G2)
# --------------------------------------------------------------------------


def test_rn_s_34_reconexao_com_conversa_nova():
    fabrica = FabricaRoteirizada(
        turnos=[turno_de_texto("um"), RoteiroDoTurno([Levantar(CLIConnectionError("caiu"))]), turno_de_texto("tres")]
    )

    async def cenario():
        sessoes, sessao = await _abrir(fabrica)
        return [await coletar(sessoes.enviar(sessao, t)) for t in ("um", "dois", "tres")]

    um, dois, tres = executar(cenario())

    assert um[0] == MensagemEntregue(True)
    assert dois == [MensagemEntregue(False), FalhaDoTurno(M.INDISPONIVEL)]
    assert tres[0] == MensagemEntregue(True)  # o agente nao lembra
    assert len(fabrica.clientes) == 2


# --------------------------------------------------------------------------
# ESC (RN-S-35, RN-S-36, N2, N3, G6)
# --------------------------------------------------------------------------


def test_rn_s_36_esc_antes_da_entrega_descarta_o_processo():
    fabrica = FabricaRoteirizada(subidas=[Trava()])

    async def cenario():
        sessoes, sessao = await _abrir(fabrica, prazo_de_subida=60)
        turno = asyncio.create_task(coletar(sessoes.enviar(sessao, "um")))
        await esperar_que(lambda: fabrica.vivos == 1)
        turno.cancel()
        with pytest.raises(asyncio.CancelledError):
            await turno
        await esperar_que(lambda: sessoes.estado(sessao) is Estado.SEM_CONEXAO)
        proximo = await coletar(sessoes.enviar(sessao, "dois"))
        return proximo

    proximo = executar(cenario())

    assert proximo[0] == MensagemEntregue(True)
    assert fabrica.clientes[0].consultas == []  # para o agente, a mensagem nunca existiu


def test_rn_s_35_esc_depois_da_entrega_interrompe_e_guarda_o_historico():
    chegou = asyncio.Event()
    fabrica = FabricaRoteirizada(turnos=[_turno_parado(chegou), turno_de_texto("dois")])

    async def cenario():
        sessoes, sessao = await _abrir(fabrica)
        turno = asyncio.create_task(coletar(sessoes.enviar(sessao, "um")))
        await chegou.wait()
        turno.cancel()
        with pytest.raises(asyncio.CancelledError):
            await turno
        await esperar_que(lambda: sessoes.estado(sessao) is Estado.OCIOSA)
        return await coletar(sessoes.enviar(sessao, "dois")), fabrica.vivos

    proximo, vivos = executar(cenario())

    assert proximo[0] == MensagemEntregue(False)
    assert fabrica.clientes[0].interrupcoes == 1
    assert vivos == 1


def test_rn_s_35_aviso_que_falha_descarta_o_processo():
    chegou = asyncio.Event()
    fabrica = FabricaRoteirizada(turnos=[_turno_parado(chegou)], interrupcao=Falha(CLIConnectionError("x")))

    async def cenario():
        sessoes, sessao = await _abrir(fabrica)
        turno = asyncio.create_task(coletar(sessoes.enviar(sessao, "um")))
        await chegou.wait()
        turno.cancel()
        await asyncio.gather(turno, return_exceptions=True)
        await esperar_que(lambda: sessoes.estado(sessao) is Estado.SEM_CONEXAO)
        return fabrica.vivos

    assert executar(cenario()) == 0


def test_n3_esc_no_instante_da_entrega_descarta_mesmo_com_a_escrita_feita():
    """O CLI ja recebeu a mensagem, mas quem le ainda nao viu MensagemEntregue:
    o processo e descartado, e a transcricao continua honesta (C2=A)."""
    liberar = asyncio.Event()
    fabrica = FabricaRoteirizada(turnos=[RoteiroDoTurno([Parar()], entrega=Trava(liberar)), turno_de_texto("dois")])

    async def cenario():
        sessoes, sessao = await _abrir(fabrica)
        vistos = []

        async def ler():
            async for evento in sessoes.enviar(sessao, "um"):
                vistos.append(evento)

        turno = asyncio.create_task(ler())
        await esperar_que(lambda: fabrica.clientes and fabrica.clientes[0].consultas)
        liberar.set()  # a dona termina a escrita na proxima volta do laco...
        turno.cancel()  # ...e quem le e cancelado antes de ler a entrega
        await asyncio.gather(turno, return_exceptions=True)
        await esperar_que(lambda: sessoes.estado(sessao) is Estado.SEM_CONEXAO)
        proximo = await coletar(sessoes.enviar(sessao, "dois"))
        return vistos, proximo

    vistos, proximo = executar(cenario())

    assert vistos == []
    assert fabrica.clientes[0].consultas == ["um"]
    assert fabrica.clientes[0].interrupcoes == 0
    assert proximo[0] == MensagemEntregue(True)


def test_g6_abandonar_o_iterador_e_interromper():
    chegou = asyncio.Event()
    fabrica = FabricaRoteirizada(turnos=[_turno_parado(chegou)])

    async def cenario():
        sessoes, sessao = await _abrir(fabrica)
        iterador = sessoes.enviar(sessao, "um")
        primeiro = await anext(iterador)
        await iterador.aclose()
        await esperar_que(lambda: sessoes.estado(sessao) is Estado.OCIOSA)
        return primeiro

    assert executar(cenario()) == MensagemEntregue(True)
    assert fabrica.clientes[0].interrupcoes == 1


def test_dp_s_04_o_resto_de_um_turno_abandonado_nao_vaza_para_o_seguinte():
    """Quem le para logo na entrega, com o resto do turno ja na fila: nada
    desse resto pode aparecer no turno seguinte."""
    chegou = asyncio.Event()
    fabrica = FabricaRoteirizada(turnos=[_turno_parado(chegou), turno_de_texto("dois")])

    async def cenario():
        sessoes, sessao = await _abrir(fabrica)
        iterador = sessoes.enviar(sessao, "um")
        await anext(iterador)
        await chegou.wait()  # "parcial" ja esta na fila do primeiro turno
        await iterador.aclose()
        await esperar_que(lambda: sessoes.estado(sessao) is Estado.OCIOSA)
        return await coletar(sessoes.enviar(sessao, "dois"))

    assert executar(cenario()) == [MensagemEntregue(False), PedacoDeTexto("dois"), FimDeTurno()]


def test_n2_a_proxima_mensagem_espera_a_cauda_em_vez_de_dar_turno_em_andamento():
    chegou = asyncio.Event()
    fabrica = FabricaRoteirizada(turnos=[_turno_parado(chegou), turno_de_texto("dois")], interrupcao=Lento(0.1))

    async def cenario():
        sessoes, sessao = await _abrir(fabrica)
        turno = asyncio.create_task(coletar(sessoes.enviar(sessao, "um")))
        await chegou.wait()
        turno.cancel()
        await asyncio.gather(turno, return_exceptions=True)
        na_cauda = sessoes.estado(sessao)
        segundo = asyncio.create_task(coletar(sessoes.enviar(sessao, "dois")))
        await asyncio.sleep(0)
        terceiro = await coletar(sessoes.enviar(sessao, "tres"))  # a vaga e de quem espera a cauda
        return na_cauda, await segundo, terceiro

    na_cauda, segundo, terceiro = executar(cenario())

    assert na_cauda is Estado.EM_TURNO
    assert segundo == [MensagemEntregue(False), PedacoDeTexto("dois"), FimDeTurno()]
    assert terceiro == [FalhaDoTurno(M.TURNO_EM_ANDAMENTO)]


def test_esc_enquanto_espera_a_cauda_nao_mexe_na_cauda():
    chegou = asyncio.Event()
    fabrica = FabricaRoteirizada(turnos=[_turno_parado(chegou)], interrupcao=Lento(0.1))

    async def cenario():
        sessoes, sessao = await _abrir(fabrica)
        turno = asyncio.create_task(coletar(sessoes.enviar(sessao, "um")))
        await chegou.wait()
        turno.cancel()
        await asyncio.gather(turno, return_exceptions=True)
        esperando = asyncio.create_task(coletar(sessoes.enviar(sessao, "dois")))
        await asyncio.sleep(0.01)
        esperando.cancel()
        await asyncio.gather(esperando, return_exceptions=True)
        await esperar_que(lambda: sessoes.estado(sessao) is Estado.OCIOSA)
        return fabrica.clientes[0].consultas

    assert executar(cenario()) == ["um"]


# --------------------------------------------------------------------------
# Ferramentas e interrupcao (RN-S-35, RN-S-44)
# --------------------------------------------------------------------------


def test_rn_s_44_fechar_cancela_a_ferramenta_em_execucao():
    comecou = asyncio.Event()
    cancelada = []

    async def pendurada(argumentos):
        comecou.set()
        try:
            await asyncio.Event().wait()
        except asyncio.CancelledError:
            cancelada.append(True)
            raise

    registro = RegistroDeFerramentas([EntradaDoRegistro("ler", Familia.WIKI, fabrica_simples("ler", pendurada))])
    fabrica = FabricaRoteirizada(
        turnos=[RoteiroDoTurno([Mensagem(pedido("mcp__wiki__ler")), ChamarFerramenta("mcp__wiki__ler", concorrente=True), Parar()])]
    )

    async def cenario():
        sessoes, sessao = await _abrir(fabrica, agente(ferramentas=("ler",)), registro)
        turno = asyncio.create_task(coletar(sessoes.enviar(sessao, "um")))
        await comecou.wait()
        await sessoes.fechar(sessao)
        return await turno

    eventos = executar(cenario())

    assert cancelada == [True]
    assert eventos == [MensagemEntregue(True), UsoDeFerramenta(Familia.WIKI, "ler", {}), FalhaDoTurno(M.SESSAO_FECHADA)]


# --------------------------------------------------------------------------
# encerrar em paralelo (RN-S-39, DP-S-06)
# --------------------------------------------------------------------------


def test_rn_s_39_encerrar_fecha_todas_em_paralelo():
    fabrica = FabricaRoteirizada(desconexao=Lento(0.2))

    async def cenario():
        sessoes = adaptador(fabrica)
        vivas = [await sessoes.abrir(agente(), contexto_novo()) for _ in range(3)]
        for sessao in vivas:
            await coletar(sessoes.enviar(sessao, "oi"))
        inicio = asyncio.get_running_loop().time()
        await sessoes.encerrar()
        return asyncio.get_running_loop().time() - inicio, [sessoes.estado(s) for s in vivas]

    duracao, estados = executar(cenario())

    assert duracao < 0.5  # tres fechamentos de 0,2 s em paralelo, nao 0,6 s
    assert estados == [Estado.FECHADA] * 3
    assert fabrica.vivos == 0


def test_rn_s_37_fechar_duas_vezes_e_como_fechar_uma():
    fabrica = FabricaRoteirizada()

    async def cenario():
        sessoes, sessao = await _abrir(fabrica)
        await coletar(sessoes.enviar(sessao, "oi"))
        await sessoes.fechar(sessao)
        await sessoes.fechar(sessao)
        return sessoes.estado(sessao)

    assert executar(cenario()) is Estado.FECHADA
    assert fabrica.vivos == 0


# --------------------------------------------------------------------------
# NFR-S-12: sem prazo de silencio
# --------------------------------------------------------------------------


def test_nfr_s_12_turno_parado_nao_termina_sozinho():
    chegou = asyncio.Event()
    fabrica = FabricaRoteirizada(turnos=[_turno_parado(chegou)])

    async def cenario():
        sessoes, sessao = await _abrir(fabrica)
        turno = asyncio.create_task(coletar(sessoes.enviar(sessao, "um")))
        await chegou.wait()
        await asyncio.sleep(PRAZO_DE_SUBIDA * 3)
        ainda = (turno.done(), sessoes.estado(sessao))
        turno.cancel()
        await asyncio.gather(turno, return_exceptions=True)
        return ainda

    assert executar(cenario()) == (False, Estado.EM_TURNO)


# --------------------------------------------------------------------------
# O log (NFR-S-17, RN-S-54)
# --------------------------------------------------------------------------

SEGREDO_DA_MENSAGEM = "mensagem-secreta-do-usuario"
SEGREDO_DO_ARGUMENTO = "argumento-secreto"
SEGREDO_DO_MODELO = "resposta-secreta-do-modelo"


def _niveis(caplog, trecho_da_mensagem: str) -> list[int]:
    return [r.levelno for r in caplog.records if r.name.startswith("fishingrod") and trecho_da_mensagem in r.getMessage()]


def test_nfr_s_17_niveis_do_log(caplog):
    fabrica = FabricaRoteirizada(
        subidas=[Falha(CLIConnectionError("x"))],
        turnos=[
            RoteiroDoTurno(
                [
                    Mensagem(inicio_de_texto(0)),
                    Mensagem(trecho(0, "Oi")),
                    Mensagem(assistente(TextBlock("Ola"))),
                    Mensagem(pedido("Bash", {"command": SEGREDO_DO_ARGUMENTO})),
                    ChamarFerramenta("mcp__ambiente__criar_frente", {"nome": SEGREDO_DO_ARGUMENTO}),
                    resultado(),
                ]
            ),
            RoteiroDoTurno([Mensagem(limite("rejected")), resultado(erro=True)]),
        ],
    )

    async def cenario():
        sessoes, sessao = await _abrir(fabrica)
        await coletar(sessoes.enviar(sessao, "subida falha"))
        await coletar(sessoes.enviar(sessao, "um"))
        await coletar(sessoes.enviar(sessao, "dois"))
        await coletar(sessoes.enviar(sessao, "   "))
        iterador = sessoes.enviar(sessao, "tres")
        fabrica.turnos.append(RoteiroDoTurno([Parar()]))
        await anext(iterador)
        await coletar(sessoes.enviar(sessao, "quatro"))
        await iterador.aclose()
        await sessoes.fechar(sessao)
        await coletar(sessoes.enviar(sessao, "cinco"))
        await sessoes.encerrar()

    with caplog.at_level(logging.DEBUG, logger="fishingrod"):
        executar(cenario())

    assert _niveis(caplog, "aberta para o agente") == [logging.INFO]
    assert set(_niveis(caplog, "conectando")) == {logging.INFO}
    assert _niveis(caplog, "] fechada") == [logging.INFO]
    assert _niveis(caplog, "adaptador de sessao encerrado") == [logging.INFO]
    assert _niveis(caplog, "terminou em indisponivel") == [logging.WARNING]
    subida = next(r for r in caplog.records if "terminou em indisponivel" in r.getMessage())
    assert subida.exc_info is not None  # a falha ao subir vai com a pilha (Q3=A)
    assert _niveis(caplog, "terminou em limite_de_uso") == [logging.WARNING]
    assert _niveis(caplog, "ferramenta negada") == [logging.WARNING]
    assert _niveis(caplog, "de fora da sessao") == [logging.WARNING]
    assert _niveis(caplog, "trechos divergentes") == [logging.WARNING]
    assert _niveis(caplog, "mensagem invalida") == [logging.INFO]
    assert _niveis(caplog, "ja tem um turno em andamento") == [logging.WARNING]
    assert _niveis(caplog, "sessao fechada") == [logging.INFO]


def test_rn_s_54_nenhum_registro_leva_mensagem_argumento_ou_texto_do_modelo(caplog):
    registro = RegistroDeFerramentas(
        [EntradaDoRegistro("ler", Familia.WIKI, fabrica_simples("ler", _que_levanta))]
    )
    fabrica = FabricaRoteirizada(
        turnos=[
            RoteiroDoTurno(
                [
                    Mensagem(assistente(TextBlock(SEGREDO_DO_MODELO))),
                    Mensagem(pedido("mcp__wiki__ler", {"chave": SEGREDO_DO_ARGUMENTO})),
                    ChamarFerramenta("mcp__wiki__ler", {"chave": SEGREDO_DO_ARGUMENTO}),
                    Mensagem(pedido("mcp__wiki__nao_existe", {"chave": SEGREDO_DO_ARGUMENTO})),
                    resultado(),
                ]
            ),
            RoteiroDoTurno([Levantar(RuntimeError("defeito"))]),
        ]
    )

    async def cenario():
        sessoes, sessao = await _abrir(fabrica, agente(ferramentas=("ler",)), registro)
        await coletar(sessoes.enviar(sessao, SEGREDO_DA_MENSAGEM))
        await coletar(sessoes.enviar(sessao, SEGREDO_DA_MENSAGEM))
        await coletar(sessoes.enviar(sessao, SEGREDO_DA_MENSAGEM + " " * 100_000))
        await sessoes.encerrar()

    with caplog.at_level(logging.DEBUG, logger="fishingrod"):
        executar(cenario())

    nossos = "\n".join(r.getMessage() for r in caplog.records if r.name.startswith("fishingrod"))
    assert nossos
    for segredo in (SEGREDO_DA_MENSAGEM, SEGREDO_DO_ARGUMENTO, SEGREDO_DO_MODELO):
        assert segredo not in nossos


async def _que_levanta(argumentos):
    raise RuntimeError("falhou")


def test_transicao_fora_da_tabela_e_defeito_no_log(caplog):
    async def cenario():
        sessoes, sessao = await _abrir(FabricaRoteirizada())
        interna = sessoes._sessoes[sessao.id]
        with caplog.at_level(logging.ERROR, logger="fishingrod.sessao"):
            sessoes._mudar(interna, Estado.OCIOSA)
        return sessoes.estado(sessao)

    assert executar(cenario()) is Estado.SEM_CONEXAO
    assert "transicao fora da tabela" in caplog.text


# --------------------------------------------------------------------------
# DP-S-08: nenhum outro temporizador
# --------------------------------------------------------------------------

_TEMPORIZADORES = re.compile(
    r"asyncio\.timeout|wait_for|asyncio\.sleep|call_later|call_at|fail_after|move_on_after|timeout_at|timeout\s*="
)


def test_dp_s_08_so_conexao_py_tem_temporizador_e_so_os_dois_prazos():
    for caminho in sorted(SESSAO.glob("*.py")):
        achados = _TEMPORIZADORES.findall(caminho.read_text(encoding="utf-8"))
        if caminho.name == "conexao.py":
            assert achados == ["asyncio.timeout"], achados
        else:
            assert achados == [], caminho.name
    conexao = (SESSAO / "conexao.py").read_text(encoding="utf-8")
    chamadas = re.findall(r"self\._esperar\(Etapa\.\w+, ([^,]+),", conexao)
    assert set(chamadas) == {"self._prazo_de_subida", "None", "self._prazo_de_interrupcao"}
