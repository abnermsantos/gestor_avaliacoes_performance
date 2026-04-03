import datetime

from dotenv import load_dotenv
from agentes import cria_agente_avaliacoes

load_dotenv()

### Temos que pegar o banco de dados com o histórico de meritos dos funcionários
### Chamamos o agente para que ele avalie com base no histórico, politica e avaliação quem merece mérito nesse período

def main():
    print("--- Iniciando Sistema de Análise de Remuneração ---\n")
    agent = cria_agente_avaliacoes()

    pergunta = "Com base na política da empresa e nas avaliações atuais, quem são os profissionais mais indicados para aumento salarial e bonus por performance?"
    print(pergunta)
    
    response = agent.invoke({"messages": [{"role": "user", "content": pergunta}]})
    if "messages" in response:
        resultado_final = response["messages"][-1].content
        print("\nANÁLISE DO ESPECIALISTA:")
        print("-" * 30)
        print(resultado_final)
        print("-" * 30)
    else:
        print("Não foi possível obter uma resposta do agente.")

if __name__ == "__main__":
    main()