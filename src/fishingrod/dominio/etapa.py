"""Etapa de execucao de uma tarefa (RN-07, RN-08)."""

from dataclasses import dataclass, field
from enum import Enum

from fishingrod.dominio.erros import exigir_texto
from fishingrod.dominio.identidade import Identidade


class ExecutorEtapa(Enum):
    AGENTE = "agente"
    USUARIO = "usuario"


@dataclass
class Etapa:
    """Passo de execucao, descoberto conversando com o orquestrador (US-17).

    A ordem das etapas e a posicao na lista de Tarefa.etapas (Q5b=A). NAO ha
    dependencia entre elas: concluir a terceira com a primeira pendente e
    permitido e nao gera aviso no dominio.
    """

    descricao: str
    executor: ExecutorEtapa
    concluida: bool = False
    id: Identidade = field(default_factory=Identidade.nova)

    def __post_init__(self) -> None:
        exigir_texto(self.descricao, "descricao da etapa")

    def concluir(self) -> None:
        # Idempotente (Q5a=B): concluir duas vezes e o mesmo que concluir uma.
        self.concluida = True

    def reabrir(self) -> None:
        # Q5a=B: o usuario pode desmarcar. Tambem idempotente.
        self.concluida = False
