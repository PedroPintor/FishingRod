"""O programa: abre o banco, a wiki e o Claude, mostra a tela de inicio e
fecha tudo na saida. `uv run fishingrod` chama `main`."""

from pathlib import Path

from textual.app import App

from fishingrod.aplicacao.portas.persistencia import ErroDePersistencia
from fishingrod.interface.montagem import FabricaDeSessoes, Programa, montar
from fishingrod.interface.tela_de_inicio import TelaDeInicio


class FishingRodApp(App):
    TITLE = "FishingRod"

    # O jeito dos botoes e campos, num lugar so (card 003): todos compactos,
    # de uma linha, sem borda e com fundo de cor - menos quadrados na tela.
    # Cada um e criado com `compact=True`; aqui fica a cor e o respiro.
    CSS = """
    Button.-textual-compact {
        min-width: 0;
        padding: 0 2;
        background: $panel;
        &:hover { background: $panel-lighten-2; }
        &:focus { text-style: bold; background-tint: $foreground 10%; }
        &.-active { background: $accent; tint: transparent; }
        &.-primary { background: $primary; color: $text; }
        &.-error { background: $error; color: $text; }
        &.-warning { background: $warning-muted; color: $text-warning; }
        &.-ligado { background: $accent; color: $text; }
    }
    Input.-textual-compact { padding: 0 1; background: $boost; }
    Select.-textual-compact > SelectCurrent { padding: 0 1; background: $panel; }
    """

    def __init__(
        self, pasta_de_dados: Path | None = None, fabricar_sessoes: FabricaDeSessoes | None = None
    ) -> None:
        """`pasta_de_dados` e `fabricar_sessoes` sao para os testes; sem eles,
        a pasta do sistema e o Claude de verdade."""
        super().__init__()
        self._pasta_de_dados = pasta_de_dados
        self._fabricar_sessoes = fabricar_sessoes
        self.programa: Programa | None = None

    async def on_mount(self) -> None:
        try:
            self.programa = await montar(self._pasta_de_dados, self._fabricar_sessoes)
        except ErroDePersistencia as erro:
            # Banco ilegivel ou de uma versao mais nova: nao da para seguir.
            self.exit(return_code=1, message=f"Não consegui abrir o banco do FishingRod: {erro}")
            return
        await self.push_screen(TelaDeInicio(self.programa))

    async def on_unmount(self) -> None:
        # Fechar o programa desliga todos os chats: nenhum processo do Claude
        # fica para tras (card 002).
        if self.programa is not None:
            await self.programa.fechar()


def main() -> None:
    FishingRodApp().run()
