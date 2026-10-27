import os
import re
import time
from urllib.parse import urlparse, parse_qs

import mysql.connector
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash
)

app = Flask(__name__)

app.secret_key = os.getenv(
    "FLASK_SECRET_KEY",
    "clave-local-para-desarrollo"
)

DB_CONFIG = {
    "host": os.getenv("MYSQL_HOST", "mysql"),
    "user": os.getenv("MYSQL_USER", "usuario"),
    "password": os.getenv("MYSQL_PASSWORD", "password"),
    "database": os.getenv("MYSQL_DATABASE", "zoologico"),
    "charset": "utf8mb4",
    "connection_timeout": 5
}


def obtener_conexion():
    return mysql.connector.connect(**DB_CONFIG)


def inicializar_base_datos():
    """
    Espera a MySQL, crea la tabla si no existe
    y agrega las columnas nuevas que falten.
    """
    conexion = None

    for intento in range(30):
        try:
            conexion = obtener_conexion()
            break
        except mysql.connector.Error:
            if intento == 29:
                raise
            print("Esperando a que MySQL este disponible...")
            time.sleep(2)

    cursor = conexion.cursor()

    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS animales (
                id INT AUTO_INCREMENT PRIMARY KEY,
                nombre VARCHAR(100) NOT NULL,
                especie VARCHAR(100) NOT NULL,
                color VARCHAR(50) NOT NULL,
                edad INT NULL,
                sexo VARCHAR(30) NULL,
                habitat VARCHAR(150) NULL,
                descripcion TEXT NULL,
                imagen_url TEXT NULL,
                video_url TEXT NULL
            )
        """)

        # Migracion para tablas creadas con la version anterior.
        cursor.execute("SHOW COLUMNS FROM animales")
        columnas_actuales = {
            fila[0] for fila in cursor.fetchall()
        }

        columnas_nuevas = {
            "edad": "INT NULL",
            "sexo": "VARCHAR(30) NULL",
            "habitat": "VARCHAR(150) NULL",
            "descripcion": "TEXT NULL",
            "imagen_url": "TEXT NULL",
            "video_url": "TEXT NULL"
        }

        for nombre_columna, tipo in columnas_nuevas.items():
            if nombre_columna not in columnas_actuales:
                cursor.execute(
                    f"ALTER TABLE animales "
                    f"ADD COLUMN {nombre_columna} {tipo}"
                )

        # Solo insertar los ejemplos si la tabla esta vacia.
        cursor.execute("SELECT COUNT(*) FROM animales")
        cantidad = cursor.fetchone()[0]

        if cantidad == 0:
            ejemplos = [
                (
                    "Simba", "Leon", "cafe", None, None,
                    "Sabana",
                    "Leon registrado en el zoologico.",
                    "https://images.unsplash.com/photo-1546182990-dffeafbe841d?auto=format&fit=crop&w=1200&q=85",
                    None
                ),
                (
                    "Manny", "Elefante", "gris", None, None,
                    "Zona tropical",
                    "Elefante registrado en el zoologico.",
                    "https://images.unsplash.com/photo-1557050543-4d5f4e07ef46?auto=format&fit=crop&w=1200&q=85",
                    None
                ),
                (
                    "Roco", "Tigre", "naranja", None, None,
                    "Zona de felinos",
                    "Tigre registrado en el zoologico.",
                    "https://images.unsplash.com/photo-1561731216-c3a4d99437d5?auto=format&fit=crop&w=1200&q=85",
                    None
                ),
                (
                    "Lola", "Jirafa", "amarilla", None, None,
                    "Sabana",
                    "Jirafa registrada en el zoologico.",
                    "https://images.unsplash.com/photo-1534567153574-2b12153a87f0?auto=format&fit=crop&w=1200&q=85",
                    None
                )
            ]

            cursor.executemany("""
                INSERT INTO animales
                (nombre, especie, color, edad, sexo, habitat,
                 descripcion, imagen_url, video_url)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, ejemplos)


        fotos_ejemplo = {
            "Simba": "https://images.unsplash.com/photo-1546182990-dffeafbe841d?auto=format&fit=crop&w=1200&q=85",
            "Manny": "https://images.unsplash.com/photo-1557050543-4d5f4e07ef46?auto=format&fit=crop&w=1200&q=85",
            "Roco": "https://images.unsplash.com/photo-1561731216-c3a4d99437d5?auto=format&fit=crop&w=1200&q=85",
            "Lola": "https://images.unsplash.com/photo-1534567153574-2b12153a87f0?auto=format&fit=crop&w=1200&q=85"
        }

        for nombre, imagen in fotos_ejemplo.items():
            cursor.execute("""
                UPDATE animales
                SET imagen_url = %s
                WHERE nombre = %s
                  AND (imagen_url IS NULL OR imagen_url = '')
            """, (imagen, nombre))

        conexion.commit()

    finally:
        cursor.close()
        conexion.close()


def validar_url(valor, campo):
    """
    Acepta URLs HTTP o HTTPS.
    Los campos vacios son opcionales.
    """
    valor = (valor or "").strip()

    if not valor:
        return None

    if len(valor) > 2000:
        raise ValueError(f"La URL de {campo} es demasiado larga.")

    partes = urlparse(valor)

    if partes.scheme not in ("http", "https") or not partes.netloc:
        raise ValueError(
            f"Introduce una URL HTTP o HTTPS valida para {campo}."
        )

    return valor


def obtener_datos_formulario():
    nombre = request.form.get("nombre", "").strip()
    especie = request.form.get("especie", "").strip()
    color = request.form.get("color", "").strip()
    sexo = request.form.get("sexo", "").strip() or None
    habitat = request.form.get("habitat", "").strip() or None
    descripcion = request.form.get("descripcion", "").strip() or None

    if not nombre or not especie or not color:
        raise ValueError(
            "Nombre, especie y color son campos obligatorios."
        )

    if len(nombre) > 100 or len(especie) > 100:
        raise ValueError("El nombre y la especie admiten hasta 100 caracteres.")

    if len(color) > 50:
        raise ValueError("El color admite hasta 50 caracteres.")

    if sexo and len(sexo) > 30:
        raise ValueError("El sexo admite hasta 30 caracteres.")

    if habitat and len(habitat) > 150:
        raise ValueError("El habitat admite hasta 150 caracteres.")

    edad_texto = request.form.get("edad", "").strip()
    edad = None

    if edad_texto:
        try:
            edad = int(edad_texto)
        except ValueError:
            raise ValueError("La edad debe ser un numero entero.")

        if edad < 0 or edad > 1000:
            raise ValueError("La edad debe estar entre 0 y 1000.")

    imagen_url = validar_url(
        request.form.get("imagen_url"),
        "la imagen"
    )

    video_url = validar_url(
        request.form.get("video_url"),
        "el video"
    )

    return (
        nombre,
        especie,
        color,
        edad,
        sexo,
        habitat,
        descripcion,
        imagen_url,
        video_url
    )


def obtener_video_embed(url):
    """
    Convierte enlaces habituales de YouTube a una URL
    de insercion. No inserta URLs arbitrarias en un iframe.
    """
    if not url:
        return None

    partes = urlparse(url)
    host = (partes.hostname or "").lower()
    video_id = None

    if host in ("youtube.com", "www.youtube.com", "m.youtube.com"):
        video_id = parse_qs(partes.query).get("v", [None])[0]

    elif host in ("youtu.be", "www.youtu.be"):
        video_id = partes.path.strip("/").split("/")[0]

    if video_id and re.fullmatch(r"[A-Za-z0-9_-]{11}", video_id):
        return f"https://www.youtube-nocookie.com/embed/{video_id}"

    return None


@app.route("/")
def index():
    busqueda = request.args.get("q", "").strip()

    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)

    try:
        if busqueda:
            cursor.execute("""
                SELECT * FROM animales
                WHERE nombre LIKE %s OR especie LIKE %s
                ORDER BY id DESC
            """, (f"%{busqueda}%", f"%{busqueda}%"))
        else:
            cursor.execute("""
                SELECT * FROM animales
                ORDER BY id DESC
            """)

        animales = cursor.fetchall()

    finally:
        cursor.close()
        conexion.close()

    return render_template(
        "index.html",
        animales=animales,
        busqueda=busqueda
    )


@app.route("/agregar", methods=["GET", "POST"])
def agregar():
    if request.method == "GET":
        return render_template("agregar.html", animal=None)

    try:
        datos = obtener_datos_formulario()

        conexion = obtener_conexion()
        cursor = conexion.cursor()

        try:
            cursor.execute("""
                INSERT INTO animales
                (nombre, especie, color, edad, sexo, habitat,
                 descripcion, imagen_url, video_url)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, datos)

            conexion.commit()

        finally:
            cursor.close()
            conexion.close()

        flash("Animal agregado correctamente.", "success")
        return redirect(url_for("index"))

    except ValueError as error:
        flash(str(error), "error")
        return redirect(url_for("agregar"))

    except mysql.connector.Error:
        app.logger.exception("Error al agregar un animal.")
        flash("No se pudo guardar el animal en MySQL.", "error")
        return redirect(url_for("agregar"))


@app.route("/editar/<int:id>", methods=["GET", "POST"])
def editar(id):
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)

    try:
        cursor.execute(
            "SELECT * FROM animales WHERE id = %s",
            (id,)
        )
        animal = cursor.fetchone()

    finally:
        cursor.close()
        conexion.close()

    if animal is None:
        flash("El animal solicitado no existe.", "error")
        return redirect(url_for("index"))

    if request.method == "GET":
        return render_template("editar.html", animal=animal)

    try:
        datos = obtener_datos_formulario()

        conexion = obtener_conexion()
        cursor = conexion.cursor()

        try:
            cursor.execute("""
                UPDATE animales
                SET nombre = %s,
                    especie = %s,
                    color = %s,
                    edad = %s,
                    sexo = %s,
                    habitat = %s,
                    descripcion = %s,
                    imagen_url = %s,
                    video_url = %s
                WHERE id = %s
            """, datos + (id,))

            conexion.commit()

        finally:
            cursor.close()
            conexion.close()

        flash("Cambios guardados correctamente.", "success")
        return redirect(url_for("detalle", id=id))

    except ValueError as error:
        flash(str(error), "error")
        return redirect(url_for("editar", id=id))

    except mysql.connector.Error:
        app.logger.exception("Error al editar un animal.")
        flash("No se pudieron guardar los cambios.", "error")
        return redirect(url_for("editar", id=id))


@app.route("/eliminar/<int:id>", methods=["POST"])
def eliminar(id):
    conexion = obtener_conexion()
    cursor = conexion.cursor()

    try:
        cursor.execute(
            "DELETE FROM animales WHERE id = %s",
            (id,)
        )
        eliminado = cursor.rowcount > 0
        conexion.commit()

    finally:
        cursor.close()
        conexion.close()

    if eliminado:
        flash("Animal eliminado correctamente.", "success")
    else:
        flash("El animal ya no existe.", "error")

    return redirect(url_for("index"))


@app.route("/detalle/<int:id>")
def detalle(id):
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)

    try:
        cursor.execute(
            "SELECT * FROM animales WHERE id = %s",
            (id,)
        )
        animal = cursor.fetchone()

    finally:
        cursor.close()
        conexion.close()

    if animal is None:
        flash("El animal solicitado no existe.", "error")
        return redirect(url_for("index"))

    video_embed = obtener_video_embed(animal.get("video_url"))

    video_url = animal.get("video_url") or ""
    ruta_video = urlparse(video_url).path.lower()
    video_directo = (
        video_url
        if ruta_video.endswith((".mp4", ".webm", ".ogg"))
        else None
    )

    return render_template(
        "detalle.html",
        animal=animal,
        video_embed=video_embed,
        video_directo=video_directo
    )


@app.errorhandler(404)
def pagina_no_encontrada(error):
    return "La pagina solicitada no existe.", 404


if __name__ == "__main__":
    inicializar_base_datos()

    print("\n========================================")
    print(" Zoologico Animalesco iniciado")
    print(" Abre la pagina en: http://localhost:5000")
    print("========================================\n", flush=True)

    app.run(host="0.0.0.0", port=5000, debug=False)