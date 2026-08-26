"""U1 - politica de aprovacao (RN-12)."""

from fishingrod.dominio import Chamador, exige_aprovacao


def test_rn_12_agente_precisa_de_aprovacao():
    assert exige_aprovacao(Chamador.AGENTE) is True


def test_rn_12_usuario_executa_direto():
    """A politica governa apenas o chamador agente: /comando do usuario nao
    pede confirmacao."""
    assert exige_aprovacao(Chamador.USUARIO) is False
