"""U1 - Ambiente e RaizWiki (RN-03, RN-04, RN-11, PBT-U1-06, PBT-U1-07)."""

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from fishingrod.dominio import Ambiente, Identidade, LocalizadorInvalido, NomeInvalido, RaizWiki

texto_nao_vazio = st.text(min_size=1, max_size=60).filter(lambda s: s.strip())
so_espaco = st.text(alphabet=" \t\n\r", min_size=1, max_size=5)


def test_rn_03_ambiente_nasce_sem_frente():
    """Q1=A: a criacao automatica de projeto-padrao existia por causa do
    IndexError em projetos[indice_ativo], razao que morreu com ESC-14."""
    assert Ambiente(nome="meu ambiente").frentes == []


def test_rn_11_raiz_wiki_deriva_da_identidade():
    ambiente = Ambiente(nome="meu ambiente")

    assert ambiente.raiz_wiki == RaizWiki(f"dados:wikis/{ambiente.id.valor}")
    assert ambiente.raiz_wiki.esquema() == "dados"


def test_ambiente_nasce_com_versao_zero():
    """Emenda de U2 (domain-entities.md 5.1): zero significa nunca gravado.

    O campo entrou por ultimo na dataclass para nao mudar o significado de
    nenhuma chamada posicional ja existente - por isso o teste tambem constroi
    posicionalmente.
    """
    assert Ambiente(nome="ambiente").versao == 0

    posicional = Ambiente("ambiente", [], Identidade.nova())
    assert posicional.versao == 0
    assert posicional.raiz_wiki == RaizWiki(f"dados:wikis/{posicional.id.valor}")


@pytest.mark.parametrize(
    "localizador",
    ["dados:/wikis/x", "dados:\\wikis\\x", "dados:C:/wikis/x", "sem-esquema"],
)
def test_rn_11_localizador_absoluto_ou_sem_esquema_levanta(localizador):
    with pytest.raises(LocalizadorInvalido):
        RaizWiki(localizador=localizador)


def test_rn_04_nome_duplicado_de_frente_e_permitido():
    ambiente = Ambiente(nome="ambiente")

    primeira = ambiente.criar_frente("mesma coisa")
    segunda = ambiente.criar_frente("mesma coisa")

    assert primeira.id != segunda.id
    assert len(ambiente.frentes) == 2


@given(nomes=st.lists(texto_nao_vazio, min_size=1, max_size=15))
@settings(max_examples=50)
def test_pbt_u1_06_frente_criada_e_encontrada_por_identidade(nomes):
    ambiente = Ambiente(nome="ambiente")

    criadas = [ambiente.criar_frente(nome) for nome in nomes]

    for frente in criadas:
        assert ambiente.buscar_frente(frente.id) is frente
    assert ambiente.buscar_frente(Identidade.nova()) is None


@given(nome=so_espaco)
@settings(max_examples=25)
def test_pbt_u1_07_nome_so_de_espaco_sempre_levanta(nome):
    with pytest.raises(NomeInvalido):
        Ambiente(nome=nome)

    with pytest.raises(NomeInvalido):
        Ambiente(nome="valido").criar_frente(nome)
