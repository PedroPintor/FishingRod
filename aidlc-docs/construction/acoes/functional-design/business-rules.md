# Business Rules — U5 `acoes`

**Fase:** CONSTRUCTION · **Unidade:** `U5 acoes` · **Portão 1 de 2 (Functional Design)**
**Data:** 2026-10-02
**Prefixo:** `RN-AC-nn`. As regras de U1 (`RN-nn`), U2 (`RN-P-nn`), U3 (`RN-W-nn`) e U4 (`RN-A-nn`)
continuam valendo; aqui entra só o que é de acionamento.

---

## 1. Fronteira

| # | Regra | Origem |
|---|---|---|
| **RN-AC-01** | O catálogo e o parser conhecem **só** o domínio, o `ServicoDeAmbiente` e a `PortaDeConfirmacao`. Nenhum `import` de `sqlite3`, `claude_agent_sdk`, `textual`, `os` ou `pathlib`, nem de adaptador | D-ARQ-04; RF-F04 |
| **RN-AC-02** | **O catálogo nunca muda o `Ambiente` diretamente.** Toda mudança passa por uma operação de U4. Ele **lê** o ambiente aberto, e só para achar as referências antes de pedir confirmação (G2) | RN-A-02; R-FD5-5 |
| **RN-AC-03** | **A invariante é do domínio e do serviço.** O catálogo valida só a **forma** dos argumentos: presença, tipo, opções e tamanho. Nome vazio, lista fechada de agentes e segundo orquestrador continuam sendo recusados por U1 e U4, e o catálogo só traduz a recusa | R-FD5-5; RN-A-02 |
| **RN-AC-04** | **Conversar não é ação.** Não existe ação de enviar mensagem | critério 4; Pergunta E2 |

## 2. Registro

| # | Regra | Origem |
|---|---|---|
| **RN-AC-05** | **As ações são dado, num registro só**: `criar_frente`, `criar_tarefa`, `criar_chat`, `criar_etapa`, `concluir_etapa`, `anotar_memoria`. A paleta, os botões e as ferramentas do agente leem o mesmo registro. O ciclo de vida do ambiente e a navegação ficam na tela (U9) | critério 2; Q1=A; R-FD5-1 |
| **RN-AC-06** | **Cada ação declara quem pode acioná-la.** Nesta iteração as 6 aceitam usuário e agente. Quem aciona fora da lista recebe `NAO_PERMITIDA` **antes de qualquer outra verificação**. O catálogo confere isso mesmo que a tela e U9 já não ofereçam a ação: a autorização não depende de a interface esconder o botão | Q2=B; D-Q2-1; SECURITY-08 |
| **RN-AC-07** | **Um nome, dois jeitos de escrever.** O nome da ação é `snake_case` ASCII minúsculo e é o nome da ferramenta do agente. O comando da barra é o mesmo nome com `-` no lugar de `_`. A conversão é bijetiva, e a barra só aceita a forma com hífen: `/criar_tarefa` é ação desconhecida (G7) | Q6=A |
| **RN-AC-08** | **O registro é verificado ao construir o catálogo**: nomes de ação únicos e no padrão; nomes de parâmetro únicos dentro da ação **e no mesmo padrão**; obrigatórios antes dos opcionais; `ESCOLHA` com opções **distintas sem maiúscula nem acento**; `TEXTO` com máximo **(inteiro ≥ 1)**; **opções só em `ESCOLHA` e máximo só em `TEXTO`**; **`POSICAO` só em ação de escopo `TAREFA`, e no máximo uma por ação**; `chamadores` não vazio **e só de `Chamador`**. Registro inválido levanta `CatalogoInvalido` — erro de montagem, não de uso | — **· `R-CG5-3`** |

> **/!\ Emenda 2026-10-02 — Code Generation de U5 `acoes`.** RN-AC-08 ganhou as verificações em
> negrito. A de `POSICAO` é a reconciliação **`R-CG5-3`** do plano de CG: a posição aponta uma etapa
> da tarefa-alvo, então sem tarefa no escopo não há lista para apontar, e com duas posições não se
> saberia qual etapa a confirmação mostra. As demais saíram da execução: "opções só em `ESCOLHA`" e
> "máximo só em `TEXTO`" já estavam em `domain-entities.md` §2.3 e passaram a ser verificadas; opções
> que só diferem em maiúscula ou acento seriam a mesma escolha por G4; o padrão `snake_case` dos
> parâmetros é o que o esquema da ferramenta do agente (U6) vai exigir. Cada uma tem um
> `CatalogoInvalido` próprio em `tests/acoes/test_registro.py`.
| **RN-AC-09** | `listar` devolve na ordem do registro e filtra por escopo e por quem pode acionar. É daí que a paleta tira a lista do usuário e U9 tira as ferramentas do orquestrador | critério 2; Q2=B |

## 3. Alvo e quem aciona

| # | Regra | Origem |
|---|---|---|
| **RN-AC-10** | **Alvo explícito.** `id_ambiente` sempre; `id_frente` em escopo `FRENTE`; `id_tarefa` em escopo `TAREFA`. Faltando o que o escopo exige, `ALVO_AUSENTE` com o que falta, **antes de qualquer leitura**. Identidades além das exigidas são ignoradas | `component-methods.md` §2.1; Pergunta 7 |
| **RN-AC-11** | **O alvo do agente é amarrado pelo sistema** à tarefa do chat: o ambiente, a frente da tarefa e a tarefa. O agente não passa identidade: **nenhum parâmetro de nenhuma ação é identidade**. Assim, ele não consegue agir em outra tarefa, em outra frente para criar tarefa, nem em outro ambiente | Q3=A; SECURITY-08 |
| **RN-AC-12** | **Quem aciona é dito pelo sistema, nunca pelo agente.** O `Acionamento` do usuário é montado pela tela; o do agente, por U9 ao abrir o chat, com `Agente.nome` | Q3=A; Q5=A |
| **RN-AC-13** | **O autor da anotação é o `autor` do `Acionamento`**: o nome do agente, ou `usuario`. Não existe parâmetro `autor`; um argumento `autor` vindo do agente é parâmetro desconhecido | Q5=A |
| **RN-AC-14** | **Pelo agente, `criar_tarefa` cria na frente da tarefa do chat.** Uma frente criada pelo agente fica vazia até o usuário criar tarefa nela | C1=A |
| **RN-AC-15** | **A barra `/` é do usuário.** `executar_comando` sempre aciona como usuário e não recebe `Acionamento` | Q9=A |

## 4. Argumentos

| # | Regra | Origem |
|---|---|---|
| **RN-AC-16** | **Pela barra, o último parâmetro leva o resto.** Cada parâmetro, menos o último, pega uma palavra (até o próximo espaço); o último pega o resto da linha, com os espaços de dentro **intactos**. Mata TD-11 | Q7=A; critério 1 |
| **RN-AC-17** | **Pelo botão e pelo agente, argumentos por nome.** Nome que não é parâmetro da ação dá `ARGUMENTO_INVALIDO` (`desconhecido`), e a ação não executa | Q3=A; Q5=A |
| **RN-AC-18** | **Obrigatório ausente** dá `ARGUMENTO_INVALIDO` (`ausente`). Texto só de espaços conta como ausente, nas duas superfícies, porque a barra já remove os espaços das pontas (G3). **Opcional ausente** recebe o padrão (`criar_chat` sem `nome` → nome do agente, regra de U1) | Q7=A; G3 |
| **RN-AC-19** | **Tipo, opção e tamanho** conferidos contra o `Parametro`: tipo errado → `tipo`; fora das opções → `opcao`; acima do máximo → `longo_demais`, com o `maximo` no detalhe | SECURITY-05; G4; G10 |
| **RN-AC-20** | Na barra, a **chave** da memória é uma palavra: `travado-por` sim, `travado por` não. Pelo agente ou pelo botão, pode ter espaço | Q7=A |
| **RN-AC-21** | **Toda a validação acontece antes da confirmação.** Você nunca é perguntado sobre uma ação que não executaria por argumento ruim, alvo ausente ou alvo inexistente | Q4=A |

## 5. Etapa pela posição

| # | Regra | Origem |
|---|---|---|
| **RN-AC-22** | **`concluir_etapa` aponta a etapa pela posição** (1, 2, 3…) na lista da tarefa-alvo. O catálogo converte a posição na etapa **antes** de pedir confirmação, e quem executa recebe a etapa já achada: o que você confirmou é o que é concluído, sem reler a posição | Q8=A; D-Q2-2 |
| **RN-AC-23** | Posição menor que 1, ou que não é número, dá `ARGUMENTO_INVALIDO`. Posição maior que o número de etapas dá `ALVO_INEXISTENTE`, com `posicao` e `total` no detalhe | Q8=A; Q10=A |
| **RN-AC-24** | `criar_etapa` e `concluir_etapa` devolvem a etapa **com a posição** | G5 |
| **RN-AC-25** | **Concluir a mesma posição duas vezes é o mesmo que uma** (herda RN-A-23) | RN-A-23; PBT-04 |
| **RN-AC-26** | **Risco aceito.** A posição só é estável porque etapa é sempre acrescentada no fim (RN-08 de U1) e nesta iteração não há apagar nem reordenar etapa. Se uma iteração trouxer qualquer um dos dois, **esta seção é reaberta** | Q8=A |

## 6. Confirmação

| # | Regra | Origem |
|---|---|---|
| **RN-AC-27** | **A política é consultada uma vez, no catálogo**, para toda ação: `exige_aprovacao(acionamento.chamador)`. Nenhuma ação consulta por conta própria, então nenhuma pode esquecer | critério 5; R-FD5-2 |
| **RN-AC-28** | **Agente: o catálogo pergunta e espera.** Monta o `PedidoDeConfirmacao` e aguarda a `PortaDeConfirmacao`. Com "sim", executa e devolve o resultado real; com "não", devolve `RECUSADA`. Uma pergunta por chamada; não há "aprovar tudo" | Q4=A; D-Q2-3; R-FD5-6 |
| **RN-AC-29** | **Usuário: executa direto**, pela barra ou pelo botão | critério 5 |
| **RN-AC-30** | **Só `True` confirma** (falha fechada). Qualquer outra resposta é `RECUSADA`. Se a porta levantar erro, o resultado é `FALHA_INESPERADA`, o erro vai para o log e **nada executa**. Se a espera for cancelada, o cancelamento passa e nada executa | SECURITY-15 |
| **RN-AC-31** | **Executa exatamente o que foi mostrado.** O pedido é imutável, a porta só responde sim ou não, e não existe "editar e aprovar" | Q4=A |
| **RN-AC-32** | **Nenhuma trava de ambiente fica presa durante a espera.** Enquanto o pedido do agente aguarda você, suas ações no mesmo ambiente seguem normalmente | RN-A-06 |
| **RN-AC-33** | **Recusada não escreve nada.** Nenhuma chamada chega a U4 | Q4=A; SECURITY-15 |

## 7. Resultado e falhas

| # | Regra | Origem |
|---|---|---|
| **RN-AC-34** | **Toda chamada termina em `Resultado`.** O catálogo não deixa exceção sair, salvo cancelamento e interrupção do processo | critério 3; Q11=A; SECURITY-15 |
| **RN-AC-35** | **Forma do `Resultado`**: `sucesso` ⇔ sem `motivo`; `dado` só no sucesso; `detalhe` só na falha. Motivo e detalhe são estruturados: **nenhuma frase em português**, nenhum caminho de disco e nenhuma pilha de chamadas. A frase é da tela | Q10=A; SECURITY-15 |
| **RN-AC-36** | **O mapeamento de exceção para motivo é total**, do mais específico para o mais geral (`domain-entities.md` §5.3). Toda exceção cai em algum motivo | Q10=A; Q11=A |
| **RN-AC-37** | **Falha inesperada vai para o log** `fishingrod.acoes`, nível ERROR, com o nome da ação, o tipo de quem acionou, o tipo do erro e a pilha. **Os argumentos não vão para o log**, porque podem trazer conteúdo seu (um valor de memória, por exemplo). Sem destino configurado, nada aparece: quem decide o destino é U9 | Q11=A; SECURITY-03 |
| **RN-AC-38** | **Ordem das verificações**, sempre a mesma: (1) a ação existe; (2) quem aciona pode; (3) o alvo tem o que o escopo exige; (4) os argumentos; (5) as referências existem; (6) a confirmação, se for agente; (7) a execução. A primeira que falha decide o motivo, e nada depois dela acontece | Q10=A |

## 8. Parser

| # | Regra | Origem |
|---|---|---|
| **RN-AC-39** | **`detectar`**: a entrada começa com `/`. Espaço antes da barra faz a entrada ser conversa, e não comando (G9) | `component-methods.md` §2.3 |
| **RN-AC-40** | **`interpretar`** separa o nome (o que vem depois de `/` até o primeiro espaço) do texto (o resto, sem os espaços das pontas). Não conhece ações nem alvo. Não muda maiúscula nem acento do que você digitou. `/` sozinho dá nome vazio, e o catálogo responde `ACAO_DESCONHECIDA` | Q9=A; R-FD5-3; G7 |
| **RN-AC-41** | **`formatar` é a inversa de `interpretar`** para nome não vazio e sem espaço e para texto sem espaço nas pontas | PBT-02 |
| **RN-AC-42** | **O parser serve também os comandos da tela** (`/ajuda`, `/sair`). Nenhum comando da tela pode ter o mesmo nome de um comando de ação; garantir isso é de U9 | Q9=A |
