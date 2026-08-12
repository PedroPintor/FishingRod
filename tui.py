"""Interface TUI (Textual) do FishingRod.

Regra desta camada: aqui so existe PINTURA.
Nenhuma decisao de negocio mora neste arquivo - toda regra esta em
sessao.py e ambiente.py. Se um dia o Textual for trocado, e este arquivo
que se joga fora.

A tela fala com o AMBIENTE (o topo da arvore) e nunca pula camada:
    Ambiente -> Projeto -> Sessao -> Chat

Sidebar:
    metade de cima  -> lista de projetos do ambiente
    metade de baixo -> arvore de sessoes do projeto ativo; cada sessao
                       abre e mostra os chats dela
"""
from rich.markup import escape

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import (
    Footer,
    Header,
    Input,
    Label,
    ListItem,
    ListView,
    RichLog,
    Static,
    Tree,
)

from Ambiente.ambiente import Ambiente, Projeto
from Ambiente.sessao import Mensagem, Sessao

# cor vem do TIPO (vocabulario fechado), nunca do AUTOR (texto livre)
CORES = {
    "usuario": "cyan",
    "agente": "green",
    "sistema": "yellow",
}

# etiquetas penduradas em cada no da arvore. A tela le o objeto pelo
# 'data' do no, nao pela posicao da linha na tela.
NO_SESSAO = "sessao"
NO_CHAT = "chat"


def formatar(m: Mensagem) -> str:
    cor = CORES.get(m.tipo, "white")
    return f"[{cor}]{escape(m.autor)}[/]: {escape(m.texto)}"


def formatar_status(status: dict) -> str:
    # o caminho completo: o usuario precisa saber ONDE ele esta
    return escape(
        f" {status['nome_projeto']} / {status['nome_sessao']} / {status['nome_chat']} "
        f"| iteracoes: {status['n_iteracoes']} "
        f"| memoria: {status['memoria']} "
    )


class TelaAmbiente(Screen):
    def __init__(self, ambiente: Ambiente) -> None:
        super().__init__()
        self.ambiente = ambiente
        # QUAIS CARDS ESTAO ABERTOS e' estado de PINTURA, nao de negocio.
        # Por isso mora aqui e nao na Sessao: o cli.py nao tem cards, a web
        # de amanha pode nem ter. Guardado por nome (nao por indice) para
        # sobreviver a criacao de sessao e troca de projeto.
        self._expandidas: set[tuple[str, str]] = set()
        self._recarregando = False

    # atalhos de LEITURA. A tela desce a arvore para pintar,
    # mas quando decide chama a mesma regra que o comando chama.
    @property
    def projeto(self) -> Projeto:
        return self.ambiente.projeto

    @property
    def sessao(self) -> Sessao:
        return self.projeto.sessao

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal(id="corpo"):
            with Vertical(id="sidebar"):
                yield Static(id="nome-ambiente")
                with Vertical(id="area-projetos"):
                    yield Label("PROJETOS", classes="titulo")
                    yield ListView(id="lista-projetos")
                with Vertical(id="area-sessoes"):
                    yield Label("SESSOES / CHATS", classes="titulo")
                    yield Tree("sessoes", id="arvore-sessoes")
            with Vertical(id="painel"):
                yield RichLog(id="chat", wrap=True, markup=True)
                yield Static(id="status")
                yield Input(placeholder="Digite sua mensagem...", id="entrada")
        yield Footer()

    async def on_mount(self) -> None:
        self.query_one("#nome-ambiente", Static).update(
            escape(f" AMBIENTE: {self.ambiente.nome} ")
        )
        arvore = self.query_one("#arvore-sessoes", Tree)
        arvore.show_root = False
        arvore.guide_depth = 3

        self._abrir_sessao_ativa()
        await self._recarregar_sidebar()
        self._repintar_chat()
        self._atualizar_status()
        self.query_one("#entrada", Input).focus()

    # ------------------------------------------------------------------
    # entrada do usuario
    # ------------------------------------------------------------------

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        # guarda o "antes" para descobrir o que o nucleo mudou.
        # a UI nao guarda estado de negocio: ela pergunta duas vezes e compara.
        posicao_antes = self._posicao()
        tamanhos_antes = self._tamanhos()

        novas = self.ambiente.enviar(event.value)
        event.input.value = ""

        mudou_de_lugar = self._posicao() != posicao_antes
        if mudou_de_lugar:
            self._abrir_sessao_ativa()

        log = self.query_one("#chat", RichLog)
        if mudou_de_lugar:
            # mudou de projeto/sessao/chat -> ESTADO: redesenha o historico inteiro
            self._repintar_chat()
            self._escrever_efemeras(novas, log)
        else:
            # mesmo lugar -> DELTA: so o que acabou de nascer
            for m in novas:
                log.write(formatar(m))

        if mudou_de_lugar or self._tamanhos() != tamanhos_antes:
            await self._recarregar_sidebar()

        self._atualizar_status()

        # o nucleo diz "encerrou"; quem decide o que isso significa e a UI
        if not self.ambiente.ativo:
            self.app.exit()

    # ------------------------------------------------------------------
    # cliques na sidebar
    # ------------------------------------------------------------------

    async def on_list_view_selected(self, event: ListView.Selected) -> None:
        if event.list_view.id != "lista-projetos":
            return
        indice = event.list_view.index
        if indice is None or indice == self.ambiente.indice_ativo:
            return
        # mesma regra que o comando /trocar-projeto usa
        if self.ambiente.trocar_projeto(indice):
            self._abrir_sessao_ativa()
            await self._recarregar_sidebar()   # trocar de projeto troca as sessoes junto
            self._repintar_chat()
            self._atualizar_status()
        self.query_one("#entrada", Input).focus()

    async def on_tree_node_selected(self, event: Tree.NodeSelected) -> None:
        """Clicou no NOME de uma sessao ou de um chat -> troca de lugar.
        Abrir/fechar o card e' outro evento (NodeExpanded/NodeCollapsed)."""
        dados = event.node.data
        if not dados:
            return

        match dados:
            case (NO_SESSAO, i_sessao):
                if i_sessao == self.projeto.indice_ativo:
                    return
                # mesma regra que o comando /trocar-sessao usa
                if not self.projeto.trocar_sessao(i_sessao):
                    return

            case (NO_CHAT, i_sessao, i_chat):
                # chat de outra sessao: troca as duas coisas, nesta ordem
                if i_sessao != self.projeto.indice_ativo:
                    if not self.projeto.trocar_sessao(i_sessao):
                        return
                if not self.sessao.trocar_chat(i_chat):
                    return

            case _:
                return

        self._abrir_sessao_ativa()
        await self._recarregar_sidebar()
        self._repintar_chat()
        self._atualizar_status()
        self.query_one("#entrada", Input).focus()

    def on_tree_node_expanded(self, event: Tree.NodeExpanded) -> None:
        self._marcar_card(event.node.data, aberto=True)

    def on_tree_node_collapsed(self, event: Tree.NodeCollapsed) -> None:
        self._marcar_card(event.node.data, aberto=False)

    def _marcar_card(self, dados, aberto: bool) -> None:
        """Abrir e fechar card e' PINTURA: nao chama nada do nucleo."""
        if self._recarregando or not dados or dados[0] != NO_SESSAO:
            return
        chave = self._chave_card(dados[1])
        if aberto:
            self._expandidas.add(chave)
        else:
            self._expandidas.discard(chave)

    def _chave_card(self, i_sessao: int) -> tuple[str, str]:
        return (self.projeto.nome, self.projeto.sessoes[i_sessao].nome)

    def _abrir_sessao_ativa(self) -> None:
        """Ao chegar num lugar novo, o card de la nasce aberto."""
        self._expandidas.add(self._chave_card(self.projeto.indice_ativo))

    # ------------------------------------------------------------------
    # leitura do nucleo (so para comparar antes/depois)
    # ------------------------------------------------------------------

    def _posicao(self) -> tuple[int, int, int]:
        """Onde o usuario esta na arvore."""
        return (self.ambiente.indice_ativo, self.projeto.indice_ativo, self.sessao.indice_ativo)

    def _tamanhos(self) -> tuple:
        """Quantos itens tem cada lista - detecta criacao em qualquer sessao."""
        return (
            len(self.ambiente.projetos),
            len(self.projeto.sessoes),
            tuple(len(s.chats) for s in self.projeto.sessoes),
        )

    # ------------------------------------------------------------------
    # pintura
    # ------------------------------------------------------------------

    async def _recarregar_sidebar(self) -> None:
        await self._recarregar_projetos()
        self._recarregar_sessoes()

    async def _recarregar_projetos(self) -> None:
        lista = self.query_one("#lista-projetos", ListView)
        await lista.clear()
        for i, nome in enumerate(self.ambiente.listar_projetos()):
            lista.append(ListItem(Label(escape(f"[{i}] {nome}"))))
        lista.index = self.ambiente.indice_ativo

    def _recarregar_sessoes(self) -> None:
        arvore = self.query_one("#arvore-sessoes", Tree)
        # expand()/collapse() abaixo disparam NodeExpanded/NodeCollapsed.
        # A flag impede que o redesenho reescreva o que o usuario escolheu.
        self._recarregando = True
        try:
            arvore.clear()
            for i, sessao in enumerate(self.projeto.sessoes):
                ativa = i == self.projeto.indice_ativo
                no = arvore.root.add(
                    escape(f"{'*' if ativa else ' '} [{i}] {sessao.nome}"),
                    data=(NO_SESSAO, i),
                )
                for j, chat in enumerate(sessao.chats):
                    no.add_leaf(
                        escape(f"{'*' if ativa and j == sessao.indice_ativo else ' '} [{j}] {chat.nome}"),
                        data=(NO_CHAT, i, j),
                    )
                if (self.projeto.nome, sessao.nome) in self._expandidas:
                    no.expand()
        finally:
            self._recarregando = False

    def _repintar_chat(self) -> None:
        log = self.query_one("#chat", RichLog)
        log.clear()
        for m in self.sessao.chat.mensagens:
            log.write(formatar(m))

    def _escrever_efemeras(self, novas: list[Mensagem], log: RichLog) -> None:
        """Ambiente e Projeto respondem sem gravar em chat.mensagens - so a
        Sessao grava. Depois de um repaint essas respostas sumiriam da tela,
        entao a UI escreve por cima as que o nucleo nao guardou."""
        gravadas = {id(m) for m in self.sessao.chat.mensagens}
        for m in novas:
            if id(m) not in gravadas:
                log.write(formatar(m))

    def _atualizar_status(self) -> None:
        self.query_one("#status", Static).update(
            formatar_status(self.ambiente.obter_status())
        )


class FishingRodTUI(App):
    TITLE = "FISHING ROD"
    SUB_TITLE = "seu ambiente de trabalho com IA"
    BINDINGS = [("ctrl+q", "quit", "Sair")]

    CSS = """
    #corpo   { height: 1fr; }
    #sidebar { width: 32; border: round $primary; }
    #painel  { width: 1fr; }

    #nome-ambiente {
        height: 1;
        background: $primary;
        color: $text;
        text-style: bold;
    }
    /* a sidebar dividida ao meio: cada area pega 1fr do que sobrou */
    #area-projetos { height: 1fr; }
    #area-sessoes  { height: 1fr; border-top: solid $primary; }
    .titulo {
        height: 1;
        width: 1fr;
        background: $panel;
        color: $text-muted;
    }
    #arvore-sessoes { height: 1fr; }

    #chat {
        height: 1fr;
        border: round $primary;
        padding: 0 1;
    }
    #status {
        height: 1;
        background: $panel;
        color: $text-muted;
    }
    """

    def on_mount(self) -> None:
        ambiente = Ambiente(nome="meu-ambiente")
        self.push_screen(TelaAmbiente(ambiente))


if __name__ == "__main__":
    FishingRodTUI().run()
