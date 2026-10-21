"""A tela de inicio: a lista dos meus ambientes, para criar, entrar e apagar.

Criar, listar e apagar ambiente nao sao acoes do catalogo (Q1=A de U5): a
tela chama o servico direto. A wiki nasce vazia, so com o indice
(EsquemaWiki.vazio): escolher a estrutura e outra ideia.
"""

from textual import events, on, work
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.message import Message
from textual.screen import Screen
from textual.widgets import Button, Footer, Label, ListItem, ListView

from fishingrod.aplicacao.esquema_wiki import EsquemaWiki
from fishingrod.aplicacao.portas.persistencia import ErroDePersistencia, ResumoAmbiente
from fishingrod.aplicacao.portas.wiki import ErroDeWiki
from fishingrod.interface.frases import quando
from fishingrod.interface.janelas import JanelaDeApagar, JanelaDeNome
from fishingrod.interface.montagem import Programa
from fishingrod.interface.tela_do_ambiente import TelaDoAmbiente

SEM_AMBIENTES = "Você ainda não tem ambientes. Crie o primeiro em [b]+ novo ambiente[/b]."


class ItemDeAmbiente(ListItem):
    """Uma linha da lista. Duplo clique entra no ambiente."""

    class Aberto(Message):
        def __init__(self, resumo: ResumoAmbiente) -> None:
            super().__init__()
            self.resumo = resumo

    def __init__(self, resumo: ResumoAmbiente) -> None:
        super().__init__(
            Horizontal(
                Label(resumo.nome, classes="nome", markup=False),
                Label(quando(resumo.atualizado_em), classes="quando"),
            )
        )
        self.resumo = resumo

    def on_click(self, evento: events.Click) -> None:
        if evento.chain >= 2:
            self.post_message(self.Aberto(self.resumo))


class ListaDeAmbientes(ListView):
    """Um clique so marca o ambiente, e nao entra nele: e o que deixa escolher
    um ambiente para apagar. Entrar e Enter, duplo clique ou o botao."""

    def _on_list_item__child_clicked(self, evento: ListItem._ChildClicked) -> None:
        evento.stop()
        self.focus()
        self.index = self._nodes.index(evento.item)


class TelaDeInicio(Screen):
    DEFAULT_CSS = """
    TelaDeInicio > Vertical { padding: 1 2; }
    TelaDeInicio #titulo { text-style: bold; margin-bottom: 1; }
    TelaDeInicio ListView { height: 1fr; border: round $panel; }
    TelaDeInicio ItemDeAmbiente Horizontal { height: 1; }
    TelaDeInicio ItemDeAmbiente .nome { width: 1fr; }
    TelaDeInicio ItemDeAmbiente .quando { color: $text-muted; }
    TelaDeInicio #vazio { color: $text-muted; padding: 1 0; }
    TelaDeInicio #botoes { height: auto; margin-top: 1; }
    TelaDeInicio #botoes Button { margin-right: 1; }
    """

    BINDINGS = [
        Binding("n", "novo", "Novo ambiente"),
        Binding("q", "app.quit", "Sair"),
    ]

    def __init__(self, programa: Programa) -> None:
        super().__init__()
        self.programa = programa

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("Meus ambientes", id="titulo")
            yield Label(SEM_AMBIENTES, id="vazio")
            yield ListaDeAmbientes(id="ambientes")
            with Horizontal(id="botoes"):
                yield Button("+ novo ambiente", variant="primary", id="novo", compact=True)
                yield Button("entrar", id="entrar", compact=True)
                yield Button("apagar", variant="error", id="apagar", compact=True)
        yield Footer()

    async def on_mount(self) -> None:
        await self.atualizar()

    async def on_screen_resume(self) -> None:
        # De volta do ambiente: o que mudou la dentro muda a ordem aqui.
        await self.atualizar()

    async def atualizar(self) -> None:
        resumos = await self.programa.servico.listar_ambientes()
        lista = self.query_one("#ambientes", ListView)
        await lista.clear()
        await lista.extend(ItemDeAmbiente(resumo) for resumo in resumos)
        self.query_one("#vazio", Label).display = not resumos
        lista.display = bool(resumos)
        if resumos:
            lista.index = 0
            lista.focus()

    def _escolhido(self) -> ResumoAmbiente | None:
        item = self.query_one("#ambientes", ListView).highlighted_child
        return item.resumo if isinstance(item, ItemDeAmbiente) else None

    # --- criar --------------------------------------------------------------

    @on(Button.Pressed, "#novo")
    def action_novo(self) -> None:
        self.app.push_screen(JanelaDeNome("Nome do novo ambiente"), self._criar)

    async def _criar(self, nome: str | None) -> None:
        if nome is None:
            return
        try:
            ambiente = await self.programa.servico.criar_ambiente(nome, EsquemaWiki.vazio())
        except (ErroDePersistencia, ErroDeWiki):
            self.notify("Não consegui criar o ambiente no disco.", severity="error")
            return
        await self.atualizar()
        self.notify(f"Ambiente {ambiente.nome} criado.", markup=False)

    # --- entrar -------------------------------------------------------------

    @on(Button.Pressed, "#entrar")
    def entrar_pelo_botao(self) -> None:
        resumo = self._escolhido()
        if resumo is None:
            self.notify("Escolha um ambiente na lista.")
            return
        self.entrar(resumo)

    @on(ListView.Selected, "#ambientes")
    def entrar_pelo_enter(self, evento: ListView.Selected) -> None:
        if isinstance(evento.item, ItemDeAmbiente):
            self.entrar(evento.item.resumo)

    @on(ItemDeAmbiente.Aberto)
    def entrar_pelo_duplo_clique(self, evento: ItemDeAmbiente.Aberto) -> None:
        self.entrar(evento.resumo)

    @work(exclusive=True, group="entrar")
    async def entrar(self, resumo: ResumoAmbiente) -> None:
        try:
            ambiente = await self.programa.servico.carregar_ambiente(resumo.id)
        except ErroDePersistencia:
            # Inclui AmbienteInexistente: outra janela pode te-lo apagado.
            self.notify("Não consegui abrir este ambiente.", severity="error")
            await self.atualizar()
            return
        await self.app.push_screen(TelaDoAmbiente(self.programa, ambiente))

    # --- apagar -------------------------------------------------------------

    @on(Button.Pressed, "#apagar")
    def pedir_para_apagar(self) -> None:
        resumo = self._escolhido()
        if resumo is None:
            self.notify("Escolha um ambiente na lista.")
            return

        async def depois(confirmou: bool | None) -> None:
            if not confirmou:
                return
            try:
                await self.programa.servico.apagar_ambiente(resumo.id)
            except ErroDePersistencia:
                self.notify("Não consegui apagar o ambiente.", severity="error")
            else:
                self.notify(f"Ambiente {resumo.nome} apagado.", markup=False)
            await self.atualizar()

        self.app.push_screen(JanelaDeApagar(resumo.nome), depois)
