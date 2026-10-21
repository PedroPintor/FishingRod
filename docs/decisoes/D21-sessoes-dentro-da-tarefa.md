# D21 — A tarefa tem sessões, e os chats moram na sessão

Status: revisada
Data do status: 2026-10-21

## O que é

Os níveis são: ambiente → frente → tarefa → **sessão** → chat. Uma tarefa pode ter várias sessões;
na tarefa, eu crio uma sessão nova ou escolho uma que já existe. Dentro da sessão ficam os chats,
e o primeiro é sempre o do orquestrador.

- A tarefa já nasce com uma sessão, com o chat do orquestrador.
- Toda sessão nova também nasce com o chat do orquestrador, e nunca tem dois.
- Uma sessão sem nome se chama "sessão 1", "sessão 2"… pela posição dela na tarefa.
- A **memória** (o quadro branco entre os agentes, [D17](D17-memoria-e-quadro-branco.md)) é de cada
  sessão: uma sessão nova começa com a memória limpa.
- As **etapas** continuam sendo da tarefa: o plano é um só, e cada sessão é um momento de
  trabalhar nele.
- Só o usuário abre sessão nova. O orquestrador não recebe essa ação como ferramenta.

## Por quê

Foi como o Pedro descreveu o trabalho, na conversa sobre a primeira tela: numa mesma tarefa, ele
volta várias vezes, e cada vez abre uma sessão, com os chats daquela vez. O código antigo já tinha
um nível chamado `Sessao`, mas ele ocupava o lugar da tarefa; o novo nível fica entre a tarefa e o
chat.

A memória ficou na sessão porque é o quadro branco dos agentes que estão trabalhando juntos
naquele momento. As etapas ficaram na tarefa porque o plano não recomeça a cada sessão. Abrir
sessão ficou só com o usuário porque o agente vive dentro de uma sessão, e decidir quando começar
outra é de quem está trabalhando.

A "sessão" desta decisão não é a `SessaoViva` do código, que é a conexão aberta com o Claude para
um chat.

## Onde aparece no código

- `src/fishingrod/dominio/sessao.py` (a `Sessao`, com os chats e a memória)
- `src/fishingrod/dominio/tarefa.py` (`criar_sessao`, `buscar_sessao`; as etapas ficam aqui)
- `src/fishingrod/aplicacao/servicos/servico_de_ambiente.py` (`criar_sessao`; `criar_chat` e
  `anotar_memoria` recebem o id da sessão)
- `src/fishingrod/aplicacao/catalogo/registro.py` (a ação `criar_sessao`, só do usuário; `criar_chat`
  e `anotar_memoria` com escopo de sessão)
- `src/fishingrod/adaptadores/persistencia/` (o documento guarda as sessões; a tabela `anotacao`
  guarda o id da sessão)
