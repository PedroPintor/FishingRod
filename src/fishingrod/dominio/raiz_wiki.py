"""RaizWiki - localizador logico da wiki de um ambiente (RN-11, RNF-11)."""

from dataclasses import dataclass

from fishingrod.dominio.erros import ErroDeDominio, exigir_texto

ESQUEMA_PADRAO = "dados"


class LocalizadorInvalido(ErroDeDominio):
    """Localizador sem esquema explicito, ou com caminho absoluto."""


@dataclass(frozen=True)
class RaizWiki:
    """Texto com esquema explicito, ex.: "dados:wikis/<id_ambiente>".

    E a unica coisa que o dominio sabe sobre a wiki (CQ1=A). O dominio NAO
    resolve o esquema em caminho real - isso e o adaptador de wiki (U3),
    montado no composition root.
    """

    localizador: str

    def __post_init__(self) -> None:
        exigir_texto(self.localizador, "localizador da wiki")
        if ":" not in self.localizador:
            raise LocalizadorInvalido(
                f"localizador [{self.localizador}] nao tem esquema explicito"
            )
        caminho = self.localizador.split(":", 1)[1]
        # RNF-11: caminho absoluto aqui vazaria decisao de filesystem para
        # dentro do dominio, e tornaria a wiki nao-portavel entre maquinas.
        if caminho.startswith(("/", "\\")) or caminho[1:3] in (":/", ":\\"):
            raise LocalizadorInvalido(
                f"localizador [{self.localizador}] nao pode ser caminho absoluto"
            )

    def esquema(self) -> str:
        return self.localizador.split(":", 1)[0]

    @staticmethod
    def para_ambiente(id_ambiente: str) -> "RaizWiki":
        return RaizWiki(localizador=f"{ESQUEMA_PADRAO}:wikis/{id_ambiente}")
