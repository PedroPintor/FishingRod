"""O tradutor: as mensagens do SDK de um turno viram eventos da porta (RN-S-17..24).

Puro (DP-S-19): sem asyncio, sem I/O, sem log. Recebe uma mensagem por vez e
devolve os eventos e os avisos que ela gerou; o adaptador emite e registra.

DP-S-10: o evento final e decidido num lugar so. O tradutor acumula o turno -
houve texto? houve uso de ferramenta? chegou sinal de falha? - e so decide no
fim da resposta (`final`) ou na queda (`queda`). O primeiro sinal tipado vence;
sem sinal, vale a mensagem de resultado; sem erro, vale RN-S-24.

O texto chega aos poucos (Q1=B). Com as mensagens parciais ligadas, o SDK manda
os trechos (`StreamEvent`) e depois o bloco completo (`AssistantMessage`). O
bloco completo e a referencia (RN-S-19): se os trechos cobriram o bloco, nada
mais sai; se cobriram so o comeco, sai o que falta; se nenhum trecho chegou,
sai o bloco inteiro; se divergem, um aviso, e nada mais sai daquele bloco.
"""

import logging
from collections import deque
from collections.abc import Collection
from dataclasses import dataclass, field, replace

from claude_agent_sdk import (
    AssistantMessage,
    RateLimitEvent,
    ResultMessage,
    ServerToolUseBlock,
    StreamEvent,
    TextBlock,
    ToolUseBlock,
)

from fishingrod.adaptadores.sessao.falhas import (
    RESPOSTA_VAZIA,
    Aviso,
    Causa,
    Classificacao,
    ErroDoAssistente,
    Fase,
    LimiteAtingido,
    ResultadoComErro,
    classificar,
)
from fishingrod.adaptadores.sessao.ferramentas import separar
from fishingrod.aplicacao.portas.sessao import (
    EventoConversa,
    Familia,
    FimDeTurno,
    PedacoDeTexto,
    UsoDeFerramenta,
)

# G3: blocos de texto do mesmo turno sao separados por uma linha em branco,
# posta no comeco do primeiro pedaco do bloco seguinte.
SEPARADOR = "\n\n"

# Um nome pedido pelo modelo vai ao aviso cortado: e texto de quem nao e
# confiavel.
_ECO_MAXIMO = 100


@dataclass(frozen=True)
class Traducao:
    eventos: tuple[EventoConversa, ...] = ()
    avisos: tuple[Aviso, ...] = ()


@dataclass
class _Bloco:
    """Um bloco de texto que esta chegando aos poucos."""

    trechos: list[str] = field(default_factory=list)
    emitiu: bool = False


class Tradutor:
    """Um por turno. `ferramentas` sao os pares (familia, nome) da sessao: so
    eles viram UsoDeFerramenta (RN-S-22)."""

    def __init__(self, ferramentas: Collection[tuple[Familia, str]]) -> None:
        self._da_sessao = frozenset(ferramentas)
        self._houve_texto = False
        self._houve_uso = False
        self._sinal: Causa | None = None
        # Os blocos de texto em transmissao, na ordem em que comecaram. Os
        # blocos completos chegam na mesma ordem.
        self._em_transmissao: deque[_Bloco] = deque()
        # Os da mensagem da API corrente, pelo indice que o StreamEvent usa.
        self._por_indice: dict[object, _Bloco] = {}

    # ----------------------------------------------------------------------
    # Uma mensagem
    # ----------------------------------------------------------------------

    def traduzir(self, mensagem: object) -> Traducao:
        eventos: list[EventoConversa] = []
        avisos: list[Aviso] = []
        match mensagem:
            case StreamEvent(event=evento) if isinstance(evento, dict):
                self._trecho(evento, eventos)
            case AssistantMessage(error=erro) if erro is not None:
                # O conteudo de uma mensagem com erro e texto do CLI, nao do
                # modelo: nao vira pedaco. So o sinal conta.
                self._sinalizar(ErroDoAssistente(str(erro)))
            case AssistantMessage(content=blocos):
                for bloco in blocos:
                    self._bloco_completo(bloco, eventos, avisos)
            case RateLimitEvent(rate_limit_info=info) if getattr(info, "status", None) == "rejected":
                self._sinalizar(LimiteAtingido(info.resets_at))
            # Pensamento, resultados de ferramenta, mensagens de sistema e o
            # resto nao viram evento (RN-S-21, RN-S-23).
        return Traducao(tuple(eventos), tuple(avisos))

    def _trecho(self, evento: dict, eventos: list[EventoConversa]) -> None:
        match evento.get("type"):
            case "message_start":
                self._por_indice = {}
            case "content_block_start":
                inicio = evento.get("content_block")
                if isinstance(inicio, dict) and inicio.get("type") == "text":
                    bloco = self._novo_bloco(evento.get("index"))
                    texto = inicio.get("text")
                    if isinstance(texto, str) and texto:
                        bloco.trechos.append(texto)
                        self._emitir(bloco, texto, eventos)
            case "content_block_delta":
                delta = evento.get("delta")
                if isinstance(delta, dict) and delta.get("type") == "text_delta":
                    texto = delta.get("text")
                    if isinstance(texto, str) and texto:
                        bloco = self._por_indice.get(evento.get("index")) or self._novo_bloco(evento.get("index"))
                        bloco.trechos.append(texto)
                        self._emitir(bloco, texto, eventos)
            # Trechos de pedido de ferramenta e de pensamento nao viram evento
            # (G9): os argumentos parciais sao JSON pela metade.

    def _novo_bloco(self, indice: object) -> _Bloco:
        bloco = _Bloco()
        self._em_transmissao.append(bloco)
        self._por_indice[indice] = bloco
        return bloco

    def _bloco_completo(self, bloco: object, eventos: list[EventoConversa], avisos: list[Aviso]) -> None:
        match bloco:
            case TextBlock(text=texto):
                transmitido = self._em_transmissao.popleft() if self._em_transmissao else _Bloco()
                recebido = "".join(transmitido.trechos)
                if texto == recebido:
                    return
                if texto.startswith(recebido):
                    self._emitir(transmitido, texto[len(recebido) :], eventos)
                    return
                avisos.append(
                    Aviso(
                        logging.WARNING,
                        "trechos divergentes do bloco de texto completo (%d de %d caracteres): "
                        "nada mais sai deste bloco",
                        (len(recebido), len(texto)),
                    )
                )
            case ToolUseBlock(name=nome, input=argumentos):
                par = separar(nome)
                if par is not None and par in self._da_sessao:
                    familia, nome_curto = par
                    eventos.append(
                        UsoDeFerramenta(familia, nome_curto, argumentos if isinstance(argumentos, dict) else {})
                    )
                    self._houve_uso = True
                else:
                    avisos.append(_de_fora(nome))
            case ServerToolUseBlock(name=nome):
                avisos.append(_de_fora(nome))
            # ThinkingBlock, ToolResultBlock, ServerToolResultBlock: nada.

    def _emitir(self, bloco: _Bloco, texto: str, eventos: list[EventoConversa]) -> None:
        if not texto:
            return
        if not bloco.emitiu and self._houve_texto:
            texto = SEPARADOR + texto
        bloco.emitiu = True
        self._houve_texto = True
        eventos.append(PedacoDeTexto(texto))

    def _sinalizar(self, sinal: Causa) -> None:
        """O primeiro sinal vence. A unica troca: um `rate_limit` do
        assistente seguido do evento de limite, que traz quando libera - o
        motivo e o mesmo, so com mais informacao."""
        if self._sinal is None:
            self._sinal = sinal
        elif self._sinal == ErroDoAssistente("rate_limit") and isinstance(sinal, LimiteAtingido):
            self._sinal = sinal

    # ----------------------------------------------------------------------
    # O fim
    # ----------------------------------------------------------------------

    @property
    def sinal(self) -> Causa | None:
        """O sinal que decidiu (ou vai decidir) o fim - para o log dizer qual."""
        return self._sinal

    def final(self, resultado: ResultMessage) -> FimDeTurno | Classificacao:
        """No fim da resposta (DP-S-10)."""
        if self._sinal is None and getattr(resultado, "is_error", False):
            self._sinal = ResultadoComErro(
                getattr(resultado, "subtype", None), getattr(resultado, "api_error_status", None)
            )
        if self._sinal is not None:
            return classificar(Fase.RESPOSTA, self._sinal)
        if self._houve_texto or self._houve_uso:
            return FimDeTurno()
        return RESPOSTA_VAZIA

    def queda(self, fase: Fase, causa: Causa) -> Classificacao:
        """A dona caiu: a conexao ja esta indo embora, entao derruba sempre.
        Um sinal que chegou antes ainda vence, porque e a causa mais
        precisa."""
        if self._sinal is not None:
            return replace(classificar(Fase.RESPOSTA, self._sinal), derruba=True)
        return classificar(fase, causa)


def _de_fora(nome: object) -> Aviso:
    """RN-S-22, G8: nao vira evento - o SDK nega -, mas vai para o log, que e
    onde uma tentativa de abuso deve aparecer."""
    return Aviso(logging.WARNING, "pedido de ferramenta de fora da sessao: [%s]", (str(nome)[:_ECO_MAXIMO],))
