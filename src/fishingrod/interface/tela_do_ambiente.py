"""A tela do ambiente: onde a pessoa trabalha.

A esquerda, so a arvore de frentes e tarefas, e no pe dela o "⚙ ambiente",
que abre a janela do ambiente. A direita, a area de trabalho:
uma aba para cada tarefa aberta; dentro da aba da tarefa, a escolha da
sessao, uma aba para cada chat dela (D21) e o painel de explicacao, com a
ficha do agente, a memoria e a wiki (card 003).

Criar frente, tarefa e sessao passa pelo catalogo, como o usuario (D18): a
mesma regra que vale para a barra `/` e para o agente vale para o botao.

A tela guarda ids, e nao as frentes e tarefas: numa recarga por conflito, o
servico troca os objetos de dentro do ambiente (RN-A-03). O Ambiente em si e
sempre o mesmo objeto, e e nele que a tela procura - e e por ele que a arvore
se redesenha quando o orquestrador cria uma frente ou uma tarefa.

No topo, o mostrador das conexoes com o Claude (card 002). Sair do ambiente
desliga os chats dele.
"""

from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import Button, ContentSwitcher, Label, Select, Tab, TabbedContent, TabPane, Tabs, Tree

from fishingrod.aplicacao.catalogo.tipos import Acionamento, Alvo, Resultado
from fishingrod.aplicacao.portas.sessao import ContextoDaSessao
from fishingrod.dominio import Ambiente, Frente, Identidade, Sessao, Tarefa
from fishingrod.interface.chat import ChatAberto
from fishingrod.interface.explicacao import EstadoDaExplicacao, PainelDeExplicacao
from fishingrod.interface.frases import frase_da_falha, frase_das_conexoes
from fishingrod.interface.janela_do_ambiente import JanelaDoAmbiente
from fishingrod.interface.janelas import JanelaDeAgente, JanelaDeNome
from fishingrod.interface.montagem import Programa

SEM_FRENTES = "Este ambiente ainda não tem frentes. Comece em [b]+ frente[/b]."
NADA_ABERTO = "Escolha uma tarefa na árvore para abri-la aqui."


def _achar(ambiente: Ambiente, id_tarefa: Identidade) -> tuple[Frente, Tarefa] | None:
    for frente in ambiente.frentes:
        tarefa = frente.buscar_tarefa(id_tarefa)
        if tarefa is not None:
            return frente, tarefa
    return None


def _achar_tarefa(ambiente: Ambiente, id_tarefa: Identidade) -> Tarefa | None:
    achado = _achar(ambiente, id_tarefa)
    return achado[1] if achado else None


def _forma_da_arvore(ambiente: Ambiente) -> tuple:
    """O que a arvore mostra: muda quando alguem (a tela ou o agente) cria,
    renomeia ou tira uma frente ou tarefa."""
    return tuple((f.id, f.nome, tuple((t.id, t.nome) for t in f.tarefas)) for f in ambiente.frentes)


def id_da_aba(prefixo: str, valor: str) -> str:
    return f"{prefixo}-{valor}"


# --------------------------------------------------------------------------
# A tarefa aberta: sessoes e chats
# --------------------------------------------------------------------------


class PainelDaTarefa(Vertical):
    """Uma tarefa aberta numa aba. Na barra de cima, a sessao escolhida e o
    botao de abrir outra, uma aba para cada chat da sessao, o botao de abrir
    outro chat e o "explicar"; embaixo, o chat que esta na frente e, a direita
    dele, o painel de explicacao, quando esta aberto (D17, D21, card 003).

    O painel de explicacao e de cada tarefa: abrir numa nao mexe na outra.
    Ele so se mostra e se esconde, sem redesenhar a tarefa - assim o campo de
    digitacao fica onde estava, com o que ja foi escrito nele.

    As abas dos chats sao Tabs e ContentSwitcher, e nao um TabbedContent: e o
    que deixa os botoes na mesma linha das abas."""

    DEFAULT_CSS = """
    PainelDaTarefa .barra { height: auto; margin-bottom: 1; }
    PainelDaTarefa .barra Select { width: 18; }
    PainelDaTarefa .barra Tabs { width: 1fr; margin-left: 1; }
    PainelDaTarefa .barra Button { margin-left: 1; }
    PainelDaTarefa #conversas { width: 1fr; height: 1fr; }
    """

    def __init__(self, programa: Programa, ambiente: Ambiente, id_tarefa: Identidade) -> None:
        super().__init__()
        self.programa = programa
        self.ambiente = ambiente
        self.id_tarefa = id_tarefa
        tarefa = self.tarefa
        self.id_sessao = tarefa.sessoes[0].id if tarefa and tarefa.sessoes else None
        self.id_chat: Identidade | None = None  # o chat a mostrar; None e o primeiro
        # Fica como esta ao trocar de sessao: o que aparece e o da sessao nova.
        self.explicacao = EstadoDaExplicacao()

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
        sessao = self._sessao(tarefa)
        ativo = None
        if sessao is not None and sessao.chats:
            ativo = (sessao.buscar_chat(self.id_chat) if self.id_chat else None) or sessao.chats[0]
        with Horizontal(classes="barra"):
            yield Select(
                [(s.nome, s.id.valor) for s in tarefa.sessoes],
                value=self.id_sessao.valor if self.id_sessao else Select.NULL,
                allow_blank=False,
                id="sessao",
                compact=True,
            )
            yield Button("+ sessão", id="nova-sessao", compact=True)
            if ativo is None:
                return
            yield Tabs(
                *(Tab(chat.nome, id=id_da_aba("chat", chat.id.valor)) for chat in sessao.chats),
                active=id_da_aba("chat", ativo.id.valor),
                id="abas-de-chat",
            )
            yield Button("+ chat", id="novo-chat", compact=True)
            explicar = Button(
                "explicar",
                id="explicar",
                classes="-ligado" if self.explicacao.aberto else "",
                tooltip="Mostra a ficha do agente, a memória da sessão e a wiki, ao lado do chat",
                compact=True,
            )
            # Clicar nao leva o foco: o cursor continua no campo de digitacao.
            explicar.can_focus = False
            yield explicar
        with Horizontal():
            with ContentSwitcher(initial=id_da_aba("conversa", ativo.id.valor), id="conversas"):
                id_frente = _achar(self.ambiente, self.id_tarefa)[0].id
                for chat in sessao.chats:
                    contexto = ContextoDaSessao(self.ambiente.id, id_frente, self.id_tarefa, sessao.id, chat.id)
                    yield ChatAberto(
                        self.programa.conversa, contexto, chat.agente, id=id_da_aba("conversa", chat.id.valor)
                    )
            yield PainelDeExplicacao(
                self.programa, self.ambiente, self.explicacao, ativo.agente, sessao, id="explicacao"
            )

    @on(Button.Pressed, "#explicar")
    async def alternar_explicacao(self, evento: Button.Pressed) -> None:
        self.explicacao.aberto = not self.explicacao.aberto
        evento.button.set_class(self.explicacao.aberto, "-ligado")
        painel = self.query_one("#explicacao", PainelDeExplicacao)
        painel.display = self.explicacao.aberto
        if self.explicacao.aberto:
            # A memoria pode ter mudado desde a ultima vez que apareceu.
            await self.atualizar()

    async def atualizar(self) -> None:
        """A memoria no painel, se ele esta aberto: os agentes anotam enquanto
        conversam. A tela chama de tempos em tempos."""
        tarefa = self.tarefa
        paineis = self.query(PainelDeExplicacao)
        if not self.explicacao.aberto or tarefa is None or not paineis:
            return
        sessao = self._sessao(tarefa)
        if sessao is not None:
            await paineis.first().mostrar_memoria(sessao)

    @on(Tabs.TabActivated, "#abas-de-chat")
    def trocar_de_chat(self, evento: Tabs.TabActivated) -> None:
        valor = evento.tab.id.removeprefix("chat-")
        self.id_chat = Identidade(valor)
        self.query_one("#conversas", ContentSwitcher).current = id_da_aba("conversa", valor)
        # A ficha segue o chat que esta na frente.
        conversa = self.query_one(f"#{id_da_aba('conversa', valor)}", ChatAberto)
        painel = self.query_one("#explicacao", PainelDeExplicacao)
        if painel.is_mounted:
            painel.mostrar_ficha(conversa.agente)
        else:
            painel.agente = conversa.agente

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


# --------------------------------------------------------------------------
# A tela
# --------------------------------------------------------------------------


class TelaDoAmbiente(Screen):
    DEFAULT_CSS = """
    TelaDoAmbiente #topo { height: 2; padding: 0 1; border-bottom: solid $panel; }
    TelaDoAmbiente #nome-do-ambiente { width: 1fr; text-style: bold; }
    TelaDoAmbiente #conexoes { padding: 0 2 0 0; color: $text-muted; }
    TelaDoAmbiente #lateral { width: 36; border-right: solid $panel; padding: 0 1; }
    TelaDoAmbiente #frentes-e-tarefas { height: 1fr; }
    TelaDoAmbiente #configuracoes { width: 100%; margin: 1 0; }
    TelaDoAmbiente .titulo-lateral { color: $text-muted; text-style: bold; margin-top: 1; }
    TelaDoAmbiente #arvore { height: auto; max-height: 20; }
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
            yield Label(frase_das_conexoes(0), id="conexoes")
            yield Button("← ambientes", id="voltar", compact=True)
        with Horizontal():
            with Vertical(id="lateral"):
                with VerticalScroll(id="frentes-e-tarefas"):
                    yield Label("FRENTES E TAREFAS", classes="titulo-lateral")
                    yield Label(SEM_FRENTES, id="sem-frentes")
                    arvore: Tree = Tree("frentes", id="arvore")
                    arvore.show_root = False
                    yield arvore
                    with Horizontal(id="botoes-da-arvore"):
                        yield Button("+ frente", id="nova-frente", compact=True)
                        yield Button("+ tarefa", id="nova-tarefa", compact=True)
                yield Button("⚙ ambiente", id="configuracoes", compact=True)
            with Vertical(id="trabalho"):
                yield Label(NADA_ABERTO, id="nada-aberto")
                yield TabbedContent(id="abertas")

    async def on_mount(self) -> None:
        self.desenhar_arvore()
        self._mostrar_abertas()
        self.atualizar()
        self.set_interval(0.5, self.atualizar)
        self.set_interval(1, self.atualizar_explicacoes)

    def atualizar(self) -> None:
        """O mostrador, e a arvore se o agente mexeu nela."""
        self.query_one("#conexoes", Label).update(frase_das_conexoes(self.programa.conversa.conexoes_abertas()))
        if _forma_da_arvore(self.ambiente) != self._forma_desenhada:
            no = self.query_one("#arvore", Tree).cursor_node
            self.desenhar_arvore(selecionar=no.data[-1] if no is not None and no.data else None)

    async def atualizar_explicacoes(self) -> None:
        """A memoria nos paineis de explicacao abertos: os agentes anotam
        enquanto conversam."""
        for painel in self.query(PainelDaTarefa):
            await painel.atualizar()

    # --- a arvore de frentes e tarefas ---------------------------------------

    def desenhar_arvore(self, selecionar: Identidade | None = None) -> None:
        self._forma_desenhada = _forma_da_arvore(self.ambiente)
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

    # --- a janela do ambiente ---------------------------------------------

    @on(Button.Pressed, "#configuracoes")
    def abrir_configuracoes(self) -> None:
        self.app.push_screen(JanelaDoAmbiente(self.programa, self.ambiente))

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
    async def action_voltar(self) -> None:
        # Sair do ambiente desliga os chats dele; uma resposta em andamento e
        # interrompida, como no Esc (card 002).
        if self.programa.conversa.conexoes_abertas():
            self.notify("Desligando os chats deste ambiente…")
        await self.programa.conversa.desligar_ambiente(self.ambiente.id)
        if self.app.screen is self:
            self.app.pop_screen()
