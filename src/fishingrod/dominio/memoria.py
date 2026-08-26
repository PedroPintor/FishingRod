"""Memoria por tarefa - blackboard (RN-09, RN-10, mata TD-03)."""

from dataclasses import dataclass, field
from datetime import UTC, datetime

from fishingrod.dominio.erros import exigir_texto


@dataclass(frozen=True)
class Anotacao:
    """Uma anotacao na memoria: quem escreveu, o que, e quando.

    criada_em existe por CQ3=C: e o que permite exibir anotacoes de chaves
    DIFERENTES em ordem cronologica unica. Sem ele so existe ordem dentro de
    cada chave.
    """

    autor: str
    valor: str
    criada_em: datetime


@dataclass
class Memoria:
    """Anotacoes por chave. Multiplas anotacoes na mesma chave acumulam.

    versao conta escritas (CQ3=C) para deteccao de conflito em U2. NAO ordena
    anotacoes: a ordem vem da posicao na lista e de Anotacao.criada_em.
    """

    anotacoes: dict[str, list[Anotacao]] = field(default_factory=dict)
    versao: int = 0

    def anotar(self, chave: str, valor: str, autor: str) -> Anotacao:
        """Acrescenta uma anotacao. Nunca substitui a anterior (US-04).

        Correcao de TD-03: o codigo atual fazia anotacoes[chave].append(...),
        que levanta KeyError quando a chave e inedita. setdefault cria a lista
        antes de acessar.
        """
        exigir_texto(chave, "chave da anotacao")
        exigir_texto(autor, "autor da anotacao")

        anotacao = Anotacao(autor=autor, valor=valor, criada_em=datetime.now(UTC))
        self.anotacoes.setdefault(chave, []).append(anotacao)
        self.versao += 1
        return anotacao

    def total_de_anotacoes(self) -> int:
        return sum(len(lista) for lista in self.anotacoes.values())
