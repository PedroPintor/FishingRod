"""Um chat aberto: a conversa, a faixa com o estado e o campo de digitar (card 002).

A tela so fala com o servico de conversa, nunca com o Claude: e o servico que
abre a sessao uma vez e a reaproveita. O turno roda numa tarefa do servico; a
tela ouve as mudancas e redesenha. Por isso redesenhar o painel da tarefa
(trocar de sessao, abrir a memoria) nao interrompe resposta nenhuma.
"""

from rich.text import Text
from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.widgets import Button, Input, Label, Static

from fishingrod.aplicacao.portas.sessao import ContextoDaSessao
from fishingrod.aplicacao.servicos.servico_de_conversa import (
    AGENTE,
    AVISO,
    USUARIO,
    EstadoDoChat,
    Linha,
    ServicoDeConversa,
)
from fishingrod.dominio import Agente, Identidade
from fishingrod.interface.frases import frase_do_aviso, frase_do_estado

DICA_DO_CAMPO = "Escreva para o agente e aperte Enter (Esc interrompe a resposta)"
CHAT_VAZIO = "Ainda não há mensagens neste chat. A primeira mensagem liga o agente."


class ChatAberto(Vertical):
    DEFAULT_CSS = """
    ChatAberto { height: 1fr; }
    ChatAberto #conversa { height: 1fr; }
    ChatAberto #linhas { padding: 0 1; }
    ChatAberto .faixa { height: 1; margin-top: 1; }
    ChatAberto .faixa #estado { width: 1fr; color: $text-muted; }
    ChatAberto .faixa Button { margin-left: 1; }
    """

    BINDINGS = [Binding("escape", "interromper", "Interromper a resposta", show=False)]

    def __init__(self, conversa: ServicoDeConversa, contexto: ContextoDaSessao, agente: Agente, **kwargs) -> None:
        super().__init__(**kwargs)
        self.conversa = conversa
        self.contexto = contexto
        self.agente = agente
        self._parar_de_ouvir = None
        self._texto = Text(CHAT_VAZIO)

    @property
    def id_chat(self) -> Identidade:
        return self.contexto.id_chat

    def compose(self) -> ComposeResult:
        with VerticalScroll(id="conversa"):
            yield Static(CHAT_VAZIO, id="linhas")
        with Horizontal(classes="faixa"):
            yield Label(frase_do_estado(EstadoDoChat.PRONTO, 0), id="estado")
            yield Button("desligar", id="desligar", compact=True, variant="warning")
        yield Input(placeholder=DICA_DO_CAMPO, id="campo")

    async def on_mount(self) -> None:
        await self.conversa.abrir(self.contexto, self.agente)
        if not self.is_attached:  # o painel foi redesenhado enquanto o banco lia
            return
        self._parar_de_ouvir = self.conversa.ouvir(self._mudou)
        self.redesenhar()
        # O processo pode morrer sem o chat mudar (a cauda de um Esc): a faixa
        # tambem se confere sozinha.
        self.set_interval(0.5, self.atualizar_faixa)

    def on_unmount(self) -> None:
        if self._parar_de_ouvir is not None:
            self._parar_de_ouvir()

    def _mudou(self, id_chat: Identidade) -> None:
        if id_chat == self.id_chat and self.is_mounted:
            self.redesenhar()

    # --- o que aparece ------------------------------------------------------

    def redesenhar(self) -> None:
        estado = self.conversa.estado(self.id_chat)
        linhas = self.conversa.linhas(self.id_chat)
        texto = _texto_da_conversa(linhas, self.agente.nome, estado) if linhas else Text(CHAT_VAZIO, style="dim")
        self._texto = texto
        self.query_one("#linhas", Static).update(texto)
        self.query_one("#conversa", VerticalScroll).scroll_end(animate=False)
        self.atualizar_faixa()

    def atualizar_faixa(self) -> None:
        estado = self.conversa.estado(self.id_chat)
        self.query_one("#estado", Label).update(frase_do_estado(estado, len(self.conversa.fila(self.id_chat))))
        self.query_one("#desligar", Button).display = estado is not EstadoDoChat.PRONTO

    def texto_da_conversa(self) -> str:
        """O que esta na tela, como texto simples (para os testes)."""
        return self._texto.plain

    # --- o que a pessoa faz -------------------------------------------------

    @on(Input.Submitted, "#campo")
    def mandar(self, evento: Input.Submitted) -> None:
        texto = evento.value
        if not texto.strip():
            return
        self.conversa.enviar(self.id_chat, texto)
        evento.input.clear()

    async def action_interromper(self) -> None:
        if self.conversa.estado(self.id_chat) is not EstadoDoChat.RESPONDENDO:
            # Sem resposta para interromper, o Esc e o da tela: voltar.
            await self.screen.run_action("voltar")
            return
        self._devolver(await self.conversa.interromper(self.id_chat))

    @on(Button.Pressed, "#desligar")
    async def desligar(self) -> None:
        self._devolver(await self.conversa.desligar(self.id_chat))

    def _devolver(self, fila: list[str]) -> None:
        """As mensagens da fila voltam para o campo, para a pessoa reescrever."""
        if not fila:
            return
        campo = self.query_one("#campo", Input)
        campo.value = " ".join([*fila, campo.value]).strip()
        campo.focus()


def _texto_da_conversa(linhas: tuple[Linha, ...], nome_do_agente: str, estado: EstadoDoChat) -> Text:
    texto = Text()
    for indice, linha in enumerate(linhas):
        if indice:
            texto.append("\n\n")
        match linha.papel:
            case papel if papel == USUARIO:
                texto.append("você: ", style="bold")
                texto.append(linha.texto)
            case papel if papel == AGENTE:
                texto.append(f"{nome_do_agente}: ", style="bold cyan")
                texto.append(linha.texto)
                for uso in linha.usos:
                    texto.append(f"\n  → pediu a ação {uso}", style="dim")
                if linha.em_andamento:
                    ao_vivo = estado is EstadoDoChat.RESPONDENDO and indice == len(linhas) - 1
                    texto.append(" ▌" if ao_vivo else " (incompleta)", style="dim")
            case papel if papel == AVISO:
                texto.append(f"⚠ {frase_do_aviso(linha.texto)}", style="yellow")
            case _:
                texto.append(linha.texto)
    return texto
