# Business Logic Model — U6 `sessao`

**Fase:** CONSTRUCTION · **Unidade:** `U6 sessao` · **Portão 1 de 4 (Functional Design)**
**Data:** 2026-10-02
**Base:** `domain-entities.md` e `business-rules.md` desta pasta; respostas Q1–Q14 e C1–C3.

---

## 1. Quem fala com quem

```
U9 (composition root) --monta--> RegistroDeFerramentas
                                   <- entradas_de_acoes(catalogo)      [U6, sem SDK]
                                   <- entradas de wiki                 [U8]
U9 --constroi--> AdaptadorSessaoClaude(registro, pasta_de_trabalho, fabrica_de_cliente)

U7 / U8 --abrir(agente, contexto)--> PortaSessao --> SessaoViva
U7 / U8 --enviar(sessao, texto)----> PortaSessao --> eventos do turno
U7 / U8 --fechar(sessao)-----------> PortaSessao

agente --pede ferramenta--> SDK --> Ferramenta.executar --> CatalogoDeAcoes.executar [U5]
                                                       --> PortaDeConfirmacao     [U9]
```

Duas consequências do desenho, que as regras garantem:

- **U7 não importa o catálogo** (o motivo de Q12=A de Units Generation continua de pé): quem conhece o
  catálogo é o módulo de ferramentas, e só U9 o importa.
- **O adaptador não conhece regra de negócio**: ele traduz `Ferramenta` neutra para o SDK e mensagens
  do SDK para eventos. Esquema, validação, confirmação e texto moram fora dele (Q9=A).

---

## 2. Abrir uma sessão (RN-S-05..15)

1. Se o adaptador já foi encerrado → `AdaptadorEncerrado`.
2. Para cada nome em `agente.ferramentas`, na ordem:
   1. nome repetido → `ConfiguracaoDeSessaoInvalida(ferramenta_repetida)`;
   2. nome fora do registro → `ConfiguracaoDeSessaoInvalida(ferramenta_desconhecida)`;
   3. `agente.papel = SUB_AGENTE` e família `AMBIENTE` → `ConfiguracaoDeSessaoInvalida(escopo_violado)`
      (R10).
3. Para cada entrada achada: `ferramenta = fabrica(contexto, agente)`. Se a fábrica levantar, ou
   devolver outro nome, ou um esquema que não é de objeto → `ConfiguracaoDeSessaoInvalida`.
4. A sessão nasce em `SEM_CONEXAO`, com as ferramentas já fabricadas e agrupadas por família. Nenhum
   processo sobe (Q2=B).
5. Devolve a `SessaoViva`. O log registra a abertura (agente, id da sessão, nomes das ferramentas).

Os passos 2.1 a 2.3 são o mesmo código de `RegistroDeFerramentas.verificar_escopo` (RN-S-15). Se
alguma verificação falhar, nada é criado.

---

## 3. Um turno (RN-S-16..27, RN-S-33)

```
enviar(sessao, texto)
  |
  +-- sessão FECHADA ............................ FalhaDoTurno(SESSAO_FECHADA)
  +-- sessão EM_TURNO ........................... FalhaDoTurno(TURNO_EM_ANDAMENTO)
  +-- texto vazio ou > 100.000 caracteres ....... FalhaDoTurno(MENSAGEM_INVALIDA)
  |
  +-- toma a vaga: EM_TURNO  (antes de qualquer espera, RN-S-27)
  +-- SEM_CONEXAO? sobe o processo (§4) ......... falhou: FalhaDoTurno(categoria) -> SEM_CONEXAO
  +-- entrega a mensagem ........................ MensagemEntregue(conversa_nova)
  +-- lê o provedor até o fim da resposta ....... PedacoDeTexto / UsoDeFerramenta
  +-- fim da resposta:
        houve texto ou uso de ferramenta ........ FimDeTurno -> OCIOSA
        não houve ............................... FalhaDoTurno(RESPOSTA_VAZIA) -> OCIOSA
        provedor sinalizou erro ................. FalhaDoTurno(categoria) -> estado do §5
```

As três primeiras saídas não tocam o provedor nem a vaga do turno: um turno em andamento continua
intacto.

### 3.1 Do provedor aos eventos

O adaptador liga o modo de mensagens parciais do SDK (Q1=B). Tabela de tradução:

| O que chega do SDK | Vira |
|---|---|
| trecho parcial de texto | `PedacoDeTexto` com o trecho, se não for vazio |
| bloco de texto completo | nada, se os trechos já cobriram o bloco; o que falta, se cobriram só o começo; o bloco inteiro, se não veio trecho nenhum (RN-S-19) |
| começo de um novo bloco de texto, depois de outro bloco de texto no mesmo turno | linha em branco no começo do primeiro pedaço desse bloco (RN-S-20) |
| bloco de pedido de ferramenta completo, de ferramenta da sessão | `UsoDeFerramenta` |
| bloco de pedido de ferramenta de fora da sessão | nada: negado e registrado no log (RN-S-11, RN-S-22) |
| trecho parcial de pedido de ferramenta | nada (G9) |
| raciocínio interno (*thinking*) | nada (RN-S-21) |
| resultado de ferramenta | nada (RN-S-23) |
| mensagem de sistema (`init`, limite de uso informativo, contagem de tokens) | nada, a não ser que seja o sinal medido de limite atingido (§4) |
| mensagem de resultado, sem erro | fim da resposta |
| mensagem de resultado, com erro | `FalhaDoTurno`, pela tabela do §4 |

O nome de família e de ferramenta sai do nome qualificado `mcp__<familia>__<nome>`. Um nome que não
segue esse formato, ou cuja família ou ferramenta não é da sessão, é "de fora da sessão".

---

## 4. Falhas (RN-S-28..31, RN-S-34)

Tabela pela causa. Os sinais concretos do SDK e do CLI (tipo de exceção, texto, código de saída) são
fixados pela medição do Code Generation (§8). Se uma causa não puder ser reconhecida com certeza, ela
cai na última linha que couber.

| Causa | Motivo | Derruba a conexão? |
|---|---|:--:|
| o executável do CLI não foi achado | `PROVEDOR_AUSENTE` | sim |
| o CLI avisa que não há login | `NAO_AUTENTICADO` | sim |
| o CLI avisa que o limite da assinatura foi atingido | `LIMITE_DE_USO` | não |
| o processo morreu, a conexão caiu, a resposta veio truncada ou ilegível, o serviço está fora | `INDISPONIVEL` | sim |
| qualquer outra exceção | `FALHA_INESPERADA`, com pilha no log | sim |
| cancelamento | **não é falha**: passa (§6) | — |

"Derruba a conexão" significa: o processo é fechado e descartado, e a sessão vai a `SEM_CONEXAO`. Na
dúvida, derruba. Uma conexão boa descartada à toa custa uma reconexão. Uma conexão quebrada mantida
custa a próxima mensagem.

---

## 5. Estados e transições (RN-S-32..41)

| De | Acontece | Para | Evento final do turno |
|---|---|---|---|
| — | `abrir` | `SEM_CONEXAO` | — |
| `SEM_CONEXAO` | `enviar`, o processo sobe e a mensagem é entregue | `EM_TURNO` | — (`MensagemEntregue(conversa_nova=True)`) |
| `SEM_CONEXAO` | `enviar`, o processo não sobe | `SEM_CONEXAO` | `FalhaDoTurno` (categoria) |
| `OCIOSA` | `enviar` | `EM_TURNO` | — (`MensagemEntregue(conversa_nova=False)`) |
| `EM_TURNO` | a resposta termina bem | `OCIOSA` | `FimDeTurno` |
| `EM_TURNO` | resposta vazia ou limite de uso | `OCIOSA` | `FalhaDoTurno` |
| `EM_TURNO` | falha que derruba (§4) | `SEM_CONEXAO` | `FalhaDoTurno` |
| `EM_TURNO` | interrupção, com o aviso ao provedor bem-sucedido | `OCIOSA` | nenhum |
| `EM_TURNO` | interrupção, com o aviso ao provedor falhando, ou antes da entrega | `SEM_CONEXAO` | nenhum |
| `EM_TURNO` | `enviar` de novo | `EM_TURNO` (sem mudança) | `FalhaDoTurno(TURNO_EM_ANDAMENTO)` no segundo envio |
| qualquer um, menos `FECHADA` | `fechar` | `FECHADA` | `FalhaDoTurno(SESSAO_FECHADA)` no turno em andamento, se houver |
| `FECHADA` | `fechar` | `FECHADA` | — (nada acontece) |
| `FECHADA` | `enviar` | `FECHADA` | `FalhaDoTurno(SESSAO_FECHADA)` |
| qualquer um | `encerrar` no adaptador | `FECHADA` | como `fechar` |

`conversa_nova = True` exatamente na primeira entrega depois de cada subida de processo.

> **/!\ Emenda 2026-10-13 — NFR Design de U6** (N2, `DP-S-05`). Nas duas linhas de interrupção, a
> sessão fica em `EM_TURNO` até o adaptador terminar de avisar o provedor (a "cauda", até 5 s). A
> linha "`EM_TURNO` | `enviar` de novo" vale quando **há alguém lendo** o turno. Na cauda não há: o
> `enviar` novo toma a vaga, espera a cauda e segue do estado a que ela levar (`OCIOSA` ou
> `SEM_CONEXAO`).

---

## 6. Interromper (Q7=A, C2=A — RN-S-35, RN-S-36, RN-S-44)

1. Quem lê o turno é cancelado (o ESC da tela cancela essa tarefa, D-Q7-1) ou abandona o iterador.
2. O adaptador cancela **todas** as execuções de ferramenta registradas na sessão. A espera da
   confirmação de U5 está entre elas, e por isso nada pendente executa (RN-AC-30).
3. **Se a mensagem ainda não tinha sido entregue**, o processo que estava subindo é fechado, e a
   sessão vai a `SEM_CONEXAO`. Para o agente, a mensagem nunca existiu.
4. **Se já tinha sido entregue**, o adaptador avisa o provedor para parar a resposta. Deu certo: a
   sessão vai a `OCIOSA`, com o histórico, incluindo a mensagem interrompida. Deu errado: o processo é
   descartado e a sessão vai a `SEM_CONEXAO`.
5. O cancelamento continua subindo até quem cancelou. Não há evento final, porque não há mais quem o
   leia.

> **/!\ Emenda 2026-10-13 — NFR Design de U6** (N3, Q2=A, `DP-S-02`). Nos passos 3 e 4, "já tinha
> sido entregue" quer dizer **o leitor recebeu `MensagemEntregue`**. No passo 4, o aviso ao provedor
> e o fim da resposta interrompida têm prazo de **5 s**; passou, o processo é descartado.

O que U7 e U9 fazem com isso (§10): se `MensagemEntregue` não chegou, o texto volta ao campo sem
rastro; se chegou, o texto volta ao campo **e** a mensagem fica na transcrição marcada como
interrompida.

---

## 7. Da ação à ferramenta (Q8=A, Q9=A, Q10=A — RN-S-46..51)

**Na montagem (U9):** `entradas_de_acoes(catalogo)` produz uma entrada por ação que aceita o
agente. Cada entrada tem uma fábrica.

**Na abertura (§2, passo 3):** a fábrica recebe o contexto e o agente e devolve a `Ferramenta`:

1. `esquema` montado a partir dos `Parametro` (RN-S-47);
2. `alvo = Alvo(contexto.id_ambiente, contexto.id_frente, contexto.id_tarefa)`;
3. `acionamento = Acionamento.agente(agente.nome)`;
4. `executar(argumentos)`:
   1. `resultado = await catalogo.executar(acao.nome, alvo, argumentos, acionamento)` — a política e
      a confirmação acontecem aqui dentro (U5);
   2. devolve `RespostaDaFerramenta(texto = JSON de resultado, erro = not resultado.sucesso)`.

**Na execução (adaptador):** o SDK chama a função traduzida. O adaptador registra a execução na
sessão (§6), passa os argumentos em cópia somente leitura, converte a `RespostaDaFerramenta` para o
formato do SDK e tira o registro no fim. Se a função levantar algo que não seja cancelamento, o
agente recebe a resposta de erro genérica e o log recebe a pilha (RN-S-43).

**Exemplo** — o orquestrador da tarefa "campanha de verão" cria uma etapa:

| Passo | O que acontece |
|---|---|
| o agente pede | `mcp__ambiente__criar_etapa` com `{"executor": "usuario", "descricao": "revisar o briefing"}` |
| evento para U7 | `UsoDeFerramenta(AMBIENTE, "criar_etapa", {…})` |
| U5 | valida, pergunta a você pela `PortaDeConfirmacao` e espera |
| você diz sim | U4 cria a etapa; `Resultado.ok(EtapaNaPosicao(…, posicao=3))` |
| o agente lê | `{"ok":true,"etapa":{"posicao":3,"descricao":"revisar o briefing","executor":"usuario","concluida":false}}` |
| você diz não | o agente lê `{"ok":false,"motivo":"recusada","detalhe":{}}`, marcado como erro |

---

## 8. Medições obrigatórias no Code Generation

O spike não mediu nada disto. Cada item vira um teste com o SDK real, que só roda quando pedido (o
NFR decide quando), e a medição fica registrada no resumo do código.

| # | O que medir | Se der errado |
|---|---|---|
| 1 | Formato das mensagens parciais de texto e como elas convivem com o bloco completo | RN-S-19 já cobre a falta de trechos; se o formato impedir os trechos, vale o bloco inteiro e a Q1 é reaberta |
| 2 | Tempo-limite de uma ferramenta que espera uma pessoa (herança 3 de U5, R-FD6-7) | Limite configurável: U6 o põe no maior valor aceito e declara. Não configurável: **U5 é reaberta** antes de U6 fechar |
| 3 | O que o aviso de interrupção do SDK faz com uma ferramenta em espera | RN-S-44 cancela pela sessão de qualquer jeito; a medição diz se o aviso ao provedor basta para a resposta parar |
| 4 | Como o CLI sinaliza falta de login e limite de uso | Sem sinal confiável, as duas categorias caem em `INDISPONIVEL` (RN-S-29) |
| 5 | O efeito de não repassar as variáveis de credencial (RN-S-52) | Se o CLI falhar sem elas numa máquina com login, a regra é revista |
| 6 | **Que, sem o parâmetro de limite de passos, o SDK não corta o turno sozinho** (D-Q12-1) | Se cortar, o corte vira `FALHA_INESPERADA` com log, e a Q12 é reaberta |
| 7 | O erro quando o CLI não está instalado | Define o sinal de `PROVEDOR_AUSENTE` |
| 8 | Que um prompt vazio não traz de volta o prompt do Claude Code (RN-S-10) | Se trouxer, sessão sem regras passa a ser recusada em `abrir` |
| 9 | Que o SDK aceita um JSON Schema completo como esquema de ferramenta | Se não aceitar, o adaptador converte o esquema neutro para o formato que o SDK aceita, sem mudar `Ferramenta` |
| 10 | **Critério 3** com a versão travada: duas sessões vivas ao mesmo tempo (R-FD6-4) | Bloqueia U6 |

> **/!\ Emenda 2026-10-13 — NFR Design de U6.** As medições 2, 3, 4 e 5 mudam de método, e entram a
> **15** (nenhuma cópia da conversa em `~/.claude/projects/`) e a **16** (ESC e prazo vencido não
> deixam processo vivo). Ver `nfr-design/nfr-design-patterns.md` §6.

---

## 9. Propriedades testáveis (PBT-01)

| # | Propriedade | Categoria | Regras |
|---|---|---|---|
| **PBT-U6-01** | **Gramática do turno.** Para qualquer roteiro de mensagens do provedor no formato do SDK (com ou sem trechos parciais, com falha sorteada em qualquer ponto: ao subir, ao entregar, no meio da resposta), os eventos seguem a gramática de RN-S-17, e `FimDeTurno` só sai se houve texto ou uso de ferramenta | Invariante (PBT-03) | RN-S-17, RN-S-24 |
| **PBT-U6-02** | **Texto preservado.** Para blocos de texto gerados (Unicode, espaços, quebras de linha) partidos em trechos de forma arbitrária, inclusive sem trecho nenhum, a concatenação dos pedaços é igual aos blocos unidos por linha em branco, e nenhum pedaço é vazio | Invariante / oráculo (PBT-03, PBT-05) | RN-S-19, RN-S-20 |
| **PBT-U6-03** | **Nunca levanta.** Para qualquer exceção sorteada (as do SDK e outras quaisquer) em qualquer ponto do turno, `enviar` termina em `FalhaDoTurno` com o motivo da tabela do §4, a sessão vai ao estado da tabela do §5 e nenhum processo fica sem dono. Só o cancelamento passa | Invariante de segurança (PBT-03) | RN-S-16, RN-S-28, RN-S-34, RN-S-38 |
| **PBT-U6-04** | **Nome qualificado, ida e volta.** Para toda família e todo nome `snake_case` válido, separar `mcp__<familia>__<nome>` devolve a família e o nome; textos fora do formato não são separados | Round-trip (PBT-02) | RN-S-12, RN-S-22 |
| **PBT-U6-05** | **Esquema fiel aos parâmetros.** Para listas de `Parametro` geradas (válidas por RN-AC-08), o esquema tem exatamente esses nomes, `required` igual aos obrigatórios, `enum` igual às opções, `maxLength` igual ao máximo, `POSICAO` inteiro com mínimo 1 e nada além. **Emenda 2026-10-13 (R-CG6-4): mais `pattern: "\S"` em texto obrigatório e `maximum: 999999999` em `POSICAO`** | Invariante (PBT-03) | RN-S-47 |
| **PBT-U6-06** | **Esquema e catálogo concordam.** Para cada uma das 6 ações, argumentos gerados **a partir do esquema** (texto não vazio dentro do máximo, valor do `enum`, inteiro ≥ 1) nunca dão `ARGUMENTO_INVALIDO` no catálogo | Verificação fácil / oráculo (PBT-05) | RN-S-47, RN-AC-17..19 |
| **PBT-U6-07** | **Texto do agente, ida e volta.** Para todo `Resultado` gerado (sucesso com os 5 tipos de `dado`, falha com os 10 motivos de U5), ler de volta o JSON devolve `ok`, `motivo` e `detalhe`; `erro == not sucesso`; e o texto **nunca** contém nenhuma identidade do ambiente gerado | Round-trip + invariante de segurança (PBT-02, PBT-03) | RN-S-50, RN-S-51 |
| **PBT-U6-08** | **R10.** Para qualquer `Agente` gerado (os dois papéis, ferramentas sorteadas do registro e nomes inexistentes, com repetição), `abrir` é recusada **se e somente se** há sub-agente com ferramenta de ambiente, nome desconhecido ou repetido; e `verificar_escopo` aponta exatamente as mesmas violações | Invariante de segurança + oráculo (PBT-03, PBT-05) | RN-S-06, RN-S-07, RN-S-15 |
| **PBT-U6-09** | **Ciclo de vida com estado.** Sequências geradas de `abrir`, `enviar` (com desfecho sorteado: bem, vazio, limite, falha que derruba), interromper (antes e depois da entrega), `fechar`, `fechar` de novo e `encerrar`, contra um modelo de estados: **depois de cada passo**, o estado, o número de processos vivos e o `conversa_nova` da próxima entrega batem com o modelo. Fechar duas vezes deixa tudo como fechar uma | Com estado + idempotência (PBT-06, PBT-04) | RN-S-32..39 |
| **PBT-U6-10** | **Sessões isoladas.** Duas sessões com roteiros gerados, intercaladas de forma arbitrária (inclusive com falha, interrupção ou fechamento de uma delas), produzem cada uma exatamente os eventos que produziria sozinha | Invariante (PBT-03) | RN-S-40 |
| **PBT-U6-11** | **Interromper cancela tudo.** Com k ferramentas em execução gerada (algumas esperando confirmação), interromper em qualquer ponto cancela as k, nenhuma efetiva depois, e a sessão termina em `OCIOSA` ou `SEM_CONEXAO` conforme §6 | Invariante de segurança (PBT-03) | RN-S-35, RN-S-44 |
| **PBT-U6-12** | **Mensagem inválida não sai.** Para texto só de espaços (de qualquer tipo de espaço Unicode) ou acima do máximo, o turno termina em `MENSAGEM_INVALIDA` e o provedor não recebe nada | Invariante (PBT-03) | RN-S-25 |

**Sem propriedade, de propósito:** a configuração de isolamento (RN-S-10, RN-S-52) e a tradução de
`Ferramenta` para o SDK. São valores fixos montados uma vez; um teste de exemplo que inspeciona as
opções montadas (sem ferramenta nativa, sem configuração da máquina, prompt em texto, ambiente sem as
variáveis de credencial, permissão pelos nomes exatos) prova mais que dados gerados.

**Geradores a construir no Code Generation (PBT-07):** roteiro de provedor no formato do SDK (blocos
de texto partidos em trechos, pedidos de ferramenta da sessão e de fora, falhas sorteadas por
posição); exceções do SDK e quaisquer outras; `Agente` com papel e ferramentas sorteados; listas de
`Parametro` válidas; `Resultado` de cada tipo; sequências de comandos de ciclo de vida. O ambiente
gerado reaproveita os geradores de U4 (`tests/ambiente/estrategias.py`) e os de U5
(`tests/acoes/estrategias.py`).

**Testes de exemplo que complementam (PBT-10):** o **teste de contrato** de TD-01, o mesmo para o
adaptador falso e para o real (este com o cliente roteirizado na suíte padrão e com o CLI de verdade
quando pedido); um exemplo por motivo de falha; reconexão com `conversa_nova`; R10 com os 6 nomes
reais; a inspeção das opções de isolamento; a confirmação pendente cancelada pela interrupção, com o
catálogo de U5 de verdade; `TURNO_EM_ANDAMENTO`; `fechar` no meio de um turno; o critério 2 (TD-02),
importando `dominio/` e `aplicacao/` sem o SDK; o critério 3 com o CLI de verdade.

---

## 10. Consequências para outras unidades

Registradas também como emenda em `unit-of-work.md`.

| Unidade | O que herda de U6 |
|---|---|
| **U5 `acoes`** | Nada muda, a não ser que a medição 2 ache um tempo-limite que não se configura. Nesse caso, U5 é reaberta (R-FD6-7) |
| **U7 `conversa`** | (1) **Fila** (C1=B): o que você escreve durante um turno sai junto, numa mensagem só, quando o turno acaba. Se a mensagem juntada passar de 100.000 caracteres, a sessão a recusa (RN-S-25). (2) **Depois de uma falha** (C3=A), a fila não sai sozinha: o texto volta ao campo. (3) **Transcrição honesta** (C2=A): uma mensagem só fica na transcrição se `MensagemEntregue` chegou. Interrompida depois disso, fica marcada como interrompida. Uma mensagem que falhou antes da entrega também não chegou ao agente. (4) **`conversa_nova`** num chat que já tem transcrição pede um aviso de que o agente não lembra o que veio antes (R-FD6-10). (5) **Qual `Agente` abre a sessão** de um chat salvo: a cópia guardada ou a configuração atual (R-FD6-9). (6) Montar o `ContextoDaSessao` a partir do chat. (7) ~~Usar cada sessão sempre a partir do mesmo contexto async (fato do spike).~~ **Emenda 2026-10-13 (NFR Design, Q1=A): dispensado; a tarefa dona de cada conexão é a única a tocar o cliente do SDK, e `enviar` pode ser chamado de qualquer tarefa.** (8) **Prompt do orquestrador**: depois de agir, contar o que fez e onde ("ação X feita, Y está no chat Z") (D-Q3-1). (9) Quando fechar a sessão de um chat, e o que mostrar no chat se `abrir` levantar `ConfiguracaoDeSessaoInvalida`. (10) `UsoDeFerramenta` vira `registrar_uso_ferramenta`; o resumo dos argumentos é de U7 |
| **U8 `bibliotecario`** | (1) As ferramentas de wiki entram no registro como entradas da família `WIKI`, com fábrica `(contexto, agente) -> Ferramenta`; o texto que o bibliotecário lê é de U8. (2) O teste R10 das instâncias reais chama `verificar_escopo`. (3) O bibliotecário abre sessão pela mesma porta, sem ferramenta nativa (RN-S-10) |
| **U9 `interface`** | (1) Montar o registro: `entradas_de_acoes(catalogo)` mais as entradas de U8. (2) Resolver a pasta de trabalho das sessões e entregá-la ao adaptador. (3) Chamar `encerrar()` no fim do programa. (4) **ESC**: cancelar a tarefa que lê o turno, devolver ao campo o texto da mensagem interrompida e o da fila, e mostrar a mensagem interrompida, se ela chegou ao agente (C2=A, D-Q7-1). (5) Mostrar a fila. (6) Escrever a frase de cada `MotivoFalhaDeSessao`; em `NAO_AUTENTICADO`, dizer como fazer o login. (7) Mostrar o aviso de conversa nova (R-FD6-10). (8) Dar destino ao log `fishingrod.sessao` |
| **Próxima iteração** | **Retomada do histórico** (opção D da Q5), junto com US-07. Ela destrava também o "desver" de uma mensagem entregue (D-Q5-1) |

---

## 11. Decisões tomadas nesta geração (para revisão no portão)

Nenhuma delas veio de pergunta. Estão aqui para você aprovar, mudar ou recusar junto com o resto.

| # | Decisão | Por quê |
|---|---|---|
| **G1** | O evento de falha se chama **`FalhaDoTurno`**, e não `ErroProvedor` | Três dos motivos não são do provedor |
| **G2** | O aviso de conversa sem histórico vai em **`MensagemEntregue`** (`conversa_nova`), e não no evento final, como a Q5=A dizia | Chega antes, num lugar só, e vale tanto para turno que termina bem quanto para turno que falha. Cobre também o reinício do programa (R-FD6-10), e não só a reconexão |
| **G3** | Blocos de texto do mesmo turno são separados por **linha em branco** pelo adaptador | Sem isso, "Vou criar a etapa." e "Pronto." chegam grudados, e U7 teria de conhecer blocos |
| **G4** | Motivo **`MENSAGEM_INVALIDA`**, com teto de **100.000 caracteres** por mensagem | SECURITY-05 exige limite em toda entrada de texto. O número é meu, folgado para colar um documento, e muda num lugar só |
| **G5** | `abrir` **levanta** `ConfiguracaoDeSessaoInvalida` em vez de devolver evento | É erro de montagem, como `CatalogoInvalido` de U5; a Q2=B continua valendo, porque `abrir` nunca falha por causa do provedor |
| **G6** | **Abandonar o iterador é interromper**; `fechar` durante um turno termina o turno em `SESSAO_FECHADA` | Nenhum jeito de largar um turno pode deixar ferramenta rodando ou processo sem dono |
| **G7** | **`encerrar()`** é do adaptador, não da porta, e depois dele `abrir` é recusada | Só o composition root encerra; e nenhum processo pode nascer depois do fim do programa |
| **G8** | Pedido de ferramenta **de fora da sessão** não vira `UsoDeFerramenta` | Não executa, porque o SDK nega. Vai para o log, que é onde uma tentativa de abuso deve aparecer |
| **G9** | `UsoDeFerramenta` sai do **bloco completo**, nunca dos trechos parciais | Os argumentos parciais são JSON pela metade |
| **G10** | O contexto tem **só identidades**; o nome do agente vem do `Agente` | Um lugar só para o nome que assina |
| **G11** | O adaptador recebe **registro, pasta de trabalho e fábrica de cliente** no construtor | A fábrica de cliente é a costura que deixa testar o adaptador real sem o CLI. A pasta é de U9, que é o único lugar que conhece caminho de disco |
| **G12** | A projeção **não tem id**, a anotação devolve **só o autor**, e um `dado` desconhecido vira `{"ok": true}` com aviso no log | O agente nunca usa id (Q3=A de U5); repetir um valor de até 20.000 caracteres só gastaria contexto |
| **G13** | Falha classificada **pela causa**, e na dúvida derruba a conexão | Conexão descartada à toa custa uma reconexão; conexão quebrada mantida custa a próxima mensagem |
| **G14** | O esquema leva `minLength: 1` em texto obrigatório e `additionalProperties: false` | Orienta o modelo; o catálogo continua sendo quem decide |
| **G15** | Regras vazias viram **prompt vazio**, nunca o prompt do Claude Code | É o que Q11=A pede. Confirmado pela medição 8 |

---

## 12. Conformidade das extensões

| Extensão | Estado | Justificativa |
|---|:--:|---|
| **`security-baseline`** | ✅ | **SECURITY-03**: log só de metadados, sem mensagem, argumento ou credencial (RN-S-54). **SECURITY-05**: limite e não vazio na mensagem (RN-S-25, G4); argumentos de ferramenta validados por quem a implementa, sem confiar no esquema (RN-S-04, RN-S-42); nenhuma consulta ou comando montado com texto do modelo. **SECURITY-08**: permissão por nome exato, pedido de fora negado e registrado (RN-S-11); autorização por objeto, com o alvo amarrado pelo contexto (RN-S-48); por função, com R10 em duas camadas (RN-S-07, RN-S-15). **SECURITY-09**: instalação mínima, sem ferramenta nativa nem configuração da máquina (RN-S-10); erro sem detalhe interno (RN-S-31). **SECURITY-11**: a lógica de escopo mora num lugar só (`verificar_escopo`); defesa em camadas (registro + R10 na abertura + permissão exata + validação de U5 + confirmação); casos de abuso considerados: instrução injetada tentando agir fora da tarefa (impossível, RN-S-48), agente em laço (interrupção, risco aceito em D-Q12-1), `Agente` adulterado no banco (RN-S-07), chave de API no ambiente (RN-S-52). **SECURITY-12**: nenhuma credencial lida, guardada ou registrada; autenticação só pela assinatura (RN-S-52, RN-S-53). **SECURITY-13**: o que vem do modelo é tratado como não confiável e passa pela validação de U5 antes de qualquer efeito. **SECURITY-15**: `enviar` nunca levanta (RN-S-16), falha fechada na abertura (RN-S-06..08), processo nunca sem dono (RN-S-38), erro genérico ao agente (RN-S-43). **N/A**: SECURITY-01, 02, 04, 06, 07 e 14 (sem armazenamento próprio, rede exposta, servidor, IAM ou infraestrutura de alerta); **SECURITY-10** fica para o NFR Requirements desta unidade, que decide a entrada do SDK como dependência (R-FD6-11) |
| **`property-based-testing`** (Full) | ✅ | **PBT-01**: 12 propriedades com categoria (§9), e o que ficou sem propriedade está justificado. **PBT-02**: PBT-U6-04 e 07. **PBT-03**: PBT-U6-01, 02, 03, 05, 07, 08, 10, 11 e 12. **PBT-04**: PBT-U6-09 (`fechar`). **PBT-05**: PBT-U6-02, 06 e 08. **PBT-06**: PBT-U6-09, conferido a cada passo. **PBT-07**: geradores listados em §9. **PBT-08** e **PBT-09**: `hypothesis` configurado desde U0; o resto é verificado no Code Generation. **PBT-10**: testes de exemplo listados em §9 |
| `resiliency-baseline` | N/A | Desabilitada em 2026-08-17 |
