# D16 — Agentes sem as ferramentas da máquina e sem a configuração do Claude Code

Status: revisada
Data do status: 2026-10-20

## O que é

Os agentes do FishingRod não recebem nenhuma das ferramentas que o Claude Code tem por padrão (ler
e escrever arquivos, rodar comandos etc.). Só usam as ferramentas que o próprio FishingRod dá a
cada um. Eles também não leem a configuração do Claude Code da máquina: nem `CLAUDE.md`, nem
servidores MCP, hooks, plugins ou skills. No código: `tools=[]`, `setting_sources=[]` e `skills=[]`.

## Por quê

Um agente do FishingRod só deve conseguir fazer o que o software permite, e cada ferramenta própria
funciona como uma cerca. Se ele herdasse a configuração do Claude Code do Pedro, o comportamento
mudaria de máquina para máquina, e o que está no `CLAUDE.md` do projeto entraria nos agentes do
produto. Os agentes do Claude Code e os agentes do FishingRod são coisas diferentes.

## O que descobrimos sobre o SDK

- O SDK, por padrão, carrega a configuração da máquina. Por isso cada opção é escrita por
  extenso, inclusive as que ficam vazias, e um teste confere uma por uma.
- O FishingRod usa o programa do Claude que vem **embutido** no pacote do SDK, nunca o `claude` do
  `PATH`. O da máquina se atualiza sozinho e mudaria a versão sem aviso. Sem o embutido, a
  conversa falha com "provedor ausente" em vez de usar outro.
- Mesmo sem o prompt do Claude Code, o programa do Claude sempre põe uma linha de apresentação
  ("You are a Claude agent, built on Anthropic's Claude Agent SDK.") antes das regras do agente.
  Não há opção que a tire.
- A conversa não é copiada para `~/.claude/projects/` (opção `no-session-persistence`).
- Os testes marcados `sdk_real` usam o Claude de verdade e gastam a assinatura. Ficam fora da
  suíte padrão e só rodam com `uv run pytest -m sdk_real`.

## Onde aparece no código

- `src/fishingrod/adaptadores/sessao/opcoes.py` (`montar_opcoes`, `localizar_cli`, `permissao_exata`)
- `tests/sessao/test_opcoes.py`, `tests/sessao/test_sdk_real.py`
