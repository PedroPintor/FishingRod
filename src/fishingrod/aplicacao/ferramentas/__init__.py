"""Ferramentas neutras e o registro delas (U6).

Reexporta `tipos` e `registro`, e NAO `acoes` (DP-S-23, R-ND6-3): `acoes.py` e
o unico modulo de U6 que importa o catalogo de U5, e so o composition root (U9)
o importa. Importar este pacote nao carrega `aplicacao.catalogo` - o teste de
fronteira confere.
"""

from fishingrod.aplicacao.ferramentas.registro import (
    PADRAO_DE_NOME,
    RegistroDeFerramentas,
    Regra,
    Violacao,
)
from fishingrod.aplicacao.ferramentas.tipos import (
    EntradaDoRegistro,
    Executar,
    Fabrica,
    Ferramenta,
    RespostaDaFerramenta,
)

__all__ = [
    "PADRAO_DE_NOME",
    "EntradaDoRegistro",
    "Executar",
    "Fabrica",
    "Ferramenta",
    "RegistroDeFerramentas",
    "Regra",
    "RespostaDaFerramenta",
    "Violacao",
]
