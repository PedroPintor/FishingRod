from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Callable
from enum import Enum

from claude_agent_sdk import ClaudeAgentOptions

MENSAGEM_DO_ORQUESTRADOR_TESTE = "OrquestradorTeste"
MENSAGEM_DO_AGENTE_TESTE = "AgenteRodMaker"

NOME_ORQUESTRADOR_FR = "orquestrador-fr"
NOME_SUB_AGENTE_ROD_MAKER = "rod-maker"

class Papel(Enum):
    ORQUESTRADOR = "orquestrador"
    SUB_AGENTE = "sub-agente"

@dataclass
class Agente(ABC):
    '''
        nome
        modelo
        ferramentas
        regras  
        caixa_de_texto 
    '''
    nome: str
    papel: Papel
    modelo: str
    ferramentas: list[Callable]
    regras: list[str]
    caixa_de_texto: str = "[Agente]"

    @abstractmethod
    def responder(self, mensagem: str) -> str: ...              

class AgenteTeste(Agente):
    def responder(self, mensagem: str) ->str:
        return "Hmmmm... a minha reposta é..... EU NAO SEI SOU APENAS UM TESTE"

class AgenteClaude(Agente):
    def construir_agente(self) -> ClaudeAgentOptions:
        return ClaudeAgentOptions()

    def responder(self, mensagem):
        return 



def ferramenta_iniciar_subAgente():
    return "Executando subAgente..."


OrquestradorTeste = AgenteTeste(
    nome=NOME_ORQUESTRADOR_FR,
    modelo="opus",
    ferramentas=[ferramenta_iniciar_subAgente],
    regras=['regra 1','regra 2'],
    caixa_de_texto=MENSAGEM_DO_ORQUESTRADOR_TESTE,
    papel=Papel.ORQUESTRADOR
)

RodMakerTeste = AgenteTeste(
    nome=NOME_SUB_AGENTE_ROD_MAKER,
    modelo="opus",
    ferramentas=[],
    regras=['regra 1','regra 2'],
    caixa_de_texto=MENSAGEM_DO_AGENTE_TESTE,
    papel=Papel.SUB_AGENTE
)

AgenteDoSistema = [
    OrquestradorTeste,
    RodMakerTeste
]