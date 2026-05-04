import datetime
import sys
import uuid

from agentes import AgenteRH

def main():
    print("\n" + "=" * 60)
    print("      SISTEMA AGÊNTICO DE ANÁLISE DE REMUNERAÇÃO")
    print("=" * 60)

    print("[*] Inicializando sistema...")
    app = AgenteRH().compilar()

    session_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": session_id}}
    
    inputs = {
        "data_hoje": datetime.date.today().strftime("%d/%m/%Y"),
        "resultado_final": "",
        "lista_bonus_inovacao": "",
    }

    print("[*] Iniciando análise técnica...")
    for output in app.stream(inputs, config):
        for no in output.keys():
            print(f"[OK] Executado: {no}")

    # Loop de decisão com human-in-the-loop
    while True:
        snapshot = app.get_state(config)

        print("\n" + "!" * 60)
        print("       AGUARDANDO VALIDAÇÃO DO GESTOR DE RH")
        print("!" * 60)

        print("\nPRÉVIA ATUALIZADA DOS BÔNUS:")
        print("-" * 30)
        print(snapshot.values.get("lista_bonus_inovacao", "Sem dados para exibir."))

        print("\nPRÉVIA ATUALIZADA DOS MÉRITOS SALARIAIS:")
        print("-" * 30)
        print(snapshot.values.get("resultado_final", "Sem dados para exibir."))
        print("-" * 30)
        
        print("\nOPÇÕES DE DECISÃO:")
        print("[1] APROVAR: Gerar relatório final e encerrar.")
        print("[2] REPROCESSAR: Executar novamente a análise.")
        print("[3] CANCELAR: Encerrar sem salvar.")
        
        decisao = input("\nEscolha uma opção (1, 2 ou 3): ").strip()

        if decisao == "1":
            print("\n[*] Aprovação recebida. Finalizando relatório...")
            for _ in app.stream(None, config):
                pass
            break
        
        elif decisao == "2":
            print("\n[*] Reiniciando fluxo de análise por solicitação do usuário...")
            inputs_limpos = {
                "data_hoje": datetime.date.today().strftime("%d/%m/%Y"),
                "resultado_final": "",
                "lista_bonus_inovacao": "",
            }

            for output in app.stream(inputs_limpos, config):
                for no in output.keys():
                    print(f"[RE-OK] Atualizado: {no}")

        elif decisao == "3":
            print("\n[!] Operação cancelada.")
            sys.exit()
        else:
            print("[!] Opção inválida.")

    # Relatório final
    print("\n" + "=" * 60)
    print("           RELATÓRIO DE REMUNERAÇÃO HOMOLOGADO")
    print("=" * 60)

    estado_final = app.get_state(config).values

    print("\n[ 1. BÔNUS DE INOVAÇÃO ]")
    print("-" * 30)
    print(estado_final.get("lista_bonus_inovacao", "").strip())

    print("\n[ 2. MÉRITO SALARIAL (APROVADOS) ]")
    print("-" * 30)
    print(estado_final.get("resultado_final", "").strip())

    print("\n" + "=" * 60)
    print("TODOS OS DADOS PROCESSADOS")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()