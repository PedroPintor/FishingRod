"""O composition root: liga os servicos ao banco, a wiki, aos agentes e ao Claude.

E o unico lugar que conhece os adaptadores de verdade. As telas recebem o
`Programa` pronto e so falam com os servicos, o catalogo e a porta da wiki.
"""

from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol

from fishingrod.adaptadores.persistencia import RepositorioSQLite, abrir_repositorio
from fishingrod.adaptadores.persistencia.localizacao import NOME_DO_BANCO, pasta_de_dados
from fishingrod.adaptadores.sessao import AdaptadorSessaoClaude
from fishingrod.adaptadores.wiki import WikiDeArquivos
from fishingrod.aplicacao.catalogo.catalogo import CatalogoDeAcoes
from fishingrod.aplicacao.catalogo.registro import ACOES
from fishingrod.aplicacao.catalogo.tipos import PedidoDeConfirmacao
from fishingrod.aplicacao.ferramentas import RegistroDeFerramentas
from fishingrod.aplicacao.ferramentas.acoes import entradas_de_acoes
from fishingrod.aplicacao.portas.sessao import PortaSessao
from fishingrod.aplicacao.portas.wiki import PortaWiki
from fishingrod.aplicacao.servicos.servico_de_ambiente import ServicoDeAmbiente
from fishingrod.aplicacao.servicos.servico_de_conversa import ServicoDeConversa
from fishingrod.dominio import Agente, Chamador, Identidade, Papel

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

# A pasta de trabalho do Claude, dentro da pasta de dados. E sempre a mesma:
# o Claude guarda as conversas por ela, e e por ela que as procura de novo
# (D22). Os agentes nao tem as ferramentas da maquina (D16): nada aqui e lido
# nem escrito por eles.
PASTA_DO_CLAUDE = "claude"


class ConfirmacaoRecusada:
    """A porta de confirmacao enquanto confirmar na tela nao existe: o que o
    usuario aciona nunca pergunta (RN-AC-29), e o que um agente pede e
    recusado - na duvida, nada executa. `ao_recusar` leva o aviso ao chat."""

    def __init__(self) -> None:
        self.ao_recusar: Callable[[Identidade, str], Awaitable[None]] | None = None

    async def confirmar(self, pedido: PedidoDeConfirmacao) -> bool:
        if self.ao_recusar is not None and pedido is not None and pedido.alvo.id_sessao is not None:
            await self.ao_recusar(pedido.alvo.id_sessao, pedido.acao)
        return False


class Sessoes(PortaSessao, Protocol):
    """A porta de sessao, mais o `encerrar` do fim do programa (G7)."""

    async def encerrar(self) -> None: ...


type FabricaDeSessoes = Callable[[RegistroDeFerramentas, Path], Sessoes]


@dataclass
class Programa:
    servico: ServicoDeAmbiente
    catalogo: CatalogoDeAcoes
    wiki: PortaWiki
    agentes: tuple[Agente, ...]
    repositorio: RepositorioSQLite
    conversa: ServicoDeConversa
    sessoes: Sessoes
    fechado: bool = field(default=False, init=False)

    async def fechar(self) -> None:
        """Desliga todos os chats e so depois fecha o banco: as respostas
        interrompidas ainda sao gravadas. Nenhum processo do Claude fica."""
        if self.fechado:
            return
        self.fechado = True
        await self.conversa.desligar_todos()
        await self.sessoes.encerrar()
        await self.repositorio.fechar()


async def montar(pasta: Path | None = None, fabricar_sessoes: FabricaDeSessoes | None = None) -> Programa:
    """`pasta` e a pasta de dados; sem ela, a do sistema (`pasta_de_dados`).
    Os testes passam uma pasta temporaria e, para nao gastar a assinatura, um
    Claude roteirizado em `fabricar_sessoes`; sem ele, o Claude de verdade."""
    pasta = pasta_de_dados() if pasta is None else Path(pasta)
    fabricar_sessoes = fabricar_sessoes or AdaptadorSessaoClaude
    repositorio = await abrir_repositorio(pasta / NOME_DO_BANCO)
    wiki = WikiDeArquivos(pasta)
    servico = ServicoDeAmbiente(repositorio, wiki, ORQUESTRADOR, (BIBLIOTECARIO,))
    confirmacao = ConfirmacaoRecusada()
    catalogo = CatalogoDeAcoes(servico, confirmacao)
    pasta_do_claude = pasta / PASTA_DO_CLAUDE
    pasta_do_claude.mkdir(parents=True, exist_ok=True)
    sessoes = fabricar_sessoes(RegistroDeFerramentas(entradas_de_acoes(catalogo)), pasta_do_claude)
    conversa = ServicoDeConversa(sessoes, repositorio)
    confirmacao.ao_recusar = conversa.acao_recusada
    return Programa(servico, catalogo, wiki, (ORQUESTRADOR, BIBLIOTECARIO), repositorio, conversa, sessoes)
