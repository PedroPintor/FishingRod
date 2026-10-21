"""Camada de dominio: estado e invariantes.

Nao persiste a si mesmo, nao roteia comando, nao conhece sessao viva e nao
importa claude_agent_sdk, sqlite3 nem textual (RF-F04, RN-13).
"""

from fishingrod.dominio.agente import Agente, Papel
from fishingrod.dominio.ambiente import Ambiente
from fishingrod.dominio.chat import Chat
from fishingrod.dominio.erros import (
    AgenteInvalido,
    ErroDeDominio,
    NomeInvalido,
    OrquestradorDuplicado,
)
from fishingrod.dominio.etapa import Etapa, ExecutorEtapa
from fishingrod.dominio.frente import Frente
from fishingrod.dominio.identidade import Identidade
from fishingrod.dominio.memoria import Anotacao, Memoria
from fishingrod.dominio.politica import Chamador, exige_aprovacao
from fishingrod.dominio.raiz_wiki import LocalizadorInvalido, RaizWiki
from fishingrod.dominio.sessao import Sessao
from fishingrod.dominio.tarefa import Tarefa

__all__ = [
    "Agente",
    "AgenteInvalido",
    "Ambiente",
    "Anotacao",
    "Chamador",
    "Chat",
    "ErroDeDominio",
    "Etapa",
    "ExecutorEtapa",
    "Frente",
    "Identidade",
    "LocalizadorInvalido",
    "Memoria",
    "NomeInvalido",
    "OrquestradorDuplicado",
    "Papel",
    "RaizWiki",
    "Sessao",
    "Tarefa",
    "exige_aprovacao",
]
