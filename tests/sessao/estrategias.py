"""Geradores de Hypothesis para U6, e o que todo teste da unidade monta igual.

Reaproveita U4 (`executar`, `ambientes_de_partida`, ORQUESTRADOR,
BIBLIOTECARIO, `ponderado`) e U5 (`montar`, `tarefas_de`, `alvo_da_tarefa`,
`ambientes_de_uma_tarefa`, `palavras`, ESPACOS) em vez de redefinir (PBT-07):
o catalogo atras das ferramentas de ambiente e o mesmo, com o servico real.

Os roteiros do provedor sao listas de passos do cliente roteirizado, com
mensagens no formato do SDK (os tipos de verdade de `claude_agent_sdk`).
"""

import asyncio
import string
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from claude_agent_sdk import (
    CLIConnectionError,
    CLIJSONDecodeError,
    CLINotFoundError,
    ProcessError,
    TextBlock,
)
from claude_agent_sdk._errors import ResultError
from hypothesis import strategies as st

from fishingrod.adaptadores.sessao import AdaptadorSessaoClaude
from fishingrod.aplicacao.catalogo.registro import ACOES
from fishingrod.aplicacao.catalogo.tipos import Parametro, TipoParametro
from fishingrod.aplicacao.ferramentas import (
    EntradaDoRegistro,
    Ferramenta,
    RegistroDeFerramentas,
    RespostaDaFerramenta,
)
from fishingrod.aplicacao.portas.sessao import ContextoDaSessao, Familia
from fishingrod.dominio import Agente, Chamador, Identidade, Papel
from tests.acoes.estrategias import ESPACOS, palavras
from tests.ambiente.estrategias import BIBLIOTECARIO, ORQUESTRADOR, executar, ponderado
from tests.sessao.cliente_roteirizado import (
    Acabar,
    ChamarFerramenta,
    FabricaRoteirizada,
    Levantar,
    Mensagem,
    Passo,
    assistente,
    inicio_de_ferramenta,
    inicio_de_mensagem,
    inicio_de_texto,
    limite,
    pedido,
    pensamento,
    resultado,
    resultado_de_ferramenta,
    sistema,
    trecho,
    trecho_de_ferramenta,
    trecho_de_pensamento,
)

__all__ = ["BIBLIOTECARIO", "ORQUESTRADOR", "executar"]

# Prazos curtos: nenhum teste espera os 60 s ou os 5 s (DP-S-08).
PRAZO_DE_SUBIDA = 0.5
PRAZO_DE_INTERRUPCAO = 0.3

# So as que o agente aciona: criar_sessao e do usuario (D21) e nao vira
# ferramenta.
NOMES_DAS_ACOES = tuple(acao.nome for acao in ACOES if Chamador.AGENTE in acao.chamadores)
NOMES_DE_WIKI = ("listar", "ler", "propor_entidade", "propor_propriedade")
NOMES_INEXISTENTES = ("apagar_tudo", "criar_projeto", "ler_arquivo")


# --------------------------------------------------------------------------
# Contexto, agente, registro
# --------------------------------------------------------------------------


def contexto_novo() -> ContextoDaSessao:
    return ContextoDaSessao(*(Identidade.nova() for _ in range(5)))


async def _responder_ok(argumentos: Any) -> RespostaDaFerramenta:
    return RespostaDaFerramenta('{"ok":true}')


ESQUEMA_ABERTO = {"type": "object", "properties": {}, "additionalProperties": True}


def fabrica_simples(
    nome: str,
    executar_: Callable[[Any], Awaitable[RespostaDaFerramenta]] = _responder_ok,
    esquema: dict | None = None,
) -> Callable[[ContextoDaSessao, Agente], Ferramenta]:
    def fabricar(contexto: ContextoDaSessao, agente: Agente) -> Ferramenta:
        return Ferramenta(nome, f"ferramenta {nome}", esquema or ESQUEMA_ABERTO, executar_)

    return fabricar


def registro_de_teste() -> RegistroDeFerramentas:
    """Os 6 nomes de acao na familia AMBIENTE e 4 nomes de wiki de teste, com
    fabricas simples: o que PBT-U6-08 precisa e o NOME e a FAMILIA."""
    return RegistroDeFerramentas(
        [EntradaDoRegistro(nome, Familia.AMBIENTE, fabrica_simples(nome)) for nome in NOMES_DAS_ACOES]
        + [EntradaDoRegistro(nome, Familia.WIKI, fabrica_simples(nome)) for nome in NOMES_DE_WIKI]
    )


@st.composite
def agentes_quaisquer(draw: Any) -> Agente:
    """Os dois papeis e ferramentas sorteadas entre as 6 acoes, os 4 de wiki e
    nomes que nao existem - com repeticao."""
    nomes = draw(
        st.lists(st.sampled_from(NOMES_DAS_ACOES + NOMES_DE_WIKI + NOMES_INEXISTENTES), max_size=6)
    )
    return Agente(
        nome=draw(st.sampled_from(["orquestrador", "bibliotecario", "outro"])),
        papel=draw(st.sampled_from(list(Papel))),
        modelo="modelo-de-teste",
        ferramentas=tuple(nomes),
    )


def agente(nome: str = "bibliotecario", *, ferramentas: tuple[str, ...] = (), regras: tuple[str, ...] = ()) -> Agente:
    papel = Papel.ORQUESTRADOR if nome == "orquestrador" else Papel.SUB_AGENTE
    return Agente(nome, papel, "modelo-de-teste", ferramentas=ferramentas, regras=regras)


def adaptador(
    fabrica: FabricaRoteirizada,
    registro: RegistroDeFerramentas | None = None,
    pasta: Path | None = None,
    prazo_de_subida: float = PRAZO_DE_SUBIDA,
    prazo_de_interrupcao: float = PRAZO_DE_INTERRUPCAO,
) -> AdaptadorSessaoClaude:
    return AdaptadorSessaoClaude(
        registro or registro_de_teste(),
        pasta or Path.cwd(),
        fabrica,
        prazo_de_subida=prazo_de_subida,
        prazo_de_interrupcao=prazo_de_interrupcao,
    )


async def coletar(iterador: Any) -> list:
    return [evento async for evento in iterador]


async def esperar_que(condicao: Callable[[], bool], prazo: float = 3.0) -> None:
    """Espera a condicao valer, cedendo o laco. Para o que acontece na tarefa
    dona depois de o leitor sair (a cauda, o fechamento)."""
    fim = asyncio.get_running_loop().time() + prazo
    while not condicao():
        if asyncio.get_running_loop().time() > fim:
            raise AssertionError("a condicao nao valeu no prazo")
        await asyncio.sleep(0.001)


# --------------------------------------------------------------------------
# Parametros (PBT-U6-05)
# --------------------------------------------------------------------------

_NOMES_SNAKE = st.from_regex(r"[a-z][a-z0-9]{0,6}(_[a-z0-9]{1,4}){0,2}", fullmatch=True)


@st.composite
def parametros_validos(draw: Any) -> tuple[Parametro, ...]:
    """Listas de 0 a 6 Parametro validas por RN-AC-08: nomes unicos,
    obrigatorios antes dos opcionais, TEXTO com maximo, ESCOLHA com opcoes
    unicas, no maximo uma POSICAO."""
    nomes = draw(st.lists(_NOMES_SNAKE, max_size=6, unique=True))
    obrigatorios = draw(st.integers(min_value=0, max_value=len(nomes)))
    posicao_usada = False
    parametros = []
    for indice, nome in enumerate(nomes):
        tipos = [TipoParametro.TEXTO, TipoParametro.ESCOLHA] + ([] if posicao_usada else [TipoParametro.POSICAO])
        tipo = draw(st.sampled_from(tipos))
        descricao = draw(st.text(min_size=1, max_size=20))
        obrigatorio = indice < obrigatorios
        if tipo is TipoParametro.TEXTO:
            maximo = draw(st.integers(min_value=1, max_value=20_000))
            parametros.append(Parametro(nome, tipo, descricao, obrigatorio=obrigatorio, maximo=maximo))
        elif tipo is TipoParametro.ESCOLHA:
            opcoes = draw(st.lists(st.text(string.ascii_lowercase, min_size=1, max_size=8), min_size=1, max_size=4, unique=True))
            parametros.append(Parametro(nome, tipo, descricao, obrigatorio=obrigatorio, opcoes=tuple(opcoes)))
        else:
            posicao_usada = True
            parametros.append(Parametro(nome, tipo, descricao, obrigatorio=obrigatorio))
    return tuple(parametros)


# --------------------------------------------------------------------------
# Texto partido em trechos (PBT-U6-02)
# --------------------------------------------------------------------------

# Unicode sem surrogate: espacos, tabulacao, quebra de linha, acento, emoji.
_CARACTERES = st.characters(exclude_categories=("Cs",)) | st.sampled_from(" \t\nãçé🎣")
blocos_de_texto = st.text(_CARACTERES, min_size=1, max_size=30)


@st.composite
def partido(draw: Any, texto: str) -> list[str]:
    """Os trechos de um bloco: o bloco todo, so o comeco dele, ou nenhum - e
    os cortes em qualquer lugar. Nenhum trecho vazio, como o SDK."""
    ate = draw(ponderado((3, st.just(len(texto))), (1, st.integers(min_value=0, max_value=len(texto)))))
    cortes = sorted(draw(st.sets(st.integers(min_value=1, max_value=max(ate - 1, 1)), max_size=5)))
    cortes = [c for c in cortes if 0 < c < ate]
    pontos = [0, *cortes, ate]
    return [texto[a:b] for a, b in zip(pontos, pontos[1:]) if b > a]


def passos_de_bloco(indice: int, texto: str, trechos: list[str]) -> list[Passo]:
    """Os trechos (StreamEvent) e depois o bloco completo (AssistantMessage),
    como o SDK manda com as mensagens parciais ligadas."""
    passos: list[Passo] = [Mensagem(inicio_de_texto(indice))]
    passos += [Mensagem(trecho(indice, t)) for t in trechos]
    passos.append(Mensagem(assistente(TextBlock(texto))))
    return passos


# --------------------------------------------------------------------------
# Excecoes (PBT-U6-03)
# --------------------------------------------------------------------------

excecoes_do_sdk = st.sampled_from(
    [
        lambda: CLINotFoundError("cli ausente"),
        lambda: CLIConnectionError("conexao caiu"),
        lambda: ProcessError("processo morreu", exit_code=1),
        lambda: ResultError("resultado com erro", {"subtype": "error_during_execution"}),
        lambda: CLIJSONDecodeError("{lixo", ValueError("json")),
        lambda: Exception("Control request timeout: initialize"),
    ]
)
excecoes_quaisquer = st.sampled_from(
    [lambda: RuntimeError("defeito"), lambda: KeyError("chave"), lambda: OSError("disco"), lambda: ValueError("valor")]
)
excecoes = st.one_of(excecoes_do_sdk, excecoes_quaisquer).map(lambda fazer: fazer())


# --------------------------------------------------------------------------
# Roteiros do provedor (PBT-U6-01)
# --------------------------------------------------------------------------

# Os desfechos de um turno roteirizado.
BEM = "bem"
COM_ERRO = "com_erro"
SINAL = "sinal"
EXCECAO = "excecao"
FIM_DO_FLUXO = "fim_do_fluxo"


@dataclass(frozen=True)
class Roteiro:
    """Um turno gerado: os passos, e o que se sabe dele para conferir."""

    passos: tuple[Passo, ...]
    desfecho: str
    tem_resposta: bool  # houve texto ou pedido de ferramenta da sessao
    textos: tuple[str, ...] = ()
    sinal: object = None
    excecao: BaseException | None = None
    usos: tuple[str, ...] = field(default=())


SINAIS = ("authentication_failed", "rate_limit", "billing_error", "server_error", "unknown", "invalid_request")


@st.composite
def roteiros(draw: Any, da_sessao: tuple[str, ...] = ("mcp__wiki__ler",), de_fora: tuple[str, ...] = ("mcp__ambiente__criar_frente", "Bash")) -> Roteiro:
    """0 a 4 blocos de texto partidos em 0 a 5 trechos; 0 a 3 pedidos da sessao
    e 0 a 2 de fora; pensamento, resultado de ferramenta, sistema e limite
    informativo intercalados; desfecho sorteado."""
    passos: list[Passo] = [Mensagem(inicio_de_mensagem())]
    textos: list[str] = []
    usos: list[str] = []
    indice = 0
    unidades = draw(
        st.lists(
            st.sampled_from(["texto", "texto", "da_sessao", "de_fora", "ruido"]), max_size=8
        )
    )
    contagem = {"texto": 0, "da_sessao": 0, "de_fora": 0}
    for unidade in unidades:
        if unidade == "texto" and contagem["texto"] < 4:
            contagem["texto"] += 1
            texto = draw(blocos_de_texto)
            passos += passos_de_bloco(indice, texto, draw(partido(texto)))
            textos.append(texto)
            indice += 1
        elif unidade == "da_sessao" and contagem["da_sessao"] < 3 and da_sessao:
            contagem["da_sessao"] += 1
            nome = draw(st.sampled_from(da_sessao))
            passos += [
                Mensagem(inicio_de_ferramenta(indice, nome)),
                Mensagem(trecho_de_ferramenta(indice, '{"a": ')),
                Mensagem(pedido(nome, {"a": draw(palavras)})),
            ]
            usos.append(nome)
            indice += 1
        elif unidade == "de_fora" and contagem["de_fora"] < 2:
            contagem["de_fora"] += 1
            passos.append(Mensagem(pedido(draw(st.sampled_from(de_fora)))))
        elif unidade == "ruido":
            passos.append(
                Mensagem(
                    draw(
                        st.sampled_from(
                            [pensamento(), resultado_de_ferramenta(), sistema(), limite("allowed"), limite("allowed_warning"), trecho_de_pensamento(indice)]
                        )
                    )
                )
            )
    desfecho = draw(st.sampled_from([BEM, BEM, COM_ERRO, SINAL, SINAL, EXCECAO, FIM_DO_FLUXO]))
    sinal = excecao = None
    if desfecho == BEM:
        passos.append(resultado())
    elif desfecho == COM_ERRO:
        passos.append(resultado(erro=True, subtipo="error_during_execution"))
    elif desfecho == SINAL:
        sinal = draw(st.sampled_from(SINAIS + ("rejected",)))
        if sinal == "rejected":
            passos.append(Mensagem(limite("rejected", resets_at=draw(st.none() | st.integers(0, 2_000_000_000)))))
        else:
            passos.append(Mensagem(assistente(TextBlock("API Error"), erro=sinal)))
        passos.append(resultado(erro=draw(st.booleans())))
    elif desfecho == EXCECAO:
        excecao = draw(excecoes)
        passos.append(Levantar(excecao))
    else:
        passos.append(Acabar())
    return Roteiro(
        tuple(passos),
        desfecho,
        tem_resposta=bool(textos or usos),
        textos=tuple(textos),
        sinal=sinal,
        excecao=excecao,
        usos=tuple(usos),
    )


def com_chamada(passos: tuple[Passo, ...], nome: str, argumentos: dict) -> tuple[Passo, ...]:
    """Os mesmos passos, com o CLI chamando a ferramenta antes do resultado."""
    return (*passos[:-1], ChamarFerramenta(nome, argumentos), passos[-1])


__all__ += [
    "ESPACOS",
    "ponderado",
]
