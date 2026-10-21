"""O servico de conversa: a tela conversa com os agentes so por aqui (card 002).

Um por programa. Para cada chat, guarda a sessao viva - aberta uma vez e
reaproveitada em toda mensagem, para nao deixar processo fantasma -, a fila
das mensagens que esperam a resposta acabar e a conversa que a tela mostra.
Grava cada mensagem no banco, e sabe quantas conexoes estao abertas.

O turno roda numa tarefa do servico, e nao da tela: a tela redesenha os chats
(trocar de sessao, abrir a memoria), e uma tarefa dela seria cancelada junto -
o que, para a porta, e interromper. A tela so escuta (`ouvir`).

Os avisos sao gravados como mensagens de papel "aviso", com um codigo, e nao
uma frase: a frase em portugues e da tela, como no catalogo (RN-AC-35).
"""

import asyncio
import json
import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum

from fishingrod.aplicacao.portas.persistencia import PortaPersistencia
from fishingrod.aplicacao.portas.sessao import (
    ContextoDaSessao,
    ErroDeSessao,
    FalhaDoTurno,
    FimDeTurno,
    MensagemEntregue,
    MotivoFalhaDeSessao,
    PedacoDeTexto,
    PortaSessao,
    SessaoViva,
    UsoDeFerramenta,
)
from fishingrod.dominio import Agente, Identidade

_log = logging.getLogger("fishingrod.conversa")
_log.addHandler(logging.NullHandler())

USUARIO = "usuario"
AGENTE = "agente"
AVISO = "aviso"

# Quantas mensagens a tela carrega ao abrir um chat. Ver "Pode melhorar" no
# card 002: em conversas longas, da para carregar menos.
MENSAGENS_AO_ABRIR = 500

# O que fica no fim do texto de uma resposta interrompida, inclusive no banco.
MARCA_DE_INTERROMPIDA = "(interrompida)"

# Os codigos dos avisos que nao sao motivo de falha da porta.
CONVERSA_RECOMECOU = "conversa_recomecou"
ACAO_RECUSADA = "acao_recusada"

# O resumo dos argumentos de uma ferramenta que vai ao banco.
_RESUMO_MAXIMO = 200


class EstadoDoChat(Enum):
    PRONTO = "pronto"  # nenhum processo: a proxima mensagem liga
    LIGADO = "ligado"  # o processo esta de pe, esperando
    RESPONDENDO = "respondendo"


@dataclass
class Linha:
    """Uma mensagem como a tela mostra. `usos` sao as ferramentas que o
    agente pediu nesta resposta; `em_andamento`, que ela ainda esta chegando
    (ou que o programa fechou no meio dela)."""

    papel: str
    texto: str
    usos: list[str] = field(default_factory=list)
    em_andamento: bool = False
    id: Identidade | None = None


def aviso(codigo: str, detalhe: str = "") -> str:
    """O texto de uma linha de aviso: o codigo e, se houver, um detalhe."""
    return f"{codigo}:{detalhe}" if detalhe else codigo


def ler_aviso(texto: str) -> tuple[str, str]:
    codigo, _, detalhe = texto.partition(":")
    return codigo, detalhe


@dataclass(eq=False)
class _Chat:
    contexto: ContextoDaSessao
    agente: Agente
    linhas: list[Linha]
    # Ja houve conversa neste chat: se o provedor disser que ela e nova, ela
    # se perdeu, e a pessoa e avisada (D22).
    teve_conversa: bool
    sessao: SessaoViva | None = None
    fila: list[str] = field(default_factory=list)
    turno: asyncio.Task[None] | None = None


type Ouvinte = Callable[[Identidade], None]


class ServicoDeConversa:
    def __init__(self, sessoes: PortaSessao, repositorio: PortaPersistencia) -> None:
        self._sessoes = sessoes
        self._repositorio = repositorio
        self._chats: dict[Identidade, _Chat] = {}
        self._ouvintes: list[Ouvinte] = []

    # ----------------------------------------------------------------------
    # O que a tela le
    # ----------------------------------------------------------------------

    async def abrir(self, contexto: ContextoDaSessao, agente: Agente) -> None:
        """Carrega a conversa antiga do chat, so na primeira vez. Nao liga
        nada: o processo sobe na primeira mensagem."""
        if contexto.id_chat in self._chats:
            return
        persistidas = await self._repositorio.listar_mensagens(contexto.id_chat, MENSAGENS_AO_ABRIR)
        if contexto.id_chat in self._chats:  # outra tela abriu enquanto este lia
            return
        linhas = [
            Linha(m.papel, m.texto, [u.tool for u in m.usos_de_ferramenta], m.em_andamento, m.id)
            for m in persistidas
        ]
        teve_conversa = any(m.papel == USUARIO for m in persistidas)
        self._chats[contexto.id_chat] = _Chat(contexto, agente, linhas, teve_conversa)

    def linhas(self, id_chat: Identidade) -> tuple[Linha, ...]:
        chat = self._chats.get(id_chat)
        return tuple(chat.linhas) if chat else ()

    def fila(self, id_chat: Identidade) -> tuple[str, ...]:
        chat = self._chats.get(id_chat)
        return tuple(chat.fila) if chat else ()

    def estado(self, id_chat: Identidade) -> EstadoDoChat:
        chat = self._chats.get(id_chat)
        if chat is None:
            return EstadoDoChat.PRONTO
        if chat.turno is not None:
            return EstadoDoChat.RESPONDENDO
        if chat.sessao is not None and self._sessoes.ligada(chat.sessao):
            return EstadoDoChat.LIGADO
        return EstadoDoChat.PRONTO

    def conexoes_abertas(self) -> int:
        """Os processos do provedor de pe agora, de todos os chats."""
        return sum(1 for chat in self._chats.values() if chat.sessao is not None and self._sessoes.ligada(chat.sessao))

    def ouvir(self, ouvinte: Ouvinte) -> Callable[[], None]:
        """`ouvinte(id_chat)` e chamado a cada mudanca num chat. Devolve a
        funcao que para de ouvir."""
        self._ouvintes.append(ouvinte)

        def parar() -> None:
            if ouvinte in self._ouvintes:
                self._ouvintes.remove(ouvinte)

        return parar

    def _avisar_ouvintes(self, chat: _Chat) -> None:
        for ouvinte in tuple(self._ouvintes):
            try:
                ouvinte(chat.contexto.id_chat)
            except Exception:
                _log.exception("um ouvinte da conversa falhou")

    # ----------------------------------------------------------------------
    # Mandar, interromper, desligar
    # ----------------------------------------------------------------------

    def enviar(self, id_chat: Identidade, texto: str) -> None:
        """Manda agora, ou poe na fila se o agente esta respondendo. Volta na
        hora: o turno roda numa tarefa do servico."""
        chat = self._chats.get(id_chat)
        if chat is None or not texto.strip():
            return
        if chat.turno is not None:
            chat.fila.append(texto)
        else:
            chat.turno = asyncio.create_task(self._atender(chat, texto))
        self._avisar_ouvintes(chat)

    async def interromper(self, id_chat: Identidade) -> list[str]:
        """O Esc: para a resposta (o que ja apareceu fica, marcado) e devolve
        as mensagens da fila, que nao saem mais."""
        chat = self._chats.get(id_chat)
        if chat is None:
            return []
        fila, chat.fila = chat.fila, []
        turno = chat.turno
        if turno is not None:
            turno.cancel()
            await asyncio.wait({turno})
        self._avisar_ouvintes(chat)
        return fila

    async def desligar(self, id_chat: Identidade) -> list[str]:
        """Interrompe, se estiver respondendo, e fecha a sessao: volta so com
        o processo morto. A proxima mensagem liga de novo e retoma a conversa
        (D22). Devolve a fila, como `interromper`."""
        fila = await self.interromper(id_chat)
        chat = self._chats.get(id_chat)
        if chat is not None and chat.sessao is not None:
            sessao, chat.sessao = chat.sessao, None
            await self._sessoes.fechar(sessao)
            _log.info("chat [%s] desligado", id_chat)
            self._avisar_ouvintes(chat)
        return fila

    async def desligar_ambiente(self, id_ambiente: Identidade) -> None:
        await asyncio.gather(
            *(self.desligar(id_chat) for id_chat, chat in self._chats.items() if chat.contexto.id_ambiente == id_ambiente)
        )

    async def desligar_todos(self) -> None:
        await asyncio.gather(*(self.desligar(id_chat) for id_chat in tuple(self._chats)))

    async def acao_recusada(self, id_sessao: Identidade, acao: str) -> None:
        """Uma acao que o orquestrador pediu e que precisava de confirmacao foi
        recusada: confirmar na tela ainda nao existe. O aviso vai para o chat
        do orquestrador da sessao - o unico que pede acoes (D03)."""
        for chat in self._chats.values():
            if chat.contexto.id_sessao == id_sessao and chat.agente.e_orquestrador:
                await self._aviso(chat, aviso(ACAO_RECUSADA, acao))
                return

    # ----------------------------------------------------------------------
    # O turno
    # ----------------------------------------------------------------------

    async def _atender(self, chat: _Chat, texto: str) -> None:
        """Um turno, e depois os da fila, um por vez, ate ela esvaziar."""
        try:
            while True:
                try:
                    await self._turno(chat, texto)
                except asyncio.CancelledError:
                    raise
                except Exception as erro:
                    # Um defeito (ou o banco falhando) nao derruba o programa:
                    # vira aviso no chat, e a fila segue.
                    _log.error("turno do chat [%s] falhou (%s)", chat.contexto.id_chat, type(erro).__name__, exc_info=erro)
                    chat.linhas.append(Linha(AVISO, MotivoFalhaDeSessao.FALHA_INESPERADA.value))
                if not chat.fila:
                    return
                texto = chat.fila.pop(0)
        finally:
            chat.turno = None
            self._avisar_ouvintes(chat)

    async def _turno(self, chat: _Chat, texto: str) -> None:
        contexto = chat.contexto
        await self._gravar(chat, Linha(USUARIO, texto))
        if chat.sessao is None:
            try:
                chat.sessao = await self._sessoes.abrir(chat.agente, contexto)
            except ErroDeSessao as erro:
                _log.error("o chat [%s] nao abriu a sessao (%s)", contexto.id_chat, type(erro).__name__, exc_info=erro)
                await self._aviso(chat, MotivoFalhaDeSessao.FALHA_INESPERADA.value)
                return

        resposta: Linha | None = None
        try:
            async for evento in self._sessoes.enviar(chat.sessao, texto):
                match evento:
                    case MensagemEntregue(conversa_nova=nova):
                        if nova and chat.teve_conversa:
                            await self._aviso(chat, CONVERSA_RECOMECOU)
                        chat.teve_conversa = True
                    case PedacoDeTexto(texto=pedaco):
                        resposta = resposta or await self._comecar_resposta(chat)
                        resposta.texto += pedaco
                        self._avisar_ouvintes(chat)
                    case UsoDeFerramenta(familia=familia, nome=nome, argumentos=argumentos):
                        resposta = resposta or await self._comecar_resposta(chat)
                        resposta.usos.append(nome)
                        await self._repositorio.registrar_uso_ferramenta(
                            resposta.id, f"{familia.value}__{nome}", _resumo(argumentos)
                        )
                        self._avisar_ouvintes(chat)
                    case FimDeTurno():
                        pass
                    case FalhaDoTurno(motivo=motivo, detalhe=detalhe):
                        if resposta is not None:
                            await self._terminar_resposta(resposta)
                            resposta = None
                        await self._aviso(chat, aviso(motivo.value, detalhe.get("libera_em", "")))
        except asyncio.CancelledError:
            # Esc, desligar ou sair: o que ja apareceu fica, marcado.
            resposta = resposta or await self._comecar_resposta(chat)
            resposta.texto = f"{resposta.texto} {MARCA_DE_INTERROMPIDA}".lstrip()
            await self._terminar_resposta(resposta)
            raise
        if resposta is not None:
            await self._terminar_resposta(resposta)

    async def _comecar_resposta(self, chat: _Chat) -> Linha:
        resposta = Linha(AGENTE, "", em_andamento=True)
        await self._gravar(chat, resposta)
        return resposta

    async def _terminar_resposta(self, resposta: Linha) -> None:
        resposta.em_andamento = False
        await self._repositorio.atualizar_mensagem(resposta.id, resposta.texto, False)

    async def _aviso(self, chat: _Chat, texto: str) -> None:
        await self._gravar(chat, Linha(AVISO, texto))

    async def _gravar(self, chat: _Chat, linha: Linha) -> None:
        contexto = chat.contexto
        linha.id = await self._repositorio.inserir_mensagem(
            contexto.id_ambiente, contexto.id_chat, linha.papel, linha.texto, linha.em_andamento
        )
        chat.linhas.append(linha)
        self._avisar_ouvintes(chat)


def _resumo(argumentos: object) -> str:
    try:
        texto = json.dumps(dict(argumentos), ensure_ascii=False, default=str)
    except (TypeError, ValueError):
        texto = "?"
    return texto[:_RESUMO_MAXIMO]
