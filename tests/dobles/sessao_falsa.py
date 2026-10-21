"""SessaoFalsa: um segundo enunciado do contrato da PortaSessao (DP-S-22, Q8=A).

Responde por roteiro de EVENTOS DA PORTA, e nao de mensagens do SDK: nao
importa `claude_agent_sdk` nem `adaptadores/`. Tem a propria maquina de
estados, escrita a mao. Como o RepositorioEmMemoria de U2, a diferenca importa:
se falso e real fossem o mesmo codigo, o teste de contrato passaria por
construcao. Duas implementacoes que discordam revelam que o CONTRATO estava
ambiguo.

O que ele compartilha com o real e so o que e da aplicacao (DP-S-21):
`RegistroDeFerramentas.preparar` na abertura e `validar_mensagem` no envio.

Para U7 e U8:
- `roteiro` e uma fila de turnos, consumida na ordem, por qualquer sessao;
  sem roteiro, o turno responde um pedaco de texto e termina bem;
- um passo `Executar` roda a Ferramenta DE VERDADE da sessao - a de acoes
  chega ao catalogo de U5 -, e a resposta fica em `respostas`;
- um passo `Esperar` para o turno ate o teste liberar: e o que deixa testar
  ESC e fechar no meio;
- `mensagens` guarda o que chegou ao agente (so o que teve MensagemEntregue);
- `conversas` sao os chats de que o agente lembra (D22): abrir de novo uma
  sessao do mesmo chat retoma a conversa, e tirar o chat daqui e o "provedor
  perdeu a conversa";
- `roteiro_do_chat` da a um chat os proprios turnos, antes do `roteiro`.
"""

import asyncio
from collections.abc import AsyncIterator, Iterable, Mapping
from dataclasses import dataclass, field
from enum import Enum

from fishingrod.aplicacao.ferramentas import Ferramenta, RegistroDeFerramentas, RespostaDaFerramenta
from fishingrod.aplicacao.portas.sessao import (
    AdaptadorEncerrado,
    ContextoDaSessao,
    EventoConversa,
    FalhaDoTurno,
    Familia,
    FimDeTurno,
    MensagemEntregue,
    MotivoFalhaDeSessao,
    PedacoDeTexto,
    SessaoViva,
    UsoDeFerramenta,
    validar_mensagem,
)
from fishingrod.dominio import Agente, Identidade

# As falhas que derrubam a conexao (RN-S-34). As outras a mantem.
_DERRUBAM = frozenset(
    {
        MotivoFalhaDeSessao.PROVEDOR_AUSENTE,
        MotivoFalhaDeSessao.NAO_AUTENTICADO,
        MotivoFalhaDeSessao.INDISPONIVEL,
        MotivoFalhaDeSessao.FALHA_INESPERADA,
    }
)


class EstadoFalso(Enum):
    SEM_CONEXAO = "sem_conexao"
    OCIOSA = "ociosa"
    EM_TURNO = "em_turno"
    FECHADA = "fechada"


@dataclass(frozen=True)
class Executar:
    """Roda a ferramenta `nome` da sessao com estes argumentos. Antes, emite o
    UsoDeFerramenta, como o real emite o pedido do agente."""

    nome: str
    argumentos: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class Esperar:
    """Para o turno ate o teste liberar o evento."""

    liberar: asyncio.Event


type Passo = EventoConversa | Executar | Esperar


@dataclass(frozen=True)
class TurnoRoteirizado:
    """Os passos de um turno. Com `entregue=False`, a mensagem nunca chega ao
    agente: o turno e so o evento final, que precisa ser uma FalhaDoTurno.
    Sem evento final nos passos, o turno termina em FimDeTurno."""

    passos: tuple[Passo, ...] = ()
    entregue: bool = True


_PADRAO = TurnoRoteirizado((PedacoDeTexto("ok"),))


@dataclass(eq=False)
class _SessaoFalsa:
    viva: SessaoViva
    ferramentas: dict[str, tuple[Familia, Ferramenta]]
    estado: EstadoFalso = EstadoFalso.SEM_CONEXAO
    lendo: bool = False
    fechada: asyncio.Event = field(default_factory=asyncio.Event)


class SessaoFalsa:
    """A PortaSessao, mais `encerrar()`, como o real."""

    def __init__(self, registro: RegistroDeFerramentas, roteiro: Iterable[TurnoRoteirizado] = ()) -> None:
        self._registro = registro
        self.roteiro: list[TurnoRoteirizado] = list(roteiro)
        self.mensagens: list[tuple[SessaoViva, str]] = []
        self.conversas: set[Identidade] = set()
        self.roteiro_do_chat: dict[Identidade, list[TurnoRoteirizado]] = {}
        self.respostas: list[tuple[str, RespostaDaFerramenta]] = []
        self._sessoes: dict[Identidade, _SessaoFalsa] = {}
        self._encerrado = False

    async def abrir(self, agente: Agente, contexto: ContextoDaSessao) -> SessaoViva:
        if self._encerrado:
            raise AdaptadorEncerrado("a sessao falsa ja foi encerrada")
        preparadas = self._registro.preparar(agente, contexto)
        viva = SessaoViva(Identidade.nova(), agente.nome, contexto)
        ferramentas = {
            ferramenta.nome: (familia, ferramenta)
            for familia, da_familia in preparadas.items()
            for ferramenta in da_familia
        }
        self._sessoes[viva.id] = _SessaoFalsa(viva, ferramentas)
        return viva

    async def enviar(self, sessao_viva: SessaoViva, mensagem: str) -> AsyncIterator[EventoConversa]:
        sessao = self._sessoes.get(getattr(sessao_viva, "id", None))
        if sessao is None or sessao.estado is EstadoFalso.FECHADA:
            yield FalhaDoTurno(MotivoFalhaDeSessao.SESSAO_FECHADA)
            return
        if sessao.lendo:
            yield FalhaDoTurno(MotivoFalhaDeSessao.TURNO_EM_ANDAMENTO)
            return
        invalida = validar_mensagem(mensagem)
        if invalida is not None:
            yield invalida
            return

        sessao.lendo = True
        id_chat = sessao_viva.contexto.id_chat
        conversa_nova = id_chat not in self.conversas
        sessao.estado = EstadoFalso.EM_TURNO
        do_chat = self.roteiro_do_chat.get(id_chat)
        turno = do_chat.pop(0) if do_chat else self.roteiro.pop(0) if self.roteiro else _PADRAO
        entregue = False
        terminou = False
        try:
            if not turno.entregue:
                final = turno.passos[-1] if turno.passos else FalhaDoTurno(MotivoFalhaDeSessao.INDISPONIVEL)
                sessao.estado = EstadoFalso.SEM_CONEXAO if final.motivo in _DERRUBAM else EstadoFalso.OCIOSA
                terminou = True
                sessao.lendo = False
                yield final
                return

            self.mensagens.append((sessao_viva, mensagem))
            self.conversas.add(id_chat)
            entregue = True
            yield MensagemEntregue(conversa_nova=conversa_nova)
            houve_resposta = False
            for passo in turno.passos:
                if sessao.estado is EstadoFalso.FECHADA:
                    break
                match passo:
                    case Executar(nome=nome, argumentos=argumentos):
                        familia, ferramenta = sessao.ferramentas[nome]
                        houve_resposta = True
                        yield UsoDeFerramenta(familia, nome, argumentos)
                        resposta = await ferramenta.executar(UsoDeFerramenta(familia, nome, argumentos).argumentos)
                        self.respostas.append((nome, resposta))
                    case Esperar(liberar=liberar):
                        await _o_primeiro(liberar, sessao.fechada)
                    case FimDeTurno() | FalhaDoTurno():
                        break
                    case _:
                        houve_resposta = houve_resposta or isinstance(passo, (PedacoDeTexto, UsoDeFerramenta))
                        yield passo
            final = self._final(sessao, turno, houve_resposta)
            terminou = True
            sessao.lendo = False
            yield final
        finally:
            if not terminou:
                sessao.lendo = False
                if sessao.estado is EstadoFalso.EM_TURNO:
                    # ESC: com a entrega, o agente lembra; sem, o processo e
                    # descartado (RN-S-35, RN-S-36).
                    sessao.estado = EstadoFalso.OCIOSA if entregue else EstadoFalso.SEM_CONEXAO

    def _final(self, sessao: _SessaoFalsa, turno: TurnoRoteirizado, houve_resposta: bool) -> EventoConversa:
        if sessao.estado is EstadoFalso.FECHADA:
            return FalhaDoTurno(MotivoFalhaDeSessao.SESSAO_FECHADA)
        final = next((p for p in turno.passos if isinstance(p, (FimDeTurno, FalhaDoTurno))), None)
        if final is None or isinstance(final, FimDeTurno):
            # RN-S-24: so termina bem se houve texto ou uso de ferramenta.
            final = FimDeTurno() if houve_resposta else FalhaDoTurno(MotivoFalhaDeSessao.RESPOSTA_VAZIA)
        if isinstance(final, FalhaDoTurno) and final.motivo in _DERRUBAM:
            sessao.estado = EstadoFalso.SEM_CONEXAO
        else:
            sessao.estado = EstadoFalso.OCIOSA
        return final

    async def fechar(self, sessao_viva: SessaoViva) -> None:
        sessao = self._sessoes.pop(getattr(sessao_viva, "id", None), None)
        if sessao is not None:
            sessao.estado = EstadoFalso.FECHADA
            sessao.fechada.set()  # acorda quem le o turno

    async def encerrar(self) -> None:
        self._encerrado = True
        for sessao in list(self._sessoes.values()):
            await self.fechar(sessao.viva)

    def ligada(self, sessao_viva: SessaoViva) -> bool:
        return self.estado(sessao_viva) in (EstadoFalso.OCIOSA, EstadoFalso.EM_TURNO)

    def estado(self, sessao_viva: SessaoViva) -> EstadoFalso:
        sessao = self._sessoes.get(getattr(sessao_viva, "id", None))
        return EstadoFalso.FECHADA if sessao is None else sessao.estado


async def _o_primeiro(*eventos: asyncio.Event) -> None:
    esperas = [asyncio.ensure_future(evento.wait()) for evento in eventos]
    try:
        await asyncio.wait(esperas, return_when=asyncio.FIRST_COMPLETED)
    finally:
        for espera in esperas:
            espera.cancel()
