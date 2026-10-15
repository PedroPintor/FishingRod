# Tech Stack Decisions — U6 `sessao`

**Fase:** CONSTRUCTION · **Unidade:** `U6 sessao` · **Data:** 2026-10-06

---

## 1. Decisões

| # | Decisão | Origem | Alternativa rejeitada |
|---|---|---|---|
| **TS-S-01** | **`claude-agent-sdk==0.2.143`** em `dependencies`: a primeira e única dependência direta de runtime | Q1=A, Q2=A, NFR-S-01/02 | Extra opcional `fishingrod[claude]` (não há outro adaptador hoje); `0.2.125` do spike (presa ao MCP 1.x); `0.2.144` (sem pacote Windows sob o corte, §2) |
| **TS-S-02** | **CLI embutido no pacote do SDK**, passado pelo caminho, sem cair no `PATH` | Q3=A, NFR-S-03 | CLI da máquina (2.1.288, se atualiza sozinho e fura o travamento); configurável (mais um caminho sem uso) |
| **TS-S-03** | **Corte `exclude-newer = 2026-08-25` mantido** | ESC-15, Q2=A | Mover o corte (mexeria no lock do projeto inteiro) |
| **TS-S-04** | **`uv audit`** para varredura de vulnerabilidades | Q4=A, NFR-S-04 | `pip-audit` no grupo dev (dependência nova para o que o uv já faz) |
| **TS-S-05** | **Bloqueador de import em subprocesso** (`sys.meta_path`, biblioteca padrão) para o teste do TD-02, junto das varreduras estáticas existentes | Q5=A, NFR-S-07 | Segundo ambiente virtual sem o SDK (lento, fora da suíte na prática); só a varredura estática (não pega import dinâmico nem transitivo) |
| **TS-S-06** | **Marcador `sdk_real`** do pytest, fora da execução padrão | Q6=A, NFR-S-08 | Script fora do pytest (envelhece em silêncio); variável de ambiente com `skip` (polui a contagem de pulos) |
| **TS-S-07** | **`logging` da biblioteca padrão**, logger `fishingrod.sessao` com `NullHandler` | Q12=A, NFR-S-17 | Descartar a saída de erro do CLI (mudaria RN-S-54 e tiraria a principal pista de falha) |
| **TS-S-08** | Testes: **`pytest` + `hypothesis`**, já em `dependency-groups.dev` | PBT-09 | — |
| **TS-S-09** | **`asyncio`** no adaptador, com o SDK usando `anyio` por dentro. Cada sessão é usada sempre a partir do mesmo contexto assíncrono. **Emenda 2026-10-13 (NFR Design, Q1=A, `DP-S-01`): isso passa a ser garantido pela tarefa dona de cada conexão, que é a única a tocar o cliente do SDK; quem chama `enviar` não precisa mais cuidar disso** | Fato medido pelo spike (plano de FD §3) | — |

## 2. A decisão que exigiu medição: qual versão

```
$ uv pip compile (claude-agent-sdk, sem versão) --exclude-newer 2026-08-25 --python-version 3.14
claude-agent-sdk==0.2.144   + 31 transitivos

Publicação no PyPI:
0.2.144  macOS/Linux 2026-08-21   Windows 2026-08-25T22:46:28Z  <- depois do corte
0.2.143  todas as plataformas 2026-08-20                         <- última antes do corte

$ uv pip compile claude-agent-sdk==0.2.143 --python-platform x86_64-pc-windows-msvc
         --exclude-newer 2026-08-25 --only-binary :all:
Resolved 32 packages   (mcp 2.1.0, pydantic 2.13.4, cryptography 50.0.0, pywin32 312, ...)
```

Os pacotes prontos têm ~100 MB porque trazem o CLI do Claude. Sob o corte, no Windows, a `0.2.144`
viria como código-fonte, **sem o CLI**, e o SDK passaria a usar o `claude` da máquina sem avisar. A
`0.2.143` é a mais nova que não tem esse problema. TS-S-02 fecha o mesmo buraco por outro lado: mesmo
que um dia o CLI embutido falte, a sessão falha em vez de trocar de CLI.

**O que muda em relação ao spike:** a `0.2.125` exigia `mcp<2`; a `0.2.143` resolve `mcp 2.1.0`.
Tudo o que o spike mediu é medido de novo no Code Generation (medições 1–11 de `nfr-requirements.md`
§6). Se alguma falhar na `0.2.143` e passar na `0.2.125`, a troca é uma linha e fica registrada.

## 3. Riscos aceitos

| Risco | Por que aceito | Onde |
|---|---|---|
| Transitivos do lado servidor do MCP instalados sem uso | Não saem sem bifurcar o SDK; a varredura os cobre | NFR-S-05 |
| Turno travado sem cair só sai com o ESC | Um prazo mataria a espera da sua confirmação; coerente com a Q12=B do FD | NFR-S-12 |
| Processo do CLI órfão numa queda dura do Python | Medido antes de decidir; proteção por sistema operacional só se a medição mostrar o problema | NFR-S-16 |
| Pacote de ~100 MB por causa do CLI embutido | É o preço de o CLI ficar travado junto do SDK | TS-S-02 |
