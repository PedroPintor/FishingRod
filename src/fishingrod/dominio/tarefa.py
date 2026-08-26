"""Tarefa - unidade de trabalho dentro de uma frente (RN-05, RN-06, RN-08)."""

from dataclasses import dataclass, field

from fishingrod.dominio.agente import Agente
from fishingrod.dominio.chat import Chat
from fishingrod.dominio.erros import OrquestradorDuplicado, exigir_texto
from fishingrod.dominio.etapa import Etapa, ExecutorEtapa
from fishingrod.dominio.identidade import Identidade
from fishingrod.dominio.memoria import Memoria


@dataclass
class Tarefa:
    """Contem chats, etapas e memoria propria.

    RN-05 e RN-06 juntas: a tarefa nasce com exatamente um orquestrador
    (Frente.criar_tarefa faz isso) e nunca chega a dois.
    """

    nome: str
    chats: list[Chat] = field(default_factory=list)
    etapas: list[Etapa] = field(default_factory=list)
    memoria: Memoria = field(default_factory=Memoria)
    id: Identidade = field(default_factory=Identidade.nova)

    def __post_init__(self) -> None:
        exigir_texto(self.nome, "nome da tarefa")
        if self.contar_orquestradores() > 1:
            raise OrquestradorDuplicado(
                "uma tarefa tem no maximo um chat com agente orquestrador"
            )

    def contar_orquestradores(self) -> int:
        return sum(1 for c in self.chats if c.agente.e_orquestrador)

    def criar_chat(self, agente: Agente, nome: str = "") -> Chat:
        """Cria um chat. Sub-agente e sempre permitido - e assim que o chat do
        bibliotecario nasce (Q14=X). Segundo orquestrador, nunca (RN-06).
        """
        if agente.e_orquestrador and self.contar_orquestradores() >= 1:
            raise OrquestradorDuplicado(
                f"tarefa [{self.nome}] ja tem um chat com agente orquestrador"
            )
        chat = Chat(agente=agente, nome=nome)
        self.chats.append(chat)
        return chat

    def buscar_chat(self, id: Identidade) -> Chat | None:
        # Busca por identidade, nunca por indice ou nome (RF-F16). Devolve None
        # quando nao acha: nao achar nao e violacao de regra (RN-14).
        return next((c for c in self.chats if c.id == id), None)

    def criar_etapa(self, descricao: str, executor: ExecutorEtapa) -> Etapa:
        # Anexa ao fim: a posicao na lista e a ordem (RN-08).
        etapa = Etapa(descricao=descricao, executor=executor)
        self.etapas.append(etapa)
        return etapa

    def buscar_etapa(self, id: Identidade) -> Etapa | None:
        return next((e for e in self.etapas if e.id == id), None)
