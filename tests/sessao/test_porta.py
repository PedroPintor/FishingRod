"""U6 - a porta: validar_mensagem e a imutabilidade dos tipos (RN-S-02, RN-S-25, DP-S-20)."""

import dataclasses

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from fishingrod.aplicacao.portas.sessao import (
    MAXIMO_DE_CARACTERES,
    AdaptadorEncerrado,
    ConfiguracaoDeSessaoInvalida,
    ContextoDaSessao,
    ErroDeSessao,
    FalhaDoTurno,
    Familia,
    FimDeTurno,
    MensagemEntregue,
    MotivoFalhaDeSessao,
    PedacoDeTexto,
    RegistroInvalido,
    SessaoViva,
    UsoDeFerramenta,
    validar_mensagem,
)
from fishingrod.dominio import Identidade
from tests.sessao.estrategias import ESPACOS


def _invalida(problema: str, **mais: str) -> FalhaDoTurno:
    return FalhaDoTurno(MotivoFalhaDeSessao.MENSAGEM_INVALIDA, {"problema": problema, **mais})


# --------------------------------------------------------------------------
# validar_mensagem (RN-S-25, G4)
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "texto",
    ["", " ", "\t\n", " ", " ", "\x1c\x1d\x1e\x1f", " " * 200_000],
    ids=["vazio", "espaco", "tab-e-linha", "nao-separavel", "separador-de-linha", "separadores", "duzentos-mil"],
)
def test_rn_s_25_mensagem_so_de_espacos_e_vazia(texto):
    assert validar_mensagem(texto) == _invalida("vazia")


def test_rn_s_25_o_que_nao_e_texto_conta_como_vazia():
    for coisa in (None, 42, b"oi", ["oi"]):
        assert validar_mensagem(coisa) == _invalida("vazia")


def test_rn_s_25_o_teto_e_100_000_caracteres():
    assert MAXIMO_DE_CARACTERES == 100_000
    assert validar_mensagem("a" * 100_000) is None
    assert validar_mensagem("a" * 100_001) == _invalida("longa_demais", maximo="100000")


def test_rn_s_25_espaco_nas_pontas_nao_invalida():
    assert validar_mensagem("  oi  ") is None


@settings(max_examples=300)
@given(st.text(st.sampled_from(ESPACOS), max_size=40))
def test_pbt_u6_12_so_espacos_nunca_sai(texto):
    """PBT-U6-12 na funcao: qualquer caractere para o qual str.isspace() e
    verdadeiro, em qualquer quantidade."""
    assert validar_mensagem(texto) == _invalida("vazia")


@settings(max_examples=300)
@given(st.integers(min_value=100_001, max_value=100_100), st.characters(exclude_categories=("Cs", "Zs", "Zl", "Zp", "Cc")))
def test_pbt_u6_12_longa_demais_nunca_sai(tamanho, caractere):
    assert validar_mensagem(caractere * tamanho) == _invalida("longa_demais", maximo="100000")


@given(st.text(min_size=1, max_size=200).filter(lambda t: t.strip()))
def test_pbt_u6_12_o_resto_sai(texto):
    assert validar_mensagem(texto) is None


# --------------------------------------------------------------------------
# Os tipos sao imutaveis (RN-S-02)
# --------------------------------------------------------------------------


def _viva() -> SessaoViva:
    contexto = ContextoDaSessao(*(Identidade.nova() for _ in range(5)))
    return SessaoViva(Identidade.nova(), "orquestrador", contexto)


@pytest.mark.parametrize(
    "objeto, campo",
    [
        (_viva(), "nome_agente"),
        (_viva().contexto, "id_chat"),
        (MensagemEntregue(True), "conversa_nova"),
        (PedacoDeTexto("oi"), "texto"),
        (UsoDeFerramenta(Familia.AMBIENTE, "criar_etapa", {}), "nome"),
        (FalhaDoTurno(MotivoFalhaDeSessao.INDISPONIVEL), "motivo"),
    ],
)
def test_rn_s_02_os_tipos_da_porta_nao_mudam(objeto, campo):
    with pytest.raises(dataclasses.FrozenInstanceError):
        setattr(objeto, campo, None)


def test_rn_s_02_argumentos_do_uso_sao_copia_funda_somente_leitura():
    original = {"lista": [1, 2], "texto": "a"}
    uso = UsoDeFerramenta(Familia.WIKI, "ler", original)

    original["lista"].append(3)
    original["novo"] = "x"

    assert uso.argumentos == {"lista": [1, 2], "texto": "a"}
    with pytest.raises(TypeError):
        uso.argumentos["texto"] = "b"


def test_rn_s_31_detalhe_da_falha_e_somente_leitura_de_texto_para_texto():
    falha = FalhaDoTurno(MotivoFalhaDeSessao.LIMITE_DE_USO, {"libera_em": "2026-10-13T00:00:00+00:00"})

    with pytest.raises(TypeError):
        falha.detalhe["libera_em"] = "outro"
    with pytest.raises(ValueError):
        FalhaDoTurno(MotivoFalhaDeSessao.LIMITE_DE_USO, {"libera_em": 3})
    with pytest.raises(ValueError):
        FalhaDoTurno("limite_de_uso")


def test_pedaco_de_texto_nunca_e_vazio():
    with pytest.raises(ValueError):
        PedacoDeTexto("")


def test_os_nove_motivos_e_as_duas_familias():
    assert [m.value for m in MotivoFalhaDeSessao] == [
        "provedor_ausente",
        "nao_autenticado",
        "limite_de_uso",
        "indisponivel",
        "resposta_vazia",
        "mensagem_invalida",
        "turno_em_andamento",
        "sessao_fechada",
        "falha_inesperada",
    ]
    assert [f.value for f in Familia] == ["ambiente", "wiki"]
    assert FimDeTurno() == FimDeTurno()


def test_os_erros_de_montagem_tem_uma_raiz():
    for erro in (ConfiguracaoDeSessaoInvalida, AdaptadorEncerrado, RegistroInvalido):
        assert issubclass(erro, ErroDeSessao)
    assert ConfiguracaoDeSessaoInvalida("x", ("v",)).violacoes == ("v",)
