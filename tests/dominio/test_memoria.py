"""U1 - Memoria (RN-09, RN-10, PBT-U1-03, PBT-U1-04). Mata TD-03."""

from datetime import UTC

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from fishingrod.dominio import Memoria, NomeInvalido

texto_nao_vazio = st.text(min_size=1).filter(lambda s: s.strip())


def test_rn_09_anotar_em_chave_inedita_nao_levanta():
    """TD-03: o codigo atual faz anotacoes[chave].append(...) e estoura
    KeyError na primeira escrita de uma chave nova."""
    memoria = Memoria()

    memoria.anotar(chave="plano", valor="descobrir o publico", autor="orquestrador")

    assert len(memoria.anotacoes["plano"]) == 1
    assert memoria.versao == 1


def test_rn_09_anotacoes_na_mesma_chave_acumulam_em_ordem():
    """US-04, segundo criterio de aceite: nao se substituem."""
    memoria = Memoria()

    memoria.anotar("plano", "primeira", "orquestrador")
    memoria.anotar("plano", "segunda", "usuario")

    valores = [a.valor for a in memoria.anotacoes["plano"]]
    assert valores == ["primeira", "segunda"]
    assert memoria.versao == 2


def test_rn_10_anotacao_carrega_carimbo_em_utc():
    memoria = Memoria()

    anotacao = memoria.anotar("chave", "valor", "autor")

    assert anotacao.criada_em.tzinfo is not None
    assert anotacao.criada_em.utcoffset() == UTC.utcoffset(None)


@pytest.mark.parametrize("chave,autor", [("", "autor"), ("   ", "autor"), ("chave", ""), ("chave", "\t")])
def test_rn_02_chave_ou_autor_vazio_levanta(chave, autor):
    with pytest.raises(NomeInvalido):
        Memoria().anotar(chave=chave, valor="qualquer", autor=autor)


@given(entradas=st.lists(st.tuples(texto_nao_vazio, st.text(), texto_nao_vazio), max_size=40))
@settings(max_examples=50)
def test_pbt_u1_03_anotar_nunca_levanta_e_conta_bate(entradas):
    memoria = Memoria()

    for chave, valor, autor in entradas:
        memoria.anotar(chave=chave, valor=valor, autor=autor)

    assert memoria.total_de_anotacoes() == len(entradas)


@given(entradas=st.lists(st.tuples(texto_nao_vazio, st.text(), texto_nao_vazio), max_size=40))
@settings(max_examples=50)
def test_pbt_u1_04_versao_conta_escritas(entradas):
    memoria = Memoria()

    for chave, valor, autor in entradas:
        memoria.anotar(chave=chave, valor=valor, autor=autor)

    assert memoria.versao == len(entradas)
