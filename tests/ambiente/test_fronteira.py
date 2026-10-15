"""U4 - fronteira do servico (RN-A-01, criterio 3).

Como tests/dominio/test_fronteira.py: verifica o GRAFO DE IMPORT, e nao a
ausencia dos pacotes no ambiente. O que nao pode existir e a aresta.

Aqui a lista e mais longa que a do dominio: alem de SDK, banco e tela, o
servico tambem nao pode tocar disco (os, pathlib, shutil). Quem apaga a pasta
da wiki e a porta, nao o servico (Q6=A) - e nenhum adaptador pode aparecer,
nem pelo nome do pacote.
"""

import ast
import pathlib

from fishingrod.aplicacao.servicos import servico_de_ambiente

PROIBIDOS = {"claude_agent_sdk", "sqlite3", "textual", "os", "pathlib", "shutil"}

ARQUIVO = pathlib.Path(servico_de_ambiente.__file__)


def _importados(caminho: pathlib.Path) -> set[str]:
    """Nomes completos dos modulos importados ("fishingrod.aplicacao.portas.wiki"),
    nao so o primeiro segmento: e o caminho inteiro que diz se e adaptador."""
    arvore = ast.parse(caminho.read_text(encoding="utf-8"), filename=str(caminho))
    importados: set[str] = set()
    for no in ast.walk(arvore):
        if isinstance(no, ast.Import):
            importados.update(alias.name for alias in no.names)
        elif isinstance(no, ast.ImportFrom) and no.module and no.level == 0:
            importados.add(no.module)
    return importados


def test_rn_a_01_servico_nao_importa_sdk_banco_tela_nem_disco():
    raizes = {nome.split(".")[0] for nome in _importados(ARQUIVO)}

    assert raizes & PROIBIDOS == set()


def test_rn_a_01_servico_so_conhece_dominio_e_portas():
    """Do projeto, so o dominio, as portas e o EsquemaWiki (que U3 pos em
    aplicacao/ por ser vocabulario da criacao). Nenhum adaptador."""
    do_projeto = {nome for nome in _importados(ARQUIVO) if nome.startswith("fishingrod")}

    assert not any(nome.startswith("fishingrod.adaptadores") for nome in do_projeto)
    assert do_projeto <= {
        "fishingrod.dominio",
        "fishingrod.aplicacao.portas.persistencia",
        "fishingrod.aplicacao.portas.wiki",
        "fishingrod.aplicacao.esquema_wiki",
    }


def test_rn_a_01_servicos_init_nao_reexporta():
    """O pacote servicos/ e compartilhado por U4, U7 e U8: importar um servico
    nao pode arrastar os outros (decisao declarada no plano, secao 3)."""
    init = ARQUIVO.parent / "__init__.py"

    assert _importados(init) == set()
