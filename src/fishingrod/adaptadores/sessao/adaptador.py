"""AdaptadorSessaoClaude: a PortaSessao sobre o claude-agent-sdk (U6).

Guarda as sessoes e os estados (FD §5), e faz o turno: valida, toma a vaga,
sobe a conexao se preciso, entrega, traduz e decide o evento final. NAO importa
o SDK (RN-S-01 no sentido forte): tudo do SDK chega por `opcoes`, `ferramentas`,
`traducao`, `falhas` e `conexao`.

Toda mudanca de estado passa por `_mudar`, que confere a tabela do FD §5; uma
transicao fora dela e defeito e vai ao log em ERROR.
"""

import asyncio
import logging
from collections.abc import AsyncIterator, Callable
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from fishingrod.adaptadores.sessao.conexao import (
    Caiu,
    Conexao,
    DoProvedor,
    Encerrada,
    Entregue,
    FabricaDeCliente,
    FimDaResposta,
    ItemDoTurno,
    cliente_real,
)
from fishingrod.adaptadores.sessao.falhas import Aviso, Causa, CliAusente, Classificacao, Fase, classificar
from fishingrod.adaptadores.sessao.ferramentas import Execucoes, nomes_qualificados, servidores
from fishingrod.adaptadores.sessao.opcoes import conversa_guardada, localizar_cli, montar_opcoes
from fishingrod.adaptadores.sessao.traducao import Tradutor
from fishingrod.aplicacao.ferramentas import Ferramenta, RegistroDeFerramentas
from fishingrod.aplicacao.portas.sessao import (
    AdaptadorEncerrado,
    ContextoDaSessao,
    EventoConversa,
    FalhaDoTurno,
    Familia,
    FimDeTurno,
    MensagemEntregue,
    MotivoFalhaDeSessao,
    SessaoViva,
    validar_mensagem,
)
from fishingrod.dominio import Agente, Identidade

_log = logging.getLogger("fishingrod.sessao")
_log.addHandler(logging.NullHandler())


class Estado(Enum):
    """FD §5. Mora no adaptador, nunca na SessaoViva."""

    SEM_CONEXAO = "sem_conexao"
    OCIOSA = "ociosa"
    EM_TURNO = "em_turno"
    FECHADA = "fechada"


# FD §5: de onde se pode ir para onde. FECHADA e terminal.
_TRANSICOES = {
    Estado.SEM_CONEXAO: frozenset({Estado.EM_TURNO, Estado.FECHADA}),
    Estado.OCIOSA: frozenset({Estado.EM_TURNO, Estado.FECHADA}),
    Estado.EM_TURNO: frozenset({Estado.OCIOSA, Estado.SEM_CONEXAO, Estado.FECHADA}),
    Estado.FECHADA: frozenset(),
}


@dataclass(eq=False)
class _Sessao:
    viva: SessaoViva
    agente: Agente
    ferramentas: dict[Familia, tuple[Ferramenta, ...]]
    estado: Estado = Estado.SEM_CONEXAO
    conexao: Conexao | None = None
    execucoes: Execucoes = field(default_factory=Execucoes)
    # A vaga do turno e do LEITOR (DP-S-05, N2): tomada na primeira chamada ao
    # iterador, antes de qualquer await, e solta quando ele sai.
    vaga: bool = False
    # Enquanto um turno interrompido termina sem leitor (a cauda do ESC, ou o
    # descarte), a sessao continua EM_TURNO, e o proximo leitor espera aqui.
    espera: asyncio.Event | None = None
    fila: asyncio.Queue[ItemDoTurno] | None = None
    # A conexao atual retomou uma conversa que o Claude ja guardava (D22).
    retomou: bool = False

    @property
    def pares(self) -> frozenset[tuple[Familia, str]]:
        return frozenset(
            (familia, ferramenta.nome) for familia, da_familia in self.ferramentas.items() for ferramenta in da_familia
        )


@dataclass
class _Leitura:
    """O que um leitor sabe do proprio turno - e o que o `finally` le."""

    assumiu: bool = False  # levou a sessao a EM_TURNO
    entregue: bool = False  # viu MensagemEntregue (N3)
    concluido: bool = False  # o evento final ja foi entregue a quem le
    conexao: Conexao | None = None


class AdaptadorSessaoClaude:
    """A PortaSessao, mais `encerrar()` (G7).

    `fabrica_de_cliente` e a costura de teste (G11): o padrao e o cliente real;
    os testes entregam um cliente roteirizado; `procurar_conversa` e a
    costura do que o Claude guarda em disco (D22). Os prazos sao os unicos do
    adaptador (DP-S-08): 60 s para subir o CLI (NFR-S-11) e 5 s para a cauda de
    uma interrupcao.

    A conversa de cada sessao e a do chat: o codigo dela no Claude e o id do
    chat. Cada conexao retoma essa conversa, se o Claude ainda a guarda.
    """

    def __init__(
        self,
        registro: RegistroDeFerramentas,
        pasta_de_trabalho: Path,
        fabrica_de_cliente: FabricaDeCliente = cliente_real,
        prazo_de_subida: float = 60,
        prazo_de_interrupcao: float = 5,
        procurar_conversa: Callable[[str, Path], bool] = conversa_guardada,
    ) -> None:
        self._registro = registro
        self._pasta_de_trabalho = Path(pasta_de_trabalho)
        self._fabrica_de_cliente = fabrica_de_cliente
        self._prazo_de_subida = prazo_de_subida
        self._prazo_de_interrupcao = prazo_de_interrupcao
        self._procurar_conversa = procurar_conversa
        self._sessoes: dict[Identidade, _Sessao] = {}
        self._encerrado = False

    # ----------------------------------------------------------------------
    # abrir (business-logic-model.md 2)
    # ----------------------------------------------------------------------

    async def abrir(self, agente: Agente, contexto: ContextoDaSessao) -> SessaoViva:
        """So prepara (Q2=B): nenhum processo sobe aqui."""
        if self._encerrado:
            raise AdaptadorEncerrado("o adaptador de sessao ja foi encerrado")
        ferramentas = self._registro.preparar(agente, contexto)
        viva = SessaoViva(Identidade.nova(), agente.nome, contexto)
        self._sessoes[viva.id] = _Sessao(viva, agente, dict(ferramentas))
        _log.info(
            "sessao [%s] aberta para o agente [%s], com as ferramentas %s",
            viva.id,
            agente.nome,
            sorted(nomes_qualificados(ferramentas)),
        )
        return viva

    # ----------------------------------------------------------------------
    # enviar (business-logic-model.md 3)
    # ----------------------------------------------------------------------

    async def enviar(self, sessao_viva: SessaoViva, mensagem: str) -> AsyncIterator[EventoConversa]:
        """Nunca levanta (RN-S-16): toda falha chega como o ultimo evento, e so
        o cancelamento passa. Sair sem ler o evento final - cancelado ou
        abandonado - e interromper (G6), e o `finally` cuida disso sem await e
        sem yield (DP-S-02)."""
        sessao = self._sessoes.get(getattr(sessao_viva, "id", None))
        recusa = self._recusa(sessao, mensagem)
        if recusa is not None:
            yield recusa
            return
        sessao.vaga = True  # antes de qualquer await (RN-S-27)
        leitura = _Leitura()
        try:
            try:
                # N2: o turno anterior foi interrompido e ainda esta terminando.
                while sessao.espera is not None:
                    await sessao.espera.wait()
                if sessao.estado is Estado.FECHADA:
                    yield self._final(sessao, leitura, FalhaDoTurno(MotivoFalhaDeSessao.SESSAO_FECHADA))
                    return

                leitura.assumiu = True
                self._mudar(sessao, Estado.EM_TURNO)
                sessao.execucoes.liberar()
                inicio = asyncio.get_running_loop().time()
                fila: asyncio.Queue[ItemDoTurno] = asyncio.Queue()
                sessao.fila = fila

                if sessao.conexao is None:
                    cli = localizar_cli()
                    if cli is None:
                        classificacao = classificar(Fase.SUBIDA, CliAusente())
                        self._registrar_falha(sessao, classificacao, CliAusente())
                        self._mudar(sessao, Estado.SEM_CONEXAO)
                        yield self._final(sessao, leitura, classificacao.evento())
                        return
                    self._conectar(sessao, cli)
                conexao = leitura.conexao = sessao.conexao
                conexao.entregar(mensagem, fila)
                tradutor = Tradutor(sessao.pares)

                while True:
                    item = await fila.get()
                    if sessao.estado is Estado.FECHADA:
                        # RN-S-37: `fechar` no meio do turno.
                        yield self._final(sessao, leitura, FalhaDoTurno(MotivoFalhaDeSessao.SESSAO_FECHADA))
                        return
                    match item:
                        case Entregue(primeira=primeira):
                            leitura.entregue = True  # imediatamente antes do yield (N3)
                            # Conversa nova: a primeira entrega de uma conexao que
                            # nao retomou nada - o agente nao lembra de antes.
                            yield MensagemEntregue(conversa_nova=primeira and not sessao.retomou)
                        case DoProvedor(mensagem=do_provedor):
                            traducao = tradutor.traduzir(do_provedor)
                            self._registrar_avisos(sessao, traducao.avisos)
                            for evento in traducao.eventos:
                                yield evento
                        case FimDaResposta(mensagem=resultado):
                            desfecho = tradutor.final(resultado)
                            if isinstance(desfecho, FimDeTurno):
                                self._mudar(sessao, Estado.OCIOSA)
                                self._registrar_duracao(sessao, inicio, "fim_de_turno")
                                yield self._final(sessao, leitura, desfecho)
                                return
                            self._registrar_falha(sessao, desfecho, tradutor.sinal)
                            if desfecho.derruba:
                                # N5: o evento so sai com o processo morto.
                                conexao.descartar()
                                await asyncio.wait({conexao.tarefa})
                            else:
                                self._mudar(sessao, Estado.OCIOSA)
                            self._registrar_duracao(sessao, inicio, desfecho.motivo.value)
                            yield self._final(sessao, leitura, desfecho.evento())
                            return
                        case Caiu(fase=fase, causa=causa):
                            desfecho = tradutor.queda(fase, causa)
                            self._registrar_falha(sessao, desfecho, causa)
                            await asyncio.wait({conexao.tarefa})  # N5
                            self._registrar_duracao(sessao, inicio, desfecho.motivo.value)
                            yield self._final(sessao, leitura, desfecho.evento())
                            return
                        case Encerrada():
                            raise RuntimeError("a conexao terminou sem dizer por que")
            except Exception as erro:
                # DP-S-10: a rede. Um defeito vira FALHA_INESPERADA, com a pilha
                # no log e nada dela no evento - e so com o processo morto.
                _log.error(
                    "turno da sessao [%s] falhou de forma inesperada (%s)",
                    sessao.viva.id,
                    type(erro).__name__,
                    exc_info=erro,
                )
                await self._derrubar(sessao, leitura)
                yield self._final(sessao, leitura, FalhaDoTurno(MotivoFalhaDeSessao.FALHA_INESPERADA))
        finally:
            self._ao_sair(sessao, leitura)

    def _recusa(self, sessao: _Sessao | None, mensagem: object) -> FalhaDoTurno | None:
        """As tres saidas que nao tocam o provedor nem a vaga: um turno em
        andamento continua intacto (business-logic-model.md 3)."""
        if sessao is None or sessao.estado is Estado.FECHADA:
            _log.info("envio recusado: sessao fechada")
            return FalhaDoTurno(MotivoFalhaDeSessao.SESSAO_FECHADA)
        if sessao.vaga:
            # Defeito de quem chama: a fila de mensagens e de U7 (C1=B).
            _log.warning("envio recusado: a sessao [%s] ja tem um turno em andamento", sessao.viva.id)
            return FalhaDoTurno(MotivoFalhaDeSessao.TURNO_EM_ANDAMENTO)
        invalida = validar_mensagem(mensagem)
        if invalida is not None:
            _log.info("envio recusado na sessao [%s]: mensagem invalida (%s)", sessao.viva.id, invalida.detalhe["problema"])
        return invalida

    def _final(self, sessao: _Sessao, leitura: _Leitura, evento: EventoConversa) -> EventoConversa:
        """Solta a vaga ANTES de entregar o evento final: quem le e para no
        evento final, sem esgotar o iterador, ja pode mandar a proxima
        mensagem."""
        leitura.concluido = True
        sessao.vaga = False
        return evento

    def _conectar(self, sessao: _Sessao, cli: Path) -> None:
        conversa = sessao.viva.contexto.id_chat.valor
        sessao.retomou = self._procurar_conversa(conversa, self._pasta_de_trabalho)
        opcoes = montar_opcoes(
            agente=sessao.agente,
            cli=cli,
            pasta_de_trabalho=self._pasta_de_trabalho,
            servidores=servidores(sessao.ferramentas, sessao.execucoes),
            permitidos=nomes_qualificados(sessao.ferramentas),
            conversa=conversa,
            retomar=sessao.retomou,
        )
        cliente = self._fabrica_de_cliente(opcoes)
        conexao: Conexao | None = None

        def sossegou() -> None:
            self._sossegou(sessao, conexao)

        def terminou() -> None:
            self._terminou(sessao, conexao)

        conexao = Conexao(
            cliente,
            prazo_de_subida=self._prazo_de_subida,
            prazo_de_interrupcao=self._prazo_de_interrupcao,
            ao_sossegar=sossegou,
            ao_terminar=terminou,
        )
        sessao.conexao = conexao
        _log.info(
            "sessao [%s] conectando ao provedor (%s)",
            sessao.viva.id,
            "retomando a conversa" if sessao.retomou else "conversa nova",
        )

    async def _derrubar(self, sessao: _Sessao, leitura: _Leitura) -> None:
        if not leitura.assumiu:
            return
        conexao = leitura.conexao
        if conexao is not None and not conexao.tarefa.done():
            conexao.descartar()
            await asyncio.wait({conexao.tarefa})
        elif conexao is None and sessao.estado is Estado.EM_TURNO:
            self._mudar(sessao, Estado.SEM_CONEXAO)

    def _ao_sair(self, sessao: _Sessao, leitura: _Leitura) -> None:
        """O `finally` de `enviar`: sem await e sem yield (DP-S-02). So age se
        o leitor saiu sem o evento final - ESC ou iterador abandonado."""
        if leitura.concluido:
            return
        sessao.vaga = False
        if not leitura.assumiu:
            return
        # RN-S-35: todas as ferramentas da sessao, inclusive a espera da sua
        # confirmacao. Nada mais executa.
        sessao.execucoes.bloquear()
        if sessao.estado is Estado.FECHADA:
            return
        conexao = leitura.conexao
        if conexao is None or conexao.tarefa.done():
            if sessao.estado is Estado.EM_TURNO:
                self._mudar(sessao, Estado.SEM_CONEXAO)
            return
        if sessao.espera is None:
            sessao.espera = asyncio.Event()
        # N3: o recado depende do que o leitor viu.
        if leitura.entregue:
            conexao.interromper()
        else:
            conexao.descartar()
        _log.info(
            "turno da sessao [%s] interrompido (%s)",
            sessao.viva.id,
            "depois da entrega" if leitura.entregue else "antes da entrega",
        )

    # ----------------------------------------------------------------------
    # O que a dona avisa (sincrono)
    # ----------------------------------------------------------------------

    def _sossegou(self, sessao: _Sessao, conexao: Conexao | None) -> None:
        """A cauda acabou com o processo vivo: OCIOSA, com o historico."""
        if sessao.conexao is not conexao or sessao.espera is None:
            return
        if sessao.estado is Estado.EM_TURNO:
            self._mudar(sessao, Estado.OCIOSA)
        self._soltar_espera(sessao)

    def _terminou(self, sessao: _Sessao, conexao: Conexao | None) -> None:
        """A dona terminou: o processo morreu. SEM_CONEXAO, a nao ser que a
        sessao ja esteja FECHADA."""
        if sessao.conexao is conexao:
            sessao.conexao = None
        if sessao.estado in (Estado.EM_TURNO, Estado.OCIOSA):
            self._mudar(sessao, Estado.SEM_CONEXAO)
        self._soltar_espera(sessao)
        _log.info("conexao da sessao [%s] encerrada", sessao.viva.id)

    def _soltar_espera(self, sessao: _Sessao) -> None:
        espera, sessao.espera = sessao.espera, None
        if espera is not None:
            espera.set()

    # ----------------------------------------------------------------------
    # fechar e encerrar (RN-S-37, RN-S-39)
    # ----------------------------------------------------------------------

    async def fechar(self, sessao_viva: SessaoViva) -> None:
        """Volta so com o processo morto (DP-S-06). Fechar de novo nao muda
        nada - so espera, se o primeiro fechamento ainda nao terminou."""
        sessao = self._sessoes.get(getattr(sessao_viva, "id", None))
        if sessao is None:
            return
        primeira_vez = sessao.estado is not Estado.FECHADA
        if primeira_vez:
            self._mudar(sessao, Estado.FECHADA)
            sessao.execucoes.bloquear()
            if sessao.fila is not None:
                sessao.fila.put_nowait(Encerrada())  # acorda quem le o turno
        conexao = sessao.conexao
        if conexao is not None:
            conexao.descartar()
            await asyncio.wait({conexao.tarefa})
        self._soltar_espera(sessao)
        self._sessoes.pop(sessao.viva.id, None)
        if primeira_vez:
            _log.info("sessao [%s] fechada", sessao.viva.id)

    async def encerrar(self) -> None:
        """Fecha todas as sessoes, em paralelo - cada fechamento pode levar
        ate ~15 s (A12). Depois disso, `abrir` levanta AdaptadorEncerrado."""
        self._encerrado = True
        sessoes = list(self._sessoes.values())
        await asyncio.gather(*(self.fechar(sessao.viva) for sessao in sessoes))
        _log.info("adaptador de sessao encerrado (%d sessoes fechadas)", len(sessoes))

    # ----------------------------------------------------------------------
    # Estado e log
    # ----------------------------------------------------------------------

    def _mudar(self, sessao: _Sessao, novo: Estado) -> None:
        if novo not in _TRANSICOES[sessao.estado]:
            _log.error(
                "transicao fora da tabela na sessao [%s]: %s -> %s",
                sessao.viva.id,
                sessao.estado.value,
                novo.value,
            )
            return
        sessao.estado = novo

    def ligada(self, sessao_viva: SessaoViva) -> bool:
        """O processo existe enquanto a dona da conexao vive: da subida ao fim
        do fechamento."""
        sessao = self._sessoes.get(getattr(sessao_viva, "id", None))
        return sessao is not None and sessao.conexao is not None

    def estado(self, sessao_viva: SessaoViva) -> Estado:
        """Para os testes e para o log de U9: o estado de uma sessao. Uma
        sessao que este adaptador nao conhece (ou ja fechou) esta FECHADA."""
        sessao = self._sessoes.get(getattr(sessao_viva, "id", None))
        return Estado.FECHADA if sessao is None else sessao.estado

    def _registrar_falha(self, sessao: _Sessao, classificacao: Classificacao, causa: Causa | None) -> None:
        pilha = causa if classificacao.com_pilha and isinstance(causa, BaseException) else None
        _log.log(
            classificacao.nivel,
            "turno da sessao [%s] (agente [%s]) terminou em %s (%s)",
            sessao.viva.id,
            sessao.viva.nome_agente,
            classificacao.motivo.value,
            _descrever(causa),
            exc_info=pilha,
        )

    def _registrar_avisos(self, sessao: _Sessao, avisos: tuple[Aviso, ...]) -> None:
        for aviso in avisos:
            _log.log(aviso.nivel, f"sessao [%s]: {aviso.mensagem}", sessao.viva.id, *aviso.argumentos)

    def _registrar_duracao(self, sessao: _Sessao, inicio: float, desfecho: str) -> None:
        _log.info(
            "turno da sessao [%s] terminou em %.1f s (%s)",
            sessao.viva.id,
            asyncio.get_running_loop().time() - inicio,
            desfecho,
        )


def _descrever(causa: Causa | None) -> str:
    """So o tipo: a mensagem de uma excecao pode trazer conteudo."""
    if causa is None:
        return "sinal do provedor"
    tipo = getattr(causa, "tipo", None)
    if isinstance(tipo, str):
        return f"{type(causa).__name__}:{tipo}"
    return type(causa).__name__
