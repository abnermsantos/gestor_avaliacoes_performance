import logging
import functools
import traceback

def monitorar_tool(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logger.info(f"Executando Tool: {func.__name__} com argumentos: {args} {kwargs}")
        try:
            resultado = func(*args, **kwargs)
            return resultado
        except Exception as e:
            # Aqui capturamos o erro real e o local exato onde ocorreu
            erro_detalhado = traceback.format_exc()
            logger.error(f"FALHA na Tool {func.__name__}:\n{erro_detalhado}")
            return f"Erro técnico na ferramenta {func.__name__}. Comunique ao suporte."
    return wrapper

# Configuração do Logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("gestor.log")
    ]
)
logger = logging.getLogger("AgenteAvaliacoes")