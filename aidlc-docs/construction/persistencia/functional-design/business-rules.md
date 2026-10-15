# Business Rules — U2 `persistencia`

**Fase:** CONSTRUCTION · **Unidade:** `U2 persistencia` · **Data:** 2026-08-26

Identificadores `RN-P-nn` são **estáveis** e entram no nome dos testes (`test_rn_p_03_*`), como em
U1: quando um teste falha, o nome diz qual regra quebrou.

---

## Integridade e round-trip

| # | Regra | Origem |
|---|---|---|
| **RN-P-01** | `carregar_ambiente(salvar_ambiente(a))` devolve um ambiente **igual** a `a` em estrutura, identidades, nomes, agentes, etapas e memória. Nada de silenciosamente perdido. | US-05, CS-01, TD-04 |
| **RN-P-02** | Todo documento gravado carrega `versao_esquema`. Nesta iteração vale sempre `1`. Carregar um documento com versão **maior** que a suportada levanta erro explícito em vez de interpretar campos que não entende. **[Emenda 2026-08-27 / NFR Design, Q9=C]** esta coluna versiona **apenas o formato do documento JSON**; o esquema **físico** (tabelas, índices, chaves) passa a ser versionado por `PRAGMA user_version`, verificado na abertura. As duas versões são independentes e hoje valem `1`. | Q3=A · Q9=C |
| **RN-P-03** | Toda operação que muda estado acontece em **uma** transação. Falha no meio não deixa estado parcial: ou tudo, ou nada. | RNF-05, critério 5 de U2 |
| **RN-P-04** | `carregar_ambiente(id)` de identidade inexistente devolve `None`. **Não levanta.** Ausência não é erro. | contrato §4.1 |
| **RN-P-15** | O banco não guarda conteúdo nem índice de wiki. A única referência é `raiz_wiki` no documento, e é localizador, não caminho absoluto. | **RNF-12**, RN-11 (U1) |
| **RN-P-16** | Nenhuma assinatura de `PortaPersistencia` menciona `sqlite3`, `cursor`, `conexão`, SQL ou nome de tabela. Se mencionar, a abstração é decorativa. | **D-ARQ-04** |

## Concorrência (Q4=C)

| # | Regra | Origem |
|---|---|---|
| **RN-P-05** | `salvar_ambiente(a)` só grava se a `versao` em disco for **igual** a `a.versao`. Se for diferente, levanta `ConflitoDeVersao` e **não grava nada**. | Q4=C, RNF-05 |
| **RN-P-06** | Gravação bem-sucedida incrementa a versão em disco e no objeto: a instância em memória fica pronta para a próxima gravação sem recarregar. | Q4=C |
| **RN-P-07** | `anotar` **nunca** levanta `ConflitoDeVersao` e **nunca** altera `Ambiente.versao`. Duas anotações concorrentes na mesma tarefa sobrevivem ambas. | Q2=B, RN-09 (U1), US-04 |

> RN-P-07 é a regra pela qual a memória saiu do documento. Se um dia alguém a mover de volta para o
> JSON, esta regra passa a ser impossível de cumprir — é o alarme embutido nessa decisão.

## Memória

| # | Regra | Origem |
|---|---|---|
| **RN-P-08** | `salvar_ambiente` **não escreve nem apaga anotação alguma.** Memória entra pela porta de anotar e sai pela carga. | Q2=B |
| **RN-P-09** | A tabela `anotacao` é append-only: sem `UPDATE`, sem `DELETE` fora da cascata de RN-P-20. | RN-09 (U1) — anotar nunca substitui |
| **RN-P-10** | Na carga, as anotações de uma tarefa voltam **na ordem em que foram escritas**, agrupadas pela mesma chave, e `Memoria.versao` recebe o total de anotações carregadas. | Q2a=A, §5.2 de `domain-entities.md` |
| **RN-P-11** | `carregar_ambiente` traz **toda** a memória de **todas** as tarefas. Não existe memória parcial: um agente que lê o blackboard leu o blackboard inteiro. | Q2a=A |

## Transcrição

| # | Regra | Origem |
|---|---|---|
| **RN-P-12** | A ordem cronológica da transcrição é a ordem do `id` (UUIDv7). Não existe coluna de sequência. | ESC-14, PBT-U1-01 |
| **RN-P-13** | `listar_mensagens(id_chat, limite)` devolve as **`limite` mais recentes**, em ordem **crescente** (a mais antiga primeiro). Com menos de `limite` mensagens, devolve todas. | Q5=A, US-06 |
| **RN-P-14** | `listar_mensagens(..., antes_de=id)` devolve as `limite` imediatamente **anteriores** a `id`. Paginar do fim para o começo cobre a transcrição inteira, sem repetir e sem pular. | Q5=A |
| **RN-P-17** | A marca `em_andamento` é preservada na leitura. **Nada** limpa mensagem órfã: nem na abertura do chat, nem na carga. O texto parcial é preservado como está. | Q6=A, critério 2 de U7 |
| **RN-P-18** | `atualizar_mensagem` altera **apenas** `texto` e `em_andamento` da linha indicada. Não muda `id`, `id_chat`, `papel` nem `criada_em` — o que preserva RN-P-12 durante o streaming. | contrato §4.1 |
| **RN-P-19** | Um uso de ferramenta pertence a uma mensagem; uma mensagem pode ter vários. ~~Voltam junto com a mensagem~~ Os **argumentos usados** voltam junto com a mensagem, na ordem em que foram registrados. **[emenda 2026-08-26 / NFR Q6]** O **resultado** da ferramenta não é persistido nesta iteração. | Q7=A, NFR Q6 |

> **RN-P-27 [Emenda 2026-08-27 / Code Generation]** `anotar` e `inserir_mensagem` **exigem que o
> ambiente exista** e levantam `AmbienteInexistente` quando não existe. Anotação e mensagem pendem
> de um ambiente: é o que a chave estrangeira de `RN-P-20` já dizia, e o que faltava ser dito no
> vocabulário da porta. Descoberta por `PBT-U2-04`, não por revisão.
>
> `registrar_uso_ferramenta` ganhou o mesmo tratamento com `MensagemInexistente`, pela mesma razão.

## Ciclo de vida do ambiente (Q8=B)

| # | Regra | Origem |
|---|---|---|
| **RN-P-20** | `apagar_ambiente(id)` remove a linha do ambiente **e** todas as anotações, mensagens e usos de ferramenta dele. Não sobra linha órfã em tabela alguma. | Q8=B |
| **RN-P-21** | `apagar_ambiente` **não toca no disco**: não apaga o diretório da wiki. Isso é do serviço de U4. | **RNF-12**, Parte 3 da clarificação |
| **RN-P-22** | `apagar_ambiente` de identidade inexistente é operação vazia bem-sucedida. Idempotente. | Parte 3 da clarificação |
| **RN-P-23** | `apagar_ambiente` apaga sem perguntar. O aviso e a confirmação são de **U9** — persistência não faz diálogo. | Parte 3 da clarificação |
| **RN-P-24** | `listar_ambientes()` devolve `ResumoAmbiente` de todos os ambientes, do mais recentemente atualizado para o mais antigo, **sem** desserializar documento algum. | Q10=B, US-05 |

## Dublês (Q9=A)

| # | Regra | Origem |
|---|---|---|
| **RN-P-25** | `RepositorioEmMemoria` e `RepositorioSQLite` passam pelo **mesmo** teste de contrato, parametrizado. Toda regra `RN-P-*` acima vale para os dois. | Q9=A, critério de U6 (mata TD-01) |
| **RN-P-26** | O falso é falso só no armazenamento. Ele **também** levanta `ConflitoDeVersao`, **também** devolve `None` para id ausente e **também** preserva `em_andamento`. Dublê que só faz o caminho feliz é dublê que faz o teste mentir. | Q9=A |

---

## Duas regras declaradas que **não** vieram de pergunta

- **RN-P-24 (`listar_ambientes`)** acrescenta um método ao contrato herdado de `component-methods.md`
  §4.1. Motivo: Q10=B permite vários ambientes na mesma instalação, e US-05 promete reabrir — mas
  para reabrir é preciso **encontrar**, e `carregar_ambiente(id)` exige já saber o id. Sem este
  método, a tela inicial de U9 não tem o que listar. É emenda ao contrato, registrada como tal.
- **RN-P-20 a RN-P-23 (`apagar_ambiente`)** acrescentam o segundo método, por Q8=B.

Ambas estão emendadas em `component-methods.md` §4.1 com o texto anterior riscado, nunca apagado.
