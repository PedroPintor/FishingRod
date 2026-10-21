"""Frente - area de atuacao dentro de um ambiente (RN-04, RN-05)."""

from dataclasses import dataclass, field

from fishingrod.dominio.agente import Agente
from fishingrod.dominio.erros import exigir_texto
from fishingrod.dominio.identidade import Identidade
from fishingrod.dominio.tarefa import Tarefa


@dataclass
class Frente:
    """Contem tarefas. Pertence ao ambiente - nunca a wiki (CQ1=A)."""

    nome: str
    tarefas: list[Tarefa] = field(default_factory=list)
    id: Identidade = field(default_factory=Identidade.nova)

    def __post_init__(self) -> None:
        exigir_texto(self.nome, "nome da frente")

    def criar_tarefa(self, nome: str, agente_orquestrador: Agente) -> Tarefa:
        """Cria a tarefa ja com a primeira sessao, e nela o chat do
        orquestrador (RN-05, D21).

        O agente vem por parametro (Q4=A) porque o dominio nao pode conhecer a
        instancia concreta do orquestrador - ela e configuracao montada no
        composition root. A tarefa so entra na frente depois que a sessao
        nasceu: um agente que nao e orquestrador e recusado sem deixar tarefa
        pela metade.
        """
        tarefa = Tarefa(nome=nome)
        tarefa.criar_sessao(agente_orquestrador)
        self.tarefas.append(tarefa)
        return tarefa

    def buscar_tarefa(self, id: Identidade) -> Tarefa | None:
        return next((t for t in self.tarefas if t.id == id), None)
