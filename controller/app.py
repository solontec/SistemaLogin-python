from flask import Flask, render_template, request, redirect, url_for, flash, session
import pymysql.cursors
import hashlib
import os

# --- Configurações do Banco de Dados MySQL ---
DB_CONFIG = {
    'host': 'localhost',
    'user': 'flaskuser',
    'password': 'SuaSenhaSeguraAqui123!', # <-- COLOQUE A SENHA REAL QUE VOCÊ DEFINIU NO MYSQL AQUI!
    'database': 'login_tcc',
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
}

# Obter o caminho absoluto para o diretório de templates
# Isso assume que 'templates' está na pasta PARENTE de 'controllers'
template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'templates'))

# Inicializar o Flask, especificando o template_folder
app = Flask(__name__, template_folder=template_dir)
app.secret_key = 'uma_chave_secreta_muito_forte_e_unica' # <-- MUDE ESTA CHAVE PARA ALGO SEGURO E ÚNICO!

# --- Funções do Banco de Dados MySQL ---

def get_db():
    """Tenta conectar ao banco de dados MySQL e retorna o objeto de conexão."""
    try:
        conn = pymysql.connect(**DB_CONFIG)
        return conn
    except pymysql.Error as e:
        # Apenas imprime o erro no console, não usa flash() aqui pois não há contexto de requisição
        print(f"Erro ao conectar ao banco de dados MySQL: {e}")
        return None

def init_db():
    """Inicializa o banco de dados, criando a tabela de usuários se não existir."""
    conn = None
    try:
        conn = get_db()
        if conn: # Só tenta criar a tabela se a conexão foi bem-sucedida
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS usuarios (
                    id INT(11) NOT NULL AUTO_INCREMENT,
                    username VARCHAR(50) NOT NULL UNIQUE,
                    password VARCHAR(64) NOT NULL,
                    rm VARCHAR(5) NOT NULL UNIQUE,
                    PRIMARY KEY (id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
            ''')
            conn.commit()
            cursor.close()
        else:
            print("Não foi possível inicializar o banco de dados: Falha na conexão MySQL.")
    except pymysql.Error as e:
        print(f"Erro ao inicializar a tabela no MySQL: {e}")
    finally:
        if conn:
            conn.close()

# --- Rotas da Aplicação ---

@app.route('/')
def index():
    """Rota inicial que redireciona para login ou success se já logado."""
    if 'username' in session:
        return redirect(url_for('success'))
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Rota para registro de novos usuários."""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        rm = request.form['rm']

        if not username or not password or not rm:
            flash('Por favor, preencha todos os campos.', 'danger')
            return render_template('register.html')

        hashed_password = hashlib.sha256(password.encode()).hexdigest()

        conn = get_db()
        if conn is None: # Se a conexão falhou, exibe mensagem ao usuário
            flash("Não foi possível conectar ao banco de dados. Tente novamente mais tarde.", "danger")
            return render_template('register.html')

        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO usuarios (username, password, rm) VALUES (%s, %s, %s)", (username, hashed_password, rm))
            conn.commit()
            flash('Registro bem-sucedido! Agora você pode fazer login.', 'success')
            return redirect(url_for('login'))
        except pymysql.err.IntegrityError as e:
            if "Duplicate entry" in str(e) and "for key 'username'" in str(e):
                flash('Nome de usuário já existe. Por favor, escolha outro.', 'danger')
            elif "Duplicate entry" in str(e) and "for key 'rm'" in str(e):
                flash('RM já existe. Por favor, insira outro.', 'danger')
            else:
                flash(f'Ocorreu um erro inesperado no registro: {e}', 'danger')
        except pymysql.Error as e:
            flash(f'Erro no banco de dados durante o registro: {e}', 'danger')
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Rota para login de usuários."""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if not username or not password:
            flash('Por favor, preencha todos os campos.', 'danger')
            return render_template('login.html')

        hashed_password = hashlib.sha256(password.encode()).hexdigest()

        conn = get_db()
        if conn is None: # Se a conexão falhou, exibe mensagem ao usuário
            flash("Não foi possível conectar ao banco de dados. Tente novamente mais tarde.", "danger")
            return render_template('login.html')

        cursor = conn.cursor()
        try:
            cursor.execute("SELECT id, username, rm FROM usuarios WHERE username = %s AND password = %s", (username, hashed_password))
            user = cursor.fetchone() # user será um dicionário devido a DictCursor
        except pymysql.Error as e:
            flash(f'Erro no banco de dados durante o login: {e}', 'danger')
            user = None
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

        if user:
            session['username'] = user['username']
            session['rm'] = user['rm']
            flash('Login bem-sucedido!', 'success')
            return redirect(url_for('success'))
        else:
            flash('Nome de usuário ou senha inválidos.', 'danger')

    return render_template('login.html')

@app.route('/success')
def success():
    """Página de sucesso após o login."""
    if 'username' in session:
        return render_template('success.html', username=session['username'], rm=session.get('rm'))
    return redirect(url_for('login'))

@app.route('/logout')
def logout():
    """Rota para fazer logout."""
    session.pop('username', None)
    session.pop('rm', None)
    flash('Você foi desconectado.', 'info')
    return redirect(url_for('login'))

if __name__ == '__main__':
    # Esta linha tenta inicializar a tabela no MySQL quando o app.py é executado diretamente.
    # Se o MySQL estiver inacessível, ela vai imprimir o erro no console, mas o Flask ainda tentará iniciar.
    init_db()
    app.run(debug=True)