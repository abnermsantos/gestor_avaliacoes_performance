import sqlite3

def setup():
    conn = sqlite3.connect('erp_simulado.db')
    cursor = conn.cursor()

    # Criar tabela
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS historico_financeiro (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome_funcionario TEXT,
            tipo TEXT,
            data_evento DATE,
            valor REAL
        )
    ''')

    # Dados de teste (Ana teve aumento recente, Bruno não tem há anos)
    dados = [
        ('Ana Silva', 'Aumento', '2025-06-01', 10.0),
        ('Bruno Santos', 'Aumento', '2021-05-20', 15.0),
        ('Carla Dias', 'Bônus', '2024-01-15', 5000.0),
        ('Elena Rose', 'Aumento', '2022-10-10', 8.0)
    ]

    cursor.executemany('INSERT INTO historico_financeiro (nome_funcionario, tipo, data_evento, valor) VALUES (?, ?, ?, ?)', dados)
    
    conn.commit()
    conn.close()
    print("Banco de dados ERP simulado pronto!")

if __name__ == "__main__":
    setup()