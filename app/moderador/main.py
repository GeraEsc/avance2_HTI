from flask import Flask, request, jsonify

app = Flask(__name__)

PALABRAS_PROHIBIDAS = {"idiota", "estupido", "basura", "spam"}
LONGITUD_MINIMA = 3
LONGITUD_MAXIMA = 2000


@app.route("/salud")
def salud():
    return jsonify({"status": "ok"}), 200


@app.route("/moderar", methods=["POST"])
def moderar():
    data = request.get_json(force=True)
    texto = data.get("texto", "")
    texto_normalizado = texto.lower()

    if len(texto) < LONGITUD_MINIMA:
        return jsonify({"aprobado": False, "motivo": "texto demasiado corto"}), 200
    if len(texto) > LONGITUD_MAXIMA:
        return jsonify({"aprobado": False, "motivo": "texto demasiado largo"}), 200

    for palabra in PALABRAS_PROHIBIDAS:
        if palabra in texto_normalizado:
            return jsonify({"aprobado": False, "motivo": f"contiene palabra prohibida: {palabra}"}), 200

    return jsonify({"aprobado": True, "motivo": None}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
