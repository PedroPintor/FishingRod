# D19 — O núcleo não depende do Claude; o SDK fica só no adaptador

Status: revisada
Data do status: 2026-10-20

## O que é

O FishingRod é agnóstico à IA usada. O Claude (pelo `claude-agent-sdk`) é o primeiro adaptador, não
uma amarra. Só a pasta do adaptador de sessão importa o SDK. O núcleo (domínio e aplicação)
conversa com qualquer IA pela mesma interface de "sessão viva": abrir, enviar mensagem, fechar.

## Por quê

A intenção do produto é não prender o usuário a uma IA. O que não pode mudar é a forma da porta:
uma sessão viva. Uma IA que responde pedido a pedido consegue imitar uma sessão guardando o
histórico; o contrário não funciona. Manter o SDK fora do núcleo também permite testar o núcleo
sem internet e sem credencial, e impede que uma falha do provedor se espalhe pelo programa.

## Onde aparece no código

- `src/fishingrod/aplicacao/portas/sessao.py` (a interface de sessão viva)
- `src/fishingrod/adaptadores/sessao/` (o único lugar que importa o SDK)
- `tests/sessao/test_fronteira.py` e `tests/dominio/test_fronteira.py` (provam que o núcleo importa sem o SDK)
