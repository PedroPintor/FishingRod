"""A ficha do agente: o que ele e, campo por campo (card 003).

Cada valor sai do que esta configurado de verdade - o Agente, o catalogo e as
opcoes que vao para o Claude -, para a ficha nunca desmentir o que o Claude
recebe. Nada aqui e escrito a mao alem das frases de quando o valor falta.

A tela nao conhece o SDK: quem le as opcoes e o composition root
(`montagem.py`), que entrega so o que a ficha mostra, em `OpcoesDoClaude`.

`FichaNaTela` desenha a ficha; e a mesma no painel de explicacao e na janela
do ambiente.
"""

from dataclasses import dataclass

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Label, Static

from fishingrod.aplicacao.catalogo.catalogo import CatalogoDeAcoes
from fishingrod.dominio import Agente, Chamador, Papel

ESFORCO_PADRAO = "padrão do Claude"
NENHUMA = "nenhuma"
SEM_INSTRUCOES = "Nenhuma instrução escrita."

PAPEIS = {
    Papel.ORQUESTRADOR: "abre cada sessão",
    Papel.SUB_AGENTE: "pode ser chamado num chat",
}


@dataclass(frozen=True)
class OpcoesDoClaude:
    """O que a ficha mostra das opcoes que vao para o Claude. `esforco` None e
    o padrao do Claude; `instrucoes` e o texto exato do `system_prompt`."""

    esforco: str | None
    ferramentas_da_maquina: tuple[str, ...]
    instrucoes: str


@dataclass(frozen=True)
class Ficha:
    nome: str
    do_software: bool
    papel: str
    modelo: str
    esforco: str
    ferramentas: tuple[str, ...]
    ferramentas_da_maquina: tuple[str, ...]
    instrucoes: str


def montar_ficha(agente: Agente, catalogo: CatalogoDeAcoes, opcoes: OpcoesDoClaude, do_software: bool) -> Ficha:
    """As ferramentas sao conferidas no catalogo: so aparece a acao que existe
    e que um agente pode acionar - a que nao passa ali o Claude nunca recebe."""
    ferramentas = tuple(nome for nome in agente.ferramentas if _agente_aciona(catalogo, nome))
    return Ficha(
        nome=agente.nome,
        do_software=do_software,
        papel=PAPEIS[agente.papel],
        modelo=agente.modelo,
        esforco=opcoes.esforco or ESFORCO_PADRAO,
        ferramentas=ferramentas,
        ferramentas_da_maquina=opcoes.ferramentas_da_maquina,
        instrucoes=opcoes.instrucoes if opcoes.instrucoes.strip() else SEM_INSTRUCOES,
    )


def _agente_aciona(catalogo: CatalogoDeAcoes, nome: str) -> bool:
    acao = catalogo.buscar(nome)
    return acao is not None and Chamador.AGENTE in acao.chamadores


def lista(nomes: tuple[str, ...]) -> str:
    """Os nomes separados por ·, ou "nenhuma"."""
    return " · ".join(nomes) if nomes else NENHUMA


class FichaNaTela(Vertical):
    """A ficha, so para ler: o nome no topo, com a marca "do software", a
    configuracao campo por campo e as instrucoes."""

    DEFAULT_CSS = """
    FichaNaTela { height: auto; }
    FichaNaTela .titulo { text-style: bold; color: $text-muted; margin-top: 1; }
    FichaNaTela #ficha-topo { height: 1; margin-top: 1; }
    FichaNaTela #ficha-nome { width: 1fr; text-style: bold; }
    FichaNaTela #ficha-marca { color: $text-muted; }
    FichaNaTela .campo { height: auto; }
    FichaNaTela .campo .rotulo { width: 24; color: $text-muted; }
    FichaNaTela .campo .valor { width: 1fr; }
    FichaNaTela #ficha-instrucoes { margin-left: 2; }
    """

    CAMPOS = (
        ("papel", "Papel"),
        ("modelo", "Modelo"),
        ("esforco", "Esforço de raciocínio"),
        ("ferramentas", "Ferramentas"),
        ("ferramentas-da-maquina", "Ferramentas da máquina"),
    )

    def compose(self) -> ComposeResult:
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

    def mostrar(self, ficha: Ficha) -> None:
        self.ficha = ficha
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
