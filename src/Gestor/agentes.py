import logging
from langchain_openai import ChatOpenAI

from servicos.rag import RagService
from servicos.planilha import PlanilhaService
from servicos.erp import ErpService
from grafo.nos import NosAvaliacoes
from grafo.compilador import Compilador
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("SistemaRemuneracao")


class AgenteRH:
    """
    Orquestrador central — instancia os serviços, monta as dependências
    e entrega o grafo compilado pronto para execução.

    É o único ponto de contato que o app.py precisa conhecer.
    """

    def __init__(self):
        logger.info("Inicializando AgenteRH...")

        # Serviços de infraestrutura
        vectorstore = RagService.get_vectorstore()
        planilha_service = PlanilhaService()
        erp_service = ErpService()

        # Dependências LLM
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

        # Composição
        nos = NosAvaliacoes(
            llm=llm,
            retriever=retriever,
            planilha_service=planilha_service,
            erp_service=erp_service,
        )
        self._compilador = Compilador(nos)

        logger.info("AgenteRH inicializado com sucesso.")

    def compilar(self):
        """Retorna o grafo LangGraph compilado, pronto para execução."""
        return self._compilador.compilar()