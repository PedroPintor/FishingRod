# Domain Entities — U6 `sessao`

**Fase:** CONSTRUCTION · **Unidade:** `U6 sessao` · **Portão 1 de 4 (Functional Design)**
**Data:** 2026-10-02
**Base:** `plans/sessao-functional-design-plan.md` (Q1–Q14, R-FD6-1..11) e
`plans/sessao-fd-clarificacao.md` (C1=B, C2=A, C3=A; D-Q12-1, D-C2-1, D-Q3-1, D-Q5-1, D-Q7-1
sem objeção), todas respondidas em 2026-10-02.

U6 não cria entidade de domínio. `Agente` e `Papel` continuam sendo de U1. O que nasce aqui são
**tipos de aplicação**: o vocabulário com que U7 e U8 conversam com a sessão, e com que U9 entrega as
ferramentas. Os tipos abaixo descrevem forma e significado, não código final.

---

## 1. Visão geral

| Tipo | O que é | Onde mora | Quem constrói |
|---|---|---|---|
| `PortaSessao` | A fronteira sobre o ciclo de vida de uma conversa com o provedor | `aplicacao/portas/sessao.py` | implementada pelo adaptador |
| `ContextoDaSessao` | De que chat é a sessão: as identidades de ambiente, frente, tarefa e chat | idem | quem abre (U7, U8) |
| `SessaoViva` | O identificador opaco de uma sessão aberta | idem | o adaptador, em `abrir` |
| `EventoConversa` | Um dos cinco eventos de um turno | idem | o adaptador |
| `MotivoFalhaDeSessao` | Por que um turno falhou | idem | o adaptador |
| `ErroDeSessao` e filhos | Erros de montagem e de encerramento | idem | o adaptador |
| `Familia` | A família de uma ferramenta: ambiente ou wiki (R9) | `aplicacao/ferramentas/` | dado fixo |
| `Ferramenta` | Uma ferramenta neutra, sem SDK: nome, descrição, esquema e função | idem | uma fábrica, na abertura |
| `RespostaDaFerramenta` | O que a função de uma ferramenta devolve ao agente | idem | a função da ferramenta |
| `EntradaDoRegistro` | Um nome de ferramenta, a família dele e a fábrica | idem | U6 (ações) e U8 (wiki) |
| `RegistroDeFerramentas` | Todas as entradas, verificadas | idem | composition root (U9) |
| `AdaptadorSessaoClaude` | A implementação da porta sobre o `claude-agent-sdk` | `adaptadores/sessao/` | composition root (U9) |

O layout dos módulos é proposta. O Code Generation pode reparti-lo em mais arquivos. O que não muda:
**só `adaptadores/sessao/` importa `claude_agent_sdk`** (RN-S-01).

---

## 2. A porta

### 2.1 `PortaSessao`

```
PortaSessao:
    async abrir(agente: Agente, contexto: ContextoDaSessao) -> SessaoViva
    enviar(sessao: SessaoViva, mensagem: str) -> AsyncIterator[EventoConversa]
    async fechar(sessao: SessaoViva) -> None
```

| Operação | Pode levantar? | O que faz |
|---|---|---|
| `abrir` | **Só** `ConfiguracaoDeSessaoInvalida` e `AdaptadorEncerrado`. **Nunca** por causa do provedor (Q2=B) | Prepara a sessão: verifica e fabrica as ferramentas. Não sobe processo |
| `enviar` | **Nunca.** Só o cancelamento passa (RN-S-16) | Um turno: entrega a mensagem e transmite os eventos até um evento final |
| `fechar` | Nunca | Encerra a sessão de vez. Repetir não faz nada (RN-S-37) |

`abrir` muda de assinatura em relação a `component-methods.md` §4.2: ganha o `contexto` (Q8=A).

### 2.2 `ContextoDaSessao` (Q8=A)

```
ContextoDaSessao:                 # imutável
    id_ambiente: Identidade
    id_frente:   Identidade
    id_tarefa:   Identidade
    id_chat:     Identidade
```

Só identidades. **O nome que assina o que o agente fizer vem do `Agente`**, nunca de quem abre (G10):
não existe um segundo lugar onde esse nome poderia divergir. Todo chat mora numa tarefa, então as
quatro identidades sempre existem, inclusive para o bibliotecário.

### 2.3 `SessaoViva`

```
SessaoViva:                       # imutável, opaco
    id: Identidade                # da sessão, não do chat; serve ao log
    nome_agente: str
    contexto: ContextoDaSessao
```

O estado da sessão (§5) fica com o adaptador, e não no objeto: quem tem a `SessaoViva` não consegue
mudá-lo por fora. U7 guarda o mapa `chat → SessaoViva` (critério 5 de U7).

---

## 3. Os eventos de um turno

```
EventoConversa = MensagemEntregue | PedacoDeTexto | UsoDeFerramenta | FimDeTurno | FalhaDoTurno
```

| Evento | Campos | Significado |
|---|---|---|
| `MensagemEntregue` | `conversa_nova: bool` | A mensagem **chegou ao agente**. Daí em diante ele lembra dela (C2=A, D-C2-1). `conversa_nova` é `True` quando esta é a primeira mensagem da conexão: a primeira do chat neste processo, ou a primeira depois de uma reconexão (Q5=A, R-FD6-10) |
| `PedacoDeTexto` | `texto: str` | Um trecho da resposta, **nunca vazio** (Q1=B) |
| `UsoDeFerramenta` | `familia: Familia`, `nome: str`, `argumentos: Mapping[str, object]` | O agente **pediu** esta ferramenta da sessão. Não garante que ela executou (R-FD6-3). Nome sem família; argumentos em cópia somente leitura |
| `FimDeTurno` | — | O turno terminou bem: houve texto ou uso de ferramenta (Q3=B) |
| `FalhaDoTurno` | `motivo: MotivoFalhaDeSessao`, `detalhe: Mapping[str, str]` | O turno terminou sem resposta completa |

**Gramática** (RN-S-17):

```
turno entregue      :  MensagemEntregue  (PedacoDeTexto | UsoDeFerramenta)*  (FimDeTurno | FalhaDoTurno)
turno não entregue  :  FalhaDoTurno
turno interrompido  :  qualquer prefixo dos dois acima, sem evento final (quem lia foi cancelado)
```

> **Mudança de nome (G1).** `component-methods.md` §4.2 chamava o evento de falha de
> `ErroProvedor`. Ele passa a se chamar `FalhaDoTurno`, porque três dos motivos não são do provedor:
> turno em andamento, sessão fechada e mensagem inválida.

### 3.1 `MotivoFalhaDeSessao` (Q4=A)

| Motivo | Quando | Derruba a conexão? | `detalhe` |
|---|---|:--:|---|
| `PROVEDOR_AUSENTE` | o CLI do Claude não está instalado ou não foi achado | sim | — |
| `NAO_AUTENTICADO` | não há login na assinatura | sim | — |
| `LIMITE_DE_USO` | o limite da assinatura foi atingido | não | `libera_em` (ISO 8601), só se o CLI informar |
| `INDISPONIVEL` | a conexão caiu, o processo morreu, o serviço está fora | sim | — |
| `RESPOSTA_VAZIA` | o turno acabou sem texto e sem uso de ferramenta (TD-01, Q3=B) | não | — |
| `MENSAGEM_INVALIDA` | a mensagem é vazia (só espaços) ou passa de 100.000 caracteres (G4) | — (nada foi enviado) | `problema` (`vazia`, `longa_demais`); `maximo` quando longa demais |
| `TURNO_EM_ANDAMENTO` | já há um turno nesta sessão (C1=B: é proteção; a fila é de U7) | — (nada foi enviado) | — |
| `SESSAO_FECHADA` | a sessão foi fechada, antes ou durante o turno | — | — |
| `FALHA_INESPERADA` | qualquer outra coisa: um defeito. O erro completo vai para o log | sim | — |

O valor de cada motivo (`provedor_ausente`, …) é o que U7 e U9 leem. A frase em português é da tela
(U9), como em U5 (RN-AC-35). O `detalhe` nunca traz texto da mensagem, caminho de disco, pilha de
chamadas ou credencial (RN-S-31).

---

## 4. Ferramentas

### 4.1 `Familia`

| Valor | Ferramentas | Dono | Quem pode receber |
|---|---|---|---|
| `AMBIENTE` (`"ambiente"`) | as 6 ações do catálogo (D-Q2-1 de U5) | U5, convertidas por U6 | só o orquestrador (R10) |
| `WIKI` (`"wiki"`) | `listar`, `ler`, `propor_entidade`, `propor_propriedade` | U8 | quem o registro permitir; nesta iteração, o bibliotecário |

A família é a chave do servidor MCP da sessão. O agente vê `mcp__ambiente__criar_etapa` e
`mcp__wiki__ler` (fato medido pelo spike; RN-S-12).

### 4.2 `Ferramenta` (Q9=A)

```
Ferramenta:                       # imutável; nenhum tipo do SDK
    nome: str                     # snake_case ASCII; igual ao da entrada do registro
    descricao: str
    esquema: Mapping              # JSON Schema de um objeto (padrão aberto, não do SDK)
    executar: async (argumentos: Mapping[str, object]) -> RespostaDaFerramenta

RespostaDaFerramenta:             # imutável
    texto: str                    # o que o agente lê
    erro: bool                    # marca o resultado como erro da ferramenta para o SDK
```

O adaptador traduz `Ferramenta` para o formato do SDK. Toda regra (esquema, validação, texto) mora
em quem fabrica a ferramenta, e não no adaptador.

### 4.3 `EntradaDoRegistro` e `RegistroDeFerramentas` (Q8=A)

```
Fabrica = (contexto: ContextoDaSessao, agente: Agente) -> Ferramenta

EntradaDoRegistro:                # imutável
    nome: str                     # único no registro inteiro, entre famílias (RN-S-13)
    familia: Familia
    fabrica: Fabrica

RegistroDeFerramentas:
    entradas: tuple[EntradaDoRegistro, ...]     # verificadas na construção (RN-S-14)
    buscar(nome) -> EntradaDoRegistro | None
    verificar_escopo(agentes: Iterable[Agente]) -> tuple[Violacao, ...]   # RN-S-15
```

`Violacao` diz qual agente, qual nome e qual regra: `ferramenta_desconhecida`,
`ferramenta_repetida` ou `escopo_violado` (R10). É a **mesma** verificação que `abrir` faz para um
agente só (Q14=A).

`Agente.ferramentas` (U1) continua guardando **nomes sem família**. A família é do registro.

### 4.4 As ferramentas de ambiente (Q9=A, Q10=A)

Um módulo de `aplicacao/ferramentas/`, **sem SDK**, transforma as ações do catálogo em entradas do
registro:

```
entradas_de_acoes(catalogo: CatalogoDeAcoes) -> tuple[EntradaDoRegistro, ...]
```

Uma entrada por ação que aceita o chamador `AGENTE` (hoje, as 6), na ordem do registro de U5. A
fábrica de cada uma faz três coisas:

| Peça | Como sai | Regra |
|---|---|---|
| **Esquema** | dos `Parametro` da ação | RN-S-47 |
| **Amarração** | `Alvo(id_ambiente, id_frente, id_tarefa)` do contexto e `Acionamento.agente(agente.nome)` | RN-S-48 |
| **Texto** | do `Resultado` que `CatalogoDeAcoes.executar` devolve | RN-S-50, RN-S-51 |

**Projeção do `dado` de sucesso** (sem ids — G12):

| Ação | `dado` de U5 | O que o agente lê |
|---|---|---|
| `criar_frente` | `Frente` | `{"ok": true, "frente": {"nome": …}}` |
| `criar_tarefa` | `Tarefa` | `{"ok": true, "tarefa": {"nome": …}}` |
| `criar_chat` | `Chat` | `{"ok": true, "chat": {"nome": …, "agente": …}}` |
| `criar_etapa`, `concluir_etapa` | `EtapaNaPosicao` | `{"ok": true, "etapa": {"posicao": 3, "descricao": …, "executor": "usuario", "concluida": false}}` |
| `anotar_memoria` | `Anotacao` | `{"ok": true, "anotacao": {"autor": …}}` — o valor não volta, porque o agente acabou de escrevê-lo |

**Falha:** `{"ok": false, "motivo": "<valor de MotivoFalha>", "detalhe": {…}}`, com `erro = True`.
O `detalhe` de U5 só tem categorias e números (`alvo`, `parametro`, `posicao`, …), nunca id.

---

## 5. Estados de uma sessão

O estado mora no adaptador (§2.3). É o mesmo para o adaptador falso, que passa pelo mesmo teste de
contrato (critério 1).

| Estado | Significa |
|---|---|
| `SEM_CONEXAO` | Não há processo do CLI. É o estado depois de `abrir` e depois de uma falha que derruba a conexão |
| `OCIOSA` | Há processo, e nenhum turno |
| `EM_TURNO` | Um turno está em andamento, incluindo a subida do processo e a espera da sua confirmação |
| `FECHADA` | Terminal. Não há processo e nunca mais haverá |

As transições estão em `business-logic-model.md` §5.

---

## 6. O adaptador

### 6.1 `AdaptadorSessaoClaude`

**Recebe no construtor** (G11), do composition root:

| Peça | Para quê |
|---|---|
| `registro: RegistroDeFerramentas` | Resolver os nomes do agente na abertura (R4) |
| `pasta_de_trabalho` | A pasta neutra onde o processo do CLI roda (Q11=A). U9 a resolve, como resolve a pasta de dados (critério 9 de U9) |
| `fabrica_de_cliente` | Quem cria o cliente do SDK. O padrão é o cliente real; os testes entregam um cliente roteirizado, com mensagens no formato do SDK, sem CLI |

**Além da porta**, tem `encerrar()`: fecha todas as sessões que abriu, e depois disso `abrir` levanta
`AdaptadorEncerrado` (G7). Só o composition root chama, no fim do programa. Não está na porta porque
nenhum serviço encerra o adaptador.

### 6.2 O adaptador falso

Mora em `tests/dobles/` (onde U2 já pôs os dublês, Q12=B de U2). Responde por roteiro e passa pelo
**mesmo** teste de contrato que o adaptador real (critério 1, TD-01). Não existe em `src/`: não há
modo "sem LLM" no programa nesta iteração.

---

## 7. Erros

```
ErroDeSessao(Exception)
  +-- ConfiguracaoDeSessaoInvalida   # abrir: nome desconhecido ou repetido, R10, fábrica defeituosa
  +-- AdaptadorEncerrado             # abrir depois de encerrar
  +-- RegistroInvalido               # construir o registro: nome fora do padrão, repetido
```

São **erros de montagem**, como `CatalogoInvalido` em U5: aparecem por defeito de quem monta (U7,
U8, U9) ou por um `Agente` adulterado no banco (R-FD6-9). Nunca por causa do provedor. Falha do
provedor é **evento**, não exceção (RN-S-16).
