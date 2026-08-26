"""U1 - Identidade (RN-01, PBT-U1-01, PBT-U1-02)."""

import uuid

from hypothesis import given, settings
from hypothesis import strategies as st

from fishingrod.dominio import Identidade


@given(quantidade=st.integers(min_value=2, max_value=200))
@settings(max_examples=25)
def test_pbt_u1_01_identidades_ordenam_por_criacao_e_nao_colidem(quantidade):
    """Ordenacao textual == ordem de criacao. E o que substitui uma coluna de
    ordenacao na paginacao de transcricao de U2 (ESC-14)."""
    valores = [Identidade.nova().valor for _ in range(quantidade)]

    assert valores == sorted(valores)
    assert len(set(valores)) == quantidade


@given(_=st.integers())
@settings(max_examples=25)
def test_pbt_u1_02_identidade_e_uuid_versao_7_canonico(_):
    identidade = Identidade.nova()

    parseado = uuid.UUID(identidade.valor)
    assert parseado.version == 7
    assert str(parseado) == identidade.valor


def test_rn_01_identidade_e_imutavel_e_comparavel_por_valor():
    a = Identidade.nova()
    copia = Identidade(valor=a.valor)

    assert a == copia
    assert hash(a) == hash(copia)
    assert {a: "usavel como chave"}[copia] == "usavel como chave"


def test_rn_01_identidades_diferentes_nao_sao_iguais():
    assert Identidade.nova() != Identidade.nova()
