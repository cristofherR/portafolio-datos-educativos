#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sanitiza el repo del portafolio: elimina credenciales, IDs internos y rutas absolutas.
Uso: python3 tools/sanitize_repo.py
Idempotente: se puede correr varias veces sin daño.
"""
import os
import re
import shutil

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Carpeta local de trabajo (opcional): solo hace falta si vas a regenerar la copia
# saneada del analizador de radar. Define AJ_WS si la tienes fuera del repo.
W = os.environ.get("AJ_WS", "")
LOG = []


def rd(p):
    with open(p, encoding="utf-8") as f:
        return f.read()


def wr(p, s):
    with open(p, "w", encoding="utf-8") as f:
        f.write(s)


def sub(path, pattern, repl, label, count=0):
    s = rd(path)
    new, n = re.subn(pattern, repl, s, count=count)
    if n:
        wr(path, new)
        LOG.append(f"  - {label}: {n} reemplazo(s)")
    else:
        LOG.append(f"  · {label}: sin coincidencias")
    return n


print("Sanitizando repo:", REPO)

# 1) Generador de datos sintéticos CCA: quitar URL real de Google Sheets y ruta absoluta
p = os.path.join(REPO, "01-cca-primera-infancia/python/generar_data_ficticia_cca.py")
if os.path.exists(p):
    sub(p,
        r'SPREADSHEET_URL = "https://docs\.google\.com/spreadsheets/d/[^"]+"',
        'SPREADSHEET_URL = os.environ.get("CCA_TEMPLATE_SHEET_URL", "")  # opcional: URL de plantilla propia',
        "CCA URL de spreadsheet")
    sub(p,
        r'OUTPUT_PATH = "/home/[^"]+"',
        'OUTPUT_PATH = os.environ.get("CCA_OUTPUT_XLSX", "CCA_2026_data_ficticia.xlsx")',
        "CCA ruta de salida")

# 2) Archivo DAX: reemplazar UUIDs internos de característica de evaluación
p = os.path.join(REPO, "03-academia-juvenil-visualizacion/sankey/dax_sankey_hse_SOLO_PEGAR.txt")
if os.path.exists(p):
    sub(p,
        r'VAR PK_Inicio\s*= "[0-9a-f-]{36}"',
        'VAR PK_Inicio  = "<UUID_EVALUACION_INICIO>"    // TODO: colocar tu propio ID',
        "DAX PK_Inicio")
    sub(p,
        r'VAR PK_Proceso\s*= "[0-9a-f-]{36}"',
        'VAR PK_Proceso = "<UUID_EVALUACION_PROCESO>"   // TODO: colocar tu propio ID',
        "DAX PK_Proceso")

# 3) Copia sanitizada del analizador de radar (config por variables de entorno)
src = os.path.join(W, "projects/academia-juvenil-2026/aj_radar_habilidades.py")
dst = os.path.join(REPO, "03-academia-juvenil-visualizacion/python/aj_radar_habilidades.py")
if os.path.exists(src):
    s = rd(src)
    s = re.sub(
        r'DB_CONFIG\s*=\s*\{[^}]*\}',
        'DB_CONFIG = {\n'
        '    "host": os.environ.get("DB_HOST", ""),\n'
        '    "dbname": os.environ.get("DB_NAME", ""),\n'
        '    "user": os.environ.get("DB_USER", ""),\n'
        '    "password": os.environ.get("DB_PASSWORD", ""),  # nunca versionar credenciales\n'
        '    "sslmode": "require",\n'
        '}\n'
        'if not all([DB_CONFIG["host"], DB_CONFIG["dbname"], DB_CONFIG["user"], DB_CONFIG["password"]]):\n'
        '    raise SystemExit(\n'
        '        "Faltan credenciales: define DB_HOST, DB_NAME, DB_USER y DB_PASSWORD "\n'
        '        "como variables de entorno (ver .env.example)."\n'
        '    )',
        s)
    s = re.sub(
        r'AJ_EVALUACIONES = \{[^}]*\}',
        'AJ_EVALUACIONES = {  # IDs de evaluación de tu propio modelo; no versionar los reales\n'
        '    "COAR": os.environ.get("AJ_EVAL_COAR", "<UUID_COAR>"),\n'
        '    "Pronabec_Comunicacion": os.environ.get("AJ_EVAL_PRONABEC_COM", "<UUID_PRONABEC_COM>"),\n'
        '    "Pronabec_Matematica": os.environ.get("AJ_EVAL_PRONABEC_MAT", "<UUID_PRONABEC_MAT>"),\n'
        '    "HSE Academia Juvenil": os.environ.get("AJ_EVAL_HSE", "<UUID_HSE>"),\n'
        '}',
        s)
    real = re.findall(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', s)
    for u in set(real):
        s = s.replace(u, "<UUID_INTERNO>")
    wr(dst, s)
    LOG.append(f"  - radar sanitizado -> {os.path.relpath(dst, REPO)}")

# 4) Verificación final dentro del repo
print("\n".join(LOG))
print("\nVERIFICACION:")
bad = []
pat = re.compile(
    r"(password\s*=\s*[\"'][^\"']+[\"']|Pwd=|api[_-]?key\s*=\s*[\"'][^\"']+"
    r"|postgres\.database\.azure\.com|database\.windows\.net|User ID=|Server=tcp"
    r"|spreadsheets/d/[A-Za-z0-9_-]{20,}|\+51\s?\d{9}|\b(?!0{8}\b)\d{8}\b)")
zero_uuid = re.compile(r"^0{8}-0{4}-0{4}-0{4}-0{8}", re.I)  # UUIDs sintéticos del ejemplo (prefijo en ceros)
for root, dirs, files in os.walk(REPO):
    if ".git" in root or os.path.relpath(root, REPO).startswith("tools"):
        continue
    for fn in files:
        fp = os.path.join(root, fn)
        try:
            t = rd(fp)
        except Exception:
            continue
        for m in pat.finditer(t):
            bad.append(f"  {os.path.relpath(fp, REPO)} :: {m.group(0)[:60]}")
        for m in re.finditer(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", t, re.I):
            if not zero_uuid.match(m.group(0)[:36]):
                bad.append(f"  {os.path.relpath(fp, REPO)} :: UUID {m.group(0)}")
if bad:
    print("ALERTA — posibles datos sensibles:")
    print("\n".join(sorted(set(bad))))
else:
    print("Limpio: sin credenciales, hosts internos, IDs de hojas ni identificadores personales.")
