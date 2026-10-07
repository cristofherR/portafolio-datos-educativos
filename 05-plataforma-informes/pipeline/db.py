# -*- coding: utf-8 -*-
"""Conexión a la base de datos institucional (PostgreSQL).

Las credenciales NUNCA se escriben aquí: se leen de variables de entorno.
Copia `.env.example` a `.env` y coloca tus propios valores.

    DB_HOST   host de la base            (p. ej. tu-servidor.ejemplo.com)
    DB_PORT   puerto                     (por defecto 5432)
    DB_NAME   nombre de la base
    DB_USER   usuario
    DB_PASSWORD  contraseña

Las consultas del pipeline son de solo lectura (SELECT) sobre vistas de reportes.
"""
import os

import psycopg2


def config(sslmode="require", connect_timeout=30):
    faltan = [k for k in ("DB_HOST", "DB_NAME", "DB_USER", "DB_PASSWORD")
              if not os.environ.get(k)]
    if faltan:
        raise SystemExit(
            "Faltan variables de entorno: " + ", ".join(faltan) +
            "\nCopia .env.example a .env y completa los valores (nunca los subas al repo).")
    return {
        "host": os.environ["DB_HOST"],
        "port": int(os.environ.get("DB_PORT", "5432")),
        "dbname": os.environ["DB_NAME"],
        "user": os.environ["DB_USER"],
        "password": os.environ["DB_PASSWORD"],
        "sslmode": sslmode,
        "connect_timeout": connect_timeout,
    }


def conn(**kw):
    return psycopg2.connect(**config(**kw))
