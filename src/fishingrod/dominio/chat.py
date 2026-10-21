"""Chat - uma aba de conversa dentro de uma sessao (components.md 2.5)."""

from dataclasses import dataclass, field

from fishingrod.dominio.agente import Agente
from fishingrod.dominio.erros import exigir_texto
from fishingrod.dominio.identidade import Identidade


@dataclass
class Chat:
    """Guarda so o que e pequeno e estavel: identidade, nome e o agente.

    Ausencias deliberadas:
    - NAO guarda mensagens (Pergunta 3B). A transcricao vem da porta de
      persistencia (U2) e e composta pelo servico de conversa (U7).
    - NAO guarda a sessao viva do SDK (Pergunta 6A). Sessao e objeto de
      aplicacao; o dominio nao conhece ciclo de vida de conexao.
    """

    agente: Agente
    nome: str = ""
    id: Identidade = field(default_factory=Identidade.nova)

    def __post_init__(self) -> None:
        if not self.nome:
            self.nome = self.agente.nome
        exigir_texto(self.nome, "nome do chat")

    def renomear(self, novo_nome: str) -> None:
        # O nome nao e identidade (RF-F16): renomear nao afeta referencia
        # alguma que ja aponte para este chat.
        self.nome = exigir_texto(novo_nome, "nome do chat")
