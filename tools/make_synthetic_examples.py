#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Genera los datos SINTÉTICOS de ejemplo que permiten reproducir este portafolio
sin acceso a ninguna base de datos ni a información real.

Salidas:
  01-cca-primera-infancia/python/cca_sheet_data.csv
  03-academia-juvenil-visualizacion/data/synthetic/agregados_hse_crecimiento.json

Uso:  python3 tools/make_synthetic_examples.py
No contiene ni produce datos de personas reales.
"""
import csv
import json
import os
import random

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
random.seed(7)

# ─────────────────────────────────────────────────────────────────────────────
# 1) CCA · hoja de recojo sintética (mismas columnas que el ETL espera)
# ─────────────────────────────────────────────────────────────────────────────
PROVINCIAS = ["PROVINCIA EJEMPLO UNO", "PROVINCIA EJEMPLO DOS"]
DISTRITOS = ["DISTRITO A", "DISTRITO B", "DISTRITO C"]
UGTS = ["UGT EJEMPLO NORTE", "UGT EJEMPLO SUR"]
NIVELES = ["Inicial - Jardín", "Inicial No Escolarizado"]

filas = []
cod_mod = 1000001
for i in range(14):
    prov = PROVINCIAS[i % len(PROVINCIAS)]
    dist = DISTRITOS[i % len(DISTRITOS)]
    ugt = UGTS[i % len(UGTS)]
    nivel = NIVELES[i % len(NIVELES)]
    escolarizado = nivel == "Inicial - Jardín"
    filas.append({
        "Provincia": prov,
        "Distrito": dist,
        "Centro Poblado": f"CP {dist.split()[-1]}-{i + 1}",
        "UGT": ugt,
        "COD_Inst": f"IE-{1000 + i}" if escolarizado else "—",
        "Cod modular": str(cod_mod),
        "Cod local": str(2000000 + i) if escolarizado else "",
        "Institución educativa": f"IE EJEMPLO {i + 1:02d}",
        "Nivel modular": nivel,
    })
    cod_mod += 1

csv_path = os.path.join(RAIZ, "01-cca-primera-infancia", "python", "cca_sheet_data.csv")
os.makedirs(os.path.dirname(csv_path), exist_ok=True)
with open(csv_path, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(filas[0].keys()))
    w.writeheader()
    w.writerows(filas)
print("CSV sintético ->", os.path.relpath(csv_path, RAIZ), f"({len(filas)} filas)")

# ─────────────────────────────────────────────────────────────────────────────
# 2) Academia Juvenil · agregados sintéticos para el Sankey
# ─────────────────────────────────────────────────────────────────────────────
NIVELES7 = ["MUY BAJO", "BAJO", "PROMEDIO BAJO", "PROMEDIO",
            "PROMEDIO ALTO", "ALTO", "MUY ALTO"]

ACADEMIAS = ["AJ EJEMPLO ALFA", "AJ EJEMPLO BETA"]
HABILIDADES = ["Asertividad", "Comunicación"]


def perfil_inicio(rng):
    """Distribución de partida, sesgada a niveles medios."""
    pesos = [6, 12, 18, 26, 18, 13, 7]
    return rng.choices(NIVELES7, weights=pesos, k=1)[0]


def desplazar(nivel, rng):
    """Movimiento realista: la mayoría sube o se queda."""
    i = NIVELES7.index(nivel)
    r = rng.random()
    if r < 0.45:
        return NIVELES7[min(6, i + 1)], "subieron"
    if r < 0.80:
        return nivel, "mismo"
    return NIVELES7[max(0, i - 1)], "bajaron"


sankey = {}
for ac in ACADEMIAS:
    for hab in HABILIDADES:
        n = 120
        inicio, proceso, flujos = {}, {}, {}
        sub = baj = igual = 0
        for _ in range(n):
            a = perfil_inicio(random)
            b, mov = desplazar(a, random)
            inicio[a] = inicio.get(a, 0) + 1
            proceso[b] = proceso.get(b, 0) + 1
            clave = f"{a} -> {b}"
            flujos[clave] = flujos.get(clave, 0) + 1
            if mov == "subieron":
                sub += 1
            elif mov == "bajaron":
                baj += 1
            else:
                igual += 1
        sankey[f"{ac}|{hab}"] = {
            "academia": ac,
            "habilidad": hab,
            "n": n,
            "niveles_inicio": inicio,
            "niveles_proceso": proceso,
            "flujos": flujos,
            "subieron": sub,
            "bajaron": baj,
            "mismo": igual,
        }

json_path = os.path.join(RAIZ, "03-academia-juvenil-visualizacion",
                         "data", "synthetic", "agregados_hse_crecimiento.json")
os.makedirs(os.path.dirname(json_path), exist_ok=True)
with open(json_path, "w", encoding="utf-8") as f:
    json.dump({"generado_por": "tools/make_synthetic_examples.py",
               "aviso": "Datos sintéticos de ejemplo. No provienen de estudiantes reales.",
               "sankey": sankey}, f, ensure_ascii=False, indent=1)
print("JSON sintético ->", os.path.relpath(json_path, RAIZ), f"({len(sankey)} diagramas)")
