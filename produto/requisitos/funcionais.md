# Requisitos funcionais

**Versão:** v0 · **Data:** 2026-08-14
**Origem:** Pedro Pintor, conversa de 14/08 — *"isso basicamente resume a ideia"*

> Primeiro conjunto de requisitos com origem direta numa fala. Não é a lista completa do
> produto: é **o mínimo que faz de um ambiente um ambiente colaborativo de trabalho com IA**.
>
> Regra de leitura: `confirmado` = dito pelo usuário · `derivado` = consequência necessária de
> algo dito, marcada como tal. Nada aqui diz **como** implementar.

---

## O mínimo colaborativo

> **Pedro:** "temos que garantir o básico para ser o ambiente colaborativo para todos. Então os
> usuários do ambiente escrevem na wiki, criam agentes, criam tarefas, alocam tarefas para
> outros usuários ou agente, sinaliza sub tarefa com impeditivo, sinaliza tarefa finalizada,
> aciona chats de IA para planejar tarefas, criar agentes, executar tarefas."

**Todo usuário do ambiente** — não só o dono — pode:

| ID | Requisito | Critério de pronto | Confiança |
|---|---|---|---|
| **RF-01** | **Criar tarefas** dentro de uma frente | Uma tarefa criada por um usuário não-dono aparece para os demais e pode receber etapas | ✅ confirmado |
| **RF-02** | **Criar agentes**, que passam a existir para o ambiente | Um agente criado por qualquer usuário fica disponível como responsável de etapa | ✅ confirmado |
| **RF-03** | **Escrever na wiki** — por caminho verificado, com revisão (P-14) | O conteúdo entra na categoria certa, no formato da wiki, e passa a ser lido pelos agentes | ✅ confirmado |
| **RF-04** | **Alocar tarefa ou etapa** a outro usuário ou a um agente | A etapa passa a ter responsável nomeado; se for agente, pode ser acionado (H-04) | ✅ confirmado |
| **RF-05** | **Sinalizar impeditivo** numa sub-etapa | A etapa fica marcada como impedida, com motivo, e isso é visível a quem depende dela | ✅ confirmado |
| **RF-06** | **Sinalizar tarefa finalizada** | A tarefa fecha e o artefato que ela produz passa a existir para quem o consome | ✅ confirmado |
| **RF-07** | **Acionar chats de IA** para três coisas: planejar tarefas, criar agentes, executar tarefas | Cada um dos três é alcançável a partir do trabalho, sem sair do ambiente | ✅ confirmado |

**Nota sobre RF-05 e RF-06 — são sinalizações humanas.** Existem em paralelo aos mecanismos
automáticos já registrados: o travamento por artefato faltante (que o ambiente detecta sozinho)
e a checagem do tipo de tarefa (que define o que conta como pronto). Ver A-15.

---

## Governança

> **Pedro:** "o software, como é compartilhado e vai ter usuários, precisa ter um certo tipo de
> **governança**. O 'usuário principal' é o **admin do ambiente** — ele que criou aquele
> ambiente, aí ele teria algumas permissões a mais."

| ID | Requisito | Confiança |
|---|---|---|
| **RF-08** | O ambiente tem um **admin** — quem o criou — com permissões adicionais | ✅ confirmado |
| **RF-09** | O admin pode **alterar a estrutura**: meta, frentes, tipos de tarefa, regras, categorias da wiki | ✅ confirmado |
| **RF-10** | O admin pode **bloquear funcionalidades** para os demais usuários | ✅ confirmado |

### O padrão é permissivo, e isso é uma decisão

O mínimo colaborativo vale **para todos por definição**; o admin **restringe** se quiser. Não é
o contrário — ninguém precisa receber permissão para criar tarefa, criar agente ou escrever na
wiki.

É uma escolha de produto com consequência: um ambiente que já nasce aberto pode ser desarrumado
por qualquer um, e a arrumação depende de o admin perceber e fechar. O caminho oposto (tudo
fechado, admin libera) protegeria a estrutura ao custo de o ambiente nascer inerte — e um
ambiente colaborativo inerte não é colaborativo. Ver `principios.md`, P-20.

---

## Alcance de ferramentas externas

> **Pedro:** "Kairogen é uma ferramenta, no caso aqui isso é um MCP. (…) o **responsável
> continua sendo o agente**; a questão é que o agente teria a ferramenta MCP do Kairogen para
> fazer a tarefa."

| ID | Requisito | Confiança |
|---|---|---|
| **RF-11** | O ambiente permite **configurar serviços MCP externos** | ✅ confirmado (como hipótese de solução — ver H-05) |
| **RF-12** | Ferramentas configuradas podem ser **associadas a um ou mais agentes** | ✅ confirmado |

**Necessidade que isto atende:** o trabalho real acontece em ferramentas externas, e um
ambiente que não as alcança devolve trabalho manual ao usuário — ver `dores.md`, D-09, e o
princípio de governança do próprio cliente: *"entre ferramentas equivalentes, ganha a que pode
ser lida por máquina"*.

**Consequência para o modelo:** a ferramenta é **do agente**, não da etapa. `/criar + Kairogen`,
como aparece na interface do cliente, é notação abreviada de "agente responsável que dispõe da
tool Kairogen". O campo de responsável recebe só o agente.

---

## O que este documento ainda não cobre

Tudo o que já está registrado como comportamento nos outros arquivos e ainda não foi escrito
como requisito: contrato consome/entrega, travamento e destravamento por artefato, tipos de
tarefa com objetivo e checagem, tarefa recorrente, momento humano, promoção de diretriz à wiki,
"andou sozinho". Estão em `glossario.md`, `principios.md` e `cenarios/` — falta a passagem para
requisito, com critério de pronto.
