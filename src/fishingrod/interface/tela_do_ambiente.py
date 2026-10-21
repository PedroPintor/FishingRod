"""A tela do ambiente: onde a pessoa trabalha.

A esquerda, a arvore de frentes e tarefas, a wiki e os agentes. A direita,
uma aba para cada tarefa ou pagina da wiki aberta; dentro da aba da tarefa,
a escolha da sessao e uma aba para cada chat dela (D21).

Criar frente, tarefa e sessao passa pelo catalogo, como o usuario (D18): a
mesma regra que vale para a barra `/` e para o agente vale para o botao.

A tela guarda ids, e nao as frentes e tarefas: numa recarga por conflito, o
servico troca os objetos de dentro do ambiente (RN-A-03). O Ambiente em si e
sempre o mesmo objeto, e e nele que a tela procura.
"""

from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import (
    Button,
    ContentSwitcher,
    Label,
    Markdown,
    Select,
    Static,
    Tab,
    TabbedContent,
    TabPane,
    Tabs,
    Tree,
)

from fishingrod.aplicacao.catalogo.tipos import Acionamento, Alvo, Resultado
from fishingrod.aplicacao.portas.wiki import ErroDeWiki
from fishingrod.dominio import Ambiente, Chat, Identidade, Sessao, Tarefa
from fishingrod.interface.frases import frase_da_falha, texto_da_memoria
from fishingrod.interface.janelas import JanelaDeAgente, JanelaDeNome
from fishingrod.interface.montagem import Programa

SEM_FRENTES = "Este ambiente ainda não tem frentes. Comece em [b]+ frente[/b]."
NADA_ABERTO = "Escolha uma tarefa na árvore, ou uma página da wiki, para abri-la aqui."
CHAT_SEM_CONVERSA = "A conversa com a IA ainda não está ligada nesta tela: ela chega no próximo card."


def _achar_tarefa(ambiente: Ambiente, id_tarefa: Identidade) -> Tarefa | None:
    for frente in ambiente.frentes:
        tarefa = frente.buscar_tarefa(id_tarefa)
        if tarefa is not None:
            return tarefa
    return None


def id_da_aba(prefixo: str, valor: str) -> str:
    # Id de widget aceita letra, numero, - e _: a barra do caminho da wiki vira --.
    return f"{prefixo}-{valor.replace('/', '--')}"


# --------------------------------------------------------------------------
# A tarefa aberta: sessoes e chats
# --------------------------------------------------------------------------


class PainelDaTarefa(Vertical):
    """Uma tarefa aberta numa aba. Em cima, a sessao escolhida, o botao de
    abrir outra e o de mostrar a memoria; embaixo, uma aba para cada chat da
    sessao, com o botao de abrir outro chat ao lado delas, e a direita a
    memoria da sessao, quando esta a mostra (D17, D21).

    As abas dos chats sao Tabs e ContentSwitcher, e nao um TabbedContent: e o
    que deixa o botao "+ chat" na mesma linha das abas."""

    DEFAULT_CSS = """
    PainelDaTarefa .sessoes { height: auto; margin-bottom: 1; }
    PainelDaTarefa .sessoes Label { padding: 1 1 0 0; }
    PainelDaTarefa .sessoes Select { width: 30; }
    PainelDaTarefa .sessoes Button { margin-left: 1; }
    PainelDaTarefa .barra-de-chats { height: auto; }
    PainelDaTarefa .barra-de-chats Tabs { width: 1fr; }
    PainelDaTarefa .barra-de-chats Button { margin-left: 1; }
    PainelDaTarefa .chat { padding: 1; }
    PainelDaTarefa .area-dos-chats { width: 1fr; }
    PainelDaTarefa #memoria { width: 40; border-left: solid $panel; padding: 0 1; }
    PainelDaTarefa #memoria .titulo-da-memoria { text-style: bold; color: $text-muted; }
    PainelDaTarefa #mostrar-memoria.-ligado { background: $accent; }
    """

    def __init__(self, programa: Programa, ambiente: Ambiente, id_tarefa: Identidade) -> None:
        super().__init__()
        self.programa = programa
        self.ambiente = ambiente
        self.id_tarefa = id_tarefa
        tarefa = self.tarefa
        self.id_sessao = tarefa.sessoes[0].id if tarefa and tarefa.sessoes else None
        self.id_chat: Identidade | None = None  # o chat a mostrar; None e o primeiro
        # Fica ligado ao trocar de sessao: a memoria que aparece e a da sessao nova.
        self.mostrar_memoria = False

    @property
    def tarefa(self) -> Tarefa | None:
        return _achar_tarefa(self.ambiente, self.id_tarefa)

    def _sessao(self, tarefa: Tarefa) -> Sessao | None:
        return tarefa.buscar_sessao(self.id_sessao) if self.id_sessao else None

    def compose(self) -> ComposeResult:
        tarefa = self.tarefa
        if tarefa is None:
            yield Label("Esta tarefa não existe mais.")
            return
        with Horizontal(classes="sessoes"):
            yield Label("Sessão:")
            yield Select(
                [(sessao.nome, sessao.id.valor) for sessao in tarefa.sessoes],
                value=self.id_sessao.valor if self.id_sessao else Select.NULL,
                allow_blank=False,
                id="sessao",
            )
            yield Button("+ sessão", id="nova-sessao")
            yield Button(
                "memória",
                id="mostrar-memoria",
                classes="-ligado" if self.mostrar_memoria else "",
                tooltip="Mostra o que os agentes desta sessão anotaram uns para os outros",
            )
        sessao = self._sessao(tarefa)
        if sessao is None or not sessao.chats:
            return
        ativo = sessao.buscar_chat(self.id_chat) if self.id_chat else None
        ativo = ativo or sessao.chats[0]
        with Horizontal():
            with Vertical(classes="area-dos-chats"):
                with Horizontal(classes="barra-de-chats"):
                    yield Tabs(
                        *(Tab(chat.nome, id=id_da_aba("chat", chat.id.valor)) for chat in sessao.chats),
                        active=id_da_aba("chat", ativo.id.valor),
                        id="abas-de-chat",
                    )
                    yield Button("+ chat", id="novo-chat")
                with ContentSwitcher(initial=id_da_aba("conversa", ativo.id.valor), id="conversas"):
                    for chat in sessao.chats:
                        yield Static(
                            _texto_do_chat(chat),
                            classes="chat",
                            markup=False,
                            id=id_da_aba("conversa", chat.id.valor),
                        )
            if self.mostrar_memoria:
                with VerticalScroll(id="memoria"):
                    yield Label(f"MEMÓRIA DA {sessao.nome.upper()}", classes="titulo-da-memoria", markup=False)
                    yield Markdown(texto_da_memoria(sessao.memoria))

    @on(Button.Pressed, "#mostrar-memoria")
    async def alternar_memoria(self) -> None:
        # Redesenhar, e nao so esconder: a memoria pode ter mudado desde a
        # ultima vez que apareceu.
        self.mostrar_memoria = not self.mostrar_memoria
        await self.recompose()

    @on(Tabs.TabActivated, "#abas-de-chat")
    def trocar_de_chat(self, evento: Tabs.TabActivated) -> None:
        valor = evento.tab.id.removeprefix("chat-")
        self.id_chat = Identidade(valor)
        self.query_one("#conversas", ContentSwitcher).current = id_da_aba("conversa", valor)

    @on(Button.Pressed, "#novo-chat")
    def pedir_agente(self) -> None:
        # O orquestrador nao aparece: cada sessao ja tem o seu, e so pode ter
        # um (D03). Os outros sao a lista fixa de agentes (D20).
        nomes = tuple(a.nome for a in self.programa.agentes if not a.e_orquestrador)
        self.app.push_screen(JanelaDeAgente(nomes), self.criar_chat)

    async def criar_chat(self, nome_do_agente: str | None) -> None:
        if nome_do_agente is None or self.id_sessao is None:
            return
        resultado = await self.programa.catalogo.executar(
            "criar_chat",
            Alvo(self.ambiente.id, id_sessao=self.id_sessao),
            {"agente": nome_do_agente},
            Acionamento.usuario(),
        )
        if not resultado.sucesso:
            self.notify(frase_da_falha(resultado), severity="error")
            return
        self.id_chat = resultado.dado.id
        await self.recompose()

    @on(Select.Changed, "#sessao")
    async def trocar_de_sessao(self, evento: Select.Changed) -> None:
        if evento.value is Select.NULL or (self.id_sessao and evento.value == self.id_sessao.valor):
            return
        self.id_sessao = Identidade(evento.value)
        self.id_chat = None
        await self.recompose()

    @on(Button.Pressed, "#nova-sessao")
    async def criar_sessao(self) -> None:
        # Sem nome: a sessao nova se chama "sessão N" (D21).
        resultado = await self.programa.catalogo.executar(
            "criar_sessao", Alvo(self.ambiente.id, id_tarefa=self.id_tarefa), {}, Acionamento.usuario()
        )
        if not resultado.sucesso:
            self.notify(frase_da_falha(resultado), severity="error")
            return
        self.id_sessao = resultado.dado.id
        self.id_chat = None
        await self.recompose()
        self.notify(f"{resultado.dado.nome} criada.", markup=False)


def _texto_do_chat(chat: Chat) -> str:
    return f"Chat com o agente {chat.agente.nome}.\n\n{CHAT_SEM_CONVERSA}"


# --------------------------------------------------------------------------
# A tela
# --------------------------------------------------------------------------


class TelaDoAmbiente(Screen):
    DEFAULT_CSS = """
    TelaDoAmbiente #topo { height: 3; padding: 0 1; border-bottom: solid $panel; }
    TelaDoAmbiente #nome-do-ambiente { width: 1fr; padding-top: 1; text-style: bold; }
    TelaDoAmbiente #lateral { width: 36; border-right: solid $panel; padding: 0 1; }
    TelaDoAmbiente .titulo-lateral { color: $text-muted; text-style: bold; margin-top: 1; }
    TelaDoAmbiente #arvore { height: auto; max-height: 20; }
    TelaDoAmbiente #wiki { height: auto; max-height: 10; }
    TelaDoAmbiente #sem-frentes { width: 100%; color: $text-muted; }
    TelaDoAmbiente #botoes-da-arvore { height: auto; }
    TelaDoAmbiente #botoes-da-arvore Button { margin-right: 1; }
    TelaDoAmbiente #trabalho { padding: 0 1; }
    TelaDoAmbiente #nada-aberto { color: $text-muted; padding: 1; }
    """

    BINDINGS = [
        Binding("escape", "voltar", "Voltar aos ambientes"),
        Binding("f", "nova_frente", "Nova frente"),
        Binding("t", "nova_tarefa", "Nova tarefa"),
    ]

    def __init__(self, programa: Programa, ambiente: Ambiente) -> None:
        super().__init__()
        self.programa = programa
        self.ambiente = ambiente

    def compose(self) -> ComposeResult:
        with Horizontal(id="topo"):
            yield Label(self.ambiente.nome, id="nome-do-ambiente", markup=False)
            yield Button("← ambientes", id="voltar")
        with Horizontal():
            with VerticalScroll(id="lateral"):
                yield Label("FRENTES E TAREFAS", classes="titulo-lateral")
                yield Label(SEM_FRENTES, id="sem-frentes")
                arvore: Tree = Tree("frentes", id="arvore")
                arvore.show_root = False
                yield arvore
                with Horizontal(id="botoes-da-arvore"):
                    yield Button("+ frente", id="nova-frente")
                    yield Button("+ tarefa", id="nova-tarefa")
                yield Label("WIKI", classes="titulo-lateral")
                wiki: Tree = Tree("wiki", id="wiki")
                wiki.show_root = False
                yield wiki
                yield Label("AGENTES", classes="titulo-lateral")
                yield Static(self._agentes(), id="agentes", markup=False)
            with Vertical(id="trabalho"):
                yield Label(NADA_ABERTO, id="nada-aberto")
                yield TabbedContent(id="abertas")

    async def on_mount(self) -> None:
        self.desenhar_arvore()
        await self.desenhar_wiki()
        self._mostrar_abertas()

    def _agentes(self) -> str:
        linhas = []
        for agente in self.programa.agentes:
            papel = "abre cada sessão" if agente.e_orquestrador else "pode ser chamado num chat"
            linhas.append(f"• {agente.nome} — {papel}")
        return "\n".join(linhas)

    # --- a arvore de frentes e tarefas ---------------------------------------

    def desenhar_arvore(self, selecionar: Identidade | None = None) -> None:
        arvore = self.query_one("#arvore", Tree)
        arvore.clear()
        no_escolhido = None
        for frente in self.ambiente.frentes:
            no_da_frente = arvore.root.add(frente.nome, data=("frente", frente.id), expand=True)
            if frente.id == selecionar:
                no_escolhido = no_da_frente
            for tarefa in frente.tarefas:
                no = no_da_frente.add_leaf(tarefa.nome, data=("tarefa", frente.id, tarefa.id))
                if tarefa.id == selecionar:
                    no_escolhido = no
        sem_frentes = not self.ambiente.frentes
        self.query_one("#sem-frentes", Label).display = sem_frentes
        arvore.display = not sem_frentes
        if no_escolhido is not None:
            arvore.move_cursor(no_escolhido)

    def _frente_escolhida(self) -> Identidade | None:
        no = self.query_one("#arvore", Tree).cursor_node
        if no is None or no.data is None:
            return None
        return no.data[1]  # ("frente", id) ou ("tarefa", id_frente, id_tarefa)

    @on(Tree.NodeSelected, "#arvore")
    async def abrir_da_arvore(self, evento: Tree.NodeSelected) -> None:
        if evento.node.data and evento.node.data[0] == "tarefa":
            await self.abrir_tarefa(evento.node.data[2])

    # --- criar frente e tarefa ---------------------------------------------

    async def _executar(self, acao: str, alvo: Alvo, argumentos: dict) -> Resultado:
        resultado = await self.programa.catalogo.executar(acao, alvo, argumentos, Acionamento.usuario())
        if not resultado.sucesso:
            self.notify(frase_da_falha(resultado), severity="error")
        return resultado

    @on(Button.Pressed, "#nova-frente")
    def action_nova_frente(self) -> None:
        async def depois(nome: str | None) -> None:
            if nome is None:
                return
            resultado = await self._executar("criar_frente", Alvo(self.ambiente.id), {"nome": nome})
            if resultado.sucesso:
                self.desenhar_arvore(selecionar=resultado.dado.id)

        self.app.push_screen(JanelaDeNome("Nome da nova frente"), depois)

    @on(Button.Pressed, "#nova-tarefa")
    def action_nova_tarefa(self) -> None:
        if not self.ambiente.frentes:
            self.notify("Crie uma frente primeiro: a tarefa mora numa frente.")
            return
        id_frente = self._frente_escolhida()
        if id_frente is None:
            self.notify("Escolha na árvore a frente da tarefa.")
            return
        frente = self.ambiente.buscar_frente(id_frente)

        async def depois(nome: str | None) -> None:
            if nome is None:
                return
            resultado = await self._executar(
                "criar_tarefa", Alvo(self.ambiente.id, id_frente), {"nome": nome}
            )
            if resultado.sucesso:
                self.desenhar_arvore(selecionar=resultado.dado.id)
                await self.abrir_tarefa(resultado.dado.id)

        self.app.push_screen(JanelaDeNome(f"Nome da nova tarefa em {frente.nome}"), depois)

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
        dado = evento.node.data
        if not dado:
            return
        localizador = self.ambiente.raiz_wiki.localizador
        try:
            if dado[0] == "index":
                titulo, texto = "wiki: index", await self.programa.wiki.ler_index(localizador)
                id_aba = id_da_aba("wiki", "index")
            else:
                pagina = await self.programa.wiki.ler(localizador, dado[1])
                titulo = f"wiki: {pagina.titulo or dado[1]}"
                texto = f"# {pagina.titulo or dado[1]}\n\n{pagina.conteudo}"
                id_aba = id_da_aba("wiki", dado[1])
        except ErroDeWiki:
            self.notify("Não consegui ler esta página da wiki.", severity="error")
            return
        await self._abrir_aba(id_aba, titulo, lambda: VerticalScroll(Markdown(texto)))

    # --- as abas -------------------------------------------------------------

    def _mostrar_abertas(self) -> None:
        abertas = self.query_one("#abertas", TabbedContent)
        tem_aba = abertas.tab_count > 0
        abertas.display = tem_aba
        self.query_one("#nada-aberto", Label).display = not tem_aba

    async def _abrir_aba(self, id_aba: str, titulo: str, conteudo) -> None:
        """Ativa a aba se ela ja esta aberta; senao, abre e ativa."""
        abertas = self.query_one("#abertas", TabbedContent)
        if not abertas.query(f"#{id_aba}"):
            await abertas.add_pane(TabPane(titulo, conteudo(), id=id_aba))
        abertas.active = id_aba
        self._mostrar_abertas()

    async def abrir_tarefa(self, id_tarefa: Identidade) -> None:
        tarefa = _achar_tarefa(self.ambiente, id_tarefa)
        if tarefa is None:
            return
        await self._abrir_aba(
            id_da_aba("tarefa", id_tarefa.valor),
            tarefa.nome,
            lambda: PainelDaTarefa(self.programa, self.ambiente, id_tarefa),
        )

    # --- voltar ------------------------------------------------------------

    @on(Button.Pressed, "#voltar")
    def action_voltar(self) -> None:
        self.app.pop_screen()
