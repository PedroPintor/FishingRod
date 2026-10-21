"""As janelinhas que aparecem por cima da tela: pedir um nome e confirmar que
apaga."""

from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label

# O mesmo limite das acoes do catalogo (MAXIMO_NOME): a janela nao deixa
# digitar um nome que o catalogo recusaria depois.
MAXIMO_NOME = 200

AVISO_SEM_NOME = "precisa de um nome"


class JanelaDeNome(ModalScreen[str | None]):
    """Pede um nome. Devolve o nome digitado, ou None se a pessoa cancelar.

    Nome vazio, ou so de espacos, nao fecha a janela: mostra o aviso e espera.
    O nome volta como foi digitado - quem decide se ele vale e o dominio.
    """

    DEFAULT_CSS = """
    JanelaDeNome { align: center middle; }
    JanelaDeNome > Vertical {
        width: 60; height: auto; padding: 1 2;
        border: round $accent; background: $surface;
    }
    JanelaDeNome #aviso { color: $error; height: 1; }
    JanelaDeNome Horizontal { height: auto; align-horizontal: right; }
    JanelaDeNome Button { margin-left: 1; }
    """

    BINDINGS = [("escape", "cancelar", "Cancelar")]

    def __init__(self, titulo: str, rotulo_do_botao: str = "Criar") -> None:
        super().__init__()
        self._titulo = titulo
        self._rotulo_do_botao = rotulo_do_botao

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label(self._titulo)
            yield Input(placeholder="nome", max_length=MAXIMO_NOME, id="nome")
            yield Label("", id="aviso")
            with Horizontal():
                yield Button("Cancelar", id="cancelar")
                yield Button(self._rotulo_do_botao, variant="primary", id="criar")

    @on(Button.Pressed, "#criar")
    @on(Input.Submitted, "#nome")
    def criar(self) -> None:
        nome = self.query_one("#nome", Input).value
        if not nome.strip():
            self.query_one("#aviso", Label).update(AVISO_SEM_NOME)
            return
        self.dismiss(nome)

    @on(Button.Pressed, "#cancelar")
    def action_cancelar(self) -> None:
        self.dismiss(None)


class JanelaDeAgente(ModalScreen[str | None]):
    """Pergunta com qual agente abrir o chat: um botao por agente. Devolve o
    nome do agente, ou None se a pessoa cancelar."""

    DEFAULT_CSS = """
    JanelaDeAgente { align: center middle; }
    JanelaDeAgente > Vertical {
        width: 50; height: auto; padding: 1 2;
        border: round $accent; background: $surface;
    }
    JanelaDeAgente .agente { width: 100%; margin-top: 1; }
    JanelaDeAgente Horizontal { height: auto; align-horizontal: right; margin-top: 1; }
    """

    BINDINGS = [("escape", "cancelar", "Cancelar")]

    def __init__(self, nomes_dos_agentes: tuple[str, ...]) -> None:
        super().__init__()
        self._nomes = nomes_dos_agentes

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("Abrir um chat novo com qual agente?")
            for indice, nome in enumerate(self._nomes):
                yield Button(nome, classes="agente", id=f"agente-{indice}")
            with Horizontal():
                yield Button("Cancelar", id="cancelar")

    @on(Button.Pressed, ".agente")
    def escolher(self, evento: Button.Pressed) -> None:
        indice = int(evento.button.id.removeprefix("agente-"))
        self.dismiss(self._nomes[indice])

    @on(Button.Pressed, "#cancelar")
    def action_cancelar(self) -> None:
        self.dismiss(None)


def aviso_de_apagar(nome_do_ambiente: str) -> str:
    return (
        f'ATENÇÃO: APAGAR O AMBIENTE "{nome_do_ambiente}" APAGA TODAS AS FRENTES, '
        "TAREFAS, SESSÕES, CHATS E A WIKI DELE. ISSO NÃO TEM VOLTA."
    )


class JanelaDeApagar(ModalScreen[bool]):
    """Confirma que apaga um ambiente. Devolve True so no botao Apagar; Cancelar
    e Esc devolvem False. O foco comeca em Cancelar: Enter sem pensar nao
    apaga nada."""

    DEFAULT_CSS = """
    JanelaDeApagar { align: center middle; }
    JanelaDeApagar > Vertical {
        width: 70; height: auto; padding: 1 2;
        border: heavy $error; background: $surface;
    }
    JanelaDeApagar #aviso { width: 100%; color: $error; text-style: bold; margin-bottom: 1; }
    JanelaDeApagar Horizontal { height: auto; align-horizontal: right; }
    JanelaDeApagar Button { margin-left: 1; }
    """

    BINDINGS = [("escape", "cancelar", "Cancelar")]

    def __init__(self, nome_do_ambiente: str) -> None:
        super().__init__()
        self._nome = nome_do_ambiente

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label(aviso_de_apagar(self._nome), id="aviso")
            with Horizontal():
                yield Button("Cancelar", id="cancelar")
                yield Button("Apagar", variant="error", id="apagar")

    def on_mount(self) -> None:
        self.query_one("#cancelar", Button).focus()

    @on(Button.Pressed, "#apagar")
    def apagar(self) -> None:
        self.dismiss(True)

    @on(Button.Pressed, "#cancelar")
    def action_cancelar(self) -> None:
        self.dismiss(False)
