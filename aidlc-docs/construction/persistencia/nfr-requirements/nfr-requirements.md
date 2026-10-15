# NFR Requirements — U2 `persistencia`

**Fase:** CONSTRUCTION · **Unidade:** `U2 persistencia` · **Portão 2 de 4** · **Data:** 2026-08-26
**Decisões que originam este documento:** Q1=A (via Q13=B), Q2=B, Q3=A, Q4=B, Q5=A, Q6=fora,
Q7=A, Q8=A, Q9=A, Q10=A, Q11=B, Q12=A, **Q13=B**

Identificadores `NFR-P-nn` são estáveis e entram no nome dos testes, como as `RN-P-nn`.

---

## 1. Desempenho

| # | Requisito | Como se verifica |
|---|---|---|
| **NFR-P-01** | Abrir um ambiente com **5.000 anotações** distribuídas em tarefas leva **≤ 1 s** | Teste de fumaça com dado gerado, marcado como lento (pulável em CI lenta). **Não é portão de merge** — é o sensor que avisa quando `Q2a=B` (carga sob demanda) deixa de ser hipótese |
| **NFR-P-02** | `listar_ambientes()` tem custo **independente** do tamanho dos ambientes | Lê `id`, `nome`, `atualizado_em`; nunca desserializa `documento` (RN-P-24). Verificável por inspeção da consulta |
| **NFR-P-03** | Durante o streaming, o disco recebe **no máximo ~2 escritas por segundo por chat** | Throttle de **500 ms** entre `atualizar_mensagem`, mais **uma escrita final obrigatória** no fim do turno (Q4=B). A final não é opcional: é ela que garante que o texto persistido é exato |
| **NFR-P-04** | `listar_mensagens(id_chat, limite)` tem custo função de `limite`, não do total do chat | Índice `idx_mensagem_chat(id_chat, id)`; a consulta ordena por `id` e limita |

**O que NFR-P-03 custa, dito por extenso:** numa queda de energia perde-se até 500 ms do turno em
andamento — cerca de meia frase. Isso está aceito, não desconhecido.

> **[Emenda 2026-08-27 / NFR Design de U2, Q5=A]** `NFR-P-03` continua sendo um alvo desta unidade,
> mas o **mecanismo** que o cumpre **não mora aqui**: o throttle é cadência de quem chama e passou
> para **U7 `conversa`** (critério 6 de `unit-of-work.md` §3). A porta de persistência escreve
> **toda** chamada que recebe — se ela descartasse escritas pelo relógio, `atualizar_mensagem`
> deixaria de ser verificável e `PBT-U2-08` precisaria de um relógio dentro do teste de contrato.

## 2. Durabilidade e integridade

| # | Requisito | Como se verifica |
|---|---|---|
| **NFR-P-05** | `journal_mode = WAL` e `synchronous = NORMAL` | Leitura não bloqueia escrita, que é o que permite a TUI ler a transcrição enquanto o agente escreve. Crash do **processo** não perde commit confirmado; queda de **energia** pode perder os últimos |
| **NFR-P-06** | **`PRAGMA foreign_keys = ON`** ligado na abertura da conexão | **Condição de existência de RN-P-20.** Sem ele a cascata não age e `apagar_ambiente` deixa órfãos em silêncio. `PBT-U2-07` falha se o pragma for esquecido — é o teste que transforma esta dívida em algo que não pode ser esquecido de novo |
| **NFR-P-07** | Banco ilegível ou corrompido → **falha explícita na inicialização**, com o caminho do arquivo, e o app não inicia | Nunca renomear, nunca recriar, nunca reparar em silêncio (Q7=A). Entre travar visível e apagar invisível, `RNF-05` já escolheu |
| **NFR-P-08** | Uma operação = uma transação (RN-P-03), **garantida por construção** | Todo o SQL de uma operação vive numa única função síncrona executada por um único `asyncio.to_thread`. Não existe ponto de `await` no meio da transação, logo não existe onde duas corrotinas intercalem |

> **NFR-P-08 é o motivo de Q13=B.** Com um cliente assíncrono por instrução, cada instrução seria um
> ponto de `await` e o `Lock` seria a **única** coisa segurando RN-P-03. Aqui ele é a segunda.

## 3. Concorrência

| # | Requisito | Como se verifica |
|---|---|---|
| **NFR-P-09** | **Uma conexão viva por processo**, aberta com `check_same_thread=False`, serializada por um `asyncio.Lock` | Os PRAGMAs (NFR-P-05, NFR-P-06) são ligados **uma vez, na abertura**. Um método novo não tem preâmbulo a esquecer |
| **NFR-P-10** | `busy_timeout = 5000 ms` | Cobre a espera entre **processos** (NFR-P-11). É maior que qualquer operação nossa e menor que a paciência de quem está olhando a tela |
| **NFR-P-11** | Duas instâncias na mesma máquina, no mesmo banco, são **suportadas** (Q8=A) | Sem arquivo de trava. A proteção de correção é o bloqueio otimista de RN-P-05, não a exclusão mútua de processos |

**Consequência declarada de NFR-P-09:** o `Lock` serializa as *instruções*, não a janela de
leitura-e-escrita. Um agente que carrega na versão 7, gasta 30 s no modelo e salva, ainda encontra
`ConflitoDeVersao` — **dentro do mesmo processo**. O bloqueio otimista continua necessário.

## 4. Segurança (`security-baseline` ativa)

| # | Requisito | Regra da extensão |
|---|---|---|
| **NFR-P-12** | **Zero dependências de runtime.** `dependencies = []` continua verdadeiro depois desta unidade | SECURITY-10 (superfície de cadeia de suprimentos) |
| **NFR-P-13** | Todo valor entra em SQL por **parâmetro vinculado**; nenhuma consulta montada por concatenação ou f-string | Entrada não confiável em SQL. Verificável por inspeção em Code Generation |
| **NFR-P-14** | Dados em claro, com **permissão restrita ao usuário**: diretório criado com `0o700` e arquivo do banco com `0o600` em POSIX. No Windows, a raiz `%LOCALAPPDATA%` do usuário já é restrita | Q12=A. O modelo de ameaça é máquina pessoal, não servidor multiusuário |
| **NFR-P-15** | **Nenhum segredo persistido.** Nenhuma tabela guarda credencial; a chave do provedor é de U6 e vem do ambiente do processo | SECURITY-12 |
| **NFR-P-16** | Falha de persistência sobe como **exceção explícita**, nunca como valor de sucesso ou `None` ambíguo | SECURITY-15 (fail-safe). `None` só significa "não existe" em `carregar_ambiente` (RN-P-04) |

## 5. Observabilidade

| # | Requisito |
|---|---|
| **NFR-P-17** | Logger `logging.getLogger("fishingrod.persistencia")`, com `NullHandler` — a unidade **não configura destino**; quem configura é o composition root de U9 |
| **NFR-P-18** | Registra **apenas falha e conflito**. Nunca operação bem-sucedida: um log por `anotar` seria ruído em volume de blackboard |

**Por que NFR-P-18 existe:** um `ConflitoDeVersao` reabsorvido por U4 com recarga e repetição é
invisível por desenho. Se ele passar a acontecer o tempo todo, este log é a única forma de descobrir.

## 6. Manutenibilidade

| # | Requisito |
|---|---|
| **NFR-P-19** | Esquema criado na abertura com `CREATE TABLE IF NOT EXISTS` **idempotente** (Q9=A). Instalação nova e existente seguem o mesmo caminho |
| **NFR-P-20** | `versao_esquema` verificada na carga (RN-P-02): maior que a suportada levanta erro explícito |
| **NFR-P-21** | O perfil de Hypothesis para os testes desta unidade usa **`deadline=None`** | Sem isso, o *deadline* padrão de 200 ms transforma qualquer I/O de disco em falha intermitente, e um teste que falha por acaso ensina a ignorar teste |

## 7. Escalabilidade — o número e o gatilho

| Dado | Volume previsto | Efeito |
|---|--:|---|
| Anotação (~1 KB) | 5.000 | ~5 MB, na tabela `anotacao` — é o que cresce |
| Estrutura (frentes/tarefas/chats/etapas) | centenas de itens | ~100 KB no documento, reescrito inteiro sem dor |
| Mensagem | sem teto | tabela, paginada por cursor (RN-P-14) |

**Gatilho declarado:** `Q2a=A` (carregar toda a memória na abertura) vale enquanto **NFR-P-01**
passar. Quando ele falhar, `Q2a=B` (carga por tarefa, sob demanda) deixa de ser hipótese e vira
trabalho — sem migração de dados, porque a tabela já estará lá.

---

## 8. Conformidade das extensões

| Extensão | Estado | Onde incide |
|---|:--:|---|
| `security-baseline` | ✅ | NFR-P-12 a NFR-P-16 |
| `property-based-testing` (Full) | ✅ | As 8 propriedades `PBT-U2-*` do Functional Design; **NFR-P-06 é verificada por `PBT-U2-07`**; NFR-P-21 mantém as propriedades executáveis sem intermitência |
| `resiliency-baseline` | N/A | Desativada na Requirements Analysis |

## 9. O que fica para o próximo portão (NFR Design de U2)

Aqui ficaram os **alvos**. O NFR Design decide a **forma**: onde mora o `Lock` e a conexão, como o
composition root entrega a raiz de dados ao repositório, qual a estrutura das funções síncronas que
NFR-P-08 exige, e como o dublê em memória cumpre as mesmas regras sem banco.
