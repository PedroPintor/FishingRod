# Cenário 02 — Ambiente de estudos da faculdade (uma pessoa só)

**Narrado por:** Pedro Pintor, em 2026-08-14
**Confiança:** alta como intenção de produto · ⚠️ **hipotético como uso** — ninguém operou isso
**Papel deste cenário:** é o **segundo domínio**, e existe para testar se as abstrações são de
trabalho ou de marketing. Ver `abertas.md`, A-03.

---

## O ambiente

| Elemento | No caso da faculdade |
|---|---|
| **Ambiente** | Meus estudos do semestre |
| **Meta** | Aprender o máximo possível e sair com um mapa mental de tudo o que aprendi |
| **Frentes** | estudo do material de sala · pesquisa de aprofundamento · exercícios · planejamento de estudos |
| **Quem participa** | uma pessoa só — ninguém é convidado |

## Os agentes que nascem do trabalho

Nenhum existe no começo. Cada um aparece quando uma tarefa se repete e o orquestrador
sozinho já não basta:

- **Leitor de material** — lê o texto da aula e devolve uma visão geral.
- **Questionador / filósofo** — usado *durante* o estudo para atacar o meu entendimento.
  Não produz peça: produz dúvida sobre o que eu achei que entendi.
- **Revisor de progresso** — na frente de planejamento, olha tudo o que estudei e em que
  etapa estou, e propõe os próximos passos ou um cronograma.

## O teste: cada abstração contra os dois domínios

| Abstração | Aquisição (João) | Estudos (Pedro) | Veredito |
|---|---|---|---|
| **Ambiente com meta** | MRR recorrente | aprender + mapa mental | ✅ generaliza |
| **Frente** | conteúdo, mídia, outbound… | material de sala, exercícios… | ✅ generaliza |
| **Card / tarefa com objetivo** | "campanha no ar medindo CPL" | "ler cap. 4 e ter visão geral" | ✅ generaliza |
| **Etapas com executor** | agente, comando, conector, VOCÊ | agente, VOCÊ (ler, assistir aula) | ✅ generaliza |
| **Aba = agente dentro do card** | copy, arquiteto-meta | leitor, questionador | ✅ generaliza |
| **Agente nasce da tarefa repetida** | rodmaker constrói qualificador de MQL | questionador vira agente próprio | ✅ generaliza |
| **Wiki como contexto universal** | ICP, oferta, narrativa | o próprio mapa mental do semestre | ✅ generaliza — e aqui a wiki **é** a meta |
| **Consome / entrega** | "preciso da URL da LP" | "preciso ter lido o material para fazer os exercícios" | ✅ generaliza |
| **Travado esperando artefato** | espera a LP subir | exercício espera a leitura | ✅ generaliza |
| **Momento humano** | gravar vídeo | assistir à aula presencial | ✅ generaliza |
| **Recorrente** | revisão semanal de canal | revisão semanal do que estudei | ✅ generaliza |
| **Multiusuário opcional** | time da Nexus | grupo de estudo, se eu quiser | ✅ generaliza |
| **As três naturezas** | execução / análise / discovery | ⚠️ **ver abaixo** | 🔴 **não generaliza como está definido** |
| **Os 14 verbos** | `/subir` `/cortar` `/analisar` CPL | não existem aqui | 🔴 **são de domínio** |

---

## 🔴 A rachadura: "execução escreve no mundo"

A definição que sustenta as três naturezas é **onde cada uma escreve**:

- execução → escreve no **mundo**, via conexões
- análise → escreve uma **decisão**
- discovery → escreve uma **diretriz** na wiki

No ambiente de estudos, **não existe mundo externo para escrever**. Não há campanha no ar,
e-mail enviado nem página publicada. Todo artefato produzido — resumo, mapa mental, exercício
resolvido — fica **dentro do próprio ambiente**.

Consequência: no domínio de estudo, quase tudo cai em "discovery", e a tripartição colapsa.
Ela não descreve trabalho em geral — descreve **trabalho de operação**, onde existe um mundo
externo que recebe as peças.

### Duas saídas possíveis (nenhuma decidida — é conversa de produto, não deste documento)

**(a) Redefinir o eixo.** Trocar "onde escreve" por **onde o artefato tem efeito**:

| Eixo genérico | Aquisição | Estudos |
|---|---|---|
| efeito fora do ambiente | campanha no ar | trabalho entregue ao professor |
| efeito sobre uma escolha | cortar o canal | mudar o cronograma de estudo |
| efeito sobre o que o ambiente sabe | diretriz de LP | conceito no mapa mental |

Sobrevive nos dois — mas ao custo de ficar mais abstrato, e abstrato é mais difícil de usar.

**(b) Natureza é rótulo do usuário, não estrutura do software.** É a sua posição. Preserva o
genérico, mas custa: sem natureza estrutural, o software não sabe **o que conta como
fechamento** de um card — e a regra "discovery só fecha com diretriz escrita" (P-04) deixa de
ser garantia e vira combinado.

**Meio-termo aparente:** o software oferece *tipo de tarefa* com critério de fechamento
configurável, e o ambiente do João configura três tipos com essas regras. Registrado como
observação; a escolha é do chat de planejamento.

---

## Sobre os verbos

O teste separa dois grupos:

- **Universais:** `/pesquisar` `/escrever` `/analisar` `/decidir` `/promover` — existem no
  estudo tanto quanto na aquisição.
- **De domínio:** `/subir` `/cortar` `/enviar` `/gravar` `/responder` — só fazem sentido onde
  há mídia, vídeo e leads.

Isso sustenta a leitura de que **o vocabulário de comandos pertence ao ambiente, não ao
software** — o mesmo destino das frentes.

---

## O que este cenário ainda não resolve

- É **hipotético**. Nenhuma parte foi operada. Vale como teste de abstração, não como evidência
  de uso — e não deve ser tratado como dor validada.
- Não mostra a **montagem** do ambiente do zero, que era justamente a pergunta A-08. Começa,
  de novo, com as frentes já definidas.
- Não diz como o usuário descobre que precisa de um agente novo, nem como o cria.
