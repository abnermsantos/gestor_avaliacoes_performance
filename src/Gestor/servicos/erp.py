import os
import sqlite3
import logging
from datetime import datetime

from utils import monitorar_processo

logger = logging.getLogger("SistemaRemuneracao")


class ErpService:
    """Responsável por consultar o histórico financeiro dos funcionários."""

    def __init__(self):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self._db_path = os.path.join(base_dir, "..", "db", "erp_simulado.db")

    @monitorar_processo
    ###!!! AQUI AINDA PRECISAMOS AJUSTAR OS 12 MESES
    def verificar_elegibilidade(self, nome_funcionario: str) -> str:
        """
        Verifica se o funcionário está apto a receber aumento.
        Retorna 'APTO' ou 'INAPTO (Aumento há X meses)'.
        """
        
        conn = sqlite3.connect(self._db_path)
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT data_evento FROM historico_financeiro
            WHERE nome_funcionario = ? AND upper(tipo) = 'AUMENTO'
            ORDER BY data_evento DESC LIMIT 1
            """,
            (nome_funcionario,),
        )

        resultado = cursor.fetchone()
        conn.close()

        if resultado:
            data_evento = datetime.strptime(resultado[0], "%Y-%m-%d")
            hoje = datetime.now()
            meses = (
                (hoje.year - data_evento.year) * 12
                + (hoje.month - data_evento.month)
            )
            if meses <= 12:
                return f"INAPTO (Aumento há {meses} meses)"

        return "APTO"