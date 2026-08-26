# Code Quality Assessment — FishingRod

**Data da análise**: 2026-08-16

---

## Test Coverage

- **Overall**: **None** — 0% automatizado.
- **Unit Tests**: ausentes.
- **Integration Tests**: ausentes.
- **Spikes exploratórios**: presentes (`testes-de-aprendizado/`), executados à mão. Valiosos como
  registro de aprendizado, **inúteis como rede de segurança** — não falham quando o código
  regride.

**Obstáculo concreto para começar a testar**: `Ambiente/agente.py:6` importa `claude_agent_sdk`.
Como `sessao.py` e `ambiente.py` importam `agente.py`, **qualquer** teste do núcleo exige o SDK
instalado. Remover esse import é pré-requisito prático para uma suíte rodar em CI.

---

## Code Quality Indicators

| Indicador | Estado | Detalhe |
|---|---|---|
| **Linting** | ❌ não configurado | Sem `ruff`, `flake8`, `pylint`. O `.gitignore` prevê `.ruff_cache`/`.mypy_cache`, mas não há config |
| **Type checking** | ❌ não configurado | Há anotações de tipo em quase tudo, mas nada as verifica — e há anotações **erradas** (ver Dívida Técnica) |
| **Code Style** | 🟡 majoritariamente consistente | Indentação de 4 espaços na maior parte; `cli.py` usa **5 espaços**; `Projeto.obter_status` e `Ambiente.buscar_projeto` têm indentação extra em bloco |
| **Documentation** | 🟢 boa onde importa | Docstrings em `tui.py` e no spike; comentários explicam **o porquê**, não o quê (`ambiente.py:55-56`, `sessao.py:76-81`, `tui.py:67-71`) — padrão acima da média |
| **Naming** | 🟢 consistente | Domínio inteiramente em português; sem acentos nos identificadores; constantes em maiúsculas |
| **Encoding** | 🟡 quase sem acentos | Código evita acentos, com exceções: `sessao.py:44` (`"não pode conter"`), `agente.py:39` (`"reposta é"`) |

---

## Technical Debt

Ordenado por gravidade.

### 🔴 TD-01 — `AgenteClaude.responder()` devolve `None`
**Local**: `Ambiente/agente.py:45-46`
```python
def responder(self, mensagem):
    return
```
Ligar este agente hoje produz `Mensagem(texto=None)`, e `tui.formatar` chama `escape(None)` →
`AttributeError`. É a dívida que bloqueia a transação de negócio central (conversar com IA de
verdade). Registrada como **[dívida]** em `vision.md` §3.2.

### 🔴 TD-02 — Provedor de LLM importado dentro do núcleo
**Local**: `Ambiente/agente.py:6` — `from claude_agent_sdk import ClaudeAgentOptions`
Viola a proibição explícita de `vision.md` §6.3. Consequências práticas: o núcleo não importa sem
o SDK; o agnosticismo a provedor (§6.4) fica só no papel; testes exigem o pacote.

### 🔴 TD-03 — `Memoria.anotar()` levanta `KeyError` na primeira anotação
**Local**: `Ambiente/memoria.py:16-19`
```python
self.anotacoes[chave].append(Anotacao(autor=autor, valor=valor))
```
`anotacoes` nasce vazio (`default_factory=dict`) e não há `setdefault`/`defaultdict`. **Toda**
primeira escrita em qualquer chave falha. O defeito está latente porque nenhum caminho de produção
chama o método — o que é, por si, o TD-04.

### 🔴 TD-04 — Persistência inexistente
Todo o estado morre com o processo. Nenhum ambiente, projeto, sessão, chat ou anotação sobrevive
a um fechamento. Impede o critério de sucesso CS-01 (reconstituir um ambiente) e a proposta
central do produto ("o contexto acumulado é o ativo").

### 🟠 TD-05 — Instâncias de agente globais e compartilhadas
**Local**: `Ambiente/agente.py:54-75`, usado em `Ambiente/ambiente.py:46`
`OrquestradorTeste` e `RodMakerTeste` são instâncias **de módulo**. Todo projeto novo aponta seu
primeiro chat para o **mesmo objeto**. Não há isolamento entre sessões, e `Sessao.listar_agentes()`
devolve o catálogo global em vez dos agentes da sessão.

### 🟠 TD-06 — Cadeia `enviar()` inteiramente síncrona
`input()` → `Ambiente.enviar` → ... → `Agente.responder` é síncrono ponta a ponta. O
`claude-agent-sdk` é `async` (`await client.query`, `async for`). A porta de sessão viva
(`abrir`/`enviar`/`fechar`) exigida por `vision.md` §6.1 **não cabe** na assinatura atual.

### 🟠 TD-07 — Nenhuma dependência declarada
Sem `pyproject.toml`/`requirements.txt`. Clone limpo não roda; versões não são reprodutíveis;
CI é impossível de montar. Ver DEP-01 em `dependencies.md`.

### 🟠 TD-08 — Divergência de vocabulário entre código e usuário
`Projeto` = "frente" (palavra **descartada** pelo usuário por ambiguidade); `Sessao` = "card /
tarefa"; `Chat` = "aba". Cada novo trecho de código amplia a dívida de tradução. Ver
`business-overview.md` → Business Dictionary.

### 🟡 TD-09 — Anotações de tipo incorretas
- `Memoria.formatar() -> dict | None` devolve, na verdade, `list[Anotacao] | None`
  (`memoria.py:26-29`).
- `Chat.nome: str = None` deveria ser `str | None` (`sessao.py:17`).
- `Agente.ferramentas: list[Callable]` guarda callables num objeto que o desenho quer
  serializável — e o spike mostrou que ferramentas são **fabricadas pela Sessão**, não carregadas
  pelo agente.

### 🟡 TD-10 — Construção de `Mensagem` com estilos misturados
`Sessao.enviar` usa posicional `(autor, texto, tipo)`; `Ambiente`/`Projeto` usam argumentos
nomeados fora de ordem (`autor`, `tipo`, `texto`). Funciona hoje, mas é convite a trocar `texto`
por `tipo` na próxima construção posicional.

### 🟡 TD-11 — Argumentos de comando quebram com espaços
Todos os `_acionar_comando` usam `mensagem.split()` e leem apenas `m[1]`. `/novo-projeto campanha
de verao` cria o projeto `"campanha"` e descarta o resto, silenciosamente.

### 🟡 TD-12 — `wiki_local` é placeholder
`Projeto.wiki_local: str = "wiki local....."` (`ambiente.py:20`) — campo sem comportamento, para
um conceito que o produto trata como central ("o repositório de inteligência do ambiente").

### 🟡 TD-13 — Reexportação implícita de tipos
`cli.py` e `tui.py` importam `Mensagem` de `Ambiente.sessao`; `ambiente.py` reexporta `Sessao`,
`Chat` e `Memoria`. Mover um tipo quebra consumidores que não deveriam conhecê-lo por ali.

### 🟡 TD-14 — Mensagens de `Ambiente`/`Projeto` não são gravadas
Só a `Sessao` grava em `chat.mensagens`. A TUI compensa com `_escrever_efemeras`
(`tui.py:284-291`), comparando `id()` dos objetos. Funciona, mas é uma regra de negócio
(o que é histórico) resolvida na camada de pintura.

### ⚪ TD-15 — `testes-de-aprendizado/` versionado como código
A própria docstring do spike diz *"Codigo DESCARTAVEL"*, mas ele está no repositório sem marcação
de ciclo de vida. Vale decidir: vira documentação, vai para uma pasta de spikes explicitamente
excluída do empacotamento, ou é removido.

---

## Patterns and Anti-patterns

### Good Patterns
- **Chain of Responsibility com composição** — cada andar atende o que é seu e delega o resto;
  a `Sessao`, último andar, assume tudo que começa com `/`, inclusive dizer que não conhece.
- **Status por composição, não por repasse** — `{"nome_ambiente": ..., **filho.obter_status()}`.
- **Núcleo sem estado de interface** — a UI guarda só pintura (`_expandidas`), pergunta o status
  e compara antes/depois. Trocar a interface não toca em regra.
- **Estado de pintura indexado por nome, não por índice** (`tui.py:217-218`) — sobrevive a
  criação de sessão e troca de projeto.
- **Cor derivada do `tipo` (vocabulário fechado), nunca do `autor` (texto livre)**
  (`tui.py:36-41`) — decisão pequena que evita uma classe inteira de bugs.
- **`escape()` em todo texto que vai para a tela** — texto do usuário não vira marcação.
- **Invariante de domínio verificada na construção e na criação** (`Sessao`, orquestrador único).
- **Defesa de "o usuário sempre está em algum lugar"** — `__post_init__` garante ao menos um
  filho em `Ambiente` e `Projeto`.
- **Comentários que explicam o porquê**, incluindo as **pegadinhas medidas** do spike
  (permissões, nome qualificado da tool, ciclo de vida do client). Documentação de aprendizado
  de qualidade rara.

### Anti-patterns
- **Instâncias globais mutáveis** como catálogo de agentes (TD-05).
- **Dependência de provedor no núcleo** (TD-02).
- **Método de escrita que sempre falha na primeira chamada** (TD-03) — latente por falta de uso.
- **Placeholder com valor de mentira** — `wiki_local = "wiki local....."` (TD-12).
- **Regra de negócio resolvida na camada de pintura** — o que conta como histórico (TD-14).
- **Retorno silencioso de `None`** onde o contrato promete `str` (TD-01).

---

## Leitura de conjunto

O código é **pequeno, coerente e bem pensado** — a arquitetura tem forma clara, as decisões estão
escritas onde importam, e as invariantes de domínio já existem. Isso é incomum em ~600 linhas.

O que falta não é qualidade de escrita: é **alcance**. Três lacunas concentram quase todo o
risco — não há LLM ligado (TD-01, TD-06), não há persistência (TD-04) e não há teste automatizado
(cobertura zero, bloqueada por TD-02). Nenhuma delas é dívida de descuido; todas são consequência
do estágio embrionário, e todas são pré-requisito do primeiro critério de sucesso do produto.
