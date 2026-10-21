"""O modelo de estados de PBT-U6-09 (PBT-05, PBT-06).

Escrito a partir da tabela do FD §5 e do §6, com as emendas N2 e N3 - e nao a
partir do adaptador. Para cada sessao: o estado, se ha processo vivo e o
`conversa_nova` da proxima entrega - que so e True enquanto o CLI nunca
recebeu uma mensagem do chat: depois disso, a conversa esta guardada e toda
conexao a retoma (D22). Cada comando devolve o evento final que o
adaptador deve emitir (None quando quem le foi cancelado: nao ha evento final).
"""

from dataclasses import dataclass, field
from enum import Enum

from fishingrod.adaptadores.sessao.adaptador import Estado
from fishingrod.aplicacao.portas.sessao import MotivoFalhaDeSessao


class Desfecho(Enum):
    """Como o provedor responde a um envio."""

    BEM = "bem"  # texto e resultado
    VAZIO = "vazio"  # resultado sem texto
    LIMITE = "limite"  # limite atingido: nao derruba
    DERRUBA = "derruba"  # a conexao cai no meio da resposta
    SUBIDA_FALHA = "subida_falha"  # o processo nao sobe (so vale sem conexao)


@dataclass
class SessaoModelada:
    estado: Estado = Estado.SEM_CONEXAO
    processo: bool = False
    proxima_nova: bool = True


@dataclass
class ModeloDeSessoes:
    sessoes: list[SessaoModelada] = field(default_factory=list)
    encerrado: bool = False

    def abrir(self) -> int:
        self.sessoes.append(SessaoModelada())
        return len(self.sessoes) - 1

    def enviar(self, indice: int, desfecho: Desfecho) -> tuple[bool | None, MotivoFalhaDeSessao | None]:
        """(conversa_nova da entrega, ou None se nao houve entrega; motivo da
        falha, ou None se terminou bem)."""
        sessao = self.sessoes[indice]
        if sessao.estado is Estado.FECHADA:
            return None, MotivoFalhaDeSessao.SESSAO_FECHADA
        if desfecho is Desfecho.SUBIDA_FALHA and sessao.estado is Estado.SEM_CONEXAO:
            sessao.processo = False
            return None, MotivoFalhaDeSessao.INDISPONIVEL
        nova = sessao.proxima_nova
        sessao.processo = True
        sessao.proxima_nova = False
        match desfecho:
            case Desfecho.VAZIO:
                sessao.estado = Estado.OCIOSA
                return nova, MotivoFalhaDeSessao.RESPOSTA_VAZIA
            case Desfecho.LIMITE:
                sessao.estado = Estado.OCIOSA
                return nova, MotivoFalhaDeSessao.LIMITE_DE_USO
            case Desfecho.DERRUBA:
                self._derrubar(sessao)
                return nova, MotivoFalhaDeSessao.INDISPONIVEL
        sessao.estado = Estado.OCIOSA
        return nova, None

    def esc_antes_da_entrega(self, indice: int, chegou_ao_cli: bool) -> None:
        """RN-S-36, N3: o processo e descartado, e para quem le a mensagem
        nunca existiu. Se o processo ja estava de pe, o CLI a recebeu e a
        guardou na conversa (D22)."""
        sessao = self.sessoes[indice]
        if sessao.estado is not Estado.FECHADA:
            self._derrubar(sessao)
            if chegou_ao_cli:
                sessao.proxima_nova = False

    def esc_depois_da_entrega(self, indice: int, aviso_funciona: bool) -> bool:
        """RN-S-35: a mensagem foi entregue. Com o aviso ao provedor bem, a
        sessao fica OCIOSA com o historico; com o aviso falhando, o processo e
        descartado. Devolve o conversa_nova da entrega."""
        sessao = self.sessoes[indice]
        nova = sessao.proxima_nova
        sessao.processo = True
        sessao.proxima_nova = False
        if aviso_funciona:
            sessao.estado = Estado.OCIOSA
        else:
            self._derrubar(sessao)
        return nova

    def fechar(self, indice: int) -> None:
        sessao = self.sessoes[indice]
        sessao.estado = Estado.FECHADA
        sessao.processo = False

    def encerrar(self) -> None:
        self.encerrado = True
        for indice in range(len(self.sessoes)):
            self.fechar(indice)

    def processos(self) -> int:
        return sum(1 for sessao in self.sessoes if sessao.processo)

    @staticmethod
    def _derrubar(sessao: SessaoModelada) -> None:
        sessao.estado = Estado.SEM_CONEXAO
        sessao.processo = False
