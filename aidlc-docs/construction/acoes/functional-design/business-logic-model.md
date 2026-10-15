# Business Logic Model — U5 `acoes`

**Fase:** CONSTRUCTION · **Unidade:** `U5 acoes` · **Portão 1 de 2 (Functional Design)**
**Data:** 2026-10-02
**Decisões de origem:** Q1=A, **Q2=B**, Q3=A, Q4=A, Q5=A, Q6=A, Q7=A, Q8=A, Q9=A, Q10=A, Q11=A,
Q12=A; **C1=A**; R-FD5-1..8 e D-Q2-1..3 sem objeção.

---

## 1. Duas entradas, um caminho

Toda ação passa pelo mesmo caminho, venha de onde vier. É isso que torna o RF-F17 uma propriedade
da arquitetura em vez de uma convenção (Pergunta 7).

| Superfície | Entra por | Argumentos chegam como | Quem aciona |
|---|---|---|---|
| Barra `/` | `parser.interpretar` → `catalogo.executar_comando` | uma linha de texto | sempre o usuário (RN-AC-15) |
| Botão / atalho | `catalogo.executar` | nomes e valores | o usuário |
| Ferramenta do orquestrador | `catalogo.executar` (U6 chama, com o alvo e o acionamento amarrados por U9) | nomes e valores | o agente |

`executar_comando` só faz uma coisa a mais: transforma o texto em argumentos por nome (§3) e
continua no mesmo caminho de `executar`.

---

## 2. O caminho de `executar` (RN-AC-38)

```
executar(nome, alvo, argumentos, acionamento) -> Resultado

  try:
    1. acao = registro[nome]                     senão  ACAO_DESCONHECIDA
    2. acionamento.chamador em acao.chamadores   senão  NAO_PERMITIDA
    3. alvo tem o que acao.escopo exige          senão  ALVO_AUSENTE
    4. convertidos = validar(acao.parametros, argumentos)
                                                 senão  ARGUMENTO_INVALIDO
    5. referencias = achar(alvo, convertidos)    # lê o ambiente aberto; não muda nada
                                                 senão  ALVO_INEXISTENTE
    6. se exige_aprovacao(acionamento.chamador):
           pedido = PedidoDeConfirmacao(acao.nome, acionamento, alvo, convertidos, referencias)
           se (await confirmacao.confirmar(pedido)) is not True:
               devolve RECUSADA                  # nada foi escrito
    7. dado = await acao.efetivar(servico, alvo, convertidos, referencias, acionamento)
    8. devolve Resultado.ok(dado)
  except Exception as erro:
    devolve Resultado.falha(motivo_de(erro))     # tabela de domain-entities.md §5.3
                                                 # FALHA_INESPERADA também vai para o log
  # cancelamento não é Exception: passa sem ser tocado
```

Pontos que o pseudocódigo não deixa óbvios:

- **Passos 1 a 4 não leem nada.** Uma chamada com argumento ruim não toca o banco nem a tela.
- **O passo 5 lê o ambiente pelo serviço** (`carregar_ambiente`), que devolve o mesmo objeto aberto
  (RN-A-03). A trava de U4 é pega e solta dentro dessa leitura: **no passo 6 nenhuma trava está
  presa** (RN-AC-32), então esperar por você não bloqueia as suas próprias ações.
- **Entre o 6 e o 7 o mundo pode mudar.** Se outro processo apagar a frente enquanto você decide, U4
  levanta `FrenteInexistente` no passo 7, e o resultado é `ALVO_INEXISTENTE`. O catálogo não tenta
  impedir isso; o serviço revalida tudo pelo id.
- **O passo 7 recebe a etapa já achada** (RN-AC-22). A posição não é relida.
- **A exceção da porta de confirmação** ~~cai no mesmo `except` e~~ **tem `try` próprio e** vira
  `FALHA_INESPERADA`: nada executa (RN-AC-30).

  > **/!\ Emenda 2026-10-02 — Code Generation de U5 `acoes` (`R-CG5-5`).** Pelo `except` geral, uma
  > porta que levantasse um `ErroDePersistencia` cairia em `FALHA_DE_ARMAZENAMENTO`, e não em
  > `FALHA_INESPERADA`. A chamada à porta tem tratamento próprio: **qualquer** `Exception` dela é
  > falha inesperada, vai para o log e nada executa.

### 2.1 O que cada passo 5 acha

| Escopo / ação | Referências achadas |
|---|---|
| `AMBIENTE` (`criar_frente`) | nenhuma além do ambiente (que precisa existir) |
| `FRENTE` (`criar_tarefa`) | `frente` |
| `TAREFA` (as outras 4) | `tarefa` (e a frente dela) |
| `concluir_etapa` | também `etapa`, como `EtapaNaPosicao`, a partir de `posicao` |

A busca por identidade dentro do ambiente é a mesma travessia que U4 faz (`_achar_frente`,
`_achar_tarefa`). O catálogo tem a dele, de poucas linhas, em vez de U4 ganhar operação pública
nova: U4 está fechada, e o que o catálogo faz aqui é só **leitura para mostrar**, não regra.

---

## 3. A barra `/` (TD-11)

### 3.1 Do texto ao comando — `ParserDeComando`

```
detectar("/criar-tarefa campanha de verao")    -> True
detectar(" /criar-tarefa x")                   -> False      (vira conversa; G9)

interpretar("/criar-tarefa   campanha   de verao  ")
    -> ComandoDigitado(nome="criar-tarefa", texto="campanha   de verao")
interpretar("/")             -> ComandoDigitado(nome="", texto="")
interpretar("criar-tarefa")  -> ValueError                   (quem chamou não usou detectar)

formatar(ComandoDigitado("criar-tarefa", "campanha de verao")) -> "/criar-tarefa campanha de verao"
```

O nome vai até o **primeiro** espaço; os espaços entre o nome e o texto e os das pontas saem; os de
**dentro** do texto ficam como você digitou (RN-AC-40).

### 3.2 Do comando aos argumentos — `CatalogoDeAcoes.executar_comando`

1. `nome_da_acao = comando.nome` com `-` trocado por `_`, desde que `comando.nome` não tenha `_`
   (G7). Não está no registro → `ACAO_DESCONHECIDA`.
2. O texto é repartido pelos parâmetros, na ordem: cada um menos o último pega uma palavra; o último
   pega o resto (RN-AC-16). Acabou o texto → os parâmetros restantes ficam ausentes.
3. Segue em `executar(nome_da_acao, alvo, argumentos, Acionamento.usuario())`.

| Você digita | Argumentos |
|---|---|
| `/criar-frente comercial e ticket` | `nome="comercial e ticket"` |
| `/criar-tarefa campanha de verao` | `nome="campanha de verao"` — **critério 1, TD-11** |
| `/criar-chat bibliotecario` | `agente="bibliotecario"` (`nome` ausente → nome do agente) |
| `/criar-chat bibliotecario pesquisa de ICP` | `agente="bibliotecario"`, `nome="pesquisa de ICP"` |
| `/criar-etapa usuario assistir a aula 3` | `executor="usuario"`, `descricao="assistir a aula 3"` |
| `/criar-etapa Usuário assistir a aula 3` | igual à linha acima (G4) |
| `/concluir-etapa 2` | `posicao=2` |
| `/anotar-memoria travado-por esperando o cliente` | `chave="travado-por"`, `valor="esperando o cliente"` |
| `/criar-tarefa` | `ARGUMENTO_INVALIDO` (`nome`, `ausente`) |
| `/concluir-etapa dois` | `ARGUMENTO_INVALIDO` (`posicao`, `tipo`) |
| `/criar-tarefa x` sem frente selecionada | `ALVO_AUSENTE` (`falta=frente`) |
| `/criar_tarefa x` | `ACAO_DESCONHECIDA` (G7) |

---

## 4. O agente pedindo uma ação (Q4=A)

Exemplo de US-17: no chat do orquestrador da tarefa "lista de cálculo 2 — capítulo 4", ele chama
`criar_etapa(executor="usuario", descricao="ler o material")`.

1. U6 recebe a chamada da ferramenta e chama `catalogo.executar("criar_etapa", alvo_do_chat,
   {"executor": "usuario", "descricao": "ler o material"}, Acionamento.agente("orquestrador"))`.
   `alvo_do_chat` e o acionamento foram amarrados por U9 ao abrir o chat; o agente não os escolheu.
2. Passos 1 a 5: tudo válido; `referencias.tarefa` é a tarefa do chat.
3. Passo 6: `exige_aprovacao(AGENTE)` é `True`. O catálogo monta o pedido e **espera**.
4. A tela (U9) mostra: quem pede (orquestrador), a ação, a tarefa pelo nome e os argumentos.
5. Você diz "sim" → passo 7 → `Resultado.ok(EtapaNaPosicao(etapa, posicao=1))`. O agente recebe
   isso no mesmo turno e pode apontar "etapa 1" depois.
   Você diz "não" → `Resultado.falha(RECUSADA)`. Nada foi escrito, e o agente sabe disso.

Se o orquestrador criar quatro etapas seguidas, são quatro pedidos, um por vez (D-Q2-3).

> **Correção à D-Q2-3.** O exemplo da clarificação ("montar uma frente com 3 tarefas são 4
> confirmações") foi escrito antes da C1. Com **C1=A** ele não acontece desse jeito: o orquestrador
> cria a frente, mas as tarefas que ele cria vão para a frente da **própria** tarefa (RN-AC-14). O
> custo declarado continua o mesmo: uma confirmação por chamada.

---

## 5. Etapa pela posição (Q8=A)

```
achar_etapa(tarefa, posicao):
    se posicao > len(tarefa.etapas):  ALVO_INEXISTENTE (alvo=etapa, posicao, total)
    devolve EtapaNaPosicao(tarefa.etapas[posicao - 1], posicao)
```

(`posicao < 1` já foi recusada no passo 4.) A etapa achada viaja no pedido e chega a `efetivar`,
que chama `concluir_etapa(id_ambiente, etapa.id)`. A posição devolvida é recalculada a partir da
tarefa depois de executar: se uma recarga por conflito tiver trocado os objetos internos (RN-A-03),
a etapa é achada de novo pelo id.

---

## 6. Rastreabilidade

| História | Ação | Como U5 sustenta |
|---|---|---|
| **US-04** | `anotar_memoria` | o autor é quem acionou, nunca escolhido pelo agente (Q5=A) |
| **US-15** | `criar_frente` | pela barra, pelo botão ou pelo orquestrador com confirmação |
| **US-16** | `criar_tarefa` | idem; pelo orquestrador, na frente da tarefa dele (C1=A) |
| **US-17** | `criar_etapa` | o orquestrador cria cada etapa da conversa, com sua confirmação, e sabe o resultado no mesmo turno (Q4=A) |
| **US-19** | `concluir_etapa` | você confirma que fez (pela barra ou pelo botão); com Q2=B, o orquestrador também pode pedir, com confirmação |
| TD-11 | todas | RN-AC-16, PBT-U5-04 |

Nenhuma das cinco **fecha** em U5: todas fecham em U9, onde ficam demonstráveis na tela.

---

## 7. Propriedades testáveis (PBT-01)

| # | Propriedade | Categoria | Regras |
|---|---|---|---|
| **PBT-U5-01** | **Ida e volta do parser.** Para todo nome não vazio e sem espaço e todo texto sem espaço nas pontas (com acentos, `/`, tabulação e espaços repetidos por dentro), `interpretar(formatar(c)) == c` | Round-trip (PBT-02) | RN-AC-40, RN-AC-41 |
| **PBT-U5-02** | **Nome e comando.** Para todo nome `snake_case` válido, converter para comando e voltar dá o mesmo nome; e nenhum texto de comando acha mais de uma ação | Round-trip (PBT-02) | RN-AC-07 |
| **PBT-U5-03** | **Nunca levanta.** Para qualquer nome (do registro ou lixo), alvo (com ou sem identidades, existentes ou não), argumentos (chaves e tipos quaisquer), acionamento e exceção sorteada para o serviço levantar — todas as de §5.3 de `domain-entities.md` e outras quaisquer —, `executar` e `executar_comando` devolvem `Resultado`, e as invariantes de RN-AC-35 valem | Invariante (PBT-03) | RN-AC-34, RN-AC-35, RN-AC-36 |
| **PBT-U5-04** | **TD-11.** Para cada ação e valores gerados (uma palavra para cada parâmetro que não é o último; texto livre com espaços por dentro para o último), o serviço recebe exatamente esses valores, e o último chega com os espaços de dentro intactos | Invariante (PBT-03) | RN-AC-16 |
| **PBT-U5-05** | **Falha fechada.** Com o agente acionando e a porta respondendo qualquer coisa que não seja `True` (`False`, `None`, `1`, `"sim"`), ou levantando erro, o serviço **nunca** é chamado, o ambiente fica igual e o resultado é `RECUSADA` ou `FALHA_INESPERADA` | Invariante de segurança (PBT-03) | RN-AC-30, RN-AC-33 |
| **PBT-U5-06** | **Oráculo com sequência.** Uma sequência gerada de ações do usuário — válidas e inválidas — pelo catálogo leva ao mesmo estado que o modelo de referência de U4 (`ModeloDeAmbientes`, em `tests/ambiente/modelo.py`), comparado pela projeção dele, **depois de cada passo**. Ação recusada não muda o modelo | Oráculo / com estado (PBT-05, PBT-06) | RN-AC-05, RN-AC-38 |
| **PBT-U5-07** | **Confirmado é igual a usuário.** A mesma ação com os mesmos argumentos, pelo agente com "sim" e pelo usuário, deixa o ambiente no mesmo estado, a não ser pelo autor da anotação, que é o nome do agente | Oráculo (PBT-05) | RN-AC-13, RN-AC-28 |
| **PBT-U5-08** | **Posição.** Numa tarefa com N etapas geradas (algumas já concluídas), concluir a posição k com 1 ≤ k ≤ N conclui exatamente a k-ésima e nenhuma outra, e devolve `posicao == k`; k > N dá `ALVO_INEXISTENTE` e k < 1 dá `ARGUMENTO_INVALIDO`, sem escrita | Invariante (PBT-03) | RN-AC-22, RN-AC-23, RN-AC-24 |
| **PBT-U5-09** | **Idempotência.** Concluir a mesma posição duas vezes deixa o ambiente igual a concluir uma | Idempotência (PBT-04) | RN-AC-25 |
| **PBT-U5-10** | **Validação antes de tudo.** Para argumentos gerados que violam uma restrição (obrigatório faltando, chave a mais, tipo errado, fora das opções, acima do máximo, só espaços), o resultado é `ARGUMENTO_INVALIDO` com o `parametro` e o `problema` certos, **sem** pergunta à porta de confirmação e **sem** chamada ao serviço | Invariante (PBT-03) | RN-AC-17, RN-AC-18, RN-AC-19, RN-AC-21 |

**Sem propriedade, de propósito:** o registro em si. São 6 entradas fixas, verificadas na construção
(RN-AC-08) e por testes de exemplo; gerar registros aleatórios testaria a verificação, não as
ações.

**Geradores a construir no Code Generation (PBT-07)**: linha de comando (nome, espaços variados,
texto com acentos e Unicode), `Alvo` coerente com um ambiente gerado (e incoerente de propósito),
`Acionamento` dos dois tipos, argumentos válidos por ação e argumentos que violam cada restrição, e
o sorteio de exceção para o serviço. O ambiente gerado reaproveita os geradores de U4
(`tests/ambiente/estrategias.py`).

**Testes de exemplo que complementam (PBT-10)**: o critério 1 literal; um exemplo por motivo de
falha; o pedido pendente não bloqueia uma ação sua no mesmo ambiente (RN-AC-32); a falha inesperada
vai para o log sem os argumentos (RN-AC-37); `CatalogoInvalido` para cada defeito de registro de
RN-AC-08.

---

## 8. Decisões tomadas nesta geração (para revisão no portão)

Nenhuma delas veio de pergunta. Estão aqui para você aprovar, mudar ou recusar junto com o resto.

| # | Decisão | Por quê |
|---|---|---|
| **G1** | `Acao.efetivar` devolve o objeto ou levanta; **só `CatalogoDeAcoes.executar` devolve `Resultado`**. Muda a assinatura de `component-methods.md` §2.1 | Um ponto de tradução em vez de seis; é o que U4 combinou (Q3=A de U4), e uma ação nova não tem como esquecer o `try` |
| **G2** | O catálogo **acha as referências antes de perguntar**, lendo o ambiente aberto | A confirmação mostra nomes, e não ids; `concluir_etapa` precisa mostrar posição e descrição (D-Q2-2); e alvo inexistente falha antes de você ser incomodado |
| **G3** | Texto só de espaços conta como **ausente** nas duas superfícies; `valor` da anotação é **obrigatório** no catálogo (o domínio aceita valor vazio) | Na barra, os dois casos já são indistinguíveis; anotação sem valor não serve a ninguém |
| **G4** | `ESCOLHA` compara sem maiúscula e sem acento | Você vai digitar `usuário`, com acento |
| **G5** | `criar_etapa` e `concluir_etapa` devolvem `EtapaNaPosicao` | Sem a posição, o orquestrador não consegue apontar a etapa que acabou de criar |
| **G6** | `PortaDeConfirmacao` mora em `aplicacao/portas/`, com U5 como dona | É uma porta como as outras: a aplicação define, uma camada de fora implementa |
| **G7** | Nome de comando comparado **exatamente**; `/criar_tarefa`, com sublinhado, não é aceito | Um jeito só de escrever cada comando |
| **G8** | `executar_comando` aciona sempre como usuário | A barra é sua; o agente não digita nela |
| **G9** | `detectar` exige `/` como **primeiro** caractere | É o que `component-methods.md` §2.3 já dizia; espaço antes vira conversa |
| **G10** | **Limites de tamanho** por parâmetro: nome de frente, tarefa e chat ≤ 200; nome de agente e chave ≤ 100; descrição de etapa ≤ 1.000; valor de anotação ≤ 20.000 caracteres | SECURITY-05 exige limite em toda entrada de texto, e esta é a primeira fronteira em que entrada **do agente** muda estado. Os números são meus, generosos de propósito, e mudam só no registro |

---

## 9. Consequências para outras unidades

Registradas também como emenda em `unit-of-work.md`, para não se perderem.

| Unidade | O que herda de U5 |
|---|---|
| **U6 `sessao`** | (1) As **6 ações** são a família de ferramentas de ambiente; o invariante R10 verifica os 6 nomes (D-Q2-1), e onde o teste mora é decisão de U6 (R-FD5-8). (2) O esquema de cada ferramenta sai de `Parametro`: tipo, obrigatório, opções, máximo e descrição. (3) **Medir** se uma ferramenta MCP in-process pode esperar uma pessoa sem tempo limite (risco de Q4=A); se houver limite, U5 é reaberta. (4) O texto que o agente recebe é montado a partir do `Resultado`, incluindo a posição da etapa |
| **U7 `conversa`** | (1) O estado da tarefa que chega ao orquestrador a cada chamada traz **as etapas, com posição e situação**, e não só a memória (D-Q2-2). (2) Cancelar o turno cancela o pedido pendente, e nada executa (RN-AC-30) |
| **U8 `bibliotecario`** | (1) A proposta usa a **mesma** `PortaDeConfirmacao` (critério 6 de U8). (2) O nome do bibliotecário é ASCII minúsculo (ex.: `bibliotecario`), porque é o que se digita em `/criar-chat` e U4 compara o nome exatamente |
| **U9 `interface`** | Implementar `PortaDeConfirmacao` (quem pede, ação, referências pelo nome, argumentos; posição **e** descrição da etapa); enfileirar pedidos de chats diferentes que chegam juntos; tirar da tela o pedido cancelado; montar `Alvo` a partir da seleção e `Acionamento` do usuário; amarrar `Alvo` e `Acionamento` de cada chat às ferramentas do agente; escrever a frase de cada `MotivoFalha`; não criar comando de tela com nome de ação; **escapar o texto** do usuário e do agente ao desenhar (marcação do Textual); dar destino ao log `fishingrod.acoes` |

**Código antigo:** `model/comando.py` **não** é removido ao fechar U5 (R-FD5-7).

---

## 10. Conformidade das extensões

| Extensão | Estado | Justificativa |
|---|:--:|---|
| **`security-baseline`** | ✅ | **SECURITY-05**: tipo, opções e tamanho conferidos antes de qualquer efeito (RN-AC-17..19, G10); nomes de ação e de parâmetro de lista fixa; injeção não se aplica (o catálogo não monta consulta, e U2 usa parâmetros); escapar texto na tela é de U9 (§9). **SECURITY-08**: autorização por objeto, com o alvo amarrado pelo sistema (RN-AC-11); autorização por função, com `chamadores` conferido no catálogo e não só na tela (RN-AC-06). **SECURITY-11**: a política mora num ponto só (RN-AC-27); defesa em camadas (quem pode acionar + alvo amarrado + validação + confirmação + lista fechada de U4); caso de abuso considerado: um agente com instrução injetada não consegue agir fora da própria tarefa (RN-AC-11) e, se inundar de pedidos, cada um é uma recusa sua, e cancelar o turno cancela a espera. **SECURITY-15**: falha fechada (RN-AC-30), tratador único (RN-AC-34), sem detalhe interno no resultado (RN-AC-35), sem trava presa (RN-AC-32). **SECURITY-03**: log de falha inesperada sem argumentos (RN-AC-37). **N/A**: SECURITY-01, 02, 04, 06, 07, 09, 12 e 14 (sem rede, servidor, IAM, criptografia em repouso própria nem credencial nesta unidade); SECURITY-10 (nenhuma dependência nova); SECURITY-13 (U5 não persiste; a integridade é de U2 e U4); limitação de taxa de SECURITY-11 (nada exposto publicamente) |
| **`property-based-testing`** (Full) | ✅ | **PBT-01**: 10 propriedades identificadas com categoria (§7), e o componente sem propriedade justificado. **PBT-02**: PBT-U5-01 e PBT-U5-02. **PBT-03**: PBT-U5-03, 04, 05, 08 e 10. **PBT-04**: PBT-U5-09. **PBT-05**: PBT-U5-06 e 07. **PBT-06**: o catálogo não guarda estado; a propriedade com estado é a sequência de PBT-U5-06, conferida a cada passo. **PBT-07**: geradores listados em §7. **PBT-08** e **PBT-09**: `hypothesis` já está configurado desde U0, com o resto verificado no Code Generation. **PBT-10**: testes de exemplo listados em §7 |
| `resiliency-baseline` | N/A | Desabilitada em 2026-08-17 |
