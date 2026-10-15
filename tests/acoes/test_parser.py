"""U5 - ParserDeComando, por exemplos (RN-AC-39..42, business-logic-model.md
3.1). A ida e volta e PBT-U5-01, em test_propriedades.py."""

import pytest

from fishingrod.aplicacao.catalogo.parser import ComandoDigitado, ParserDeComando

parser = ParserDeComando()


# --- detectar (RN-AC-39, G9) --------------------------------------------------


@pytest.mark.parametrize(
    "entrada",
    ["/criar-tarefa campanha de verao", "/", "/ajuda", "//", "/ texto"],
)
def test_rn_ac_39_barra_no_primeiro_caractere_e_comando(entrada):
    assert parser.detectar(entrada)


@pytest.mark.parametrize(
    "entrada",
    [" /criar-tarefa x", "\t/x", "", "criar-tarefa", "a/b", " /x", "／criar"],
)
def test_rn_ac_39_g9_qualquer_outra_coisa_e_conversa(entrada):
    """Espaco antes da barra faz a entrada ser conversa. A barra de largura
    cheia nao e a barra."""
    assert not parser.detectar(entrada)


# --- interpretar (RN-AC-40) -------------------------------------------------


@pytest.mark.parametrize(
    ("entrada", "nome", "texto"),
    [
        # os exemplos de business-logic-model.md 3.1
        ("/criar-tarefa campanha de verao", "criar-tarefa", "campanha de verao"),
        ("/criar-tarefa   campanha   de verao  ", "criar-tarefa", "campanha   de verao"),
        ("/", "", ""),
        # o nome vai ate o PRIMEIRO espaco, de qualquer tipo (R-CG5-6)
        ("/criar-tarefa\tcampanha", "criar-tarefa", "campanha"),
        ("/criar-tarefa campanha", "criar-tarefa", "campanha"),
        ("/anotar-memoria x\ny", "anotar-memoria", "x\ny"),
        ("/ campanha", "", "campanha"),
        ("/sair", "sair", ""),
        ("/sair   ", "sair", ""),
        # nada e normalizado: maiuscula, acento e a barra de dentro ficam
        ("/Criar-Tarefa Ação de Verão", "Criar-Tarefa", "Ação de Verão"),
        ("/criar_tarefa x", "criar_tarefa", "x"),
        ("//x a/b", "/x", "a/b"),
    ],
)
def test_rn_ac_40_separa_nome_e_texto(entrada, nome, texto):
    assert parser.interpretar(entrada) == ComandoDigitado(nome, texto)


def test_rn_ac_40_os_espacos_de_dentro_ficam_como_foram_digitados():
    """TD-11, no parser: nada aperta os espacos do meio."""
    comando = parser.interpretar("/criar-frente  comercial \t e ticket ")

    assert comando.texto == "comercial \t e ticket"


@pytest.mark.parametrize("entrada", ["criar-tarefa", "", " /x", "texto qualquer"])
def test_rn_ac_40_interpretar_sem_barra_e_erro_de_quem_chamou(entrada):
    with pytest.raises(ValueError):
        parser.interpretar(entrada)


# --- formatar (RN-AC-41) ----------------------------------------------------


@pytest.mark.parametrize(
    ("comando", "linha"),
    [
        (ComandoDigitado("criar-tarefa", "campanha de verao"), "/criar-tarefa campanha de verao"),
        (ComandoDigitado("sair", ""), "/sair"),
        (ComandoDigitado("sair"), "/sair"),
        (ComandoDigitado("", ""), "/"),
        (ComandoDigitado("", "x"), "/ x"),
    ],
)
def test_rn_ac_41_formatar(comando, linha):
    assert parser.formatar(comando) == linha
    assert parser.interpretar(linha) == comando


def test_rn_ac_42_o_parser_serve_os_comandos_da_tela():
    """Nao conhece o catalogo: /ajuda e interpretado como qualquer outro."""
    assert parser.interpretar("/ajuda criar-tarefa") == ComandoDigitado("ajuda", "criar-tarefa")
