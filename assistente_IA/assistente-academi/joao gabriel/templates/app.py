from flask import Flask, render_template, jsonify
import random
from tarefas import tarefas

app = Flask(__name__)
TOTAL_SUGESTOES = 4


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/sugestoes")
def sugestoes():
    quantidade = min(TOTAL_SUGESTOES, len(tarefas))
    tarefas_escolhidas = random.sample(tarefas, quantidade)
    return jsonify(tarefas_escolhidas)


if __name__ == "__main__":
    app.run(debug=True)