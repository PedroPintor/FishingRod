# D06 — Tudo local: cada pessoa na própria máquina, com a própria assinatura

Status: revisada
Data do status: 2026-10-20

## O que é

O FishingRod roda na máquina de quem usa. Os dados (banco e wikis) ficam numa pasta do próprio
computador. Não há servidor, nuvem nem conta compartilhada: cada pessoa usa o programa com a
própria assinatura do Claude.

## Por quê

Nesta fase o software é para uma pessoa só; uso em time, nuvem e implantação ficaram de fora de
propósito. Rodar local é o mais simples de construir e de testar. E uma credencial nunca serve a
mais de uma pessoa: cada um paga e usa a sua assinatura. O desenho evita fechar a porta para uma
wiki compartilhada no futuro (a wiki é endereçada por caminho relativo, nunca absoluto), mas não
constrói nada disso agora.

## Onde aparece no código

- `src/fishingrod/adaptadores/persistencia/localizacao.py` (a pasta de dados do sistema: no Windows, `%LOCALAPPDATA%\FishingRod`)
- `src/fishingrod/dominio/raiz_wiki.py`
