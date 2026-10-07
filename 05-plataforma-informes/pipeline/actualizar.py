# -*- coding: utf-8 -*-
"""Actualiza la plataforma de informes AJ 2026 de punta a punta.

Todo parte de la BD (TOV + HSE + PRONABEC + COAR + jerarquía) y termina en la web.

Uso:
    python3 pipeline/actualizar.py             # BD -> datos -> informes -> web + auditoria
    python3 pipeline/actualizar.py --sin-bd    # no consulta Azure (usa los datos locales)
    python3 pipeline/actualizar.py --solo-web  # solo estudiantes.json + credenciales
    python3 pipeline/actualizar.py --todo      # rehace los 284 PDF aunque no cambien

La web NO necesita reiniciarse: app.py recarga estudiantes.json cuando cambia.
"""
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
AJ = os.path.dirname(HERE)
TOV = os.path.join(AJ, "informe_personal_tov")
LOGS = os.path.join(HERE, "logs")
os.makedirs(LOGS, exist_ok=True)
PY = sys.executable
URL = os.environ.get("AJ_URL", "")  # p. ej. https://mi-plataforma.ejemplo.com


def correr(titulo, cmd, cwd, critico=True):
    print(f"\n=== {titulo} ===", flush=True)
    t = time.time()
    p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    salida = (p.stdout or "").strip()
    for linea in salida.splitlines()[-14:]:
        print("   " + linea, flush=True)
    if p.returncode != 0:
        print("   !! salida de error:", flush=True)
        for linea in (p.stderr or "").strip().splitlines()[-8:]:
            print("   " + linea, flush=True)
        if critico:
            print(f"   PASO FALLIDO ({time.time()-t:.0f}s) -> se detiene la actualizacion", flush=True)
            return False
    print(f"   [{time.time()-t:.0f}s]", flush=True)
    return True


def main():
    args = set(sys.argv[1:])
    solo_web = "--solo-web" in args
    sin_bd = "--sin-bd" in args or solo_web
    todo = "--todo" in args
    t0 = time.time()
    print("ACTUALIZACION PLATAFORMA AJ 2026 ·", time.strftime("%Y-%m-%d %H:%M"), flush=True)

    if not solo_web:
        if not sin_bd:
            if not correr("1/4 Consolidar datos (BD: TOV + HSE + PRONABEC + COAR)",
                          [PY, "consolidar_datos.py"], TOV, critico=False):
                print("   -> se continua con el datos_integrados_ancash.json existente", flush=True)
        else:
            print("\n=== 1/4 Consolidar datos: OMITIDO (--sin-bd) ===", flush=True)

        cmd = [PY, os.path.join(HERE, "generar.py")] + (["--todo"] if todo else [])
        if not correr("2/4 Generar/actualizar informes (incremental)", cmd, HERE):
            return 1
        if not correr("3/4 Preparar datos de la web", [PY, os.path.join(HERE, "prep_web.py")], HERE):
            return 1
        if not correr("4/4 Auditoria geometrica (solo lo regenerado)",
                      [PY, os.path.join(HERE, "auditoria.py"), "--cambiados"], HERE, critico=False):
            print("   (la auditoria no pudo completarse; los informes ya estan publicados)", flush=True)
    else:
        if not correr("Preparar datos de la web", [PY, os.path.join(HERE, "prep_web.py")], HERE):
            return 1

    # verificacion final: lo que ve la web == lo que hay en disco
    import json
    est = json.load(open(os.path.join(AJ, "web", "data", "estudiantes.json"), encoding="utf-8"))
    man = json.load(open(os.path.join(AJ, "informes_2026", "manifest.json"), encoding="utf-8"))
    faltan = [e["estudiante"] for e in est["estudiantes"]
              if e.get("archivo") and not os.path.exists(
                  os.path.join(AJ, "informes_2026", e["archivo"]))]
    print(f"\nRESULTADO: estudiantes {est['total']} | informes {man['total']} "
          f"(completos {man['completos']} / incompletos {man['incompletos']}) | "
          f"PDF faltantes {len(faltan)} | {time.time()-t0:.0f}s")
    print("Plataforma al dia." + ((" Web: " + URL) if URL else ""), flush=True)
    log = os.path.join(LOGS, "actualizacion_" + time.strftime("%Y-%m-%d_%H%M") + ".txt")
    open(log, "w", encoding="utf-8").write(
        f"{time.strftime('%Y-%m-%d %H:%M')}\n{est['total']} estudiantes, {man['total']} informes, "
        f"{len(faltan)} faltantes\n")
    return 1 if faltan else 0


if __name__ == "__main__":
    sys.exit(main())
