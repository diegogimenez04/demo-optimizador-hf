FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py model.py demo_proceso_unificado.html ./

EXPOSE 7860

CMD ["gunicorn", "-w", "2", "--timeout", "90", "-b", "0.0.0.0:7860", "app:app"]
