"""A tabela de falhas: da fase e da causa para o motivo (DP-S-09, N6).

`classificar` e pura e total: toda causa cai numa linha, e o que nao se
reconhece com certeza nunca vai para uma categoria errada (RN-S-29). A
categoria vem da FASE e de sinal TIPADO, nunca de texto: nenhuma mensagem de
excecao e lida aqui.

DP-S-19: este modulo nao registra nada. Devolve o nivel de log como dado, e o
adaptador registra.
"""

import logging
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from types import MappingProxyType

from claude_agent_sdk import CLIConnectionError, CLIJSONDecodeError, CLINotFoundError, ProcessError

from fishingrod.aplicacao.portas.sessao import FalhaDoTurno, MotivoFalhaDeSessao


class Fase(Enum):
    """Onde a tarefa dona estava quando caiu."""

    SUBIDA = "subida"
    ENTREGA = "entrega"
    RESPOSTA = "resposta"


# --------------------------------------------------------------------------
# As causas que nao sao excecao
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class CliAusente:
    """O CLI embutido nao existe (DP-S-15): nada chegou a subir."""


@dataclass(frozen=True)
class PrazoVencido:
    """A subida nao terminou no prazo (NFR-S-11)."""


@dataclass(frozen=True)
class FimSemResultado:
    """O fluxo do SDK acabou sem mensagem de resultado: a resposta veio
    truncada."""


@dataclass(frozen=True)
class ErroDoAssistente:
    """O sinal tipado de `AssistantMessage.error` (A8)."""

    tipo: str


@dataclass(frozen=True)
class LimiteAtingido:
    """Um `RateLimitEvent` com `status == "rejected"`. `resets_at` e o instante
    Unix em que o limite libera, quando o CLI informa."""

    resets_at: int | None = None


@dataclass(frozen=True)
class ResultadoComErro:
    """Uma mensagem de resultado com erro, sem nenhum sinal tipado antes (N6).
    So o subtipo e o status HTTP, que nao carregam conteudo."""

    subtipo: str | None = None
    status: int | None = None


type Sinal = CliAusente | PrazoVencido | FimSemResultado | ErroDoAssistente | LimiteAtingido | ResultadoComErro
type Causa = BaseException | Sinal


# --------------------------------------------------------------------------
# A classificacao
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class Classificacao:
    """O motivo, se a falha derruba a conexao, e como registrar. `com_pilha`
    so vale quando a causa e uma excecao."""

    motivo: MotivoFalhaDeSessao
    derruba: bool
    nivel: int
    com_pilha: bool = False
    detalhe: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "detalhe", MappingProxyType(dict(self.detalhe)))

    def evento(self) -> FalhaDoTurno:
        return FalhaDoTurno(self.motivo, self.detalhe)


# RN-S-24: nao esta na tabela de causas, porque nao e falha do provedor - o
# turno acabou bem, so que sem nada. Mantem a conexao e o historico.
RESPOSTA_VAZIA = Classificacao(MotivoFalhaDeSessao.RESPOSTA_VAZIA, derruba=False, nivel=logging.WARNING)

_INDISPONIVEL_NA_RESPOSTA = frozenset({"billing_error", "server_error", "unknown"})


def classificar(fase: Fase, causa: Causa) -> Classificacao:
    """O §4 de nfr-design-patterns.md, linha por linha. O cancelamento nao
    chega aqui: nao e falha, e passa (RN-S-16)."""
    match causa:
        case CliAusente():
            return Classificacao(MotivoFalhaDeSessao.PROVEDOR_AUSENTE, True, logging.WARNING)
        case ErroDoAssistente(tipo="authentication_failed"):
            return Classificacao(MotivoFalhaDeSessao.NAO_AUTENTICADO, True, logging.WARNING)
        case ErroDoAssistente(tipo="rate_limit"):
            return Classificacao(MotivoFalhaDeSessao.LIMITE_DE_USO, False, logging.WARNING)
        case LimiteAtingido(resets_at=resets_at):
            return Classificacao(
                MotivoFalhaDeSessao.LIMITE_DE_USO, False, logging.WARNING, detalhe=_libera_em(resets_at)
            )
        case ErroDoAssistente(tipo=tipo) if tipo in _INDISPONIVEL_NA_RESPOSTA:
            return Classificacao(MotivoFalhaDeSessao.INDISPONIVEL, True, logging.WARNING)
        case ErroDoAssistente():
            # invalid_request e pedido malformado - defeito nosso (N6). Um sinal
            # que esta versao nao conhece tambem nao vai para categoria errada.
            return Classificacao(MotivoFalhaDeSessao.FALHA_INESPERADA, True, logging.ERROR)
        case ResultadoComErro():
            return Classificacao(MotivoFalhaDeSessao.FALHA_INESPERADA, True, logging.ERROR)
        case FimSemResultado() | PrazoVencido():
            return Classificacao(MotivoFalhaDeSessao.INDISPONIVEL, True, logging.WARNING)
    if fase is Fase.SUBIDA:
        # Na subida, tudo e INDISPONIVEL, menos o CLI ausente - com a pilha,
        # porque e a principal pista de por que o processo nao subiu (Q3=A).
        if isinstance(causa, CLINotFoundError):
            return Classificacao(MotivoFalhaDeSessao.PROVEDOR_AUSENTE, True, logging.WARNING)
        return Classificacao(MotivoFalhaDeSessao.INDISPONIVEL, True, logging.WARNING, com_pilha=True)
    if isinstance(causa, (CLIConnectionError, ProcessError, CLIJSONDecodeError)):
        return Classificacao(MotivoFalhaDeSessao.INDISPONIVEL, True, logging.WARNING)
    # Qualquer outra excecao, inclusive defeito no proprio adaptador.
    return Classificacao(MotivoFalhaDeSessao.FALHA_INESPERADA, True, logging.ERROR, com_pilha=True)


def _libera_em(resets_at: int | None) -> dict[str, str]:
    """ISO 8601 em UTC, quando o CLI informa um instante que se le. Um valor
    absurdo some, em vez de derrubar a classificacao."""
    if resets_at is None or isinstance(resets_at, bool) or not isinstance(resets_at, int):
        return {}
    try:
        return {"libera_em": datetime.fromtimestamp(resets_at, UTC).isoformat()}
    except (OverflowError, OSError, ValueError):
        return {}


# --------------------------------------------------------------------------
# Avisos (DP-S-19)
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class Aviso:
    """Algo que vai para o log, como dado: o nivel, a mensagem no formato do
    `logging` e os argumentos. Nunca texto de mensagem nem argumento de
    ferramenta."""

    nivel: int
    mensagem: str
    argumentos: tuple[object, ...] = ()
