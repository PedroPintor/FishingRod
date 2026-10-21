"""Tarefa - unidade de trabalho dentro de uma frente (RN-05, RN-08, D21)."""

from dataclasses import dataclass, field

from fishingrod.dominio.agente import Agente
from fishingrod.dominio.erros import AgenteInvalido, exigir_texto
from fishingrod.dominio.etapa import Etapa, ExecutorEtapa
from fishingrod.dominio.identidade import Identidade
from fishingrod.dominio.sessao import Sessao


@dataclass
class Tarefa:
    """Contem sessoes e etapas.

    As etapas sao da tarefa, e nao da sessao (D21): o plano e um so, e cada
    sessao e um momento de trabalhar nele. A memoria, ao contrario, e de cada
    sessao.
    """

    nome: str
    sessoes: list[Sessao] = field(default_factory=list)
    etapas: list[Etapa] = field(default_factory=list)
    id: Identidade = field(default_factory=Identidade.nova)

    def __post_init__(self) -> None:
        exigir_texto(self.nome, "nome da tarefa")

    def criar_sessao(self, agente_orquestrador: Agente, nome: str = "") -> Sessao:
        """Cria a sessao ja com um chat do orquestrador (RN-05, D21).

        O agente vem por parametro (Q4=A) porque o dominio nao pode conhecer a
        instancia concreta do orquestrador - ela e configuracao montada no
        composition root.

        `nome` vazio vira "sessão N", com N a posicao da sessao na tarefa: a
        aba precisa de um nome, e o usuario nao precisa inventar um.
        """
        if not agente_orquestrador.e_orquestrador:
            raise AgenteInvalido(
                "a sessao nasce com um chat de agente orquestrador; "
                f"[{agente_orquestrador.nome}] tem papel {agente_orquestrador.papel.value}"
            )
        sessao = Sessao(nome=nome or f"sessão {len(self.sessoes) + 1}")
        sessao.criar_chat(agente_orquestrador)
        self.sessoes.append(sessao)
        return sessao

    def buscar_sessao(self, id: Identidade) -> Sessao | None:
        return next((s for s in self.sessoes if s.id == id), None)

    def criar_etapa(self, descricao: str, executor: ExecutorEtapa) -> Etapa:
        # Anexa ao fim: a posicao na lista e a ordem (RN-08).
        etapa = Etapa(descricao=descricao, executor=executor)
        self.etapas.append(etapa)
        return etapa

    def buscar_etapa(self, id: Identidade) -> Etapa | None:
        return next((e for e in self.etapas if e.id == id), None)
