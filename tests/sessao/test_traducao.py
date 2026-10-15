"""U6 - o tradutor puro (RN-S-17..24, DP-S-10, DP-S-19, PBT-U6-01 e 02).

Sem asyncio e sem processo: o tradutor recebe as mensagens do SDK, uma a uma,
e devolve eventos e avisos. As mensagens sao os tipos de verdade do SDK.
"""

import logging

from claude_agent_sdk import ServerToolUseBlock, TextBlock, ThinkingBlock, ToolUseBlock
from hypothesis import given, settings
from hypothesis import strategies as st

from fishingrod.adaptadores.sessao.falhas import Classificacao, Fase, FimSemResultado
from fishingrod.adaptadores.sessao.traducao import SEPARADOR, Tradutor
from fishingrod.aplicacao.portas.sessao import (
    Familia,
    FimDeTurno,
    MotivoFalhaDeSessao as M,
    PedacoDeTexto,
    UsoDeFerramenta,
)
from tests.sessao.cliente_roteirizado import (
    Acabar,
    Levantar,
    Mensagem,
    assistente,
    inicio_de_ferramenta,
    inicio_de_mensagem,
    inicio_de_texto,
    limite,
    pedido,
    pensamento,
    resultado,
    resultado_de_ferramenta,
    sistema,
    trecho,
    trecho_de_ferramenta,
    trecho_de_pensamento,
)
from tests.sessao.estrategias import (
    BEM,
    COM_ERRO,
    EXCECAO,
    FIM_DO_FLUXO,
    SINAL,
    blocos_de_texto,
    partido,
    passos_de_bloco,
    roteiros,
)
from tests.sessao.test_falhas import esperado

DA_SESSAO = {(Familia.WIKI, "ler"), (Familia.AMBIENTE, "criar_etapa")}


def _traduzir(*mensagens, tradutor: Tradutor | None = None):
    tradutor = tradutor or Tradutor(DA_SESSAO)
    eventos, avisos = [], []
    for mensagem in mensagens:
        traducao = tradutor.traduzir(mensagem)
        eventos += traducao.eventos
        avisos += traducao.avisos
    return eventos, avisos, tradutor


def _texto(eventos) -> str:
    return "".join(e.texto for e in eventos if isinstance(e, PedacoDeTexto))


# --------------------------------------------------------------------------
# RN-S-19, RN-S-20: o texto
# --------------------------------------------------------------------------


def test_rn_s_19_sem_trecho_nenhum_o_bloco_inteiro_vira_um_pedaco():
    eventos, avisos, _ = _traduzir(assistente(TextBlock("Olá, Pedro.")))

    assert eventos == [PedacoDeTexto("Olá, Pedro.")]
    assert avisos == []


def test_rn_s_19_trechos_que_cobrem_o_bloco_e_nada_mais_sai():
    eventos, _, _ = _traduzir(inicio_de_texto(0), trecho(0, "Olá, "), trecho(0, "Pedro."), assistente(TextBlock("Olá, Pedro.")))

    assert eventos == [PedacoDeTexto("Olá, "), PedacoDeTexto("Pedro.")]


def test_rn_s_19_trechos_que_cobrem_so_o_comeco_e_sai_o_que_falta():
    eventos, _, _ = _traduzir(inicio_de_texto(0), trecho(0, "Olá"), assistente(TextBlock("Olá, Pedro.")))

    assert eventos == [PedacoDeTexto("Olá"), PedacoDeTexto(", Pedro.")]


def test_rn_s_19_trechos_divergentes_viram_aviso_e_nada_mais_sai_daquele_bloco():
    eventos, avisos, _ = _traduzir(
        inicio_de_texto(0), trecho(0, "Oi"), assistente(TextBlock("Olá, Pedro.")), assistente(TextBlock("Depois."))
    )

    assert eventos == [PedacoDeTexto("Oi"), PedacoDeTexto(SEPARADOR + "Depois.")]
    assert [a.nivel for a in avisos] == [logging.WARNING]
    assert "Pedro" not in avisos[0].mensagem % avisos[0].argumentos


def test_rn_s_19_trecho_vazio_nunca_vira_pedaco():
    eventos, _, _ = _traduzir(inicio_de_texto(0), trecho(0, ""), assistente(TextBlock("")), assistente(TextBlock("a")))

    assert eventos == [PedacoDeTexto("a")]


def test_rn_s_20_linha_em_branco_entre_blocos_mesmo_com_ferramenta_no_meio():
    eventos, _, _ = _traduzir(
        assistente(TextBlock("Vou criar a etapa.")),
        pedido("mcp__ambiente__criar_etapa", {"executor": "usuario"}),
        inicio_de_mensagem(),
        inicio_de_texto(0),
        trecho(0, "Pron"),
        assistente(TextBlock("Pronto.")),
    )

    assert eventos == [
        PedacoDeTexto("Vou criar a etapa."),
        UsoDeFerramenta(Familia.AMBIENTE, "criar_etapa", {"executor": "usuario"}),
        PedacoDeTexto(SEPARADOR + "Pron"),
        PedacoDeTexto("to."),
    ]


# --------------------------------------------------------------------------
# RN-S-21..23: o que nao vira evento
# --------------------------------------------------------------------------


def test_rn_s_21_raciocinio_nao_vira_evento():
    eventos, avisos, _ = _traduzir(
        trecho_de_pensamento(0), pensamento(), assistente(ThinkingBlock(thinking="segredo", signature="s"))
    )

    assert eventos == [] and avisos == []


def test_rn_s_23_resultado_de_ferramenta_e_sistema_nao_viram_evento():
    eventos, avisos, _ = _traduzir(resultado_de_ferramenta(), sistema("init"), sistema("compact_boundary"), limite("allowed"), limite("allowed_warning"))

    assert eventos == [] and avisos == []


def test_rn_s_22_uso_de_ferramenta_sai_do_bloco_completo_e_nunca_do_trecho():
    eventos, _, _ = _traduzir(
        inicio_de_ferramenta(0, "mcp__wiki__ler"),
        trecho_de_ferramenta(0, '{"chave": "pa'),
        pedido("mcp__wiki__ler", {"chave": "pagina"}),
    )

    assert eventos == [UsoDeFerramenta(Familia.WIKI, "ler", {"chave": "pagina"})]


def test_rn_s_22_pedido_de_fora_da_sessao_vira_aviso_e_nao_evento():
    eventos, avisos, _ = _traduzir(
        pedido("mcp__ambiente__criar_frente"),
        pedido("Bash", {"command": "rm -rf /"}),
        pedido("mcp__wiki__" + "x" * 500),
        assistente(ServerToolUseBlock(id="s", name="web_search", input={})),
    )

    assert eventos == []
    assert [a.nivel for a in avisos] == [logging.WARNING] * 4
    assert all(len(a.mensagem % a.argumentos) < 200 for a in avisos)
    assert all("rm -rf" not in a.mensagem % a.argumentos for a in avisos)


def test_rn_s_22_argumentos_que_nao_sao_objeto_viram_objeto_vazio():
    eventos, _, _ = _traduzir(assistente(ToolUseBlock(id="t", name="mcp__wiki__ler", input="lixo")))

    assert eventos == [UsoDeFerramenta(Familia.WIKI, "ler", {})]


# --------------------------------------------------------------------------
# RN-S-24, DP-S-10: o evento final
# --------------------------------------------------------------------------


def _resultado(erro=False):
    return resultado(erro=erro).mensagem


def test_rn_s_24_sem_texto_nem_uso_e_resposta_vazia():
    _, _, tradutor = _traduzir(pensamento(), sistema())

    final = tradutor.final(_resultado())

    assert isinstance(final, Classificacao) and final.motivo is M.RESPOSTA_VAZIA and final.derruba is False


def test_rn_s_24_so_uso_de_ferramenta_ja_e_fim_de_turno():
    _, _, tradutor = _traduzir(pedido("mcp__wiki__ler"))

    assert tradutor.final(_resultado()) == FimDeTurno()


def test_rn_s_24_pedido_de_fora_nao_conta_como_resposta():
    _, _, tradutor = _traduzir(pedido("Bash"))

    assert tradutor.final(_resultado()).motivo is M.RESPOSTA_VAZIA


def test_dp_s_10_o_conteudo_de_uma_mensagem_com_erro_nao_vira_pedaco():
    eventos, _, tradutor = _traduzir(assistente(TextBlock("Please run /login"), erro="authentication_failed"))

    assert eventos == []
    assert tradutor.final(_resultado(erro=True)).motivo is M.NAO_AUTENTICADO


def test_dp_s_10_o_primeiro_sinal_vence():
    _, _, tradutor = _traduzir(assistente(erro="server_error"), assistente(erro="authentication_failed"), assistente(TextBlock("a")))

    assert tradutor.final(_resultado()).motivo is M.INDISPONIVEL


def test_dp_s_10_limite_depois_de_rate_limit_traz_quando_libera():
    _, _, tradutor = _traduzir(assistente(erro="rate_limit"), limite("rejected", resets_at=1_767_225_600))

    final = tradutor.final(_resultado(erro=True))

    assert final.motivo is M.LIMITE_DE_USO and final.derruba is False
    assert final.detalhe == {"libera_em": "2026-01-01T00:00:00+00:00"}


def test_n6_resultado_com_erro_sem_sinal_e_falha_inesperada():
    _, _, tradutor = _traduzir(assistente(TextBlock("a")))

    final = tradutor.final(_resultado(erro=True))

    assert final.motivo is M.FALHA_INESPERADA and final.derruba is True
    assert tradutor.sinal is not None  # o log diz qual


def test_dp_s_10_na_queda_o_sinal_anterior_vence_e_derruba():
    _, _, tradutor = _traduzir(assistente(erro="rate_limit"))

    queda = tradutor.queda(Fase.RESPOSTA, FimSemResultado())

    assert queda.motivo is M.LIMITE_DE_USO and queda.derruba is True


# --------------------------------------------------------------------------
# PBT-U6-01: a gramatica, no tradutor puro
# --------------------------------------------------------------------------


def _motivo_esperado(roteiro):
    """O oraculo: a tabela literal de test_falhas.py e RN-S-24."""
    if roteiro.desfecho == BEM:
        return None if roteiro.tem_resposta else M.RESPOSTA_VAZIA
    if roteiro.desfecho == COM_ERRO:
        return M.FALHA_INESPERADA
    if roteiro.desfecho == SINAL:
        return M.LIMITE_DE_USO if roteiro.sinal in ("rejected", "rate_limit") else esperado(
            Fase.RESPOSTA, _como_causa(roteiro.sinal)
        ).motivo
    if roteiro.desfecho == EXCECAO:
        return esperado(Fase.RESPOSTA, roteiro.excecao).motivo
    return M.INDISPONIVEL


def _como_causa(sinal):
    from fishingrod.adaptadores.sessao.falhas import ErroDoAssistente

    return ErroDoAssistente(sinal)


@settings(max_examples=200)
@given(roteiros(da_sessao=("mcp__wiki__ler", "mcp__ambiente__criar_etapa")))
def test_pbt_u6_01_gramatica_do_turno_no_tradutor(roteiro):
    tradutor = Tradutor(DA_SESSAO)
    eventos = []
    final = None
    for passo in roteiro.passos:
        match passo:
            case Mensagem(mensagem=mensagem) if type(mensagem).__name__ == "ResultMessage":
                final = tradutor.final(mensagem)
                break
            case Mensagem(mensagem=mensagem):
                eventos += tradutor.traduzir(mensagem).eventos
            case Levantar(excecao=excecao):
                final = tradutor.queda(Fase.RESPOSTA, excecao)
                break
            case Acabar():
                final = tradutor.queda(Fase.RESPOSTA, FimSemResultado())
                break

    assert all(isinstance(e, (PedacoDeTexto, UsoDeFerramenta)) for e in eventos)
    assert all(e.texto for e in eventos if isinstance(e, PedacoDeTexto))
    if isinstance(final, FimDeTurno):
        assert eventos, "FimDeTurno so com texto ou uso de ferramenta"
    motivo = None if isinstance(final, FimDeTurno) else final.motivo
    assert motivo is _motivo_esperado(roteiro)
    # RN-S-22: um uso por pedido da sessao, na ordem.
    usos = [f"mcp__{e.familia.value}__{e.nome}" for e in eventos if isinstance(e, UsoDeFerramenta)]
    assert usos == list(roteiro.usos)
    if roteiro.desfecho != SINAL:
        assert _texto(eventos) == SEPARADOR.join(t for t in roteiro.textos)


# --------------------------------------------------------------------------
# PBT-U6-02: texto preservado
# --------------------------------------------------------------------------


@st.composite
def turnos_de_texto(draw):
    """Blocos Unicode, cada um partido em trechos de qualquer jeito - o bloco
    todo, so o comeco, nenhum -, com pedidos de ferramenta entre eles."""
    blocos = draw(st.lists(blocos_de_texto, min_size=1, max_size=4))
    mensagens = []
    for indice, texto in enumerate(blocos):
        mensagens += [p.mensagem for p in passos_de_bloco(indice, texto, draw(partido(texto)))]
        if draw(st.booleans()):
            mensagens.append(pedido("mcp__wiki__ler", {"chave": "x"}))
    return blocos, mensagens


@settings(max_examples=200)
@given(turnos_de_texto())
def test_pbt_u6_02_texto_preservado(gerado):
    blocos, mensagens = gerado

    eventos, avisos, _ = _traduzir(*mensagens)

    pedacos = [e for e in eventos if isinstance(e, PedacoDeTexto)]
    assert all(p.texto for p in pedacos)
    assert _texto(eventos) == SEPARADOR.join(blocos)
    assert avisos == []


@st.composite
def divergencias(draw):
    """Um bloco e trechos que comecam iguais e divergem num ponto sorteado -
    construidos assim, e nao filtrados (medido no passo 25: com filtro, metade
    dos exemplos era descartada)."""
    antes = draw(blocos_de_texto)
    corte = draw(st.integers(0, len(antes)))
    outro = draw(st.characters(exclude_categories=("Cs",)).filter(lambda c: corte == len(antes) or c != antes[corte]))
    divergente = antes[:corte] + outro + draw(st.text(max_size=5))
    if corte == len(antes):
        divergente = antes + outro  # passou do fim do bloco: tambem diverge
    return antes, divergente


@settings(max_examples=100)
@given(divergencias(), blocos_de_texto)
def test_pbt_u6_02_trechos_divergentes_devolvem_aviso_e_param_o_bloco(gerado, depois):
    """O que ja saiu, saiu; nada mais sai daquele bloco, e o seguinte segue."""
    antes, divergente = gerado
    assert not antes.startswith(divergente)
    eventos, avisos, _ = _traduzir(
        inicio_de_texto(0), trecho(0, divergente), assistente(TextBlock(antes)), assistente(TextBlock(depois))
    )

    assert _texto(eventos) == divergente + SEPARADOR + depois
    assert len(avisos) == 1 and avisos[0].nivel == logging.WARNING
