"""A gramatica do index.md (RN-W-18, RN-W-19, RN-W-21), sem disco.

montar_indice e pura (DP-W-07): estes testes comparam texto com texto. O que o
disco acrescenta - quais paginas entram, criacao da raiz, publicacao atomica -
esta em test_wiki_de_arquivos.py e test_propriedades.py.
"""

from hypothesis import given
from hypothesis import strategies as st

from fishingrod.adaptadores.wiki.indice import SEM_PROPRIEDADES, VAZIO, montar_indice
from tests.wiki import estrategias as est

_SLUGS = st.from_regex(r"[a-z0-9]{1,6}(-[a-z0-9]{1,6}){0,2}", fullmatch=True)


def test_rn_w_18_a_gramatica_do_exemplo():
    """O exemplo de domain-entities.md 3, byte a byte."""
    entidades = {
        "clientes": {
            "dr-marcelo": "dentista, ticket alto, fechou em duas reuniões",
            "nexo-b2b": "agência parceira, indica leads",
        },
        "ofertas": {"plano-anual": "preço, prazo e o que entra em cada faixa"},
    }

    assert montar_indice("Nexo Aquisição", entidades) == (
        "# Wiki — Nexo Aquisição\n"
        "\n"
        "## Entidades\n"
        "\n"
        "### [[clientes]]\n"
        "\n"
        "- [[clientes/dr-marcelo]]: dentista, ticket alto, fechou em duas reuniões\n"
        "- [[clientes/nexo-b2b]]: agência parceira, indica leads\n"
        "\n"
        "### [[ofertas]]\n"
        "\n"
        "- [[ofertas/plano-anual]]: preço, prazo e o que entra em cada faixa\n"
    )


def test_rn_w_19_wiki_vazia_e_estado_valido_e_legivel():
    """Parte B.3 de U1: o ambiente nasce com wiki mesmo sem entidade (US-08)."""
    assert montar_indice("Nexo Aquisição", {}) == (
        "# Wiki — Nexo Aquisição\n"
        "\n"
        "## Entidades\n"
        "\n"
        "(vazio — ainda não tem nenhuma entidade)\n"
    )
    assert VAZIO == "(vazio — ainda não tem nenhuma entidade)"


def test_rn_w_19_entidade_sem_propriedade_legivel():
    """"Entidade vazia" e diferente de "entidade quebrada", e o agente precisa
    ver a diferenca."""
    texto = montar_indice("ambiente", {"clientes": {}, "ofertas": {"plano": "preco"}})

    assert "### [[clientes]]\n\n(sem propriedades)\n\n### [[ofertas]]" in texto
    assert SEM_PROPRIEDADES == "(sem propriedades)"


def test_rn_w_21_ordem_alfabetica_do_slug_nas_entidades_e_nas_paginas():
    texto = montar_indice(
        "ambiente",
        {
            "ofertas": {"zeta": "z", "alfa": "a"},
            "clientes": {"nexo-b2b": "n", "dr-marcelo": "d"},
        },
    )
    links = [linha for linha in texto.split("\n") if "[[" in linha]

    assert links == [
        "### [[clientes]]",
        "- [[clientes/dr-marcelo]]: d",
        "- [[clientes/nexo-b2b]]: n",
        "### [[ofertas]]",
        "- [[ofertas/alfa]]: a",
        "- [[ofertas/zeta]]: z",
    ]


@given(
    nome=st.text(est.QUALQUER, max_size=20),
    entidades=st.dictionaries(
        _SLUGS, st.dictionaries(_SLUGS, st.text(est.QUALQUER, max_size=20), max_size=4), max_size=4
    ),
)
def test_rn_w_21_a_ordem_de_entrada_nao_chega_a_saida(nome, entidades):
    """O mesmo conteudo em ordem invertida da os mesmos bytes - e a metade pura
    de PBT-U3-02; a metade com disco esta em test_propriedades.py."""
    invertido = {
        entidade: dict(reversed(list(paginas.items())))
        for entidade, paginas in reversed(list(entidades.items()))
    }

    assert montar_indice(nome, entidades) == montar_indice(nome, invertido)


@given(nome=st.text(est.QUALQUER, max_size=20))
def test_rn_w_18_cabecalho_e_uma_linha_so_e_o_arquivo_termina_em_lf(nome):
    """Um nome com quebra partiria o titulo em dois e quebraria a gramatica."""
    texto = montar_indice(nome, {})
    primeira, segunda = texto.split("\n")[:2]

    assert primeira.startswith("# Wiki — ")
    assert segunda == ""
    assert texto.endswith(VAZIO + "\n")
    assert "\r" not in texto
