# U1 `dominio` — Modelo de lógica de negócio

**Estágio:** CONSTRUCTION — Functional Design · **Unidade:** `U1 dominio` · **Data:** 2026-08-26

Operações do domínio com pré-condições, pós-condições e erros. É a especificação que o Code
Generation de U1 implementa e que os testes verificam.

---

## 1. `Identidade`

### `Identidade.nova() -> Identidade`

| | |
|---|---|
| **Entrada** | nenhuma |
| **Pré** | — |
| **Pós** | devolve identidade única, com carimbo de tempo embutido (UUIDv7 via `uuid.uuid7()`) |
| **Erros** | nenhum |
| **Regras** | RN-01 |

**Propriedade que precisa valer** (base da paginação de U2): dadas duas chamadas em sequência,
`a.valor <= b.valor` na comparação textual. É o que substitui uma coluna de ordenação.

---

## 2. `Ambiente`

### `Ambiente(nome)` — construtor

| | |
|---|---|
| **Pré** | `nome` não vazio |
| **Pós** | `id` novo; `frentes == []`; `raiz_wiki == RaizWiki("dados:wikis/" + id.valor)` |
| **Erros** | `NomeInvalido` |
| **Regras** | RN-01, RN-02, RN-03, RN-11 |

### `criar_frente(nome) -> Frente`

| | |
|---|---|
| **Pré** | `nome` não vazio |
| **Pós** | frente nova anexada ao fim de `frentes`; devolvida ao chamador; **não persiste** |
| **Erros** | `NomeInvalido` |
| **Regras** | RN-02, RN-04 (duplicata permitida) |

### `buscar_frente(id) -> Frente | None`

Busca por identidade, nunca por índice ou nome. Devolve `None` se não achar (RN-14).

---

## 3. `Frente`

### `criar_tarefa(nome, agente_orquestrador) -> Tarefa`

| | |
|---|---|
| **Entrada** | `nome: str`, `agente_orquestrador: Agente` |
| **Pré** | `nome` não vazio; `agente_orquestrador.papel == ORQUESTRADOR` |
| **Pós** | tarefa nova com **um** chat do orquestrador, `etapas == []`, `memoria` vazia; anexada a `tarefas` |
| **Erros** | `NomeInvalido`, `AgenteInvalido` |
| **Regras** | RN-02, RN-04, RN-05 |

> **Mudança declarada em relação a `component-methods.md` §1.3**, que escrevia
> `criar_tarefa(nome)` e dizia que a tarefa nascia com "o orquestrador padrão". O domínio não pode
> conhecer a instância concreta do orquestrador — ela é configuração montada no composition root
> (`components.md` §2.9). Q4=A resolveu passando o agente por parâmetro. **Emenda a aplicar em
> `component-methods.md` §1.3** no fechamento desta unidade.

---

## 4. `Tarefa`

### `criar_chat(agente) -> Chat`

| | |
|---|---|
| **Pré** | se `agente.papel == ORQUESTRADOR`, então `contar_orquestradores() == 0` |
| **Pós** | chat novo anexado a `chats`; nome inicial derivado do nome do agente |
| **Erros** | `OrquestradorDuplicado` |
| **Regras** | RN-06 |

### `criar_etapa(descricao, executor) -> Etapa`

| | |
|---|---|
| **Pré** | `descricao` não vazia |
| **Pós** | etapa anexada ao **fim** de `etapas` (a posição é a ordem — RN-08); `concluida == False` |
| **Erros** | `NomeInvalido` |
| **Regras** | RN-02, RN-08 |

### `contar_orquestradores() -> int`

Conta chats cujo agente tem `papel == ORQUESTRADOR`. Usada pela pré-condição de `criar_chat`; é
consulta pura, sem efeito.

---

## 5. `Etapa`

### `concluir()` / `reabrir()`

| | `concluir()` | `reabrir()` |
|---|---|---|
| **Pós** | `concluida == True` | `concluida == False` |
| **Idempotente** | sim | sim |
| **Erros** | nenhum | nenhum |
| **Regras** | RN-07, RN-08 | RN-07 |

**Não há verificação de ordem** (Q5b=A): concluir a terceira etapa com a primeira pendente é
permitido e não gera aviso no domínio.

---

## 6. `Memoria`

### `anotar(chave, valor, autor)`

| | |
|---|---|
| **Pré** | `autor` não vazio; `chave` não vazia |
| **Pós** | `anotacoes[chave]` ganha uma `Anotacao(autor, valor, criada_em=agora UTC)` **ao fim** da lista; `versao += 1` |
| **Erros** | `NomeInvalido` (autor ou chave vazios) — **nunca `KeyError`** |
| **Regras** | RN-09, RN-10 |

**Fluxo com chave inédita** (o caso que mata TD-03):

1. `anotar("plano", "x", "orquestrador")` em memória vazia
2. `anotacoes` não tem `"plano"` → a lista é **criada**, não acessada
3. `anotacoes == {"plano": [Anotacao(...)]}`, `versao == 1`
4. Segunda chamada na mesma chave → lista com **dois** elementos, `versao == 2`

O passo 2 é literalmente o defeito de hoje: o código atual indexa antes de criar.

---

## 7. `politica.exige_aprovacao(chamador) -> bool`

| Entrada | Saída | Regra |
|---|---|---|
| `Chamador.AGENTE` | `True` | RN-12 |
| `Chamador.USUARIO` | `False` | RN-12 |

Função pura, sem estado, sem I/O. Único ponto de decisão sobre aprovação em todo o sistema — U5 e
U8 a consultam, e é só o corpo dela que muda quando a configuração voltar.

---

## 8. Propriedades para `hypothesis` (extensão `property-based-testing`, PBT-01)

A extensão exige que as propriedades sejam **nomeadas** neste estágio; a implementação é do Code
Generation.

| ID | Propriedade | Estratégia | Origem |
|---|---|---|---|
| **PBT-U1-01** | Duas identidades geradas em sequência ordenam por criação (`a.valor <= b.valor`) e nunca colidem | repetição de `Identidade.nova()` | RN-01, ESC-14 |
| **PBT-U1-02** | `Identidade.nova()` sempre produz UUID versão 7 válido em formato canônico | idem | RN-01 |
| **PBT-U1-03** | Para qualquer sequência de `(chave, valor, autor)` válidos, `anotar` nunca levanta, e o total de anotações é igual ao número de chamadas | `st.lists(st.tuples(texto, texto, texto))` | **TD-03**, RN-09 |
| **PBT-U1-04** | `versao` ao fim é igual ao número de chamadas de `anotar` | idem | RN-10 |
| **PBT-U1-05** | Para qualquer sequência de `concluir`/`reabrir`, `concluida` reflete a última chamada (idempotência) | `st.lists(st.booleans())` | RN-07 |
| **PBT-U1-06** | Para qualquer nome não vazio, `criar_frente` seguido de `buscar_frente(f.id)` devolve a mesma frente; para identidade não criada, devolve `None` | `st.text()` filtrado | RN-04, RN-14 |
| **PBT-U1-07** | Para qualquer nome cujo `strip()` seja vazio, toda criação levanta `NomeInvalido` | `st.text(alphabet=" \t\n")` | RN-02 |

**Não é propriedade, é teste direto**: RN-05/RN-06 (orquestrador duplicado), RN-11 (formato da raiz)
e RN-13 (import). Casos únicos e determinísticos — gerar entrada aleatória para eles seria
cerimônia sem informação.

---

## 9. Conformidade das extensões habilitadas

| Extensão | Situação | Justificativa |
|---|---|---|
| `property-based-testing` (Full) | **Conforme** | PBT-01 satisfeito: 7 propriedades nomeadas com estratégia e origem. PBT-02 a PBT-10 (execução, shrinking, contra-exemplos versionados) valem no Code Generation, não aqui |
| `security-baseline` | **Conforme** | Aplicáveis nesta unidade: SECURITY-15 (fail-safe) — erros de domínio são tipados e nenhuma operação deixa a entidade em estado parcial. **N/A**: HTTP, IAM, CORS, rede, credenciais, criptografia — a unidade não tem I/O, rede nem segredo. SECURITY-05 (confinamento de caminho) é de U3: aqui a `RaizWiki` é só texto com esquema, e RN-11 já proíbe caminho absoluto |
| `resiliency-baseline` | **N/A** | Desabilitada em 2026-08-17 |

---

## 10. Emendas a aplicar nos artefatos de Application Design

Aplicadas ao fechar o Code Generation de U1, marcando o texto substituído e nunca apagando:

| Artefato | Trecho | Motivo |
|---|---|---|
| `component-methods.md` §1.3 | `criar_tarefa(nome)` → `criar_tarefa(nome, agente_orquestrador)` | Q4=A (ver §3) |
| `component-methods.md` §1.7 | `Memoria` ganha `versao`; `Anotacao` ganha `criada_em` | CQ3=C |
| `component-methods.md` §1.1 | `Identidade.nova()` usa `uuid.uuid7()` da stdlib | CQ2=D |
| `components.md` §2.2 | `Ambiente` nasce sem frente (a criação automática some) | Q1=A |

**Fora de U1, registradas na Parte B.3 do arquivo de clarificação e a aplicar quando aquelas
unidades chegarem**: `services.md` §2 e `unit-of-work.md` U4 perdem a invariante "ao menos uma
entidade" na criação da wiki.
