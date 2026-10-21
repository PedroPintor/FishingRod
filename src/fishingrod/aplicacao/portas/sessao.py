"""Porta de sessao: o ciclo de vida de uma conversa com o provedor (U6).

Este e o contrato inteiro (DP-S-20): a porta, os tipos, os cinco eventos de um
turno, os motivos de falha, a familia de uma ferramenta, os erros e a
validacao da mensagem. U7 e U8 importam so daqui - nunca de
`adaptadores/sessao` nem de `aplicacao/ferramentas`.

RN-S-01, RN-S-02: nenhum tipo do SDK atravessa esta fronteira, e este modulo
nao importa `claude_agent_sdk`. Falha do provedor e EVENTO, nao excecao
(RN-S-16): as excecoes daqui sao erros de montagem, como `CatalogoInvalido` em
U5.
"""

import copy
from collections.abc import AsyncIterator, Mapping
from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType
from typing import Protocol

from fishingrod.dominio import Agente, Identidade

# --------------------------------------------------------------------------
# Quem e a sessao (domain-entities.md 2.2, 2.3)
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class ContextoDaSessao:
    """De que chat e a sessao (Q8=A). So identidades: o nome que assina o que
    o agente fizer vem do `Agente`, nunca de quem abre (G10). Todo chat mora
    numa sessao de uma tarefa, entao as cinco sempre existem, inclusive para o
    bibliotecario.

    `id_sessao` e a sessao do dominio (Sessao, D21), onde o chat mora - e nao
    esta SessaoViva, que e a conexao aberta com o provedor para um chat."""

    id_ambiente: Identidade
    id_frente: Identidade
    id_tarefa: Identidade
    id_sessao: Identidade
    id_chat: Identidade


@dataclass(frozen=True)
class SessaoViva:
    """O identificador opaco de uma sessao aberta.

    O estado (SEM_CONEXAO, OCIOSA, EM_TURNO, FECHADA) fica com o adaptador, e
    nao aqui: quem tem a SessaoViva nao consegue muda-lo por fora. `id` e da
    sessao, nao do chat, e serve ao log.
    """

    id: Identidade
    nome_agente: str
    contexto: ContextoDaSessao


class Familia(Enum):
    """A familia de uma ferramenta (R9) - e a chave do servidor MCP da sessao.

    Mora na porta (R-ND6-1): U7 le a familia em UsoDeFerramenta sem importar
    `aplicacao/ferramentas`.
    """

    AMBIENTE = "ambiente"
    WIKI = "wiki"


# --------------------------------------------------------------------------
# Os eventos de um turno (domain-entities.md 3)
# --------------------------------------------------------------------------
# Gramatica (RN-S-17):
#   turno entregue     : MensagemEntregue (PedacoDeTexto | UsoDeFerramenta)* (FimDeTurno | FalhaDoTurno)
#   turno nao entregue : FalhaDoTurno
#   turno interrompido : qualquer prefixo dos dois, sem evento final


@dataclass(frozen=True)
class MensagemEntregue:
    """A mensagem chegou ao agente: daqui em diante ele lembra dela (C2=A).

    `conversa_nova` e True na primeira entrega de cada conexao - a primeira do
    chat neste processo, ou a primeira depois de uma reconexao (G2, RN-S-41).
    """

    conversa_nova: bool


@dataclass(frozen=True)
class PedacoDeTexto:
    """Um trecho da resposta, nunca vazio (Q1=B)."""

    texto: str

    def __post_init__(self) -> None:
        if not isinstance(self.texto, str) or not self.texto:
            raise ValueError("PedacoDeTexto: o texto nunca e vazio")


@dataclass(frozen=True)
class UsoDeFerramenta:
    """O agente PEDIU esta ferramenta da sessao - nao garante que ela executou
    (R-FD6-3). O nome e sem familia.

    Os argumentos ficam numa copia funda e somente leitura: nem quem montou o
    evento, nem quem o recebe, muda o que o outro ve.
    """

    familia: Familia
    nome: str
    argumentos: Mapping[str, object]

    def __post_init__(self) -> None:
        object.__setattr__(self, "argumentos", somente_leitura(self.argumentos))


@dataclass(frozen=True)
class FimDeTurno:
    """O turno terminou bem: houve texto ou uso de ferramenta (RN-S-24)."""


class MotivoFalhaDeSessao(Enum):
    """Por que um turno falhou (Q4=A). O valor e o que U7 e U9 leem; a frase
    em portugues e da tela (U9), como em U5."""

    PROVEDOR_AUSENTE = "provedor_ausente"
    NAO_AUTENTICADO = "nao_autenticado"
    LIMITE_DE_USO = "limite_de_uso"
    INDISPONIVEL = "indisponivel"
    RESPOSTA_VAZIA = "resposta_vazia"
    MENSAGEM_INVALIDA = "mensagem_invalida"
    TURNO_EM_ANDAMENTO = "turno_em_andamento"
    SESSAO_FECHADA = "sessao_fechada"
    FALHA_INESPERADA = "falha_inesperada"


@dataclass(frozen=True)
class FalhaDoTurno:
    """O turno terminou sem resposta completa.

    `detalhe` e de texto para texto e nunca traz conteudo (RN-S-31): so
    `problema` e `maximo` em MENSAGEM_INVALIDA, e `libera_em` em LIMITE_DE_USO
    quando o CLI informar.
    """

    motivo: MotivoFalhaDeSessao
    detalhe: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.motivo, MotivoFalhaDeSessao):
            raise ValueError("FalhaDoTurno: motivo precisa ser um MotivoFalhaDeSessao")
        if not all(isinstance(c, str) and isinstance(v, str) for c, v in self.detalhe.items()):
            raise ValueError("FalhaDoTurno: detalhe e de texto para texto")
        object.__setattr__(self, "detalhe", MappingProxyType(dict(self.detalhe)))


type EventoConversa = MensagemEntregue | PedacoDeTexto | UsoDeFerramenta | FimDeTurno | FalhaDoTurno


def somente_leitura(valor: Mapping[str, object]) -> Mapping[str, object]:
    """Copia funda, embrulhada para leitura. A copia funda impede que um valor
    aninhado (uma lista dentro dos argumentos) mude por fora depois."""
    return MappingProxyType(copy.deepcopy(dict(valor)))


# --------------------------------------------------------------------------
# A mensagem (RN-S-25, G4, DP-S-20)
# --------------------------------------------------------------------------

# G4: folgado para colar um documento; muda so aqui.
MAXIMO_DE_CARACTERES = 100_000

VAZIA = "vazia"
LONGA_DEMAIS = "longa_demais"


def validar_mensagem(texto: object) -> FalhaDoTurno | None:
    """None se a mensagem pode sair; a falha, se nao pode. Funcao pura,
    usada pelo adaptador real e pelo falso (DP-S-21).

    Vazia e so de espacos no sentido de `str.isspace()` (R-CG5-6 de U5): o
    `strip()` corta exatamente esses caracteres. O que nao e texto nao tem
    texto, e conta como vazia.
    """
    if not isinstance(texto, str) or not texto.strip():
        return FalhaDoTurno(MotivoFalhaDeSessao.MENSAGEM_INVALIDA, {"problema": VAZIA})
    if len(texto) > MAXIMO_DE_CARACTERES:
        return FalhaDoTurno(
            MotivoFalhaDeSessao.MENSAGEM_INVALIDA,
            {"problema": LONGA_DEMAIS, "maximo": str(MAXIMO_DE_CARACTERES)},
        )
    return None


# --------------------------------------------------------------------------
# Erros (domain-entities.md 7)
# --------------------------------------------------------------------------
# Erros de montagem: aparecem por defeito de quem monta (U7, U8, U9) ou por um
# Agente adulterado no banco (R-FD6-9). Nunca por causa do provedor.


class ErroDeSessao(Exception):
    """Raiz da hierarquia."""


class ConfiguracaoDeSessaoInvalida(ErroDeSessao):
    """`abrir` recusou o agente: nome desconhecido ou repetido, R10, ou uma
    fabrica defeituosa (RN-S-06..08). `violacoes` traz as violacoes de escopo
    achadas, quando foi isso; fica vazio quando foi a fabrica."""

    def __init__(self, mensagem: str, violacoes: tuple[object, ...] = ()) -> None:
        super().__init__(mensagem)
        self.violacoes = violacoes


class AdaptadorEncerrado(ErroDeSessao):
    """`abrir` depois de `encerrar()` (G7, RN-S-39): nenhum processo nasce
    depois do fim do programa."""


class RegistroInvalido(ErroDeSessao):
    """O registro de ferramentas foi montado errado (RN-S-14): nome fora do
    padrao, repetido, familia desconhecida."""


# --------------------------------------------------------------------------
# A porta (domain-entities.md 2.1)
# --------------------------------------------------------------------------


class PortaSessao(Protocol):
    """O ciclo de vida de uma conversa com o provedor."""

    async def abrir(self, agente: Agente, contexto: ContextoDaSessao) -> SessaoViva:
        """So prepara: verifica e fabrica as ferramentas, e NAO sobe processo
        (Q2=B). Levanta so ConfiguracaoDeSessaoInvalida e AdaptadorEncerrado,
        nunca por causa do provedor. A sessao nasce em SEM_CONEXAO."""
        ...

    def enviar(self, sessao: SessaoViva, mensagem: str) -> AsyncIterator[EventoConversa]:
        """Um turno: entrega a mensagem e transmite os eventos ate um evento
        final, na gramatica de RN-S-17.

        NUNCA levanta (RN-S-16): toda falha chega como FalhaDoTurno, o ultimo
        evento. So o cancelamento passa. Cancelar quem le, ou abandonar o
        iterador, e interromper (G6): as ferramentas em execucao sao
        canceladas e o provedor e avisado (RN-S-35).
        """
        ...

    async def fechar(self, sessao: SessaoViva) -> None:
        """Encerra a sessao de vez (RN-S-37). Um turno em andamento termina em
        FalhaDoTurno(SESSAO_FECHADA). Volta so com o processo morto (DP-S-06).
        Nunca levanta; fechar de novo nao faz nada."""
        ...
