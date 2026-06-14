import json
import html as html_utils
import os
import re
import sqlite3
import tempfile
import unicodedata
from datetime import date, datetime, timedelta

try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv():
        return None
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

try:
    import mysql.connector

    MYSQL_ERROR = mysql.connector.Error
except ImportError:
    mysql = None
    MYSQL_ERROR = Exception


load_dotenv()

MODELO_ESCOLHIDO = "gemma4:31b-cloud"
EXTENSOES_FOTO_PERFIL = {"png", "jpg", "jpeg", "webp", "gif"}
MAX_MENSAGENS_MEMORIA = 12
MAX_MENSAGENS_HISTORICO_INTERFACE = 80
MAX_CARACTERES_MEMORIA = 1800
TERMOS_ABAS_REMOVIDAS = (
    "modo foco",
    "modo-foco",
    "vark",
    "aba tarefas",
    "aba de tarefas",
    "pagina tarefas",
    "pÃ¡gina tarefas",
    "menu tarefas",
    "tela tarefas",
    "ferramenta tarefas",
    "ferramenta de tarefas",
)
RESPOSTA_ABA_REMOVIDA = (
    "Essa area nao esta disponivel na versao atual do Vortex AI. "
    "Posso te ajudar com o assistente, flashcards, simulado, calendario, perfil, ajustes ou notas."
)
PROMPT_ASSISTENTE_VORTEX = """
Voce e o assistente academico do Vortex AI, uma plataforma de apoio aos alunos de tecnologia.
Seu papel e responder duvidas, explicar conteudos e orientar o aluno no uso do site.

Contexto do site Vortex AI:
- Assistente IA: tela de conversa para tirar duvidas sobre tecnologia, programacao, IA e estudos.
- Flashcard: permite criar e excluir cartoes de revisao salvos para o aluno logado.
- Simulado: gera questoes de multipla escolha com IA sobre um tema informado pelo aluno.
- Calendario: mostra o calendario mensal para organizacao dos estudos.
- Perfil: mostra matricula, nome, e-mail e permite atualizar a foto de perfil.
- Ajustes: permite alterar nome, e-mail, senha e preferencia de tema claro/escuro.
- Widget de notas: botao flutuante com 5 notas editaveis para anotacoes rapidas.

Areas em que voce deve ajudar:
- Tecnologia, programacao, logica, bancos de dados, engenharia de software, dados, infraestrutura e IA.
- Duvidas academicas, organizacao de estudos e uso das ferramentas do Vortex AI.
- Explicacoes didaticas com exemplos simples, analogias curtas e passos praticos.
- Codigo, quando fizer sentido, usando exemplos claros e comentando apenas o necessario.

Como responder:
- Responda em portugues do Brasil, com tom amigavel, claro e direto.
- Use formatacao simples em Markdown: titulos curtos, listas com marcadores, negrito apenas para termos importantes e blocos de codigo quando necessario.
- Nao use tabelas, tags HTML como <br> ou linhas muito longas. Prefira paragrafos curtos e listas faceis de ler no chat.
- Nao recomende, explique, liste ou direcione o aluno para areas removidas do site. Se o aluno perguntar por uma area removida, diga apenas que ela nao esta disponivel na versao atual e ofereca as ferramentas ativas: assistente, flashcards, simulado, calendario, perfil, ajustes e notas.
- Se o aluno pedir para salvar, colocar, adicionar ou guardar uma explicacao em uma nota do Notion, nao mande o aluno copiar e colar manualmente. O sistema salva automaticamente quando a nota e informada.
- Se o aluno pedir orientacao dentro do site, indique a aba correta e explique o que fazer.
- Quando receber um contexto da base de conhecimento, interprete a pergunta do aluno e responda usando apenas as informacoes relevantes desse contexto.
- Para perguntas sobre datas, horarios, salas, professores, avaliacoes, VRAU, A360, AFE, curso ou calendario, nao invente: use a base de conhecimento enviada pelo sistema.
- Se a pergunta for ampla, de uma resposta inicial util e sugira um proximo passo concreto.
- Se faltar informacao para resolver uma duvida tecnica, faca no maximo uma pergunta objetiva.
- Se o aluno pedir algo fora do escopo academico, redirecione com gentileza para estudos, tecnologia ou uso do Vortex.
- Nao invente dados pessoais, notas, senhas, matricula, registros internos ou informacoes que voce nao recebeu.
- Para problemas de login, cadastro, foto, senha ou banco de dados, explique possibilidades e oriente procurar suporte quando depender de acesso administrativo.
"""

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "chave-dev")
IS_VERCEL = os.getenv("VERCEL") == "1"
DATA_DIR = os.getenv("APP_DATA_DIR") or (tempfile.gettempdir() if IS_VERCEL else app.root_path)
FLASHCARDS_DB = os.path.join(DATA_DIR, "flashcards.db")
NOTION_DB = os.path.join(DATA_DIR, "notion_notes.db")
CHAT_HISTORY_DB = os.path.join(DATA_DIR, "chat_history.db")
NOTION_NOTE_COUNT = 5
PROFILE_UPLOAD_DIR = os.path.join(
    DATA_DIR if IS_VERCEL else os.path.join(app.root_path, "static"),
    "uploads",
    "perfil",
)
BASE_CONHECIMENTO_PATHS = (
    os.getenv("BASE_CONHECIMENTO_PATH"),
    os.path.join(app.root_path, "base_de_conhecimento.json"),
    os.path.abspath(os.path.join(app.root_path, "..", "base_de_conhecimento.json")),
    os.path.abspath("base_de_conhecimento.json"),
)
MAX_TRECHOS_BASE_CONHECIMENTO = 10
MAX_CARACTERES_CONTEXTO_CONHECIMENTO = 5000
BASE_CONHECIMENTO_CACHE = {
    "path": None,
    "mtime": None,
    "trechos": [],
}


def extensao_permitida(nome_arquivo):
    return "." in nome_arquivo and nome_arquivo.rsplit(".", 1)[1].lower() in EXTENSOES_FOTO_PERFIL


def foto_perfil_filename(usuario_id):
    if not usuario_id:
        return "imagens/foto_henrique.jpeg"

    usuario_seguro = secure_filename(str(usuario_id))
    for extensao in EXTENSOES_FOTO_PERFIL:
        nome_arquivo = f"{usuario_seguro}.{extensao}"
        caminho_relativo = f"uploads/perfil/{nome_arquivo}"
        caminho_upload = os.path.join(PROFILE_UPLOAD_DIR, nome_arquivo)
        caminho_static = os.path.join(app.root_path, "static", caminho_relativo)

        if os.path.exists(caminho_upload) or os.path.exists(caminho_static):
            return caminho_relativo

    return "imagens/foto_henrique.jpeg"


@app.context_processor
def injetar_foto_perfil():
    filename = foto_perfil_filename(session.get("usuario_logado"))

    if filename.startswith("uploads/perfil/"):
        nome_arquivo = os.path.basename(filename)
        caminho_upload = os.path.join(PROFILE_UPLOAD_DIR, nome_arquivo)

        if os.path.exists(caminho_upload):
            versao = int(os.path.getmtime(caminho_upload))
            return {
                "foto_perfil_url": url_for(
                    "perfil_upload", filename=nome_arquivo, v=versao
                )
            }

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
            CREATE TABLE IF NOT EXISTS chat_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario_id TEXT NOT NULL,
                title TEXT NOT NULL DEFAULT 'Novo chat',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS chat_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario_id TEXT NOT NULL,
                session_id INTEGER,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES chat_sessions(id)
            )
            """
        )
        colunas = [
            coluna[1]
            for coluna in cursor.execute("PRAGMA table_info(chat_history)").fetchall()
        ]

        if "session_id" not in colunas:
            cursor.execute("ALTER TABLE chat_history ADD COLUMN session_id INTEGER")

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
    if mysql is None:
        raise RuntimeError("O pacote mysql-connector-python nao esta instalado.")

    host = os.getenv("DB_HOST") or "127.0.0.1"
    if host.lower() == "localhost":
        host = "127.0.0.1"

    return mysql.connector.connect(
        host=host,
        port=int(os.getenv("DB_PORT", "3306")),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
        connection_timeout=int(os.getenv("DB_CONNECTION_TIMEOUT", "5")),
        use_pure=True,
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


def titulo_chat_por_mensagem(mensagem):
    titulo = " ".join(str(mensagem).split())

    if not titulo:
        return "Novo chat"

    return titulo[:47] + "..." if len(titulo) > 50 else titulo


def criar_sessao_chat(usuario_id=None, titulo="Novo chat"):
    usuario_id = usuario_id or usuario_chat_atual()

    with sqlite3.connect(CHAT_HISTORY_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO chat_sessions (usuario_id, title)
            VALUES (?, ?)
            """,
            (usuario_id, titulo),
        )
        conn.commit()
        session_id = cursor.lastrowid

    session["chat_session_id"] = session_id
    return session_id


def migrar_historico_antigo(cursor, usuario_id):
    mensagens_antigas = cursor.execute(
        """
        SELECT COUNT(*)
        FROM chat_history
        WHERE usuario_id = ? AND session_id IS NULL
        """,
        (usuario_id,),
    ).fetchone()[0]

    if not mensagens_antigas:
        return None

    cursor.execute(
        """
        INSERT INTO chat_sessions (usuario_id, title)
        VALUES (?, ?)
        """,
        (usuario_id, "Chat antigo"),
    )
    session_id = cursor.lastrowid
    cursor.execute(
        """
        UPDATE chat_history
        SET session_id = ?
        WHERE usuario_id = ? AND session_id IS NULL
        """,
        (session_id, usuario_id),
    )

    return session_id


def garantir_sessao_chat_atual():
    usuario_id = usuario_chat_atual()
    sessao_id = session.get("chat_session_id")

    with sqlite3.connect(CHAT_HISTORY_DB) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        sessao_migrada = migrar_historico_antigo(cursor, usuario_id)

        if sessao_id:
            sessao = cursor.execute(
                """
                SELECT id
                FROM chat_sessions
                WHERE id = ? AND usuario_id = ?
                """,
                (sessao_id, usuario_id),
            ).fetchone()

            if sessao:
                conn.commit()
                return sessao["id"]

        sessao = cursor.execute(
            """
            SELECT id
            FROM chat_sessions
            WHERE usuario_id = ?
            ORDER BY updated_at DESC, id DESC
            LIMIT 1
            """,
            (usuario_id,),
        ).fetchone()

        if sessao:
            session["chat_session_id"] = sessao["id"]
            conn.commit()
            return sessao["id"]

        if sessao_migrada:
            session["chat_session_id"] = sessao_migrada
            conn.commit()
            return sessao_migrada

    return criar_sessao_chat(usuario_id)


def listar_sessoes_chat():
    usuario_id = usuario_chat_atual()
    sessao_ativa = garantir_sessao_chat_atual()

    with sqlite3.connect(CHAT_HISTORY_DB) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        rows = cursor.execute(
            """
            SELECT
                s.id,
                s.title,
                s.created_at,
                s.updated_at,
                COUNT(h.id) AS total_mensagens
            FROM chat_sessions s
            LEFT JOIN chat_history h
                ON h.session_id = s.id
                AND h.usuario_id = s.usuario_id
            WHERE s.usuario_id = ?
            GROUP BY s.id
            ORDER BY s.updated_at DESC, s.id DESC
            """,
            (usuario_id,),
        ).fetchall()

    return [
        {
            "id": row["id"],
            "title": row["title"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
            "total_mensagens": row["total_mensagens"],
            "active": row["id"] == sessao_ativa,
        }
        for row in rows
    ]


def ativar_sessao_chat(session_id):
    usuario_id = usuario_chat_atual()

    with sqlite3.connect(CHAT_HISTORY_DB) as conn:
        cursor = conn.cursor()
        sessao = cursor.execute(
            """
            SELECT id
            FROM chat_sessions
            WHERE id = ? AND usuario_id = ?
            """,
            (session_id, usuario_id),
        ).fetchone()

    if not sessao:
        return False

    session["chat_session_id"] = session_id
    return True


def obter_historico_chat(limite=MAX_MENSAGENS_MEMORIA):
    usuario_id = usuario_chat_atual()
    sessao_id = garantir_sessao_chat_atual()

    with sqlite3.connect(CHAT_HISTORY_DB) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        rows = cursor.execute(
            """
            SELECT role, content
            FROM chat_history
            WHERE usuario_id = ? AND session_id = ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (usuario_id, sessao_id, limite),
        ).fetchall()

    return [
        {"role": row["role"], "content": row["content"]}
        for row in reversed(rows)
    ]


def salvar_no_historico_chat(role, content):
    usuario_id = usuario_chat_atual()
    sessao_id = garantir_sessao_chat_atual()
    conteudo_limitado = str(content)[:MAX_CARACTERES_MEMORIA]

    with sqlite3.connect(CHAT_HISTORY_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO chat_history (usuario_id, session_id, role, content)
            VALUES (?, ?, ?, ?)
            """,
            (usuario_id, sessao_id, role, conteudo_limitado),
        )
        cursor.execute(
            """
            UPDATE chat_sessions
            SET
                title = CASE
                    WHEN title = 'Novo chat' AND ? = 'user' THEN ?
                    ELSE title
                END,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ? AND usuario_id = ?
            """,
            (role, titulo_chat_por_mensagem(content), sessao_id, usuario_id),
        )
        cursor.execute(
            """
            DELETE FROM chat_history
            WHERE usuario_id = ?
              AND session_id = ?
              AND id NOT IN (
                SELECT id
                FROM chat_history
                WHERE usuario_id = ?
                  AND session_id = ?
                ORDER BY id DESC
                LIMIT ?
              )
            """,
            (
                usuario_id,
                sessao_id,
                usuario_id,
                sessao_id,
                MAX_MENSAGENS_HISTORICO_INTERFACE,
            ),
        )
        conn.commit()


def limpar_historico_chat(usuario_id=None, sessao_id=None):
    usuario_id = usuario_id or usuario_chat_atual()
    sessao_id = sessao_id or garantir_sessao_chat_atual()

    with sqlite3.connect(CHAT_HISTORY_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM chat_history WHERE usuario_id = ? AND session_id = ?",
            (usuario_id, sessao_id),
        )
        cursor.execute(
            """
            UPDATE chat_sessions
            SET title = 'Novo chat', updated_at = CURRENT_TIMESTAMP
            WHERE usuario_id = ? AND id = ?
            """,
            (usuario_id, sessao_id),
        )
        conn.commit()


def normalizar_texto_busca(valor):
    texto = " ".join(str(valor).lower().split())
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(
        caractere for caractere in texto if not unicodedata.combining(caractere)
    )
    substituicoes_mojibake = {
        "ãƒâ¡": "a",
        "ãƒâ ": "a",
        "ãƒâ¢": "a",
        "ãƒâ£": "a",
        "ãƒâ©": "e",
        "ãƒâª": "e",
        "ãƒâ­": "i",
        "ãƒâ³": "o",
        "ãƒâ´": "o",
        "ãƒâµ": "o",
        "ãƒâº": "u",
        "ãƒâ§": "c",
        "ã¡": "a",
        "ã ": "a",
        "ã¢": "a",
        "ã£": "a",
        "ã©": "e",
        "ãª": "e",
        "ã­": "i",
        "ã³": "o",
        "ã´": "o",
        "ãµ": "o",
        "ãº": "u",
        "ã§": "c",
    }

    for errado, correto in substituicoes_mojibake.items():
        texto = texto.replace(errado, correto)

    return texto


def corrigir_texto_mojibake(valor):
    if isinstance(valor, dict):
        return {
            corrigir_texto_mojibake(chave): corrigir_texto_mojibake(conteudo)
            for chave, conteudo in valor.items()
        }

    if isinstance(valor, list):
        return [corrigir_texto_mojibake(item) for item in valor]

    if not isinstance(valor, str) or not any(marcador in valor for marcador in ("Ã", "Â")):
        return valor

    texto = valor

    for _ in range(2):
        try:
            texto_corrigido = texto.encode("latin1").decode("utf-8")
        except UnicodeError:
            break

        if texto_corrigido == texto:
            break

        texto = texto_corrigido

    return texto


def caminho_base_conhecimento():
    for caminho in BASE_CONHECIMENTO_PATHS:
        if caminho and os.path.exists(caminho):
            return caminho

    return None


def carregar_dados_base_conhecimento():
    caminho = caminho_base_conhecimento()

    if not caminho:
        return None

    try:
        with open(caminho, "r", encoding="utf-8") as arquivo:
            dados = json.load(arquivo)
    except UnicodeDecodeError:
        with open(caminho, "r", encoding="latin1") as arquivo:
            dados = json.load(arquivo)
    except (OSError, json.JSONDecodeError) as erro:
        print("Erro ao carregar base de conhecimento:", erro)
        return None

    return corrigir_texto_mojibake(dados)


MESES_CALENDARIO = {
    "janeiro": 1,
    "fevereiro": 2,
    "marco": 3,
    "abril": 4,
    "maio": 5,
    "junho": 6,
    "julho": 7,
    "agosto": 8,
    "setembro": 9,
    "outubro": 10,
    "novembro": 11,
    "dezembro": 12,
}

DIAS_SEMANA_CALENDARIO = {
    "segunda-feira": 0,
    "terca-feira": 1,
    "quarta-feira": 2,
    "quinta-feira": 3,
    "sexta-feira": 4,
    "sabado": 5,
    "domingo": 6,
}


def texto_base_para_tela(valor):
    if not isinstance(valor, str):
        return valor

    texto = valor

    for _ in range(2):
        if not any(marcador in texto for marcador in ("\u00c3", "\u00c2")):
            break

        try:
            texto_corrigido = texto.encode("latin1").decode("utf-8")
        except UnicodeError:
            break

        if texto_corrigido == texto:
            break

        texto = texto_corrigido

    return texto


def chave_texto_calendario(valor):
    texto = texto_base_para_tela(str(valor or "")).lower()
    texto = unicodedata.normalize("NFD", texto)
    return "".join(letra for letra in texto if unicodedata.category(letra) != "Mn")


def data_br_para_date(valor):
    if not valor:
        return None

    try:
        return datetime.strptime(str(valor), "%d/%m/%Y").date()
    except ValueError:
        return None


def obter_ano_calendario_base(dados):
    curso = dados.get("curso", {})

    for chave in ("inicio_aulas", "fim_aulas"):
        data_curso = data_br_para_date(curso.get(chave))
        if data_curso:
            return data_curso.year

    return date.today().year


def expandir_datas_mes_calendario(texto_data, mes, ano):
    numeros = [int(numero) for numero in re.findall(r"\d{1,2}", str(texto_data or ""))]

    if not numeros:
        return []

    texto_normalizado = chave_texto_calendario(texto_data)

    if " a " in f" {texto_normalizado} " and len(numeros) >= 2:
        inicio = min(numeros[0], numeros[1])
        fim = max(numeros[0], numeros[1])
        numeros = list(range(inicio, fim + 1))

    datas = []
    for dia in numeros:
        try:
            datas.append(date(ano, mes, dia))
        except ValueError:
            continue

    return datas


def classificar_evento_calendario(evento):
    texto_evento = chave_texto_calendario(evento.get("evento"))
    texto_tipo = chave_texto_calendario(evento.get("tipo"))

    if "feriado" in texto_tipo or "feriado" in texto_evento or "recesso" in texto_evento:
        return "feriado"

    if "verificacao de aprendizagem" in texto_evento or " va" in texto_evento:
        return "prova"

    if "prazo" in texto_evento or "lancamento" in texto_evento:
        return "prazo"

    return "academico"


def adicionar_evento_calendario(eventos, data_evento, titulo, tipo, descricao="", origem=""):
    if not data_evento or not titulo:
        return

    eventos.append(
        {
            "data": data_evento.isoformat(),
            "titulo": texto_base_para_tela(titulo),
            "tipo": tipo,
            "descricao": texto_base_para_tela(descricao),
            "origem": texto_base_para_tela(origem),
        }
    )


def datas_periodo_avaliacao(item):
    data_unica = data_br_para_date(item.get("data"))
    if data_unica:
        return [data_unica]

    inicio = data_br_para_date(item.get("inicio"))
    fim = data_br_para_date(item.get("fim"))

    if not inicio or not fim:
        return []

    datas = []
    data_atual = inicio
    while data_atual <= fim:
        datas.append(data_atual)
        data_atual += timedelta(days=1)

    return datas


def montar_eventos_calendario_base(dados):
    eventos = []
    ano = obter_ano_calendario_base(dados)
    calendario_academico = dados.get("calendario_academico", {})

    for mes_nome, itens in calendario_academico.items():
        mes = MESES_CALENDARIO.get(chave_texto_calendario(mes_nome))
        if not mes:
            continue

        for item in itens:
            titulo = item.get("evento")
            tipo = classificar_evento_calendario(item)
            origem = item.get("tipo") or "Calendario academico"

            for data_evento in expandir_datas_mes_calendario(item.get("data"), mes, ano):
                adicionar_evento_calendario(eventos, data_evento, titulo, tipo, origem=origem)

    avaliacoes = dados.get("avaliacoes", {})
    for nome, valor in avaliacoes.items():
        nome_formatado = texto_base_para_tela(str(nome).replace("_", " ").upper())

        if isinstance(valor, list):
            for item in valor:
                numero = item.get("numero")
                titulo = f"{nome_formatado} {numero}" if numero else nome_formatado
                tipo = "prova" if str(nome).lower() == "vrau" else "avaliacao"

                datas = datas_periodo_avaliacao(item)
                for data_evento in datas:
                    adicionar_evento_calendario(
                        eventos,
                        data_evento,
                        titulo,
                        tipo,
                        descricao="",
                        origem="Avaliacoes",
                    )

                if datas and str(nome).lower() in ("a360", "afe"):
                    adicionar_evento_calendario(
                        eventos,
                        datas[0],
                        f"Simulado sugerido - {titulo}",
                        "simulado",
                        descricao="Revisao sugerida antes da avaliacao",
                        origem="Sugestao Vortex",
                    )

        elif isinstance(valor, dict):
            titulo = valor.get("descricao") or nome_formatado.title()
            for data_evento in datas_periodo_avaliacao(valor):
                adicionar_evento_calendario(
                    eventos,
                    data_evento,
                    titulo,
                    "prova",
                    descricao="Marco importante da disciplina",
                    origem="Avaliacoes",
                )

    curso = dados.get("curso", {})
    inicio_aulas = data_br_para_date(curso.get("inicio_aulas"))
    fim_aulas = data_br_para_date(curso.get("fim_aulas"))
    sala_principal = curso.get("sala_principal", "")

    adicionar_evento_calendario(
        eventos,
        inicio_aulas,
        "Inicio das aulas",
        "academico",
        descricao=sala_principal,
        origem="Curso",
    )
    adicionar_evento_calendario(
        eventos,
        fim_aulas,
        "Fim das aulas",
        "academico",
        descricao=sala_principal,
        origem="Curso",
    )

    dias_sem_aula = {
        date.fromisoformat(evento["data"])
        for evento in eventos
        if evento.get("tipo") == "feriado"
    }

    horarios = dados.get("horarios", [])
    if inicio_aulas and fim_aulas and horarios:
        data_atual = inicio_aulas

        while data_atual <= fim_aulas:
            if data_atual not in dias_sem_aula:
                for aula in horarios:
                    dia_semana = DIAS_SEMANA_CALENDARIO.get(chave_texto_calendario(aula.get("dia")))

                    if dia_semana != data_atual.weekday():
                        continue

                    descricao = (
                        f"{aula.get('inicio')} as {aula.get('fim')} - "
                        f"{aula.get('professor')} - {aula.get('local')}"
                    )
                    adicionar_evento_calendario(
                        eventos,
                        data_atual,
                        aula.get("materia"),
                        "aula",
                        descricao=descricao,
                        origem="Aula da semana",
                    )

            data_atual += timedelta(days=1)

    eventos.sort(key=lambda evento: (evento["data"], evento["tipo"], evento["titulo"]))
    return eventos


def juntar_valores(*valores):
    partes = []

    for valor in valores:
        if valor is None:
            continue

        if isinstance(valor, (list, tuple)):
            partes.extend(str(item) for item in valor if item)
        elif valor:
            partes.append(str(valor))

    return ", ".join(partes)


def adicionar_trecho(trechos, titulo, texto):
    texto = " ".join(str(texto).split())

    if not texto:
        return

    trechos.append(
        {
            "titulo": titulo,
            "texto": texto,
            "busca": normalizar_texto_busca(f"{titulo} {texto}"),
        }
    )


def formatar_periodo(item):
    if not isinstance(item, dict):
        return str(item)

    if item.get("data"):
        return f"data {item.get('data')}"

    if item.get("inicio") and item.get("fim"):
        return f"de {item.get('inicio')} ate {item.get('fim')}"

    return juntar_valores(*item.values())


def montar_trechos_base_conhecimento(dados):
    trechos = []
    universidade = dados.get("universidade")
    curso = dados.get("curso", {})

    adicionar_trecho(
        trechos,
        "Curso",
        (
            f"Universidade: {universidade}. Curso: {curso.get('nome')}. "
            f"Turno: {curso.get('turno')}. Modalidade: {curso.get('modalidade')}. "
            f"Sala principal: {curso.get('sala_principal')}. "
            f"Inicio das aulas: {curso.get('inicio_aulas')}. "
            f"Fim das aulas: {curso.get('fim_aulas')}."
        ),
    )

    materias = dados.get("materias", [])
    if materias:
        resumo_materias = []

        for materia in materias:
            professores = materia.get("professores") or materia.get("professor")
            texto_materia = (
                f"{materia.get('nome')} - professor(es): {juntar_valores(professores)}"
            )
            if materia.get("modalidade"):
                texto_materia += f" - modalidade: {materia.get('modalidade')}"

            resumo_materias.append(texto_materia)
            adicionar_trecho(trechos, f"Materia - {materia.get('nome')}", texto_materia)

        adicionar_trecho(trechos, "Materias do curso", "; ".join(resumo_materias))

    horarios = dados.get("horarios", [])
    if horarios:
        resumo_horarios = []

        for horario in horarios:
            texto_horario = (
                f"{horario.get('dia')}: {horario.get('materia')}, "
                f"professor {horario.get('professor')}, local {horario.get('local')}, "
                f"das {horario.get('inicio')} as {horario.get('fim')}."
            )
            resumo_horarios.append(texto_horario)
            adicionar_trecho(trechos, f"Horario - {horario.get('dia')}", texto_horario)

        adicionar_trecho(trechos, "Horarios das aulas", " ".join(resumo_horarios))

    avaliacoes = dados.get("avaliacoes", {})
    if avaliacoes:
        resumo_avaliacoes = []

        for nome, valor in avaliacoes.items():
            if isinstance(valor, list):
                for item in valor:
                    texto_avaliacao = (
                        f"{nome.upper()} {item.get('numero')}: {formatar_periodo(item)}."
                    )
                    resumo_avaliacoes.append(texto_avaliacao)
                    adicionar_trecho(trechos, f"Avaliacao - {nome.upper()}", texto_avaliacao)
            elif isinstance(valor, dict):
                texto_avaliacao = (
                    f"{nome.replace('_', ' ').title()}: {formatar_periodo(valor)}. "
                    f"{valor.get('descricao', '')}"
                )
                resumo_avaliacoes.append(texto_avaliacao)
                adicionar_trecho(trechos, f"Avaliacao - {nome}", texto_avaliacao)

        adicionar_trecho(trechos, "Avaliacoes", " ".join(resumo_avaliacoes))

    laboratorios = dados.get("laboratorios", [])
    if laboratorios:
        resumo_labs = []

        for laboratorio in laboratorios:
            texto_lab = f"{laboratorio.get('nome')}: {laboratorio.get('localizacao')}."
            resumo_labs.append(texto_lab)
            adicionar_trecho(trechos, f"Laboratorio - {laboratorio.get('nome')}", texto_lab)

        adicionar_trecho(trechos, "Laboratorios", " ".join(resumo_labs))

    calendario = dados.get("calendario_academico", {})
    for mes, eventos in calendario.items():
        textos_eventos = []

        for evento in eventos:
            texto_evento = (
                f"{mes.title()} dia {evento.get('data')}: {evento.get('evento')}"
            )
            if evento.get("tipo"):
                texto_evento += f" ({evento.get('tipo')})"

            texto_evento += "."
            textos_eventos.append(texto_evento)
            adicionar_trecho(trechos, f"Calendario - {mes}", texto_evento)

        adicionar_trecho(trechos, f"Calendario academico - {mes}", " ".join(textos_eventos))

    for item in dados.get("faq", []):
        adicionar_trecho(
            trechos,
            f"FAQ - {item.get('pergunta')}",
            f"Pergunta: {item.get('pergunta')} Resposta: {item.get('resposta')}",
        )

    return trechos


def carregar_trechos_base_conhecimento():
    caminho = caminho_base_conhecimento()

    if not caminho:
        return []

    mtime = os.path.getmtime(caminho)

    if (
        BASE_CONHECIMENTO_CACHE["path"] == caminho
        and BASE_CONHECIMENTO_CACHE["mtime"] == mtime
    ):
        return BASE_CONHECIMENTO_CACHE["trechos"]

    dados = carregar_dados_base_conhecimento()

    if not dados:
        return []

    trechos = montar_trechos_base_conhecimento(dados)
    BASE_CONHECIMENTO_CACHE.update({"path": caminho, "mtime": mtime, "trechos": trechos})
    return trechos


def palavras_busca(texto):
    palavras_ignoradas = {
        "a",
        "as",
        "com",
        "da",
        "de",
        "do",
        "dos",
        "e",
        "em",
        "eu",
        "fica",
        "ficam",
        "me",
        "minha",
        "o",
        "onde",
        "os",
        "para",
        "por",
        "qual",
        "quais",
        "quando",
        "que",
        "quem",
        "sobre",
        "um",
        "uma",
    }
    texto_normalizado = normalizar_texto_busca(texto)

    palavras = []

    for palavra in re.findall(r"\b[\w-]+\b", texto_normalizado):
        if palavra in palavras_ignoradas:
            continue

        if palavra.isdigit() or len(palavra) >= 3:
            palavras.append(palavra)

    return palavras


def termos_busca_base_conhecimento(prompt):
    texto = normalizar_texto_busca(prompt)
    termos = [(palavra, 2) for palavra in palavras_busca(prompt)]
    grupos_semanticos = (
        (
            ("onde", "local", "localizacao", "fica", "ficam", "sala", "bloco"),
            ("local", "localizacao", "sala", "bloco", "presencial", "presenciais"),
        ),
        (
            ("quando", "data", "dia", "periodo", "prazo"),
            ("data", "inicio", "fim", "periodo", "calendario"),
        ),
        (
            ("aula", "aulas", "materia", "materias", "disciplina", "disciplinas"),
            ("aula", "aulas", "materia", "materias", "sala"),
        ),
        (
            ("prova", "provas", "avaliacao", "avaliacoes", "va", "vrau", "a360", "afe"),
            ("avaliacao", "avaliacoes", "verificacao", "aprendizagem", "data", "periodo"),
        ),
        (
            ("professor", "professora", "professores", "ministra", "leciona"),
            ("professor", "professores", "materia", "disciplina"),
        ),
        (
            ("laboratorio", "laboratorios", "lab", "labs"),
            ("laboratorio", "laboratorios", "localizacao", "sala", "bloco"),
        ),
    )

    termos_existentes = {palavra for palavra, _ in termos}

    for gatilhos, expansoes in grupos_semanticos:
        if not any(gatilho in texto for gatilho in gatilhos):
            continue

        for expansao in expansoes:
            if expansao not in termos_existentes:
                termos.append((expansao, 1))
                termos_existentes.add(expansao)

    return termos


def pergunta_sobre_base_conhecimento(prompt):
    texto = normalizar_texto_busca(prompt)
    termos_base = (
        "a360",
        "afe",
        "aula",
        "aulas",
        "avaliacao",
        "avaliacoes",
        "bloco",
        "calendario academico",
        "curso",
        "disciplina",
        "disciplinas",
        "faculdade",
        "feriado",
        "fim das aulas",
        "horario",
        "horarios",
        "laboratorio",
        "laboratorios",
        "materia",
        "materias",
        "modalidade",
        "professor",
        "professora",
        "professores",
        "projeto",
        "projeto final",
        "sala",
        "semestre",
        "turno",
        "unieva",
        "unievangelica",
        "universidade",
        "va",
        "vrau",
    )
    dias_semana = (
        "segunda",
        "terca",
        "quarta",
        "quinta",
        "sexta",
        "sabado",
        "domingo",
    )
    meses = (
        "janeiro",
        "fevereiro",
        "marco",
        "abril",
        "maio",
        "junho",
        "julho",
    )

    return (
        any(termo in texto for termo in termos_base)
        or any(dia in texto for dia in dias_semana)
        or any(mes in texto for mes in meses)
    )


def buscar_trechos_base_conhecimento(prompt):
    if not pergunta_sobre_base_conhecimento(prompt):
        return []

    termos_busca = termos_busca_base_conhecimento(prompt)

    if not termos_busca:
        return []

    texto_prompt = normalizar_texto_busca(prompt)
    trechos_pontuados = []

    for trecho in carregar_trechos_base_conhecimento():
        busca = trecho["busca"]
        pontuacao = 0

        for palavra, peso in termos_busca:
            if palavra.isdigit():
                if re.search(rf"\b{re.escape(palavra)}\b", busca):
                    pontuacao += 5 * peso
            elif palavra in busca:
                pontuacao += (3 if len(palavra) >= 6 else 1) * peso

        frase_prompt = texto_prompt.strip()

        if frase_prompt and frase_prompt in busca:
            pontuacao += 8

        if pontuacao:
            trechos_pontuados.append((pontuacao, trecho))

    trechos_pontuados.sort(key=lambda item: item[0], reverse=True)
    trechos_ordenados = [trecho for _, trecho in trechos_pontuados]

    filtros_categoria = []

    if "laboratorio" in texto_prompt:
        filtros_categoria = ["laboratorio"]
    elif "vrau" in texto_prompt:
        filtros_categoria = ["vrau"]
    elif "a360" in texto_prompt:
        filtros_categoria = ["a360"]
    elif "afe" in texto_prompt:
        filtros_categoria = ["afe"]

    if filtros_categoria:
        trechos_filtrados = [
            trecho
            for trecho in trechos_ordenados
            if any(filtro in trecho["busca"] for filtro in filtros_categoria)
        ]

        if trechos_filtrados:
            return trechos_filtrados[:MAX_TRECHOS_BASE_CONHECIMENTO]

    return trechos_ordenados[:MAX_TRECHOS_BASE_CONHECIMENTO]


def montar_contexto_base_conhecimento(prompt):
    trechos = buscar_trechos_base_conhecimento(prompt)

    if not trechos:
        return None

    linhas = [
        "Base de conhecimento da faculdade encontrada para a pergunta do aluno:",
        "Use estes dados como fonte principal quando a pergunta for sobre faculdade, curso, aulas, professores, horarios, avaliacoes, calendario, laboratorios ou FAQ.",
        "Para perguntas sobre professores, responda apenas com nomes de professores que estejam nos trechos abaixo.",
        "Nao use nomes vindos do historico da conversa se eles contradisserem a base de conhecimento abaixo.",
        "Se o dado solicitado nao aparecer abaixo, diga que nao encontrou essa informacao na base.",
    ]

    for trecho in trechos:
        linhas.append(f"- {trecho['titulo']}: {trecho['texto']}")

    contexto = "\n".join(linhas)
    return contexto[:MAX_CARACTERES_CONTEXTO_CONHECIMENTO]


def resposta_fallback_base_conhecimento(prompt):
    trechos = buscar_trechos_base_conhecimento(prompt)

    if not trechos:
        return None

    texto_prompt = normalizar_texto_busca(prompt)
    numeros_prompt = re.findall(r"\b\d+\b", texto_prompt)

    for categoria in ("laboratorio", "vrau", "a360", "afe"):
        if categoria not in texto_prompt or not numeros_prompt:
            continue

        padroes = []

        for numero in numeros_prompt:
            padroes.append(f"{categoria} {numero}")

            if numero.isdigit():
                padroes.append(f"{categoria} {int(numero):02d}")

        trechos_exatos = [
            trecho
            for trecho in trechos
            if any(padrao in trecho["busca"] for padrao in padroes)
        ]

        if trechos_exatos:
            trechos = trechos_exatos
            break

    titulos_agregados = {
        "Avaliacoes",
        "Horarios das aulas",
        "Laboratorios",
        "Materias do curso",
    }
    trechos_especificos = [
        trecho for trecho in trechos if trecho["titulo"] not in titulos_agregados
    ]
    trechos_resposta = trechos_especificos or trechos
    linhas = [
        "Nao consegui acionar a IA agora, mas encontrei estes trechos na base de conhecimento:"
    ]

    for trecho in trechos_resposta[:3]:
        texto = trecho["texto"]

        if len(texto) > 320:
            texto = texto[:317].rstrip() + "..."

        linhas.append(f"- {texto}")

    return "\n".join(linhas)


def pergunta_sobre_aba_removida(prompt):
    texto = normalizar_texto_busca(prompt)
    perguntas_curtas_tarefas = {
        "tarefas",
        "a tarefas",
        "as tarefas",
        "onde fica tarefas",
        "onde fica a tarefas",
        "onde fica a aba tarefas",
        "cade tarefas",
        "cadÃª tarefas",
    }

    if texto in perguntas_curtas_tarefas:
        return True

    return any(normalizar_texto_busca(termo) in texto for termo in TERMOS_ABAS_REMOVIDAS)


def extrair_slot_nota(prompt):
    texto = normalizar_texto_busca(prompt)
    palavras_para_slots = {
        "primeira": 1,
        "segunda": 2,
        "terceira": 3,
        "quarta": 4,
        "quinta": 5,
    }

    for palavra, slot in palavras_para_slots.items():
        if re.search(rf"\b{palavra}\s+nota\b|\bnota\s+{palavra}\b", texto):
            return slot

    match_flexivel = re.search(
        r"\bnota\b(?:\s+(?:de|do|da|minha|numero|n(?:umero|o))){0,3}\s*([1-5])\b",
        texto,
    )

    if match_flexivel:
        return int(match_flexivel.group(1))

    match_notion = re.search(r"\b(?:notion|notas?)\b(?:\s+(?:de|do|da|minha))*\s*([1-5])\b", texto)

    if match_notion:
        return int(match_notion.group(1))

    match_direto = re.search(r"\bnota\s*(?:numero|n|no|n\u00ba)?\s*([1-5])\b", texto)

    if match_direto:
        return int(match_direto.group(1))

    match = re.search(r"\bnota\s*(?:n[uÃº]mero\s*)?([1-5])\b", texto)

    if not match:
        return None

    return int(match.group(1))


def pedido_para_salvar_no_notion(prompt):
    texto = normalizar_texto_busca(prompt)
    slot = extrair_slot_nota(texto)

    if not slot:
        return None

    acoes = (
        "coloque",
        "coloca",
        "colocar",
        "bote",
        "bota",
        "botar",
        "poe",
        "salve",
        "salvar",
        "adicione",
        "adicionar",
        "guarde",
        "guardar",
        "mande",
        "mandar",
        "jogue",
        "jogar",
        "anote",
        "anotar",
        "registre",
        "registrar",
    )
    destinos = ("notion", "nota", "notas", "anotacao", "anotaÃ§Ã£o")

    if any(acao in texto for acao in acoes) and "anotacoes" in texto:
        return slot

    if any(acao in texto for acao in acoes) and any(destino in texto for destino in destinos):
        return slot

    referencias_conteudo = (
        "explicacao",
        "explicaÃ§Ã£o",
        "resposta",
        "isso",
        "esse conteudo",
        "esse conteÃºdo",
        "essa explicacao",
        "essa explicaÃ§Ã£o",
        "o que voce explicou",
        "o que vocÃª explicou",
    )

    if any(acao in texto for acao in acoes) and any(
        referencia in texto for referencia in referencias_conteudo
    ):
        return slot

    return None


def resposta_assistente_salvavel(conteudo):
    texto = normalizar_texto_busca(conteudo)
    padroes_respostas_de_sistema = (
        r"\bpronto,\s+salvei\b",
        r"\bainda\s+nao\s+encontrei\b",
        r"\bnao\s+foi\s+possivel\s+salvar\b",
        r"\bcopie\b",
        r"\bcole\b",
        r"\bclique\s+no\s+widget\b",
        r"\bpoxa\b",
        r"\bnao\s+registrei\b",
        r"\bnao\s+registrei\s+a\s+nota\b",
    )

    return bool(texto) and not any(
        re.search(padrao, texto) for padrao in padroes_respostas_de_sistema
    )

def pedido_correcao_salvar_notion(prompt):
    texto = normalizar_texto_busca(prompt)
    reclamacoes = (
        "voce nao fez",
        "vocÃª nÃ£o fez",
        "nao fez",
        "nÃ£o fez",
        "nao salvou",
        "nÃ£o salvou",
        "nao colocou",
        "nÃ£o colocou",
        "nao foi para a nota",
        "nÃ£o foi para a nota",
    )

    return any(reclamacao in texto for reclamacao in reclamacoes)


def recuperar_slot_ultimo_pedido_notion():
    usuario_id = usuario_chat_atual()
    sessao_id = garantir_sessao_chat_atual()

    with sqlite3.connect(CHAT_HISTORY_DB) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        rows = cursor.execute(
            """
            SELECT content
            FROM chat_history
            WHERE usuario_id = ? AND session_id = ? AND role = 'user'
            ORDER BY id DESC
            LIMIT 10
            """,
            (usuario_id, sessao_id),
        ).fetchall()

    for row in rows:
        slot = pedido_para_salvar_no_notion(row["content"])

        if slot:
            return slot

    return None


def obter_ultima_resposta_assistente():
    usuario_id = usuario_chat_atual()
    sessao_id = garantir_sessao_chat_atual()

    with sqlite3.connect(CHAT_HISTORY_DB) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        rows = cursor.execute(
            """
            SELECT role, content
            FROM chat_history
            WHERE usuario_id = ? AND session_id = ?
            ORDER BY id DESC
            LIMIT 10
            """,
            (usuario_id, sessao_id),
        ).fetchall()

    for index, row in enumerate(rows):
        if row["role"] != "assistant" or not resposta_assistente_salvavel(row["content"]):
            continue

        pergunta = None

        for anterior in rows[index + 1 :]:
            if anterior["role"] == "user":
                pergunta = anterior["content"]
                break

        return row["content"], pergunta

    return None, None


def formatar_inline_nota(texto):
    texto_seguro = html_utils.escape(texto)
    texto_seguro = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", texto_seguro)
    texto_seguro = re.sub(r"`([^`]+)`", r"<code>\1</code>", texto_seguro)
    return texto_seguro


def markdown_para_html_nota(texto):
    linhas = str(texto).replace("\r\n", "\n").split("\n")
    partes = []
    lista_aberta = None
    codigo_aberto = False
    bloco_codigo = []

    def fechar_lista():
        nonlocal lista_aberta
        if lista_aberta:
            partes.append(f"</{lista_aberta}>")
            lista_aberta = None

    def fechar_codigo():
        nonlocal codigo_aberto, bloco_codigo
        if codigo_aberto:
            partes.append(
                f"<pre><code>{html_utils.escape(chr(10).join(bloco_codigo))}</code></pre>"
            )
            bloco_codigo = []
            codigo_aberto = False

    for linha in linhas:
        texto_linha = linha.strip()

        if texto_linha.startswith("```"):
            if codigo_aberto:
                fechar_codigo()
            else:
                fechar_lista()
                codigo_aberto = True
                bloco_codigo = []
            continue

        if codigo_aberto:
            bloco_codigo.append(linha)
            continue

        if not texto_linha:
            fechar_lista()
            continue

        titulo = re.match(r"^#{1,3}\s+(.+)", texto_linha)
        if titulo:
            fechar_lista()
            partes.append(f"<h2>{formatar_inline_nota(titulo.group(1))}</h2>")
            continue

        item_lista = re.match(r"^[-*]\s+(.+)", texto_linha)
        if item_lista:
            if lista_aberta != "ul":
                fechar_lista()
                partes.append("<ul>")
                lista_aberta = "ul"
            partes.append(f"<li>{formatar_inline_nota(item_lista.group(1))}</li>")
            continue

        item_ordenado = re.match(r"^\d+\.\s+(.+)", texto_linha)
        if item_ordenado:
            if lista_aberta != "ol":
                fechar_lista()
                partes.append("<ol>")
                lista_aberta = "ol"
            partes.append(f"<li>{formatar_inline_nota(item_ordenado.group(1))}</li>")
            continue

        fechar_lista()
        partes.append(f"<p>{formatar_inline_nota(texto_linha)}</p>")

    fechar_codigo()
    fechar_lista()

    return "".join(partes)


def titulo_nota_por_pergunta(pergunta, slot):
    if not pergunta:
        return f"Nota {slot}"

    titulo = re.sub(r"[^\w\s-]", "", str(pergunta)).strip()
    titulo = " ".join(titulo.split())

    if not titulo:
        return f"Nota {slot}"

    return titulo[:32]


def salvar_ultima_resposta_na_nota(slot):
    resposta, pergunta = obter_ultima_resposta_assistente()

    if not resposta:
        return (
            "Ainda nao encontrei uma explicacao anterior para salvar. "
            "Me peÃ§a primeiro para explicar algo e depois diga em qual nota devo colocar."
        )

    usuario_id = usuario_notas_atual()
    garantir_notas_usuario(usuario_id)
    conteudo_novo = markdown_para_html_nota(resposta)

    with sqlite3.connect(NOTION_DB) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        row = cursor.execute(
            """
            SELECT title, content_html
            FROM notion_notes
            WHERE usuario_id = ? AND slot = ?
            """,
            (usuario_id, slot),
        ).fetchone()

        titulo_atual = row["title"] if row else f"Nota {slot}"
        conteudo_atual = row["content_html"] if row else ""
        titulo = titulo_atual

        if titulo_atual == f"Nota {slot}":
            titulo = titulo_nota_por_pergunta(pergunta, slot)

        separador = "<hr>" if conteudo_atual.strip() else ""
        content_html = f"{conteudo_atual}{separador}{conteudo_novo}"
        cursor.execute(
            """
            UPDATE notion_notes
            SET title = ?, content_html = ?
            WHERE usuario_id = ? AND slot = ?
            """,
            (titulo, content_html, usuario_id, slot),
        )
        conn.commit()

    return f"Pronto, salvei essa explicacao na nota {slot} do Notion."


def bot(prompt):
    slot_nota = pedido_para_salvar_no_notion(prompt)

    if not slot_nota and pedido_correcao_salvar_notion(prompt):
        slot_nota = recuperar_slot_ultimo_pedido_notion()

    if slot_nota:
        resposta = salvar_ultima_resposta_na_nota(slot_nota)
        salvar_no_historico_chat("user", prompt)
        salvar_no_historico_chat("assistant", resposta)
        return resposta

    if pergunta_sobre_aba_removida(prompt):
        salvar_no_historico_chat("user", prompt)
        salvar_no_historico_chat("assistant", RESPOSTA_ABA_REMOVIDA)
        return RESPOSTA_ABA_REMOVIDA

    contexto_conhecimento = montar_contexto_base_conhecimento(prompt)

    try:
        from ollama import chat
    except ImportError:
        if contexto_conhecimento:
            resposta = resposta_fallback_base_conhecimento(prompt)
            salvar_no_historico_chat("user", prompt)
            salvar_no_historico_chat("assistant", resposta)
            return resposta

        return "O pacote ollama nÃ£o estÃ¡ instalado neste ambiente."

    historico = [
        mensagem
        for mensagem in obter_historico_chat(MAX_MENSAGENS_MEMORIA)
        if not pergunta_sobre_aba_removida(mensagem["content"])
    ]
    mensagens = [{"role": "system", "content": PROMPT_ASSISTENTE_VORTEX}]

    if contexto_conhecimento:
        mensagens.append({"role": "system", "content": contexto_conhecimento})

    mensagens.extend(historico)
    mensagens.append({"role": "user", "content": prompt})

    try:
        response = chat(
            model=MODELO_ESCOLHIDO,
            messages=mensagens,
        )
        resposta = response["message"]["content"]

        if not resposta.strip():
            return "A IA nao retornou uma resposta agora. Tente enviar a pergunta de novo em alguns segundos."

        salvar_no_historico_chat("user", prompt)
        salvar_no_historico_chat("assistant", resposta)
        return resposta
    except Exception as e:
        print("Erro no bot:", e)

        if contexto_conhecimento:
            resposta = resposta_fallback_base_conhecimento(prompt)
            salvar_no_historico_chat("user", prompt)
            salvar_no_historico_chat("assistant", resposta)
            return resposta

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


@app.route("/uploads/perfil/<path:filename>")
def perfil_upload(filename):
    return send_from_directory(PROFILE_UPLOAD_DIR, secure_filename(filename))


@app.route("/login", methods=["GET", "POST"])
def login():
    mensagem = None
    tipo_mensagem = None

    if request.method == "POST":
        matricula_digitada = request.form.get("matricula", "").strip()
        senha_digitada = request.form.get("senha", "").strip()

        if not matricula_digitada or not senha_digitada:
            mensagem = "Preencha matrÃ­cula e senha para entrar."
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

            mensagem = "MatrÃ­cula ou senha incorretos. Tente novamente."
            tipo_mensagem = "erro"
        except MYSQL_ERROR:
            mensagem = "NÃ£o foi possÃ­vel conectar ao banco agora. Verifique se o MySQL estÃ¡ ativo."
            tipo_mensagem = "erro"
        finally:
            if cursor:
                cursor.close()
            if conexao:
                conexao.close()

    return render_template("arthur.html", mensagem=mensagem, tipo_mensagem=tipo_mensagem)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/assistente")
@app.route("/home")
def assistente_academica():
    return render_template("marcos.html")


@app.route("/foco")
@app.route("/modo-foco")
def modo_foco():
    return redirect(url_for("assistente_academica"))


@app.route("/vark")
def vark():
    return redirect(url_for("assistente_academica"))


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


@app.route("/calendario/eventos")
def calendario_eventos():
    if "usuario_logado" not in session:
        return jsonify({"erro": "Faca login para ver o calendario."}), 401

    dados = carregar_dados_base_conhecimento()
    if not dados:
        return jsonify({"eventos": []})

    return jsonify({"eventos": montar_eventos_calendario_base(dados)})


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
        from ollama import chat

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
    return redirect(url_for("assistente_academica"))


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
    except MYSQL_ERROR:
        usuario_db = None
    finally:
        if cursor:
            cursor.close()
        if conexao:
            conexao.close()

    if not usuario_db:
        return "Erro: UsuÃ¡rio nÃ£o encontrado no banco."

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
    except MYSQL_ERROR as err:
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
        except MYSQL_ERROR as err:
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
        return "Mensagem nÃ£o enviada corretamente.", 400

    mensagem_usuario = dados["msg"]
    resposta_bot = bot(mensagem_usuario)

    return resposta_bot


@app.route("/chat/historico", methods=["GET", "DELETE"])
def historico_chat():
    if request.method == "DELETE":
        limpar_historico_chat()
        return jsonify({"ok": True})

    return jsonify(obter_historico_chat(MAX_MENSAGENS_HISTORICO_INTERFACE))


@app.route("/chat/sessoes", methods=["GET", "POST"])
def sessoes_chat():
    if request.method == "POST":
        session_id = criar_sessao_chat()
        return jsonify({"id": session_id, "sessoes": listar_sessoes_chat()}), 201

    return jsonify(
        {
            "active_session_id": garantir_sessao_chat_atual(),
            "sessoes": listar_sessoes_chat(),
        }
    )


@app.route("/chat/sessoes/<int:session_id>/ativar", methods=["POST"])
def ativar_chat(session_id):
    if not ativar_sessao_chat(session_id):
        return jsonify({"erro": "Chat nao encontrado."}), 404

    return jsonify(
        {
            "active_session_id": session_id,
            "historico": obter_historico_chat(MAX_MENSAGENS_HISTORICO_INTERFACE),
            "sessoes": listar_sessoes_chat(),
        }
    )


if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)
