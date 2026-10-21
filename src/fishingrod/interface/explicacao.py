"""O painel de explicacao: o que explica um agente e uma sessao (card 003).

Mora dentro de cada tarefa, a direita do chat, porque tudo o que explica e de
um chat ou de uma sessao. Tem tres abas: a ficha do agente do chat que esta na
frente, a memoria da sessao (D17) e a wiki do ambiente, com a pagina aberta
ali mesmo.

Mexer no painel nao tira o foco do campo de digitacao: o botao "explicar" e as
abas do painel nao recebem foco no clique. E nada aqui toca na conversa - a
resposta de um agente segue no servico de conversa.
"""

from dataclasses import dataclass

from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.widgets import Label, Markdown, Static, TabbedContent, TabPane, Tabs, Tree

from fishingrod.aplicacao.portas.wiki import ErroDeWiki
from fishingrod.dominio import Agente, Ambiente, Sessao
from fishingrod.interface.ficha import Ficha, lista
from fishingrod.interface.frases import texto_da_memoria
from fishingrod.interface.montagem import Programa

FICHA = "aba-ficha"
MEMORIA = "aba-memoria"
WIKI = "aba-wiki"

ESCOLHA_UMA_PAGINA = "Escolha o index ou uma página na árvore para lê-la aqui."


@dataclass
class EstadoDaExplicacao:
    """O que o painel lembra quando a tarefa se redesenha (trocar de sessao,
    abrir um chat): se esta aberto, em que aba e que pagina da wiki."""

    aberto: bool = False
    aba: str = FICHA
    pagina: tuple | None = None  # o `data` do no da wiki: ("index",) ou ("pagina", caminho)


class PainelDeExplicacao(Vertical):
    DEFAULT_CSS = """
    PainelDeExplicacao { width: 52; border-left: solid $panel; padding: 0 0 0 1; }
    PainelDeExplicacao TabbedContent { height: 1fr; }
    PainelDeExplicacao TabPane { padding: 0; }
    PainelDeExplicacao .titulo { text-style: bold; color: $text-muted; margin-top: 1; }
    PainelDeExplicacao #ficha-topo { height: 1; margin-top: 1; }
    PainelDeExplicacao #ficha-nome { width: 1fr; text-style: bold; }
    PainelDeExplicacao #ficha-marca { color: $text-muted; }
    PainelDeExplicacao .campo { height: auto; }
    PainelDeExplicacao .campo .rotulo { width: 24; color: $text-muted; }
    PainelDeExplicacao .campo .valor { width: 1fr; }
    PainelDeExplicacao #ficha-instrucoes { margin-left: 2; }
    PainelDeExplicacao #wiki { height: auto; max-height: 12; }
    PainelDeExplicacao #pagina { height: 1fr; border-top: solid $panel; }
    """

    CAMPOS = (
        ("papel", "Papel"),
        ("modelo", "Modelo"),
        ("esforco", "Esforço de raciocínio"),
        ("ferramentas", "Ferramentas"),
        ("ferramentas-da-maquina", "Ferramentas da máquina"),
    )

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
                    with Horizontal(id="ficha-topo"):
                        yield Label("", id="ficha-nome", markup=False)
                        yield Label("do software", id="ficha-marca")
                    yield Label("CONFIGURAÇÃO", classes="titulo")
                    for chave, rotulo in self.CAMPOS:
                        with Horizontal(classes="campo"):
                            yield Label(rotulo, classes="rotulo")
                            yield Label("", id=f"ficha-{chave}", classes="valor", markup=False)
                    yield Label("INSTRUÇÕES", classes="titulo")
                    yield Static("", id="ficha-instrucoes", markup=False)
            with TabPane("memória", id=MEMORIA):
                with VerticalScroll():
                    yield Label("", id="titulo-da-memoria", classes="titulo", markup=False)
                    yield Markdown("", id="memoria")
            with TabPane("wiki", id=WIKI):
                wiki: Tree = Tree("wiki", id="wiki")
                wiki.show_root = False
                yield wiki
                with VerticalScroll(id="pagina"):
                    yield Markdown(ESCOLHA_UMA_PAGINA, id="texto-da-pagina")

    async def on_mount(self) -> None:
        # As abas mudam com o clique, sem levar o foco: o cursor fica no campo.
        self.query_one(TabbedContent).query_one(Tabs).can_focus = False
        self.mostrar_ficha(self.agente)
        await self.mostrar_memoria(self.sessao)
        await self.desenhar_wiki()
        if self.estado.pagina is not None:
            await self.abrir_pagina(self.estado.pagina)

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
        self.ficha = self.programa.ficha(agente)
        self._escrever_ficha(self.ficha)

    def _escrever_ficha(self, ficha: Ficha) -> None:
        self.query_one("#ficha-nome", Label).update(ficha.nome)
        self.query_one("#ficha-marca", Label).display = ficha.do_software
        valores = {
            "papel": ficha.papel,
            "modelo": ficha.modelo,
            "esforco": ficha.esforco,
            "ferramentas": lista(ficha.ferramentas),
            "ferramentas-da-maquina": lista(ficha.ferramentas_da_maquina),
        }
        for chave, valor in valores.items():
            self.query_one(f"#ficha-{chave}", Label).update(valor)
        self.query_one("#ficha-instrucoes", Static).update(ficha.instrucoes)

    # --- a memoria -----------------------------------------------------------

    async def mostrar_memoria(self, sessao: Sessao) -> None:
        """Redesenha so se mudou: e chamada de tempos em tempos, porque os
        agentes anotam enquanto conversam."""
        self.sessao = sessao
        self.query_one("#titulo-da-memoria", Label).update(f"MEMÓRIA DA {sessao.nome.upper()}")
        texto = texto_da_memoria(sessao.memoria)
        if texto != self._memoria_desenhada:
            self._memoria_desenhada = texto
            await self.query_one("#memoria", Markdown).update(texto)

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
        """A pagina abre aqui, no painel: a area de trabalho e so das tarefas."""
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
        await self.query_one("#texto-da-pagina", Markdown).update(texto)
