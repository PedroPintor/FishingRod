# D18 — No chat, texto que começa com / é comando; o resto vai para o agente

Status: revisada
Data do status: 2026-10-20

## O que é

No campo de mensagem, o que começa com `/` é um comando direto para o software (por exemplo,
`/criar_frente Comercial`), executado sem passar pela IA. Qualquer outro texto é mensagem para o
agente do chat.

## Por quê

É o jeito de trabalhar do Claude Code, que o usuário de validação já usa, e está na maquete do João
(paleta de comandos com `/`). Os comandos vêm de um catálogo único de ações: a mesma regra serve à
barra `/`, a botões e atalhos, e às ferramentas do orquestrador
([D15](D15-orquestrador-age-com-confirmacao.md)). Assim a regra mora num lugar só.

## Onde aparece no código

- `src/fishingrod/aplicacao/catalogo/parser.py` (separa o nome do comando do resto do texto)
- `src/fishingrod/aplicacao/catalogo/catalogo.py`, `registro.py`, `argumentos.py`
- O campo de mensagem que faz essa separação na tela ainda não existe.
