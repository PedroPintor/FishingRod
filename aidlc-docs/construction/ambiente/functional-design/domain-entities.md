# Domain Entities — U4 `ambiente`

**Fase:** CONSTRUCTION · **Unidade:** `U4 ambiente` · **Portão 1 de 2 (Functional Design)**
**Data:** 2026-10-02
**Decisões de origem:** `construction/plans/ambiente-functional-design-plan.md` (Q1–Q12) e
`construction/plans/ambiente-fd-clarificacao.md` (C1, D-Q12-1, D-Q12-2)

> U4 **não cria entidade de domínio nova**. As entidades são de U1 (`Ambiente`, `Frente`, `Tarefa`,
> `Chat`, `Etapa`, `Memoria`, `RaizWiki`, `Agente`) e os tipos de fronteira são das portas de U2 e
> U3. Este documento descreve o **serviço**: o que ele guarda, o que recebe, o que devolve e os
> erros que levanta.

---

## 1. `ServicoDeAmbiente`

Mora em `aplicacao/servicos/`. Não importa `sqlite3`, `claude_agent_sdk`, `textual`, `os`,
`pathlib` nem `shutil` (critério 3; D-ARQ-04; D-ARQ-08). Conhece só domínio e portas.

### 1.1 Construção

```
ServicoDeAmbiente(
    persistencia: PortaPersistencia,
    wiki: PortaWiki,
    orquestrador: Agente,                 # Q8=A
    agentes_de_chat: tuple[Agente, ...],  # Q9=A — a lista fechada
)
```

| Parâmetro | O que é | Validação na construção |
|---|---|---|
| `persistencia` | porta de U2, já montada pelo composition root (U9) | — |
| `wiki` | porta de U3, já montada pelo composition root | — |
| `orquestrador` | o agente que toda tarefa nova recebe no seu primeiro chat (RN-05 de U1) | papel tem de ser `ORQUESTRADOR` → senão `AgenteInvalido` (U1) |
| `agentes_de_chat` | os únicos agentes com que `criar_chat` pode abrir um chat. Nesta iteração, o bibliotecário | nomes únicos entre si → senão `AgenteInvalido` |

O serviço **não constrói adaptador** (`services.md` §1, passo 3) e não lê configuração.

### 1.2 Estado que o serviço guarda (Q1=A)

| Estado | Forma | Para quê |
|---|---|---|
| **Ambientes abertos** | `dict[Identidade, Ambiente]` | Um objeto só por ambiente no processo. A TUI e os agentes enxergam o mesmo objeto (RN-A-03) |
| **Travas** | `dict[Identidade, asyncio.Lock]`, criadas sob demanda | Uma operação por vez em cada ambiente (Q10=A, RN-A-06) |

O serviço **não** guarda: transcrição (U7), sessão viva (U6/U7), propostas pendentes (U8), nem um
"ambiente ativo" (Q2=A — todo alvo é explícito).

---

## 2. Operações (C1=A: 10 operações)

Todas são `async`. Q3=A: devolvem o objeto afetado ou levantam exceção tipada; **não** devolvem
`Resultado`, que é de U5.

| Grupo | Operação | Devolve | Histórias |
|---|---|---|---|
| Ciclo do ambiente | `criar_ambiente(nome, esquema: EsquemaWiki)` | `Ambiente` | US-08, US-09 |
| | `carregar_ambiente(id_ambiente)` | `Ambiente` | US-05 |
| | `listar_ambientes()` | `list[ResumoAmbiente]` | (Q10=B de Units Generation, tela inicial) |
| | `apagar_ambiente(id_ambiente)` | `None` | (critério 6, Q8=B de U2) |
| Estrutura | `criar_frente(id_ambiente, nome)` | `Frente` | US-15 |
| | `criar_tarefa(id_ambiente, id_frente, nome)` | `Tarefa` | US-16, US-05 |
| | `criar_chat(id_ambiente, id_tarefa, nome_agente, nome="")` | `Chat` | Q14=X (delegação ao bibliotecário) |
| | `criar_etapa(id_ambiente, id_tarefa, descricao, executor: ExecutorEtapa)` | `Etapa` | US-17 |
| | `concluir_etapa(id_ambiente, id_etapa)` | `Etapa` | US-19 |
| Memória | `anotar_memoria(id_ambiente, id_tarefa, chave, valor, autor)` | `Anotacao` | US-04 |

**Fora desta iteração, por decisão (Q7=X + C1=A):** `reabrir_etapa`. O domínio já tem
`Etapa.reabrir()`; só não há operação de serviço que a chame.

### 2.1 Forma dos parâmetros (Q2=A)

- Toda operação, exceto `criar_ambiente` e `listar_ambientes`, recebe **`id_ambiente` explícito**.
- Depois vem o **id do alvo imediato**: a frente para `criar_tarefa`, a tarefa para `criar_chat`,
  `criar_etapa` e `anotar_memoria`, a etapa para `concluir_etapa`.
- Dentro do ambiente, o alvo é achado **por identidade** (RN-A-08), sem índice e sem nome (RF-F16).
- `criar_chat` recebe o **nome** do agente, não o `Agente` (Q9=A): quem chama, seja a tela ou o
  orquestrador, não consegue entregar um agente fora da lista.

---

## 3. Erros

### 3.1 Novos, desta unidade (D-Q12-2)

Moram em `aplicacao/servicos/`, ao lado do serviço.

```
ErroDeServicoDeAmbiente(Exception)          # raiz dos erros novos
├── FrenteInexistente                       # id_frente não existe neste ambiente
├── TarefaInexistente                       # id_tarefa não existe neste ambiente
├── EtapaInexistente                        # id_etapa não existe neste ambiente
└── AgenteDesconhecido                      # nome_agente fora de agentes_de_chat (Q9=A)
```

Mensagens **sem** caminho de disco e sem detalhe de adaptador; carregam o id que faltou.

### 3.2 Reaproveitados

| Erro | De onde vem | Quando o serviço o levanta ou deixa passar |
|---|---|---|
| **`AmbienteInexistente`** | `aplicacao/portas/persistencia.py` (U2) | **D-Q12-1**: o serviço converte o `None` da porta neste erro, em `carregar_ambiente` e em toda operação que recebe `id_ambiente` |
| `ConflitoDeVersao` | U2 | Só depois de **3 tentativas** sem sucesso (Q4=A, RN-A-11) |
| demais `ErroDePersistencia` | U2 | Atravessam sem tradução (Q3=A: quem traduz é U5) |
| `ErroDeWiki` e subclasses | U3 | Atravessam sem tradução. Em `criar_ambiente`, `TituloInvalido` e `DescricaoObrigatoria` chegam **antes** de qualquer escrita (DP-W-10 de U3) |
| `NomeInvalido`, `OrquestradorDuplicado`, `AgenteInvalido` | U1 | Atravessam sem tradução: são o domínio dizendo não |

**Nenhuma exceção é engolida**, com uma única exceção declarada: a falha ao apagar a wiki
**depois** de o ambiente já ter saído do banco (RN-A-16).

---

## 4. Tipos que U4 consome sem alterar

| Tipo | Dono | Uso aqui |
|---|---|---|
| `EsquemaWiki`, `EntidadeSemente`, `PropriedadeSemente` | U3 (`aplicacao/esquema_wiki.py`) | entrada de `criar_ambiente` |
| `PropostaWiki`, `PaginaProposta` | U3 (porta) | conversão do esquema (RN-A-13) |
| `ResumoAmbiente` | U2 (porta) | saída de `listar_ambientes` |
| `Anotacao` | U1 | saída de `anotar_memoria` |
| `ExecutorEtapa` | U1 | entrada de `criar_etapa` |

## 5. Acréscimo a um tipo de outra unidade (Q6=A)

**`PortaWiki` ganha uma quinta operação**, implementada em `WikiDeArquivos` (U3) durante o Code
Generation **desta** unidade:

```
async def apagar(self, localizador: str) -> None
```

| Aspecto | Regra |
|---|---|
| Efeito | Remove a raiz da wiki inteira, com tudo que há dentro |
| Raiz inexistente | Operação vazia bem-sucedida (mesma regra de `apagar_ambiente` em U2, RN-P-22) |
| Confinamento | A raiz é obtida por `resolver_raiz` (`DP-W-01`), o mesmo ponto único das outras operações. Nada fora dela é removido, inclusive através de symlink ou junction |
| Erros | `LocalizadorNaoReconhecido`; falha de I/O vira `ArmazenamentoIndisponivel` (`NFR-W-13`), sem caminho absoluto na mensagem |
| Quem chama | Só `ServicoDeAmbiente.apagar_ambiente` |

Isso **reabre U3** para um acréscimo pequeno, registrado como emenda (§8 de
`business-logic-model.md`).
