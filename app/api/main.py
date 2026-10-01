import os
import json
import secrets

import boto3
import psycopg2
import requests
from flask import Flask, request, jsonify, render_template
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
        host=DB_HOST,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        sslmode="require",
    )


def init_db():
    conn = db()
    cur = conn.cursor()

    cur.execute(
        """
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
        """
    )

    # Agrega soporte para roles sin borrar usuarios existentes.
    cur.execute(
        """
        ALTER TABLE usuarios
        ADD COLUMN IF NOT EXISTS rol TEXT NOT NULL DEFAULT 'usuario';
        """
    )

    conn.commit()
    cur.close()
    conn.close()


def usuario_actual():
    auth = request.headers.get("Authorization", "")

    if not auth.startswith("Bearer "):
        return None

    token = auth.split(" ", 1)[1]
    return TOKENS.get(token)


# ==========================================================
# FRONTEND
# ==========================================================

@app.route("/")
def inicio():
    return render_template("index.html")


@app.route("/vista-previa", methods=["POST"])
def vista_previa():
    contenido = request.form.get("contenido", "")

    try:
        respuesta = requests.post(
            f"{MODERADOR_URL}/moderacion/resenas/1/vista-previa",
            data={"contenido": contenido},
            timeout=5,
        )

        respuesta.raise_for_status()

    except requests.RequestException:
        return (
            '<div class="error">'
            "No fue posible generar la vista previa."
            "</div>",
            502,
            {"Content-Type": "text/html; charset=utf-8"},
        )

    return (
        respuesta.text,
        respuesta.status_code,
        {"Content-Type": "text/html; charset=utf-8"},
    )


# ==========================================================
# HEALTHCHECK
# ==========================================================

@app.route("/salud")
def salud():
    return jsonify({"status": "ok"}), 200


# ==========================================================
# USUARIOS
# ==========================================================

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
            """
            INSERT INTO usuarios (
                nombre_usuario,
                email,
                password_hash
            )
            VALUES (%s, %s, %s)
            RETURNING id
            """,
            (
                nombre_usuario,
                email,
                generate_password_hash(password),
            ),
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
        """
        SELECT
            id,
            nombre_usuario,
            rol,
            password_hash
        FROM usuarios
        WHERE nombre_usuario = %s
        """,
        (nombre_usuario,),
    )

    row = cur.fetchone()

    cur.close()
    conn.close()

    if not row or not check_password_hash(row[3], password or ""):
        return jsonify({"error": "credenciales invalidas"}), 401

    token = secrets.token_hex(16)

    TOKENS[token] = {
        "id": row[0],
        "nombre_usuario": row[1],
        "rol": row[2],
    }

    return jsonify({
    "token": token,
    "id": row[0],
    "usuario": row[1],
    "rol": row[2],
}), 200


# ==========================================================
# HILOS
# ==========================================================

@app.route("/hilos", methods=["POST"])
def crear_hilo():
    usuario = usuario_actual()

    if not usuario:
        return jsonify({"error": "no autenticado"}), 401

    usuario_id = usuario["id"]

    data = request.get_json(force=True)

    titulo = data.get("titulo")
    categoria = data.get("categoria", "")

    if not titulo:
        return jsonify({"error": "falta titulo"}), 400

    conn = db()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO hilos (
            usuario_id,
            titulo,
            categoria
        )
        VALUES (%s, %s, %s)
        RETURNING id
        """,
        (
            usuario_id,
            titulo,
            categoria,
        ),
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

    cur.execute(
        """
        SELECT
            h.id,
            h.titulo,
            h.categoria,
            u.nombre_usuario,
            h.fecha_creacion
        FROM hilos h
        JOIN usuarios u
            ON h.usuario_id = u.id
        ORDER BY h.fecha_creacion DESC
        """
    )

    filas = cur.fetchall()

    cur.close()
    conn.close()

    hilos = [
        {
            "id": fila[0],
            "titulo": fila[1],
            "categoria": fila[2],
            "autor": fila[3],
            "fecha": str(fila[4]),
        }
        for fila in filas
    ]

    return jsonify(hilos), 200


# ==========================================================
# COMENTARIOS + MODERACION
# ==========================================================

@app.route("/hilos/<int:hilo_id>/comentarios", methods=["POST"])
def crear_comentario(hilo_id):
    usuario_id = usuario_actual()

    if not usuario_id:
        return jsonify({"error": "no autenticado"}), 401

    data = request.get_json(force=True)

    texto = data.get("texto")

    if not texto:
        return jsonify({"error": "falta texto"}), 400

    try:
        respuesta_moderador = requests.post(
            f"{MODERADOR_URL}/moderar",
            json={"texto": texto},
            timeout=5,
        )

        respuesta_moderador.raise_for_status()
        veredicto = respuesta_moderador.json()

    except requests.RequestException:
        return jsonify(
            {"error": "servicio de moderacion no disponible"}
        ), 502

    estado = (
        "aprobado"
        if veredicto.get("aprobado")
        else "rechazado"
    )

    conn = db()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO comentarios (
            hilo_id,
            usuario_id,
            texto,
            estado
        )
        VALUES (%s, %s, %s, %s)
        RETURNING id
        """,
        (
            hilo_id,
            usuario_id,
            texto,
            estado,
        ),
    )

    comentario_id = cur.fetchone()[0]

    conn.commit()
    cur.close()
    conn.close()

    if estado == "rechazado":
        s3.put_object(
            Bucket=S3_BUCKET,
            Key=f"moderacion/rechazados/{comentario_id}.json",
            Body=json.dumps(
                {
                    "comentario_id": comentario_id,
                    "hilo_id": hilo_id,
                    "texto": texto,
                    "motivo": veredicto.get("motivo"),
                }
            ),
        )

    return jsonify(
        {
            "id": comentario_id,
            "estado": estado,
        }
    ), 201


@app.route("/hilos/<int:hilo_id>/comentarios", methods=["GET"])
def listar_comentarios(hilo_id):
    conn = db()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT
            c.id,
            c.texto,
            c.estado,
            c.fecha,
            c.usuario_id,
            u.nombre_usuario
        FROM comentarios c
        JOIN usuarios u ON c.usuario_id = u.id
        WHERE c.hilo_id = %s
          AND c.estado = 'aprobado'
        ORDER BY c.fecha
        """,
        (hilo_id,),
    )

    filas = cur.fetchall()

    cur.close()
    conn.close()

    return jsonify([
        {
            "id": r[0],
            "texto": r[1],
            "estado": r[2],
            "fecha": str(r[3]),
            "usuario_id": r[4],
            "autor": r[5],
        }
        for r in filas
    ]), 200

@app.route("/comentarios/<int:comentario_id>", methods=["DELETE"])
def eliminar_comentario(comentario_id):
    usuario = usuario_actual()

    if not usuario:
        return jsonify({"error": "no autenticado"}), 401

    conn = db()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT usuario_id
        FROM comentarios
        WHERE id = %s
        """,
        (comentario_id,),
    )

    comentario = cur.fetchone()

    if not comentario:
        cur.close()
        conn.close()
        return jsonify({"error": "comentario no encontrado"}), 404

    propietario_id = comentario[0]

    if (
        usuario["id"] != propietario_id
        and usuario["rol"] != "admin"
    ):
        cur.close()
        conn.close()
        return jsonify({"error": "no autorizado"}), 403

    cur.execute(
        """
        DELETE FROM comentarios
        WHERE id = %s
        """,
        (comentario_id,),
    )

    conn.commit()
    cur.close()
    conn.close()

    return jsonify({
        "mensaje": "comentario eliminado"
    }), 200

@app.route("/admin/comentarios", methods=["GET"])
def admin_listar_comentarios():
    usuario = usuario_actual()

    if not usuario:
        return jsonify({"error": "no autenticado"}), 401

    if usuario["rol"] != "admin":
        return jsonify({"error": "requiere administrador"}), 403

    conn = db()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT
            c.id,
            c.hilo_id,
            c.texto,
            c.estado,
            c.fecha,
            c.usuario_id,
            u.nombre_usuario
        FROM comentarios c
        JOIN usuarios u ON c.usuario_id = u.id
        ORDER BY c.fecha DESC
        """
    )

    filas = cur.fetchall()

    cur.close()
    conn.close()

    return jsonify([
        {
            "id": r[0],
            "hilo_id": r[1],
            "texto": r[2],
            "estado": r[3],
            "fecha": str(r[4]),
            "usuario_id": r[5],
            "autor": r[6],
        }
        for r in filas
    ]), 200


@app.route(
    "/admin/comentarios/<int:comentario_id>/estado",
    methods=["PATCH"]
)
def admin_cambiar_estado_comentario(comentario_id):
    usuario = usuario_actual()

    if not usuario:
        return jsonify({"error": "no autenticado"}), 401

    if usuario["rol"] != "admin":
        return jsonify({"error": "requiere administrador"}), 403

    data = request.get_json(force=True)
    estado = data.get("estado")

    if estado not in ["aprobado", "rechazado", "pendiente"]:
        return jsonify({"error": "estado invalido"}), 400

    conn = db()
    cur = conn.cursor()

    cur.execute(
        """
        UPDATE comentarios
        SET estado = %s
        WHERE id = %s
        RETURNING id
        """,
        (estado, comentario_id),
    )

    actualizado = cur.fetchone()

    if not actualizado:
        conn.rollback()
        cur.close()
        conn.close()
        return jsonify({"error": "comentario no encontrado"}), 404

    conn.commit()
    cur.close()
    conn.close()

    return jsonify({
        "id": comentario_id,
        "estado": estado
    }), 200


@app.route("/admin/hilos/<int:hilo_id>", methods=["DELETE"])
def admin_eliminar_hilo(hilo_id):
    usuario = usuario_actual()

    if not usuario:
        return jsonify({"error": "no autenticado"}), 401

    if usuario["rol"] != "admin":
        return jsonify({"error": "requiere administrador"}), 403

    conn = db()
    cur = conn.cursor()

    try:
        cur.execute(
            "DELETE FROM calificaciones WHERE hilo_id = %s",
            (hilo_id,),
        )

        cur.execute(
            "DELETE FROM comentarios WHERE hilo_id = %s",
            (hilo_id,),
        )

        cur.execute(
            """
            DELETE FROM hilos
            WHERE id = %s
            RETURNING id
            """,
            (hilo_id,),
        )

        eliminado = cur.fetchone()

        if not eliminado:
            conn.rollback()
            return jsonify({"error": "hilo no encontrado"}), 404

        conn.commit()

    finally:
        cur.close()
        conn.close()

    return jsonify({
        "mensaje": "hilo eliminado"
    }), 200

# ==========================================================
# CALIFICACIONES
# ==========================================================

@app.route("/hilos/<int:hilo_id>/calificaciones", methods=["POST"])
def crear_calificacion(hilo_id):
    usuario = usuario_actual()

    if not usuario:
        return jsonify({"error": "no autenticado"}), 401

    usuario_id = usuario["id"]

    data = request.get_json(force=True)
    puntuacion = data.get("puntuacion")

    if puntuacion not in [1, 2, 3, 4, 5]:
        return jsonify({"error": "puntuacion debe ser 1-5"}), 400

    conn = db()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO calificaciones (
            hilo_id,
            usuario_id,
            puntuacion
        )
        VALUES (%s, %s, %s)
        ON CONFLICT (hilo_id, usuario_id)
        DO UPDATE SET
            puntuacion = EXCLUDED.puntuacion,
            fecha = NOW()
        RETURNING id
        """,
        (
            hilo_id,
            usuario_id,
            puntuacion,
        ),
    )

    calificacion_id = cur.fetchone()[0]

    conn.commit()

    cur.execute(
        """
        SELECT
            COALESCE(AVG(puntuacion), 0),
            COUNT(*)
        FROM calificaciones
        WHERE hilo_id = %s
        """,
        (hilo_id,),
    )

    promedio, total = cur.fetchone()

    cur.close()
    conn.close()

    return jsonify({
        "id": calificacion_id,
        "puntuacion": puntuacion,
        "promedio": round(float(promedio), 2),
        "total": total,
    }), 200


# ==========================================================
# INICIO DE LA APLICACION
# ==========================================================


@app.route("/hilos/<int:hilo_id>/calificaciones", methods=["GET"])
def obtener_calificaciones(hilo_id):
    usuario = usuario_actual()

    conn = db()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT
            COALESCE(AVG(puntuacion), 0),
            COUNT(*)
        FROM calificaciones
        WHERE hilo_id = %s
        """,
        (hilo_id,),
    )

    promedio, total = cur.fetchone()

    mi_puntuacion = None

    if usuario:
        cur.execute(
            """
            SELECT puntuacion
            FROM calificaciones
            WHERE hilo_id = %s
              AND usuario_id = %s
            """,
            (
                hilo_id,
                usuario["id"],
            ),
        )

        fila = cur.fetchone()

        if fila:
            mi_puntuacion = fila[0]

    cur.close()
    conn.close()

    return jsonify({
        "promedio": round(float(promedio), 2),
        "total": total,
        "mi_puntuacion": mi_puntuacion,
    }), 200


if __name__ == "__main__":
    init_db()
    app.run(
        host="0.0.0.0",
        port=5000,
    )
