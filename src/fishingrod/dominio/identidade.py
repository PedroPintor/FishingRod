"""Identidade opaca e estavel (RN-01, ESC-14, RF-F16)."""

import uuid
from dataclasses import dataclass


@dataclass(frozen=True)
class Identidade:
    """UUIDv7 em texto canonico.

    Substitui indice posicional e nome como referencia. Ordenavel por tempo de
    criacao, que e o que da paginacao de transcricao em U2 sem coluna extra.

    Criada no construtor da entidade de dominio, nunca no adaptador de
    persistencia (Pergunta 4B): o repositorio le a identidade que ja existe.
    """

    valor: str

    @staticmethod
    def nova() -> "Identidade":
        # uuid7 e stdlib a partir do Python 3.14. O projeto subiu para 3.14
        # exatamente por isto (CQ2=D) - antes disso a alternativa era escrever
        # a geracao a mao ou trazer dependencia para dentro do dominio.
        return Identidade(valor=str(uuid.uuid7()))

    def __str__(self) -> str:
        return self.valor
