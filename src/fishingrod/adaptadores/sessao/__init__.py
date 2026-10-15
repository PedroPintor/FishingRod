"""Adaptador de sessao sobre o claude-agent-sdk (U6).

O unico pacote do projeto que importa `claude_agent_sdk` (RN-S-01). U9 importa
daqui o AdaptadorSessaoClaude; U7 e U8 falam com ele so pela PortaSessao.
"""

from fishingrod.adaptadores.sessao.adaptador import AdaptadorSessaoClaude

__all__ = ["AdaptadorSessaoClaude"]
