import logging
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from grafo.state import AgentState
from grafo.nos import NosAvaliacoes

logger = logging.getLogger("SistemaRemuneracao")


class Compilador:
    """
    Responsável exclusivamente por montar a topologia do grafo.
    Não conhece LLM, retriever ou serviços — só sabe ligar nós.
    """

    def __init__(self, nos: NosAvaliacoes):
        self._nos = nos

    def compilar(self) -> StateGraph:
        """Monta edges, nodes e checkpointer. Retorna o grafo compilado."""
        workflow = StateGraph(AgentState)

        workflow.add_node("identificador_bonus", self._nos.identificar_bonus)
        workflow.add_node("filtro_compliance", self._nos.filtro_compliance)
        workflow.add_node("analista_merito", self._nos.analista_merito)
        workflow.add_node("finalizador", self._nos.finalizador)

        workflow.set_entry_point("identificador_bonus")

        workflow.add_edge("identificador_bonus", "filtro_compliance")
        workflow.add_edge("filtro_compliance", "analista_merito")
        workflow.add_edge("analista_merito", "finalizador")
        workflow.add_edge("finalizador", END)

        logger.info("Grafo compilado com sucesso.")
        return workflow.compile(
            checkpointer=MemorySaver(),
            interrupt_before=["finalizador"],
        )