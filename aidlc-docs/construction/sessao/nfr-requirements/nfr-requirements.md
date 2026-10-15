# NFR Requirements — U6 `sessao`

**Fase:** CONSTRUCTION · **Unidade:** `U6 sessao` · **Portão 2 de 4** · **Data:** 2026-10-06
**Decisões que originam este documento:** Q1=A, Q2=A, Q3=A, Q4=A (com A1 e A2), Q5=A (mantendo as
varreduras estáticas), Q6=A, Q7=A, Q8=A, Q9=A, Q10=A, Q11=A, Q12=A
(`construction/plans/sessao-nfr-requirements-plan.md`)

Identificadores `NFR-S-nn` são estáveis e entram no nome dos testes, como as `RN-S-nn`.

---

## 1. Cadeia de suprimentos (SECURITY-10)

| # | Requisito | Como se verifica |
|---|---|---|
| **NFR-S-01** | `claude-agent-sdk` entra em **`dependencies`** como dependência obrigatória, e é a **única** dependência direta de runtime do projeto | Inspeção do `pyproject.toml`. A fronteira do núcleo é garantida por NFR-S-07, não pelo empacotamento (Q1=A) |
| **NFR-S-02** | Versão **exata `==0.2.143`**, travada no `uv.lock` com o hash de cada pacote. O corte `exclude-newer = 2026-08-25` de ESC-15 **não muda** | Medido em 2026-10-06: sob o corte, só com pacotes prontos para Windows, a 0.2.143 resolve **32 pacotes** sem compilar nada (Q2=A) |
| **NFR-S-03** | A sessão usa **o CLI embutido no pacote do SDK**, passado ao SDK pelo caminho, explicitamente. Se o CLI embutido não existir, a falha é `PROVEDOR_AUSENTE`. **Nunca** cai no `claude` do `PATH` | O SDK, sem caminho explícito, procura o embutido e depois o `PATH` sem avisar (medido no código da 0.2.143). Teste com o adaptador real e uma fábrica de cliente que aponta para um caminho inexistente (Q3=A) |
| **NFR-S-04** | **`uv audit`** roda no Code Generation de U6, o resultado fica no resumo do código, e o comando entra nas instruções de Build and Test. **A1**: vulnerabilidade conhecida em pacote que U6 usa **bloqueia o portão** de U6 até a troca de versão. **A2**: vulnerabilidade só em pacote que U6 não usa vira **risco aceito**, com o motivo registrado | Saída do comando no `code-summary.md` (Q4=A) |
| **NFR-S-05** | Os transitivos do **lado servidor do MCP** (`starlette`, `uvicorn`, `sse-starlette`, `python-multipart`, `pyjwt`, entre outros) ficam instalados sem uso | **Risco aceito**: não podem sair sem bifurcar o SDK. NFR-S-04 os cobre. "Sem dependência não usada" vale para as diretas |
| **NFR-S-06** | SBOM e integridade de CI: **N/A** nesta iteração | Sem implantação em produção nem pipeline de CI; o `uv.lock` é o inventário completo. Reavaliar quando houver distribuição (RNF-07) |

## 2. Fronteira do núcleo e testes

| # | Requisito | Como se verifica |
|---|---|---|
| **NFR-S-07** | **TD-02**: importar **todos** os módulos de `dominio/` e `aplicacao/` funciona com o SDK indisponível | Teste na suíte padrão que sobe um **Python novo** com um bloqueador de import: qualquer `import claude_agent_sdk` levanta `ImportError`, como faria com o pacote desinstalado. As varreduras estáticas de import das `test_fronteira.py` existentes **continuam** (Q5=A). A estática aponta a linha; o subprocesso prova que o pacote inteiro carrega |
| **NFR-S-08** | Os testes com o **SDK real** levam o marcador **`sdk_real`**, registrado no `pyproject.toml`, e ficam **fora** de `uv run pytest`. Rodam com `uv run pytest -m sdk_real` | A suíte padrão não muda de contagem por causa deles (nem `skipped`). No Code Generation, eles rodam uma vez, e o resultado de cada medição (§6) vai para o resumo do código (Q6=A) |
| **NFR-S-09** | **Critério 1 de U6**: o mesmo teste de contrato roda no adaptador falso (suíte padrão) e no real (`sdk_real`) | Um único módulo de contrato parametrizado pelo adaptador |
| **NFR-S-10** | Testes de propriedade com **`hypothesis`** (PBT-09), semente impressa na falha e encolhimento ligado, como nas unidades anteriores | `PBT-U6-01..12` rodam só com o adaptador falso e o cliente simulado; nenhuma propriedade chama o provedor |

## 3. Tempo

| # | Requisito | Como se verifica |
|---|---|---|
| **NFR-S-11** | Subir o CLI espera no máximo **60 s**. Passou disso: `FalhaDoTurno(INDISPONIVEL)` sem entrega, e a conexão é descartada (RN-S-33, RN-S-34) | É o padrão do SDK, `max(CLAUDE_CODE_STREAM_CLOSE_TIMEOUT, 60 s)`, conferido no código da 0.2.143. O adaptador não muda essa variável. Teste com cliente simulado que nunca termina de conectar e relógio do teste (Q7=A) |
| **NFR-S-12** | **Nenhum prazo** de silêncio nem de duração de turno. A ferramenta que espera a sua confirmação espera o tempo que for. A defesa contra um turno travado é o ESC (RN-S-35), como na Q12=B do FD | Teste de exemplo: um turno simulado parado por tempo longo no relógio do teste não termina sozinho (Q8=A) |
| **NFR-S-13** | Uma sessão só termina por **`fechar`** (ou por `encerrar()` do adaptador) | Quem chama `fechar` é U7/U9, nos três momentos que você listou: **sair do ambiente, fechar o chat, fechar o software**. Nada fecha uma sessão por inatividade (§7) |

> **/!\ Emenda 2026-10-13 — NFR Design de U6** (Q3=A, `R-ND6-8`). NFR-S-11: o prazo de 60 s passa a
> ser **também do adaptador**, em volta da subida inteira (processo, checagem de versão e
> inicialização), porque o prazo do próprio SDK levanta uma `Exception` genérica (A7). Qualquer falha
> nessa fase é `INDISPONIVEL`, menos CLI ausente e falta de login reconhecida. O adaptador continua
> sem mexer em `CLAUDE_CODE_STREAM_CLOSE_TIMEOUT`. ~~Teste com cliente simulado que nunca termina de
> conectar e relógio do teste~~ **Teste com cliente simulado que nunca termina de conectar e prazo
> curto passado no construtor** (`DP-S-08`).

## 4. Capacidade e desempenho

| # | Requisito | Como se verifica |
|---|---|---|
| **NFR-S-14** | **Sem teto** de sessões conectadas. Turnos de **sessões diferentes correm em paralelo** (RN-S-40, critério 3). Dentro de uma sessão, um turno por vez (RN-S-26), e a fila de mensagens é de U7 | Medição 12 (§6) registra a memória de um processo do CLI (Q9=A) |
| **NFR-S-15** | **Sem alvo de desempenho com portão.** O teste `sdk_real` registra o **tempo para conectar** e o **tempo até o primeiro `PedacoDeTexto`** como linha de base | Medição 13 (§6). Números no resumo do código, sem limite que reprove (Q10=A) |

## 5. Confiabilidade e observabilidade

| # | Requisito | Como se verifica |
|---|---|---|
| **NFR-S-16** | **Queda dura do FishingRod** (processo morto pelo sistema): o Code Generation mede se o CLI termina sozinho ao perder a entrada. Se terminar, o risco some. Se não, vira **risco aceito** com o sintoma registrado: processo `claude` órfão até reiniciar a máquina | Medição 14 (§6). Nenhum código específico de plataforma nesta iteração (Q11=A) |
| **NFR-S-17** | Logger **`fishingrod.sessao`** com `NullHandler`, como em U2. Níveis fixos: **INFO** abrir, conectar, fechar, encerrar; **WARNING** ferramenta negada, trechos divergentes, `dado` desconhecido; **ERROR** `FALHA_INESPERADA` e exceção dentro de ferramenta, com a pilha; **DEBUG** a saída de erro do CLI. O conteúdo segue RN-S-54. O destino é de U9 | Teste com `caplog` por nível; teste de que nenhum registro contém o texto da mensagem nem os argumentos (Q12=A) |
| **NFR-S-18** | Nenhuma nova tentativa automática além da reconexão na próxima mensagem (RN-S-34) | resiliency-baseline desabilitada (RNF-08) |

> **/!\ Emenda 2026-10-13 — NFR Design de U6** (Q3=A; `nfr-design-patterns.md` §4). NFR-S-17
> ganha casos em **WARNING**: a falha ao subir o CLI, **com a pilha**; as falhas do turno vindas do
> provedor (`PROVEDOR_AUSENTE`, `NAO_AUTENTICADO`, `LIMITE_DE_USO`, `INDISPONIVEL`), só com o motivo;
> e `TURNO_EM_ANDAMENTO`, que é defeito de quem chama. `MENSAGEM_INVALIDA` e `SESSAO_FECHADA` ficam em
> **INFO**. **ERROR** passa a cobrir também o sinal `invalid_request` e a mensagem de resultado com
> erro sem sinal reconhecido (N6), sem pilha, porque não houve exceção.

## 6. Medições com o SDK real (marcador `sdk_real`)

As 10 medições do FD (`business-logic-model.md` §8) continuam, agora com a versão e o CLI destas
decisões. Este estágio acrescenta quatro:

| # | O que medir | Se der errado |
|---|---|---|
| 1–10 | As do FD, sem mudança. A **2** (tempo-limite da ferramenta que espera confirmação) ainda pode reabrir U5. A **10** é o critério 3 com a `0.2.143` | Como no FD |
| **11** | O **CLI embutido** é o que roda (não o do `PATH`) e enxerga o seu login da assinatura | Se não enxergar, Q3 é reaberta antes de U6 fechar |
| **12** | Memória de **um processo do CLI** conectado e ocioso | Só registro. É o número que justificaria um teto no futuro (Q9) |
| **13** | Tempo para conectar e tempo até o primeiro `PedacoDeTexto` | Só registro (Q10) |
| **14** | O CLI termina sozinho quando o processo Python que o subiu é morto | Não termina: risco aceito com o sintoma (Q11) |

## 7. O que este estágio passa adiante

- **U7 `conversa` e U9 `interface`**: são eles que chamam `fechar`. Os gatilhos são **sair do
  ambiente, fechar o chat e fechar o software** (comentário da Q8), e no fim do programa
  `encerrar()` (G7). **Nenhum** fechamento por inatividade, porque a sessão nova nasce sem o histórico
  (Q5=A do FD), e fechar por tempo faria você voltar a um chat que esqueceu a conversa.
- **U9 `interface`**: o comentário da Q9 supôs que o programa só deixaria mandar uma mensagem por vez,
  mesmo com várias sessões abertas. **U6 não impõe isso**: cada sessão tem o próprio turno, e turnos
  de chats diferentes correm ao mesmo tempo (NFR-S-14). O que pode limitar é a tela: se ela mostra um
  chat por vez, você manda num, troca de chat e manda no outro enquanto o primeiro ainda responde.
  Se a tela vai permitir isso nesta iteração é decisão de U9, não restrição desta unidade.
- **Build and Test**: `uv audit` (NFR-S-04) e `uv run pytest -m sdk_real` (NFR-S-08) entram nas
  instruções.

## 8. Conformidade das extensões

| Regra | Estado | Onde |
|---|---|---|
| SECURITY-10 | ✅ Conforme | Travamento exato com hash (NFR-S-02), fonte oficial, varredura com política de bloqueio (NFR-S-04), transitivos sem uso declarados (NFR-S-05), SBOM e CI N/A com motivo (NFR-S-06) |
| SECURITY-03 | ✅ Conforme | NFR-S-17 mantém RN-S-54 e acrescenta o teste de que nada de mensagem ou argumento chega ao log |
| SECURITY-09 | ✅ Conforme | NFR-S-03: o CLI que roda é o travado, nunca um trocado em silêncio |
| SECURITY-11 | ✅ Conforme | Riscos aceitos com nome: NFR-S-05, NFR-S-12 (sem prazo, defesa pelo ESC), NFR-S-16 (queda dura) |
| SECURITY-12 | ✅ Conforme | Sem mudança: RN-S-52 continua, e a lista de variáveis é conferida contra a `0.2.143` |
| SECURITY-15 | ✅ Conforme | NFR-S-11: subir o CLI tem prazo e termina em falha tipada, nunca em espera eterna sem dono |
| SECURITY-05, 08, 13 | ✅ Conforme | Decididas no FD; nada aqui as altera |
| SECURITY-01, 02, 04, 06, 07, 14 | N/A | Sem armazenamento próprio, rede exposta, servidor, IAM ou infraestrutura de alerta |
| PBT-09 | ✅ Conforme | `hypothesis` (NFR-S-10; TS-S-08) |
| PBT-08 | ✅ Conforme | Semente impressa na falha e encolhimento ligado; propriedades nunca chamam o provedor, então não há motivo para desligar o encolhimento |
| PBT-01..07, 10 | N/A neste estágio | Decididas no FD (`PBT-U6-01..12`) e executadas no Code Generation |
