"""As opcoes do SDK, escritas por extenso num arquivo so (DP-S-11..17).

E o arquivo de seguranca da unidade. O padrao do SDK carrega a configuracao da
maquina (A1): `setting_sources=None` le usuario, projeto e local, e
`skills=None` nao desliga as skills. Por isso toda opcao que importa e escrita
aqui, inclusive as que precisam ficar vazias, e um teste de inspecao confere
cada uma - inclusive as que ficam no valor padrao (nfr-design-patterns.md 5).

Recebe os servidores MCP ja montados e os nomes permitidos; nao importa nenhum
outro modulo do adaptador.
"""

import logging
import sys
from collections.abc import Collection, Mapping
from pathlib import Path
from typing import Any

import claude_agent_sdk
from claude_agent_sdk import (
    ClaudeAgentOptions,
    McpSdkServerConfig,
    PermissionResultAllow,
    PermissionResultDeny,
    ToolPermissionContext,
    get_session_info,
)
from claude_agent_sdk.types import CanUseTool

from fishingrod.dominio import Agente

# Cada modulo que registra instala o proprio NullHandler (R-ND6-14): sem destino
# configurado, nada vaza para a tela - quem decide o destino e U9.
_log = logging.getLogger("fishingrod.sessao")
_log.addHandler(logging.NullHandler())

# Um nome pedido pelo modelo vai ao log cortado: e texto de quem nao e confiavel.
_ECO_MAXIMO = 100


# --------------------------------------------------------------------------
# O CLI (DP-S-15, TS-S-02)
# --------------------------------------------------------------------------

_PASTA_DO_SDK = Path(claude_agent_sdk.__file__).parent


def localizar_cli(pasta_do_sdk: Path = _PASTA_DO_SDK) -> Path | None:
    """O CLI embutido no pacote do SDK, ou None. NUNCA o `claude` do PATH: o da
    maquina se atualiza sozinho e furaria o travamento da versao (NFR-S-03).
    Sem ele, o turno termina em PROVEDOR_AUSENTE sem tentar subir."""
    nome = "claude.exe" if sys.platform == "win32" else "claude"
    caminho = pasta_do_sdk / "_bundled" / nome
    return caminho if caminho.is_file() else None


# --------------------------------------------------------------------------
# A credencial (DP-S-12, RN-S-52, RN-S-53)
# --------------------------------------------------------------------------
# Variaveis que fazem o CLI usar outra credencial ou outro endereco. Cada uma
# vai para o `env` do processo com "" por cima: o SDK so ACRESCENTA ao ambiente
# herdado (A2), entao sobrescrever e o unico jeito de nao repassar. O valor
# nunca e lido. O CLI le estas variaveis por um ambiente tipado que faz
# `trim() || undefined`: vazio vale como ausente (medicao 5 confirma).
#
# Origem: as listas que o proprio CLI 2.1.238 embutido usa (conferidas no
# binario em 2026-10-13, passo 2 do plano). Proxy e certificado da maquina
# (HTTPS_PROXY, NODE_EXTRA_CA_CERTS) ficam: mudam a rota, nao a credencial,
# e tira-los quebraria a sessao de quem esta atras de um proxy.

# As credenciais do proprio CLI (lista QDe).
_CREDENCIAIS = (
    "ANTHROPIC_API_KEY",
    "ANTHROPIC_AUTH_TOKEN",
    "CLAUDE_CODE_OAUTH_TOKEN",
    "AWS_BEARER_TOKEN_BEDROCK",
    "ANTHROPIC_FOUNDRY_API_KEY",
    "ANTHROPIC_FOUNDRY_AUTH_TOKEN",
    "ANTHROPIC_AWS_API_KEY",
)
# Outras fontes de credencial que o CLI proibe a configuracao remota de mudar
# (lista EN_): token por descritor de arquivo, renovacao, identidade federada e
# credencial entregue por um host.
_OUTRAS_FONTES = (
    "CLAUDE_CODE_API_KEY_FILE_DESCRIPTOR",
    "CLAUDE_CODE_OAUTH_TOKEN_FILE_DESCRIPTOR",
    "CLAUDE_CODE_OAUTH_REFRESH_TOKEN",
    "CLAUDE_CODE_SESSION_ACCESS_TOKEN",
    "ANTHROPIC_IDENTITY_TOKEN",
    "ANTHROPIC_IDENTITY_TOKEN_FILE",
    "ANTHROPIC_FEDERATION_RULE_ID",
    "ANTHROPIC_PROFILE",
    "CLAUDE_CODE_HOST_CREDS_FILE",
    "CLAUDE_CODE_HOST_AUTH_ENV_VAR",
    "CLAUDE_CODE_PROVIDER_MANAGED_BY_HOST",
)
# Os enderecos (listas ZDe e tZt, mais o que a EN_ acrescenta).
_ENDERECOS = (
    "ANTHROPIC_BASE_URL",
    "_CLAUDE_CODE_ASSUME_FIRST_PARTY_BASE_URL",
    "ANTHROPIC_BEDROCK_BASE_URL",
    "ANTHROPIC_VERTEX_BASE_URL",
    "ANTHROPIC_FOUNDRY_BASE_URL",
    "ANTHROPIC_AWS_BASE_URL",
    "ANTHROPIC_GOOGLE_CLOUD_BASE_URL",
    "ANTHROPIC_BEDROCK_MANTLE_BASE_URL",
    "ANTHROPIC_CUSTOM_HEADERS",
    "ANTHROPIC_UNIX_SOCKET",
    "CLAUDE_CODE_API_BASE_URL",
    "CLAUDE_CODE_CUSTOM_OAUTH_URL",
)
# Os provedores alternativos (as chaves da lista JDe).
_PROVEDORES = (
    "CLAUDE_CODE_USE_BEDROCK",
    "CLAUDE_CODE_USE_VERTEX",
    "CLAUDE_CODE_USE_FOUNDRY",
    "CLAUDE_CODE_USE_ANTHROPIC_AWS",
    "CLAUDE_CODE_USE_ANTHROPIC_GOOGLE_CLOUD",
    "CLAUDE_CODE_USE_MANTLE",
    "CLAUDE_CODE_USE_GATEWAY",
)

VARIAVEIS_DE_CREDENCIAL: tuple[str, ...] = _CREDENCIAIS + _OUTRAS_FONTES + _ENDERECOS + _PROVEDORES


# --------------------------------------------------------------------------
# A conversa guardada pelo Claude (D22)
# --------------------------------------------------------------------------


def conversa_guardada(conversa: str, pasta_de_trabalho: Path) -> bool:
    """O Claude ainda guarda esta conversa? Ele a procura pela pasta de
    trabalho, entao a pergunta tambem. Sem ela (apagada, outro computador,
    parada ha mais de 30 dias), o chat recomeca do zero."""
    return get_session_info(conversa, directory=str(pasta_de_trabalho)) is not None


# --------------------------------------------------------------------------
# A espera da sua confirmacao (DP-S-16)
# --------------------------------------------------------------------------

# O maior valor aceito (~24,8 dias, o teto de um temporizador do Node): uma
# ferramenta que espera a pessoa decidir nao e cortada pelo CLI (medicao 2).
TEMPO_LIMITE_DE_FERRAMENTA_MS = 2147483647


# --------------------------------------------------------------------------
# A permissao (DP-S-14, N1)
# --------------------------------------------------------------------------


def permissao_exata(nomes: Collection[str]) -> CanUseTool:
    """O `can_use_tool`: permite os nomes qualificados EXATOS da sessao, nega
    todo o resto e registra a negacao. Nunca curinga, nunca prefixo (RN-S-11).

    E o unico ponto de decisao: `allowed_tools` fica vazio, porque o SDK nao
    chama o `can_use_tool` para o que `allowed_tools` ja liberou (A15).
    """
    permitidos = frozenset(nomes)

    async def can_use_tool(
        nome: str, entrada: dict[str, Any], contexto: ToolPermissionContext
    ) -> PermissionResultAllow | PermissionResultDeny:
        if isinstance(nome, str) and nome in permitidos:
            return PermissionResultAllow()
        _log.warning("ferramenta negada: [%s]", str(nome)[:_ECO_MAXIMO])
        return PermissionResultDeny(message="Esta ferramenta nao existe nesta sessao.")

    return can_use_tool


def _saida_de_erro(linha: str) -> None:
    """DP-S-17: nada do CLI chega ao terminal - a TUI de U9 nao pode ser
    desenhada por cima. Fica no log, so em DEBUG (RN-S-54)."""
    _log.debug("saida de erro do CLI: %s", linha)


# --------------------------------------------------------------------------
# As opcoes (nfr-design-patterns.md 5)
# --------------------------------------------------------------------------


def montar_opcoes(
    *,
    agente: Agente,
    cli: Path,
    pasta_de_trabalho: Path,
    servidores: Mapping[str, McpSdkServerConfig],
    permitidos: Collection[str],
    conversa: str,
    retomar: bool,
) -> ClaudeAgentOptions:
    """Linha por linha, o §5 de nfr-design-patterns.md. As diferencas: `model`,
    que vem do Agente (R-CG6-3), e a conversa (D22): o codigo dela e o id do
    chat, e `retomar` diz se o Claude ja a guarda (`resume`) ou se ela nasce
    agora com esse codigo (`session_id`).

    Ficam no valor padrao, de proposito: continue_conversation,
    fork_session (retomar continua na mesma conversa), add_dirs, plugins,
    max_turns (sem limite de passos, D-Q12-1), hooks, agents, session_store,
    permission_mode, permission_prompt_tool_name e user.
    """
    env = {nome: "" for nome in VARIAVEIS_DE_CREDENCIAL}
    env["MCP_TOOL_TIMEOUT"] = str(TEMPO_LIMITE_DE_FERRAMENTA_MS)
    return ClaudeAgentOptions(
        cli_path=cli,
        # Nenhuma ferramenta nativa do CLI, para nenhum agente (RN-S-10).
        tools=[],
        allowed_tools=[],
        can_use_tool=permissao_exata(permitidos),
        # Nenhuma configuracao da maquina: CLAUDE.md, servidores MCP, hooks,
        # plugins, permissoes, skills (A1).
        setting_sources=[],
        skills=[],
        strict_mcp_config=True,
        mcp_servers=dict(servidores),
        # So as regras do agente, sempre como texto - mesmo vazio, nunca o
        # prompt do Claude Code (G15, medicao 8).
        system_prompt="\n\n".join(agente.regras),
        model=agente.modelo,
        cwd=pasta_de_trabalho,
        include_partial_messages=True,
        env=env,
        # O Claude guarda a conversa em ~/.claude/projects/ e a retoma pelo
        # codigo (D22, que derruba DP-S-13; medicao 15 invertida).
        resume=conversa if retomar else None,
        session_id=None if retomar else conversa,
        stderr=_saida_de_erro,
    )
