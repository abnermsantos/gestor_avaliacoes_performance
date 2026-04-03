import os
import sqlite3
from langchain_openai import ChatOpenAI
import pandas as pd
from PyPDF2 import PdfReader
from langchain.agents import create_agent
from langchain_core.tools import tool
from utils import monitorar_tool

from datetime import datetime


@tool
@monitorar_tool
def get_planilha_avaliacoes() -> str:
    """Lê as notas de desempenho: Nome, Cargo, Área, Média final e competências específicas."""
    
    caminho_planilha = os.getenv("CAMINHO_AVALIACOES")
    if not caminho_planilha:
        return "Erro: A variável CAMINHO_AVALIACOES não foi encontrada no .env"
    
    try:
        if caminho_planilha.endswith('.csv'):
            df = pd.read_csv(caminho_planilha)
        else:
            df = pd.read_excel(caminho_planilha)
        
        df = df.sort_values(by="Média final", ascending=False)
        return df.to_string(index=False, float_format='{:.3f}'.format)
        
    except Exception as e:
        return f"Erro ao ler a planilha: {str(e)}"

@tool
@monitorar_tool
def get_politica_remuneracao()-> str:
    """Lê o documento PDF que contém as regras, critérios de aumento salarial e políticas de remuneração da empresa."""

    caminho_pdf = os.getenv("CAMINHO_POLITICA")
    if not caminho_pdf:
        return "Erro: A variável CAMINHO_POLITICA não foi configurada no .env"
    
    if not os.path.exists(caminho_pdf):
        return f"Erro: O arquivo PDF não foi encontrado em: {caminho_pdf}"

    try:
        reader = PdfReader(caminho_pdf)
        texto_completo = ""
        
        for page in reader.pages:
            texto_completo += page.extract_text() + "\n"
        
        return texto_completo if texto_completo.strip() else "O PDF está vazio ou não possui texto extraível."
        
    except Exception as e:
        return f"Erro ao ler o PDF da política: {str(e)}"

@tool
@monitorar_tool
def get_historico_erp(nome_funcionario: str) -> str:
    """
    Consulta o histórico de aumentos e bônus de um funcionário no banco SQLite em src/gestor/db.
    Use isto para verificar a data do último aumento e validar a regra de 12 meses.
    """
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        db_path = os.path.join(base_dir, "db", "erp_simulado.db")
        
        if not os.path.exists(db_path):
            return f"Erro: Arquivo não encontrado em {db_path}. Verifique se rodou o setup_db.py"
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Busca o último aumento salarial
        query = """
            SELECT tipo, data_evento, valor 
            FROM historico_financeiro 
            WHERE nome_funcionario = ? AND tipo = 'Aumento'
            ORDER BY data_evento DESC LIMIT 1
        """
        cursor.execute(query, (nome_funcionario,))
        resultado = cursor.fetchone()
        conn.close()
        if resultado:
            tipo, data_str, valor = resultado
            # Cálculo de meses
            data_evento = datetime.strptime(data_str, "%Y-%m-%d")
            hoje = datetime.now() # Ou a data que você preferir
            meses = (hoje.year - data_evento.year) * 12 + (hoje.month - data_evento.month)
            
            status = "APTO por tempo" if meses >= 12 else f"INAPTO (apenas {meses} meses desde o último aumento)"
            return f"Último aumento: {data_str} ({status})."
        
        return "Sem histórico: APTO por tempo (novo funcionário)."
    except Exception as e:
        return f"Erro ao acessar ERP: {str(e)}"

def cria_agente_avaliacoes():
    prompt = """
        Você é um Especialista em Compliance e Remuneração. Sua decisão deve ser baseada nos dados das ferramentas.

        PROCESSO DE DECISÃO MANDATÓRIO:
        1. EXTRAÇÃO DE REGRA: Leia 'get_politica_remuneracao' e identifique o valor exato da Média Mínima para aumento.
        2. VALIDAÇÃO DE TEMPO: Se 'get_historico_erp' retornar "INAPTO", o funcionário NÃO pode entrar no ranking de aumento, independente da nota.
        3. COMPARAÇÃO MATEMÁTICA: Compare a Média da planilha com a Regra da get_politica_remuneracao. 
            - Use 3 casas decimais. 
            - Se a nota for 0.001 menor que o critério, o funcionário é INELEGÍVEL.
            - NÃO arredonde valores.

        OUTPUT ESPERADO:
        - TABELA DE EXCLUSÃO: Todos os inaptos (por tempo ou por nota insuficiente).
        - TOP AUMENTO SALARIAL: Apenas quem passou em AMBOS os critérios (Tempo E Nota).
        - DESTAQUES PARA BÔNUS: Conforme as regras específicas da política.

        Seja frio e analítico. Justifique citando os números exatos fornecidos pelas ferramentas.
        """
    
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.1)

    return create_agent(
        model=llm,
        tools=[get_planilha_avaliacoes, get_politica_remuneracao, get_historico_erp],
        system_prompt= prompt)