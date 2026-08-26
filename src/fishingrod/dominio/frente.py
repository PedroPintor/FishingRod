"""Frente - area de atuacao dentro de um ambiente (RN-04, RN-05)."""

from dataclasses import dataclass, field

from fishingrod.dominio.agente import Agente
from fishingrod.dominio.erros import AgenteInvalido, exigir_texto
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
        """Cria a tarefa ja com um chat do orquestrador (RN-05).

        O agente vem por parametro (Q4=A) porque o dominio nao pode conhecer a
        instancia concreta do orquestrador - ela e configuracao montada no
        composition root (U9). Isto corrige a assinatura de
        component-methods.md 1.3, que escrevia criar_tarefa(nome) e falava em
        "orquestrador padrao".
        """
        if not agente_orquestrador.e_orquestrador:
            raise AgenteInvalido(
                "a tarefa nasce com um chat de agente orquestrador; "
                f"[{agente_orquestrador.nome}] tem papel {agente_orquestrador.papel.value}"
            )
        tarefa = Tarefa(nome=nome)
        tarefa.criar_chat(agente_orquestrador)
        self.tarefas.append(tarefa)
        return tarefa

    def buscar_tarefa(self, id: Identidade) -> Tarefa | None:
        return next((t for t in self.tarefas if t.id == id), None)
