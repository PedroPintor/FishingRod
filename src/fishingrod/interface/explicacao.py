"""O painel de explicacao: o que explica um agente e uma sessao (card 003).

Mora dentro de cada tarefa, a direita do chat, porque tudo o que explica e de
um chat ou de uma sessao. Tem tres abas: a ficha do agente do chat que esta na
frente, a memoria da sessao (D17) e a wiki do ambiente - a lista das paginas
ou uma pagina aberta, com o "voltar" para a lista.

Nada no painel recebe foco: nem o botao "explicar", nem as abas, nem a
arvore, nem os quadros de texto. O cursor fica no campo de digitacao do chat.
E isso tambem evita uma armadilha da Textual: uma aba com algo focado dentro
volta a ser a aba ativa, e prendia a pessoa na aba "wiki". Rolar com a roda
do mouse e clicar continuam funcionando. E nada aqui toca na conversa - a
resposta de um agente segue no servico de conversa.
"""

from dataclasses import dataclass

from textual import on
from textual.app import ComposeResult
from textual.containers import Vertical, VerticalScroll
from textual.widget import Widget
from textual.widgets import Button, ContentSwitcher, Label, Markdown, TabbedContent, TabPane, Tree

from fishingrod.aplicacao.portas.wiki import ErroDeWiki
from fishingrod.dominio import Agente, Ambiente, Sessao
from fishingrod.interface.ficha import FichaNaTela
from fishingrod.interface.frases import texto_da_memoria
from fishingrod.interface.montagem import Programa

FICHA = "aba-ficha"
MEMORIA = "aba-memoria"
WIKI = "aba-wiki"

LISTA_DA_WIKI = "wiki-lista"
PAGINA_DA_WIKI = "wiki-pagina"


@dataclass
class EstadoDaExplicacao:
    """O que o painel lembra quando a tarefa se redesenha (trocar de sessao,
    abrir um chat): se esta aberto, em que aba e que pagina da wiki."""

    aberto: bool = False
    aba: str = FICHA
    pagina: tuple | None = None  # o `data` do no da wiki: ("index",) ou ("pagina", caminho)


def sem_foco(raiz: Widget) -> None:
    """Tira o foco de `raiz` e de tudo dentro dela. O Markdown monta os seus
    blocos de novo a cada pagina, por isso e chamada outra vez depois."""
    for widget in (raiz, *raiz.query("*")):
        widget.can_focus = False


class PainelDeExplicacao(Vertical):
    DEFAULT_CSS = """
    PainelDeExplicacao { width: 52; border-left: solid $panel; padding: 0 0 0 1; }
    PainelDeExplicacao TabbedContent { height: 1fr; }
    PainelDeExplicacao TabPane { padding: 0; }
    PainelDeExplicacao .titulo { text-style: bold; color: $text-muted; margin-top: 1; }
    PainelDeExplicacao #wiki-pagina #voltar-a-lista { margin-top: 1; }
    """

    def __init__(
        self, programa: Programa, ambiente: Ambiente, estado: EstadoDaExplicacao, agente: Agente, sessao: Sessao, **kwargs
    ) -> None:
        super().__init__(**kwargs)
        self.programa = programa
        self.ambiente = ambiente
        self.estado = estado
        self.agente = agente
        self.sessao = sessao
        self._memoria_desenhada: str | None = None
        self.display = estado.aberto

    def compose(self) -> ComposeResult:
        with TabbedContent(initial=self.estado.aba):
            with TabPane("ficha", id=FICHA):
                with VerticalScroll():
                    yield FichaNaTela()
            with TabPane("memória", id=MEMORIA):
                with VerticalScroll():
                    yield Label("", id="titulo-da-memoria", classes="titulo", markup=False)
                    yield Markdown("", id="memoria")
            with TabPane("wiki", id=WIKI):
                with ContentSwitcher(initial=LISTA_DA_WIKI, id="telas-da-wiki"):
                    with VerticalScroll(id=LISTA_DA_WIKI):
                        wiki: Tree = Tree("wiki", id="wiki")
                        wiki.show_root = False
                        yield wiki
                    with VerticalScroll(id=PAGINA_DA_WIKI):
                        yield Button("← voltar", id="voltar-a-lista", compact=True)
                        yield Markdown("", id="texto-da-pagina")

    async def on_mount(self) -> None:
        self.mostrar_ficha(self.agente)
        await self.mostrar_memoria(self.sessao)
        await self.desenhar_wiki()
        if self.estado.pagina is not None:
            await self.abrir_pagina(self.estado.pagina)
        sem_foco(self)

    @on(TabbedContent.TabActivated)
    async def trocar_de_aba(self, evento: TabbedContent.TabActivated) -> None:
        evento.stop()  # a tela tem o seu proprio TabbedContent, das tarefas
        self.estado.aba = evento.pane.id
        if evento.pane.id == MEMORIA:
            await self.mostrar_memoria(self.sessao)

    # --- a ficha -------------------------------------------------------------

    def mostrar_ficha(self, agente: Agente) -> None:
        """A ficha segue o chat que esta na frente."""
        self.agente = agente
        self.query_one(FichaNaTela).mostrar(self.programa.ficha(agente))

    # --- a memoria -----------------------------------------------------------

    async def mostrar_memoria(self, sessao: Sessao) -> None:
        """Redesenha so se mudou: e chamada de tempos em tempos, porque os
        agentes anotam enquanto conversam."""
        self.sessao = sessao
        self.query_one("#titulo-da-memoria", Label).update(f"MEMÓRIA DA {sessao.nome.upper()}")
        texto = texto_da_memoria(sessao.memoria)
        if texto != self._memoria_desenhada:
            self._memoria_desenhada = texto
            memoria = self.query_one("#memoria", Markdown)
            await memoria.update(texto)
            sem_foco(memoria)

    # --- a wiki --------------------------------------------------------------

    async def desenhar_wiki(self) -> None:
        wiki = self.query_one("#wiki", Tree)
        wiki.clear()
        localizador = self.ambiente.raiz_wiki.localizador
        wiki.root.add_leaf("index", data=("index",))
        try:
            entidades = await self.programa.wiki.listar(localizador, "")
            for entidade in entidades:
                no = wiki.root.add(entidade, expand=False)
                for pagina in await self.programa.wiki.listar(localizador, entidade):
                    no.add_leaf(pagina, data=("pagina", f"{entidade}/{pagina}"))
        except ErroDeWiki:
            self.notify("Não consegui ler a wiki deste ambiente.", severity="error")

    @on(Tree.NodeSelected, "#wiki")
    async def abrir_da_wiki(self, evento: Tree.NodeSelected) -> None:
        if evento.node.data:
            await self.abrir_pagina(evento.node.data)

    async def abrir_pagina(self, dado: tuple) -> None:
        """A pagina abre aqui, no lugar da lista: a area de trabalho e so das
        tarefas."""
        localizador = self.ambiente.raiz_wiki.localizador
        try:
            if dado[0] == "index":
                texto = await self.programa.wiki.ler_index(localizador)
            else:
                pagina = await self.programa.wiki.ler(localizador, dado[1])
                texto = f"# {pagina.titulo or dado[1]}\n\n{pagina.conteudo}"
        except ErroDeWiki:
            self.notify("Não consegui ler esta página da wiki.", severity="error")
            return
        self.estado.pagina = dado
        markdown = self.query_one("#texto-da-pagina", Markdown)
        await markdown.update(texto)
        sem_foco(markdown)
        self.query_one("#telas-da-wiki", ContentSwitcher).current = PAGINA_DA_WIKI
        self.query_one(f"#{PAGINA_DA_WIKI}", VerticalScroll).scroll_home(animate=False)

    @on(Button.Pressed, "#voltar-a-lista")
    def voltar_a_lista(self, evento: Button.Pressed) -> None:
        evento.stop()
        self.estado.pagina = None
        self.query_one("#telas-da-wiki", ContentSwitcher).current = LISTA_DA_WIKI
