"""Os tipos de uma ferramenta neutra, sem SDK (U6, domain-entities.md 4.2, 4.3).

Uma Ferramenta e o que o agente pode chamar: nome, descricao, esquema e a
funcao. Quem a fabrica e dono de toda regra - esquema, validacao, texto do
resultado -; o adaptador de sessao so a traduz para o SDK (Q9=A).

RN-S-01: nada daqui importa `claude_agent_sdk` nem o catalogo de U5.
"""

from collections.abc import Awaitable, Callable, Mapping
from dataclasses import dataclass, field

from fishingrod.aplicacao.portas.sessao import ContextoDaSessao, Familia, somente_leitura
from fishingrod.dominio import Agente


@dataclass(frozen=True)
class RespostaDaFerramenta:
    """O que a funcao de uma ferramenta devolve ao agente. `erro` marca o
    resultado como erro da ferramenta para o SDK - o agente le o texto de
    qualquer jeito."""

    texto: str
    erro: bool = False


# Recebe os argumentos do modelo como vieram, em copia somente leitura
# (RN-S-42), e valida por conta propria: o adaptador nao confia que o modelo
# respeitou o esquema.
type Executar = Callable[[Mapping[str, object]], Awaitable[RespostaDaFerramenta]]


@dataclass(frozen=True)
class Ferramenta:
    """Uma ferramenta neutra. `nome` e snake_case ASCII, igual ao da entrada do
    registro; `esquema` e JSON Schema de um objeto (o padrao aberto, nao o do
    SDK), guardado em copia funda somente leitura."""

    nome: str
    descricao: str
    esquema: Mapping[str, object]
    executar: Executar = field(repr=False, compare=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "esquema", somente_leitura(self.esquema))


# Chamada uma vez, na abertura da sessao (RN-S-08): amarra a ferramenta ao chat
# (o contexto) e a quem assina (o agente).
type Fabrica = Callable[[ContextoDaSessao, Agente], Ferramenta]


@dataclass(frozen=True)
class EntradaDoRegistro:
    """Um nome de ferramenta, a familia dele e a fabrica. `nome` e unico no
    registro inteiro, entre familias (RN-S-13)."""

    nome: str
    familia: Familia
    fabrica: Fabrica = field(repr=False, compare=False)
