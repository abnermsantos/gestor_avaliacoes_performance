import os
import sqlite3
from dotenv import load_dotenv
import pandas as pd
from PyPDF2 import PdfReader
from datetime import datetime
from typing import TypedDict, List

# LangChain & LangGraph
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_chroma import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough

from utils import monitorar_processo

load_dotenv()

# --- ESTADO DO AGENTE ---
class AgentState(TypedDict):
    planilha_dados: str
    politica_regras: str
    lista_bonus_inovacao: str
    funcionarios_aptos: List[str]
    resultado_final: str
    data_hoje: str
    aprovado_pelo_humano: bool
    feedback_humano: str

# --- TOOLS ---
@monitorar_processo
def extrair_planilha() -> str:
    caminho = os.getenv("CAMINHO_AVALIACOES")
    try:
        df = pd.read_excel(caminho) if caminho.endswith('.xlsx') else pd.read_csv(caminho)
        return df.to_string(index=False, float_format='{:.3f}'.format)
    except Exception as e:
        return f"Erro planilha: {e}"

@monitorar_processo
def inicializar_conhecimento():
    """Carrega o PDF na VectorStore usando os Embeddings do HuggingFace"""
    try:
        caminho = os.getenv("CAMINHO_POLITICA")
        reader = PdfReader(caminho)
        texto_completo = "\n".join([p.extract_text() for p in reader.pages])

        # Chunking: divide o PDF em partes menores
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=400, chunk_overlap=40)
        docs = text_splitter.create_documents([texto_completo])

        # Modelo Multilíngue do HuggingFace
        model_name = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
        embeddings = HuggingFaceEmbeddings(model_name=model_name)

        # Cria o banco vetorial Chroma em memória
        vectorstore = Chroma.from_documents(
            documents=docs, 
            embedding=embeddings,
            collection_name="politica_rh"
        )

        return vectorstore
    except Exception as e:
        print(f"Erro crítico na inicialização: {e}")
        return None
    
@monitorar_processo
def consultar_historico_erp(nome_funcionario: str) -> str:
    """Consulta o banco de dados e retorna o status de tempo."""
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        db_path = os.path.join(base_dir, "db", "erp_simulado.db")
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        query = """
            SELECT data_evento FROM historico_financeiro 
            WHERE nome_funcionario = ? AND tipo = 'Aumento'
            ORDER BY data_evento DESC LIMIT 1
        """
        cursor.execute(query, (nome_funcionario,))
        resultado = cursor.fetchone()
        conn.close()

        if resultado:
            data_str = resultado[0]
            data_evento = datetime.strptime(data_str, "%Y-%m-%d")
            hoje = datetime.now()
            meses = (hoje.year - data_evento.year) * 12 + (hoje.month - data_evento.month)
            
            if meses <= 12:
                return f"INAPTO (Aumento há {meses} meses)"
        
        return "APTO"
    except Exception as e:
        return f"ERRO: {e}"

def no_finalizador(state: AgentState):
    return state
    
# --- NÓ 1: IDENTIFICADOR DE BÔNUS ---
@monitorar_processo
def no_identificar_bonus(state: AgentState):
    """Analisa quem merece bônus de inovação com base na política e notas."""
    
    planilha = extrair_planilha()
    vectorstore = inicializar_conhecimento()
    retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    
    format_docs = lambda docs: "\n\n".join(d.page_content for d in docs)
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", """Você é um Analista de Recompensas. Sua tarefa é IDENTIFICAR APENAS quem deve receber o BÔNUS DE INOVAÇÃO.
                        REGRAS DA POLÍTICA:
                        {contexto_politica}
                        
                        DADOS DOS FUNCIONÁRIOS:
                        {planilha}
                        
                        INSTRUÇÃO:
                        1. Localize na política os critérios para "Bônus".
                        2. Liste os funcionários que atendem a esses critérios específicos."""),
            ("human", "{query}")
        ]
    )

    pergunta = "Quem merece bônus por inovação?"
    cadeia = (
        {
            "query": RunnablePassthrough(),
            "contexto_politica": RunnablePassthrough() | retriever | format_docs,
            "planilha": lambda x: planilha
        } 
        | prompt 
        | llm 
        | StrOutputParser() 
    )

    resposta = cadeia.invoke(pergunta)
    return {
        "planilha_dados": planilha, 
        "lista_bonus_inovacao": resposta
    }

# --- NÓ 2: FILTRO DE COMPLIANCE ---
@monitorar_processo
def no_filtro_compliance(state: AgentState):
    """Varre a planilha e separa quem pode ou não receber aumento pelo tempo de casa."""
    
    from io import StringIO
    df = pd.read_csv(StringIO(state["planilha_dados"]), sep=r"\s{2,}", engine='python')
    
    funcionarios_aptos = []
    for nome in df['Nome']:
        status = consultar_historico_erp(nome)
        if status == "APTO":
            funcionarios_aptos.append(nome)
    
    df_filtrado = df[df['Nome'].isin(funcionarios_aptos)]
    planilha_somente_aptos = df_filtrado.to_string(index=False, float_format='{:.3f}'.format)

    return {
        "planilha_dados": planilha_somente_aptos
    }

# --- NÓ 3: ANALISTA DE MÉRITO ---
@monitorar_processo
def no_analista_merito(state: AgentState):
    """Aplica os critérios exatos de nota do PDF apenas nos funcionários aprovados pelo compliance."""
    
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    vectorstore = inicializar_conhecimento()
    retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
    
    format_docs = lambda docs: "\n\n".join(d.page_content for d in docs)
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", """Você é um Especialista em Remuneração. Sua tarefa é criar uma LISTA DE APTOS AO AUMENTO SALARIAL.
                        REGRAS DA POLÍTICA (Extraia a nota de corte aqui):
                        {contexto_merito}
                        
                        DADOS DE PERFORMANCE (Use as notas reais sem aproximação):
                        {planilha_dados}
                        
                        INSTRUÇÕES:
                        1. Liste APENAS o nome e a Média Final de quem atingiu ou superou o critério da politica_regras.
                        2. Use precisão de 3 casas decimais e NÃO aplique arredondamentos e truncamentos 
                        (Por exemplo: 4.499 NÃO é 4.500). 
                        3. Se ninguém atingir o critério, retorne "Nenhum funcionário elegível para aumento neste ciclo".
                        4. NÃO mencione exclusões, inaptos ou justificativas de quem ficou de fora.
                        5. Formate como uma lista limpa: "Nome - Média: X.XXX"
                        """
            ),
            ("human", "{query}")
        ]
    ) 
    
    pergunta = "Quem merece aumento salarial por performance?"
    cadeia = (
        {
            "query": RunnablePassthrough(),
            "contexto_merito": RunnablePassthrough() | retriever | format_docs,
            "planilha_dados": lambda x: state["planilha_dados"]
        } 
        | prompt 
        | llm 
        | StrOutputParser() 
    )

    resposta = cadeia.invoke(pergunta)
    return {"resultado_final": resposta}

# --- CONFIGURAÇÃO DO GRAFO ---
def cria_grafo_avaliacoes():
    workflow = StateGraph(AgentState)
    
    workflow.add_node("identificador_bonus", no_identificar_bonus)
    workflow.add_node("filtro_compliance", no_filtro_compliance)
    workflow.add_node("analista_merito", no_analista_merito)
    workflow.add_node("finalizador", no_finalizador)
    
    workflow.set_entry_point("identificador_bonus")
    
    workflow.add_edge("identificador_bonus", "filtro_compliance")
    workflow.add_edge("filtro_compliance", "analista_merito")
    workflow.add_edge("analista_merito", "finalizador")
    workflow.add_edge("finalizador", END)
    
    memory = MemorySaver()
    return workflow.compile(checkpointer=memory, interrupt_before=["finalizador"])