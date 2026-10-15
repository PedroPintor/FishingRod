"""Adaptador de persistencia em SQLite (U2).

U9 escreve um import so, sem conhecer a divisao interna do pacote. `localizacao`
nao e reexportada de proposito: quem resolve o caminho e o composition root, e o
repositorio recebe o Path pronto (DP-P-05).
"""

from fishingrod.adaptadores.persistencia.repositorio_sqlite import (
    RepositorioSQLite,
    abrir_repositorio,
)

__all__ = ["RepositorioSQLite", "abrir_repositorio"]
