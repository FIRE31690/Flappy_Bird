"""Excepciones propias del dominio: permiten distinguir errores previsibles."""


class GestorError(Exception):
    """Clase base de todos los errores controlados de la aplicación (herencia)."""


class ValidacionError(GestorError):
    """Dato de entrada con formato o rango incorrecto."""


class ReglaNegocioError(GestorError):
    """Operación válida en formato pero prohibida por una regla del negocio."""


class NoEncontradoError(GestorError):
    """El registro solicitado no existe."""


class PersistenciaError(GestorError):
    """Problema al leer/escribir archivos JSON, CSV o TXT."""


class EntornoNoSoportadoError(GestorError):
    """La terminal o el sistema no puede ejecutar el juego (sin curses o ventana muy pequeña)."""
