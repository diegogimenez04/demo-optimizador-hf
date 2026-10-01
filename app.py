#!/usr/bin/env python3
# app.py — Demo Grupo Investigación — Formulario -> model.py (ortools)
# Uso: pip install flask ortools  &&  python app.py  -> http://localhost:5000
# Solo accede a este directorio y subdirectorios.
import pathlib
from datetime import datetime, timedelta
from collections import Counter
from flask import Flask, request, jsonify, send_from_directory

from model import function_model

BASE_DIR = pathlib.Path(__file__).parent
app = Flask(__name__)

OPTIMIZER_HTML = r"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Optimizador — Demo Grupo Investigación</title>
<script src="https://www.gstatic.com/charts/loader.js"></script>
<style>
 *{box-sizing:border-box} body{margin:0;font-family:Inter,Segoe UI,Arial,sans-serif;color:#1e293b;background:#f8fafc;line-height:1.5}
 header{background:linear-gradient(135deg,#0f172a 0%,#1e3a5f 60%,#0e7490 100%);color:#fff;padding:24px}
 header h1{margin:0;font-size:20px} header p{margin:6px 0 0;opacity:.9;font-size:13px;max-width:900px}
 .badge{display:inline-block;margin-top:10px;background:#facc15;color:#422006;font-size:11px;font-weight:700;padding:4px 10px;border-radius:999px}
 main{max-width:1200px;margin:0 auto;padding:16px}
 .card{background:#fff;border:1px solid #e2e8f0;border-radius:14px;padding:16px;margin-bottom:16px;box-shadow:0 1px 2px rgba(0,0,0,.04)}
 .card h3{margin:0 0 6px;font-size:15px} .meta{font-size:12px;color:#64748b;margin-bottom:8px}
 label{font-size:12px;font-weight:600;color:#334155;display:block;margin:6px 0 4px}
 input,select{width:100%;padding:8px 10px;border:1px solid #cbd5e1;border-radius:8px;font-size:13px;background:#fff}
 input:focus{outline:2px solid #38bdf8;border-color:#38bdf8}
 .row{display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px}
 @media(max-width:800px){.row{grid-template-columns:1fr}}
 table{width:100%;border-collapse:collapse;margin-top:8px}
 th{font-size:11px;text-transform:uppercase;letter-spacing:.4px;color:#475569;background:#f8fafc;padding:8px;border:1px solid #e2e8f0;text-align:left}
 td{border:1px solid #e2e8f0;padding:4px}
 td input{border:none;padding:6px 8px;border-radius:0}
 td input:focus{outline:1px solid #38bdf8}
 .btn{border:none;padding:9px 14px;border-radius:999px;font-weight:700;font-size:13px;cursor:pointer}
 .btn-primary{background:#0f172a;color:#fff} .btn-primary:disabled{opacity:.5;cursor:not-allowed}
 .btn-ghost{background:#fff;border:1px solid #cbd5e1;color:#334155} .btn-danger{background:#fee2e2;border:1px solid #fecaca;color:#991b1b}
 .toolbar{display:flex;gap:8px;flex-wrap:wrap;margin-top:10px}
 .kpi{display:flex;gap:8px;flex-wrap:wrap;margin:8px 0}
 .kpi span{background:#f1f5f9;border:1px solid #e2e8f0;border-radius:999px;padding:4px 10px;font-size:12px;font-weight:600}
 .alert{padding:10px 12px;border-radius:8px;font-size:12px;margin:8px 0}
 .alert-warn{background:#fef9c3;border:1px solid #facc15;color:#713f12}
 .alert-err{background:#fee2e2;border:1px solid #fecaca;color:#7f1d1d}
 .alert-ok{background:#dcfce7;border:1px solid #86efac;color:#14532d}
 #timeline-live{height:340px;border:1px solid #f1f5f9;border-radius:10px;background:#fcfcfc}
 .note{font-size:12px;color:#64748b}
 a{color:#0ea5e9;text-decoration:none}
</style>
</head>
<body>
<header>
  <h1>Optimizador — Demo Grupo Investigación <span style="font-weight:400;opacity:.8">| Form → Modelo OR-Tools</span></h1>
  <p>Formulario más simple posible que consume los parámetros del <code>model_input</code> de <code>starplastic.ipynb</code> y ejecuta <code>function_model</code> (ortools SCIP). Sin logo, datos sintéticos.</p>
  <span class="badge">DEMO · DATOS SINTÉTICOS</span>
  <div style="margin-top:8px;font-size:12px"><a href="/demo" style="color:#facc15">↗ Ver proceso unificado histórico (7 escenarios)</a></div>
</header>
<main>
  <div class="card">
    <h3>Parámetros globales</h3>
    <div class="row">
      <div><label>Fecha inicio plan</label><input id="fecha_inicio_plan" type="datetime-local" value="2023-10-11T12:00"></div>
      <div><label>Tiempo setup (hs) — changeover</label><input id="tiempo_setup" type="number" step="0.1" value="0.5"></div>
      <div><label>Cantidad operarios disponibles</label><input id="cantidad_operarios" type="number" min="1" value="3"></div>
    </div>
    <div class="meta">Validación 3: fecha inicio no puede ser anterior a ahora-3h (UTC). Validación 4: cada OT operarios_requeridos ≤ disponibles.</div>
  </div>

  <div class="card">
    <h3>Máquinas disponibles</h3>
    <div class="meta">Pool de máquinas del proceso. Por defecto 5 máquinas (23, 24, 25, 26, 27) para mostrar escalabilidad — edita, añade o elimina. Las OTs y ventanas usan este listado.</div>
    <div id="machines-list" class="kpi"></div>
    <div class="row" style="grid-template-columns:1fr auto;align-items:end">
      <div><label>Nueva máquina ID</label><input id="new-machine" placeholder="Ej: 28, M6, COEX-28"></div>
      <div><button class="btn btn-ghost" onclick="addMachine()">+ Añadir máquina</button></div>
    </div>
  </div>

  <div class="card">
    <h3>Órdenes de Trabajo (OTs)</h3>
    <div class="meta">Campos mínimos para el modelo: ot_nro, maquina_nro, horas, prioridad, operarios_requeridos, fecha_vencimiento. 5 OTs asignadas por defecto (una por máquina).</div>
    <table id="ots-table">
      <thead><tr><th>ID</th><th>OT nro</th><th>Máquina</th><th>Horas</th><th>Prioridad</th><th>Operarios req.</th><th>Vencimiento</th><th></th></tr></thead>
      <tbody></tbody>
    </table>
    <div class="toolbar">
      <button class="btn btn-ghost" onclick="addOT()">+ Añadir OT</button>
      <button class="btn btn-ghost" onclick="resetOTsExample()">Restaurar ejemplo 5 OTs</button>
      <button class="btn btn-ghost" onclick="clearOTs()">Vaciar</button>
    </div>
  </div>

  <div class="card">
    <h3>Máquinas fuera de servicio</h3>
    <div class="meta">Ventanas de indisponibilidad por máquina. Si no hay, deja vacío. Validación 9: hora_fin &gt; hora_inicio.</div>
    <table id="fs-table">
      <thead><tr><th>ID</th><th>Máquina</th><th>Hora inicio</th><th>Hora fin</th><th></th></tr></thead>
      <tbody></tbody>
    </table>
    <div class="toolbar">
      <button class="btn btn-ghost" onclick="addFS()">+ Añadir ventana</button>
      <button class="btn btn-ghost" onclick="clearFS()">Vaciar</button>
    </div>
  </div>

  <div class="card">
    <div class="toolbar">
      <button id="btn-run" class="btn btn-primary" onclick="runModel()">▶ Optimizar (ejecutar function_model)</button>
      <button class="btn btn-ghost" onclick="downloadJSON()">Descargar JSON model_input</button>
      <span id="run-status" class="note"></span>
    </div>
    <div id="validaciones"></div>
  </div>

  <div id="results" style="display:none">
    <div class="card">
      <h3>Resultados — Indicadores</h3>
      <div id="kpis" class="kpi"></div>
      <div class="row">
        <div><label>Completamiento (makespan hs)</label><div id="kpi-mk" class="kpi"><span>-</span></div></div>
        <div><label>Productividad operarios</label><div id="kpi-prod" class="kpi"><span>-</span></div></div>
        <div><label>Total producción / setup</label><div id="kpi-setup" class="kpi"><span>-</span></div></div>
      </div>
      <h3 style="margin-top:12px">Agenda por máquina (Gantt)</h3>
      <div id="timeline-live"></div>
      <h3 style="margin-top:12px">Tablas agenda</h3>
      <div id="agenda-tables" style="display:grid;grid-template-columns:1fr 1fr;gap:12px"></div>
      <details style="margin-top:10px"><summary style="cursor:pointer;font-size:12px;color:#475569">Ver JSON model_output completo</summary><pre id="raw-output" style="background:#0f172a;color:#e2e8f0;padding:12px;border-radius:8px;overflow:auto;max-height:300px;font-size:11px"></pre></details>
    </div>
  </div>
</main>
<footer style="text-align:center;color:#94a3b8;font-size:12px;padding:10px">Demo Grupo Investigación · Sin logo · Flask + ortools · Solo este directorio</footer>
<script>
let otId=1, fsId=1;
let machines=["23","24","25","26","27"];
function renderMachines(){
 const cont=document.getElementById('machines-list');
 cont.innerHTML=machines.map(m=>`<span>${m} <button onclick="removeMachine('${m}')" style="margin-left:6px;border:none;background:#fee2e2;color:#991b1b;border-radius:999px;cursor:pointer;padding:1px 6px">×</button></span>`).join('');
 // update all selects
 document.querySelectorAll('select[data-k=\"maquina_nro\"], select[data-k=\"maquina\"]').forEach(sel=>{
   const cur=sel.value;
   sel.innerHTML=machines.map(mm=>`<option value=\"${mm}\" ${mm===cur?'selected':''}>${mm}</option>`).join('');
   if(cur && !machines.includes(cur)) sel.innerHTML+=`<option value=\"${cur}\" selected>${cur} (fuera de pool)</option>`;
 });
}
function addMachine(){
 const inp=document.getElementById('new-machine');
 const v=inp.value.trim();
 if(!v) return;
 if(machines.includes(v)){ alert('Máquina ya existe'); return; }
 machines.push(v); inp.value=''; renderMachines();
}
function removeMachine(m){
 if(machines.length<=1){ alert('Debe quedar al menos 1 máquina'); return; }
 machines=machines.filter(x=>x!==m); renderMachines();
}
function machineOptions(selected){
 return machines.map(mm=>`<option value=\"${mm}\" ${mm===selected?'selected':''}>${mm}</option>`).join('');
}
function addOT(pref={}){
 const tb=document.querySelector('#ots-table tbody');
 const id=otId++;
 const selMachine=pref.maquina_nro||machines[(id-1)%machines.length];
 const tr=document.createElement('tr');
 tr.innerHTML=`<td><input value="${pref.id||id}" data-k="id" type="number" min="1"></td>
 <td><input value="${pref.ot_nro||'OT'+id}" data-k="ot_nro"></td>
 <td><select data-k="maquina_nro" style="border:none;padding:6px 8px">${machineOptions(selMachine)}</select></td>
 <td><input value="${pref.horas||8}" data-k="horas" type="number" step="0.1" min="0.1"></td>
 <td><input value="${pref.prioridad||id}" data-k="prioridad" type="number" min="1"></td>
 <td><input value="${pref.operarios_requeridos||1}" data-k="operarios_requeridos" type="number" min="1" step="1"></td>
 <td><input value="${pref.fecha_vencimiento||'2023-10-20'}" data-k="fecha_vencimiento" type="date"></td>
 <td><button class="btn btn-danger" onclick="this.closest('tr').remove()" style="padding:4px 8px">×</button></td>`;
 tb.appendChild(tr);
}
function addFS(pref={}){
 const tb=document.querySelector('#fs-table tbody');
 const id=fsId++;
 const selMachine=pref.maquina||machines[0];
 const tr=document.createElement('tr');
 tr.innerHTML=`<td><input value="${pref.id||id}" data-k="id" type="number" min="1"></td>
 <td><select data-k="maquina" style="border:none;padding:6px 8px">${machineOptions(selMachine)}</select></td>
 <td><input value="${pref.hora_inicio||'2023-10-12T20:00'}" data-k="hora_inicio" type="datetime-local"></td>
 <td><input value="${pref.hora_fin||'2023-10-12T10:00'}" data-k="hora_fin" type="datetime-local"></td>
 <td><button class="btn btn-danger" onclick="this.closest('tr').remove()" style="padding:4px 8px">×</button></td>`;
 tb.appendChild(tr);
}
function clearOTs(){document.querySelector('#ots-table tbody').innerHTML=''; otId=1;}
function clearFS(){document.querySelector('#fs-table tbody').innerHTML=''; fsId=1;}
function resetOTsExample(){
 clearOTs();
 // 5 OTs, una por máquina para mostrar proceso con 5 máquinas
 addOT({id:1, ot_nro:'24597', maquina_nro:'23', horas:34.9, prioridad:3, operarios_requeridos:1, fecha_vencimiento:'2023-10-20'});
 addOT({id:2, ot_nro:'24599', maquina_nro:'24', horas:12, prioridad:2, operarios_requeridos:1, fecha_vencimiento:'2023-10-20'});
 addOT({id:3, ot_nro:'24608', maquina_nro:'25', horas:14, prioridad:1, operarios_requeridos:2, fecha_vencimiento:'2023-10-20'});
 addOT({id:4, ot_nro:'24610', maquina_nro:'26', horas:8, prioridad:4, operarios_requeridos:1, fecha_vencimiento:'2023-10-20'});
 addOT({id:5, ot_nro:'24612', maquina_nro:'27', horas:10, prioridad:5, operarios_requeridos:1, fecha_vencimiento:'2023-10-20'});
}
function resetFSExample(){
 clearFS();
 addFS({id:1, maquina:'25', hora_inicio:'2023-10-12T20:00', hora_fin:'2023-10-12T10:00'});
 addFS({id:2, maquina:'27', hora_inicio:'2023-10-12T17:00', hora_fin:'2023-10-12T08:00'});
}
function collect(){
 const fecha_inicio_plan=document.getElementById('fecha_inicio_plan').value;
 const tiempo_setup=parseFloat(document.getElementById('tiempo_setup').value);
 const cantidad_operarios=parseInt(document.getElementById('cantidad_operarios').value);
 const ots=[...document.querySelectorAll('#ots-table tbody tr')].map(tr=>{
   const o={}; tr.querySelectorAll('input,select').forEach(inp=>{o[inp.dataset.k]=inp.value});
   o.id=parseInt(o.id); o.horas=parseFloat(o.horas); o.prioridad=parseInt(o.prioridad); o.operarios_requeridos=parseInt(o.operarios_requeridos);
   return o;
 });
 const fuera=[...document.querySelectorAll('#fs-table tbody tr')].map(tr=>{
   const o={}; tr.querySelectorAll('input,select').forEach(inp=>{o[inp.dataset.k]=inp.value}); o.id=parseInt(o.id); return o;
 });
 return {fecha_inicio_plan, tiempo_setup, cantidad_operarios, ots, fuera_servicios:fuera};
}
function downloadJSON(){
 const data=collect(); const blob=new Blob([JSON.stringify(data,null,2)],{type:'application/json'});
 const a=document.createElement('a'); a.href=URL.createObjectURL(blob); a.download='model_input.json'; a.click();
}
async function runModel(){
 const btn=document.getElementById('btn-run'); btn.disabled=true; btn.textContent='⏳ Optimizando…';
 document.getElementById('run-status').textContent=''; document.getElementById('validaciones').innerHTML='';
 const payload=collect();
  // quick client checks
   if(payload.ots.length===0){ document.getElementById('validaciones').innerHTML='<div class=\"alert alert-err\">Añade al menos 1 OT.</div>'; btn.disabled=false; btn.textContent='▶ Optimizar'; return; }
 try{
  const res=await fetch('/api/optimize',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});
  const js=await res.json();
  if(!res.ok){ throw new Error(js.error||'Error'); }
  renderValidaciones(js.validaciones);
  if(js.model_output && Object.keys(js.model_output).length>0){
    renderResults(js.model_output);
  } else {
    document.getElementById('validaciones').innerHTML+='<div class=\"alert alert-err\">Modelo infactible — revisa validaciones.</div>';
  }
  document.getElementById('run-status').textContent=`OK · ${js.solver_info||''}`;
 }catch(e){
  document.getElementById('validaciones').innerHTML=`<div class="alert alert-err">Error: ${e.message}</div>`;
  document.getElementById('run-status').textContent='Error';
 }finally{ btn.disabled=false; btn.textContent='▶ Optimizar (ejecutar function_model)';}
}
function renderValidaciones(v){
 if(!v) return; let html='';
 for(const [k,val] of Object.entries(v)){
  const isOk = (typeof val==='string' && val.includes('ok')) || (Array.isArray(val) && val.every(x=>JSON.stringify(x).includes('ok')));
  const cls=isOk?'alert-ok':'alert-warn';
  html+=`<div class="alert ${cls}"><strong>${k}:</strong> ${Array.isArray(val)? val.map(x=>JSON.stringify(x)).join(' | ') : JSON.stringify(val) }</div>`;
 }
 document.getElementById('validaciones').innerHTML=html;
}
function renderResults(out){
 document.getElementById('results').style.display='block';
 document.getElementById('kpis').innerHTML=`<span>Completamiento: ${out.completamiento_ordenes?.toFixed(2)} hs</span><span>Prod: ${(out.productividad_operarios*100).toFixed(1)}%</span><span>Setup: ${out.total_setup}</span><span>Tardanza: ${out.tardanza_total}</span>`;
 document.getElementById('kpi-mk').innerHTML=`<span>${out.completamiento_ordenes?.toFixed(2)} hs</span>`;
 document.getElementById('kpi-prod').innerHTML=`<span>${(out.productividad_operarios*100).toFixed(1)} %</span>`;
 document.getElementById('kpi-setup').innerHTML=`<span>Prod ${out.total_produccion} hs / Setup ${out.total_setup} hs</span>`;
 document.getElementById('raw-output').textContent=JSON.stringify(out,null,2);
 // tables
 const agenda=out.agenda_maquina_ot||[];
 const personal=out.agenda_personal||[];
 let html=`<div><h4>agenda_maquina_ot</h4><table><thead><tr><th>OT</th><th>Maq</th><th>Inicio</th><th>Fin</th></tr></thead><tbody>${agenda.map(r=>`<tr><td>${r.ot_nro}</td><td>${r.maquina_nro}</td><td>${r.hora_inicio}</td><td>${r.hora_fin}</td></tr>`).join('')}</tbody></table></div>`;
 html+=`<div><h4>agenda_personal</h4><table><thead><tr><th>ID</th><th>Cant</th><th>Inicio</th><th>Fin</th></tr></thead><tbody>${personal.map(r=>`<tr><td>${r.id}</td><td>${r.cant_personal}</td><td>${r.hora_inicio}</td><td>${r.hora_fin}</td></tr>`).join('')}</tbody></table></div>`;
 document.getElementById('agenda-tables').innerHTML=html;
 drawTimelineLive(agenda);
 window.scrollTo({top: document.getElementById('results').offsetTop-20, behavior:'smooth'});
}
function drawTimelineLive(agenda){
 if(!agenda || agenda.length===0) return;
 google.charts.load('current',{packages:['timeline']});
 google.charts.setOnLoadCallback(()=>{
   const el=document.getElementById('timeline-live');
   const chart=new google.visualization.Timeline(el);
   const dt=new google.visualization.DataTable();
   dt.addColumn({type:'string',id:'Maquina'});
   dt.addColumn({type:'string',id:'OT'});
   dt.addColumn({type:'date',id:'Start'});
   dt.addColumn({type:'date',id:'End'});
   // parse dd/mm/yyyy hh:mm -> date
   function parse(s){
     // s like 12/10/2023 08:00  or 12/10/2023 08:00 from model (d/m/Y H:M)
     const m=s.match(/(\d+)\/(\d+)\/(\d+)\s+(\d+):(\d+)/);
     if(!m) return new Date(s);
     return new Date(parseInt(m[3]), parseInt(m[2])-1, parseInt(m[1]), parseInt(m[4]), parseInt(m[5]));
   }
   dt.addRows(agenda.map(r=>[String(r.maquina_nro), String(r.ot_nro), parse(r.hora_inicio), parse(r.hora_fin)]));
   chart.draw(dt,{timeline:{showRowLabels:true},avoidOverlappingGridLines:true});
 });
}
renderMachines(); resetOTsExample(); resetFSExample();
</script>
</body>
</html>
"""

@app.route("/")
def index():
    return OPTIMIZER_HTML, 200, {"Content-Type": "text/html; charset=utf-8"}

@app.route("/demo")
def demo():
    p = BASE_DIR / "demo_proceso_unificado.html"
    if p.exists():
        return p.read_text(encoding="utf-8"), 200, {"Content-Type": "text/html; charset=utf-8"}
    return "demo not found", 404

@app.route("/api/health")
def health():
    return jsonify({"ok": True})

@app.route("/api/optimize", methods=["POST"])
def optimize():
    try:
        data = request.get_json(force=True)
        # --- parse globales ---
        fecha_inicio_plan_str = data.get("fecha_inicio_plan")
        # accept datetime-local like 2023-10-11T12:00
        try:
            fecha_inicio_plan = datetime.fromisoformat(fecha_inicio_plan_str)
        except:
            fecha_inicio_plan = datetime.strptime(fecha_inicio_plan_str, "%d/%m/%Y %H:%M")

        tiempo_setup = float(data.get("tiempo_setup", 0.5))
        cantidad_operarios = int(data.get("cantidad_operarios", 3))
        ots_raw = data.get("ots", [])
        fuera_raw = data.get("fuera_servicios", [])

        # build model_input-like structures
        # ots: add required fields for downstream
        model_ots = []
        for o in ots_raw:
            # fecha_vencimiento may be YYYY-MM-DD
            fv = o.get("fecha_vencimiento")
            try:
                fecha_v = datetime.fromisoformat(fv)
            except:
                try:
                    fecha_v = datetime.strptime(fv, "%Y-%m-%d")
                except:
                    fecha_v = datetime.strptime(fv, "%d/%m/%Y")
            model_ots.append({
                "id": int(o["id"]),
                "ot_nro": str(o["ot_nro"]),
                "maquina_nro": str(o["maquina_nro"]),
                "horas": float(o["horas"]),
                "prioridad": int(o["prioridad"]),
                "operarios_requeridos": int(o["operarios_requeridos"]),
                "fecha_vencimiento": fecha_v,
            })

        # fuera_servicios
        model_fuera = []
        for f in fuera_raw:
            if not f.get("maquina"):
                continue
            hi = f.get("hora_inicio")
            hf = f.get("hora_fin")
            try:
                hi_dt = datetime.fromisoformat(hi)
            except:
                hi_dt = datetime.strptime(hi, "%d/%m/%Y %H:%M")
            try:
                hf_dt = datetime.fromisoformat(hf)
            except:
                hf_dt = datetime.strptime(hf, "%d/%m/%Y %H:%M")
            model_fuera.append({"id": int(f["id"]), "maquina": str(f["maquina"]), "hora_inicio": hi_dt, "hora_fin": hf_dt})

        # --- derived sets/params like notebook ---
        lista_id = [{"id": e["id"], "ot": e["ot_nro"], "maquina": e["maquina_nro"]} for e in model_ots]
        ots = [o["ot_nro"] for o in model_ots]
        maquinas = list(set(o["maquina_nro"] for o in model_ots))
        fuera_servicios = list(set(item["maquina"] for item in model_fuera))
        operarios_requeridos = {o["ot_nro"]: o["operarios_requeridos"] for o in model_ots}
        asignacion = {o["ot_nro"]: o["maquina_nro"] for o in model_ots}
        prioridad = {o["ot_nro"]: o["prioridad"] for o in model_ots}
        proc = {o["ot_nro"]: o["horas"] for o in model_ots}
        fecha_vencimiento = {o["ot_nro"]: o["fecha_vencimiento"] for o in model_ots}
        fecha_entrega = {ot_nro: (fecha - fecha_inicio_plan).total_seconds()/3600 + 24 for ot_nro, fecha in fecha_vencimiento.items()}

        tiinactiva = {}
        tfinactiva = {}
        for item in model_fuera:
            maq = item["maquina"]
            tiinactiva[maq] = float((item["hora_inicio"] - fecha_inicio_plan).total_seconds()/3600)
            tfinactiva[maq] = float((item["hora_fin"] - fecha_inicio_plan).total_seconds()/3600)

        changeover = {(ot1, ot2): tiempo_setup if ot1 != ot2 else 0.0 for ot1 in ots for ot2 in ots}

        # --- validaciones simplificadas ---
        dicc_validaciones = {}

        # V1: prioridad 1 vs fuera servicio (from notebook)
        ot_prioridad_1 = next((o for o in model_ots if o["prioridad"] == 1), None)
        if ot_prioridad_1:
            msgs=[]
            for fs in model_fuera:
                if fs["maquina"] == ot_prioridad_1["maquina_nro"]:
                    if fs["maquina"] in tiinactiva and tiinactiva[fs["maquina"]] < ot_prioridad_1["horas"]:
                        msgs.append(f"OT {ot_prioridad_1['ot_nro']} prio1 {ot_prioridad_1['horas']}hs bloquea maq {fs['maquina']} ventana {fs['hora_inicio']}->{fs['hora_fin']}")
            dicc_validaciones["Validacion_1"] = "; ".join(msgs) if msgs else "ok - prio1 maquina disponible"
        else:
            dicc_validaciones["Validacion_1"] = "sin OT prioridad 1"

        # V2: fecha inicio vs plan
        v2=[]
        for fs in model_fuera:
            if fs["hora_inicio"] < fecha_inicio_plan:
                v2.append(f"Maquina {fs['maquina']}: fuera servicio anterior a plan")
            else:
                v2.append(f"Maquina {fs['maquina']}: ok")
        dicc_validaciones["Validacion_2"] = v2 if v2 else "sin fuera servicio"

        # V3: fecha inicio plan vs ahora-3h
        fecha_control = datetime.now() - timedelta(hours=3)
        if fecha_inicio_plan < fecha_control:
            dicc_validaciones["Validacion_3"] = f"fecha inicio plan {fecha_inicio_plan} anterior a {fecha_control} (hoy-3h) - solo aviso demo"
        else:
            dicc_validaciones["Validacion_3"] = "ok"

        # V4: operarios requeridos <= disponibles
        v4=[]
        for o in model_ots:
            if o["operarios_requeridos"] > cantidad_operarios:
                v4.append(f"OT {o['ot_nro']} requiere {o['operarios_requeridos']} > {cantidad_operarios}")
            else:
                v4.append(f"OT {o['ot_nro']}: ok")
        dicc_validaciones["Validacion_4"] = v4

        # V5: IDs duplicados
        ids = [o["id"] for o in model_ots]
        dups = [id for id,c in Counter(ids).items() if c>1]
        dicc_validaciones["Validacion_5"] = f"IDs duplicados {dups}" if dups else "ok - ids unicos"

        # V7: vencimiento < inicio
        v7=[]
        for o in model_ots:
            if o["fecha_vencimiento"] < fecha_inicio_plan:
                v7.append(f"OT {o['ot_nro']}: vencimiento anterior a inicio")
            else:
                v7.append(f"OT {o['ot_nro']}: ok")
        dicc_validaciones["Validacion_7"] = v7

        # V8: fraccional
        frac=[]
        for k,v in operarios_requeridos.items():
            if (v - int(v)) != 0:
                frac.append(f"OT {k}: fraccional")
        dicc_validaciones["Validacion_8"] = "; ".join(frac) if frac else "ok - enteros"

        # V9: fin < inicio fuera servicio
        v9=[]
        for fs in model_fuera:
            maq=fs["maquina"]
            if maq in tiinactiva and maq in tfinactiva and tiinactiva[maq] >= tfinactiva[maq]:
                v9.append(f"Maquina {maq}: fin < inicio")
            else:
                v9.append(f"Maquina {maq}: ok")
        dicc_validaciones["Validacion_9"] = v9 if v9 else "sin fuera servicio"

        # V10 + operarios list logic (notebook final)
        max_operarios_por_maquina={}
        for o in model_ots:
            maq=o["maquina_nro"]; req=o["operarios_requeridos"]
            max_operarios_por_maquina[maq]=max(max_operarios_por_maquina.get(maq,0), req)
        total_operarios_requeridos = sum(max_operarios_por_maquina.values())
        if total_operarios_requeridos < cantidad_operarios:
            operarios = [f"o{i+1}" for i in range(cantidad_operarios)]
        else:
            operarios = [f"o{i+1}" for i in range(total_operarios_requeridos)]
        dicc_validaciones["Validacion_10_operarios"] = f"max_por_maq {max_operarios_por_maquina} total {total_operarios_requeridos} -> operarios {operarios} (cant {len(operarios)}) vs solicitados {cantidad_operarios}"

        # early block if critical infeasible
        crit_fail=False
        if dups: crit_fail=True
        if any(o["operarios_requeridos"] > len(operarios) for o in model_ots):
            # actually model checks vs original cantidad but we already expanded operarios
            pass

        # --- run model ---
        # Need fecha_entrega dict already, tiinactiva/tfinactiva may be empty dict -> model expects entries for fuera_servicios only
        model_output = function_model(lista_id, operarios, ots, maquinas, fuera_servicios, operarios_requeridos, asignacion, prioridad, proc, fecha_entrega, tiinactiva, tfinactiva, changeover, fecha_inicio_plan)

        # function_model prints to stdout; capture solver info if needed
        solver_info = f"operarios {operarios} | maquinas {maquinas} | ots {ots}"

        return jsonify({"validaciones": dicc_validaciones, "model_output": model_output, "solver_info": solver_info})
    except Exception as e:
        import traceback
        return jsonify({"error": str(e), "trace": traceback.format_exc()}), 500

if __name__ == "__main__":
    # only this directory — HF Spaces uses PORT=7860, local defaults to 5000
    import os
    port = int(os.environ.get("PORT", 5000))
    host = "0.0.0.0" if os.environ.get("PORT") else "127.0.0.1"
    print(f"Serving from {BASE_DIR} on {host}:{port}")
    print(f"Open http://{host}:{port}  (form)  and http://{host}:{port}/demo (historico)")
    app.run(host=host, port=port, debug=False)
