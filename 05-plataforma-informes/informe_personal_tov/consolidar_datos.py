# -*- coding: utf-8 -*-
"""Consolida por estudiante (Áncash 2026): TOV + HSE Inicio/Proceso + PRONABEC + COAR.
Salida: datos_integrados_ancash.json
"""
import sys, os, json, re
from collections import defaultdict
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "pipeline"))
from db import conn

BASE = os.path.dirname(os.path.abspath(__file__))
CONFIG = os.environ.get("AJ_CONFIG", os.path.join(os.path.dirname(BASE), "config", "evaluaciones.json"))
if not os.path.exists(CONFIG):
    raise SystemExit(
        "Falta config/evaluaciones.json (copia config/evaluaciones.example.json "
        "y coloca los identificadores de tus evaluaciones). Se puede apuntar con AJ_CONFIG.")
OUT = os.path.join(BASE, "datos_integrados_ancash.json")

_EV = json.load(open(CONFIG, encoding="utf-8"))
HSE_INICIO = _EV["hse_inicio"]
HSE_PROCESO = _EV["hse_proceso"]
PRONA_COM = _EV["pronabec_comunicacion"]
PRONA_MAT = _EV["pronabec_matematica"]
COAR = _EV["coar"]

BLANCO = {"En blanco", "BL.", "No respondió la pregunta"}

HSE_RANGOS = {
    "Asertividad": [(50,"MUY ALTO"),(45,"ALTO"),(42,"PROMEDIO ALTO"),(39,"PROMEDIO"),(33,"PROMEDIO BAJO"),(21,"BAJO"),(0,"MUY BAJO")],
    "Comunicación": [(40,"MUY ALTO"),(36,"ALTO"),(33,"PROMEDIO ALTO"),(30,"PROMEDIO"),(25,"PROMEDIO BAJO"),(20,"BAJO"),(0,"MUY BAJO")],
    "Autoestima": [(55,"MUY ALTO"),(51,"ALTO"),(47,"PROMEDIO ALTO"),(42,"PROMEDIO"),(35,"PROMEDIO BAJO"),(21,"BAJO"),(0,"MUY BAJO")],
    "Toma de decisiones": [(41,"MUY ALTO"),(37,"ALTO"),(34,"PROMEDIO ALTO"),(30,"PROMEDIO"),(25,"PROMEDIO BAJO"),(17,"BAJO"),(0,"MUY BAJO")],
}
DIM_KEYS = {"Asertividad":"Asertividad","Comunicación":"Comunicacion",
            "Autoestima":"Autoestima","Toma de decisiones":"TomaDecisiones"}

def as_dict(v):
    return v if isinstance(v, dict) else (json.loads(v) if v else {})

def nivel(rangos, sc):
    if sc is None: return None
    return next((n for u,n in rangos if sc>=u), None)

def cargar_def(cur, pk):
    cur.execute("SELECT rptas_correctas FROM bd_evaluaciones.evaluacion WHERE pk=%s",(pk,))
    return as_dict(cur.fetchone()[0])

def score_bin(cur, pk):
    """Devuelve {fk_evaluado: {correctas,total, hab:{h:{c,t}}, curso:{c:{c,t}}}}"""
    rc = cargar_def(cur, pk)
    preg = rc.get("preguntas", {}); meta = rc.get("metadatos", {})
    cur.execute("""SELECT fk_evaluado::text, respuestas FROM bd_evaluaciones.evaluaciones
                   WHERE fk_caracteristica_evaluacion=%s AND respuestas::text<>'{}'""",(pk,))
    out={}
    for fk,resp in cur.fetchall():
        r=as_dict(resp); cor=0; tot=0
        hab=defaultdict(lambda:{"c":0,"t":0})
        curso=defaultdict(lambda:{"c":0,"t":0})
        for n,d in preg.items():
            txt=r.get(f"preg_{n}","")
            pesos=[o["peso"] for o in d.get("respuestas",[])]
            mx=max(pesos) if pesos else 0
            if not d.get("respuestas"): continue
            tot+=1
            h=meta.get(n,{}).get("habilidad","") or ""; cu=meta.get(n,{}).get("curso","") or ""
            hab[h]["t"]+=1
            if cu: curso[cu]["t"]+=1
            hit=False
            if txt and txt not in BLANCO and txt!="Inválido":
                for o in d.get("respuestas",[]):
                    if o["texto"]==txt:
                        if o["peso"]==mx: hit=True
                        break
            if hit:
                cor+=1; hab[h]["c"]+=1
                if cu: curso[cu]["c"]+=1
        out[fk]={"correctas":cor,"total":tot,
                 "hab":{k:v for k,v in hab.items() if k},
                 "curso":{k:v for k,v in curso.items() if k}}
    return out

def score_hse(cur, pk):
    """Devuelve {fk_evaluado: {dim_score, dim_max, total, niveles}}"""
    rc = cargar_def(cur, pk)
    preg = rc.get("preguntas", {}); meta = rc.get("metadatos", {})
    cur.execute("""SELECT fk_evaluado::text, respuestas FROM bd_evaluaciones.evaluaciones
                   WHERE fk_caracteristica_evaluacion=%s AND respuestas::text<>'{}'""",(pk,))
    out={}
    for fk,resp in cur.fetchall():
        r=as_dict(resp)
        sc=defaultdict(int); mx=defaultdict(int)
        for n,d in preg.items():
            h=meta.get(n,{}).get("habilidad",""); txt=r.get(f"preg_{n}","")
            pesos=[o["peso"] for o in d.get("respuestas",[])]
            mx[h]+=max(pesos) if pesos else 0
            for o in d.get("respuestas",[]):
                if o["texto"]==txt: sc[h]+=o["peso"]; break
        rec={"dim":{}, "dim_max":{}, "total":0}
        for h,k in DIM_KEYS.items():
            s=sc.get(h,0); rec["dim"][k]=s; rec["dim_max"][k]=mx.get(h,0)
            rec.setdefault("niveles",{})[k]=nivel(HSE_RANGOS[h], s)
        rec["total"]=sum(rec["dim"].values())
        out[fk]=rec
    return out

AREAS12 = ['Ciencias','Numérica','Ingeniería','Artística','Social','Emprendedora','Salud','Gastronómica','Estética','Deportiva','Seguridad, defensa y orden público','Aeronáutica y servicios de vuelo']
BLOQUES6 = ['Claridad subjetiva','Confianza decisional','Metas personales','Apoyo familiar','Influencia familiar','Barreras percibidas']
TOVJSON = os.environ.get("AJ_TOV_JSON", os.path.join(os.path.dirname(BASE), "datos",
                                                     "dashboard_tov_resultados.json"))

GRADO_MAP={"1ero":"1","2ndo":"2","3ero":"3","4rto":"4","5nto":"5"}

def parse_grado(com):
    if not com: return None
    m=re.match(r"\s*Sec-([0-9A-Za-z]+)-", com.strip())
    return GRADO_MAP.get(m.group(1).lower()) if m else None

def norm_gen(g):
    if not g: return ""
    g=g.strip().lower()
    if g in ("femenino","fememino","f","m"): return "F"
    if g in ("masculino","h"): return "M"
    return ""

def main():
    c=conn(); cur=c.cursor()
    # TOV por estudiante
    cur.execute("""SELECT clave, estudiante, genero, num_grado, seccion, nom_ie, area, valor
                   FROM reportes.vw_tov_areas_largo_ancash_2026 WHERE periodo='Proceso'""")
    est={}
    for clave,nom,gen,gr,sec,ie,area,val in cur.fetchall():
        e=est.setdefault(clave, {"clave":clave,"estudiante":nom,"genero":gen,"grado":gr,
                                 "seccion":sec,"ie":ie,"areas":{},"tops":[]})
        e["areas"][area]=float(val) if val is not None else None
    # grado + genero normalizado desde el maestro
    cur.execute("SELECT pk::text, comentarios, genero FROM bd_evaluaciones.estudiantes WHERE pk::text = ANY(%s)",
                (list(est.keys()),))
    for pk, com, gen in cur.fetchall():
        if pk in est:
            est[pk]["grado"]=parse_grado(com) or est[pk].get("grado")
            est[pk]["genero_norm"]=norm_gen(gen) or norm_gen(est[pk].get("genero"))
    # bloques TOV (6) desde el JSON original, via pk_evaluacion -> fk_evaluado
    dj=json.load(open(TOVJSON,encoding="utf-8"))
    pro=[x for x in dj["estudiantes"] if x.get("periodo")=="Proceso"]
    pks=[x["pk_evaluacion"] for x in pro]
    cur.execute("SELECT pk::text, fk_evaluado::text FROM bd_evaluaciones.evaluaciones WHERE pk::text = ANY(%s)",(pks,))
    mp={r[0]:r[1] for r in cur.fetchall()}
    n_blo=0
    for x in pro:
        k=mp.get(x["pk_evaluacion"])
        if k and k in est:
            for b in BLOQUES6:
                if isinstance(x.get(b),(int,float)):
                    est[k]["areas"][b]=float(x[b]); n_blo+=1
    print("bloques TOV enlazados:", n_blo)
    for e in est.values():
        validos=[(a,e["areas"].get(a)) for a in AREAS12 if isinstance(e["areas"].get(a),(int,float))]
        validos.sort(key=lambda x:-x[1])
        e["tops"]=[a for a,_ in validos[:3]]

    print("TOV estudiantes:", len(est))
    print("grados:", defaultdict(int, {g: sum(1 for e in est.values() if e["grado"]==g) for g in set(e["grado"] for e in est.values())}))
    print("genero:", defaultdict(int, {g: sum(1 for e in est.values() if e.get("genero_norm")==g) for g in set(e.get("genero_norm") for e in est.values())}))

    hse_i=score_hse(cur, HSE_INICIO); hse_p=score_hse(cur, HSE_PROCESO)
    pc=score_bin(cur, PRONA_COM); pm=score_bin(cur, PRONA_MAT); co=score_bin(cur, COAR)
    cur.close(); c.close()

    n_hse=n_pc=n_pm=n_co=0
    for k,e in est.items():
        if k in hse_p:
            e["hse_proceso"]=hse_p[k]; n_hse+=1
            if k in hse_i: e["hse_inicio"]=hse_i[k]
        if k in pc: e["pronabec_com"]=pc[k]; n_pc+=1
        if k in pm: e["pronabec_mat"]=pm[k]; n_pm+=1
        if k in co: e["coar"]=co[k]; n_co+=1

    print(f"HSE Proceso: {n_hse} | PRONABEC Com: {n_pc} | PRONABEC Mat: {n_pm} | COAR: {n_co}")
    json.dump(list(est.values()), open(OUT,"w",encoding="utf-8"), ensure_ascii=False, indent=1)
    print("OK ->", OUT, "| n=", len(est))

if __name__=="__main__":
    main()
