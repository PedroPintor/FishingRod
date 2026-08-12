from enum import Enum

class Comando(Enum):
    AJUDA = "/ajuda"
    SAIR = "/sair"
    # ambiente
    NOVO_PROJETO = "/novo-projeto"
    PROJETOS = "/projetos"
    TROCAR_PROJETO = "/trocar-projeto"
    # projeto
    SESSOES = "/sessoes"
    NOVA_SESSAO = "/nova-sessao"
    TROCAR_SESSAO = "/trocar-sessao"
    #sessao
    CHATS = "/chats"
    AGENTES = "/agentes"
    NOME_CHAT = "/nome-chat"
    NOVO_CHAT = "/novo-chat"
    TROCAR_CHAT = "/trocar-chat"


