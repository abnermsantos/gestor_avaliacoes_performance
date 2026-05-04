import os
import logging
from PyPDF2 import PdfReader
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

logger = logging.getLogger("SistemaRemuneracao")


class RagService:
    """
    Gerencia o ciclo de vida do vectorstore.
    Mantém uma única instância em memória durante toda a execução.
    """

    _instancia: Chroma | None = None

    @classmethod
    def get_vectorstore(cls) -> Chroma:
        """
        Retorna o vectorstore singleton.
        Carrega o PDF e gera embeddings apenas na primeira chamada.
        """
        if cls._instancia is not None:
            logger.info("Vectorstore já inicializado — reutilizando instância.")
            return cls._instancia

        logger.info("Inicializando vectorstore pela primeira vez...")

        caminho = os.getenv("CAMINHO_POLITICA")
        if not caminho or not os.path.exists(caminho):
            raise FileNotFoundError(
                f"Arquivo de política não encontrado. "
                f"Verifique CAMINHO_POLITICA no .env. Valor atual: '{caminho}'"
            )

        reader = PdfReader(caminho)
        paginas = [p.extract_text() for p in reader.pages if p.extract_text()]
        if not paginas:
            raise ValueError("O PDF da política não contém texto extraível.")

        docs = RecursiveCharacterTextSplitter(
            chunk_size=400, chunk_overlap=40
        ).create_documents(["\n".join(paginas)])
        
        logger.info(f"PDF dividido em {len(docs)} chunks.")

        embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
        )

        cls._instancia = Chroma.from_documents(
            documents=docs,
            embedding=embeddings,
            collection_name="politica_rh",
        )
        logger.info("Vectorstore inicializado com sucesso.")
        
        return cls._instancia

    @classmethod
    def reset(cls) -> None:
        """Descarta a instância atual. Útil em testes ou atualização da política."""
        cls._instancia = None
        logger.info("Vectorstore resetado.")