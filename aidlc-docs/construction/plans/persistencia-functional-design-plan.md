# Functional Design Plan — U2 `persistencia`

**Fase:** CONSTRUCTION · **Unidade:** `U2 persistencia` · **Profundidade:** comprehensive
**Data:** 2026-08-26
**Base:** `unit-of-work.md` §3 (U2), `components.md` §4.1, `component-methods.md` §4.1,
`requirements.md` (RNF-05, RNF-12, ESC-13, D-ARQ-04), U1 já implementada

---

## 1. Contexto da unidade

| Campo | Conteúdo |
|---|---|
| **Componentes** | `PortaPersistencia` (interface, `aplicacao/portas/`), `RepositorioSQLite` (`adaptadores/`) |
| **Histórias** | US-05 (a estrutura sobrevive a fechar e reabrir), US-06 (transcrição antiga continua visível) |
| **Dívidas** | **TD-04** — persistência inexistente |
| **Depende de** | U0, U1 (entidades já implementadas e testadas) |
| **Estágios** | FD **EXECUTE** (aqui) · NFR-R **EXECUTE** · NFR-D **EXECUTE** · INFRA SKIP · CG EXECUTE |
| **Portões** | 4 — é a primeira unidade com NFR |

**Contrato herdado** (`component-methods.md` §4.1), que este estágio detalha mas não reabre:

```
class PortaPersistencia(Protocol):
    async def salvar_ambiente(ambiente) -> None
    async def carregar_ambiente(id) -> Ambiente | None
    async def inserir_mensagem(id_chat, papel, texto, em_andamento) -> Identidade
    async def atualizar_mensagem(id_mensagem, texto, em_andamento) -> None
    async def registrar_uso_ferramenta(id_mensagem, tool, args_resumo, resultado_resumo) -> None
    async def listar_mensagens(id_chat, limite) -> list[MensagemPersistida]
```

**Decisão já fechada** (ESC-13, D-ARQ-04): persistência **híbrida** — `Ambiente` é documento;
transcrição é tabela. O banco **não** guarda conteúdo nem índice da wiki (RNF-12).

---

## 2. Fronteira desta unidade

**Faz**: define o que é documento e o que é tabela, a forma de serializar, a semântica de cada
operação da porta e o comportamento em conflito e em falha.

**Não faz**: `ServicoConversa` e a política de gravação do turno (U7 — esta unidade só oferece as
operações que aquela usa); nada de wiki (U3); nada de tela (U9).

---

## 3. Passos do Functional Design

- [x] **Step 1** — Consolidar respostas às perguntas da §4 e analisar ambiguidades
      (Q1=A, Q3=A, Q4=C, Q5=A, Q6=A, Q7=A, Q8=B, Q9=A; **Q2 reaberta pelo usuário**)
- [x] **Step 2** — `persistencia-fd-clarificacao.md` criado: Q2 reaberta com 4 opções, Q2a e Q1a
      novas, consequências de Q8=B declaradas. **Parado, aguardando respostas.**
- [x] **Step 3** — Gerar `construction/persistencia/functional-design/domain-entities.md`
      (modelo de dados: tabelas, colunas, tipos, índices, o que é documento)
- [x] **Step 4** — Gerar `construction/persistencia/functional-design/business-rules.md`
      (regras `RN-P-nn`: round-trip, conflito, ordem, transação)
- [x] **Step 5** — Gerar `construction/persistencia/functional-design/business-logic-model.md`
      (semântica de cada operação da porta, com pré/pós-condição e erros)
- [x] **Step 6** — Nomear as propriedades PBT desta unidade — PBT-U2-01..08
- [x] **Step 7** — Registrar conformidade das extensões e apresentar o portão

---

## 4. Perguntas

---

### Q1 — Onde fica o arquivo do banco, e quantos bancos existem?

Q10=B decidiu "vários ambientes locais, cada um mais uma linha no SQLite" — logo, **um banco só**
com várias linhas de ambiente. Falta dizer **onde** o arquivo mora, e isso também decide onde a
wiki de U3 será materializada (a `RaizWiki` é `dados:wikis/<id>`; o `dados:` precisa resolver em
algum lugar real).

A) **Pasta de dados do usuário** — `%LOCALAPPDATA%\FishingRod\` no Windows,
   `~/.local/share/fishingrod/` no Linux/Mac, via `platformdirs` ou equivalente escrito à mão.
   *Ganho*: o software funciona de qualquer diretório; dados não se misturam ao código.
   *Custo*: ou uma dependência nova, ou ~10 linhas por plataforma escritas por nós.
B) **Pasta fixa no diretório de trabalho** — `./dados/fishingrod.db` e `./dados/wikis/<id>/`.
   *Ganho*: zero dependência, tudo visível ao lado do projeto, fácil de inspecionar e apagar
   durante o desenvolvimento. *Custo*: rodar de outro diretório cria outro banco — surpresa.
C) **Configurável por variável de ambiente**, com (B) como padrão.
   *Custo*: mais um caminho de configuração para testar.

**Minha recomendação: B nesta iteração.** O uso é você e ~20 pessoas rodando localmente, e ver os
dados ao lado do código durante o desenvolvimento vale mais do que a arrumação de (A). Trocar
depois é barato: o caminho entra no composition root, e nenhum código de domínio o conhece.

[Answer]: A 

---

### Q2 — Granularidade do documento: o que é salvo a cada mudança?

`Ambiente` é documento. Mas "documento" pode ser uma coisa só ou vários.

A) **Um documento por `Ambiente`**, contendo frentes, tarefas, chats, etapas e memória inteiras.
   `salvar_ambiente` reescreve a linha toda. *Ganho*: uma transação, impossível salvar metade;
   `carregar_ambiente` é uma leitura só. *Custo*: criar uma etapa reescreve o ambiente inteiro —
   irrelevante em kilobytes, relevante se um ambiente chegar a megabytes.
B) **Um documento por `Frente`**, com o ambiente guardando só a lista de identidades.
   *Ganho*: escrita menor. *Custo*: `carregar_ambiente` vira N+1 leituras e a atomicidade some.
C) **Tabelas relacionais normais** para frente/tarefa/chat/etapa. *Custo*: contradiz ESC-13 e
   D-ARQ-04, que escolheram híbrido justamente para não manter esquema relacional de estrutura que
   muda a cada iteração.

**Minha recomendação: A.** É o que ESC-13 já escolheu; registro a pergunta porque o custo (reescrita
total) só fica visível agora, e é melhor você vê-lo antes do que descobri-lo depois.

[Answer]: vamos pensar melhor, vc disse que seria irrelevante para kilobytes mas eu conheço como o meu usuario é e ele vai cehgar a usar megabytes, ja temos que pesar em uma maneira otimizado de armazenar. oq eu tinha pensando é que o ambiente contem as partes mais acima que nao variam ou variam pouco. as sessoes com os chats sao os que mais variam. como seguir ? quais opcoes temos ? 

---

### Q3 — O documento carrega versão de esquema?

Quando U4, U5 ou uma iteração futura acrescentar um campo, os bancos existentes terão documentos no
formato velho.

A) **Sim, campo `versao_esquema` no documento.** Ao carregar, se a versão for menor que a atual,
   um passo de migração explícito roda. Nesta iteração existe só a versão 1 e nenhuma migração.
   *Ganho*: quando a primeira mudança vier, o lugar de tratá-la já existe e os dados antigos dizem
   quem são. *Custo*: um campo e um `if` que hoje não fazem nada.
B) **Não.** Se o formato mudar, apaga-se o banco e recomeça. *Ganho*: menos código.
   *Custo*: perder dados de teste real — e, no seu caso, de uso real com ~20 pessoas.

**Minha recomendação: A.** É barato agora e caro depois; e `property-based-testing` já vai exigir a
propriedade de round-trip, que fica mais honesta com a versão explícita.

[Answer]: A 

---

### Q4 — Duas escritas concorrentes no mesmo ambiente: o que acontece?

O caso é real nesta arquitetura: orquestrador e bibliotecário têm sessões vivas simultâneas
(critério 3 de U6), e as duas podem disparar ações que mudam estrutura.

A) **Última escrita vence.** Sem verificação. *Ganho*: nada a implementar.
   *Custo*: uma etapa criada pelo bibliotecário pode sumir silenciosamente quando o orquestrador
   salvar uma versão que não a continha — corrupção silenciosa, exatamente o que RNF-05 proíbe.
B) **Bloqueio otimista com `Memoria.versao`.** *Custo*: `versao` é da memória, não do ambiente —
   não cobre criar frente ou tarefa.
C) **Bloqueio otimista com uma versão do próprio documento** (coluna `versao` na linha do
   ambiente): salvar exige que a versão em disco seja a mesma que foi lida; se não for, erro
   tipado e quem chamou recarrega e repete. *Ganho*: cobre toda mudança de estrutura e satisfaz
   RNF-05 de verdade. *Custo*: `salvar_ambiente` passa a poder falhar, e U4 precisa tratar.
D) **Serializar tudo em uma fila de escrita** dentro do processo. *Ganho*: o conflito não existe.
   *Custo*: esconde o problema em vez de resolvê-lo se um dia houver dois processos.

**Minha recomendação: C.** É a única que faz RNF-05 ser verdade em vez de intenção. Declaro o custo
real: `salvar_ambiente` deixa de ser "sempre funciona" e U4 ganha um caminho de erro.

[Answer]: C 

---

### Q5 — `listar_mensagens(id_chat, limite)`: qual a semântica?

US-06 quer a transcrição antiga visível ao reabrir. Com transcrição longa, é preciso decidir o que
`limite` significa.

A) **As `limite` mensagens mais recentes**, devolvidas em ordem cronológica crescente, mais um
   cursor opcional para carregar as anteriores. *Ganho*: é o que uma janela de chat precisa.
B) **As `limite` primeiras** desde o começo. *Custo*: reabrir mostraria o começo da conversa, não
   o fim — o oposto do que se espera de um chat.
C) Sem paginação nesta iteração: sempre tudo. *Custo*: uma transcrição de meses trava a abertura
   do chat, e o problema aparece exatamente quando o produto estiver dando certo.

**Minha recomendação: A.**

[Answer]: A

---

### Q6 — Mensagem "em andamento" órfã: o que acontece ao reabrir?

`inserir_mensagem(..., em_andamento=True)` grava a mensagem do agente antes de a resposta terminar.
Se o processo morrer no meio do turno, a linha fica marcada para sempre. O critério 2 de U7 diz que
ela **permanece marcada** — não some nem se apresenta como completa. Falta decidir o resto.

A) **Fica marcada e a interface a mostra como interrompida.** Nenhuma limpeza automática. O texto
   parcial é preservado. *Ganho*: nada é perdido, e o usuário vê o que houve.
B) **Ao abrir o chat, o repositório fecha as órfãs** (remove a marca, mantém o texto). *Custo*:
   apagar a evidência de que a resposta foi cortada — a mensagem passa a parecer completa.
C) **Ao abrir, apaga as órfãs.** *Custo*: perde o texto parcial, que muitas vezes é a parte útil.

**Minha recomendação: A**, com a marca aparecendo na leitura (`MensagemPersistida.em_andamento`)
para U7 e U9 decidirem como exibir.

[Answer]: A

---

### Q7 — `registrar_uso_ferramenta`: tabela própria ou parte da mensagem?

A) **Tabela própria** `uso_ferramenta(id, id_mensagem, tool, args_resumo, resultado_resumo, criado_em)`.
   *Ganho*: uma mensagem pode ter vários usos; consultar "o que o agente fez" fica trivial; e é
   material direto para a auditoria que o produto promete. *Custo*: mais uma tabela.
B) **Coluna JSON na linha da mensagem.** *Ganho*: menos tabelas. *Custo*: consulta por ferramenta
   vira varredura de texto.

**Minha recomendação: A.**

[Answer]: A

---

### Q8 — Existe apagar nesta iteração?

Nenhuma das 14 histórias da linha fina pede apagar ambiente, frente, tarefa ou chat.

A) **Não existe apagar.** A porta não ganha `apagar_*`. *Ganho*: menos superfície e nenhuma decisão
   sobre o que acontece com a wiki e a transcrição de um ambiente apagado.
B) **Existe apagar ambiente**, porque acumular ambientes de teste vai incomodar rápido no uso real.
   *Custo*: precisa decidir o destino da wiki no disco (apagar junto? deixar órfã?) — decisão que
   pertenceria a U3/U4 e que nenhuma história pediu.

**Minha recomendação: A**, com a observação honesta de que você provavelmente vai querer (B) na
primeira semana de uso — mas aí será com a wiki já implementada e a decisão informada.

[Answer]: B - quando apagarmos ja vamos apagar tudo e apenas ter uma mensagem de aviso antes e de confirmacao antes de apagar o ambiente avisando o usuario sobre o perigo de apagar, que vai deletar tudo dentro do ambiente.

---

### Q9 — O adaptador falso (para testar U4, U5, U7 sem banco) faz parte desta unidade?

O critério de U6 exige que adaptador falso e real passem pelo **mesmo** teste de contrato (mata
TD-01). A mesma ideia se aplica aqui.

A) **Sim**: esta unidade entrega `RepositorioSQLite` **e** `RepositorioEmMemoria`, mais um teste de
   contrato que roda contra os dois. *Ganho*: as unidades seguintes testam sem tocar disco, e o
   falso não pode divergir do real sem quebrar o teste. *Custo*: mais código nesta unidade.
B) **Não**: só o real; cada unidade seguinte inventa seu próprio dublê. *Custo*: dublês divergentes
   — o defeito clássico que faz o teste passar e a produção falhar.

**Minha recomendação: A.**

[Answer]: A

---

## 5. O que este estágio **não** decide

- **Como** o SQLite é configurado (WAL, timeout, `asyncio.to_thread`, pool) — isso é **NFR Design**
  de U2, o portão seguinte. Aqui decide-se o *comportamento*; lá, o mecanismo
- A política de gravação do turno de conversa (U7)
- Qualquer coisa de wiki (U3) ou tela (U9)

---

## 6. Execução (2026-08-26)

7/7 passos concluídos. Respostas: Q1=A, Q1a=B, Q2=B, Q2a=A, Q3=A, Q4=C, Q5=A, Q6=A, Q7=A, Q8=B,
Q9=A, sem objeções à Parte 3 da clarificação.

Artefatos: `construction/persistencia/functional-design/` — `domain-entities.md`,
`business-rules.md` (26 regras RN-P-01..26), `business-logic-model.md` (8 propriedades
PBT-U2-01..08).

Emendas aplicadas em artefatos aprovados: `components.md` §4.1, `component-methods.md` §4.1,
`unit-of-work.md` U2/U4/U9 — todas riscando o texto substituído. Uma emenda de **código** fica
pendente para Code Generation: `Ambiente` ganha `versao: int = 0`.
