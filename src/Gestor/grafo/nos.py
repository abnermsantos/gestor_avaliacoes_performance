import logging
import re
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

    def _parse_tempo_minimo(self, resposta: str) -> int:
        """Extrai o primeiro número inteiro da resposta do LLM."""
        
        resposta = resposta.strip()
        match = re.search(r'\d+', resposta)
        return int(match.group()) if match else 0

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
        """Filtra funcionários inaptos por tempo (definido na política) via consulta ao ERP."""

        prompt = ChatPromptTemplate.from_messages([
            ("system", """Você é um Analista de Compliance especialista em interpretar políticas de RH.
                Sua tarefa é extrair o critério de tempo mínimo entre aumentos salariais e retorná-lo em meses.

                REGRAS DA POLÍTICA:
                {contexto_politica}

                REGRAS DE CONVERSÃO OBRIGATÓRIAS:
                - "1 ano" ou "um ano" ou "no último ano" → 12
                - "2 anos" ou "dois anos" → 24
                - "6 meses" ou "seis meses" → 6
                - "1 ano e meio" ou "18 meses" → 18
                - Qualquer variação textual de tempo DEVE ser convertida para o número inteiro de meses.
                - Se não houver critério de tempo definido → 0

                INSTRUÇÕES:
                1. Localize na política o critério de tempo entre aumentos salariais.
                2. Converta o tempo encontrado para meses usando as regras acima.
                3. Retorne SOMENTE o número inteiro, sem texto, sem unidade, sem pontuação.
                
                EXEMPLOS DE SAÍDA ESPERADA:
                Política diz "12 meses"           → 12
                Política diz "1 ano"              → 12
                Política diz "no último ano"      → 12
                Política diz "a cada dois anos"   → 24
                Política diz "semestralmente"     → 6
                Política não menciona tempo       → 0"""),
            ("human", "{query}"),
        ])

        cadeia = (
            {
                "query": RunnablePassthrough(),
                "contexto_politica": RunnablePassthrough() | self._retriever | self._format_docs,
            }
            | prompt
            | self._llm
            | StrOutputParser()
        )

        resposta = cadeia.invoke("Qual o tempo mínimo para um funcionário ser elegível a um novo aumento salarial?")
        tempo_minimo = self._parse_tempo_minimo(resposta)

        df = self._planilha.de_string(state["planilha_dados"])

        aptos = [
            nome for nome in df["Nome"]
            if self._erp.verificar_elegibilidade(nome, tempo_minimo) == "APTO"
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