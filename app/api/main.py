import os
import json
import secrets
import psycopg2
import boto3
import requests
from flask import Flask, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

DB_HOST = os.environ["DB_HOST"]
DB_NAME = os.environ["DB_NAME"]
DB_USER = os.environ["DB_USER"]
DB_PASSWORD = os.environ["DB_PASSWORD"]
S3_BUCKET = os.environ["S3_BUCKET"]
AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")
MODERADOR_URL = os.environ.get("MODERADOR_URL", "http://moderador:5001")

TOKENS = {}
s3 = boto3.client("s3", region_name=AWS_REGION)


def db():
    return psycopg2.connect(
        host=DB_HOST, dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD,
        sslmode="require"
    )


def init_db():
    conn = db()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id SERIAL PRIMARY KEY,
            nombre_usuario TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            fecha_registro TIMESTAMP DEFAULT NOW()
        );
        CREATE TABLE IF NOT EXISTS hilos (
            id SERIAL PRIMARY KEY,
            usuario_id INT REFERENCES usuarios(id),
            titulo TEXT NOT NULL,
            categoria TEXT,
            fecha_creacion TIMESTAMP DEFAULT NOW()
        );
        CREATE TABLE IF NOT EXISTS comentarios (
            id SERIAL PRIMARY KEY,
            hilo_id INT REFERENCES hilos(id),
            usuario_id INT REFERENCES usuarios(id),
            texto TEXT NOT NULL,
            estado TEXT DEFAULT 'pendiente',
            fecha TIMESTAMP DEFAULT NOW()
        );
        CREATE TABLE IF NOT EXISTS calificaciones (
            id SERIAL PRIMARY KEY,
            hilo_id INT REFERENCES hilos(id),
            usuario_id INT REFERENCES usuarios(id),
            puntuacion INT CHECK (puntuacion BETWEEN 1 AND 5),
            fecha TIMESTAMP DEFAULT NOW()
        );
    """)
    conn.commit()
    cur.close()
    conn.close()


def usuario_actual():
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return None
    return TOKENS.get(auth.split(" ", 1)[1])


@app.route("/salud")
def salud():
    return jsonify({"status": "ok"}), 200


@app.route("/registro", methods=["POST"])
def registro():
    data = request.get_json(force=True)
    nombre_usuario = data.get("nombre_usuario")
    email = data.get("email")
    password = data.get("password")
    if not all([nombre_usuario, email, password]):
        return jsonify({"error": "faltan campos"}), 400
    conn = db()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO usuarios (nombre_usuario, email, password_hash) VALUES (%s, %s, %s) RETURNING id",
            (nombre_usuario, email, generate_password_hash(password)),
        )
        usuario_id = cur.fetchone()[0]
        conn.commit()
    except psycopg2.errors.UniqueViolation:
        conn.rollback()
        return jsonify({"error": "usuario o email ya existe"}), 409
    finally:
        cur.close()
        conn.close()
    return jsonify({"id": usuario_id}), 201


@app.route("/login", methods=["POST"])
def login():
    data = request.get_json(force=True)
    nombre_usuario = data.get("nombre_usuario")
    password = data.get("password")
    conn = db()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, password_hash FROM usuarios WHERE nombre_usuario = %s",
        (nombre_usuario,),
    )
    row = cur.fetchone()
    cur.close()
    conn.close()
    if not row or not check_password_hash(row[1], password or ""):
        return jsonify({"error": "credenciales invalidas"}), 401
    token = secrets.token_hex(16)
    TOKENS[token] = row[0]
    return jsonify({"token": token}), 200


@app.route("/hilos", methods=["POST"])
def crear_hilo():
    usuario_id = usuario_actual()
    if not usuario_id:
        return jsonify({"error": "no autenticado"}), 401
    data = request.get_json(force=True)
    titulo = data.get("titulo")
    categoria = data.get("categoria", "")
    if not titulo:
        return jsonify({"error": "falta titulo"}), 400
    conn = db()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO hilos (usuario_id, titulo, categoria) VALUES (%s, %s, %s) RETURNING id",
        (usuario_id, titulo, categoria),
    )
    hilo_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"id": hilo_id}), 201


@app.route("/hilos", methods=["GET"])
def listar_hilos():
    conn = db()
    cur = conn.cursor()
    cur.execute("""
        SELECT h.id, h.titulo, h.categoria, u.nombre_usuario, h.fecha_creacion
        FROM hilos h JOIN usuarios u ON h.usuario_id = u.id
        ORDER BY h.fecha_creacion DESC
    """)
    filas = cur.fetchall()
    cur.close()
    conn.close()
    hilos = [
        {"id": r[0], "titulo": r[1], "categoria": r[2], "autor": r[3], "fecha": str(r[4])}
        for r in filas
    ]
    return jsonify(hilos), 200


@app.route("/hilos/<int:hilo_id>/comentarios", methods=["POST"])
def crear_comentario(hilo_id):
    usuario_id = usuario_actual()
    if not usuario_id:
        return jsonify({"error": "no autenticado"}), 401
    data = request.get_json(force=True)
    texto = data.get("texto")
    if not texto:
        return jsonify({"error": "falta texto"}), 400

    veredicto = requests.post(
        f"{MODERADOR_URL}/moderar", json={"texto": texto}, timeout=5
    ).json()
    estado = "aprobado" if veredicto.get("aprobado") else "rechazado"

    conn = db()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO comentarios (hilo_id, usuario_id, texto, estado) VALUES (%s, %s, %s, %s) RETURNING id",
        (hilo_id, usuario_id, texto, estado),
    )
    comentario_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()

    if estado == "rechazado":
        s3.put_object(
            Bucket=S3_BUCKET,
            Key=f"moderacion/rechazados/{comentario_id}.json",
            Body=json.dumps({
                "comentario_id": comentario_id,
                "hilo_id": hilo_id,
                "texto": texto,
                "motivo": veredicto.get("motivo"),
            }),
        )

    return jsonify({"id": comentario_id, "estado": estado}), 201


@app.route("/hilos/<int:hilo_id>/comentarios", methods=["GET"])
def listar_comentarios(hilo_id):
    conn = db()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, texto, estado, fecha FROM comentarios WHERE hilo_id = %s AND estado = 'aprobado' ORDER BY fecha",
        (hilo_id,),
    )
    filas = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify([
        {"id": r[0], "texto": r[1], "estado": r[2], "fecha": str(r[3])} for r in filas
    ]), 200


@app.route("/hilos/<int:hilo_id>/calificaciones", methods=["POST"])
def crear_calificacion(hilo_id):
    usuario_id = usuario_actual()
    if not usuario_id:
        return jsonify({"error": "no autenticado"}), 401
    data = request.get_json(force=True)
    puntuacion = data.get("puntuacion")
    if puntuacion not in [1, 2, 3, 4, 5]:
        return jsonify({"error": "puntuacion debe ser 1-5"}), 400
    conn = db()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO calificaciones (hilo_id, usuario_id, puntuacion) VALUES (%s, %s, %s) RETURNING id",
        (hilo_id, usuario_id, puntuacion),
    )
    calificacion_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"id": calificacion_id}), 201


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000)
