from typing import TypedDict


class AgentState(TypedDict):
    planilha_dados: str        # DataFrame serializado (passagem entre nós)
    lista_bonus_inovacao: str  # saída do nó identificador_bonus
    resultado_final: str       # saída do nó analista_merito
    data_hoje: str             # data de execução