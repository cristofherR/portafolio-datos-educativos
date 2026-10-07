# -*- coding: utf-8 -*-
"""
INFORME PERSONAL INTEGRADO — Academia Juvenil Áncash 2026  (v2 · 3 páginas)
Integra: TOV (vocacional) + HSE (socioemocional Inicio→Proceso) + Académico (PRONABEC/COAR)
con desglose POR HABILIDAD (qué falló / qué reforzar) y consejo cruzado vocacional↔académico.
Diseño A4, lenguaje amigable, apto para descarga.

Uso:
  python3 generar_informe_integrado.py "NOMBRE O PARTE"   # 1 estudiante
  python3 generar_informe_integrado.py --todos            # los 284
  python3 generar_informe_integrado.py --muestra 3        # primeros N
Salida: informe_integrado_pdf/Informe_AJ_<nombre>.pdf  [+ ZIP con --todos]
"""
import sys, os, json, subprocess, datetime, unicodedata, re, zipfile
from jinja2 import Template
import contenido_cualitativo as C
import consejos_academicos as CA

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, "datos_integrados_ancash.json")
OUT = os.path.join(BASE, "informe_integrado_pdf")
os.makedirs(OUT, exist_ok=True)

UMBRAL = 3.41
AREAS12 = list(C.AREAS.keys())

# ── HSE ────────────────────────────────────────────────────────────────
HSE_DIMS = [("Asertividad","Asertividad","🗣️","#0EA5E9"),
            ("Comunicacion","Comunicación","💬","#8B5CF6"),
            ("Autoestima","Autoestima","💗","#EC4899"),
            ("TomaDecisiones","Toma de decisiones","🎯","#F59E0B")]
HSE_DESC = {
 "Asertividad":"Tu capacidad de decir lo que piensas y poner límites con respeto.",
 "Comunicación":"Tu forma de expresar ideas y de escuchar a los demás.",
 "Autoestima":"Cómo te valoras y cuánto confías en ti mismo.",
 "Toma de decisiones":"Cómo eliges y cómo asumes las consecuencias de tus decisiones.",
}
NIVEL_COLOR = {"MUY ALTO":"#1B5E20","ALTO":"#43A047","PROMEDIO ALTO":"#A5D6A7",
               "PROMEDIO":"#FDD835","PROMEDIO BAJO":"#FB8C00","BAJO":"#E53935","MUY BAJO":"#8E1F1F"}
def nivel_txt(n):
    return {"MUY ALTO":"Es una de tus grandes fortalezas.",
            "ALTO":"Es una fortaleza clara en ti.",
            "PROMEDIO ALTO":"Vas muy bien: la usas con frecuencia.",
            "PROMEDIO":"Vas en un punto medio; con práctica puede crecer.",
            "PROMEDIO BAJO":"Está en camino. Se fortalece con experiencias y apoyo.",
            "BAJO":"Es un espacio para crecer. Todos podemos desarrollarla con acompañamiento.",
            "MUY BAJO":"Es un espacio para crecer. Todos podemos desarrollarla con acompañamiento."}.get(n,"")

NIVEL_TOV = [("Excelente",4.5,"#15803D"),("Alto",4.0,"#2563EB"),("Medio-alto",3.41,"#0EA5E9"),("En proceso",0,"#F59E0B")]
def nivel_tov(v):
    for n,l,c in NIVEL_TOV:
        if v>=l: return n,c
    return "En proceso","#F59E0B"

FRASES_INTRO = ("Este informe no dice «qué debes estudiar». Reúne, en un solo lugar, qué te dice tu test "
                "de orientación, cómo vas en lo socioemocional y en lo académico —y, sobre todo, qué puedes "
                "mejorar. Úsalo como una brújula para explorar, preguntar y decidir con más información.")

def slug(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii","ignore").decode()
    s = re.sub(r"[^A-Za-z0-9]+","_",s).strip("_")
    return s[:60] or "estudiante"

def construir(e):
    # ---- TOV ----
    tops=[]
    for a in e.get("tops",[]):
        v=e["areas"].get(a)
        if not isinstance(v,(int,float)): continue
        n,_=nivel_tov(v)
        tops.append({"area":a,"icono":C.ICONO[a],"color":C.COLOR[a],"valor":round(v,2),
                     "pct":round(v/5*100),"nivel":n,
                     "carreras":C.AREAS[a]["carreras"],"donde":C.AREAS[a]["donde"]})
    fortalezas=[]
    for a in e.get("tops",[]):
        for f in C.AREAS[a]["fortalezas"]:
            if f not in fortalezas: fortalezas.append(f)
    fortalezas=fortalezas[:8]
    bloques=[]
    for b in C.ORDEN_BLOQUES:
        v=e["areas"].get(b,0) or 0
        alto=v>=UMBRAL
        texto=C.BLOQUES[b]["alto"] if alto else C.BLOQUES[b]["bajo"]
        color=("#15803D" if alto else "#F59E0B") if b!="Barreras percibidas" else ("#F59E0B" if alto else "#15803D")
        bloques.append({"nombre":b,"icono":C.BLOQUES[b]["icono"],"texto":texto,
                        "pintar":int(round(v)),"color":color})
    vals=sorted([(a,e["areas"].get(a)) for a in AREAS12 if isinstance(e["areas"].get(a),(int,float))],key=lambda x:x[1])
    explorar=[{"area":a,"icono":C.ICONO[a],"mensaje":C.MENSAJE_EXPLORAR[a]} for a,_ in vals[:2]]
    t1=(e.get("tops") or ["Ciencias"])[0]
    narrativa=(f"En tu test, las áreas que más te atrajeron fueron <b>{'</b>, <b>'.join(e.get('tops',[]))}</b>. "
               f"Esto dice de ti que {C.AREAS[t1]['evalua'][0].lower()}{C.AREAS[t1]['evalua'][1:]} "
               f"Es una pista, no una etiqueta: tus intereses pueden ampliarse con el tiempo. "
               f"Tus resultados también muestran fortalezas como {', '.join(fortalezas[:4]).lower()}, "
               f"que te servirán en cualquier camino que elijas.")

    # ---- HSE ----
    hp=e.get("hse_proceso"); hi=e.get("hse_inicio")
    hse_dims=[]; hse_total=None
    if hp:
        for k,nombre,icono,color in HSE_DIMS:
            val=hp["dim"].get(k) or 0; mx=hp["dim_max"].get(k) or 1
            niv=hp.get("niveles",{}).get(k)
            delta=None; ddir=None
            if hi and isinstance(hi["dim"].get(k),(int,float)):
                delta=val-hi["dim"][k]; ddir="up" if delta>0 else ("down" if delta<0 else "eq")
            hse_dims.append({"nombre":nombre,"icono":icono,"color":color,"valor":val,"max":mx,
                             "pct":round(val/mx*100),"nivel":niv,"nivel_txt":nivel_txt(niv),
                             "desc":HSE_DESC[nombre],"delta":delta,"ddir":ddir,
                             "nivel_color":NIVEL_COLOR.get(niv,"#9E9E9E")})
        tot=hp.get("total",0); tot_max=sum(hp["dim_max"].values()) or 1
        nivel_tot=("MUY ALTO" if tot>=174 else "ALTO" if tot>=162 else "PROMEDIO ALTO" if tot>=152
                   else "PROMEDIO" if tot>=142 else "PROMEDIO BAJO" if tot>=127 else "BAJO" if tot>=88 else "MUY BAJO")
        hse_total={"valor":tot,"max":tot_max,"pct":round(tot/tot_max*100),"nivel":nivel_tot,
                   "color":NIVEL_COLOR.get(nivel_tot,"#9E9E9E")}

    # ---- Académico (por habilidad) + cruce ----
    acad=CA.pruebas_estudiante(e)
    cruce=CA.cruce(e, e.get("tops",[]))

    return dict(est=e.get("estudiante",""), grado=e.get("grado","") or "", genero=e.get("genero_norm","") or "",
                ie=e.get("ie","") or "", seccion=e.get("seccion","") or "",
                fecha=datetime.date.today().strftime("%d/%m/%Y"), intro=FRASES_INTRO,
                tops=tops, fortalezas=fortalezas, bloques=bloques, explorar=explorar, narrativa=narrativa,
                hse_dims=hse_dims, hse_total=hse_total, acad=acad, cruce=cruce)

PLANTILLA = Template(open(os.path.join(BASE,"plantilla_integrada.html"),encoding="utf-8").read())

def render_html(ctx):
    return PLANTILLA.render(**ctx)

def uno(e, idx=0):
    ctx=construir(e); name=slug(e["estudiante"])
    p=os.path.join(OUT,f"Informe_AJ_{name}.pdf")
    if os.path.exists(p): p=os.path.join(OUT,f"Informe_AJ_{name}_{idx:03d}.pdf")
    h=os.path.join(OUT,f"_tmp_{os.path.basename(p)[:-4]}.html")
    open(h,"w",encoding="utf-8").write(render_html(ctx))
    subprocess.run(["/usr/bin/google-chrome","--headless=new","--disable-gpu","--no-sandbox",
                    "--no-pdf-header-footer",f"--print-to-pdf={p}",f"file://{h}"],
                   capture_output=True,timeout=120)
    return p

def todos_zip(est):
    from playwright.sync_api import sync_playwright
    pdfs=[]
    with sync_playwright() as pw:
        b=pw.chromium.launch(executable_path="/usr/bin/google-chrome",args=["--no-sandbox","--disable-gpu"])
        pg=b.new_page()
        for i,e in enumerate(est,1):
            ctx=construir(e); name=slug(e["estudiante"])
            h=os.path.join(OUT,f"_tmp_{name}_{i:03d}.html")
            open(h,"w",encoding="utf-8").write(render_html(ctx))
            pdf=os.path.join(OUT,f"Informe_AJ_{name}_{i:03d}.pdf")
            pg.goto("file://"+h); pg.pdf(path=pdf,format="A4",print_background=True)
            pdfs.append(pdf)
        b.close()
    zpath=os.path.join(OUT,"Informes_AJ_Ancash_2026_integrado.zip")
    with zipfile.ZipFile(zpath,"w",zipfile.ZIP_DEFLATED) as z:
        for f in pdfs: z.write(f,os.path.basename(f))
    return zpath,len(pdfs)

def cargar():
    return json.load(open(DATA,encoding="utf-8"))

def main():
    args=sys.argv[1:]; est=cargar()
    print(f"Estudiantes: {len(est)}")
    if not args: args=["--muestra","3"]
    if args[0]=="--todos":
        z,n=todos_zip(est); print(f"ZIP: {z} ({n})"); return
    if args[0]=="--muestra": sel=est[:int(args[1])]
    else:
        q=args[0].upper(); sel=[e for e in est if q in (e.get("estudiante") or "").upper()]
    print(f"Generando {len(sel)}...")
    for e in sel:
        print("OK:",os.path.basename(uno(e)))

if __name__=="__main__":
    main()
