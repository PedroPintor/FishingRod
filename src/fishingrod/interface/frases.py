"""O que a tela escreve para a pessoa: o Resultado do catalogo e as datas.

O catalogo devolve so categorias (RN-AC-35); a frase em portugues e da tela.
"""

from datetime import date, datetime

from fishingrod.aplicacao.catalogo.tipos import MotivoFalha, Resultado
from fishingrod.dominio import Memoria

MEMORIA_VAZIA = (
    "Esta sessão ainda não tem anotações. Quando os agentes conversarem, o que eles "
    "anotarem para os outros aparece aqui."
)

_ALVOS = {
    "ambiente": "o ambiente",
    "frente": "a frente",
    "tarefa": "a tarefa",
    "sessao": "a sessão",
    "etapa": "a etapa",
}


def frase_da_falha(resultado: Resultado) -> str:
    """Uma frase curta sobre por que a acao nao aconteceu."""
    detalhe = resultado.detalhe
    match resultado.motivo:
        case MotivoFalha.ARGUMENTO_INVALIDO if detalhe.get("problema") == "longo_demais":
            return f"O nome passa de {detalhe.get('maximo')} caracteres."
        case MotivoFalha.ARGUMENTO_INVALIDO if detalhe.get("problema") == "ausente":
            return "Precisa de um nome."
        case MotivoFalha.ARGUMENTO_INVALIDO:
            return "O que foi digitado não vale para esta ação."
        case MotivoFalha.ALVO_AUSENTE | MotivoFalha.ALVO_INEXISTENTE:
            alvo = _ALVOS.get(detalhe.get("alvo") or detalhe.get("falta", ""), "o item")
            return f"Não achei {alvo}. Talvez tenha sido apagado."
        case MotivoFalha.REGRA_VIOLADA:
            return "Isso não é permitido aqui."
        case MotivoFalha.CONFLITO:
            return "Outra janela mexeu neste ambiente ao mesmo tempo. Tente de novo."
        case MotivoFalha.FALHA_DE_ARMAZENAMENTO:
            return "Não consegui gravar no disco."
        case MotivoFalha.RECUSADA:
            return "A ação foi recusada."
    return "Algo deu errado, e nada foi feito."


def texto_da_memoria(memoria: Memoria) -> str:
    """A memoria da sessao em markdown: um titulo por assunto (a chave), e as
    anotacoes dele na ordem em que foram escritas, com quem escreveu (D17)."""
    if not memoria.anotacoes:
        return MEMORIA_VAZIA
    partes = []
    for chave, anotacoes in memoria.anotacoes.items():
        partes.append(f"### {chave}")
        for anotacao in anotacoes:
            hora = anotacao.criada_em.astimezone().strftime("%d/%m %H:%M")
            partes.append(f"- {anotacao.valor}  \n  *{anotacao.autor}, {hora}*")
    return "\n\n".join(partes)


def quando(atualizado_em: datetime, hoje: date | None = None) -> str:
    """'mexido hoje', 'mexido ontem' ou 'mexido há N dias', no dia local."""
    hoje = date.today() if hoje is None else hoje
    dias = (hoje - atualizado_em.astimezone().date()).days
    if dias <= 0:
        return "mexido hoje"
    if dias == 1:
        return "mexido ontem"
    return f"mexido há {dias} dias"
