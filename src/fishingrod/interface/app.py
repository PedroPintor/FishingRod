"""O programa: abre o banco e a wiki, mostra a tela de inicio e fecha tudo na
saida. `uv run fishingrod` chama `main`."""

from pathlib import Path

from textual.app import App

from fishingrod.aplicacao.portas.persistencia import ErroDePersistencia
from fishingrod.interface.montagem import Programa, montar
from fishingrod.interface.tela_de_inicio import TelaDeInicio


class FishingRodApp(App):
    TITLE = "FishingRod"

    def __init__(self, pasta_de_dados: Path | None = None) -> None:
        """`pasta_de_dados` e para os testes; sem ela, a pasta do sistema."""
        super().__init__()
        self._pasta_de_dados = pasta_de_dados
        self.programa: Programa | None = None

    async def on_mount(self) -> None:
        try:
            self.programa = await montar(self._pasta_de_dados)
        except ErroDePersistencia as erro:
            # Banco ilegivel ou de uma versao mais nova: nao da para seguir.
            self.exit(return_code=1, message=f"Não consegui abrir o banco do FishingRod: {erro}")
            return
        await self.push_screen(TelaDeInicio(self.programa))

    async def on_unmount(self) -> None:
        if self.programa is not None:
            await self.programa.fechar()


def main() -> None:
    FishingRodApp().run()
