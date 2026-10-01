---
title: Demo Optimizador HF
emoji: ⚙️
colorFrom: blue
colorTo: indigo
sdk: docker
pinned: false
---

# Demo Optimizador — Grupo Investigación

Demo Grupo Investigación — Optimización de Procesos Industriales (sin logo, datos sintéticos).

- `demo_proceso_unificado.html` — 7 escenarios históricos (Caso 1 E1-E3+E1.1, Caso 2 E4-E5+E4.1) con Gantt, personal, KPIs.
- `app.py` + `model.py` — Formulario → `function_model` (ortools SCIP) en vivo. Por defecto 5 OTs (una por máquina 23-27).

## Uso local
```bash
pip install -r requirements.txt
python app.py
# http://127.0.0.1:5000  (form)
# http://127.0.0.1:5000/demo  (histórico)
```

## Deploy HF Spaces (Docker)
Espacio espera puerto `7860`:
```bash
gunicorn -w 2 --timeout 90 -b 0.0.0.0:7860 app:app
```
Build via `Dockerfile` incluido.

Repo: https://github.com/diegogimenez04/demo-optimizador-hf
