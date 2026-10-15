# Code Summary — U4 `ambiente`

**Fase:** CONSTRUCTION · **Unidade:** `U4 ambiente` · **Portão 2 de 2, Parte 2** · **Data:** 2026-10-02
**Plano executado:** `construction/plans/ambiente-code-generation-plan.md` — **13/13 passos**

---

## 1. Resultado

```
uv run pytest     ->  343 passed, 7 skipped      (era 272 passed, 7 skipped)
pyproject.toml    ->  dependencies = []          (pyproject.toml e uv.lock sem diff)
mutação           ->  16/16 defeitos injetados derrubaram pelo menos um teste
```

| | |
|---|--:|
| Testes novos | **71** (62 em `tests/ambiente/`, 9 em `tests/wiki/`) |
| Linhas em `src/` | **497** novas (o serviço) + **53** acrescentadas em U3 |
| Linhas em `tests/ambiente/` | **2.097** |
| Dependências novas | **0** |

Os 7 pulados são os mesmos de antes, nenhum novo: 5 de symlink de U3 (`NFR-W-18`), 1 de permissão
POSIX de U3 e 1 de U2. O teste de link desta unidade **não** é pulado: usa junction no Windows.

**Tempo.** A suíte inteira levou 66–67 s nas duas execuções desta geração, contra 17 s na medição
do baseline. Os testes novos somam cerca de 15 s (medido com `--durations`). O resto está nas
propriedades de U3 que tocam disco (`PBT-U3-02` sozinha levou 10,6 s), o mesmo regime de I/O lento
desta máquina descrito em `construction/wiki/code/code-summary.md` §3.1. O sensor `NFR-W-02` passou
nas duas execuções.

---

## 2. Arquivos

### Criados em `src/`

| Arquivo | Linhas | Conteúdo |
|---|--:|---|
| `aplicacao/servicos/servico_de_ambiente.py` | 497 | os 5 erros (`ErroDeServicoDeAmbiente` e 4 subclasses), `proposta_do_esquema` (RN-A-13), a busca de alvo por identidade (RN-A-08), `ServicoDeAmbiente` com os auxiliares `_trava`, `_abrir`, `_recarregar`, `_gravar`, `_mutar` e as **10 operações** |

### Modificados em `src/` (U3 reaberta, Q6=A)

| Arquivo | Linhas | Mudança |
|---|--:|---|
| `aplicacao/portas/wiki.py` | 186 → 205 | `apagar(localizador)` no `Protocol`, com a semântica e `R-CG4-2` na docstring |
| `adaptadores/wiki/wiki_de_arquivos.py` | 396 → 430 | `apagar` / `_apagar`: `resolver_raiz`, raiz inexistente é operação vazia, raiz sem `index.md` é `CaminhoForaDaRaiz`, `shutil.rmtree` dentro de `traduzindo_erros` |

### Criados em `tests/ambiente/`

| Arquivo | Testes | O que carrega |
|---|--:|---|
| `estrategias.py` | — | `executar`, os dois agentes fixos, `novo_servico`, `nova_wiki`, `semear`, `ponderado`, `ambientes_de_partida`, os geradores de esquema, nome e comando |
| `modelo.py` | — | `ModeloDeAmbientes` (previsão e efeito), `projetar`, `resolver` (seletor → id) e `chamar` |
| `instrumentos.py` | — | `PersistenciaEspia` e `WikiEspia`: diário compartilhado, gancho antes de delegar, `Injecao` (uma falha na n-ésima chamada, antes ou depois), ceder o laço |
| `test_fronteira.py` | 3 | RN-A-01 pelo grafo de import: nada de SDK, banco, tela, `os`, `pathlib`, `shutil` nem `fishingrod.adaptadores`; `servicos/__init__.py` sem reexportar |
| `test_servico_de_ambiente.py` | 50 | os exemplos, regra a regra (§6) |
| `test_propriedades.py` | 6 | **`PBT-U4-01` a `PBT-U4-06`** |
| `test_integracao.py` | 3 | `RepositorioSQLite` + `WikiDeArquivos` reais: US-05 fechando e reabrindo o programa, critérios 1 e 6, e conflito entre duas conexões ao mesmo banco |

### Modificados em `tests/wiki/`

| Arquivo | Mudança |
|---|---|
| `test_wiki_de_arquivos.py` | +8 testes de `apagar` (57 → 65); `apagar` entra nos três testes que percorrem todas as operações (corrotina, uma ida ao thread, esquema desconhecido) |
| `test_propriedades.py` | **`PBT-U3-08`** |

### Documentação emendada (texto riscado, nada apagado)

| Artefato | Emenda |
|---|---|
| `construction/wiki/nfr-design/logical-components.md` §1 | ~~4~~ **5** operações, com nota sobre `apagar` |
| `construction/wiki/code/code-summary.md` §2 | ~~4~~ **5** operações, contagem de testes e nota da reabertura |

`services.md`, `component-methods.md` (§3.1 e §4.3), `components.md` e `unit-of-work.md` já tinham
sido emendados no Functional Design. **O código antigo** (`Ambiente/`, `model/`, `cli.py`,
`tui.py`) não foi tocado.

---

## 3. Decisões tomadas durante a execução

O que o plano não fixava, ou onde a execução divergiu dele.

| # | Decisão | Motivo |
|---|---|---|
| 1 | **Quarto auxiliar, `_gravar`**, além dos três que o plano nomeava (`_abrir`, `_recarregar`, `_mutar`) | `_mutar` e `anotar_memoria` precisam da mesma reação a falha: recarregar (RN-A-09), anotar a falha da recarga (`R-CG4-1`), fechar no cancelamento (`R-CG4-5`). Num lugar só, como o FD pedia, em vez de duas cópias. `ConflitoDeVersao` passa direto, porque quem o trata é `_mutar` |
| 2 | A nota de `R-CG4-1` traz **só o tipo** do erro da recarga | Mesmo critério do `WARNING` de RN-A-18: a mensagem de um erro de porta pode carregar detalhe do armazenamento, e a nota vai junto com o erro até a tela |
| 3 | Mensagens dos erros novos levam o **id** que faltou e, em `AgenteDesconhecido`, a lista de nomes aceitos | O orquestrador (via U5) consegue corrigir o pedido sem adivinhar |
| 4 | `PBT-U4-01` gera também `criar_ambiente` e, portanto, sequências com vários ambientes | O plano dizia "as 10 operações"; com um ambiente só, `criar_ambiente` ficaria de fora da propriedade de estado |
| 5 | `test_integracao.py` ganhou um terceiro teste: **conflito entre duas conexões reais** ao mesmo arquivo | É o "outro processo" de RN-A-10 com o bloqueio otimista do SQLite de verdade, e não o do dublê. Cabe no escopo do passo 11 (adaptadores reais) |
| 6 | **`event()` do Hypothesis** nas propriedades | É o que deixa ver, com `--hypothesis-show-statistics`, se cada ramo foi exercitado (§4). Fica no código para a próxima pessoa poder medir de novo |
| 7 | Os geradores foram **reescritos depois de medidos** (§4) | As 6 propriedades passaram na primeira execução, e três delas não testavam o que prometiam |

---

## 4. Os geradores, medidos e endurecidos

As seis propriedades passaram na primeira execução. Isso não prova nada sozinho, então medi o que
cada uma exercitava. Três estavam fracas:

| Propriedade | Primeira versão | Causa | Correção | Depois |
|---|---|---|---|---|
| **`PBT-U4-02`** conflito | **0 de 40** exemplos com conflito | metade dos passos era `carregar`; e cada serviço só abria o ambiente no próprio primeiro passo, já atualizado | os dois "processos" abrem o ambiente antes de qualquer escrita; `carregar` com peso 1 em 7 | **~30%** dos exemplos com conflito |
| **`PBT-U4-05`** falha | a falha disparava em **~22%** dos exemplos | `na_chamada` até 25, com sequências que fazem poucas chamadas | teto 8 | **~80%** disparam, antes e depois |
| **`PBT-U4-03`** esquema | `DescricaoObrigatoria` **nunca** alcançada; em `PBT-U4-04`, exemplos **abortados** pelo filtro de descrição de U3 | título hostil em quase todo esquema; até 9 descrições filtradas por esquema | três famílias com peso (válido / descrição vazia / título hostil); descrição **construída** para nunca normalizar a vazio, sem filtro | os 4 ramos aparecem (aceito, aceito vazio, `TituloInvalido`, `DescricaoObrigatoria`); nenhum aborto |

Na `PBT-U4-01`, `criar_chat` nunca dava certo: boa parte das sequências começava num ambiente sem
tarefa. `ambientes_de_partida` garante pelo menos uma tarefa com uma etapa, acrescentadas pela API
pública. Depois disso, as 10 operações aparecem com sucesso e com erro nas estatísticas.

### O teste dos testes: 16 mutações

Cada defeito foi injetado no código, um de cada vez, e restaurado em seguida (script fora do
repositório). Todos derrubaram pelo menos um teste:

| # | Defeito injetado | Primeiro teste que caiu |
|---|---|---|
| M01 | não recarregar depois de falha de gravação | `test_rn_a_09_falha_na_gravacao_deixa_a_memoria_igual_ao_disco` |
| M02 | sem nova tentativa no conflito | `test_rn_a_10_conflito_entre_duas_conexoes_reais_ao_mesmo_banco` |
| M03 | banco antes da wiki ao criar | `test_pbt_u4_03_a_wiki_nasce_igual_ao_esquema` |
| M04 | recarga troca o objeto em vez de atualizá-lo (G2) | `test_rn_a_10_conflito_entre_duas_conexoes_reais_ao_mesmo_banco` |
| M05 | sem trava | `test_rn_a_06_mesmo_ambiente_uma_operacao_por_vez` |
| M06 | wiki antes do banco ao apagar | `test_pbt_u4_05_falha_nao_deixa_rastro` |
| M07 | falha da wiki ao apagar propaga (G1) | `test_rn_a_18_falha_ao_apagar_a_wiki_vira_warning_e_nao_erro` |
| M08 | `anotar_memoria` também grava o documento | `test_pbt_u4_02_conflito_nao_perde_mudanca` |
| M09 | `_abrir` não guarda o aberto | `test_us_05_o_ambiente_sobrevive_a_fechar_e_reabrir` |
| M10 | `criar_chat` aceita qualquer nome | `test_pbt_u4_02_conflito_nao_perde_mudanca` |
| M11 | concluir alterna em vez de concluir | `test_pbt_u4_01_memoria_igual_ao_disco_e_ao_modelo` |
| M12 | semente nasce com conteúdo inventado | `test_pbt_u4_03_a_wiki_nasce_igual_ao_esquema` |
| M13 | falha da recarga substitui o erro da gravação | `test_r_cg4_1_recarga_que_falha_vira_nota_e_fecha_o_ambiente` |
| M14 | cancelamento não fecha o ambiente | `test_r_cg4_5_cancelamento_no_meio_da_gravacao_fecha_o_ambiente` |
| M15 | `apagar` segue link (`os.walk` com `followlinks`) | `test_apagar_nao_segue_link_para_fora_da_wiki` (junction, nesta máquina) |
| M16 | `apagar` sem a guarda do índice | `test_r_cg4_2_pasta_sem_indice_nao_e_apagada[dados:wikis]` |

Os contraexemplos que o Hypothesis encontrou durante as mutações ficaram em `.hypothesis/` (pasta
ignorada pelo git). Contra o código correto eles passam, e continuam sendo repetidos como casos de
regressão.

---

## 5. Contrato publicado para as próximas unidades

```
ServicoDeAmbiente(persistencia, wiki, orquestrador, agentes_de_chat)

criar_ambiente(nome, esquema)                                 -> Ambiente
carregar_ambiente(id_ambiente)                                -> Ambiente
listar_ambientes()                                            -> list[ResumoAmbiente]
apagar_ambiente(id_ambiente)                                  -> None
criar_frente(id_ambiente, nome)                               -> Frente
criar_tarefa(id_ambiente, id_frente, nome)                    -> Tarefa
criar_chat(id_ambiente, id_tarefa, nome_agente, nome="")      -> Chat
criar_etapa(id_ambiente, id_tarefa, descricao, executor)      -> Etapa
concluir_etapa(id_ambiente, id_etapa)                         -> Etapa
anotar_memoria(id_ambiente, id_tarefa, chave, valor, autor)   -> Anotacao
```

Erros que podem sair: os 5 desta unidade, `AmbienteInexistente` e `ConflitoDeVersao` (e os demais
`ErroDePersistencia`), `ErroDeWiki` e subclasses, e `NomeInvalido` / `OrquestradorDuplicado` /
`AgenteInvalido` do domínio. Nada mais: o modelo de `PBT-U4-01` trata qualquer outra exceção como
defeito.

---

## 6. Rastreio

| Especificação | Onde se verifica |
|---|---|
| **US-04** anotar sem erro, sem perder a anterior | `test_rn_a_25_anotar_nao_grava_o_documento_e_acumula`, `PBT-U4-01`, integração |
| **US-05** — **fecha aqui** | `PBT-U4-01` (memória ≡ disco depois de cada passo) e `test_us_05_o_ambiente_sobrevive_a_fechar_e_reabrir` (SQLite real, programa fechado e reaberto) |
| **US-08 / US-09** | `test_us_08_us_09_criar_ambiente_materializa_a_wiki_do_esquema`, `test_us_08_esquema_vazio_nasce_so_com_o_indice`, `PBT-U4-03` |
| **US-15 / US-16** | `test_us_15_us_16_frente_e_tarefa_com_o_orquestrador_do_construtor`, `PBT-U4-01` |
| **US-17** (gravação) / **US-19** | `test_us_17_etapas_anexam_ao_fim_e_us_19_concluir`, `PBT-U4-01`, `PBT-U4-06` |
| RN-A-01 | `test_fronteira.py` (3) |
| RN-A-02, RN-A-08 | `test_rn_a_02_*` (2), `test_rn_a_08_*` (2), `PBT-U4-01` (erro previsto pelo modelo) |
| RN-A-03..07 | `test_rn_a_03_*`, `test_rn_a_04_*`, `test_rn_a_05_*` (8 operações), `test_rn_a_06_*` (2), `test_rn_a_07_*` |
| RN-A-09..12 | `test_rn_a_09_*` (3), `test_rn_a_10_*` (+ integração), `test_rn_a_11_*`, `test_rn_a_12_*` (2), `PBT-U4-02`, `PBT-U4-05` |
| RN-A-13..20 | `test_rn_a_13_*`, `test_rn_a_14_*`, `test_rn_a_16_*` (3), `test_rn_a_17_*` (2), `test_rn_a_18_*`, `test_rn_a_19_*`, `test_rn_a_20_*`, `PBT-U4-03`, `PBT-U4-04` |
| RN-A-21..24 | `test_us_15_us_16_*`, `test_rn_a_22_*` (2), `test_rn_a_23_*`, `test_rn_a_24_*`, `PBT-U4-06` |
| RN-A-25..26 | `test_rn_a_25_*`; RN-A-26 é a razão de `PBT-U4-02` não comparar memória (`R-CG4-3`) |
| `R-CG4-1..5` | `test_r_cg4_1_*`, `test_r_cg4_2_*` (2), `PBT-U4-02`, `PBT-U4-06` + `PBT-U3-08`, `test_r_cg4_5_*` |
| Critérios de pronto 1–6 | 1 → `test_us_08_us_09_*`, `PBT-U4-03` · 2 → RN-A-02/08 · 3 → `test_fronteira.py` · 4 → `test_criterio_4_*`, `PBT-U4-04` · 5 → RN-A-10/11, `PBT-U4-02` · 6 → `test_rn_a_17_*`, `test_criterio_1_e_6_*` |

---

## 7. Conformidade das extensões

| Extensão / regra | Estado | Rationale |
|---|:--:|---|
| `security-baseline` SECURITY-05 (confinamento) | ✅ | `apagar` usa `resolver_raiz`, não segue link (verificado nesta máquina com junction, e por mutação) e só remove raiz com índice (`R-CG4-2`, verificado por mutação) |
| SECURITY-10 (dependências) | ✅ | Zero dependência nova; `pyproject.toml` e `uv.lock` sem diff |
| SECURITY-13 (integridade) | ✅ | Memória ≡ disco depois de falha e de conflito (`PBT-U4-01/02/05`); nunca ambiente sem wiki (`PBT-U4-05`) |
| SECURITY-15 (falha segura) | ✅ | Erros tipados; o único não propagado é o de RN-A-18, com `WARNING` sem caminho; a falha da recarga vai como nota, não é descartada |
| Demais regras | N/A | Sem rede, servidor, IAM ou HTTP |
| PBT-02 (round-trip) | ✅ | `PBT-U4-01`: memória → disco → serviço novo, depois de cada passo |
| PBT-03 (invariantes) | ✅ | `PBT-U4-03`, `04`, `05` |
| PBT-04 (idempotência) | ✅ | `PBT-U4-06` (`concluir_etapa`) e `PBT-U3-08` (`apagar`) |
| PBT-05 (oráculo) | ✅ | `ModeloDeAmbientes` em `PBT-U4-01/02/04`; validação de U3 refeita como oráculo em `PBT-U4-03` |
| PBT-06 (com estado) | ✅ | Sequências de 0 a 15 comandos, verificação depois de cada um, modelo simplificado |
| PBT-07 (geradores) | ✅ | Centralizados em `tests/ambiente/estrategias.py`, reaproveitando U2 e U3; distribuição medida e corrigida (§4) |
| PBT-08 (encolhimento e semente) | ✅ | Padrão do Hypothesis, nada desligado. A parte de CI é de Build and Test |
| PBT-10 (complementar) | ✅ | Exemplos e propriedades em arquivos separados; todo caminho crítico tem os dois |
| `resiliency-baseline` | N/A | Desativada em Requirements Analysis |

---

## 8. Para as próximas unidades

- **U5 (ações)**: é quem traduz as exceções em `Resultado` (Q3=A). A lista fechada está na §5.
  `ConflitoDeVersao` só chega depois de 3 tentativas, com a memória já igual ao disco: repetir o
  pedido é seguro. `AgenteDesconhecido` traz na mensagem os nomes aceitos.
- **U8 (bibliotecário)**: o chat do bibliotecário nasce por `criar_chat(..., "bibliotecario")`.
  O nome precisa bater **exatamente** com o `Agente` passado em `agentes_de_chat`.
- **U9 (composition root)**: monta `ServicoDeAmbiente(repo, wiki, orquestrador, (bibliotecario,))`,
  um serviço por processo. É quem decide o destino do logger `fishingrod.ambiente`, que hoje só tem
  `NullHandler`. A tela de início precisa garantir uma frente, porque o ambiente nasce sem
  (RN-A-15). Também é dela confirmar antes de `apagar_ambiente` (RN-P-23).
- **Comportamento que a tela precisa conhecer**: referências a objetos **de dentro** do ambiente
  (uma `Frente`, uma `Tarefa`) podem ficar velhas depois de uma recarga por conflito. O `Ambiente`
  continua o mesmo objeto (G2); o resto se busca de novo pelo id (RN-A-03).
