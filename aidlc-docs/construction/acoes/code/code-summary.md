# Code Summary — U5 `acoes`

**Fase:** CONSTRUCTION · **Unidade:** `U5 acoes` · **Portão 2 de 2, Parte 2** · **Data:** 2026-10-02
**Plano executado:** `construction/plans/acoes-code-generation-plan.md` — **18/18 passos**

---

## 1. Resultado

```
uv run pytest     ->  691 passed, 7 skipped      (era 343 passed, 7 skipped)
pyproject.toml    ->  dependencies = []          (pyproject.toml e uv.lock sem diff)
mutação           ->  12/12 defeitos derrubaram pelo menos um teste
                      (10/12 só com as propriedades; os 2 restantes são cobertos por exemplo, de propósito)
```

| | |
|---|--:|
| Itens de teste novos | **348** (97 funções; as propriedades por ação são parametrizadas) |
| Linhas em `src/` | **1.232** novas (5 módulos do catálogo e a porta); nenhum arquivo de `src/` modificado |
| Linhas em `tests/acoes/` | **2.955** |
| Dependências novas | **0** |

Os 7 testes pulados são os mesmos de antes; nenhum é novo. A suíte inteira levou de 82 s a 94 s nas três
execuções desta geração. Os testes de U5 sozinhos levam cerca de 18 s, quase tudo nas propriedades.

**TD-11 morre aqui.** `/criar-tarefa campanha de verao` chega ao serviço com o nome inteiro (critério 1,
`test_criterio_1_criar_tarefa_campanha_de_verao`). Os espaços de dentro ficam intactos para qualquer
separador (`PBT-U5-04`).

---

## 2. Arquivos

### Criados em `src/`

| Arquivo | Linhas | Conteúdo |
|---|--:|---|
| `aplicacao/catalogo/tipos.py` | 263 | `Escopo`, `TipoParametro`, `Parametro`, `Alvo`, `Acionamento` (`usuario()`, `agente(nome)`), `EtapaNaPosicao`, `Referencias`, `PedidoDeConfirmacao` (argumentos numa cópia somente leitura), `MotivoFalha` (os 10), `Resultado` (`ok`, `falha` e as invariantes de RN-AC-35 verificadas na construção), `Efetivar`, `Acao`, `ErroDoCatalogo`, `CatalogoInvalido` |
| `aplicacao/portas/confirmacao.py` | 39 | `PortaDeConfirmacao` (`Protocol`), com a semântica de RN-AC-27/30/31/32 na docstring |
| `aplicacao/catalogo/parser.py` | 61 | `ComandoDigitado` e `ParserDeComando` (`detectar`, `interpretar`, `formatar`); não importa nada do projeto |
| `aplicacao/catalogo/argumentos.py` | 181 | `repartir` (a barra, Q7=A), `converter` (as duas entradas), `sem_maiuscula_nem_acento` (G4), `ArgumentoRecusado` (interno) |
| `aplicacao/catalogo/registro.py` | 268 | as **6 ações** com `efetivar`, os limites de G10 e a busca por identidade dentro do ambiente aberto |
| `aplicacao/catalogo/catalogo.py` | 420 | `comando_de`, `nome_de`, a verificação do registro (RN-AC-08, `R-CG5-3`), a tabela de exceção para `Resultado` e `CatalogoDeAcoes`, com o caminho de RN-AC-38 comum às duas entradas |

`aplicacao/catalogo/__init__.py` continua **vazio** (já existia, com 0 bytes), como o plano declarou.

### Criados em `tests/acoes/`

| Arquivo | Itens | O que carrega |
|---|--:|---|
| `estrategias.py` | — | `montar` (o catálogo sobre o serviço real e o `RepositorioEmMemoria`); espaços (os 29 de `str.isspace()`), palavras e textos livres; escritas da opção com maiúscula e acento; `entradas_validas`, `violacoes` (com `casos_de_violacao`), linhas da barra; geradores de "qualquer coisa"; a tabela de exceções; `Passo` e `passos` (PBT-U5-06) |
| `instrumentos.py` | — | `ServicoEspiao`, `ServicoSabotado`, `ConfirmacaoFixa`, `ConfirmacaoQueLevanta`, `ConfirmacaoQueEspera`, `ConfirmacaoProibida` (com `PerguntaProibida`) |
| `modelo.py` | — | `forma` (projeção sem ids), `prever` (RN-AC-38 escrita de forma ingênua), `chamada_de_u4` e `devolvido_para_u4` (ponte para o `ModeloDeAmbientes` de U4) |
| `test_fronteira.py` | 6 | RN-AC-01 pelo grafo de import; `catalogo/__init__.py` vazio; parser e argumentos sem o serviço, verificado no AST e em tempo de execução, num subprocesso; critério 4 |
| `test_parser.py` | 35 | os exemplos de `business-logic-model.md` §3.1, G9, o `ValueError`, `formatar` |
| `test_argumentos.py` | 89 | a tabela de §3.2; G3 nas duas entradas; G4; cada máximo de G10 no limite e um acima; `None`; `bool`, `float` e dígito árabe-índico em `POSICAO`; `sobrando`; a ordem dentro de `ARGUMENTO_INVALIDO` |
| `test_registro.py` | 45 | as 6 ações como dado; `listar` e `buscar`; **24 defeitos de registro**, cada um com seu `CatalogoInvalido`; os casos-limite válidos |
| `test_catalogo.py` | 62 | os exemplos do passo 14, regra a regra (§6) |
| `test_propriedades.py` | 109 | **`PBT-U5-01` a `PBT-U5-10`** (§4) |
| `test_integracao.py` | 2 | `RepositorioSQLite` e `WikiDeArquivos` reais: US-04, 15, 16, 17 e 19 de ponta a ponta, fechando e reabrindo o programa; recusa que não chega ao disco |

### Documentação emendada (texto marcado, nada apagado)

| Artefato | Emenda |
|---|---|
| `functional-design/domain-entities.md` §2.2 | `POSICAO`: teto de 999.999.999 também para o inteiro |
| `functional-design/domain-entities.md` §5.1 e §7 | referências de regra corrigidas: ~~RN-AC-33~~ **RN-AC-35**, ~~RN-AC-32~~ **RN-AC-34** |
| `functional-design/domain-entities.md` §5.2 | **`sobrando`** (`R-CG5-1`, planejada); **`falta=ambiente`**; eco do nome desconhecido cortado em 100 caracteres |
| `functional-design/business-rules.md` RN-AC-08 | **`R-CG5-3`** (planejada: `POSICAO` só em escopo `TAREFA`, no máximo uma) e as verificações que a execução acrescentou (§3, decisão 6) |
| `functional-design/business-logic-model.md` §2 | a porta de confirmação ~~cai no mesmo `except`~~ **tem `try` próprio** (`R-CG5-5`) |

O plano previa duas emendas, `sobrando` e `R-CG5-3`. As outras três corrigem texto que o código
mostrou estar errado ou incompleto, e estão marcadas igual. O código antigo (`model/comando.py`,
`Ambiente/`, `cli.py`, `tui.py`) **não foi tocado** (R-FD5-7).

---

## 3. Decisões tomadas durante a execução

O que o plano não fixava, ou onde a execução divergiu dele.

| # | Decisão | Motivo |
|---|---|---|
| 1 | `Efetivar` é um alias `type` (preguiçoso), e `ServicoDeAmbiente` entra em `tipos.py` **só sob `TYPE_CHECKING`** | Em tempo de execução, importar `tipos.py` não carrega o serviço, e `parser.py` e `argumentos.py` ficam puros mesmo importando os tipos. `test_importar_parser_e_argumentos_nao_carrega_o_servico` verifica isso num subprocesso |
| 2 | A busca por identidade (`achar_frente`, `achar_tarefa`) mora em **`registro.py`**, e não em `catalogo.py` | As duas pontas a usam: o catálogo no passo 5, e as ações de etapa para devolver a posição. Como o catálogo já importa o registro, o contrário seria ciclo |
| 3 | `POSICAO` aceita inteiro **até 999.999.999** | Simetria com o texto de até 9 dígitos. Sem o teto, `str()` de um inteiro gigante no detalhe chegaria ao limite de conversão do Python. Emendado no FD |
| 4 | `ALVO_AUSENTE` com `falta=ambiente` quando `id_ambiente` é `None` | `Alvo` exige o campo pelo tipo, mas um defeito de montagem em U9 não deve virar falha inesperada. Emendado no FD |
| 5 | O nome desconhecido devolvido no detalhe é **cortado em 100 caracteres** | O `Resultado` vai para o contexto do agente. Emendado no FD |
| 6 | RN-AC-08 verifica também: padrão `snake_case` dos parâmetros, opções distintas depois de G4, máximo inteiro ≥ 1, opções só em `ESCOLHA`, máximo só em `TEXTO`, item que não é `Acao` | As duas do meio já estavam em `domain-entities.md` §2.3; as outras fecham buracos que um registro mal montado abriria. Emendado no FD |
| 7 | A porta tem `try` próprio, **dentro** do caminho, e o log de falha dela leva o tipo do erro original | `R-CG5-5`. A primeira versão levantava uma exceção interna para cair no `except` geral, mas o log mostraria o tipo interno em vez do erro da porta. A versão final é mais simples |
| 8 | As descrições de ação e de parâmetro **têm acento**; comentários e docstrings não têm | As descrições são texto de produto: a paleta as mostra e o esquema da ferramenta do agente as carrega (U6). O resto segue a convenção do código |
| 9 | `Resultado.dado` é o **objeto vivo** do ambiente aberto | É o que U4 devolve (Q1=A de U4). Um teste de exemplo pegou o efeito disso (a etapa criada aparece concluída depois de concluí-la) e passou a ler o estado na hora; a docstring do teste registra o porquê |
| 10 | `montar` semeia uma **cópia, com versão zero**, **só no repositório**, sem materializar a wiki | Nenhuma das 6 ações toca a wiki, porque o ciclo de vida ficou fora (Q1=A); o `WikiDeArquivos` continua sendo o do serviço. A cópia deixa o mesmo ambiente gerado semear dois repositórios (`PBT-U5-07`) e mantém intocado o objeto do teste. O plano citava `semear` de U4, que materializa a wiki; aqui ela é só custo |
| 11 | `Passo` e o gerador `passos` moram em `estrategias.py`, e não em `modelo.py` | PBT-07: geradores centralizados. Além disso, `modelo.py` importa de `estrategias.py`, e o contrário seria ciclo |
| 12 | `ConfirmacaoProibida` levanta `PerguntaProibida`, que é **`BaseException`** | Uma `AssertionError` comum seria capturada pelo catálogo e viraria `FALHA_INESPERADA` em silêncio |
| 13 | `PBT-U5-01` ganhou uma propriedade irmã: toda linha que começa com `/` é interpretada, e o que sai está no domínio em que `formatar` é a inversa | É o outro lado da ida e volta; 200 exemplos, como a primeira |
| 14 | `event()` do Hypothesis nas propriedades | Mesma decisão de U4: deixa medir de novo com `--hypothesis-show-statistics` |
| 15 | As propriedades "por ação" passaram a ser **parametrizadas** por ação, e PBT-U5-05 e 10 também pela resposta e pelo tipo de violação | §4: sorteando, combinações inteiras ficavam de fora. O total de exemplos de cada uma continua igual ou acima do plano |

---

## 4. Os geradores, medidos e endurecidos

As 10 propriedades passaram na primeira execução. Isso sozinho não prova nada, então medi o que cada
uma exercitava. Cinco tinham lacunas, todas com a mesma causa de fundo: **o Hypothesis favorece a
primeira opção de cada sorteio**, e `sampled_from` encolhe para o índice 0.

| Propriedade | Primeira versão | Correção | Depois |
|---|---|---|---|
| **`PBT-U5-03`** nunca levanta | só ~21% dos exemplos com entrada válida; o resto parava no passo 4. **`alvo_inexistente`, `recusada` e `falha_inesperada` nunca apareciam** | três modos (`quase`, `valida`, `qualquer`), com `quase` primeiro e peso dobrado: ação e argumentos válidos, mas alvo, quem aciona e porta quaisquer; o agente vem antes do usuário, e a resposta que não confirma vem antes de `True` | os **9 motivos** alcançáveis com o registro padrão aparecem (`recusada` 23%, `alvo_inexistente` 16%, `falha_inesperada` 4%…). `NAO_PERMITIDA` só aparece com um registro de teste, e tem exemplo próprio |
| **`PBT-U5-04`** TD-11 | **nenhum `anotar_memoria`** em 100 exemplos | parametrizada por ação (6 × 17) | as 6 ações, sempre |
| **`PBT-U5-05`** falha fechada | a resposta `[]` **nunca** saiu; `0` e `"sim"` em ~1% | parametrizada por ação e por resposta (6 × 9 × 2) | as 54 combinações, inclusive `1`, `"sim"` e `"True"`, que um `if resposta:` deixaria passar |
| **`PBT-U5-07`** confirmado = usuário | `criar_chat` em 1,6% | parametrizada por ação (6 × 10) | as 6 ações |
| **`PBT-U5-10`** validação antes | **`opcao` nunca** (só existe em `criar_etapa`); `tipo` em 3,7% | parametrizada pelos **36 pares** (ação, tipo de violação) que existem, 3 exemplos cada | os 36 pares |

As outras cinco já cobriam o que prometiam. `PBT-U5-06` alcança, nas sequências, sucesso e os quatro
motivos que o caminho do usuário sem sabotagem pode dar, pela barra (55% dos exemplos) e por argumentos
(70%). A lista fechada de agentes entra como `ARGUMENTO_INVALIDO`. `PBT-U5-08` sorteia posição dentro
(48%), além do fim (18%) e menor que 1 (33%), como `int` e como texto (cerca de metade cada).

### O teste dos testes: 12 mutações

Cada defeito do plano foi injetado no código, um de cada vez, e restaurado em seguida. O script ficou
fora do repositório, e o md5 dos fontes foi conferido depois. A mutação rodou duas vezes: contra
`tests/acoes` inteira e só contra `test_propriedades.py`.

| # | Defeito injetado | Primeiro teste que caiu (suíte) | Só as propriedades |
|---|---|---|---|
| M01 | agente executa sem perguntar | `test_recusada_rn_ac_33_nada_e_escrito` | morto (`PBT-U5-05`) |
| M02 | `if resposta:` em vez de `is True` | `test_rn_ac_30_so_true_confirma[1]` | morto (`PBT-U5-05[…-1]`) |
| M03 | `split()` ingênuo no último parâmetro | `test_rn_ac_16_tabela_da_barra[criar_frente…]` | morto (`PBT-U5-04`) |
| M04 | validação depois da confirmação (pergunta antes de validar) | `test_rn_ac_13_o_autor_e_quem_acionou` | morto (`PBT-U5-05`) |
| M05 | `ErroDePersistencia` antes de `AmbienteInexistente` no mapeamento | `test_alvo_inexistente` | morto (`PBT-U5-06`) |
| M06 | `except BaseException`, engolindo o cancelamento | `test_rn_ac_30_cancelar_a_espera_cancela_e_nada_executa` | **vivo**: cancelamento é cenário de tempo, coberto por exemplo |
| M07 | posição sem o `- 1` | `test_criterio_3_g1_…[/concluir-etapa 2-…]` | morto (`PBT-U5-04[concluir_etapa]`) |
| M08 | autor vindo do argumento (parâmetro `autor` opcional no registro) | `test_rn_ac_16_tabela_da_barra[anotar_memoria…]` | morto (`PBT-U5-04[anotar_memoria]`) |
| M09 | sem a verificação de `chamadores` | `test_nao_permitida_rn_ac_06_antes_de_qualquer_outra_verificacao` | **vivo**: as 6 ações aceitam os dois chamadores, então só um registro de teste mostra o defeito |
| M10 | escolha sem tirar o acento | `test_rn_ac_16_tabela_da_barra[criar_etapa-Usuário…]` | morto (`PBT-U5-04[criar_etapa]`) |
| M11 | sem o limite de tamanho | `test_g10_limite_de_tamanho[criar_frente…]` | morto (`PBT-U5-06`) |
| M12 | o parser apertando os espaços de dentro | `test_rn_ac_40_separa_nome_e_texto[…]` | morto (`PBT-U5-01`) |

Os dois que só os exemplos pegam são exatamente os casos que `business-logic-model.md` §7 manda para
exemplo (PBT-10): o cancelamento durante a espera e `NAO_PERMITIDA` com registro de teste.

---

## 5. Contrato publicado para as próximas unidades

```
# aplicacao/catalogo/catalogo.py
CatalogoDeAcoes(servico, confirmacao, acoes=ACOES)        # CatalogoInvalido se o registro for mal formado
    listar(escopo=None, chamador=None)                -> tuple[Acao, ...]
    buscar(nome)                                      -> Acao | None
    async executar(nome, alvo, argumentos, acionamento) -> Resultado     # botão e agente (U6)
    async executar_comando(comando, alvo)               -> Resultado     # barra "/", sempre usuário
comando_de(nome_da_acao) -> str          nome_de(comando) -> str | None

# aplicacao/catalogo/parser.py
ParserDeComando().detectar(entrada) -> bool
                 .interpretar(entrada) -> ComandoDigitado      # ValueError sem "/"
                 .formatar(comando) -> str

# aplicacao/portas/confirmacao.py — U9 implementa, U8 reaproveita
PortaDeConfirmacao.confirmar(pedido: PedidoDeConfirmacao) -> bool   # espera; só True confirma
```

`Resultado.dado` por ação: `Frente`, `Tarefa`, `Chat`, `EtapaNaPosicao`, `EtapaNaPosicao`,
`Anotacao`. Fora a montagem, o catálogo **nunca levanta**: só o cancelamento e a interrupção do
processo passam.

**Para U6:** o esquema de cada ferramenta sai de `Parametro` (tipo, obrigatório, opções, máximo,
descrição). Os nomes das ferramentas são os 6 nomes de `listar(chamador=Chamador.AGENTE)`. Continua
**aberto o risco** de a ferramenta MCP in-process ter tempo limite enquanto espera a pessoa (Q4=A). Se
houver, U5 é reaberta.

---

## 6. Rastreio

| Especificação | Onde se verifica |
|---|---|
| **US-04** `anotar_memoria` | `test_rn_ac_13_o_autor_e_quem_acionou`, `PBT-U5-07`, integração (dois autores, depois de reabrir) |
| **US-15 / US-16** | `test_criterio_1_*`, `test_rn_ac_14_c1_a_*`, `PBT-U5-04`, `PBT-U5-06`, integração |
| **US-17** (pelo orquestrador, com confirmação) | `test_criterio_5_*`, `test_rn_ac_32_*`, `PBT-U5-05`, `PBT-U5-07`, integração |
| **US-19** | `test_d_q2_2_*`, `PBT-U5-08`, `PBT-U5-09`, integração |
| **TD-11** — **morre aqui** | `test_criterio_1_*`, `test_rn_ac_16_*`, `test_rn_ac_40_*`, `PBT-U5-01`, `PBT-U5-04`; mutações M03 e M12 |
| RN-AC-01..04 | `test_fronteira.py` (6) |
| RN-AC-05..09 | `test_registro.py` (45) |
| RN-AC-10..15 | `test_rn_ac_10_*`, `test_alvo_ausente_*`, `test_rn_ac_11_e_13_*`, `test_rn_ac_13_*`, `test_rn_ac_14_*`, `test_rn_ac_15_*`, `test_regra_violada_*` |
| RN-AC-16..21 | `test_argumentos.py` (89), `test_rn_ac_21_*` (5), `PBT-U5-04`, `PBT-U5-10` |
| RN-AC-22..26 | `test_d_q2_2_*`, `test_alvo_inexistente`, `test_g5_*`, `PBT-U5-08`, `PBT-U5-09`. RN-AC-26 é risco aceito, sem teste |
| RN-AC-27..33 | `test_criterio_5_*`, `test_rn_ac_30_*` (3 grupos), `test_rn_ac_31_*` (2), `test_rn_ac_32_*`, `test_recusada_*`, `PBT-U5-05` |
| RN-AC-34..38 | `test_falha_inesperada_rn_ac_37_*`, `test_conflito_armazenamento_e_regra_*`, `test_resultado_nao_traz_frase_*`, `PBT-U5-03`, `PBT-U5-06` |
| RN-AC-39..42 | `test_parser.py` (35), `PBT-U5-01` |
| `R-CG5-1..6` | 1 → `test_r_cg5_1_*` · 2 → `test_alvo_ausente_antes_dos_argumentos_*` · 3 → `test_rn_ac_08_*[posicao…]` · 4 → `test_r_cg5_4_*` · 5 → `test_rn_ac_30_r_cg5_5_*` · 6 → `test_g3_*`, `test_rn_ac_16_o_ultimo_leva_*`, `ESPACOS` nos geradores |
| G1–G10 | G1 → `test_criterio_3_g1_*` · G2/D-Q2-2 → `test_d_q2_2_*` · G3 → `test_g3_*` · G4 → `test_g4_*` · G5 → `test_g5_*` · G6 → `test_fronteira.py` · G7 → `test_acao_desconhecida_pela_barra_g7`, `PBT-U5-02` · G8 → `test_rn_ac_15_*` · G9 → `test_rn_ac_39_*` · G10 → `test_g10_*` |
| Critérios de pronto 1–6 | 1 → `test_criterio_1_*` · 2 → `test_registro.py` · 3 → `test_criterio_3_g1_*`, `PBT-U5-03` · 4 → `test_criterio_4_*` · 5 → `test_criterio_5_*`, `PBT-U5-05` · 6 → `test_criterio_6_*` |

---

## 7. Conformidade das extensões

| Extensão / regra | Estado | Justificativa |
|---|:--:|---|
| `security-baseline` SECURITY-05 (validação de entrada) | ✅ | Tipo, opções e tamanho conferidos antes de qualquer efeito, com limite em toda entrada de texto (G10); `PBT-U5-10` nos 36 pares (ação, violação); mutação M11 morta |
| SECURITY-08 (controle de acesso) | ✅ | `chamadores` conferido no catálogo antes de tudo (`test_nao_permitida_*`, M09 morta); nenhum parâmetro é identidade (`test_rn_ac_11_e_13_*`); o alvo vem do sistema |
| SECURITY-11 (desenho seguro) | ✅ | A política é consultada num ponto só (M01 morta); pedido pendente não trava o ambiente (`test_rn_ac_32_*`) |
| SECURITY-15 (falha segura) | ✅ | `PBT-U5-03` (nunca levanta, 9 motivos alcançados); `PBT-U5-05` (falha fechada, M02 morta); `R-CG5-5`; o cancelamento passa (M06 morta) |
| SECURITY-03 (log) | ✅ | Falha inesperada vai para `fishingrod.acoes` com ação, tipo de quem acionou, tipo do erro e pilha, **sem os argumentos**: verificado no serviço que falha e na porta que levanta |
| SECURITY-10 (dependências) | ✅ | Zero dependência nova; `pyproject.toml` e `uv.lock` sem diff |
| Demais regras de `security-baseline` | N/A | Sem rede, servidor, IAM, HTTP, criptografia própria ou credencial nesta unidade |
| PBT-01 (identificação) | ✅ | As 10 propriedades do FD, implementadas com o nome `test_pbt_u5_NN_*` |
| PBT-02 (round-trip) | ✅ | `PBT-U5-01` (e a irmã), `PBT-U5-02` |
| PBT-03 (invariantes) | ✅ | `PBT-U5-03`, `04`, `05`, `08`, `10` |
| PBT-04 (idempotência) | ✅ | `PBT-U5-09` |
| PBT-05 (oráculo) | ✅ | `PBT-U5-06` (o `ModeloDeAmbientes` de U4, que também precisa concordar com cada sucesso) e `PBT-U5-07` |
| PBT-06 (com estado) | ✅ | `PBT-U5-06`: sequências de 0 a 15 comandos, verificação depois de cada um |
| PBT-07 (geradores) | ✅ | Centralizados em `tests/acoes/estrategias.py`, reaproveitando U2–U4; medidos e endurecidos (§4) |
| PBT-08 (encolhimento e semente) | ✅ | Padrão do Hypothesis, nada desligado. A parte de CI fica para Build and Test |
| PBT-09 (framework) | ✅ | Hypothesis, em `dev` desde U0 |
| PBT-10 (complementar) | ✅ | Exemplos (`test_parser`, `test_argumentos`, `test_registro`, `test_catalogo`, `test_integracao`) separados das propriedades; M06 e M09 mostram por que os dois são necessários |
| `resiliency-baseline` | N/A | Desabilitada em 2026-08-17 |
