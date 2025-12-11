from enum import Enum

class StatusAtivo(str, Enum):
    alugado = "alugado"
    vazio = "vazio"

class TipoAtivo(str, Enum):
    comercial = "comercial"
    direitos = "direitos"
    hotelaria = "hotelaria"
    loteamento = "loteamento"
    residencial = "residencial"
    terreno = "terreno"

class FinalidadeAtivo(str, Enum):
    condohotel = "condohotel"
    direitos = "direitos"
    locacao = "locacao"
    locacao_incorporacao = "locacao_incorporacao"
    locacao_projeto = "locacao_projeto"
    locacao_venda = "locacao_venda"
    uso = "uso"
    venda = "venda"

class GrauDesmobilizacaoAtivo(str, Enum):
    facil = "facil"
    moderado = "moderado"
    dificil = "dificil"

class PotencialAtivo(str, Enum):
    baixo = "baixo"
    medio = "medio"
    medio_alto = "medio_alto"
    alto = "alto"
