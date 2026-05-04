import logging
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_chroma import Chroma

from grafo.state import AgentState
from servicos.planilha import PlanilhaService
from servicos.erp import ErpService
from utils import monitorar_processo

logger = logging.getLogger("SistemaRemuneracao")


class NosAvaliacoes:
    """
    Contém os nós do grafo de avaliações.
    Recebe dependências injetadas — não sabe como o grafo é montado.
    """

    def __init__(
        self,
        llm: ChatOpenAI,
        retriever,
        planilha_service: PlanilhaService,
        erp_service: ErpService,
    ):
        self._llm = llm
        self._retriever = retriever
        self._planilha = planilha_service
        self._erp = erp_service
        self._format_docs = lambda docs: "\n\n".join(d.page_content for d in docs)

    # -----------------------------------------------------------------------
    # NÓ 1 — Identificador de Bônus
    # -----------------------------------------------------------------------

    @monitorar_processo
    def identificar_bonus(self, state: AgentState) -> dict:
        """Analisa quem merece bônus de inovação com base na política e notas."""
        
        df = self._planilha.carregar()
        planilha_str = self._planilha.para_string(df)

        prompt = ChatPromptTemplate.from_messages([
            ("system", """Você é um Analista de Recompensas. Sua tarefa é IDENTIFICAR APENAS quem deve receber o BÔNUS DE INOVAÇÃO.
                REGRAS DA POLÍTICA:
                {contexto_politica}

                DADOS DOS FUNCIONÁRIOS:
                {planilha}

                INSTRUÇÃO:
                1. Localize na política os critérios para "Bônus".
                2. Liste os funcionários que atendem a esses critérios específicos."""),
            ("human", "{query}"),
        ])

        cadeia = (
            {
                "query": RunnablePassthrough(),
                "contexto_politica": RunnablePassthrough() | self._retriever | self._format_docs,
                "planilha": lambda x: planilha_str,
            }
            | prompt
            | self._llm
            | StrOutputParser()
        )

        resposta = cadeia.invoke("Quem merece bônus por inovação?")
        return {
            "planilha_dados": planilha_str,
            "lista_bonus_inovacao": resposta,
        }

    # -----------------------------------------------------------------------
    # NÓ 2 — Filtro de Compliance
    # -----------------------------------------------------------------------

    @monitorar_processo
    def filtro_compliance(self, state: AgentState) -> dict:
        """Filtra funcionários inaptos por tempo via consulta ao ERP."""
        
        df = self._planilha.de_string(state["planilha_dados"])

        aptos = [
            nome for nome in df["Nome"]
            if self._erp.verificar_elegibilidade(nome) == "APTO"
        ]

        df_filtrado = df[df["Nome"].isin(aptos)]
        return {
            "planilha_dados": self._planilha.para_string(df_filtrado)
        }

    # -----------------------------------------------------------------------
    # NÓ 3 — Analista de Mérito
    # -----------------------------------------------------------------------

    @monitorar_processo
    def analista_merito(self, state: AgentState) -> dict:
        """Aplica critérios da política apenas nos funcionários aprovados pelo compliance."""
        prompt = ChatPromptTemplate.from_messages([
            ("system", """Você é um Especialista em Remuneração. Sua tarefa é criar uma LISTA DE APTOS AO AUMENTO SALARIAL.
                REGRAS DA POLÍTICA (Extraia a nota de corte aqui):
                {contexto_merito}

                DADOS DE PERFORMANCE (Use as notas reais sem aproximação):
                {planilha_dados}

                INSTRUÇÕES:
                1. Liste APENAS o nome e a Média Final de quem atingiu ou superou o critério da política.
                2. Use precisão de 3 casas decimais e NÃO aplique arredondamentos ou truncamentos
                (Por exemplo: 4.499 NÃO é 4.500).
                3. Se ninguém atingir o critério, retorne "Nenhum funcionário elegível para aumento neste ciclo".
                4. NÃO mencione exclusões, inaptos ou justificativas de quem ficou de fora.
                5. Formate como uma lista limpa: "Nome - Média: X.XXX"
                """),
            ("human", "{query}"),
        ])

        cadeia = (
            {
                "query": RunnablePassthrough(),
                "contexto_merito": RunnablePassthrough() | self._retriever | self._format_docs,
                "planilha_dados": lambda x: state["planilha_dados"],
            }
            | prompt
            | self._llm
            | StrOutputParser()
        )

        resposta = cadeia.invoke("Quem merece aumento salarial por performance?")
        return {"resultado_final": resposta}

    # -----------------------------------------------------------------------
    # NÓ 4 — Finalizador
    # -----------------------------------------------------------------------

    def finalizador(self, state: AgentState) -> AgentState:
        """Nó de passagem — suporta o interrupt_before do human-in-the-loop."""
        return state