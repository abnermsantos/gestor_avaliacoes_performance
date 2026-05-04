import os
import logging
import pandas as pd
from io import StringIO

from utils import monitorar_processo

logger = logging.getLogger("SistemaRemuneracao")


class PlanilhaService:
    """Responsável por carregar e parsear o arquivo de avaliações."""

    @monitorar_processo
    def carregar(self) -> pd.DataFrame:
        """Lê o arquivo de avaliações e retorna um DataFrame."""
        
        caminho = os.getenv("CAMINHO_AVALIACOES")
        if not caminho or not os.path.exists(caminho):
            raise FileNotFoundError(
                f"Arquivo de avaliações não encontrado. "
                f"Verifique CAMINHO_AVALIACOES no .env. Valor atual: '{caminho}'"
            )
        
        if caminho.endswith(".xlsx"):
            return pd.read_excel(caminho)
        return pd.read_csv(caminho)

    @monitorar_processo
    def para_string(self, df: pd.DataFrame) -> str:
        """Serializa o DataFrame para string formatada (passagem entre nós)."""

        return df.to_string(index=False, float_format="{:.3f}".format)

    @monitorar_processo
    def de_string(self, texto: str) -> pd.DataFrame:
        """Desserializa a string de volta para DataFrame."""
        
        return pd.read_csv(
            StringIO(texto),
            sep=r"\s{2,}",
            engine="python",
        )