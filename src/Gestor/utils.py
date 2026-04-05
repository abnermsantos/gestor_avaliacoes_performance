import logging
import functools
import traceback

# Configuração do Logger para arquivo
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("gestor_rh.log", encoding='utf-8')
    ]
)
logger = logging.getLogger("SistemaRemuneracao")

def monitorar_processo(func):
    """Decorador para capturar erros e logs sem poluir o terminal."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logger.info(f"Iniciando: {func.__name__}")
        try:
            resultado = func(*args, **kwargs)
            logger.info(f"Sucesso: {func.__name__}")
            return resultado
        except Exception as e:
            erro_detalhado = traceback.format_exc()
            logger.error(f"FALHA CRÍTICA em {func.__name__}:\n{erro_detalhado}")
            # Retornamos uma mensagem amigável para o Estado do Agente
            return f"Erro processado no log: {str(e)}"
    return wrapper