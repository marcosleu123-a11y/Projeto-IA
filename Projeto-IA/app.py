import os
import random
from ollama import chat

import mysql.connector
from dotenv import load_dotenv
from flask import (
    Flask,
    jsonify,
    redirect,
    render_template,
    request,
    send_from_directory,
    session,
    url_for,
)

from tarefas import tarefas as tarefas_sugestoes


load_dotenv()

MODELO_ESCOLHIDO = "gpt-oss:20b-cloud"
TOTAL_SUGESTOES = 4

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "chave-dev")


def conectar_banco():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
    )


def bot(prompt):
    try:
        from ollama import chat
    except ImportError:
        return "O pacote ollama não está instalado neste ambiente."

    prompt_do_sistema = """
    Você é um professor. Explique de forma didática qualquer assunto que o usuário pedir.
    """

    try:
        response = chat(
            model=MODELO_ESCOLHIDO,
            messages=[
                {"role": "system", "content": prompt_do_sistema},
                {"role": "user", "content": prompt},
            ],
        )
        return response["message"]["content"]
    except Exception as e:
        print("Erro no bot:", e)
        return "Desculpe, ocorreu um erro ao gerar a resposta."


@app.route("/")
def index():
    return redirect(url_for("login"))


@app.route("/imagens/<path:filename>")
def imagens(filename):
    imagens_dir = os.path.abspath(os.path.join(app.root_path, "..", "imagens"))
    return send_from_directory(imagens_dir, filename)


@app.route("/login", methods=["GET", "POST"])
def login():
    mensagem = None
    tipo_mensagem = None

    if request.method == "POST":
        matricula_digitada = request.form.get("matricula", "").strip()
        senha_digitada = request.form.get("senha", "").strip()

        if not matricula_digitada or not senha_digitada:
            mensagem = "Preencha matrícula e senha para entrar."
            tipo_mensagem = "erro"
            return render_template(
                "arthur.html", mensagem=mensagem, tipo_mensagem=tipo_mensagem
            )

        conexao = None
        cursor = None

        try:
            conexao = conectar_banco()
            cursor = conexao.cursor(dictionary=True)
            cursor.execute("SELECT * FROM users WHERE matricula = %s", (matricula_digitada,))
            usuario = cursor.fetchone()

            if usuario and usuario["senha"] == senha_digitada:
                session["usuario_logado"] = matricula_digitada
                return redirect(url_for("assistente_academica"))

            mensagem = "Matrícula ou senha incorretos. Tente novamente."
            tipo_mensagem = "erro"
        except mysql.connector.Error:
            mensagem = "Não foi possível conectar ao banco agora. Verifique se o MySQL está ativo."
            tipo_mensagem = "erro"
        finally:
            if cursor:
                cursor.close()
            if conexao:
                conexao.close()

    return render_template("arthur.html", mensagem=mensagem, tipo_mensagem=tipo_mensagem)


@app.route("/assistente")
@app.route("/home")
def assistente_academica():
    return render_template("marcos.html")


@app.route("/foco")
@app.route("/modo-foco")
def modo_foco():
    return render_template("felipe.html")


@app.route("/tarefas")
def tarefas():
    return render_template("index.html")


@app.route("/perfil")
def perfil():
    if "usuario_logado" not in session:
        return redirect(url_for("login"))

    matricula_da_sessao = session["usuario_logado"]
    conexao = None
    cursor = None

    try:
        conexao = conectar_banco()
        cursor = conexao.cursor(dictionary=True)
        cursor.execute(
            "SELECT matricula, nome, email FROM users WHERE matricula = %s",
            (matricula_da_sessao,),
        )
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

    return render_template(
        "caio.html",
        matricula_do_aluno=usuario_db["matricula"],
        nome_do_aluno=usuario_db["nome"],
        email_do_aluno=usuario_db["email"],
    )


@app.route("/ajustes", methods=["GET", "POST"])
def ajustes():
    if "usuario_logado" not in session:
        return redirect(url_for("login"))

    matricula_atual = session["usuario_logado"]
    dados_usuario = {"matricula": matricula_atual, "nome": "", "email": ""}
    mensagem_sucesso = None
    conexao = None
    cursor = None

    try:
        conexao = conectar_banco()
        cursor = conexao.cursor(dictionary=True)

        if request.method == "POST":
            nome_digitado = request.form.get("nome")
            email_digitado = request.form.get("email")
            senha_digitada = request.form.get("senha")

            if nome_digitado:
                cursor.execute(
                    "UPDATE users SET nome = %s WHERE matricula = %s",
                    (nome_digitado, matricula_atual),
                )

            if email_digitado:
                cursor.execute(
                    "UPDATE users SET email = %s WHERE matricula = %s",
                    (email_digitado, matricula_atual),
                )

            if senha_digitada:
                cursor.execute(
                    "UPDATE users SET senha = %s WHERE matricula = %s",
                    (senha_digitada, matricula_atual),
                )

            conexao.commit()
            mensagem_sucesso = "Dados atualizados com sucesso!"

        cursor.execute(
            "SELECT matricula, nome, email FROM users WHERE matricula = %s",
            (matricula_atual,),
        )
        resultado = cursor.fetchone()

        if resultado:
            dados_usuario["nome"] = resultado["nome"] or ""
            dados_usuario["email"] = resultado["email"] or ""
    except mysql.connector.Error as err:
        print(f"Erro no banco: {err}")
    finally:
        if cursor:
            cursor.close()
        if conexao:
            conexao.close()

    return render_template(
        "pedrosa.html", usuario=dados_usuario, mensagem=mensagem_sucesso
    )


@app.route("/cadastro", methods=["GET", "POST"])
def cadastro():
    if request.method == "POST":
        matricula_nova = request.form.get("matricula")
        senha_nova = request.form.get("senha")
        nome_novo = request.form.get("nome")
        email_novo = request.form.get("email")
        conexao = None
        cursor = None

        try:
            conexao = conectar_banco()
            cursor = conexao.cursor()
            cursor.execute(
                "INSERT INTO users (matricula, senha, nome, email) VALUES (%s, %s, %s, %s)",
                (matricula_nova, senha_nova, nome_novo, email_novo),
            )
            conexao.commit()
        except mysql.connector.Error as err:
            mensagem = f"Erro ao cadastrar: {err}"
            return render_template(
                "cadastro.html", mensagem=mensagem, tipo_mensagem="erro"
            )
        finally:
            if cursor:
                cursor.close()
            if conexao:
                conexao.close()

        return redirect(url_for("login"))

    return render_template("cadastro.html")


@app.route("/sugestoes")
def sugestoes():
    quantidade = min(TOTAL_SUGESTOES, len(tarefas_sugestoes))
    tarefas_escolhidas = random.sample(tarefas_sugestoes, quantidade)
    return jsonify(tarefas_escolhidas)


@app.route("/chat", methods=["POST"])
def conversar():
    dados = request.get_json()

    if not dados or "msg" not in dados:
        return "Mensagem não enviada corretamente.", 400

    mensagem_usuario = dados["msg"]
    resposta_bot = bot(mensagem_usuario)

    return resposta_bot


if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)
