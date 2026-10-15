# Contexto do Produto — FishingRod

Esta pasta responde **uma pergunta só**: de que o usuário do FishingRod precisa, e
por quê.

É trabalho de **exploração**, não de projeto. Aqui investigamos a dor; noutro lugar
se decide a solução. A pasta existe para que, quando chegar a hora de planejar o
desenvolvimento, exista um material escrito para dar direcionamento — em vez de
memória de conversa e intuição.

Serve a dois leitores:

- **Você**, ao decidir o que construir e o que recusar.
- **Os agentes de IA**, como contexto de entrada — inclusive o chat seguinte, que
  vai usar isto para planejar a construção.

---

## A fronteira desta pasta

O teste é a pergunta que o item responde:

| Responde… | Vai para… |
|---|---|
| O que a pessoa precisa, e por quê | **aqui** |
| Como nós construímos | **outro chat** (planejamento e decisão de software) |

Exemplo real, para calibrar:

- ✅ *"O usuário não quer ficar preso a um único LLM"* — é necessidade dele, com
  motivo dele. Fica aqui.
- ❌ *"Confinar os tipos do SDK ao adaptador"* — é decisão de desenho. Sai daqui,
  mesmo sendo consequência direta da necessidade acima.

Regra prática: se a frase só faz sentido para quem lê o código, não é aqui.
Escolha de tecnologia, arquitetura, modelagem e registro de decisão (ADR) ficam
todos **fora** desta pasta.

**E um segundo teste, para não transformar solução em princípio:** antes de escrever
uma regra do produto, pergunte *"isto é o que o usuário precisa, ou é como eu pretendo
atender?"*. Se existir uma segunda maneira de atender, é **hipótese** — vai para
`hipoteses-de-solucao.md`, com as alternativas e o critério de validação. Só o que não
tem alternativa vira princípio.

---

## O fluxo: bruto → destilado

```
   material das reuniões        eu destilo           você direciona
   + o que você sabe                │                      │
           │                        ▼                      ▼
           ▼                  os demais .md   ─────►  outro chat:
       bruto/*.md    ───────►   (asserções)           planejamento
     (matéria-prima)          rastreável ao bruto     e construção
      nunca editado
```

**Duas regras que sustentam a pasta inteira:**

1. **`bruto/` nunca é editado nem apagado.** É o registro do que o usuário disse,
   com a palavra dele. Quando uma necessidade destilada parecer errada daqui a
   três meses, o bruto é o tribunal.
2. **Todo item destilado aponta para a origem.** Item sem rastro até o bruto é
   invenção minha, e você precisa enxergar isso de relance.

---

## Mapa

| Arquivo | O que entra | O que **não** entra | Status |
|---|---|---|---|
| `bruto/` | Material das reuniões, transcrições, o que o usuário falou sem filtro. **A fonte hoje é `informacoes-usuario/`, na raiz** — não duplicada aqui de propósito | Nada meu. Só a voz dele (e a sua). | 🟢 14 itens lidos, incl. transcrição |
| `visao.md` | Uma página: o incômodo, para quem, a aposta. Mais os **não-objetivos**. | Lista de features | ⬜ nasce do bruto |
| `personas.md` | Quem é o usuário: rotina, contexto de trabalho, nível de habilidade | Demografia decorativa | ⬜ nasce do bruto |
| `dores.md` | Catálogo de dores, cada uma com a evidência que a sustenta | Dor suposta por mim | 🟡 v1 — 11 dores, **2 declaradas** pelo usuário |
| `necessidades.md` | O "trabalho" que a pessoa contrata o software para fazer, e o critério dela de sucesso | Solução disfarçada de necessidade | ⬜ nasce do bruto |
| `cenarios/` | Narrativas de uso do começo ao fim, concretas | Abstração | 🟢 3 — operação (João), estudos e maturação (Pedro) |
| `hipoteses-de-solucao.md` | Ideias de **como** atender uma necessidade, com alternativas e critério de validação | Decisão. Nada aqui está escolhido | 🟢 3 hipóteses |
| `glossario.md` | As palavras **do usuário** e o que significam para ele | Termo que só existe no código | 🟢 15 termos, vocabulário acordado ao vivo |
| `principios.md` | Regras de decisão de produto ("na dúvida, X vence Y") e o motivo | Boa intenção sem trade-off | 🟢 11 princípios |
| `requisitos/funcionais.md` | O que o sistema precisa fazer, com critério de aceite | Como é implementado | 🟡 v0 — RF-01 a RF-12, o mínimo colaborativo |
| `criterios-de-sucesso.md` | Como saberemos que funcionou | Critério que ninguém consegue verificar | 🟡 v0 — 4 critérios, 1 lacuna séria |
| `requisitos/nao-funcionais.md` | Qualidade percebida: rapidez, não perder trabalho, privacidade, autonomia | Escolha de tecnologia | ⬜ nasce do bruto |
| `historias/` | Histórias de usuário fatiadas | Épico vago | ⬜ nasce do bruto |
| `abertas.md` | O que ainda não sabemos sobre o usuário: premissas, riscos, perguntas | Certeza fingida | 🟡 v2 — 2 respondidas, 4 novas |

Os arquivos ⬜ ainda não existem — nascem do material, com conteúdo real. Criar
arquivo vazio agora só faria a pasta mentir sobre o próprio estado.

---

## Convenções

- **Idioma**: português.
- **Identificadores**: `D-nn` (dor), `N-nn` (necessidade), `RF-nn`, `RNF-nn`,
  `H-nn` (história). Estáveis: uma vez atribuído, o número não muda nem é
  reciclado. Item que morre vira `status: revogado`, não some.
- **Rastro**: cada item traz `origem:` apontando o trecho de `bruto/` que o gerou.
- **Confiança**: item vindo direto da fala do usuário é `confirmado`; item que eu
  inferi é `inferido` — e inferência precisa ser validada antes de virar base de
  decisão.
- **Data**: ISO (`AAAA-MM-DD`), sempre absoluta. Nunca "semana passada".
