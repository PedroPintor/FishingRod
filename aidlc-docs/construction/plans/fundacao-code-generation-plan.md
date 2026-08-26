# Code Generation Plan — U0 `fundacao`

**Fase:** CONSTRUCTION · **Unidade:** `U0 fundacao` (passo 0, fora do loop de design — Q3=C / R5)
**Data:** 2026-08-25 · **Base:** `inception/application-design/unit-of-work.md` §3 (U0) e §4 (layout)
**Estágios da unidade:** FD SKIP · NFR-R SKIP · NFR-D SKIP · INFRA SKIP · **CG EXECUTE**
(motivos já registrados e aprovados em `unit-of-work.md` §3)

> **Este plano é a única fonte de verdade da geração de código de U0.** A Parte 2 executa
> exatamente estes passos, na ordem, marcando `[x]` a cada conclusão. Nada fora daqui é gerado.

---

## 1. Contexto da unidade

| Campo | Conteúdo |
|---|---|
| **Histórias** | **Nenhuma.** U0 é infraestrutura de build; declarado em `unit-of-work-story-map.md` §3 |
| **Depende de** | — (primeira unidade) |
| **Entrega para** | Todas as demais: `uv sync` e `uv run pytest` funcionando, e o pacote `src/fishingrod/` existindo vazio |
| **Dívidas técnicas** | Nenhuma |
| **Requisitos rastreados** | **ESC-15** (scaffolding `uv`, `pyproject.toml`, `uv.lock`, layout `src/`, `exclude-newer`) · **SECURITY-10** (dependências diretas travadas) |
| **Extensões** | `property-based-testing` — só a **instalação** de `hypothesis`; nenhuma propriedade é escrita aqui (a primeira é de U1) |

### Ambiente verificado antes de planejar

- `uv 0.11.6` instalado · `Python 3.13.14`
- Código atual na raiz: `Ambiente/`, `model/`, `cli.py`, `tui.py`, `testes-de-aprendizado/`
- **Nenhum** `pyproject.toml`, `requirements.txt` ou `uv.lock` existe hoje (confirma o achado da
  engenharia reversa)

### Regra de coexistência (Q8=A)

Nada do código atual é movido, reescrito ou apagado nesta unidade. `Ambiente/`, `model/`, `cli.py`,
`tui.py` continuam funcionando como estão. O `pyproject.toml` empacota **apenas** `src/fishingrod/`,
e é isso que impede o build de tentar recolher os módulos antigos da raiz.

---

## 2. Decisões pequenas tomadas neste plano (declaradas, não perguntadas)

Coisas reversíveis que nenhum estágio anterior fixou. Se discordar de qualquer uma, é hora de dizer.

| Decisão | Escolha | Motivo |
|---|---|---|
| Nome do pacote | `fishingrod` | Já é o nome usado no layout de `unit-of-work.md` §4 |
| `requires-python` | ~~`>=3.13`~~ **`>=3.14`** | ~~É a versão em uso; frouxo demais obrigaria a testar o que ninguém roda~~ **[emenda 2026-08-25T21:00:00Z, durante o FD de U1]** O usuário perguntou por que não subir a versão em vez de contornar a ausência de `uuid.uuid7()` no 3.13 (CQ2=D). Verificado: 3.14.4 tem `uuid.uuid7()`, e `claude-agent-sdk` + `textual` resolvem **e importam** nela. `pyproject.toml` alterado, `.venv` recriado, `uv.lock` regerado, `uv run pytest` = 2 passed. Motivo da escolha original era fraco ("é a versão em uso") e não era restrição de ninguém |
| `exclude-newer` | `2026-08-25` (data de hoje) | ESC-15 pede política de idade mínima; a data congela o universo de resolução e torna o `uv.lock` reprodutível |
| Runner de teste | `pytest` | Único citado nos artefatos de desenho |
| `pytest-asyncio` | **Não entra agora** | Nada async existe antes de U6; entra no `pyproject.toml` quando U6 precisar |
| Linter / formatador | **Não entra** | Nenhum estágio anterior decidiu adotar um; acrescentar aqui seria escopo novo sem aprovação |
| Build backend | `hatchling` | Padrão para layout `src/`, sem configuração extra |

---

## 3. Passos de geração

> **Executado em 2026-08-25T19:30:00Z — 7/7 passos concluídos.** Resultado e evidências em
> `aidlc-docs/construction/fundacao/code/code-summary.md`. O Step 5 fechou sem alteração: o
> `.gitignore` já estava correto.


### Step 1 — `pyproject.toml` na raiz

- [x] Criar `pyproject.toml` com: nome `fishingrod`, versão `0.1.0`, `requires-python = ">=3.13"`
- [x] Build backend `hatchling`, empacotando **somente** `src/fishingrod`
- [x] Dependências de runtime: **nenhuma ainda** (`claude-agent-sdk` entra em U6, `textual` em U9)
- [x] Grupo de dependências de desenvolvimento: `pytest`, `hypothesis`
- [x] `[tool.uv]` com `exclude-newer`
- [x] `[tool.pytest.ini_options]` com `testpaths = ["tests"]`
- **Rastreio**: ESC-15, SECURITY-10

### Step 2 — Layout `src/fishingrod/` (camada no topo, Q9=A)

- [x] Criar `src/fishingrod/__init__.py`
- [x] Criar os diretórios de camada, cada um com `__init__.py` vazio:
      `dominio/`, `aplicacao/`, `aplicacao/portas/`, `aplicacao/catalogo/`, `aplicacao/servicos/`,
      `adaptadores/`, `interface/`
- [x] **Nenhum arquivo de lógica** — os pacotes nascem vazios; quem os preenche é U1 em diante
- **Rastreio**: ESC-15, `unit-of-work.md` §4

### Step 3 — Estrutura de testes

- [x] Criar `tests/` com `__init__.py` e um `tests/test_fundacao.py` contendo **um** teste que
      importa `fishingrod` e afirma que o pacote resolve
- [x] Justificativa do teste existir: o critério de pronto de U0 exige `uv run pytest` executando; um
      arquivo de teste real prova a instalação editável do layout `src/`, o que "coletar 0 testes"
      não prova
- **Rastreio**: critério de pronto 2 de U0

### Step 4 — Resolver e travar dependências

- [x] Executar `uv sync` para criar `.venv` e **`uv.lock`**
- [x] Verificar que `uv.lock` foi criado na raiz e **não** está no `.gitignore`
- **Rastreio**: ESC-15, SECURITY-10

### Step 5 — Ajuste do `.gitignore`

- [x] Verificar que `.venv/` já está ignorado (está) e que `uv.lock` **não** está
- [x] Modificar **in-place** apenas se algo faltar; não reescrever o arquivo
- **Rastreio**: SECURITY-10 (lockfile versionado é o que trava a dependência de verdade)

### Step 6 — Verificação do critério de pronto de U0

- [x] `uv sync` conclui sem erro
- [x] `uv run pytest` executa e o teste do Step 3 passa
- [x] `uv run python -c "import fishingrod"` funciona
- [x] `Ambiente/`, `model/`, `cli.py` e `tui.py` continuam intactos (Q8=A)
- [x] Nenhum arquivo duplicado do tipo `*_new.py` / `*_modified.py` foi criado
- **Rastreio**: `unit-of-work.md` §3, critérios 1 a 4 de U0

### Step 7 — Resumo em markdown

- [x] Escrever `aidlc-docs/construction/fundacao/code/code-summary.md` com: arquivos criados,
      arquivos modificados, saída real dos comandos de verificação e o estado de cada critério
- [x] **Somente markdown** nesse diretório; nenhum código em `aidlc-docs/`
- **Rastreio**: regra de localização de `construction/code-generation.md`

---

## 4. O que este plano **não** faz

Declarado para o portão de aprovação não carregar expectativa errada:

- Não escreve entidade, porta, adaptador, serviço ou tela — isso é U1 a U9
- Não cria `dominio/politica.py` (a política de aprovação da rodada 4) — ela é de **U1**
- Não instala `claude-agent-sdk` nem `textual` — entram nas unidades que os usam, para que o
  critério "importar o núcleo com o SDK ausente" (U6, TD-02) continue testável
- Não move nem apaga o código atual
- Não configura CI, empacotamento para distribuição ou publicação

---

## 5. Escopo

**7 passos**, todos de infraestrutura. Nenhuma história implementada, nenhuma dívida técnica morta.
O produto de U0 é um projeto que instala, importa e roda teste — a base sem a qual as nove unidades
seguintes não têm onde ser verificadas.
