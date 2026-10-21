"""As propriedades da porta, nas DUAS implementacoes (PBT-U2-01..08).

A fixture `repositorio` e parametrizada: cada teste deste arquivo roda uma vez
sobre RepositorioSQLite e uma vez sobre RepositorioEmMemoria. E o que RN-P-25
pede - toda regra RN-P-* vale para os dois.

O ultimo teste e diferente dos outros: em vez de verificar cada implementacao
contra a especificacao, verifica uma contra a outra, numa sequencia gerada de
operacoes. E ele que descobre ambiguidade no contrato antes de U4, U7 e U8
comecarem a depender dele.
"""

import copy
from datetime import UTC, datetime

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from fishingrod.adaptadores.persistencia import abrir_repositorio
from fishingrod.aplicacao.portas.persistencia import (
    ConflitoDeVersao,
    ErroDePersistencia,
    MensagemInexistente,
)
from fishingrod.dominio import Ambiente, Anotacao, Identidade
from tests.dobles.repositorio_memoria import RepositorioEmMemoria
from tests.persistencia import estrategias as est
from tests.persistencia.estrategias import executar

# Um repositorio por teste, reaproveitado entre os exemplos gerados.
#
# E seguro porque cada exemplo cria um Ambiente com identidade nova: nenhum
# exemplo enxerga o estado do anterior. E funciona com um laco de eventos novo
# por exemplo porque, verificado nesta versao (CPython 3.14.4), asyncio.Lock so
# se prende a um laco quando ha disputa - e nestes testes nunca ha.


@pytest.fixture(params=["sqlite", "memoria"])
def repositorio(request, tmp_path):
    if request.param == "memoria":
        yield RepositorioEmMemoria()
        return

    repo = executar(abrir_repositorio(tmp_path / "fishingrod.db"))
    yield repo
    executar(repo.fechar())


async def _ambiente_salvo(repositorio):
    """Mensagem e anotacao pendem de um ambiente que precisa existir.

    Nao era pre-condicao declarada no Functional Design: apareceu aqui, quando
    PBT-U2-04 inseriu mensagem num ambiente nunca salvo e o adaptador real
    recusou pela chave estrangeira que existe para a cascata de RN-P-20.
    """
    ambiente = Ambiente(nome="ambiente de teste")
    await repositorio.salvar_ambiente(ambiente)
    return ambiente


def _anotar_roteiro(ambiente, roteiro):
    """Aplica o roteiro no dominio E na porta, em paralelo.

    Os dois lados precisam andar juntos porque RN-P-08 proibe salvar_ambiente de
    tocar anotacao: sem este replay, o round-trip falharia por a regra estar
    sendo cumprida.
    """
    sessoes = est.sessoes_de(ambiente)
    if not sessoes:
        return []

    aplicadas = []
    for indice, (chave, autor, valor) in enumerate(roteiro):
        sessao = sessoes[indice % len(sessoes)]
        anotacao = sessao.memoria.anotar(chave, valor, autor)
        aplicadas.append((sessao, chave, anotacao))
    return aplicadas


# --------------------------------------------------------------------------
# PBT-U2-01 e PBT-U2-02 - round-trip e memoria
# --------------------------------------------------------------------------


@given(ambiente=est.ambientes(), roteiro=est.roteiros_de_anotacao())
@settings(max_examples=30)
def test_pbt_u2_01_round_trip_preserva_o_ambiente(repositorio, ambiente, roteiro):
    """RN-P-01: nada de silenciosamente perdido."""

    async def cenario():
        await repositorio.salvar_ambiente(ambiente)
        for sessao, chave, anotacao in _anotar_roteiro(ambiente, roteiro):
            await repositorio.anotar(ambiente.id, sessao.id, chave, anotacao)

        carregado = await repositorio.carregar_ambiente(ambiente.id)
        assert carregado == ambiente

    executar(cenario())


@given(
    ambiente=est.ambientes(),
    roteiro=st.lists(
        st.tuples(est.texto_nao_vazio, est.texto_nao_vazio, st.text(max_size=30)),
        min_size=1,
        max_size=10,
    ),
)
@settings(max_examples=30)
def test_pbt_u2_02_memoria_volta_na_ordem_de_escrita(repositorio, ambiente, roteiro):
    """RN-P-10: mesmas anotacoes, mesmas chaves, mesma ordem, versao = total."""

    async def cenario():
        await repositorio.salvar_ambiente(ambiente)
        sessoes = est.sessoes_de(ambiente)
        if not sessoes:
            return

        sessao = sessoes[0]
        for chave, autor, valor in roteiro:
            anotacao = sessao.memoria.anotar(chave, valor, autor)
            await repositorio.anotar(ambiente.id, sessao.id, chave, anotacao)

        carregado = await repositorio.carregar_ambiente(ambiente.id)
        memoria = est.sessoes_de(carregado)[0].memoria

        assert memoria.anotacoes == sessao.memoria.anotacoes
        assert memoria.versao == len(roteiro)
        assert memoria.versao == memoria.total_de_anotacoes()

    executar(cenario())


@given(ambiente=est.ambientes(), autores=st.lists(est.texto_nao_vazio, min_size=2, max_size=2))
@settings(max_examples=25)
def test_pbt_u2_06_anotacoes_concorrentes_sobrevivem_todas(repositorio, ambiente, autores):
    """RN-P-07: e a regra pela qual a memoria saiu do documento."""

    async def cenario():
        await repositorio.salvar_ambiente(ambiente)
        sessoes = est.sessoes_de(ambiente)
        if not sessoes:
            return

        sessao = sessoes[0]
        for volta in range(6):
            autor = autores[volta % 2]
            anotacao = est.anotacao_agora(autor, f"nota {volta}")
            # Sem recarregar o ambiente no meio: e exatamente a intercalacao que
            # o bloqueio otimista transformaria em falso conflito.
            await repositorio.anotar(ambiente.id, sessao.id, "achados", anotacao)

        carregado = await repositorio.carregar_ambiente(ambiente.id)
        memoria = est.sessoes_de(carregado)[0].memoria

        assert memoria.total_de_anotacoes() == 6
        assert [a.valor for a in memoria.anotacoes["achados"]] == [
            f"nota {i}" for i in range(6)
        ]
        assert {a.autor for a in memoria.anotacoes["achados"]} == set(autores)

    executar(cenario())


# --------------------------------------------------------------------------
# PBT-U2-03 - bloqueio otimista
# --------------------------------------------------------------------------


@given(ambiente=est.ambientes(), nome_novo=est.texto_nao_vazio, nome_perdido=est.texto_nao_vazio)
@settings(max_examples=30)
def test_pbt_u2_03_versao_obsoleta_levanta_e_nao_grava(
    repositorio, ambiente, nome_novo, nome_perdido
):
    """RN-P-05: levanta ConflitoDeVersao E nada e gravado."""

    async def cenario():
        await repositorio.salvar_ambiente(ambiente)
        assert ambiente.versao == 1

        obsoleto = copy.deepcopy(ambiente)  # ainda na versao 1

        ambiente.nome = nome_novo
        await repositorio.salvar_ambiente(ambiente)
        assert ambiente.versao == 2

        obsoleto.nome = nome_perdido
        with pytest.raises(ConflitoDeVersao):
            await repositorio.salvar_ambiente(obsoleto)

        carregado = await repositorio.carregar_ambiente(ambiente.id)
        assert carregado.nome == nome_novo
        assert carregado.versao == 2

    executar(cenario())


# --------------------------------------------------------------------------
# PBT-U2-04 e PBT-U2-05 - transcricao
# --------------------------------------------------------------------------


@given(
    textos=st.lists(st.text(max_size=30), min_size=1, max_size=12),
    limite=st.integers(min_value=1, max_value=15),
)
@settings(max_examples=40)
def test_pbt_u2_04_limite_ordem_e_as_mais_recentes(repositorio, textos, limite):
    """RN-P-13: min(limite, n) itens, crescentes, e sao os mais recentes."""
    id_chat = Identidade.nova()

    async def cenario():
        ambiente = await _ambiente_salvo(repositorio)
        for texto in textos:
            await repositorio.inserir_mensagem(
                ambiente.id, id_chat, "usuario", texto, False
            )

        pagina = await repositorio.listar_mensagens(id_chat, limite)

        assert len(pagina) == min(limite, len(textos))
        assert [m.id.valor for m in pagina] == sorted(m.id.valor for m in pagina)
        assert [m.texto for m in pagina] == textos[-len(pagina) :]

    executar(cenario())


@given(
    textos=st.lists(st.text(max_size=20), min_size=1, max_size=15),
    limite=st.integers(min_value=1, max_value=4),
)
@settings(max_examples=40)
def test_pbt_u2_05_paginar_reconstroi_a_transcricao_inteira(repositorio, textos, limite):
    """RN-P-14: sem repeticao e sem lacuna."""
    id_chat = Identidade.nova()

    async def cenario():
        ambiente = await _ambiente_salvo(repositorio)
        for texto in textos:
            await repositorio.inserir_mensagem(
                ambiente.id, id_chat, "agente", texto, False
            )

        reconstruida = []
        cursor = None
        while True:
            pagina = await repositorio.listar_mensagens(id_chat, limite, antes_de=cursor)
            if not pagina:
                break
            reconstruida = list(pagina) + reconstruida
            cursor = pagina[0].id

        ids = [m.id.valor for m in reconstruida]
        assert len(set(ids)) == len(ids)  # sem repeticao
        assert [m.texto for m in reconstruida] == textos  # sem lacuna

    executar(cenario())


@given(texto=st.text(max_size=30), parcial=st.text(max_size=30))
@settings(max_examples=25)
def test_rn_p_17_e_rn_p_18_em_andamento_e_preservado(repositorio, texto, parcial):
    """RN-P-17: nada limpa mensagem orfa; o texto parcial fica como esta."""
    id_chat = Identidade.nova()

    async def cenario():
        ambiente = await _ambiente_salvo(repositorio)
        id_mensagem = await repositorio.inserir_mensagem(
            ambiente.id, id_chat, "agente", parcial, True
        )
        [antes] = await repositorio.listar_mensagens(id_chat, 10)
        assert antes.em_andamento is True
        assert antes.texto == parcial

        await repositorio.atualizar_mensagem(id_mensagem, texto, False)
        [depois] = await repositorio.listar_mensagens(id_chat, 10)

        assert depois.id == antes.id  # a ordem nao muda
        assert depois.papel == antes.papel
        assert depois.criada_em == antes.criada_em
        assert depois.texto == texto
        assert depois.em_andamento is False

    executar(cenario())


def test_mensagem_inexistente_levanta_nas_duas_implementacoes(repositorio):
    """Aqui a ausencia E defeito, ao contrario de carregar_ambiente (RN-P-04)."""

    async def cenario():
        fantasma = Identidade.nova()
        with pytest.raises(MensagemInexistente):
            await repositorio.atualizar_mensagem(fantasma, "texto", False)
        with pytest.raises(MensagemInexistente):
            await repositorio.registrar_uso_ferramenta(fantasma, "ler", "{}")

    executar(cenario())


def test_rn_p_04_id_ausente_devolve_none(repositorio):
    """Ausencia e resultado, nao erro."""
    assert executar(repositorio.carregar_ambiente(Identidade.nova())) is None


# --------------------------------------------------------------------------
# PBT-U2-07 - exclusao
# --------------------------------------------------------------------------


@given(ambiente=est.ambientes(), roteiro=est.roteiros_de_anotacao())
@settings(max_examples=25)
def test_pbt_u2_07_apagar_nao_deixa_orfao(repositorio, ambiente, roteiro):
    """RN-P-20, so por comportamento observavel - a inspecao das tabelas do
    adaptador real esta em test_sqlite.py, que e onde ela pode existir."""

    async def cenario():
        await repositorio.salvar_ambiente(ambiente)
        id_chat = Identidade.nova()
        id_mensagem = await repositorio.inserir_mensagem(
            ambiente.id, id_chat, "usuario", "oi", False
        )
        await repositorio.registrar_uso_ferramenta(id_mensagem, "ler", "{}")
        for sessao, chave, anotacao in _anotar_roteiro(ambiente, roteiro):
            await repositorio.anotar(ambiente.id, sessao.id, chave, anotacao)

        await repositorio.apagar_ambiente(ambiente.id)

        assert await repositorio.carregar_ambiente(ambiente.id) is None
        assert await repositorio.listar_mensagens(id_chat, 50) == []

        # As anotacoes tambem foram: reinserido o mesmo ambiente, a memoria
        # volta vazia em vez de ressuscitar o que estava la.
        ressuscitado = copy.deepcopy(ambiente)
        ressuscitado.versao = 0
        for sessao in est.sessoes_de(ressuscitado):
            sessao.memoria.anotacoes = {}
            sessao.memoria.versao = 0
        await repositorio.salvar_ambiente(ressuscitado)

        carregado = await repositorio.carregar_ambiente(ambiente.id)
        assert all(t.memoria.total_de_anotacoes() == 0 for t in est.sessoes_de(carregado))

    executar(cenario())


def test_rn_p_22_apagar_id_inexistente_e_no_op(repositorio):
    executar(repositorio.apagar_ambiente(Identidade.nova()))


def test_salvar_ambiente_apagado_por_outra_instancia_levanta(repositorio):
    """Decisao tomada na geracao: linha ausente com versao > 0 e conflito, nao
    insercao. Inserir aqui ressuscitaria um ambiente que alguem removeu de
    proposito - a escrita cega que RN-P-05 existe para impedir."""

    async def cenario():
        ambiente = await _ambiente_salvo(repositorio)
        await repositorio.apagar_ambiente(ambiente.id)

        assert ambiente.versao == 1
        with pytest.raises(ConflitoDeVersao):
            await repositorio.salvar_ambiente(ambiente)

    executar(cenario())


# --------------------------------------------------------------------------
# PBT-U2-08 - o teste diferencial
# --------------------------------------------------------------------------

_OPERACOES = st.one_of(
    st.tuples(st.just("salvar")),
    st.tuples(st.just("carregar")),
    st.tuples(st.just("anotar"), st.integers(0, 4), est.texto_nao_vazio, st.text(max_size=15)),
    st.tuples(st.just("inserir"), st.text(max_size=15), st.booleans()),
    st.tuples(st.just("atualizar"), st.integers(0, 4), st.text(max_size=15), st.booleans()),
    st.tuples(st.just("uso"), st.integers(0, 4), est.texto_nao_vazio),
    st.tuples(st.just("listar"), st.integers(1, 5)),
    st.tuples(st.just("apagar")),
)

# O roteiro roda duas vezes, uma em cada implementacao, e os Ambiente
# carregados sao comparados - com as anotacoes dentro. Um datetime.now() por
# execucao fazia `criada_em` diferir em microssegundos entre as duas.
_INSTANTE_DO_ROTEIRO = datetime(2026, 1, 1, tzinfo=UTC)


async def _rodar_roteiro(repositorio, ambiente, id_chat, operacoes):
    """Executa a sequencia e devolve o observavel de cada passo.

    O que entra na comparacao e o que o contrato promete: textos, papeis,
    marcas, memoria, versao e o TIPO do erro. Fica de fora o que a porta nunca
    prometeu ser igual - identidades geradas e carimbos de tempo do
    armazenamento.
    """
    observado = []
    mensagens: list[Identidade] = []

    for operacao in operacoes:
        nome = operacao[0]
        try:
            if nome == "salvar":
                await repositorio.salvar_ambiente(ambiente)
                observado.append(("salvar", ambiente.versao))

            elif nome == "carregar":
                observado.append(("carregar", await repositorio.carregar_ambiente(ambiente.id)))

            elif nome == "anotar":
                sessoes = est.sessoes_de(ambiente)
                if not sessoes:
                    observado.append(("anotar", "sem sessao"))
                    continue
                sessao = sessoes[operacao[1] % len(sessoes)]
                anotacao = Anotacao(
                    autor="agente", valor=operacao[3], criada_em=_INSTANTE_DO_ROTEIRO
                )
                await repositorio.anotar(ambiente.id, sessao.id, operacao[2], anotacao)
                observado.append(("anotar", None))

            elif nome == "inserir":
                mensagens.append(
                    await repositorio.inserir_mensagem(
                        ambiente.id, id_chat, "agente", operacao[1], operacao[2]
                    )
                )
                observado.append(("inserir", len(mensagens)))

            elif nome == "atualizar":
                if not mensagens:
                    observado.append(("atualizar", "sem mensagem"))
                    continue
                alvo = mensagens[operacao[1] % len(mensagens)]
                await repositorio.atualizar_mensagem(alvo, operacao[2], operacao[3])
                observado.append(("atualizar", None))

            elif nome == "uso":
                if not mensagens:
                    observado.append(("uso", "sem mensagem"))
                    continue
                alvo = mensagens[operacao[1] % len(mensagens)]
                await repositorio.registrar_uso_ferramenta(alvo, operacao[2], "{}")
                observado.append(("uso", None))

            elif nome == "listar":
                pagina = await repositorio.listar_mensagens(id_chat, operacao[1])
                observado.append(
                    (
                        "listar",
                        [
                            (
                                m.papel,
                                m.texto,
                                m.em_andamento,
                                tuple((u.tool, u.args_resumo) for u in m.usos_de_ferramenta),
                            )
                            for m in pagina
                        ],
                    )
                )

            elif nome == "apagar":
                await repositorio.apagar_ambiente(ambiente.id)
                mensagens.clear()
                observado.append(("apagar", None))

        except ErroDePersistencia as erro:
            observado.append((nome, "erro", type(erro).__name__))

    return observado


@given(
    ambiente=est.ambientes(),
    operacoes=st.lists(_OPERACOES, min_size=1, max_size=12),
)
@settings(max_examples=30)
def test_pbt_u2_08_as_duas_implementacoes_concordam(tmp_path, ambiente, operacoes):
    """RN-P-25 e RN-P-26: mesmo resultado observavel, inclusive os mesmos erros.

    Se duble e real fossem o mesmo codigo, esta propriedade passaria por
    construcao. Sao dois codigos independentes: quando discordam, quem estava
    ambiguo era o contrato.
    """
    id_chat = Identidade.nova()

    real = executar(abrir_repositorio(tmp_path / "diferencial.db"))
    try:
        observado_real = executar(
            _rodar_roteiro(real, copy.deepcopy(ambiente), id_chat, operacoes)
        )
    finally:
        executar(real.fechar())

    observado_falso = executar(
        _rodar_roteiro(RepositorioEmMemoria(), copy.deepcopy(ambiente), id_chat, operacoes)
    )

    assert observado_real == observado_falso
