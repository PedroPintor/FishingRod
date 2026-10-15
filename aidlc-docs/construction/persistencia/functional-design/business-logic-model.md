# Business Logic Model — U2 `persistencia`

**Fase:** CONSTRUCTION · **Unidade:** `U2 persistencia` · **Data:** 2026-08-26

Semântica operação por operação: entrada, pré-condição, efeito, pós-condição, erro.

---

## 1. O contrato final da porta

```python
class PortaPersistencia(Protocol):
    # --- ambiente (documento) ---
    async def salvar_ambiente(self, ambiente: Ambiente) -> None: ...
    async def carregar_ambiente(self, id: Identidade) -> Ambiente | None: ...
    async def listar_ambientes(self) -> list[ResumoAmbiente]: ...        # novo — RN-P-24
    async def apagar_ambiente(self, id: Identidade) -> None: ...         # novo — Q8=B

    # --- memória (tabela, append-only) ---
    async def anotar(self, id_ambiente: Identidade, id_tarefa: Identidade,
                     chave: str, anotacao: Anotacao) -> None: ...        # novo — Q2=B

    # --- transcrição (tabela) ---
    async def inserir_mensagem(self, id_ambiente: Identidade, id_chat: Identidade,
                               papel: str, texto: str, em_andamento: bool) -> Identidade: ...
    async def atualizar_mensagem(self, id_mensagem: Identidade, texto: str,
                                 em_andamento: bool) -> None: ...
    async def registrar_uso_ferramenta(self, id_mensagem: Identidade, tool: str,
                                       args_resumo: str) -> None: ...   # [emenda Q6]
    async def listar_mensagens(self, id_chat: Identidade, limite: int,
                               antes_de: Identidade | None = None) -> list[MensagemPersistida]: ...
```

**Três desvios do contrato herdado, todos declarados:**

| Desvio | Motivo |
|---|---|
| `listar_ambientes` e `apagar_ambiente` novos | RN-P-24 (sem listar não há como reabrir) e Q8=B |
| `anotar` novo | Q2=B — memória virou tabela |
| `inserir_mensagem` ganhou `id_ambiente` | Sem ela, `apagar_ambiente` não acha as mensagens: `id_chat` mora no JSON e não tem tabela para referenciar (§2 de `domain-entities.md`) |

Nenhuma menciona SQL — RN-P-16 preservada.

> **[Emenda 2026-08-27 / Code Generation]** Uma **pré-condição implícita** virou explícita:
> `anotar` e `inserir_mensagem` exigem que o **ambiente exista**, e levantam `AmbienteInexistente`
> quando não existe. Não foi decisão de projeto — foi achado de teste: `PBT-U2-04` inseriu mensagem
> num ambiente nunca salvo e o adaptador real deixou `sqlite3.IntegrityError` vazar pela porta,
> porque a chave estrangeira que existe para a cascata de `RN-P-20` também torna o ambiente uma
> pré-condição. Sem o erro nomeado, o vocabulário da porta ficaria furado (`NFR-P-16`) e as duas
> implementações discordariam (`RN-P-26`). Ver `RN-P-27`.

---

## 2. Operações

### `salvar_ambiente(ambiente)`

- **Pré**: `ambiente.versao` é a versão lida da última carga (ou `0` para ambiente novo).
- **Efeito**: numa transação — grava documento, `nome`, `atualizado_em`, e `versao + 1`, **desde que**
  a versão em disco seja `ambiente.versao`. Ambiente inexistente é inserido com `versao = 1`.
- **Pós**: disco e `ambiente.versao` avançam juntos (RN-P-06). Nenhuma anotação escrita ou apagada
  (RN-P-08). Nenhuma mensagem tocada.
- **Erro**: `ConflitoDeVersao` se a versão em disco divergir — e **nada** é gravado (RN-P-05).

> Quem chama trata assim: recarrega, reaplica a mudança, salva de novo. **U4 ganha esse caminho de
> erro** — é o custo que Q4=C declarou.

### `carregar_ambiente(id)`

- **Efeito**: lê a linha; se `versao_esquema > 1`, levanta (RN-P-02). Desserializa o documento, lê
  **todas** as anotações do ambiente e as distribui pelas tarefas, reconstruindo cada `Memoria` na
  ordem de escrita, com `versao = total de anotações daquela tarefa` (RN-P-10, RN-P-11).
- **Pós**: `Ambiente` de domínio completo, com `versao` igual à do disco. Round-trip fecha (RN-P-01).
- **Erro**: nenhum para id ausente — devolve `None` (RN-P-04).

### `listar_ambientes()`

- **Efeito**: lê `id`, `nome`, `atualizado_em`. **Sem desserializar documento** — é uma tela de
  escolha, não uma carga (RN-P-24).
- **Pós**: lista ordenada do mais recente para o mais antigo. Vazia quando não há ambiente.

### `apagar_ambiente(id)`

- **Efeito**: numa transação, apaga a linha do ambiente; anotações, mensagens e usos vão junto por
  cascata (RN-P-20).
- **Pós**: nenhuma linha órfã. O diretório da wiki **continua no disco** — apagá-lo é de U4
  (RN-P-21).
- **Erro**: nenhum. Id inexistente é no-op (RN-P-22).

### `anotar(id_ambiente, id_tarefa, chave, anotacao)`

- **Efeito**: um `INSERT` com `id` UUIDv7 novo. Nada mais é lido, nada é comparado.
- **Pós**: a anotação existe e é a última daquela tarefa. `Ambiente.versao` **inalterada** (RN-P-07).
- **Erro**: nenhum de concorrência — dois `anotar` simultâneos ambos vencem. É o ponto da decisão.
  **[emenda 2026-08-27]** `AmbienteInexistente` se o ambiente não existe (`RN-P-27`).

### `inserir_mensagem(...) -> Identidade`

- **Efeito**: insere com `id` UUIDv7 novo, que é também a posição cronológica (RN-P-12).
- **Pós**: devolve o id — é o que U7 guarda para chamar `atualizar_mensagem` durante o streaming.
- **Erro**: **[emenda 2026-08-27]** `AmbienteInexistente` se o ambiente não existe (`RN-P-27`).

### `atualizar_mensagem(id, texto, em_andamento)`

- **Pré**: a mensagem existe.
- **Efeito**: altera **só** `texto` e `em_andamento` (RN-P-18).
- **Pós**: a ordem da transcrição não muda, porque `id` não muda.
- **Erro**: id inexistente levanta — aqui a ausência **é** defeito, ao contrário de
  `carregar_ambiente`: só se atualiza o que se acabou de inserir.

### `registrar_uso_ferramenta(id_mensagem, ...)`

- **Efeito**: insere uma linha ligada à mensagem. Várias por mensagem são normais (RN-P-19).
- **[emenda 2026-08-26 / NFR Q6]** O parâmetro ~~`resultado_resumo`~~ saiu: o resultado não existe
  no instante do evento de uso, e nenhuma unidade desenha a correlação que o preencheria.
- **Pós**: volta junto com a mensagem em `listar_mensagens`.

### `listar_mensagens(id_chat, limite, antes_de=None)`

- **Efeito**: sem `antes_de`, as `limite` de maior `id`; com `antes_de`, as `limite` de maior `id`
  **menor** que ele. Em ambos os casos, a saída é reordenada crescente (RN-P-13, RN-P-14).
- **Pós**: cada `MensagemPersistida` carrega `em_andamento` como está no disco (RN-P-17) e seus usos
  de ferramenta.
- **Nota**: a mais antiga da página é o cursor da página seguinte. Como UUIDv7 é único e ordenável,
  paginar não repete nem pula (PBT-U2-05).

---

## 3. Propriedades PBT (`property-based-testing = Yes/Full`)

| # | Propriedade | Regra que sustenta |
|---|---|---|
| **PBT-U2-01** | Para todo `Ambiente` gerado (frentes/tarefas/chats/etapas arbitrários), `carregar(salvar(a)) == a` | RN-P-01 |
| **PBT-U2-02** | Para toda sequência de `anotar`, a memória carregada tem as mesmas anotações, nas mesmas chaves, na mesma ordem, com `versao` igual ao total | RN-P-10 |
| **PBT-U2-03** | Para toda sequência de salvamentos, salvar com versão obsoleta **sempre** levanta `ConflitoDeVersao` e **nunca** altera o disco | RN-P-05 |
| **PBT-U2-04** | Para toda transcrição de `n` mensagens e todo `limite > 0`, `listar_mensagens` devolve `min(limite, n)` itens, crescentes, e são exatamente os mais recentes | RN-P-13 |
| **PBT-U2-05** | Paginar por cursor até esgotar reconstrói a transcrição **inteira**, sem repetição e sem lacuna | RN-P-14 |
| **PBT-U2-06** | Para toda intercalação de `anotar` de dois autores, **todas** as anotações sobrevivem | RN-P-07 |
| **PBT-U2-07** | Depois de `apagar_ambiente`, nenhuma tabela tem linha daquele ambiente | RN-P-20 |
| **PBT-U2-08** | Para toda sequência de operações da porta, `RepositorioEmMemoria` e `RepositorioSQLite` produzem o **mesmo** resultado observável — inclusive os mesmos erros | RN-P-25, RN-P-26 |

**PBT-U2-01 e PBT-U2-02 geram memória por `anotar()`**, nunca montando `anotacoes`/`versao` à mão —
pelo motivo em `domain-entities.md` §5.2.

**PBT-U2-08 é o teste de contrato.** É ele que impede o dublê de divergir do real — a mesma ideia que
mata TD-01 em U6, aplicada uma unidade antes.

---

## 4. Conformidade das extensões

| Extensão | Regra aplicável | Estado | Justificativa |
|---|---|:--:|---|
| `security-baseline` | Integridade dos dados persistidos (SECURITY-13 / RNF-05) | ✅ | RN-P-03 (uma transação por operação) e RN-P-05 (bloqueio otimista) — a corrupção silenciosa é impedida, não desencorajada |
| `security-baseline` | Sem segredo em código ou em dado persistido | ✅ | Nenhuma tabela guarda credencial; a chave do provedor é de U6 e vem do ambiente do processo |
| `security-baseline` | Superfície de dependências | ✅ | Q1a=B mantém **zero** dependência de runtime; `sqlite3` é stdlib |
| `security-baseline` | Entrada não confiável em SQL | ✅ | Todo valor entra por parâmetro vinculado; nenhuma consulta é montada por concatenação. **Verificável em Code Generation** |
| `security-baseline` | Dado de usuário fora do diretório do código | ✅ | Q1=A põe o banco na pasta de dados do sistema operacional |
| `property-based-testing` | Propriedades para as invariantes centrais | ✅ | 8 propriedades, cobrindo round-trip, ordem, paginação, conflito, exclusão e equivalência de dublês |
| `resiliency-baseline` | — | N/A | Desativada na Requirements Analysis (`aidlc-state.md`) |

---

## 5. O que fica para o próximo portão (NFR Design de U2)

Decidido aqui foi **comportamento**. Estes são **mecanismo** e não pertencem a este estágio:

- `PRAGMA foreign_keys = ON` — **sem ele a cascata de RN-P-20 não acontece** e órfãos aparecem em
  silêncio. É a dependência mais importante que este estágio deixa em aberto.
- Modo WAL, `busy_timeout`, e como `async` chega ao `sqlite3` síncrono (`asyncio.to_thread`).
- Onde o esquema é criado e como se verifica que já existe.
- Se há uma conexão por operação ou uma conexão viva.

---

## 6. Emendas feitas em artefatos aprovados

| Artefato | Emenda |
|---|---|
| `component-methods.md` §4.1 | Contrato de `PortaPersistencia` atualizado: `listar_ambientes`, `apagar_ambiente`, `anotar` acrescentados; `inserir_mensagem` ganha `id_ambiente`; `listar_mensagens` ganha `antes_de` |
| `components.md` §4.1 (`RepositorioSQLite`) | A estratégia híbrida passa a ter três tabelas além do documento; memória sai do documento |
| `unit-of-work.md` §3 (U2) | Critério de pronto ganha exclusão em cascata (Q8=B) e equivalência de dublês (Q9=A) |
| `unit-of-work.md` §3 (U9) | **Novo critério**: aviso e confirmação antes de apagar ambiente |
| `unit-of-work.md` §3 (U4) | **Novo critério**: tratar `ConflitoDeVersao`; apagar ambiente remove o diretório da wiki **depois** do banco |
| `component-methods.md`, `components.md`, `services.md`, `unit-of-work.md` (U7), Pergunta F | **[2026-08-26 / NFR Q6]** `resultado_resumo` removido do contrato e da descrição da transcrição; Pergunta F=B parcialmente revogada |
| `ambiente.py` (U1, código) | `Ambiente` ganha `versao: int = 0` — §5.1 de `domain-entities.md`. **Especificado aqui, aplicado em Code Generation**: este estágio não escreve código |

As emendas em documento foram aplicadas neste estágio, riscando o texto substituído e nunca apagando.
A emenda em código é a única pendente, e é de Code Generation.
