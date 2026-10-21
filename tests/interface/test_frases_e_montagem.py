"""As frases da tela e a montagem do programa (card 001)."""

import asyncio
from datetime import UTC, date, datetime, timedelta

from fishingrod.aplicacao.catalogo.tipos import MotivoFalha, Resultado
from fishingrod.dominio import Memoria
from fishingrod.interface.frases import MEMORIA_VAZIA, frase_da_falha, quando, texto_da_memoria
from fishingrod.interface.montagem import BIBLIOTECARIO, ORQUESTRADOR, ConfirmacaoRecusada, montar


def test_quando_conta_os_dias_no_dia_local():
    hoje = date(2026, 10, 21)
    meio_dia = datetime(2026, 10, 21, 12, tzinfo=UTC)

    assert quando(meio_dia, hoje) == "mexido hoje"
    assert quando(meio_dia - timedelta(days=1), hoje) == "mexido ontem"
    assert quando(meio_dia - timedelta(days=3), hoje) == "mexido há 3 dias"


def test_memoria_em_markdown_por_assunto_e_na_ordem_de_escrita():
    memoria = Memoria()
    assert texto_da_memoria(memoria) == MEMORIA_VAZIA

    memoria.anotar("icp", "dentistas", "orquestrador")
    memoria.anotar("tom", "formal", "usuario")
    memoria.anotar("icp", "clínicas pequenas", "bibliotecario")
    texto = texto_da_memoria(memoria)

    assert texto.index("### icp") < texto.index("dentistas") < texto.index("clínicas pequenas")
    assert texto.index("clínicas pequenas") < texto.index("### tom")
    assert "*bibliotecario," in texto


def test_toda_falha_vira_uma_frase():
    for motivo in MotivoFalha:
        assert frase_da_falha(Resultado.falha(motivo)).strip()

    longo = Resultado.falha(MotivoFalha.ARGUMENTO_INVALIDO, problema="longo_demais", maximo=200)
    assert frase_da_falha(longo) == "O nome passa de 200 caracteres."
    sumiu = Resultado.falha(MotivoFalha.ALVO_INEXISTENTE, alvo="sessao")
    assert "a sessão" in frase_da_falha(sumiu)


def test_o_orquestrador_tem_as_ferramentas_do_agente_e_nao_abre_sessao():
    assert ORQUESTRADOR.e_orquestrador and not BIBLIOTECARIO.e_orquestrador
    assert "criar_frente" in ORQUESTRADOR.ferramentas
    assert "criar_sessao" not in ORQUESTRADOR.ferramentas


def test_pedido_de_agente_na_tela_e_recusado():
    assert asyncio.run(ConfirmacaoRecusada().confirmar(None)) is False


def test_montar_abre_o_banco_na_pasta_de_dados(tmp_path):
    async def cenario():
        programa = await montar(tmp_path)
        try:
            return await programa.servico.listar_ambientes(), programa.agentes
        finally:
            await programa.fechar()

    ambientes, agentes = asyncio.run(cenario())

    assert ambientes == []
    assert agentes == (ORQUESTRADOR, BIBLIOTECARIO)
    assert (tmp_path / "fishingrod.db").is_file()
