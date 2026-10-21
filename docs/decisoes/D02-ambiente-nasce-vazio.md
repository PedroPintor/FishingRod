# D02 — O ambiente nasce vazio, sem frente

Status: revisada
Data do status: 2026-10-20

## O que é

Criar um ambiente não cria nenhuma frente automaticamente. A primeira frente também é criada
pelo usuário. É a tela que ajuda o usuário a ter onde trabalhar logo depois de criar o ambiente.

## Por quê

O código antigo criava uma frente padrão (`projeto-padrao`) só porque, sem ela, o programa
quebrava ao procurar "a frente ativa" pela posição numa lista. Com a identidade única de cada
coisa (ver [D05](D05-nomes-repetidos-identidade-unica.md)), esse motivo deixou de existir. Assim
nada é criado sem o usuário pedir, e o nome da frente padrão não vira uma decisão escondida no
código. O Pedro acrescentou: existe uma tela de início, onde se escolhe ou cria um ambiente, e é a
tela que conduz a criação de frentes.

## Onde aparece no código

- `src/fishingrod/dominio/ambiente.py`
- `src/fishingrod/aplicacao/servicos/servico_de_ambiente.py` (`criar_ambiente`)
