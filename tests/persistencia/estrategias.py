"""Geradores de Hypothesis para U2, e o auxiliar que roda corrotina em teste.

Regra desta unidade, vinda de domain-entities.md 5.2: os geradores constroem
Ambiente SO pela API publica, e memoria SO por anotar(). Uma
Memoria(anotacoes={...}, versao=0) montada a mao nao faz round-trip - e isso e
correto, nao defeito. Gerar por dentro esconderia a diferenca.
"""

import asyncio
from datetime import UTC, datetime
from typing import Any

from hypothesis import strategies as st

from fishingrod.dominio import (
    Agente,
    Ambiente,
    Anotacao,
    ExecutorEtapa,
    Papel,
    Sessao,
    Tarefa,
)

# Sem surrogates (Cs) e sem caracteres de controle (Cc): o primeiro nao
# sobrevive a codificacao UTF-8, e o segundo inclui NUL, que o SQLite trata de
# forma propria. Nenhum dos dois e texto que um usuario digita.
_CARACTERES = st.characters(exclude_categories=("Cs", "Cc"))

texto_nao_vazio = st.text(_CARACTERES, min_size=1, max_size=20).filter(lambda s: s.strip())


def executar(coro: Any) -> Any:
    """Roda a corrotina num laco proprio.

    Nao usamos pytest-asyncio: Hypothesis gera centenas de exemplos por
    propriedade, e um laco compartilhado pela funcao de teste e onde essa
    combinacao costuma produzir falha intermitente. asyncio.run da um laco por
    exemplo, sem plugin nenhum.
    """
    return asyncio.run(coro)


@st.composite
def agentes(draw: Any, orquestrador: bool = True) -> Agente:
    return Agente(
        nome=draw(texto_nao_vazio),
        papel=Papel.ORQUESTRADOR if orquestrador else Papel.SUB_AGENTE,
        modelo=draw(texto_nao_vazio),
        ferramentas=tuple(draw(st.lists(texto_nao_vazio, max_size=3))),
        regras=tuple(draw(st.lists(texto_nao_vazio, max_size=2))),
    )


@st.composite
def ambientes(draw: Any) -> Ambiente:
    """Frentes, tarefas, sessoes, chats e etapas arbitrarios - tudo pela API
    publica.

    Memoria fica vazia aqui de proposito: quem a preenche e `anotar`, no teste,
    para que dominio e disco andem juntos (RN-P-08).
    """
    ambiente = Ambiente(nome=draw(texto_nao_vazio))

    for _ in range(draw(st.integers(min_value=0, max_value=3))):
        frente = ambiente.criar_frente(draw(texto_nao_vazio))

        for _ in range(draw(st.integers(min_value=0, max_value=3))):
            tarefa = frente.criar_tarefa(
                draw(texto_nao_vazio), draw(agentes(orquestrador=True))
            )

            for _ in range(draw(st.integers(min_value=0, max_value=2))):
                tarefa.criar_sessao(
                    draw(agentes(orquestrador=True)), nome=draw(texto_nao_vazio)
                )

            for sessao in tarefa.sessoes:
                for _ in range(draw(st.integers(min_value=0, max_value=2))):
                    sessao.criar_chat(
                        draw(agentes(orquestrador=False)), nome=draw(texto_nao_vazio)
                    )

            for _ in range(draw(st.integers(min_value=0, max_value=3))):
                etapa = tarefa.criar_etapa(
                    draw(texto_nao_vazio),
                    draw(st.sampled_from(list(ExecutorEtapa))),
                )
                if draw(st.booleans()):
                    etapa.concluir()

    return ambiente


def tarefas_de(ambiente: Ambiente) -> list[Tarefa]:
    return [tarefa for frente in ambiente.frentes for tarefa in frente.tarefas]


def sessoes_de(ambiente: Ambiente) -> list[Sessao]:
    return [sessao for tarefa in tarefas_de(ambiente) for sessao in tarefa.sessoes]


@st.composite
def roteiros_de_anotacao(draw: Any, quantidade: int = 8) -> list[tuple[str, str, str]]:
    """(chave, autor, valor) - a sessao e escolhida no teste, que conhece o
    ambiente gerado."""
    return draw(
        st.lists(
            st.tuples(texto_nao_vazio, texto_nao_vazio, st.text(_CARACTERES, max_size=40)),
            max_size=quantidade,
        )
    )


def anotacao_agora(autor: str, valor: str) -> Anotacao:
    return Anotacao(autor=autor, valor=valor, criada_em=datetime.now(UTC))
