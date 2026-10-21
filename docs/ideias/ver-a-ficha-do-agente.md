# Ver a ficha do agente

Estado: em aprofundamento, para virar o card 003
De onde veio: conversa do Pedro com a IA sobre o próximo card, em 2026-10-21. Faz parte de
[organizar a interface em áreas](organizar-a-interface-em-areas.md).

Abro a ficha de um agente (o orquestrador, o bibliotecário) e vejo o que ele é. Quando ele faz
algo que eu não esperava, a ficha me dá a pista do porquê.

A ficha tem duas partes:

- **Configuração:** o que o agente pode e não pode fazer, e com que modelo. É aqui que entendo
  por que o meu orquestrador não pode fazer tal ação.
- **Instruções:** o texto que o agente recebe dizendo como trabalhar. É um prompt.

Quem pode mexer em cada parte depende do agente:

| Agente | Configuração | Instruções |
|---|---|---|
| Orquestrador | fixa: é do software, e as opções dele já foram pensadas | o usuário escreve, para o orquestrador fazer sentido naquele ambiente |
| Bibliotecário | fixa | fixa: ele é a solução do software para cuidar da wiki; se o usuário mexer nele, o software perde o controle de como a wiki é cuidada |
| Os outros agentes | o usuário escolhe numa lista do que é permitido, que o software oferece | o usuário escreve, seguindo um modelo base (ver [formato de agente](formato-de-agente.md)) |

Talvez o bibliotecário nem precise aparecer. Revisar mais para a frente se a configuração do
orquestrador deve mesmo ser fixa.

O que já existe no código: cada agente tem nome, papel, modelo, ferramentas e regras
(`src/fishingrod/dominio/agente.py`), e os dois agentes de hoje são montados em
`src/fishingrod/interface/montagem.py`. As regras viram as instruções que o Claude recebe
(`system_prompt` em `src/fishingrod/adaptadores/sessao/opcoes.py`). Hoje nenhum dos dois agentes
tem instruções escritas: o orquestrador age só com o que o modelo já sabe e com a descrição das
ações que pode pedir.

Relacionada: [escrever as instruções do orquestrador](escrever-instrucoes-do-orquestrador.md).
