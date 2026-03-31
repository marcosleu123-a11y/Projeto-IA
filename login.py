import os
from flask import Flask, request, render_template, redirect, url_for, send_from_directory, session, jsonify
import mysql.connector

app = Flask(__name__)

# Sessão Secreta para manter o usuário logado
app.secret_key = 'vortex_secreto_123'


@app.route('/')
def index():
    return redirect(url_for('login'))


@app.route('/imagens/<path:filename>')
def imagens(filename):
    imagens_dir = os.path.abspath(os.path.join(app.root_path, '..', 'imagens'))
    return send_from_directory(imagens_dir, filename)


@app.route('/login', methods=['GET', 'POST'])
def login():
    mensagem = None
    tipo_mensagem = None

    if request.method == 'POST':

        matricula_digitada = request.form.get('matricula', '').strip()
        senha_digitada = request.form.get('senha', '').strip()

        if not matricula_digitada or not senha_digitada:
            mensagem = 'Preencha matrícula e senha para entrar.'
            tipo_mensagem = 'erro'
            return render_template('arthur.html', mensagem=mensagem, tipo_mensagem=tipo_mensagem)

        conexao = None
        cursor = None
        try:

            conexao = mysql.connector.connect(
                host='localhost',
                user='root',
                password='Caiofabio2109',
                database='usersdb'
            )

            cursor = conexao.cursor(dictionary=True)

            comando_sql = "SELECT * FROM users WHERE matricula = %s"

            cursor.execute(comando_sql, (matricula_digitada,))

            usuario = cursor.fetchone()

            if usuario and usuario['senha'] == senha_digitada:
                session['usuario_logado'] = matricula_digitada
                return redirect(url_for('assistente_academica'))
            else:

                mensagem = 'Matrícula ou senha incorretos. Tente novamente.'
                tipo_mensagem = 'erro'
        except mysql.connector.Error:
            mensagem = 'Não foi possível conectar ao banco agora. Verifique se o MySQL está ativo.'
            tipo_mensagem = 'erro'
        finally:

            if cursor:
                cursor.close()
            if conexao:
                conexao.close()

        return render_template('arthur.html', mensagem=mensagem, tipo_mensagem=tipo_mensagem)

    return render_template('arthur.html', mensagem=mensagem, tipo_mensagem=tipo_mensagem)


@app.route('/assistente')
def assistente_academica():

    return render_template('marcos.html')


@app.route('/foco')
def modo_foco():

    return render_template('felipe.html')


@app.route('/perfil')
def perfil():

    if 'usuario_logado' not in session:
        return redirect(url_for('login'))

    matricula_da_sessao = session['usuario_logado']

    try:
        conexao = mysql.connector.connect(
            host='localhost',
            user='root',
            password='Caiofabio2109',
            database='usersdb'
        )
        cursor = conexao.cursor(dictionary=True)
        cursor.execute(
            "SELECT matricula, nome, email FROM users WHERE matricula = %s", (matricula_da_sessao,))
        usuario_db = cursor.fetchone()

    except mysql.connector.Error:
        usuario_db = None

    finally:
        if cursor:
            cursor.close()
        if conexao:
            conexao.close()
    if not usuario_db:
        return "Erro: Usuário não encontrado no banco."

    return render_template('caio.html', matricula_do_aluno=usuario_db['matricula'], nome_do_aluno=usuario_db['nome'], email_do_aluno=usuario_db['email'])


@app.route('/ajustes', methods=['GET', 'POST'])
def ajustes():

    if 'usuario_logado' not in session:
        return redirect(url_for('login'))

    matricula_atual = session['usuario_logado']  
    dados_usuario = {'matricula': matricula_atual, 'nome': '', 'email': ''}
    mensagem_sucesso = None

    try:
        conexao = mysql.connector.connect(
            host='localhost', user='root', password='Caiofabio2109', database='usersdb'
        )
        cursor = conexao.cursor(dictionary=True)

        if request.method == 'POST':
            nome_digitado = request.form.get('nome')
            email_digitado = request.form.get('email')
            senha_digitada = request.form.get('senha')
            
            if nome_digitado:
                cursor.execute(
                    "UPDATE users SET nome = %s WHERE matricula = %s",
                    (nome_digitado, matricula_atual)
                )
            
            if email_digitado:
                cursor.execute(
                    "UPDATE users SET email = %s WHERE matricula = %s",
                    (email_digitado, matricula_atual)
                )

            if senha_digitada:
                cursor.execute(
                    "UPDATE users SET senha = %s WHERE matricula = %s",
                    (senha_digitada, matricula_atual)
                )

            conexao.commit()
            mensagem_sucesso = "Dados atualizados com sucesso!"

        cursor.execute(
            "SELECT matricula, nome, email FROM users WHERE matricula = %s", (matricula_atual,))
        resultado = cursor.fetchone()

        if resultado:
            dados_usuario['nome'] = resultado['nome'] if resultado['nome'] else ''
            dados_usuario['email'] = resultado['email'] if resultado['email'] else ''

    except mysql.connector.Error as err:
        print(f"Erro no banco: {err}")
    finally:
        if 'cursor' in locals() and cursor:
            cursor.close()
        if 'conexao' in locals() and conexao:
            conexao.close()

    return render_template('pedrosa.html', usuario=dados_usuario, mensagem=mensagem_sucesso)


@app.route('/tarefas')
def tarefas():
    return render_template('index.html')


@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if request.method == 'POST':
        matricula_nova = request.form.get('matricula')
        senha_nova = request.form.get('senha')
        nome_novo = request.form.get('nome')
        email_novo = request.form.get('email')

        try:
            conexao = mysql.connector.connect(
                host='localhost',
                user='root',
                password='Caiofabio2109',
                database='usersdb'
            )
            cursor = conexao.cursor()
            cursor.execute(
                "INSERT INTO users (matricula, senha, nome, email) VALUES (%s, %s, %s, %s)", (matricula_nova, senha_nova, nome_novo, email_novo))
        except mysql.connector.Error as err:
            mensagem = f'Erro ao cadastrar: {err}'
            return render_template('cadastro.html', mensagem=mensagem, tipo_mensagem='erro')
        finally:
            if conexao:
                conexao.commit()

            if cursor:
                cursor.close()

            if conexao:
                conexao.close()

        return redirect(url_for('login'))

    return render_template('cadastro.html')


@app.route("/sugestoes")
def sugestoes():
    quantidade = min(TOTAL_SUGESTOES, len(tarefas))
    tarefas_escolhidas = random.sample(tarefas, quantidade)
    return jsonify(tarefas_escolhidas)


if __name__ == '__main__':

    app.run(debug=True)
