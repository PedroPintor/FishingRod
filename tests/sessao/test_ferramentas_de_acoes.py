"""U6 - as acoes do catalogo como ferramentas (US-17, RN-S-46..51, PBT-U6-05..07).

Sempre com o catalogo de U5 DE VERDADE, sobre o ServicoDeAmbiente real (a
montagem de U5): o que se testa aqui e a costura entre o esquema, a amarracao
e o texto que o agente le - e o catalogo e quem decide.
"""

import json
import logging
import re
from datetime import UTC, datetime
from typing import Any

import jsonschema
import pytest
from hypothesis import event, given, settings
from hypothesis import strategies as st

from fishingrod.aplicacao.catalogo.argumentos import MAIOR_POSICAO
from fishingrod.aplicacao.catalogo.catalogo import CatalogoDeAcoes
from fishingrod.aplicacao.catalogo.registro import ACOES
from fishingrod.aplicacao.catalogo.tipos import (
    Acao,
    EtapaNaPosicao,
    MotivoFalha,
    Resultado,
    TipoParametro,
)
from fishingrod.aplicacao.ferramentas import Ferramenta, RegistroDeFerramentas, RespostaDaFerramenta
from fishingrod.aplicacao.ferramentas.acoes import entradas_de_acoes, esquema_de, texto_do_resultado
from fishingrod.aplicacao.portas.sessao import ContextoDaSessao, Familia
from fishingrod.dominio import Anotacao, Chamador, Identidade
from tests.acoes.estrategias import (
    alvo_da_tarefa,
    ambientes_de_uma_tarefa,
    montar,
    tarefas_de,
)
from tests.acoes.instrumentos import ConfirmacaoFixa, ServicoEspiao
from tests.ambiente.estrategias import ambientes_de_partida
from tests.sessao.estrategias import BIBLIOTECARIO, ORQUESTRADOR, executar, parametros_validos, ponderado

REGISTRO = {acao.nome: acao for acao in ACOES}
# As acoes que viram ferramenta: criar_sessao e so do usuario (D21).
ACOES_DO_AGENTE = tuple(acao for acao in ACOES if Chamador.AGENTE in acao.chamadores)


def _ambiente_simples(etapas: int = 0):
    """Uma frente, uma tarefa (com o chat do orquestrador) e `etapas` etapas -
    montado a mao, para o exemplo ser sempre o mesmo."""
    from fishingrod.dominio import Ambiente, ExecutorEtapa

    ambiente = Ambiente("Nexo")
    tarefa = ambiente.criar_frente("Comercial").criar_tarefa("Campanha", ORQUESTRADOR)
    for indice in range(etapas):
        tarefa.criar_etapa(f"etapa {indice + 1}", ExecutorEtapa.AGENTE)
    return ambiente


def _contexto(ambiente, frente, tarefa) -> ContextoDaSessao:
    return ContextoDaSessao(ambiente.id, frente.id, tarefa.id, tarefa.sessoes[0].id, tarefa.sessoes[0].chats[0].id)


def _ferramentas(catalogo: CatalogoDeAcoes, contexto: ContextoDaSessao, agente=ORQUESTRADOR) -> dict[str, Ferramenta]:
    registro = RegistroDeFerramentas(entradas_de_acoes(catalogo))
    quem = agente.__class__(agente.nome, agente.papel, agente.modelo, ferramentas=tuple(e.nome for e in registro.entradas))
    return {f.nome: f for f in registro.preparar(quem, contexto)[Familia.AMBIENTE]}


# --------------------------------------------------------------------------
# As entradas (RN-S-46)
# --------------------------------------------------------------------------


def test_rn_s_46_uma_entrada_por_acao_do_agente_na_ordem_do_registro():
    entradas = entradas_de_acoes(CatalogoDeAcoes(servico=None, confirmacao=None))

    assert [e.nome for e in entradas] == [a.nome for a in ACOES_DO_AGENTE]
    assert "criar_sessao" not in [e.nome for e in entradas]
    assert {e.familia for e in entradas} == {Familia.AMBIENTE}


def test_rn_s_46_acao_so_do_usuario_nao_vira_ferramenta():
    so_do_usuario = Acao(
        "renomear_frente", "Renomeia.", ACOES[0].escopo, ACOES[0].parametros, frozenset({Chamador.USUARIO}), ACOES[0].efetivar
    )
    catalogo = CatalogoDeAcoes(servico=None, confirmacao=None, acoes=(*ACOES, so_do_usuario))

    assert "renomear_frente" not in [e.nome for e in entradas_de_acoes(catalogo)]


def test_rn_s_46_a_ferramenta_tem_o_nome_e_a_descricao_da_acao(tmp_path):
    async def cenario():
        montagem = await montar(tmp_path, None, ConfirmacaoFixa(True))
        contexto = ContextoDaSessao(*(Identidade.nova() for _ in range(5)))
        return _ferramentas(montagem.catalogo, contexto)

    ferramentas = executar(cenario())

    for acao in ACOES_DO_AGENTE:
        assert ferramentas[acao.nome].descricao == acao.descricao
        assert ferramentas[acao.nome].esquema == esquema_de(acao.parametros)


# --------------------------------------------------------------------------
# PBT-U6-05: o esquema e fiel aos parametros
# --------------------------------------------------------------------------


@settings(max_examples=200)
@given(parametros_validos())
def test_pbt_u6_05_esquema_fiel_aos_parametros(parametros):
    esquema = esquema_de(parametros)

    assert set(esquema) == {"type", "properties", "required", "additionalProperties"}
    assert esquema["type"] == "object"
    assert esquema["additionalProperties"] is False
    assert list(esquema["properties"]) == [p.nome for p in parametros]
    assert esquema["required"] == [p.nome for p in parametros if p.obrigatorio]
    for parametro in parametros:
        propriedade = esquema["properties"][parametro.nome]
        assert propriedade["description"] == parametro.descricao
        match parametro.tipo:
            case TipoParametro.TEXTO:
                esperado = {"type", "description", "maxLength"} | ({"minLength", "pattern"} if parametro.obrigatorio else set())
                assert set(propriedade) == esperado
                assert propriedade["type"] == "string"
                assert propriedade["maxLength"] == parametro.maximo
                if parametro.obrigatorio:
                    assert propriedade["minLength"] == 1
                    assert propriedade["pattern"] == r"\S"
            case TipoParametro.ESCOLHA:
                assert set(propriedade) == {"type", "description", "enum"}
                assert propriedade["enum"] == list(parametro.opcoes)
            case TipoParametro.POSICAO:
                assert propriedade == {
                    "type": "integer",
                    "description": parametro.descricao,
                    "minimum": 1,
                    "maximum": MAIOR_POSICAO,
                }
    jsonschema.Draft202012Validator.check_schema(esquema)


# --------------------------------------------------------------------------
# PBT-U6-06: esquema e catalogo concordam
# --------------------------------------------------------------------------


@st.composite
def argumentos_do_esquema(draw: Any, esquema: dict) -> dict[str, object]:
    """Argumentos gerados A PARTIR DO ESQUEMA - e nao dos Parametro -, e
    conferidos com jsonschema antes de usar."""
    argumentos: dict[str, object] = {}
    for nome, propriedade in esquema["properties"].items():
        if nome not in esquema["required"] and draw(st.booleans()):
            continue
        if "enum" in propriedade:
            argumentos[nome] = draw(st.sampled_from(propriedade["enum"]))
        elif propriedade["type"] == "integer":
            argumentos[nome] = draw(
                ponderado(
                    (3, st.integers(propriedade["minimum"], 4)),
                    (1, st.integers(propriedade["minimum"], propriedade["maximum"])),
                    (1, st.just(propriedade["maximum"])),
                )
            )
        else:
            minimo, maximo = propriedade.get("minLength", 0), propriedade["maxLength"]
            texto = draw(
                ponderado(
                    (4, st.text(min_size=minimo, max_size=min(maximo, 30))),
                    (1, st.just("x" * maximo)),
                )
            )
            argumentos[nome] = texto
    try:
        jsonschema.validate(argumentos, esquema)
    except jsonschema.ValidationError:
        # O que o esquema recusa nunca chega ao catalogo (A16): o gerador tenta
        # de novo.
        from hypothesis import reject

        reject()
    return argumentos


# Parametrizado pela acao: medido no passo 25, o sorteio deixava acoes sem o
# caminho de "sim" ou de "nao". 6 x 17 = ~100 exemplos.
@pytest.mark.parametrize("nome", [a.nome for a in ACOES_DO_AGENTE])
@settings(max_examples=17)
@given(st.data(), st.booleans())
def test_pbt_u6_06_esquema_e_catalogo_concordam(tmp_path, nome, data, sim):
    """O catalogo real nunca recusa como ARGUMENTO_INVALIDO o que o esquema
    aceitou. A unica excecao e regra de dominio, que nao cabe num esquema: o
    nome de agente fora da lista fechada de U4 (`fora_da_lista`)."""
    # concluir_etapa precisa de etapas para a posicao apontar alguma.
    ambiente = data.draw(ambientes_de_uma_tarefa(minimo=4 if nome == "concluir_etapa" else 0, maximo=4))
    acao = REGISTRO[nome]
    argumentos = data.draw(argumentos_do_esquema(esquema_de(acao.parametros)))
    if nome == "criar_chat" and data.draw(st.booleans()):
        argumentos["agente"] = BIBLIOTECARIO.nome

    async def cenario():
        montagem = await montar(tmp_path, ambiente, ConfirmacaoFixa(sim))
        frente, tarefa = tarefas_de(ambiente)[0]
        ferramenta = _ferramentas(montagem.catalogo, _contexto(ambiente, frente, tarefa))[nome]
        return await ferramenta.executar(argumentos)

    resposta = executar(cenario())

    lido = json.loads(resposta.texto)
    event(f"{nome} -> {'ok' if lido['ok'] else lido['motivo']}")
    if lido["ok"] is False and lido["motivo"] == MotivoFalha.ARGUMENTO_INVALIDO.value:
        assert (nome, lido["detalhe"]) == ("criar_chat", {"parametro": "agente", "problema": "fora_da_lista"})


# --------------------------------------------------------------------------
# PBT-U6-07: o texto do agente, ida e volta
# --------------------------------------------------------------------------


@st.composite
def resultados(draw: Any, tipo: str) -> tuple[Resultado, Any]:
    """Sucesso com um dos 5 tipos de `dado`, tirado de um ambiente gerado por
    U4 (`ambientes_de_partida` garante uma tarefa com etapa), ou falha com um
    motivo e `detalhe` gerado."""
    ambiente = draw(ambientes_de_partida())
    com_etapas = [(f, t) for f, t in tarefas_de(ambiente) if t.etapas]
    frente, tarefa = draw(st.sampled_from(com_etapas if tipo == "etapa" else tarefas_de(ambiente)))
    match tipo:
        case "frente":
            return Resultado.ok(frente), ambiente
        case "tarefa":
            return Resultado.ok(tarefa), ambiente
        case "sessao":
            return Resultado.ok(draw(st.sampled_from(tarefa.sessoes))), ambiente
        case "chat":
            chats = [chat for sessao in tarefa.sessoes for chat in sessao.chats]
            return Resultado.ok(draw(st.sampled_from(chats))), ambiente
        case "etapa":
            posicao = draw(st.integers(1, len(tarefa.etapas)))
            return Resultado.ok(EtapaNaPosicao(tarefa.etapas[posicao - 1], posicao)), ambiente
        case "anotacao":
            anotacao = Anotacao(draw(st.text(min_size=1, max_size=10)), draw(st.text(max_size=30)), datetime.now(UTC))
            return Resultado.ok(anotacao), ambiente
    detalhe = draw(st.dictionaries(st.text("abcdefghij_", min_size=1, max_size=8), st.text("abcxyz0123 çã", max_size=8), max_size=3))
    return Resultado.falha(MotivoFalha(tipo), **detalhe), ambiente


def _identidades(ambiente) -> list[str]:
    ids = [ambiente.id]
    for frente in ambiente.frentes:
        ids.append(frente.id)
        for tarefa in frente.tarefas:
            ids += [tarefa.id, *(e.id for e in tarefa.etapas)]
            for sessao in tarefa.sessoes:
                ids += [sessao.id, *(c.id for c in sessao.chats)]
    return [str(i) for i in ids]


class _CatalogoFixo:
    """Devolve sempre o mesmo Resultado: o que se testa e a ferramenta, nao o
    catalogo."""

    def __init__(self, resultado: Resultado) -> None:
        self.resultado = resultado

    def listar(self, chamador=None):
        return ACOES[:1]

    async def executar(self, nome, alvo, argumentos, acionamento):
        return self.resultado


# Parametrizado pelo tipo: medido no passo 25, o sorteio deixava Frente em um
# terco dos exemplos e motivos de falha de fora. 16 tipos x 10 = 160 exemplos.
_TIPOS_DE_RESULTADO = ["frente", "tarefa", "sessao", "chat", "etapa", "anotacao", *(m.value for m in MotivoFalha)]


@pytest.mark.parametrize("tipo", _TIPOS_DE_RESULTADO)
@settings(max_examples=10)
@given(st.data())
def test_pbt_u6_07_texto_do_agente_ida_e_volta(tipo, data):
    gerado = data.draw(resultados(tipo))
    resultado, ambiente = gerado
    event("sucesso: " + type(resultado.dado).__name__ if resultado.sucesso else "falha: " + resultado.motivo.value)
    entrada = entradas_de_acoes(_CatalogoFixo(resultado))[0]
    ferramenta = entrada.fabrica(ContextoDaSessao(ambiente.id, ambiente.id, ambiente.id, ambiente.id, ambiente.id), ORQUESTRADOR)

    resposta = executar(ferramenta.executar({}))

    lido = json.loads(resposta.texto)
    assert resposta.texto == texto_do_resultado(resultado)
    assert lido["ok"] is resultado.sucesso
    assert resposta.erro is (not resultado.sucesso)
    if not resultado.sucesso:
        assert lido["motivo"] == resultado.motivo.value
        assert lido["detalhe"] == dict(resultado.detalhe)
    for identidade in _identidades(ambiente):
        assert identidade not in resposta.texto
    # RN-S-50: acento sai como acento. O JSON so escapa caractere de controle
    # (abaixo de U+0020), e e so isso que pode aparecer como \uXXXX.
    assert all(int(codigo, 16) < 0x20 for codigo in re.findall(r"\\u([0-9a-f]{4})", resposta.texto))


def test_rn_s_51_projecao_de_cada_tipo_de_dado():
    from fishingrod.dominio import Agente, Ambiente, ExecutorEtapa, Papel

    ambiente = Ambiente("Nexo")
    frente = ambiente.criar_frente("Comercial")
    tarefa = frente.criar_tarefa("Campanha de verão", ORQUESTRADOR)
    sessao = tarefa.criar_sessao(ORQUESTRADOR, "revisão")
    chat = sessao.criar_chat(Agente("bibliotecario", Papel.SUB_AGENTE, "m"), "Pesquisa")
    etapa = tarefa.criar_etapa("revisar o briefing", ExecutorEtapa.USUARIO)

    assert texto_do_resultado(Resultado.ok(frente)) == '{"ok":true,"frente":{"nome":"Comercial"}}'
    assert texto_do_resultado(Resultado.ok(tarefa)) == '{"ok":true,"tarefa":{"nome":"Campanha de verão"}}'
    assert texto_do_resultado(Resultado.ok(sessao)) == '{"ok":true,"sessao":{"nome":"revisão"}}'
    assert texto_do_resultado(Resultado.ok(chat)) == '{"ok":true,"chat":{"nome":"Pesquisa","agente":"bibliotecario"}}'
    assert texto_do_resultado(Resultado.ok(EtapaNaPosicao(etapa, 3))) == (
        '{"ok":true,"etapa":{"posicao":3,"descricao":"revisar o briefing","executor":"usuario","concluida":false}}'
    )
    assert texto_do_resultado(Resultado.ok(Anotacao("orquestrador", "x" * 20_000, datetime.now(UTC)))) == (
        '{"ok":true,"anotacao":{"autor":"orquestrador"}}'
    )


def test_rn_s_51_dado_desconhecido_vira_ok_e_aviso(caplog):
    with caplog.at_level(logging.WARNING, logger="fishingrod.sessao.ferramentas"):
        texto = texto_do_resultado(Resultado.ok({"segredo": "nao vaza"}))

    assert texto == '{"ok":true}'
    assert [r.levelno for r in caplog.records] == [logging.WARNING]
    assert "dict" in caplog.records[0].getMessage()
    assert "nao vaza" not in caplog.text


# --------------------------------------------------------------------------
# Exemplos de ponta a ponta com o catalogo real
# --------------------------------------------------------------------------


@pytest.mark.parametrize("sim", [True, False], ids=["voce-diz-sim", "voce-diz-nao"])
def test_exemplo_do_business_logic_model_criar_etapa(tmp_path, sim):
    """business-logic-model.md §7: o orquestrador cria uma etapa."""

    async def cenario():
        ambiente = _ambiente_simples(etapas=2)
        montagem = await montar(tmp_path, ambiente, ConfirmacaoFixa(sim), instrumento=ServicoEspiao)
        frente, tarefa = tarefas_de(ambiente)[0]
        ferramenta = _ferramentas(montagem.catalogo, _contexto(ambiente, frente, tarefa))["criar_etapa"]
        resposta = await ferramenta.executar({"executor": "usuario", "descricao": "revisar o briefing"})
        return resposta, montagem.visto.mudancas()

    resposta, mudancas = executar(cenario())

    if sim:
        assert resposta == RespostaDaFerramenta(
            '{"ok":true,"etapa":{"posicao":3,"descricao":"revisar o briefing","executor":"usuario","concluida":false}}'
        )
        assert [m[0] for m in mudancas] == ["criar_etapa"]
    else:
        assert resposta == RespostaDaFerramenta('{"ok":false,"motivo":"recusada","detalhe":{}}', erro=True)
        assert mudancas == []


def test_rn_s_48_anotar_memoria_e_assinada_pelo_nome_do_agente(tmp_path):
    async def cenario():
        ambiente = _ambiente_simples()
        confirmacao = ConfirmacaoFixa(True)
        montagem = await montar(tmp_path, ambiente, confirmacao)
        frente, tarefa = tarefas_de(ambiente)[0]
        ferramenta = _ferramentas(montagem.catalogo, _contexto(ambiente, frente, tarefa))["anotar_memoria"]
        resposta = await ferramenta.executar({"chave": "tom", "valor": "mais formal"})
        aberto = await montagem.aberto(ambiente.id)
        sessao = aberto.buscar_frente(frente.id).buscar_tarefa(tarefa.id).sessoes[0]
        anotacoes = sessao.memoria.anotacoes["tom"]
        return resposta, anotacoes, confirmacao.pedidos

    resposta, anotacoes, pedidos = executar(cenario())

    assert resposta.texto == '{"ok":true,"anotacao":{"autor":"orquestrador"}}'
    assert [(a.autor, a.valor) for a in anotacoes] == [("orquestrador", "mais formal")]
    assert pedidos[0].acionamento.autor == "orquestrador"
    assert pedidos[0].acionamento.chamador is Chamador.AGENTE


def test_rn_s_48_o_modelo_nao_tem_onde_passar_id_nem_autor(tmp_path):
    """Nenhum esquema tem campo de id, alvo ou autor; e um `autor` passado a
    forca e recusado pelo catalogo (o SDK ja o barraria, A16), sem escrever
    nada."""
    for acao in ACOES:
        propriedades = esquema_de(acao.parametros)["properties"]
        assert not any(p.startswith("id") or p in {"alvo", "autor", "acionamento", "chamador"} for p in propriedades)

    async def cenario():
        ambiente = _ambiente_simples()
        montagem = await montar(tmp_path, ambiente, ConfirmacaoFixa(True), instrumento=ServicoEspiao)
        frente, tarefa = tarefas_de(ambiente)[0]
        ferramenta = _ferramentas(montagem.catalogo, _contexto(ambiente, frente, tarefa))["anotar_memoria"]
        resposta = await ferramenta.executar({"chave": "k", "valor": "v", "autor": "usuario"})
        return resposta, montagem.visto.mudancas()

    resposta, mudancas = executar(cenario())

    assert json.loads(resposta.texto) == {
        "ok": False,
        "motivo": "argumento_invalido",
        "detalhe": {"parametro": "autor", "problema": "desconhecido"},
    }
    assert resposta.erro is True
    assert mudancas == []


def test_rn_s_48_o_alvo_vem_do_contexto(tmp_path):
    """Duas sessoes, duas tarefas: cada ferramenta age na tarefa do proprio
    contexto, e o modelo nao consegue apontar outra."""

    async def cenario():
        from fishingrod.dominio import Ambiente

        ambiente = Ambiente("Nexo")
        frente = ambiente.criar_frente("Comercial")
        uma = frente.criar_tarefa("Uma", ORQUESTRADOR)
        outra = frente.criar_tarefa("Outra", ORQUESTRADOR)
        montagem = await montar(tmp_path, ambiente, ConfirmacaoFixa(True))
        ferramenta = _ferramentas(montagem.catalogo, _contexto(ambiente, frente, outra))["criar_etapa"]
        await ferramenta.executar({"executor": "agente", "descricao": "so na outra"})
        aberto = await montagem.aberto(ambiente.id)
        return [t.nome for t in aberto.buscar_frente(frente.id).tarefas if t.etapas], uma.nome

    com_etapa, _ = executar(cenario())

    assert com_etapa == ["Outra"]


def test_alvo_da_tarefa_e_o_mesmo_do_contexto():
    """O Alvo que a fabrica monta e o mesmo que U5 usa para a tarefa do chat
    (RN-AC-11)."""
    ambiente = _ambiente_simples()
    frente, tarefa = tarefas_de(ambiente)[0]
    contexto = _contexto(ambiente, frente, tarefa)
    alvo = alvo_da_tarefa(ambiente, frente, tarefa)

    assert (contexto.id_ambiente, contexto.id_frente, contexto.id_tarefa) == (alvo.id_ambiente, alvo.id_frente, alvo.id_tarefa)
