#!/usr/bin/env python3
"""
Genera data ficticia coherente para CCA 2026.
- Hoja BD: se preserva EXACTAMENTE igual (formato, mayúsculas, datos)
- Familias, Docentes, Reportes_Rapidos, Asistencia, Historial: datos ficticios coherentes entre sí
"""

import requests
import openpyxl
from openpyxl.styles import Font
from copy import copy
import io
import random
import datetime
import string

# ── Config ──────────────────────────────────────────────────
SPREADSHEET_URL = os.environ.get("CCA_TEMPLATE_SHEET_URL", "")  # opcional: URL de plantilla propia
OUTPUT_PATH = os.environ.get("CCA_OUTPUT_XLSX", "CCA_2026_data_ficticia.xlsx")

random.seed(42)

# ── Nombres realistas ──────────────────────────────────────
NOMBRES_M = [
    "JUAN CARLOS", "JOSE LUIS", "PEDRO", "MIGUEL", "FELIX",
    "VICTOR", "RAUL", "MARIO", "WALTER", "RUBEN",
    "EDGAR", "HUMBERTO", "JULIO CESAR", "OSCAR", "HECTOR",
    "MOISES", "ISRAEL", "SAMUEL", "ELIAS", "SANTOS",
]

NOMBRES_F = [
    "MARIA", "JUANA", "ROSA", "ELENA", "CARMEN",
    "MARTHA", "LUCIA", "SILVIA", "GLORIA", "BERTHA",
    "YOLANDA", "SANDRA", "VERONICA", "FELICITA", "SABINA",
    "TEODORA", "BASILIA", "FLORENCIA", "MARCELINA", "ANTONIA",
]

APELLIDOS = [
    "RAMOS", "QUISPE", "HUAMAN", "CONDORI", "MAMANI",
    "GARCIA", "RODRIGUEZ", "LOPEZ", "MARTINEZ", "SANCHEZ",
    "FLORES", "TORRES", "HUAYTA", "YANAC", "ROJAS",
    "SALAZAR", "LLANOS", "SANTOS", "PALOMINO", "DE LA CRUZ",
    "ESPINOZA", "QUIROZ", "ALVARADO", "JAMANCA", "CORDOVA",
]

RELACIONES = ["MADRE", "PADRE", "ABUELA", "ABUELO", "TIA", "TIO", "HERMANA MAYOR", "HERMANO MAYOR", "OTRO FAMILIAR", "APODERADO"]
LENGUAS = ["QUECHUA", "CASTELLANO", "QUECHUA", "QUECHUA", "CASTELLANO", "QUECHUA", "QUECHUA"]  # 55% quechua approx
GRADOS_DOCENTE = ["MULTIGRADO", "INICIAL - 3 AÑOS", "INICIAL - 4 AÑOS", "INICIAL - 5 AÑOS", "INICIAL - 3 AÑOS", "INICIAL - 4 AÑOS", "INICIAL - 5 AÑOS", "MULTIGRADO", "MULTIGRADO"]
CORTES = ["PRE TEST", "POST TEST"]

# ── Helper: nombre ficticio ────────────────────────────────
def nombre_random():
    """Genera un nombre completo realista."""
    sexo = random.choice(["M", "F"])
    nombre = random.choice(NOMBRES_M) if sexo == "M" else random.choice(NOMBRES_F)
    apellido1 = random.choice(APELLIDOS)
    apellido2 = random.choice(APELLIDOS)
    return f"{nombre} {apellido1} {apellido2}"


# ── Cargar BD desde Google Sheets ──────────────────────────
def cargar_bd():
    """Carga la plantilla: primero un archivo local, si no, una URL remota.

    La plantilla debe traer las hojas: BD, Familias, Docentes,
    Reportes_Rapidos, Asistencia e Historial (el script solo rellena filas).
    """
    local = os.environ.get("CCA_TEMPLATE_XLSX", "")
    if local:
        print(f"Cargando plantilla local: {local}")
        return openpyxl.load_workbook(local)
    if SPREADSHEET_URL:
        print("Descargando plantilla (export .xlsx)...")
        resp = requests.get(SPREADSHEET_URL, timeout=30)
        resp.raise_for_status()
        return openpyxl.load_workbook(io.BytesIO(resp.content))
    raise SystemExit(
        "Falta la plantilla de origen. Define CCA_TEMPLATE_XLSX (ruta a un .xlsx "
        "local) o CCA_TEMPLATE_SHEET_URL (URL de exportación de tu hoja).\n"
        "Ver REPRODUCIR.md"
    )


def extraer_ies(wb):
    """Extrae lista de IIEE desde la hoja BD (excluye header y filas vacías)."""
    ws = wb['BD']
    ies = []
    for r in range(2, ws.max_row + 1):
        cod_inst = ws.cell(r, 2).value
        if cod_inst is None:
            continue
        ie_data = {
            'row': r,
            'N': ws.cell(r, 1).value,
            'COD_Inst': cod_inst,
            'UGT': str(ws.cell(r, 3).value or ""),
            'Provincia': str(ws.cell(r, 4).value or ""),
            'Distrito': str(ws.cell(r, 5).value or ""),
            'Centro_Poblado': str(ws.cell(r, 6).value or ""),
            'IE_nombre': str(ws.cell(r, 7).value or ""),
            'Cod_modular': str(ws.cell(r, 8).value or ""),
            'Cod_local': ws.cell(r, 9).value,
            'Nivel': str(ws.cell(r, 10).value or ""),
            'CT': str(ws.cell(r, 14).value or ""),
            'Facilitador': str(ws.cell(r, 16).value or ""),
            'Ciclo': str(ws.cell(r, 17).value or ""),
            'Sesion': str(ws.cell(r, 18).value or ""),
        }
        ies.append(ie_data)
    return ies


# ── Generar datos ficticios ────────────────────────────────

def generar_familias(ies):
    """Genera registros ficticios de familias."""
    registros = []
    for ie in ies:
        n_fam = random.randint(2, 6)
        # Si no hay facilitador, skip
        facilitador = ie['Facilitador'] if ie['Facilitador'] else f"FACILITADOR {ie['N']}"
        for _ in range(n_fam):
            edad_ninio = random.randint(3, 5)  # 3-5 años
            relacion = random.choice(RELACIONES)
            edad_cuidador = random.randint(22, 65)
            lengua = random.choice(LENGUAS)
            corte = random.choice(CORTES)
            fecha_aplicacion = random_fecha(2026, 3, 7)

            row = [
                random_timestamp(2026, 3, 7),     # Timestamp
                ie['UGT'],                         # UGT
                ie['IE_nombre'],                   # IE
                int(ie['Cod_modular']) if ie['Cod_modular'].isdigit() else None,  # Cod_modular
                nombre_random(),                   # Apellidos_nombres
                relacion,                          # Relacion
                edad_cuidador,                     # Edad_cuidador
                edad_ninio,                        # Edad_ninio
                lengua,                            # Lengua_materna
                fecha_aplicacion,                  # Fecha_aplicacion
                corte,                             # Corte
            ]
            # Preg_1 to Preg_24 (respuestas 1-4 en escala Likert)
            for p in range(24):
                row.append(random.randint(1, 4))
            # Pregunta_abierta_1, Pregunta_abierta_2
            row.append(f"RESPUESTA ABIERTA {random.randint(1, 100)}")
            row.append(f"RESPUESTA ABIERTA {random.randint(1, 100)}")
            # Facilitador
            row.append(facilitador)

            registros.append(row)
    return registros


def generar_docentes(ies):
    """Genera registros ficticios de docentes."""
    registros = []
    for ie in ies:
        n_doc = random.randint(1, 4)
        facilitador = ie['Facilitador'] if ie['Facilitador'] else f"FACILITADOR {ie['N']}"
        for _ in range(n_doc):
            lengua = random.choice(LENGUAS)
            corte = random.choice(CORTES)
            fecha_aplicacion = random_fecha(2026, 3, 7)
            experiencia = random.randint(1, 20)

            row = [
                random_timestamp(2026, 3, 7),     # Timestamp
                ie['UGT'],                         # UGT
                ie['IE_nombre'],                   # IE
                int(ie['Cod_modular']) if ie['Cod_modular'].isdigit() else None,  # COd_modular
                nombre_random(),                   # Apellidos_nombres
                random.choice(GRADOS_DOCENTE),     # Grado
                experiencia,                       # Anios_experiencia
                lengua,                            # Lengua_materna
                fecha_aplicacion,                  # Fecha_aplicacion
                corte,                             # Corte
            ]
            # Preg_1 to Preg_30
            for p in range(30):
                row.append(random.randint(1, 4))
            # Pregunta_abierta_1 to 4
            for _ in range(4):
                row.append(f"RESPUESTA ABIERTA {random.randint(1, 100)}")
            # Facilitador
            row.append(facilitador)

            registros.append(row)
    return registros


def generar_reportes_rapidos(ies):
    """Genera reportes rápidos de sesiones."""
    registros = []
    temas = [
        "ESTRATEGIAS DE LECTOESCRITURA", "MATERIAL DIDACTICO", "JUEGOS DE APRENDIZAJE",
        "DESARROLLO SOCIOEMOCIONAL", "PLANIFICACION CURRICULAR", "EVALUACION FORMATIVA",
        "LENGUA MATERNA Y CASTELLANO", "ATENCION A LA DIVERSIDAD", "TRABAJO CON FAMILIAS",
        "PREPARACION DE MATERIAL CONCRETO", "NARRACION DE CUENTOS", "CANCIONES INFANTILES",
    ]
    publicos = ["SESION CON FAMILIAS", "SESION CON DOCENTES", "SESION CON FAMILIAS Y DOCENTES", "SESION CON DOCENTES"]
    
    for ie in ies:
        n_reportes = random.randint(1, 4)
        facilitador = ie['Facilitador'] if ie['Facilitador'] else f"FACILITADOR {ie['N']}"
        ciclo = ie['Ciclo'] if ie['Ciclo'] else random.choice(["CICLO I", "CICLO II", "CICLO III"])
        sesion_base = ie['Sesion'] if ie['Sesion'] else "SESION 1"

        for i in range(n_reportes):
            fecha = random_fecha(2026, 4, 7)
            tema = random.choice(temas)
            publico = random.choice(publicos)
            asis_fam = random.randint(0, 12) if "FAMILIAS" in publico.upper() else 0
            asis_doc = random.randint(1, 5) if "DOCENTES" in publico.upper() else 0
            asis_otros = random.randint(0, 3)
            otros_texto = f"AUTORIDADES COMUNALES" if asis_otros > 0 else None
            desarrollo = f"SE DESARROLLO LA SESION SOBRE {tema}. DINAMICA DE GRUPO, REFLEXION Y COMPROMISOS."
            incidencia = random.choice(["NO", "SI"])
            desc_inc = f"SE REPORTO {random.choice(['RETRASO', 'INASISTENCIA', 'FALTA DE MATERIAL'])}." if incidencia == "SI" else None
            atencion_adicional = random.choice(["NO", "SI"])
            desc_atencion = f"SE BRINDO {random.choice(['ACOMPAÑAMIENTO INDIVIDUAL', 'MATERIAL ADICIONAL', 'VISITA DOMICILIARIA'])}." if atencion_adicional == "SI" else None

            row = [
                random_timestamp(2026, 4, 7),     # Timestamp
                ie['UGT'],                         # UGT
                ie['IE_nombre'],                   # IE
                None,                              # Cod_modular (muchos están vacíos en datos reales)
                facilitador,                       # Facilitador
                fecha,                             # Fecha_Sesion
                ciclo,                             # Ciclo
                f"SESION {i+1}",                   # Sesion
                tema,                              # Tema
                publico,                           # Publico_asistente
                asis_fam,                          # Asist_Familias
                asis_doc,                          # Asist_Docentes
                asis_otros,                        # Asist_Otros_Cant
                otros_texto,                       # Asist_Otros_Texto
                desarrollo,                        # Desarrollo
                incidencia,                        # Incidencias_SN
                desc_inc,                          # Descripcion_Incidencia
                atencion_adicional,                # Atencion_Adicional
                desc_atencion,                     # Descripcion_Atencion_Adicional
            ]
            registros.append(row)
    return registros


def generar_asistencias(ies):
    """Genera registros de asistencia (formato de enlace)."""
    registros = []
    for ie in ies:
        # No todas las IE tienen registro de asistencia
        if random.random() > 0.6:
            continue
        facilitador = ie['Facilitador'] if ie['Facilitador'] else f"FACILITADOR {ie['N']}"
        fec_inicio = random_fecha(2026, 4, 5)
        fec_fin = random_fecha(2026, 5, 6)

        row = [
            random_timestamp(2026, 5, 6),         # Timestamp
            ie['UGT'],                             # UGT
            ie['IE_nombre'],                       # IE
            int(ie['Cod_modular']) if ie['Cod_modular'].isdigit() else None,  # Cod_modular
            facilitador,                           # Facilitador
            fec_inicio,                            # Fecha_inicio
            fec_fin,                               # Fecha_fin
            f"https://docs.google.com/spreadsheets/d/{random_id()}/edit",  # Enlace
        ]
        registros.append(row)
    return registros


def generar_historial(familias, docentes, reportes, asistencias, ies):
    """Genera historial basado en los registros de las otras hojas."""
    registros = []
    
    # Por cada familia contestada → un historial de evaluación
    for i, fam in enumerate(familias):
        if i % 2 != 0:  # No todas generan historial, alternamos
            continue
        timestamp = fam[0]
        ugt = fam[1]
        ie_nombre = fam[2]
        cod_mod = fam[3]
        facilitador = fam[-1]
        
        fecha_str = fam[9].strftime("%Y-%m-%d") if isinstance(fam[9], datetime.datetime) else "2026-05-01"
        
        row = [
            timestamp + datetime.timedelta(seconds=random.randint(10, 300)),
            "EVALUACION - FAMILIAS",
            ugt,
            ie_nombre,
            cod_mod,
            facilitador,
            f"REGISTRO DE RESPUESTAS DE ENCUESTA {fam[10]} A FAMILIAS APLICADO EL DIA: {fecha_str} EN LA IE: {ie_nombre} - {ugt}",
            2.0 if fam[10] == "PRE TEST" else 1.0,
        ]
        registros.append(row)
    
    # Por cada docente contestado → un historial de evaluación
    for i, doc in enumerate(docentes):
        if i % 2 != 0:
            continue
        timestamp = doc[0]
        ugt = doc[1]
        ie_nombre = doc[2]
        cod_mod = doc[3]
        facilitador = doc[-1]
        
        fecha_str = doc[8].strftime("%Y-%m-%d") if isinstance(doc[8], datetime.datetime) else "2026-05-01"
        
        row = [
            timestamp + datetime.timedelta(seconds=random.randint(10, 300)),
            "EVALUACION - DOCENTES",
            ugt,
            ie_nombre,
            cod_mod,
            facilitador,
            f"REGISTRO DE RESPUESTAS DE ENCUESTA {doc[9]} A DOCENTES APLICADO EL DIA: {fecha_str} EN LA IE: {ie_nombre} - {ugt}",
            3.0,
        ]
        registros.append(row)
    
    # Por cada reporte rápido → un historial de "Reporte al día"
    for rep in reportes:
        timestamp = rep[0]
        ugt = rep[1]
        ie_nombre = rep[2]
        cod_mod = rep[3]
        facilitador = rep[4]
        fecha_sesion = rep[5]
        ciclo = rep[6] or ""
        sesion = rep[7] or ""
        tema = rep[8] or ""
        publico = rep[9] or ""
        asis_fam = rep[10] or 0
        asis_doc = rep[11] or 0
        
        fecha_str = fecha_sesion.strftime("%Y-%m-%d") if isinstance(fecha_sesion, datetime.datetime) else "2026-05-01"
        
        row = [
            timestamp + datetime.timedelta(seconds=random.randint(10, 300)),
            "REPORTE AL DIA",
            ugt,
            ie_nombre if ie_nombre else str(int(rep[2])) if isinstance(rep[2], (int, float)) else "",
            cod_mod,
            facilitador,
            f"REGISTRO DEL REPORTE DEL DIA: {fecha_str} EN LA IE: {ie_nombre} - {ugt}",
            f"{publico}. {ciclo} - {sesion}. TEMA: {tema}. ASISTENTES: {asis_fam} FAMILIAS; {asis_doc} DOCENTES.",
        ]
        registros.append(row)
    
    # Por cada asistencia → un historial
    for asi in asistencias:
        timestamp = asi[0]
        ugt = asi[1]
        ie_nombre = asi[2]
        cod_mod = asi[3]
        facilitador = asi[4]
        fec_ini = asi[5]
        fec_fin = asi[6]
        enlace = asi[7]
        
        ini_str = fec_ini.strftime("%Y-%m-%d") if isinstance(fec_ini, datetime.datetime) else ""
        fin_str = fec_fin.strftime("%Y-%m-%d") if isinstance(fec_fin, datetime.datetime) else ""
        
        row = [
            timestamp + datetime.timedelta(seconds=random.randint(10, 300)),
            "REGISTRO DE ASISTENCIAS",
            ugt,
            ie_nombre,
            cod_mod,
            facilitador,
            f"REGISTRO DE ASISTENCIA DESDE {ini_str} HASTA {fin_str} EN LA IE: {ie_nombre} EN {ugt}",
            enlace,
        ]
        registros.append(row)
    
    # Ordenar por timestamp
    registros.sort(key=lambda x: x[0])
    return registros


# ── Helpers de fecha ──────────────────────────────────────
def random_timestamp(year, month_start, month_end):
    """Genera timestamp aleatorio entre month_start y month_end de year."""
    m = random.randint(month_start, month_end)
    d = random.randint(1, 28)
    h = random.randint(8, 18)
    mi = random.randint(0, 59)
    s = random.randint(0, 59)
    ms = random.randint(0, 999999)
    return datetime.datetime(year, m, d, h, mi, s, ms)


def random_fecha(year, month_start, month_end):
    """Genera fecha (sin hora) aleatoria."""
    m = random.randint(month_start, month_end)
    d = random.randint(1, 28)
    return datetime.datetime(year, m, d)


def random_id():
    """Genera un ID aleatorio para enlaces."""
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=44))


# ── Copiar estilos de celda ────────────────────────────────
def copiar_celda(origen, destino):
    """Copia estilo de una celda origen a destino."""
    if origen.font:
        destino.font = copy(origen.font)
    if origen.border:
        destino.border = copy(origen.border)
    if origen.fill:
        destino.fill = copy(origen.fill)
    if origen.number_format:
        destino.number_format = origen.number_format
    if origen.protection:
        destino.protection = copy(origen.protection)
    if origen.alignment:
        destino.alignment = copy(origen.alignment)


# ── Main ──────────────────────────────────────────────────
def main():
    print("=" * 60)
    print("GENERADOR DE DATA FICTICIA CCA 2026")
    print("=" * 60)
    
    # 1. Cargar archivo original
    wb = cargar_bd()
    ies = extraer_ies(wb)
    print(f"✓ IIEE cargadas: {len(ies)}")
    
    # 2. Preservar BD exactamente como está (no tocamos la hoja)
    
    # 3. Generar datos ficticios
    print("Generando familias ficticias...")
    familias = generar_familias(ies)
    print(f"  → {len(familias)} registros")
    
    print("Generando docentes ficticios...")
    docentes = generar_docentes(ies)
    print(f"  → {len(docentes)} registros")
    
    print("Generando reportes rápidos...")
    reportes = generar_reportes_rapidos(ies)
    print(f"  → {len(reportes)} registros")
    
    print("Generando asistencias...")
    asistencias = generar_asistencias(ies)
    print(f"  → {len(asistencias)} registros")
    
    print("Generando historial (dependiente de las demás hojas)...")
    historial = generar_historial(familias, docentes, reportes, asistencias, ies)
    print(f"  → {len(historial)} registros")
    
    # ── Escribir en el archivo ─────────────────────────
    
    # Familias
    ws = wb['Familias']
    # Limpiar datos existentes (dejar header)
    for r in range(ws.max_row, 1, -1):
        ws.delete_rows(r)
    
    for i, row_data in enumerate(familias):
        r = i + 2
        for c, val in enumerate(row_data, 1):
            ws.cell(r, c, val)
    
    # Docentes
    ws = wb['Docentes']
    for r in range(ws.max_row, 1, -1):
        ws.delete_rows(r)
    
    for i, row_data in enumerate(docentes):
        r = i + 2
        for c, val in enumerate(row_data, 1):
            ws.cell(r, c, val)
    
    # Reportes_Rapidos
    ws = wb['Reportes_Rapidos']
    for r in range(ws.max_row, 1, -1):
        ws.delete_rows(r)
    
    for i, row_data in enumerate(reportes):
        r = i + 2
        for c, val in enumerate(row_data, 1):
            ws.cell(r, c, val)
    
    # Asistencia
    ws = wb['Asistencia']
    for r in range(ws.max_row, 1, -1):
        ws.delete_rows(r)
    
    for i, row_data in enumerate(asistencias):
        r = i + 2
        for c, val in enumerate(row_data, 1):
            ws.cell(r, c, val)
    
    # Historial
    ws = wb['Historial']
    for r in range(ws.max_row, 1, -1):
        ws.delete_rows(r)
    
    for i, row_data in enumerate(historial):
        r = i + 2
        for c, val in enumerate(row_data, 1):
            ws.cell(r, c, val)
    
    # Guardar
    wb.save(OUTPUT_PATH)
    print(f"\n✓ Archivo guardado: {OUTPUT_PATH}")
    
    # ── Verificación ──────────────────────────────────
    print("\n" + "=" * 60)
    print("VERIFICACIÓN")
    print("=" * 60)
    
    wb2 = openpyxl.load_workbook(OUTPUT_PATH)
    for sname in wb2.sheetnames:
        ws = wb2[sname]
        non_empty = sum(1 for r in range(2, ws.max_row + 1) if any(ws.cell(r, c).value is not None for c in range(1, ws.max_column + 1)))
        print(f"  {sname}: {ws.max_row} filas ({non_empty} con datos)")
    
    print("\n✓ COMPLETADO")


if __name__ == "__main__":
    main()
