"""Adaptador de wiki em arquivos markdown (U3).

U9 escreve um import so, sem conhecer a divisao interna do pacote. As outras
unidades nao importam daqui: dependem de `aplicacao/portas/wiki.py` (DP-W-09).

O NullHandler e instalado aqui, uma vez, para o logger da unidade (NFR-W-16):
sem destino configurado, nenhum aviso vaza para a tela da TUI. Quem decide para
onde o log vai e o composition root de U9.
"""

import logging

from fishingrod.adaptadores.wiki.wiki_de_arquivos import WikiDeArquivos

logging.getLogger("fishingrod.wiki").addHandler(logging.NullHandler())

__all__ = ["WikiDeArquivos"]
