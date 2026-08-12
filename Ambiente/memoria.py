from dataclasses import dataclass, field

CHAVE_PLANO = "plano"

@dataclass
class Anotacao:
    autor: str
    valor: str


@dataclass
class Memoria:
    anotacoes: dict[str, list[Anotacao]] = field(default_factory=dict)
    versao: int = 0

    def anotar(self, chave: str, valor: str, autor: str) -> bool:
        self.anotacoes[chave].append(Anotacao(autor=autor, valor=valor))
        self.versao += 1
        return True

    def anotar_plano(self, valor: str, autor: str) -> bool:
        if CHAVE_PLANO in self.anotacoes:
            return False
        return self.anotar(chave=CHAVE_PLANO, valor=valor, autor=autor)
        
    def formatar(self) -> dict | None:
        if CHAVE_PLANO in self.anotacoes:
            return self.anotacoes[CHAVE_PLANO]
        return None


    