from flask import Flask, request, redirect, session, render_template, g, jsonify, send_from_directory
from flask_socketio import SocketIO, emit
from werkzeug.utils import secure_filename
from jinja2 import ChoiceLoader, FileSystemLoader
import sqlite3
import hashlib
import os
import requests
import re
import json


app = Flask(__name__, template_folder="templates", static_folder="static")
app.secret_key = os.environ.get("SECRET_KEY", "chave_secreta")
app.jinja_loader = ChoiceLoader([
    FileSystemLoader(os.path.join(os.path.dirname(__file__), "templates")),
    FileSystemLoader(os.path.dirname(__file__)),
])
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

UPLOAD_FOLDER = os.path.join("static", "assets")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@socketio.on("login_check")
def login_check(data):
    if session.get("usuario"):
        emit("change_page", {"url": data.get("url")})
    else:
        emit("open_modal")


@socketio.on("buscarUser")
def buscar_user(data):
    print(data)
    if session.get("usuario"):
        if data["rota"] == "carrinho":
            emit("adicionar_roupa")
        elif data["rota"] == "wishlist":
            emit("adicionar_wishlist", { 'id': data['produto'] })
    else:
        emit("open_modal")


@socketio.on("carregar_produtos")
def carregar_produtos():
    with sqlite3.connect("noir.db") as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        produtos = cursor.execute("SELECT * FROM produtos").fetchall()

        resposta = []

        for p in produtos:
            fotos = cursor.execute(
                "SELECT caminho FROM fotos_produto WHERE produto_id = ? ORDER BY id ASC",
                (p["produto_id"],),
            ).fetchall()

            resposta.append(
                {
                    "produto_id": p["produto_id"],
                    "nome": p["nome"],
                    "preco": p["preco"],
                    "tipo": p["tipo"],
                    "quantidade": p["quantidade"],
                    "fotos": [f["caminho"] for f in fotos],  # lista das 4 imagens
                }
            )

        socketio.emit("renderizar_produtos", {"produtos": resposta})


@socketio.on("salvarFoto")
def salvar_foto(data):

    url = data.get("url")
    email = session.get("email")

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        """
                    UPDATE usuarios 
                    SET foto = ? 
                    WHERE email = ?
                """,
        (url, email),
    )

    conn.commit()
    conn.close()

    session["foto"] = url


@socketio.on("adicionarCarrinho")
def salvar_carrinho(data):
    user_id = obter_user()
    adicionar_ao_carrinho(user_id, data)


@socketio.on("adicionarWishlist")
def salvar_wishlist(data):
    user_id = obter_user()
    adicionar_a_wishlist(user_id, data)


@socketio.on("removerProduto")
def remover_item(data):
    print(data)

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        """
                   DELETE FROM carrinho WHERE id = ?""",
        (data["produtoId"],),
    )

    conn.commit()
    conn.close()


@socketio.on("removerWishlist")
def remover_wishlist(data):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        """
                   DELETE FROM wishlist WHERE id = ?""",
        (data["id"],),
    )

    conn.commit()
    conn.close()


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect("noir.db", timeout=30, check_same_thread=False)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA journal_mode=WAL;")
        g.db.execute("PRAGMA busy_timeout = 30000;")
    return g.db


@app.teardown_appcontext
def close_db(exception):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    conn = sqlite3.connect("noir.db")
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT,
            email TEXT UNIQUE,
            senha TEXT,
            foto TEXT,
            is_admin INTEGER DEFAULT 0
        )
    """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS produtos (
            produto_id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            tipo TEXT NOT NULL,
            tamanho TEXT NOT NULL,
            quantidade INTEGER NOT NULL,
            preco INTEGER NOT NULL,
            foto TEXT,
            descricao TEXT,
            tamanhos_disponiveis TEXT DEFAULT 'PP,P,M,G,GG'
        )
    """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS avaliacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
            produto_id INTEGER NOT NULL,
            nota REAL NOT NULL, -- Nota de 0 a 5
            FOREIGN KEY(usuario_id) REFERENCES usuarios(id),
            FOREIGN KEY(produto_id) REFERENCES produtos(produto_id),
            UNIQUE(usuario_id, produto_id) -- Garante apenas 1 avaliação por usuário/produto
        )
    """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS carrinho (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
            produto_id INTEGER NOT NULL,
            quantidade INTEGER NOT NULL,
            preco REAL NOT NULL,
            cupom TEXT,
            tamanho_selecionado TEXT,
            FOREIGN KEY(usuario_id) REFERENCES usuarios(id),
            FOREIGN KEY(produto_id) REFERENCES produtos(produto_id)
        )
    """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS cupom (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cupom TEXT UNIQUE,
            desconto REAL NOT NULL
        )
    """
    )

    try:
        cursor.execute("ALTER TABLE usuarios ADD COLUMN is_admin INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass

    try:
        cursor.execute("SELECT descricao FROM produtos LIMIT 1")
    except sqlite3.OperationalError:
        cursor.execute("ALTER TABLE produtos ADD COLUMN descricao TEXT")

    try:
        cursor.execute("SELECT tamanhos_disponiveis FROM produtos LIMIT 1")
    except sqlite3.OperationalError:
        cursor.execute(
            "ALTER TABLE produtos ADD COLUMN tamanhos_disponiveis TEXT DEFAULT 'PP,P,M,G,GG'"
        )

    # Migrações para a tabela carrinho
    for col_def in [
        "usuario_id INTEGER",
        "cliente_id INTEGER",
        "dados_produto TEXT",
        "cupom TEXT",
        "quantidade INTEGER DEFAULT 1",
        "preco REAL DEFAULT 0",
        "tamanho_selecionado TEXT",
    ]:
        try:
            cursor.execute(f"ALTER TABLE carrinho ADD COLUMN {col_def}")
        except sqlite3.OperationalError:
            pass

    # Garante que a tabela wishlist exista
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS wishlist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente_id INTEGER,
            produto_id INTEGER,
            dados_produto TEXT
        )
    """
    )

    # Garante que fotos_produto exista
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS fotos_produto (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            produto_id INTEGER,
            caminho TEXT
        )
    """
    )

    # Sincroniza usuario_id e cliente_id se um deles estiver preenchido e o outro nulo
    cursor.execute("UPDATE carrinho SET usuario_id = cliente_id WHERE usuario_id IS NULL AND cliente_id IS NOT NULL")
    cursor.execute("UPDATE carrinho SET cliente_id = usuario_id WHERE cliente_id IS NULL AND usuario_id IS NOT NULL")

    conn.commit()
    conn.close()


init_db()


def hash_senha(senha):
    return hashlib.sha256(senha.encode()).hexdigest()


@app.route("/")
def home():

    return render_template(
        "index.html",
        logado=True,
        usuario=session["usuario"] if "usuario" in session else None,
        is_admin=session.get("is_admin", False),
    )


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        senha = request.form["password"]

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, nome, email, is_admin FROM usuarios WHERE email = ? AND senha = ?",
            (email, hash_senha(senha)),
        )
        usuario = cursor.fetchone()
        conn.close()

        if usuario:
            session["usuario_id"] = usuario["id"]
            session["usuario"] = usuario["nome"]
            session["email"] = email
            session["is_admin"] = bool(usuario["is_admin"])
            return redirect("/")
        else:
            return render_template("login.html", erro="Email ou senha incorretos!")

    return render_template("login.html")


@app.route("/cadastro", methods=["GET", "POST"])
def cadastro():
    if request.method == "POST":
        nome = request.form["username"]
        email = request.form["email"]
        senha = request.form["password"]

        conn = get_db()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO usuarios (nome, email, senha) VALUES (?, ?, ?)",
                (nome, email, hash_senha(senha)),
            )
            conn.commit()
            conn.close()
            return redirect("/login")
        except sqlite3.IntegrityError:
            conn.close()
            return render_template("cadastro.html", erro="Email já existe!")

    return render_template("cadastro.html")


@app.route("/visualizar", methods=["GET", "POST"])
def visualizar():
    return render_template("visualizer.html")


def adicionar_ao_carrinho(cliente_id, produto):
    conn = get_db()
    cursor = conn.cursor()

    dados_json = json.dumps(produto)
    dados = produto.get("produto", {})
    tamanho = produto.get("tamanho", "M")
    produto_id = dados.get("produto_id")
    preco = dados.get("preco", 0)

    cursor.execute(
        """
        INSERT INTO carrinho (cliente_id, usuario_id, produto_id, dados_produto, tamanho_selecionado, preco, quantidade)
        VALUES (?, ?, ?, ?, ?, ?, 1)
    """,
        (cliente_id, cliente_id, produto_id, dados_json, tamanho, preco),
    )

    conn.commit()
    conn.close()


def adicionar_a_wishlist(cliente_id, produto):
    conn = get_db()
    cursor = conn.cursor()

    dados_json = json.dumps(produto)
    dados = produto.get("produto", {})
    id = dados.get("produto_id")

    cursor.execute(
        """
                   SELECT * FROM wishlist WHERE (cliente_id = ? OR cliente_id IS NULL) AND produto_id = ?""",
        (cliente_id, id),
    )

    cadastrado = cursor.fetchone()
    if cadastrado:
        print("já cadastrado!")
        conn.close()
        return

    cursor.execute(
        """
        INSERT INTO wishlist (cliente_id, produto_id, dados_produto)
        VALUES (?, ?, ?)
    """,
        (cliente_id, id, dados_json),
    )

    print("dados enviados com sucesso! dados:" + dados_json)

    conn.commit()
    conn.close()


def obter_carrinho():
    user_id = obter_user()
    if not user_id:
        return []

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        """
                   SELECT * FROM carrinho WHERE cliente_id = ? OR usuario_id = ?""",
        (user_id, user_id),
    )

    colunas = cursor.fetchall()
    carrinho = [dict(row) for row in colunas]

    return carrinho


def obter_wishlist():
    user_id = obter_user()
    if not user_id:
        return []

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        """
                   SELECT * FROM wishlist WHERE cliente_id = ?""",
        (user_id,),
    )

    colunas = cursor.fetchall()
    wishlist = [dict(row) for row in colunas]

    return wishlist


def obter_user():
    if "usuario_id" in session:
        return session["usuario_id"]

    email = session.get("email")
    if not email:
        return None

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        """SELECT id FROM usuarios WHERE email = ?
                   """,
        (email,),
    )
    row = cursor.fetchone()
    if row:
        session["usuario_id"] = row[0]
        return row[0]
    return None


def calcular_compra():
    carrinho_bruto = obter_carrinho()

    carrinho = []
    for item in carrinho_bruto:
        if item.get("dados_produto"):
            try:
                dados_produto_dict = json.loads(item["dados_produto"])
                item["produto_info"] = dados_produto_dict.get("produto", {})
            except Exception:
                item["produto_info"] = {"preco": item.get("preco", 0)}
        else:
            item["produto_info"] = {"preco": item.get("preco", 0)}
        carrinho.append(item)

    valor_compra = 0
    for item in carrinho:
        valor_item = item.get("produto_info", {}).get("preco", 0)
        valor_compra += valor_item

    return valor_compra


@app.route("/carrinho", methods=["GET", "POST"])
def carrinho():
    if not obter_user():
        return redirect("/login")

    carrinho_bruto = obter_carrinho()

    carrinho = []
    for item in carrinho_bruto:
        item_copy = dict(item)
        if item_copy.get("dados_produto"):
            try:
                dados_produto_dict = json.loads(item_copy["dados_produto"])
                item_copy["produto_info"] = dados_produto_dict.get("produto", {})
            except Exception:
                item_copy["produto_info"] = {
                    "preco": item_copy.get("preco", 0),
                    "nome": "",
                    "tipo": "",
                    "fotos": ["placeholder.png"],
                }
            if "dados_produto" in item_copy:
                del item_copy["dados_produto"]
        else:
            item_copy["produto_info"] = {
                "preco": item_copy.get("preco", 0),
                "nome": "",
                "tipo": "",
                "fotos": ["placeholder.png"],
            }
        carrinho.append(item_copy)
    valor_compra = calcular_compra()
    return render_template("bag.html", carrinho=carrinho, valor_compra=valor_compra)


@app.route("/wishlist")
def wishlist():
    if not obter_user():
        return redirect("/login")

    wishlist_bruta = obter_wishlist()

    wishlist = []
    for item in wishlist_bruta:
        item_copy = dict(item)
        if item_copy.get("dados_produto"):
            try:
                dados_produto_dict = json.loads(item_copy["dados_produto"])
                item_copy["produto_info"] = dados_produto_dict.get("produto", {})
            except Exception:
                item_copy["produto_info"] = {"fotos": ["placeholder.png"]}
            if "dados_produto" in item_copy:
                del item_copy["dados_produto"]
        wishlist.append(item_copy)

    return render_template("wishlist.html", wishlist=wishlist)


@app.route("/produtos", methods=["GET", "POST"])
def produtos():
    if "usuario_id" not in session:
        return redirect("/login")

    if not session.get("is_admin", False):
        return "Acesso negado! Você precisa ser administrador.", 403

    conn = get_db()

    with sqlite3.connect("noir.db", timeout=10, check_same_thread=False) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # --- SE FOR POST: inserção ---
        if request.method == "POST":
            nome_bruto = request.form["nome"]
            tipo_bruto = request.form["tipo"]
            tamanho = request.form.get("tamanho", "")
            quantidade = int(request.form["quantidade"])
            preco = int(float(request.form["preco"].replace(",", ".")) * 100)

            nome = nome_bruto.upper()
            tipo = tipo_bruto.upper()

            cursor.execute(
                """
                INSERT INTO produtos (nome, tipo, tamanho, quantidade, preco)
                VALUES (?, ?, ?, ?, ?)
            """,
                (nome, tipo, tamanho, quantidade, preco),
            )

            produto_id = cursor.lastrowid

            foto1 = request.files.get("foto1")
            foto2 = request.files.get("foto2")
            foto3 = request.files.get("foto3")
            foto4 = request.files.get("foto4")
            fotos = [foto1, foto2, foto3, foto4]

            for foto in fotos:
                if foto.filename != "":
                    foto_filename = secure_filename(foto.filename)
                    foto.save(os.path.join(UPLOAD_FOLDER, foto_filename))

                    cursor.execute(
                        """
                    INSERT INTO fotos_produto (produto_id, caminho)
                    VALUES (?, ?)
                    """,
                        (produto_id, foto_filename),
                    )

            conn.commit()

        # --- SEMPRE: buscar lista ---
        cursor.execute("SELECT * FROM produtos ORDER BY produto_id DESC")
        produtos_lista = cursor.fetchall()

    return render_template("prateleira.html", produtos=produtos_lista)


@app.route("/perfil")
def perfil():
    user_id = obter_user()
    if not user_id:
        return redirect("/login")

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT foto FROM usuarios WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    foto_url = row["foto"] if (row and row["foto"]) else None

    return render_template(
        "perfil.html",
        usuario=session.get("usuario"),
        email=session.get("email"),
        foto=foto_url,
    )


@app.route("/faq")
def faq():
    return render_template("faq.html")


@app.route("/dashboard")
def dashboard():
    return redirect("/produtos")


@app.route("/remover_do_carrinho/<int:produto_id>", methods=["POST"])
def remover_do_carrinho(produto_id):
    user_id = obter_user()
    if user_id:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM carrinho WHERE (usuario_id = ? OR cliente_id = ?) AND produto_id = ?",
            (user_id, user_id, produto_id),
        )
        conn.commit()
    return redirect("/carrinho")


@app.route("/adicionar_ao_carrinho/<int:produto_id>", methods=["POST"])
def adicionar_ao_carrinho_route(produto_id):
    user_id = obter_user()
    if not user_id:
        return redirect("/login")

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM produtos WHERE produto_id = ?", (produto_id,))
    prod = cursor.fetchone()
    if prod:
        fotos = cursor.execute(
            "SELECT caminho FROM fotos_produto WHERE produto_id = ?", (produto_id,)
        ).fetchall()
        prod_data = {
            "produto": {
                "produto_id": prod["produto_id"],
                "nome": prod["nome"],
                "preco": prod["preco"],
                "tipo": prod["tipo"],
                "quantidade": prod["quantidade"],
                "fotos": [f["caminho"] for f in fotos] if fotos else ["placeholder.png"],
            },
            "tamanho": prod["tamanho"].split(",")[0] if prod["tamanho"] else "M",
        }
        adicionar_ao_carrinho(user_id, prod_data)
    return redirect("/carrinho")


@app.route("/favicon/<path:filename>")
@app.route("/favicon.ico")
def favicon(filename="logo.png"):
    return send_from_directory("static/assets", filename)


@app.route("/font/<path:filename>")
@app.route("/fonts/<path:filename>")
@app.route("/static/font/<path:filename>")
@app.route("/static/fonts/<path:filename>")
@app.route("/static/styles/font/<path:filename>")
def fonts(filename):
    return send_from_directory("static/fonts", filename)


@app.route("/aplicar_cupom", methods=["POST"])
def aplicar_cupom():
    user_id = obter_user()
    if not user_id:
        return redirect("/login")

    codigo_cupom = request.form.get("cupom", "").strip().upper()
    if not codigo_cupom:
        return redirect("/carrinho")

    conn = get_db()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # Verifica se o cupom existe
    cur.execute("SELECT * FROM cupom WHERE UPPER(cupom) = ?", (codigo_cupom,))
    cupom = cur.fetchone()

    if not cupom:
        session["mensagem_cupom"] = "Cupom inválido!"
        return redirect("/carrinho")

    # Obtém o desconto (ex: 0.10 para 10%)
    desconto = float(cupom["desconto"])

    # Aplica o cupom a todos os itens do carrinho do usuário
    cur.execute(
        "UPDATE carrinho SET cupom = ? WHERE usuario_id = ? OR cliente_id = ?",
        (codigo_cupom, user_id, user_id),
    )
    conn.commit()

    # Salva o estado na sessão
    session["cupom_aplicado"] = codigo_cupom
    session["desconto"] = desconto
    session["mensagem_cupom"] = (
        f"Cupom '{codigo_cupom}' aplicado! ({int(desconto * 100)}% de desconto)"
    )

    return redirect("/carrinho")


categoria = {
    "CALÇADOS": 1.2,
    "ACESSORIOS": 0.3,
    "CALÇA": 0.8,
    "JAQUETA": 0.8,
    "ROUPA": 0.8,
    "DEFAULT": 0.8,
}


def get_peso_por_tipo(tipo_produto):
    tipo_normalizado = tipo_produto.upper().strip()

    # Mapeia tipos comuns de 'roupas' para a categoria principal
    if tipo_normalizado in ["CALÇA", "JAQUETA", "CAMISETA", "MOLETOM"]:
        return categoria["ROUPA"]

    # Retorna o peso se encontrado, senão usa o padrão
    return categoria.get(tipo_normalizado, categoria["DEFAULT"])


def obter_regiao(uf):
    regioes = {
        "Norte": ["AC", "AP", "AM", "PA", "RO", "RR", "TO"],
        "Nordeste": ["AL", "BA", "CE", "MA", "PB", "PE", "PI", "RN", "SE"],
        "Centro-Oeste": ["DF", "GO", "MT", "MS"],
        "Sudeste": ["ES", "MG", "RJ", "SP"],
        "Sul": ["PR", "RS", "SC"],
    }
    for regiao, estados in regioes.items():
        if uf in estados:
            return regiao
    return "Desconhecida"


def obter_fator(regiao):
    fatores = {
        "Sudeste": 1.0,
        "Sul": 1.1,
        "Centro-Oeste": 1.25,
        "Nordeste": 1.4,
        "Norte": 1.6,
        "Desconhecida": 1.8,  # Fator padrão
    }
    return fatores.get(regiao, 1.8)


@app.route("/calcular_frete", methods=["POST"])
def calcular_frete_api():
    user_id = obter_user()
    if not user_id:
        return jsonify({"erro": "Usuário não logado"}), 401

    # Pega o CEP do formulário e limpa (remove não-dígitos)
    cep = request.form.get("cep", "")
    cep_limpo = "".join(filter(str.isdigit, cep))

    if len(cep_limpo) != 8:
        return jsonify({"erro": "CEP inválido. Forneça 8 dígitos."}), 400

    conn = get_db()
    cur = conn.cursor()

    # 1. Buscar itens do carrinho e juntar com produtos para obter tipo, preco e quantidade
    cur.execute(
        """
        SELECT c.id, c.produto_id, c.quantidade, c.preco, c.dados_produto, p.tipo, p.nome
        FROM carrinho c
        LEFT JOIN produtos p ON c.produto_id = p.produto_id
        WHERE c.usuario_id = ? OR c.cliente_id = ?
    """,
        (user_id, user_id),
    )
    itens_carrinho = cur.fetchall()

    if not itens_carrinho:
        return jsonify({"erro": "Seu carrinho está vazio"}), 400

    # Calcula peso total e valor total (em centavos)
    peso_total_kg = 0.0
    valor_pedido_total_cents = 0

    for item in itens_carrinho:
        tipo = item["tipo"]
        preco = item["preco"] or 0
        qtd = item["quantidade"] or 1
        if item["dados_produto"]:
            try:
                dp = json.loads(item["dados_produto"])
                prod_info = dp.get("produto", {})
                if not tipo:
                    tipo = prod_info.get("tipo", "DEFAULT")
                if not preco:
                    preco = prod_info.get("preco", 0)
            except Exception:
                pass
        if not tipo:
            tipo = "DEFAULT"

        peso_item = get_peso_por_tipo(tipo)
        peso_total_kg += peso_item * qtd
        valor_pedido_total_cents += int(preco) * int(qtd)

    desconto = session.get("desconto", 0)
    if desconto > 0:
        valor_pedido_total_cents = int(valor_pedido_total_cents * (1 - desconto))

    try:
        res = requests.get(f"https://viacep.com.br/ws/{cep_limpo}/json/", timeout=5)
        res.raise_for_status()  # Lança exceção para erros HTTP (4xx, 5xx)
        dados_cep = res.json()

        if dados_cep.get("erro"):
            return jsonify({"erro": "CEP não encontrado"}), 404

    except requests.RequestException as e:
        print(f"Erro na API ViaCEP: {e}")
        return (
            jsonify({"erro": "Não foi possível consultar o CEP. Tente novamente."}),
            500,
        )

    uf = dados_cep.get("uf")
    regiao = obter_regiao(uf)
    fator = obter_fator(regiao)

    frete_cents = int((peso_total_kg * 5) * fator * 100)

    if valor_pedido_total_cents >= 15000:
        frete_cents = 0

    frete_gratis = frete_cents == 0

    resultado = {
        "cidade": dados_cep.get("localidade"),
        "uf": uf,
        "regiao": regiao,
        "cep": dados_cep.get("cep"),
        "peso_total_kg": round(peso_total_kg, 2),
        "valor_pedido_reais": round(valor_pedido_total_cents / 100.0, 2),
        "valor_frete_reais": round(frete_cents / 100.0, 2),
        "frete_gratis": frete_gratis,
        "mensagem_frete": (
            "Grátis 🎉" if frete_gratis else f"R$ {round(frete_cents / 100.0, 2):.2f}"
        ),
        "cupom_aplicado": session.get("cupom_aplicado"),
        "desconto_aplicado": int(desconto * 100) if desconto > 0 else 0,
    }

    return jsonify(resultado)


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "false").lower() in ["1", "true"]
    socketio.run(app, debug=debug, host="0.0.0.0", port=port, allow_unsafe_werkzeug=True)

