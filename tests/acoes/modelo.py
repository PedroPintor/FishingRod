"""O oraculo de U5: a forma sem identidades, a previsao do motivo e a ponte
para o modelo de U4.

`prever` e RN-AC-38 escrita do jeito mais ingenuo possivel, sobre o
`AmbienteModelo` de U4: a acao existe, o alvo tem o que o escopo exige, os
argumentos (a violacao vem marcada pelo gerador), as referencias existem, e o
que so U4 descobre (a lista fechada de agentes). No sucesso, o efeito e
aplicado pelo `ModeloDeAmbientes.aplicar` de U4, sem reescrever nada dele.
"""

from collections.abc import Callable

from fishingrod.aplicacao.catalogo.tipos import Escopo, EtapaNaPosicao, MotivoFalha
from fishingrod.dominio import Ambiente, ExecutorEtapa
from tests.acoes.estrategias import BIBLIOTECARIO, REGISTRO, Passo
from tests.ambiente.modelo import Chamada, ModeloDeAmbientes

# --------------------------------------------------------------------------
# A forma sem identidades
# --------------------------------------------------------------------------


def forma(ambiente: Ambiente, autor: Callable[[str], str] = lambda autor: autor) -> tuple:
    """A projecao de U4 sem nenhuma identidade, para comparar dois ambientes
    que criaram objetos com ids diferentes. `autor` traduz o autor das
    anotacoes - e o que deixa PBT-U5-07 comparar o agente com o usuario."""
    return (
        ambiente.nome,
        tuple(
            (
                frente.nome,
                tuple(
                    (
                        tarefa.nome,
                        tuple(
                            (
                                sessao.nome,
                                tuple((chat.agente.nome, chat.nome) for chat in sessao.chats),
                                tuple(
                                    (chave, tuple((autor(a.autor), a.valor) for a in lista))
                                    for chave, lista in sessao.memoria.anotacoes.items()
                                ),
                            )
                            for sessao in tarefa.sessoes
                        ),
                        tuple((e.descricao, e.executor, e.concluida) for e in tarefa.etapas),
                    )
                    for tarefa in frente.tarefas
                ),
            )
            for frente in ambiente.frentes
        ),
    )


# --------------------------------------------------------------------------
# A previsao (RN-AC-38)
# --------------------------------------------------------------------------

Previsao = tuple[MotivoFalha | None, dict[str, str]]


def prever(passo: Passo, modelo: ModeloDeAmbientes) -> Previsao:
    """O motivo e o detalhe esperados, na ordem de RN-AC-38. O passo 2 (quem
    aciona) nao aparece: o usuario pode as 7."""
    acao = REGISTRO.get(passo.acao) if passo.acao else None
    if acao is None:
        return MotivoFalha.ACAO_DESCONHECIDA, {"acao": passo.como_chegou}

    alvo = passo.alvo
    if acao.escopo is Escopo.FRENTE and alvo.id_frente is None:
        return MotivoFalha.ALVO_AUSENTE, {"falta": "frente"}
    if acao.escopo is Escopo.TAREFA and alvo.id_tarefa is None:
        return MotivoFalha.ALVO_AUSENTE, {"falta": "tarefa"}
    if acao.escopo is Escopo.SESSAO and alvo.id_sessao is None:
        return MotivoFalha.ALVO_AUSENTE, {"falta": "sessao"}

    if passo.violacao is not None:
        return MotivoFalha.ARGUMENTO_INVALIDO, dict(passo.violacao)

    vista = modelo.ambientes.get(alvo.id_ambiente)
    if vista is None:
        return MotivoFalha.ALVO_INEXISTENTE, {"alvo": "ambiente"}
    if acao.escopo is Escopo.FRENTE and ModeloDeAmbientes._frente(vista, alvo.id_frente) is None:
        return MotivoFalha.ALVO_INEXISTENTE, {"alvo": "frente"}
    if acao.escopo is Escopo.SESSAO and ModeloDeAmbientes._sessao(vista, alvo.id_sessao) is None:
        return MotivoFalha.ALVO_INEXISTENTE, {"alvo": "sessao"}
    if acao.escopo is Escopo.TAREFA:
        tarefa = ModeloDeAmbientes._tarefa(vista, alvo.id_tarefa)
        if tarefa is None:
            return MotivoFalha.ALVO_INEXISTENTE, {"alvo": "tarefa"}
        posicao = passo.esperados.get("posicao")
        if posicao is not None and posicao > len(tarefa.etapas):
            return MotivoFalha.ALVO_INEXISTENTE, {
                "alvo": "etapa",
                "posicao": str(posicao),
                "total": str(len(tarefa.etapas)),
            }

    # O que so U4 descobre, no passo 7.
    if acao.nome == "criar_chat" and passo.esperados["agente"] != BIBLIOTECARIO.nome:
        return MotivoFalha.ARGUMENTO_INVALIDO, {"parametro": "agente", "problema": "fora_da_lista"}
    return None, {}


# --------------------------------------------------------------------------
# A ponte para U4
# --------------------------------------------------------------------------


def chamada_de_u4(passo: Passo, modelo: ModeloDeAmbientes, autor: str) -> Chamada:
    """A operacao de U4 que o catalogo deve ter chamado, na forma do modelo de
    U4. A posicao vira o id da etapa, como no catalogo."""
    alvo, valores = passo.alvo, passo.esperados
    match passo.acao:
        case "criar_frente":
            return Chamada("criar_frente", alvo.id_ambiente, None, (valores["nome"],))
        case "criar_tarefa":
            return Chamada("criar_tarefa", alvo.id_ambiente, alvo.id_frente, (valores["nome"],))
        case "criar_sessao":
            return Chamada("criar_sessao", alvo.id_ambiente, alvo.id_tarefa, (valores.get("nome", ""),))
        case "criar_chat":
            return Chamada(
                "criar_chat",
                alvo.id_ambiente,
                alvo.id_sessao,
                (valores["agente"], valores.get("nome", "")),
            )
        case "criar_etapa":
            return Chamada(
                "criar_etapa",
                alvo.id_ambiente,
                alvo.id_tarefa,
                (valores["descricao"], ExecutorEtapa(valores["executor"])),
            )
        case "concluir_etapa":
            vista = modelo.ambientes[alvo.id_ambiente]
            tarefa = ModeloDeAmbientes._tarefa(vista, alvo.id_tarefa)
            etapa = tarefa.etapas[valores["posicao"] - 1]
            return Chamada("concluir_etapa", alvo.id_ambiente, etapa.id, ())
        case "anotar_memoria":
            return Chamada(
                "anotar_memoria",
                alvo.id_ambiente,
                alvo.id_sessao,
                (valores["chave"], valores["valor"], autor),
            )
    raise AssertionError(f"acao sem ponte: {passo.acao}")


def devolvido_para_u4(dado: object) -> object:
    """O modelo de U4 le o id do objeto que o servico devolveu; o catalogo
    devolve a etapa com a posicao (G5)."""
    return dado.etapa if isinstance(dado, EtapaNaPosicao) else dado
