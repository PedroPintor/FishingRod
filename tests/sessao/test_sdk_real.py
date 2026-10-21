"""U6 - as medicoes com o CLI de verdade (marcador `sdk_real`; medicoes 1 a 17).

Fora da suite padrao (DP-S-24): gastam o limite da sua assinatura e precisam do
seu login no CLI embutido. Rodam com `uv run pytest -m sdk_real`. Usam o
apelido `haiku`, o mais barato - o que se mede e o comportamento da sessao, nao
a qualidade da resposta -, a nao ser a 17, que compara apelidos.

Cada medicao grava o que viu em `MEDICOES`; no fim, o registro vai para o JSON
apontado por FISHINGROD_MEDICOES (ou para a pasta temporaria), e o passo 26 do
plano o copia para o resumo do codigo.

As medicoes 2, 10, 11 e 16 BLOQUEIAM U6: se uma falhar, a geracao para e volta
ao usuario antes de qualquer ajuste.
"""

import asyncio
import json
import os
import re
import subprocess
import sys
import tempfile
import textwrap
import time
import uuid
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ClaudeSDKClient,
    ResultMessage,
    StreamEvent,
    SystemMessage,
    TextBlock,
    ToolResultBlock,
    UserMessage,
)

from fishingrod.adaptadores.sessao import AdaptadorSessaoClaude
from fishingrod.adaptadores.sessao.adaptador import Estado
from fishingrod.adaptadores.sessao.opcoes import localizar_cli
from fishingrod.aplicacao.ferramentas import EntradaDoRegistro, Ferramenta, RegistroDeFerramentas, RespostaDaFerramenta
from fishingrod.aplicacao.ferramentas.acoes import entradas_de_acoes
from fishingrod.aplicacao.portas.sessao import (
    ContextoDaSessao,
    FalhaDoTurno,
    Familia,
    FimDeTurno,
    MensagemEntregue,
    PedacoDeTexto,
    UsoDeFerramenta,
)
from fishingrod.dominio import Agente, Ambiente, Papel
from tests.acoes.estrategias import montar
from tests.acoes.instrumentos import ConfirmacaoFixa, ServicoEspiao
from tests.sessao.estrategias import ORQUESTRADOR, contexto_novo

pytestmark = pytest.mark.sdk_real

MODELO = "haiku"
PRAZO_DO_TESTE = 240
MEDICOES: dict[str, Any] = {}


@pytest.fixture(scope="module", autouse=True)
def _gravar_medicoes():
    yield
    destino = Path(os.environ.get("FISHINGROD_MEDICOES", Path(tempfile.gettempdir()) / "fishingrod-medicoes-u6.json"))
    destino.write_text(json.dumps(MEDICOES, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print(f"\nmedicoes gravadas em {destino}")


def medir(numero: int, **dados: Any) -> None:
    MEDICOES.setdefault(f"medicao_{numero:02d}", {}).update(dados)


def rodar(coro, prazo: float = PRAZO_DO_TESTE):
    async def com_prazo():
        async with asyncio.timeout(prazo):
            return await coro

    return asyncio.run(com_prazo())


# --------------------------------------------------------------------------
# Instrumentos
# --------------------------------------------------------------------------


class ClienteGravado:
    """O ClaudeSDKClient de verdade, anotando cada mensagem com o instante."""

    def __init__(self, opcoes: ClaudeAgentOptions) -> None:
        self.opcoes = opcoes
        self._cliente = ClaudeSDKClient(options=opcoes)
        self.mensagens: list[tuple[float, Any]] = []
        self.inicio_da_conexao: float | None = None
        self.fim_da_conexao: float | None = None

    async def connect(self, prompt: Any = None) -> None:
        self.inicio_da_conexao = time.monotonic()
        await self._cliente.connect()
        self.fim_da_conexao = time.monotonic()

    async def query(self, prompt: str) -> None:
        await self._cliente.query(prompt)

    async def receive_response(self):
        async for mensagem in self._cliente.receive_response():
            self.mensagens.append((time.monotonic(), mensagem))
            yield mensagem

    async def interrupt(self) -> None:
        await self._cliente.interrupt()

    async def disconnect(self) -> None:
        await self._cliente.disconnect()

    def init(self) -> dict:
        for _, mensagem in self.mensagens:
            if isinstance(mensagem, SystemMessage) and mensagem.subtype == "init":
                return mensagem.data
        return {}


class FabricaGravada:
    def __init__(self, ajuste: Callable[[ClaudeAgentOptions], None] | None = None) -> None:
        self.ajuste = ajuste
        self.clientes: list[ClienteGravado] = []

    def __call__(self, opcoes: ClaudeAgentOptions) -> ClienteGravado:
        if self.ajuste is not None:
            self.ajuste(opcoes)
        cliente = ClienteGravado(opcoes)
        self.clientes.append(cliente)
        return cliente


def _processos() -> list[dict]:
    """Todos os processos da maquina, pelo sistema (e nao pelo contador do
    falso): PowerShell no Windows, `ps` nos outros."""
    if sys.platform == "win32":
        # Em UTF-8 dos dois lados: o caminho do CLI passa por "Area de
        # Trabalho" com acento, e o codigo de pagina do console quebra a leitura.
        comando = (
            "[Console]::OutputEncoding = [System.Text.Encoding]::UTF8; "
            "Get-CimInstance Win32_Process | "
            "Select-Object ProcessId,ParentProcessId,Name,ExecutablePath,WorkingSetSize | ConvertTo-Json -Compress"
        )
        saida = subprocess.run(
            ["powershell", "-NoProfile", "-Command", comando],
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            timeout=60,
        ).stdout or ""
        dados = json.loads(saida) if saida.strip() else []
        dados = [dados] if isinstance(dados, dict) else dados
        return [
            {
                "pid": d["ProcessId"],
                "ppid": d["ParentProcessId"],
                "nome": (d.get("Name") or "").lower(),
                "caminho": d.get("ExecutablePath"),
                "memoria": d.get("WorkingSetSize"),
            }
            for d in dados
        ]
    saida = subprocess.run(["ps", "-eo", "pid=,ppid=,rss=,comm="], capture_output=True, text=True, timeout=60).stdout
    processos = []
    for linha in saida.splitlines():
        pid, ppid, rss, comando = linha.split(None, 3)
        processos.append({"pid": int(pid), "ppid": int(ppid), "nome": Path(comando).name.lower(), "caminho": comando, "memoria": int(rss) * 1024})
    return processos


def processos_claude() -> list[dict]:
    return [p for p in _processos() if p["nome"].startswith("claude")]


def descendentes(pid: int | None = None) -> list[dict]:
    """Os processos `claude` que descendem deste Python (ou de `pid`),
    percorrendo a arvore inteira: no Windows, o python do ambiente virtual do
    uv e um lancador que abre o Python de verdade como filho."""
    todos = _processos()
    raizes = {pid or os.getpid()}
    mudou = True
    while mudou:
        mudou = False
        for processo in todos:
            if processo["ppid"] in raizes and processo["pid"] not in raizes:
                raizes.add(processo["pid"])
                mudou = True
    return [p for p in todos if p["pid"] in raizes and p["nome"].startswith("claude")]


async def esperar(condicao: Callable[[], bool], prazo: float = 30.0) -> bool:
    fim = time.monotonic() + prazo
    while time.monotonic() < fim:
        if condicao():
            return True
        await asyncio.sleep(0.2)
    return condicao()


def _pasta(tmp_path: Path, nome: str = "trabalho") -> Path:
    pasta = tmp_path / nome
    pasta.mkdir(parents=True, exist_ok=True)
    return pasta


def _agente(*regras: str, ferramentas: tuple[str, ...] = (), modelo: str = MODELO, papel=Papel.SUB_AGENTE) -> Agente:
    nome = "orquestrador" if papel is Papel.ORQUESTRADOR else "bibliotecario"
    return Agente(nome, papel, modelo, ferramentas=ferramentas, regras=regras)


def _texto(eventos: list) -> str:
    return "".join(e.texto for e in eventos if isinstance(e, PedacoDeTexto))


def _resumo(eventos: list) -> list[str]:
    return [type(e).__name__ + (f"({e.motivo.value})" if isinstance(e, FalhaDoTurno) else "") for e in eventos]


async def _turno(sessoes, sessao, mensagem: str) -> tuple[list, dict]:
    inicio = time.monotonic()
    tempos: dict[str, float] = {}
    eventos = []
    async for evento in sessoes.enviar(sessao, mensagem):
        agora = time.monotonic() - inicio
        if isinstance(evento, MensagemEntregue):
            tempos.setdefault("ate_entrega_s", round(agora, 2))
        if isinstance(evento, PedacoDeTexto):
            tempos.setdefault("ate_primeiro_pedaco_s", round(agora, 2))
        eventos.append(evento)
    tempos["turno_s"] = round(time.monotonic() - inicio, 2)
    return eventos, tempos


class FerramentaQueEspera:
    """Espera `segundos` - a pessoa decidindo. Anota quando comecou e como
    terminou."""

    def __init__(self, segundos: float) -> None:
        self.segundos = segundos
        self.inicios: list[float] = []
        self.fins: list[tuple[float, str]] = []

    async def __call__(self, argumentos) -> RespostaDaFerramenta:
        self.inicios.append(time.monotonic())
        try:
            await asyncio.sleep(self.segundos)
        except asyncio.CancelledError:
            self.fins.append((time.monotonic(), "cancelada"))
            raise
        self.fins.append((time.monotonic(), "terminou"))
        return RespostaDaFerramenta('{"ok":true}')


_ESQUEMA_DE_MOTIVO = {
    "type": "object",
    "properties": {"motivo": {"type": "string", "description": "Por que chamou."}},
    "required": ["motivo"],
    "additionalProperties": False,
}


def _registro_com(nome: str, executar) -> RegistroDeFerramentas:
    def fabricar(contexto, quem):
        return Ferramenta(nome, f"Ferramenta de teste: {nome}.", _ESQUEMA_DE_MOTIVO, executar)

    return RegistroDeFerramentas([EntradaDoRegistro(nome, Familia.WIKI, fabricar)])


REGRA_DE_TESTE = (
    "Voce e um agente de teste automatizado. Siga exatamente o que o usuario pedir sobre ferramentas, "
    "sem comentar, e responda em portugues numa frase curta."
)


# --------------------------------------------------------------------------
# 1, 8, 11, 12, 13: um turno simples, muito observado
# --------------------------------------------------------------------------


def test_medicoes_1_8_11_12_13_um_turno_observado(tmp_path, caplog):
    fabrica = FabricaGravada()
    pasta = _pasta(tmp_path)

    async def cenario():
        sessoes = AdaptadorSessaoClaude(RegistroDeFerramentas([]), pasta, fabrica)
        sessao = await sessoes.abrir(_agente(), contexto_novo())  # regras vazias: medicao 8
        um, tempos_um = await _turno(
            sessoes, sessao, "Voce tem instrucoes de sistema? Se nao tiver nenhuma, responda exatamente: SEM INSTRUCOES. "
            "Se tiver, copie a primeira frase delas."
        )
        filhos = descendentes()
        dois, tempos_dois = await _turno(sessoes, sessao, "Escreva tres frases curtas sobre pesca.")
        await sessoes.encerrar()
        return um, tempos_um, dois, tempos_dois, filhos

    um, tempos_um, dois, tempos_dois, filhos = rodar(cenario())
    cliente = fabrica.clientes[0]
    init = cliente.init()
    trechos = [m for _, m in cliente.mensagens if isinstance(m, StreamEvent)]
    tipos_de_delta = sorted(
        {m.event.get("delta", {}).get("type") for m in trechos if m.event.get("type") == "content_block_delta"} - {None}
    )
    completos = [m for _, m in cliente.mensagens if isinstance(m, AssistantMessage)]
    medir(
        1,
        stream_events=len(trechos),
        tipos_de_delta=tipos_de_delta,
        mensagens_completas=len(completos),
        pedacos_no_segundo_turno=sum(1 for e in dois if isinstance(e, PedacoDeTexto)),
        trechos_divergentes="trechos divergentes" in caplog.text,
    )
    medir(8, resposta=_texto(um)[:300], menciona_claude_code="claude code" in _texto(um).lower())
    medir(
        11,
        cli_embutido=str(localizar_cli()),
        caminhos_dos_filhos=[f["caminho"] for f in filhos],
        resposta_ok=um[-1] == FimDeTurno(),
        init_api_key_source=init.get("apiKeySource"),
        init_modelo=init.get("model"),
        init_ferramentas=init.get("tools"),
        init_versao_do_cli=init.get("claude_code_version"),
    )
    medir(12, memoria_mb=[round((f["memoria"] or 0) / 2**20, 1) for f in filhos])
    medir(
        13,
        primeiro_turno=tempos_um,
        segundo_turno=tempos_dois,
        conectar_s=round(cliente.fim_da_conexao - cliente.inicio_da_conexao, 2),
        checagem_de_versao_s=_tempo_de_versao(),
    )

    assert um[0] == MensagemEntregue(conversa_nova=True)
    assert um[-1] == FimDeTurno() and dois[-1] == FimDeTurno()
    assert dois[0] == MensagemEntregue(conversa_nova=False)
    # 11 (BLOQUEIA): o CLI que roda e o embutido, e ele enxerga o login.
    assert filhos, "nenhum processo claude filho deste Python"
    assert all(Path(f["caminho"]).resolve() == Path(localizar_cli()).resolve() for f in filhos if f["caminho"])
    # 8: prompt vazio nao traz o do Claude Code; nenhuma ferramenta nativa.
    assert "claude code" not in _texto(um).lower()
    assert all(nome.startswith("mcp__") for nome in init.get("tools", []))
    # 1: os trechos chegam e convivem com o bloco completo.
    assert "trechos divergentes" not in caplog.text


def _tempo_de_versao() -> float:
    inicio = time.monotonic()
    subprocess.run([str(localizar_cli()), "-v"], capture_output=True, timeout=30)
    return round(time.monotonic() - inicio, 2)


# --------------------------------------------------------------------------
# 2 (BLOQUEIA): o tempo-limite de uma ferramenta que espera uma pessoa
# --------------------------------------------------------------------------


def test_medicao_2_tempo_limite_da_ferramenta_e_configuravel(tmp_path):
    """MCP_TOOL_TIMEOUT pequeno (3 s) e uma ferramenta que espera 10 s: se o
    CLI corta perto de 3 s, a variavel vale para o servidor do SDK - e o valor
    maximo de DP-S-16 tambem."""
    espera = FerramentaQueEspera(10)

    def ajuste(opcoes: ClaudeAgentOptions) -> None:
        opcoes.env["MCP_TOOL_TIMEOUT"] = "3000"

    fabrica = FabricaGravada(ajuste)

    async def cenario():
        sessoes = AdaptadorSessaoClaude(_registro_com("esperar", espera), _pasta(tmp_path), fabrica)
        sessao = await sessoes.abrir(_agente(REGRA_DE_TESTE, ferramentas=("esperar",)), contexto_novo())
        eventos, _ = await _turno(sessoes, sessao, "Chame a ferramenta esperar uma unica vez, com motivo 'teste'. Depois responda: ok.")
        await sessoes.encerrar()
        return eventos

    eventos = rodar(cenario())
    cliente = fabrica.clientes[0]
    resultado = next(
        (
            (instante, bloco)
            for instante, m in cliente.mensagens
            if isinstance(m, UserMessage) and isinstance(m.content, list)
            for bloco in m.content
            if isinstance(bloco, ToolResultBlock)
        ),
        None,
    )
    corte_s = round(resultado[0] - espera.inicios[0], 2) if resultado and espera.inicios else None
    medir(
        2,
        ferramenta_chamada=bool(espera.inicios),
        resposta_do_cli_em_s=corte_s,
        resultado_e_erro=getattr(resultado[1], "is_error", None) if resultado else None,
        texto_do_resultado=str(getattr(resultado[1], "content", ""))[:200] if resultado else None,
        como_a_ferramenta_terminou=[como for _, como in espera.fins],
        eventos=_resumo(eventos),
    )

    assert espera.inicios, "o modelo nao chamou a ferramenta: a medicao nao se fez"
    assert corte_s is not None and corte_s < 9, "o CLI nao cortou perto de 3 s: MCP_TOOL_TIMEOUT nao vale (reabre U5)"


# --------------------------------------------------------------------------
# 3: o aviso de interrupcao com uma ferramenta em espera, e a cauda
# --------------------------------------------------------------------------


def test_medicao_3_interromper_com_ferramenta_em_espera(tmp_path):
    espera = FerramentaQueEspera(60)

    async def cenario():
        sessoes = AdaptadorSessaoClaude(_registro_com("esperar", espera), _pasta(tmp_path))
        sessao = await sessoes.abrir(_agente(REGRA_DE_TESTE, ferramentas=("esperar",)), contexto_novo())
        leitor = asyncio.create_task(
            _turno(sessoes, sessao, "Chame a ferramenta esperar uma unica vez, com motivo 'teste'. Depois responda: ok.")
        )
        chamou = await esperar(lambda: bool(espera.inicios), prazo=90)
        esc = time.monotonic()
        leitor.cancel()
        await asyncio.gather(leitor, return_exceptions=True)
        await esperar(lambda: sessoes.estado(sessao) is not Estado.EM_TURNO, prazo=30)
        cauda = round(time.monotonic() - esc, 2)
        estado = sessoes.estado(sessao)
        depois, _ = await _turno(sessoes, sessao, "Responda apenas: pronto.")
        await sessoes.encerrar()
        return chamou, cauda, estado, depois

    chamou, cauda, estado, depois = rodar(cenario())
    medir(
        3,
        ferramenta_chamada=chamou,
        cauda_s=cauda,
        estado_depois_do_esc=estado.value,
        ferramenta_terminou=[como for _, como in espera.fins],
        turno_seguinte=_resumo(depois),
    )

    assert chamou
    assert [como for _, como in espera.fins] == ["cancelada"]
    assert estado in (Estado.OCIOSA, Estado.SEM_CONEXAO)
    assert depois[-1] == FimDeTurno()


# --------------------------------------------------------------------------
# 4: como o CLI sinaliza falta de login
# --------------------------------------------------------------------------


def test_medicao_4_sem_login(tmp_path):
    vazia = _pasta(tmp_path, "config-vazia")

    def ajuste(opcoes: ClaudeAgentOptions) -> None:
        opcoes.env["CLAUDE_CONFIG_DIR"] = str(vazia)  # so neste teste (R-ND6-13)

    fabrica = FabricaGravada(ajuste)

    async def cenario():
        sessoes = AdaptadorSessaoClaude(RegistroDeFerramentas([]), _pasta(tmp_path), fabrica)
        sessao = await sessoes.abrir(_agente(), contexto_novo())
        eventos, _ = await _turno(sessoes, sessao, "Responda apenas: ok.")
        await sessoes.encerrar()
        return eventos

    eventos = rodar(cenario())
    sinais = [
        {"tipo": type(m).__name__, "erro": getattr(m, "error", None), "is_error": getattr(m, "is_error", None), "subtipo": getattr(m, "subtype", None)}
        for _, m in (fabrica.clientes[0].mensagens if fabrica.clientes else [])
        if isinstance(m, (AssistantMessage, ResultMessage))
    ]
    medir(4, eventos=_resumo(eventos), sinais=sinais)

    assert isinstance(eventos[-1], FalhaDoTurno)


# --------------------------------------------------------------------------
# 5: sem repassar a chave, a sessao responde pela assinatura
# --------------------------------------------------------------------------


def test_medicao_5_chave_falsa_no_ambiente_nao_e_repassada(tmp_path, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-chave-falsa-de-teste")
    monkeypatch.setenv("ANTHROPIC_BASE_URL", "http://127.0.0.1:9")
    fabrica = FabricaGravada()

    async def cenario():
        sessoes = AdaptadorSessaoClaude(RegistroDeFerramentas([]), _pasta(tmp_path), fabrica)
        sessao = await sessoes.abrir(_agente(), contexto_novo())
        eventos, _ = await _turno(sessoes, sessao, "Responda apenas: ok.")
        await sessoes.encerrar()
        return eventos

    eventos = rodar(cenario())
    init = fabrica.clientes[0].init()
    medir(5, eventos=_resumo(eventos), init_api_key_source=init.get("apiKeySource"))

    assert eventos[-1] == FimDeTurno(), "vazio foi tratado como valor: cai na opcao B da Q5"


# --------------------------------------------------------------------------
# 6: sem limite de passos, o turno nao e cortado
# --------------------------------------------------------------------------


def test_medicao_6_sem_limite_de_passos(tmp_path):
    contagem = []

    async def contar(argumentos) -> RespostaDaFerramenta:
        contagem.append(1)
        return RespostaDaFerramenta(json.dumps({"ok": True, "numero": len(contagem)}))

    fabrica = FabricaGravada()

    async def cenario():
        sessoes = AdaptadorSessaoClaude(_registro_com("contar", contar), _pasta(tmp_path), fabrica)
        sessao = await sessoes.abrir(_agente(REGRA_DE_TESTE, ferramentas=("contar",)), contexto_novo())
        eventos, _ = await _turno(
            sessoes, sessao, "Chame a ferramenta contar 8 vezes, uma de cada vez, com motivo 'teste'. Depois responda: fim."
        )
        await sessoes.encerrar()
        return eventos

    eventos = rodar(cenario())
    resultado = next((m for _, m in fabrica.clientes[0].mensagens if isinstance(m, ResultMessage)), None)
    medir(
        6,
        chamadas=len(contagem),
        usos=sum(1 for e in eventos if isinstance(e, UsoDeFerramenta)),
        final=_resumo(eventos)[-1],
        num_turns=getattr(resultado, "num_turns", None),
        subtipo=getattr(resultado, "subtype", None),
    )

    assert len(contagem) >= 6
    assert eventos[-1] == FimDeTurno()


# --------------------------------------------------------------------------
# 7: o erro quando o CLI nao existe
# --------------------------------------------------------------------------


def test_medicao_7_cli_ausente(tmp_path):
    def ajuste(opcoes: ClaudeAgentOptions) -> None:
        opcoes.cli_path = tmp_path / "nao-existe" / "claude.exe"

    async def cenario():
        sessoes = AdaptadorSessaoClaude(RegistroDeFerramentas([]), _pasta(tmp_path), FabricaGravada(ajuste))
        sessao = await sessoes.abrir(_agente(), contexto_novo())
        eventos, _ = await _turno(sessoes, sessao, "oi")
        return eventos

    eventos = rodar(cenario())
    medir(7, eventos=_resumo(eventos))

    assert eventos == [FalhaDoTurno(eventos[-1].motivo)] and eventos[-1].motivo.value == "provedor_ausente"


# --------------------------------------------------------------------------
# 9: o SDK aceita o JSON Schema completo das acoes
# --------------------------------------------------------------------------


def test_medicao_9_esquema_completo_das_acoes(tmp_path):
    ambiente = Ambiente("Nexo")
    frente = ambiente.criar_frente("Comercial")
    tarefa = frente.criar_tarefa("Campanha", ORQUESTRADOR)
    fabrica = FabricaGravada()

    async def cenario():
        montagem = await montar(tmp_path, ambiente, ConfirmacaoFixa(True), instrumento=ServicoEspiao)
        registro = RegistroDeFerramentas(entradas_de_acoes(montagem.catalogo))
        sessoes = AdaptadorSessaoClaude(registro, _pasta(tmp_path), fabrica)
        quem = _agente(REGRA_DE_TESTE, ferramentas=tuple(e.nome for e in registro.entradas), papel=Papel.ORQUESTRADOR)
        sessao = await sessoes.abrir(quem, ContextoDaSessao(ambiente.id, frente.id, tarefa.id, tarefa.sessoes[0].id, tarefa.sessoes[0].chats[0].id))
        eventos, _ = await _turno(
            sessoes,
            sessao,
            "Use a ferramenta criar_etapa uma vez, com executor 'usuario' e descricao 'revisar o briefing'. Depois responda: feito.",
        )
        await sessoes.encerrar()
        return eventos, montagem.visto.mudancas()

    eventos, mudancas = rodar(cenario())
    init = fabrica.clientes[0].init()
    usos = [dict(e.argumentos) for e in eventos if isinstance(e, UsoDeFerramenta)]
    medir(9, ferramentas_no_init=init.get("tools"), usos=usos, mudancas=[m[0] for m in mudancas], final=_resumo(eventos)[-1])

    assert sorted(t for t in init.get("tools", []) if t.startswith("mcp__ambiente__")) == sorted(
        f"mcp__ambiente__{e}" for e in ("criar_frente", "criar_tarefa", "criar_chat", "criar_etapa", "concluir_etapa", "anotar_memoria")
    )
    assert [m[0] for m in mudancas] == ["criar_etapa"]


# --------------------------------------------------------------------------
# 10 (BLOQUEIA): duas sessoes vivas ao mesmo tempo (criterio 3)
# --------------------------------------------------------------------------


def test_medicao_10_duas_sessoes_vivas_ao_mesmo_tempo(tmp_path):
    async def cenario():
        sessoes = AdaptadorSessaoClaude(RegistroDeFerramentas([]), _pasta(tmp_path))
        uma = await sessoes.abrir(_agente(), contexto_novo())
        outra = await sessoes.abrir(_agente(), contexto_novo())
        (eventos_uma, _), (eventos_outra, _) = await asyncio.gather(
            _turno(sessoes, uma, "Responda apenas: um."), _turno(sessoes, outra, "Responda apenas: dois.")
        )
        vivos = descendentes()
        segunda_uma, _ = await _turno(sessoes, uma, "Responda apenas: tres.")
        await sessoes.encerrar()
        await asyncio.sleep(1)
        return eventos_uma, eventos_outra, segunda_uma, vivos, descendentes()

    eventos_uma, eventos_outra, segunda_uma, vivos, depois = rodar(cenario())
    medir(10, processos_com_as_duas=len(vivos), finais=[_resumo(eventos_uma)[-1], _resumo(eventos_outra)[-1]], processos_depois=len(depois))

    assert eventos_uma[-1] == FimDeTurno() and eventos_outra[-1] == FimDeTurno()
    assert segunda_uma[0] == MensagemEntregue(conversa_nova=False)
    assert len(vivos) == 2
    assert depois == []


# --------------------------------------------------------------------------
# 14: o CLI termina sozinho quando o Python que o subiu morre?
# --------------------------------------------------------------------------

_FILHO = textwrap.dedent(
    """
    import asyncio, sys
    from pathlib import Path
    from fishingrod.adaptadores.sessao import AdaptadorSessaoClaude
    from fishingrod.aplicacao.ferramentas import RegistroDeFerramentas
    from fishingrod.aplicacao.portas.sessao import ContextoDaSessao
    from fishingrod.dominio import Agente, Identidade, Papel

    async def main():
        sessoes = AdaptadorSessaoClaude(RegistroDeFerramentas([]), Path(sys.argv[1]))
        contexto = ContextoDaSessao(*(Identidade.nova() for _ in range(5)))
        sessao = await sessoes.abrir(Agente("bibliotecario", Papel.SUB_AGENTE, "haiku"), contexto)
        async for _ in sessoes.enviar(sessao, "Responda apenas: ok."):
            pass
        print("PRONTO", flush=True)
        await asyncio.Event().wait()

    asyncio.run(main())
    """
)


def test_medicao_14_queda_dura_do_python(tmp_path):
    roteiro = tmp_path / "filho.py"
    roteiro.write_text(_FILHO, encoding="utf-8")
    filho = subprocess.Popen([sys.executable, str(roteiro), str(_pasta(tmp_path))], stdout=subprocess.PIPE, text=True)
    try:
        linha = filho.stdout.readline()
        clis = descendentes(filho.pid)
        # Queda dura do Python que E DONO do CLI (o pai do processo claude),
        # e nao do lancador do uv: TerminateProcess, sem passar por finally.
        donos = sorted({c["ppid"] for c in clis})
        for dono in donos:
            subprocess.run(["taskkill", "/F", "/PID", str(dono)] if sys.platform == "win32" else ["kill", "-9", str(dono)], capture_output=True)
        time.sleep(10)
        vivos = [p for p in processos_claude() if p["pid"] in {c["pid"] for c in clis}]
    finally:
        if filho.poll() is None:
            filho.kill()
    medir(14, pronto=linha.strip(), clis_antes=len(clis), donos_mortos=donos, clis_vivos_10s_depois=len(vivos))
    for orfao in vivos:  # limpeza: nao deixar processo da medicao para tras
        subprocess.run(["taskkill", "/F", "/PID", str(orfao["pid"])] if sys.platform == "win32" else ["kill", "-9", str(orfao["pid"])], capture_output=True)

    assert linha.strip() == "PRONTO" and clis


# --------------------------------------------------------------------------
# 15: a conversa e guardada em ~/.claude/projects/, com o id do chat (D22)
# --------------------------------------------------------------------------
# Invertida pelo card 002: antes conferia que NADA era guardado (DP-S-13).


def test_medicao_15_a_conversa_e_guardada_com_o_id_do_chat(tmp_path):
    marca = f"fishingrod-medicao-15-{uuid.uuid4().hex[:8]}"
    pasta = _pasta(tmp_path, marca)
    projetos = Path.home() / ".claude" / "projects"
    contexto = contexto_novo()

    async def cenario():
        sessoes = AdaptadorSessaoClaude(RegistroDeFerramentas([]), pasta)
        sessao = await sessoes.abrir(_agente(), contexto)
        eventos, _ = await _turno(sessoes, sessao, "Responda apenas: ok.")
        await sessoes.encerrar()
        return eventos

    eventos = rodar(cenario())
    marca_saneada = re.sub(r"[^A-Za-z0-9]", "-", marca)
    copias = [str(p) for p in projetos.rglob("*.jsonl") if marca_saneada in str(p) or marca in str(p)] if projetos.exists() else []
    medir(15, final=_resumo(eventos)[-1], copias=copias, pasta_de_projetos=str(projetos))

    assert eventos[-1] == FimDeTurno()
    assert [Path(c).name for c in copias] == [f"{contexto.id_chat.valor}.jsonl"]


# --------------------------------------------------------------------------
# 16 (BLOQUEIA): ESC e prazo vencido nao deixam processo
# --------------------------------------------------------------------------


def test_medicao_16_esc_e_prazo_vencido_nao_deixam_processo(tmp_path):
    async def esc_na_subida():
        sessoes = AdaptadorSessaoClaude(RegistroDeFerramentas([]), _pasta(tmp_path))
        sessao = await sessoes.abrir(_agente(), contexto_novo())
        leitor = asyncio.create_task(_turno(sessoes, sessao, "Responda apenas: ok."))
        await esperar(lambda: bool(descendentes()), prazo=30)
        subiu = len(descendentes())
        leitor.cancel()
        await asyncio.gather(leitor, return_exceptions=True)
        await esperar(lambda: sessoes.estado(sessao) is Estado.SEM_CONEXAO, prazo=30)
        await asyncio.sleep(1)
        restantes = descendentes()
        await sessoes.encerrar()
        return subiu, len(restantes)

    async def esc_na_resposta():
        sessoes = AdaptadorSessaoClaude(RegistroDeFerramentas([]), _pasta(tmp_path))
        sessao = await sessoes.abrir(_agente(), contexto_novo())
        primeiro_pedaco = asyncio.Event()

        async def ler():
            async for evento in sessoes.enviar(sessao, "Escreva um texto de 300 palavras sobre rios."):
                if isinstance(evento, PedacoDeTexto):
                    primeiro_pedaco.set()

        leitor = asyncio.create_task(ler())
        await asyncio.wait_for(primeiro_pedaco.wait(), 120)
        esc = time.monotonic()
        leitor.cancel()
        await asyncio.gather(leitor, return_exceptions=True)
        await esperar(lambda: sessoes.estado(sessao) is not Estado.EM_TURNO, prazo=30)
        cauda = round(time.monotonic() - esc, 2)
        estado = sessoes.estado(sessao)
        await sessoes.fechar(sessao)
        await asyncio.sleep(1)
        return estado, cauda, len(descendentes())

    async def prazo_vencido():
        sessoes = AdaptadorSessaoClaude(RegistroDeFerramentas([]), _pasta(tmp_path), prazo_de_subida=0.3)
        sessao = await sessoes.abrir(_agente(), contexto_novo())
        eventos = []
        vivos_no_evento = None
        async for evento in sessoes.enviar(sessao, "Responda apenas: ok."):
            eventos.append(evento)
            vivos_no_evento = len(descendentes())
        await sessoes.encerrar()
        return eventos, vivos_no_evento

    subiu, restantes_subida = rodar(esc_na_subida())
    estado, cauda, restantes_resposta = rodar(esc_na_resposta())
    eventos_prazo, vivos_no_evento = rodar(prazo_vencido())
    medir(
        16,
        esc_na_subida={"processos_ao_subir": subiu, "processos_depois": restantes_subida},
        esc_na_resposta={"estado": estado.value, "cauda_s": cauda, "processos_depois_de_fechar": restantes_resposta},
        prazo_vencido={"eventos": _resumo(eventos_prazo), "processos_no_evento": vivos_no_evento},
    )

    assert restantes_subida == 0
    assert estado is Estado.OCIOSA and restantes_resposta == 0
    assert eventos_prazo[-1] == FalhaDoTurno(eventos_prazo[-1].motivo) and eventos_prazo[-1].motivo.value == "indisponivel"
    assert vivos_no_evento == 0


# --------------------------------------------------------------------------
# 17: o modelo vem do Agente (R-CG6-3)
# --------------------------------------------------------------------------


def test_medicao_17_o_modelo_vem_do_agente(tmp_path):
    fabrica = FabricaGravada()

    async def cenario():
        sessoes = AdaptadorSessaoClaude(RegistroDeFerramentas([]), _pasta(tmp_path), fabrica)
        com_apelido = await sessoes.abrir(_agente(modelo="haiku"), contexto_novo())
        inexistente = await sessoes.abrir(_agente(modelo="modelo-que-nao-existe"), contexto_novo())
        bom, _ = await _turno(sessoes, com_apelido, "Responda apenas: ok.")
        ruim, _ = await _turno(sessoes, inexistente, "Responda apenas: ok.")
        await sessoes.encerrar()
        return bom, ruim

    bom, ruim = rodar(cenario())
    modelos = [cliente.init().get("model") for cliente in fabrica.clientes]
    sinais = [
        {"tipo": type(m).__name__, "erro": getattr(m, "error", None), "is_error": getattr(m, "is_error", None)}
        for cliente in fabrica.clientes[1:]
        for _, m in cliente.mensagens
        if isinstance(m, (AssistantMessage, ResultMessage))
    ]
    medir(17, modelos_no_init=modelos, apelido=_resumo(bom), inexistente=_resumo(ruim), sinais_do_inexistente=sinais)

    assert bom[-1] == FimDeTurno()
    assert modelos[0] and "haiku" in modelos[0]
    assert isinstance(ruim[-1], FalhaDoTurno)
