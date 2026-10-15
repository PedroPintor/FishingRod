"""As propriedades de U3 que precisam do disco: PBT-U3-02, 03, 04, 06 e 08 (esta
acrescentada por U4, junto com `apagar` - R-CG4-4).

Contra a WikiDeArquivos real sobre tmp_path (NFR-W-19). Cada exemplo gerado usa
uma pasta propria dentro de tmp_path, entao nenhum exemplo enxerga o que o
anterior escreveu, e o que fica fora da wiki do exemplo serve de testemunha de
que nada vazou.

A camada de unidade de PBT-U3-01, 05 e 07 esta em test_caminhos.py e
test_frontmatter.py; PBT-U3-06, aqui, carrega tambem a camada de ponta a ponta
de PBT-U3-01.
"""

import itertools
import re
from pathlib import Path

from hypothesis import given, settings
from hypothesis import strategies as st

from fishingrod.adaptadores.wiki import WikiDeArquivos
from fishingrod.aplicacao.caminho_wiki import caminho, normalizar_valor, slug
from fishingrod.aplicacao.portas.wiki import ConteudoPagina, ErroDeWiki, PropostaWiki
from tests.wiki import estrategias as est
from tests.wiki.estrategias import executar

_NUMERO = itertools.count()
_LINHA_DE_PAGINA = re.compile(r"- \[\[([^\]]+)\]\]: (.*)")
_LINHA_DE_ENTIDADE = re.compile(r"### \[\[([^\]]+)\]\]")


def _nova_wiki(tmp_path: Path) -> tuple[WikiDeArquivos, str, Path]:
    """Uma wiki por exemplo, numa pasta propria. Pasta propria, e nao so
    localizador novo: assim o custo de olhar a arvore de um exemplo nao cresce
    com o numero de exemplos que vieram antes."""
    dados = tmp_path / f"exemplo-{next(_NUMERO)}" / "dados"
    return WikiDeArquivos(dados), est.LOCALIZADOR, dados / "wikis" / "teste"


def _uma_por_proposta(wiki, localizador, paginas) -> None:
    """Cada pagina numa proposta propria, criando a entidade junto: a ordem de
    criacao no disco e a ordem da lista."""
    for pagina in paginas:
        proposta = PropostaWiki(entidades_novas=(pagina.entidade,), paginas=(pagina,))
        executar(wiki.escrever_proposta(localizador, proposta))


def _ler_indice(raiz: Path) -> list[str]:
    # bytes + decode, e split em LF: read_text traduziria quebras de linha, e
    # splitlines partiria em caracteres que o indice trata como texto comum.
    return (raiz / "index.md").read_bytes().decode("utf-8").split("\n")


# --------------------------------------------------------------------------
# PBT-U3-02 - indice deterministico e idempotente
# --------------------------------------------------------------------------


@settings(max_examples=50)
@given(
    dados=st.data(),
    paginas=st.lists(
        est.paginas_validas(), max_size=6, unique_by=lambda p: caminho(p.entidade, p.titulo)
    ),
)
def test_pbt_u3_02_indice_deterministico_e_idempotente(tmp_path, dados, paginas):
    """Duas wikis com o mesmo conteudo, criado em ordens diferentes, dao o mesmo
    index.md byte a byte - e renderizar de novo nao muda nada (RN-W-17,
    RN-W-21). E o que deixa chamar a renderizacao sem medo depois de qualquer
    escrita."""
    embaralhadas = dados.draw(st.permutations(paginas))
    wiki_a, local_a, raiz_a = _nova_wiki(tmp_path)
    wiki_b, local_b, raiz_b = _nova_wiki(tmp_path)

    _uma_por_proposta(wiki_a, local_a, paginas)
    _uma_por_proposta(wiki_b, local_b, embaralhadas)
    executar(wiki_a.renderizar_index(local_a, "ambiente"))
    executar(wiki_b.renderizar_index(local_b, "ambiente"))

    indice = (raiz_a / "index.md").read_bytes()
    assert (raiz_b / "index.md").read_bytes() == indice

    executar(wiki_a.renderizar_index(local_a, "ambiente"))
    assert (raiz_a / "index.md").read_bytes() == indice


# --------------------------------------------------------------------------
# PBT-U3-03 - round-trip de pagina
# --------------------------------------------------------------------------


@given(pagina=est.paginas_validas())
def test_pbt_u3_03_round_trip_de_pagina(tmp_path, pagina):
    """Para qualquer titulo, descricao e corpo, ler(escrever(p)) devolve os tres
    (RN-W-13). Titulo e descricao voltam normalizados - e o que
    normalizar_valor promete -, e o corpo volta byte a byte, inclusive `---`,
    CR e linha em branco no comeco (PBT-U3-07, agora passando pelo disco)."""
    wiki, local, _ = _nova_wiki(tmp_path)
    _uma_por_proposta(wiki, local, [pagina])

    logico = caminho(pagina.entidade, pagina.titulo)
    assert executar(wiki.ler(local, logico)) == ConteudoPagina(
        caminho=logico,
        titulo=normalizar_valor(pagina.titulo),
        descricao=normalizar_valor(pagina.descricao),
        conteudo=pagina.conteudo,
    )


# --------------------------------------------------------------------------
# PBT-U3-04 - o indice lista exatamente as paginas escritas pelo app
# --------------------------------------------------------------------------


def _plantar_o_que_o_app_nao_escreveu(raiz: Path, entidades: set[str], paginas: dict) -> None:
    """Lixo que o indice nao pode mostrar (RN-W-02): pasta solta na raiz, nome
    fora do formato, arquivo que nao e .md, subpasta (o nivel 3) e pagina sem
    descricao. Os nomes com espaco nao colidem com slug nenhum, nem em sistema
    de arquivos que ignora caixa."""
    raiz.mkdir(parents=True, exist_ok=True)
    (raiz / "notas.txt").write_text("solto", encoding="utf-8")
    (raiz / "Pasta Solta").mkdir(exist_ok=True)
    (raiz / "Pasta Solta" / "pagina.md").write_text("---\ndescricao: escondida\n---\n", encoding="utf-8")
    for entidade in entidades:
        pasta = raiz / entidade
        (pasta / "Fora do Formato.md").write_text("---\ndescricao: com descricao\n---\n", encoding="utf-8")
        (pasta / "leia-me.txt").write_text("x", encoding="utf-8")
        (pasta / "nivel 3").mkdir(exist_ok=True)
        (pasta / "nivel 3" / "fundo.md").write_text("---\ndescricao: funda\n---\n", encoding="utf-8")
        if f"{entidade}/sem-descricao" not in paginas:
            (pasta / "sem-descricao.md").write_text("---\ntitulo: x\n---\n", encoding="utf-8")


@settings(max_examples=50)
@given(propostas=est.sequencias_de_propostas())
def test_pbt_u3_04_o_indice_lista_exatamente_as_paginas_escritas_pelo_app(tmp_path, propostas):
    """Nem mais, nem menos (RN-W-20, criterio 1 de U3), para qualquer sequencia
    de propostas - inclusive as recusadas, que nao podem ter deixado rastro
    (DP-W-10) - e com lixo no disco que o app nao escreveu (RN-W-02).

    Cruza os dois leitores de frontmatter: a escrita e conferida pelo
    cabecalho, que e o que o indice usa (NFR-W-20)."""
    wiki, local, raiz = _nova_wiki(tmp_path)
    entidades: set[str] = set()
    paginas: dict[str, str] = {}

    for proposta in propostas:
        try:
            executar(wiki.escrever_proposta(local, proposta))
        except ErroDeWiki:
            continue  # recusada antes de tocar o disco: o modelo nao muda
        entidades.update(slug(titulo) for titulo in proposta.entidades_novas)
        for pagina in proposta.paginas:
            paginas[caminho(pagina.entidade, pagina.titulo)] = normalizar_valor(pagina.descricao)

    _plantar_o_que_o_app_nao_escreveu(raiz, entidades, paginas)
    executar(wiki.renderizar_index(local, "ambiente"))

    linhas = _ler_indice(raiz)
    no_indice = {m[1]: m[2] for linha in linhas if (m := _LINHA_DE_PAGINA.fullmatch(linha))}
    entidades_no_indice = {m[1] for linha in linhas if (m := _LINHA_DE_ENTIDADE.fullmatch(linha))}

    assert no_indice == paginas
    assert entidades_no_indice == entidades


# --------------------------------------------------------------------------
# PBT-U3-06 - dois niveis irrepresentaveis (e nada fora da raiz)
# --------------------------------------------------------------------------


def _arvore_fora(base: Path, raiz: Path) -> set[tuple]:
    """Tudo que existe em `base` fora de `raiz`, com tamanho e instante de
    escrita de cada arquivo. Pasta entra so pelo nome: criar uma wiki nova
    muda o instante da pasta-mae, e isso nao e vazamento."""
    fora = set()
    for item in base.rglob("*"):
        if item.is_relative_to(raiz):
            continue
        if item.is_dir():
            fora.add((item.relative_to(base).as_posix(), "pasta"))
        else:
            dados = item.stat()
            fora.add((item.relative_to(base).as_posix(), dados.st_size, dados.st_mtime_ns))
    return fora


@settings(max_examples=50)
@given(
    propostas=st.lists(est.propostas_hostis(), min_size=1, max_size=4),
    caminhos=st.lists(est.caminhos_hostis, max_size=4),
)
def test_pbt_u3_06_nenhuma_operacao_cria_terceiro_nivel_nem_escreve_fora(
    tmp_path, propostas, caminhos
):
    """Dois niveis irrepresentaveis (RN-W-01, criterio 6 de U3): nenhuma entrada,
    por nenhuma das quatro operacoes, produz arquivo a mais de dois niveis da
    raiz. E, de passagem, PBT-U3-01 de ponta a ponta: titulo e caminho hostis
    nao criam nem alteram nada fora da wiki do exemplo."""
    wiki, local, raiz = _nova_wiki(tmp_path)
    dados = raiz.parent.parent
    exemplo = dados.parent
    # Sentinelas fora da wiki: o banco mora na raiz de dados, ao lado de
    # wikis/, e e o primeiro alvo de uma escrita que escapasse.
    (dados / "wikis").mkdir(parents=True)
    (dados / "fishingrod.db").write_bytes(b"o banco de U2")
    (exemplo / "fora").mkdir()
    (exemplo / "fora" / "segredo.md").write_text("---\ndescricao: nao e da wiki\n---\n", encoding="utf-8")
    antes = _arvore_fora(exemplo, raiz)

    for proposta in propostas:
        try:
            executar(wiki.escrever_proposta(local, proposta))
        except ErroDeWiki:
            pass
    for caminho_hostil in caminhos:
        for operacao in (wiki.listar, wiki.ler):
            try:
                executar(operacao(local, caminho_hostil))
            except ErroDeWiki:
                pass
    executar(wiki.renderizar_index(local, "ambiente"))

    assert _arvore_fora(exemplo, raiz) == antes
    for item in raiz.rglob("*"):
        profundidade = len(item.relative_to(raiz).parts)
        assert profundidade <= 2, item
        if profundidade == 1:
            assert item.is_dir() or item.name == "index.md", item
        else:
            assert item.is_file() and item.suffix == ".md", item


# --------------------------------------------------------------------------
# PBT-U3-08 - apagar e idempotente e nao toca o vizinho (acrescentada por U4)
# --------------------------------------------------------------------------


def _fotografar(raiz: Path) -> dict[str, bytes]:
    return {
        item.relative_to(raiz).as_posix(): item.read_bytes()
        for item in raiz.rglob("*")
        if item.is_file()
    }


@settings(max_examples=25)
@given(
    proposta=est.propostas_validas(),
    proposta_vizinha=est.propostas_validas(),
    vezes=st.integers(min_value=1, max_value=3),
)
def test_pbt_u3_08_apagar_e_idempotente_e_nao_toca_o_vizinho(
    tmp_path, proposta, proposta_vizinha, vezes
):
    """R-CG4-4 (PBT-04): apagar k vezes deixa o mesmo que apagar uma - a raiz
    some e listar devolve [] -, e a wiki do outro ambiente, na mesma pasta de
    dados, fica identica byte a byte."""
    wiki, local, raiz = _nova_wiki(tmp_path)
    local_vizinha = "dados:wikis/vizinha"
    for localizador, conteudo in ((local, proposta), (local_vizinha, proposta_vizinha)):
        executar(wiki.escrever_proposta(localizador, conteudo))
        executar(wiki.renderizar_index(localizador, "ambiente"))
    vizinha = raiz.parent / "vizinha"
    antes = _fotografar(vizinha)

    for _ in range(vezes):
        executar(wiki.apagar(local))
        assert not raiz.exists()
        assert executar(wiki.listar(local, "")) == []

    assert _fotografar(vizinha) == antes
