"""U1 - fronteira da camada de dominio (RN-13, RF-F04).

Verifica o GRAFO DE IMPORT, nao a ausencia dos pacotes no ambiente. E essa
diferenca que mantem o teste valido depois de U6 instalar claude-agent-sdk e
U9 instalar textual: o que nao pode existir e a aresta, nao o pacote.
"""

import ast
import pathlib

import fishingrod.dominio

PROIBIDOS = {"claude_agent_sdk", "sqlite3", "textual"}

RAIZ_DOMINIO = pathlib.Path(fishingrod.dominio.__file__).parent


def _modulos_importados(caminho: pathlib.Path) -> set[str]:
    arvore = ast.parse(caminho.read_text(encoding="utf-8"), filename=str(caminho))
    importados: set[str] = set()
    for no in ast.walk(arvore):
        if isinstance(no, ast.Import):
            importados.update(alias.name.split(".")[0] for alias in no.names)
        elif isinstance(no, ast.ImportFrom) and no.module and no.level == 0:
            importados.add(no.module.split(".")[0])
    return importados


def test_rn_13_dominio_nao_importa_sdk_sqlite_nem_textual():
    arquivos = sorted(RAIZ_DOMINIO.glob("*.py"))
    assert arquivos, "nenhum modulo de dominio encontrado"

    ofensas = {
        arquivo.name: sorted(_modulos_importados(arquivo) & PROIBIDOS)
        for arquivo in arquivos
        if _modulos_importados(arquivo) & PROIBIDOS
    }

    assert ofensas == {}


def test_rn_13_dominio_importa_apenas_stdlib_e_ele_mesmo():
    """Nenhuma dependencia de terceiros no dominio - e o que torna o criterio
    de TD-02 em U6 verificavel de verdade."""
    permitidos = {"dataclasses", "enum", "uuid", "datetime", "fishingrod", "typing", "collections"}

    for arquivo in sorted(RAIZ_DOMINIO.glob("*.py")):
        fora = _modulos_importados(arquivo) - permitidos
        assert fora == set(), f"{arquivo.name} importa {sorted(fora)}"
