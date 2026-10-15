"""O registro de ferramentas e a verificacao de escopo (U6, RN-S-06..08, RN-S-13..15).

O registro e montado uma vez pelo composition root (U9): as entradas de acoes
(`acoes.py`) mais as de wiki (U8). `Agente.ferramentas` guarda nomes sem
familia; a familia e daqui.

DP-S-21: `preparar` (o que `abrir` usa) e `verificar_escopo` (o que o teste das
instancias reais chama, em U8 e U9) aplicam a MESMA verificacao, num metodo so.
O adaptador real e o falso chamam `preparar`.

Nao importa o catalogo de U5 (DP-S-23): o padrao de nome de RN-AC-07 e repetido
aqui, e um teste confere que os dois aceitam os mesmos nomes.
"""

import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType

from fishingrod.aplicacao.ferramentas.tipos import EntradaDoRegistro, Ferramenta
from fishingrod.aplicacao.portas.sessao import (
    ConfiguracaoDeSessaoInvalida,
    ContextoDaSessao,
    Familia,
    RegistroInvalido,
)
from fishingrod.dominio import Agente

# snake_case ASCII minusculo, sem sublinhado duplo nem nas pontas - o padrao de
# RN-AC-07. Sem `__` num nome, `mcp__<familia>__<nome>` se separa sem
# ambiguidade (RN-S-12).
PADRAO_DE_NOME = re.compile(r"[a-z][a-z0-9]*(?:_[a-z0-9]+)*")


class Regra(Enum):
    """Qual regra um nome de `Agente.ferramentas` quebrou."""

    FERRAMENTA_DESCONHECIDA = "ferramenta_desconhecida"  # RN-S-06
    FERRAMENTA_REPETIDA = "ferramenta_repetida"  # RN-S-06
    ESCOPO_VIOLADO = "escopo_violado"  # RN-S-07, R10


@dataclass(frozen=True)
class Violacao:
    """Qual agente, qual nome e qual regra."""

    agente: str
    nome: str
    regra: Regra


class RegistroDeFerramentas:
    """Todas as entradas, verificadas na construcao (RN-S-14). Nao muda depois
    de montado: e a unica coisa que as sessoes compartilham."""

    def __init__(self, entradas: Iterable[EntradaDoRegistro]) -> None:
        entradas = tuple(entradas)
        _verificar(entradas)
        self._entradas = entradas
        self._por_nome = {entrada.nome: entrada for entrada in entradas}

    @property
    def entradas(self) -> tuple[EntradaDoRegistro, ...]:
        return self._entradas

    def buscar(self, nome: str) -> EntradaDoRegistro | None:
        return self._por_nome.get(nome) if isinstance(nome, str) else None

    def verificar_escopo(self, agentes: Iterable[Agente]) -> tuple[Violacao, ...]:
        """RN-S-15: RN-S-06 e RN-S-07 aplicadas a uma colecao. Vazio quer dizer
        que todos abririam."""
        return tuple(violacao for agente in agentes for violacao in self._violacoes(agente))

    def preparar(
        self, agente: Agente, contexto: ContextoDaSessao
    ) -> Mapping[Familia, tuple[Ferramenta, ...]]:
        """Verifica e fabrica as ferramentas de uma sessao, agrupadas por
        familia - so as familias presentes, na ordem do enum; dentro de cada
        uma, na ordem de `agente.ferramentas`.

        Se alguma verificacao falhar, levanta ConfiguracaoDeSessaoInvalida e
        nada e criado: nao existe sessao pela metade (RN-S-06).
        """
        violacoes = self._violacoes(agente)
        if violacoes:
            raise ConfiguracaoDeSessaoInvalida(
                f"o agente [{agente.nome}] nao pode abrir sessao: "
                + ", ".join(f"[{v.nome}] {v.regra.value}" for v in violacoes),
                violacoes,
            )
        por_familia: dict[Familia, list[Ferramenta]] = {}
        for nome in agente.ferramentas:
            entrada = self._por_nome[nome]
            por_familia.setdefault(entrada.familia, []).append(_fabricar(entrada, contexto, agente))
        return MappingProxyType(
            {familia: tuple(por_familia[familia]) for familia in Familia if familia in por_familia}
        )

    def _violacoes(self, agente: Agente) -> tuple[Violacao, ...]:
        """Para cada nome, na ordem: repetido, desconhecido, R10
        (business-logic-model.md 2). R10 vale para todo agente que NAO e
        orquestrador - na duvida sobre o papel, recusa."""
        violacoes: list[Violacao] = []
        vistos: set[str] = set()
        for nome in agente.ferramentas:
            if nome in vistos:
                violacoes.append(Violacao(agente.nome, nome, Regra.FERRAMENTA_REPETIDA))
                continue
            vistos.add(nome)
            entrada = self.buscar(nome)
            if entrada is None:
                violacoes.append(Violacao(agente.nome, nome, Regra.FERRAMENTA_DESCONHECIDA))
            elif entrada.familia is Familia.AMBIENTE and not agente.e_orquestrador:
                violacoes.append(Violacao(agente.nome, nome, Regra.ESCOPO_VIOLADO))
        return tuple(violacoes)


def _verificar(entradas: tuple[EntradaDoRegistro, ...]) -> None:
    vistos: set[str] = set()
    for entrada in entradas:
        if not isinstance(entrada, EntradaDoRegistro):
            raise RegistroInvalido(f"o registro tem um item que nao e EntradaDoRegistro: {entrada!r}")
        if not isinstance(entrada.nome, str) or not PADRAO_DE_NOME.fullmatch(entrada.nome):
            raise RegistroInvalido(f"nome de ferramenta fora do padrao snake_case: {entrada.nome!r}")
        if entrada.nome in vistos:
            # RN-S-13: unico no registro inteiro, entre familias.
            raise RegistroInvalido(f"ferramenta [{entrada.nome}] repetida no registro")
        vistos.add(entrada.nome)
        if not isinstance(entrada.familia, Familia):
            raise RegistroInvalido(f"ferramenta [{entrada.nome}] com familia desconhecida")
        if not callable(entrada.fabrica):
            raise RegistroInvalido(f"ferramenta [{entrada.nome}] sem fabrica")


def _fabricar(entrada: EntradaDoRegistro, contexto: ContextoDaSessao, agente: Agente) -> Ferramenta:
    """RN-S-08: a fabrica que levanta, que devolve outro nome, ou um esquema
    que nao e de objeto, impede a abertura.

    "De objeto" e `type: "object"` com `properties`: o SDK troca, sem avisar,
    um esquema sem `properties` por outro que ele mesmo inventa (A17).
    """
    try:
        ferramenta = entrada.fabrica(contexto, agente)
    except Exception as erro:
        raise ConfiguracaoDeSessaoInvalida(
            f"a fabrica da ferramenta [{entrada.nome}] falhou ({type(erro).__name__})"
        ) from erro
    if not isinstance(ferramenta, Ferramenta):
        raise ConfiguracaoDeSessaoInvalida(f"a fabrica de [{entrada.nome}] nao devolveu uma Ferramenta")
    if ferramenta.nome != entrada.nome:
        raise ConfiguracaoDeSessaoInvalida(
            f"a fabrica de [{entrada.nome}] devolveu a ferramenta [{ferramenta.nome}]"
        )
    esquema = ferramenta.esquema
    if esquema.get("type") != "object" or not isinstance(esquema.get("properties"), Mapping):
        raise ConfiguracaoDeSessaoInvalida(f"a ferramenta [{entrada.nome}] tem esquema que nao e de objeto")
    return ferramenta
