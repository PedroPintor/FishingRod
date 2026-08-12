from dataclasses import dataclass
from typing import Literal

@dataclass
class Mensagem:
    autor: str
    texto: str
    tipo: Literal["usuario","sistema","agente"]