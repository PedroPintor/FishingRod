"""As frases da tela e a montagem do programa (card 001)."""

import asyncio
from datetime import UTC, date, datetime, timedelta

from fishingrod.aplicacao.catalogo.tipos import MotivoFalha, Resultado
from fishingrod.aplicacao.portas.sessao import MotivoFalhaDeSessao
from fishingrod.aplicacao.servicos.servico_de_conversa import ACAO_RECUSADA, CONVERSA_RECOMECOU, EstadoDoChat, aviso
from fishingrod.dominio import Memoria
from fishingrod.interface.frases import (
    MEMORIA_VAZIA,
    frase_da_falha,
    frase_das_conexoes,
    frase_do_aviso,
    frase_do_estado,
    quando,
    texto_da_memoria,
)
from fishingrod.interface.montagem import BIBLIOTECARIO, ORQUESTRADOR, PASTA_DO_CLAUDE, ConfirmacaoRecusada, montar


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


def test_todo_aviso_do_chat_vira_uma_frase():
    generica = frase_do_aviso("codigo-que-nao-existe")
    for motivo in MotivoFalhaDeSessao:
        assert frase_do_aviso(motivo.value).strip()
    assert frase_do_aviso(CONVERSA_RECOMECOU) == "Não consegui retomar a conversa; ela recomeça do zero."
    assert "criar_frente" in frase_do_aviso(aviso(ACAO_RECUSADA, "criar_frente"))
    assert frase_do_aviso(MotivoFalhaDeSessao.INDISPONIVEL.value) != generica


def test_o_limite_da_assinatura_diz_quando_libera():
    texto = aviso(MotivoFalhaDeSessao.LIMITE_DE_USO.value, "2026-10-21T18:30:00+00:00")

    assert frase_do_aviso(texto, UTC).endswith("Ele libera em 21/10 às 18:30.")
    assert frase_do_aviso(MotivoFalhaDeSessao.LIMITE_DE_USO.value) == "Você atingiu o limite da sua assinatura do Claude."


def test_a_faixa_e_o_mostrador():
    assert frase_do_estado(EstadoDoChat.RESPONDENDO, 2) == "● ligado · respondendo… · 2 na fila"
    assert frase_das_conexoes(1) == "Claude: 1 conexão aberta"
    assert frase_das_conexoes(2) == "Claude: 2 conexões abertas"


def test_montar_cria_a_pasta_do_claude_e_fechar_duas_vezes_nao_quebra(tmp_path):
    async def cenario():
        programa = await montar(tmp_path)
        await programa.fechar()
        await programa.fechar()

    asyncio.run(cenario())

    assert (tmp_path / PASTA_DO_CLAUDE).is_dir()
