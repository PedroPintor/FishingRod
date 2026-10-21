"""Card 002 - o servico de conversa, com o adaptador de verdade sobre um Claude
roteirizado. Cada teste segue um item de "Como testar" do card (os de tela
estao em tests/interface/test_chat.py)."""

import asyncio

from claude_agent_sdk import CLIConnectionError, TextBlock

from fishingrod.aplicacao.portas.sessao import MotivoFalhaDeSessao
from fishingrod.aplicacao.servicos.servico_de_conversa import (
    ACAO_RECUSADA,
    AGENTE,
    AVISO,
    CONVERSA_RECOMECOU,
    MARCA_DE_INTERROMPIDA,
    USUARIO,
    EstadoDoChat,
    aviso,
)
from fishingrod.interface.montagem import montar
from tests.conversa.instrumentos import ate, ate_responder, com_roteiro, preparar, textos
from tests.sessao.cliente_roteirizado import (
    ChamarFerramenta,
    FabricaRoteirizada,
    Levantar,
    Mensagem,
    Parar,
    RoteiroDoTurno,
    assistente,
    resultado,
    turno_de_texto,
)


def rodar(tmp_path, fabrica, roteiro):
    async def principal():
        programa = await montar(tmp_path, com_roteiro(fabrica))
        try:
            return await roteiro(programa, *await preparar(programa))
        finally:
            await programa.fechar()

    return asyncio.run(principal())


def _parado(liberar: asyncio.Event, chegou: asyncio.Event, texto: str = "parcial") -> RoteiroDoTurno:
    return RoteiroDoTurno([Mensagem(assistente(TextBlock(texto))), Parar(liberar, chegou), resultado()])


def test_cinco_mensagens_seguidas_usam_um_processo_so(tmp_path):
    fabrica = FabricaRoteirizada(turnos=[turno_de_texto(f"resposta {n}") for n in range(5)])

    async def roteiro(programa, ambiente, orquestrador, _):
        conversa = programa.conversa
        abertas = []
        for n in range(5):
            conversa.enviar(orquestrador.id, f"mensagem {n}")
            await ate_responder(conversa, orquestrador)
            abertas.append(conversa.conexoes_abertas())
        return abertas, textos(conversa, orquestrador)

    abertas, linhas = rodar(tmp_path, fabrica, roteiro)

    assert len(fabrica.clientes) == 1
    assert abertas == [1, 1, 1, 1, 1]
    assert linhas == [linha for n in range(5) for linha in ((USUARIO, f"mensagem {n}"), (AGENTE, f"resposta {n}"))]


def test_mensagem_mandada_durante_a_resposta_espera_na_fila(tmp_path):
    liberar, chegou = asyncio.Event(), asyncio.Event()
    fabrica = FabricaRoteirizada(turnos=[_parado(liberar, chegou), turno_de_texto("segunda")])

    async def roteiro(programa, ambiente, orquestrador, _):
        conversa = programa.conversa
        conversa.enviar(orquestrador.id, "um")
        await chegou.wait()
        conversa.enviar(orquestrador.id, "dois")
        durante = (conversa.fila(orquestrador.id), list(fabrica.clientes[0].consultas))
        liberar.set()
        await ate_responder(conversa, orquestrador)
        return durante, fabrica.clientes[0].consultas, textos(conversa, orquestrador)

    (fila, consultas_durante), consultas, linhas = rodar(tmp_path, fabrica, roteiro)

    assert fila == ("dois",) and consultas_durante == ["um"]
    assert consultas == ["um", "dois"]
    assert linhas == [(USUARIO, "um"), (AGENTE, "parcial"), (USUARIO, "dois"), (AGENTE, "segunda")]


def test_interromper_marca_a_resposta_e_devolve_a_fila(tmp_path):
    chegou = asyncio.Event()
    fabrica = FabricaRoteirizada(turnos=[_parado(asyncio.Event(), chegou)])

    async def roteiro(programa, ambiente, orquestrador, _):
        conversa = programa.conversa
        conversa.enviar(orquestrador.id, "um")
        await chegou.wait()
        await ate(lambda: (AGENTE, "parcial") in textos(conversa, orquestrador))
        conversa.enviar(orquestrador.id, "dois")
        conversa.enviar(orquestrador.id, "tres")
        devolvidas = await conversa.interromper(orquestrador.id)
        guardadas = await programa.repositorio.listar_mensagens(orquestrador.id, 10)
        return devolvidas, conversa.estado(orquestrador.id), textos(conversa, orquestrador), guardadas

    devolvidas, estado, linhas, guardadas = rodar(tmp_path, fabrica, roteiro)

    assert devolvidas == ["dois", "tres"]
    assert estado is EstadoDoChat.LIGADO  # o Esc nao desliga: o processo fica
    assert linhas == [(USUARIO, "um"), (AGENTE, f"parcial {MARCA_DE_INTERROMPIDA}")]
    assert [(m.papel, m.texto, m.em_andamento) for m in guardadas] == [
        (USUARIO, "um", False),
        (AGENTE, f"parcial {MARCA_DE_INTERROMPIDA}", False),
    ]


def test_dois_chats_respondem_ao_mesmo_tempo(tmp_path):
    liberar, chegou = asyncio.Event(), asyncio.Event()
    fabrica = FabricaRoteirizada(turnos=[_parado(liberar, chegou, "A comecou"), turno_de_texto("B respondeu")])

    async def roteiro(programa, ambiente, a, b):
        conversa = programa.conversa
        conversa.enviar(a.id, "para A")
        await chegou.wait()
        conversa.enviar(b.id, "para B")
        await ate_responder(conversa, b)
        durante = (conversa.estado(a.id), textos(conversa, b), conversa.conexoes_abertas())
        liberar.set()
        await ate_responder(conversa, a)
        return durante, textos(conversa, a)

    (estado_de_a, linhas_de_b, abertas), linhas_de_a = rodar(tmp_path, fabrica, roteiro)

    assert estado_de_a is EstadoDoChat.RESPONDENDO
    assert linhas_de_b == [(USUARIO, "para B"), (AGENTE, "B respondeu")]
    assert abertas == 2
    assert linhas_de_a == [(USUARIO, "para A"), (AGENTE, "A comecou")]
    assert len(fabrica.clientes) == 2


def test_falha_num_chat_avisa_so_nele_e_o_outro_continua(tmp_path):
    fabrica = FabricaRoteirizada(
        turnos=[RoteiroDoTurno([Levantar(CLIConnectionError("caiu"))]), turno_de_texto("tudo certo")]
    )

    async def roteiro(programa, ambiente, a, b):
        conversa = programa.conversa
        conversa.enviar(a.id, "oi")
        await ate_responder(conversa, a)
        conversa.enviar(b.id, "oi")
        await ate_responder(conversa, b)
        return textos(conversa, a), textos(conversa, b), conversa.estado(a.id)

    linhas_de_a, linhas_de_b, estado_de_a = rodar(tmp_path, fabrica, roteiro)

    assert linhas_de_a == [(USUARIO, "oi"), (AVISO, MotivoFalhaDeSessao.INDISPONIVEL.value)]
    assert linhas_de_b == [(USUARIO, "oi"), (AGENTE, "tudo certo")]
    assert estado_de_a is EstadoDoChat.PRONTO  # o processo caiu: nao conta mais


def test_conversa_que_o_claude_perdeu_avisa_e_recomeca_do_zero(tmp_path):
    fabrica = FabricaRoteirizada(turnos=[turno_de_texto("primeira"), turno_de_texto("de novo")])

    async def roteiro(programa, ambiente, orquestrador, _):
        conversa = programa.conversa
        conversa.enviar(orquestrador.id, "um")
        await ate_responder(conversa, orquestrador)
        await conversa.desligar(orquestrador.id)
        fabrica.conversas.clear()  # a pasta do Claude foi apagada
        conversa.enviar(orquestrador.id, "dois")
        await ate_responder(conversa, orquestrador)
        return textos(conversa, orquestrador)

    linhas = rodar(tmp_path, fabrica, roteiro)

    assert linhas == [
        (USUARIO, "um"),
        (AGENTE, "primeira"),  # o texto antigo continua
        (USUARIO, "dois"),
        (AVISO, CONVERSA_RECOMECOU),
        (AGENTE, "de novo"),
    ]


def test_desligar_e_mandar_de_novo_retoma_sem_aviso(tmp_path):
    fabrica = FabricaRoteirizada()

    async def roteiro(programa, ambiente, orquestrador, _):
        conversa = programa.conversa
        conversa.enviar(orquestrador.id, "um")
        await ate_responder(conversa, orquestrador)
        await conversa.desligar(orquestrador.id)
        desligado = (conversa.estado(orquestrador.id), conversa.conexoes_abertas(), fabrica.vivos)
        conversa.enviar(orquestrador.id, "dois")
        await ate_responder(conversa, orquestrador)
        return desligado, conversa.conexoes_abertas(), textos(conversa, orquestrador)

    desligado, abertas, linhas = rodar(tmp_path, fabrica, roteiro)

    assert desligado == (EstadoDoChat.PRONTO, 0, 0)
    assert abertas == 1
    assert AVISO not in [papel for papel, _ in linhas]
    assert fabrica.opcoes[1].resume == fabrica.opcoes[0].session_id


def test_fechar_o_programa_desliga_todos_os_chats(tmp_path):
    chegou = asyncio.Event()
    fabrica = FabricaRoteirizada(turnos=[turno_de_texto("ok"), _parado(asyncio.Event(), chegou)])

    async def principal():
        programa = await montar(tmp_path, com_roteiro(fabrica))
        _, a, b = await preparar(programa)
        programa.conversa.enviar(a.id, "oi")
        await ate_responder(programa.conversa, a)
        programa.conversa.enviar(b.id, "oi")
        await chegou.wait()
        antes = fabrica.vivos
        await programa.fechar()
        return antes, fabrica.vivos

    antes, depois = asyncio.run(principal())

    assert (antes, depois) == (2, 0)


def test_acao_que_o_orquestrador_pede_e_recusada_e_o_chat_avisa(tmp_path):
    fabrica = FabricaRoteirizada(
        turnos=[
            RoteiroDoTurno(
                [ChamarFerramenta("mcp__ambiente__criar_frente", {"nome": "marketing"}), *turno_de_texto("tentei").passos]
            )
        ]
    )

    async def roteiro(programa, ambiente, orquestrador, _):
        conversa = programa.conversa
        conversa.enviar(orquestrador.id, "crie a frente marketing")
        await ate_responder(conversa, orquestrador)
        return textos(conversa, orquestrador), [f.nome for f in ambiente.frentes]

    linhas, frentes = rodar(tmp_path, fabrica, roteiro)

    assert (AVISO, aviso(ACAO_RECUSADA, "criar_frente")) in linhas
    assert frentes == ["vendas"]


def test_reabrir_o_programa_traz_a_conversa_do_banco(tmp_path):
    fabrica = FabricaRoteirizada(turnos=[turno_de_texto("guardada")])

    async def principal():
        programa = await montar(tmp_path, com_roteiro(fabrica))
        _, orquestrador, _ = await preparar(programa)
        programa.conversa.enviar(orquestrador.id, "oi")
        await ate_responder(programa.conversa, orquestrador)
        await programa.fechar()

        de_novo = await montar(tmp_path, com_roteiro(fabrica))
        try:
            await de_novo.conversa.abrir(orquestrador.contexto, orquestrador.agente)
            return textos(de_novo.conversa, orquestrador), de_novo.conversa.estado(orquestrador.id)
        finally:
            await de_novo.fechar()

    linhas, estado = asyncio.run(principal())

    assert linhas == [(USUARIO, "oi"), (AGENTE, "guardada")]
    assert estado is EstadoDoChat.PRONTO
