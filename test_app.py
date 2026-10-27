
import pytest
import app as zoo_app


@pytest.fixture
def cliente():
    zoo_app.app.config.update(
        TESTING=True,
        SECRET_KEY="clave-de-prueba"
    )

    with zoo_app.app.test_client() as cliente:
        yield cliente


class CursorFalso:
    def __init__(self):
        self.consulta = None
        self.datos = None
        self.cerrado = False

    def execute(self, consulta, datos):
        self.consulta = consulta
        self.datos = datos

    def close(self):
        self.cerrado = True


class ConexionFalsa:
    def __init__(self):
        self.cursor_falso = CursorFalso()
        self.confirmado = False
        self.cerrado = False

    def cursor(self):
        return self.cursor_falso

    def commit(self):
        self.confirmado = True

    def close(self):
        self.cerrado = True


def test_abrir_formulario_agregar(cliente):
    respuesta = cliente.get("/agregar")

    assert respuesta.status_code == 200
    assert b"nombre" in respuesta.data.lower()


def test_agregar_animal_correctamente(cliente, monkeypatch):
    conexion_falsa = ConexionFalsa()

    datos_prueba = (
        "Toby",
        "Leon",
        "cafe",
        5,
        "Macho",
        "Sabana",
        "Animal de prueba",
        "https://ejemplo.com/leon.jpg",
        ""
    )

    monkeypatch.setattr(
        zoo_app,
        "obtener_datos_formulario",
        lambda: datos_prueba
    )

    monkeypatch.setattr(
        zoo_app,
        "obtener_conexion",
        lambda: conexion_falsa
    )

    respuesta = cliente.post("/agregar", follow_redirects=False)

    assert respuesta.status_code == 302
    assert respuesta.headers["Location"].endswith("/")

    assert "INSERT INTO animales" in conexion_falsa.cursor_falso.consulta
    assert conexion_falsa.cursor_falso.datos == datos_prueba

    assert conexion_falsa.confirmado is True
    assert conexion_falsa.cursor_falso.cerrado is True
    assert conexion_falsa.cerrado is True


def test_rechazar_datos_invalidos(cliente, monkeypatch):
    def datos_invalidos():
        raise ValueError("El nombre es obligatorio.")

    monkeypatch.setattr(
        zoo_app,
        "obtener_datos_formulario",
        datos_invalidos
    )

    def conexion_no_debe_usarse():
        pytest.fail("No se debe conectar a MySQL con datos invalidos.")

    monkeypatch.setattr(
        zoo_app,
        "obtener_conexion",
        conexion_no_debe_usarse
    )

    respuesta = cliente.post("/agregar", follow_redirects=False)

    assert respuesta.status_code == 302
    assert respuesta.headers["Location"].endswith("/agregar")

    with cliente.session_transaction() as sesion:
        mensajes = sesion["_flashes"]
        assert any(
            "El nombre es obligatorio." in mensaje
            for categoria, mensaje in mensajes
        )


def test_error_de_mysql(cliente, monkeypatch):
    def datos_validos():
        return (
            "Toby", "Leon", "cafe", 5, "Macho",
            "Sabana", "Prueba", "", ""
        )

    def conexion_con_error():
        raise zoo_app.mysql.connector.Error("Error de prueba")

    monkeypatch.setattr(
        zoo_app,
        "obtener_datos_formulario",
        datos_validos
    )

    monkeypatch.setattr(
        zoo_app,
        "obtener_conexion",
        conexion_con_error
    )

    respuesta = cliente.post("/agregar", follow_redirects=False)

    assert respuesta.status_code == 302
    assert respuesta.headers["Location"].endswith("/agregar")

    with cliente.session_transaction() as sesion:
        mensajes = sesion["_flashes"]
        assert any(
            "No se pudo guardar el animal en MySQL." in mensaje
            for categoria, mensaje in mensajes
        )
