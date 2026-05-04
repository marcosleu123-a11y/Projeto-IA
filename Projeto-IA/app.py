import json
import os
import random
import sqlite3
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
from werkzeug.utils import secure_filename

from tarefas import tarefas as tarefas_sugestoes


load_dotenv()

MODELO_ESCOLHIDO = "gpt-oss:20b-cloud"
TOTAL_SUGESTOES = 4
EXTENSOES_FOTO_PERFIL = {"png", "jpg", "jpeg", "webp", "gif"}
MAX_MENSAGENS_MEMORIA = 12
MAX_CARACTERES_MEMORIA = 1800
PROMPT_ASSISTENTE_VORTEX = """
Você é o assistente acadêmico do Vortex AI, uma plataforma de apoio aos alunos de tecnologia.
Seu papel é responder dúvidas, explicar conteúdos e orientar o aluno no uso do site.

Contexto do site Vortex AI:
- Assistente IA: tela de conversa para tirar dúvidas sobre tecnologia, programação, IA e estudos.
- Modo Foco: cronômetro de concentração para sessões de estudo, com histórico visual da sessão.
- Tarefas: gera sugestões de tarefas acadêmicas e permite marcar itens concluídos.
- Flashcard: permite criar e excluir cartões de revisão salvos para o aluno logado.
- Simulado: gera questões de múltipla escolha com IA sobre um tema informado pelo aluno.
- VARK: explica estilos de aprendizagem e aponta para o questionário VARK.
- Calendário: mostra o calendário mensal para organização dos estudos.
- Perfil: mostra matrícula, nome, e-mail e permite atualizar a foto de perfil.
- Ajustes: permite alterar nome, e-mail, senha e preferência de tema claro/escuro.
- Widget de notas: botão flutuante com 5 notas editáveis para anotações rápidas.

Áreas em que você deve ajudar:
- Tecnologia, programação, lógica, bancos de dados, engenharia de software, dados, infraestrutura e IA.
- Dúvidas acadêmicas, organização de estudos e uso das ferramentas do Vortex AI.
- Explicações didáticas com exemplos simples, analogias curtas e passos práticos.
- Código, quando fizer sentido, usando exemplos claros e comentando apenas o necessário.

Como responder:
- Responda em português do Brasil, com tom amigável, claro e direto.
- Se o aluno pedir orientação dentro do site, indique a aba correta e explique o que fazer.
- Se a pergunta for ampla, dê uma resposta inicial útil e sugira um próximo passo concreto.
- Se faltar informação para resolver uma dúvida técnica, faça no máximo uma pergunta objetiva.
- Se o aluno pedir algo fora do escopo acadêmico, redirecione com gentileza para estudos, tecnologia ou uso do Vortex.
- Não invente dados pessoais, notas, senhas, matrícula, registros internos ou informações que você não recebeu.
- Para problemas de login, cadastro, foto, senha ou banco de dados, explique possibilidades e oriente procurar suporte quando depender de acesso administrativo.
"""

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "chave-dev")
FLASHCARDS_DB = os.path.join(app.root_path, "flashcards.db")
NOTION_DB = os.path.join(app.root_path, "notion_notes.db")
CHAT_HISTORY_DB = os.path.join(app.root_path, "chat_history.db")
NOTION_NOTE_COUNT = 5
PROFILE_UPLOAD_DIR = os.path.join(app.root_path, "static", "uploads", "perfil")


def extensao_permitida(nome_arquivo):
    return "." in nome_arquivo and nome_arquivo.rsplit(".", 1)[1].lower() in EXTENSOES_FOTO_PERFIL


def foto_perfil_filename(usuario_id):
    if not usuario_id:
        return "imagens/foto_henrique.jpeg"

    usuario_seguro = secure_filename(str(usuario_id))
    for extensao in EXTENSOES_FOTO_PERFIL:
        caminho_relativo = f"uploads/perfil/{usuario_seguro}.{extensao}"
        caminho_absoluto = os.path.join(app.root_path, "static", caminho_relativo)
        if os.path.exists(caminho_absoluto):
            return caminho_relativo

    return "imagens/foto_henrique.jpeg"


@app.context_processor
def injetar_foto_perfil():
    filename = foto_perfil_filename(session.get("usuario_logado"))
    caminho_absoluto = os.path.join(app.root_path, "static", filename)
    versao = int(os.path.getmtime(caminho_absoluto)) if os.path.exists(caminho_absoluto) else None
    return {"foto_perfil_url": url_for("static", filename=filename, v=versao)}


def init_flashcards_db():
    with sqlite3.connect(FLASHCARDS_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS flashcards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conteudo TEXT NOT NULL,
                usuario_id TEXT NOT NULL
            )
            """
        )
        conn.commit()


def init_notion_db():
    with sqlite3.connect(NOTION_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS notion_notes (
                usuario_id TEXT NOT NULL,
                slot INTEGER NOT NULL,
                title TEXT NOT NULL,
                content_html TEXT NOT NULL DEFAULT '',
                PRIMARY KEY (usuario_id, slot)
            )
            """
        )
        conn.commit()


def init_chat_history_db():
    with sqlite3.connect(CHAT_HISTORY_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS chat_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.commit()


def usuario_notas_atual():
    return session.get("usuario_logado", "visitante")


def garantir_notas_usuario(usuario_id):
    with sqlite3.connect(NOTION_DB) as conn:
        cursor = conn.cursor()
        cursor.executemany(
            """
            INSERT OR IGNORE INTO notion_notes (usuario_id, slot, title, content_html)
            VALUES (?, ?, ?, '')
            """,
            [
                (usuario_id, slot, f"Nota {slot}")
                for slot in range(1, NOTION_NOTE_COUNT + 1)
            ],
        )
        cursor.execute(
            "DELETE FROM notion_notes WHERE usuario_id = ? AND slot > ?",
            (usuario_id, NOTION_NOTE_COUNT),
        )
        conn.commit()


init_flashcards_db()
init_notion_db()
init_chat_history_db()


def conectar_banco():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
    )


def usuario_chat_atual():
    usuario_id = session.get("usuario_logado")

    if usuario_id:
        return str(usuario_id)

    visitante_id = session.get("visitante_chat_id")

    if not visitante_id:
        visitante_id = f"visitante-{os.urandom(8).hex()}"
        session["visitante_chat_id"] = visitante_id

    return visitante_id


def obter_historico_chat():
    usuario_id = usuario_chat_atual()

    with sqlite3.connect(CHAT_HISTORY_DB) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        rows = cursor.execute(
            """
            SELECT role, content
            FROM chat_history
            WHERE usuario_id = ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (usuario_id, MAX_MENSAGENS_MEMORIA),
        ).fetchall()

    return [
        {"role": row["role"], "content": row["content"]}
        for row in reversed(rows)
    ]


def salvar_no_historico_chat(role, content):
    usuario_id = usuario_chat_atual()
    conteudo_limitado = str(content)[:MAX_CARACTERES_MEMORIA]

    with sqlite3.connect(CHAT_HISTORY_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO chat_history (usuario_id, role, content)
            VALUES (?, ?, ?)
            """,
            (usuario_id, role, conteudo_limitado),
        )
        cursor.execute(
            """
            DELETE FROM chat_history
            WHERE usuario_id = ?
              AND id NOT IN (
                SELECT id
                FROM chat_history
                WHERE usuario_id = ?
                ORDER BY id DESC
                LIMIT ?
              )
            """,
            (usuario_id, usuario_id, MAX_MENSAGENS_MEMORIA),
        )
        conn.commit()


def limpar_historico_chat(usuario_id=None):
    usuario_id = usuario_id or usuario_chat_atual()

    with sqlite3.connect(CHAT_HISTORY_DB) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM chat_history WHERE usuario_id = ?", (usuario_id,))
        conn.commit()


def bot(prompt):
    try:
        from ollama import chat
    except ImportError:
        return "O pacote ollama não está instalado neste ambiente."

    historico = obter_historico_chat()

    try:
        response = chat(
            model=MODELO_ESCOLHIDO,
            messages=[
                {"role": "system", "content": PROMPT_ASSISTENTE_VORTEX},
                *historico,
                {"role": "user", "content": prompt},
            ],
        )
        resposta = response["message"]["content"]
        salvar_no_historico_chat("user", prompt)
        salvar_no_historico_chat("assistant", resposta)
        return resposta
    except Exception as e:
        print("Erro no bot:", e)
        return "Desculpe, ocorreu um erro ao gerar a resposta."


def normalizar_questoes_simulado(texto_ia):
    inicio = texto_ia.find("[")
    fim = texto_ia.rfind("]")

    if inicio == -1 or fim == -1 or fim <= inicio:
        raise ValueError("A IA nao retornou uma lista JSON.")

    dados = json.loads(texto_ia[inicio : fim + 1])

    if not isinstance(dados, list) or not dados:
        raise ValueError("A lista de questoes esta vazia.")

    questoes = []

    for item in dados:
        if not isinstance(item, dict):
            continue

        pergunta = str(item.get("question", "")).strip()
        opcoes = item.get("options", [])
        resposta = item.get("answer")

        if not pergunta or not isinstance(opcoes, list) or len(opcoes) < 2:
            continue

        opcoes = [str(opcao).strip() for opcao in opcoes if str(opcao).strip()]

        opcoes = opcoes[:4]

        if len(opcoes) < 2:
            continue

        try:
            resposta = int(resposta)
        except (TypeError, ValueError):
            continue

        if resposta < 0 or resposta >= len(opcoes):
            continue

        questoes.append(
            {
                "question": pergunta,
                "options": opcoes[:4],
                "answer": resposta,
            }
        )

    if not questoes:
        raise ValueError("Nenhuma questao valida foi gerada.")

    return questoes


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
                limpar_historico_chat(matricula_digitada)
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


@app.route("/logout")
def logout():
    usuario_id = session.get("usuario_logado") or session.get("visitante_chat_id")

    if usuario_id:
        limpar_historico_chat(str(usuario_id))

    session.clear()
    return redirect(url_for("login"))


@app.route("/assistente")
@app.route("/home")
def assistente_academica():
    return render_template("marcos.html")


@app.route("/foco")
@app.route("/modo-foco")
def modo_foco():
    return render_template("felipe.html")


@app.route("/vark")
def vark():
    if "usuario_logado" not in session:
        return redirect(url_for("login"))

    return render_template("caioo.html")


@app.route("/simulado")
def simulado():
    if "usuario_logado" not in session:
        return redirect(url_for("login"))

    return render_template("simulado.html")


@app.route("/calendario")
def calendario():
    if "usuario_logado" not in session:
        return redirect(url_for("login"))

    return render_template("calendario.html")


@app.route("/simulado/gerar", methods=["POST"])
def gerar_simulado():
    if "usuario_logado" not in session:
        return jsonify({"erro": "Faca login para gerar um simulado."}), 401

    dados = request.get_json(silent=True) or {}
    tema = str(dados.get("tema", "")).strip()

    try:
        quantidade = int(dados.get("quantidade", 5))
    except (TypeError, ValueError):
        quantidade = 5

    quantidade = max(1, min(quantidade, 10))

    if not tema:
        return jsonify({"erro": "Informe um tema para o simulado."}), 400

    prompt = f"""
    Crie exatamente {quantidade} questoes de multipla escolha sobre "{tema}".
    Retorne apenas um array JSON valido, sem markdown e sem texto fora do JSON.
    Use este formato:
    [
      {{
        "question": "Texto da pergunta",
        "options": ["Opcao A", "Opcao B", "Opcao C", "Opcao D"],
        "answer": 0
      }}
    ]
    O campo "answer" deve ser o indice da opcao correta, de 0 a 3.
    """

    try:
        resposta = chat(
            model=MODELO_ESCOLHIDO,
            messages=[
                {
                    "role": "system",
                    "content": "Voce gera simulados educacionais em JSON valido.",
                },
                {"role": "user", "content": prompt},
            ],
        )
        texto_ia = resposta["message"]["content"]
        questoes = normalizar_questoes_simulado(texto_ia)
    except Exception as erro:
        print("Erro ao gerar simulado:", erro)
        return jsonify({"erro": "Nao foi possivel gerar o simulado agora."}), 500

    return jsonify({"questions": questoes[:quantidade]})


@app.route("/tarefas")
def tarefas():
    return render_template("index.html")


@app.route("/flashcards")
def flashcards():
    if "usuario_logado" not in session:
        return redirect(url_for("login"))

    usuario_id = session["usuario_logado"]

    with sqlite3.connect(FLASHCARDS_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, conteudo FROM flashcards WHERE usuario_id = ? ORDER BY id DESC",
            (usuario_id,),
        )
        flashcards_usuario = cursor.fetchall()

    return render_template("flashcards.html", flashcards=flashcards_usuario)


@app.route("/salvar_flashcard", methods=["POST"])
def salvar_flashcard():
    if "usuario_logado" not in session:
        return redirect(url_for("login"))

    conteudo = request.form.get("conteudo", "").strip()

    if conteudo:
        with sqlite3.connect(FLASHCARDS_DB) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO flashcards (conteudo, usuario_id) VALUES (?, ?)",
                (conteudo, session["usuario_logado"]),
            )
            conn.commit()

    return redirect(url_for("flashcards"))


@app.route("/deletar_flashcard", methods=["POST"])
def deletar_flashcard():
    if "usuario_logado" not in session:
        return redirect(url_for("login"))

    id_flashcard = request.form.get("id")

    if id_flashcard:
        with sqlite3.connect(FLASHCARDS_DB) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM flashcards WHERE id = ? AND usuario_id = ?",
                (id_flashcard, session["usuario_logado"]),
            )
            conn.commit()

    return redirect(url_for("flashcards"))


@app.route("/perfil", methods=["GET", "POST"])
def perfil():
    if "usuario_logado" not in session:
        return redirect(url_for("login"))

    matricula_da_sessao = session["usuario_logado"]
    mensagem_foto = None
    tipo_mensagem_foto = None

    if request.method == "POST":
        arquivo_foto = request.files.get("foto")

        if not arquivo_foto or not arquivo_foto.filename:
            mensagem_foto = "Selecione uma imagem antes de salvar."
            tipo_mensagem_foto = "erro"
        elif not extensao_permitida(arquivo_foto.filename):
            mensagem_foto = "Use uma imagem PNG, JPG, JPEG, WEBP ou GIF."
            tipo_mensagem_foto = "erro"
        else:
            os.makedirs(PROFILE_UPLOAD_DIR, exist_ok=True)
            extensao = arquivo_foto.filename.rsplit(".", 1)[1].lower()
            matricula_segura = secure_filename(str(matricula_da_sessao))

            for extensao_antiga in EXTENSOES_FOTO_PERFIL:
                caminho_antigo = os.path.join(
                    PROFILE_UPLOAD_DIR, f"{matricula_segura}.{extensao_antiga}"
                )
                if os.path.exists(caminho_antigo):
                    os.remove(caminho_antigo)

            arquivo_foto.save(os.path.join(PROFILE_UPLOAD_DIR, f"{matricula_segura}.{extensao}"))
            mensagem_foto = "Foto atualizada com sucesso!"
            tipo_mensagem_foto = "sucesso"

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
        mensagem_foto=mensagem_foto,
        tipo_mensagem_foto=tipo_mensagem_foto,
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


@app.route("/api/notes", methods=["GET"])
def listar_notas():
    usuario_id = usuario_notas_atual()
    garantir_notas_usuario(usuario_id)

    with sqlite3.connect(NOTION_DB) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        rows = cursor.execute(
            """
            SELECT slot, title, content_html
            FROM notion_notes
            WHERE usuario_id = ? AND slot <= ?
            ORDER BY slot ASC
            """,
            (usuario_id, NOTION_NOTE_COUNT),
        ).fetchall()

    return jsonify([dict(row) for row in rows])


@app.route("/api/notes/<int:slot>", methods=["GET"])
def obter_nota(slot):
    if slot < 1 or slot > NOTION_NOTE_COUNT:
        return jsonify({"error": "Nota invalida."}), 404

    usuario_id = usuario_notas_atual()
    garantir_notas_usuario(usuario_id)

    with sqlite3.connect(NOTION_DB) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        row = cursor.execute(
            """
            SELECT slot, title, content_html
            FROM notion_notes
            WHERE usuario_id = ? AND slot = ?
            """,
            (usuario_id, slot),
        ).fetchone()

    if row is None:
        return jsonify({"error": "Nota nao encontrada."}), 404

    return jsonify(dict(row))


@app.route("/api/notes/<int:slot>", methods=["PUT"])
def salvar_nota(slot):
    if slot < 1 or slot > NOTION_NOTE_COUNT:
        return jsonify({"error": "Nota invalida."}), 404

    usuario_id = usuario_notas_atual()
    garantir_notas_usuario(usuario_id)

    dados = request.get_json(silent=True) or {}
    title = str(dados.get("title") or "").strip() or f"Nota {slot}"
    content_html = str(dados.get("content_html") or "").strip()

    with sqlite3.connect(NOTION_DB) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE notion_notes
            SET title = ?, content_html = ?
            WHERE usuario_id = ? AND slot = ?
            """,
            (title, content_html, usuario_id, slot),
        )
        conn.commit()
        row = cursor.execute(
            """
            SELECT slot, title, content_html
            FROM notion_notes
            WHERE usuario_id = ? AND slot = ?
            """,
            (usuario_id, slot),
        ).fetchone()

    return jsonify(dict(row))


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
