# Component Inventory — FishingRod

**Data da análise**: 2026-08-16

---

## Application Packages

| Pacote | Propósito |
|---|---|
| `Ambiente/` | Núcleo de domínio: `Ambiente`, `Projeto`, `Sessao`, `Chat`, `Memoria`, `Agente` |
| `model/` | Vocabulário compartilhado: `Comando`, `Mensagem` |
| `cli.py` (módulo raiz) | Interface de terminal (REPL + menu inicial) |
| `tui.py` (módulo raiz) | Interface Textual |

**Observação**: nenhum dos dois pacotes tem `__init__.py`. Funcionam como *namespace packages*
e só resolvem quando o processo roda a partir da raiz do repositório.

---

## Infrastructure Packages

**Nenhum.** Sem CDK, Terraform, CloudFormation, Docker ou script de deploy.

---

## Shared Packages

| Pacote | Tipo | Propósito |
|---|---|---|
| `model/` | Models | `Mensagem` (dado trafegado) e `Comando` (vocabulário fechado). Consumido por núcleo **e** interfaces |

---

## Test Packages

| Pacote | Tipo | Propósito |
|---|---|---|
| `testes-de-aprendizado/` | Spike / experimento | `spike_claudeSDK.py` — validou closure + tool MCP in-process + isolamento de autor, com 7 descobertas medidas. `teste-dict.py` — experimento avulso |

**Não há testes automatizados**: nenhum `pytest`, `unittest`, `tests/` ou CI. O nome da pasta é
literal — são *testes de aprendizado*, não suíte de regressão.

---

## Documentation and Design Assets

| Item | Tipo | Propósito |
|---|---|---|
| `docs/aidlc-inputs/vision.md` | Entrada AI-DLC | Vision Document v0, com marcação de origem e confiança |
| `produto/` | Descoberta | 12 arquivos: dores, princípios, glossário, cenários, requisitos funcionais, critérios de sucesso, hipóteses, questões abertas |
| `informacoes-usuario/` | Material bruto | Insumo do usuário (`interface-v3-nexus.html`) |
| `interface_ilustrativa.html` | Maquete | ~55 KB; wiki, kanban, memória da sessão |
| `CLAUDE.md` | Regras do processo | Workflow AI-DLC do repositório |
| `.aidlc-rule-details/` | Regras do processo | Detalhamento por estágio + 3 extensões |

---

## Total Count

- **Total de pacotes de código**: 4 (`Ambiente/`, `model/`, `testes-de-aprendizado/`, módulos raiz)
- **Application**: 2 (`Ambiente/`, módulos raiz `cli.py` + `tui.py`)
- **Infrastructure**: 0
- **Shared**: 1 (`model/`)
- **Test**: 1 (`testes-de-aprendizado/`, spike apenas)
- **Arquivos Python**: 10
- **Linhas de Python (produção)**: ~591 (`Ambiente/` 464 + `model/` 30 + `cli.py` 77 + ... )
- **Linhas de Python (spike)**: ~476
- **Classes de domínio**: 8 (`Ambiente`, `Projeto`, `Sessao`, `Chat`, `Memoria`, `Anotacao`, `Agente`, `Mensagem`) + 2 enums (`Comando`, `Papel`) + 2 implementações de agente
