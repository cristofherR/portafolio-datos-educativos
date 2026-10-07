#!/usr/bin/env python3
"""
ETL: Carga datos del sheet CCA a base de datos.

Usage:
    python3 scripts/cca_etl.py                  # SQL a consola
    python3 scripts/cca_etl.py --db postgresql   # Ejecuta en PostgreSQL
    python3 scripts/cca_etl.py --dry-run         # Solo muestra resumen

Requiere: pip install psycopg2-binary (solo si --db postgresql)
"""

import csv
import argparse
import sys
import os
from collections import defaultdict

CSV_PATH = os.path.join(os.path.dirname(__file__), "cca_sheet_data.csv")


# ── Tipos de IIEE ──
TIPO_INICIAL_JARDIN = 1
TIPO_NO_ESCOLARIZADO = 2


def parse_csv(path):
    """Lee el CSV y retorna lista de dicts normalizados."""
    rows = []
    with open(path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for r in reader:
            row = {k.strip(): v.strip() if v else '' for k, v in r.items()}
            rows.append(row)
    return rows


def extract_entities(rows):
    """
    Extrae entidades normalizadas del CSV.
    Retorna dict con: provincias, distritos, centros_poblados, ugt, iiee, iiee_ugt
    """
    provincias = {}       # nombre -> id (1-based)
    distritos = {}        # (prov_nombre, dist_nombre) -> id
    centros_poblados = {} # (dist_id, cp_nombre) -> id
    ugts = {}             # nombre -> id
    iiees = []            # lista de dicts
    iiee_ugt = []         # lista de (iiee_nombre, cod_mod, ugt_nombre)
    errores = []

    pid = dpid = cpid = uid = 0
    # Forzamos nombres normalizados
    TIPO_MAP = {
        'Inicial - Jardín': TIPO_INICIAL_JARDIN,
        'Inicial No Escolarizado': TIPO_NO_ESCOLARIZADO,
    }

    for row in rows:
        provincia = row.get('Provincia', '').strip().upper()
        distrito = row.get('Distrito', '').strip().upper()
        centro_pob = row.get('Centro Poblado', '').strip().upper()
        ugt_nombre = row.get('UGT', '').strip()
        cod_inst = row.get('COD_Inst', '').strip()
        cod_mod = row.get('Cod modular', '').strip()
        cod_local = row.get('Cod local', '').strip()
        iee_nombre = row.get('Institución educativa', '').strip()
        nivel = row.get('Nivel modular', '').strip()

        # ── Provincia ──
        if provincia not in provincias:
            pid += 1
            provincias[provincia] = pid

        # ── Distrito ──
        dist_key = (provincia, distrito)
        if dist_key not in distritos:
            dpid += 1
            distritos[dist_key] = dpid

        # ── Centro Poblado ──
        cp_key = (distritos[dist_key], centro_pob)
        if cp_key not in centros_poblados:
            cpid += 1
            centros_poblados[cp_key] = cpid

        # ── UGT ──
        if ugt_nombre not in ugts:
            uid += 1
            ugts[ugt_nombre] = uid

        # ── Tipo IIEE ──
        tipo_id = TIPO_MAP.get(nivel)
        if tipo_id is None:
            errores.append(f"Tipo no reconocido: '{nivel}' en fila {row}")
            continue

        # ── IIEE ──
        # No Escolarizado: cod_inst = '—' o vacío, cod_local vacío
        cod_inst_clean = None
        cod_local_clean = None
        if tipo_id == TIPO_NO_ESCOLARIZADO:
            # Generamos ID interno
            cod_inst_clean = f"NOESCO-{cod_mod}"
            cod_local_clean = None
        else:
            if cod_inst and cod_inst not in ('—', '-'):
                cod_inst_clean = cod_inst
            if cod_local and cod_local not in ('—', '-'):
                cod_local_clean = cod_local

        iiees.append({
            'cod_inst': cod_inst_clean,
            'cod_modular': cod_mod,
            'cod_local': cod_local_clean,
            'nombre': iee_nombre,
            'tipo_id': tipo_id,
            'centro_poblado_id': centros_poblados[cp_key],
            'ugt_id': ugts[ugt_nombre],
            'ugt_nombre': ugt_nombre,
        })

        # ── Relación IIEE ↔ UGT ──
        iiee_ugt.append({
            'cod_mod': cod_mod,
            'ugt_id': ugts[ugt_nombre],
            'ugt_nombre': ugt_nombre,
        })

    return {
        'provincias': provincias,
        'distritos': distritos,
        'centros_poblados': centros_poblados,
        'ugts': ugts,
        'iiees': iiees,
        'iiee_ugt': iiee_ugt,
        'errores': errores,
    }


def print_summary(entities):
    """Imprime resumen del proceso ETL."""
    provincias = entities['provincias']
    distritos = entities['distritos']
    cp = entities['centros_poblados']
    ugts = entities['ugts']
    iiees = entities['iiees']
    iiee_ugt = entities['iiee_ugt']
    errores = entities['errores']

    jardines = sum(1 for i in iiees if i['tipo_id'] == TIPO_INICIAL_JARDIN)
    no_esc = sum(1 for i in iiees if i['tipo_id'] == TIPO_NO_ESCOLARIZADO)

    # IIEE únicas por cod_mod (para detectar duplicados)
    unicas = set(i['cod_modular'] for i in iiees)

    # Conteo por UGT
    ugt_counts = defaultdict(int)
    for i in iiees:
        ugt_counts[i['ugt_nombre']] += 1

    # Duplicados (mismo cod_mod en >1 UGT)
    dupes = defaultdict(list)
    for i in iiees:
        dupes[i['cod_modular']].append(i['ugt_nombre'])
    duplicados = {k: v for k, v in dupes.items() if len(v) > 1}

    print("=" * 55)
    print("  RESUMEN ETL — CCA Sheet Data")
    print("=" * 55)
    print(f"  Provincias:        {len(provincias)}")
    print(f"  Distritos:         {len(distritos)}")
    print(f"  Centros Poblados:  {len(cp)}")
    print(f"  UGTs:              {len(ugts)}")
    print(f"  IIEE (total):      {len(iiees)}")
    print(f"    ├ Inicial Jardín:  {jardines}")
    print(f"    └ No Escolarizado: {no_esc}")
    print(f"  IIEE únicas:       {len(unicas)}")
    print()
    print("  ── IIEE por UGT ──")
    for ug, cnt in sorted(ugt_counts.items(), key=lambda x: -x[1]):
        print(f"    {ug:<22s}  {cnt:>2d}")
    print()
    if duplicados:
        print("  ⚠  Duplicados (misma IIEE en >1 UGT):")
        for cod_mod, ugts_list in duplicados.items():
            iie = next(i for i in iiees if i['cod_modular'] == cod_mod)
            print(f"    {iie['nombre']:>30s} (mod:{cod_mod}) → {', '.join(ugts_list)}")
    else:
        print("  ✅ Sin duplicados")
    print()
    if errores:
        print(f"  ❌ Errores ({len(errores)}):")
        for e in errores:
            print(f"    {e}")
    else:
        print("  ✅ Sin errores de parseo")
    print("=" * 55)


def generate_sql(entities):
    """Genera sentencias INSERT para PostgreSQL."""
    lines = [
        "-- ============================================================",
        "-- INSERT generado automáticamente por cca_etl.py",
        "-- Fecha: 2026-06-25",
        "-- ============================================================",
        "",
        "BEGIN;",
        "",
    ]

    # ── Provincia ──
    lines.append("-- Provincia")
    for nombre, pid in sorted(entities['provincias'].items(), key=lambda x: x[1]):
        lines.append(f"INSERT INTO provincia (id, nombre) VALUES ({pid}, '{nombre}') ON CONFLICT DO NOTHING;")
    lines.append("")

    # ── Distrito ──
    lines.append("-- Distrito")
    for (prov_nombre, dist_nombre), did in sorted(entities['distritos'].items(), key=lambda x: x[1]):
        prov_id = entities['provincias'][prov_nombre]
        lines.append(f"INSERT INTO distrito (id, nombre, provincia_id) VALUES ({did}, '{dist_nombre}', {prov_id}) ON CONFLICT DO NOTHING;")
    lines.append("")

    # ── Centro Poblado ──
    lines.append("-- Centro Poblado")
    for (dist_id, cp_nombre), cpid in sorted(entities['centros_poblados'].items(), key=lambda x: x[1]):
        lines.append(f"INSERT INTO centro_poblado (id, nombre, distrito_id) VALUES ({cpid}, '{cp_nombre}', {dist_id}) ON CONFLICT DO NOTHING;")
    lines.append("")

    # ── UGT ──
    lines.append("-- UGT")
    for nombre, uid in sorted(entities['ugts'].items(), key=lambda x: x[1]):
        lines.append(f"INSERT INTO ugt (id, nombre) VALUES ({uid}, '{nombre}') ON CONFLICT DO NOTHING;")
    lines.append("")

    # ── IIEE ──
    lines.append("-- IIEE")
    for i, iie in enumerate(entities['iiees']):
        cod_inst_val = f"'{iie['cod_inst']}'" if iie['cod_inst'] else "NULL"
        cod_local_val = f"'{iie['cod_local']}'" if iie['cod_local'] else "NULL"
        nombre_clean = iie['nombre'].replace("'", "''")
        lines.append(
            f"INSERT INTO iiee (cod_inst, cod_modular, cod_local, nombre, tipo_iiee_id, centro_poblado_id) "
            f"VALUES ({cod_inst_val}, '{iie['cod_modular']}', {cod_local_val}, '{nombre_clean}', {iie['tipo_id']}, {iie['centro_poblado_id']}) "
            f"ON CONFLICT (cod_modular) DO NOTHING;"
        )
    lines.append("")

    # ── IIEE-UGT (relación N:M) ──
    lines.append("-- IIEE ↔ UGT")
    # Necesitamos mapear cod_mod -> id (después del insert, asumimos la secuencia)
    # Para el INSERT simple, usamos subquery
    iiee_ugt_added = set()
    for rel in entities['iiee_ugt']:
        key = (rel['cod_mod'], rel['ugt_id'])
        if key not in iiee_ugt_added:
            iiee_ugt_added.add(key)
            lines.append(
                f"INSERT INTO iiee_ugt (iiee_id, ugt_id) "
                f"SELECT i.id, {rel['ugt_id']} FROM iiee i WHERE i.cod_modular = '{rel['cod_mod']}' "
                f"ON CONFLICT DO NOTHING;"
            )
    lines.append("")

    lines.append("COMMIT;")
    lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="CCA ETL: Sheet → BD")
    parser.add_argument("--csv", default=CSV_PATH, help="Ruta al CSV")
    parser.add_argument("--dry-run", action="store_true", help="Solo mostrar resumen")
    parser.add_argument("--sql-output", help="Guardar SQL en archivo")
    args = parser.parse_args()

    if not os.path.exists(args.csv):
        print(f"❌ No se encuentra el CSV: {args.csv}")
        sys.exit(1)

    rows = parse_csv(args.csv)
    entities = extract_entities(rows)

    print_summary(entities)

    if entities['errores']:
        print("\n⚠️  Hay errores de parseo. Revisa antes de continuar.")

    if args.dry_run:
        return

    sql = generate_sql(entities)

    if args.sql_output:
        with open(args.sql_output, 'w') as f:
            f.write(sql)
        print(f"\n✅ SQL guardado en: {args.sql_output}")
    else:
        print("\n" + sql)


if __name__ == '__main__':
    main()
