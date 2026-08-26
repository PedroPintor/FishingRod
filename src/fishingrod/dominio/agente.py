"""Agente como configuracao imutavel (components.md 2.9)."""

from dataclasses import dataclass, field
from enum import Enum

from fishingrod.dominio.erros import exigir_texto


class Papel(Enum):
    ORQUESTRADOR = "orquestrador"
    SUB_AGENTE = "sub_agente"


@dataclass(frozen=True)
class Agente:
    """Configuracao de um agente: nome, papel, modelo, ferramentas, regras.

    Nao tem responder() e nao guarda estado de sessao - por isso pode ser
    compartilhada entre chats sem o risco da instancia unica que existe hoje
    em AgenteDoSistema (Pergunta 6A).

    ferramentas guarda NOMES de ferramenta, nao funcoes (emenda R4 / Q12=A):
    o registro nome->funcao e montado pelo composition root (U9) e resolvido
    pelo adaptador de sessao (U6). E isso que evita ServicoConversa ter de
    importar CatalogoDeAcoes.
    """

    nome: str
    papel: Papel
    modelo: str
    ferramentas: tuple[str, ...] = ()
    regras: tuple[str, ...] = field(default=())

    def __post_init__(self) -> None:
        exigir_texto(self.nome, "nome do agente")
        exigir_texto(self.modelo, "modelo do agente")

    @property
    def e_orquestrador(self) -> bool:
        return self.papel is Papel.ORQUESTRADOR
