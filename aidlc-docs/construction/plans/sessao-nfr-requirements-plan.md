# NFR Requirements — U6 `sessao`

**Fase:** CONSTRUCTION · **Unidade:** `U6 sessao` · **Portão 2 de 4** · **Data:** 2026-10-02
**Entrada:** `construction/sessao/functional-design/` (aprovado em 2026-10-02T22:28:28Z)

> Enquanto houver `[Answer]:` vazio abaixo, **nenhum artefato de NFR é gerado**.

---

## 1. Fronteira deste estágio

O Functional Design decidiu **o comportamento** da sessão: a porta, os 5 eventos, os 4 estados, os
9 motivos de falha e as 54 regras `RN-S-*`. Ele deixou uma lista de itens para cá (plano de FD §8 e
R-FD6-11). Este estágio decide **como esse comportamento se sustenta**: a entrada do SDK como
primeira dependência de runtime do projeto, qual versão, qual CLI, os tempos, os limites, a
varredura de vulnerabilidades e quando roda o teste com o Claude de verdade.

**Não se reabre aqui:** o contrato da porta, as regras `RN-S-*`, as propriedades `PBT-U6-*`, as
decisões G1–G15. Se uma resposta abaixo tornar uma regra impossível de cumprir, isso é achado
bloqueante e volta como emenda ao Functional Design.

**Um item do §8 do FD que perdeu o objeto:** "o número exato do limite de passos". A Q12=B do FD
decidiu que não há limite, então não há número a escolher. Fica registrado para não parecer esquecido.

## 2. O que foi medido antes de perguntar

Nada aqui instalou o SDK no projeto. Foram consultas ao índice de pacotes e ao resolvedor do uv.

| Fato medido | Por que importa |
|---|---|
| Com o corte `exclude-newer = 2026-08-25` (ESC-15), o uv resolve **`claude-agent-sdk 0.2.144`** | É a versão que entraria se ninguém escolhesse |
| O pacote pronto para **Windows** da 0.2.144 foi publicado em **2026-08-25T22:46:28Z**, depois do corte. Os de macOS e Linux saíram em 2026-08-21 | **No Windows, a 0.2.144 só existe como código-fonte sob o corte**. Os pacotes prontos têm ~100 MB porque trazem o CLI do Claude embutido; o código-fonte tem 344 KB e não traz. Instalar a 0.2.144 nesta máquina daria um SDK **sem o CLI embutido** |
| A **0.2.143** é a última versão com pacote Windows publicado antes do corte (2026-08-20) | Candidata natural a versão travada |
| A **0.2.125**, a versão do spike, exige `mcp<2`. A 0.2.144 aceita `mcp<3` e o corte resolve `mcp 2.1.0` | Travar a versão do spike mantém o MCP 1.x que foi medido; subir muda a versão principal do MCP |
| O SDK traz **31 pacotes transitivos**, entre eles `mcp`, `pydantic`, `cryptography`, `starlette`, `uvicorn`, `sse-starlette`, `pyjwt`, `pywin32` | Boa parte é o lado **servidor** do MCP, que U6 não usa: os servidores de ferramenta são in-process |
| O CLI `claude` instalado na máquina é o **2.1.288** | É diferente do CLI embutido no pacote do SDK, e se atualiza sozinho |
| O uv instalado (0.11.6) tem o comando **`uv audit`** | Varredura de vulnerabilidades sem dependência nova (Q4) |
| No código-fonte da 0.2.143, o SDK procura **primeiro o CLI embutido** e, se não achar, o `claude` do `PATH`, sem avisar | Com a 0.2.144 no Windows (sem CLI embutido), a sessão usaria **em silêncio** o CLI da máquina (Q2, Q3) |
| No mesmo código, a espera pela inicialização do CLI é `max(CLAUDE_CODE_STREAM_CLOSE_TIMEOUT, 60 s)` | O padrão de 60 s existe e só pode ser **aumentado** por variável de ambiente (Q7) |

## 3. Decisões que as extensões já tomam (sem pergunta)

| Regra | Decisão |
|---|---|
| SECURITY-10, travamento | A versão do SDK fica exata no `uv.lock`, que já guarda o hash de cada pacote. Fonte única: PyPI oficial |
| SECURITY-10, sem dependência não usada | Vale para **dependências diretas**: entra só o SDK. Os transitivos que U6 não usa (o lado servidor do MCP) não podem ser removidos sem bifurcar o SDK; ficam como **risco aceito declarado**, e a varredura da Q4 cobre todos eles |
| SECURITY-10, SBOM e CI | O projeto roda localmente, sem implantação em produção nem pipeline de CI nesta iteração. O `uv.lock` é o inventário completo. SBOM e CI ficam **N/A** e são reavaliados quando houver distribuição (RNF-07) |
| PBT-09 | `hypothesis`, já em `dependency-groups.dev` desde U0. Nada muda |
| resiliency-baseline | Desabilitada (RNF-08). Nada de nova tentativa automática além da reconexão na próxima mensagem, já decidida em RN-S-34 |

## 4. Passos

- [x] **Step 1** — Ler os artefatos de Functional Design de U6
- [x] **Step 2** — Criar este plano com passos em checkbox
- [x] **Step 3** — Gerar perguntas por categoria de NFR, com tag `[Answer]:`
- [x] **Step 4** — Salvar o plano em `construction/plans/`
- [x] **Step 5** — Respostas coletadas em 2026-10-06T22:21:46Z: todas A (Q4 com A1 e A2; Q5 mantendo as varreduras estáticas). Sem ambiguidade. O comentário da Q9 supôs que só se manda uma mensagem por vez mesmo com várias sessões; U6 não impõe isso (RN-S-40), registrado em `nfr-requirements.md` §7 para U9
- [x] **Step 6** — Gerado `nfr-requirements/nfr-requirements.md` (18 requisitos `NFR-S-01..18`, 4 medições novas 11–14)
- [x] **Step 7** — Gerado `nfr-requirements/tech-stack-decisions.md` (9 decisões `TS-S-01..09`, 4 riscos aceitos)
- [x] **Step 8** — Apresentar a conclusão e aguardar aprovação. Conclusão apresentada em 2026-10-06T22:21:46Z. **APROVADO em 2026-10-06T22:26:08Z** ("aprovado . vamos para o proximo estagio")

---

## 5. Perguntas

### Q1 — O SDK entra como dependência obrigatória ou opcional?

É a **primeira dependência de runtime** do projeto. O núcleo continua sem ela de qualquer jeito: a
fronteira é garantida pelo teste do TD-02 (Q5), não pelo empacotamento.

A) **Obrigatória**, em `dependencies`. *Ganho*: `uv sync` instala tudo, o programa sempre roda.
   *Custo*: quem um dia quiser só outro provedor instala o SDK do Claude junto.
B) **Opcional**, como extra `fishingrod[claude]`. *Ganho*: o empacotamento já diz que o Claude é
   um adaptador entre outros. *Custo*: sem o extra, o programa abre e não tem com quem conversar;
   o composition root (U9) precisa tratar isso. Hoje não existe outro adaptador.
C) Outra — diga qual.

**Recomendação: A.** O FishingRod é agnóstico a LLM pela porta de sessão, não pelo `pyproject`.
Quando o segundo adaptador existir, transformar a dependência em extra é uma mudança de três linhas.

[Answer]: A

---

### Q2 — Qual versão do SDK fica travada?

A) **`0.2.143`**: a última com pacote Windows publicado antes do corte de ESC-15. *Ganho*: dentro da
   política, com CLI embutido nas três plataformas, mais nova que o spike. *Custo*: o spike mediu a
   0.2.125 com MCP 1.x; a 0.2.143 traz MCP 2.x, e tudo o que o spike mediu precisa ser medido de
   novo. A medição 10 do FD (critério 3) já obriga isso para qualquer versão.
B) **`0.2.125`**: a do spike. *Ganho*: os fatos do §3 do plano de FD valem sem tradução. *Custo*:
   fica presa ao MCP 1.x, uma versão principal atrás, e mais de 20 versões atrás do SDK.
C) **Mover o corte de ESC-15** para uma data recente e pegar a versão mais nova. *Custo*: o corte
   vale para o projeto inteiro e mexe no `uv.lock` de tudo; deixaria de ser uma decisão de U6.
D) Deixar o uv escolher (`0.2.144`). *Custo*: **no Windows ela vem sem o CLI embutido**, e o SDK passa
   a usar o CLI da máquina sem avisar (§2).
   Listada só para registrar por que não.

**Recomendação: A.** As 10 medições do FD rodam de qualquer jeito com a versão travada. Se alguma
falhar na 0.2.143 e passar na 0.2.125, a troca é uma linha e fica registrada.

[Answer]: A

---

### Q3 — Qual CLI do Claude a sessão usa?

O pacote do SDK traz um CLI embutido, e a máquina tem outro instalado (2.1.288), que se atualiza
sozinho. O SDK aceita um caminho explícito para o CLI.

A) **O CLI embutido no pacote.** *Ganho*: a versão do CLI fica amarrada ao `uv.lock`; o que foi
   medido no Code Generation é o que roda depois; `PROVEDOR_AUSENTE` vira um caso raro de
   instalação quebrada. *Custo*: o CLI do FishingRod e o seu podem ter versões diferentes. A
   medição 4 do FD precisa confirmar que o embutido enxerga o seu login da assinatura.
B) **O CLI instalado na máquina.** *Ganho*: uma versão só para você. *Custo*: ele se atualiza
   sozinho; uma atualização pode mudar um comportamento medido sem nenhuma mudança no projeto, e
   isso fura o travamento de SECURITY-10.
C) **Configurável**, com o embutido como padrão. *Custo*: mais um caminho a testar, sem um uso hoje.

**Recomendação: A.** É o único jeito de o travamento da Q2 valer também para o processo que de fato
conversa com o Claude. Como o SDK cai no CLI da máquina sem avisar quando o embutido falta (§2), o
adaptador passa o caminho do embutido explicitamente, e a falta dele vira `PROVEDOR_AUSENTE` em vez
de troca silenciosa.

[Answer]: A

---

### Q4 — Como é feita a varredura de vulnerabilidades (SECURITY-10)?

Com o SDK, o projeto passa de zero para 32 pacotes de runtime. SECURITY-10 exige uma varredura
configurada ou documentada.

A) **`uv audit`**, que já existe no uv instalado. Roda no Code Generation de U6, o resultado fica
   registrado no resumo do código, e o comando entra nas instruções de Build and Test.
   *Ganho*: nenhuma dependência nova. *Custo*: nenhum pipeline o roda sozinho; é um passo
   documentado, que é o que SECURITY-10 aceita sem CI.
B) **`pip-audit`** no grupo `dev`. *Custo*: mais uma dependência para fazer o que o uv já faz.
C) Outra — diga qual.

**E se a varredura achar algo?**

- A1) Vulnerabilidade **conhecida em pacote que U6 usa**: bloqueia o portão de U6 até trocar de versão.
- A2) Vulnerabilidade só em pacote **que U6 não usa** (o lado servidor do MCP): registrada como risco
  aceito, com o motivo.

**Recomendação: A, com A1 e A2.**

[Answer]: A com A1 e A2

---

### Q5 — Como o teste do TD-02 simula "SDK desinstalado"?

O critério de aceite (`component-dependency.md`) pede um teste que importa `dominio/` e `aplicacao/`
com o SDK **desinstalado**, e o import não falha. A partir de U6, o SDK estará instalado.

A) **Subprocesso com o SDK bloqueado.** O teste sobe um Python novo que instala um bloqueador de
   import: qualquer `import claude_agent_sdk` levanta `ImportError`, como se o pacote não existisse.
   Depois importa todos os módulos de `dominio/` e `aplicacao/`. *Ganho*: roda na suíte padrão, em
   segundos, e falha exatamente como falharia sem o pacote. *Custo*: é equivalência, não remoção
   literal.
B) **Um segundo ambiente virtual sem o SDK.** *Ganho*: literal. *Custo*: cria e sincroniza um
   ambiente a cada execução; lento, e fora da suíte padrão na prática.
C) **Só a varredura estática** de import, como as `test_fronteira.py` de U1, U4 e U5 já fazem.
   *Custo*: não pega import dinâmico nem import feito por um transitivo.

**Recomendação: A, mantendo também as varreduras estáticas que já existem.** A e C se completam:
a estática aponta a linha; o subprocesso prova que o pacote inteiro carrega.

[Answer]:  A mantendo a varredura estatisticas que ja existem

---

### Q6 — Quando roda o teste com o Claude de verdade?

As 10 medições do FD e o critério 3 precisam do SDK real, do seu login e gastam a sua assinatura.
Não podem fazer parte da suíte padrão (`691 passed`).

A) **Marcador do pytest `sdk_real`, fora da suíte padrão.** `uv run pytest` não o executa; quem quer
   roda `uv run pytest -m sdk_real`. No Code Generation, eu rodo uma vez e registro o resultado de
   cada medição no resumo do código. *Ganho*: o teste mora junto dos outros e não é esquecido.
B) **Script separado**, fora do pytest. *Custo*: fica fora da disciplina dos testes e envelhece
   em silêncio.
C) **Variável de ambiente** que libera os testes (pulados sem ela). *Custo*: aparecem como
   `skipped` em toda execução, misturados com os 7 pulos que já existem.

**Recomendação: A.**

[Answer]: A

---

### Q7 — Quanto tempo a sessão espera o CLI subir?

`enviar` em `SEM_CONEXAO` sobe o processo antes de entregar a mensagem (RN-S-33). Se não subir,
o turno termina em `FalhaDoTurno` sem entrega.

A) **60 segundos**, e depois `INDISPONIVEL`. É o padrão do próprio SDK para a inicialização (conferido
   no código da 0.2.143, §2), então o número é o do fornecedor e só fica declarado e testável.
B) **30 segundos.** *Custo*: na primeira vez do dia, com o CLI sendo carregado do disco, pode falhar à toa.
C) **Sem limite**: você aperta ESC se demorar. *Custo*: uma sessão travada em `EM_TURNO` sem prazo
   depende de você perceber.

**Recomendação: A.** Se a versão travada for outra (Q2), o Code Generation confere o padrão de novo;
se ele não existir, o adaptador aplica os 60 s ele mesmo.

[Answer]: A

---

### Q8 — Um turno pode ficar em silêncio por quanto tempo?

A Q12=B do FD tirou o limite de passos, e uma ferramenta pode esperar a sua confirmação pelo tempo
que for (U5). Resta saber se há prazo para o provedor ficar **sem mandar nada**.

A) **Sem prazo de silêncio nem de turno.** A defesa é o ESC, como na Q12=B. *Ganho*: coerente com o
   que já foi decidido; um turno que espera você confirmar nunca morre sozinho. *Custo*: se o
   provedor travar sem cair, só o ESC tira a sessão dali.
B) **Prazo de silêncio de 10 minutos**, sem contar o tempo em que uma ferramenta espera a sua
   confirmação. Estourou: `INDISPONIVEL`, e a conexão cai. *Custo*: um relógio a mais, e um caso a
   mais em cada propriedade de ciclo de vida.
C) Outro valor — diga qual.

**Recomendação: A.** Com B, o relógio teria de saber quando o tempo "não conta", e o ganho é cobrir
uma falha que o ESC já cobre.

[Answer]: A - vamos seguir com A. fazer B teria que ter o comportamento de retorno do hitorico do chat tambem para funcionar bem a usabilidade, pq se nao, nos podemo encerrar quando nao devia, o usuario poderia estar simplismente fazendo outra coisa e quando voltou para continuar a conversa o chat perdeu o historico. vamos manter sem tempo, oque fecharia automaticamente é se o usuario sair do ambiente, fechar o chat ou fechar o software.

---

### Q9 — Quantas sessões podem estar conectadas ao mesmo tempo?

Cada sessão conectada é um processo do CLI. `abrir` não sobe processo (RN-S-05); quem sobe é a
primeira mensagem.

A) **Sem teto em U6**, e o Code Generation mede e registra a memória de um processo do CLI. *Ganho*:
   nenhuma regra nova; com poucos usuários e poucos chats abertos, o número real fica pequeno.
   *Custo*: se um dia houver dezenas de chats ativos, a máquina sente antes do programa.
B) **Teto de N processos** (por exemplo, 8). Ao passar do teto, a sessão ociosa mais antiga é
   desconectada e perde o histórico na próxima mensagem (`conversa_nova = True`). *Custo*: uma
   regra nova de ciclo de vida, que volta ao FD como emenda, e uma perda de histórico que você não
   pediu.
C) Outro — diga qual.

**Recomendação: A.** A medição de memória transforma a decisão de B em algo que um número pode
justificar depois.
s
[Answer]: A - o usuario pode conversar em varios chats paralelamente, entao nao podemos ter um limite de sessoes. no nosso caso agora, eu acho que o nosso software esta encaminhando para somente ser possivel mandar uma menasgem por vez mesmo se eu tivesse mais de uma sessao aberta. se estiver assim, nao tem problema, na em uma proxima iteracao nos vamos ter que colocar esse tipo de usabilidade, onde o usuario pode enviar mensagem para varios chats paralelamente.

---

### Q10 — Há alvo de desempenho?

O tempo de resposta é quase todo do provedor, que U6 não controla. O que é nosso é subir o
processo e converter os eventos.

A) **Medir e registrar, sem portão.** O teste com o SDK real anota o tempo para conectar e o tempo
   até o primeiro pedaço de texto, e o resumo do código guarda os números como linha de base.
   *Ganho*: quando ficar lento, há um antes para comparar.
B) **Alvo com portão** (por exemplo, conectar em até 10 s). *Custo*: um teste que falha por causa da
   rede ou do provedor, não do código.
C) Nada. 

**Recomendação: A.** É o que a U2 fez com o tempo de abrir um ambiente, sem o problema de depender
de rede.

[Answer]: A

---

### Q11 — E se o FishingRod morrer de repente?

RN-S-38 garante que nenhum processo do CLI fica sem dono nos caminhos normais e de erro. Uma queda
dura do Python (o processo morto pelo sistema, a janela fechada à força) não passa por esses
caminhos.

A) **Aceitar e medir.** O Code Generation mata o processo do Python com uma sessão conectada e
   verifica se o CLI termina sozinho ao perder a entrada. Se terminar, o risco some. Se não, fica
   registrado como risco aceito, com o sintoma (processo `claude` órfão até reiniciar a máquina).
B) **Amarrar os processos filhos ao pai** pelo sistema operacional (Job Object no Windows). *Custo*:
   código específico de plataforma, só para a queda dura.
C) Outro — diga qual.

**Recomendação: A.** Primeiro saber se o problema existe.

[Answer]: A

---

### Q12 — Como o log de U6 é configurado?

RN-S-54 já decidiu o **conteúdo**: só metadados, nunca texto, argumentos ou credencial, e a saída de
erro do CLI só em DEBUG. Falta a **forma**, até U9 decidir o destino.

A) **Como em U2**: logger `fishingrod.sessao` com `NullHandler`; níveis fixos — INFO para abrir,
   conectar, fechar e encerrar; WARNING para ferramenta negada, divergência de trechos e `dado`
   desconhecido; ERROR para `FALHA_INESPERADA` e exceção dentro de ferramenta; DEBUG para a saída
   de erro do CLI. *Ganho*: o mesmo padrão nas duas unidades com log; U9 liga tudo num lugar só.
B) **Descartar a saída de erro do CLI** em vez de levá-la ao DEBUG. *Ganho*: nada que o CLI escreva
   pode vazar para um arquivo de log. *Custo*: muda RN-S-54 (emenda ao FD) e tira a principal pista
   quando o CLI falhar.
C) Outro — diga qual.

**Recomendação: A.**

[Answer]: A

---
