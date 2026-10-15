"""Onde o arquivo do banco mora (DP-P-05, Q1=A + Q1a=B).

Funcao pura: resolve um caminho e nao toca em disco. Quem chama e o composition
root de U9; o repositorio recebe o Path pronto. E por isso que todo teste desta
unidade passa um tmp_path sem precisar de monkeypatch.

As ~12 linhas abaixo sao a alternativa que Q1a=B preferiu a uma dependencia de
runtime (platformdirs). NFR-P-12 continua verdadeiro.

Sem variavel de ambiente de override: nenhuma historia pede, e configuracao
criada "por precaucao" nunca e removida depois.
"""

import os
import sys
from pathlib import Path

NOME_DO_BANCO = "fishingrod.db"


def pasta_de_dados() -> Path:
    """A raiz de dados do usuario, por sistema operacional.

    E tambem a raiz que resolve o esquema `dados:` de RaizWiki: U3 materializa
    `wikis/<id_ambiente>/` debaixo desta pasta (domain-entities.md 7). Anotado
    aqui para nao ser redescoberto la.
    """
    if sys.platform == "win32":
        raiz = os.environ.get("LOCALAPPDATA")
        base = Path(raiz) if raiz else Path.home() / "AppData" / "Local"
        return base / "FishingRod"

    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "FishingRod"

    # Linux e os demais POSIX: XDG Base Directory.
    xdg = os.environ.get("XDG_DATA_HOME")
    base = Path(xdg) if xdg else Path.home() / ".local" / "share"
    return base / "fishingrod"


def caminho_do_banco() -> Path:
    return pasta_de_dados() / NOME_DO_BANCO
