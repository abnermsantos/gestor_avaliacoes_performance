import logging
import functools
import traceback

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("gestor_rh.log", encoding="utf-8")
    ],
)

logger = logging.getLogger("SistemaRemuneracao")


def monitorar_processo(func):
    """Decorador de log — registra início, sucesso e falhas sem poluir o terminal."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logger.info(f"Iniciando: {func.__qualname__}")
        try:
            resultado = func(*args, **kwargs)
            logger.info(f"Sucesso: {func.__qualname__}")
            return resultado
        except Exception as e:
            logger.error(f"FALHA em {func.__qualname__}:\n{traceback.format_exc()}")
            raise  # propaga a exceção — quem chama decide como tratar
    return wrapper