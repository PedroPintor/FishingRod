# Domain Entities — U2 `persistencia`

**Fase:** CONSTRUCTION · **Unidade:** `U2 persistencia` · **Data:** 2026-08-26
**Decisões que originam este modelo:** Q1=A, Q1a=B, Q2=B, Q2a=A, Q3=A, Q4=C, Q5=A, Q6=A, Q7=A,
Q8=B, Q9=A · `ESC-13`, `D-ARQ-04`, `RNF-05`, `RNF-12`

---

## 1. A regra de corte: o que é documento e o que é tabela

`ESC-13` escolheu persistência híbrida sem dizer onde exatamente cortar. Q2 fechou o critério, e ele
não é "coisas grandes viram tabela":

> **É tabela o que cresce sem teto por escrita de agente e nunca é reescrito — só acrescentado.
> É documento o que uma pessoa cria e edita, cuja forma muda a cada iteração.**

| Dado | Quem escreve | Cresce sem teto? | Reescrito? | Destino |
|---|---|:--:|:--:|---|
| Frente, Tarefa, Chat, Etapa | pessoa (clique/comando) | não | sim | **documento** |
| `RaizWiki` | derivada na criação | não | não | **documento** |
| Anotação de memória | agente, a cada chamada | **sim** | **nunca** | **tabela `anotacao`** |
| Mensagem de transcrição | agente e usuário | **sim** | só a linha em andamento | **tabela `mensagem`** |
| Uso de ferramenta | agente | **sim** | **nunca** | **tabela `uso_ferramenta`** |

A transcrição já estava desse lado por ESC-13. A memória entrou pelo mesmo critério — não por
tamanho, mas porque `Q4=C` (bloqueio otimista) transformaria duas anotações simultâneas num
**falso conflito**, e um blackboard onde a segunda anotação é rejeitada não é um blackboard.

## 2. A consequência estrutural: identidades sem tabela para apontar

Como frente, tarefa e chat vivem **dentro do JSON**, não existe tabela para `anotacao.id_tarefa` e
`mensagem.id_chat` referenciarem. Isso tem um preço concreto: **sem uma coluna `id_ambiente` em cada
tabela filha, `apagar_ambiente` não teria como encontrar o que apagar** (Q8=B). Por isso `anotacao`
e `mensagem` carregam `id_ambiente` além do id lógico — é a única aresta que o banco consegue
percorrer.

---

## 3. Esquema

```sql
-- Estrutura do ambiente, como documento. Uma linha por ambiente (Q10=B).
CREATE TABLE ambiente (
    id             TEXT    PRIMARY KEY,   -- UUIDv7 (Identidade)
    nome           TEXT    NOT NULL,
    versao         INTEGER NOT NULL,      -- bloqueio otimista (Q4=C)
    versao_esquema INTEGER NOT NULL,      -- Q3=A; hoje sempre 1
    documento      TEXT    NOT NULL,      -- JSON: frentes -> tarefas -> chats/etapas + raiz_wiki
    criado_em      TEXT    NOT NULL,      -- ISO-8601 UTC
    atualizado_em  TEXT    NOT NULL
);

-- Memória (blackboard). Append-only: nenhum UPDATE, nenhum DELETE fora da cascata.
CREATE TABLE anotacao (
    id          TEXT NOT NULL PRIMARY KEY,  -- UUIDv7 gerado na inserção; dá a ordem de escrita
    id_ambiente TEXT NOT NULL REFERENCES ambiente(id) ON DELETE CASCADE,
    id_tarefa   TEXT NOT NULL,              -- vive no documento; sem FK possível
    chave       TEXT NOT NULL,
    autor       TEXT NOT NULL,
    valor       TEXT NOT NULL,
    criada_em   TEXT NOT NULL
);
CREATE INDEX idx_anotacao_tarefa ON anotacao(id_tarefa, id);

-- Transcrição. Append-only, exceto a linha do turno corrente (em_andamento).
CREATE TABLE mensagem (
    id           TEXT    NOT NULL PRIMARY KEY,  -- UUIDv7: é a ordem cronológica (ESC-14)
    id_ambiente  TEXT    NOT NULL REFERENCES ambiente(id) ON DELETE CASCADE,
    id_chat      TEXT    NOT NULL,
    papel        TEXT    NOT NULL,              -- 'usuario' | 'agente'
    texto        TEXT    NOT NULL,
    em_andamento INTEGER NOT NULL,              -- 0/1
    criada_em    TEXT    NOT NULL
);
CREATE INDEX idx_mensagem_chat ON mensagem(id_chat, id);

-- Uso de ferramenta (Q7=A). Várias linhas por mensagem.
CREATE TABLE uso_ferramenta (
    id               TEXT NOT NULL PRIMARY KEY,
    id_mensagem      TEXT NOT NULL REFERENCES mensagem(id) ON DELETE CASCADE,
    tool             TEXT NOT NULL,
    args_resumo      TEXT NOT NULL,
    -- [emenda 2026-08-26 / NFR Q6] coluna `resultado_resumo` removida -- ver §5.3
    criado_em        TEXT NOT NULL
);
CREATE INDEX idx_uso_mensagem ON uso_ferramenta(id_mensagem);
```

**Nenhuma tabela de wiki, nenhuma coluna de conteúdo de wiki** — RNF-12. A única referência é
`raiz_wiki` dentro do documento, e é um localizador (`dados:wikis/<id>`), não um caminho.

> **Dependência para o NFR Design (próximo portão):** `ON DELETE CASCADE` só age se
> `PRAGMA foreign_keys = ON` estiver ligado na conexão — o SQLite o mantém **desligado por padrão**.
> Este estágio decide que a cascata é o comportamento exigido (RN-P-20); ligar o pragma é mecanismo
> e pertence lá. Se for esquecido, `apagar_ambiente` deixa órfãos silenciosos.

---

## 4. Forma do documento (`ambiente.documento`)

```json
{
  "id": "0199...", "nome": "Campanha de verão",
  "raiz_wiki": "dados:wikis/0199...",
  "frentes": [
    { "id": "...", "nome": "...",
      "tarefas": [
        { "id": "...", "nome": "...",
          "chats": [ { "id": "...", "nome": "...",
                       "agente": { "nome": "...", "papel": "orquestrador",
                                   "modelo": "...", "ferramentas": [], "regras": [] } } ],
          "etapas": [ { "id": "...", "descricao": "...",
                        "executor": "agente", "concluida": false } ]
        } ]
    } ]
}
```

**Ausências deliberadas.** O documento **não** contém `Tarefa.memoria` (tabela `anotacao`) nem
mensagem alguma (tabela `mensagem`). `versao` e `versao_esquema` são colunas, não campos do JSON —
ficam legíveis por consulta sem desserializar.

---

## 5. Emendas que este modelo exige em código já aprovado

### 5.1 `Ambiente` ganha `versao: int = 0` (U1, aprovada)

Q4=C precisa de uma revisão do agregado, e `salvar_ambiente(ambiente)` só sabe qual versão comparar
se o próprio `Ambiente` a carregar. A alternativa — `salvar_ambiente(ambiente, versao_lida)` —
empurraria a escrituração para U4 em toda chamada.

**Custo declarado:** é emenda a uma unidade já aprovada. Um campo, sua serialização e um teste.
Precedente idêntico já existe em `Memoria.versao`, criado em U1 exatamente para este fim.

### 5.2 `Memoria.versao` deixa de ser o detector de conflito, e passa a ser derivada

Com a memória em tabela, quem detecta conflito é `Ambiente.versao`. Na carga, `Memoria.versao`
recebe **o número de anotações carregadas** — e isso é exato, porque `anotar()` incrementa `versao`
uma vez por anotação acrescentada, então `versao == total_de_anotacoes()` para toda memória
construída pela API pública. Nenhuma coluna nova.

**Consequência para o teste de round-trip:** a propriedade PBT gera memórias **via `anotar()`**,
nunca montando `anotacoes` e `versao` à mão — uma `Memoria(anotacoes={...}, versao=0)` construída
diretamente não faz round-trip, e isso é correto, não um defeito.

### 5.3 `uso_ferramenta` perde `resultado_resumo` (emenda de 2026-08-26, NFR Requirements Q6)

O texto original desta seção dizia que a tabela guardaria ~~`args_resumo` **e** `resultado_resumo`~~.
A coluna de resultado **sai desta iteração**. Dois motivos, e o segundo é o que decide:

1. Nenhum critério de aceite desta iteração lê resultado de ferramenta depois do fato. A **Pergunta
   F=B** da Application Design a justificou por auditoria (*"por que o bibliotecário propôs
   aquilo"*), mas **US-14 pede revisão antes de salvar**, em fluxo vivo — não leitura de histórico.
   A Pergunta F=B fica **parcialmente revogada**, não apagada.
2. **A coluna era não-preenchível.** No stream do SDK o resultado não existe no instante em que o
   evento de uso de ferramenta chega, e nenhuma unidade tem desenhada a correlação entre a chamada
   e o resultado. Manter a coluna era manter uma dívida sem dono.

`args_resumo` fica: é auto-limitado por natureza (argumentos de chamada são pequenos e
estruturados) e responde "qual ferramenta foi chamada com quê", que é o que US-06 mostra.

**Consequência para Q6 do NFR:** com a coluna fora, a discussão de truncamento e teto rígido some
junto. Não há teto a definir porque não há campo sem teto.

---

## 6. Tipos de fronteira (`aplicacao/portas/`)

```
@dataclass(frozen=True)
class MensagemPersistida:
    id: Identidade; id_chat: Identidade; papel: str; texto: str
    em_andamento: bool; criada_em: datetime
    usos_de_ferramenta: tuple[UsoDeFerramenta, ...]

@dataclass(frozen=True)
class UsoDeFerramenta:
    tool: str; args_resumo: str; criado_em: datetime   # [emenda Q6] sem resultado_resumo

@dataclass(frozen=True)
class ResumoAmbiente:          # para a tela inicial escolher qual abrir
    id: Identidade; nome: str; atualizado_em: datetime

class ConflitoDeVersao(Exception):   # Q4=C
    """A versão em disco avançou desde a leitura. Quem chamou recarrega e repete."""
```

Vivem em `aplicacao/portas/`, não no domínio: são o vocabulário da porta. `ConflitoDeVersao` **não**
é `ErroDeDominio` — o domínio não sabe que existe disco.

---

## 7. Onde o arquivo mora (Q1=A + Q1a=B)

| Plataforma | Raiz |
|---|---|
| Windows | `%LOCALAPPDATA%\FishingRod\` |
| Linux | `$XDG_DATA_HOME/fishingrod/` ou `~/.local/share/fishingrod/` |
| macOS | `~/Library/Application Support/FishingRod/` |

Dentro dela: `fishingrod.db` e `wikis/<id_ambiente>/`. A resolução são ~12 linhas sobre
`sys.platform` no **composition root** — zero dependência de runtime nova (Q1a=B), e nenhum módulo
de domínio ou de aplicação conhece o caminho.

**Consequência fora desta unidade:** é esta raiz que resolve o esquema `dados:` de
`RaizWiki` (`dados:wikis/<id>`). **U3 materializa a wiki debaixo dela** — anotado para não ser
redescoberto lá.
