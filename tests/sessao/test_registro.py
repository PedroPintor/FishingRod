"""U6 - o registro de ferramentas e a verificacao de escopo (RN-S-06..08, RN-S-13..15, PBT-U6-08)."""

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from fishingrod.aplicacao.catalogo import catalogo as catalogo_de_u5
from fishingrod.aplicacao.catalogo.catalogo import CatalogoDeAcoes
from fishingrod.aplicacao.ferramentas import (
    PADRAO_DE_NOME,
    EntradaDoRegistro,
    Ferramenta,
    RegistroDeFerramentas,
    Regra,
    Violacao,
)
from fishingrod.aplicacao.ferramentas.acoes import entradas_de_acoes
from fishingrod.aplicacao.portas.sessao import (
    ConfiguracaoDeSessaoInvalida,
    Familia,
    RegistroInvalido,
)
from fishingrod.dominio import Agente, Papel
from tests.sessao.estrategias import (
    BIBLIOTECARIO,
    NOMES_DAS_ACOES,
    NOMES_DE_WIKI,
    ORQUESTRADOR,
    agente,
    agentes_quaisquer,
    contexto_novo,
    fabrica_simples,
    registro_de_teste,
)

# --------------------------------------------------------------------------
# O registro (RN-S-13, RN-S-14)
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "nome", ["Criar", "criar-etapa", "criar__etapa", "_criar", "criar_", "criação", "", "1criar", "criar etapa", 7]
)
def test_rn_s_14_nome_fora_do_padrao_e_registro_invalido(nome):
    with pytest.raises(RegistroInvalido):
        RegistroDeFerramentas([EntradaDoRegistro(nome, Familia.WIKI, fabrica_simples("x"))])


def test_rn_s_13_nome_e_unico_entre_familias():
    with pytest.raises(RegistroInvalido):
        RegistroDeFerramentas(
            [
                EntradaDoRegistro("ler", Familia.WIKI, fabrica_simples("ler")),
                EntradaDoRegistro("ler", Familia.AMBIENTE, fabrica_simples("ler")),
            ]
        )


def test_rn_s_14_familia_desconhecida_ou_item_estranho_e_registro_invalido():
    with pytest.raises(RegistroInvalido):
        RegistroDeFerramentas([EntradaDoRegistro("ler", "wiki", fabrica_simples("ler"))])
    with pytest.raises(RegistroInvalido):
        RegistroDeFerramentas([("ler", Familia.WIKI)])
    with pytest.raises(RegistroInvalido):
        RegistroDeFerramentas([EntradaDoRegistro("ler", Familia.WIKI, None)])


def test_padrao_de_nome_e_o_mesmo_de_rn_ac_07():
    """O padrao foi repetido para registro.py nao carregar o catalogo; os dois
    precisam aceitar exatamente os mesmos nomes."""
    assert PADRAO_DE_NOME.pattern == catalogo_de_u5._NOME.pattern


@settings(max_examples=300)
@given(st.text(st.sampled_from("abz09_-A Ç"), max_size=12))
def test_padrao_de_nome_aceita_o_mesmo_que_o_catalogo(texto):
    assert bool(PADRAO_DE_NOME.fullmatch(texto)) == bool(catalogo_de_u5._NOME.fullmatch(texto))


def test_buscar_pelo_nome_sem_familia():
    registro = registro_de_teste()

    assert registro.buscar("criar_etapa").familia is Familia.AMBIENTE
    assert registro.buscar("ler").familia is Familia.WIKI
    assert registro.buscar("mcp__wiki__ler") is None
    assert registro.buscar(None) is None


# --------------------------------------------------------------------------
# preparar (RN-S-06..08, DP-S-21)
# --------------------------------------------------------------------------


def test_rn_s_08_preparar_fabrica_com_o_contexto_e_o_agente_e_agrupa_por_familia():
    recebidos = []

    def fabricar(nome):
        def fabrica(contexto, quem):
            recebidos.append((nome, contexto, quem))
            return Ferramenta(nome, "d", {"type": "object", "properties": {}}, None)

        return fabrica

    registro = RegistroDeFerramentas(
        [EntradaDoRegistro(n, f, fabricar(n)) for n, f in [("ler", Familia.WIKI), ("criar_etapa", Familia.AMBIENTE), ("listar", Familia.WIKI)]]
    )
    quem = agente("orquestrador", ferramentas=("listar", "criar_etapa", "ler"))
    contexto = contexto_novo()

    preparadas = registro.preparar(quem, contexto)

    assert list(preparadas) == [Familia.AMBIENTE, Familia.WIKI]
    assert [f.nome for f in preparadas[Familia.WIKI]] == ["listar", "ler"]
    assert [f.nome for f in preparadas[Familia.AMBIENTE]] == ["criar_etapa"]
    assert all(c is contexto and q is quem for _, c, q in recebidos)
    assert [n for n, _, _ in recebidos] == ["listar", "criar_etapa", "ler"]


def test_rn_s_08_sessao_sem_ferramenta_nao_tem_familia():
    assert dict(registro_de_teste().preparar(agente(), contexto_novo())) == {}


def _registro_com(fabrica) -> RegistroDeFerramentas:
    return RegistroDeFerramentas([EntradaDoRegistro("ler", Familia.WIKI, fabrica)])


def _abrir_com(fabrica):
    return _registro_com(fabrica).preparar(agente(ferramentas=("ler",)), contexto_novo())


def test_rn_s_08_fabrica_que_levanta_impede_a_abertura():
    def fabrica(contexto, quem):
        raise RuntimeError("quebrou")

    with pytest.raises(ConfiguracaoDeSessaoInvalida, match="falhou"):
        _abrir_com(fabrica)


def test_rn_s_08_fabrica_que_devolve_outro_nome_impede_a_abertura():
    with pytest.raises(ConfiguracaoDeSessaoInvalida, match="devolveu a ferramenta"):
        _abrir_com(fabrica_simples("listar"))


@pytest.mark.parametrize(
    "esquema",
    [{"type": "string"}, {"type": "object"}, {"type": "object", "properties": []}, {"properties": {}}],
)
def test_rn_s_08_esquema_que_nao_e_de_objeto_impede_a_abertura(esquema):
    """Sem `properties`, o SDK trocaria o esquema sem avisar (A17)."""
    with pytest.raises(ConfiguracaoDeSessaoInvalida, match="esquema"):
        _abrir_com(fabrica_simples("ler", esquema=esquema))


def test_rn_s_08_fabrica_que_nao_devolve_ferramenta_impede_a_abertura():
    with pytest.raises(ConfiguracaoDeSessaoInvalida):
        _abrir_com(lambda contexto, quem: "ler")


def test_rn_s_06_nome_desconhecido_ou_repetido_impede_a_abertura():
    registro = registro_de_teste()

    with pytest.raises(ConfiguracaoDeSessaoInvalida) as desconhecido:
        registro.preparar(agente(ferramentas=("ler", "apagar_tudo")), contexto_novo())
    with pytest.raises(ConfiguracaoDeSessaoInvalida) as repetido:
        registro.preparar(agente(ferramentas=("ler", "ler")), contexto_novo())

    assert desconhecido.value.violacoes == (Violacao("bibliotecario", "apagar_tudo", Regra.FERRAMENTA_DESCONHECIDA),)
    assert repetido.value.violacoes == (Violacao("bibliotecario", "ler", Regra.FERRAMENTA_REPETIDA),)


def test_rn_s_06_nenhuma_fabrica_roda_se_a_verificacao_falha():
    chamadas = []

    def fabrica(contexto, quem):
        chamadas.append(quem)
        return Ferramenta("ler", "d", {"type": "object", "properties": {}}, None)

    registro = _registro_com(fabrica)

    with pytest.raises(ConfiguracaoDeSessaoInvalida):
        registro.preparar(agente(ferramentas=("ler", "nao_existe")), contexto_novo())
    assert chamadas == []


# --------------------------------------------------------------------------
# R10 (RN-S-07, RN-S-15, criterio 6)
# --------------------------------------------------------------------------


def test_rn_s_07_sub_agente_com_ferramenta_de_ambiente_e_recusado():
    with pytest.raises(ConfiguracaoDeSessaoInvalida) as recusa:
        registro_de_teste().preparar(agente(ferramentas=("ler", "criar_etapa")), contexto_novo())

    assert recusa.value.violacoes == (Violacao("bibliotecario", "criar_etapa", Regra.ESCOPO_VIOLADO),)


def test_rn_s_07_orquestrador_recebe_as_de_ambiente_e_sub_agente_as_de_wiki():
    registro = registro_de_teste()

    assert registro.preparar(agente("orquestrador", ferramentas=NOMES_DAS_ACOES), contexto_novo())
    assert registro.preparar(agente(ferramentas=NOMES_DE_WIKI), contexto_novo())


def test_rn_s_15_verificar_escopo_junta_as_violacoes_de_uma_colecao():
    agentes = [
        agente("orquestrador", ferramentas=("criar_etapa", "criar_etapa")),
        agente(ferramentas=("ler", "anotar_memoria", "inexistente")),
    ]

    assert registro_de_teste().verificar_escopo(agentes) == (
        Violacao("orquestrador", "criar_etapa", Regra.FERRAMENTA_REPETIDA),
        Violacao("bibliotecario", "anotar_memoria", Regra.ESCOPO_VIOLADO),
        Violacao("bibliotecario", "inexistente", Regra.FERRAMENTA_DESCONHECIDA),
    )


def test_r10_com_os_6_nomes_reais():
    """As 6 acoes de verdade, vindas do catalogo de U5: nenhuma chega a um
    sub-agente, e o orquestrador recebe todas."""
    catalogo = CatalogoDeAcoes(servico=None, confirmacao=None)
    registro = RegistroDeFerramentas(entradas_de_acoes(catalogo))
    nomes = tuple(entrada.nome for entrada in registro.entradas)

    assert nomes == NOMES_DAS_ACOES
    violacoes = registro.verificar_escopo([BIBLIOTECARIO.__class__(BIBLIOTECARIO.nome, Papel.SUB_AGENTE, "m", ferramentas=nomes)])
    assert [v.regra for v in violacoes] == [Regra.ESCOPO_VIOLADO] * 6
    assert registro.verificar_escopo([Agente(ORQUESTRADOR.nome, Papel.ORQUESTRADOR, "m", ferramentas=nomes)]) == ()
    for nome in nomes:
        with pytest.raises(ConfiguracaoDeSessaoInvalida):
            registro.preparar(Agente("bibliotecario", Papel.SUB_AGENTE, "m", ferramentas=(nome,)), contexto_novo())


# --------------------------------------------------------------------------
# PBT-U6-08
# --------------------------------------------------------------------------


def _oraculo(quem: Agente) -> list[Violacao]:
    """Escrito a partir de RN-S-06 e RN-S-07, sem olhar o registro."""
    ambiente, wiki = set(NOMES_DAS_ACOES), set(NOMES_DE_WIKI)
    violacoes, vistos = [], set()
    for nome in quem.ferramentas:
        if nome in vistos:
            violacoes.append(Violacao(quem.nome, nome, Regra.FERRAMENTA_REPETIDA))
            continue
        vistos.add(nome)
        if nome not in ambiente | wiki:
            violacoes.append(Violacao(quem.nome, nome, Regra.FERRAMENTA_DESCONHECIDA))
        elif nome in ambiente and quem.papel is not Papel.ORQUESTRADOR:
            violacoes.append(Violacao(quem.nome, nome, Regra.ESCOPO_VIOLADO))
    return violacoes


@settings(max_examples=200)
@given(agentes_quaisquer())
def test_pbt_u6_08_r10_preparar_recusa_se_e_somente_se_o_oraculo_acha_violacao(quem):
    registro = registro_de_teste()
    esperado = _oraculo(quem)

    assert list(registro.verificar_escopo([quem])) == esperado
    if esperado:
        with pytest.raises(ConfiguracaoDeSessaoInvalida) as recusa:
            registro.preparar(quem, contexto_novo())
        assert list(recusa.value.violacoes) == esperado
    else:
        preparadas = registro.preparar(quem, contexto_novo())
        assert sorted(f.nome for fs in preparadas.values() for f in fs) == sorted(quem.ferramentas)
