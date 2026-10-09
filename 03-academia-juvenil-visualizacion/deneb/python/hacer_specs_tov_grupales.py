#!/usr/bin/env python3
"""Genera los 2 graficos grupales que faltaban del TOV (Vega-Lite v5, Deneb):

  A) BARRAS ORDENADAS POR AREA       -> ranking de las 12 areas por promedio
  B) APILADO 100% POR TRAMO          -> composicion de estudiantes por descriptor

Fuente: tabla del modelo (Academia Juvenil 2026).
Fuente (misma tabla del radar): TOV_Areas  -> TOV_Areas
Campos que deben ir al bucket Values de Deneb (todos "No resumir"):
    area, orden, valor, tramo   (+ estudiante, nom_ie, seccion, genero, ...)

Tramos (mismos del radar) y umbral de "Acuerdo" = 3.41.
Salidas: spec_tov_barras_ordenadas_ancash_v2.json / spec_tov_apilado_tramo_ancash_v2.json
         (+ copias *_SOLO_PEGAR.json)
"""
import json, os

BASE = os.path.dirname(os.path.abspath(__file__))

TRAMOS = ["Desacuerdo marcado", "Desacuerdo", "Posición intermedia", "Acuerdo", "Acuerdo marcado"]
COLORES = ["#C00000", "#ED7D31", "#BFA26B", "#9CC069", "#2E7D32"]
UMBRAL = 3.41

DESC_VL = ("datum.promedio == 0 ? 'Sin datos' : "
           "datum.promedio <= 1.80 ? 'Desacuerdo marcado' : "
           "datum.promedio <= 2.60 ? 'Desacuerdo' : "
           "datum.promedio <= 3.40 ? 'Posición intermedia' : "
           "datum.promedio <= 4.20 ? 'Acuerdo' : 'Acuerdo marcado'")

CFG = [
    {"name": "cfg_fuente", "expr": "'Segoe UI'"},
    {"name": "cfg_fs_ejes", "expr": "10"},
    {"name": "cfg_fs_etq", "expr": "9.5"},
    {"name": "cfg_etq_color", "expr": "'#565656'"},
    {"name": "cfg_umbral", "expr": "'#F0A868'"},
    {"name": "cfg_azul", "expr": "'#1F4E79'"},
    {"name": "cfg_fs_leyenda", "expr": "9"},
]

AGG_AREA = [{"filter": "isValid(datum.valor)"},
            {"aggregate": [{"op": "mean", "field": "valor", "as": "promedio"},
                           {"op": "valid", "field": "valor", "as": "n"}],
             "groupby": ["area"]},
            {"calculate": DESC_VL, "as": "descriptor"}]

COLOR_SCALE = {"field": "descriptor", "type": "nominal",
               "scale": {"domain": TRAMOS, "range": COLORES},
               "legend": {"title": None, "orient": "bottom", "columns": 3,
                          "labelFontSize": {"expr": "cfg_fs_leyenda"}, "labelLimit": 200}}
COLOR_TRAMO = {"field": "tramo", "type": "nominal",
               "scale": {"domain": TRAMOS, "range": COLORES},
               "legend": {"title": None, "orient": "bottom", "columns": 3,
                          "labelFontSize": {"expr": "cfg_fs_leyenda"}, "labelLimit": 200}}

# ── A) BARRAS ORDENADAS POR AREA ────────────────────────────────────────────
barras = {
    "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
    "description": ("TOV Academia Juvenil 2026 · SOLO ÁNCASH — ranking de las 12 áreas "
                    "de afinidad por promedio declarado (N registros). Barras ordenadas "
                    "de mayor a menor; color = descriptor del promedio; línea naranja punteada "
                    "= umbral 3.41 'Acuerdo'. Ajusta colores/fuentes en cfg_*."),
    "background": "transparent",
    "width": 420, "height": 330, "padding": 6,
    "config": {"view": {"stroke": None},
               "axis": {"labelFontSize": {"expr": "cfg_fs_ejes"}, "titleFontSize": {"expr": "cfg_fs_ejes"},
                        "labelColor": {"expr": "cfg_etq_color"}, "titleColor": {"expr": "cfg_etq_color"}}},
    "params": CFG,
    "layer": [
        {"data": {"values": [{"u": UMBRAL}]},
         "mark": {"type": "rule", "color": {"expr": "cfg_umbral"}, "strokeWidth": 1.4, "strokeDash": [5, 4]},
         "encoding": {"x": {"field": "u", "type": "quantitative"}}},
        {"transform": AGG_AREA,
         "mark": {"type": "bar", "cornerRadiusEnd": 2},
         "encoding": {
             "y": {"field": "area", "type": "nominal",
                   "sort": {"field": "promedio", "op": "mean", "order": "descending"},
                   "axis": {"title": None, "labelLimit": 240}},
             "x": {"field": "promedio", "type": "quantitative", "scale": {"domain": [0, 5]},
                   "axis": {"title": "Promedio (1–5)", "tickCount": 6}},
             "color": COLOR_SCALE,
             "tooltip": [{"field": "area", "type": "nominal", "title": "Área"},
                         {"field": "promedio", "type": "quantitative", "title": "Promedio", "format": ".2f"},
                         {"field": "n", "type": "quantitative", "title": "n válido"},
                         {"field": "descriptor", "type": "nominal", "title": "Descriptor"}]}},
        {"transform": AGG_AREA,
         "mark": {"type": "text", "align": "left", "dx": 4,
                  "fontSize": {"expr": "cfg_fs_etq"}, "color": {"expr": "cfg_etq_color"}},
         "encoding": {"y": {"field": "area", "type": "nominal",
                            "sort": {"field": "promedio", "op": "mean", "order": "descending"}},
                      "x": {"field": "promedio", "type": "quantitative", "scale": {"domain": [0, 5]}},
                      "text": {"field": "promedio", "type": "quantitative", "format": ".2f"}}},
    ],
}

# ── B) APILADO 100% POR TRAMO ───────────────────────────────────────────────
apilado = {
    "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
    "description": ("TOV Academia Juvenil 2026 · SOLO ÁNCASH — composición de estudiantes "
                    "por descriptor en cada una de las 12 áreas (100% apilado, N registros). "
                    "Áreas ordenadas por promedio. Descriptor = ayuda de lectura (no hay puntos "
                    "de corte validados). Ajusta colores/fuentes en cfg_*."),
    "background": "transparent",
    "width": 420, "height": 330, "padding": 6,
    "config": {"view": {"stroke": None},
               "axis": {"labelFontSize": {"expr": "cfg_fs_ejes"}, "titleFontSize": {"expr": "cfg_fs_ejes"},
                        "labelColor": {"expr": "cfg_etq_color"}, "titleColor": {"expr": "cfg_etq_color"}}},
    "params": CFG,
    "transform": [{"filter": "isValid(datum.tramo)"}],
    "mark": {"type": "bar"},
    "encoding": {
        "y": {"field": "area", "type": "nominal",
              "sort": {"field": "valor", "op": "mean", "order": "descending"},
              "axis": {"title": None, "labelLimit": 240}},
        "x": {"aggregate": "count", "stack": "normalize",
              "axis": {"title": "% de estudiantes", "format": ".0%"}},
        "color": COLOR_TRAMO,
        "tooltip": [{"field": "area", "type": "nominal", "title": "Área"},
                    {"field": "tramo", "type": "nominal", "title": "Descriptor"},
                    {"aggregate": "count", "type": "quantitative", "title": "Estudiantes"}],
    },
}

for spec, base in ((barras, "spec_tov_barras_ordenadas_ancash_v2.json"),
                   (apilado, "spec_tov_apilado_tramo_ancash_v2.json")):
    for ruta in (os.path.join(BASE, base),
                 os.path.join(BASE, base.replace("spec_tov_", "TOV_").replace(".json", "_SOLO_PEGAR.json"))):
        with open(ruta, "w", encoding="utf-8") as fh:
            json.dump(spec, fh, ensure_ascii=False, indent=1)
    print("escrito:", base, os.path.getsize(os.path.join(BASE, base)), "B")
