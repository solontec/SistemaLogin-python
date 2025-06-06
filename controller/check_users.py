import sqlite3

DATABASE = 'database.db' # Nome do seu arquivo de banco de dados SQLite

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row # Permite acessar colunas por nome
    return conn

def fetch_users():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT id, username, rm, password FROM usuarios") # Selecione todas as colunas
        users = cursor.fetchall()
        
        print("--- Usuários Registrados ---")
        if users:
            for user in users:
                # O hash da senha é longo, então imprima apenas os primeiros e últimos caracteres
                # ou não imprima para segurança. Exemplo:
                # print(f"ID: {user['id']}, Usuário: {user['username']}, RM: {user['rm']}, Senha (HASH): {user['password'][:8]}...{user['password'][-8:]}")
                print(f"ID: {user['id']}, Usuário: {user['username']}, RM: {user['rm']}, Senha (HASH): {user['password']}")
        else:
            print("Nenhum usuário encontrado na tabela 'usuarios'.")
            
    except sqlite3.OperationalError as e:
        print(f"Erro ao acessar o banco de dados: {e}")
        print("Verifique se a tabela 'usuarios' existe e se o banco de dados 'database.db' foi criado.")
    finally:
        conn.close()

if __name__ == '__main__':
    fetch_users()