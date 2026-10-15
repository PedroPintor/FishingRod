"""U5 com os adaptadores REAIS: RepositorioSQLite e WikiDeArquivos.

O resto da unidade testa contra o RepositorioEmMemoria. Este arquivo fecha
US-04, US-15, US-16, US-17 e US-19 de ponta a ponta, sem tela, do jeito que o
usuario as vive: cria o ambiente, trabalha pela barra e pelo orquestrador,
fecha o programa, abre de novo - e tudo esta la, com os dois autores na
memoria.
"""

from fishingrod.adaptadores.persistencia import abrir_repositorio
from fishingrod.adaptadores.wiki import WikiDeArquivos
from fishingrod.aplicacao.catalogo.catalogo import CatalogoDeAcoes
from fishingrod.aplicacao.catalogo.parser import ParserDeComando
from fishingrod.aplicacao.catalogo.tipos import Acionamento, Alvo
from fishingrod.aplicacao.esquema_wiki import EsquemaWiki
from fishingrod.dominio import ExecutorEtapa
from tests.acoes.estrategias import ORQUESTRADOR, executar
from tests.acoes.instrumentos import ConfirmacaoFixa
from tests.ambiente.estrategias import novo_servico

parser = ParserDeComando()


async def _sessao(dados, porta, trabalho):
    """Uma execucao do programa: abre o banco, monta servico e catalogo, faz o
    trabalho, fecha o banco - como o composition root de U9 vai fazer."""
    repo = await abrir_repositorio(dados / "fishingrod.db")
    try:
        servico = novo_servico(repo, WikiDeArquivos(dados))
        return await trabalho(servico, CatalogoDeAcoes(servico, porta))
    finally:
        await repo.fechar()


def test_us_04_15_16_17_19_de_ponta_a_ponta_e_depois_de_reabrir(tmp_path):
    porta = ConfirmacaoFixa(True)  # a pessoa diz "sim" a tudo o que o orquestrador pede

    async def trabalhar(servico, catalogo):
        ambiente = await servico.criar_ambiente("Nexo Aquisição", EsquemaWiki.vazio())
        usar = catalogo.executar_comando

        # US-15 e US-16, pela barra - o criterio 1 literal
        frente = (await usar(parser.interpretar("/criar-frente Aquisição"), Alvo(ambiente.id))).dado
        tarefa = (
            await usar(parser.interpretar("/criar-tarefa campanha de verao"), Alvo(ambiente.id, frente.id))
        ).dado
        alvo = Alvo(ambiente.id, frente.id, tarefa.id)

        # US-17 e US-04, pelo orquestrador, com confirmacao
        orquestrador = Acionamento.agente(ORQUESTRADOR.nome)
        etapa = await catalogo.executar(
            "criar_etapa", alvo, {"executor": "usuário", "descricao": "ligar para 5 clínicas"}, orquestrador
        )
        anotacao = await catalogo.executar(
            "anotar_memoria", alvo, {"chave": "icp", "valor": "dentistas, ticket alto"}, orquestrador
        )

        # US-19 e US-04, pela barra
        concluida = await usar(parser.interpretar("/concluir-etapa 1"), alvo)
        travado = await usar(parser.interpretar("/anotar-memoria travado-por esperando o cliente"), alvo)

        resultados = (etapa, anotacao, concluida, travado)
        assert all(r.sucesso for r in resultados), resultados
        assert etapa.dado.posicao == 1 and concluida.dado.posicao == 1
        return ambiente, frente, tarefa

    async def reabrir(servico, catalogo):
        return await servico.carregar_ambiente(ambiente.id)

    ambiente, frente, tarefa = executar(_sessao(tmp_path, porta, trabalhar))
    reaberto = executar(_sessao(tmp_path, ConfirmacaoFixa(False), reabrir))

    assert [p.acao for p in porta.pedidos] == ["criar_etapa", "anotar_memoria"]
    assert reaberto == ambiente and reaberto is not ambiente
    [frente_lida] = reaberto.frentes
    [tarefa_lida] = frente_lida.tarefas
    assert (frente_lida.nome, tarefa_lida.nome) == ("Aquisição", "campanha de verao")
    assert [(e.descricao, e.executor, e.concluida) for e in tarefa_lida.etapas] == [
        ("ligar para 5 clínicas", ExecutorEtapa.USUARIO, True)
    ]
    memoria = {
        chave: [(a.autor, a.valor) for a in lista]
        for chave, lista in tarefa_lida.memoria.anotacoes.items()
    }
    assert memoria == {
        "icp": [(ORQUESTRADOR.nome, "dentistas, ticket alto")],
        "travado-por": [("usuario", "esperando o cliente")],
    }


def test_recusado_pelo_usuario_nao_chega_ao_disco(tmp_path):
    """RN-AC-33 com o banco de verdade: depois do "nao", reabrir o programa
    mostra o ambiente como estava."""

    async def trabalhar(servico, catalogo):
        ambiente = await servico.criar_ambiente("Nexo", EsquemaWiki.vazio())
        resultado = await catalogo.executar(
            "criar_frente", Alvo(ambiente.id), {"nome": "Nova"}, Acionamento.agente(ORQUESTRADOR.nome)
        )
        return ambiente, resultado

    async def reabrir(servico, catalogo):
        return await servico.carregar_ambiente(ambiente.id)

    ambiente, resultado = executar(_sessao(tmp_path, ConfirmacaoFixa(False), trabalhar))
    reaberto = executar(_sessao(tmp_path, ConfirmacaoFixa(False), reabrir))

    assert not resultado.sucesso
    assert reaberto.frentes == [] and reaberto.versao == ambiente.versao == 1
