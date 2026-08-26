# Critérios de sucesso

**Versão:** v0 · **Data:** 2026-08-14

Como saberemos que o FishingRod funcionou. Critério vago não é critério — cada item aqui
precisa ser verificável por alguém que não participou da conversa.

---

## CS-01 — O teste de reconstituição (o mais forte que temos)

> **Pedro, 2026-08-14:** "o software tem que conseguir **produzir as peças** para ser possível
> configurar o ambiente dessa maneira. (…) vou gerar um ambiente próprio que vai ser a
> **reconstituição do que aconteceu de verdade** para eu dar para o meu cliente usar e testar."

**O critério:** o FishingRod consegue reconstituir, dentro dele, o ambiente que hoje existe em
Markdown — *Nexo Aquisição*, com as seis frentes, os tipos de tarefa do João, as regras, a wiki
e os cards em andamento.

**Por que é um bom critério:**

1. **O alvo já existe e é verificável.** Não é uma especificação a interpretar — é um ambiente
   real, escrito, com 12 arquivos e uma interface. Ou o software comporta aquilo, ou não.
2. **Testa suficiência, não features.** Se faltar uma peça, ela aparece no momento da montagem,
   não numa revisão de requisitos.
3. **Produz o próprio material de validação.** O resultado é um ambiente que o cliente pode usar
   — o que fecha o buraco de A-08 (ninguém observou uma montagem acontecendo) e alimenta
   `bruto/` com uso real.

**Cuidado registrado:** reconstituir o ambiente do João prova que o software serve **àquele**
ambiente. Não prova generalidade. O par natural é reconstituir também um ambiente do outro
domínio — o de estudos do `cenarios/02` — e ver se as mesmas peças bastam.

---

## CS-02 — Operar várias tarefas no mesmo dia

> **João Nishi:** "nesse modo de uso que eu tô pensando aqui, fica muito fácil eu **operar
> cinco, seis tasks diferentes durante o dia**."

**O critério:** o usuário toca cinco ou seis tarefas distintas num dia sem perder o fio de
nenhuma — nenhuma cai por esquecimento, e o que estava travado volta a andar sem ele precisar
lembrar.

É a resposta direta a D-10 (*"como eu garanto que faço todas?"*). É verificável por observação
num dia real de trabalho.

---

## CS-03 — O ambiente ainda vale depois de acumular

**Derivado de D-02 e P-19.** As duas camadas que dão valor de longo prazo — conteúdo da wiki e
agentes — só existem depois de uso. Logo, o produto só provou seu ponto quando alguém trabalha
nele por tempo suficiente para acumular, **e o acumulado continua correto**.

**O critério:** depois de N semanas, a wiki é lida e usada sem que ninguém precise corrigi-la
antes de confiar nela. O contraexemplo já aconteceu no arranjo manual: três meses sem ingestão,
descobertos só numa auditoria (`painel.md`, lacuna 5).

**Falta definir:** quanto é N, e como se mede "continua correto".

---

## CS-04 — A pergunta de confronto do cliente, virada contra o produto

> **João Nishi** (`por-que-esse-sistema.md`, §4): **"Isso escala ou é hora vendida?"**

Ele aplica isso a cada decisão do negócio dele. Vale aplicar a cada função do FishingRod:
**toda função que exigir manutenção manual recorrente do usuário é hora vendida disfarçada de
recurso** — e recria exatamente a dor que o produto promete resolver (D-01).

Não é um teste de aceite; é uma régua para dizer não durante o desenvolvimento.

---

## O que falta — e é a lacuna mais séria deste documento

**Nunca perguntamos ao João como *ele* saberia que valeu.** Todos os critérios acima ou são do
Pedro, ou foram derivados por mim de falas sobre outros assuntos. O bloco G do guia de leitura
(`bruto/00-guia-de-despejo.md`) — *"o que precisa ser verdade daqui a seis meses para você dizer
que valeu; que comportamento seu teria mudado; o que você teria parado de fazer"* — segue sem
resposta para a ferramenta.

É a pergunta mais barata de fazer e a que mais protege contra construir a coisa certa para o
problema errado.
