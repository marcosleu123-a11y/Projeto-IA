import os
from flask import Flask, request, render_template, redirect, url_for, send_from_directory
import mysql.connector

app = Flask(__name__)


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
    return render_template('caio.html')   

@app.route('/ajustes') 
def ajustes():
    return render_template('pedrosa.html')

@app.route('/tarefas')
def tarefas():
    return render_template('index.html')

@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if request.method == 'POST':
        matricula_nova = request.form.get('matricula')
        senha_nova = request.form.get('senha')
        
        try:
            conexao = mysql.connector.connect(
                host='localhost',
                user='root',
                password='Caiofabio2109',
                database='usersdb'
            )
            cursor = conexao.cursor()
            cursor.execute("INSERT INTO users (matricula, senha) VALUES (%s, %s)", (matricula_nova, senha_nova))
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
