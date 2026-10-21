"""Os tipos do catalogo de acoes (U5): o registro, quem e onde, a confirmacao
e o Resultado.

Este e o vocabulario com que a tela (U9), o agente (U6) e o catalogo conversam
(domain-entities.md). Nenhuma entidade de dominio nasce aqui: Ambiente, Frente,
Tarefa, Sessao, Etapa, Chat e Anotacao continuam sendo de U1.

RN-AC-01: sem I/O e sem nada de fora do dominio. O ServicoDeAmbiente aparece so
na anotacao de tipo de `Efetivar`, importado sob TYPE_CHECKING: em tempo de
execucao este modulo nao carrega o servico, e por isso parser.py e argumentos.py
continuam puros mesmo importando daqui.
"""

from collections.abc import Awaitable, Callable, Mapping
from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType
from typing import TYPE_CHECKING

from fishingrod.dominio import Chamador, Etapa, Frente, Identidade, Sessao, Tarefa

if TYPE_CHECKING:
    from fishingrod.aplicacao.servicos.servico_de_ambiente import ServicoDeAmbiente


# --------------------------------------------------------------------------
# O registro (domain-entities.md 2)
# --------------------------------------------------------------------------


class Escopo(Enum):
    """Em que nivel da arvore a acao age - e, por isso, que identidades o Alvo
    precisa ter (RN-AC-10). Etapa nao e escopo (R-FD5-4): e argumento,
    apontada pela posicao."""

    AMBIENTE = "ambiente"
    FRENTE = "frente"
    TAREFA = "tarefa"
    SESSAO = "sessao"


class TipoParametro(Enum):
    """Como um argumento e lido e validado (domain-entities.md 2.2)."""

    TEXTO = "texto"
    ESCOLHA = "escolha"
    POSICAO = "posicao"


@dataclass(frozen=True)
class Parametro:
    """Um argumento de uma acao. A forma e verificada ao construir o catalogo
    (RN-AC-08), e nao aqui: um registro mal montado e erro de montagem do
    catalogo, e e la que CatalogoInvalido nasce.

    `opcoes` so existe em ESCOLHA; `maximo` (numero de caracteres, G10) so em
    TEXTO.
    """

    nome: str
    tipo: TipoParametro
    descricao: str
    obrigatorio: bool = True
    opcoes: tuple[str, ...] = ()
    maximo: int | None = None


@dataclass(frozen=True)
class Alvo:
    """As identidades sobre as quais a acao age. Sempre explicito: nunca "o item
    ativo" escondido no nucleo.

    Cada escopo usa so as identidades que exige; as demais sao ignoradas
    (RN-AC-10). Para o agente, quem monta e U9, ao abrir o chat, e o agente nao
    consegue muda-lo (RN-AC-11).
    """

    id_ambiente: Identidade
    id_frente: Identidade | None = None
    id_tarefa: Identidade | None = None
    id_sessao: Identidade | None = None


# O autor que assina o que o usuario escreve - o mesmo texto que U4 e a tela
# ja usam.
AUTOR_USUARIO = "usuario"


@dataclass(frozen=True)
class Acionamento:
    """Quem acionou e o nome que assina o que for escrito.

    Construido pelo sistema - a tela para o usuario, U9 ao abrir o chat para o
    agente -, nunca a partir de algo que o agente escreveu (RN-AC-12). E o
    autor da anotacao de memoria (RN-AC-13).
    """

    chamador: Chamador
    autor: str

    @classmethod
    def usuario(cls) -> "Acionamento":
        return cls(Chamador.USUARIO, AUTOR_USUARIO)

    @classmethod
    def agente(cls, nome: str) -> "Acionamento":
        return cls(Chamador.AGENTE, nome)


# --------------------------------------------------------------------------
# Confirmacao (domain-entities.md 4)
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class EtapaNaPosicao:
    """Uma etapa junto com a posicao dela (1, 2, 3...) na tarefa.

    A posicao e linguagem de apontar, nao identidade: nao e guardada em lugar
    nenhum, e o servico continua recebendo o id (Q8=A, RF-F16).
    """

    etapa: Etapa
    posicao: int


@dataclass(frozen=True)
class Referencias:
    """O que o alvo e os argumentos apontam, ja achado no ambiente aberto antes
    de pedir confirmacao (G2). E leitura: o catalogo nao muda nenhum destes
    objetos (RN-AC-02)."""

    frente: Frente | None = None
    tarefa: Tarefa | None = None
    sessao: Sessao | None = None
    etapa: EtapaNaPosicao | None = None


@dataclass(frozen=True)
class PedidoDeConfirmacao:
    """O que a tela mostra quando um agente pede uma acao - e exatamente o que
    vai executar depois do "sim" (RN-AC-22, RN-AC-31).

    Os argumentos ficam numa copia somente leitura: nem a porta, nem quem
    montou o pedido, consegue mudar depois o que vai executar.
    """

    acao: str
    acionamento: Acionamento
    alvo: Alvo
    argumentos: Mapping[str, object]
    referencias: Referencias

    def __post_init__(self) -> None:
        object.__setattr__(self, "argumentos", MappingProxyType(dict(self.argumentos)))


# --------------------------------------------------------------------------
# Como uma acao termina (domain-entities.md 5)
# --------------------------------------------------------------------------


class MotivoFalha(Enum):
    """Por que uma acao nao aconteceu (Q10=A). O valor e o que o agente le; a
    frase em portugues e da tela (RN-AC-35)."""

    ACAO_DESCONHECIDA = "acao_desconhecida"
    NAO_PERMITIDA = "nao_permitida"
    ARGUMENTO_INVALIDO = "argumento_invalido"
    ALVO_AUSENTE = "alvo_ausente"
    ALVO_INEXISTENTE = "alvo_inexistente"
    REGRA_VIOLADA = "regra_violada"
    CONFLITO = "conflito"
    FALHA_DE_ARMAZENAMENTO = "falha_de_armazenamento"
    RECUSADA = "recusada"
    FALHA_INESPERADA = "falha_inesperada"


@dataclass(frozen=True)
class Resultado:
    """Como toda acao termina, quando executada pelo catalogo (criterio 3).

    As invariantes de RN-AC-35 sao verificadas na construcao, e nao so
    prometidas: `sucesso` se e somente se nao ha `motivo`; `dado` so no sucesso;
    `detalhe` so na falha, de texto para texto. Um Resultado que as quebra e
    defeito de quem o montou, e levanta ValueError. Quem constroi deve usar
    `ok` e `falha`, que nunca as quebram.
    """

    sucesso: bool
    motivo: MotivoFalha | None = None
    detalhe: Mapping[str, str] = field(default_factory=dict)
    dado: object | None = None

    def __post_init__(self) -> None:
        if self.sucesso != (self.motivo is None):
            raise ValueError("Resultado: sucesso exige motivo None, e falha exige motivo")
        if self.motivo is not None and not isinstance(self.motivo, MotivoFalha):
            raise ValueError("Resultado: motivo precisa ser um MotivoFalha")
        if self.sucesso and self.detalhe:
            raise ValueError("Resultado: detalhe so existe na falha")
        if not self.sucesso and self.dado is not None:
            raise ValueError("Resultado: dado so existe no sucesso")
        if not all(isinstance(c, str) and isinstance(v, str) for c, v in self.detalhe.items()):
            raise ValueError("Resultado: detalhe e de texto para texto")
        object.__setattr__(self, "detalhe", MappingProxyType(dict(self.detalhe)))

    @classmethod
    def ok(cls, dado: object | None = None) -> "Resultado":
        return cls(sucesso=True, dado=dado)

    @classmethod
    def falha(cls, motivo: MotivoFalha, **detalhe: object) -> "Resultado":
        """Os valores do detalhe viram texto aqui: posicao e total chegam como
        int, e o agente le tudo como texto de qualquer jeito."""
        return cls(
            sucesso=False,
            motivo=motivo,
            detalhe={chave: str(valor) for chave, valor in detalhe.items()},
        )


# --------------------------------------------------------------------------
# A acao (domain-entities.md 2.4)
# --------------------------------------------------------------------------

# Chama UMA operacao do servico e devolve o objeto que ela devolveu, ou deixa a
# excecao subir. Nao devolve Resultado (G1): quem traduz e o catalogo, num ponto
# so. Recebe os argumentos ja convertidos e as referencias ja achadas; nao
# valida, nao consulta politica e nao captura excecao.
type Efetivar = Callable[
    ["ServicoDeAmbiente", Alvo, Mapping[str, object], Referencias, Acionamento],
    Awaitable[object],
]


@dataclass(frozen=True)
class Acao:
    """Uma acao do ambiente, como dado (RN-AC-05).

    `nome` e snake_case: e o nome da ferramenta do agente, e vira o comando da
    barra trocando `_` por `-` (RN-AC-07). `chamadores` diz quem pode aciona-la
    (RN-AC-06).
    """

    nome: str
    descricao: str
    escopo: Escopo
    parametros: tuple[Parametro, ...]
    chamadores: frozenset[Chamador]
    efetivar: Efetivar = field(repr=False, compare=False)


# --------------------------------------------------------------------------
# Erros (domain-entities.md 7)
# --------------------------------------------------------------------------


class ErroDoCatalogo(Exception):
    """Raiz dos erros do catalogo. Fora da montagem, o catalogo nao levanta:
    toda falha de uso vira Resultado (RN-AC-34)."""


class CatalogoInvalido(ErroDoCatalogo):
    """RN-AC-08: registro mal formado, descoberto ao construir o catalogo. E
    erro de montagem, nao de uso - e a unica excecao que o catalogo levanta."""
