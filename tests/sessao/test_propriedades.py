"""U6 - as propriedades de ponta a ponta (PBT-U6-01, 03, 09, 10, 11 e 12).

Sempre no adaptador REAL, com o cliente roteirizado no lugar do CLI. O
oraculo dos motivos e a tabela literal de test_falhas.py, nunca `classificar`;
o do ciclo de vida e o ModeloDeSessoes. Nenhuma propriedade chama o provedor.
"""

import asyncio
import json
from pathlib import Path
from typing import Any

import pytest
from claude_agent_sdk import ClaudeAgentOptions, CLIConnectionError, TextBlock
from hypothesis import event, given, settings
from hypothesis import strategies as st

from fishingrod.adaptadores.sessao.adaptador import AdaptadorSessaoClaude, Estado
from fishingrod.adaptadores.sessao.falhas import ErroDoAssistente, Fase
from fishingrod.aplicacao.ferramentas import RegistroDeFerramentas
from fishingrod.aplicacao.ferramentas.acoes import entradas_de_acoes
from fishingrod.aplicacao.portas.sessao import (
    AdaptadorEncerrado,
    ContextoDaSessao,
    FalhaDoTurno,
    FimDeTurno,
    MensagemEntregue,
    MotivoFalhaDeSessao as M,
    PedacoDeTexto,
    UsoDeFerramenta,
)
from tests.acoes.estrategias import ambientes_de_uma_tarefa, montar, tarefas_de
from tests.acoes.instrumentos import ServicoEspiao
from tests.sessao.cliente_roteirizado import (
    Bem,
    ChamarFerramenta,
    FabricaRoteirizada,
    Falha,
    Lento,
    Levantar,
    Mensagem,
    Parar,
    RoteiroDoTurno,
    Trava,
    assistente,
    limite,
    pedido,
    resultado,
    turno_de_texto,
)
from tests.sessao.estrategias import (
    BEM,
    COM_ERRO,
    ESPACOS,
    EXCECAO,
    ORQUESTRADOR,
    SINAL,
    ponderado,
    SINAIS,
    adaptador,
    agente,
    coletar,
    contexto_novo,
    esperar_que,
    excecoes,
    executar,
    registro_de_teste,
    roteiros,
)
from tests.sessao.modelo import Desfecho, ModeloDeSessoes
from tests.sessao.test_falhas import esperado

BIBLIOTECARIO_COM_LER = agente(ferramentas=("ler",))


def gramatica(eventos: list) -> None:
    """RN-S-17: MensagemEntregue, pedacos e usos, exatamente um evento final;
    ou so a falha, quando nao houve entrega."""
    assert eventos, "turno sem evento"
    *meio, final = eventos
    assert isinstance(final, (FimDeTurno, FalhaDoTurno)), final
    if meio:
        assert isinstance(meio[0], MensagemEntregue), meio[0]
        assert all(isinstance(e, (PedacoDeTexto, UsoDeFerramenta)) for e in meio[1:]), meio
    else:
        assert isinstance(final, FalhaDoTurno)
    if isinstance(final, FimDeTurno):
        assert any(isinstance(e, (PedacoDeTexto, UsoDeFerramenta)) for e in meio), "FimDeTurno sem resposta"


def _motivo_da_resposta(roteiro) -> M | None:
    if roteiro.desfecho == BEM:
        return None if roteiro.tem_resposta else M.RESPOSTA_VAZIA
    if roteiro.desfecho == COM_ERRO:
        return M.FALHA_INESPERADA
    if roteiro.desfecho == SINAL:
        if roteiro.sinal == "rejected":
            return M.LIMITE_DE_USO
        return esperado(Fase.RESPOSTA, ErroDoAssistente(roteiro.sinal)).motivo
    if roteiro.desfecho == EXCECAO:
        return esperado(Fase.RESPOSTA, roteiro.excecao).motivo
    return M.INDISPONIVEL


# --------------------------------------------------------------------------
# PBT-U6-01: a gramatica, no adaptador inteiro
# --------------------------------------------------------------------------


@settings(max_examples=100)
@given(
    roteiros(da_sessao=("mcp__wiki__ler",)),
    ponderado((3, st.just("nenhuma")), (1, st.just("subida")), (1, st.just("entrega"))),
    excecoes,
)
def test_pbt_u6_01_gramatica_do_turno_no_adaptador(roteiro, onde, excecao):
    fabrica = FabricaRoteirizada(
        subidas=[Falha(excecao)] if onde == "subida" else [],
        turnos=[RoteiroDoTurno(list(roteiro.passos), entrega=Falha(excecao) if onde == "entrega" else Bem())],
    )

    async def cenario():
        sessoes = adaptador(fabrica)
        sessao = await sessoes.abrir(BIBLIOTECARIO_COM_LER, contexto_novo())
        return await coletar(sessoes.enviar(sessao, "oi"))

    eventos = executar(cenario())

    gramatica(eventos)
    final = eventos[-1]
    motivo = None if isinstance(final, FimDeTurno) else final.motivo
    event(f"onde={onde} desfecho={roteiro.desfecho} final={getattr(motivo, 'value', 'fim_de_turno')}")
    if onde == "subida":
        assert len(eventos) == 1 and motivo is esperado(Fase.SUBIDA, excecao).motivo
    elif onde == "entrega":
        assert len(eventos) == 1 and motivo is esperado(Fase.ENTREGA, excecao).motivo
    else:
        assert motivo is _motivo_da_resposta(roteiro)
        usos = [e for e in eventos if isinstance(e, UsoDeFerramenta)]
        assert len(usos) == len(roteiro.usos)


# --------------------------------------------------------------------------
# PBT-U6-03: nunca levanta
# --------------------------------------------------------------------------

_DERRUBAM = {M.PROVEDOR_AUSENTE, M.NAO_AUTENTICADO, M.INDISPONIVEL, M.FALHA_INESPERADA}


# Parametrizado pelo ponto da falha: 5 x 30 = 150 exemplos.
@pytest.mark.parametrize("ponto", ["subida", "entrega", "resposta", "sinal", "cauda"])
@settings(max_examples=30)
@given(st.data(), st.booleans())
def test_pbt_u6_03_enviar_nunca_levanta(ponto, data, ja_conectada):
    causa = data.draw(st.sampled_from(SINAIS + ("rejected",)) if ponto == "sinal" else excecoes)
    chegou = asyncio.Event()
    fabrica = FabricaRoteirizada()
    turnos = [turno_de_texto("aquecimento")] if ja_conectada else []
    if ponto == "subida":
        ja_conectada = False
        turnos = []
        fabrica.subidas.append(Falha(causa))
    elif ponto == "entrega":
        turnos.append(RoteiroDoTurno(entrega=Falha(causa)))
    elif ponto == "resposta":
        turnos.append(RoteiroDoTurno([Mensagem(assistente(TextBlock("meio"))), Levantar(causa)]))
    elif ponto == "sinal":
        mensagem = limite("rejected", 1_767_225_600) if causa == "rejected" else assistente(erro=causa)
        turnos.append(RoteiroDoTurno([Mensagem(mensagem), resultado(erro=True)]))
    else:
        turnos.append(RoteiroDoTurno([Mensagem(assistente(TextBlock("meio"))), Parar(chegou=chegou)]))
        fabrica.interrupcao = Falha(causa)
    fabrica.turnos.extend(turnos)

    async def cenario():
        sessoes = adaptador(fabrica)
        sessao = await sessoes.abrir(agente(), contexto_novo())
        if ja_conectada:
            await coletar(sessoes.enviar(sessao, "aquecimento"))
        if ponto == "cauda":
            turno = asyncio.create_task(coletar(sessoes.enviar(sessao, "oi")))
            await chegou.wait()
            turno.cancel()
            resultado_do_turno = await asyncio.gather(turno, return_exceptions=True)
            await esperar_que(lambda: sessoes.estado(sessao) is not Estado.EM_TURNO)
            return resultado_do_turno, None, sessoes.estado(sessao), fabrica.vivos
        eventos, vivos_no_evento = [], None
        async for evento in sessoes.enviar(sessao, "oi"):
            eventos.append(evento)
            vivos_no_evento = fabrica.vivos
        return eventos, vivos_no_evento, sessoes.estado(sessao), fabrica.vivos

    eventos, vivos_no_evento, estado, vivos = executar(cenario())

    event(f"conectada={ja_conectada} causa={causa if isinstance(causa, str) else type(causa).__name__}")
    if ponto == "cauda":
        # So o cancelamento passa; o aviso que falha descarta o processo.
        assert isinstance(eventos[0], asyncio.CancelledError)
        assert (estado, vivos) == (Estado.SEM_CONEXAO, 0)
        return
    gramatica(eventos)
    final = eventos[-1]
    assert isinstance(final, FalhaDoTurno)
    fase = {"subida": Fase.SUBIDA, "entrega": Fase.ENTREGA}.get(ponto, Fase.RESPOSTA)
    if ponto == "sinal":
        esperado_ = M.LIMITE_DE_USO if causa == "rejected" else esperado(fase, ErroDoAssistente(causa)).motivo
    else:
        esperado_ = esperado(fase, causa).motivo
    assert final.motivo is esperado_
    if final.motivo in _DERRUBAM:
        assert vivos_no_evento == 0  # N5: o evento so sai com o processo morto
        assert estado is Estado.SEM_CONEXAO
    else:
        assert estado is Estado.OCIOSA and vivos == 1


# --------------------------------------------------------------------------
# PBT-U6-09: o ciclo de vida, contra o modelo
# --------------------------------------------------------------------------

_SELETOR = st.integers(min_value=0, max_value=3)
# Medido no passo 25: sem peso, 42% das sequencias nao abriam sessao nenhuma.
# Toda sequencia comeca com `abrir`, e enviar pesa mais que o resto.
COMANDOS = ponderado(
    (4, st.tuples(st.just("enviar"), _SELETOR, st.sampled_from(list(Desfecho)))),
    (2, st.just(("abrir",))),
    (1, st.tuples(st.just("esc_antes"), _SELETOR)),
    (1, st.tuples(st.just("esc_depois"), _SELETOR, st.booleans())),
    (1, st.tuples(st.just("enviar_na_cauda"), _SELETOR)),
    (1, st.tuples(st.just("fechar"), _SELETOR)),
    (1, st.just(("encerrar",))),
)

_TURNOS = {
    Desfecho.BEM: lambda: turno_de_texto("ok"),
    Desfecho.SUBIDA_FALHA: lambda: turno_de_texto("ok"),
    Desfecho.VAZIO: lambda: RoteiroDoTurno([resultado()]),
    Desfecho.LIMITE: lambda: RoteiroDoTurno([Mensagem(limite("rejected")), resultado(erro=True)]),
    Desfecho.DERRUBA: lambda: RoteiroDoTurno([Levantar(CLIConnectionError("caiu"))]),
}


class Motorista:
    """Traduz cada comando em roteiro para a fabrica, executa no adaptador e
    no modelo, e confere os dois depois de cada passo."""

    def __init__(self) -> None:
        self.fabrica = FabricaRoteirizada()
        self.sessoes = adaptador(self.fabrica, prazo_de_subida=5)
        self.modelo = ModeloDeSessoes()
        self.vivas: list = []

    def _consultas(self) -> int:
        return sum(len(cliente.consultas) for cliente in self.fabrica.clientes)

    def _sem_conexao(self, indice: int) -> bool:
        return self.modelo.sessoes[indice].estado is Estado.SEM_CONEXAO

    async def abrir(self) -> None:
        if self.modelo.encerrado:
            try:
                await self.sessoes.abrir(agente(), contexto_novo())
            except AdaptadorEncerrado:
                return
            raise AssertionError("abrir depois de encerrar")
        self.vivas.append(await self.sessoes.abrir(agente(), contexto_novo()))
        self.modelo.abrir()

    async def enviar(self, indice: int, desfecho: Desfecho) -> None:
        if self.modelo.sessoes[indice].estado is not Estado.FECHADA:
            if desfecho is Desfecho.SUBIDA_FALHA and self._sem_conexao(indice):
                self.fabrica.subidas.append(Falha(CLIConnectionError("nao subiu")))
            else:
                self.fabrica.turnos.append(_TURNOS[desfecho]())
        nova, motivo = self.modelo.enviar(indice, desfecho)
        eventos = await coletar(self.sessoes.enviar(self.vivas[indice], "oi"))
        gramatica(eventos)
        if nova is None:
            assert len(eventos) == 1
        else:
            assert eventos[0] == MensagemEntregue(conversa_nova=nova)
        final = eventos[-1]
        assert (None if isinstance(final, FimDeTurno) else final.motivo) is motivo

    async def esc_antes(self, indice: int) -> None:
        if self.modelo.sessoes[indice].estado is Estado.FECHADA:
            return
        liberar = asyncio.Event()
        if self._sem_conexao(indice):
            self.fabrica.subidas.append(Trava(liberar))
            pronto = lambda n=self.fabrica.nascidos: self.fabrica.nascidos > n  # noqa: E731
        else:
            self.fabrica.turnos.append(RoteiroDoTurno(entrega=Trava(liberar)))
            # Com varias sessoes, o cliente desta nao e o ultimo criado: vale o
            # total de consultas de todos.
            pronto = lambda n=self._consultas(): self._consultas() > n  # noqa: E731
        turno = asyncio.create_task(coletar(self.sessoes.enviar(self.vivas[indice], "oi")))
        await esperar_que(pronto)
        turno.cancel()
        await asyncio.gather(turno, return_exceptions=True)
        self.modelo.esc_antes_da_entrega(indice)

    async def esc_depois(self, indice: int, aviso_funciona: bool, e_mandar_de_novo: bool = False) -> None:
        if self.modelo.sessoes[indice].estado is Estado.FECHADA:
            return
        chegou = asyncio.Event()
        self.fabrica.turnos.append(RoteiroDoTurno([Mensagem(assistente(TextBlock("parcial"))), Parar(chegou=chegou)]))
        self.fabrica.interrupcao = Lento(0.02) if aviso_funciona else Falha(CLIConnectionError("aviso falhou"))
        vistos: list = []

        async def ler():
            async for evento in self.sessoes.enviar(self.vivas[indice], "oi"):
                vistos.append(evento)

        turno = asyncio.create_task(ler())
        await chegou.wait()
        turno.cancel()
        await asyncio.gather(turno, return_exceptions=True)
        nova = self.modelo.esc_depois_da_entrega(indice, aviso_funciona)
        assert vistos[0] == MensagemEntregue(conversa_nova=nova)
        if e_mandar_de_novo:
            # N2: chega durante a cauda, e espera em vez de dar TURNO_EM_ANDAMENTO.
            await self.enviar(indice, Desfecho.BEM)

    async def fechar(self, indice: int) -> None:
        await self.sessoes.fechar(self.vivas[indice])
        self.modelo.fechar(indice)

    async def encerrar(self) -> None:
        await self.sessoes.encerrar()
        self.modelo.encerrar()

    async def conferir(self) -> None:
        await esperar_que(lambda: all(self.sessoes.estado(s) is not Estado.EM_TURNO for s in self.vivas))
        await esperar_que(lambda: self.fabrica.vivos == self.modelo.processos())
        for indice, sessao in enumerate(self.vivas):
            assert self.sessoes.estado(sessao) is self.modelo.sessoes[indice].estado, indice


@settings(max_examples=60)
@given(st.lists(COMANDOS, min_size=0, max_size=19).map(lambda resto: [("abrir",), *resto]))
def test_pbt_u6_09_ciclo_de_vida_contra_o_modelo(comandos):
    async def cenario():
        motorista = Motorista()
        for comando in comandos:
            if comando[0] not in ("abrir", "encerrar") and motorista.vivas:
                event(f"comando={comando[0]}")
            nome, *argumentos = comando
            if nome in ("abrir", "encerrar"):
                await getattr(motorista, nome)()
            elif motorista.vivas:
                indice = argumentos[0] % len(motorista.vivas)
                match nome:
                    case "enviar":
                        await motorista.enviar(indice, argumentos[1])
                    case "esc_antes":
                        await motorista.esc_antes(indice)
                    case "esc_depois":
                        await motorista.esc_depois(indice, argumentos[1])
                    case "enviar_na_cauda":
                        await motorista.esc_depois(indice, True, e_mandar_de_novo=True)
                    case "fechar":
                        await motorista.fechar(indice)
            await motorista.conferir()
        event(f"sessoes={len(motorista.vivas)} fechadas={sum(1 for s in motorista.modelo.sessoes if s.estado is Estado.FECHADA)}")
        await motorista.encerrar()
        await motorista.conferir()

    executar(cenario())


# --------------------------------------------------------------------------
# PBT-U6-10: sessoes isoladas
# --------------------------------------------------------------------------


class FabricaPorSessao:
    """Cada sessao com o proprio roteiro, escolhido pelo prompt (as regras do
    agente): A ou B."""

    def __init__(self, a: FabricaRoteirizada, b: FabricaRoteirizada) -> None:
        self.por_prompt = {"A": a, "B": b}

    def __call__(self, opcoes: ClaudeAgentOptions):
        return self.por_prompt[opcoes.system_prompt](opcoes)


def _turnos(roteiros_) -> list[RoteiroDoTurno]:
    return [RoteiroDoTurno(list(r.passos)) for r in roteiros_]


_ROTEIROS = st.lists(roteiros(da_sessao=("mcp__wiki__ler",)), min_size=1, max_size=3)


async def _sozinha(roteiros_, mensagens: int) -> list:
    fabrica = FabricaRoteirizada(turnos=_turnos(roteiros_))
    sessoes = adaptador(fabrica)
    sessao = await sessoes.abrir(agente(ferramentas=("ler",), regras=("B",)), contexto_novo())
    eventos = []
    for _ in range(mensagens):
        eventos += await coletar(sessoes.enviar(sessao, "oi"))
    await sessoes.encerrar()
    return eventos


# Parametrizado pela perturbacao: medido no passo 25, o sorteio deixava mais
# da metade sem perturbacao nenhuma. 3 x 20 = 60 exemplos.
@pytest.mark.parametrize("perturbacao", ["nada", "esc", "fechar"])
@settings(max_examples=20)
@given(_ROTEIROS, _ROTEIROS, st.lists(st.booleans(), min_size=1, max_size=60), st.integers(0, 6))
def test_pbt_u6_10_sessoes_isoladas(perturbacao, de_a, de_b, ordem, quando):
    async def cenario():
        sessoes = AdaptadorSessaoClaude(
            registro_de_teste(),
            Path.cwd(),
            FabricaPorSessao(FabricaRoteirizada(turnos=_turnos(de_a)), FabricaRoteirizada(turnos=_turnos(de_b))),
            prazo_de_subida=1,
            prazo_de_interrupcao=0.3,
        )
        a = await sessoes.abrir(agente(ferramentas=("ler",), regras=("A",)), contexto_novo())
        b = await sessoes.abrir(agente(ferramentas=("ler",), regras=("B",)), contexto_novo())
        restantes = {"A": len(de_a), "B": len(de_b)}
        iteradores = {"A": None, "B": None}
        vistos = {"A": [], "B": []}
        passos = 0
        perturbada = False

        async def avancar(qual: str) -> None:
            if iteradores[qual] is None:
                if restantes[qual] == 0:
                    return
                restantes[qual] -= 1
                iteradores[qual] = sessoes.enviar(a if qual == "A" else b, "oi")
            try:
                vistos[qual].append(await anext(iteradores[qual]))
            except StopAsyncIteration:
                iteradores[qual] = None

        escolhas = [("A" if x else "B") for x in ordem]
        while restantes["A"] or restantes["B"] or any(iteradores.values()):
            qual = escolhas[passos % len(escolhas)]
            if not restantes[qual] and iteradores[qual] is None:
                qual = "B" if qual == "A" else "A"
            if not perturbada and passos >= quando and perturbacao != "nada":
                perturbada = True
                vistos_antes = len(vistos["A"])
                if perturbacao == "esc" and iteradores["A"] is not None:
                    await iteradores["A"].aclose()
                    iteradores["A"] = None
                elif perturbacao == "fechar":
                    await sessoes.fechar(a)
                restantes["A"] = 0 if perturbacao == "fechar" else restantes["A"]
                corte = vistos_antes
            await avancar(qual)
            passos += 1
        await sessoes.encerrar()
        return vistos, (corte if perturbada else None)

    vistos, corte = executar(cenario())
    event(f"perturbacao={perturbacao} efetiva={corte is not None}")
    sozinha_b = executar(_sozinha(de_b, len(de_b)))
    sozinha_a = executar(_sozinha(de_a, len(de_a)))

    assert vistos["B"] == sozinha_b
    if corte is None:
        assert vistos["A"] == sozinha_a
    else:
        assert vistos["A"][:corte] == sozinha_a[:corte]


# --------------------------------------------------------------------------
# PBT-U6-11: interromper cancela tudo
# --------------------------------------------------------------------------


class ConfirmacaoMista:
    """Cada pedido, na ordem, ou e confirmado na hora, ou espera ate o teste
    liberar - a pessoa pensando."""

    def __init__(self, esperas: list[bool]) -> None:
        self.esperas = list(esperas)
        self.chegaram = 0
        self.liberada = asyncio.Event()

    async def confirmar(self, pedido) -> bool:
        espera = self.esperas[self.chegaram] if self.chegaram < len(self.esperas) else True
        self.chegaram += 1
        if espera:
            await self.liberada.wait()
        return True


@settings(max_examples=60)
@given(
    st.lists(st.booleans(), min_size=1, max_size=4),
    st.sampled_from(["antes_da_entrega", "com_ferramentas", "chamada_na_cauda"]),
    ambientes_de_uma_tarefa(minimo=0, maximo=2),
)
def test_pbt_u6_11_interromper_cancela_tudo(tmp_path, esperas, quando, ambiente):
    k = len(esperas)
    chegou = asyncio.Event()

    def chamada(i: int) -> ChamarFerramenta:
        return ChamarFerramenta(
            "mcp__ambiente__criar_etapa", {"executor": "agente", "descricao": f"etapa {i}"}, concorrente=True
        )

    fabrica = FabricaRoteirizada(interrupcao=Lento(0.02))
    if quando == "antes_da_entrega":
        fabrica.subidas.append(Trava())
    turno = RoteiroDoTurno(
        [Mensagem(pedido("mcp__ambiente__criar_etapa")) for _ in range(k)] + [chamada(i) for i in range(k)] + [Parar(chegou=chegou)]
    )
    if quando == "chamada_na_cauda":
        # O CLI chama mais uma ferramenta depois do ESC, antes de processar a
        # interrupcao: nada pode executar.
        turno.cauda = [ChamarFerramenta("mcp__ambiente__criar_etapa", {"executor": "agente", "descricao": "tarde"}), resultado(erro=True)]
    fabrica.turnos.append(turno)
    confirmacao = ConfirmacaoMista(esperas)

    async def cenario():
        montagem = await montar(tmp_path, ambiente, confirmacao, instrumento=ServicoEspiao)
        frente, tarefa = tarefas_de(ambiente)[0]
        contexto = ContextoDaSessao(ambiente.id, frente.id, tarefa.id, tarefa.chats[0].id)
        registro = RegistroDeFerramentas(entradas_de_acoes(montagem.catalogo))
        sessoes = AdaptadorSessaoClaude(registro, Path.cwd(), fabrica, prazo_de_subida=5, prazo_de_interrupcao=1)
        quem = ORQUESTRADOR.__class__(ORQUESTRADOR.nome, ORQUESTRADOR.papel, "m", ferramentas=tuple(e.nome for e in registro.entradas))
        sessao = await sessoes.abrir(quem, contexto)
        leitor = asyncio.create_task(coletar(sessoes.enviar(sessao, "crie as etapas")))
        if quando == "antes_da_entrega":
            await esperar_que(lambda: fabrica.vivos == 1)
        else:
            await chegou.wait()
            # as k chamadas chegaram a confirmacao, e as que nao esperam ja
            # executaram e responderam
            await esperar_que(lambda: confirmacao.chegaram == k)
            await esperar_que(lambda: len(fabrica.clientes[0].resultados) == sum(1 for e in esperas if not e))
        mudancas_no_esc = len(montagem.visto.mudancas())
        leitor.cancel()
        await asyncio.gather(leitor, return_exceptions=True)
        confirmacao.liberada.set()  # tarde demais: nada pode executar
        await esperar_que(lambda: sessoes.estado(sessao) is not Estado.EM_TURNO)
        await asyncio.sleep(0.02)
        interna = sessoes._sessoes[sessao.id]
        resultados = fabrica.clientes[0].textos_dos_resultados() if fabrica.clientes else []
        estado = sessoes.estado(sessao)
        await sessoes.encerrar()
        return mudancas_no_esc, len(montagem.visto.mudancas()), resultados, estado, len(interna.execucoes)

    mudancas_no_esc, mudancas_depois, resultados, estado, em_execucao = executar(cenario())
    event(f"quando={quando} k={k} esperando={sum(esperas)}")

    assert mudancas_depois == mudancas_no_esc  # nenhuma mudanca depois do ESC
    assert em_execucao == 0
    if quando == "antes_da_entrega":
        assert estado is Estado.SEM_CONEXAO
        assert resultados == [] and mudancas_no_esc == 0
        return
    assert estado is Estado.OCIOSA
    interrompidas = [texto for _, texto, _ in resultados if json.loads(texto).get("motivo") == "interrompida"]
    esperadas = sum(1 for e in esperas if e) + (1 if quando == "chamada_na_cauda" else 0)
    assert len(interrompidas) == esperadas
    assert mudancas_no_esc == sum(1 for e in esperas if not e)


# --------------------------------------------------------------------------
# PBT-U6-12: mensagem invalida nao sai
# --------------------------------------------------------------------------


@settings(max_examples=100)
@given(
    st.one_of(
        st.text(st.sampled_from(ESPACOS), max_size=30).map(lambda t: ("vazia", t)),
        st.integers(100_001, 100_100).map(lambda n: ("longa_demais", "a" * n)),
    )
)
def test_pbt_u6_12_mensagem_invalida_nao_sai_no_adaptador(gerado):
    problema, texto = gerado
    fabrica = FabricaRoteirizada()

    async def cenario():
        sessoes = adaptador(fabrica)
        sessao = await sessoes.abrir(agente(), contexto_novo())
        return await coletar(sessoes.enviar(sessao, texto)), sessoes.estado(sessao)

    eventos, estado = executar(cenario())

    detalhe = {"problema": problema} | ({"maximo": "100000"} if problema == "longa_demais" else {})
    assert eventos == [FalhaDoTurno(M.MENSAGEM_INVALIDA, detalhe)]
    assert estado is Estado.SEM_CONEXAO
    assert fabrica.clientes == []  # o cliente nem foi criado
