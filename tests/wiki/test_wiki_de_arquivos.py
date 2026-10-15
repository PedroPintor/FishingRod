"""As cinco operacoes contra uma pasta de verdade, sem duplo (NFR-W-19). A
quinta, `apagar`, foi acrescentada por U4 (Q6=A) e tem secao propria no fim.

Nao existe duplo em memoria de PortaWiki: tmp_path ja e uma pasta descartavel
por teste, e um duplo sem sistema de arquivos nao reproduziria o confinamento -
mentiria justamente onde o risco mora. U4 e U8 vao testar contra esta mesma
classe.

Os testes olham o disco por dentro (bytes, permissoes, temporarios) quando a
regra e sobre o disco; o resto passa so pela porta.
"""

import asyncio
import inspect
import logging
import os
import shutil
import stat
import time
from pathlib import Path

import pytest

from fishingrod.adaptadores.wiki import WikiDeArquivos
from fishingrod.aplicacao.esquema_wiki import EsquemaWiki
from fishingrod.aplicacao.portas.wiki import (
    ArmazenamentoIndisponivel,
    CaminhoForaDaRaiz,
    ConteudoPagina,
    DescricaoObrigatoria,
    EntidadeInexistente,
    ErroDeWiki,
    LocalizadorNaoReconhecido,
    PaginaInexistente,
    PaginaProposta,
    PropostaWiki,
    TituloInvalido,
)
from tests.wiki.estrategias import LOCALIZADOR, executar

NOME = "Nexo Aquisição"


@pytest.fixture
def wiki(tmp_path) -> WikiDeArquivos:
    return WikiDeArquivos(tmp_path / "dados")


@pytest.fixture
def raiz(tmp_path) -> Path:
    """Onde LOCALIZADOR mora no disco. So os testes que olham o disco por
    dentro usam isto - a porta nunca ve um Path."""
    return tmp_path / "dados" / "wikis" / "teste"


def _pagina(entidade="Clientes", titulo="Dr. Marcelo", descricao="dentista", conteudo="corpo"):
    return PaginaProposta(entidade=entidade, titulo=titulo, descricao=descricao, conteudo=conteudo)


def _escrever(wiki, *paginas, entidades_novas=("Clientes",)):
    proposta = PropostaWiki(entidades_novas=entidades_novas, paginas=paginas)
    executar(wiki.escrever_proposta(LOCALIZADOR, proposta))


def _indice(raiz) -> str:
    return (raiz / "index.md").read_bytes().decode("utf-8")


def _latin1(texto: str) -> bytes:
    """Bytes que nao sao UTF-8 valido: "c" com cedilha em latin-1."""
    return texto.encode("ascii").replace(b"c,", bytes([0xE7]))


# --------------------------------------------------------------------------
# O contrato
# --------------------------------------------------------------------------


def test_dp_w_09_as_operacoes_sao_corrotinas(wiki):
    for operacao in ("listar", "ler", "escrever_proposta", "renderizar_index", "apagar"):
        assert inspect.iscoroutinefunction(getattr(wiki, operacao)), operacao


def test_os_sete_erros_tem_a_mesma_raiz():
    """Quem quiser tratar tudo captura ErroDeWiki - e nada de fora dela sai da
    porta (RN-W-36)."""
    for erro in (
        LocalizadorNaoReconhecido,
        CaminhoForaDaRaiz,
        PaginaInexistente,
        EntidadeInexistente,
        DescricaoObrigatoria,
        TituloInvalido,
        ArmazenamentoIndisponivel,
    ):
        assert issubclass(erro, ErroDeWiki)


def test_nfr_w_03_cada_operacao_e_uma_unica_ida_ao_thread(wiki, monkeypatch):
    """DP-W-03: o miolo e sincrono e vai inteiro para o thread. Mais de uma ida
    significaria await no meio de uma operacao, e outra corrotina podendo
    intercalar."""
    original = asyncio.to_thread
    idas = []

    async def contando(funcao, /, *args, **kwargs):
        idas.append(funcao.__name__)
        return await original(funcao, *args, **kwargs)

    monkeypatch.setattr(asyncio, "to_thread", contando)

    _escrever(wiki, _pagina())
    executar(wiki.renderizar_index(LOCALIZADOR, NOME))
    executar(wiki.listar(LOCALIZADOR, "clientes"))
    executar(wiki.ler(LOCALIZADOR, "clientes/dr-marcelo"))
    executar(wiki.apagar(LOCALIZADOR))

    assert idas == ["_escrever_proposta", "_renderizar_index", "_listar", "_ler", "_apagar"]


# --------------------------------------------------------------------------
# O ambiente nasce com wiki (US-08, US-09, business-logic-model.md 6)
# --------------------------------------------------------------------------


def test_us_08_esquema_vazio_nasce_com_indice_vazio(wiki, raiz):
    """Proposta vazia nao escreve nada, e quem cria a raiz e renderizar_index
    (RN-W-25). Indice vazio e estado valido, e legivel (Parte B.3 de U1)."""
    executar(wiki.escrever_proposta(LOCALIZADOR, PropostaWiki()))
    assert not raiz.exists()

    executar(wiki.renderizar_index(LOCALIZADOR, NOME))

    assert _indice(raiz) == (
        "# Wiki — Nexo Aquisição\n\n## Entidades\n\n(vazio — ainda não tem nenhuma entidade)\n"
    )
    assert [item.name for item in raiz.iterdir()] == ["index.md"]


def test_us_09_o_esquema_do_formulario_vira_a_primeira_proposta(wiki, raiz):
    """O fluxo que U4 vai executar: a semente nasce com descricao e sem
    conteudo, e a estrutura e a que o dono digitou - nenhuma entidade vem do
    produto."""
    esquema = EsquemaWiki.a_partir_do_formulario(
        {
            "entidades": [
                {
                    "titulo": "ICP",
                    "propriedades": [
                        {"titulo": "Dentistas", "descricao": "ticket alto, decisão rápida"}
                    ],
                },
                {"titulo": "Provas"},
            ]
        }
    )
    proposta = PropostaWiki(
        entidades_novas=tuple(entidade.titulo for entidade in esquema.entidades),
        paginas=tuple(
            PaginaProposta(
                entidade=entidade.titulo,
                titulo=propriedade.titulo,
                descricao=propriedade.descricao,
                conteudo="",
            )
            for entidade in esquema.entidades
            for propriedade in entidade.propriedades
        ),
    )

    executar(wiki.escrever_proposta(LOCALIZADOR, proposta))
    executar(wiki.renderizar_index(LOCALIZADOR, NOME))

    assert executar(wiki.listar(LOCALIZADOR, "")) == ["icp", "provas"]
    assert executar(wiki.ler(LOCALIZADOR, "icp/dentistas")) == ConteudoPagina(
        caminho="icp/dentistas",
        titulo="Dentistas",
        descricao="ticket alto, decisão rápida",
        conteudo="",
    )
    assert _indice(raiz).endswith(
        "### [[icp]]\n\n"
        "- [[icp/dentistas]]: ticket alto, decisão rápida\n\n"
        "### [[provas]]\n\n"
        "(sem propriedades)\n"
    )


def test_us_09_formulario_sem_entidades_e_o_esquema_vazio():
    assert EsquemaWiki.a_partir_do_formulario({}) == EsquemaWiki.vazio()
    assert EsquemaWiki.a_partir_do_formulario({"entidades": []}) == EsquemaWiki.vazio()


# --------------------------------------------------------------------------
# listar (business-logic-model.md 2)
# --------------------------------------------------------------------------


def test_nfr_w_06_listar_e_ler_nao_criam_a_raiz(wiki, tmp_path):
    assert executar(wiki.listar(LOCALIZADOR, "")) == []
    with pytest.raises(EntidadeInexistente):
        executar(wiki.listar(LOCALIZADOR, "clientes"))
    with pytest.raises(PaginaInexistente):
        executar(wiki.ler(LOCALIZADOR, "clientes/dr-marcelo"))

    assert list(tmp_path.iterdir()) == []


def test_rn_w_02_listar_so_ve_o_que_e_da_wiki(wiki, raiz):
    """Pasta na raiz e entidade; .md dentro de entidade e pagina. index.md,
    arquivo solto, nome fora do formato e subpasta (o nivel 3) ficam de fora."""
    _escrever(
        wiki,
        _pagina(titulo="Nexo B2B"),
        _pagina(titulo="Dr. Marcelo"),
        entidades_novas=("Clientes", "Ofertas"),
    )
    executar(wiki.renderizar_index(LOCALIZADOR, NOME))
    (raiz / "notas.txt").write_text("solto", encoding="utf-8")
    (raiz / "Rascunhos").mkdir()
    (raiz / "clientes" / "leia-me.txt").write_text("x", encoding="utf-8")
    (raiz / "clientes" / "Anotacao Solta.md").write_text("x", encoding="utf-8")
    (raiz / "clientes" / "nivel-3").mkdir()
    (raiz / "clientes" / "nivel-3" / "fundo.md").write_text("x", encoding="utf-8")

    assert executar(wiki.listar(LOCALIZADOR, "")) == ["clientes", "ofertas"]
    assert executar(wiki.listar(LOCALIZADOR, "clientes")) == ["dr-marcelo", "nexo-b2b"]
    assert executar(wiki.listar(LOCALIZADOR, "Clientes")) == ["dr-marcelo", "nexo-b2b"]
    assert executar(wiki.listar(LOCALIZADOR, "ofertas")) == []


@pytest.mark.parametrize("caminho", ["clientes/dr-marcelo", "..", "../fora", "con", "a/b/c", "/"])
def test_rn_w_01_listar_aceita_vazio_ou_uma_entidade_e_so(wiki, caminho):
    _escrever(wiki, _pagina())

    with pytest.raises(CaminhoForaDaRaiz):
        executar(wiki.listar(LOCALIZADOR, caminho))


# --------------------------------------------------------------------------
# ler (business-logic-model.md 3)
# --------------------------------------------------------------------------


def test_r_cg3_3_ler_devolve_o_caminho_canonico(wiki):
    """Titulo ou slug levam a mesma pagina, e o caminho que volta e sempre o
    canonico - o mesmo que aparece no indice."""
    _escrever(wiki, _pagina(titulo="Dr. Marcelo & Cia", conteudo="Conversou em março."))
    esperado = ConteudoPagina(
        caminho="clientes/dr-marcelo-e-cia",
        titulo="Dr. Marcelo & Cia",
        descricao="dentista",
        conteudo="Conversou em março.",
    )

    assert executar(wiki.ler(LOCALIZADOR, "clientes/dr-marcelo-e-cia")) == esperado
    assert executar(wiki.ler(LOCALIZADOR, "Clientes/Dr. Marcelo & Cia")) == esperado


@pytest.mark.parametrize(
    "caminho",
    ["clientes", "clientes/dr-marcelo/extra", "../clientes/dr-marcelo", "clientes/..", "", "/clientes"],
)
def test_rn_w_01_ler_exige_exatamente_dois_segmentos_validos(wiki, caminho):
    _escrever(wiki, _pagina())

    with pytest.raises(CaminhoForaDaRaiz):
        executar(wiki.ler(LOCALIZADOR, caminho))


def test_ler_pagina_que_nao_existe(wiki):
    _escrever(wiki, _pagina())

    with pytest.raises(PaginaInexistente):
        executar(wiki.ler(LOCALIZADOR, "clientes/ninguem"))


def test_rn_w_15_pagina_sem_frontmatter_e_lida_sem_falhar(wiki, raiz):
    _escrever(wiki, _pagina())
    (raiz / "clientes" / "solta.md").write_bytes(b"so texto, sem bloco\n")

    assert executar(wiki.ler(LOCALIZADOR, "clientes/solta")) == ConteudoPagina(
        caminho="clientes/solta", titulo="", descricao="", conteudo="so texto, sem bloco\n"
    )


def test_nfr_w_10_ler_bytes_que_nao_sao_utf8_trava_visivel(wiki, raiz, tmp_path):
    """Travar visivel em vez de deformar: com errors="replace" o agente leria
    texto corrompido como bom, e RN-W-26 gravaria a corrupcao de volta."""
    _escrever(wiki, _pagina())
    arquivo = raiz / "clientes" / "latin1.md"
    bytes_originais = _latin1("---\ndescricao: prec,o\n---\n")
    arquivo.write_bytes(bytes_originais)

    with pytest.raises(ArmazenamentoIndisponivel) as erro:
        executar(wiki.ler(LOCALIZADOR, "clientes/latin1"))

    assert arquivo.read_bytes() == bytes_originais
    assert str(tmp_path) not in str(erro.value)  # NFR-W-17


# --------------------------------------------------------------------------
# escrever_proposta (business-logic-model.md 4)
# --------------------------------------------------------------------------


def test_rn_w_13_rn_w_31_o_arquivo_e_montado_pelo_adaptador_em_utf8_e_lf(wiki, raiz):
    """Bytes exatos: nenhum CRLF do Windows, nenhum bloco escrito por outro."""
    _escrever(
        wiki,
        _pagina(titulo="Dr. Marcelo & Cia", descricao="dentista, ticket alto", conteudo="um\ndois\n"),
    )

    assert (raiz / "clientes" / "dr-marcelo-e-cia.md").read_bytes() == (
        "---\ntitulo: Dr. Marcelo & Cia\ndescricao: dentista, ticket alto\n---\n\num\ndois\n"
    ).encode("utf-8")


def test_rn_w_06_criar_entidade_que_ja_existe_e_no_op(wiki):
    _escrever(wiki, _pagina())
    _escrever(wiki, entidades_novas=("Clientes", "clientes", "CLIENTES"))

    assert executar(wiki.listar(LOCALIZADOR, "")) == ["clientes"]
    assert executar(wiki.listar(LOCALIZADOR, "clientes")) == ["dr-marcelo"]


def test_rn_w_26_reescrever_substitui_a_pagina_inteira(wiki):
    """Conteudo completo, nao fragmento (C4=A). O que ficou velho e riscado
    pelo bibliotecario, nao pela porta."""
    _escrever(wiki, _pagina(descricao="antiga", conteudo="trabalha sozinho"))
    _escrever(
        wiki,
        _pagina(descricao="nova", conteudo="~~trabalha sozinho~~ contratou duas auxiliares"),
        entidades_novas=(),
    )

    lida = executar(wiki.ler(LOCALIZADOR, "clientes/dr-marcelo"))
    assert (lida.descricao, lida.conteudo) == (
        "nova",
        "~~trabalha sozinho~~ contratou duas auxiliares",
    )


@pytest.mark.parametrize("titulo", ["", "...", "../..", "con", "NUL", "lpt9"])
def test_rn_w_05_titulo_invalido_e_recusado_antes_de_tocar_o_disco(wiki, tmp_path, titulo):
    """A pagina valida da mesma proposta tambem nao e escrita (DP-W-10)."""
    proposta = PropostaWiki(
        entidades_novas=("Clientes",), paginas=(_pagina(), _pagina(titulo=titulo))
    )

    with pytest.raises(TituloInvalido):
        executar(wiki.escrever_proposta(LOCALIZADOR, proposta))
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("entidade", ["", "~", "aux"])
def test_rn_w_05_entidade_com_titulo_invalido_e_recusada(wiki, tmp_path, entidade):
    with pytest.raises(TituloInvalido):
        executar(wiki.escrever_proposta(LOCALIZADOR, PropostaWiki(entidades_novas=(entidade,))))
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("descricao", ["", "   ", "\n\t", '""', "' '"])
def test_rn_w_14_descricao_vazia_e_recusada_antes_de_tocar_o_disco(wiki, tmp_path, descricao):
    proposta = PropostaWiki(
        entidades_novas=("Clientes",),
        paginas=(_pagina(), _pagina(titulo="Nexo", descricao=descricao)),
    )

    with pytest.raises(DescricaoObrigatoria):
        executar(wiki.escrever_proposta(LOCALIZADOR, proposta))
    assert list(tmp_path.iterdir()) == []


def test_rn_w_28_pagina_sob_entidade_que_nao_existe(wiki, tmp_path):
    with pytest.raises(EntidadeInexistente):
        executar(wiki.escrever_proposta(LOCALIZADOR, PropostaWiki(paginas=(_pagina(),))))
    assert list(tmp_path.iterdir()) == []


def test_rn_w_28_entidade_que_nasce_na_mesma_proposta_vale(wiki):
    _escrever(wiki, _pagina(entidade="Ofertas"), entidades_novas=("Ofertas",))

    assert executar(wiki.listar(LOCALIZADOR, "ofertas")) == ["dr-marcelo"]


def test_rn_w_28_entidade_que_ja_existe_no_disco_vale(wiki):
    _escrever(wiki, entidades_novas=("Clientes",))
    _escrever(wiki, _pagina(), entidades_novas=())

    assert executar(wiki.listar(LOCALIZADOR, "clientes")) == ["dr-marcelo"]


def test_rn_w_36_texto_que_nao_cabe_em_utf8_e_recusado_sem_truncar_a_pagina(wiki, raiz):
    """Surrogate isolado - que um JSON com escape de surrogate produz - nao
    existe em UTF-8. A falha vem antes de abrir o arquivo: a pagina que ja
    existia continua inteira, e o erro e da porta, nao UnicodeEncodeError."""
    _escrever(wiki, _pagina(conteudo="conteudo que precisa sobreviver"))
    arquivo = raiz / "clientes" / "dr-marcelo.md"
    antes = arquivo.read_bytes()

    with pytest.raises(ArmazenamentoIndisponivel):
        _escrever(wiki, _pagina(conteudo="quebrado " + chr(0xD800)), entidades_novas=())

    assert arquivo.read_bytes() == antes


def test_nfr_w_13_erro_do_sistema_vira_erro_da_porta(wiki, raiz, tmp_path):
    """Um arquivo comum onde a entidade deveria nascer: o mkdir falha, e o que
    chega e ArmazenamentoIndisponivel, com o caminho logico e sem o absoluto
    (NFR-W-17)."""
    raiz.mkdir(parents=True)
    (raiz / "clientes").write_text("um arquivo, nao uma pasta", encoding="utf-8")

    with pytest.raises(ArmazenamentoIndisponivel) as erro:
        _escrever(wiki, entidades_novas=("Clientes",))

    assert isinstance(erro.value.__cause__, OSError)
    assert "[clientes]" in str(erro.value)
    assert str(tmp_path) not in str(erro.value)


# --------------------------------------------------------------------------
# Localizador (RN-W-09)
# --------------------------------------------------------------------------


@pytest.mark.parametrize("localizador", ["nuvem:wikis/teste", "wikis/teste"])
def test_rn_w_09_as_operacoes_recusam_esquema_desconhecido(wiki, tmp_path, localizador):
    operacoes = (
        lambda: wiki.listar(localizador, ""),
        lambda: wiki.ler(localizador, "clientes/dr-marcelo"),
        lambda: wiki.escrever_proposta(localizador, PropostaWiki(entidades_novas=("Clientes",))),
        lambda: wiki.renderizar_index(localizador, NOME),
        lambda: wiki.apagar(localizador),
    )
    for operacao in operacoes:
        with pytest.raises(LocalizadorNaoReconhecido):
            executar(operacao())

    assert list(tmp_path.iterdir()) == []


def test_rn_w_07_localizador_que_sai_da_pasta_de_dados_nao_escreve_nada(wiki, tmp_path):
    with pytest.raises(CaminhoForaDaRaiz):
        executar(wiki.renderizar_index("dados:../fora", NOME))
    assert list(tmp_path.iterdir()) == []


# --------------------------------------------------------------------------
# renderizar_index (business-logic-model.md 5)
# --------------------------------------------------------------------------


def test_rn_w_18_o_indice_inteiro(wiki, raiz):
    """O exemplo de domain-entities.md 3, agora passando pelo disco."""
    _escrever(
        wiki,
        _pagina(titulo="Nexo B2B", descricao="agência parceira, indica leads"),
        _pagina(titulo="Dr. Marcelo", descricao="dentista, ticket alto, fechou em duas reuniões"),
        _pagina(
            entidade="Ofertas",
            titulo="Plano Anual",
            descricao="preço, prazo e o que entra em cada faixa",
        ),
        entidades_novas=("Clientes", "Ofertas"),
    )

    executar(wiki.renderizar_index(LOCALIZADOR, NOME))

    assert _indice(raiz) == (
        "# Wiki — Nexo Aquisição\n"
        "\n"
        "## Entidades\n"
        "\n"
        "### [[clientes]]\n"
        "\n"
        "- [[clientes/dr-marcelo]]: dentista, ticket alto, fechou em duas reuniões\n"
        "- [[clientes/nexo-b2b]]: agência parceira, indica leads\n"
        "\n"
        "### [[ofertas]]\n"
        "\n"
        "- [[ofertas/plano-anual]]: preço, prazo e o que entra em cada faixa\n"
    )


def test_rn_w_20_pagina_sem_descricao_fica_fora_e_intocada(wiki, raiz, caplog):
    """O unico evento silencioso por desenho - e por isso o WARNING (NFR-W-16)."""
    _escrever(wiki, _pagina())
    sem_bloco = raiz / "clientes" / "sem-bloco.md"
    sem_bloco.write_bytes(b"so texto")
    sem_descricao = raiz / "clientes" / "sem-descricao.md"
    sem_descricao.write_bytes(b"---\ntitulo: x\ndescricao:\n---\n")
    antes = [(arquivo.read_bytes(), arquivo.stat().st_mtime_ns) for arquivo in (sem_bloco, sem_descricao)]

    caplog.set_level(logging.WARNING, logger="fishingrod.wiki")
    executar(wiki.renderizar_index(LOCALIZADOR, NOME))

    indice = _indice(raiz)
    assert "[[clientes/dr-marcelo]]" in indice
    assert "sem-bloco" not in indice and "sem-descricao" not in indice
    depois = [(arquivo.read_bytes(), arquivo.stat().st_mtime_ns) for arquivo in (sem_bloco, sem_descricao)]
    assert depois == antes
    avisos = [registro.getMessage() for registro in caplog.records]
    assert any("[clientes/sem-bloco]" in aviso for aviso in avisos)
    assert any("[clientes/sem-descricao]" in aviso for aviso in avisos)


def test_nfr_w_10_pagina_ilegivel_fica_fora_do_indice_sem_ser_tocada(wiki, raiz, caplog):
    _escrever(wiki, _pagina())
    arquivo = raiz / "clientes" / "latin1.md"
    bytes_originais = _latin1("---\ndescricao: prec,o\n---\n")
    arquivo.write_bytes(bytes_originais)

    caplog.set_level(logging.WARNING, logger="fishingrod.wiki")
    executar(wiki.renderizar_index(LOCALIZADOR, NOME))

    assert "latin1" not in _indice(raiz)
    assert arquivo.read_bytes() == bytes_originais
    assert any(
        "[clientes/latin1]" in registro.getMessage() and "UTF-8" in registro.getMessage()
        for registro in caplog.records
    )


def test_nfr_w_16_renderizacao_concluida_vai_para_debug(wiki, caplog):
    _escrever(wiki, _pagina())

    caplog.set_level(logging.DEBUG, logger="fishingrod.wiki")
    executar(wiki.renderizar_index(LOCALIZADOR, NOME))

    [registro] = [r for r in caplog.records if r.levelno == logging.DEBUG]
    assert registro.getMessage().startswith("indice renderizado: 1 paginas em 1 entidades")


def test_rn_w_17_o_indice_anterior_nunca_e_lido(wiki, raiz):
    """Lixo no index.md - ate bytes que nao sao UTF-8 - nao atrapalha: ele e
    saida, nunca entrada. Apagar e renderizar devolve o mesmo arquivo."""
    _escrever(wiki, _pagina())
    executar(wiki.renderizar_index(LOCALIZADOR, NOME))
    bom = _indice(raiz)

    (raiz / "index.md").write_bytes(bytes([0xFF, 0xFE, 0x00]) + b"lixo")
    executar(wiki.renderizar_index(LOCALIZADOR, NOME))
    assert _indice(raiz) == bom

    (raiz / "index.md").unlink()
    executar(wiki.renderizar_index(LOCALIZADOR, NOME))
    assert _indice(raiz) == bom


def test_nfr_w_11_o_indice_e_publicado_por_os_replace_e_nunca_fica_pela_metade(
    wiki, raiz, monkeypatch
):
    """A publicacao falha no ultimo passo: o indice anterior continua inteiro,
    e nenhum temporario fica para tras."""
    _escrever(wiki, _pagina())
    executar(wiki.renderizar_index(LOCALIZADOR, NOME))
    anterior = _indice(raiz)

    chamadas = []

    def replace_que_falha(origem, destino):
        chamadas.append((Path(origem).parent, Path(destino).name))
        raise OSError(5, "disco ocupado")

    _escrever(wiki, _pagina(titulo="Nexo"), entidades_novas=())
    monkeypatch.setattr(os, "replace", replace_que_falha)

    with pytest.raises(ArmazenamentoIndisponivel):
        executar(wiki.renderizar_index(LOCALIZADOR, NOME))

    assert chamadas == [(raiz.resolve(), "index.md")]  # temporario na MESMA pasta
    assert _indice(raiz) == anterior
    assert sorted(item.name for item in raiz.iterdir()) == ["clientes", "index.md"]


@pytest.mark.skipif(os.name != "posix", reason="chmod no Windows so mexe no bit de leitura - R-CG3-5")
def test_nfr_w_07_permissoes_restritas_em_posix(wiki, raiz, tmp_path):
    """0o700 em toda pasta que a wiki cria, 0o600 em todo arquivo - a mesma
    politica do banco em U2 (NFR-P-14)."""
    _escrever(wiki, _pagina())
    executar(wiki.renderizar_index(LOCALIZADOR, NOME))

    def modo(caminho):
        return stat.S_IMODE(os.stat(caminho).st_mode)

    for pasta in (tmp_path / "dados", tmp_path / "dados" / "wikis", raiz, raiz / "clientes"):
        assert modo(pasta) == 0o700, pasta
    for arquivo in (raiz / "index.md", raiz / "clientes" / "dr-marcelo.md"):
        assert modo(arquivo) == 0o600, arquivo


# --------------------------------------------------------------------------
# apagar (acrescentada por U4: Q6=A, R-CG4-2)
# --------------------------------------------------------------------------


def _wiki_completa(wiki, localizador=LOCALIZADOR):
    proposta = PropostaWiki(
        entidades_novas=("Clientes", "Ofertas"),
        paginas=(_pagina(), _pagina(entidade="Ofertas", titulo="Plano Anual")),
    )
    executar(wiki.escrever_proposta(localizador, proposta))
    executar(wiki.renderizar_index(localizador, NOME))


def _arvore(base: Path) -> list[str]:
    return sorted(item.relative_to(base).as_posix() for item in base.rglob("*"))


def _link_de_pasta(link: Path, alvo: Path) -> None:
    """Junction no Windows, symlink no resto. Junction nao exige privilegio,
    entao este teste roda na maquina do dono - ao contrario dos de symlink de
    test_caminhos.py, que la sao pulados (Q3=A de U3)."""
    if os.name == "nt":
        import _winapi  # privado, mas e o que os testes do proprio CPython usam

        _winapi.CreateJunction(str(alvo), str(link))
    else:
        link.symlink_to(alvo, target_is_directory=True)


def test_apagar_remove_a_raiz_inteira(wiki, raiz):
    _wiki_completa(wiki)

    executar(wiki.apagar(LOCALIZADOR))

    assert not raiz.exists()
    assert raiz.parent.is_dir()  # so a wiki deste ambiente: wikis/ continua
    assert executar(wiki.listar(LOCALIZADOR, "")) == []


def test_apagar_raiz_que_nao_existe_e_operacao_vazia(wiki, tmp_path):
    """Mesma regra de apagar_ambiente em U2 (RN-P-22). E sem criar nada no
    caminho."""
    executar(wiki.apagar(LOCALIZADOR))

    assert list(tmp_path.iterdir()) == []


def test_apagar_nao_toca_a_wiki_vizinha(wiki, tmp_path):
    vizinha = "dados:wikis/vizinha"
    _wiki_completa(wiki, vizinha)
    _wiki_completa(wiki)
    antes = _arvore(tmp_path / "dados" / "wikis" / "vizinha")

    executar(wiki.apagar(LOCALIZADOR))

    assert _arvore(tmp_path / "dados" / "wikis" / "vizinha") == antes
    assert executar(wiki.listar(vizinha, "clientes")) == ["dr-marcelo"]


@pytest.mark.parametrize("localizador", ["dados:wikis", "dados:wikis/teste/clientes"])
def test_r_cg4_2_pasta_sem_indice_nao_e_apagada(wiki, tmp_path, localizador):
    """`dados:wikis` passa pelo confinamento - esta dentro da pasta de dados - e,
    sem a guarda do indice, levaria a wiki de todos os ambientes."""
    _wiki_completa(wiki)
    (tmp_path / "dados" / "fishingrod.db").write_bytes(b"o banco de U2")
    antes = _arvore(tmp_path)

    with pytest.raises(CaminhoForaDaRaiz):
        executar(wiki.apagar(localizador))

    assert _arvore(tmp_path) == antes


def test_rn_w_07_apagar_localizador_que_sai_da_pasta_de_dados(wiki, tmp_path):
    """Mesmo com um index.md no destino: a guarda do indice vem depois do
    confinamento, nao no lugar dele."""
    fora = tmp_path / "fora"
    fora.mkdir()
    (fora / "index.md").write_text("parece uma wiki", encoding="utf-8")

    with pytest.raises(CaminhoForaDaRaiz):
        executar(wiki.apagar("dados:../fora"))

    assert (fora / "index.md").read_text(encoding="utf-8") == "parece uma wiki"


def test_apagar_nao_segue_link_para_fora_da_wiki(wiki, raiz, tmp_path):
    """O que o link aponta fica intacto: rmtree remove a entrada e nao desce
    nela. Um link plantado na wiki - na raiz ou dentro de uma entidade - nao
    vira um jeito de apagar o resto do disco."""
    _wiki_completa(wiki)
    fora = tmp_path / "fora"
    fora.mkdir()
    (fora / "segredo.md").write_text("nao e da wiki", encoding="utf-8")
    _link_de_pasta(raiz / "atalho", fora)
    _link_de_pasta(raiz / "clientes" / "atalho", fora)

    executar(wiki.apagar(LOCALIZADOR))

    assert not raiz.exists()
    assert (fora / "segredo.md").read_text(encoding="utf-8") == "nao e da wiki"


def test_nfr_w_13_falha_ao_apagar_vira_erro_da_porta(wiki, tmp_path, monkeypatch):
    _wiki_completa(wiki)

    def rmtree_que_falha(caminho, *args, **kwargs):
        raise PermissionError(13, "acesso negado", str(Path(caminho) / "clientes" / "dr-marcelo.md"))

    monkeypatch.setattr(shutil, "rmtree", rmtree_que_falha)

    with pytest.raises(ArmazenamentoIndisponivel) as erro:
        executar(wiki.apagar(LOCALIZADOR))

    assert isinstance(erro.value.__cause__, PermissionError)
    assert str(tmp_path) not in str(erro.value)  # NFR-W-17


# --------------------------------------------------------------------------
# Desempenho (NFR-W-02, DP-W-11)
# --------------------------------------------------------------------------


def test_nfr_w_02_aprovacao_numa_wiki_de_500_paginas(wiki):
    """<= 1 s para escrever 10 paginas e renderizar o indice de uma wiki com
    500. Roda na suite padrao, de proposito (DP-W-11): teste que nao roda
    apodrece.

    O orcamento era 500 ms e subiu para 1 s em 2026-10-02 (emenda a NFR-W-02):
    dentro da suite, o I/O de metadados desta maquina fica 6-7x mais lento, e
    as medicoes ficaram entre 521 e 870 ms sem regressao nenhuma.

    E o unico teste da unidade cujo resultado depende da maquina - disco lento
    ou antivirus podem derruba-lo sem regressao nenhuma. A margem e grande: a
    escala real e de dezenas de paginas (NFR-W-04).
    """
    entidades = tuple(f"entidade {numero:02d}" for numero in range(25))
    existentes = tuple(
        _pagina(entidade=entidade, titulo=f"pagina {numero:02d}", descricao=f"descricao {numero}")
        for entidade in entidades
        for numero in range(20)
    )
    executar(
        wiki.escrever_proposta(LOCALIZADOR, PropostaWiki(entidades_novas=entidades, paginas=existentes))
    )
    executar(wiki.renderizar_index(LOCALIZADOR, NOME))

    aprovacao = PropostaWiki(
        paginas=tuple(
            _pagina(entidade=entidades[numero], titulo=f"nova {numero}", conteudo="texto " * 200)
            for numero in range(10)
        )
    )

    async def aprovar():
        await wiki.escrever_proposta(LOCALIZADOR, aprovacao)
        await wiki.renderizar_index(LOCALIZADOR, NOME)

    inicio = time.perf_counter()
    executar(aprovar())
    decorrido = time.perf_counter() - inicio

    assert len(executar(wiki.listar(LOCALIZADOR, "entidade-00"))) == 21
    assert decorrido <= 1.0, f"a aprovacao levou {decorrido * 1000:.0f} ms"
