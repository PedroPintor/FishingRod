"""U6 - as opcoes do SDK, linha por linha (DP-S-11..17, criterio 7, US-02, R-CG6-3).

O teste recebe as opcoes pela fabrica de cliente (G11) e confere o §5 de
nfr-design-patterns.md - inclusive as opcoes que ficam no valor padrao. E por
isso que nao ha propriedade aqui (business-logic-model.md §9): sao valores
fixos montados uma vez, e uma inspecao prova mais que dados gerados.
"""

import dataclasses
import logging
import warnings
from pathlib import Path

import pytest
from claude_agent_sdk import ClaudeAgentOptions, ToolPermissionContext
from claude_agent_sdk._internal.transport.subprocess_cli import SubprocessCLITransport
from claude_agent_sdk.types import _warn_if_can_use_tool_shadowed

from fishingrod.adaptadores.sessao import adaptador as modulo_adaptador
from fishingrod.adaptadores.sessao.adaptador import Estado
from fishingrod.adaptadores.sessao.opcoes import (
    TEMPO_LIMITE_DE_FERRAMENTA_MS,
    VARIAVEIS_DE_CREDENCIAL,
    localizar_cli,
    permissao_exata,
)
from fishingrod.aplicacao.portas.sessao import FalhaDoTurno, MotivoFalhaDeSessao
from tests.sessao.cliente_roteirizado import FabricaRoteirizada
from tests.sessao.estrategias import adaptador, agente, coletar, contexto_novo, executar

# As opcoes que o adaptador escreve. Toda outra fica no valor padrao do SDK.
ESCRITAS = {
    "cli_path",
    "tools",
    "allowed_tools",
    "can_use_tool",
    "setting_sources",
    "skills",
    "strict_mcp_config",
    "mcp_servers",
    "system_prompt",
    "model",
    "cwd",
    "include_partial_messages",
    "env",
    "resume",
    "session_id",
    "stderr",
}


CONTEXTO = contexto_novo()


def _opcoes_de(quem, pasta: Path | None = None) -> ClaudeAgentOptions:
    fabrica = FabricaRoteirizada()

    async def cenario():
        sessoes = adaptador(fabrica, pasta=pasta)
        sessao = await sessoes.abrir(quem, CONTEXTO)
        await coletar(sessoes.enviar(sessao, "oi"))
        await sessoes.encerrar()

    executar(cenario())
    return fabrica.opcoes[0]


@pytest.fixture(scope="module")
def opcoes(tmp_path_factory) -> ClaudeAgentOptions:
    pasta = tmp_path_factory.mktemp("trabalho")
    return _opcoes_de(
        agente("bibliotecario", ferramentas=("ler", "listar"), regras=("Seja breve.", "Cite a fonte.")), pasta
    )


# --------------------------------------------------------------------------
# Linha por linha (nfr-design-patterns.md §5)
# --------------------------------------------------------------------------


def test_dp_s_15_cli_path_e_o_embutido(opcoes):
    assert opcoes.cli_path == localizar_cli()
    assert Path(opcoes.cli_path).parent.name == "_bundled"


def test_rn_s_10_nenhuma_ferramenta_nativa(opcoes):
    assert opcoes.tools == []


def test_dp_s_14_allowed_tools_vazio_e_can_use_tool_decide(opcoes):
    assert opcoes.allowed_tools == []
    assert callable(opcoes.can_use_tool)


def test_rn_s_10_nenhuma_configuracao_da_maquina(opcoes):
    assert opcoes.setting_sources == []
    assert opcoes.skills == []
    assert opcoes.strict_mcp_config is True


def test_rn_s_12_um_servidor_por_familia_presente(opcoes):
    assert list(opcoes.mcp_servers) == ["wiki"]
    servidor = opcoes.mcp_servers["wiki"]
    assert servidor["type"] == "sdk" and servidor["name"] == "wiki"


def test_rn_s_12_sessao_sem_ferramenta_nao_tem_servidor():
    assert _opcoes_de(agente()).mcp_servers == {}


def test_rn_s_10_o_prompt_e_so_as_regras(opcoes):
    assert opcoes.system_prompt == "Seja breve.\n\nCite a fonte."


def test_g15_regras_vazias_viram_prompt_vazio_e_nao_o_do_claude_code():
    prompt = _opcoes_de(agente()).system_prompt

    assert prompt == "" and isinstance(prompt, str)


def test_r_cg6_3_o_modelo_vem_do_agente():
    quem = agente()
    outro = dataclasses.replace(quem, modelo="haiku")

    assert _opcoes_de(quem).model == "modelo-de-teste"
    assert _opcoes_de(outro).model == "haiku"


def test_rn_s_10_o_processo_roda_na_pasta_de_trabalho(opcoes, tmp_path_factory):
    assert Path(opcoes.cwd).name.startswith("trabalho")


def test_q1_b_mensagens_parciais_ligadas(opcoes):
    assert opcoes.include_partial_messages is True


def test_dp_s_12_e_dp_s_16_o_ambiente_do_processo(opcoes):
    """Cada variavel de credencial sobrescrita com vazio, o tempo-limite da
    ferramenta no maximo, e nada mais - em especial, nunca CLAUDE_CONFIG_DIR."""
    esperado = {nome: "" for nome in VARIAVEIS_DE_CREDENCIAL} | {"MCP_TOOL_TIMEOUT": "2147483647"}

    assert opcoes.env == esperado
    assert "CLAUDE_CONFIG_DIR" not in opcoes.env
    assert TEMPO_LIMITE_DE_FERRAMENTA_MS == 2**31 - 1


def test_rn_s_52_a_lista_de_credenciais():
    """Pelo menos as cinco do NFR Design, mais as que o CLI 2.1.238 lista
    como credencial, endereco ou provedor (passo 2 do plano). Sem repeticao e
    sem proxy: proxy muda a rota, nao a credencial."""
    for obrigatoria in (
        "ANTHROPIC_API_KEY",
        "ANTHROPIC_AUTH_TOKEN",
        "ANTHROPIC_BASE_URL",
        "CLAUDE_CODE_USE_BEDROCK",
        "CLAUDE_CODE_USE_VERTEX",
        "CLAUDE_CODE_OAUTH_TOKEN",
        "ANTHROPIC_CUSTOM_HEADERS",
    ):
        assert obrigatoria in VARIAVEIS_DE_CREDENCIAL
    assert len(set(VARIAVEIS_DE_CREDENCIAL)) == len(VARIAVEIS_DE_CREDENCIAL)
    assert not {"HTTPS_PROXY", "HTTP_PROXY", "NODE_EXTRA_CA_CERTS", "CLAUDE_CONFIG_DIR"} & set(VARIAVEIS_DE_CREDENCIAL)


def test_d22_a_conversa_nasce_com_o_id_do_chat_e_e_guardada(opcoes):
    """D22 derruba DP-S-13: a conversa fica em ~/.claude/projects/, com o id
    do chat como codigo. Numa conversa que ainda nao existe, `session_id`;
    numa que existe, `resume` (test_adaptador.py)."""
    assert opcoes.session_id == CONTEXTO.id_chat.valor
    assert opcoes.resume is None
    assert opcoes.extra_args == {}


def test_dp_s_17_a_saida_de_erro_do_cli_vai_ao_log_em_debug(opcoes, caplog):
    with caplog.at_level(logging.DEBUG, logger="fishingrod.sessao"):
        opcoes.stderr("linha do CLI")

    assert [(r.levelno, r.getMessage()) for r in caplog.records] == [(logging.DEBUG, "saida de erro do CLI: linha do CLI")]


def test_dp_s_11_todas_as_outras_opcoes_ficam_no_valor_padrao(opcoes):
    """Inclusive as ausentes: continue_conversation, fork_session,
    add_dirs, plugins, max_turns (sem limite de passos), hooks, agents,
    session_store, permission_mode, permission_prompt_tool_name e user."""
    padrao = ClaudeAgentOptions()
    for campo in dataclasses.fields(ClaudeAgentOptions):
        if campo.name in ESCRITAS:
            continue
        assert getattr(opcoes, campo.name) == getattr(padrao, campo.name), campo.name
    for ausente in (
        "continue_conversation",
        "fork_session",
        "add_dirs",
        "plugins",
        "max_turns",
        "hooks",
        "agents",
        "session_store",
        "permission_mode",
        "permission_prompt_tool_name",
        "user",
    ):
        assert ausente not in ESCRITAS


def test_n1_nenhum_aviso_de_can_use_tool_sombreado(opcoes):
    with warnings.catch_warnings(record=True) as avisos:
        warnings.simplefilter("always")
        _warn_if_can_use_tool_shadowed(opcoes)

    assert avisos == []


def test_o_comando_do_cli_que_o_sdk_monta():
    """O que chega ao CLI, montado pelo proprio SDK: e o que liga cada opcao
    ao comportamento medido."""
    comando = SubprocessCLITransport("", _opcoes_de(agente(regras=("R",))))._build_command()

    assert comando[comando.index("--tools") + 1] == ""
    assert comando[comando.index("--system-prompt") + 1] == "R"
    assert comando[comando.index("--model") + 1] == "modelo-de-teste"
    assert "--setting-sources=" in comando
    assert "--strict-mcp-config" in comando
    assert "--include-partial-messages" in comando
    assert "--no-session-persistence" not in comando
    assert any(parte.startswith("--session-id=") for parte in comando)
    assert "--allowedTools" not in comando
    assert "--max-turns" not in comando
    assert not any(parte.startswith("--resume") for parte in comando)
    assert "--fork-session" not in comando


# --------------------------------------------------------------------------
# O CLI embutido ou nenhum (DP-S-15, NFR-S-03)
# --------------------------------------------------------------------------


def test_dp_s_15_sem_o_cli_embutido_localizar_devolve_none(tmp_path):
    assert localizar_cli(tmp_path) is None
    assert localizar_cli() is not None


def test_nfr_s_03_sem_o_cli_o_turno_e_provedor_ausente_sem_subir(monkeypatch):
    monkeypatch.setattr(modulo_adaptador, "localizar_cli", lambda: None)
    fabrica = FabricaRoteirizada()

    async def cenario():
        sessoes = adaptador(fabrica)
        sessao = await sessoes.abrir(agente(), contexto_novo())
        eventos = await coletar(sessoes.enviar(sessao, "oi"))
        return eventos, sessoes.estado(sessao)

    eventos, estado = executar(cenario())

    assert eventos == [FalhaDoTurno(MotivoFalhaDeSessao.PROVEDOR_AUSENTE)]
    assert estado is Estado.SEM_CONEXAO
    assert fabrica.clientes == []  # nunca tentou subir, nem o claude do PATH


# --------------------------------------------------------------------------
# A permissao exata (DP-S-14, RN-S-11)
# --------------------------------------------------------------------------


def _decidir(permitidos, nome):
    async def cenario():
        return await permissao_exata(permitidos)(nome, {}, ToolPermissionContext(tool_use_id="t"))

    return executar(cenario())


def test_rn_s_11_permite_so_o_nome_exato():
    permitidos = {"mcp__ambiente__criar_etapa", "mcp__wiki__ler"}

    assert _decidir(permitidos, "mcp__ambiente__criar_etapa").behavior == "allow"
    assert _decidir(permitidos, "mcp__wiki__ler").behavior == "allow"


@pytest.mark.parametrize(
    "nome",
    [
        "mcp__ambiente__",
        "mcp__ambiente__*",
        "mcp__ambiente__criar_frente",  # o nome de outra sessao
        "MCP__AMBIENTE__CRIAR_ETAPA",
        "mcp__ambiente__criar_etapa ",
        "Bash",
        "Read",
        "",
    ],
)
def test_rn_s_11_nega_curinga_prefixo_e_nome_de_outra_sessao(nome, caplog):
    with caplog.at_level(logging.WARNING, logger="fishingrod.sessao"):
        decisao = _decidir({"mcp__ambiente__criar_etapa"}, nome)

    assert decisao.behavior == "deny"
    assert [r.levelno for r in caplog.records] == [logging.WARNING]


def test_rn_s_11_o_nome_negado_vai_ao_log_cortado(caplog):
    with caplog.at_level(logging.WARNING, logger="fishingrod.sessao"):
        _decidir(set(), "x" * 5_000)

    assert len(caplog.records[0].getMessage()) < 200
