"""Politica de aprovacao de acao acionada por agente (RN-12).

Rodada 4 de Units Generation: o parametro configuravel foi retirado desta
iteracao. O comportamento e constante - agente sempre pede confirmacao - e o
ponto de decisao fica em um lugar so.

Quando a configuracao voltar (campo em Ambiente, arquivo de config, o que for),
SO O CORPO de exige_aprovacao muda: nenhum chamador, nenhuma tela e nenhum
contrato de porta e tocado. U5 (ferramentas de ambiente) e U8 (propostas do
bibliotecario) consultam esta funcao.

Escopo sem historia de origem - declarado em unit-of-work-story-map.md 4.
"""

from enum import Enum

APROVACAO_DE_AGENTE_OBRIGATORIA = True


class Chamador(Enum):
    AGENTE = "agente"
    USUARIO = "usuario"


def exige_aprovacao(chamador: Chamador) -> bool:
    """True quando a acao precisa de confirmacao do usuario antes de executar.

    Acao disparada pelo usuario via /comando executa direto: a politica governa
    apenas o chamador agente.
    """
    return chamador is Chamador.AGENTE and APROVACAO_DE_AGENTE_OBRIGATORIA
