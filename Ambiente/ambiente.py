from dataclasses import dataclass, field

from Ambiente.sessao import (
    Sessao,
    Chat,   
    Memoria
)
from Ambiente.agente import OrquestradorTeste
from model.comando import Comando
from model.mensagem import Mensagem

COMANDOS_AMBIENTE = [Comando.PROJETOS,Comando.NOVO_PROJETO,Comando.TROCAR_PROJETO,Comando.AJUDA,Comando.SAIR]
COMANDOS_PROJETO = [Comando.SESSOES,Comando.NOVA_SESSAO,Comando.TROCAR_SESSAO]

NOME_PROJETO_PADRAO = "projeto-padrao"

@dataclass
class Projeto:
    nome: str                              
    wiki_local: str = "wiki local....."
    sessoes: list[Sessao] = field(default_factory=list)
    indice_ativo: int = 0

    @property
    def sessao(self) -> Sessao:
        return self.sessoes[self.indice_ativo]

    def __post_init__(self):
            if len(self.sessoes) < 1:
                self.criar_sessao(f"{self.nome}-sessao")

    def trocar_sessao(self, indice: int) -> bool:
        if not 0 <= indice < len(self.sessoes):
            return False
        self.indice_ativo = indice
        return True

    def _buscar_sessao(self, nome: str) -> Sessao | None:
        for s in self.sessoes:
            if s.nome == nome:
                return s
        return None
    
    def criar_sessao(self, nome: str) -> Sessao | None:
        if not self._buscar_sessao(nome):
            s = Sessao(chats=[Chat(agente=OrquestradorTeste)],memoria=Memoria(),nome=nome)
            self.sessoes.append(s)
            return s
        return None

    def listar_sessoes(self) -> list[str]:
        return [s.nome for s in self.sessoes]

    def obter_status(self) -> dict:
            # cada andar acrescenta o proprio nome e delega o resto.
            # nao e repasse: e composicao.
            return {"nome_projeto": self.nome, **self.sessao.obter_status()}

    def _detectar_comando_projeto(self, mensagem: str) -> bool:
        if not mensagem.startswith("/"):
            return False
        try:
            return Comando(mensagem.split()[0]) in COMANDOS_PROJETO
        except ValueError:
            return False

    def _acionar_comando(self, mensagem: str) -> str:
        # so chega aqui comando que passou pelo _detectar_comando_projeto,
        # entao Comando(...) nao pode falhar
        m = mensagem.split()
        comando = m[0]
        valor = m[1] if len(m) > 1 else None

        c = Comando(comando)
        match c:
            case Comando.SESSOES:
                return "\n".join(
                    f"{'*' if i == self.indice_ativo else ' '} [{i}] {nome}"
                    for i, nome in enumerate(self.listar_sessoes())
                )
            case Comando.NOVA_SESSAO:
                if not valor:
                    return f"Erro - Uso: {Comando.NOVA_SESSAO.value} <nome>"
                if not self.criar_sessao(valor):
                    return f"Sessao [{valor}] ja existe - Tente outro nome"
                return f"Sessao [{valor}] criada"
            case Comando.TROCAR_SESSAO:
                if not valor:
                    return f"Erro - Uso: {Comando.TROCAR_SESSAO.value} <indice>"
                try:
                    indice = int(valor)
                except ValueError:
                    return "Erro - Digite um numero referente ao indice da Sessao"
                if not self.trocar_sessao(indice):
                    return f"Erro - Sessao indice [{valor}] nao existe (sessoes: 0 a {len(self.sessoes) - 1})"
                return f"Sessao ativa: [{valor}] {self.sessao.nome}"
            case _:
                raise ValueError(f"{c} esta em COMANDOS_PROJETO mas nao tem case em Projeto._acionar_comando")


    def enviar(self, mensagem: str) -> list[Mensagem]:
        if self._detectar_comando_projeto(mensagem=mensagem):
            return [Mensagem(autor="comando",tipo="sistema",texto=self._acionar_comando(mensagem))]
        return self.sessao.enviar(mensagem)

    


@dataclass
class Ambiente:
    nome: str
    projetos: list[Projeto] = field(default_factory=list)
    indice_ativo: int = 0
    ativo: bool = True

    @property
    def projeto(self) -> Projeto:
        return self.projetos[self.indice_ativo]

    def __post_init__(self):
        # um Ambiente sem projeto nenhum nao consegue responder nada:
        # self.projeto estoura IndexError. Mesma defesa que o Projeto faz
        # com as sessoes - o usuario sempre esta em algum lugar.
        if len(self.projetos) < 1:
            self.criar_projeto(NOME_PROJETO_PADRAO)

    def trocar_projeto(self, indice: int) -> bool:
        if not 0 <= indice < len(self.projetos):
            return False
        self.indice_ativo = indice
        return True

    def buscar_projeto(self, nome:str) -> tuple[int,Projeto] | None:
            for i, p in enumerate(self.projetos):
                if p.nome == nome:
                    return i,p
            return None
    
    def criar_projeto(self, nome: str) -> Projeto | None:
        if not self.buscar_projeto(nome):
            p = Projeto(nome=nome)
            self.projetos.append(p)
            return p
        return None

    def listar_projetos(self) -> list[str]:
        return [p.nome for p in self.projetos]

    def obter_status(self) -> dict:
        return {"nome_ambiente": self.nome, **self.projeto.obter_status()}

    def _detectar_comando_ambiente(self, mensagem: str) -> bool:
        if not mensagem.startswith("/"):
            return False
        try:
            return Comando(mensagem.split()[0]) in COMANDOS_AMBIENTE
        except ValueError:
            return False

    def _acionar_comando(self, mensagem: str) -> str:
        # so chega aqui comando que passou pelo _detectar_comando_ambiente,
        # entao Comando(...) nao pode falhar
        m = mensagem.split()
        comando = m[0]
        valor = m[1] if len(m) > 1 else None

        c = Comando(comando)
        match c:
            case Comando.AJUDA:
                return "\n".join(cmd.value for cmd in Comando)

            case Comando.SAIR:
                self.ativo = False
                return "Encerrando Ambiente..."

            case Comando.PROJETOS:
                return "\n".join(
                    f"{'*' if i == self.indice_ativo else ' '} [{i}] {nome}"
                    for i, nome in enumerate(self.listar_projetos())
                )
            case Comando.NOVO_PROJETO:
                if not valor:
                    return f"Erro - Uso: {Comando.NOVO_PROJETO.value} <nome>"
                if not self.criar_projeto(valor):
                    return f"Projeto [{valor}] ja existe - Tente outro nome"
                return f"Projeto [{valor}] criado"
            case Comando.TROCAR_PROJETO:
                if not valor:
                    return f"Erro - Uso: {Comando.TROCAR_PROJETO.value} <indice>"
                try:
                    indice = int(valor)
                except ValueError:
                    return "Erro - Digite um numero referente ao indice do Projeto"
                if not self.trocar_projeto(indice):
                    return f"Erro - Projeto indice [{valor}] nao existe (projetos: 0 a {len(self.projetos) - 1})"
                return f"Projeto ativo: [{valor}] {self.projeto.nome}"
            case _:
                raise ValueError(f"{c} esta em COMANDOS_AMBIENTE mas nao tem case em Ambiente._acionar_comando")


    def enviar(self, mensagem: str) -> list[Mensagem]:
        if self._detectar_comando_ambiente(mensagem):
            return [Mensagem(autor="comando",tipo="sistema",texto=self._acionar_comando(mensagem))]
        return self.projeto.enviar(mensagem)

    

