# -*- coding: utf-8 -*-
"""
Plataforma de descarga de informes — Academia Juvenil 2026  (version saneada)

Version publica del proyecto real: se conservan la construccion de la plataforma,
los filtros cruzados, el modo por credencial y la automatizacion de reportes.
NO incluye credenciales ni datos de estudiantes (la lista de estudiantes y la base
local de contrasenas se generan aparte y nunca se versionan).
Login con las mismas credenciales de la intranet (copia local en SQLite).
Filtros cruzados tipo Power BI + selección con checkboxes + ZIP individual.
"""
import base64
import hashlib
import hmac
import json
import os
import re
import sqlite3
import tempfile
import time
import unicodedata
import zipfile
from datetime import datetime, timedelta, timezone
from typing import List

import bcrypt
from fastapi import FastAPI, Form, HTTPException, Request, Response
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse, StreamingResponse

BASE = os.environ.get("AJ_WEB", os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "data")
STATIC = os.path.join(BASE, "static")
PDF_DIR = os.environ.get("AJ_INFORMES",
          os.path.join(os.path.dirname(BASE), "informes_2026"))
DB = os.path.join(DATA, "plataforma.db")
EST_FILE = os.path.join(DATA, "estudiantes.json")
_EST = {"t": None, "d": None, "mapa": {}}

# Logo embebido: elimina una petición por página (clave con latencia alta)
LOGO_B64 = "data:image/png;base64," + base64.b64encode(
    open(os.path.join(STATIC, "logo_560.png"), "rb").read()).decode()
FAVICON = '<link rel="icon" href="data:image/png;base64,' + base64.b64encode(
    open(os.path.join(STATIC, "favicon_aj.png"), "rb").read()).decode() + '">'


def pagina(html: str) -> str:
    return html.replace("__LOGO__", LOGO_B64).replace("__FAVICON__", FAVICON)


def academias_de(cuenta: str):
    """(academias permitidas, aviso). Solo entran cuentas AJ<academia>."""
    n = normaliza(cuenta)
    if not n or not n.startswith("aj"):
        return set(), ("Esta plataforma es solo para cuentas de Academia Juvenil. "
                       "Si necesitas acceso, escribe a coordinación MEL.")
    clave = n[2:]
    if clave in estudiantes()["mapa"]:
        return {estudiantes()["mapa"][clave]}, None
    return set(), ("Tu cuenta aún no tiene informes generados en esta campaña. "
                   "Si crees que es un error, escribe a coordinación MEL.")


def datos_panel(cuenta: str):
    """(datos, academia_fija | None, aviso)"""
    permitidas, aviso = academias_de(cuenta)
    datos = [x for x in estudiantes()["datos"] if x["academia"] in permitidas]
    return datos, (next(iter(permitidas)) if len(permitidas) == 1 else None), aviso


def html_panel(cuenta: str = "") -> str:
    datos, fija, aviso = datos_panel(cuenta)
    return (pagina(PANEL)
            .replace("__DATOS__", json.dumps(datos, ensure_ascii=False))
            .replace("__ACADEMIA_FIJA__", json.dumps(fija, ensure_ascii=False))
            .replace("__CUENTA__", json.dumps(cuenta or "", ensure_ascii=False))
            .replace("__AVISO__", json.dumps(aviso or "", ensure_ascii=False)))

SECRET_FILE = os.path.join(DATA, ".secret")
if os.path.exists(SECRET_FILE):
    SECRET = open(SECRET_FILE, "rb").read()
else:
    SECRET = os.urandom(32)
    open(SECRET_FILE, "wb").write(SECRET)
    os.chmod(SECRET_FILE, 0o600)

# ---------------- alcance por credenciales -------------
# Cada cuenta AJ<NOMBRE> ve SOLO la academia que coincide con su nombre
# (AJCuenca -> AJ CUENCA). Las demás cuentas de la intranet (DNI de
# coordinación / MEL) mantienen acceso general.
def normaliza(s: str) -> str:
    s = unicodedata.normalize("NFKD", s or "")
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]", "", s.lower())


ACADEMIAS_TODAS = []


def estudiantes():
    """Datos de la plataforma. Se recargan solos cuando estudiantes.json cambia
    en disco: la web se mantiene al día sin reiniciar el servicio."""
    try:
        t = os.path.getmtime(EST_FILE)
    except OSError:
        t = None
    if _EST["d"] is None or _EST["t"] != t:
        try:
            with open(EST_FILE, encoding="utf-8") as fh:
                d = json.load(fh)
        except Exception:
            d = None  # archivo en escritura: se conserva lo último válido
        if d is not None:
            acads = sorted({x["academia"] for x in d["estudiantes"] if x["academia"] != "SIN DATO"})
            mapa = {}
            for a in acads:
                n = normaliza(a)
                mapa[n[2:] if n.startswith("aj") else n] = a
            _EST.update(t=t, d=d, mapa=mapa)
    return {"datos": (_EST["d"] or {}).get("estudiantes", []), "mapa": _EST["mapa"]}

MAX_INTENTOS = 5
ESPERA_SEG = 30

app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)


# ---------------- sesión ----------------
def firma(dni: str) -> str:
    b = base64.urlsafe_b64encode(hmac.new(SECRET, dni.encode(), hashlib.sha256).digest()).decode().rstrip("=")
    return f"{dni}.{b}"


def dni_de_cookie(v: str):
    if not v or "." not in v:
        return None
    dni, b = v.rsplit(".", 1)
    esperado = base64.urlsafe_b64encode(hmac.new(SECRET, dni.encode(), hashlib.sha256).digest()).decode().rstrip("=")
    return dni if hmac.compare_digest(b, esperado) else None


def usuario(request: Request):
    return dni_de_cookie(request.cookies.get("aj_sesion", ""))


# ---------------- base de datos ----------------
def db():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    return c


def ahora():
    return datetime.now(timezone.utc)


def validar(dni: str, clave: str):
    """Devuelve (ok, mensaje, segundos_espera)."""
    c = db()
    try:
        r = c.execute("select * from cuentas where dni = ? collate nocase", (dni.strip(),)).fetchone()
        if not r:
            return False, "Usuario o contraseña incorrectos.", 0
        if not normaliza(r["dni"]).startswith("aj"):
            # solo las cuentas de Academia Juvenil entran a esta plataforma
            return False, ("Esta plataforma es solo para cuentas de Academia Juvenil. "
                           "Si necesitas acceso, escribe a coordinación MEL."), 0
        if not r["is_active"]:
            return False, "La cuenta está inactiva.", 0
        if r["locked_until"]:
            lu = datetime.fromisoformat(r["locked_until"])
            if lu.tzinfo is None:
                lu = lu.replace(tzinfo=timezone.utc)
            if lu > ahora():
                return False, "Demasiados intentos.", int((lu - ahora()).total_seconds()) + 1
        h = r["password_hash"] or ""
        ok = False
        try:
            ok = bcrypt.checkpw(clave.encode("utf-8"), h.encode("utf-8"))
        except Exception:
            ok = False
        if ok:
            c.execute("update cuentas set failed_attempts=0, locked_until=NULL, last_login_at=? where dni=?",
                      (ahora().isoformat(), r["dni"]))
            c.commit()
            return True, "ok", 0
        n = (r["failed_attempts"] or 0) + 1
        if n >= MAX_INTENTOS:
            c.execute("update cuentas set failed_attempts=0, locked_until=? where dni=?",
                      ((ahora() + timedelta(seconds=ESPERA_SEG)).isoformat(), r["dni"]))
            c.commit()
            return False, "Demasiados intentos.", ESPERA_SEG
        c.execute("update cuentas set failed_attempts=? where dni=?", (n, r["dni"]))
        c.commit()
        return False, "Usuario o contraseña incorrectos.", 0
    finally:
        c.close()


# ---------------- páginas ----------------
LOGIN = """<!doctype html>
<html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Mi reporte personal — Academia Juvenil</title>
__FAVICON__
<style>
 *{box-sizing:border-box}
 body{margin:0;background:#fff;font-family:'Segoe UI',Roboto,Helvetica,Arial,sans-serif;color:#1a1a1a;
      min-height:100vh;display:flex;align-items:center;justify-content:center}
 .wrap{width:100%;max-width:430px;padding:24px;text-align:center}
 .logo{width:280px;max-width:80%;margin:0 auto 26px;display:block}
 h1{font-size:20px;font-weight:600;margin:0 0 4px}
 p.sub{color:#666;font-size:13px;margin:0 0 26px}
 .box{box-shadow:0 6px 24px rgba(0,0,0,.08);border:1px solid #ececec;border-radius:14px;padding:26px 22px;text-align:left}
 label{display:block;font-size:12px;font-weight:600;color:#444;margin:0 0 6px}
 input{width:100%;padding:12px;border:1px solid #d9d9d9;border-radius:9px;font-size:15px;margin-bottom:16px;outline:none}
 input:focus{border-color:#00AEEF}
 button{width:100%;padding:13px;border:0;border-radius:9px;background:#00AEEF;color:#fff;font-size:15px;font-weight:600;cursor:pointer}
 button:hover{background:#009bd6}
 .msg{margin-top:16px;padding:11px;border-radius:9px;font-size:13px;display:none}
 .err{background:#FDECEA;color:#B3261E}
 .ok{background:#E7F7EE;color:#0B7A44}
</style></head><body>
<div class="wrap">
  <img class="logo" src="__LOGO__" alt="Academia Juvenil">
  <h1>Mi reporte personal</h1>
  <p class="sub">Academia Juvenil 2026</p>
  <div class="box">
    <form id="f">
      <label for="u">Usuario</label>
      <input id="u" name="usuario" autocomplete="username" required autofocus>
      <label for="p">Contraseña</label>
      <input id="p" name="clave" type="password" autocomplete="current-password" required>
      <button id="b" type="submit">Ingresar</button>
    </form>
    <div id="m" class="msg"></div>
  </div>
  <p class="sub" style="margin-top:18px">Acceso exclusivo para cuentas de Academia Juvenil (AJ).</p>
</div>
<script>
const f=document.getElementById('f'),m=document.getElementById('m'),b=document.getElementById('b');
f.addEventListener('submit',async e=>{
  e.preventDefault(); m.style.display='none'; b.disabled=true; b.textContent='Ingresando…';
  const fd=new URLSearchParams(new FormData(f));
  try{
    const r=await fetch('login',{method:'POST',body:fd});
    const ct=r.headers.get('content-type')||'';
    if(ct.indexOf('text/html')>=0){document.open();document.write(await r.text());document.close();return;}
    const j=await r.json();
    if(j.ok){location.href='panel';return;}
    m.className='msg err';
    m.textContent = (j.espera>0) ? ('Demasiados intentos. Espera '+j.espera+' segundos e inténtalo otra vez.')
                                 : j.mensaje;
    m.style.display='block';
  }catch(err){ m.className='msg err'; m.textContent='Error de conexión. Vuelve a intentarlo.'; m.style.display='block'; }
  b.disabled=false; b.textContent='Ingresar';
});
</script></body></html>"""


@app.get("/", response_class=HTMLResponse)
def raiz(request: Request):
    cuenta = usuario(request)
    if cuenta:
        return HTMLResponse(html_panel(cuenta), headers={"Cache-Control": "no-store"})
    return HTMLResponse(pagina(LOGIN), headers={"Cache-Control": "no-store"})


@app.post("/login")
def login(usuario_: str = Form("", alias="usuario"), clave: str = Form("")):
    ok, msg, espera = validar(usuario_, clave)
    if not ok:
        return JSONResponse({"ok": False, "mensaje": msg, "espera": espera}, status_code=200)
    # el panel va en la misma respuesta: ahorra una vuelta de red
    r = HTMLResponse(html_panel(usuario_.strip()))
    r.set_cookie("aj_sesion", firma(usuario_.strip()), httponly=True, samesite="lax", max_age=8 * 3600)
    return r


@app.get("/salir")
def salir():
    r = RedirectResponse("/")
    r.delete_cookie("aj_sesion", path="/")
    r.headers["Cache-Control"] = "no-store"
    return r


PANEL = """<!doctype html>
<html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Mi reporte personal — Academia Juvenil</title>
__FAVICON__
<style>
 *{box-sizing:border-box}
 body{margin:0;background:#f5f7f9;font-family:'Segoe UI',Roboto,Helvetica,Arial,sans-serif;color:#1a1a1a}
 header{background:#fff;border-bottom:1px solid #e8e8e8;padding:12px 22px;display:flex;align-items:center;gap:14px}
 header img{height:46px}
 header h1{font-size:17px;margin:0;font-weight:600}
 header .sp{flex:1}
 header a{font-size:13px;color:#666;text-decoration:none;border:1px solid #ddd;padding:7px 12px;border-radius:8px}
 main{max-width:1080px;margin:0 auto;padding:20px}
 .filtros{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:12px;background:#fff;
          border:1px solid #e8e8e8;border-radius:12px;padding:16px}
 .filtros label{display:block;font-size:11px;font-weight:700;color:#666;text-transform:uppercase;letter-spacing:.4px;margin-bottom:5px}
 select,input[type=text]{width:100%;padding:9px;border:1px solid #d9d9d9;border-radius:8px;font-size:14px;background:#fff}
 .acciones{display:flex;flex-wrap:wrap;gap:10px;align-items:center;margin:14px 0 10px}
 .acciones .sp{flex:1}
 button{cursor:pointer;border:0;border-radius:9px;padding:11px 16px;font-size:14px;font-weight:600}
 .b1{background:#00AEEF;color:#fff}.b1:hover{background:#009bd6}
 .b2{background:#fff;color:#333;border:1px solid #d9d9d9}
 .b3{background:#00BF63;color:#fff}.b3:hover{background:#00a955}
 button:disabled{opacity:.55;cursor:not-allowed}
 .chk{display:flex;align-items:center;gap:8px;font-size:13px;background:#fff;border:1px solid #e8e8e8;padding:9px 13px;border-radius:9px}
 table{width:100%;border-collapse:collapse;background:#fff;border:1px solid #e8e8e8;border-radius:12px;overflow:hidden}
 th,td{padding:10px 12px;text-align:left;font-size:14px;border-bottom:1px solid #f0f0f0}
 th{background:#fafbfc;font-size:11px;text-transform:uppercase;letter-spacing:.4px;color:#666}
 tr:hover td{background:#fafcff}
 .badge{font-size:11px;padding:3px 9px;border-radius:20px;font-weight:600;white-space:nowrap}
 .si{background:#E7F7EE;color:#0B7A44}.no{background:#FFF3E0;color:#B26A00}
 .warn{color:#B26A00;font-size:11px;display:block}
 .contador{font-size:13px;color:#555}
 .salir{font-size:13px;font-weight:600;color:#333;text-decoration:none;border:1px solid #d9d9d9;background:#fff;
        padding:9px 15px;border-radius:9px;display:inline-flex;align-items:center;gap:7px}
 .salir:hover{background:#FDECEA;border-color:#E7B4AE;color:#B3261E}
 .salir svg{width:15px;height:15px;stroke:currentColor;fill:none;stroke-width:2;stroke-linecap:round;stroke-linejoin:round}
 .chip{font-size:12px;font-weight:600;color:#0B7A44;background:#E7F7EE;border-radius:20px;padding:5px 13px;white-space:nowrap}
 #aviso{display:none;position:fixed;left:50%;bottom:26px;transform:translateX(-50%);background:#111;color:#fff;
        padding:13px 22px;border-radius:10px;font-size:14px;z-index:9;box-shadow:0 6px 20px rgba(0,0,0,.25)}
 #aviso.ok{background:#0B7A44}
 .vacio{padding:26px;text-align:center;color:#888;background:#fff;border:1px solid #e8e8e8;border-radius:12px}
</style></head><body>
<header>
  <img src="__LOGO__" alt="Academia Juvenil">
  <h1>Mi reporte personal</h1><span class="chip" id="chip"></span><div class="sp"></div>
  <a class="salir" id="salir" href="salir" title="Cerrar la sesión">
    <svg viewBox="0 0 24 24"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><path d="m16 17 5-5-5-5"/><path d="M21 12H9"/></svg>
    Cerrar sesión
  </a>
</header>
<main>
  <div class="filtros">
    <div><label for="f_academia">Academia</label><select id="f_academia"></select></div>
    <div><label for="f_cp">Centro poblado</label><select id="f_cp"></select></div>
    <div><label for="f_ie">Institución educativa</label><select id="f_ie"></select></div>
    <div><label for="f_aula">Aula</label><select id="f_aula"></select></div>
    <div><label for="f_nombre">Buscar estudiante</label><input id="f_nombre" type="text" placeholder="Apellidos o nombres…"></div>
  </div>
  <div class="acciones">
    <button class="b2" id="limpiar" type="button">Limpiar filtros</button>
    <label class="chk"><input type="checkbox" id="todos"> Marcar todos los informes</label>
    <div class="sp"></div>
    <span class="contador" id="contador"></span>
    <button class="b3" id="descargar" type="button" disabled>Descargar seleccionados (ZIP)</button>
  </div>
  <table>
    <thead><tr><th style="width:44px"></th><th>Estudiante</th><th style="width:170px">Academia</th>
      <th style="width:220px">Estado</th></tr></thead>
    <tbody id="lista"></tbody>
  </table>
  <div id="vacio" class="vacio" style="display:none">Ningún estudiante coincide con los filtros.</div>
</main>
<div id="aviso"></div>
<script>
const DATOS = __DATOS__;
const FIJA = __ACADEMIA_FIJA__;
const CUENTA = __CUENTA__;
const AVISO_INI = __AVISO__;
const $ = id => document.getElementById(id);
const fmt = s => (s||'').trim();
function opciones(sel, valores, etiqueta){
  const actual = sel.value;
  sel.innerHTML = '<option value="">' + etiqueta + '</option>' +
    valores.map(v=>'<option value="'+v.replace(/"/g,'&quot;')+'">'+v+'</option>').join('');
  if(valores.includes(actual)) sel.value = actual;
}
function filtrados(){
  const a=$('f_academia').value, cp=$('f_cp').value, ie=$('f_ie').value, au=$('f_aula').value,
        q=fmt($('f_nombre').value).toLowerCase();
  return DATOS.filter(x=>
    (!a||x.academia===a) && (!cp||x.centro_poblado===cp) && (!ie||x.ie===ie) && (!au||x.aula===au) &&
    (!q||x.estudiante.toLowerCase().includes(q)));
}
function refrescarFiltros(){
  const a=$('f_academia').value, cp=$('f_cp').value, ie=$('f_ie').value, au=$('f_aula').value;
  const resta = (excluir) => DATOS.filter(x=>
      (excluir==='a' ||!a||x.academia===a) && (excluir==='cp'||!cp||x.centro_poblado===cp) &&
      (excluir==='ie'||!ie||x.ie===ie) && (excluir==='au'||!au||x.aula===au));
  const u = (arr,k)=>[...new Set(arr.map(x=>x[k]))].sort();
  opciones($('f_academia'), u(resta('a'),'academia'), 'Todas');
  opciones($('f_cp'),       u(resta('cp'),'centro_poblado'), 'Todos');
  opciones($('f_ie'),       u(resta('ie'),'ie'), 'Todas');
  opciones($('f_aula'),     u(resta('au'),'aula'), 'Todas');
  if(FIJA) $('f_academia').value = FIJA;
}
function pintar(){
  const rows = filtrados();
  const tb = $('lista'); tb.innerHTML='';
  rows.forEach(x=>{
    const tr = document.createElement('tr');
    const estado = x.completo
      ? '<span class="badge si">Información completa</span>'
      : '<span class="badge no">Información incompleta</span><span class="warn">El informe se puede descargar; verás «Información no disponible» en las secciones sin datos.</span>';
    tr.innerHTML = '<td><input type="checkbox" class="ck" data-id="'+x.clave+'"'+(x.completo?'':'')+'></td>'+
      '<td>'+x.estudiante+'</td><td>'+fmt(x.academia)+'</td><td>'+estado+'</td>';
    tb.appendChild(tr);
  });
  $('vacio').style.display = rows.length? 'none':'block';
  tb.querySelectorAll('.ck').forEach(c=>c.addEventListener('change',actualizarContador));
  actualizarContador();
  sincronizarTodos();
}
function marcados(){ return [...document.querySelectorAll('.ck:checked')]; }
function actualizarContador(){
  const n = marcados().length;
  $('contador').textContent = n + ' seleccionado' + (n===1?'':'s') + ' de ' + filtrados().length + ' mostrados';
  $('descargar').disabled = n===0;
}
function sincronizarTodos(){
  const visibles = [...document.querySelectorAll('.ck')];
  const t = $('todos');
  t.checked = visibles.length>0 && visibles.every(c=>c.checked);
  t.indeterminate = !t.checked && visibles.some(c=>c.checked);
}
function aviso(txt, ok, ms){
  const a=$('aviso'); a.textContent=txt; a.className = ok?'ok':''; a.style.display='block';
  if(ms) setTimeout(()=>a.style.display='none', ms);
}
['f_academia','f_cp','f_ie','f_aula'].forEach(id=>$(id).addEventListener('change',()=>{
  refrescarFiltros(); pintar();
}));
$('f_nombre').addEventListener('input', pintar);
$('limpiar').addEventListener('click',()=>{
  ['f_academia','f_cp','f_ie','f_aula'].forEach(id=>$(id).value='');
  if(FIJA) $('f_academia').value = FIJA;
  $('f_nombre').value=''; document.querySelectorAll('.ck').forEach(c=>c.checked=false);
  $('todos').checked=false; refrescarFiltros(); pintar();
});
$('todos').addEventListener('change',e=>{
  document.querySelectorAll('.ck').forEach(c=>c.checked=e.target.checked);
  actualizarContador();
});
$('descargar').addEventListener('click',async ()=>{
  const ids = marcados().map(c=>c.dataset.id);
  if(!ids.length) return;
  aviso('Iniciando descarga de '+ids.length+' informe(s)…', false, 0);
  $('descargar').disabled = true;
  try{
    const r = await fetch('zip', {method:'POST', headers:{'Content-Type':'application/json'},
                                 body: JSON.stringify({ids})});
    if(!r.ok) throw new Error('http '+r.status);
    const blob = await r.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href=url; a.download='Informes_Academia_Juvenil_2026.zip'; a.click();
    URL.revokeObjectURL(url);
    aviso('Descarga finalizada: '+ids.length+' informe(s).', true, 6000);
  }catch(e){
    aviso('No se pudo completar la descarga. Inténtalo otra vez.', false, 6000);
  }
  $('descargar').disabled = false;
});
// --- alcance según las credenciales ---
if(CUENTA){
  $('chip').textContent = AVISO_INI ? 'Sin informes asignados'
                       : (FIJA ? ('Acceso: '+FIJA) : 'Acceso general');
}
if(FIJA){
  // El select de academia no aporta si la cuenta está acotada a una sola
  $('f_academia').parentElement.style.display = 'none';
}
if(AVISO_INI){
  document.querySelector('.filtros').style.display='none';
  document.querySelector('.acciones').style.display='none';
  document.querySelector('table').style.display='none';
}
pintar(); refrescarFiltros(); pintar();
if(AVISO_INI){
  const v=$('vacio'); v.textContent=AVISO_INI; v.style.display='block';
  document.querySelector('main').style.paddingTop='0';
}
</script></body></html>"""


@app.get("/panel", response_class=HTMLResponse)
def panel(request: Request):
    cuenta = usuario(request)
    if not cuenta:
        return RedirectResponse("/")
    return HTMLResponse(html_panel(cuenta), headers={"Cache-Control": "no-store"})
@app.get("/logo.png")
def logo():
    r = FileResponse(os.path.join(STATIC, "logo_560.png"), media_type="image/png")
    r.headers["Cache-Control"] = "public, max-age=604800, immutable"
    return r


@app.post("/zip")
async def zip_descarga(request: Request):
    cuenta = usuario(request)
    if not cuenta:
        raise HTTPException(401)
    body = await request.json()
    ids = body.get("ids") or []
    permitidas, _ = academias_de(cuenta)
    por_clave = {x["clave"]: x for x in estudiantes()["datos"] if x["academia"] in permitidas}
    sel = [por_clave[i] for i in ids if i in por_clave]
    sel.sort(key=lambda x: x["estudiante"].upper())
    if not sel:
        raise HTTPException(400, "sin seleccion")
    tmp = tempfile.NamedTemporaryFile(prefix="informes_aj_", suffix=".zip", delete=False)
    tmp.close()
    with zipfile.ZipFile(tmp.name, "w", zipfile.ZIP_DEFLATED, compresslevel=1) as z:
        for x in sel:
            ruta = os.path.join(PDF_DIR, x["archivo"])
            if os.path.exists(ruta):
                z.write(ruta, arcname=x["archivo"])
    nombre = "Informes_Academia_Juvenil_2026.zip"
    return FileResponse(tmp.name, media_type="application/zip", filename=nombre,
                        background=__import__("starlette.background", fromlist=["BackgroundTask"]).BackgroundTask(
                            lambda p=tmp.name: os.path.exists(p) and os.remove(p)))
