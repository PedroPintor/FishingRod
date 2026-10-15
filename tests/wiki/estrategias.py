"""Geradores de Hypothesis para U3, e o auxiliar que roda corrotina em teste.

O alfabeto hostil (DP-W-12) mora aqui e so aqui: PBT-U3-01 (confinamento) e
PBT-U3-05 (slug) o compartilham, e um ataque acrescentado nesta lista passa a
valer para as duas de uma vez.

Os titulos validos sao CONSTRUIDOS para ter slug aproveitavel, em vez de
filtrados depois: com o alfabeto Unicode inteiro, boa parte dos textos
aleatorios nao tem letra latina nenhuma, e um filtro descartaria quase tudo.
"""

import asyncio
import string
from typing import Any

from hypothesis import strategies as st

from fishingrod.aplicacao.caminho_wiki import NOMES_RESERVADOS, normalizar_valor, slug
from fishingrod.aplicacao.portas.wiki import PaginaProposta, PropostaWiki

# Curto de proposito: no Windows o caminho de tmp_path ja e longo, e o que
# interessa exercitar e o que vem depois da raiz.
LOCALIZADOR = "dados:wikis/teste"


def executar(coro: Any) -> Any:
    """Roda a corrotina num laco proprio. Mesma decisao e mesmo motivo de U2
    (tests/persistencia/estrategias.py): sem pytest-asyncio, um laco por
    chamada, e Hypothesis livre para gerar centenas de exemplos."""
    return asyncio.run(coro)


# Qualquer caractere que o UTF-8 consegue gravar. Ao contrario de U2, aqui os
# caracteres de controle ENTRAM: quebra de linha, tabulacao e NUL dentro de um
# titulo sao exatamente o que o slug e normalizar_valor precisam aguentar. So
# os surrogates (Cs) ficam de fora, porque nao existem em UTF-8 - o caso deles
# tem teste proprio em test_wiki_de_arquivos.py.
QUALQUER = st.characters(exclude_categories=("Cs",))

# O que a gramatica do frontmatter trata de um jeito especial, em FRAGMENTOS
# misturados a texto qualquer. Precisa ser fragmento, e nao caractere: o
# Hypothesis funde um one_of de caracteres num intervalo so, e dez caracteres
# somem no meio de um milhao - um ":" no meio de uma descricao quase nunca era
# gerado, e um leitor que cortasse a descricao no ":" passava por todas as
# propriedades. Verificado injetando esse defeito.
_FRAGMENTOS_DA_GRAMATICA = (":", ": ", '"', "'", "#", "-", "---", " ", "\t", "\r", "\n", "\r\n")


def _textos_de_frontmatter(fragmentos: int) -> st.SearchStrategy[str]:
    return st.lists(
        st.sampled_from(_FRAGMENTOS_DA_GRAMATICA) | st.text(QUALQUER, max_size=4),
        max_size=fragmentos,
    ).map("".join)


textos_de_frontmatter = _textos_de_frontmatter(8)

_ALFANUMERICO = string.ascii_letters + string.digits


# --------------------------------------------------------------------------
# Alfabeto hostil (DP-W-12, NFR-W-18)
# --------------------------------------------------------------------------

FRAGMENTOS_HOSTIS = (
    # travessia e caminho absoluto
    "..",
    "../..",
    "..\\..",
    "/etc/passwd",
    "C:\\Windows",
    "\\\\servidor\\c$",
    "~",
    "~/",
    ".",
    "./",
    # separadores repetidos
    "/",
    "//",
    "\\",
    "\\\\",
    # NUL, que o sistema de arquivos recusa no meio de um nome
    "\x00",
    # nomes reservados do Windows, em caixas e formas diferentes (RN-W-05)
    "con",
    "NUL",
    "Com1",
    "lpt9",
    "aux.md",
    "COM\u00b9",  # "1" sobrescrito, que a NFKD transforma em "1"
    # Unicode que vira ponto ou barra depois da NFKD
    "\uff0e\uff0e",  # dois pontos de largura cheia -> ".."
    "\u2025",  # "dois pontos de guia" -> ".."
    "\uff0f",  # barra de largura cheia -> "/"
    "\uff3c",  # contrabarra de largura cheia
    "\u2215",  # barra de divisao
    "\u00a0",  # espaco sem quebra
    "\u200b",  # espaco de largura zero
    "\u0130",  # I com ponto, que muda de tamanho ao virar minuscula
    "\ufb03",  # ligadura "ffi"
    # coisas que parecem a estrutura da propria wiki
    "%2e%2e%2f",
    "index",
    "index.md",
    "---",
)

titulos_hostis = st.one_of(
    st.sampled_from(FRAGMENTOS_HOSTIS),
    st.lists(
        st.one_of(st.sampled_from(FRAGMENTOS_HOSTIS), st.text(QUALQUER, max_size=4)),
        min_size=1,
        max_size=5,
    ).map("".join),
)

# Caminho logico hostil: segmentos hostis colados com "/" - inclusive nenhum,
# um, e tres ou mais segmentos, que a wiki de dois niveis nao tem.
caminhos_hostis = st.lists(titulos_hostis, max_size=4).map("/".join)


# --------------------------------------------------------------------------
# Entradas validas
# --------------------------------------------------------------------------

# Lixo qualquer em volta de pelo menos um alfanumerico ASCII: o slug nunca sai
# vazio, e o lixo continua exercitando NFKD, acento e caractere de controle.
titulos_validos = (
    st.tuples(
        _textos_de_frontmatter(2),
        st.text(_ALFANUMERICO, min_size=1, max_size=4),
        _textos_de_frontmatter(2),
    )
    .map("".join)
    .filter(lambda titulo: slug(titulo) not in NOMES_RESERVADOS)
)

descricoes_validas = textos_de_frontmatter.filter(
    lambda descricao: normalizar_valor(descricao) != ""
)

# O corpo e markdown escrito por agente: `---` e regua horizontal e VAI
# aparecer (RN-W-16). Estes fragmentos fazem o corpo parecer frontmatter de
# proposito - inclusive comecando por `---`, por linha em branco e por "\r".
_FRAGMENTOS_DE_CORPO = (
    "---",
    "\n",
    "\r\n",
    "\r",
    "\n---\n",
    "titulo: falso",
    "descricao: falsa",
    "~~riscado~~",
    "[[outra/pagina]]",
    " ",
)

corpos = st.lists(
    st.one_of(st.sampled_from(_FRAGMENTOS_DE_CORPO), st.text(QUALQUER, max_size=10)),
    max_size=12,
).map("".join)


@st.composite
def paginas_validas(draw: Any, entidade: str | None = None) -> PaginaProposta:
    return PaginaProposta(
        entidade=draw(titulos_validos) if entidade is None else entidade,
        titulo=draw(titulos_validos),
        descricao=draw(descricoes_validas),
        conteudo=draw(corpos),
    )


@st.composite
def propostas_validas(draw: Any) -> PropostaWiki:
    """Toda pagina cai numa entidade que a propria proposta cria, entao nenhuma
    proposta daqui levanta erro."""
    entidades = draw(st.lists(titulos_validos, min_size=1, max_size=3))
    paginas = draw(
        st.lists(
            st.sampled_from(entidades).flatmap(lambda e: paginas_validas(entidade=e)),
            max_size=4,
        )
    )
    return PropostaWiki(entidades_novas=tuple(entidades), paginas=tuple(paginas))


@st.composite
def sequencias_de_propostas(draw: Any) -> list[PropostaWiki]:
    """Uma sessao de trabalho: propostas em sequencia sobre o mesmo punhado de
    entidades. Metade e bem formada - e ainda assim pode ser recusada, se cita
    uma entidade que nenhuma proposta anterior criou -; a outra metade vem de
    propostas_quaisquer.

    Sem a metade bem formada, quase toda proposta gerada seria recusada por
    titulo hostil, e uma propriedade sobre "as paginas escritas" passaria sem
    ter visto pagina nenhuma.
    """
    entidades = draw(st.lists(titulos_validos, min_size=1, max_size=3, unique_by=slug))
    da_sessao = st.sampled_from(entidades)
    propostas = []
    for _ in range(draw(st.integers(min_value=1, max_value=5))):
        if draw(st.booleans()):
            novas = draw(st.lists(da_sessao, max_size=2))
            # Metade das vezes as paginas caem nas entidades que a propria
            # proposta cria (aceita); na outra, em qualquer uma da sessao
            # (aceita so se uma proposta anterior a criou).
            alvo = st.sampled_from(novas) if novas and draw(st.booleans()) else da_sessao
            paginas = draw(
                st.lists(alvo.flatmap(lambda e: paginas_validas(entidade=e)), max_size=3)
            )
            propostas.append(PropostaWiki(entidades_novas=tuple(novas), paginas=tuple(paginas)))
        else:
            propostas.append(draw(propostas_quaisquer()))
    return propostas


@st.composite
def propostas_hostis(draw: Any) -> PropostaWiki:
    """Bem formadas em tudo, menos nos titulos: as entidades que as paginas citam
    nascem na mesma proposta, e toda descricao e valida.

    E o que da dentes a PBT-U3-06. Uma proposta hostil que caisse por outro
    motivo - entidade inexistente, descricao vazia - nunca chegaria ao disco, e
    um confinamento quebrado passaria despercebido. Verificado: com o slug e as
    etapas 1 e 3 desligadas, a propriedade so falhava com estas propostas.
    """
    titulo = titulos_hostis | titulos_validos
    entidades = draw(st.lists(titulo, min_size=1, max_size=3))
    paginas = draw(
        st.lists(
            st.builds(
                PaginaProposta,
                entidade=st.sampled_from(entidades),
                titulo=titulo,
                descricao=descricoes_validas,
                conteudo=corpos,
            ),
            max_size=3,
        )
    )
    return PropostaWiki(entidades_novas=tuple(entidades), paginas=tuple(paginas))


@st.composite
def propostas_quaisquer(draw: Any) -> PropostaWiki:
    """Titulos validos e hostis, descricoes boas e vazias, entidades que existem
    e que nao existem. Parte destas propostas e recusada - e a recusa precisa
    acontecer antes de tocar o disco (DP-W-10)."""
    titulo = titulos_validos | titulos_hostis
    entidades = draw(st.lists(titulo, max_size=3))
    entidade_da_pagina = (st.sampled_from(entidades) | titulo) if entidades else titulo
    paginas = draw(
        st.lists(
            st.builds(
                PaginaProposta,
                entidade=entidade_da_pagina,
                titulo=titulo,
                descricao=descricoes_validas | st.text(QUALQUER, max_size=3),
                conteudo=corpos,
            ),
            max_size=4,
        )
    )
    return PropostaWiki(entidades_novas=tuple(entidades), paginas=tuple(paginas))
