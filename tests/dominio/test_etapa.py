"""U1 - Etapa (RN-07, RN-08, PBT-U1-05)."""

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from fishingrod.dominio import Etapa, ExecutorEtapa, NomeInvalido


def test_rn_07_concluir_e_reabrir_sao_idempotentes():
    etapa = Etapa(descricao="mapear concorrentes", executor=ExecutorEtapa.AGENTE)
    assert etapa.concluida is False

    etapa.concluir()
    etapa.concluir()
    assert etapa.concluida is True

    etapa.reabrir()
    etapa.reabrir()
    assert etapa.concluida is False


@pytest.mark.parametrize("descricao", ["", "   ", "\n"])
def test_rn_02_descricao_vazia_levanta(descricao):
    with pytest.raises(NomeInvalido):
        Etapa(descricao=descricao, executor=ExecutorEtapa.USUARIO)


@given(chamadas=st.lists(st.booleans(), max_size=30))
@settings(max_examples=50)
def test_pbt_u1_05_estado_reflete_a_ultima_chamada(chamadas):
    """True = concluir, False = reabrir. Qualquer sequencia termina no estado
    da ultima chamada - e essa a definicao de idempotencia aqui."""
    etapa = Etapa(descricao="passo", executor=ExecutorEtapa.AGENTE)

    for concluir in chamadas:
        etapa.concluir() if concluir else etapa.reabrir()

    esperado = chamadas[-1] if chamadas else False
    assert etapa.concluida is esperado
