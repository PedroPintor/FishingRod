"""Testes da unidade U0 `fundacao`.

Provam o criterio de pronto da unidade: o layout `src/` esta instalado e
resolve por import, e as camadas previstas em `unit-of-work.md` §4 existem.
"""

import importlib


def test_pacote_fishingrod_resolve():
    """O layout src/ esta instalado; importar o pacote nao levanta."""
    modulo = importlib.import_module("fishingrod")
    assert modulo.__name__ == "fishingrod"


def test_camadas_previstas_existem():
    """Cada camada de `unit-of-work.md` §4 e um pacote importavel.

    Q9=A pos a camada no topo justamente para que a regra de import de
    `component-dependency.md` §1 seja verificavel pelo caminho do modulo.
    Se uma camada nao existir, essa verificacao nao teria onde acontecer.
    """
    camadas = [
        "fishingrod.dominio",
        "fishingrod.aplicacao",
        "fishingrod.aplicacao.portas",
        "fishingrod.aplicacao.catalogo",
        "fishingrod.aplicacao.servicos",
        "fishingrod.adaptadores",
        "fishingrod.interface",
    ]
    for camada in camadas:
        assert importlib.import_module(camada) is not None
