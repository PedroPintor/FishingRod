# Domain Entities — U5 `acoes`

**Fase:** CONSTRUCTION · **Unidade:** `U5 acoes` · **Portão 1 de 2 (Functional Design)**
**Data:** 2026-10-02
**Base:** `plans/acoes-functional-design-plan.md` (Q1–Q12, R-FD5-1..8) e
`plans/acoes-fd-clarificacao.md` (C1=A, D-Q2-1..3), todas respondidas em 2026-10-02.

U5 não cria entidade de domínio nova: `Ambiente`, `Frente`, `Tarefa`, `Chat`, `Etapa` e
`Anotacao` continuam sendo de U1. O que nasce aqui são os **tipos de aplicação** com que a tela, o
agente e o catálogo conversam. Os tipos abaixo descrevem forma e significado, não código final.

---

## 1. Visão geral

| Tipo | O que é | Quem constrói |
|---|---|---|
| `Escopo` | Em que nível da árvore uma ação age | registro (dado fixo) |
| `TipoParametro` | Como um argumento é lido e validado | registro |
| `Parametro` | Um argumento de uma ação: nome, tipo, obrigatório, limite | registro |
| `Acao` | Uma ação do ambiente, como dado | registro |
| `Alvo` | As identidades sobre as quais a ação age | a tela (usuário) ou U9 ao abrir o chat (agente) |
| `Acionamento` | Quem acionou: usuário ou agente, e o nome que assina | a tela ou U9 — **nunca o agente** |
| `ComandoDigitado` | O que o parser extrai de `/nome texto` | `ParserDeComando` |
| `Referencias` | As frente, tarefa e etapa que o alvo e os argumentos apontam, já achadas | `CatalogoDeAcoes` |
| `EtapaNaPosicao` | Uma etapa junto com a posição dela na tarefa | `CatalogoDeAcoes` |
| `PedidoDeConfirmacao` | O que a tela mostra quando um agente pede uma ação | `CatalogoDeAcoes` |
| `Resultado` | Como toda ação termina | `CatalogoDeAcoes` |
| `MotivoFalha` | Por que uma ação não aconteceu | `CatalogoDeAcoes` |
| `PortaDeConfirmacao` | A pergunta "sim ou não?" feita à pessoa | implementada por U9 |
| `CatalogoDeAcoes` | O registro e o único ponto de execução | composition root (U9) |
| `ParserDeComando` | Tradutor de sintaxe da barra `/` | composition root (U9) |

---

## 2. O registro

### 2.1 `Escopo`

```
Escopo = AMBIENTE | FRENTE | TAREFA
```

Diz quais identidades o `Alvo` precisa ter (RN-AC-10):

| Escopo | Exige no `Alvo` |
|---|---|
| `AMBIENTE` | `id_ambiente` |
| `FRENTE` | `id_ambiente` e `id_frente` |
| `TAREFA` | `id_ambiente` e `id_tarefa` |

Etapa **não** é escopo (R-FD5-4): `concluir_etapa` tem escopo `TAREFA`, e a etapa é argumento,
apontada pela posição (Q8=A).

### 2.2 `TipoParametro`

| Tipo | Aceita | Recusa |
|---|---|---|
| `TEXTO` | texto | outro tipo; texto acima do limite do parâmetro (G10) |
| `ESCOLHA` | uma das `opcoes` do parâmetro, sem diferenciar maiúscula e acento: `Usuário` vale `usuario` (G4) | qualquer outro valor |
| `POSICAO` | inteiro ≥ 1 **e até 999.999.999**, ou texto só de dígitos (até 9) | zero, negativo, `bool`, fração, texto que não é número, **inteiro acima de 999.999.999** |

> **/!\ Emenda 2026-10-02 — Code Generation de U5 `acoes`.** O teto de nove dígitos vale também para
> o inteiro, e não só para o texto: a mesma posição é aceita ou recusada igual nas duas formas. Sem
> o teto, um inteiro gigante passaria pela validação e chegaria a `ALVO_INEXISTENTE` com um `posicao`
> de milhares de dígitos no detalhe. Só dígitos ASCII no texto: `int("٢")` vale 2 em Python.

### 2.3 `Parametro`

```
Parametro:
    nome: str                  # minúsculo, ASCII; único dentro da ação
    tipo: TipoParametro
    descricao: str             # lida pela paleta e pelo esquema da ferramenta do agente
    obrigatorio: bool = True
    opcoes: tuple[str, ...]    # só em ESCOLHA, e nunca vazio nesse caso
    maximo: int | None         # só em TEXTO: número máximo de caracteres (G10)
```

Os obrigatórios vêm **antes** dos opcionais (RN-AC-08). É o que torna a gramática posicional da
barra (Q7=A) sem ambiguidade.

### 2.4 `Acao`

```
Acao:
    nome: str                          # snake_case: é o nome da ferramenta do agente
    descricao: str
    escopo: Escopo
    parametros: tuple[Parametro, ...]
    chamadores: frozenset[Chamador]    # quem pode acionar (Q2=B: as 6 aceitam os dois)
    efetivar: (servico, alvo, argumentos, referencias, acionamento) -> Awaitable[objeto]
```

- **`nome`** vira o comando da barra trocando `_` por `-` (Q6=A): `criar_tarefa` →
  `/criar-tarefa`.
- **`efetivar`** chama **uma** operação de `ServicoDeAmbiente` e devolve o objeto que ela devolveu,
  ou deixa a exceção subir. **Não devolve `Resultado`** (G1): quem traduz para `Resultado` é o
  `CatalogoDeAcoes`, num ponto só. O critério 3 ("toda ação devolve `Resultado`") vale na fronteira
  do catálogo, que é o único caminho para executar uma ação.
- `efetivar` recebe os argumentos **já convertidos** e as referências **já achadas**. Não valida,
  não consulta política e não captura exceção.

### 2.5 As 6 ações (Q1=A, Q2=B)

| Ação | Barra | Escopo | Parâmetros, em ordem | Operação de U4 | Dado devolvido |
|---|---|---|---|---|---|
| `criar_frente` | `/criar-frente` | AMBIENTE | `nome` TEXTO ≤ 200 | `criar_frente(id_ambiente, nome)` | `Frente` |
| `criar_tarefa` | `/criar-tarefa` | FRENTE | `nome` TEXTO ≤ 200 | `criar_tarefa(id_ambiente, id_frente, nome)` | `Tarefa` |
| `criar_chat` | `/criar-chat` | TAREFA | `agente` TEXTO ≤ 100; `nome` TEXTO ≤ 200, **opcional** | `criar_chat(id_ambiente, id_tarefa, agente, nome)` | `Chat` |
| `criar_etapa` | `/criar-etapa` | TAREFA | `executor` ESCOLHA {`agente`, `usuario`}; `descricao` TEXTO ≤ 1.000 | `criar_etapa(id_ambiente, id_tarefa, descricao, executor)` | `EtapaNaPosicao` |
| `concluir_etapa` | `/concluir-etapa` | TAREFA | `posicao` POSICAO | `concluir_etapa(id_ambiente, id_etapa)` | `EtapaNaPosicao` |
| `anotar_memoria` | `/anotar-memoria` | TAREFA | `chave` TEXTO ≤ 100; `valor` TEXTO ≤ 20.000 | `anotar_memoria(id_ambiente, id_tarefa, chave, valor, autor)` | `Anotacao` |

Todas aceitam `chamadores = {USUARIO, AGENTE}` nesta iteração (D-Q2-1).

**Não existe** parâmetro `autor` em `anotar_memoria` (Q5=A): o autor vem do `Acionamento`. **Não
existe** parâmetro de identidade em nenhuma ação (Q3=A): toda identidade vem do `Alvo`.

**Ficam fora do registro** (Q1=A): criar, carregar, listar e apagar ambiente, que a tela de início
(U9) chama direto no serviço, e os comandos de navegação da tela (`/ajuda`, `/sair`, trocar de
chat), que são da U9.

---

## 3. Quem e onde

### 3.1 `Alvo`

```
Alvo:
    id_ambiente: Identidade
    id_frente: Identidade | None = None
    id_tarefa: Identidade | None = None
```

Sempre **explícito**: nunca "o item ativo" escondido no núcleo. Cada escopo usa só as identidades
que exige, e as demais são ignoradas (RN-AC-10).

**De onde vem:**

- **Usuário**: a tela monta a partir do que está selecionado. Tarefa selecionada → as três
  identidades; só frente selecionada → ambiente e frente; nada selecionado → só ambiente.
- **Agente**: U9 monta uma vez, ao abrir o chat, com o ambiente, a **frente da tarefa** e a
  **tarefa** do chat, e o amarra às ferramentas daquele chat (Q3=A). O agente não consegue
  mudá-lo. Consequência de **C1=A**: `criar_tarefa` acionada pelo agente cria na frente da própria
  tarefa dele.

### 3.2 `Acionamento`

```
Acionamento:
    chamador: Chamador     # USUARIO | AGENTE (dominio/politica.py, U1)
    autor: str             # quem assina o que for escrito
```

| Construção | `chamador` | `autor` |
|---|---|---|
| `Acionamento.usuario()` | `USUARIO` | `usuario` |
| `Acionamento.agente(nome)` | `AGENTE` | o nome do agente do chat (`Agente.nome`) |

Construído **pelo sistema** (a tela para o usuário; U9 ao abrir o chat para o agente), nunca a
partir de algo que o agente escreveu (RN-AC-12). É o `autor` da anotação de memória (Q5=A).

### 3.3 `ComandoDigitado`

```
ComandoDigitado:
    nome: str     # o que veio depois de "/" até o primeiro espaço; pode ser vazio
    texto: str    # o resto da linha, sem os espaços das pontas
```

Produto do parser. **Não** sabe se o nome é uma ação do catálogo ou um comando da tela (Q9=A).

---

## 4. Confirmação

### 4.1 `Referencias`

```
Referencias:
    frente: Frente | None
    tarefa: Tarefa | None
    etapa: EtapaNaPosicao | None
```

O que o alvo e os argumentos apontam, **já achado** no ambiente aberto antes de pedir confirmação
(G2). Serve para a tela mostrar nomes em vez de identidades, e para `efetivar` receber a etapa já
resolvida. É leitura: o catálogo não muda nenhum desses objetos (RN-AC-02).

### 4.2 `EtapaNaPosicao`

```
EtapaNaPosicao:
    etapa: Etapa
    posicao: int     # 1, 2, 3... na lista da tarefa
```

A posição é **linguagem de apontar**, não identidade: não é guardada em lugar nenhum, e o serviço
continua recebendo o id (Q8=A, RF-F16). `criar_etapa` e `concluir_etapa` devolvem a etapa **com** a
posição (G5), para quem acionou — em especial o agente — poder apontá-la depois.

### 4.3 `PedidoDeConfirmacao`

```
PedidoDeConfirmacao:        # imutável
    acao: str                          # nome da ação
    acionamento: Acionamento           # quem está pedindo (o nome do agente)
    alvo: Alvo
    argumentos: Mapping[str, object]   # já convertidos; somente leitura
    referencias: Referencias           # frente, tarefa e etapa já achadas
```

É **exatamente** o que vai executar: depois do "sim", o catálogo executa com estes argumentos e
estas referências, sem reler a posição da etapa (RN-AC-22, RN-AC-28). Em `concluir_etapa`,
`referencias.etapa` traz posição **e** descrição, para uma posição errada ficar visível antes de
você dizer "sim" (D-Q2-2).

### 4.4 `PortaDeConfirmacao`

```
PortaDeConfirmacao (protocolo):
    async confirmar(pedido: PedidoDeConfirmacao) -> bool
```

- Mora em `aplicacao/portas/`, como as outras portas; a dona é U5 e quem implementa é a tela (U9).
- **Só `True` confirma** (RN-AC-27). Qualquer outro valor é recusa.
- **Espera** a resposta (Q4=A): a chamada do agente fica parada até você responder.
- É o mecanismo que U8 vai reaproveitar para a proposta do bibliotecário (critério 6 de U8). Como o
  pedido do bibliotecário entra nela é decisão do FD de U8.

---

## 5. Como uma ação termina

### 5.1 `Resultado`

```
Resultado:                          # imutável
    sucesso: bool
    motivo: MotivoFalha | None
    detalhe: Mapping[str, str]      # vazio no sucesso
    dado: objeto | None             # só no sucesso

Resultado.ok(dado)
Resultado.falha(motivo, **detalhe)
```

**Invariantes** (~~RN-AC-33~~ **RN-AC-35** — emenda 2026-10-02, Code Generation: referência
corrigida): `sucesso` ⇔ `motivo is None`; `dado` só existe no sucesso; `detalhe`
só existe na falha. Nenhum campo traz frase em português, caminho de disco ou pilha de chamadas.

### 5.2 `MotivoFalha` (Q10=A)

| Motivo | Quando | `detalhe` |
|---|---|---|
| `ACAO_DESCONHECIDA` | o nome não está no registro | `acao` |
| `NAO_PERMITIDA` | quem acionou não está em `chamadores` | `acao`, `chamador` |
| `ARGUMENTO_INVALIDO` | faltou, sobrou, nome desconhecido, tipo errado, fora das opções, longo demais, ou agente fora da lista fechada | `parametro`, `problema` (`ausente`, `desconhecido`, `tipo`, `opcao`, `longo_demais`, `fora_da_lista`, **`sobrando`**); `maximo` quando longo demais |
| `ALVO_AUSENTE` | o `Alvo` não tem a identidade que o escopo exige (ex.: `/criar-tarefa` sem frente selecionada) | `falta` (~~`frente` ou `tarefa`~~ **`ambiente`**, `frente` ou `tarefa`) |

> **/!\ Emenda 2026-10-02 — Code Generation de U5 `acoes`.**
> - **`sobrando`** (`R-CG5-1`): texto que sobra na barra numa ação **sem** parâmetro. Vem sem
>   `parametro`, porque não é de parâmetro nenhum. Nenhuma das 6 ações chega a isso (o último
>   parâmetro sempre leva o resto); existe para a gramática ser total em qualquer registro.
> - **`falta=ambiente`**: `Alvo.id_ambiente` é obrigatório pelo tipo, mas um `None` ali (defeito de
>   montagem em U9) dá `ALVO_AUSENTE` em vez de falha inesperada.
> - **Eco cortado**: o nome desconhecido que volta no detalhe (`acao` de `ACAO_DESCONHECIDA` e
>   `parametro` de `desconhecido`) é cortado em 100 caracteres. É texto de quem acionou, e o agente
>   não precisa receber de volta, inteira, uma chave de tamanho qualquer.
| `ALVO_INEXISTENTE` | o ambiente, a frente, a tarefa ou a etapa apontada não existe | `alvo` (`ambiente`, `frente`, `tarefa`, `etapa`); `posicao` e `total` para etapa |
| `REGRA_VIOLADA` | o domínio recusou (nome vazio, segundo orquestrador, papel errado) | `erro` (nome do tipo do erro) |
| `CONFLITO` | outro processo gravou o mesmo ambiente três vezes seguidas (`ConflitoDeVersao` de U4) | — |
| `FALHA_DE_ARMAZENAMENTO` | o banco ou a wiki falhou | `erro` (nome do tipo do erro) |
| `RECUSADA` | você disse "não" à confirmação | — |
| `FALHA_INESPERADA` | qualquer outro erro: um defeito (Q11=A) | — (o erro completo vai para o log) |

### 5.3 Mapeamento das exceções

Do mais específico para o mais geral. **A tabela é total**: toda exceção cai em algum motivo
(RN-AC-34, PBT-U5-03).

| Exceção | Origem | Motivo |
|---|---|---|
| `AmbienteInexistente` | U2 | `ALVO_INEXISTENTE` (`alvo=ambiente`) |
| `FrenteInexistente` / `TarefaInexistente` / `EtapaInexistente` | U4 | `ALVO_INEXISTENTE` (`frente` / `tarefa` / `etapa`) |
| `AgenteDesconhecido` | U4 | `ARGUMENTO_INVALIDO` (`parametro=agente`, `problema=fora_da_lista`) |
| `ConflitoDeVersao` | U2, depois das 3 tentativas de U4 | `CONFLITO` |
| demais `ErroDePersistencia` (`BancoIlegivel`, `EsquemaIncompativel`, …) | U2 | `FALHA_DE_ARMAZENAMENTO` |
| `ErroDeWiki` (qualquer) | U3 | `FALHA_DE_ARMAZENAMENTO` |
| `ErroDeDominio` (`NomeInvalido`, `OrquestradorDuplicado`, `AgenteInvalido`) | U1 | `REGRA_VIOLADA` |
| qualquer outra `Exception` | defeito | `FALHA_INESPERADA` + log ERROR |
| cancelamento (`BaseException`) | — | **não é capturado**: passa |

`AmbienteInexistente` e `ConflitoDeVersao` herdam de `ErroDePersistencia`; por isso vêm antes da
linha geral. `ErroDeWiki` só aparece por defeito, já que o ciclo de vida ficou fora (Q1=A), e entra
na tabela para ela ser total.

---

## 6. Os dois componentes

### 6.1 `CatalogoDeAcoes`

```
CatalogoDeAcoes:
    construtor(servico: ServicoDeAmbiente,
               confirmacao: PortaDeConfirmacao,
               acoes: tuple[Acao, ...] = as 6 do registro)

    listar(escopo: Escopo | None = None, chamador: Chamador | None = None) -> tuple[Acao, ...]
    buscar(nome: str) -> Acao | None

    async executar(nome: str, alvo: Alvo, argumentos: Mapping[str, object],
                   acionamento: Acionamento) -> Resultado          # botão e agente
    async executar_comando(comando: ComandoDigitado, alvo: Alvo) -> Resultado   # barra "/"

comando_de(nome_da_acao: str) -> str     # criar_tarefa -> criar-tarefa
```

- **Não guarda estado** além do registro e das duas referências do construtor. Duas execuções
  concorrentes não se veem; quem serializa o acesso ao ambiente é a trava de U4.
- `acoes` é parâmetro do construtor para teste (ex.: uma ação só de usuário, que exercita
  `NAO_PERMITIDA`). Registro inválido levanta **`CatalogoInvalido`** na construção (RN-AC-08): é
  erro de montagem, não de uso. É a **única** exceção que o catálogo levanta.
- **`executar_comando` é sempre do usuário**: a barra `/` é sua, e o agente não digita nela. Por
  isso não recebe `Acionamento`; usa `Acionamento.usuario()`.

### 6.2 `ParserDeComando`

```
ParserDeComando:
    detectar(entrada: str) -> bool                   # começa com "/"
    interpretar(entrada: str) -> ComandoDigitado     # exige detectar(entrada)
    formatar(comando: ComandoDigitado) -> str        # a inversa de interpretar
```

- **Não conhece o catálogo** (Q9=A), nem o alvo (R-FD5-3): a tela passa o alvo direto ao catálogo.
  Serve igual para as ações e para os comandos da tela.
- `interpretar` de texto que não começa com `/` é erro de quem chamou (`ValueError`); para todo
  texto que começa com `/`, ele **nunca** levanta.

---

## 7. Erros

```
ErroDoCatalogo
└── CatalogoInvalido        registro mal formado, na construção (RN-AC-08)
```

Fora isso, o catálogo **não levanta**: toda falha de uso vira `Resultado` (~~RN-AC-32~~
**RN-AC-34** — emenda 2026-10-02, Code Generation: referência corrigida).
