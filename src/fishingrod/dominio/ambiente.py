"""Ambiente - agregado raiz (RN-03, RN-11)."""

from dataclasses import dataclass, field

from fishingrod.dominio.erros import exigir_texto
from fishingrod.dominio.frente import Frente
from fishingrod.dominio.identidade import Identidade
from fishingrod.dominio.raiz_wiki import RaizWiki


@dataclass
class Ambiente:
    """Espaco de trabalho: frentes e o localizador da propria wiki.

    Nasce SEM frente (Q1=A). A criacao automatica de "projeto-padrao" que o
    codigo atual faz existia porque projetos[indice_ativo] estourava
    IndexError - razao que morreu quando a identidade opaca substituiu o
    indice (ESC-14). Quem garante que o usuario tem onde trabalhar e a tela de
    inicio (U9).

    As frentes pertencem a este ambiente, nunca a wiki (CQ1=A). O ambiente
    conhece a wiki apenas pela RaizWiki.
    """

    nome: str
    frentes: list[Frente] = field(default_factory=list)
    id: Identidade = field(default_factory=Identidade.nova)
    raiz_wiki: RaizWiki | None = None

    def __post_init__(self) -> None:
        exigir_texto(self.nome, "nome do ambiente")
        if self.raiz_wiki is None:
            # Q9=A: montada aqui, a partir da propria identidade. Isso torna a
            # coerencia entre ambiente e raiz uma invariante, nao uma convencao
            # que algum servico precise lembrar de honrar.
            self.raiz_wiki = RaizWiki.para_ambiente(self.id.valor)

    def criar_frente(self, nome: str) -> Frente:
        # Nome duplicado e permitido (RN-04): a identidade distingue. A regra
        # antiga que recusava duplicata existia porque o nome era a chave de
        # busca.
        frente = Frente(nome=nome)
        self.frentes.append(frente)
        return frente

    def buscar_frente(self, id: Identidade) -> Frente | None:
        return next((f for f in self.frentes if f.id == id), None)
