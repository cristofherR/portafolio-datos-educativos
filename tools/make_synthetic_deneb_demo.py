#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Genera los datos SINTETICOS de ejemplo para los visuales Deneb de Academia Juvenil.

No usa ninguna fuente real: los valores son de relleno, con la MISMA forma (campos y
tipos) que esperan las especificaciones de `03-academia-juvenil-visualizacion/deneb/`.

Salidas:
  03-academia-juvenil-visualizacion/data/synthetic/tov_areas_demo.json
  03-academia-juvenil-visualizacion/data/synthetic/sankey_hse_v13_demo.json

Uso:  python3 tools/make_synthetic_deneb_demo.py
"""
import json
import os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(BASE, "03-academia-juvenil-visualizacion", "data", "synthetic")

TRAMOS = ["Desacuerdo marcado", "Desacuerdo", "Posición intermedia", "Acuerdo", "Acuerdo marcado"]


def tramo_de(v):
    if v <= 1.80:
        return TRAMOS[0]
    if v <= 2.60:
        return TRAMOS[1]
    if v <= 3.40:
        return TRAMOS[2]
    if v <= 4.20:
        return TRAMOS[3]
    return TRAMOS[4]


AREAS = [
    "Ciencias", "Numérica", "Ingeniería", "Tecnología", "Comunicación", "Liderazgo",
    "Creatividad", "Ciudadanía", "Autonomía", "Colaboración", "Bienestar", "Proyectos",
]
BLOQUES = ["Estrategias de estudio", "Barreras percibidas", "Apoyo percibido",
           "Motivación", "Autoconcepto", "Expectativas"]

HABILIDADES = ["Asertividad", "Comunicación", "Autoestima", "Toma de Decisiones"]
CATS = ["Muy bajo", "Bajo", "Medio bajo", "Medio", "Medio alto", "Alto", "Muy alto"]


def build_tov_areas():
    rows = []
    for i, area in enumerate(AREAS, start=1):
        for corte, base in (("Inicio", 2.6), ("Proceso", 3.3)):
            # valor sintetico determinista en 1..5
            valor = round(min(5.0, max(1.0, base + (i % 5) * 0.18)), 3)
            rows.append({
                "area": area,
                "orden": i,
                "valor": valor,
                "tramo": tramo_de(valor),
                "periodo": corte,
                "bloque": BLOQUES[(i - 1) % len(BLOQUES)],
                "estudiante": "DEMO",
                "n": 6,
            })
    return rows


def build_sankey():
    rows = []
    for hab in HABILIDADES:
        for o in range(1, 8):
            for d in range(max(1, o - 1), min(7, o + 2) + 1):
                n = 1 + ((o + d) % 4)
                rows.append({
                    "Habilidad": hab,
                    "Categoria_Origen": CATS[o - 1],
                    "Orden_Corte_Origen": o,
                    "Categoria_Destino": CATS[d - 1],
                    "Orden_Corte_Destino": d,
                    "N": n,
                })
    return rows


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    tov = build_tov_areas()
    sankey = build_sankey()
    with open(os.path.join(OUT_DIR, "tov_areas_demo.json"), "w", encoding="utf-8") as f:
        json.dump(tov, f, ensure_ascii=False, indent=2)
    with open(os.path.join(OUT_DIR, "sankey_hse_v13_demo.json"), "w", encoding="utf-8") as f:
        json.dump(sankey, f, ensure_ascii=False, indent=2)
    print("tov_areas_demo.json   -> %d filas" % len(tov))
    print("sankey_hse_v13_demo.json -> %d filas" % len(sankey))


if __name__ == "__main__":
    main()
