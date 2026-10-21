"""Geradores de Hypothesis para U4, e o que todo teste da unidade monta igual.

Reaproveita U2 (`ambientes`, `texto_nao_vazio`) e U3 (titulos e descricoes) em
vez de redefinir (PBT-07): um ataque acrescentado no alfabeto hostil de U3
passa a valer aqui tambem, e um Ambiente gerado aqui e construido pela mesma
API publica que U2 ja exercita.

Os comandos (PBT-06) sao tuplas, como em PBT-U2-08:

    (operacao, seletor_de_ambiente, seletor_de_alvo, *argumentos)

O alvo e um SELETOR - um inteiro que escolhe entre os ids que existem, ou None
para um id que nao existe -, e nao um id: o gerador nao sabe quais ids o
servico vai criar, e um inteiro encolhe bem. Quem traduz seletor em id e
`modelo.resolver`.
"""

import asyncio
import itertools
import string
from pathlib import Path
from typing import Any

from hypothesis import strategies as st

from fishingrod.adaptadores.wiki import WikiDeArquivos
from fishingrod.aplicacao.esquema_wiki import EntidadeSemente, EsquemaWiki, PropriedadeSemente
from fishingrod.aplicacao.servicos.servico_de_ambiente import (
    ServicoDeAmbiente,
    proposta_do_esquema,
)
from fishingrod.dominio import Agente, Ambiente, ExecutorEtapa, Papel
from tests.persistencia import estrategias as est_persistencia
from tests.wiki import estrategias as est_wiki

ORQUESTRADOR = Agente(nome="orquestrador", papel=Papel.ORQUESTRADOR, modelo="modelo-de-teste")
BIBLIOTECARIO = Agente(nome="bibliotecario", papel=Papel.SUB_AGENTE, modelo="modelo-de-teste")

ambientes = est_persistencia.ambientes
texto_nao_vazio = est_persistencia.texto_nao_vazio
executores = st.sampled_from(list(ExecutorEtapa))

_PASTAS = itertools.count()


@st.composite
def ambientes_de_partida(draw: Any) -> Ambiente:
    """`ambientes` de U2, com a garantia de pelo menos uma tarefa com uma etapa,
    acrescentadas pela mesma API publica quando o sorteio nao as trouxe.

    Sem isto, boa parte das sequencias comecava num ambiente vazio, e
    `criar_chat` nunca dava certo - nao havia sessao onde abrir o chat
    (medido com --hypothesis-show-statistics na primeira versao).
    """
    ambiente = draw(ambientes())
    tarefas = [tarefa for frente in ambiente.frentes for tarefa in frente.tarefas]
    if not tarefas:
        frente = ambiente.frentes[0] if ambiente.frentes else ambiente.criar_frente(draw(texto_nao_vazio))
        tarefas = [frente.criar_tarefa(draw(texto_nao_vazio), ORQUESTRADOR)]
    if not any(tarefa.etapas for tarefa in tarefas):
        tarefas[0].criar_etapa(draw(texto_nao_vazio), draw(executores))
    return ambiente


def executar(coro: Any) -> Any:
    """Mesma decisao de U2 e U3: sem pytest-asyncio, um laco por chamada. Aqui
    o cenario inteiro de um exemplo roda numa corrotina so - e e por isso que
    as travas do servico, que nascem dentro dele, nunca atravessam lacos."""
    return asyncio.run(coro)


def novo_servico(persistencia: Any, wiki: Any) -> ServicoDeAmbiente:
    """O servico como U9 vai monta-lo nesta iteracao: o orquestrador e o
    bibliotecario como unico agente de chat."""
    return ServicoDeAmbiente(persistencia, wiki, ORQUESTRADOR, (BIBLIOTECARIO,))


def pasta_de_dados(tmp_path: Path) -> Path:
    """Uma pasta de dados por exemplo gerado. tmp_path e da funcao de teste e
    passa por todos os exemplos; sem isto, o que um exemplo escreveu na wiki
    apareceria no seguinte."""
    return tmp_path / f"exemplo-{next(_PASTAS)}"


def nova_wiki(tmp_path: Path) -> tuple[WikiDeArquivos, Path]:
    dados = pasta_de_dados(tmp_path)
    return WikiDeArquivos(dados), dados


async def semear(persistencia: Any, wiki: Any, ambiente: Ambiente, esquema: EsquemaWiki) -> None:
    """Um ambiente que ja existe no disco, como se outra sessao o tivesse
    criado: banco e wiki, sem passar pelo servico que esta sob teste.

    E o que deixa as propriedades comecarem de um ambiente rico - frentes,
    tarefas, sessoes, chats e etapas gerados por `ambientes` de U2 - em vez de sempre do
    vazio.
    """
    localizador = ambiente.raiz_wiki.localizador
    await wiki.escrever_proposta(localizador, proposta_do_esquema(esquema))
    await wiki.renderizar_index(localizador, ambiente.nome)
    await persistencia.salvar_ambiente(ambiente)


def ponderado(*pares: tuple[int, st.SearchStrategy]) -> st.SearchStrategy:
    """Escolha com peso. O primeiro par e para onde o Hypothesis encolhe, entao
    ele deve ser o caso mais simples."""
    return st.sampled_from([estrategia for peso, estrategia in pares for _ in range(peso)]).flatmap(
        lambda estrategia: estrategia
    )


# --------------------------------------------------------------------------
# Esquemas (PBT-U4-03)
# --------------------------------------------------------------------------


def _esquemas(titulos: st.SearchStrategy[str], descricoes: st.SearchStrategy[str]) -> st.SearchStrategy[EsquemaWiki]:
    propriedade = st.builds(PropriedadeSemente, titulo=titulos, descricao=descricoes)
    entidade = st.builds(
        EntidadeSemente, titulo=titulos, propriedades=st.lists(propriedade, max_size=3).map(tuple)
    )
    return st.builds(EsquemaWiki, entidades=st.lists(entidade, max_size=3).map(tuple))


# Construidas para nunca normalizar para vazio, em vez de filtradas: com ate
# nove descricoes por esquema, o filtro de `descricoes_validas` de U3 chegava a
# abortar exemplos (medido com --hypothesis-show-statistics). O texto termina
# num alfanumerico, entao normalizar_valor nao acha par de aspas externas para
# tirar, e sobra pelo menos esse caractere. O comeco continua sendo o texto
# hostil da gramatica do frontmatter.
descricoes_validas = st.tuples(
    est_wiki.textos_de_frontmatter,
    st.text(string.ascii_letters + string.digits, min_size=1, max_size=4),
).map("".join)

# Inclui o vazio (lista de tamanho zero), e titulos que colidem no slug
# ("Clientes" e "clientes") quando o Hypothesis os sorteia.
esquemas_validos = _esquemas(est_wiki.titulos_validos, descricoes_validas)

# Tres familias, com peso: validos; titulos validos com descricoes que
# normalizam para vazio; titulos do alfabeto hostil de U3. Parte destes
# esquemas e recusada - e a recusa precisa vir antes de qualquer escrita, no
# banco e no disco. As familias sao separadas porque, misturadas num gerador
# so, o titulo hostil aparecia em quase todo esquema e DescricaoObrigatoria
# nunca era alcancada (medido).
esquemas_quaisquer = ponderado(
    (2, esquemas_validos),
    (1, _esquemas(est_wiki.titulos_validos, descricoes_validas | st.sampled_from(["", "   ", '""', "\n\t"]))),
    (1, _esquemas(est_wiki.titulos_validos | est_wiki.titulos_hostis, descricoes_validas)),
)


# --------------------------------------------------------------------------
# Comandos (PBT-U4-01, 02, 04, 05)
# --------------------------------------------------------------------------

# Validos na maior parte das vezes; vazio e so espaco testam que o erro do
# dominio chega antes de qualquer gravacao (RN-A-02).
nomes = ponderado((3, texto_nao_vazio), (1, st.sampled_from(["", " ", "  \t "])))

valores = st.text(st.characters(exclude_categories=("Cs", "Cc")), max_size=20)

# Inteiro escolhe entre os que existem; None e um id que nao existe. Para o
# ambiente, o id inexistente e mais raro: ele invalida o comando inteiro antes
# de chegar ao alvo, e com o mesmo peso dos alvos tomava um quarto da sequencia.
seletores = ponderado((4, st.integers(min_value=0, max_value=7)), (1, st.none()))
seletores_de_ambiente = ponderado((12, st.integers(min_value=0, max_value=7)), (1, st.none()))

# O bibliotecario e o unico agente de chat. O nome do orquestrador e um texto
# qualquer caem em AgenteDesconhecido (RN-A-22).
nomes_de_agente = ponderado(
    (3, st.just(BIBLIOTECARIO.nome)),
    (1, st.just(ORQUESTRADOR.nome)),
    (1, texto_nao_vazio),
)

# "" vira o nome do agente (Chat, de U1); so espaco e nome invalido.
nomes_de_chat = ponderado((2, st.just("")), (2, texto_nao_vazio), (1, st.just("   ")))

# "" vira "sessão N" (Tarefa, de U1); so espaco e nome invalido.
nomes_de_sessao = nomes_de_chat


def _comando(operacao: str, alvo: bool, *argumentos: st.SearchStrategy) -> st.SearchStrategy[tuple]:
    return st.tuples(
        st.just(operacao), seletores_de_ambiente, seletores if alvo else st.none(), *argumentos
    )


comandos_de_estrutura = ponderado(
    (3, _comando("criar_frente", False, nomes)),
    (3, _comando("criar_tarefa", True, nomes)),
    (2, _comando("criar_sessao", True, nomes_de_sessao)),
    (2, _comando("criar_chat", True, nomes_de_agente, nomes_de_chat)),
    (3, _comando("criar_etapa", True, nomes, executores)),
    (3, _comando("concluir_etapa", True)),
    (3, _comando("anotar_memoria", True, nomes, valores, nomes)),
)


def comandos(*, criar: bool = False, apagar: bool = True) -> st.SearchStrategy[tuple]:
    """As 11 operacoes. `apagar` e raro de proposito: depois dele, todo comando
    sobre aquele ambiente e AmbienteInexistente, e uma sequencia que apagasse
    cedo demais exercitaria pouco."""
    pares: list[tuple[int, st.SearchStrategy]] = [
        (16, comandos_de_estrutura),
        (1, _comando("carregar_ambiente", False)),
        (1, st.tuples(st.just("listar_ambientes"), st.none(), st.none())),
    ]
    if apagar:
        pares.append((1, _comando("apagar_ambiente", False)))
    if criar:
        pares.append(
            (2, st.tuples(st.just("criar_ambiente"), st.none(), st.none(), nomes, esquemas_validos))
        )
    return ponderado(*pares)
