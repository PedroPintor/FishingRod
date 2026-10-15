"""U6 - a tabela de falhas (DP-S-09, N6, RN-S-28..31, PBT-U6-03 na funcao).

A tabela do §4 de nfr-design-patterns.md esta aqui como DADO LITERAL, e e o
oraculo das propriedades de ponta a ponta (test_propriedades.py): elas comparam
com `esperado`, nunca com `classificar`. Um oraculo que chama o codigo testado
nao testa nada.
"""

import logging
from dataclasses import dataclass
from typing import Any

import pytest
from claude_agent_sdk import CLIConnectionError, CLIJSONDecodeError, CLINotFoundError, ProcessError
from claude_agent_sdk._errors import ResultError
from hypothesis import given, settings
from hypothesis import strategies as st

from fishingrod.adaptadores.sessao.falhas import (
    RESPOSTA_VAZIA,
    Aviso,
    CliAusente,
    Classificacao,
    ErroDoAssistente,
    Fase,
    FimSemResultado,
    LimiteAtingido,
    PrazoVencido,
    ResultadoComErro,
    classificar,
)
from fishingrod.aplicacao.portas.sessao import FalhaDoTurno, MotivoFalhaDeSessao as M

WARNING, ERROR = logging.WARNING, logging.ERROR
TODAS = frozenset(Fase)
DEPOIS_DE_SUBIR = frozenset({Fase.ENTREGA, Fase.RESPOSTA})
SDK_DE_CONEXAO = (CLIConnectionError, ProcessError, CLIJSONDecodeError)


@dataclass(frozen=True)
class Linha:
    fases: frozenset[Fase]
    casa: Any  # causa -> bool
    motivo: M
    derruba: bool
    nivel: int
    com_pilha: bool = False


def _sinal(*tipos: str):
    return lambda causa: isinstance(causa, ErroDoAssistente) and causa.tipo in tipos


def _tipo(*tipos: type):
    return lambda causa: isinstance(causa, tipos)


# A tabela, linha por linha, na ordem: a primeira que casa decide.
TABELA = (
    Linha(TODAS, _tipo(CliAusente), M.PROVEDOR_AUSENTE, True, WARNING),
    Linha(frozenset({Fase.SUBIDA}), _tipo(CLINotFoundError), M.PROVEDOR_AUSENTE, True, WARNING),
    Linha(TODAS, _sinal("authentication_failed"), M.NAO_AUTENTICADO, True, WARNING),
    Linha(TODAS, _sinal("rate_limit"), M.LIMITE_DE_USO, False, WARNING),
    Linha(TODAS, _tipo(LimiteAtingido), M.LIMITE_DE_USO, False, WARNING),
    Linha(TODAS, _sinal("billing_error", "server_error", "unknown"), M.INDISPONIVEL, True, WARNING),
    Linha(TODAS, _tipo(ErroDoAssistente), M.FALHA_INESPERADA, True, ERROR),  # invalid_request e desconhecidos
    Linha(TODAS, _tipo(ResultadoComErro), M.FALHA_INESPERADA, True, ERROR),
    Linha(TODAS, _tipo(FimSemResultado, PrazoVencido), M.INDISPONIVEL, True, WARNING),
    Linha(frozenset({Fase.SUBIDA}), lambda causa: True, M.INDISPONIVEL, True, WARNING, com_pilha=True),
    Linha(DEPOIS_DE_SUBIR, _tipo(*SDK_DE_CONEXAO), M.INDISPONIVEL, True, WARNING),
    Linha(DEPOIS_DE_SUBIR, lambda causa: True, M.FALHA_INESPERADA, True, ERROR, com_pilha=True),
)


def esperado(fase: Fase, causa: object) -> Linha:
    return next(linha for linha in TABELA if fase in linha.fases and linha.casa(causa))


# --------------------------------------------------------------------------
# Linha por linha
# --------------------------------------------------------------------------

CASOS = [
    (Fase.SUBIDA, CliAusente(), M.PROVEDOR_AUSENTE, True, WARNING, False),
    (Fase.SUBIDA, CLINotFoundError("x"), M.PROVEDOR_AUSENTE, True, WARNING, False),
    (Fase.SUBIDA, PrazoVencido(), M.INDISPONIVEL, True, WARNING, False),
    (Fase.SUBIDA, Exception("Control request timeout: initialize"), M.INDISPONIVEL, True, WARNING, True),
    (Fase.SUBIDA, CLIConnectionError("x"), M.INDISPONIVEL, True, WARNING, True),
    (Fase.SUBIDA, ProcessError("x", exit_code=1), M.INDISPONIVEL, True, WARNING, True),
    (Fase.SUBIDA, RuntimeError("x"), M.INDISPONIVEL, True, WARNING, True),
    (Fase.ENTREGA, ErroDoAssistente("authentication_failed"), M.NAO_AUTENTICADO, True, WARNING, False),
    (Fase.RESPOSTA, ErroDoAssistente("authentication_failed"), M.NAO_AUTENTICADO, True, WARNING, False),
    (Fase.RESPOSTA, ErroDoAssistente("rate_limit"), M.LIMITE_DE_USO, False, WARNING, False),
    (Fase.RESPOSTA, LimiteAtingido(None), M.LIMITE_DE_USO, False, WARNING, False),
    (Fase.RESPOSTA, ErroDoAssistente("billing_error"), M.INDISPONIVEL, True, WARNING, False),
    (Fase.RESPOSTA, ErroDoAssistente("server_error"), M.INDISPONIVEL, True, WARNING, False),
    (Fase.RESPOSTA, ErroDoAssistente("unknown"), M.INDISPONIVEL, True, WARNING, False),
    (Fase.RESPOSTA, ErroDoAssistente("invalid_request"), M.FALHA_INESPERADA, True, ERROR, False),
    (Fase.RESPOSTA, ErroDoAssistente("um_sinal_novo"), M.FALHA_INESPERADA, True, ERROR, False),
    (Fase.ENTREGA, CLIConnectionError("x"), M.INDISPONIVEL, True, WARNING, False),
    (Fase.ENTREGA, CLINotFoundError("x"), M.INDISPONIVEL, True, WARNING, False),
    (Fase.RESPOSTA, ProcessError("x"), M.INDISPONIVEL, True, WARNING, False),
    (Fase.RESPOSTA, ResultError("x", {"subtype": "error_during_execution"}), M.INDISPONIVEL, True, WARNING, False),
    (Fase.RESPOSTA, CLIJSONDecodeError("{", ValueError("x")), M.INDISPONIVEL, True, WARNING, False),
    (Fase.RESPOSTA, FimSemResultado(), M.INDISPONIVEL, True, WARNING, False),
    (Fase.RESPOSTA, ResultadoComErro("error_during_execution", 500), M.FALHA_INESPERADA, True, ERROR, False),
    (Fase.RESPOSTA, RuntimeError("defeito"), M.FALHA_INESPERADA, True, ERROR, True),
    (Fase.ENTREGA, KeyError("x"), M.FALHA_INESPERADA, True, ERROR, True),
    (Fase.RESPOSTA, Exception("Control request timeout: initialize"), M.FALHA_INESPERADA, True, ERROR, True),
]


@pytest.mark.parametrize("fase, causa, motivo, derruba, nivel, com_pilha", CASOS, ids=lambda v: getattr(v, "value", None) or type(v).__name__)
def test_dp_s_09_a_tabela_linha_por_linha(fase, causa, motivo, derruba, nivel, com_pilha):
    classificacao = classificar(fase, causa)

    assert (classificacao.motivo, classificacao.derruba, classificacao.nivel, classificacao.com_pilha) == (
        motivo,
        derruba,
        nivel,
        com_pilha,
    )
    linha = esperado(fase, causa)
    assert (linha.motivo, linha.derruba, linha.nivel, linha.com_pilha) == (motivo, derruba, nivel, com_pilha)


def test_rn_s_31_limite_de_uso_leva_libera_em_em_iso_utc():
    assert classificar(Fase.RESPOSTA, LimiteAtingido(1_767_225_600)).detalhe == {"libera_em": "2026-01-01T00:00:00+00:00"}
    assert classificar(Fase.RESPOSTA, LimiteAtingido(None)).detalhe == {}
    assert classificar(Fase.RESPOSTA, ErroDoAssistente("rate_limit")).detalhe == {}


@pytest.mark.parametrize("absurdo", [10**30, -(10**30), True, "amanha", 1.5])
def test_rn_s_31_instante_absurdo_some_em_vez_de_derrubar(absurdo):
    assert classificar(Fase.RESPOSTA, LimiteAtingido(absurdo)).detalhe == {}


def test_rn_s_31_nenhum_detalhe_carrega_conteudo():
    """Fora do limite de uso, o detalhe e vazio - a mensagem da excecao nunca
    chega ao evento."""
    for fase, causa, *_ in CASOS:
        if not isinstance(causa, LimiteAtingido):
            assert classificar(fase, causa).detalhe == {}


def test_resposta_vazia_mantem_a_conexao():
    assert RESPOSTA_VAZIA == Classificacao(M.RESPOSTA_VAZIA, derruba=False, nivel=WARNING)
    assert RESPOSTA_VAZIA.evento() == FalhaDoTurno(M.RESPOSTA_VAZIA)


def test_aviso_e_dado():
    aviso = Aviso(WARNING, "x [%s]", ("y",))

    assert (aviso.nivel, aviso.mensagem % aviso.argumentos) == (WARNING, "x [y]")


# --------------------------------------------------------------------------
# Total e pura
# --------------------------------------------------------------------------

_EXCECOES = st.sampled_from(
    [
        CLINotFoundError,
        CLIConnectionError,
        lambda: ProcessError("x", exit_code=2),
        lambda: ResultError("x", {}),
        lambda: CLIJSONDecodeError("x", ValueError()),
        Exception,
        RuntimeError,
        KeyError,
        OSError,
        ValueError,
        TimeoutError,
        ZeroDivisionError,
        UnicodeDecodeError.__new__,
    ]
).map(lambda fazer: fazer() if fazer is not UnicodeDecodeError.__new__ else UnicodeDecodeError("utf-8", b"\xff", 0, 1, "x"))
_SINAIS = st.one_of(
    st.just(CliAusente()),
    st.just(PrazoVencido()),
    st.just(FimSemResultado()),
    st.builds(ErroDoAssistente, st.one_of(st.sampled_from(["authentication_failed", "rate_limit", "billing_error", "server_error", "unknown", "invalid_request"]), st.text(max_size=10))),
    st.builds(LimiteAtingido, st.one_of(st.none(), st.integers(), st.booleans())),
    st.builds(ResultadoComErro, st.none() | st.text(max_size=5), st.none() | st.integers()),
)


@settings(max_examples=300)
@given(st.sampled_from(list(Fase)), st.one_of(_EXCECOES, _SINAIS, st.none(), st.text(max_size=5)))
def test_pbt_u6_03_a_tabela_e_total_e_bate_com_o_oraculo(fase, causa):
    classificacao = classificar(fase, causa)
    linha = esperado(fase, causa)

    assert isinstance(classificacao.motivo, M)
    assert (classificacao.motivo, classificacao.derruba, classificacao.nivel) == (linha.motivo, linha.derruba, linha.nivel)
    assert classificacao.nivel in (WARNING, ERROR)
    # RN-S-29: NAO_AUTENTICADO e LIMITE_DE_USO so com sinal tipado.
    if classificacao.motivo in (M.NAO_AUTENTICADO, M.LIMITE_DE_USO):
        assert isinstance(causa, (ErroDoAssistente, LimiteAtingido))
    assert classificacao.motivo not in (M.MENSAGEM_INVALIDA, M.TURNO_EM_ANDAMENTO, M.SESSAO_FECHADA, M.RESPOSTA_VAZIA)
