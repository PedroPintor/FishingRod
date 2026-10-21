"""U5 - as 10 propriedades (PBT-U5-01..10), como o plano de CG as fixou na
secao 4: geracao, verificacao e numero de exemplos.

Cada exemplo roda o cenario inteiro numa corrotina so (`executar`), sobre o
ServicoDeAmbiente real e o RepositorioEmMemoria. Encolhimento e semente ficam no
padrao do Hypothesis (perfil `fishingrod`).
"""

import pytest
from hypothesis import event, given, settings
from hypothesis import strategies as st

from fishingrod.aplicacao.catalogo.catalogo import comando_de, nome_de
from fishingrod.aplicacao.catalogo.parser import ComandoDigitado, ParserDeComando
from fishingrod.aplicacao.catalogo.registro import ACOES
from fishingrod.aplicacao.catalogo.tipos import Acionamento, MotivoFalha, Resultado
from fishingrod.dominio import Chamador, ExecutorEtapa
from tests.acoes.estrategias import (
    BIBLIOTECARIO,
    RESPOSTAS_QUE_NAO_CONFIRMAM,
    NOMES_DAS_ACOES,
    NOMES_DAS_ACOES_DO_AGENTE,
    ORQUESTRADOR,
    REGISTRO,
    acionamentos,
    acionamentos_de_agente,
    alvo_da_tarefa,
    alvos_quaisquer,
    ambientes_de_partida,
    ambientes_de_uma_tarefa,
    argumentos_quaisquer,
    entradas_validas,
    erros_da_tabela,
    executar,
    linhas_de,
    lugares_de_sabotagem,
    montar,
    nomes_de_comando,
    nomes_quaisquer,
    ponderado,
    passos,
    respostas,
    casos_de_violacao,
    separadores,
    tarefa_com_etapas,
    tarefas_de,
    textos_da_barra,
    textos_livres,
    violacoes,
)
from tests.acoes.instrumentos import (
    ConfirmacaoFixa,
    ConfirmacaoProibida,
    ConfirmacaoQueLevanta,
    ServicoEspiao,
    ServicoSabotado,
)
from tests.acoes.modelo import chamada_de_u4, devolvido_para_u4, forma, prever
from tests.ambiente.modelo import ModeloDeAmbientes, projetar

parser = ParserDeComando()
USUARIO = Acionamento.usuario()


def _invariantes(resultado: object) -> None:
    """RN-AC-35, verificadas de fora - alem de o proprio Resultado recusar a
    construcao que as quebra."""
    assert isinstance(resultado, Resultado)
    assert resultado.sucesso == (resultado.motivo is None)
    if resultado.sucesso:
        assert dict(resultado.detalhe) == {}
    else:
        assert resultado.dado is None
        assert all(isinstance(c, str) and isinstance(v, str) for c, v in resultado.detalhe.items())


def _chamada_esperada(acao: str, alvo, valores: dict, tarefa, autor: str) -> tuple:
    """A operacao de U4, com os argumentos exatos, que o servico deve receber."""
    match acao:
        case "criar_frente":
            return ("criar_frente", (alvo.id_ambiente, valores["nome"]))
        case "criar_tarefa":
            return ("criar_tarefa", (alvo.id_ambiente, alvo.id_frente, valores["nome"]))
        case "criar_sessao":
            return ("criar_sessao", (alvo.id_ambiente, alvo.id_tarefa, valores.get("nome", "")))
        case "criar_chat":
            return (
                "criar_chat",
                (alvo.id_ambiente, alvo.id_sessao, valores["agente"], valores.get("nome", "")),
            )
        case "criar_etapa":
            return (
                "criar_etapa",
                (alvo.id_ambiente, alvo.id_tarefa, valores["descricao"], ExecutorEtapa(valores["executor"])),
            )
        case "concluir_etapa":
            return ("concluir_etapa", (alvo.id_ambiente, tarefa.etapas[valores["posicao"] - 1].id))
        case "anotar_memoria":
            return (
                "anotar_memoria",
                (alvo.id_ambiente, alvo.id_sessao, valores["chave"], valores["valor"], autor),
            )
    raise AssertionError(acao)


# --------------------------------------------------------------------------
# PBT-U5-01 e 02: ida e volta (PBT-02)
# --------------------------------------------------------------------------


@settings(max_examples=200)
@given(nome=nomes_de_comando, texto=st.just("") | textos_livres())
def test_pbt_u5_01_ida_e_volta_do_parser(nome, texto):
    comando = ComandoDigitado(nome, texto)

    assert parser.interpretar(parser.formatar(comando)) == comando


@settings(max_examples=200)
@given(resto=st.text(max_size=30))
def test_pbt_u5_01_toda_linha_com_barra_e_interpretada(resto):
    """O outro lado da ida e volta: para todo texto que comeca com `/`,
    interpretar nunca levanta, e o que ele devolve esta no dominio em que
    formatar e a inversa."""
    comando = parser.interpretar("/" + resto)

    assert not any(c.isspace() for c in comando.nome)
    assert comando.texto == comando.texto.strip()
    assert parser.interpretar(parser.formatar(comando)) == comando


_NOMES_SNAKE = st.from_regex(r"[a-z][a-z0-9]{0,6}(_[a-z0-9]{1,6}){0,3}", fullmatch=True)


@settings(max_examples=100)
@given(
    nome=_NOMES_SNAKE,
    texto=st.text(max_size=20)
    | st.sampled_from([comando_de(n) for n in NOMES_DAS_ACOES])
    | st.sampled_from(NOMES_DAS_ACOES),
)
def test_pbt_u5_02_nome_e_comando(nome, texto):
    assert nome_de(comando_de(nome)) == nome
    assert "_" not in comando_de(nome)
    # nenhum texto de comando acha mais de uma acao - e a que ele acha e
    # exatamente a de comando igual a ele (G7)
    achadas = [acao for acao in ACOES if nome_de(texto) == acao.nome]
    assert len(achadas) <= 1
    assert all(comando_de(acao.nome) == texto for acao in achadas)


# --------------------------------------------------------------------------
# PBT-U5-03: nunca levanta (PBT-03)
# --------------------------------------------------------------------------


def _porta_qualquer(dados):
    """Uma resposta qualquer da porta, ou uma porta que levanta um erro da
    tabela (R-CG5-5)."""
    if dados.draw(st.booleans(), label="porta_levanta"):
        erro, _ = dados.draw(erros_da_tabela, label="erro_da_porta")
        return ConfirmacaoQueLevanta(lambda: erro("porta"))
    return ConfirmacaoFixa(dados.draw(respostas, label="resposta"))


@settings(max_examples=150)
@given(ambiente=ambientes_de_partida(), dados=st.data())
def test_pbt_u5_03_nunca_levanta(tmp_path, ambiente, dados):
    """Tres modos. `valida`: tudo certo e a porta diz sim -
    sem sabotagem e sucesso, com sabotagem e o motivo da tabela. `quase`: acao
    e argumentos validos, mas alvo, quem aciona e porta quaisquer - e o que
    leva aos passos 5 e 6. `qualquer`: lixo em tudo.

    [Endurecido no passo 17] Com dois modos, sorteados por booleano, so ~21%
    dos exemplos eram validos, e o lixo parava no passo 4: alvo inexistente,
    recusa e porta que levanta nao apareciam nenhuma vez. `quase` vem primeiro e
    com peso dobrado, e nele o agente vem antes do usuario: e o unico modo que
    chega a RECUSADA, e o Hypothesis favorece a primeira opcao de cada sorteio.
    """
    modo = dados.draw(
        ponderado((2, st.just("quase")), (1, st.just("valida")), (1, st.just("qualquer"))), label="modo"
    )
    pela_barra = dados.draw(st.booleans(), label="pela_barra")
    sabotagem = dados.draw(st.none() | st.tuples(erros_da_tabela, lugares_de_sabotagem), label="sabotagem")

    if modo == "qualquer":
        alvo = dados.draw(alvos_quaisquer(ambiente), label="alvo")
        nome = dados.draw(nomes_quaisquer, label="nome")
        argumentos = dados.draw(argumentos_quaisquer, label="argumentos")
        comando = dados.draw(
            nomes_de_comando | st.sampled_from([comando_de(n) for n in NOMES_DAS_ACOES]), label="comando"
        )
        linha = "/" + comando + dados.draw(st.just("") | separadores) + dados.draw(textos_da_barra)
        acionamento = dados.draw(acionamentos, label="acionamento")
        porta = _porta_qualquer(dados)
    else:
        frente, tarefa = tarefa_com_etapas(ambiente)
        acao = REGISTRO[dados.draw(st.sampled_from(NOMES_DAS_ACOES), label="acao")]
        entrada = dados.draw(entradas_validas(acao, etapas=len(tarefa.etapas)), label="entrada")
        nome, argumentos = acao.nome, entrada.escritos
        linha = dados.draw(linhas_de(entrada), label="linha")
        if modo == "valida":
            alvo = alvo_da_tarefa(ambiente, frente, tarefa)
            # criar_sessao e so do usuario (D21): pelo agente, seria NAO_PERMITIDA.
            so_usuario = Chamador.AGENTE not in acao.chamadores
            acionamento = USUARIO if pela_barra or so_usuario else dados.draw(acionamentos, label="acionamento")
            porta = ConfirmacaoFixa(True)
        else:
            alvo = dados.draw(alvos_quaisquer(ambiente), label="alvo")
            acionamento = dados.draw(acionamentos_de_agente | st.just(USUARIO), label="acionamento")
            porta = _porta_qualquer(dados)

    def instrumento(servico):
        if sabotagem is None:
            return ServicoEspiao(servico)
        (erro, _), onde = sabotagem
        return ServicoSabotado(servico, lambda: erro("sabotado"), onde)

    async def cenario():
        m = await montar(tmp_path, ambiente, porta, instrumento=instrumento)
        if pela_barra:
            return await m.catalogo.executar_comando(parser.interpretar(linha), alvo)
        return await m.catalogo.executar(nome, alvo, argumentos, acionamento)

    resultado = executar(cenario())

    _invariantes(resultado)
    event(f"motivo: {resultado.motivo.value if resultado.motivo else 'sucesso'}")
    event(f"modo: {modo}")
    if modo == "valida":
        if sabotagem is None:
            assert resultado.sucesso, resultado
        else:
            # entrada valida e sabotagem no passo 5 ou no 7: o motivo e o da
            # tabela de domain-entities.md 5.3
            assert resultado.motivo is sabotagem[0][1], (sabotagem, resultado)


# --------------------------------------------------------------------------
# PBT-U5-04: TD-11 (PBT-03)
# --------------------------------------------------------------------------


# [Endurecido no passo 17] As propriedades "por acao" sao parametrizadas pela
# acao, e nao sorteadas: sorteando, o Hypothesis favorecia as primeiras do
# registro, e PBT-U5-04 rodou 100 exemplos sem nenhum anotar_memoria. O total
# de exemplos e 7 x 17 = 119.
@pytest.mark.parametrize("nome_acao", NOMES_DAS_ACOES)
@settings(max_examples=17)
@given(ambiente=ambientes_de_partida(), dados=st.data())
def test_pbt_u5_04_td_11_o_servico_recebe_exatamente_o_que_foi_digitado(
    tmp_path, nome_acao, ambiente, dados
):
    frente, tarefa = tarefa_com_etapas(ambiente)
    alvo = alvo_da_tarefa(ambiente, frente, tarefa)
    acao = REGISTRO[nome_acao]
    entrada = dados.draw(entradas_validas(acao, etapas=len(tarefa.etapas)), label="entrada")
    linha = dados.draw(linhas_de(entrada), label="linha")

    async def cenario():
        m = await montar(tmp_path, ambiente, ConfirmacaoProibida(), instrumento=ServicoEspiao)
        resultado = await m.catalogo.executar_comando(parser.interpretar(linha), alvo)
        return resultado, m.visto.mudancas()

    resultado, mudancas = executar(cenario())

    assert resultado.sucesso, resultado
    # a opcao na forma canonica, a posicao como o id da etapa, e o ultimo com
    # os espacos de dentro intactos
    assert mudancas == [_chamada_esperada(acao.nome, alvo, entrada.esperados, tarefa, "usuario")]


# --------------------------------------------------------------------------
# PBT-U5-05: falha fechada (PBT-03)
# --------------------------------------------------------------------------


LEVANTA = "a porta levanta"


# Por acao do agente e por resposta: 6 x 9 = 54 combinacoes, 2 exemplos cada
# (108) - criar_sessao fica de fora, porque o agente nao chega a pergunta. As
# respostas que um `if resposta:` deixaria passar - 1, "sim", "True" - nao
# dependem da sorte.
@pytest.mark.parametrize("resposta", [*RESPOSTAS_QUE_NAO_CONFIRMAM, LEVANTA], ids=repr)
@pytest.mark.parametrize("nome_acao", NOMES_DAS_ACOES_DO_AGENTE)
@settings(max_examples=2)
@given(ambiente=ambientes_de_partida(), dados=st.data())
def test_pbt_u5_05_falha_fechada(tmp_path, nome_acao, resposta, ambiente, dados):
    frente, tarefa = tarefa_com_etapas(ambiente)
    alvo = alvo_da_tarefa(ambiente, frente, tarefa)
    acao = REGISTRO[nome_acao]
    entrada = dados.draw(entradas_validas(acao, etapas=len(tarefa.etapas)), label="entrada")
    acionamento = dados.draw(acionamentos_de_agente, label="acionamento")
    levanta = resposta is LEVANTA
    if levanta:
        # inclusive um erro de tipo conhecido da tabela (R-CG5-5)
        erro, _ = dados.draw(erros_da_tabela, label="erro_da_porta")
        porta = ConfirmacaoQueLevanta(lambda: erro("porta"))
    else:
        porta = ConfirmacaoFixa(resposta)

    async def cenario():
        m = await montar(tmp_path, ambiente, porta, instrumento=ServicoEspiao)
        aberto = await m.aberto(ambiente.id)
        antes = (forma(aberto), aberto.versao)
        resultado = await m.catalogo.executar(acao.nome, alvo, entrada.escritos, acionamento)
        aberto = await m.aberto(ambiente.id)
        no_disco = await m.repositorio.carregar_ambiente(ambiente.id)
        return resultado, antes, (forma(aberto), aberto.versao), (forma(no_disco), no_disco.versao), m.visto.mudancas()

    resultado, antes, depois, no_disco, mudancas = executar(cenario())

    assert mudancas == []
    assert depois == antes == no_disco
    assert resultado.motivo is (MotivoFalha.FALHA_INESPERADA if levanta else MotivoFalha.RECUSADA)
    assert len(porta.pedidos) == 1


# --------------------------------------------------------------------------
# PBT-U5-06: oraculo com sequencia (PBT-05, PBT-06)
# --------------------------------------------------------------------------


@settings(max_examples=60)
@given(ambiente=ambientes_de_partida(), dados=st.data())
def test_pbt_u5_06_sequencia_de_comandos_contra_o_modelo_de_u4(tmp_path, ambiente, dados):
    modelo = ModeloDeAmbientes()
    modelo.acrescentar(ambiente)
    porta = ConfirmacaoProibida()

    async def cenario():
        m = await montar(tmp_path, ambiente, porta)
        for _ in range(dados.draw(st.integers(min_value=0, max_value=15), label="tamanho")):
            passo = dados.draw(passos(modelo.ambientes[ambiente.id]), label="passo")
            motivo, detalhe = prever(passo, modelo)

            resultado = await passo.executar(m.catalogo)

            event(f"motivo: {motivo.value if motivo else 'sucesso'}")
            event("pela barra" if passo.linha is not None else "por argumentos")
            assert (resultado.motivo, dict(resultado.detalhe)) == (motivo, detalhe), passo
            if resultado.sucesso:
                chamada = chamada_de_u4(passo, modelo, "usuario")
                assert modelo.prever(chamada) is None  # o oraculo de U4 concorda
                modelo.aplicar(chamada, devolvido_para_u4(resultado.dado))
            # depois de CADA comando, e nao so no fim
            assert projetar(await m.aberto(ambiente.id)) == modelo.ambientes[ambiente.id]

    executar(cenario())

    assert not porta.perguntou


# --------------------------------------------------------------------------
# PBT-U5-07: confirmado e igual a usuario (PBT-05)
# --------------------------------------------------------------------------


@pytest.mark.parametrize("nome_acao", NOMES_DAS_ACOES_DO_AGENTE)
@settings(max_examples=10)
@given(ambiente=ambientes_de_partida(), dados=st.data())
def test_pbt_u5_07_agente_com_sim_e_igual_a_usuario(tmp_path, nome_acao, ambiente, dados):
    frente, tarefa = tarefa_com_etapas(ambiente)
    alvo = alvo_da_tarefa(ambiente, frente, tarefa)
    acao = REGISTRO[nome_acao]
    entrada = dados.draw(entradas_validas(acao, etapas=len(tarefa.etapas)), label="entrada")
    agente = dados.draw(st.sampled_from([ORQUESTRADOR.nome, BIBLIOTECARIO.nome]), label="agente")
    porta = ConfirmacaoFixa(True)

    async def cenario():
        pelo_agente = await montar(tmp_path, ambiente, porta)
        pelo_usuario = await montar(tmp_path, ambiente, ConfirmacaoProibida())
        do_agente = await pelo_agente.catalogo.executar(
            acao.nome, alvo, entrada.escritos, Acionamento.agente(agente)
        )
        do_usuario = await pelo_usuario.catalogo.executar(acao.nome, alvo, entrada.escritos, USUARIO)
        trocar = lambda autor: "usuario" if autor == agente else autor  # noqa: E731
        return (
            do_agente,
            do_usuario,
            forma(await pelo_agente.aberto(ambiente.id), autor=trocar),
            forma(await pelo_usuario.aberto(ambiente.id)),
        )

    do_agente, do_usuario, forma_agente, forma_usuario = executar(cenario())

    assert do_agente.sucesso and do_usuario.sucesso
    assert forma_agente == forma_usuario
    assert len(porta.pedidos) == 1
    if acao.nome == "anotar_memoria":
        assert (do_agente.dado.autor, do_usuario.dado.autor) == (agente, "usuario")


# --------------------------------------------------------------------------
# PBT-U5-08: posicao (PBT-03)
# --------------------------------------------------------------------------


@settings(max_examples=60)
@given(ambiente=ambientes_de_uma_tarefa(), dados=st.data())
def test_pbt_u5_08_posicao(tmp_path, ambiente, dados):
    [(frente, tarefa)] = tarefas_de(ambiente)
    total = len(tarefa.etapas)
    alvo = alvo_da_tarefa(ambiente, frente, tarefa)
    k = dados.draw(st.integers(min_value=-2, max_value=total + 3), label="k")
    escrito = dados.draw(st.sampled_from([k, str(k)]), label="escrito")
    pela_barra = dados.draw(st.booleans(), label="pela_barra")

    async def cenario():
        m = await montar(tmp_path, ambiente, ConfirmacaoProibida(), instrumento=ServicoEspiao)
        if pela_barra:
            resultado = await m.catalogo.executar_comando(
                parser.interpretar(f"/concluir-etapa {escrito}"), alvo
            )
        else:
            resultado = await m.catalogo.executar("concluir_etapa", alvo, {"posicao": escrito}, USUARIO)
        depois = (await m.aberto(ambiente.id)).frentes[0].tarefas[0].etapas
        return resultado, [(e.id, e.concluida) for e in depois], m.visto.mudancas()

    resultado, depois, mudancas = executar(cenario())

    antes = [(e.id, e.concluida) for e in tarefa.etapas]
    event("dentro" if 1 <= k <= total else ("alem do fim" if k > total else "menor que 1"))
    event("como texto" if isinstance(escrito, str) else "como int")
    if 1 <= k <= total:
        assert resultado.sucesso and resultado.dado.posicao == k
        esperado = list(antes)
        esperado[k - 1] = (antes[k - 1][0], True)
        assert depois == esperado  # so a k-esima mudou
    elif k > total:
        assert (resultado.motivo, dict(resultado.detalhe)) == (
            MotivoFalha.ALVO_INEXISTENTE,
            {"alvo": "etapa", "posicao": str(k), "total": str(total)},
        )
        assert (depois, mudancas) == (antes, [])
    else:
        assert (resultado.motivo, dict(resultado.detalhe)) == (
            MotivoFalha.ARGUMENTO_INVALIDO,
            {"parametro": "posicao", "problema": "tipo"},
        )
        assert (depois, mudancas) == (antes, [])


# --------------------------------------------------------------------------
# PBT-U5-09: idempotencia (PBT-04)
# --------------------------------------------------------------------------


@settings(max_examples=40)
@given(ambiente=ambientes_de_uma_tarefa(minimo=1, maximo=4), dados=st.data())
def test_pbt_u5_09_concluir_de_novo_e_o_mesmo_que_uma_vez(tmp_path, ambiente, dados):
    [(frente, tarefa)] = tarefas_de(ambiente)
    alvo = alvo_da_tarefa(ambiente, frente, tarefa)
    posicao = dados.draw(st.integers(min_value=1, max_value=len(tarefa.etapas)), label="posicao")
    vezes = dados.draw(st.integers(min_value=1, max_value=3), label="vezes")

    async def cenario():
        m = await montar(tmp_path, ambiente, ConfirmacaoProibida())
        uma_vez = None
        resultados = []
        for _ in range(vezes):
            resultados.append(
                await m.catalogo.executar("concluir_etapa", alvo, {"posicao": posicao}, USUARIO)
            )
            if uma_vez is None:
                uma_vez = forma(await m.aberto(ambiente.id))
        return resultados, uma_vez, forma(await m.aberto(ambiente.id))

    resultados, uma_vez, depois = executar(cenario())

    assert all(r.sucesso and r.dado.posicao == posicao for r in resultados)
    assert depois == uma_vez


# --------------------------------------------------------------------------
# PBT-U5-10: validacao antes de tudo (PBT-03)
# --------------------------------------------------------------------------


# Por acao e por tipo de violacao que cabe nela: 36 pares, 3 exemplos cada
# (108). Sorteando, `opcao` - que so existe em criar_etapa - nunca aparecia.
_PARES_DE_VIOLACAO = sorted(
    {
        (nome, tipo)
        for nome in NOMES_DAS_ACOES_DO_AGENTE
        for tipo, _ in casos_de_violacao(REGISTRO[nome])
    }
)


@pytest.mark.parametrize(("nome_acao", "tipo"), _PARES_DE_VIOLACAO)
@settings(max_examples=3)
@given(ambiente=ambientes_de_partida(), dados=st.data())
def test_pbt_u5_10_argumento_ruim_nao_pergunta_nem_le(tmp_path, nome_acao, tipo, ambiente, dados):
    frente, tarefa = tarefa_com_etapas(ambiente)
    alvo = alvo_da_tarefa(ambiente, frente, tarefa)
    acao = REGISTRO[nome_acao]
    violacao = dados.draw(violacoes(acao, tipo), label="violacao")
    acionamento = dados.draw(acionamentos_de_agente, label="acionamento")
    porta = ConfirmacaoProibida()

    async def cenario():
        m = await montar(tmp_path, ambiente, porta, instrumento=ServicoEspiao)
        resultado = await m.catalogo.executar(acao.nome, alvo, violacao.argumentos, acionamento)
        return resultado, m.visto.chamadas

    resultado, chamadas = executar(cenario())

    assert (resultado.motivo, dict(resultado.detalhe)) == (
        MotivoFalha.ARGUMENTO_INVALIDO,
        violacao.detalhe,
    )
    assert not porta.perguntou
    assert chamadas == []  # nem leitura
