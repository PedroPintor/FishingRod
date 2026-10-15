"""U6 - o contrato da PortaSessao (criterio 1, TD-01, NFR-S-09, DP-S-22).

UM modulo, tres implementacoes:
- `falsa`: a SessaoFalsa de tests/dobles, escrita a mao;
- `roteirizada`: o adaptador real, com o cliente roteirizado no lugar do CLI;
- `real`: o adaptador real com o CLI de verdade - so com `-m sdk_real`, porque
  gasta o limite da sua assinatura.

Se o falso e o real discordam aqui, o contrato estava ambiguo - e e isso que
este teste existe para descobrir antes de U7 e U8 dependerem dele.
"""

import inspect

import pytest

from fishingrod.adaptadores.sessao import AdaptadorSessaoClaude
from fishingrod.aplicacao.portas.sessao import (
    ConfiguracaoDeSessaoInvalida,
    FalhaDoTurno,
    FimDeTurno,
    MensagemEntregue,
    MotivoFalhaDeSessao as M,
    PedacoDeTexto,
    PortaSessao,
    UsoDeFerramenta,
)
from fishingrod.dominio import Agente, Papel
from tests.dobles.sessao_falsa import SessaoFalsa
from tests.sessao.cliente_roteirizado import FabricaRoteirizada
from tests.sessao.estrategias import adaptador, coletar, contexto_novo, executar, registro_de_teste

PEDIDO = "Responda somente com a palavra: pronto."


def _agente(modelo: str) -> Agente:
    return Agente("bibliotecario", Papel.SUB_AGENTE, modelo, regras=("Responda em portugues, numa frase curta.",))


@pytest.fixture(
    params=[
        "falsa",
        "roteirizada",
        pytest.param("real", marks=pytest.mark.sdk_real),
    ]
)
def implementacao(request, tmp_path):
    """(fabricar a porta, o agente). A porta e fabricada dentro do laco de
    cada teste."""
    match request.param:
        case "falsa":
            return (lambda: SessaoFalsa(registro_de_teste())), _agente("modelo-de-teste")
        case "roteirizada":
            return (lambda: adaptador(FabricaRoteirizada())), _agente("modelo-de-teste")
        case "real":
            pasta = tmp_path / "trabalho"
            pasta.mkdir()
            return (lambda: AdaptadorSessaoClaude(registro_de_teste(), pasta)), _agente("haiku")
    raise AssertionError(request.param)


def _gramatica(eventos: list) -> None:
    *meio, final = eventos
    assert isinstance(final, (FimDeTurno, FalhaDoTurno))
    if meio:
        assert isinstance(meio[0], MensagemEntregue)
        assert all(isinstance(e, (PedacoDeTexto, UsoDeFerramenta)) for e in meio[1:])
    if isinstance(final, FimDeTurno):
        assert any(isinstance(e, (PedacoDeTexto, UsoDeFerramenta)) for e in meio)


async def _encerrar(porta) -> None:
    await porta.encerrar()


def test_criterio_1_td_01_resposta_nao_vazia(implementacao):
    fabricar, quem = implementacao

    async def cenario():
        porta: PortaSessao = fabricar()
        sessao = await porta.abrir(quem, contexto_novo())
        um = await coletar(porta.enviar(sessao, PEDIDO))
        dois = await coletar(porta.enviar(sessao, PEDIDO))
        await _encerrar(porta)
        return um, dois

    um, dois = executar(cenario())

    for eventos in (um, dois):
        _gramatica(eventos)
        assert eventos[-1] == FimDeTurno()
        assert "".join(e.texto for e in eventos if isinstance(e, PedacoDeTexto)).strip()
    assert um[0] == MensagemEntregue(conversa_nova=True)
    assert dois[0] == MensagemEntregue(conversa_nova=False)


def test_mensagem_invalida_e_falha_tipada_sem_tocar_o_provedor(implementacao):
    fabricar, quem = implementacao

    async def cenario():
        porta = fabricar()
        sessao = await porta.abrir(quem, contexto_novo())
        vazia = await coletar(porta.enviar(sessao, " \n\t "))
        longa = await coletar(porta.enviar(sessao, "a" * 100_001))
        await _encerrar(porta)
        return vazia, longa

    vazia, longa = executar(cenario())

    assert vazia == [FalhaDoTurno(M.MENSAGEM_INVALIDA, {"problema": "vazia"})]
    assert longa == [FalhaDoTurno(M.MENSAGEM_INVALIDA, {"problema": "longa_demais", "maximo": "100000"})]


def test_turno_em_andamento_e_falha_tipada(implementacao):
    fabricar, quem = implementacao

    async def cenario():
        porta = fabricar()
        sessao = await porta.abrir(quem, contexto_novo())
        primeiro = porta.enviar(sessao, PEDIDO)
        entregue = await anext(primeiro)
        segundo = await coletar(porta.enviar(sessao, PEDIDO))
        resto = [evento async for evento in primeiro]
        await _encerrar(porta)
        return [entregue, *resto], segundo

    primeiro, segundo = executar(cenario())

    _gramatica(primeiro)
    assert segundo == [FalhaDoTurno(M.TURNO_EM_ANDAMENTO)]


def test_fechar_e_idempotente_e_depois_tudo_e_sessao_fechada(implementacao):
    fabricar, quem = implementacao

    async def cenario():
        porta = fabricar()
        sessao = await porta.abrir(quem, contexto_novo())
        await coletar(porta.enviar(sessao, PEDIDO))
        await porta.fechar(sessao)
        await porta.fechar(sessao)
        depois = await coletar(porta.enviar(sessao, PEDIDO))
        await _encerrar(porta)
        return depois

    assert executar(cenario()) == [FalhaDoTurno(M.SESSAO_FECHADA)]


def test_fechar_sessao_que_nunca_conectou(implementacao):
    fabricar, quem = implementacao

    async def cenario():
        porta = fabricar()
        sessao = await porta.abrir(quem, contexto_novo())
        await porta.fechar(sessao)
        depois = await coletar(porta.enviar(sessao, PEDIDO))
        await _encerrar(porta)
        return depois

    assert executar(cenario()) == [FalhaDoTurno(M.SESSAO_FECHADA)]


def test_r10_abrir_recusa_sub_agente_com_ferramenta_de_ambiente(implementacao):
    fabricar, _ = implementacao

    async def cenario():
        porta = fabricar()
        try:
            with pytest.raises(ConfiguracaoDeSessaoInvalida):
                await porta.abrir(Agente("bibliotecario", Papel.SUB_AGENTE, "m", ferramentas=("criar_etapa",)), contexto_novo())
        finally:
            await _encerrar(porta)

    executar(cenario())


def test_esc_e_so_cancelamento(implementacao):
    """Cancelar quem le nao vira evento nem excecao alem do cancelamento, e a
    sessao continua usavel."""
    fabricar, quem = implementacao

    async def cenario():
        porta = fabricar()
        sessao = await porta.abrir(quem, contexto_novo())
        iterador = porta.enviar(sessao, PEDIDO)
        await anext(iterador)
        await iterador.aclose()
        depois = await coletar(porta.enviar(sessao, PEDIDO))
        await _encerrar(porta)
        return depois

    depois = executar(cenario())

    _gramatica(depois)
    assert depois[-1] == FimDeTurno()


def test_os_tres_implementam_a_porta():
    for classe in (SessaoFalsa, AdaptadorSessaoClaude):
        for operacao in ("abrir", "enviar", "fechar", "encerrar"):
            assert callable(getattr(classe, operacao))
    assert inspect.iscoroutinefunction(AdaptadorSessaoClaude.abrir)
    assert inspect.isasyncgenfunction(AdaptadorSessaoClaude.enviar)
    assert inspect.isasyncgenfunction(SessaoFalsa.enviar)
