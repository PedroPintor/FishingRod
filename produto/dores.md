# Dores — o que o FishingRod resolve

**Versão:** v1 · **Data:** 2026-08-14
**Origem:** `informacoes-usuario/` — 12 arquivos de trabalho (12–13/08) **+ transcrição da
reunião João × Pintor de 14/08 + `interface-v3-nexus.html` produzido pelo João**

> **Aviso de método — atualizado em 2026-08-14.** A v0 deste documento foi escrita antes da
> transcrição, quando nenhum material falava sobre a ferramenta. Todas as dores eram
> inferidas de comportamento.
>
> Com a reunião, **duas dores passaram a ser declaradas pelo usuário** (D-10 e D-11) e
> várias inferências ganharam confirmação direta. Cada item abaixo traz o estado atual:
> `confirmado` (ele disse), `inferido` (eu li do comportamento).

---

## O achado que enquadra todas as dores

O material **não descreve** um ambiente de trabalho com IA. Ele **é** um, rodando, montado
à mão em Markdown e skills:

| Peça do ambiente | Onde aparece no material |
|---|---|
| Ambiente nomeado | "Ambiente de Trabalho — Aquisição Nexus" (`LEIA-ME.md`) |
| Orquestrador | Nelson — "o orquestrador de IA do projeto" (`brief-pintor-crm.md` §3) |
| Sub-agentes | `revisor`, `arquiteto-meta`, `Content Strategist`, `cs-content-creator`, `radar-diario-de-trends`, `bibliotecário` |
| Fábrica de agentes | **`rodmaker`** — "construir via rodmaker o agente qualificador de MQL" (`plano-10-dias.md` §2) |
| Contexto de longo prazo | `knowledge-icp-nexus`, `knowledge-oferta-nexus`, `knowledge-narrativa-nexus`, `knowledge-padrao-de-qualidade-de-entrega` |
| Separação memória × estado | "Wiki = memória. Este ambiente = estado. Quando um fato aqui se provar permanente, ele sobe pra wiki via bibliotecário" (`LEIA-ME.md`) |
| Tarefas | 43 tasks nomeadas em `backlog-d10.md`, com dono, custo e critério de pronto |
| Fluxo de trabalho com portão | pauta → roteiro → **portão do `revisor`** → gravação → derivados → medição → pauta |
| Rituais | ritual semanal de 30 min · fechamento mensal · 4 checkpoints |

**Consequência:** o usuário não precisa ser convencido de que quer isso. Ele já construiu
uma versão manual e paga o custo de mantê-la. A pergunta do produto não é "ele usaria?",
é **"por que a versão manual dói?"** — que é o que este documento tenta responder.

---

## D-01 — Manter o ambiente vivo é trabalho manual concentrado num só ponto

**Evidência:** em `LEIA-ME.md`, a tabela de arquivos tem uma coluna "Quem atualiza".
São **9 arquivos, 9 vezes "Nelson"**. Todo o estado do ambiente — painel, custos, frentes,
backlog, plano — existe porque alguém reescreve arquivo à mão.

**O custo:** manutenção compete com o trabalho real. E há uma regra escrita justamente
porque o sistema não garante nada sozinho: *"Se um número não está no `painel.md`, ele não
existe. Não decidimos por memória."* Regra escrita à mão é sintoma de garantia que falta.

**Confiança:** inferido (forte — a evidência é estrutural, não retórica).

---

## D-02 — A memória de longo prazo depende de um ritual humano, e falha em silêncio

**Evidência:** o ambiente tem um mecanismo explícito de promoção estado → memória
("sobe pra wiki via bibliotecário"). Ele **falhou por cerca de três meses**, e a falha só
foi notada quando alguém foi auditar: `painel.md`, lacuna 5 — *"MRR e custo fixo nunca
ingeridos na wiki (último registro: R$9k de 25/05)"*. O material é de agosto.

**O custo:** a memória de longo prazo — o ativo central do FishingRod — degrada sem avisar.
Ninguém descobre no momento da falha; descobre meses depois, ao tentar usar.

**Confiança:** inferido (muito forte — é uma falha datada, não uma hipótese).

---

## D-03 — O elo entre decisão e execução precisa ser remontado à mão, em prosa

**Evidência:** `por-que-esse-sistema.md` existe inteiro para explicar por que as 43 tasks
do backlog são aquelas. 148 linhas escritas para religar intenção → execução. O caminho
crítico do backlog é um diagrama ASCII desenhado à mão.

**O custo:** a resposta a "por que estou fazendo esta task?" não é uma consulta ao ambiente
— é um ensaio que alguém escreve e que envelhece no instante seguinte.

**Confiança:** inferido.

---

## D-04 — O contexto que impede a IA de sair genérica está espalhado e é remontado a cada pedido

**Evidência:** é a justificativa literal do Grupo 4 do backlog — *"o que impede o prompt de
sair genérico"*. Duas tasks dizem a dor com todas as letras:

- T-A02 (biblioteca de prompts): *"**Sem biblioteca, você reescreve o mesmo pedido todo dia
  com resultado diferente.**"*
- T-A01 (kit de marca): *"Sem isso, o Kairogen gera imagem bonita e fora da marca toda vez."*

**O custo:** mesmo pedido, resultado diferente. É variância de qualidade causada por contexto
que não persiste — a dor mais central do produto, dita pelo próprio material.

**Confiança:** inferido (muito forte — está escrito quase nas palavras do produto).

---

## D-05 — O que foi resolvido num projeto não chega ao próximo

**Evidência:** `setup-ambiente.md` e `brief-pintor-crm.md` trazem a mesma nota:
*"Referência pronta: `trabalho/arpe/setup-conectores.md` já traz `search-console-mcp` e
`mcp-wordpress` investigados, com comandos. **Reaproveitar**."*

Reaproveitamento entre projetos depende de alguém lembrar que o arquivo existe e colar
o caminho no briefing.

**O custo:** capacidade instalada num projeto não vira capacidade do ambiente. Cada projeto
recomeça perto do zero.

**Confiança:** inferido.

---

## D-06 — A aprovação humana é o gargalo declarado, e não tem instrumentação

**Evidência:** `plano-10-dias.md` §6 nomeia isso como **o risco número 1**: *"Aprovação vira
gargalo."* E `por-que-esse-sistema.md` §10: *"O gargalo mais provável é o João. (…)
**Se ele estiver reescrevendo, o sistema falhou.**"*

A mitigação proposta é inteiramente processual — entregar em lotes, portão antes dele,
aprovação como sim/não. Nada disso é apoiado por mecanismo; depende de todos se comportarem.

**O custo:** o humano é o recurso mais escasso do ambiente e o único sem instrumento.
Não há fila, não há lote, não há registro de aprovação — só combinado.

**Confiança:** inferido (forte — a dor é declarada, a ausência de instrumento é observada).

---

## D-07 — Criar agente novo é atividade rotineira, mas artesanal

**Evidência:** o cronograma D-10 põe **construção de agentes no caminho crítico**: dias 1–2
"construir agente qualificador de MQL (rodmaker)", dias 3–4 "construir agente de listas e
sequências (rodmaker)". Dois agentes novos em quatro dias, num plano de dez.

**O custo:** o ambiente cresce por agentes novos, e essa é a operação mais frequente — mas
depende do `rodmaker` ser acionado por alguém que sabe acioná-lo.

**Confiança:** inferido. **Nota:** valida diretamente a intenção de "cada projeto é um espaço
onde o usuário cria os seus agentes".

---

## D-08 — Trabalho começa e não termina, e nada no ambiente força o fechamento

**Evidência:** `por-que-esse-sistema.md` §10, dito como o risco mais sério de todos:
*"a Nexus tem **oito projetos de inovação registrados e nenhum concluído**. Todos 'em
evolução'. Este sistema não pode ser o nono."*

A defesa criada foi, de novo, processual: data-limite (23/08), teste de aceite objetivo
(10 de 10) e checkpoints que mandam parar.

**O custo:** sem acompanhamento com critério de pronto, o ambiente vira arquivo de coisas
inacabadas — e a produtividade prometida nunca se realiza.

**Confiança:** inferido (forte — é um padrão histórico contado pelo próprio usuário).

---

## D-09 — Ferramenta que não é legível por máquina devolve trabalho manual ao operador

**Evidência:** `setup-ambiente.md` eleva isso a princípio de governança do stack:
*"**Entre ferramentas equivalentes, ganha a que pode ser lida por máquina.** Ferramenta sem
API ou MCP transfere trabalho manual para o João — e não há braço para isso."* O critério
sozinho já decidiu duas compras (SEMrush × SE Ranking, Smartlead × Instantly).

E em `brief-pintor-crm.md` §3: *"Um painel que depende de digitação manual **morre em 3
semanas**, e com ele morre a capacidade de decidir."*

**O custo / o que isso exige do FishingRod:** o ambiente precisa alcançar as ferramentas
externas onde o trabalho realmente acontece. Um ambiente que só sabe de si mesmo devolve
ao usuário exatamente o trabalho manual que ele está tentando eliminar.

**Confiança:** inferido (muito forte — é um princípio explícito, aplicado a decisões reais).

---

---

# Dores declaradas pelo usuário (reunião de 2026-08-14)

As duas abaixo saíram da boca dele, sobre a ferramenta. São as âncoras do produto.

## D-10 — "É muita função. Como eu garanto que faço todas, sendo um só?"

**Evidência — literal:**
> **João:** "quando eu quis realmente fazer isso: p***, **é muita função, é função para c*****
> para fazer. Como que eu vou garantir que eu vou fazer todas e ainda fazer a gravação que é
> externo?**"

**O custo:** não é falta de organização — é **capacidade de execução paralela com garantia**.
Ele sabe exatamente o que precisa ser feito (43 tasks, 9 papéis, 6 frentes mapeados). O que
falta é conseguir tocar tudo sem que algo caia por esquecimento.

**O que ele espera do ambiente:** *"nesse modo de uso que eu tô pensando aqui, fica muito
fácil eu operar cinco, seis tasks diferentes durante o dia."*

**Confiança:** ✅ **confirmado** — declarado, sobre a ferramenta.

---

## D-11 — O trabalho para quando depende de um humano ou de outro trabalho

**Evidência:** o João identificou o único ponto verdadeiramente offline da operação —
> "a gravação é a única coisa que é offline do total"
> "a única coisa que vai dar realmente trabalho mesmo parece que é a gravação"

E descreveu o comportamento que quer no lugar de parar:
> "fica só o chat aqui travado esperando (…) **posso mudar de card aqui também. Continuar.**"

Na interface que ele mesmo montou, isso virou estado de primeira classe: cards `travado` com
o motivo escrito (*"espera «url da LP no ar» — card lp-clinicas"*) e destravamento automático
quando o artefato aparece.

**O custo:** hoje, dependência entre trabalhos vive na cabeça de alguém. Quando o artefato
fica pronto, ninguém é avisado — o trabalho bloqueado só volta a andar quando a pessoa lembra.

**Confiança:** ✅ **confirmado** — o problema e a solução desejada foram descritos por ele.

---

# Dor de segunda persona (Pedro, 2026-08-14)

## D-12 — Times que trabalham com IA não compartilham o contexto que produzem

**Evidência:** relato do Pedro, a partir de observação própria — *"isso resolve um problema
que eu já vi"*. Quatro sintomas nomeados por ele:

1. **Contexto não se reaproveita entre tarefas** — cada pessoa reconstrói do zero.
2. **Não se acompanha o ritmo do colega** que está usando IA, porque o volume produzido é alto.
3. **O material gerado fica externo** ao ambiente e **não passa por filtro de revisão**.
4. **Decisões, razões e aprendizados não ficam num lugar compartilhado** — então quem pega a
   tarefa depois começa sem contexto bom para continuar.

**O custo:** o ganho individual de produtividade com IA não vira ganho de time. Pior: aumenta
a dispersão, porque cada pessoa produz mais material solto.

**Confiança:** 🟡 **observada pelo Pedro, não validada em campo.** Não é dor do João — ele não
falou disso; a Nexus tem um operador. Esta é a dor que justifica o multiusuário, e por isso
merece evidência própria antes de virar base de decisão pesada.

---

# Reclassificação das dores inferidas

A reunião confirmou parte do que estava inferido:

| Dor | Estado agora | O que confirmou |
|---|---|---|
| **D-04** contexto remontado a cada pedido | ✅ **confirmado** | *"ou seja, eu não repito mais isso."* — sobre diretriz promovida à wiki |
| **D-05** o que foi feito não chega ao próximo | ✅ **confirmado** | *"esse discover sobe também do que o outro discover tem na wiki (…) quando for a hora esse cara vai saber das ideias."* |
| **D-02** memória de longo prazo degrada | 🟡 parcial | A wiki como contexto universal foi confirmada; a **falha silenciosa** dela não foi discutida |
| **D-06** aprovação humana sem instrumento | 🟡 parcial | Momento humano virou estado explícito na interface, mas o gargalo em si não foi falado |
| **D-08** trabalho não termina | 🟡 parcial | Aparece como critério de fechamento por artefato (P-04), não como dor nomeada |
| **D-01, D-03, D-07, D-09** | ⬜ ainda inferido | Não tocadas na reunião |

---

## A restrição que atravessa todas

*"Não há braço. (…) Essa restrição não é um problema a contornar. **É o que define a
arquitetura inteira.**"* (`por-que-esse-sistema.md` §4)

E a pergunta de confronto que ele aplica a cada decisão do negócio:
**"Isso escala ou é hora vendida?"**

Vale aplicá-la ao FishingRod, item por item. Toda função do produto que exigir manutenção
manual recorrente é hora vendida disfarçada de recurso.
