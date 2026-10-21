"""O que a tela escreve para a pessoa: o Resultado do catalogo e as datas.

O catalogo devolve so categorias (RN-AC-35); a frase em portugues e da tela.
"""

from datetime import date, datetime, tzinfo

from fishingrod.aplicacao.catalogo.tipos import MotivoFalha, Resultado
from fishingrod.aplicacao.portas.sessao import MotivoFalhaDeSessao
from fishingrod.aplicacao.servicos.servico_de_conversa import (
    ACAO_RECUSADA,
    CONVERSA_RECOMECOU,
    EstadoDoChat,
    ler_aviso,
)
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


_ESTADOS_DO_CHAT = {
    EstadoDoChat.PRONTO: "○ pronto para conversar",
    EstadoDoChat.LIGADO: "● ligado",
    EstadoDoChat.RESPONDENDO: "● ligado · respondendo…",
}


def frase_do_estado(estado: EstadoDoChat, na_fila: int) -> str:
    """O texto da faixa do chat (card 002)."""
    frase = _ESTADOS_DO_CHAT[estado]
    if na_fila:
        frase += f" · {na_fila} na fila"
    return frase


def frase_das_conexoes(abertas: int) -> str:
    """O mostrador da tela do ambiente: os processos do Claude vivos agora."""
    return f"Claude: {abertas} {'conexão aberta' if abertas == 1 else 'conexões abertas'}"


_AVISOS = {
    CONVERSA_RECOMECOU: "Não consegui retomar a conversa; ela recomeça do zero.",
    MotivoFalhaDeSessao.PROVEDOR_AUSENTE.value: "Não achei o Claude que vem junto com o FishingRod.",
    MotivoFalhaDeSessao.NAO_AUTENTICADO.value: (
        "O Claude está sem login. Entre na sua conta pelo Claude Code e mande a mensagem de novo."
    ),
    MotivoFalhaDeSessao.INDISPONIVEL.value: (
        "O Claude está fora do ar ou não respondeu. Mande a mensagem de novo daqui a pouco."
    ),
    MotivoFalhaDeSessao.RESPOSTA_VAZIA.value: "O agente terminou sem responder nada.",
    MotivoFalhaDeSessao.MENSAGEM_INVALIDA.value: "A mensagem está vazia ou passa do tamanho máximo.",
    MotivoFalhaDeSessao.SESSAO_FECHADA.value: "O chat foi desligado antes da resposta.",
}


def frase_do_aviso(texto: str, fuso: tzinfo | None = None) -> str:
    """O aviso gravado no chat (um codigo) em portugues. O que nao se
    reconhece vira a frase de falha generica - nunca some."""
    codigo, detalhe = ler_aviso(texto)
    if codigo == ACAO_RECUSADA:
        return (
            f"O agente pediu a ação {detalhe}, e ela foi recusada: "
            "confirmar as ações dos agentes na tela ainda não existe."
        )
    if codigo == MotivoFalhaDeSessao.LIMITE_DE_USO.value:
        frase = "Você atingiu o limite da sua assinatura do Claude."
        try:
            libera = datetime.fromisoformat(detalhe).astimezone(fuso)
        except ValueError:
            return frase
        return f"{frase} Ele libera em {libera.strftime('%d/%m às %H:%M')}."
    return _AVISOS.get(codigo, "Algo deu errado nesta resposta. Os outros chats e o resto do programa continuam.")


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
