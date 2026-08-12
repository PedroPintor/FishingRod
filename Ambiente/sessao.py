from dataclasses import dataclass, field

from Ambiente.agente import (
    Agente, 
    Papel,
    AgenteDoSistema
)
from Ambiente.memoria import Memoria
from model.comando import Comando
from model.mensagem import Mensagem


@dataclass
class Chat:
    agente: Agente
    mensagens: list[Mensagem] = field(default_factory=list)
    nome: str = None
    iteracoes: int = 0

    def __post_init__(self):
        if not self.nome:
            self.nome = self.agente.nome

    def adicionar_iteracao(self) -> None:
          self.iteracoes += 1

@dataclass
class Sessao:
    nome: str
    chats: list[Chat] = field(default_factory=list)
    memoria: Memoria = field(default_factory=Memoria)
    indice_ativo: int = 0

    @property
    def chat(self) -> Chat:
        return self.chats[self.indice_ativo]

    def _contar_orquestradores(self) -> int:
        return sum(1 for c in self.chats if c.agente.papel == Papel.ORQUESTRADOR)
    

    def __post_init__(self):
        if self._contar_orquestradores() > 1:
            raise ValueError("Sessao não pode conter mais de um Agente com papel ORQUESTRADOR.")

    def obter_status(self) -> dict:
        return{
            "nome_sessao":  self.nome,
            "n_iteracoes":  self.chat.iteracoes,
            "nome_chat":    self.chat.nome,
            "memoria":      self.memoria.anotacoes,
        }

    def trocar_chat(self, indice: int) -> bool:
        if not 0 <= indice < len(self.chats):
            return False
        self.indice_ativo = indice
        return True

    def listar_agentes(self) -> list[Agente]:
        return list(AgenteDoSistema)


    def buscar_agente(self, nome:str) -> Agente | None:
        for g in AgenteDoSistema:
            if g.nome == nome:
                return g
        return None

    def criar_chat(self, agente: Agente) -> bool:
        if agente.papel == Papel.ORQUESTRADOR and self._contar_orquestradores() >= 1:
            return False
        self.chats.append(Chat(agente=agente))
        return True
        
    def _detectar_comando(self, mensagem: str) -> bool:
        # A Sessao e o ultimo andar da cadeia. Os andares de cima perguntam
        # "esse comando e meu?" porque eles podem passar adiante. Aqui nao tem
        # para quem passar: se parece comando, e responsabilidade dela - inclusive
        # dizer que nao conhece.
        return mensagem.startswith("/")

    def _acionar_comando(self, mensagem: str) -> str:
        m = mensagem.split()
        comando_str = m[0]

        try:
            comando = Comando(comando_str)
        except ValueError:
            return f"Erro - comando desconhecido: {comando_str} (veja: {Comando.AJUDA.value})"

        match comando:

            case Comando.NOME_CHAT:
                if len(m) < 2:
                    return f"Erro - Uso:{Comando.NOME_CHAT.value} <novo nome>"
                self.chat.nome = m[1]
                return f"Renomeado para: {m[1]}"
 
            case Comando.NOVO_CHAT:
                if len(m) < 2:
                    return f"Erro - Uso: {Comando.NOVO_CHAT.value} <agente>"
                agente = self.buscar_agente(m[1])
                if agente is None:
                    return f"Erro - SubAgente {m[1]} nao existe. (Veja: {Comando.AGENTES.value})"
                if not self.criar_chat(agente=agente):
                    return "Erro - a sessao ja tem um orquestrador"
                return f"Novo chat criado: [{len(self.chats) - 1}] {self.chats[-1].nome}"

            case Comando.CHATS:
                return "\n".join(
                    f"{'*' if i == self.indice_ativo else ' '} [{i}] {c.nome}[{c.agente.papel.value}]"
                    for i, c in enumerate(self.chats)
                )

            case Comando.TROCAR_CHAT:
                if len(m) < 2:
                    return f"Erro - Uso:{Comando.TROCAR_CHAT.value} <indice>"
                try:
                    indice = int(m[1])
                except ValueError:
                    return f"Erro - '{m[1]}' nao e um numero"
                if not self.trocar_chat(indice):
                    return f"Erro - Indice {indice} nao existe (chats: 0 a {len(self.chats) - 1})"
                return f"Chat ativo: [{indice}] {self.chat.nome}"

            case Comando.AGENTES:
                agentes = self.listar_agentes()
                return "\n".join(f"{a.nome} ({a.papel.value})" for a in agentes)

            case _:
                # comando que existe no Enum mas ninguem na cadeia atende
                return f"Erro - comando desconhecido: {comando_str} (veja: {Comando.AJUDA.value})"

    def enviar(self, mensagem: str) -> list[Mensagem]:
        chat = self.chat
        novas_mensagens = [Mensagem("<NOME_USUARIO>", mensagem, "usuario")]
        if self._detectar_comando(mensagem):
            novas_mensagens.append(Mensagem('comando', self._acionar_comando(mensagem), "sistema"))
        else:
            novas_mensagens.append(Mensagem(chat.agente.caixa_de_texto, chat.agente.responder(mensagem), "agente"))
        chat.mensagens.extend(novas_mensagens)
        chat.adicionar_iteracao()
        return novas_mensagens




