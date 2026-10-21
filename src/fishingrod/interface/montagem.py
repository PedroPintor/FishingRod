"""O composition root: liga o servico ao banco, a wiki e aos agentes.

E o unico lugar que conhece os adaptadores de verdade. As telas recebem o
`Programa` pronto e so falam com o servico, o catalogo e a porta da wiki.
"""

from dataclasses import dataclass
from pathlib import Path

from fishingrod.adaptadores.persistencia import RepositorioSQLite, abrir_repositorio
from fishingrod.adaptadores.persistencia.localizacao import NOME_DO_BANCO, pasta_de_dados
from fishingrod.adaptadores.wiki import WikiDeArquivos
from fishingrod.aplicacao.catalogo.catalogo import CatalogoDeAcoes
from fishingrod.aplicacao.catalogo.registro import ACOES
from fishingrod.aplicacao.catalogo.tipos import PedidoDeConfirmacao
from fishingrod.aplicacao.portas.wiki import PortaWiki
from fishingrod.aplicacao.servicos.servico_de_ambiente import ServicoDeAmbiente
from fishingrod.dominio import Agente, Chamador, Papel

# Os agentes desta iteracao (D20). O modelo e o apelido que o CLI do Claude
# entende, e nao uma versao exata: a versao muda, o apelido nao. As
# ferramentas do orquestrador sao as acoes do catalogo que o agente pode
# acionar; as do bibliotecario chegam com o card dele.
ORQUESTRADOR = Agente(
    nome="orquestrador",
    papel=Papel.ORQUESTRADOR,
    modelo="opus",
    ferramentas=tuple(acao.nome for acao in ACOES if Chamador.AGENTE in acao.chamadores),
)
BIBLIOTECARIO = Agente(nome="bibliotecario", papel=Papel.SUB_AGENTE, modelo="sonnet")


class ConfirmacaoRecusada:
    """A porta de confirmacao enquanto nenhum agente conversa na tela: o que o
    usuario aciona nunca pergunta (RN-AC-29), e um pedido de agente que
    chegasse aqui e recusado - na duvida, nada executa."""

    async def confirmar(self, pedido: PedidoDeConfirmacao) -> bool:
        return False


@dataclass
class Programa:
    servico: ServicoDeAmbiente
    catalogo: CatalogoDeAcoes
    wiki: PortaWiki
    agentes: tuple[Agente, ...]
    repositorio: RepositorioSQLite

    async def fechar(self) -> None:
        await self.repositorio.fechar()


async def montar(pasta: Path | None = None) -> Programa:
    """`pasta` e a pasta de dados; sem ela, a do sistema (`pasta_de_dados`).
    Os testes passam uma pasta temporaria."""
    pasta = pasta_de_dados() if pasta is None else Path(pasta)
    repositorio = await abrir_repositorio(pasta / NOME_DO_BANCO)
    wiki = WikiDeArquivos(pasta)
    servico = ServicoDeAmbiente(repositorio, wiki, ORQUESTRADOR, (BIBLIOTECARIO,))
    catalogo = CatalogoDeAcoes(servico, ConfirmacaoRecusada())
    return Programa(servico, catalogo, wiki, (ORQUESTRADOR, BIBLIOTECARIO), repositorio)
