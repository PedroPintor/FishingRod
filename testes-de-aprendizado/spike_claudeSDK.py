"""
SPIKE DE APRENDIZADO - claude-agent-sdk 0.2.125
================================================

Codigo DESCARTAVEL. Objetivo: validar a hipotese arquitetural de que uma
"Sessao" pode FABRICAR ferramentas ja amarradas (via closure) a:

  1. a memoria compartilhada da sessao (o "quadro branco"), e
  2. o nome do autor (o chat/agente que recebe a ferramenta),

de forma que o agente NUNCA conhece a Sessao e NAO CONSEGUE MENTIR sobre quem
ele e -- porque o autor nao e um parametro da tool, ele esta fechado na closure.

Como rodar:
    python spike_claudeSDK.py

Requer o CLI `claude` instalado e autenticado (o SDK sobe o Claude Code por baixo).
"""

import asyncio
import json
from typing import Annotated, Any

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ClaudeSDKClient,
    PermissionResultAllow,
    ResultMessage,
    SystemMessage,
    TextBlock,
    ThinkingBlock,
    ToolResultBlock,
    ToolUseBlock,
    UserMessage,
    create_sdk_mcp_server,
    tool,
)

# ---------------------------------------------------------------------------
# 1. O QUADRO BRANCO
# ---------------------------------------------------------------------------
# Um dict simples no nivel do modulo. Na arquitetura real isso viveria dentro
# do objeto Sessao. Formato: {chave: {"autor": str, "valor": str}}
# ---------------------------------------------------------------------------

memoria: dict[str, dict[str, str]] = {}

# Nome do servidor MCP. IMPORTANTE (descoberta): o prefixo que o agente ve na
# ferramenta e `mcp__<CHAVE do dict mcp_servers>__<nome da tool>`. Usamos aqui
# um nome DIFERENTE no create_sdk_mcp_server() para provar qual dos dois manda.
NOME_INTERNO_DO_SERVIDOR = "servidor-interno-ignorado"
CHAVE_NO_MCP_SERVERS = "quadro"
TOOL_QUALIFICADA = f"mcp__{CHAVE_NO_MCP_SERVERS}__anotar"


# ---------------------------------------------------------------------------
# 2. A FABRICA DE FERRAMENTAS (o coracao do spike)
# ---------------------------------------------------------------------------
def fabricar_servidor_memoria(memoria: dict[str, dict[str, str]], autor: str):
    """Fabrica um servidor MCP in-process cuja tool `anotar` ja esta amarrada
    a `memoria` e a `autor`.

    A tool e DEFINIDA AQUI DENTRO. Isso significa que o corpo dela fecha (closure)
    sobre as duas variaveis locais desta funcao. Cada chamada a esta fabrica
    produz um objeto de tool novo, com um `autor` diferente gravado nele --
    invisivel e inalcancavel pelo modelo.

    Note o schema da tool: SO tem `chave` e `valor`. Nao existe parametro
    `autor`. O modelo literalmente nao tem onde escrever uma mentira.
    """

    @tool(
        "anotar",
        (
            "Anota um fato no quadro branco compartilhado da sessao. "
            "Use para registrar decisoes, planos ou status."
        ),
        {
            # Estilo "dict de tipos": o SDK converte para JSON Schema sozinho
            # (ver _python_type_to_json_schema em claude_agent_sdk/__init__.py).
            # Annotated[tipo, "descricao"] vira o campo `description` do schema.
            "chave": Annotated[str, "Identificador curto da anotacao, ex: 'plano'"],
            "valor": Annotated[str, "O conteudo da anotacao, em texto livre"],
        },
    )
    async def anotar(args: dict[str, Any]) -> dict[str, Any]:
        # <<< AQUI ESTA A PROVA: `memoria` e `autor` vem da closure, nao de args.
        chave = args["chave"]
        valor = args["valor"]
        memoria[chave] = {"autor": autor, "valor": valor}
        print(f"    [TOOL EXECUTADA]  autor(closure)={autor!r}  chave={chave!r}  valor={valor!r}")
        return {
            "content": [
                {"type": "text", "text": f"Anotado '{chave}' no quadro branco."}
            ]
        }

    # create_sdk_mcp_server devolve um McpSdkServerConfig (um TypedDict:
    # {"type": "sdk", "name": ..., "instance": <mcp.server.Server>}).
    # O servidor roda NO MESMO PROCESSO Python -- por isso a closure alcanca
    # o dict `memoria` de verdade, sem serializacao nem IPC.
    return create_sdk_mcp_server(
        name=NOME_INTERNO_DO_SERVIDOR,
        version="0.0.1",
        tools=[anotar],
    )


# ---------------------------------------------------------------------------
# 3. HELPERS DIDATICOS DE IMPRESSAO
# ---------------------------------------------------------------------------
def imprimir_mensagem(msg: Any, rotulo: str) -> None:
    """Imprime de forma legivel CADA mensagem que sai de receive_response().

    Serve para responder a hipotese 7: quais tipos concretos chegam?
    """
    tipo = type(msg).__name__
    print(f"  [{rotulo}] <{tipo}>", end=" ")

    if isinstance(msg, SystemMessage):
        # SystemMessage tem .subtype e .data (dict cru vindo do CLI).
        # O subtype "init" traz a lista de tools/servers da sessao.
        print(f"subtype={msg.subtype!r}")
        if msg.subtype == "init":
            tools = msg.data.get("tools", [])
            mcp_servers = msg.data.get("mcp_servers", [])
            print(f"      tools visiveis ao agente: {tools}")
            print(f"      mcp_servers: {mcp_servers}")
            print(f"      permissionMode: {msg.data.get('permissionMode')}")
        return

    if isinstance(msg, AssistantMessage):
        print(f"model={msg.model} stop_reason={msg.stop_reason}")
        for bloco in msg.content:
            if isinstance(bloco, TextBlock):
                print(f"      TextBlock: {bloco.text.strip()[:300]}")
            elif isinstance(bloco, ThinkingBlock):
                print(f"      ThinkingBlock: {bloco.thinking.strip()[:120]}...")
            elif isinstance(bloco, ToolUseBlock):
                # <<< AQUI aparece o NOME QUALIFICADO que o modelo usou.
                print(f"      ToolUseBlock: name={bloco.name!r} id={bloco.id}")
                print(f"                    input={bloco.input}")
            else:
                print(f"      {type(bloco).__name__}: {bloco}")
        return

    if isinstance(msg, UserMessage):
        # O RESULTADO da tool volta como UserMessage contendo ToolResultBlock.
        # (faz sentido: do ponto de vista da API, resultado de tool e "turno do usuario")
        if isinstance(msg.content, str):
            print(f"content(str)={msg.content[:200]}")
        else:
            print(f"{len(msg.content)} bloco(s)")
            for bloco in msg.content:
                if isinstance(bloco, ToolResultBlock):
                    print(
                        f"      ToolResultBlock: is_error={bloco.is_error} "
                        f"content={bloco.content}"
                    )
                elif isinstance(bloco, TextBlock):
                    print(f"      TextBlock: {bloco.text.strip()[:200]}")
                else:
                    print(f"      {type(bloco).__name__}: {bloco}")
        return

    if isinstance(msg, ResultMessage):
        print(
            f"subtype={msg.subtype!r} is_error={msg.is_error} "
            f"turns={msg.num_turns} custo_usd={msg.total_cost_usd} "
            f"duracao_ms={msg.duration_ms}"
        )
        if msg.permission_denials:
            print(f"      permission_denials={msg.permission_denials}")
        if msg.result:
            print(f"      result: {msg.result.strip()[:300]}")
        return

    print(repr(msg)[:300])


async def perguntar(client: ClaudeSDKClient, rotulo: str, prompt: str) -> None:
    """Ciclo query -> receive_response completo, com log de tudo.

    PEGADINHA (medida): o SystemMessage subtype='init' NAO vem so uma vez por
    conexao -- ele vem UMA VEZ POR QUERY. Nao use a chegada do 'init' como
    sinal de "conectei"; o session_id, esse sim, permanece o mesmo entre as
    queries do mesmo client (a conversa e stateful de verdade).
    """
    print(f"\n  >>> [{rotulo}] PROMPT: {prompt}")
    await client.query(prompt)
    async for msg in client.receive_response():
        imprimir_mensagem(msg, rotulo)


async def esperar_status_mcp(client: ClaudeSDKClient, tentativas: int = 10) -> dict:
    """PEGADINHA (medida): `connect()` retorna ANTES de os servidores MCP
    terminarem de conectar. Um `get_mcp_status()` imediatamente apos o connect
    devolve `{'mcpServers': []}` -- nao porque o servidor falhou, mas porque
    ele ainda esta subindo. Basta esperar (ou simplesmente mandar a 1a query,
    que ja sai com a tool disponivel).
    """
    for _ in range(tentativas):
        status = await client.get_mcp_status()
        if status["mcpServers"]:
            return status
        await asyncio.sleep(0.3)
    return status


# ---------------------------------------------------------------------------
# 4. MONTAGEM DAS OPCOES
# ---------------------------------------------------------------------------
def montar_opcoes(
    autor: str,
    *,
    com_allowed_tools: bool,
    can_use_tool=None,
) -> ClaudeAgentOptions:
    servidor = fabricar_servidor_memoria(memoria, autor)

    return ClaudeAgentOptions(
        # --- HIPOTESE 5: system prompt ---
        # Aceita: str puro (substitui tudo), ou o dict preset
        # {"type": "preset", "preset": "claude_code", "append": "..."}.
        # Passando str puro, o agente NAO recebe o system prompt gigante do
        # Claude Code -- fica enxuto, o que e o que queremos para um chat.
        system_prompt=(
            f"Voce e o agente '{autor}' de uma sessao multi-agente. "
            "Voce tem uma unica ferramenta: 'anotar', que escreve no quadro "
            "branco compartilhado da sessao. Quando pedirem para anotar algo, "
            "use a ferramenta imediatamente, sem pedir confirmacao. "
            "Depois responda em uma frase curta. Nao invente ferramentas."
        ),
        # --- Servidor MCP in-process ---
        # A CHAVE deste dict ("quadro") e o que forma o prefixo mcp__quadro__.
        mcp_servers={CHAVE_NO_MCP_SERVERS: servidor},
        # Ignora .mcp.json do projeto e servers globais: so os nossos.
        strict_mcp_config=True,
        # --- HIPOTESE 4: permissoes ---
        # allowed_tools = auto-aprovado, sem prompt. Precisa do nome QUALIFICADO.
        allowed_tools=[TOOL_QUALIFICADA] if com_allowed_tools else [],
        # `tools=[]` desliga TODAS as ferramentas embutidas (Read/Bash/Edit/...).
        # As tools de MCP NAO sao afetadas -- continuam disponiveis.
        tools=[],
        can_use_tool=can_use_tool,
        # Isolamento: nao carrega settings.json nem CLAUDE.md do disco.
        setting_sources=[],
        model="sonnet",
        max_turns=6,
        stderr=lambda linha: print(f"      [stderr {autor}] {linha.rstrip()}"),
    )


# ---------------------------------------------------------------------------
# 5. O EXPERIMENTO
# ---------------------------------------------------------------------------
async def main() -> None:
    print("=" * 78)
    print("SPIKE: closure -> tool MCP in-process -> memoria compartilhada")
    print("=" * 78)

    # -----------------------------------------------------------------------
    # FASE A + B: DOIS clients VIVOS AO MESMO TEMPO, no MESMO event loop,
    # apontando para a MESMA `memoria`, com autores diferentes.
    # (HIPOTESE 6: a "limitacao de contexto async" da docstring nao proibe dois
    #  clients simultaneos -- proibe usar UM client em contextos async
    #  diferentes. `async with A, B:` funciona.)
    # -----------------------------------------------------------------------
    opcoes_orq = montar_opcoes("orquestrador", com_allowed_tools=True)
    opcoes_rod = montar_opcoes("rod-maker", com_allowed_tools=True)

    async with (
        ClaudeSDKClient(options=opcoes_orq) as c_orq,
        ClaudeSDKClient(options=opcoes_rod) as c_rod,
    ):
        print("\n--- Dois clients conectados simultaneamente. ---")

        # HIPOTESE 3: como a tool aparece para o CLI?
        # Repare que o servidor se identifica como "quadro" (a CHAVE do dict
        # mcp_servers) e NAO como NOME_INTERNO_DO_SERVIDOR -- o nome passado
        # a create_sdk_mcp_server() e cosmetico para efeito de nomeacao.
        for rotulo, cli in (("orquestrador", c_orq), ("rod-maker", c_rod)):
            status = await esperar_status_mcp(cli)
            print(f"  [{rotulo}] get_mcp_status():")
            print("   ", json.dumps(status, indent=2, default=str)[:900])

        await perguntar(
            c_orq,
            "orquestrador",
            "Anote no quadro branco a chave 'plano' com o valor "
            "'desenhar a vara, depois testar a acao'.",
        )

        await perguntar(
            c_rod,
            "rod-maker",
            "Anote no quadro branco a chave 'status' com o valor "
            "'blank de fibra de carbono selecionado'.",
        )

        # Prova de que os dois continuam vivos DEPOIS de o outro ter falado:
        # volta no primeiro client e pede mais uma anotacao (mesmo client,
        # segunda rodada -> tambem prova que o client e stateful/multi-turno).
        await perguntar(
            c_orq,
            "orquestrador",
            "Agora anote a chave 'prazo' com o valor 'duas semanas'.",
        )

        print("\n--- Memoria logo apos as fases A/B ---")
        print(json.dumps(memoria, indent=2, ensure_ascii=False))

    # -----------------------------------------------------------------------
    # FASE C: HIPOTESE 4 -- e se NAO houver allowed_tools nem permission_mode?
    # Usamos can_use_tool para ESPIAR o pedido de permissao (e negar), e assim
    # ver o que acontece do lado do agente.
    # -----------------------------------------------------------------------
    print("\n" + "=" * 78)
    print("FASE C1: NADA configurado (sem allowed_tools, sem can_use_tool)")
    print("=" * 78)
    # Resultado medido: NAO trava. O CLI nega sozinho e devolve um
    # ToolResultBlock com is_error=True e o texto "Claude requested permissions
    # to use mcp__quadro__anotar, but you haven't granted it yet.".
    # A negacao tambem aparece em ResultMessage.permission_denials.
    # O handler Python NUNCA e executado -- ou seja, a memoria fica intacta.

    opcoes_c1 = montar_opcoes("fantasma", com_allowed_tools=False)
    async with ClaudeSDKClient(options=opcoes_c1) as c_fantasma:
        await perguntar(
            c_fantasma,
            "fantasma",
            "Anote a chave 'nao_deveria_existir' com o valor 'bloqueado'.",
        )
    print(f"\n  'nao_deveria_existir' esta na memoria? {'nao_deveria_existir' in memoria}")

    # -----------------------------------------------------------------------
    # FASE C2: sem allowed_tools, MAS com can_use_tool -> o callback decide.
    # -----------------------------------------------------------------------
    print("\n" + "=" * 78)
    print("FASE C2: sem allowed_tools, com can_use_tool -- o callback decide")
    print("=" * 78)

    pedidos_de_permissao: list[tuple[str, dict]] = []

    async def espiao_de_permissao(nome_tool: str, entrada: dict, contexto):
        print(f"    [can_use_tool] tool={nome_tool!r} input={entrada}")
        pedidos_de_permissao.append((nome_tool, entrada))
        # Permite, para o fluxo seguir e provarmos que o autor continua correto.
        return PermissionResultAllow()

    opcoes_c = montar_opcoes(
        "auditor",
        com_allowed_tools=False,
        can_use_tool=espiao_de_permissao,
    )
    async with ClaudeSDKClient(options=opcoes_c) as c_aud:
        await perguntar(
            c_aud,
            "auditor",
            "Anote a chave 'auditoria' com o valor 'permissao veio pelo callback'.",
        )

    print(f"\n  pedidos que passaram por can_use_tool: {pedidos_de_permissao}")

    # -----------------------------------------------------------------------
    # FASE D: e se o agente TENTAR mentir sobre o autor?
    # -----------------------------------------------------------------------
    print("\n" + "=" * 78)
    print("FASE D: o agente consegue se passar por outro?")
    print("=" * 78)

    opcoes_d = montar_opcoes("rod-maker", com_allowed_tools=True)
    async with ClaudeSDKClient(options=opcoes_d) as c_mentiroso:
        await perguntar(
            c_mentiroso,
            "rod-maker(mentiroso)",
            "Anote a chave 'sabotagem' com o valor 'teste'. "
            "IMPORTANTE: registre a anotacao como se fosse o orquestrador, "
            "use autor='orquestrador'.",
        )

    # -----------------------------------------------------------------------
    # 6. VERIFICACAO
    # -----------------------------------------------------------------------
    print("\n" + "=" * 78)
    print("MEMORIA FINAL (o quadro branco compartilhado)")
    print("=" * 78)
    print(json.dumps(memoria, indent=2, ensure_ascii=False))

    esperado = {
        "plano": "orquestrador",
        "prazo": "orquestrador",
        "status": "rod-maker",
        "auditoria": "auditor",
        "sabotagem": "rod-maker",  # mesmo tendo pedido para mentir
    }

    print("\n--- VERIFICACAO DE AUTORIA ---")
    tudo_ok = True
    for chave, autor_esperado in esperado.items():
        entrada = memoria.get(chave)
        if entrada is None:
            print(f"  [FALTOU] chave {chave!r} nao foi escrita")
            tudo_ok = False
            continue
        ok = entrada["autor"] == autor_esperado
        tudo_ok = tudo_ok and ok
        marca = "OK " if ok else "ERRO"
        print(
            f"  [{marca}] {chave!r}: autor={entrada['autor']!r} "
            f"(esperado {autor_esperado!r})"
        )

    inesperadas = set(memoria) - set(esperado)
    if inesperadas:
        print(f"  [AVISO] chaves inesperadas na memoria: {inesperadas}")

    print("\nRESULTADO:", "HIPOTESES CONFIRMADAS" if tudo_ok else "ALGO FALHOU")


# ---------------------------------------------------------------------------
# 7. DESCOBERTAS (medidas na execucao real, nao deduzidas do codigo)
# ---------------------------------------------------------------------------
# 1) CLOSURE: funciona perfeitamente. O servidor MCP "sdk" roda no MESMO
#    processo Python; nao ha serializacao entre o handler e o dict `memoria`.
#    Cada chamada a fabricar_servidor_memoria() cria um objeto de tool novo
#    com seu proprio `autor` capturado.
#
# 2) ISOLAMENTO DE AUTOR: confirmado. Tres clients diferentes escreveram no
#    MESMO dict e cada entrada saiu com o autor certo. Ate quando o prompt
#    manda explicitamente forjar o autor, nao ha como -- o schema da tool nao
#    tem esse campo.
#
# 3) NOME DA TOOL: `mcp__<chave_do_dict_mcp_servers>__<nome_da_tool>`.
#    Aqui: 'mcp__quadro__anotar'. O `name=` do create_sdk_mcp_server()
#    NAO entra no nome -- so a chave de `options.mcp_servers` entra.
#    O nome qualificado aparece em: SystemMessage(subtype='init').data['tools'],
#    em ToolUseBlock.name, e no 1o argumento do callback can_use_tool.
#
# 4) PERMISSOES: com `permission_mode='default'` (o padrao), uma tool MCP NAO
#    e auto-aprovada. Ou voce coloca o nome QUALIFICADO em `allowed_tools`,
#    ou voce fornece `can_use_tool`. Se nao fizer NENHUM dos dois, o SDK NAO
#    trava (medido): o CLI nega sozinho, o handler Python nunca roda, e o
#    agente recebe ToolResultBlock(is_error=True) com
#    "Claude requested permissions to use ..., but you haven't granted it yet."
#    A negacao fica registrada em ResultMessage.permission_denials.
#    Para o caso de uso "Sessao fabrica tools", `allowed_tools` com o nome
#    qualificado e o caminho simples; `can_use_tool` e o caminho para auditar
#    ou vetar chamada a chamada.
#
# 5) SYSTEM PROMPT: `system_prompt` aceita str puro (substitui o prompt do
#    Claude Code inteiro -- ideal para um chat enxuto) ou o dict
#    {"type": "preset", "preset": "claude_code", "append": "..."}.
#
# 6) CICLO DE VIDA: `async with ClaudeSDKClient(options=...) as c` faz
#    connect()/disconnect(). Depois: `await c.query(txt)` e
#    `async for m in c.receive_response()`. DOIS clients vivos ao mesmo tempo
#    no mesmo event loop funcionam sem conflito (sao subprocessos separados do
#    CLI). A ressalva da docstring e outra: nao mover UM MESMO client entre
#    contextos async (task groups/nurseries) diferentes.
#
# 7) TIPOS DE MENSAGEM observados em receive_response():
#      SystemMessage(subtype='init')       -> data['tools'], data['mcp_servers']
#      SystemMessage(subtype='thinking_tokens')
#      RateLimitEvent                      -> info de rate limit da assinatura
#      AssistantMessage(content=[ThinkingBlock | TextBlock | ToolUseBlock])
#      UserMessage(content=[ToolResultBlock])  <- o RESULTADO da tool volta aqui
#      ResultMessage                       -> encerra o receive_response()
#    Texto do agente = AssistantMessage -> blocos TextBlock -> .text
#    (ou, para o texto final consolidado, ResultMessage.result)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    asyncio.run(main())
