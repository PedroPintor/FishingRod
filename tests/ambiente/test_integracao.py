"""U4 com os adaptadores REAIS: RepositorioSQLite e WikiDeArquivos.

O resto da unidade testa contra o RepositorioEmMemoria, e isso basta porque
PBT-U2-08 prova que os dois concordam. Este arquivo existe para fechar US-05 de
ponta a ponta do jeito que o usuario a vive - criar, trabalhar, fechar o
programa, abrir de novo -, e para ver o conflito de versao acontecer entre duas
conexoes de verdade ao mesmo arquivo, que e o "outro processo" de RN-A-10.

O layout e o da instalacao: uma pasta de dados com o banco e, ao lado dele,
wikis/.
"""

import pytest

from fishingrod.adaptadores.persistencia import abrir_repositorio
from fishingrod.adaptadores.wiki import WikiDeArquivos
from fishingrod.aplicacao.esquema_wiki import EsquemaWiki
from fishingrod.aplicacao.portas.persistencia import AmbienteInexistente
from fishingrod.dominio import ExecutorEtapa
from tests.ambiente.estrategias import BIBLIOTECARIO, ORQUESTRADOR, executar, novo_servico

ESQUEMA = EsquemaWiki.a_partir_do_formulario(
    {
        "entidades": [
            {
                "titulo": "Clientes",
                "propriedades": [
                    {"titulo": "Dr. Marcelo", "descricao": "dentista, ticket alto"},
                ],
            },
            {"titulo": "Ofertas"},
        ]
    }
)


async def _sessao(dados, trabalho):
    """Uma execucao do programa: abre o banco, monta o servico, faz o
    trabalho, fecha o banco - como o composition root de U9 vai fazer."""
    repo = await abrir_repositorio(dados / "fishingrod.db")
    try:
        return await trabalho(novo_servico(repo, WikiDeArquivos(dados)))
    finally:
        await repo.fechar()


def test_us_05_o_ambiente_sobrevive_a_fechar_e_reabrir(tmp_path):
    async def trabalhar(servico):
        ambiente = await servico.criar_ambiente("Nexo Aquisição", ESQUEMA)
        frente = await servico.criar_frente(ambiente.id, "Aquisição")
        tarefa = await servico.criar_tarefa(ambiente.id, frente.id, "Prospectar dentistas")
        await servico.criar_chat(ambiente.id, tarefa.id, BIBLIOTECARIO.nome, "wiki")
        etapa = await servico.criar_etapa(ambiente.id, tarefa.id, "listar 20 clínicas", ExecutorEtapa.AGENTE)
        await servico.criar_etapa(ambiente.id, tarefa.id, "ligar para 5", ExecutorEtapa.USUARIO)
        await servico.concluir_etapa(ambiente.id, etapa.id)
        await servico.anotar_memoria(ambiente.id, tarefa.id, "icp", "dentistas", "orquestrador")
        await servico.anotar_memoria(ambiente.id, tarefa.id, "icp", "clínicas pequenas", "usuário")
        return ambiente

    async def reabrir(servico):
        return await servico.carregar_ambiente(original.id), await servico.listar_ambientes()

    original = executar(_sessao(tmp_path, trabalhar))
    reaberto, resumos = executar(_sessao(tmp_path, reabrir))

    assert reaberto == original
    assert reaberto is not original
    [tarefa] = reaberto.frentes[0].tarefas
    assert [(c.agente, c.nome) for c in tarefa.chats] == [
        (ORQUESTRADOR, ORQUESTRADOR.nome),
        (BIBLIOTECARIO, "wiki"),
    ]
    assert [e.concluida for e in tarefa.etapas] == [True, False]
    assert [a.valor for a in tarefa.memoria.anotacoes["icp"]] == ["dentistas", "clínicas pequenas"]
    assert [(r.id, r.nome) for r in resumos] == [(original.id, "Nexo Aquisição")]


def test_criterio_1_e_6_a_wiki_nasce_com_o_ambiente_e_morre_com_ele(tmp_path):
    wiki = WikiDeArquivos(tmp_path)

    async def criar(servico):
        return await servico.criar_ambiente("Nexo", ESQUEMA)

    ambiente = executar(_sessao(tmp_path, criar))
    pasta = tmp_path / "wikis" / ambiente.id.valor
    assert (pasta / "index.md").is_file()
    assert executar(wiki.listar(ambiente.raiz_wiki.localizador, "")) == ["clientes", "ofertas"]

    async def apagar(servico):
        await servico.apagar_ambiente(ambiente.id)

    async def procurar(servico):
        with pytest.raises(AmbienteInexistente):
            await servico.carregar_ambiente(ambiente.id)
        return await servico.listar_ambientes()

    executar(_sessao(tmp_path, apagar))

    assert executar(_sessao(tmp_path, procurar)) == []
    assert not pasta.exists()


def test_rn_a_10_conflito_entre_duas_conexoes_reais_ao_mesmo_banco(tmp_path):
    """Duas conexoes ao mesmo arquivo - dois processos. O que escreve com a
    memoria velha recebe ConflitoDeVersao do SQLite, recarrega, reaplica, e as
    duas mudancas ficam no disco."""

    async def cenario():
        repo_um = await abrir_repositorio(tmp_path / "fishingrod.db")
        repo_outro = await abrir_repositorio(tmp_path / "fishingrod.db")
        try:
            um = novo_servico(repo_um, WikiDeArquivos(tmp_path))
            outro = novo_servico(repo_outro, WikiDeArquivos(tmp_path))

            ambiente = await um.criar_ambiente("Nexo", EsquemaWiki.vazio())
            await outro.criar_frente(ambiente.id, "do outro")
            await um.criar_frente(ambiente.id, "deste")

            assert [f.nome for f in ambiente.frentes] == ["do outro", "deste"]
            assert ambiente.versao == 3
            terceiro = novo_servico(repo_outro, WikiDeArquivos(tmp_path))
            assert await terceiro.carregar_ambiente(ambiente.id) == ambiente
        finally:
            await repo_um.fechar()
            await repo_outro.fechar()

    executar(cenario())
