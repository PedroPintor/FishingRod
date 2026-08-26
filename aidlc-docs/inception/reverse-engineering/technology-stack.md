# Technology Stack — FishingRod

**Data da análise**: 2026-08-16

---

## Programming Languages

| Linguagem | Versão | Uso |
|---|---|---|
| Python | 3.13 (evidência: `__pycache__/*.cpython-313.pyc`) | Toda a aplicação. Usa recursos modernos: `match`/`case` (3.10+), `X \| None` (3.10+), `@dataclass`, `Literal`, `Annotated` |
| HTML/CSS/JS | — | `interface_ilustrativa.html` (maquete, não executa contra o núcleo) |

**Requisito de versão**: `match`/`case` exige **Python ≥ 3.10**; nada no código exige 3.13
especificamente.

---

## Frameworks

| Framework | Versão | Propósito |
|---|---|---|
| `textual` | não declarada | Interface de terminal (`tui.py`): `App`, `Screen`, `Tree`, `ListView`, `RichLog`, `Input`, CSS embutido |
| `rich` | não declarada (dependência do `textual`) | `rich.markup.escape` — impede que texto do usuário vire marcação |
| `claude-agent-sdk` | `0.2.125` (só no cabeçalho do spike) | Primeiro adaptador de LLM. Usa `ClaudeSDKClient`, `ClaudeAgentOptions`, `create_sdk_mcp_server`, `@tool` |

**Biblioteca padrão em uso**: `dataclasses`, `enum`, `abc`, `typing`, `asyncio` (só no spike),
`json` (só no spike).

---

## Infrastructure

**Nenhuma.** Processo local único. Sem servidor, sem nuvem, sem container, sem porta de rede,
sem armazenamento persistente.

---

## Build Tools

**Nenhuma.** Não há `pyproject.toml`, `setup.py`, `requirements.txt`, `Pipfile`, `poetry.lock`,
`uv.lock` nem `Makefile`.

- **Execução**: `python cli.py` ou `python tui.py`, a partir da raiz do repositório.
- **Consequência**: as três dependências externas não estão declaradas em lugar nenhum do
  repositório. Reproduzir o ambiente exige conhecimento tácito.

---

## Testing Tools

**Nenhuma.** Sem `pytest`, `unittest`, `hypothesis`, `coverage`, `tox` ou CI.

`testes-de-aprendizado/` contém spikes exploratórios executados à mão, não uma suíte.

---

## Version Control and Process

| Ferramenta | Estado |
|---|---|
| Git | ✅ ativo — 1 commit (`14f81eb`, "Versiona o FishingRod: ambiente de orquestracao multi-agente") |
| `.gitignore` | ✅ completo — Python, venvs, segredos (`.env`), caches de teste, Windows/OneDrive, IDEs |
| CI/CD | ❌ ausente |
| Linter / formatter | ❌ nenhum configurado (`.ruff_cache`/`.mypy_cache` aparecem no `.gitignore`, mas nenhuma config existe) |

---

## Externalidades previstas (ainda não no stack)

| Item | Estado |
|---|---|
| Persistência (arquivo, SQLite, outro) | ❌ não escolhida — nem discutida |
| Servidores MCP externos | ❌ previstos no produto (RF-11, RF-12), não implementados |
| Segundo adaptador de LLM | ❌ o produto exige agnosticismo a provedor; hoje só há o Claude, incompleto |
| Interface web | ❌ existe apenas como maquete HTML |
