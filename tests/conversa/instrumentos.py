"""O que os testes do card 002 usam: o programa montado numa pasta temporaria,
com o adaptador de verdade sobre um Claude roteirizado (sem CLI, sem gastar a
assinatura), e um ambiente com uma tarefa pronta para conversar."""

import asyncio
from dataclasses import dataclass
from pathlib import Path

from fishingrod.adaptadores.sessao import AdaptadorSessaoClaude
from fishingrod.aplicacao.catalogo.tipos import Acionamento, Alvo
from fishingrod.aplicacao.esquema_wiki import EsquemaWiki
from fishingrod.aplicacao.portas.sessao import ContextoDaSessao
from fishingrod.aplicacao.servicos.servico_de_conversa import EstadoDoChat, ServicoDeConversa
from fishingrod.dominio import Agente, Ambiente
from fishingrod.interface.montagem import FabricaDeSessoes, Programa, montar
from tests.sessao.cliente_roteirizado import FabricaRoteirizada


def com_roteiro(fabrica: FabricaRoteirizada) -> FabricaDeSessoes:
    """O `fabricar_sessoes` da montagem: o adaptador real, com o cliente
    roteirizado no lugar do CLI."""

    def fabricar(registro, pasta: Path) -> AdaptadorSessaoClaude:
        return AdaptadorSessaoClaude(
            registro, pasta, fabrica, prazo_de_subida=5, prazo_de_interrupcao=1, procurar_conversa=fabrica.guardada
        )

    return fabricar


@dataclass
class Chat:
    contexto: ContextoDaSessao
    agente: Agente

    @property
    def id(self):
        return self.contexto.id_chat


async def preparar(programa: Programa, nome: str = "loja", agente: Agente | None = None) -> tuple[Ambiente, Chat, Chat]:
    """Um ambiente com uma frente, uma tarefa e, na sessao dela, o chat do
    orquestrador e um do bibliotecario. `agente` troca o agente que conversa
    nos dois chats (os testes com o Claude de verdade usam um mais barato)."""
    ambiente = await programa.servico.criar_ambiente(nome, EsquemaWiki.vazio())
    usuario = Acionamento.usuario()
    frente = (await programa.catalogo.executar("criar_frente", Alvo(ambiente.id), {"nome": "vendas"}, usuario)).dado
    tarefa = (
        await programa.catalogo.executar("criar_tarefa", Alvo(ambiente.id, frente.id), {"nome": "site"}, usuario)
    ).dado
    sessao = tarefa.sessoes[0]
    await programa.catalogo.executar("criar_chat", Alvo(ambiente.id, id_sessao=sessao.id), {"agente": "bibliotecario"}, usuario)
    chats = [
        Chat(ContextoDaSessao(ambiente.id, frente.id, tarefa.id, sessao.id, chat.id), agente or chat.agente)
        for chat in sessao.chats
    ]
    for chat in chats:
        await programa.conversa.abrir(chat.contexto, chat.agente)
    return ambiente, chats[0], chats[1]


async def ate_responder(conversa: ServicoDeConversa, *chats: Chat, prazo: float = 5) -> None:
    async with asyncio.timeout(prazo):
        while any(conversa.estado(chat.id) is EstadoDoChat.RESPONDENDO for chat in chats):
            await asyncio.sleep(0.01)


async def ate(condicao, prazo: float = 5) -> None:
    async with asyncio.timeout(prazo):
        while not condicao():
            await asyncio.sleep(0.01)


def textos(conversa: ServicoDeConversa, chat: Chat) -> list[tuple[str, str]]:
    return [(linha.papel, linha.texto) for linha in conversa.linhas(chat.id)]
