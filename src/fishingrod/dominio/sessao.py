"""Sessao - um momento de trabalho dentro de uma tarefa (D21).

Nao confundir com a SessaoViva de aplicacao/portas/sessao.py: aquela e a
conexao aberta com o Claude para UM chat; esta e o que o usuario chama de
sessao - um conjunto de chats que trabalham juntos, com uma memoria comum.
"""

from dataclasses import dataclass, field

from fishingrod.dominio.agente import Agente
from fishingrod.dominio.chat import Chat
from fishingrod.dominio.erros import OrquestradorDuplicado, exigir_texto
from fishingrod.dominio.identidade import Identidade
from fishingrod.dominio.memoria import Memoria


@dataclass
class Sessao:
    """Contem chats e a memoria compartilhada entre eles (D17, D21).

    RN-05 e RN-06 juntas, agora por sessao: a sessao nasce com exatamente um
    orquestrador (Tarefa.criar_sessao faz isso) e nunca chega a dois.
    """

    nome: str
    chats: list[Chat] = field(default_factory=list)
    memoria: Memoria = field(default_factory=Memoria)
    id: Identidade = field(default_factory=Identidade.nova)

    def __post_init__(self) -> None:
        exigir_texto(self.nome, "nome da sessao")
        if self.contar_orquestradores() > 1:
            raise OrquestradorDuplicado(
                "uma sessao tem no maximo um chat com agente orquestrador"
            )

    def contar_orquestradores(self) -> int:
        return sum(1 for c in self.chats if c.agente.e_orquestrador)

    def criar_chat(self, agente: Agente, nome: str = "") -> Chat:
        """Cria um chat. Sub-agente e sempre permitido - e assim que o chat do
        bibliotecario nasce (Q14=X). Segundo orquestrador, nunca (RN-06).
        """
        if agente.e_orquestrador and self.contar_orquestradores() >= 1:
            raise OrquestradorDuplicado(
                f"sessao [{self.nome}] ja tem um chat com agente orquestrador"
            )
        chat = Chat(agente=agente, nome=nome)
        self.chats.append(chat)
        return chat

    def buscar_chat(self, id: Identidade) -> Chat | None:
        # Busca por identidade, nunca por indice ou nome (RF-F16). Devolve None
        # quando nao acha: nao achar nao e violacao de regra (RN-14).
        return next((c for c in self.chats if c.id == id), None)
