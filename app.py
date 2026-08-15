import sqlite3
import requests
from flask import Flask, redirect, render_template_string, request, url_for

app = Flask(__name__)

TELEGRAM_TOKEN =  "SEU_TOKEN_AQUI"
CHAT_ID = "SEU_CHAT_ID_AQUI"

def init_db():
    conn = sqlite3.connect("estoque.db")
    c = conn.cursor()
    c.execute(
        """CREATE TABLE IF NOT EXISTS produtos 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  nome TEXT NOT NULL, 
                  quantidade INTEGER NOT NULL, 
                  limite_minimo INTEGER NOT NULL)"""
    )
    conn.commit()
    conn.close()


def enviar_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        requests.post(
            url, json={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"}
        )
    except Exception as e:
        print(f"Erro ao enviar: {e}")


HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Painel de Estoque</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
<style>
    body { font-family: Arial, sans-serif; margin: 15px; background: #f4f4f9; color: #333; }
    h2 { margin-bottom: 15px; }
    form.card { background: #fff; padding: 15px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); margin-bottom: 20px; }
    input, button { display: block; width: 100%; margin: 8px 0; padding: 12px; box-sizing: border-box; border-radius: 6px; border: 1px solid #ccc; font-size: 14px; }
    .btn-salvar { background: #28a745; color: white; border: none; font-weight: bold; cursor: pointer; }
    .btn-notificar { background: #007bff; color: white; border: none; font-weight: bold; cursor: pointer; }
    /* Novo layout dos cards de produtos */
    .item { background: #fff; padding: 12px 15px; margin-bottom: 10px; border-radius: 8px; border-left: 6px solid #28a745; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    .alerta { border-left-color: #dc3545; background: #ffe6e6; }
    .item-header { margin-bottom: 8px; font-size: 15px; line-height: 1.4; }
    .item-actions { text-align: right; margin: 0; }
    .btn-deletar { background: #dc3545; color: white; border: none; border-radius: 5px; padding: 6px 12px; cursor: pointer; width: auto; display: inline-block; font-size: 13px; font-weight: bold; margin: 0; }
</style>
</head>
<body>
    <h2>📦 Gestão de Estoque</h2>
    
    <form class="card" action="/adicionar" method="POST">
        <h3>Adicionar / Atualizar Produto</h3>
        <input type="text" name="nome" placeholder="Nome do Produto" required>
        <input type="number" name="quantidade" placeholder="Quantidade Atual" required>
        <input type="number" name="limite" placeholder="Estoque Mínimo (Alerta)" value="5" required>
        <button type="submit" class="btn-salvar">Salvar Produto</button>
    </form>

<h3>📋 Produtos Cadastrados</h3>
{% for item in produtos %}
    <div class="item {% if item[2] < item[3] %}alerta{% endif %}">
        <div class="item-header">
            <b>{{ item[1] }}</b> — Qtd: {{ item[2] }} <small>(Mín: {{ item[3] }})</small>
            {% if item[2] < item[3] %}
                <br><span style="color: #dc3545; font-weight: bold; font-size: 13px;">⚠️ Estoque Baixo!</span>
            {% endif %}
        </div>
        <form action="/deletar/{{ item[0] }}" method="POST" class="item-actions">
            <button type="submit" class="btn-deletar" onclick="return confirm('Deseja remover este produto?')">🗑️ Excluir</button>
        </form>
    </div>
{% else %}
    <p>Nenhum produto cadastrado no momento.</p>
{% endfor %}

    <br>
    <form action="/verificar" method="POST">
        <button type="submit" class="btn-notificar">🔔 Enviar Relatório no Telegram</button>
    </form>
</body>
</html>
"""


@app.route("/")
def index():
    init_db()
    conn = sqlite3.connect("estoque.db")
    c = conn.cursor()
    c.execute("SELECT id, nome, quantidade, limite_minimo FROM produtos")
    produtos = c.fetchall()
    conn.close()
    return render_template_string(HTML_TEMPLATE, produtos=produtos)


@app.route("/adicionar", methods=["POST"])
def adicionar():
    nome = request.form["nome"].strip()
    qtd = int(request.form["quantidade"])
    limite = int(request.form["limite"])

    conn = sqlite3.connect("estoque.db")
    c = conn.cursor()

    # Se digitar o mesmo nome, atualiza. Se for novo, insere.
    c.execute("SELECT id FROM produtos WHERE LOWER(nome) = LOWER(?)", (nome,))
    existe = c.fetchone()

    if existe:
        c.execute(
            "UPDATE produtos SET quantidade = ?, limite_minimo = ? WHERE id = ?",
            (qtd, limite, existe[0]),
        )
    else:
        c.execute(
            "INSERT INTO produtos (nome, quantidade, limite_minimo) VALUES (?, ?, ?)",
            (nome, qtd, limite),
        )

    conn.commit()
    conn.close()

    if qtd < limite:
        enviar_telegram(
            f"⚠️ *ALERTA DE ESTOQUE:* O produto *{nome}* está com apenas *{qtd}* unidades!"
        )

    return redirect(url_for("index"))


@app.route("/deletar/<int:id_produto>", methods=["POST"])
def deletar(id_produto):
    conn = sqlite3.connect("estoque.db")
    c = conn.cursor()
    c.execute("DELETE FROM produtos WHERE id = ?", (id_produto,))
    conn.commit()
    conn.close()
    return redirect(url_for("index"))


@app.route("/verificar", methods=["POST"])
def verificar():
    conn = sqlite3.connect("estoque.db")
    c = conn.cursor()
    c.execute("SELECT nome, quantidade, limite_minimo FROM produtos")
    todos = c.fetchall()
    conn.close()

    if todos:
        msg = "📊 *RELATÓRIO ATUAL DE ESTOQUE*\n\n"
        for nome, qtd, limite in todos:
            status = "⚠️ (BAIXO)" if qtd < limite else "✅ (OK)"
            msg += f"• *{nome}*: {qtd} un. {status}\n"
        enviar_telegram(msg)

    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

