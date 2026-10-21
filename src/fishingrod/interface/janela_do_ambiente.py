"""A janela do ambiente: as configuracoes, por cima da tela (card 003).

Abre pelo "⚙ ambiente", no pe da lateral. E o lugar das coisas do ambiente
que nao sao de uma tarefa; comeca simples, com duas secoes, e vai ganhando
outras:

- inicio: o nome do ambiente e as frentes, com quantas tarefas cada uma tem;
- agentes: a lista dos agentes do ambiente e a ficha de cada um, a mesma do
  painel de explicacao. So para ler.
"""

from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import Button, ContentSwitcher, Label, OptionList
from textual.widgets.option_list import Option

from fishingrod.dominio import Ambiente
from fishingrod.interface.ficha import PAPEIS, FichaNaTela
from fishingrod.interface.montagem import Programa

INICIO = "secao-inicio"
AGENTES = "secao-agentes"
SECOES = ((INICIO, "início"), (AGENTES, "agentes"))

SEM_FRENTES = "Este ambiente ainda não tem frentes."


def frase_das_tarefas(quantas: int) -> str:
    return f"{quantas} {'tarefa' if quantas == 1 else 'tarefas'}"


class JanelaDoAmbiente(ModalScreen[None]):
    DEFAULT_CSS = """
    JanelaDoAmbiente { align: center middle; }
    JanelaDoAmbiente > Vertical {
        width: 90; height: 30; padding: 0 1;
        border: round $accent; border-title-color: $text; background: $surface;
    }
    JanelaDoAmbiente #menu { width: 16; height: 1fr; border-right: solid $panel; padding-top: 1; }
    JanelaDoAmbiente #menu Button { width: 100%; margin-bottom: 1; }
    JanelaDoAmbiente #secoes { width: 1fr; height: 1fr; padding: 1 0 0 2; }
    JanelaDoAmbiente .titulo { text-style: bold; color: $text-muted; }
    JanelaDoAmbiente .linha { height: auto; }
    JanelaDoAmbiente .linha .rotulo { width: 10; color: $text-muted; }
    JanelaDoAmbiente #lista-de-frentes { height: auto; }
    JanelaDoAmbiente #agentes { height: auto; max-height: 6; border: none; padding: 0; }
    JanelaDoAmbiente #rodape { height: auto; align-horizontal: right; padding: 1 0 0 0; }
    """

    BINDINGS = [Binding("escape", "fechar", "Fechar")]

    def __init__(self, programa: Programa, ambiente: Ambiente) -> None:
        super().__init__()
        self.programa = programa
        self.ambiente = ambiente

    def compose(self) -> ComposeResult:
        janela = Vertical()
        janela.border_title = f"{self.ambiente.nome} · configurações"
        with janela:
            with Horizontal():
                with Vertical(id="menu"):
                    for indice, (secao, rotulo) in enumerate(SECOES):
                        yield Button(rotulo, id=f"ir-{secao}", compact=True, classes="-ligado" if indice == 0 else "")
                with ContentSwitcher(initial=INICIO, id="secoes"):
                    with VerticalScroll(id=INICIO):
                        yield from self._inicio()
                    with VerticalScroll(id=AGENTES):
                        yield Label("AGENTES DO AMBIENTE", classes="titulo")
                        yield OptionList(
                            *(
                                Option(f"{agente.nome} — {PAPEIS[agente.papel]}", id=agente.nome)
                                for agente in self.programa.agentes
                            ),
                            id="agentes",
                        )
                        yield FichaNaTela()
            with Horizontal(id="rodape"):
                yield Button("fechar", id="fechar", compact=True)

    def _inicio(self) -> ComposeResult:
        yield Label("INÍCIO", classes="titulo")
        with Horizontal(classes="linha"):
            yield Label("Nome", classes="rotulo")
            yield Label(self.ambiente.nome, id="nome-do-ambiente", markup=False)
        with Horizontal(classes="linha"):
            yield Label("Frentes", classes="rotulo")
            linhas = [f"{frente.nome} ({frase_das_tarefas(len(frente.tarefas))})" for frente in self.ambiente.frentes]
            yield Label("\n".join(linhas) or SEM_FRENTES, id="lista-de-frentes", markup=False)

    def on_mount(self) -> None:
        self.mostrar_agente(0)

    @on(Button.Pressed, "#menu Button")
    def ir_para(self, evento: Button.Pressed) -> None:
        secao = evento.button.id.removeprefix("ir-")
        self.query_one("#secoes", ContentSwitcher).current = secao
        for botao in self.query("#menu Button"):
            botao.set_class(botao is evento.button, "-ligado")

    @on(OptionList.OptionHighlighted, "#agentes")
    def trocar_de_agente(self, evento: OptionList.OptionHighlighted) -> None:
        self.mostrar_agente(evento.option_index)

    def mostrar_agente(self, indice: int) -> None:
        self.query_one("#agentes", OptionList).highlighted = indice
        self.query_one(FichaNaTela).mostrar(self.programa.ficha(self.programa.agentes[indice]))

    @on(Button.Pressed, "#fechar")
    def action_fechar(self) -> None:
        self.dismiss(None)
